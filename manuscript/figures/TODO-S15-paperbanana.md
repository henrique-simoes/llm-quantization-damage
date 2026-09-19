# TODO for keyed model: render S15 figures with PaperBanana (do NOT render here)

Owner constraint: PaperBanana is NOT installed on multivac, must not be installed here, no API keys here, cloud-dependent (see manuscript/figures/RENDERING.md §1, PROVENANCE.md §8). Pre-drawn schematics committed (paperbanana/diagram-F20/F21/F25.txt, diagrams.yaml, plots.yaml F1.., venue-multivac, 30+ data/*.csv, extract.py) do NOT cover S15. Do not run paperbanana here — render on a keyed machine.

## What the keyed model must do

1. Extend `manuscript/figures/paperbanana/plots.yaml` with F29..F32 below (venue multivac, iterations 3, format png, output manuscript/figures/rendered).
2. Extend `manuscript/figures/data/` with the four CSVs (generate via `extract.py`-style script from `data/raw/e12/s15/`, never by hand).
3. Run: `paperbanana plot-batch --manifest manuscript/figures/paperbanana/plots.yaml --venue multivac --iterations 3 --optimize --format png --output-dir manuscript/figures/rendered` (plots need only VLM provider; `GOOGLE_API_KEY` free tier sufficient. Diagrams need image provider too — not needed for S15).
4. Verify each render against its CSV + honesty constraints, commit PNGs + CSVs + specs.

## Figure specs (PaperBanana-consumable, following FIGURE-PROGRAMME.md rules)

- F29 AA-LCR resolved accuracy: grouped dot plot with Wilson 95% intervals. X: accuracy 0.5-1.0. Y: 4 arms (Q4-DFlash2, Q4-MTP, Q6-DFlash2, Q6-MTP), two points each (subset n=30, full n=100/198 where exists; MTP full missing by design). Data: data/raw/e12/s15/JUDGE-OUTPUT-resolved-majority.jsonl aggregated to arm×subset/full (subset 26/25/24/22 of 30; full 87/100, 83/100). Caption must carry judge IDs (muse-spark|xhigh, gpt-5.6-luna|medium, deepseek-ai/DeepSeek-V4.1-Flash|max), n, Wilson, and MTP-full-missing caveat. Honesty: overlapping intervals drawn overlapping; n<30 rule N/A (n=30 exactly, still show interval). Source PN-86/94/95.
- F30 GPQA accuracy: same encoding, arms Q4-DFlash2 full 175/198 + subset 45/50, Q4-MTP 47/50, Q6-DFlash2 full 178/198 + subset 47/50, Q6-MTP 48/50. Regex last-match scoring per R32, AA-primary = simple-evals (0 divergences). Caption carries n, extraction, truncation 1/494. Source PN-87.
- F31 T4 speed/energy/acceptance: three-panel (decode tok/s median, acceptance mean, energy J/req median) × bench (AA-LCR, GPQA) × drafter (MTP n=4, DFlash2 n=7) × quant. Values in PN-88 (AA-LCR dec 39.3/24.7/34.6/23.7, acc 0.504/0.710/0.465/0.653, en 36.9k/45.4k/40.9k/50.5k J; GPQA dec 48.9/27.3/42.1/28.2, acc 0.340/0.474/0.342/0.471, en 28.3k/78.4k/34.9k/66.1k J). Honesty: acceptance denominators differ by draft depth — report alongside tau/decode, never alone. Source PN-88 + results/aalcr+gpqa answers.jsonl timings/spec/energy_j_request.
- F32 T5 host RAM: dot plot peak container anon MiB by arm (MTP ~5.38-5.40 GiB both quants, DFlash2 ~1.75-1.77 GiB both quants; quant contributes ~16 MiB of 3.6 GiB). Annotate mechanism (checkpoints carry draft KV). n=1 per arm, one soak shape — label as such. Source PN-84 + results/t5-stability.jsonl.

## Data to use (already mirrored)

- data/raw/e12/s15/JUDGE-INPUT.jsonl(.sha256), JUDGE-OUTPUT-muse-spark-xhigh/gpt-5.6-luna-medium/deepseek-v4.1-flash-max/resolved-majority.jsonl, t1-pilot.json, t2-kvmap.json(l), t3-speed.json(l), t5-stability.jsonl, subsets.json, JUDGING-PENDING.md (closed).
- Full per-item timings/spec/energy stay in /srv/bench/e12/s15/results/aalcr+gpqa/*/answers.jsonl (too large to commit; cite by path per paper-notes protocol).
