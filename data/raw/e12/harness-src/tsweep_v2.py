#!/usr/bin/env python3
"""tsweep_v2.py — the G13 fix (plan qbench-t1-plan-a §3.3, §5).

Fixes e11c's tsweep defects:
  * NEVER returns early; every cell kept; resumable (skips cells already in the output
    JSON unless --redo) — a 3 h sweep must not lose everything on cell 11.
  * Full ratio set {default, 54,46, 56,44, 58,42, 60,40, 62,38} at the speed ctx.
  * Selection among ok cells: max decode_tok_s with the D2 noise floor — if the top two
    are within 10 %, both re-run to median-of-3 (seeds varied per rep); ties broken by
    smaller |imbalance|, then the ratio nearer default.
  * Ceiling bracketing: start one LADDER rung above the known ceiling; climb while a
    ratio succeeds (winner + runner-up per rung); every failed rung is attempted TWICE
    with the winning ratio (R2: a rung is only "failed" after two attempts); if none
    succeeds at the start rung, descend until one does, then re-test the rung above.
  * Per cell: exact command, image id, ctx requested/reported, ok + stage + CLASSIFIED
    failure mode, per-GPU true-peak VRAM (1 Hz sampler across prefill+decode), prefill
    tok/s, decode tok/s at depth (n_predict 192), MTP acceptance + mean accepted length,
    imbalance, serverlog path + bytes.

Usage: tsweep_v2.py --quant {Q4_K_XL,Q5_K_XL,Q6_K,Q6_K_XL} [--out ...] [--redo]
Q6_K additionally runs the D3 -ctxcp 4-vs-32 A/B at its winning cell.
"""
import argparse
import json
import os
import re
import sys
import time

sys.path.insert(0, "/srv/bench/e12/experiments")
import lib_e12 as L
import pad_e12 as P

ALL_RATIOS = [None, "54,46", "56,44", "58,42", "60,40", "62,38"]
LADDER = [262144, 245760, 229376, 212992, 196608, 180224, 163840, 147456, 131072, 114688, 98304]
DECODE_TOKENS = 192

QUANTS = {
    "Q4_K_XL": {"model": "/srv/models/Qwen3.8-27B-UD-Q4_K_XL.gguf", "start": 212992,
                "mode": "ceiling_and_speed", "ratios": ALL_RATIOS},
    "Q5_K_XL": {"model": "/srv/models/Qwen3.8-27B-UD-Q5_K_XL.gguf", "start": 262144,
                "mode": "speed", "ratios": ALL_RATIOS},
    "Q6_K": {"model": "/srv/bench/models/Qwen3.8-27B-UD-Q6_K.gguf", "start": 262144,
             "mode": "speed", "ratios": ALL_RATIOS, "d3": True},
    # Q6_K_XL ratios CORRECTED 2026-08-30. The list was ["58,42","62,38","60,40"], all of
    # which push MORE model onto GPU0 — but the measurement shows 58,42 already OVERSHOOTS
    # for this quant: default split leaves GPU1 heavy by 1,482 MiB (14,356/15,838, E11a
    # @245,760 no-spec) while -ts 58,42 leaves GPU0 heavy by 2,760 MiB (15,036/12,276,
    # measured here @196,608, compute-buffer-oom). The balance point is BETWEEN default and
    # 58,42, and the old list contained no ratio there, so every cell would have failed and
    # G21 would have concluded "rebalance does not lift the Q6_K_XL ceiling" — a false
    # negative on the highest-fidelity quant. Physically: Q6_K_XL's layers are the largest
    # (25.30 GB), so a SMALLER layer-fraction shift moves the same MiB than on Q6_K (21.98 GB),
    # whose optimum is 58,42. Bracket both sides instead.
    "Q6_K_XL": {"model": "/srv/models/Qwen3.8-27B-UD-Q6_K_XL.gguf", "start": 196608,
                "mode": "g21", "ratios": [None, "52,48", "54,46", "56,44", "58,42"]},
}

SUFFIX = "\n\n# Summary:\n"


def ratio_rank(ts):
    """Order for 'ratio nearer default' tie-break: default first, then distance from 50/50."""
    if ts is None:
        return -1
    a = int(ts.split(",")[0])
    return a - 50


