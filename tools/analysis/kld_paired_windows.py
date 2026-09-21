#!/usr/bin/env python3
"""Paired window-level inference on KL-divergence differences between builds.

llama-perplexity prints the CUMULATIVE mean KLD after each chunk (5 decimals). Per-window means are
recovered by differencing: c_k = k*m_k - (k-1)*m_(k-1). Builds were scored on identical windows
against identical reference logits, so differences are paired by window. Percentile bootstrap over
windows, B=20,000, seed 20260921. Windows are contiguous 2,048-token chunks of one corpus per domain,
so this addresses within-window token dependence and between-build covariance, not corpus sampling.
Usage: kld_paired_windows.py <dir-with-ssa-*-kld.serverlog> > out.json
"""
import json, random, re, statistics as st, sys
ROW = re.compile(r'\s*(\d+)\s+[\d.]+ ±\s+[\d.]+\s+-?[\d.]+ ±\s+[\d.]+\s+([\d.]+) ±')
def windows(path):
    cum = {}
    for line in open(path, errors='ignore'):
        r = ROW.match(line)
        if r: cum[int(r.group(1))] = float(r.group(2))
    m = [cum[k] for k in sorted(cum)]
    return [m[0]] + [(i + 1) * m[i] - i * m[i - 1] for i in range(1, len(m))]
def main(d):
    random.seed(20260921); out = {}
    arms = ['Q6_K', 'Q5_K_XL', 'Q4_K_XL']
    for dom in ['code', 'wikitext2', 'humaneval']:
        w = {a: windows(f'{d}/ssa-{a}-{dom}-kld.serverlog') for a in arms}
        n = len(w[arms[0]]); out[dom] = {'n_windows': n, 'per_window': w, 'pairs': {}}
        for a, b in [(arms[0], arms[1]), (arms[1], arms[2]), (arms[0], arms[2])]:
            diff = [y - x for x, y in zip(w[a], w[b])]
            bs = sorted(st.mean(random.choices(diff, k=n)) for _ in range(20000))
            out[dom]['pairs'][f'{b}-{a}'] = {'mean_diff': st.mean(diff), 'ci95': [bs[500], bs[19499]],
                'windows_positive': sum(x > 0 for x in diff), 't': st.mean(diff) / (st.stdev(diff) / n ** .5)}
    json.dump(out, sys.stdout, indent=1)
if __name__ == '__main__': main(sys.argv[1])
