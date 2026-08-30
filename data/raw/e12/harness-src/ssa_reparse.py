#!/usr/bin/env python3
"""ssa_reparse.py — recover SSA metrics from the serverlogs.

ssa_kld.py's regexes expected ASCII "+/-"; llama.cpp emits Unicode "±" and "Δ", so every
KLD cell ran fine and returned rc=0 while its metrics parsed empty. The numbers were never
lost — they are in /srv/bench/server-timings/ssa-*.serverlog, which is precisely why hard
rule 2 (logs before teardown) exists. This re-parses them. No GPU time is spent.

It also fixes the harness's real defect: a `kld` cell with no mean_kld is NOT ok.
"""
import json, re, os, glob, sys

LOGS = "/srv/bench/server-timings"
RESULTS = "/srv/bench/e12/ssa/ssa-results.json"
OUT = "/srv/bench/e12/ssa/ssa-results-parsed.json"

NUM = r"([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)"
PAT = {
    "mean_kld":       rf"Mean\s+KLD:\s*{NUM}\s*±\s*{NUM}",
    "max_kld":        rf"Maximum\s+KLD:\s*{NUM}",
    "median_kld":     rf"Median\s+KLD:\s*{NUM}",
    "kld_99p":        rf"99\.0%\s+KLD:\s*{NUM}",
    "kld_95p":        rf"95\.0%\s+KLD:\s*{NUM}",
    "kld_90p":        rf"90\.0%\s+KLD:\s*{NUM}",
    "mean_dp_pct":    rf"Mean\s+Δp:\s*{NUM}\s*±\s*{NUM}\s*%",
    "rms_dp_pct":     rf"RMS\s+Δp\s*:\s*{NUM}\s*±\s*{NUM}\s*%",
    "top1_agree_pct": rf"Same\s+top\s+p:\s*{NUM}\s*±\s*{NUM}\s*%",
    "ppl":            rf"(?:Final estimate:\s*)?PPL\s*=\s*{NUM}\s*(?:±|\+/-)\s*{NUM}",
    "ppl_ratio":      rf"PPL\s+ratio:\s*{NUM}\s*(?:±|\+/-)\s*{NUM}",
}

def parse(path):
    txt = open(path, encoding="utf-8", errors="replace").read()
    m = {}
    for k, p in PAT.items():
        h = re.search(p, txt)
        if h:
            g = h.groups()
            m[k] = float(g[0])
            if len(g) > 1 and g[1] is not None:
                m[k + "_err"] = float(g[1])
    return m

base = json.load(open(RESULTS)) if os.path.exists(RESULTS) else {"cells": []}
recovered, broken = 0, []
for c in base.get("cells", []):
    lp = c.get("serverlog")
    if not lp or not os.path.exists(lp):
        broken.append((c.get("label"), "serverlog missing")); continue
    m = parse(lp)
    c["metrics_reparsed"] = m
    # the defect this fixes: a kld cell with no mean_kld is NOT a success
    if c.get("mode") == "kld" and "mean_kld" not in m:
        c["ok"] = False; c["failure_mode"] = "kld-metrics-absent"
        broken.append((c.get("label"), "no mean_kld in log"))
    else:
        recovered += 1
base["reparsed_note"] = ("metrics recovered from serverlogs 2026-08-30; ssa_kld.py's ASCII '+/-' "
                         "patterns did not match llama.cpp's Unicode '±'/'Δ' output. No re-run needed.")
json.dump(base, open(OUT, "w"), indent=1)

cells = base.get("cells", [])
print(f"reference arm: {base.get('reference_arm')} | {base.get('tokens_per_cell')} tokens/cell "
      f"(n_ctx {base.get('n_ctx')} x {base.get('chunks')} chunks)")
print(f"recovered {recovered}/{len(cells)} cells -> {OUT}")
if broken:
    print("PROBLEM CELLS:"); [print("   ", b) for b in broken]
print()
h = f"{'arm':<9} {'domain':<10} {'kv':<5} {'mode':<5} {'meanKLD':>10} {'±':>9} {'top1 %':>15} {'RMS Δp %':>16} {'PPL':>9} {'PPLratio':>9}"
print(h); print("-" * len(h))
for c in cells:
    m = c.get("metrics_reparsed", {})
    def g(k, f="{:.6f}"):
        v = m.get(k); return f.format(v) if isinstance(v, (int, float)) else "—"
    t1 = (f"{m['top1_agree_pct']:.3f}±{m.get('top1_agree_pct_err',0):.3f}"
          if "top1_agree_pct" in m else "—")
    rd = (f"{m['rms_dp_pct']:.3f}±{m.get('rms_dp_pct_err',0):.3f}"
          if "rms_dp_pct" in m else "—")
    print(f"{c['arm']:<9} {c['domain']:<10} {c['kv']:<5} {c['mode']:<5} "
          f"{g('mean_kld'):>10} {g('mean_kld_err'):>9} {t1:>15} {rd:>16} "
          f"{g('ppl','{:.4f}'):>9} {g('ppl_ratio','{:.5f}'):>9}")