def cell_key(ctx, ts, rep, tag):
    return f"{ctx}:{ts or 'default'}:{rep}:{tag or 'base'}"


def parse_acceptance(serverlog_path):
    try:
        txt = open(serverlog_path, errors="replace").read()
    except Exception:
        return {}
    m = re.findall(r"draft acceptance = ([\d.]+) \(\s*(\d+) accepted /\s*(\d+) generated\)"
                   r"(?:, mean len = ([\d.]+))?", txt)
    if not m:
        return {}
    acc, accn, genn, meanlen = m[-1]
    out = {"mtp_acceptance": float(acc), "draft_accepted": int(accn), "draft_generated": int(genn)}
    if meanlen:
        out["mean_accepted_len"] = float(meanlen)
    return out


class Sweep:
    def __init__(self, quant, out, redo=False):
        self.q = quant
        self.cfg = QUANTS[quant]
        self.out = out
        self.redo = redo
        self.data = {
            "experiment": "e12-tensor-split-rebalance-v2", "quant": quant,
            "model": self.cfg["model"], "mode": self.cfg["mode"],
            "source": "e12-wave1", "run_ids": ["tsweep-v2-" + quant],
            "sm": "layer", "kv": "q4_0", "spec": "mtp2", "ctxcp": 4,
            "decode_tokens": DECODE_TOKENS,
            "sampling": L.SAMPLING_NON_THINKING,
            "sampling_note": "DEC-2 non-thinking block on every request (owner 2026-08-30); "
                             "speed/acceptance rows are NOT directly comparable to e11 rows "
                             "measured at temperature 0; ceiling brackets are VRAM-based and "
                             "unaffected; per-quant comparisons are internal to this wave.",
            "ratios": self.cfg["ratios"], "ladder": LADDER,
            "policy": {"climb": "winner+runner-up per rung; failed rung attempted twice with "
                                "the winning ratio (R2)",
                       "d2": "top-two decode medians within 10% -> median-of-3; ties: smaller "
                             "|imbalance|, then ratio nearer default",
                       "d3": "one -ctxcp 4 vs 32 A/B pair at the Q6_K winning cell",
                       "prefill_gate": "a cell FAILS as 'pad-too-short' unless the measured "
                                       "prefill reaches >=0.90 of the requested ctx "
                                       "(enforced 2026-08-30; previously documented only)"},
            "cells": [], "best": None, "best_speed": None, "best_at_ceiling": None,
            "ceiling": None, "d3": None, "g21": None,
        }
        self.keys = set()
        if not redo:
            try:
                prev = json.load(open(out))
                self.data.update({k: prev[k] for k in prev if k != "cells"})
                self.data["cells"] = prev.get("cells", [])
                self.keys = {cell_key(c["ctx_requested"], c.get("ts"), c.get("rep", 1),
                                      c.get("tag")) for c in self.data["cells"]}
                print(f"resuming: {len(self.data['cells'])} cells already present", flush=True)
            except Exception:
                pass
        self.env = L.record_env(self.cfg["model"], self.cfg["start"], ts=None, ctxcp=4,
                                extra={"mode": self.cfg["mode"]})
        self.data["env"] = self.env

    def write(self):
        tmp = self.out + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.data, f, indent=1)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self.out)

    def have(self, ctx, ts, rep=1, tag=None):
        return cell_key(ctx, ts, rep, tag) in self.keys

    def run_cell(self, ctx, ts, rep=1, tag=None, ctxcp=4):
        key = cell_key(ctx, ts, rep, tag)
        if key in self.keys and not self.redo:
            print(f"  skip existing {key}", flush=True)
            return next(c for c in self.data["cells"] if cell_key(
                c["ctx_requested"], c.get("ts"), c.get("rep", 1), c.get("tag")) == key)
        lbl = ("e12-%s-c%d-ts%s" % (self.q, ctx, (ts or "default").replace(",", "_")))
        if tag:
            lbl += f"-{tag}"
        if rep > 1:
            lbl += f"-rep{rep}"
        rec = {"key": key, "ctx_requested": ctx, "ts": ts, "rep": rep, "tag": tag,
               "ctxcp": ctxcp, "ok": False, "stage": "launch", "failure_mode": None,
               "error": "", "n_ctx_reported": 0, "command": None, "image_id": None,
               "prefill_tokens": 0, "prefill_frac": None, "prefill_tok_s": None,
               "decode_tok_s": None, "n_predict": DECODE_TOKENS, "seed": L.SEED + rep,
               "sampling": L.SAMPLING_NON_THINKING, "spec_live": None,
               "draft_n": None, "draft_n_accepted": None,
               "vram_peak_mib": [], "vram_prefill_end_mib": [], "imbalance_mib": None,
               "imbalance_timealigned_mib": None, "load_seconds": None,
               "serverlog": None, "serverlog_bytes": None, "free_bytes": None,
               "when_utc": L.utcnow()}
        sampler = L.VramSampler()
        try:
            L.preflight()
            sampler.start()
            cmd, rc, err = L.launch(self.cfg["model"], ctx, ts=ts, ctxcp=ctxcp)
            rec["command"] = cmd
            rec["image_id"] = L.image_provenance()["image_id"]
            if rc != 0:
                rec["error"] = f"docker run failed: {err}"
                rec["failure_mode"] = L.classify_failure("", "launch", err)
                return self.finish_cell(rec, lbl, sampler)
            okh, secs = L.wait_health(600)
            rec["load_seconds"] = secs
            if not okh:
                rec["stage"] = "health"
                rec["error"] = ("load hang / died: " + L.container_err(600)).replace("\n", " ")[:400]
                rec["failure_mode"] = L.classify_failure(L.container_err(2000), "health")
                return self.finish_cell(rec, lbl, sampler)
            rec["n_ctx_reported"] = L.props_nctx()
            if rec["n_ctx_reported"] != ctx:
                rec["stage"] = "props"
                rec["error"] = f"silent shrink to {rec['n_ctx_reported']} (requested {ctx})"
                rec["failure_mode"] = "props-shrink"
                return self.finish_cell(rec, lbl, sampler)
            # --- deep prefill: >=90 % of the window (behavioural gate; VRAM recorded) ---
            rec["stage"] = "prefill"
            target = int(ctx * 0.95) - 512
            text, exact = P.build(target, with_needles=False)
            rec["prefill_tokens"] = exact
            rec["prefill_frac"] = round(exact / ctx, 4)
            rec["prefill_target_tokens"] = target
            # HARD GATE (added 2026-08-30): the contract above says ">=90 % of the window".
            # It was documented but never enforced, and the pad builder's fixed-bracket
            # bisection silently returned 169,823/212,992 = 0.797 for Q4_K_XL — recorded as
            # if it were full depth. Decode tok/s is strongly depth-dependent (37.22 -> 7.19
            # across depth on Q6_K), and peak VRAM is sampled across prefill, so a short pad
            # makes BOTH the speed row and the ceiling verdict optimistic. Fail loudly.
            if rec["prefill_frac"] < 0.90:
                rec["failure_mode"] = "pad-too-short"
                rec["error"] = (f"prefill reached {exact} tokens = {rec['prefill_frac']:.4f} "
                                f"of ctx {ctx} (target {target}); below the 0.90 depth gate")
                return self.finish_cell(rec, lbl, sampler)
            r = L.post("/completion", {"prompt": text, "n_predict": 1, "cache_prompt": False,
                                       "seed": L.SEED, **L.SAMPLING_NON_THINKING}, timeout=7200)
            rec["prefill_tok_s"] = (r.get("timings", {}) or {}).get("prompt_per_second")
            rec["vram_prefill_end_mib"] = sampler.last()
            # --- decode at depth, n_predict 192 (D2) ---
            rec["stage"] = "generate"
            r2 = L.post("/completion", {"prompt": text + SUFFIX, "n_predict": DECODE_TOKENS,
                                        "cache_prompt": True, "seed": L.SEED + rep,
                                        **L.SAMPLING_NON_THINKING}, timeout=3600)
            tm = r2.get("timings", {}) or {}
            rec["decode_tok_s"] = tm.get("predicted_per_second")
            rec["draft_n"] = tm.get("draft_n")
            rec["draft_n_accepted"] = tm.get("draft_n_accepted")
            rec["spec_live"] = L.spec_live(r2)
            if tm.get("draft_n"):
                rec["mtp_acceptance"] = round((tm.get("draft_n_accepted") or 0) / tm["draft_n"], 4)
            rec["truncated"] = r2.get("truncated")
            rec["ok"] = (rec["truncated"] is False
                          and bool(r2.get("content") or tm.get("predicted_per_second")))
            if not rec["ok"] and rec["failure_mode"] is None:
                rec["failure_mode"] = "incomplete-response"
            rec["stage"] = "done"
        except Exception as e:
            rec["error"] = (f"{rec['stage']} failed: {e} | "
                            + L.container_err(400)).replace("\n", " ")[:500]
            rec["failure_mode"] = L.classify_failure(L.container_err(2000), rec["stage"], str(e))
        return self.finish_cell(rec, lbl, sampler)

    def finish_cell(self, rec, lbl, sampler):
        try:
            nb, tg = L.save_and_kill(lbl)
            rec["serverlog"] = f"{L.TIMINGS_DIR}/{lbl}.serverlog"
            rec["serverlog_bytes"] = nb
            acc = parse_acceptance(rec["serverlog"])
            for k in ("mtp_acceptance", "mean_accepted_len"):
                if rec.get(k) is None and k in acc:
                    rec[k] = acc[k]
            if rec.get("mtp_acceptance") is None and rec.get("draft_n_accepted") is not None:
                rec["mtp_acceptance"] = round(rec["draft_n_accepted"] / max(rec["draft_n"], 1), 4)
        except Exception as e:
            rec["teardown_error"] = str(e)[:300]
            rec["ok"] = False
            rec["failure_mode"] = "teardown-fail"
        s = sampler.stop()
        rec["vram_peak_mib"] = s["vram_peak_mib"]
        rec["imbalance_mib"] = s["imbalance_mib"]
        rec["imbalance_timealigned_mib"] = s["imbalance_timealigned_mib"]
        rec["free_bytes"] = L.df_b1()
        rec["finished_utc"] = L.utcnow()
        if rec["ok"]:
            rec["failure_mode"] = None
        self.data["cells"].append(rec)
        self.keys.add(rec["key"])
        self.write()
        print("   " + json.dumps({k: rec.get(k) for k in
                                  ("ok", "stage", "failure_mode", "decode_tok_s",
                                   "prefill_tok_s", "prefill_frac", "mtp_acceptance",
                                   "vram_peak_mib", "imbalance_mib", "error")})[:340],
                                 flush=True)
        return rec

    def ok_cells(self, ctx=None, tag=None, rep=None):
        out = []
        for c in self.data["cells"]:
            if not c["ok"]:
                continue
            if ctx is not None and c["ctx_requested"] != ctx:
                continue
            if tag is None:
                if c.get("tag") not in (None, "retest"):
                    continue          # ctxcp32 / other instrument cells are not sweep cells
            elif c.get("tag") != tag:
                continue
            if rep is not None and c.get("rep", 1) != rep:
                continue
            out.append(c)
        return out

    def attempts_of(self, ctx, ts):
        """Number of launch attempts of one (ctx, ts) config, any tag/rep (A6 counting)."""
        return sum(1 for c in self.data["cells"]
                   if c["ctx_requested"] == ctx and c.get("ts") == ts)

    def launch_args_failed(self, ctx, ts):
        """True iff any attempt of (ctx, ts) died on a deterministic argv error — that is
        an instrument failure, not VRAM evidence, so R2's retest must not burn on it."""
        return any(c.get("failure_mode") == "launch-args" for c in self.data["cells"]
                   if c["ctx_requested"] == ctx and c.get("ts") == ts)

    def pick_best(self, cells):
        """max decode_tok_s; D2 contest resolution happens in the sweep loop (needs re-runs);
        static tie-breaks: smaller |imbalance|, then ratio nearer default."""
        if not cells:
            return None
        return sorted(cells, key=lambda c: (-(c.get("decode_tok_s") or 0),
                                            c.get("imbalance_mib") if c.get("imbalance_mib")
                                            is not None else 1 << 30,
                                            ratio_rank(c.get("ts"))))[0]


