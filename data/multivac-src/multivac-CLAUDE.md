# Multivac — Qwen3-27B Quantization Benchmark Study

## What this project is

A technical report benchmarking **Qwen3.8-27B** across quantization levels and inference backends on **2× NVIDIA RTX 5060 Ti 16GB** (Blackwell, sm120). The study compares **llama.cpp GGUF quantizations** (IQ4_XS, Q4_K_XL, Q5_K_XL, Q6_K_XL, Q3_K_XL) against **vLLM NVFP4** (W4A4, FP8 KV cache), with speculative decoding methods (MTP and DFlash2).

The host machine is called **multivac** — a headless Ubuntu server accessed via SSH from a Mac Studio. This Claude Code session runs ON multivac itself.

## PROJECT OBJECTIVES — two separate deliverables (do NOT conflate)

**Track A — "best config for THIS machine" (the operational answer for the user).**
⚠️ **SCOPE NARROWED 2026-08-29: Track A is llama.cpp-only.** vLLM NVFP4 is eliminated on measured
data — context ceiling 51,200 (measured) / 98,304 (historical) vs the native 262,144, and
HumanEval+ 85.4/84.1 vs Q6_K_XL 93.9/91.5. It is **not** eliminated for poor GPU splitting: its
TP=2 tensor parallelism splits more evenly than llama.cpp's layer split. vLLM remains in scope
for Track B. See E11 EXECUTION LOG.
One pinned, reproducible configuration that maximises, in **strict priority order**:
**(1) accuracy → (2) usable context length → (3) tok/s.**
A faster config that is measurably less accurate loses. A more accurate config that reaches less
context still beats a less accurate one at any context. tok/s only breaks ties between configs
that are indistinguishable on (1) and (2) within CIs. Deliverable: **one config line** + the
measurements that justify it + a fallback ladder. Opinionated, machine-specific to
2× RTX 5060 Ti 16GB. **This is not the paper.**

**Track B — the technical report / article (neutral, for AI engineers and researchers).**
An even-handed investigation of how **backend** (llama.cpp vs vLLM), **quantization** (GGUF
ladder vs NVFP4), **KV-cache dtype**, **split mode**, and **speculative-decoding method** move
every tracked metric: PPL, KL, HumanEval+, SWE-bench, agentic step counts, tok/s, J/tok, VRAM,
context ceiling. No "best setup" framing — report trade-off curves and the strongest
configuration **per objective** (accuracy-max / speed-max / energy-max / context-max), each with
protocol, n, and CIs, plus explicit reproducibility caveats. Track A's experiments feed Track B
as data; **Track B must never inherit Track A's priority ordering.**

Every experiment in the TEST PLAN declares the track(s) it serves. Collection is shared,
conclusions are not.

## Hardware

- **GPUs**: 2× RTX 5060 Ti 16GB (Blackwell, sm120), power limit 180W each
- **CPU**: AMD Ryzen 5 8500G (12 threads)
- **RAM**: 14 GiB (constrains vLLM checkpoint prefetch)
- **Driver**: NVIDIA 595.84, CUDA 13.2
- **Disk**: 218GB total, **43GB free as of 2026-08-29** (the 49 `sweb.eval` images were pruned; 0 remain)
- **No BMC/IPMI** → wall power not measurable; GPU energy integrated from 1Hz samples, CPU via RAPL

## Key directories

| Path | Contents |
|---|---|
| `/srv/bench/` | Main benchmark workspace |
| `/srv/bench/orchestrator/` | Durable worker + watchdog (worker.sh, lib.sh, watchdog.sh, state/) |
| `/srv/bench/evalplus_results/` | HumanEval+ results (humaneval/, humaneval-thinking-v2/) |
| `/srv/bench/swebench-results/` | SWE-bench runs (thinking/, verified50/, agentic-steps/) |
| `/srv/bench/perplexity/` | Perplexity results (llama.cpp GGUF + NVFP4 vLLM) |
| `/srv/bench/champion-20260821/` | 30 recovered agentic runs with full timings (184K files, 2.2GB) |
| `/srv/bench/rigor/` | Additional experiments: evalplus, context controls, T3 agentic data |
| `/srv/bench/server-timings/` | llama.cpp server logs per config |
| `/srv/bench/telemetry/` | Prometheus, Grafana, node_exporter, nvidia_gpu_exporter, cAdvisor, Netdata |
| `/srv/bench/power-log.csv` | 1Hz GPU+CPU power logger |
| `/srv/bench/ledger-data.json` | Machine-readable snapshot of ALL metrics |
| `/srv/bench/bootstrap-ci.json` | Bootstrap 95% CIs (B=10,000, seed 20260825) |
| `/srv/bench/champion-timings.json` | 30 structured agentic run timings |
| `/srv/models/` | GGUF model files (IQ4_XS, Q4_K_XL, Q5_K_XL, Q6_K_XL + DFlash2 drafter) |
| `~/Documents/multivac-paper/data/` | Paper data mirror (PAPER-REFERENCES.md, orchestrator scripts) |
| `~/Documents/multivac-paper/data/PAPER-REFERENCES.md` | **THE canonical reference** — 830+ lines of findings, decisions, data tables |

## Docker images (DO NOT prune blindly)

| Image | Role |
|---|---|
| `llamacpp-mtp:latest` | All llama.cpp MTP + no-spec runs |
| `llama-dflash2:latest` | All DFlash2 results (z-lab fork, v0.1.2-dev, build 50, commit f7aadef) |
| `vllm/vllm-openai:nightly` | All vLLM spec-decode speed runs (MTP ns2/ns4) |
| `swebench/sweb.eval.*` | SWE-bench evaluation images — **all pruned as of 2026-08-29, 0 on disk** |
| ~~`llamacpp-dflash2-pr27342:1deefcc-sm120-cuda128-abi`~~ | **GONE.** Produced EVERY tensor-split and EVERY 262,144-token result in this file. Its loss is why E6/E1b exist. |

Surviving llama.cpp images and their versions (checked 2026-08-29): `llamacpp-mtp:latest` = 0.3.0-dev (build 1, commit d222767); `llama-dflash2:latest` = 0.1.2-dev (build 50, commit f7aadef). Both expose `-sm {none,layer,row,tensor}`, `-ctk/-ctv`, `--spec-type draft-mtp`, `-ctxcp`, `-fit`.

## Engine versions

| Engine | Version | Used for |
|---|---|---|
| vLLM stable | 0.27.1 | NVFP4 HumanEval+ (85.4/84.1), SWE-bench |
| vLLM nightly | 0.26.1rc1.dev1219+g46638857f | All spec-decode speed runs |
| llama.cpp MTP | llamacpp-mtp:latest | All llama.cpp MTP + no-spec results |
| llama.cpp DFlash2 | v0.1.2-dev build 50, commit f7aadef (z-lab fork) | All DFlash2 results |
| evalplus | patched venv /srv/bench/.venv-evalplus | HumanEval+ |
| mini-swe-agent | 2.4.6, venv /srv/bench/.venv-swebench | SWE-bench |

## Orchestrator (durable worker)

Lives at `/srv/bench/orchestrator/`. Survives client disconnects, session cycles, crashes.

- **Status**: `tail /srv/bench/orchestrator/worker.log`
- **State files**: `ls /srv/bench/orchestrator/state/`
- **Stop**: `pkill -f orchestrator/watchdog.sh && pkill -f orchestrator/worker.sh`
- **Re-run a job**: `rm /srv/bench/orchestrator/state/<job>.done`
- **Rules**: lib.sh ALWAYS captures `docker logs` before container teardown; gpu_busy() prevents contention; every job is idempotent.

### Job queue (ALL COMPLETE as of 2026-08-28 18:00 UTC)

1. ✅ `score-thinking` — scored 6 SWE-bench thinking runs
2. ✅ `bootstrap-ci` — B=10,000 CIs for all results
3. ✅ `agentic-steps` — T3-style step counts for IQ4_XS (mean 23) and Q5_K_XL (mean 29)
4. ✅ `score-verified50` — 50-instance SWE-bench: 49 completed, 37 resolved (75.5%)
5. ✅ `nvfp4-ppl` — vLLM NVFP4 perplexity: PPL=8.5848 (Protocol: 160 chunks @512 tokens)
6. ✅ `nvfp4-ppl-p1` — Protocol-1-matched NVFP4 re-score: PPL=6.7073 (done 2026-08-28 22:18)

## Current results summary

