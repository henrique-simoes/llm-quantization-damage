#!/usr/bin/env python3
"""s9d_depthsweep.py — MTP draft-depth sweep across the quant ladder AT MATCHED DEPTH.

Reinstated by the owner 2026-08-31 from the DEC-12 cancelled set (-> DEC-13). It is the one
cancelled item that REPAIRS a claim the report makes, rather than adding one it lacks.

WHAT IT FIXES
  PN-9 reports that MTP acceptance differs sharply by quantization -- 0.897 (Q6_K_XL), 0.564
  (Q4_K_XL), 0.516 (Q5_K_XL) -- and then has to retract most of its own force, because those
  three cells sat at DIFFERENT context depths (262,144 / 212,992 / 196,608) and DIFFERENT -ts
  ratios. Quant, depth and ratio are confounded, and the note says so explicitly: "a signal
  that the Phase-5 sweep must resolve at matched depth, NOT a measured quant ranking."
  This is that sweep.

  PN-24 reports n=4 > n=2 with the margin growing with depth, measured on UD-Q6_K alone, and
  warns "do not carry this ordering to Q4_K_XL or Q5_K_XL without measuring." This measures it,
  and adds n=8 so the question becomes "where is the optimum" rather than "which of two".

DESIGN
  4 arms x 2 matched depths x 3 draft depths = 24 cells.
    arms    : UD-Q4_K_XL, UD-Q5_K_XL, UD-Q6_K, UD-Q6_K_XL -- each at its OWN Wave-1 winning
              -ts ratio, because the ratio is not portable (PN-7). The ratio therefore varies
              with the arm BY NECESSITY; it is held fixed within an arm across every cell, so
              it cannot confound the draft-depth or depth comparisons, only the between-arm one
              -- which is stated, not hidden.
    depths  : 131,072 and 196,608. Both have VERIFIED pads in the rebuilt ladder (prefill_frac
              0.9435 / 0.9474) and both are reachable by all four arms, including Q6_K_XL whose
              ceiling is 212,992. Unverified pads are not used: PN-5 is exactly the defect of a
              pad that silently comes up short and makes a cell incomparable.
    n_draft : 2, 4, 8.

  Per cell: ONE deep prefill, then THREE 512-token generations.
    - Three reps because this host's within-arm decode noise reaches 32.9 % (PN-19); a single
      reading cannot support a speed claim. Reps 2-3 are nearly free because the server's
      prefix cache means the pad is not re-processed -- recorded per rep as prompt_n/cache_n
      so the claim "the reps are cheap" is checkable rather than asserted.
    - 512 tokens, not S8's 192: acceptance is a ratio over draft events, and S8's at-depth
      acceptance read exactly 1.000 for both arms over 192 tokens, which is not a stable
      estimate. Acceptance is pooled over the three reps.

  A cell is VALID only if prefill_frac >= 0.90 (the PN-5 gate, asserted in code this time,
  not written in a docstring). Invalid cells are recorded with valid=false and excluded from
  every aggregate.
"""
import argparse, json, os, statistics, subprocess, sys, time

sys.path.insert(0, "/srv/bench/e12/experiments")
import lib_e12 as L

E12  = "/srv/bench/e12"
OUTD = f"{E12}/s9"
PADS = f"{E12}/pads"

ARMS = [   # (name, host path, winning -ts from Wave 1)
    ("Q4_K_XL",  "/srv/models/Qwen3.8-27B-UD-Q4_K_XL.gguf",       "56,44"),
    ("Q5_K_XL",  "/srv/models/Qwen3.8-27B-UD-Q5_K_XL.gguf",       "54,46"),
    ("Q6_K",     "/srv/bench/models/Qwen3.8-27B-UD-Q6_K.gguf",    "58,42"),
    ("Q6_K_XL",  "/srv/models/Qwen3.8-27B-UD-Q6_K_XL.gguf",       "56,44"),
]
# ctx -> verified pad file (pads-manifest.json, all_ok=true, rebuilt after the PN-5 defect)
# 262,144 is present for the Q6_K-only addendum (--depths 262144) and is deliberately NOT in
# DEFAULT_DEPTHS: Q6_K_XL's ceiling is 212,992, so including it by default would fail that arm
# and destroy the matched-depth property the whole sweep exists for.
DEPTHS = {131072: f"{PADS}/pad_124006_0.txt",
          196608: f"{PADS}/pad_186265_0.txt",
          262144: f"{PADS}/pad_248524_0.txt"}
DEFAULT_DEPTHS = [131072, 196608]
NDRAFT = [2, 4, 8]
REPS, GEN_TOKENS, DEPTH_GATE = 3, 512, 0.90


def log(*a):
    print(f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}]", *a, flush=True)