def sweep_ceiling_and_speed(S):
    """Q4_K_XL: start one rung above the known ceiling; full 6-ratio sweep at the start
    rung (the speed row); climb while a ratio succeeds; every failed rung is attempted
    twice with the winning ratio (R2/A6) — including the start rung after a descend."""
    start = S.cfg["start"]
    i = LADDER.index(start)
    rung = start
    while True:
        print(f"=== {S.q} rung {rung}: full ratio sweep", flush=True)
        for ts in S.cfg["ratios"]:
            S.run_cell(rung, ts)
        if S.ok_cells(ctx=rung):
            break
        if i + 1 >= len(LADDER):
            S.data["ceiling"] = {"ctx": None, "note": "no rung succeeded (all cells failed)"}
            return
        i += 1
        rung = LADDER[i]
    S.data["best_speed"] = rung
    while True:
        oks = S.ok_cells(ctx=rung)
        if not oks:
            break
        ranked = S.pick_best(oks)
        S.data["best_at_ceiling"] = ranked
        if i == 0:
            S.data["ceiling"] = {"ctx": rung, "note": "ladder top (262,144) reached"}
            break
        nxt = LADDER[i - 1]
        wts = ranked["ts"]
        print(f"=== climb: {rung} -> {nxt} with winner {wts}", flush=True)
        if S.attempts_of(nxt, wts) == 0:
            S.run_cell(nxt, wts)
        runner = next((c for c in oks if c["ts"] != wts), None)
        if runner is not None and S.attempts_of(nxt, runner["ts"]) == 0:
            S.run_cell(nxt, runner["ts"])
        if (not S.ok_cells(ctx=nxt) and S.attempts_of(nxt, wts) < 2
                and not S.launch_args_failed(nxt, wts)):
            print(f"=== re-test (attempt {S.attempts_of(nxt, wts) + 1}): {nxt} with {wts}",
                  flush=True)
            S.run_cell(nxt, wts, tag="retest")
        if S.ok_cells(ctx=nxt):
            i -= 1
            rung = nxt
            continue
        n_att = S.attempts_of(nxt, wts)
        S.data["ceiling"] = {"ctx": rung, "failed_rung_above": nxt,
                             "failed_rung_attempts": n_att,
                             "note": f"rung {nxt} failed; winning config attempted "
                                     f"{n_att} times (R2 two-attempt rule)"}
        break
    if S.data.get("ceiling") is None:
        S.data["ceiling"] = {"ctx": rung, "note": "climb ended"}
        oks = S.ok_cells(ctx=rung)
        S.data["best_at_ceiling"] = S.pick_best(oks) if oks else None
    resolve_best(S)


