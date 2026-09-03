#!/usr/bin/env python3
"""mk100_analyse.py — the paired analysis for MK-NIAH at n=100.

Written BEFORE the second arm landed, so the test is fixed in advance rather than chosen after
seeing the numbers. Reports, in this order:
  1. per-arm score with Wilson 95% (the marginal view)
  2. the PAIRED contingency table — both correct / only-reference / only-arm / neither
  3. exact McNemar on the discordant pairs, AND the minimum p that count could have produced
     (PN-40: reporting a null without stating the test's floor is the error this project
     committed once already)
  4. accuracy recovery, computed against the MEASURED reference (89.0), not the n=12 pilot's 100.0
"""
import json, math, sys

OUT = "/srv/bench/e12/ruler/s12-ruler.json"
REF, ARM = "Q6_K_XL", "Q4_K_XL"

def wilson(k, n, z=1.96):
    if not n: return (None, None)
    p = k/n; d = 1 + z*z/n; c = (p + z*z/(2*n))/d
    h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
    return round(100*(c-h), 1), round(100*(c+h), 1)

def exact_p(b, c):
    n = b + c
    if n == 0: return 1.0
    k = min(b, c)
    return min(1.0, 2*sum(math.comb(n, i) for i in range(k+1))/2**n)

def correct(pred, refs):
    return any(r.lower() in pred.lower() for r in refs)

d = json.load(open(OUT))
cells = {c["arm"]: c for c in d["cells"] if c.get("task") == "mk100" and c.get("ok")}
if len(cells) < 2:
    print(f"  only {len(cells)} mk100 cell(s) present — second arm not finished"); sys.exit(1)

P = {}
for a in (REF, ARM):
    s = json.load(open(f"/srv/bench/e12/ruler/s12-preds-{a}-mk100-c131072.json"))
    P[a] = [correct(p, r) for p, r in zip(s["preds"], s["refs"])]

n = len(P[REF])
kr, ka = sum(P[REF]), sum(P[ARM])
both     = sum(1 for i in range(n) if P[REF][i] and P[ARM][i])
ref_only = sum(1 for i in range(n) if P[REF][i] and not P[ARM][i])
arm_only = sum(1 for i in range(n) if not P[REF][i] and P[ARM][i])
neither  = sum(1 for i in range(n) if not P[REF][i] and not P[ARM][i])
disc = ref_only + arm_only
p    = exact_p(ref_only, arm_only)
floor = exact_p(0, disc)

print(f"=== MK-NIAH @131,072, n={n}, RULER string_match_all ===")
print(f"  {REF:9s} {kr}/{n} = {100*kr/n:5.1f}%   Wilson95 {wilson(kr,n)}")
print(f"  {ARM:9s} {ka}/{n} = {100*ka/n:5.1f}%   Wilson95 {wilson(ka,n)}")
print(f"\n  accuracy recovery = {100*ka/kr:.2f}%   (vs the MEASURED reference, not the n=12 pilot)")
print(f"\n=== paired table ===")
print(f"  both correct {both} | {REF} only {ref_only} | {ARM} only {arm_only} | neither {neither}")
print(f"\n=== exact McNemar ===")
print(f"  discordant {disc}   p = {p:.4f}   {'SEPARATED at 0.05' if p < 0.05 else 'not separated at 0.05'}")
print(f"  minimum p obtainable with {disc} discordant pairs = {floor:.4f}"
      f"  -> the test {'COULD' if floor < 0.05 else 'could NOT'} have reached 0.05")
dp = (ka - kr)/n
se = math.sqrt((disc - (ref_only-arm_only)**2/n)/n**2) if n else 0
print(f"\n  paired difference {100*dp:+.2f} pts, 95% CI "
      f"[{100*(dp-1.96*se):+.2f}, {100*(dp+1.96*se):+.2f}]")