def cell(arm, model, ts, ctx, pad_text, n):
    lab = f"{arm}-c{ctx}-n{n}"
    log(f"=== {lab}: launching (-ts {ts}) ===")
    spec = f"--spec-type draft-mtp --spec-draft-n-max {n}"
    cmd, rc, err = L.launch(model, ctx, kv="q4_0", spec="none", sm="layer",
                            ts=ts, ctxcp=32, extra=spec)
    c = {"arm": arm, "model": model, "ts": ts, "ctx": ctx, "n_draft": n,
         "launch_cmd": cmd, "launch_rc": rc, "ok": False, "valid": False,
         "failure_mode": None, "reps": []}
    if rc != 0:
        c["failure_mode"] = f"launch-rc-{rc}"; c["error"] = err[:300]
        L.save_and_kill(f"s9d-{lab}"); log(f"    LAUNCH FAILED: {err[:150]}"); return c
    healthy, secs = L.wait_health(900)
    if not healthy:
        c["failure_mode"] = "load-or-health-failed"; c["health_wait_s"] = secs
        L.save_and_kill(f"s9d-{lab}")
        slog = f"{L.TIMINGS_DIR}/s9d-{lab}.serverlog"
        c["failure_class"] = L.classify_failure(
            open(slog).read() if os.path.exists(slog) else "", "load", err)
        log(f"    LOAD FAILED ({c['failure_class']}) after {secs}s"); return c
    c["n_ctx_reported"] = L.props_nctx()
    if c["n_ctx_reported"] != ctx:            # -fit off is set; this must never differ
        c["failure_mode"] = f"n_ctx-mismatch-{c['n_ctx_reported']}"
        L.save_and_kill(f"s9d-{lab}"); log(f"    N_CTX MISMATCH: {c['n_ctx_reported']}"); return c

    vs = L.VramSampler(); vs.start()
    try:
        for rep in range(REPS):
            r = L.post("/v1/chat/completions",
                       {"messages": [{"role": "user", "content": pad_text}],
                        "temperature": 0, "top_p": 1, "max_tokens": GEN_TOKENS,
                        "seed": L.SEED, "chat_template_kwargs": {"enable_thinking": False}},
                       timeout=7200)
            tm = r.get("timings", {}) or {}
            c["reps"].append({
                "rep": rep, "decode_tok_s": tm.get("predicted_per_second"),
                "prefill_tok_s": tm.get("prompt_per_second"),
                "prompt_n": tm.get("prompt_n"), "cache_n": tm.get("cache_n"),
                "predicted_n": tm.get("predicted_n"),
                "draft_n": tm.get("draft_n"), "draft_n_accepted": tm.get("draft_n_accepted")})
            log(f"    rep{rep}: decode={tm.get('predicted_per_second')} "
                f"prompt_n={tm.get('prompt_n')} cache_n={tm.get('cache_n')} "
                f"draft={tm.get('draft_n_accepted')}/{tm.get('draft_n')}")
        c["ok"] = True
    except Exception as e:
        c["failure_mode"] = "generate-failed"; c["error"] = str(e)[:300]
    finally:
        try:
            c["vram"] = vs.stop()       # stop() returns the summary: peaks + imbalance
        except Exception as e:
            c["vram"] = {"error": str(e)[:120]}

    if c["ok"]:
        ds = [r["decode_tok_s"] for r in c["reps"] if r.get("decode_tok_s")]
        # depth comes from rep 0 — the only rep that actually prefills the pad
        p0 = c["reps"][0]
        c["prompt_n"] = p0.get("prompt_n")
        c["prefill_tok_s"] = p0.get("prefill_tok_s")
        c["prefill_frac"] = round((p0.get("prompt_n") or 0) / ctx, 4)
        c["prefix_cache_worked"] = bool(c["reps"][-1].get("cache_n"))
        dn = sum(r.get("draft_n") or 0 for r in c["reps"])
        da = sum(r.get("draft_n_accepted") or 0 for r in c["reps"])
        c["decode_tok_s_median"] = round(statistics.median(ds), 3) if ds else None
        c["decode_tok_s_reps"] = [round(x, 3) for x in ds]
        c["decode_spread_pct"] = (round(100 * (max(ds) - min(ds)) / min(ds), 1)
                                  if ds and min(ds) else None)
        c["acceptance"] = round(da / dn, 4) if dn else None
        c["draft_n_total"], c["draft_accepted_total"] = dn, da
        # PN-5's gate, asserted in code rather than documented in a docstring
        c["valid"] = c["prefill_frac"] >= DEPTH_GATE
        if not c["valid"]:
            c["invalid_reason"] = f"prefill_frac {c['prefill_frac']} < {DEPTH_GATE}"
        log(f"    -> decode_median={c['decode_tok_s_median']} (reps {c['decode_tok_s_reps']}, "
            f"spread {c['decode_spread_pct']}%) acceptance={c['acceptance']} "
            f"prefill_frac={c['prefill_frac']} valid={c['valid']}")
    L.save_and_kill(f"s9d-{lab}")
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", default="")
    ap.add_argument("--depths", default="")
    ap.add_argument("--ndraft", default="")
    ap.add_argument("--out", default="s9d-depthsweep.json")
    ap.add_argument("--tag", default="s9d-depthsweep")
    a = ap.parse_args()
    os.makedirs(OUTD, exist_ok=True)
    L.preflight()

    arms = [x for x in ARMS if not a.arms or x[0] in a.arms.split(",")]
    want = ([int(x) for x in a.depths.split(",")] if a.depths else DEFAULT_DEPTHS)
    depths = {k: v for k, v in DEPTHS.items() if k in want}
    ndraft = [int(x) for x in a.ndraft.split(",")] if a.ndraft else NDRAFT

    out = {"experiment": a.tag, "source": "e12-s9", "run_ids": ["s9d"],
           "reinstated_by": "DEC-13 (owner, from the DEC-12 cancelled set)",
           "repairs": ["PN-9 quant/depth/ratio confound", "PN-24 generality across the ladder"],
           "image_id": subprocess.run(["docker", "inspect", "-f", "{{.Id}}", L.IMAGE],
                                      capture_output=True, text=True).stdout.strip(),
           "kv": "q4_0", "sm": "layer", "ctxcp": 32, "seed": L.SEED,
           "sampling": "greedy temp=0 top_p=1",
           "sampling_note": ("greedy: this measures throughput and draft acceptance, both of "
                             "which are sampling-independent mechanics, and greedy removes "
                             "sampling variance from the decode reading"),
           "design": {"arms": [x[0] for x in arms], "ts_per_arm": {x[0]: x[2] for x in arms},
                      "depths": sorted(depths), "n_draft": ndraft,
                      "reps_per_cell": REPS, "gen_tokens": GEN_TOKENS,
                      "depth_gate": DEPTH_GATE,
                      "pads": {str(k): v for k, v in depths.items()}},
           "confound_statement": ("-ts varies BETWEEN arms because the optimum is not portable "
                                  "(PN-7), and is held fixed WITHIN an arm across every cell. "
                                  "Draft-depth and context-depth comparisons are therefore clean; "
                                  "the between-arm comparison carries the ratio with it."),
           "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "cells": []}

    pads = {ctx: open(p).read() for ctx, p in depths.items()}
    total = len(arms) * len(depths) * len(ndraft)
    log(f"{total} cells: {len(arms)} arms x {len(depths)} depths x {len(ndraft)} draft depths")

    i = 0
    for arm, model, ts in arms:
        for ctx in sorted(depths):
            for n in ndraft:
                i += 1
                log(f"--- cell {i}/{total} ---")
                out["cells"].append(cell(arm, model, ts, ctx, pads[ctx], n))
                json.dump(out, open(f"{OUTD}/{a.out}", "w"), indent=1)

    # ---- aggregates, over VALID cells only
    val = [c for c in out["cells"] if c.get("valid")]
    out["summary"] = {
        "cells_total": len(out["cells"]), "cells_valid": len(val),
        "cells_failed": [f"{c['arm']}-c{c['ctx']}-n{c['n_draft']}: {c['failure_mode']}"
                         for c in out["cells"] if not c["ok"]],
        "acceptance_at_matched_depth": {
            str(ctx): {c["arm"] + f"-n{c['n_draft']}": c["acceptance"]
                       for c in val if c["ctx"] == ctx}
            for ctx in sorted(depths)},
        "decode_median_at_matched_depth": {
            str(ctx): {c["arm"] + f"-n{c['n_draft']}": c["decode_tok_s_median"]
                       for c in val if c["ctx"] == ctx}
            for ctx in sorted(depths)},
        "best_n_per_arm_per_depth": {},
    }
    for ctx in sorted(depths):
        for arm, _, _ in arms:
            cs = [c for c in val if c["ctx"] == ctx and c["arm"] == arm
                  and c.get("decode_tok_s_median")]
            if cs:
                b = max(cs, key=lambda c: c["decode_tok_s_median"])
                out["summary"]["best_n_per_arm_per_depth"][f"{arm}@{ctx}"] = {
                    "n": b["n_draft"], "decode_tok_s_median": b["decode_tok_s_median"],
                    "acceptance": b["acceptance"],
                    "all_n": {c["n_draft"]: c["decode_tok_s_median"] for c in cs}}

    out["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    json.dump(out, open(f"{OUTD}/{a.out}", "w"), indent=1)
    log("ACCEPTANCE: " + json.dumps(out["summary"]["acceptance_at_matched_depth"]))
    log("BEST-N: " + json.dumps(out["summary"]["best_n_per_arm_per_depth"]))
    log(f"done: {len(val)}/{len(out['cells'])} valid cells")
    sys.exit(0 if val else 2)      # measured nothing -> non-zero, no .done marker


if __name__ == "__main__":
    main()