def sweep_speed(S):
    """Q5/Q6: full ratio sweep at the native-max ctx; no rung above exists."""
    start = S.cfg["start"]
    S.data["best_speed"] = start
    for ts in S.cfg["ratios"]:
        S.run_cell(start, ts)
    if not S.ok_cells(ctx=start):
        # 2026-08-30: previously the ceiling was asserted unconditionally, so a rung where
        # EVERY ratio failed would still publish "ceiling = 262,144".
        S.data["ceiling"] = {"ctx": None, "attempted_ctx": start,
                             "note": "no ratio succeeded at the native maximum; this quant "
                                     "has no rebalanced ceiling at this rung"}
        return
    S.data["ceiling"] = {"ctx": start,
                         "note": "262,144 is the engine/native maximum — no rung above "
                                 "exists to bracket; historical failed rungs BELOW it are "
                                 "recorded per-cell with classified modes"}
    resolve_best(S)


def sweep_g21(S):
    """Q6_K_XL (G21, owner gate Q-A1=YES): start at 196,608 with the named ratios;
    descend while all fail (down to 131,072); if a rung passes, a BOUNDED climb (max two
    rungs above the start) with the two-attempt rule brackets the rebalanced ceiling."""
    start = S.cfg["start"]
    i = LADDER.index(start)
    rung = start
    climbs = 0
    while True:
        print(f"=== {S.q} rung {rung}: ratios {S.cfg['ratios']}", flush=True)
        for ts in S.cfg["ratios"]:
            S.run_cell(rung, ts)
        oks = S.ok_cells(ctx=rung)
        if oks:
            S.data["best_speed"] = rung
            break
        if i + 1 >= len(LADDER) or LADDER[i + 1] < 131072:
            S.data["g21"] = {"verdict": "rebalance does not lift the Q6_K_XL MTP ceiling "
                                        "above 131,072 on this image",
                             "note": "all named ratios failed at every rung tried down to "
                                     "131,072; the published 131,072 MTP (default-split) "
                                     "ceiling stands as the un-rebalanced lower bound",
                             "ceiling_ctx": None}
            S.data["ceiling"] = {"ctx": None, "note": S.data["g21"]["verdict"]}
            return
        i += 1
        rung = LADDER[i]
    while True:
        oks = S.ok_cells(ctx=rung)
        if not oks:
            break
        ranked = S.pick_best(oks)
        S.data["best_at_ceiling"] = ranked
        wts = ranked["ts"]
        if i == 0 or climbs >= 2 or LADDER[i - 1] > 229376:
            S.data["ceiling"] = {"ctx": rung,
                                 "note": "bracket bound reached (start rung +2 climbs or "
                                         "ladder top); higher rungs out of G21 scope"}
            break
        nxt = LADDER[i - 1]
        print(f"=== g21 bracket above: {nxt} with {wts} (2 attempts)", flush=True)
        if S.attempts_of(nxt, wts) == 0:
            S.run_cell(nxt, wts)
        if (not S.ok_cells(ctx=nxt) and S.attempts_of(nxt, wts) < 2
                and not S.launch_args_failed(nxt, wts)):
            S.run_cell(nxt, wts, tag="retest")
        if S.ok_cells(ctx=nxt):
            i -= 1
            rung = nxt
            climbs += 1
            continue
        n_att = S.attempts_of(nxt, wts)
        S.data["ceiling"] = {"ctx": rung, "failed_rung_above": nxt,
                             "failed_rung_attempts": n_att,
                             "note": f"rung {nxt} failed; winning config attempted "
                                     f"{n_att} times (R2 two-attempt rule)"}
        break
    S.data["g21"] = {"verdict": f"Q6_K_XL MTP ceiling rebalanced to "
                                f"{(S.data.get('ceiling') or {}).get('ctx') or 'no success'} "
                                f"(published default-split: 131,072)",
                     "best_ts": (S.data.get("best_at_ceiling") or {}).get("ts"),
                     "ceiling": S.data.get("ceiling")}


