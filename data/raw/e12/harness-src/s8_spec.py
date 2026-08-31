#!/usr/bin/env python3
"""s8_spec.py — merged speculative-decoding test: MTP vs DFlash2, quality AND speed.

Owner design 2026-08-30: rather than run Wave 2's setting sweeps (6-10 h) and SSA S6
(generative HumanEval+) separately, run HumanEval+ ONCE PER SPEC CONFIG and harvest three
answers from the same generations.

WHY pass@1 is NOT the discriminator here. Speculative decoding is designed to be
output-LOSSLESS: at greedy it should emit exactly the tokens no-spec would. If that holds,
every config yields identical code and identical pass@1, and pass@1 measures nothing. If it
does not hold, pass@1 at n=164 (+/-4.6 pts) still cannot resolve arms 1-3 points apart. So the
winner is decided on SPEED CONDITIONAL ON PROVEN EQUIVALENCE, and pass@1 rides along as
face validity (the S6 deliverable).

What each run yields:
  1. exact-output-match vs the no-spec baseline + first-divergence index  -> closes G8
  2. decode tok/s and draft acceptance on a REAL coding workload          -> the spec winner
  3. pass@1 via the e11 evalplus pipeline, with Wilson CIs and McNemar    -> S6 face validity

SAMPLING EXCEPTION, deliberate and scoped: greedy (temp 0), NOT DEC-2's official sampling.
Losslessness is defined at greedy and exact-match is only meaningful there. Recorded in the
artifact so this cannot later look like protocol drift.

PHASE 2 (atdepth) exists because the phase-1 verdict is a SHORT-CONTEXT verdict, and
PAPER-REFERENCES records that MTP vs DFlash2 REVERSES at long context (MTP 32.62 tok/s @168K
acceptance 0.92 vs DFlash2 30.26 @184K acceptance 0.55, the opposite of the 1K-generation
result). It also tests a known hazard: the "1.19 GiB draft-worker wall". DFlash2 needs a
SEPARATE 1.1 GB draft GGUF, and the Track A config already peaks at 15,322/15,082 MiB of
~15,650 usable at 262,144 -- so DFlash may simply not fit at the deployment context. If it
does not, that is the answer for deployment, and it is cheap to establish.
"""
import argparse, difflib, json, os, re, subprocess, sys, time

sys.path.insert(0, "/srv/bench/e12/experiments")
import lib_e12 as L

E12   = "/srv/bench/e12"
OUTD  = f"{E12}/s8"
EV    = "/srv/bench/.venv-evalplus/bin"
Q6K   = "/srv/bench/models/Qwen3.8-27B-UD-Q6_K.gguf"     # Track A primary
DRAFT = "/models/dflash2/Qwen3.8-27B-DFlash2-Q4_K_M.gguf"  # container path
HE_CTX = 32768        # HumanEval+ prompts are short; keeps VRAM free for the draft model

CONFIGS = [
    ("nospec",  ""),
    ("mtp2",    "--spec-type draft-mtp --spec-draft-n-max 2"),
    ("mtp4",    "--spec-type draft-mtp --spec-draft-n-max 4"),
    ("dflash4", f"--spec-type draft-dflash --spec-draft-n-max 4 -md {DRAFT}"),
]

def log(*a):
    print(f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}]", *a, flush=True)

