#!/usr/bin/env python3
"""ssa_s7.py — SSA step S7: standard multiple-choice task anchors.

HellaSwag and Winogrande, both scored by log-probability over fixed candidate answers, so
there is no generation and the cost is a fraction of a generative benchmark. Their job here is
FACE VALIDITY and comparability with published tables — NOT ranking the arms. At the task
counts affordable here the confidence intervals are far wider than the 1-3 point gaps between
quantizations, exactly as they were for HumanEval+; PN-13 is the ranking instrument, not this.

Data is third-party and pinned by sha256 in /srv/bench/corpus/s7-data-provenance.json.
Raw tool output is kept per run (PN-17: a parser is a lossy interpretation you may need to redo).
"""
import json, os, re, subprocess, sys, time

sys.path.insert(0, "/srv/bench/e12/experiments")
import ssa_kld as K

CORPUS = "/srv/bench/corpus"
OUT    = "/srv/bench/e12/ssa/ssa-s7-results.json"
LOGS   = "/srv/bench/server-timings"
ARMS   = ["Q6_K_XL", "Q6_K", "Q5_K_XL", "Q4_K_XL"]

def run(arm, bench, tasks, n_ctx=2048):
    label = f"ssa7-{arm}-{bench}-n{tasks}"
    flag  = {"hellaswag": "--hellaswag", "winogrande": "--winogrande"}[bench]
    dfile = {"hellaswag": "/corpus/hellaswag_val_full.txt",
             "winogrande": "/corpus/winogrande-debiased-eval.csv"}[bench]
    cmd = ["docker", "run", "--rm", "--name", "ssa-s7", "--gpus", "all", "--network", "host",
           "-v", "/srv/models:/models:ro", "-v", "/srv/bench/models:/models2:ro",
           "-v", f"{CORPUS}:/corpus:ro",
           "--entrypoint", "/app/llama-perplexity", K.IMAGE,
           "-m", K.ARMS[arm], "-f", dfile, flag, f"{flag}-tasks", str(tasks),
           "-c", str(n_ctx), "-ngl", "99", "-fa", "on",
           "-ctk", "q4_0", "-ctv", "q4_0", "-s", str(K.SEED)]
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True)
    out = (p.stdout or "") + "\n" + (p.stderr or "")
    os.makedirs(LOGS, exist_ok=True)
    with open(f"{LOGS}/{label}.serverlog", "w") as f:   # log first, always
        f.write(out)
    return {"label": label, "arm": arm, "bench": bench, "tasks": tasks,
            "rc": p.returncode, "seconds": round(time.time() - t0, 1),
            "serverlog": f"{LOGS}/{label}.serverlog",
            "command": " ".join(cmd), "score": parse(out, bench),
            # rc=0 with no parsed accuracy is NOT success (PN-17)
            "ok": p.returncode == 0 and "acc_pct" in parse(out, bench)}

def parse(out, bench):
    """llama-perplexity prints a RUNNING table, one row per task; the LAST row is the result.

    Real format (tab-separated, note the % suffix and the trailing CI column that the first
    version of this parser did not account for -- caught by the pilot gate before any budget
    was spent, which is exactly what the gate is for):
        task\tacc_norm\t95% confidence interval
        25\t72.00000000%\t[52.4177%, 85.7275%]
    Winogrande prints the same shape plus a final summary line.
    """
    m = {}
    rows = re.findall(r"^\s*(\d+)\s*\t\s*([\d.]+)\s*%\s*\t\s*\[\s*([\d.]+)\s*%\s*,\s*([\d.]+)\s*%\s*\]",
                      out, re.M)
    if not rows:   # tolerate whitespace-separated variants
        rows = re.findall(r"^\s*(\d+)\s+([\d.]+)\s*%\s+\[\s*([\d.]+)\s*%\s*,\s*([\d.]+)\s*%\s*\]",
                          out, re.M)
    if rows:
        n, acc, lo, hi = rows[-1]
        m["n"] = int(n); m["acc_pct"] = float(acc)
        m["ci95_lo_pct"] = float(lo); m["ci95_hi_pct"] = float(hi)
        m["n_rows"] = len(rows)
    h = re.search(r"Final Winogrande score\((\d+) tasks\):\s*([\d.]+)\s*(?:\+/-|\u00b1)\s*([\d.]+)", out)
    if h:
        m["n"] = int(h.group(1)); m["acc_pct"] = float(h.group(2)); m["acc_err_pct"] = float(h.group(3))
    # scoring rate, excluding model load: the engine logs when scoring begins
    t = re.search(r"^(\d+)\.(\d+)\.(\d+)\.(\d+)\s+I\s+\w+_score\s*:\s*calculating", out, re.M)
    if t:
        m["load_seconds"] = int(t.group(1)) * 60 + int(t.group(2)) + int(t.group(3)) / 1000.0
    return m