### Perplexity (WikiText-2)
**Protocol 1** — `llama-perplexity`, **602 chunks, n_ctx=512, batch 512**, full WikiText-2 test set (verified in `/srv/bench/perplexity-results/ppl-*.log`). llama.cpp scores only the **second half** of each 512-token window, using the first half as context.
  IQ4_XS 6.6839 ±0.04133 | Q4_K_XL 6.6617 ±0.04116 | Q5_K_XL 6.6556 ±0.04114 | Q6_K_XL 6.6511 ±0.04111  *(`err` = llama.cpp's reported ± standard error)*
**Protocol 2** — 20 chunks @ c4096, tensor split, f16 KV (champion-20260821 ablation): Q3 5.55 | IQ4 5.53 | Q4_K_M 5.50 | Q5 5.51 | Q6 5.51
**NVFP4** — vLLM echo+logprobs, **160 chunks, seq_len=512, stride=512, 77,621 tokens**, avg NLL 2.149994 → PPL **8.5848**. Scores **all** tokens from position 0 with **no prior context**.
**NVFP4 (Protocol 1-matched)** — vLLM, **602 × 512-token windows** (Protocol 1's exact windows from `/srv/bench/corpus/wikitext2-test.txt`, GGUF-tokenized via llama-server /tokenize), scoring **positions 256..** of each window (half-window rule): avg NLL 1.903193 → PPL **6.7073** (154,714 scored tokens; +1-token/window retok drift). Alt cross-check (all positions ≥1): 8.0775. Result: `/srv/bench/perplexity/nvfp4-vllm-ppl-protocol1.json`; sidecar with all per-token logprobs: `nvfp4-p1-token-logprobs.json`. See OPTIMIZATION-LOG §13.72.
**Reconciled comparison (Protocol 1 windows, half-window scoring — the like-for-like table):** Q6_K_XL 6.6511 | Q5_K_XL 6.6556 | Q4_K_XL 6.6617 | IQ4_XS 6.6839 | **NVFP4 6.7073** → NVFP4's true degradation vs the GGUF ladder is **+0.8–0.85 %**, not the +29 % the naive 8.58-vs-6.65 comparison suggested.
⚠️ The three protocols produce different absolute values and MUST NEVER be mixed in one table.
⚠️ Protocol 1 and the legacy NVFP4 run differ in: **(a) corpus files** — Protocol 1 used `/srv/bench/corpus/wikitext2-test.txt` (308,707 tokens), the legacy NVFP4 run used `/srv/bench/perplexity/wikitext-2-test.txt` (297,053 tokens), different parquet conversions (discovered 2026-08-28, §13.72); **(b) corpus coverage** (602 vs 160 windows); **(c) scoring window** (half-window with context vs all positions with none). The previously suspected tokenizer axis is WRONG — GGUF and HF tokenizations agree exactly on both files. Do not describe Protocol 1 as "long context" or "full corpus, large window".
⚠️ `nvfp4-vllm-ppl.json` self-labels `"protocol": 2` — that field is **wrong/unrelated** to Protocol 2 above.

### HumanEval+ (non-thinking, greedy)
Q3_K_XL 84.1/81.7 | IQ4_XS 90.2/87.8 | Q5_K_XL 93.3/90.9 | Q6_K_XL 93.9/91.5 — monotonic ✓

### HumanEval+ (thinking, max_tokens 4096)
| Config | HE | HE+ | Empty% |
|---|---|---|---|
| mtp-IQ4_XS | 86.6 | 86.0 | 12.8 |
| mtp-Q4_K_XL | 87.8 | 86.0 | 12.2 |
| mtp-Q5_K_XL | 89.0 | 86.0 | 11.0 |
| **mtp-Q6_K_XL** | **90.9** | **88.4** | **7.9** |
| dflash-IQ4_XS | 89.0 | 87.8 | 10.4 |
| dflash-Q4_K_XL | 90.2 | 87.2 | 8.5 |
| NVFP4 (vLLM) | 85.4 | 84.1 | 12.8 |

### SWE-bench
- **Thinking (3-instance calibration)** — resolved/**completed**, NOT resolved/submitted:

| Config | submitted | completed | resolved | empty patches |
|---|---|---|---|---|
| mtp-Q6_K_XL | 3 | 3 | **3** | 0 |
| mtp-Q4_K_XL | 3 | 3 | 2 | 0 |
| mtp-Q5_K_XL | 3 | 3 | 2 | 0 |
| dflash-IQ4_XS | 3 | 3 | 2 | 0 |
| dflash-Q4_K_XL | 3 | 3 | 2 | 0 |
| vllm-NVFP4 | 3 | 3 | 2 | 0 |
| ⚠️ **mtp-IQ4_XS** | 3 | **1** | 1 | **2** |

⚠️ `mtp-IQ4_XS` is **n=1, not n=3** — 2 of its 3 instances produced empty patches. Never report it as "2/3" or compare it to the other rows.

- **Verified50 (Q6_K, non-thinking)**: **37/49 = 75.5%** (74.0% of 50). Verified 2026-08-28 against 49 unique per-instance `report.json` files; manifest at `/srv/bench/swebench-results/verified50/per-instance-manifest.json`. `astropy__astropy-13236` had an empty patch and was never submitted.
- **IQ4_XS verified50**: 36/47 in the (stale) ledger was the pre-ARM64-fix figure; 37/49 was the §13.66 correction. **Final x86_64-corrected total (§13.71): 38/49 = 77.6%**. ⚠️ Host-architecture caveat: django-10097 resolves only on x86_64 — ARM64 (Mac) scoring under-counted this quant by exactly this instance.
- **Q5_K_XL verified50**: 35/48 in the (stale) ledger was pre-ARM64-fix; 37/50 was the §13.66 correction. **Final x86_64-corrected total (§13.71): 38/50 = 76.0%**. Same host-architecture caveat — see §13.71.
- Aggregation ground truth: `swebench_agg.py` per-instance report.json, x86fix runs superseding ARM64 ones; ledger refreshed 2026-08-28 with `source`/`run_ids` provenance.
- **vLLM NVFP4 (thinking, no-spec @98K)**: 2/3

⚠️ `ledger-data.json` SWE-bench rows are unreliable — see "Known instrumentation defects" below.

### Speed (llama.cpp, ctx=32768, 1024 gen, 3-run median)
⚠️ **These are decode into a nearly EMPTY KV cache.** At a genuinely full window the same class of
config is 3–5× slower (Q6_K+MTP: 37.22 tok/s at depth 0 → **7.19 tok/s at depth 186,265**). Never
quote this table as long-context speed — see E11 EXECUTION LOG.
| Config | tok/s | J/tok |
|---|---|---|
| IQ4_XS DFlash2 n=4 | **57.5** | 3.70 |
| Q6_K_XL DFlash2 n=4 | 44.7 | 4.79 |
| IQ4_XS MTP n=2 | 46.9 | 4.35 |
| Q6_K_XL MTP n=2 | 31.7 | 6.29 |
| IQ4_XS no-spec | 27.2 | 7.46 |
| Q6_K_XL no-spec | 16.5 | 11.78 |

### vLLM NVFP4 Speed (TP=2, fp8 KV, enforce-eager)
| Config | tok/s | speedup |
|---|---|---|
| No-spec | 12.44 | 1.00× |
| MTP ns=2 | 28.11 | 2.26× |
| MTP ns=4 | 41.21 | 3.31× |
| DFlash2 | INFEASIBLE (OOM on 2×16GB) |

### Agentic step counts (T3-style, 3 instances)
| Quant | Mean steps | Converges? |
|---|---|---|
| Q3_K_XL | 250 | ❌ ALL hit limit |
| IQ4_XS | 23 | ✅ fastest |
| Q5_K_XL | 29 | ✅ |
| Q6_K_XL | ~45 | ✅ |

### Energy (key numbers; full artifact `/srv/bench/energy-per-benchmark.json`, §13.73)
Power logger covers 2026-08-27T16:21Z onward only — earlier runs uncoverable (listed in artifact).
| Config | tok/s | J/tok |
|---|---|---|
| IQ4_XS DFlash2 n=4 | 57.5 | **3.70** (best) |
| Q6_K_XL DFlash2 n=4 | 44.7 | 4.79 |
| Q6_K_XL MTP n=2 | 31.7 | 6.29 |
| Q6_K_XL no-spec | 16.5 | 11.78 |
Spec decoding cuts J/tok ~2–2.5× at every quant. Benchmark energies (GPU Wh): HumanEval thinking 288–564; agentic T3 window 208; PPL runs 14–33; nvfp4-ppl failed-retry tax 377 GPU / 1.18 kWh system.

### KL divergence (cited, Unsloth; artifact `/srv/bench/kl-divergence.json`, §13.74)
NVFP4: KLD mean zh 0.01628 / code 0.02600 / refgen 0.03993 / chat 0.05818; top-1 recovery 92–97 %. GGUF Dynamic v3 (figure-read, approximate): IQ4_XS ≈ 0.019, Q4_K_XL ≈ 0.0085, Q5_K_XL ≈ 0.0038, Q6_K_XL ≈ 0.0016. Published KL ranking agrees with our measured PPL ranking.

## Headline findings

1. **Q3 is agentic-useless**: fastest raw tok/s (116.9 with MTP n=8) but loops to step limit in every agentic task. Single-shot benchmarks do NOT predict agentic competence.
2. **Speculation ranking flips with context**: DFlash2 wins at short context (57.5 vs 46.9 MTP); MTP wins at long context (32.6 vs 22.9 DFlash2 at 168K).
3. **DFlash2 vLLM OOM on 2×16GB**: BF16 draft (3.6GB) + NVFP4 weights don't fit; llama.cpp's Q4 GGUF drafter (1.1GB) does. Reportable finding about deployment constraints.
4. **KV quantization unlocks 256K context — but it is QUANT-DEPENDENT**: q4_0 KV → 262,144 measured on Q5_K_XL; f16 caps at 147,456 on the same quant. **Q6_K_XL is predicted to top out near ~210K, not 262K** (see VRAM MODEL — the old ÷2 arithmetic was wrong). q8_0 is not merely OOM, it is **broken on this stack** (illegal memory access even at c4096).
5. **MTP depth optimum is context- and quant-dependent**: Q3 peaks at n=8 (116.9 tok/s); Q6 peaks at n=2 (40.9 tok/s, n=8 gives only 37.5).
6. **Only `-sm layer` works on 5060 Ti**: `-sm tensor` crashes (CUDA illegal memory access in upstream builds; worked in the z-lab fork image — **which is no longer on disk**, so tensor split is currently unreproved on any surviving image, see G7/E6); `-sm row` unsupported (no split buffers).
7. **Model recommendation**: Q6_K_XL for best accuracy (91.5 HE+, 88.4 thinking, 3/3 SWE); IQ4_XS for speed+efficiency (57.5 tok/s DFlash2, 4.35 J/tok MTP, mean 23 agentic steps).
8. **Spec-method ranking is CONTEXT-DEPENDENT** (2026-08-29 long-context analysis): DFlash2 wins ≤32K (57.5 vs 46.9 tok/s) but its acceptance collapses at depth (0.41–0.55 @184K); MTP n=2 wins ≥100K and was the top-5 at every long-context measurement. Spec decode is greedy-lossless → method affects speed only; accuracy is a quant property.
9. **262,144-token context (the model's native limit) is reachable on 2×16GB — for SOME quants**: measured with q4_0 KV + MTP n=2 on Q5_K_XL (39.33 tok/s, 14,234 MiB/GPU) and on the now-deleted old UD-Q6_K (40.90 tok/s). ⚠️ Not established for Q6_K_XL (predicted OOM, E1 pending), and **not** established with MTP on IQ4_XS (`iq4tensor-20260820-1403`: 262,144 + MTP fails to allocate; no-spec OK). `props-iq4_xs.json` records `n_ctx` and `speculative.types=none` but **never the KV dtype** — it cannot support an "f16 @262,144" claim. vLLM NVFP4 caps at 98,304 (48K with MTP) — a cross-backend finding.
10. **The two GPUs are NOT a pool, and the default layer split wastes both capacity and speed**
    (E11c, 2026-08-29): with `-sm layer` each layer's weights AND its KV slice live on one card
    (no NVLink on 5060 Ti), so the limit is **per-card 16,311 MiB**, not the 32,622 MiB aggregate.
    The default placement stranded 1,955–3,829 MiB on GPU0 while GPU1 OOMed within 473–1,119 MiB
    of its wall. `-ts 58,42` took `Q6_K + MTP n2 + q4_0` from **196,608 @ 7.19 tok/s** to
    **262,144 @ 13.85 tok/s** — **+33 % context and +93 % speed from one flag.** Ratio choice is
    not monotone-safe (54,46 failed where 58,42 loaded) and must be re-swept per config.
11. **Decode at a FULL window is 3–5× slower than the published speed tables**, which measure
    decode into a nearly empty KV cache (Q6_K+MTP: 37.22 tok/s at depth 0 → 7.19 at depth 186,265,
    before rebalancing). Never quote `ctx=32768` throughput as long-context throughput.
12. **Long-context accuracy-vs-context is UNMEASURED for every quant** — the report's biggest open hole (see OPEN GAPS G1).

## Data exclusion list (MUST NOT enter the paper)

1. `Q6_K_openai_temp_0.0` — 51% empty, dirty run
2. `NVFP4_openai_temp_0.0.jsonl` — 1 solution, aborted
3. ALL `humaneval-thinking/` (v1) — max_new_tokens=768, superseded by v2
4. `vllm-NVFP4-mtp/` — context-limited partial (MTP ceiling)
5. `verified50` and `q3-verified50` with no eval.log — incomplete (verified50 NOW scored)
6. `power-dflash2-bench.csv` — header mislabeled
7. Old non-thinking SWE runs with different instance sets

## Known instrumentation defects (audited 2026-08-28)

These are **reporting bugs, not data loss**. The raw evidence is intact; the derived summaries are wrong.

1. **`collect-metrics.py` first-match regex** — it uses `re.search(r"Instances {k}: (\d+)", log)`, which returns only the **first** match. `verified50/eval.log` concatenates 7 batch reports, so `ledger-data.json` publishes batch 1's `8/5/3` instead of the true `49/37/12`. Any concatenated eval.log is under-reported by this parser. Fix = sum matches, or read per-instance `report.json`.
2. **swebench artifacts land in the worker's cwd, not `/srv/bench`** — the worker runs from `/home/multivac`, so per-instance evidence is at `/home/multivac/logs/run_evaluation/<run-id>/` and reports at `/home/multivac/*.json`. Searching only `/srv/bench` makes the run look unaudited. **Look in `/home/multivac` too.**
3. **`openai__Q6_K.verified50-score.json` holds only the LAST batch** (1 instance) — every batch overwrites it. It is not the run summary. Use `per-instance-manifest.json` instead.
4. **Ledger SWE-bench rows for `iq4_xs-verified50` / `q5_k_xl-verified50` were pre-ARM64-fix** — they read the stale Mac-side eval.log and missed the §13.66 correction for django-11433 / django-11451. **Fixed 2026-08-28** — ledger now aggregates per-instance report.json via `swebench_agg.py` (38/49 and 38/50, with `run_ids` provenance).
5. **`~/Documents/multivac-paper/data/orchestrator/worker.sh` is a stale mirror** of the live `/srv/bench/orchestrator/worker.sh` — they differ in `job_score_verified50`. The live one is authoritative.
6. **`nvfp4-ppl` failed 24 times before succeeding** (22× exit 1, 1× exit 15, 1× exit 143) between 06:19 and 17:43 UTC on 2026-08-28; the 18:00 run succeeded. The `.done` marker records success only — the retry history lives in `worker.log`.
7. **`ledger-data.json` is rewritten every 5 min** by `snapshot_metrics` even with no new jobs, so its content hash is time-bound and not an immutable artifact.
8. **Server-timing sample counts are unbalanced** (`IQ4_XS__dflash2_n4` n=16 vs `Q6_K_XL__nospec` n=58; `agentic-IQ4_XS` n=293 vs `agentic-Q5_K_XL` n=680 vs `mtp-Q6_K_XL` n=2937). These are opportunistic server-log scrapes, **not balanced trials** — use the `speed/*` 3-run medians for cross-quant comparison, never `server_timings`.
9. **Non-thinking HumanEval+ ledger keys are ambiguous** — `Q6Kfix` (93.9/91.5) is the good Q6 run; `Q6_K` (43.3, 84 empties) is the dirty run already on the exclusion list; `lcpp-q6k`, `deep-32768`, `deep-131072` are all 93.3/90.2 and need provenance before use.
10. **`batch-score-verified50.sh` never pruned anything** — SWE-bench mangles `__` to `_1776_` in image names (`astropy__astropy-12907` → `sweb.eval.x86_64.astropy_1776_astropy-12907`), so its `grep "$iid"` matched nothing. The 2026-08-28 run left all 49 eval images on disk (~74 GB reclaimable). **Fixed 2026-08-28.**

### Fixed on 2026-08-28
- `swebench_agg.py` (new) — deduplicated per-instance aggregation, shared by `collect-metrics.py` and `bootstrap-ci.py`. Both previously used the first-match regex; both now key on `instance_id` and declare composite runs explicitly. Falls back to *summing* all eval.log batches when no per-instance data exists, and emits `source` / `run_ids` provenance plus an `eval_log_disagrees` flag when the log and the reports diverge.
- `batch-score-verified50.sh` prune loop — now mangles `__`→`_1776_` and matches.

## LONG-CONTEXT CONFIGURATION ANALYSIS (2026-08-29)

Purpose: choose the best config for **long-context accuracy-first coding** (huge codebases in one window), and expose what remains unproven. Evidence trail: `champion-20260821/raw/*.json` (llama.cpp timings embedded per run), PAPER-REFERENCES "THE CONTEXT AXIS" section, `/srv/bench/kvquant-ctx-20260821-2106.txt`, `/srv/bench/n8-ctx-ceiling-20260822-0938.txt`, `/srv/bench/props-iq4_xs.json`, `/srv/bench/kl-divergence.json`.

### Structural facts (measured)
1. **Speculative decoding is greedy-lossless**: accepted draft tokens are exactly the target's greedy output → spec method (MTP/DFlash2/none) does NOT change accuracy, only speed. **Accuracy is a quant property.**
2. **Acceptance (draft_n_accepted/draft_n) is a SPEED metric, not accuracy.** Q3-embedded hit 1.000 acceptance at 250K while being the worst agentic quant — never conflate the two.
3. **Spec ranking is context-dependent**: DFlash2 wins ≤32K (57.5 tok/s); MTP n2 wins ≥100K; DFlash2 acceptance collapses at depth (0.41–0.55 @184K) while MTP holds (0.75–1.00).
4. **Context-vs-speed degradation is graceful**: decode −38% and prefill −38% from 40K→250K (Q3-embedded: 71.6→44.6 tok/s; 860→538 tok/s). No cliff.
5. **MTP trade at 40K**: 1.96× decode speedup (23.2→45.6 tok/s) but prefill −27% (1300→945 tok/s).

### Measured long-context runs (actual context ≥ 100K; acceptance from raw JSONs)
| config | served ctx | actual ctx | decode tok/s | acceptance |
|---|---|---|---|---|
| Q3_K_XL-embedded + MTP n2 (tensor c262144) | 262,144 | **258,779** | 45.17 | **1.000** |
| Q3_K_XL-embedded + MTP n2 | 262,144 | 248,368 | 44.61 | 1.000 |
| Q3_K_XL-embedded + MTP n2 | 262,144 | 179,709 | **50.12** | 1.000 |
| Q3_K_XL-embedded + MTP n2 | 262,144 | 99,885 | 59.27 | 1.000 |
| Q5_K_XL-embedded + MTP n2 (tensor c147456) | 147,456 | 139,872 | 42.86 | 1.000 |
| IQ4_XS + MTP n2 (layer c180) | 184,320 | 168,011 | 32.62 / 29.53 / 28.55 | 0.922 / 0.801 / 0.752 |
| IQ4_XS + DFlash2 n4 (layer c196) | 196,608 | 184,011 | 30.26 / 23.88 / 22.91 | 0.553 / 0.410 / 0.434 |
| Q4_K_M + MTP n2 (layer c163) | 163,840 | 152,011 | 28.65 / 28.60 | 0.882 / 0.876 |
| IQ4_XS no-spec (layer c180) | 184,320 | 40,347 | 23.22 / 23.11 | — |

⚠️ **Corrected 2026-08-29:** only **q3-embedded** and **Q4_K_M** (16,464,440,224 B, per `/srv/models/download.log`) are gone. **`q5-embedded` IS the current on-disk `Qwen3.8-27B-UD-Q5_K_XL.gguf`** (mtime Aug 21 18:22 = the file measured at 262K) — all four on-disk GGUFs carry the MTP head, so there was never a separate embedded build (G9). Rows using q3-embedded or Q4_K_M are irreproducible without re-download; all rows are additionally irreproducible on current images (see G7). Current on-disk set: IQ4_XS 14.25 GB, Q4_K_XL 17.56 GB, Q5_K_XL 20.88 GB, Q6_K_XL 25.30 GB, DFlash2 drafter 1.14 GB.

### VRAM MODEL — measured slopes, and why the old ceiling table was wrong (corrected 2026-08-29)

⚠️ The previous table computed per-GPU KV as `total ÷ 2 GPUs` from rates f16/q8_0/q4_0 =
64/32/16 KiB per token. **The measured per-GPU q4_0 rate is 16.0 KiB/token/GPU — 2× what that
table assumed** — which is why it wrongly concluded `Q6_K_XL + q4_0 @262,144` fits "with ~1 GiB
headroom". Measured slope (`n8-ctx-ceiling-20260822-0938`, Q6_K, tensor, q4_0, MTP n=8):
131,072 → 196,608 → 262,144 gives **13,134 → 14,158 → 15,182 MiB/GPU** = exactly **+1,024 MiB
per +65,536 tokens**.

**Empirical VRAM model** (validated against 3 independent measured points to ≤0.2 %):

    VRAM_per_GPU(MiB) ≈ (file_bytes / 2^30 / 2) * 1024  +  ctx * rate  +  180–420 fixed
    rate:  q4_0 = 16.0 KiB/token/GPU      f16 = ~34.5 KiB/token/GPU   (both measured, tensor split)
    practical ceiling ≈ 15,650 MiB/GPU   (max stable ever observed 15,636; card total 16,311)

Validation: Q5_K_XL q4_0 @262,144 → 9,955+4,096+183 = **14,234** (measured 14,234 ✓) ·
Q4_K_M q4_0 @262,144 → 7,851+4,096+339 = **12,286** (measured 12,286 ✓) ·
IQ4_XS f16 max-stable → (15,636−6,796−300)/34.5 KiB = **~246K** (bisect measured 245,760 ✓).
Q4_K_M's exact size (16,464,440,224 B) recovered from `/srv/models/download.log`.

### Context ceilings on 2×16GB — MEASURED (M) vs PREDICTED (P)
| quant | weights MiB/GPU | q4_0 KV | f16 KV |
|---|---|---|---|
| IQ4_XS | 6,796 | 262,144 = native cap (P ~547K) | ~245,760 **M** (bisect, no-spec) |
| Q4_K_XL | 8,373 | 262,144 (P) | ~196,608 (P) |
| Q5_K_XL | 9,955 | ⚠️ **SUPERSEDED — see E11a: 196,608** on a surviving image; E1's 163,840 was a VRAM-gate artifact, and the 262,144 row came from the deleted tensor-split image | **147,456 ✓ M, 15,198 MiB** |
| **Q6_K_XL** | **12,064** | **~210,000 (P) → test 196,608. 262,144 needs 16,343–16,580 MiB > 16,311 capacity → PREDICTED OOM** | **~98,304 (P)** |
| old UD-Q6_K (gone, ≈21.6 GB) | 10,284 | 262,144 ✓ M — 14,760 MiB | — |
| vLLM NVFP4 (fp8 KV) | — | 98,304 hard cap; ~48K with MTP | — |

⚠️ **q8_0 KV is unusable on this stack** — three independent failures: illegal memory access
@c4096 (kvhyp-20260820-1335), "failed to allocate" @262K (kvquant-20260821-2106), "FAIL out of
memory" @262K (matrix-q3q6-20260821-2125). `{f16, q4_0}` are the only KV options. Do not spend
GPU time re-testing q8_0 unless the image changes.

⚠️ **Speculative decoding costs context.** `IQ4_XS ctx=262,144 + MTP FAILS to allocate, but
no-MTP at 262,144 OK` (iq4tensor-20260820-1403). `props-iq4_xs.json` — the artifact cited for
"IQ4_XS 262,144 ✓" — records `n_ctx=262144` **and `speculative.types = none`**, and does **not**
record the KV dtype. That row therefore proves a *no-spec* ceiling, and its "f16" label is an
inference, not evidence. **props-*.json never record cache-type — never cite them for a KV claim.**

⚠️ **Every tensor-split result and every 262,144 result in this file was produced on
`llamacpp-dflash2-pr27342:1deefcc-sm120-cuda128-abi`, which is NO LONGER ON DISK.** Surviving
images: `llamacpp-mtp:latest` (0.3.0-dev, build 1, d222767) and `llama-dflash2:latest`
(0.1.2-dev, build 50, f7aadef) — both expose `-sm {none,layer,row,tensor}`, `-ctk/-ctv`,
`--spec-type draft-mtp`, `-ctxcp`, `-fit`. Until E6 re-proves `-sm tensor` on a surviving image,
treat every tensor-split row as **irreproducible-on-current-images**. Known-good on a surviving
image: `llamacpp-mtp:latest` + `-sm layer` + q4_0 KV + `--spec-type draft-mtp --spec-draft-n-max 2`
@131,072 (ran to completion inside `job_agentic_steps`).

**OPEN HYPOTHESIS — E1 decides Q6_K_XL's real ceiling.** Every slope above comes from
**tensor-split** runs. If `-sm layer` distributes the KV cache by layer, per-GPU KV could be
~half (8 KiB/token/GPU at q4_0) → `Q6_K_XL + q4_0 @262,144` would land near **14.5 GiB/GPU and
fit**. If instead layer split shows the same 16 KiB/token/GPU, Q6_K_XL is a ~200K quant and
Q5_K_XL is the only 262K-capable accuracy quant. **Measure this before believing either.**

### ⚠️ SUPERSEDED 2026-08-29 by E11 — see E11 EXECUTION LOG for the current Track A candidate
### (historical) CURRENT RECOMMENDATION — Track A, PROVISIONAL, blocked on E1+E2+E3
**Provisional pick: `Q6_K_XL + MTP n=2 + q4_0 KV @ the largest ctx E1 proves`** (expect 196,608;
262,144 only if E1's layer-split hypothesis holds). Rationale: accuracy is quant-dominated
(KLD 0.0016 = 12× better than IQ4_XS; PPL 6.6511; HE+ 91.5; thinking 88.4; SWE calib 3/3);
spec decode is greedy-lossless so MTP n=2 buys ~2× decode without touching outputs; q4_0 is the
only KV dtype that reaches ≥196K on this quant.
⚠️ The earlier claim "`Q6_K_XL + q4_0 @262,144` fits by math with ~1 GiB headroom" is
**WITHDRAWN** — the corrected model predicts OOM by 30–270 MiB under tensor split.
**Measured fallback (full native window): `Q5_K_XL + MTP n=2 + q4_0 @262,144`** — 39.33 tok/s,
14,234 MiB/GPU, on the exact on-disk GGUF; one fidelity step down (KLD 0.0038, HE+ 90.9).
**Zero-KV-risk fallback: `Q6_K_XL + f16 KV @ ~98,304`** — no KV-quant error at all.
**Eliminated for Track A:** vLLM NVFP4 (98K cap), DFlash2 (acceptance collapse at depth),
Q3_K_XL (agentic-useless), IQ4_XS as primary (stays the ≤32K speed pick: 57.5 tok/s, 3.70 J/tok).
Practical window: 262,144 tokens ≈ 0.9–1.1 MB dense source ≈ **10–20K LOC**; 196,608 ≈ 8–15K LOC.

## OPEN GAPS — status as of 2026-08-29 (audited against the machine, not inferred)

- **G1 — No task-accuracy-vs-context measurement exists for ANY quant.** STILL FULLY OPEN, and
  **worse than previously written**: there are **no 100K–250K task outputs to score**. Every
  `.diff` in `champion-20260821` came from a **40,347-token** prompt (all 81 context-tagged raw
  files are `c40k`); the 100K–258K runs generated **50–55-token JSON needle answers**, not code
  edits. G1 cannot be closed without new GPU time (E5).
- **G2 — KV-quantization fidelity at depth unmeasured.** OPEN. q4_0 unlocks the big windows but
  its NLL/accuracy cost at 100–250K attended tokens is unknown. Note the axis is now only
  **f16 vs q4_0** (q8_0 is broken on this stack).
- **G3 — Q6_K_XL max context is unmeasured and the old math was wrong.** OPEN and **now the
  user's headline question**. Corrected model predicts OOM at 262,144 under tensor split and
  ~210K feasible; the layer-split hypothesis could restore 262,144. E1 settles it.
- **G4 — Retrieval at depth: PARTIALLY ANSWERED, weakly.** The champion "cold context" probes
  were already 3-needle retrieval tests over a real django corpus, machine-checked via
  `"retrieval_pass": true` in the result JSONs, and they **pass at 99,885 / 179,709 / 248,368 /
  258,779 tokens (Q3-embedded) and 139,872 (Q5-embedded)**. ⚠️ Weak evidence: **verbatim marker
  strings** at only **25 % / 50 % / ~100 % depth**, no code semantics, n=1, and the KV dtype of
  those runs is not recorded anywhere. Does NOT license "accuracy holds at 250K".
- **G5 — Q6_K_XL long-context prefill unmeasured.** OPEN (Q3-embedded: 538 tok/s @250K ≈ 8 min
  ingest; MTP prefill −27 % measured only at 40K on IQ4_XS).
- **G6 — Thinking mode × long context × MTP unmeasured on llama.cpp.** OPEN.
- **G7 — Image provenance: WORSE THAN WRITTEN.** The image behind **every** tensor-split and
  **every** 262,144 result — `llamacpp-dflash2-pr27342:1deefcc-sm120-cuda128-abi` — **is gone
  from disk**. Only `llamacpp-mtp:latest` and `llama-dflash2:latest` remain. Half-answered:
  `llamacpp-mtp:latest` + `-sm layer` + q4_0 + draft-mtp n=2 @131,072 is proven (it ran
  `job_agentic_steps` to completion). Unproven on surviving images: `-sm tensor`, and q4_0 at
  ≥180K. E6.
- **G8 — Losslessness assumes greedy verification.** OPEN (temperature > 0 with draft-mtp untested).
- **G9 — Embedded-MTP provenance: RESOLVED 2026-08-29.** All four on-disk GGUFs contain the MTP
  head — `qwen35.nextn_predict_layers` + `blk.64.nextn.{eh_proj,enorm,hnorm,shared_head_norm}.weight`
  (verify: `head -c 60000000 <gguf> | strings -n 6 | grep nextn`). There was never a separate
  "embedded-drafter" build: **`q5-embedded` IS the current `/srv/models/Qwen3.8-27B-UD-Q5_K_XL.gguf`**
  (mtime Aug 21 18:22 = the file measured at 262K). Only `q3-embedded` and `Q4_K_M` are truly gone.
- **G10 — Statistical power.** OPEN (verified50 n=49 → ±12 pt CI). Any accuracy-vs-context claim
  needs multi-task/multi-seed + Wilson/bootstrap CIs.
- **G11 — KV dtype of the long-context needle runs is unrecorded (NEW).** The champion 262K probe
  JSONs store timings and `retrieval_pass` but not `-ctk/-ctv`, and no launch wrapper survives in
  the champion tree. If those runs were q4_0, we already hold partial G2 evidence at 250K for
  free; if f16, we hold none. Must be resolved or the runs labelled KV-UNKNOWN in both tracks.
- **G12 — `nvfp4-20260822-1029` provenance (NEW).** PAPER-REFERENCES reports an NVFP4 run
  "ctx=262,144 n=2 52.58 tok/s (12,622 MiB) with tensor+q4_0 flags" — but `-sm tensor` and q4_0 KV
  are llama.cpp concepts and NVFP4 caps at 98,304 on vLLM. Either the label or the flags are wrong.
  Resolve before either deliverable cites that row.

## TEST PLAN (2026-08-29) — how to fill the gaps. Follow this literally.

Read this whole section before running anything. Every experiment states **track, gap,
priority, cost, method, exact commands, output artifact, decision rule**. Run P0 in order
(E0 → E6 → E1 → E2 → E3); everything else may run in any order once its inputs exist.

### Shared recipe — launch, verify, measure, tear down
All llama.cpp experiments use this exact skeleton. Do not improvise flags; the ones below are
verified present in both surviving images (`--help` checked 2026-08-29).

```bash
# 1. LAUNCH  (vary: IMG, MODEL, SM, CTX, CTK/CTV, SPEC)
docker rm -f llamasrv 2>/dev/null
docker run -d --name llamasrv --gpus all --network host -v /srv/models:/models:ro \
  "$IMG" -m "/models/Qwen3.8-27B-UD-${QUANT}.gguf" \
  -ngl 99 --split-mode "$SM" --ctx-size "$CTX" \
  --cache-type-k "$KV" --cache-type-v "$KV" \
  -fit off -ctxcp 4 -np 1 --seed 20260829 \
  --spec-type draft-mtp --spec-draft-n-max 2 \
  --host 0.0.0.0 --port 8080
```
`-fit off` is mandatory: without it llama.cpp silently shrinks the context to make it fit, and
the run reports success at a window you did not ask for.

```bash
# 2. VERIFY the window is real (never trust the launch alone)
curl -sf localhost:8080/health >/dev/null || echo "SERVER DEAD"
curl -s localhost:8080/props | grep -o '"n_ctx":[0-9]*'          # MUST equal $CTX
nvidia-smi --query-gpu=index,memory.used --format=csv,noheader   # per-GPU VRAM after load

# 3. PROVE it decodes (a server that loads but cannot generate is a failure)
curl -s localhost:8080/completion -H 'Content-Type: application/json' \
  -d '{"prompt":"def fib(n):","n_predict":64,"temperature":0,"cache_prompt":false}' \
  | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d["timings"]["predicted_per_second"])'

# 4. MEASURE VRAM AGAIN AFTER A DEEP PREFILL — compute buffers grow with the batch,
#    so post-load VRAM understates the true peak. Prefill to >=90% of $CTX, then re-read.

# 5. TEAR DOWN — ALWAYS via kill_server so docker logs are persisted first
source /srv/bench/orchestrator/lib.sh
kill_server llamasrv "<label>"      # writes /srv/bench/server-timings/<label>.serverlog
```

### Running these through the orchestrator (preferred for anything >10 min)
Add a `job_<name>()` to `/srv/bench/orchestrator/worker.sh` following the existing idiom, and
append the call to the `while true` main loop:

```bash
job_my_experiment() {
  local J=my-experiment
  job_done $J && return 0
  gpu_busy && { jlog $J "waiting: GPU busy"; return 0; }
  mark_start $J; gpu_acquire
  timeout 21600 bash "$ORCH/my-experiment.sh" >> "$LOGS/$J.log" 2>&1
  local rc=$?
  gpu_release
  [ $rc -eq 0 ] && mark_done $J || jlog $J "FAILED (exit $rc)"
}
```
Rules that are not optional: idempotent (guard on `job_done`), `gpu_acquire`/`gpu_release`
around all GPU work, `kill_server` before every container removal, write a JSON artifact under
`/srv/bench/`, re-run with `rm /srv/bench/orchestrator/state/<job>.done`.

---

### E0 [both tracks, P0, ~15 min, no GPU] — Environment truth pass
**Mostly DONE 2026-08-29.** Confirmed: MTP heads present in all 4 on-disk GGUFs (G9 closed);
only `llamacpp-mtp:latest` + `llama-dflash2:latest` survive; both expose every flag the plan
needs; disk 43 G free; 0 `sweb.eval` images remain.
**Remaining:** write `/srv/bench/env-manifest.json` recording, for both images,
`docker image inspect --format '{{.Id}} {{.Created}}'`, the `--version` string, and the GGUF
sha256/size list. Every experiment artifact must reference this manifest by image id, because
the historical image is gone and this must not happen twice.

### E6 [Track A+B, G7, P0, ~30 min GPU] — Split-mode reproducibility on surviving images
**Run this BEFORE E1** — it decides which split modes E1 is even allowed to sweep.
Method: at a cheap `CTX=32768`, q4_0 KV, MTP n=2, run the shared recipe for the 4 cells
{`llamacpp-mtp:latest`, `llama-dflash2:latest`} × {`layer`, `tensor`}. Record load OK/FAIL, the
exact CUDA error if any, decode tok/s, per-GPU VRAM.
Output: `/srv/bench/splitmode-repro.json`.
Decision: if `-sm tensor` fails on both surviving images (the historical upstream failure mode
was `CUDA error: an illegal memory access was encountered`), then **layer split is the only
reproducible mode**, E1 sweeps layer only, and every tensor-split row in this file gets the
label `irreproducible-on-current-images` in both deliverables.

### E1 [Track A, G3, P0, ~60–90 min GPU] — **Q6_K_XL's ACTUAL maximum context** (the headline question)
Measure it; do not infer it. Sweep, for each split mode E6 cleared:
`Q6_K_XL` × KV {q4_0, f16} × spec {draft-mtp n=2, none} × ctx ladder
**262144 → 245760 → 229376 → 212992 → 196608 → 180224 → 163840 → 147456 → 131072**.
Descend until the first success, then **re-test the rung above it** to bracket the ceiling.
A cell counts as SUCCESS only if all four hold: server healthy · `/props` `n_ctx` equals the
requested value · a 64-token greedy generation completes · peak per-GPU VRAM (measured after a
≥90 %-of-window prefill) ≤ ~15,700 MiB.
Also record, per cell, the **per-GPU KV slope** (VRAM difference between adjacent rungs ÷ token
difference) — this is what tests the layer-split hypothesis and is a Track B result in its own right.
Output: `/srv/bench/q6-ceiling.json` — one record per cell:
`{image_id, sm, kv, spec, ctx_requested, ctx_reported, ok, vram_gpu0, vram_gpu1, prefill_tok_s, decode_tok_s, err}`.
Predictions to check against (if measurement disagrees, the model is wrong — trust the measurement
and rewrite the VRAM MODEL section): tensor+q4_0 first success ≈ **196,608–212,992**;
tensor+f16 ≈ **98,304**; layer+q4_0 = **262,144 if and only if the layer-split hypothesis holds**.
**Decision:** `CTX_MAX_Q6` := the largest bracketed success. Everything downstream uses it.

### E1b [Track A+B, G7, P1, ~45 min GPU] — Re-prove Q5_K_XL and IQ4_XS on surviving images
The 262,144 proofs came from the deleted image, so the whole ceiling table is currently
unreproducible. Repeat E1's ladder (abbreviated: 262144 → 229376 → 196608) for `Q5_K_XL` and
`IQ4_XS` at q4_0 + MTP n=2 on the cleared split modes. Append to `/srv/bench/q6-ceiling.json`
(rename it `/srv/bench/ctx-ceilings.json` once it covers more than Q6).
**Decision:** if Q5_K_XL no longer reaches 262,144 on a surviving image, the "measured fallback"
in the recommendation is void and must be restated at whatever it does reach.

### E2 [Track A+B, G2, P0, ~2–3 h GPU] — KV fidelity: does q4_0 cost accuracy at depth?
Two complementary measures, because neither alone is sufficient.

**(a) Paired greedy-divergence test** — the cleanest causal measure. At depths
{32K, 64K, 98K} (the windows where **both** f16 and q4_0 fit on Q6_K_XL), build one fixed code
prompt, then generate **256 tokens greedy (`temperature 0`, same `--seed`, `cache_prompt:false`)**
under `-ctk/-ctv f16` and again under `q4_0`, changing nothing else. Record the index of the
first differing token and the token-level exact-match rate. Spec decode is greedy-lossless, so
KV dtype is the only variable — **any divergence is KV error, attributable and unambiguous.**

**(b) NLL ladder** — the numeric fidelity metric. Score mean NLL of the final 256 tokens of a
long **code** prefix (never wikitext — the target workload is code) at
{32K, 64K, 128K, 192K, CTX_MAX_Q6} × {f16 where it fits, q4_0} × {Q6_K_XL, Q5_K_XL}.
Reuse the scoring method from `/srv/bench/orchestrator/nvfp4-ppl-protocol1.sh` (echo + logprobs,
half-window rule) so the numbers stay comparable to the perplexity work. Build prefixes with the
champion prompt builders (`champion-20260821/build_django_*_prompt.py`).
⚠️ This is a **fourth** scoring protocol — label it explicitly and never place it in a table with
Protocols 1/2 or the NVFP4 runs.

Output: `/srv/bench/kv-fidelity.json`.
**Decision rule:** adopt q4_0 iff **(a)** ≥250/256 exact-match at 98K **and** **(b)** ΔNLL ≤3 %
relative to f16 at the deepest common window. Otherwise demote down the ladder
**q4_0 → f16 @~98,304 → Q5_K_XL(q4_0) @262,144** (q8_0 is not a rung — it is broken here).

### E3 [Track A P0 / Track B P1, G4, ~3 h GPU] — Code-NIAH: retrieval and comprehension at depth
**Reuse `champion-20260821/run_cold_code_context_probe.py`** — it already builds a real django
corpus, plants `# AUDIT FACT` markers, and self-validates via `retrieval_pass`. Do not rewrite it;
extend it:
1. **Depths** {10, 25, 50, 75, 90, 99} % — the existing probe only covers 25/50/~100 %, and the
   75–95 % band is exactly where long-context models fail.
2. **Two needle classes**: (i) *verbatim marker* (existing, easy — keep for continuity);
   (ii) **code-semantic**, e.g. "which function raises `FooError`, and what is the default of its
   second parameter?" planted at depth. Class (ii) is the one that models the real workload;
   class (i) alone is not evidence of comprehension.
3. **Padding must be real repo files** (as the probe already does). Never pad with repeated
   filler — repetition makes attention trivially easy and inflates every score.
4. Configs: `Q6_K_XL(q4_0)@CTX_MAX_Q6`, `Q6_K_XL(f16)@98304`, `Q5_K_XL(q4_0)@262144`,
   `IQ4_XS(q4_0)@262144`. Windows {40K, 98K, 128K, 180K, max}. **3 seeds.**
Output: `/srv/bench/code-niah.json`; metric = exact-match (class i) and graded correctness
(class ii), reported **per depth**, with Wilson CIs.
**Decision rule (Track A):** a config is eligible only if class-(ii) accuracy at 90 % depth is
≥90 % and shows no cliff versus its 50 %-depth score.

### E4 [Track A+B, G1 partial, P1, ~2 h, CPU-only] — Score the champion outputs that already exist
⚠️ **Scope corrected 2026-08-29:** this yields **accuracy at 40K across quants**, NOT
accuracy-vs-context. Every champion `.diff` came from a 40,347-token prompt; there are no
100K–250K task outputs anywhere on this host.
Method: gate the oracles with `/home/multivac/validate-oracles.sh` (G1 imports / G2 fails-pre /
G3 passes-fix — an oracle that fails any gate is noise, not a test), then apply each
`champion-20260821/raw/*.model.diff` to a pristine worktree and run the gated tests with
`--parallel 1` (the parallel runner dies with `cannot pickle 'traceback'`).
Output: `/srv/bench/champion-40k-accuracy.json`.
Value: a free quant-accuracy datapoint at 40K (q3-embedded, q5-embedded, q4km, iq4xs, dflash2),
and it settles whether Q3's *edits* were correct at 40K. Note its 250K *needle* answers were
already correct — so the "acceptance ≠ accuracy" warning must be phrased about **agentic
competence**, not retrieval.

### E5 [Track A+B, G1+G5+G6, P1, ~10–15 GPU-h, overnight] — Definitive accuracy-vs-context sweep
Run only after E1/E2/E6 have pinned image, split mode, KV dtype and `CTX_MAX`.
Grid: django prefix-edit tasks at **{40K, 98K, 150K, CTX_MAX}** × **{Q6_K_XL, Q5_K_XL, IQ4_XS}**
× chosen KV × greedy × **3 seeds**, plus **one thinking-on arm at the winning config** (closes G6).
Pad to depth with real repo files. Record per run: prefill tok/s, decode tok/s, acceptance,
peak per-GPU VRAM, oracle pass/fail. Score with the same gated harness as E4.
Output: `/srv/bench/accuracy-vs-context.json` → this is the paper's accuracy-vs-context figure
(Track B) and Track A's proof that its pick does not degrade at depth.

### E7 [both tracks, G8+G10, P2, protocol not experiment] — Statistics & sampling
≥3 seeds per headline config. **Wilson** CIs for pass rates, **bootstrap** (B=10,000, seed
20260825, matching `bootstrap-ci.json`) for continuous metrics. A claim enters **either**
deliverable only if CIs separate or the effect exceeds the CI width; otherwise report it as
"indistinguishable at n=…". All losslessness claims are **greedy-only** unless a temperature>0
draft-mtp test is run (G8). Track B additionally reports n and CI on every table row.

### E8 [Track A, G5, P1, ~1 h GPU] — Speed and energy at the chosen config
After E1–E3 select the config: run the 3-run-median speed probe (`/srv/bench/speed-probe2.py`)
at **filled** contexts {4K, 40K, 98K, CTX_MAX} and integrate `/srv/bench/power-log.csv` over each
window for J/tok (method: OPTIMIZATION-LOG §13.73). Closes G5 (Q6_K_XL prefill at depth) and
gives Track A its tok/s number **at the accuracy-first config**, not at a config nobody will run.
Output: `/srv/bench/chosen-config-speed.json`.

### E9 [Track B only, P2, ~3 h GPU] — Cross-backend comparison at equal context
Run E3's code-NIAH and a reduced E5 grid on **vLLM NVFP4 at 98,304** so the report compares
backends **at the same context**, not each at its own ceiling. Without this, every llama.cpp-vs-
vLLM statement in the article is confounded by window size.

### E10 [both tracks, P0, ~10 min, no GPU] — Provenance repairs
(a) **G11** — determine the KV dtype of the champion 262K needle runs (search any surviving
launch wrapper / shell history / `server-timings/*.serverlog`); if unrecoverable, label those
rows **KV-UNKNOWN** in both deliverables — do not guess.
(b) **G12** — resolve the `nvfp4-20260822-1029` row in PAPER-REFERENCES ("NVFP4 … tensor+q4_0
flags" is internally contradictory).
(c) Correct the `props-*.json` citations: they record `n_ctx` and `speculative.types`, never the
cache type.

---

### TRACK A — final decision procedure (run in this order, stop at the first config that passes)
1. `CTX_MAX_Q6` := E1's bracketed maximum for `Q6_K_XL` on a **surviving** image (E6-cleared split mode).
2. If E2 clears q4_0 (divergence ≤6/256 at 98K **and** ΔNLL ≤3 %) → candidate is
   **`Q6_K_XL + MTP n=2 + q4_0 @ CTX_MAX_Q6`**.
3. Candidate is **confirmed** only if E3 shows ≥90 % code-semantic accuracy at 90 % depth with no
   cliff vs 50 % depth, and E5 shows no accuracy drop at `CTX_MAX_Q6` versus 40K beyond CI width.
4. On any failure, demote in this order and re-run steps 2–3:
   **Q6_K_XL(q4_0)@CTX_MAX → Q6_K_XL(f16)@~98,304 → Q5_K_XL(q4_0)@262,144 → Q5_K_XL(f16)@147,456.**
   (Accuracy outranks context: a Q6 window of 98K beats a Q5 window of 262K **only if** E2/E3/E5
   show Q5 is measurably worse on task accuracy. If Q5 and Q6 are indistinguishable within CIs,
   priority (2) applies and the larger window wins.)
5. Report tok/s and J/tok from E8 **last** — it is a tiebreaker, never a selector.

### Hygiene rules for every experiment here
1. `-fit off` always, and assert `/props` `n_ctx` — a silently shrunk window has invalidated
   results on this host before.
2. Never remove a container without `kill_server` (it persists `docker logs` first).
3. Never `docker image prune` — the image that produced every 262K result is already gone.
4. Record the **image id** from `env-manifest.json` in every artifact.
5. VRAM is measured **after a deep prefill**, never only after load.
6. Never mix scoring protocols in one table; E2(b) is a new, fourth protocol.
7. Every artifact is JSON under `/srv/bench/`, with `source` and `run_ids` provenance fields, the
   same convention `swebench_agg.py` established.

## EXECUTION LOG — 2026-08-29 P0 run (E0/E6/E10/E1/E1b/E9a) + OBSERVATIONS FOR AGENTS

This section records what the 2026-08-29 afternoon execution pass actually did, what it found,
and the operational lessons. Read it before re-running any of these experiments.

### Completed and where the evidence lives
| Experiment | Result | Artifact |
|---|---|---|
| E0 | Image IDs + versions + GGUF sha256/sizes pinned | `/srv/bench/env-manifest.json` |
| E6 | layer ✓ on both images (mtp 39.3 / dflash2 35.6 tok/s); tensor ✗ CUDA-IMA on both | `/srv/bench/splitmode-repro.json` |
| E10 | G11 → KV-UNKNOWN; G12 → llama.cpp NVFP4-GGUF run (weights deleted); props convention | `/srv/bench/provenance-repairs.json` |
| E1 | Q6_K_XL ceilings: **131,072** MTP / **245,760** no-spec / **98,304** f16 / <65,536 f16+MTP | `/srv/bench/q6-ceiling.json` |
| E1b+E1b4 | **Q4_K_XL 196,608 · Q5_K_XL 163,840 · IQ4_XS 262,144 ✓** (MTP n2, q4_0, layer) | `/srv/bench/ctx-ceilings.json` |
| NVFP4 provenance | `/srv/engines/nvfp4` weights sha256 `c473512c70ea…`/`1d8268aa85ac…` = HF current rev `57926ba` — **the HF cache has NO weights**; vLLM must mount `/srv/engines/nvfp4` | `/srv/bench/nvfp4-vllm-context.json` (partial) |
| E9a (partial) | nightly KV pool **52,337 tokens @ gmu 0.97** → ceiling **51,200 boots**; gmu 0.99 impossible; speed/NIAH/MTP **not yet measured** (aborted — bugs identified, fixes known, see below) | log: `/srv/bench/nvfp4-vllm-context.log`; serverlogs under `/srv/bench/server-timings/` |

**Measured XL-tier ladder (MTP n2, q4_0, layer, surviving image) — the Track A frontier:**
IQ4_XS 262,144 (39.5 tok/s) → Q4_K_XL 196,608 (30.2) → Q5_K_XL 163,840 (24.5) → Q6_K_XL 131,072 (32.3).
Context ceiling is monotonic in quant size; accuracy and window trade off directly. Historical
262K results for Q5/old-Q6 were tensor-split on the deleted z-lab image and do NOT reproduce.

### E9a restart instructions (the fixes are known — ~60 min to finish)
The script `/srv/bench/e9a2-nvfp4.sh` is on disk and structurally sound; apply these three fixes
(or use them as-is: two were already applied in the /tmp copy — recreate from this section if
/tmp was cleared):
1. **vLLM requires `"model"` in every OpenAI request body** (llama.cpp does not). Add
   `"model": "/engine"` (the served name = the mount path) to the prefill/decode bodies and to
   the NIAH probe payload. Without it: HTTP 400. The first pass crashed here — cost: one full run.
2. **`json.loads(urllib.request.urlopen(...))` is a bug** — pass `.read()`:
   `json.loads(urllib.request.urlopen(r, timeout=3600).read())`. The current script crashes with
   `TypeError: ... not HTTPResponse` AFTER the request succeeds (deep prefill ran unmeasured).
3. **MTP syntax**: `--speculative-config method=mtp num_speculative_tokens=2` (key=value pairs).
   The JSON-string form reaches vLLM as a plain str → `AttributeError: 'str' object has no
   attribute 'items'` → boot fails in ~60 s. Unmeasured arm: MTP ceiling + decode on vLLM.
Then re-run phases B2–F of the script (boot 51,200 → prefill/decode at depth with VRAM →
NIAH at {40K, 43K} → MTP arm at 49,152/40,960 → stable-image pool comparison (see below) →
aggregate to `/srv/bench/nvfp4-vllm-context.json`).
**Open question worth one boot**: the historical "cap at 98,304" was on the STABLE image
(v0.27.1). Nightly pool = 52,337 @ gmu 0.97. Boot stable once at max-model-len 4096, gmu 0.97,
and read its pool — if stable gives ~100K, the 98K historical rows are stable-image-specific and
the nightly is NOT the right image for context-max; if stable also gives ~52K, the historical
98K cap claim needs re-examination (it may never have been KV-bound in the way written).

### Observations for other agents (operational lessons, learned the expensive way)
1. **vLLM boot = 13–16 min** (weight load dominates); failures fail FAST (<2 min) — time-box
   health waits at 20 min and treat a 60–120 s death as a config error, not a load.
2. **gmu 0.99 is impossible on 16 GB cards** — boot dies in ~60 s. gmu 0.97 is the ceiling that
   boots; pool = 52,337 tokens on nightly.
3. **vLLM `/v1/*` requires `"model"`** in the body even in offline single-model serving. This
   cost one full experiment pass. llama.cpp does not require it.
4. **`json.loads(urlopen(...))` without `.read()`** crashes after a successful request — the
   measurement is then lost even though the GPU work happened. Always `.read()`.
5. **llama-dflash2:latest needs `--entrypoint /app/llama-server`** — its default entrypoint is a
   wrapper that rejects `--host` (`invalid argument: --host`, dies in ~19 s).
6. **VRAM under layer split is GPU1-bound and noisy**: ±100–200 MiB load-to-load variance (draft
   head + output layers + allocator layout). Marginal rungs are NONDETERMINISTIC — Q4_K_XL's
   212,992-style surprises: in E1, 245,760 passed while 212,992 OOMed in the same arm. Always
   bracket a ceiling with a re-test, and state the variance in the artifact.
7. **Q4_K_XL fails differently**: at 229,376/262,144 the server HANGS during init (no error
   output within 10 min; 572-byte serverlogs) — not a clean OOM. Treat init-hang ≠ OOM when
   labelling failure modes; both were observed on the same host in the same run.
8. **Measure VRAM AFTER a deep prefill** — load-time VRAM understates peak by the compute
   buffers; two of today's ceilings would have been over-optimistic otherwise.
9. **`kill_server` (lib.sh) before every container removal** — it persists `docker logs` to
   `/srv/bench/server-timings/<label>.serverlog`, which is how the OOM-vs-IMA vs init-hang
   failure modes were recoverable at all.
10. **pkill self-match**: `pkill -f <pattern>` kills your own ssh session when the pattern
    appears in your command line — use `pkill -f 'name[pattern]rest'` bracket trick or exact
    pid files. Hit twice today; each cost a dropped session.
11. **Historical artifacts**: every 262,144 / tensor-split number predates the image deletion and
    the split-mode discovery — treat them as `irreproducible-on-current-images` and never mix
    them into a table with fresh measurements without that label.
12. **The NVFP4 vLLM weights are NOT in the HF cache** (`blobs/` = 26 MB of config only). They
    live in `/srv/engines/nvfp4/` — mount that, and keep the sha256 pin (`c473512c70ea…`) in
    every artifact.

## E11 EXECUTION LOG — 2026-08-29 evening (Q6_K, functional ceilings, depth benchmark)

Harness: `/srv/bench/e11/` (`lib_probe.py`, `pad.py`, `ctx_ceiling.py`, `depth_bench.py`,
`tsweep.py`, `score.py`, `validate*.py`, runners `run_phase{A,B,C}.sh`). Artifacts land in
`/srv/bench/e11/*.json`. All runs: `llamacpp-mtp:latest`
(`sha256:feb0231976b6…`, 0.3.0-dev build 1 d222767), `-sm layer`, `-fit off -ctxcp 4 -np 1`,
seed 20260829, greedy.

### DECISION — Track A is llama.cpp-only from here (vLLM NVFP4 eliminated, with data)
The elimination is correct but **not for the reason of poor GPU splitting** — vLLM uses tensor
parallelism (TP=2), which splits *every layer* across both cards and is **more balanced than
llama.cpp's layer split**, not less. It fails on the other two axes:
- **Context**: measured 2026-08-29 (E9a) — nightly KV pool = **52,337 tokens**, ceiling
  **CONFIRMED 51,200** at gmu 0.97; gmu 0.99 will not boot. Historical stable-image cap was
  98,304. Against the model's native 262,144 that is **5.1× short** (or 2.7× short on stable),
  and MTP roughly halves it again (~48K).
- **Accuracy**: HumanEval+ **85.4/84.1** vs Q6_K_XL **93.9/91.5** (−7.4 pts); KLD on code
  0.02600 vs Q6_K_XL 0.0016 (16×); PPL 6.7073 vs 6.6511 on matched Protocol-1 windows.
⇒ NVFP4 cannot hold the window *and* match Q6 fidelity. Remaining Track A work is llama.cpp only.
vLLM stays in scope for **Track B** (the report still needs the cross-backend comparison, E9).

### THE TWO CARDS ARE NOT A POOL — and that is where the context is being lost
With `--split-mode layer` each layer's weights **and its slice of the KV cache** live on one
card. There is no NVLink on 5060 Ti. The binding limit is therefore **per-card 16,311 MiB**,
never the 32,622 MiB total: a run OOMs when the *heavier* card fills, while the other still has
room that is physically unreachable. Measured peaks — GPU1 is the binding card every time:

| config | ctx | GPU0 | GPU1 | **idle on GPU0** | free on GPU1 |
|---|---|---|---|---|---|
| Q5_K_XL + MTP n2 | 196,608 | 12,482 | 15,792 | **3,829 MiB** | 519 |
| Q6_K + MTP n2 | 196,608 | 12,978 | 15,640 | **3,333 MiB** | 671 |
| Q6_K + no-spec | 262,144 | 13,910 | 15,192 | 2,401 | 1,119 |
| Q6_K_XL + no-spec | 245,760 | 14,356 | 15,838 | 1,955 | 473 |

Cause: the serverlog confirms MTP builds a **separate draft context against the target model**
(`common_speculative_init_result`) — which is why enabling MTP costs Q6_K_XL 114,688 tokens of
window (245,760 → 131,072). That draft context plus the output/embedding layer sit at the end of
the layer stack and land on the last device (placement is inference from the consistent
asymmetry; the log does not state it). **Every ceiling in this file was set by the unluckier
card, not by the hardware.** `-ts/--tensor-split` is present in both images and moves layers
(with their KV) toward GPU0 — E11c.

### E11a — FUNCTIONAL context ceilings (behavioural gate, not a VRAM threshold)
Success rule: healthy + `/props n_ctx` == requested + a real ~95%-of-window prefill + a 64-token
generation. VRAM recorded, **never gated**.

| config | ceiling | prefill tok/s | **decode at FULL depth** | MTP acc | VRAM peak |
|---|---|---|---|---|---|
| Q5_K_XL + MTP n2 | **196,608** | 621 | **15.47** | 0.848 | 12,482 / 15,792 |
| **Q6_K + MTP n2** | **196,608** | 569 | **7.19** | n/r | 12,978 / 15,640 |
| **Q6_K + no-spec** | **262,144** | 627 | 3.45 | — | 13,910 / 15,192 |
| Q6_K_XL + no-spec | 245,760 | 650 | 3.53 | — | 14,356 / 15,838 |

1. **UD-Q6_K (21.98 GB) is the context win the XL tier could not deliver.** With MTP it reaches
   196,608 vs Q6_K_XL's 131,072 (**+50 %**); without MTP it reaches the **full native 262,144**,
   which Q6_K_XL cannot (262,144 fails with a genuine `failed to allocate compute pp buffers`).
   File verified byte-exact (21,983,677,344 B) and carries `blk.64.nextn` → MTP-capable.
2. **E1's Q5_K_XL ceiling of 163,840 was WRONG — the real ceiling is 196,608.** E1 rejected that
   rung because peak VRAM hit 15,794 MiB against its 15,700 MiB gate, but Q6_K_XL ran fine today
   at **15,838 MiB**. The threshold sat inside the ±100–200 MiB noise it was trying to measure.
   ⚠️ **Any E1 rung failed on VRAM alone (not a real error) must be re-tested.** E1's rejections
   that WERE real errors (Q6_K_XL @262,144) are confirmed.

### ⚠️ DECODE AT DEPTH ≠ DECODE AT AN EMPTY WINDOW (measurement correction, affects every speed row)
Same server, same flags, `Q6_K + MTP n2 @196,608`:
- **depth 0 → 37.22 tok/s** median over 40 tasks, MTP acceptance **0.986**
- **depth 186,265 → 7.19 tok/s** (−81 %)
E1's ladder (Q6_K_XL 26.35 / 30.46 / 32.28 tok/s) and the `ctx=32768` speed table (57.5 / 46.9 /
31.7 …) are **decode into a nearly empty KV cache** in a large *allocated* window. They are not
what a full window feels like. The historical 57.5 tok/s headline is additionally a different
config on all three axes: **IQ4_XS** (smallest quant) + **DFlash2 n=4** (different drafter) at
**ctx 32,768**.
Historical long-context curves show a *milder* penalty (Q3-embedded 71.6 @40K → 44.6 @250K,
−38 %; IQ4_XS+MTP 46.9 @32K → ~28–32 @168K) — but those were measured on the **deleted
tensor-split image**. Under `-sm tensor` attention over the KV is shared across both cards; under
`-sm layer` the owning card does all of it. **UNRESOLVED**: whether the steeper −81 % is a
layer-split artifact, an acceptance collapse, or both.
**UNEXPLAINED, decision-relevant**: at the *identical* 196,608 window, Q5_K_XL decodes at
**15.47 tok/s** vs Q6_K's **7.19** — 2.15× apart for models 5 % apart in size. Q5's acceptance at
depth is 0.848; Q6_K's was not captured (acceptance recording was added after that rung ran).
E11b's per-task acceptance at 65,536 / 131,072 is the instrument that settles it.

### E11b — accuracy / drift / speed vs depth (INTERRUPTED, restart after E11c)
Design: the same 40 HumanEval+ problems at each depth, padded with **real django source**
(`/srv/bench/e11/corpus.txt`, needles at 10/50/90 %), scored through the standard
`evalplus.sanitize → evalplus.evaluate` pipeline with Wilson CIs. Three signals: pass@1;
**output drift vs depth 0** (greedy is deterministic, so any text change is context-induced — far
more sensitive than pass/fail at n=40); needle retrieval.
Completed before the interrupt: `Q6K-mtp196` depth 0 (40/40, 37.22 tok/s, acceptance 0.986) —
`/srv/bench/e11/depthbench-Q6K-mtp196.json`, `bench/Q6K-mtp196/Q6K-mtp196_d0.jsonl`.
Stopped deliberately: benchmarking at 196,608 is wasted if E11c moves the ceiling.
⚠️ n=40 gives a pass@1 CI of ~±9 pts — it **cannot** rank Q6_K against Q6_K_XL (~1 pt apart).
It is sized to detect *degradation with depth*, which is the open question.

### E11c — TENSOR-SPLIT REBALANCE — **THE HEADLINE RESULT** (Q6_K done, others running)
| Q6_K + MTP n=2, q4_0, layer | ctx | decode @ full depth | MTP acc | GPU0 / GPU1 | idle GPU0 |
|---|---|---|---|---|---|
| default split | 196,608 | 7.19 tok/s | n/r | 12,978 / 15,640 | 3,333 MiB |
| **`-ts 58,42`** | **262,144** | **13.85 tok/s** | 0.889 | **15,320 / 15,080** | 991 MiB |
| `-ts 54,46` | 262,144 | FAIL at load | — | — | — |

⇒ **One flag bought +65,536 tokens (+33 %) AND +93 % decode speed at once.** The default
placement stranded 3,333 MiB on GPU0 while GPU1 OOMed 671 MiB from its wall, and it also gave
GPU1 disproportionate attention work — which is a large part of why decode at depth looked so bad.
⇒ **`Qwen3.8-27B-UD-Q6_K` + MTP n=2 + q4_0 + `-sm layer` + `-ts 58,42` @262,144 is the current
Track A candidate: the model's FULL native window at Q6 fidelity, at 13.85 tok/s at full depth.**
⇒ Ratio matters and is not monotone-safe: 54,46 failed to load where 58,42 succeeded. Any change
of quant, KV dtype or spec setting requires re-sweeping `-ts`.

### E11c (original plan, for reference)
Sweeps `-ts` {54,46 | 58,42 | 62,38} at the rung above each current ceiling, stopping at the
first success: Q6_K+MTP and Q5_K_XL+MTP at 262,144→229,376, Q6_K_XL+MTP at 196,608→163,840.
Prediction from the measured imbalance (upper bound — `-ts` moves whole layers, ~440 MiB each at
this context, and the draft context may not move): Q5_K_XL 28,274 MiB total → balanced 14,137/card
→ ~3,000 MiB recovered ≈ **+95K tokens**; Q6_K+MTP 28,618 → ~2,680 MiB ≈ **+85K tokens**. Both
land past the native cap, i.e. **262,144 with MTP** may be reachable for both.
Artifacts: `/srv/bench/e11/tsweep-*.json`.

### Harness bugs caught in pre-flight (before any GPU time was spent)
1. **The model reasons by default.** `max_tokens=16` returned **empty content** with 70 chars of
   reasoning. Unfixed this reproduces the historical 8–13 % empty rates and would have silently
   corrupted a small-sample benchmark.
2. **`/no_think` does NOT work on this chat template** — the widely-cited Qwen3 idiom still
   emitted 130 reasoning chars and empty content. Only
   **`"chat_template_kwargs": {"enable_thinking": false}`** works (2 tokens, 0 reasoning, correct).
3. **Prefix caching works and is what makes depth testing affordable**: `prompt_n 8223 → 516,
   cache_n 7749`. Without it, 40 problems at 250K would cost ~2.5 h per cell instead of ~15 min.
4. Needles resolve 3/3 at 8K; 5 HumanEval tasks, 0 empties, median 173 output tokens (1024 is ample).

### Environment corrections
- **`/srv/models` is a SEPARATE 110 GB disk (`/dev/sda`) at 99 % full — 1.2 GB free.** The 43 GB
  free is on `/` (`/dev/sdb2`). New GGUFs go to **`/srv/bench/models/`**, mounted into containers
  as `/models2` (`lib_probe.MODEL_DIRS`). Disk after Q6_K: 23 GB free on `/`.
- **The NVFP4 weights ARE in the HF cache** — `/srv/models/.hf-cache/models--unsloth--Qwen3.8-27B-NVFP4/blobs`
  holds the real 22 GB (`c473512c70ea…` = `model.safetensors`), duplicating `/srv/engines/nvfp4`.
  The earlier observation "the HF cache has NO weights, blobs/ = 26 MB of config only" is **WRONG**.
  ⇒ **22 GB reclaimable on the full models disk** (keep the `/srv/engines` copy, it is what vLLM mounts).



## OFFICIAL REFERENCES — Qwen3.8-27B (fetched 2026-08-29, both URLs)

Sources: `https://huggingface.co/Qwen/Qwen3.8-27B` (model card) and
`https://unsloth.ai/docs/models/qwen3.8` (Unsloth llama.cpp guide).

### Published benchmark scores (the ONLY official numbers for this model)
| benchmark | official score |
|---|---|
| LiveCodeBench v6 | **90.3** |
| SWE-bench Pro | **61.7** |
| Terminal Bench 2.1 (Terminus) | **73.0** |
| HumanEval / HumanEval+ | **NOT PUBLISHED** |

⚠️ Our SWE-bench work is **Verified**, not **Pro** — 75.5 % is *not* comparable to 61.7.
⚠️ Neither LiveCodeBench v6 nor SWE-bench Pro is set up on this host. See G19.

### Official sampling settings (Qwen card and Unsloth agree exactly)
| mode | temp | top_p | top_k | min_p | presence_penalty | repetition_penalty |
|---|---|---|---|---|---|---|
| **Thinking** | 1.0 | 0.95 | 20 | 0.0 | 0.0 | 1.0 |
| **Instruct / non-thinking** | 0.7 | 0.80 | 20 | 0.0 | **1.5** | 1.0 |

⚠️ **Every benchmark on this host used greedy `temperature 0`** — neither setting. Greedy is still
the right instrument for *controlled quant comparison* (no sampling variance), but absolute scores
under it are not comparable to published numbers. State both facts in the paper. See G16.

### Context
- Native **262,144**; extensible to ~1,000,000 via **YaRN, scaling factor 4.0** (untested here).
- Recommended max output: reasoning 262,144; final response 131,072.

### Thinking control (documented knob — we have been using a different one)
`--chat-template-kwargs '{"reasoning_effort":"medium"}'`, options **`xhigh` | `medium` | `low` |
`none`**. We validated `{"enable_thinking": false}` instead; `reasoning_effort: none` is the
documented equivalent and is untested here. See G17.

### Unsloth quantization guidance
- Unsloth's **recommended default for Qwen3.8-27B is `UD-Q4_K_XL`**, on the claim that Dynamic 3.0
  GGUFs give "10 % more accuracy at the same size". `UD-Q3_K_XL` is their tighter-VRAM fallback.
- ⚠️ That recommendation is a **general** one, not specific to a 2×16 GB full-native-context target;
  our own measurements put `UD-Q6_K` at the full 262,144 window, so the Unsloth default is not
  automatically the right pick here.

### Full Q4–Q6 ladder available in `unsloth/Qwen3.8-27B-GGUF` (sizes from the HF API, 2026-08-29)
| quant | size | status on this host |
|---|---|---|
| UD-IQ4_XS | 14.25 GB | tested — 262,144 (default split) |
| UD-Q4_K_S | 15.36 GB | **untested** |
| UD-Q4_K_M | 16.46 GB | historical only — GGUF deleted |
| UD-Q4_K_XL | 17.56 GB | tested — 196,608 (default split); **Unsloth's recommended default** |
| UD-Q5_K_S | 18.67 GB | **untested** |
| UD-Q5_K_M | 19.77 GB | **untested** |
| UD-Q5_K_XL | 20.88 GB | tested — 262,144 @ `-ts 54,46`, 8.22 tok/s (ratio-confounded, G13) |
| **UD-Q6_K** | **21.98 GB** | tested — **262,144 @ `-ts 58,42`, 13.85 tok/s** ← current best |
| UD-Q6_K_M | 23.09 GB | **untested** — closest untried step UP in fidelity |
| UD-Q6_K_L | 24.19 GB | **untested** |
| UD-Q6_K_XL | 25.30 GB | tested — 131,072 MTP / 245,760 no-spec; rebalance incomplete (G21) |

## OPEN GAPS FROM THE E11 RUN — parked 2026-08-29 to narrow onto candidate selection
Recorded in detail so they can be resumed later. **None of these blocks candidate selection;
all of them matter for the Track B paper.**

- **G13 — `tsweep.py` stops at the FIRST ratio that loads, not the BEST one.** This is a design
  bug when the objective includes speed. Evidence: `Q5_K_XL` succeeded on the first ratio tried
  (`54,46`) with a **744 MiB** residual imbalance and 8.22 tok/s, while `Q6_K` needed `58,42`
  (54,46 failed) and landed at a **240 MiB** imbalance and 13.85 tok/s. ⚠️ **The Q5-vs-Q6 speed
  comparison is therefore RATIO-CONFOUNDED and must not be quoted as a model property.** Fix:
  sweep all ratios, keep the fastest that loads, and report the imbalance alongside.
- **G14 — Speed-vs-filled-context curve is UNMEASURED.** Only 3 points exist for Q6_K+MTP
  (depth 0 → 37.22 tok/s default split; depth 186,265 → 7.19 default; depth 248,522 → 13.85
  rebalanced). The shape between 0 and 186K is unknown. `speed_curve.py` (E11d) is written,
  validated and queued but never ran — an ascending pad ladder makes the whole curve cost ≈ one
  prefill (~15 min/config).
- **G15 — E11b accuracy-vs-depth is 1/16 complete.** Only `Q6K-mtp196` depth 0 (40 tasks,
  37.22 tok/s, acceptance 0.986) exists. Interrupted deliberately when E11c moved the ceilings.
- **G16 — EVERY benchmark on this host used greedy `temperature 0`, which matches NEITHER
  official setting.** Qwen's published settings are **non-thinking: temp 0.7, top_p 0.80,
  top_k 20, presence_penalty 1.5**; **thinking: temp 1.0, top_p 0.95, top_k 20, min_p 0.0,
  presence_penalty 0.0** (model card + Unsloth docs, fetched 2026-08-29). Greedy remains the
  correct choice for *controlled quant comparison* (zero sampling variance), but it means our
  absolute scores are **not comparable to any published number**. Both must be stated in the paper.
- **G17 — `reasoning_effort` is the documented thinking control and is UNTESTED here.** Unsloth
  documents `--chat-template-kwargs '{"reasoning_effort":"medium"}'` with `xhigh|medium|low|none`.
  We used `{"enable_thinking": false}`, which is validated to work but is not the documented knob.
  `reasoning_effort: none` should be compared against it before the paper claims a "non-thinking" mode.
- **G18 — Six quants in the Q4–Q6 band are UNTESTED**: `UD-Q4_K_S` 15.36 GB, `UD-Q4_K_M` 16.46 GB
  (tested historically, GGUF deleted), `UD-Q5_K_S` 18.67 GB, `UD-Q5_K_M` 19.77 GB,
  `UD-Q6_K_M` 23.09 GB, `UD-Q6_K_L` 24.19 GB. Sizes from the HF repo listing (2026-08-29).
- **G19 — We cannot validate against the official card with the benchmarks we run.** Qwen
  publishes **LiveCodeBench v6 90.3**, **SWE-bench Pro 61.7**, **Terminal Bench 2.1 (Terminus)
  73.0** for Qwen3.8-27B — and **does not publish HumanEval at all**. Our SWE-bench is
  **Verified**, a different benchmark from **Pro**, so 75.5 % is not comparable to 61.7. Any claim
  that a quant "respects the official benchmarks" needs LiveCodeBench v6 or SWE-bench Pro, neither
  of which is set up on this host.
- **G20 — No BF16/Q8 reference on disk → we cannot compute our OWN KL divergence.** The KLD table
  in this file is *cited from Unsloth*, not measured. BF16 is 54.7 GB (2 shards) and Q8_K_XL is
  31.46 GB; neither fits the 2×16 GB VRAM budget, and RAM is 14 GiB. KL vs a local reference is
  the most sensitive quant-ranking instrument available and is currently out of reach.
- **G21 — Q6_K_XL rebalance never completed.** Only `-ts 54,46` @196,608 was tried (failed to
  allocate); `58,42` and `62,38` were never reached before the abort. Its true rebalanced ceiling
  is unknown — and since `58,42` is what unlocked Q6_K, this is likely an under-measurement.
- **G22 — Statistical power is the binding limit on every accuracy claim.** HumanEval+ at n=164
  gives ±4.6 pts; the quants in this band differ by 1–3 pts. SWE-bench Verified at n=50 gives
  ±12 pts. **No task benchmark runnable on this host can cleanly rank these quants.** Perplexity /
  NLL on a code corpus is the only sensitive, cheap, monotonic discriminator we have.
- **G23 — 22 GB is reclaimable but not reclaimed.** `/srv/models` (110 GB, `/dev/sda`) is at 99 %
  with 1.2 GB free. `/srv/models/.hf-cache/models--unsloth--Qwen3.8-27B-NVFP4/blobs` holds a full
  22 GB duplicate of `/srv/engines/nvfp4` (sha256 `c473512c70ea…` matches). Deleting the cache copy
  would free the models disk for the G18 quants. **Not done — needs an explicit decision.**

## Remaining work

### Still needed for BOTH deliverables
Run P0 in this order — see TEST PLAN for exact commands and decision rules:
- [x] **E0** Environment truth pass — **DONE 2026-08-29**: `/srv/bench/env-manifest.json` written (image IDs, version strings, GGUF sha256+sizes). — P0
- [x] **E6** Split-mode reproducibility — **DONE 2026-08-29**: `-sm tensor` = CUDA illegal-memory-access on BOTH surviving images; **layer is the only reproducible mode**; `llama-dflash2:latest` requires `--entrypoint /app/llama-server`. Artifact: `/srv/bench/splitmode-repro.json`. — P0
- [x] **E1** Q6_K_XL actual max context — **DONE 2026-08-29**: **131,072 with MTP n2** (OOM serverlog-verified at 147,456+); 245,760 no-spec; 98,304 f16; f16+MTP <65,536. Layer-split KV-halving hypothesis REFUTED (q4_0 slope ~16.5 KiB/token/GPU = same as tensor). MTP costs ~114K tokens of window (vLLM 98K→48K finding reproduced). Artifact: `/srv/bench/q6-ceiling.json`. — P0
- [x] **E1b** (+E1b4 extension for Q4_K_XL) — **DONE 2026-08-29**: ceilings with MTP n2 + q4_0 + layer on surviving image: **Q4_K_XL 196,608** (262K/229K = init-hang, not OOM), **Q5_K_XL 163,840** (262K OOMs — the historical tensor-split 262K result does NOT reproduce), **IQ4_XS 262,144 ✓ full native window (39.5 tok/s, peak 14,474 MiB)**. Artifact: `/srv/bench/ctx-ceilings.json`. — P1
- [~] **E9a** vLLM NVFP4 context/speed/NIAH — **PARTIALLY DONE 2026-08-29, aborted by user request** (see EXECUTION LOG below for state + exact restart instructions). Core findings: nightly KV pool = **52,337 tokens @ gmu 0.97** → bootable ceiling **51,200**; gmu 0.99 impossible on 16 GB cards.
- [ ] **E2** KV fidelity f16 vs q4_0: paired greedy divergence + NLL ladder (G2) — P0 *(q8_0 dropped — broken on this stack)*
- [x] **E10** Provenance repairs — **DONE 2026-08-29**: G11 = champion needle runs are **KV-UNKNOWN** (launcher lost; labelled, not guessed); G12 = the "NVFP4 tensor+q4_0 @262,144" row was a **llama.cpp NVFP4-GGUF run** (weights since deleted, irreproducible); props-*.json citation convention set. Artifact: `/srv/bench/provenance-repairs.json`. — P0, no GPU
- [ ] **E3** Code-NIAH at 6 depths × 2 needle classes (G4) — P0 for Track A, P1 for Track B
- [ ] **E4** Score existing champion outputs — **40K only**, no long-context diffs exist (G1 partial) — P1, CPU-only
- [ ] **E5** Definitive accuracy-vs-context sweep (G1+G5+G6) — P1, overnight
- [ ] **E8** Speed + energy at the finally chosen config (G5) — P1
- [ ] **E7** Statistics & sampling protocol (G8+G10) — P2
- [ ] **E9** Cross-backend comparison at equal context, vLLM NVFP4 @98,304 (Track B) — P2
- [x] Perplexity protocol reconciliation — **DONE 2026-08-28** (OPTIMIZATION-LOG §13.72): NVFP4 re-scored on Protocol 1's exact 602 windows → PPL 6.7073 vs GGUF ladder 6.65–6.68 (+0.8 %). The two legacy runs also used **different corpus files** (`/srv/bench/corpus/` vs `/srv/bench/perplexity/`) — tokenizer hypothesis disproven.
- [x] Bootstrap CIs missing for: `mtp-Q6_K_XL (thinking)`, `dflash-IQ4_XS (thinking)`, `dflash-Q4_K_XL (thinking)`, and `verified50` — **completed 2026-08-28** (verified50: 75.51 [63.27, 87.76], n=49, source per-instance report.json).
- [x] Fix `collect-metrics.py` to sum concatenated eval.log batches (defect 1 above) — done 2026-08-28 via shared `swebench_agg.py`; ledger refreshed with corrected numbers.
- [x] Energy per benchmark — **DONE 2026-08-29** (OPTIMIZATION-LOG §13.73): 1 Hz power-log integration over covered windows (telemetry starts 2026-08-27T16:21Z — earlier benchmarks uncoverable, listed explicitly). Headlines: spec decoding cuts J/tok ~2–2.5× (Q6 no-spec 11.78 → DFlash2 4.79); **IQ4_XS DFlash2 = 3.70 J/tok** (best); HumanEval thinking runs cost 288–564 Wh each; nvfp4-ppl retry tax 377 Wh GPU / 1.18 kWh system across 22 failed startups. Artifact: `/srv/bench/energy-per-benchmark.json`.
- [x] KL divergence — **DONE 2026-08-29** (OPTIMIZATION-LOG §13.74): cited Unsloth published per-quant numbers with archived evidence (`/srv/bench/kl-divergence.json`, `/srv/bench/kl-evidence/`). NVFP4 KLD table (text, verbatim: zh 0.01628/93.55 %, code 0.02600/96.68 %, refgen 0.03993/94.46 %, chat 0.05818/92.15 %); GGUF Dynamic-v3 per-quant KLD published as figures (read: IQ4_XS ≈ 0.019, Q4_K_XL ≈ 0.0085, Q5_K_XL ≈ 0.0038, Q6_K_XL ≈ 0.0016). Published KL ranking **agrees** with our measured PPL ranking; NVFP4's 92–97 % top-1 recovery brackets UD-IQ4_XS's ≈94 %, consistent with NVFP4 PPL 6.7073 ≈ IQ4_XS 6.6839.
- [ ] **Track A deliverable** — the single pinned config for this machine, produced by the TEST PLAN's decision procedure (accuracy → context → tok/s)
- [ ] **Track B deliverable** — the neutral technical report/article. Blocked on the same experiments, but framed per-objective with CIs and reproducibility caveats, never on machine-specific preference
- [ ] The paper/report itself — **besides the E0–E10 gap-filling experiments above** (see OPEN GAPS + PROPOSED EXPERIMENTS; the long-context config recommendation is CONDITIONAL on E1+E2).

### Irrecoverable data
- Per-config server timings for thinking mtp-IQ4_XS / mtp-Q4_K_XL / mtp-Q5_K_XL (containers destroyed before `docker logs`)
- Exact reproducibility of 2026-08-20 ablations (image + models gone)
- Q3_K_XL and Q4_K_M GGUFs not in /srv/models

## Artifacts

- **Ledger**: https://claude.ai/code/artifact/eea1a677-9b88-4bf2-b9c0-3ec861915079
- **Benchmark Matrix**: https://claude.ai/code/artifact/4ddbefa0-0626-4b39-989f-70ec38ce57aa

## User context

The user (simoeshz@gmail.com) operates from a Mac Studio, SSHing into multivac. Sessions often run from the Mac-side Claude Code instance. This Claude Code session runs directly on multivac. Communication is often in Portuguese but technical content is in English.

## Important rules

1. **Never blind-prune Docker images** while the suite has pending work — `docker image prune -a` would delete critical benchmark images.
2. **Never mix perplexity protocols** in one comparison table.
3. **Never delete test data** — excluded data is retained and labeled, never removed.
4. **Always capture `docker logs`** before removing any llama.cpp container.
5. **PAPER-REFERENCES.md is the canonical reference** — all findings, decisions, and data provenance live there. Always check it first.