def resolve_best(S):
    """D2 selection at the speed ctx: max decode; contest -> median-of-3 re-runs."""
    rung = S.data.get("best_speed") or S.cfg["start"]
    oks = [c for c in S.ok_cells(ctx=rung, rep=1)]
    if not oks:
        return
    def rank(c, speed=None):
        value = c.get("decode_tok_s") if speed is None else speed
        return (-(value or 0),
                c.get("imbalance_mib") if c.get("imbalance_mib") is not None else 1 << 30,
                ratio_rank(c.get("ts")))

    ranked = sorted(oks, key=rank)
    top = ranked[0]
    contest = None
    if len(ranked) > 1:
        second = ranked[1]
        a, b = top.get("decode_tok_s") or 0, second.get("decode_tok_s") or 0
        if a > 0 and b > 0 and abs(a - b) / max(a, b) <= 0.10:
            contest = {"contested": [top["ts"], second["ts"]],
                       "base": {top["ts"]: a, second["ts"]: b}}
            med = {}
            for cand in (top, second):
                vals = [cand.get("decode_tok_s") or 0]
                for rep in (2, 3):
                    c = S.run_cell(rung, cand["ts"], rep=rep)
                    vals.append(c.get("decode_tok_s") or 0)
                med[cand["ts"]] = sorted(vals)[1]
            contest["median_of_3"] = med
            top = sorted((top, second),
                         key=lambda c: (-med[c["ts"]],
                                        c.get("imbalance_mib") if c.get("imbalance_mib")
                                        is not None else 1 << 30,
                                        ratio_rank(c.get("ts"))))[0]
    S.data["d2"] = contest or {"contested": None,
                               "note": "top-two gap > 10 % — no re-run required"}
    # static tie-break chain across ALL ok cells at the rung
    S.data["best"] = {"ctx": top["ctx_requested"], "ts": top["ts"],
                      "decode_tok_s": top.get("decode_tok_s"),
                      "decode_tok_s_rep1": top.get("decode_tok_s"),
                      "decode_tok_s_median3": (contest or {}).get(
                          "median_of_3", {}).get(top["ts"]),
                      "selected_on": "median_of_3" if contest else "rep1",
                      "imbalance_mib": top.get("imbalance_mib"),
                      "mtp_acceptance": top.get("mtp_acceptance"),
                      "key": top["key"],
                      "rule": "max decode_tok_s; D2 median-of-3 on contest; ties: smaller "
                              "|imbalance|, then ratio nearer default"}