def main():
    """Owner-scoped 2026-08-30: HellaSwag only, 400 tasks, all four arms (~99 min measured).

    Winogrande is dropped -- its 1,267 tasks cost ~69 min/arm on their own, disproportionate for a
    second general-reasoning benchmark that, like HellaSwag, cannot rank these arms. HellaSwag is
    the one the arXiv llama.cpp quantization paper (METHOD-REFERENCES R7) used, so it carries the
    comparability argument.

    Measured cost basis: 250 s fixed model load per cell + 3.08 s per task.

    Resumable: a cell already scored in the results file is skipped, so a restart resumes.
    The FIRST cell acts as the gate -- if it does not produce a parsed accuracy, stop rather than
    spend the remaining budget (the parser was already verified against the pilot log, but a gate
    that costs nothing when it passes is worth keeping).
    """
    if K.gpu_busy():
        print("REFUSING: a GPU experiment is running"); sys.exit(4)
    os.makedirs("/srv/bench/e12/ssa", exist_ok=True)

    TASKS = 400
    prov = json.load(open(f"{CORPUS}/s7-data-provenance.json"))
    data = {"experiment": "ssa-s7", "source": "e12-ssa", "run_ids": ["ssa-s7"],
            "protocol": "SSA S7 - HellaSwag, logprob-scored, 400 tasks x 4 arms",
            "scope_note": ("owner-scoped to HellaSwag only; Winogrande dropped as disproportionate "
                           "(~69 min/arm) for a second benchmark that also cannot rank the arms"),
            "purpose": "FACE VALIDITY and comparability with published tables; NOT a quant ranker",
            "power_note": ("at n=400 the binomial 95% interval is roughly +/-4-5 points while the "
                           "arms are separated by 1-3 points on task benchmarks -- this design "
                           "CANNOT rank them and is not intended to. PN-13/PN-21 rank them."),
            "cost_basis": {"model_load_seconds": 250, "seconds_per_task": 3.08,
                           "source": "measured from the 25-task pilot, not estimated"},
            "data_provenance": prov, "tasks": TASKS, "seed": K.SEED, "kv": "q4_0",
            "image_id": K.image_id(),
            "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "cells": []}
    if os.path.exists(OUT):
        try:
            prev = json.load(open(OUT))
            if prev.get("tasks") == TASKS:
                data = prev; data["cells"] = prev.get("cells", [])
        except Exception:
            pass
    done = {c["arm"] for c in data["cells"]
            if c.get("bench") == "hellaswag" and c.get("tasks") == TASKS and c.get("ok")}

    for i, arm in enumerate(ARMS):
        if arm in done:
            print(f"skip {arm} (already scored)", flush=True); continue
        c = run(arm, "hellaswag", TASKS)
        data["cells"].append(c)
        json.dump(data, open(OUT, "w"), indent=1)
        sc = c["score"]
        print(f"  {arm:<9} rc={c['rc']} {c['seconds']:>6.0f}s  acc_norm="
              f"{sc.get('acc_pct')}  CI95=[{sc.get('ci95_lo_pct')}, {sc.get('ci95_hi_pct')}]",
              flush=True)
        if i == 0 and not c["ok"]:
            print("GATE: first cell produced no parsed accuracy - stopping, budget not spent.")
            print("      inspect", c["serverlog"])
            data["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            json.dump(data, open(OUT, "w"), indent=1)
            sys.exit(2)

    data["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    json.dump(data, open(OUT, "w"), indent=1)
    nok = sum(1 for c in data["cells"] if c.get("ok"))
    print(f"S7 done: {nok}/{len(data['cells'])} cells scored -> {OUT}")
    sys.exit(0 if nok else 2)

if __name__ == "__main__":
    main()
