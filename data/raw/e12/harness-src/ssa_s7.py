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
            "ok": p.returncode == 0}

def parse(out, bench):
    m = {}
    # winogrande prints a final line with an uncertainty; hellaswag prints a running
    # "<n>\t<acc>" table whose LAST row is the final score.
    h = re.search(r"Final Winogrande score\((\d+) tasks\):\s*([\d.]+)\s*(?:\+/-|±)\s*([\d.]+)", out)
    if h:
        m["n"], m["acc_pct"], m["acc_err_pct"] = int(h.group(1)), float(h.group(2)), float(h.group(3))
    rows = re.findall(r"^\s*(\d+)\s+([\d.]+)\s*$", out, re.M)
    if rows and "acc_pct" not in m:
        m["n"], m["acc_pct"] = int(rows[-1][0]), float(rows[-1][1])
    h2 = re.search(r"Final result:\s*([\d.]+)\s*(?:\+/-|±)\s*([\d.]+)", out)
    if h2:
        m["acc_pct"], m["acc_err_pct"] = float(h2.group(1)), float(h2.group(2))
    return m

def main():
    if K.gpu_busy():
        print("REFUSING: a GPU experiment is running"); sys.exit(4)
    os.makedirs("/srv/bench/e12/ssa", exist_ok=True)

    prov = json.load(open(f"{CORPUS}/s7-data-provenance.json"))
    data = {"experiment": "ssa-s7", "source": "e12-ssa", "run_ids": ["ssa-s7"],
            "protocol": "SSA S7 — logprob-scored multiple-choice anchors (HellaSwag, Winogrande)",
            "purpose": "face validity and comparability with published tables; NOT a quant ranker",
            "data_provenance": prov, "seed": K.SEED, "kv": "q4_0",
            "image_id": K.image_id(),
            "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "cells": []}

    # --- PILOT (small-tests-first is a hard gate) -------------------------------
    print("=== pilot: HellaSwag 25 tasks on the reference arm ===", flush=True)
    pilot = run("Q6_K_XL", "hellaswag", 25)
    data["cells"].append(pilot); data["pilot"] = pilot
    json.dump(data, open(OUT, "w"), indent=1)
    print(f"pilot rc={pilot['rc']} {pilot['seconds']}s score={pilot['score']}", flush=True)
    if not pilot["ok"] or "acc_pct" not in pilot["score"]:
        print("PILOT GATE FAILED — not spending the budget. Inspect", pilot["serverlog"])
        sys.exit(2)

    # size the real run from what the pilot actually cost (~10 min/arm budget)
    per_task = max(pilot["seconds"] / 25.0, 0.01)
    hs_tasks = int(max(200, min(2000, 600 / per_task)))
    print(f"pilot: {per_task:.2f}s/task -> HellaSwag n={hs_tasks} per arm", flush=True)
    data["sizing"] = {"pilot_seconds_per_task": round(per_task, 3), "hellaswag_tasks": hs_tasks}

    for arm in ARMS:
        for bench, n in (("hellaswag", hs_tasks), ("winogrande", 1267)):
            c = run(arm, bench, n)
            data["cells"].append(c)
            json.dump(data, open(OUT, "w"), indent=1)
            print(f"  {arm:<9} {bench:<11} n={n:<5} rc={c['rc']} {c['seconds']:>6.0f}s "
                  f"score={c['score'].get('acc_pct')}", flush=True)

    data["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    json.dump(data, open(OUT, "w"), indent=1)
    nok = sum(1 for c in data["cells"] if c["ok"] and "acc_pct" in c["score"])
    print(f"S7 done: {nok}/{len(data['cells'])} cells scored -> {OUT}")
    sys.exit(0 if nok else 2)

if __name__ == "__main__":
    main()
