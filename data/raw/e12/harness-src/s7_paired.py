#!/usr/bin/env python3
"""Recover PER-TASK correctness from HellaSwag's running accuracy table and run the PAIRED test.

llama-perplexity prints cumulative acc_norm after each task. Differencing it recovers each
task's individual outcome:  correct(n) = round(acc(n)*n - acc(n-1)*(n-1)).
Because every arm was run with the same seed (20260830), the tool selects the SAME randomized
tasks for each -- so these are PAIRED observations, and McNemar is far more powerful than the
independent intervals the tool prints. This is Miller/Anthropic's paired-difference
recommendation (METHOD-REFERENCES R6) applied to data we already have, at zero GPU cost.
"""
import re, glob, os, math, json, itertools

LOGS = "/srv/bench/server-timings"

def per_task(path):
    txt = open(path, encoding="utf-8", errors="replace").read()
    rows = re.findall(r"^\s*(\d+)\s*\t\s*([\d.]+)\s*%", txt, re.M)
    out, prev_correct = [], 0
    for n_s, acc_s in rows:
        n = int(n_s); cum = float(acc_s) / 100.0 * n
        c = int(round(cum - prev_correct))
        out.append(1 if c >= 1 else 0)
        prev_correct = cum
    return out

arms = {}
for p in sorted(glob.glob(f"{LOGS}/ssa7-*-hellaswag-n400.serverlog")):
    arm = os.path.basename(p).split("-")[1]
    v = per_task(p)
    if v: arms[arm] = v

print("per-task vectors recovered:")
for a, v in arms.items():
    print(f"  {a:<9} n={len(v)}  correct={sum(v)}  acc={100*sum(v)/len(v):.2f}%")
print()
order = ["Q6_K_XL", "Q6_K", "Q5_K_XL", "Q4_K_XL"]
order = [a for a in order if a in arms]
print("PAIRED comparisons (McNemar, same tasks, same seed):")
print(f"{'pair':<22} {'b':>4} {'c':>4} {'diff pts':>9} {'chi2':>7} {'p':>8}  verdict")
print("-" * 78)
res = {}
for a, b in itertools.combinations(order, 2):
    va, vb = arms[a], arms[b]
    n = min(len(va), len(vb))
    B = sum(1 for i in range(n) if va[i] == 1 and vb[i] == 0)   # a right, b wrong
    C = sum(1 for i in range(n) if va[i] == 0 and vb[i] == 1)   # b right, a wrong
    diff = 100.0 * (sum(va[:n]) - sum(vb[:n])) / n
    if B + C == 0:
        chi2, p, verdict = 0.0, 1.0, "IDENTICAL on every task"
    else:
        chi2 = (abs(B - C) - 1) ** 2 / (B + C)          # continuity-corrected
        p = math.erfc(math.sqrt(max(chi2, 0) / 2))
        verdict = "DISTINGUISHABLE (p<0.05)" if p < 0.05 else "not distinguishable"
    res[f"{a}_vs_{b}"] = {"b": B, "c": C, "diff_pts": round(diff, 2),
                          "chi2": round(chi2, 3), "p": round(p, 4), "verdict": verdict}
    print(f"{a+' vs '+b:<22} {B:>4} {C:>4} {diff:>+9.2f} {chi2:>7.3f} {p:>8.4f}  {verdict}")
json.dump({"arms": {a: {"n": len(v), "correct": sum(v)} for a, v in arms.items()},
           "paired": res}, open("/srv/bench/e12/ssa/ssa-s7-paired.json", "w"), indent=1)
print("\n-> /srv/bench/e12/ssa/ssa-s7-paired.json")