def run_d3(S):
    """D3: -ctxcp 4 vs 32 A/B at the winning cell."""
    best = S.data.get("best")
    if not best:
        return
    winner = next(c for c in S.data["cells"] if c["key"] == best["key"])
    alt = S.run_cell(best["ctx"], best["ts"], tag="ctxcp32", ctxcp=32)
    d = {"ctxcp4": {k: winner.get(k) for k in
                    ("key", "vram_peak_mib", "imbalance_mib", "decode_tok_s",
                     "prefill_tok_s", "n_ctx_reported")},
         "ctxcp32": {k: alt.get(k) for k in
                     ("key", "vram_peak_mib", "imbalance_mib", "decode_tok_s",
                      "prefill_tok_s", "n_ctx_reported")}}
    if alt["ok"]:
        dv = [((alt["vram_peak_mib"][g] - winner["vram_peak_mib"][g])
               if winner.get("vram_peak_mib") and len(winner["vram_peak_mib"]) == 2 else None)
              for g in range(2)]
        ds = (((alt.get("decode_tok_s") or 0) - (winner.get("decode_tok_s") or 0))
              / max(winner.get("decode_tok_s") or 1, 1e-9))
        d["delta_vram_mib"] = dv
        d["delta_decode_frac"] = round(ds, 4)
        noise = all(x is not None and abs(x) <= 200 for x in dv)
        if noise and abs(ds) <= 0.10:
            d["verdict"] = ("adopt ctxcp 32 for Waves 2-4 (delta within R2 noise: "
                            "|dv|<=200 MiB and |d_decode|<=10%)")
        else:
            d["verdict"] = ("keep ctxcp 4; candidate config line's ctxcp value is a "
                            "material confounder — FINDING (plan D3)")
    else:
        d["verdict"] = "ctxcp 32 cell failed to run: " + str(alt.get("failure_mode"))
    S.data["d3"] = d
    S.write()
    print("D3: " + json.dumps(d)[:400], flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quant", required=True, choices=list(QUANTS))
    ap.add_argument("--out", default=None)
    ap.add_argument("--redo", action="store_true")
    a = ap.parse_args()
    out = a.out or f"/srv/bench/e12/tsweep-v2-{a.quant}.json"
    S = Sweep(a.quant, out, redo=a.redo)
    t0 = time.time()
    try:
        if S.cfg["mode"] == "ceiling_and_speed":
            sweep_ceiling_and_speed(S)
        elif S.cfg["mode"] == "speed":
            sweep_speed(S)
        elif S.cfg["mode"] == "g21":
            sweep_g21(S)
        if S.cfg.get("d3"):
            run_d3(S)
    except Exception as e:
        S.data["fatal"] = str(e)[:500]
        S.write()
        print(f"FATAL in sweep {a.quant}: {e}", flush=True)
        L.gpu_lock_release()
        return 1
    S.write()
    L.gpu_lock_release()
    n_ok = len([c for c in S.data["cells"] if c.get("ok")])
    if n_ok == 0:
        # 2026-08-30: this returned 0 regardless, so the runner wrote a .done marker for a
        # sweep in which every single cell failed (seen when a lock-contention race made all
        # 6 Q6_K cells fail). A sweep with no successful cell has measured nothing.
        print(f"SWEEP {a.quant} produced NO successful cells ({len(S.data['cells'])} "
              f"attempted) -> failing so no .done marker is written", flush=True)
        return 2
    print(f"SWEEP {a.quant} DONE in {(time.time()-t0)/60:.1f} min, {n_ok} ok cells -> {out}",
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