# ---------------------------------------------------------------- phase 1
def gen_one_config(name, spec_args, tasks, ctx=HE_CTX, max_tokens=1024):
    """Launch one spec config and generate all HumanEval+ completions under it."""
    log(f"=== config {name}: launching (ctx={ctx}) ===")
    cmd, rc, err = L.launch(Q6K, ctx, kv="q4_0", spec="none", sm="layer",
                            ts="58,42", ctxcp=32, extra=spec_args)
    rec = {"config": name, "spec_args": spec_args, "launch_cmd": cmd, "launch_rc": rc,
           "ctx": ctx, "max_tokens": max_tokens, "sampling": "greedy temp=0 top_p=1",
           "argv": None, "items": [], "ok": False, "failure_mode": None}
    if rc != 0:
        rec["failure_mode"] = f"launch-rc-{rc}"; rec["error"] = err[:400]
        L.save_and_kill(f"s8-{name}-launchfail"); return rec
    if not L.wait_health(600):
        rec["failure_mode"] = "health-timeout"
        L.save_and_kill(f"s8-{name}-health"); return rec
    rec["argv"] = L.container_argv()

    t0 = time.time()
    for i, (tid, prob) in enumerate(tasks):
        try:
            r = L.post("/v1/chat/completions",
                       {"messages": [{"role": "user", "content": prob["prompt"]}],
                        "temperature": 0, "top_p": 1, "max_tokens": max_tokens,
                        "seed": L.SEED,
                        # this model REASONS by default and returns empty content on a small
                        # budget; /no_think does not work on this template (PN-2)
                        "chat_template_kwargs": {"enable_thinking": False}},
                       timeout=1800)
            tm = r.get("timings", {}) or {}
            txt = r["choices"][0]["message"]["content"] or ""
            rec["items"].append({
                "task_id": tid, "solution": txt,
                "decode_tok_s": tm.get("predicted_per_second"),
                "predicted_n": tm.get("predicted_n"), "prompt_n": tm.get("prompt_n"),
                "draft_n": tm.get("draft_n"), "draft_n_accepted": tm.get("draft_n_accepted"),
            })
        except Exception as e:
            rec["items"].append({"task_id": tid, "solution": "", "error": str(e)[:200]})
        if (i + 1) % 40 == 0:
            log(f"    {name}: {i+1}/{len(tasks)} ({time.time()-t0:.0f}s)")
    rec["seconds"] = round(time.time() - t0, 1)
    rec["ok"] = sum(1 for it in rec["items"] if it.get("solution")) > 0
    # aggregate speed + acceptance over items that actually generated
    ds = [it["decode_tok_s"] for it in rec["items"] if it.get("decode_tok_s")]
    dn = sum(it.get("draft_n") or 0 for it in rec["items"])
    da = sum(it.get("draft_n_accepted") or 0 for it in rec["items"])
    rec["decode_tok_s_mean"] = round(sum(ds) / len(ds), 3) if ds else None
    rec["decode_tok_s_median"] = round(sorted(ds)[len(ds)//2], 3) if ds else None
    rec["acceptance"] = round(da / dn, 4) if dn else None
    rec["draft_n_total"], rec["draft_accepted_total"] = dn, da
    L.save_and_kill(f"s8-{name}-he")
    log(f"=== {name}: {rec['seconds']}s  decode_median={rec['decode_tok_s_median']} "
        f"acceptance={rec['acceptance']} ===")
    return rec

def equivalence(recs):
    """Exact-output match against the no-spec baseline + first divergence index."""
    base = next((r for r in recs if r["config"] == "nospec"), None)
    if not base:
        return {"error": "no baseline"}
    bmap = {it["task_id"]: it.get("solution", "") for it in base["items"]}
    out = {}
    for r in recs:
        if r["config"] == "nospec":
            continue
        same = diff = 0; firsts = []
        for it in r["items"]:
            b = bmap.get(it["task_id"], ""); s = it.get("solution", "")
            if b == s:
                same += 1
            else:
                diff += 1
                idx = next((i for i, (x, y) in enumerate(zip(b, s)) if x != y), min(len(b), len(s)))
                firsts.append(idx)
        n = same + diff
        out[r["config"]] = {
            "n": n, "exact_match": same, "differs": diff,
            "exact_match_pct": round(100.0 * same / n, 2) if n else None,
            "first_divergence_char_median": (sorted(firsts)[len(firsts)//2] if firsts else None),
            "lossless": diff == 0,
        }
    return out

# ---------------------------------------------------------------- phase 2
def atdepth(ladder, pad_text):
    """Speed only, at depth. Establishes whether DFlash even LOADS at the Track A context."""
    res = []
    for name, spec_args in CONFIGS:
        for ctx in ladder:
            log(f"=== atdepth {name} @ {ctx} ===")
            cmd, rc, err = L.launch(Q6K, ctx, kv="q4_0", spec="none", sm="layer",
                                    ts="58,42", ctxcp=32, extra=spec_args)
            cell = {"config": name, "ctx": ctx, "launch_cmd": cmd, "ok": False,
                    "failure_mode": None}
            if rc != 0 or not L.wait_health(600):
                cell["failure_mode"] = "load-or-health-failed"
                cell["error"] = err[:300]
                L.save_and_kill(f"s8-atdepth-{name}-{ctx}")
                res.append(cell); log(f"    FAILED: {cell['failure_mode']} -> trying a lower rung")
                continue         # ladder DESCENDS: a failure means try lower, not stop
            try:
                n_pad = int(ctx * 0.945)
                r = L.post("/v1/chat/completions",
                           {"messages": [{"role": "user", "content": pad_text[:n_pad*4]},
                                         ],
                            "temperature": 0, "top_p": 1, "max_tokens": 192,
                            "seed": L.SEED,
                            "chat_template_kwargs": {"enable_thinking": False}},
                           timeout=7200)
                tm = r.get("timings", {}) or {}
                dn, da = tm.get("draft_n") or 0, tm.get("draft_n_accepted") or 0
                cell.update({"ok": True,
                             "decode_tok_s": tm.get("predicted_per_second"),
                             "prefill_tok_s": tm.get("prompt_per_second"),
                             "prompt_n": tm.get("prompt_n"),
                             "prefill_frac": round((tm.get("prompt_n") or 0) / ctx, 4),
                             "acceptance": round(da / dn, 4) if dn else None})
                log(f"    ok decode={cell['decode_tok_s']} acc={cell['acceptance']} "
                    f"prefill_frac={cell['prefill_frac']}")
            except Exception as e:
                cell["failure_mode"] = "generate-failed"; cell["error"] = str(e)[:300]
            L.save_and_kill(f"s8-atdepth-{name}-{ctx}")
            res.append(cell)
            if cell["ok"]:
                log(f"    {name}: highest reachable rung is {ctx} -- not testing lower")
                break            # descending ladder: first success IS this config's ceiling
    return res

# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True, choices=["humaneval", "atdepth", "score"])
    ap.add_argument("--ladder", default="262144,212992,163840,131072")
    a = ap.parse_args()
    os.makedirs(OUTD, exist_ok=True)
    L.preflight()

    if a.phase == "humaneval":
        from evalplus.data import get_human_eval_plus
        probs = get_human_eval_plus()
        tasks = sorted(probs.items(), key=lambda kv: int(kv[0].split("/")[1]))
        log(f"{len(tasks)} HumanEval+ problems, {len(CONFIGS)} configs, greedy, ctx={HE_CTX}")
        data = {"experiment": "s8-spec", "source": "e12-s8", "run_ids": ["s8"],
                "quant": "UD-Q6_K", "quant_note": "Track A primary; the spec question is about the METHOD, not the quant",
                "image_id": subprocess.run(["docker","inspect","-f","{{.Id}}","llamacpp-mtp:latest"],
                                          capture_output=True, text=True).stdout.strip(),
                "sampling_exception": ("greedy temp=0 -- DELIBERATE departure from DEC-2 official "
                                       "sampling: losslessness is defined at greedy and exact-match "
                                       "is only meaningful there"),
                "power_note": ("pass@1 at n=164 carries ~+/-4.6 pts and CANNOT rank spec configs; "
                               "the winner is decided on speed CONDITIONAL ON equivalence"),
                "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "configs": []}
        for name, spec in CONFIGS:
            data["configs"].append(gen_one_config(name, spec, tasks))
            json.dump(data, open(f"{OUTD}/s8-humaneval.json", "w"), indent=1)
            # jsonl for the e11 evalplus pipeline
            with open(f"{OUTD}/s8-{name}.jsonl", "w") as f:
                for it in data["configs"][-1]["items"]:
                    f.write(json.dumps({"task_id": it["task_id"],
                                        "solution": it.get("solution", "")}) + "\n")
        data["equivalence"] = equivalence(data["configs"])
        data["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        json.dump(data, open(f"{OUTD}/s8-humaneval.json", "w"), indent=1)
        log("EQUIVALENCE: " + json.dumps(data["equivalence"]))
        nok = sum(1 for c in data["configs"] if c["ok"])
        log(f"phase humaneval done: {nok}/{len(CONFIGS)} configs generated")
        sys.exit(0 if nok else 2)

    if a.phase == "atdepth":
        ladder = [int(x) for x in a.ladder.split(",")]
        pad = open(f"{E12}/corpus.txt").read()
        data = {"experiment": "s8-atdepth", "source": "e12-s8", "quant": "UD-Q6_K",
                "ts": "58,42", "ctxcp": 32, "kv": "q4_0",
                "purpose": ("does each spec method LOAD and how fast is it at the Track A "
                            "deployment context; tests the 1.19 GiB draft-worker wall"),
                "ladder": ladder,
                "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "cells": atdepth(ladder, pad)}
        data["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        json.dump(data, open(f"{OUTD}/s8-atdepth.json", "w"), indent=1)
        nok = sum(1 for c in data["cells"] if c["ok"])
        log(f"phase atdepth done: {nok}/{len(data['cells'])} cells ok")
        sys.exit(0 if nok else 2)

    if a.phase == "score":
        out = {}
        for name, _ in CONFIGS:
            j = f"{OUTD}/s8-{name}.jsonl"
            if not os.path.exists(j):
                continue
            subprocess.run([f"{EV}/evalplus.sanitize", "--samples", j],
                           capture_output=True, text=True, timeout=3600)
            san = j.replace(".jsonl", "-sanitized.jsonl")
            src = san if os.path.exists(san) else j
            r = subprocess.run([f"{EV}/evalplus.evaluate", "--dataset", "humaneval",
                                "--samples", src],
                               capture_output=True, text=True, timeout=7200)
            open(f"{OUTD}/s8-{name}-eval.txt", "w").write(r.stdout + "\n" + r.stderr)
            m = re.findall(r"(base|base \+ extra|humaneval\+?)[^\d]*([\d.]+)", r.stdout, re.I)
            out[name] = {"raw_tail": r.stdout[-1200:], "parsed": m}
            log(f"scored {name}: {m}")
        json.dump(out, open(f"{OUTD}/s8-scores.json", "w"), indent=1)
        log("phase score done")
        sys.exit(0)

if __name__ == "__main__":
    main()
