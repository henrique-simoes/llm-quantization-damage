# Technical Report — Documentation References Log

## vLLM NVFP4 + FP8 KV Cache (config justification)

### Empirical finding (this deployment)
- vLLM v0.27.1 auto-selects `kv_cache_dtype=torch.float8_e4m3fn` for the NVFP4 checkpoint on Blackwell (sm120, RTX 5060 Ti), via FlashInfer backend. Observed in engine startup logs.
- Checkpoint `config.json` -> `quantization_config.kv_cache_scheme`: {num_bits: 8, type: float, strategy: tensor, symmetric: true, dynamic: false, observer: static_minmax}. => Static per-tensor FP8 (E4M3) KV scales are CALIBRATED INTO THE CHECKPOINT by Unsloth/NVIDIA ModelOpt. vLLM applies them automatically.
- Model native context: max_position_embeddings = 262144.
- On 2x RTX 5060 Ti 16GB (TP=2): NVFP4 weights ~11.3 GiB/GPU; FP8 KV cache capacity = 113,322 tokens (3.46x concurrency @ 32K). FP16 KV would be ~half (~56K tokens).

### Documentation sources
- vLLM Quantized KV Cache docs: https://docs.vllm.ai/en/latest/features/quantization/quantized_kvcache/
  - "No calibration (default scales): All quantization scales are set to 1.0" when kv_cache_dtype=fp8 and no calibration provided. (Our checkpoint DOES provide calibration.)
  - Per-attention-head quantization only with Flash Attention backend.
- vLLM Blog, "The State of FP8 KV-Cache and Attention Quantization in vLLM" (2026-04-22): https://vllm.ai/blog/2026-04-22-fp8-kvcache
- NVIDIA/vLLM recommended Qwen3 NVFP4 production recipe: kv-cache-dtype fp8, attention-backend flashinfer, moe-backend marlin, max-model-len 262144, speculative mtp. (via nvidia/Qwen3.6-35B-A3B-NVFP4 model card + community recipes)
  - https://huggingface.co/nvidia/Qwen3.6-35B-A3B-NVFP4
- NVFP4 format background (E2M1 + dual-level FP8 micro-block / FP32 per-tensor scaling): NVIDIA NVFP4 overview.
  - https://arunksingh16.medium.com/nvidia-nvfp4-quantization-blackwell-and-the-path-to-production-inference-12407e14e084
- Unsloth Dynamic NVFP4 guide: https://unsloth.ai/docs/basics/nvfp4
- Claim to cite carefully: "FP8 KV cache calibration allows ~2x longer context lengths" and ">99% accuracy preservation on MMLU/HellaSwag/GSM8k" — verify primary source before citing as fact.

### Config decision (SWE-bench + HumanEval, vLLM NVFP4)
- Use DOCUMENTED process: FP8 KV cache (checkpoint-calibrated), FlashInfer attention, tensor-parallel-size 2, enforce-eager (fits 2x16GB).
- max-model-len set near full FP8 KV capacity to (a) follow recipe intent and (b) prevent SWE-bench agent context-window overflow (which truncated an 8K run to an empty patch).
- KV precision differs from llama.cpp runs (FP16 KV default) — document as an inherent backend difference, not a confound we introduced.

_Last updated: 2026-08-26_

## vLLM speculative decoding support for Qwen3_5 NVFP4 (verified in-container, v0.27.1)
- Architecture of checkpoint: Qwen3_5ForConditionalGeneration (model_type qwen3_5), 64 layers, multimodal (vision_config present, language_model_only flag).
- Checkpoint SHIPS MTP weights: 15 tensors (mtp.fc.weight, mtp.layers.0.*). => native MTP available, no separate draft model.
- vLLM registry (model_executor/models/registry.py) includes:
  - Qwen3_5MTP -> (qwen3_5_mtp, Qwen3_5MTP) and Qwen3_5MoeMTP  => MTP supported for THIS arch.
  - DFlashDraftModel -> (qwen3_dflash, DFlashQwen3ForCausalLM) => DFlash supported in vLLM (needs a vLLM/HF-format DFlash DRAFT model; config.py note: "DFlash needs a non-causal-capable backend like FLASH_ATTN").
  - Also present: qwen3_eagle3 (EAGLE3), qwen3_dspark.
- vLLM SpeculativeConfig methods (config/speculative.py) Literal includes: mtp, qwen3_5_mtp, eagle, eagle3, dflash, ngram, draft_model, extract_hidden_states.
- MTP invocation (docs.vllm.ai/en/latest/features/speculative_decoding/mtp/): speculative-config method=mtp, num_speculative_tokens=1 good default. MTP only works for families vLLM supports (qwen3_5 IS supported).
- FAIRNESS: llama.cpp used "DFlash2" (draft-dflash + GGUF drafter Qwen3.8-27B-DFlash2-Q4_K_M). vLLM has "dflash" -- must confirm same generation/algorithm and source a vLLM-loadable DFlash draft (GGUF drafter NOT loadable by vLLM).
- LOSSLESS under greedy (temp=0): accepted tokens == target model greedy tokens => pass@1 accuracy unchanged vs no-spec; only SPEED (tok/s, TTFT/TPOT) differs. Accuracy numbers reusable; only speed re-measured per method.
- Docs: https://docs.vllm.ai/en/latest/features/speculative_decoding/mtp/

## Community / documented setups for MTP + DFlash2 on Qwen3-27B NVFP4 (for correct comparison)
### Reference deployment (closest to ours): adrienbrault/qwen3.8-27b-rtx5090
- Qwen3-27B NVFP4 (W4A4) on ONE RTX 5090 32GB, vLLM + LMCache, MTP spec-decode.
- MTP ns=4 (num_speculative_tokens). Flags noted: --no-async-scheduling, --mamba-cache-mode align.
- kv-cache-dtype: they push nvfp4 KV (even more aggressive than fp8); gpu-memory-utilization 0.93 (0.95 OOMs on single card).
- max-model-len up to 262144. Decode 124/183 t/s single-stream; 511/639 aggregate at concurrency 4/8. Prefill 12.8K t/s @8K. SWE-Bench Verified 66.2%.
- URL: https://github.com/adrienbrault/qwen3.8-27b-rtx5090
### MTP community norm
- num_speculative_tokens 2-4 (adrienbrault 4; NVIDIA/others 2-3). llama.cpp used n-max 2.
- Uses in-checkpoint MTP weights (our unsloth NVFP4 has them). No extra model. Works on STOCK vllm-openai:latest.
### DFlash2 community norm (z-lab / incoai)
- vLLM config: method=dflash, model=incoai/Qwen3.8-27B-DFlash2 (or z-lab/Qwen3.8-27B-DFlash2), num_speculative_tokens=7. llama.cpp used n-max 4.
- Draft model = 2B params, BF16 (~4-5GB download). NOT NVFP4.
- DFlash2 = block-diffusion drafter (predicts a whole block per pass, keeps top candidates, lightweight selector). Speedups 2.67x-3.43x by concurrency.
- **vLLM support requires a PR/nightly build** (e.g. git+.../pull/52816/head or #40898/#38300). Stock v0.27.1 has qwen3_dflash.py + registry entry + config Literal "dflash", but speculators-config parsing landed via PR -> MUST verify stock image actually runs it, else need a newer vLLM Docker image.
- URLs: https://huggingface.co/z-lab/Qwen3.8-27B-DFlash2 , https://huggingface.co/incoai/Qwen3.8-27B-DFlash2 , https://github.com/vllm-project/vllm/pull/38300 , https://regolo.ai/train-run-dflash-speculative-decoding-vllm/
### DSpark (bonus, out of current scope): Qwen3.8-27B-DSpark-NVFP4 drafter, 88.5->180.3 t/s single RTX 5090, byte-identical. (qwen3_dspark.py in vLLM.)
### Fairness note
- For apples-to-apples with llama.cpp, match speculative depth per method: MTP ns=2 (llama n-max 2), DFlash2 ns=4 (llama n-max 4). Optionally ALSO report community-optimal (MTP 4, DFlash 7).
- Spec-decode is lossless under greedy => accuracy identical to no-spec; only SPEED differs.

## vLLM image decision for spec-decode (MTP + DFlash2)
- Stock multivac image vllm/vllm-openai:latest = v0.27.1 -> has DFlash(v1) only, NOT DFlash2. Verified: registry lacks DFlash2DraftModel; zero "DFlash2" strings in package.
- DFlash2 = vLLM PR #52816 (SubSir, "DFlash2: local convolution + candidate selector"), MERGED to main 2026-08-21. NOT in any stable release as of 2026-08-26. Requires main/nightly build.
  - PR: https://github.com/vllm-project/vllm/pull/52816 ; docs: https://docs.vllm.ai/en/latest/api/vllm/v1/worker/gpu/spec_decode/dflash2/
  - Inco AI DFlash2 blog: https://inco.ai/blog/dflash2/ ; draft models: z-lab/Qwen3.8-27B-DFlash2 (3.6GB BF16, arch DFlash2DraftModel), incoai/Qwen3.8-27B-DFlash2
- DECISION (user approved): pull newer vLLM Docker image = nightly (tracks main, includes #52816). Run ALL vLLM spec runs on ONE consistent image for fair speed comparison. Pin exact image digest + vLLM __version__/commit for reproducibility in paper.
- Official vLLM recipe (recipes.vllm.ai/Qwen/Qwen3.8-27B) CONFIRMS our base config:
  - MTP: vllm serve unsloth/Qwen3.8-27B-NVFP4 --tensor-parallel-size 2 --max-model-len 262144 --kv-cache-dtype fp8 --reasoning-parser qwen3 --enable-auto-tool-choice --tool-call-parser qwen3_coder  + speculative-config method=mtp num_speculative_tokens=3
  - DFlash2: speculative-config method=dflash model=incoai/Qwen3.8-27B-DFlash2 num_speculative_tokens=7
  - (We cap max-model-len at 98304 due to 2x16GB KV ceiling, not 262144.)
- Depth plan (user: both matched+optimal): MTP ns=2 (match llama n-max2) & ns=4 (optimal); DFlash2 ns=4 (match llama n-max4) & ns=7 (optimal). Recipe/community MTP default is 3 (note in paper).
- Accuracy note: spec-decode lossless under greedy -> HumanEval pass@1 unchanged; existing v0.27.1 accuracy (85.4/84.1) reused, version documented. Speed table measured on nightly across all vLLM configs.

## FINDING: DFlash2-on-vLLM NOT VIABLE on 2x RTX 5060 Ti 16GB (with NVFP4 base)
- Deterministic CUDA OOM at draft-workspace allocation: "Tried to allocate 1.19 GiB, 1.05 GiB free, 14.42 GiB in use" — identical across gpu-memory-utilization {0.78,0.80,0.85,0.97}, num_speculative_tokens {2,4}, max-model-len {3072,4096,8192,16384}, and with PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True.
- Memory budget per GPU (15.48 GiB usable): NVFP4 weights 11.3 GiB + DFlash2 BF16 2B draft ~3.1 GiB = 14.42 GiB, leaving 1.05 GiB; fixed draft workspace (DFlash2 local-conv + candidate-selector buffers) needs 1.19 GiB -> OOM by ~140 MiB. gpu-memory-utilization does NOT govern the draft (loaded additionally), so lowering it does not help.
- WHY llama.cpp FITS DFlash2 but vLLM does not (key backend contrast for paper):
  1. Draft precision: llama.cpp drafter = Qwen3.8-27B-DFlash2 GGUF Q4_K_M (~1.5 GiB) vs vLLM draft = z-lab/incoai BF16 (~3.6 GiB). ~2.4 GiB heavier.
  2. Parallelism: llama.cpp -sm layer (pipeline/layer-split) packs main-model layers across GPUs leaving headroom; vLLM tensor-parallel shards each layer but replicates/loads the full BF16 draft workspace per worker.
  3. No public NVFP4/FP8 DFlash2 draft exists for this base -> can't shrink the vLLM draft.
- Untested last resort: vLLM pipeline-parallel (PP=2) placement — but vLLM spec-decode + PP support is limited/uncertain; likely dead-end.
- CONCLUSION: DFlash2 comparison stays llama.cpp-only (fits via Q4 GGUF draft + layer-split). vLLM speculative comparison = MTP (ns2, ns4) vs no-spec. This memory contrast is itself a reportable result.

## vLLM NVFP4 speculative-decoding SPEED table (nightly 0.26.1rc1.dev1219+g46638857f, 2x RTX 5060 Ti 16GB, TP=2, fp8 KV, enforce-eager, greedy, 3-run median, single-stream, 1024-tok gen)
| Config | decode tok/s | speedup | acceptance | TTFT s | TPOT ms | avg power W | J/tok | peak VRAM MiB | max ctx |
|---|---|---|---|---|---|---|---|---|---|
| No-spec  | 12.44 | 1.00x | -     | 0.31 | 83.8 | 126.1 | 9.96 | 15424 | 98304 |
| MTP ns=2 | 28.11 | 2.26x | 0.709 | 0.46 | 86.2 | 132.7 | 4.57 | 15528 | 40960 |
| MTP ns=4 | 41.21 | 3.31x | 0.559 | 0.51 | 70.5 | 148.4 | 3.60 | 15566 | 40960 |
| DFlash2  | N/A - deterministic CUDA OOM on 2x16GB (2B BF16 draft + NVFP4 weights); llama.cpp-only | | | | | | | | |
Notes:
- decode_tok_s medians; MTP4 raw runs [32.54,41.21,41.24] (first = warmup outlier, median robust). MTP2 [25.16,29.02,28.11]. NOSPEC [12.44,12.44,13.26].
- Acceptance rate = accepted/draft draft-tokens (vLLM /metrics). Falls with depth (0.709@ns2 -> 0.559@ns4) but net throughput rises.
- Energy: MTP halves J/token vs no-spec (9.96 -> 4.57 -> 3.60) despite higher instantaneous power, because generation finishes faster.
- Context ceiling: no-spec 98K; MTP ~48K (draft head shrinks KV); measured/run at 40960 (>SWE 32K need). DFlash2 could not load at any ctx.
- Speed probe: identical AVL-tree prompt, max_tokens=1024, temp=0, seed=20260825. Prompt ~92 tok.
- llama.cpp MTP/DFlash2 speed to be measured with matching probe for cross-backend table.

## REMEDIATION: vLLM SWE-bench config (autonomous, 2026-08-27)
- Attempted vLLM SWE-bench with MTP(ns=2) @ max-model-len 40960. One agentic trajectory (thinking ON) exceeded ctx: ContextWindowExceededError "maximum context length 40960, value=40961". MTP's draft head lowers the fp8-KV ceiling to ~48K (vs 98K no-spec), so long SWE trajectories do not fit.
- FIX: run vLLM SWE-bench at NO-SPEC @ max-model-len 98304 (fits all 3 trajectories). Justification: under greedy decoding (temp=0) speculative decoding is LOSSLESS -> the resolve rate is identical to MTP; only speed differs, and MTP/no-spec SPEED is measured separately via the throughput probe. So SWE resolve on no-spec == SWE resolve on MTP.
- MTP(ns=2) partial run (2/3 instances that fit under 40960) kept as supplementary at swebench-results/thinking/vllm-NVFP4-mtp/. Definitive 3/3 run at swebench-results/thinking/vllm-NVFP4/ (no-spec, 98K).
- This is itself a documented finding: MTP trades context headroom for speed; on 2x16GB the vLLM MTP config cannot serve full-length agentic SWE trajectories, whereas no-spec (98K) and llama.cpp (32K, layer-split) can.

## RESULTS UPDATE (2026-08-27)
### vLLM NVFP4 SWE-bench (no-spec @98K, thinking ON) -- DEFINITIVE
- Instances completed 3/3, RESOLVED 2/3, unresolved 1, errors 0.
- Patches: astropy__astropy-12907=504 (resolved), django__django-10880=713, django__django-10973=2862.
- Config: no-spec chosen because MTP ctx ceiling (~48K) < some trajectories (overflowed @40961). Resolve is lossless-identical to MTP under greedy. Result dir: swebench-results/thinking/vllm-NVFP4/.
- MTP(ns2) partial (context-limited): only 1/3 usable, astropy resolved. dir: vllm-NVFP4-mtp/. Supplementary only.

### llama.cpp Q4_K_XL speed (same probe, 3-run median) -- nospec validated
- nospec: decode 23.02 tok/s, TTFT 0.43s, TPOT 43.4ms, avg_power 201.9W, peak_vram 10062 MiB, J/tok 8.77.
- CROSS-BACKEND FINDING: llama.cpp nospec (23.0 t/s) ~1.85x faster than vLLM nospec (12.44 t/s), at lower VRAM (10.1 vs 15.4 GiB) but higher power (202 vs 126 W). Likely vLLM --enforce-eager (no CUDA graphs, required to fit 2x16GB) costs decode throughput. mtp_n2 + dflash2_n4 measuring next.

### ORCHESTRATION FIXES (lessons)
- BUG1: chained phases via a client-side Monitor -> torn down on session cycle -> Phase2/3 never launched, GPU idle ~5h (07:12-12:30 UTC). FIX: single detached on-server chain script (phase23-chain.sh) survives client cycles.
- BUG2: docker entrypoint wrong. TRUTH via inspect: llamacpp-mtp ENTRYPOINT=/app/llama-server (pass NO prefix); llama-dflash2 ENTRYPOINT=/app/llama-cli (must --entrypoint /app/llama-server). Fixed in phase2-llamacpp-speed.sh AND run-humaneval-thinking-v2.sh (which had same latent bug).

## CROSS-BACKEND SPEED TABLE (complete, same probe, 2x RTX 5060 Ti 16GB, greedy, 3-run median, 1024-tok gen)
| Backend | Config | decode tok/s | speedup(own nospec) | acceptance | mean_accept_len | TTFT s | avg_power W | peak_vram MiB | J/tok |
|---|---|---|---|---|---|---|---|---|---|
| vLLM NVFP4 | no-spec | 12.44 | 1.00 | -     | -    | 0.31 | 126.1 | 15424 | 9.96 |
| vLLM NVFP4 | MTP ns2 | 28.11 | 2.26 | 0.709 | -    | 0.46 | 132.7 | 15528 | 4.57 |
| vLLM NVFP4 | MTP ns4 | 41.21 | 3.31 | 0.559 | -    | 0.51 | 148.4 | 15566 | 3.60 |
| llama.cpp Q4_K_XL | no-spec | 23.00 | 1.00 | - | - | 0.43 | 207.0 | 10062 | 9.00 |
| llama.cpp Q4_K_XL | MTP n2 | 32.69 | 1.42 | 0.728 | 2.46 | 0.44 | 214.1 | 11014 | 6.55 |
| llama.cpp Q4_K_XL | DFlash2 n4 | 38.51 | 1.67 | 0.714 | 3.86 | 0.45 | 218.2 | 11356 | 5.67 |
| vLLM NVFP4 | DFlash2 | INFEASIBLE (OOM on 2x16GB) | | | | | | | |
Notes:
- vLLM MTP scales harder (3.31x) vs llama.cpp (1.42-1.67x): vLLM --enforce-eager cripples baseline -> more spec headroom. Best absolute ~tie: vLLM MTP-ns4 41.2 vs llama.cpp DFlash2-n4 38.5.
- MTP acceptance cross-validates across engines (llama 0.728 vs vLLM 0.709 @ depth 2).
- DFlash2 wins on llama.cpp via longer mean accepted length (3.86 vs 2.46).
- llama.cpp TPOT unreliable (batches SSE chunks); use decode tok/s. vLLM VRAM higher (NVFP4 11GB/GPU); llama.cpp Q4_K_XL ~5GB/GPU + drafter.
- llama.cpp draws more power (~207-218W) but lower energy/token than vLLM nospec; vLLM MTP-ns4 best J/tok (3.60).

## HumanEval+ thinking-v2 results (llama.cpp, greedy, reasoning ON, max_tokens 4096)
| config | HumanEval pass@1 | HumanEval+ pass@1 | empty% | status |
|---|---|---|---|---|
| mtp-IQ4_XS | 86.6 | 86.0 | 12.8 | DONE (5257s) |
| mtp-Q4_K_XL | running | | | |
| mtp-Q5_K_XL | queued | | | |
| mtp-Q6_K_XL | queued | | | |
| dflash-IQ4_XS | queued | | | |
| dflash-Q4_K_XL | queued | | | |
Note: ~13% empty is normal for thinking-mode (matches vLLM NVFP4 12.8%); counts as fail in pass@1. Validation-gate bug fixed (quoted-heredoc \$jsonl + threshold has_code>=130).
vLLM NVFP4 (done): HumanEval 85.4 / HumanEval+ 84.1, empty 12.8%.

## TELEMETRY / POWER MEASUREMENT INFRASTRUCTURE (2026-08-27)
All containerized (docker compose at /srv/bench/telemetry/docker-compose.yml). NOTHING installed on host.
| service | port | role |
|---|---|---|
| Prometheus | 9091 | TSDB, retention 180d / 6GB cap, PromQL windowed energy export (9090 reserved for vLLM) |
| node_exporter | 9100 | CPU/RAM/disk/net + RAPL cumulative energy counters (node_rapl_package_joules_total) |
| nvidia_gpu_exporter | 9835 | per-GPU power/util/mem/temp; image tag MUST be :latest (v1.2.0 panics on new driver: clocks_event_reasons_* fqName with space -> invalid metric name) |
| cAdvisor | 8081 | per-container attribution (8080 reserved for llama.cpp) |
| Grafana | 3000 | dashboards (host dir must be chown 472:472) |
| Netdata | 19999 | per-second full-system telemetry, gpus:all for native GPU collector |
Plus lightweight redundant CSV logger: /srv/bench/power-logger.sh -> /srv/bench/power-log.csv (1 Hz; GPU per-device W, CPU RAPL-derived W, cumulative Wh; resumes across restarts via /srv/bench/.power-logger.state).
MEASUREMENT NOTES for paper:
- RTX 5060 Ti (consumer) has NO cumulative GPU energy counter (nvidia-smi total_energy_consumption unsupported) -> GPU energy is INTEGRATED from 1 Hz power samples. CPU energy uses exact RAPL cumulative counters (root-only; read via sudo).
- No BMC/IPMI on this consumer board -> true wall power is NOT measurable. est_system_w = GPU + CPU_pkg + PLATFORM_W(45W documented constant estimate for mobo/RAM/NVMe/fans/PSU loss). Report GPU and CPU as measured; label system total as an estimate.
- Disk constraint: only ~21GB free -> Prometheus capped at 6GB/180d.
- Retired redundant GPU-only logger (engines/power-logger.sh); its 5.6MB data preserved.

## HISTORICAL POWER DATA + DATA-INTEGRITY WARNING (2026-08-27)
- OS/root fs created 2026-08-20 02:09 UTC; boot 2026-08-20 12:33. No power logging existed before 2026-08-25 11:23 -> NO data for first ~4.5 days. RAPL cannot fill this gap (counter wraps at 65532610987 uJ, ~50 min at idle).
- MEASURED window 2026-08-25 11:23 -> 2026-08-27 16:30 UTC (53.1 h, 180,879 samples @1Hz, GPU only):
  - GPU pair average 110.4 W (min 19.4, max 358.3); GPU energy 5.828 kWh
  - idle (<60W) 44% of time @ avg 24.3 W; busy (>=150W) 33% of time @ avg 213.1 W
- Whole-machine ESTIMATE (not measured, no BMC): GPU 110.4 + CPU ~20 + platform ~45 = ~175 W avg => ~9.3 kWh over the 53.1 h. Naive extrapolation to full 7.6-day OS life ~32 kWh -- INDICATIVE ONLY (unmeasured 4.5 days assumed similar; unverifiable).
- *** DATA INTEGRITY BUG in legacy file engines/dflash2-results/power-dflash2-bench.csv ***
  Header says: timestamp,gpu0_power_w,gpu1_power_w,gpu0_temp_c,gpu1_temp_c
  ACTUAL layout: timestamp,gpu0_power,gpu0_temp,gpu1_power,gpu1_temp  (cols 2..5 shifted; trailing comma)
  Cause: legacy logger did `nvidia-smi --query-gpu=power.draw,temperature.gpu | tr "\n" ","` (interleaves per-GPU pairs) but wrote a header assuming grouped columns.
  Consequence: summing cols 1+2 adds POWER+TEMPERATURE -> physically impossible values. Any analysis of this file MUST use cols 1 and 3 for power. New /srv/bench/power-log.csv is correctly labeled.
HumanEval+ thinking-v2 running results: mtp-IQ4_XS 86.6/86.0 (12.8% empty, 5257s); mtp-Q4_K_XL 87.8/86.0 (12.2% empty, 9214s). vLLM NVFP4 85.4/84.1 (12.8% empty). Empty rate tightly clustered 12.2-12.8% across ALL backends+quants => property of thinking mode @4096 max_tokens, not backend/quant specific.

## ENGINE BUILD PROVENANCE -- DFlash2 (IMPORTANT, 2026-08-27)
Two DIFFERENT llama.cpp-family images exist on multivac; they are NOT the same codebase:
| image | version | build | commit | built | used in our runs? |
|---|---|---|---|---|---|
| llama-dflash2:latest | 0.1.2-dev | 50 | f7aadef | 2026-08-25 11:12 | YES -- ALL DFlash2 results |
| llamacpp-dflash2-pr27342:1deefcc-sm120-cuda128-abi | 0.2.0-dev | 10588 | 70adb1b4c | 2026-08-23 06:11 | NO |
- Build 10588 matches upstream llama.cpp numbering => the pr27342 image is upstream llama.cpp + PR #27342.
- Build 50 / v0.1.2-dev indicates a separate research fork (not upstream), provenance not self-documented in image labels (labels only show base ubuntu/CUDA).
- ALL DFlash2 numbers reported so far (speed 38.51 tok/s @ accept 0.714; SWE-bench thinking dflash-IQ4_XS 3/3 and dflash-Q4_K_XL 3/3; upcoming HumanEval+ dflash configs) come from llama-dflash2:latest (fork, commit f7aadef).
- REPRODUCIBILITY RISK: a technical report citing "DFlash2 in llama.cpp" should pin an identifiable upstream reference (PR #27342, commit 70adb1b4c) or explicitly state the fork + commit. Otherwise reviewers cannot reproduce.
- OPEN DECISION: (a) keep fork results and document commit f7aadef explicitly, (b) re-run DFlash2 configs on the pr27342 upstream image for citability, or (c) run both and compare (also validates the fork).
- Also note: NO git operations were performed by this session; both images pre-existed (Aug 23 and Aug 25), and the only image pulled was vllm/vllm-openai:nightly (user-authorized).

## UPSTREAM DFlash2 STATUS (checked 2026-08-27 ~17:15 UTC)
- llama.cpp PR #27342 "spec : add DFlash2 support (local convolution + candidate selector)": MERGED 2026-08-27T17:05:58Z by ngxson (Xuan-Son Nguyen), but into staging branch xsn/dflash2 -- NOT master. Merge commit 4a6ad487a6f7c615a5d5662be9248694a9ac1254. URL https://github.com/ggml-org/llama.cpp/pull/27342
- Follow-up PR #27816 (xsn/dflash2 -> master), created 2026-08-27T17:08:35Z: OPEN + DRAFT, REVIEW_REQUIRED, MERGEABLE, +538/-24, 2 commits. => DFlash2 is NOT in llama.cpp master as of this writing; master contains no dflash sources.
- xsn/dflash2 branch HEAD at check time: 4e2f54f8f (past the merge commit).
- CAVEAT: local image llamacpp-dflash2-pr27342 was built 2026-08-23 from commit 70adb1b4c = PRE-MERGE PR state, already stale vs merged code. So it is NOT equivalent to the merged upstream result either.
- Therefore three candidate provenances for DFlash2 numbers: (a) fork llama-dflash2:latest v0.1.2-dev build50 f7aadef [ALL current results], (b) stale pre-merge PR build 70adb1b4c, (c) fresh build from merged xsn/dflash2 (4a6ad487/4e2f54f8f) -- (c) would require compiling llama.cpp inside Docker.
DECISION (user, 2026-08-27): Use the FORK build for all DFlash2 results and document precisely.
  -> Engine: llama-dflash2:latest, llama.cpp-family v0.1.2-dev, build 50, commit f7aadef.
  -> Paper must state: DFlash2 results obtained with this build; upstream DFlash2 (PR #27342) merged into llama.cpp staging branch xsn/dflash2 on 2026-08-27T17:05:58Z (merge commit 4a6ad487), with landing in master pending draft PR #27816 at time of writing. No results were produced from the upstream build.
  -> No re-runs required; Phase 3 dflash-IQ4_XS / dflash-Q4_K_XL already configured with this image.

# ============================================================
# COMPREHENSIVE ADDENDUM (2026-08-27) -- fills gaps: hardware, versions,
# checkpoints, perplexity, ALL non-thinking results, SGLang, data hygiene
# ============================================================

## HARDWARE & PLATFORM (multivac)
- GPUs: 2x NVIDIA GeForce RTX 5060 Ti 16GB (Blackwell, sm120), 15.48 GiB usable each, power limit 180 W each
- CPU: AMD Ryzen 5 8500G (12 threads) -- RAPL energy counters exposed via /sys/class/powercap/intel-rapl* (root-only)
- System RAM: 14 GiB  <-- CONSTRAINT: vLLM disabled checkpoint auto-prefetch ("checkpoint 21.81 GiB exceeds 90% of available RAM 6.13 GiB")
- NVIDIA driver 595.84, CUDA 13.2
- No BMC/IPMI -> wall power not measurable (see TELEMETRY section)
- Root fs created 2026-08-20 02:09 UTC; disk 218G total, ~21G free at 2026-08-27
- Multi-GPU: llama.cpp uses -sm layer (pipeline; -sm row FAILS on 5060 Ti); vLLM uses tensor-parallel-size 2

## ENGINE / TOOL VERSION MATRIX (from engines/VERSOES.txt 2026-08-23 + later checks)
| engine | version | image id / build | used for |
|---|---|---|---|
| vLLM (stable) | 0.27.1 | sha256:0a51ea5b4ae2... | NVFP4 HumanEval+ thinking (85.4/84.1), NVFP4 SWE-bench |
| vLLM (nightly) | 0.26.1rc1.dev1219+g46638857f | vllm/vllm-openai:nightly | ALL spec-decode speed runs (MTP ns2/ns4), DFlash2 attempts |
| SGLang | 0.5.18 | sha256:9e148f5ac788... | ATTEMPTED, FAILED (see SGLANG section) |
| llama.cpp (upstream+PR27342) | 0.2.0-dev build 10588 commit 70adb1b4c | llamacpp-dflash2-pr27342:1deefcc-sm120-cuda128-abi | NOT used for results |
| llama.cpp MTP | (llamacpp-mtp:latest, built 2026-08-25 22:35) | feb0231976b6 | ALL llama.cpp MTP + no-spec runs |
| llama.cpp DFlash2 fork | 0.1.2-dev build 50 commit f7aadef | llama-dflash2:latest (22bb8b7fed8b) | ALL DFlash2 results (user-approved provenance) |
| llama-perplexity | (llama-perplexity:latest, 2026-08-25 22:29) | a45d7af7c94e | perplexity runs |
| evalplus | venv /srv/bench/.venv-evalplus (py3.14) | patched: base.py max_new_tokens 768->4096; codegen.py line88 impl=impl or "" | HumanEval+ |
| mini-swe-agent | 2.4.6 | venv /srv/bench/.venv-swebench | SWE-bench |
| litellm provider | hosted_vllm/ prefix; api_base in model_kwargs | | SWE-bench routing |

## MODEL CHECKPOINTS & PROVENANCE (rule: only Qwen official / Unsloth / bartowski)
| file | bytes | notes |
|---|---|---|
| Qwen3.8-27B-UD-IQ4_XS.gguf | 14,252,845,984 | Unsloth dynamic |
| Qwen3.8-27B-UD-Q4_K_XL.gguf | 17,559,178,144 | Unsloth dynamic |
| Qwen3.8-27B-UD-Q5_K_XL.gguf | 20,876,938,144 | Unsloth dynamic |
| Qwen3.8-27B-UD-Q6_K_XL.gguf | 25,299,061,664 | Unsloth dynamic |
| dflash2/Qwen3.8-27B-DFlash2-Q4_K_M.gguf | 1,143,006,752 (1.1 GB) | DFlash2 drafter (llama.cpp) |
| unsloth/Qwen3.8-27B-NVFP4 (HF) | ~22 GB | vLLM; arch Qwen3_5ForConditionalGeneration, 64 layers, ships 15 MTP tensors, kv_cache_scheme fp8 static |
| z-lab/Qwen3.8-27B-DFlash2 (HF) | 3.6 GB BF16 | vLLM DFlash2 drafter -- DOWNLOADED but UNUSABLE (OOM) |
- Q3_K_XL was also tested (non-thinking) but the GGUF is not currently in /srv/models.

## PERPLEXITY (WikiText-2, llama.cpp, llama-perplexity:latest) -- COMPLETE
| quant | PPL | +/- |
|---|---|---|
| IQ4_XS | 6.6839 | 0.04133 |
| Q4_K_XL | 6.6617 | 0.04116 |
| Q5_K_XL | 6.6556 | 0.04114 |
| Q6_K_XL | 6.6511 | 0.04111 |
- Monotonic improvement with bit-width, as expected. CIs overlap between adjacent quants -> differences are small relative to uncertainty; state this in the paper.
- NOT MEASURED: NVFP4 perplexity (llama-perplexity is GGUF-only) and DFlash2/MTP perplexity.
  NOTE: speculative decoding is LOSSLESS under greedy -> MTP/DFlash2 perplexity == base quant perplexity; no separate runs needed. Document this rather than running them.

## NON-THINKING HumanEval+ RESULTS (greedy, temp 0) -- COMPLETE, with hygiene
| config | HumanEval | HumanEval+ | empty | verdict |
|---|---|---|---|---|
| Q3_K_XL | 84.1 | 81.7 | 0% | CLEAN |
| IQ4fix (IQ4_XS) | 90.2 | 87.8 | 0% | CLEAN |
| Q5_K_XL | 93.3 | 90.9 | 0% | CLEAN |
| Q6Kfix (Q6_K_XL) | 93.9 | 91.5 | 0% | CLEAN |
| lcpp-q6k | 93.3 | 90.2 | 0% | CLEAN |
| deep-32768 | 93.3 | 90.2 | 0% | CLEAN (32K ctx) |
| deep-131072 | 93.3 | 90.2 | 0% | CLEAN (128K ctx) |
| Q6_K (old) | 43.3 | 43.3 | 51% | *** DIRTY -- EXCLUDE *** |
| NVFP4 (old) | n/a | n/a | 1 solution only | *** ABORTED -- EXCLUDE *** |
- CLEAN QUANT LADDER (non-thinking): Q3 81.7 < IQ4 87.8 < Q5 90.9 < Q6 91.5 (HumanEval+). Monotonic, matches perplexity ordering.
- CONTEXT-LENGTH CONTROL: deep-32768 and deep-131072 score IDENTICALLY (93.3/90.2) => context window size does not affect HumanEval+ accuracy (expected: prompts are short). Useful control experiment for the paper.

## SWE-bench VERIFIED 50-INSTANCE RUNS (non-thinking) -- larger-n results
| run | completed | resolved | unresolved | errors | resolve rate |
|---|---|---|---|---|---|
| iq4_xs-verified50 | 47 | 36 | 11 | 2 | 76.6% (36/47) |
| q5_k_xl-verified50 | 48 | 35 | 13 | 2 | 72.9% (35/48) |
| verified50 | 50 dirs | no eval.log | | | INCOMPLETE |
| q3-verified50 | 49 dirs | no eval.log | | | INCOMPLETE |
- The 2 errors in each are INFRASTRUCTURE, not model failures: SWE-bench eval image django__django-11451 has no linux/arm64 manifest ("no matching manifest for linux/arm64/v8") -> evaluation was run on an arm64 host (Mac). Exclude from denominator or re-run on x86.
- CAUTION: IQ4_XS (76.6%) > Q5_K_XL (72.9%) INVERTS the HumanEval/perplexity ordering, but at n~=50 a single instance is ~2% -> difference of 1 instance. NOT significant; must report bootstrap CIs before drawing any ordering conclusion.

## SGLANG ATTEMPT -- FAILED (2026-08-23), documented in engines/sglang-fp8-FALHOU.txt
- SGLang v0.5.18 (image sha256:9e148f5ac788...). "SGLang nao subiu em 131072/65536/32768/16384" -- did not start at ANY context length tried.
- Failure: torch.OutOfMemoryError: Tried to allocate 1.19 GiB; GPU 0 15.48 GiB total, 566 MiB free, 14.92 GiB in use.
- Stack: scheduler.py init_model_worker -> maybe_init_draft_worker -> eagle_worker_v2.EagleDraftWorker -> TpModelWorker -> ModelRunner.load_model
  => OOM occurred initializing the EAGLE SPECULATIVE DRAFT WORKER.
- Diagnostic logs: engines/diag-tp1-ctx8k.log, engines/diag-tp2-ctx8k.log.
- NO SGLang results exist. Any public statement must say SGLang was attempted and could not be brought up on this hardware.

## CROSS-ENGINE FINDING: the 1.19 GiB draft-worker wall
Three independent stacks hit the SAME failure class on 2x16GB when adding a separate speculative draft model on top of the 27B weights:
| engine | method | draft model | outcome |
|---|---|---|---|
| SGLang 0.5.18 | EAGLE | (internal) | OOM "Tried to allocate 1.19 GiB" at EagleDraftWorker init |
| vLLM nightly | DFlash2 | z-lab BF16 3.6 GB | OOM "Tried to allocate 1.19 GiB" -- identical size, at every util 0.78-0.97, every ctx 3K-16K, every depth |
| llama.cpp fork | DFlash2 | GGUF Q4_K_M 1.1 GB | WORKS (38.51 tok/s, acceptance 0.714) |
- Interpretation: on 16 GB/GPU, a BF16/FP16 draft model plus a fixed ~1.19 GiB draft workspace does not fit alongside the target model. llama.cpp succeeds because (a) its drafter is 4-bit quantized (1.1 GB vs 3.6 GB) and (b) -sm layer pipelining leaves headroom that tensor-parallel replication does not.
- MTP avoids this entirely: its predictor is an in-checkpoint head, not a separate model -> works on BOTH vLLM and llama.cpp.
- This is a substantive, reportable hardware/deployment finding, not merely a config failure.

## DATA HYGIENE -- EXCLUSION LIST (must NOT enter the paper)
1. evalplus_results/humaneval/Q6_K_openai_temp_0.0_eval_results.json -- 51% empty, 43.3 pass@1 (artifact). Use Q6Kfix.
2. evalplus_results/humaneval/NVFP4_openai_temp_0.0.jsonl -- 1 solution, aborted run.
3. ALL of evalplus_results/humaneval-thinking/ (v1) -- produced with max_new_tokens=768; thinking consumed the budget, near-empty outputs. Superseded by humaneval-thinking-v2/.
4. swebench-results/thinking/vllm-NVFP4-mtp/ -- context-limited partial (MTP 40960 ceiling), only 1/3 usable. Supplementary only; definitive run is vllm-NVFP4/ (no-spec 98K).
5. verified50 and q3-verified50 -- no eval.log, incomplete.
6. engines/dflash2-results/power-dflash2-bench.csv -- header mislabeled (see DATA-INTEGRITY WARNING); use cols 1 and 3 for power.
7. Old non-thinking SWE runs (mtp-n1, mtp-n8, *-calib, plumbing, arm64-fix*) use different instance sets than the thinking runs -> NOT directly comparable.
- RULE: no test result or research data is ever deleted; excluded data is retained and labeled.

## OPEN ITEMS / NOT YET MEASURED
- NVFP4 perplexity (needs custom vLLM logprob script; llama-perplexity is GGUF-only) -- DECISION PENDING
- mtp-IQ4_XS SWE-bench thinking: 2/3 instances failed to infra 503s -> re-run pending
- Bootstrap 95% CIs (B=10,000) for pass@1 and resolve rate -- REQUIRED before any ordering claims
- KL divergence: cite Unsloth published per-quant numbers (not measured locally)
- Energy/kWh per benchmark: extract from Prometheus + power-log.csv windows
- Q3_K_XL GGUF not present in /srv/models (results exist from earlier run)
HumanEval+ thinking-v2 update: mtp-Q5_K_XL 89.0/86.0 (11.0% empty, 9255s).
PATTERN (3 of 6 configs): base HumanEval rises monotonically with bit-width (IQ4 86.6 -> Q4 87.8 -> Q5 89.0), mirroring perplexity and the non-thinking ladder, BUT HumanEval+ is pinned at exactly 86.0 for all three => the extra-test suite saturates under thinking mode and does not discriminate between quants. Empty rate declines with bit-width (12.8 -> 12.2 -> 11.0%), suggesting higher-precision quants finish reasoning within the 4096-token budget slightly more often. Verify against Q6/dflash configs before claiming.

## PRIOR EXPERIMENT INDEX (recovered from /srv/bench/engines logs, runs predating 2026-08-26)
These are earlier engine-bring-up experiments. They INDEPENDENTLY CORROBORATE later findings.

| log | config | outcome |
|---|---|---|
| v13-nvfp4-sem-mtp.log | vLLM NVFP4, NO MTP, fp8 KV | GPU KV cache 86,016 tokens; max concurrency 2.62x @32K |
| v13-nvfp4-com-mtp.log | vLLM NVFP4 WITH MTP, fp8 KV | Engine core initialization FAILED |
| v14-nvfp4-gmu097-mtp.log | vLLM NVFP4 WITH MTP, gpu-mem-util 0.97, fp8 KV | GPU KV cache 42,697 tokens; max concurrency 1.30x @32K |
| v14-fp8-gmu097.log | vLLM FP8 weights, gpu-mem-util 0.97 | CUDA OutOfMemory -> engine init failed |
| v13-fp8-nodeepgemm*.log | vLLM FP8, deepgemm disabled | (bring-up attempts) |
| v13-nvfp4-chunked.log | vLLM NVFP4, chunked prefill | (bring-up) |
| v14-nvfp4-gmu097-max.log | vLLM NVFP4, gmu 0.97, max ctx | (bring-up) |
| diag-tp1-ctx8k.log / diag-tp2-*.log | SGLang TP1/TP2 diagnostics @8K | see SGLANG section (all failed) |
| dflash2-rebuild*.log (x8), dflash2-rebuild-vmm*.log | llama.cpp DFlash2 image build attempts (VMM/no-VMM variants) | led to llama-dflash2:latest (build 50, f7aadef) |
| dflash2-bench.log | DFlash2 IQ4_XS speed bench (2026-08-25) | *** TRUNCATED: "No space left on device" -- disk filled mid-run *** |

### KEY CORROBORATIONS (independent replication, different session/date)
1. **MTP halves KV capacity on NVFP4** -- prior run: 86,016 tok (no MTP) -> 42,697 tok (MTP) = 0.50x.
   My independent 2026-08-27 measurement: ~98K (no-spec, 98304 max-len) -> ~48K ceiling with MTP = ~0.49x. SAME RATIO, replicated.
   This is the mechanism behind the SWE-bench ContextWindowExceeded @40961 with MTP.
2. **FP8 weights do NOT fit on 2x16GB** (v14-fp8-gmu097 OOM) -> NVFP4 (W4A4) was NECESSARY, not merely preferred. This justifies the NVFP4 choice in the paper.
3. **fp8 KV cache was used from the start** (kv_cache_dtype=fp8 in v13/v14) -- consistent with the checkpoint-calibrated kv_cache_scheme finding.

### INFRASTRUCTURE INCIDENT: disk exhaustion 2026-08-25
- engines/dflash2-bench.log shows repeated "No space left on device" from the legacy power logger during the DFlash2 benchmark => that run's data is incomplete/untrustworthy.
- Cause: Docker accumulation. As of 2026-08-27: images 100.1 GB (86.59 GB reclaimable), build cache 44.62 GB, root fs 91% full (21 GB free) -- driven by 8+ llama.cpp image rebuild attempts.
- RISK: a blind `docker image prune -a` WOULD DELETE llama-dflash2:latest (not running between configs, therefore counted "reclaimable") and break the two pending dflash HumanEval configs. Never blind-prune while the suite is running.
- Images that MUST be retained: llamacpp-mtp:latest, llama-dflash2:latest, llama-perplexity:latest, vllm/vllm-openai:nightly, all swebench/sweb.eval.* (SWE-bench evaluation), telemetry stack images.

### LOGGING GAP IDENTIFIED + FIXED (2026-08-27)
- PROBLEM: run-humaneval-thinking-v2.sh destroyed each llama.cpp container (`docker rm -f llamasrv`) WITHOUT dumping `docker logs`, so per-config server-side timings (tg = X t/s) and draft-acceptance stats were LOST for mtp-IQ4_XS, mtp-Q4_K_XL, mtp-Q5_K_XL. raw.jsonl stores only task_id+solution (reasoning discarded), so token counts are not reconstructible either.
- FIXED: script now writes `docker logs llamasrv > /srv/bench/server-timings/<config>.serverlog` BEFORE removing the container. Applies to remaining configs (dflash-IQ4_XS, dflash-Q4_K_XL).
- RECOVERED: mtp-Q6_K_XL timings captured live mid-run (server-timings/mtp-Q6_K_XL.serverlog) + continuous `docker logs -f` tail armed.
- STILL MISSING: per-config throughput for mtp-IQ4_XS, mtp-Q4_K_XL, mtp-Q5_K_XL. Recoverable only by re-running the controlled speed probe per quant (~5 min each).

### SPEED-DATA COVERAGE GAP (affects the paper's "Speed" axis)
- Controlled probe (speed-probe2.py) has been run ONLY on Q4_K_XL: no-spec 23.00, MTP n2 32.69, DFlash2 n4 38.51 tok/s.
- => We have a SPECULATION-METHOD axis but NO QUANT axis for speed. The paper title promises speed trade-offs across quants.
- Q6_K_XL live in-run estimate: 31.03 tok/s mean (median 31.17, range 25.13-34.71, n=193 samples) -- NOT probe-comparable (different workload).
- ACTION REQUIRED: run controlled probe for IQ4_XS, Q5_K_XL, Q6_K_XL (Q3_K_XL GGUF absent from /srv/models).

## RECOVERED: 2026-08-20 llama.cpp ablations (files final-20260820-1314.txt, mtp-clean-20260820-1257.txt)
Setup: host multivac, img llamacpp-nccl231:latest (NOTE: image no longer present), Qwen3.8-27B-UD-Q4_K_M.gguf / IQ4_XS, kv=q8_0, greedy, n=300 tokens, 3 runs each.
NOT directly comparable to our 2026-08-27 probe numbers (different image, different quant variant K_M vs K_XL, kv q8_0, different prompt) -- use for RELATIVE ordering and for the split-mode evidence.

### A. SPLIT-MODE MATRIX @ctx 32768 (why -sm layer is mandatory)
| id | quant | split | spec | decode tok/s | acceptance (mean len) | VRAM (g0/g1) | result |
|---|---|---|---|---|---|---|---|
| A1 | Q4_K_M | layer | none | 23.99 (23.55/24.20/24.23) | - | 8188/9264 MiB | OK |
| A2 | Q4_K_M | layer | MTP n2 | 32.66 (32.12/32.95/32.92) | 0.618 (2.23) | 8110/9994 MiB | OK |
| D2 | IQ4_XS | layer | MTP n2 | 38.66 (39.09/37.08/39.80) | 0.596 (2.19) | 7076/9080 MiB | OK |
| B1 | Q4_K_M | tensor | none | - | - | - | FAILED: CUDA error "an illegal memory access was encountered" (ggml-cuda.cu:106) |
| B2 | Q4_K_M | tensor | MTP n2 | - | - | - | FAILED: same illegal memory access |
| D1 | IQ4_XS | tensor | MTP n2 | - | - | - | FAILED: same illegal memory access |
| C1 | Q4_K_M | row | none | - | - | - | FAILED: "llama_model_load: error loading model: device CUDA0 does not support split buffers" |
=> HARDWARE FINDING (citable, with exact errors): on 2x RTX 5060 Ti, llama.cpp -sm row is unsupported (no split-buffer support) and -sm tensor crashes with CUDA illegal memory access, reproducibly, across two quants and with/without MTP. ONLY -sm layer (pipeline) works. This justifies -sm layer throughout the study.

### B. QUANT SPEED AXIS (partially fills the gap)
- IQ4_XS MTP n2: 38.66 tok/s vs Q4_K_M MTP n2: 32.66 tok/s => IQ4_XS ~18.4% faster (smaller quant, memory-bandwidth-bound decode).
- CROSS-SESSION CONSISTENCY CHECK: our 2026-08-27 probe gave Q4_K_XL MTP n2 = 32.69 tok/s; Aug-20 Q4_K_M MTP n2 = 32.66 tok/s. Near-identical despite different image and kv dtype -> measurement is stable.
- Baseline no-spec: Aug-20 Q4_K_M 23.99 vs our Q4_K_XL 23.00 -> consistent (~4% apart).

### C. MTP VARIANT ABLATION @ctx 8192 (mtp-clean-20260820-1257.txt, Q4_K_M, layer, kv q8_0)
| variant | decode tok/s | acceptance range (mean len) | VRAM (g0/g1) |
|---|---|---|---|
| 1. baseline, no speculation | 23.99 | - | 7598/8674 MiB |
| 2. MTP EMBEDDED head, n-max 2 | 30.64 | 0.495-0.667 (1.99-2.33) | 7520/9212 MiB |
| 3. MTP SEPARATE draft (mtp-Qwen3.8-27B-Q4_0.gguf), n-max 2 | 28.98 | 0.442-0.503 (1.88-2.01) | 7520/9988 MiB |
| 4. MTP SEPARATE draft, n-max 3 | 26.20 | 0.364-0.616 (2.08-2.85) | 7598/10060 MiB |
=> FINDINGS: (a) the EMBEDDED MTP head outperforms a SEPARATE draft model (30.64 vs 28.98) AND uses less VRAM (9212 vs 9988 MiB on g1); (b) increasing separate-draft depth to n-max 3 HURTS (26.20) with high run-to-run variance (19.64-33.10) -- deeper speculation lowers acceptance faster than it adds tokens at this size; (c) acceptance ~0.44-0.67 on Aug-20 build vs 0.728 measured 2026-08-27 on llamacpp-mtp:latest -> build-dependent, do not mix across builds in one table.

### D. PROVENANCE CAVEAT
- Image llamacpp-nccl231:latest used for these runs is NO LONGER on the host (not in docker images). Results are retained for relative/qualitative claims (split-mode support, quant ordering, embedded-vs-separate MTP) but cannot be re-run exactly.
- Model Qwen3.8-27B-UD-Q4_K_M.gguf and mtp-Qwen3.8-27B-Q4_0.gguf are also NOT in /srv/models today (current set is IQ4_XS/Q4_K_XL/Q5_K_XL/Q6_K_XL + dflash2 drafter).

# ============================================================
# MAJOR RECOVERY: champion-20260821 suite (30 timed runs) -- 2026-08-27
# Location /srv/bench/champion-20260821/ (184,709 files, 2.2 GB). Previously UNDOCUMENTED.
# ============================================================
Agentic Django code-editing evaluation with FULL llama.cpp timings embedded in every result JSON
(prompt_n, prompt_per_second, predicted_n, predicted_per_second, draft_n, draft_n_accepted).
Tasks: django-cold, django-{37273,37274,37278}-prefix-edits-c40k, prefix-cold, prefix-tool, functional-code(-nothink).
Also present: 33-case oracle-validation tree (JS/TS, package.json+biome.json), custom harness scripts
(run_cold_repo_code_eval.py, run_tool_call_code_eval.py, run_edit_tool_code_eval.py, run_cold_code_context_probe.py).

## *** THE CONTEXT AXIS (this is the paper's "Context Trade-offs") ***
Q3 embedded, tensor split, n_ctx 262144, same cold-repo task at increasing prompt length:
| prompt tokens | prefill tok/s | decode tok/s | acceptance |
|---|---|---|---|
| 40,347 | 860.5 | 71.59 | 0.973 |
| 99,885 | 750.7 | 59.27 | 1.000 |
| 179,709 | 625.3 | 50.12 | 1.000 |
| 248,368 | 548.2 | 44.61 | 1.000 |
| 258,779 | 537.9 | 45.17 | 1.000 |
=> Decode falls 71.6 -> 44.6 tok/s (-38%) and prefill 860 -> 538 tok/s (-38%) from 40K to 250K context.
   Clean, monotonic degradation curve on a SINGLE config -- directly usable as a headline figure.
Q5 embedded tensor c147456 at 139,872 prompt: prefill 650.5, decode 42.86, acceptance 1.000.

## *** MTP SPEEDUP AT LONG CONTEXT (with repeats) ***
IQ4_XS, layer split, n_ctx 180K, identical task (django-37278-prefix-edits-c40k), 40,347-token prompt:
| config | run 1 | run 2 | prefill tok/s |
|---|---|---|---|
| no MTP | 23.22 | 23.11 | ~1300 |
| MTP n=2 | 45.62 | 45.56 | ~945 |
=> MTP = 1.96x decode speedup at 40K context (vs 1.42x measured at short context on 2026-08-27).
   SPECULATION HELPS MORE AS CONTEXT GROWS. Repeats agree to within 0.5% -> excellent reproducibility.
   NOTE the trade: MTP LOWERS prefill (1300 -> 945 tok/s, -27%) while raising decode.

## *** MTP vs DFlash2 REVERSES AT LONG CONTEXT ***
| method | context | decode tok/s | acceptance |
|---|---|---|---|
| MTP n2 (layer c180) | 168,011 | 32.62 / 29.53 / 28.55 | 0.92 / 0.80 / 0.75 |
| DFlash2 (layer c196) | 184,011 | 30.26 / 22.91 / 23.88 | 0.55 / 0.43 / 0.41 |
=> At long context MTP BEATS DFlash2 on both speed and acceptance -- the OPPOSITE of the short-context
   result (2026-08-27 probe: DFlash2 38.51 > MTP 32.69 at 1K generation).
   DFlash2 acceptance collapses (0.41-0.59) at long context while MTP holds (0.75-0.99).
   => Speculation-method ranking is CONTEXT-DEPENDENT. This is a headline finding and must be stated as such;
      any single-context comparison would have drawn the wrong conclusion.

## *** CORRECTION: TENSOR SPLIT DOES WORK (supersedes the Aug-20 finding) ***
- Aug-20 (image llamacpp-nccl231): -sm tensor FAILED with CUDA illegal memory access; -sm row FAILED (no split buffers).
- Aug-21 (champion build, z-lab fork): -sm TENSOR RAN SUCCESSFULLY at n_ctx 262144 (Q3) and 147456 (Q5).
- => The earlier "tensor split always fails" claim is BUILD-SPECIFIC, not hardware-fundamental. CORRECTED.
- Moreover tensor-split runs were FASTER than layer-split runs on the same 40K task:
  q3 tensor 71.59 and q5 tensor 52.94 vs iq4xs layer 47.39 and q4km layer 40.22 (quant differs -- confounded, but the split mode did not break).
- -sm row remains unsupported ("device CUDA0 does not support split buffers") -- that finding stands.

## *** ORIGIN OF THE dflash2 BRANCH (answers the user's UI question) ***
/srv/bench/champion-20260821/dflash-build-context/llama.cpp is a real git checkout:
  branch: dflash2 | HEAD 1deefcc "Add p_min in DFlash2" (2026-08-21) | remote https://github.com/z-lab/llama.cpp-fork.git
=> This is the source of the "dflash2 branch / PR #27342" seen in the UI.
=> CORRECTS earlier note: image llamacpp-dflash2-pr27342:1deefcc-... was built from Z-LAB'S FORK at 1deefcc,
   NOT from upstream llama.cpp. Both DFlash2 images derive from the z-lab fork.

## SERVED CONTEXT SIZES (from props.json)
- dflash2-layer-c196: n_ctx 196,608, model Qwen3.8-27B-UD-IQ4_XS.gguf
- q4km-mtp2-layer-c163: n_ctx 163,840, model Qwen3.8-27B-UD-Q4_K_M.gguf
- Also referenced: c180 (184,320?), c262144 (Q3), c147456 (Q5)
=> The 27B model WAS run at up to 256K context on 2x16GB. Combined with the fp8-KV vLLM ceiling (~113K),
   llama.cpp reaches materially longer contexts on identical hardware -- another cross-backend finding.

## QUANTS APPEARING HERE THAT ARE NOT IN THE CURRENT MODEL SET
- q3-embedded (Q3_K_XL family), q4km (Q4_K_M), q5-embedded -- GGUFs no longer in /srv/models.
- Results retained; exact re-runs not possible without re-download.

## STATUS
- 30 runs carry complete timings; 50 result JSONs total (plus .arguments.json, props, slots).
- NOT yet integrated into the main results tables. Next: fold the context curve and the MTP/DFlash2 reversal
  into the report; decide whether to re-download Q3_K_XL/Q4_K_M for a complete quant x context matrix.

# ============================================================
# SECOND MAJOR RECOVERY (2026-08-27): ~40 experiment reports at /srv/bench/*.txt + /srv/bench/rigor/
# These substantially SUPERSEDE several earlier headline numbers. Read this section first.
# ============================================================

## *** PEAK THROUGHPUT IS 116.9 tok/s, NOT 71.6 ***
q3-depth100-20260821-2247 (Q3_K_XL, tensor, kv=q4_0, ctx=131072, thinking off, greedy):
| MTP depth | tok/s | acceptance |
|---|---|---|
| n=4 | 92.6 / 84.6 | 0.892 |
| n=6 | 102.3 / 89.5 | 0.837 |
| n=8 | **116.9 / 117.5** | 0.868 |
n8-repeat-20260822-0008 (Q3_K_XL, n=8, three COLD repeats): 116.77 / 116.62 / 116.58 tok/s -> spread 0.16%.
=> Highest verified decode rate in the study. Reproducible across cold restarts.

## *** MTP DEPTH OPTIMUM DEPENDS ON CONTEXT AND TASK *** (headline finding)
mtpdepth-coding-20260821-2213 (coding task, ctx=131072, kv=q4_0):
| depth | tok/s | acceptance |
|---|---|---|
| n=0 | 21.58 | - |
| n=2 | 53.59 | 0.966 |
| n=3 | 62.70 | 0.926 |
| n=4 | 64.50 | 0.890 |
| n=6 | 67.11 | 0.829 |
| n=8 | 92.63 | 0.793 |
=> monotonically FASTER to n=8 (4.29x over no-spec) despite falling acceptance.

mtpdepth-tensor-tensor-20260820-1346 (Q4_K_M, tensor, ctx=32768, kv=q4_0):
| depth | tok/s | acceptance |
|---|---|---|
| no-spec | 36.59 | - |
| n=2 | 48.58 | 0.601 |
| n=4 | 40.64 | 0.386 |
| n=6 | 30.10 | 0.274 |
| n=8 | 44.67 | 0.212 |
| n=12 | 36.95 | 0.142 |
=> n=2 is OPTIMAL; deeper is WORSE. Variants tested: +backend-sampling 44.86, +f16 draft KV 44.65 (no effect).
=> CONCLUSION: optimal speculative depth is NOT a constant. Short context/general task -> n=2.
   Long context coding task -> n=8. Any paper recommending a single depth would be wrong.

## *** QUANT x CONTEXT MATRIX AT NATIVE 262,144 (this closes the "missing quant axis") ***
matrix-q3q6-20260821-2125 (tensor split, MTP n=2, greedy, img llamacpp-dflash2-pr27342:1deefcc):
| quant | KV | ctx | tok/s | VRAM/GPU |
|---|---|---|---|---|
| Q3_K_XL | q4_0 | 262,144 | 54.64 | 10,786 MiB |
| IQ4_XS | q4_0 | 262,144 | 51.15 | 11,312 MiB |
| Q4_K_M | q4_0 | 262,144 | 48.61 | 12,286 MiB |
| Q6_K | q4_0 | 262,144 | 41.29 | 14,760 MiB |
| Q6_K | f16 | 32,768 | 43.23 | 11,818 MiB |
| Q5_K_XL | f16 | 32,768 | 40.43 | 11,292 MiB |
| Q6_K | q8_0 | 262,144 | FAIL out of memory | - |
=> Clean monotonic speed ladder by bit-width AT FULL 256K CONTEXT: Q3 54.64 > IQ4 51.15 > Q4_K_M 48.61 > Q6 41.29.
=> ALL FIVE QUANTS FIT 262,144 CONTEXT on 2x16GB when KV is q4_0.

n8-ctx-ceiling-20260822-0938 (Q6_K, tensor, q4_0):
| ctx | depth | tok/s | VRAM |
|---|---|---|---|
| 262,144 | n=8 | 37.53 | 15,182 MiB |
| 196,608 | n=8 | 37.50 | 14,158 MiB |
| 131,072 | n=8 | 37.64 | 13,134 MiB |
| 262,144 | n=2 | 40.90 | 14,734 MiB |
=> Decode is FLAT vs context window size when the prompt is short (37.5-37.6). Cost comes from FILLED context, not allocated window.

## *** KV-CACHE QUANTIZATION IS WHAT UNLOCKS 256K ***
kvquant-ctx-20260821-2106 (Q5_K_XL, tensor, MTP n=2):
| KV dtype | ctx | result |
|---|---|---|
| q8_0 | 262,144 | FAIL: failed to allocate |
| q4_0 | 262,144 | OK 39.33 tok/s, 14,234 MiB |
| f16 | 147,456 | OK 40.28 tok/s, 15,198 MiB |
=> q4_0 KV buys 1.78x more context for a 2.4% throughput cost.
kvhyp-20260820-1335 (Q4_K_M, tensor): f16 KV OK to ctx=131,072 (36.60 tok/s, 12,322 MiB); ctx=262,144 OOM.
   q8_0 KV at c4096 FAILED with "illegal memory access" -> q8_0 KV is buggy on this stack; q4_0 and f16 are the usable options.
bisect-20260820-1416 (IQ4_XS, f16 KV): max stable ctx ~245,760 (55.99 tok/s, 15,636 MiB).
iq4tensor-20260820-1403: IQ4_XS ctx=262,144 + MTP FAILS to allocate, but no-MTP at 262,144 OK (39.75 tok/s).
   => confirms MTP's KV cost; with MTP the ceiling drops to 196,608 (55.90 tok/s).

## *** SPECULATION-STACK ABLATION (combining methods HURTS) ***
specstack-20260820-1523 (Q3_K_XL, tensor, f16 KV, ctx=32768):
| variant | tok/s | acceptance |
|---|---|---|
| MTP n=2 (reference) | 63.81 | 0.671 |
| MTP n=1 | 58.24 | 0.780 |
| ngram-cache alone | 34.67 | 0.386 |
| MTP n=2 + ngram-cache | 49.12 | 0.563 |
| MTP n=2 + ngram-map-k | 62.05 | 0.671 |
| MTP n=3 + ngram-cache | 44.17 | 0.399 |
| MTP n=2, p-min 0.1 | 63.01 | 0.671 |
| MTP n=2, n-min 1 | 63.70 | 0.671 |
=> Stacking ngram-cache onto MTP COSTS 23% throughput (63.81 -> 49.12). MTP alone is best.
=> p-min and n-min tuning had no meaningful effect at this depth.

## *** A SECOND PERPLEXITY SET -- DIFFERENT PROTOCOL, AND NON-MONOTONIC ***
ppl-allquants-20260821-2213 (wikitext2, 20 chunks, c4096, tensor, f16 KV):
| quant | PPL | +/- |
|---|---|---|
| Q3_K_XL | 5.5474 | 0.06200 |
| IQ4_XS | 5.5250 | 0.06184 |
| Q4_K_M | **5.5031** | 0.06154 |
| Q5_K_XL | 5.5110 | 0.06177 |
| Q6_K | 5.5073 | 0.06171 |
=> NOT monotonic: Q4_K_M beats BOTH Q5_K_XL and Q6_K. All within +/-0.062 of each other -> differences are noise.
=> DIFFERENT ABSOLUTE VALUES from the perplexity-results set (6.65-6.68) because of a different protocol
   (20 chunks @ c4096, tensor, f16 KV vs the full-corpus run). *** THE TWO PPL SETS MUST NEVER BE MIXED. ***
   Report one protocol, state it explicitly, or report both separately with their protocols.

## OTHER RECOVERED RUNS
- q3full-20260820-1422: Q3_K_XL ctx=262,144 62.67 tok/s (15,668 MiB) vs ctx=32,768 63.28 tok/s -> window size alone is nearly free.
- tensor-ctx-20260820-1328: Q4_K_M tensor at ctx=4096 START-FAIL CUDA error -> the Aug-20 tensor instability was context/build dependent.
- nvfp4-20260822-1029: "NVFP4 ctx=32768 n=2 52.89 tok/s (9,052 MiB); ctx=262,144 n=2 52.58 tok/s (12,622 MiB)" with tensor+q4_0 flags.
  *** VERIFY ENGINE: flags look like llama.cpp, but NVFP4 is a vLLM format. Do not publish until the engine is confirmed. ***
- ctxcurve-20260820-1500 (CALIBRATED, prefix-cached -- the authoritative context curve):
| target | prompt_n | cache_n | FILLED | prefill t/s | decode t/s | TTFT s |
|---|---|---|---|---|---|---|
| 32,768 | 32,561 | 1,997 | 34,558 | 887.2 | 65.47 | 36.7 |
| 65,536 | 34,754 | 34,298 | 69,052 | 743.0 | 61.12 | 46.8 |
| 131,072 | 69,250 | 68,792 | 138,042 | 599.6 | 52.18 | 115.5 |
| 196,608 | 69,255 | 137,782 | 207,037 | 471.0 | 45.02 | 147.0 |
| 245,760 | 52,002 | 206,777 | 258,779 | 400.5 | 41.92 | 129.9 |
  => decode 65.47 -> 41.92 (-36%), prefill 887 -> 401 (-55%) from 34K to 259K FILLED context. TTFT up to 147 s.
  => Earlier curves (1426, 1436) were UNDERFILLED/uncalibrated -- superseded by the 1500 run. Use 1500 only.

## /srv/bench/rigor/ -- NOT YET MINED
deep-131072.txt, deep-32768.txt (7.8 KB each, the context-control evals), evalplus-Q3_K_XL.txt, evalplus-Q5_K_XL.txt,
recalib-newbuild.txt, T3-INTERROMPIDO.txt (interrupted run), swebench-q3.txt (1.1 MB -- a full Q3 SWE-bench run).

## *** CORRECTION: SWE-bench "thinking" configs were NEVER SCORED ***
exit_statuses_*.yaml lists instances under "Submitted", which means A PATCH WAS PRODUCED, not that tests passed.
An earlier summary misread this as "3/3 resolved" and that error propagated into the ledger. Corrected 2026-08-27.
Unscored-but-evaluable runs (have preds.json with patches, no eval.log):
  thinking/{mtp-IQ4_XS(1 patch), mtp-Q4_K_XL, mtp-Q5_K_XL, mtp-Q6_K_XL, dflash-IQ4_XS, dflash-Q4_K_XL} (3 patches each)
  verified50 (50 instances, 49 patches) <- a FULL 50-instance run never scored
  q3-verified50 (49 dirs, 5 patches), mtp-n1, mtp-n8, plumbing, vllm-calib
Scored runs: iq4_xs-verified50 36/47, q5_k_xl-verified50 35/48, dflash2-calibration 2/2,
  mtp-n1-calib 2/3, mtp-n8-calib 3/3, thinking/vllm-NVFP4 2/3, thinking/vllm-NVFP4-mtp 1/1.
NOTE: scoring the 3-instance thinking runs is cheap (all 3 eval images present locally).
      Scoring verified50 needs ~50 SWE-bench images (~4 GB each) -> not feasible at 25 GB free without batching.

# ============================================================
# THIRD RECOVERY (2026-08-27): /srv/bench/rigor/ -- AGENTIC BEHAVIOUR DATA
# This section contains the single most decision-relevant finding in the study.
# ============================================================

## *** T3: Q3_K_XL CANNOT COMPLETE AGENTIC TASKS *** (rigor/T3-INTERROMPIDO.txt)
Run deliberately stopped at 6/50 instances, with the conclusion already determined:
| model | mean steps | median | max | hit 250-step limit |
|---|---|---|---|---|
| Q6_K | 45 | 37 | 132 | **0 of 6** |
| Q3_K_XL | 250 | 250 | 250 | **6 of 6 (ALL)** |
Corroborated by rigor/swebench-q3.txt (1.1 MB): exit status "LimitsExceeded: 6" instances.
Decision recorded at the time: the remaining 44 instances would have cost ~88 h for zero new information.
=> Q3_K_XL is the FASTEST quant in raw tok/s (54.64 @262K, 116.9 with MTP n=8) but is USELESS for agentic
   coding: it loops until the step limit and never converges. Raw throughput is not a proxy for agentic utility.
=> THIS DISQUALIFIES Q3 for agentic work regardless of its speed, and is a headline result for the report:
   *** a quantization can be fast, score acceptably on HumanEval (84.1/81.7), and still fail completely
   on multi-step agentic tasks. Single-shot benchmarks do not predict agentic competence. ***

## COMPLETE Q6 INVENTORY (the user asked; there IS more Q6 data than was in the ledger)
| source | measurement |
|---|---|
| matrix-q3q6-20260821-2125 | Q6_K kv=f16 ctx=32,768 -> 43.23 tok/s, 11,818 MiB |
| matrix-q3q6-20260821-2125 | Q6_K kv=q4_0 ctx=262,144 -> 41.29 tok/s, 14,760 MiB |
| matrix-q3q6-20260821-2125 | Q6_K kv=q8_0 ctx=262,144 -> FAIL out of memory |
| n8-ctx-ceiling-20260822-0938 | Q6_K n=8: 262,144 -> 37.53 / 196,608 -> 37.50 / 131,072 -> 37.64 tok/s |
| n8-ctx-ceiling-20260822-0938 | Q6_K n=2 @262,144 -> 40.90 tok/s (n=2 BEATS n=8 for Q6) |
| ppl-allquants-20260821-2213 | Q6_K PPL 5.5073 +/- 0.06171 (protocol 2) |
| perplexity-results/ppl-Q6_K_XL | PPL 6.6511 +/- 0.04111 (protocol 1) |
| rigor/recalib-newbuild.txt | Q6_K 9 reps: mean 50.77, median 43.53, min 27.82, max 97.02 tok/s (sd 23.81) -> HIGH prompt-dependent variance |
| evalplus humaneval Q6Kfix | HumanEval 93.9 / HumanEval+ 91.5, 0% empty (BEST accuracy of any quant) |
| evalplus humaneval Q6_K (old) | 43.3/43.3, 51% empty -> DIRTY, excluded |
| rigor/T3 | mean 45 agentic steps, median 37, zero limit hits (BEST agentic behaviour) |
| humaneval-thinking-v2/mtp-Q6_K_XL | in progress at time of writing |
NOTE: MTP depth optimum is QUANT-DEPENDENT too -- Q6_K is faster at n=2 (40.90) than n=8 (37.53),
while Q3_K_XL is much faster at n=8 (116.9) than n=4 (92.6). Depth must be tuned per quant AND per workload.

## rigor/ EVALPLUS + CONTEXT CONTROL (confirms existing numbers, adds provenance)
- rigor/evalplus-Q3_K_XL.txt: pass@1 0.841 / 0.817  (matches humaneval Q3_K_XL)
- rigor/evalplus-Q5_K_XL.txt: pass@1 0.933 / 0.909  (matches humaneval Q5_K_XL)
- rigor/deep-32768.txt:  pass@1 0.933 / 0.902
- rigor/deep-131072.txt: pass@1 0.933 / 0.902  -> identical: the context-length control, now with provenance
- rigor/recalib-newbuild.txt: build 10588 commit 70adb1b4c, endpoint 127.0.0.1:8080

## =========== WHAT IS ACTUALLY LOST (definitive audit) ===========
IRRECOVERABLE:
1. Per-config llama.cpp server timings for humaneval-thinking-v2 mtp-IQ4_XS / mtp-Q4_K_XL / mtp-Q5_K_XL.
   Containers were destroyed before `docker logs` was captured; raw.jsonl stores only task_id+solution
   (reasoning text discarded) so token counts cannot be reconstructed. FIXED going forward (script patched);
   mtp-Q6_K_XL was rescued mid-run.
2. Exact reproducibility of the 2026-08-20 ablations: image llamacpp-nccl231:latest and models
   Qwen3.8-27B-UD-Q4_K_M.gguf and mtp-Qwen3.8-27B-Q4_0.gguf are no longer on disk. Results retained.
3. Q3_K_XL and Q4_K_M GGUFs absent from /srv/models -> their runs cannot be repeated without re-download.
4. The 2026-08-25 DFlash2 benchmark: truncated mid-run by disk exhaustion. Partial data only.
DELIBERATELY STOPPED (not lost):
5. T3 agentic run stopped at 6/50 with the conclusion already established (documented reasoning).
NOT LOST, MERELY UNSCORED (recoverable by running evaluation only -- no GPU time):
6. swebench verified50 (50 instances, 49 patches) <- a FULL 50-instance run
7. swebench thinking/{mtp-IQ4_XS, mtp-Q4_K_XL, mtp-Q5_K_XL, mtp-Q6_K_XL, dflash-IQ4_XS, dflash-Q4_K_XL}
8. swebench q3-verified50 (5 patches), mtp-n1, mtp-n8, plumbing, vllm-calib
=> Item 6 is the single biggest recoverable win: a 50-instance SWE-bench Verified result already generated.

# ============================================================
# DURABLE BENCHMARK WORKER (deployed 2026-08-27 20:58 UTC)
# /srv/bench/orchestrator/ -- survives client disconnects, session cycles, crashes and reboots.
# ============================================================

## Components
| file | role |
|---|---|
| orchestrator/worker.sh | main loop; runs the job queue in priority order, forever, re-checking every 5 min |
| orchestrator/lib.sh | shared helpers; encodes the rules that were learned from data loss |
| orchestrator/watchdog.sh | restarts the worker within 2 min if it dies; VERIFIED by kill test |
| orchestrator/state/<job>.{started,done,failed} | idempotency markers -- restart is always safe |
| orchestrator/worker.log | one line per event, per job |
| orchestrator/logs/<job>.log | full per-job log |
| server-timings/<label>.serverlog | llama.cpp server logs, ALWAYS captured before container teardown |
| /srv/bench/ledger-data.json | machine-readable snapshot of every metric (refreshed each cycle) |
| /srv/bench/champion-timings.json | 30 recovered agentic runs, structured |
| /srv/bench/bootstrap-ci.json | bootstrap 95% CIs, B=10,000, seed 20260825 |

## Rules encoded in lib.sh (each exists because something was lost)
1. kill_server() ALWAYS runs `docker logs > server-timings/<label>.serverlog` BEFORE `docker rm`.
   (Per-config timings for 3 HumanEval configs were lost exactly this way.)
2. gpu_busy() checks for run-humaneval-thinking-v2.sh, phase4-quant-speed.sh, phase34-waiter.sh and a
   lock file, so the worker never contends with the pipelines already running.
3. Every job is idempotent: job_done() short-circuits, and per-item checks skip already-scored configs.
4. snapshot_metrics() refreshes ledger-data.json + champion-timings.json every cycle, so the UI/report
   can always be regenerated from disk without re-deriving anything.
5. Nothing is ever deleted; scoring only ADDS eval.log files next to existing predictions.

## Job queue (priority order, as deployed)
1. score-thinking      -- CPU only. Scores the 6 SWE-bench "thinking" runs that had patches but were never
                          evaluated ("Submitted" != resolved). All 3 eval images already local.
2. bootstrap-ci        -- CPU only. B=10,000 CIs for every HumanEval and SWE-bench result.
3. agentic-steps       -- GPU. T3-style step-count profile for IQ4_XS and Q5_K_XL at ctx 131072, q4_0 KV,
                          MTP n=2. THE decisive missing datum for the model recommendation
                          (Q3 loops to 250 steps; Q6 converges in ~45; IQ4/Q5 unknown).
4. score-verified50    -- CPU only, but defers itself unless >=40 GB free (needs ~50 eval images).
                          A FULL 50-instance SWE-bench Verified run with 49 patches, never scored.

## Verification performed
- bash -n syntax check on all three shell files; ast.parse on bootstrap-ci.py. All passed.
- Kill test: `kill -9` the worker -> watchdog revived it in <2 min with a new pid, and it resumed the
  in-flight job correctly. Confirmed durable.

## How to operate
- status:    tail /srv/bench/orchestrator/worker.log ; ls /srv/bench/orchestrator/state/
- stop all:  pkill -f orchestrator/watchdog.sh && pkill -f orchestrator/worker.sh
- re-run a job: rm /srv/bench/orchestrator/state/<job>.done   (worker picks it up next cycle)
- data for the report/UI: /srv/bench/ledger-data.json, champion-timings.json, bootstrap-ci.json,
  PAPER-REFERENCES.md. All mirrored to ~/Documents/multivac-paper/data/ on the Mac.

## Still NOT automated (needs a human decision)
- NVFP4 perplexity (llama-perplexity is GGUF-only; needs a custom vLLM logprob script).
- Re-download of Q3_K_XL / Q4_K_M GGUFs to complete the quant x context matrix (~30 GB).
- Deciding which perplexity protocol the report will use (the two sets disagree and must not be mixed).

# ============================================================
# SESSION UPDATE 2026-08-28 00:20 UTC
# ============================================================

## Phase 3 HumanEval+ thinking v2: COMPLETE (6/6 llama.cpp configs done, 1 running)
| config | HumanEval | HumanEval+ | empty % | wall time |
|---|---|---|---|---|
| mtp-IQ4_XS | 86.6 | 86.0 | 12.8% | 88 min |
| mtp-Q4_K_XL | 87.8 | 86.0 | 12.2% | 154 min |
| mtp-Q5_K_XL | 89.0 | 86.0 | 11.0% | 154 min |
| **mtp-Q6_K_XL** | **90.9** | **88.4** | **7.9%** | 149 min |
| dflash-IQ4_XS | 89.0 | 87.8 | 10.4% | 80 min |
| dflash-Q4_K_XL | running (65/164) | — | — | — |
| NVFP4 (vLLM) | 85.4 | 84.1 | 12.8% | — |
=> Q6_K_XL BREAKS THE CEILING at 88.4 HumanEval+ (vs 86.0 plateau for IQ4/Q4/Q5).
   Also lowest empty rate (7.9% vs 10-13%).
   DFlash2 IQ4_XS at 87.8 is slightly above MTP IQ4_XS (86.0) but bootstrap CI overlaps.

## SWE-bench thinking: NOW SCORED (worker job score-thinking DONE)
| config | completed | resolved | unresolved | errors |
|---|---|---|---|---|
| mtp-IQ4_XS | 1 | 1 | 0 | 0 |
| mtp-Q4_K_XL | 3 | 2 | 1 | 0 |
| mtp-Q5_K_XL | 3 | 2 | 1 | 0 |
| **mtp-Q6_K_XL** | **3** | **3** | **0** | **0** |
| dflash-IQ4_XS | 3 | 2 | 1 | 0 |
| dflash-Q4_K_XL | 3 | 2 | 1 | 0 |
=> Q6_K_XL is the ONLY quant resolving all 3 instances under reasoning. Consistent with T3 agentic finding.
   CORRECTION: the earlier "3/3 for 5 configs" was wrong; actual scores are 2/3 for 4 configs, 3/3 for Q6 only.

## Bootstrap 95% CIs computed (worker job bootstrap-ci DONE, B=10,000, seed 20260825)
Key intervals (HumanEval+ thinking): all at n=164
- Q6_K_XL: 88.4 [skip] -- needs re-running (completed after bootstrap; will update)
- Q5_K_XL: 86.0 [80.5-90.9]
- Q4_K_XL: 86.0 [80.5-90.9]
- IQ4_XS: 86.0 [80.5-90.9]
=> Q4/Q5/IQ4 have IDENTICAL intervals: they are statistically indistinguishable.
Key intervals (SWE-bench 50-instance):
- IQ4_XS: 76.6% [63.8-87.2]
- Q5_K_XL: 72.9% [60.4-85.4]
=> Intervals overlap completely. No ordering claim is warranted.

## Worker system operational
- score-thinking: DONE
- bootstrap-ci: DONE
- agentic-steps: waiting (GPU busy with Phase 3 dflash-Q4_K_XL)
- score-verified50: deferred (25 GB free, needs 40)
- Watchdog verified: revived worker after kill -9 within 2 min

## Phase 3 COMPLETE — dflash-Q4_K_XL (2026-08-28 01:49 UTC)
Wall time: 8110s (135 min)
HumanEval base: 148/164 (90.2%)
HumanEval+:     143/164 (87.2%)
Empty rate:      14/164 (8.5%)
=> DFlash2 Q4_K_XL vs MTP Q4_K_XL: +1.2pp HE+ (87.2 vs 86.0), lower empty (8.5% vs 12.2%), 12% faster wall.
=> Both within bootstrap CI overlap — not statistically significant.
=> ALL 7 Phase 3 thinking configs now complete.

## Phase 4 STARTED (2026-08-28 01:49 UTC)
4 quants × 3 methods = 12 cells speed matrix.
Container: llamacpp-mtp:latest (already up).

## Phase 4 COMPLETE — Speed Matrix (2026-08-28 02:50 UTC)
4 quants × 3 methods = 12 cells. ctx=32768, 1024 gen tokens, 3 cold repeats.
| Config | tok/s | TTFT | Power W | VRAM MB | J/tok | Spread |
|---|---|---|---|---|---|---|
| IQ4_XS nospec | 27.2 | 0.497s | 202.7 | 8532 | 7.46 | 6.6% |
| IQ4_XS MTP n=2 | 46.9 | 0.879s | 204.0 | 9486 | 4.35 | 6.7% |
| IQ4_XS DFlash2 n=4 | 57.5 | 0.449s | 213.8 | 9822 | 3.70 | 13.1% |
| Q4_K_XL nospec | 22.8 | 0.678s | 204.7 | 10062 | 8.96 | 8.1% |
| Q4_K_XL MTP n=2 | 32.6 | 1.747s | 207.0 | 11014 | 6.41 | 13.5% |
| Q4_K_XL DFlash2 n=4 | 38.4 | 0.456s | 217.0 | 11356 | 5.65 | 11.2% |
| Q5_K_XL nospec | 19.8 | 0.456s | 207.4 | 11454 | 10.50 | 7.6% |
| Q5_K_XL MTP n=2 | 29.8 | 0.483s | 210.4 | 12408 | 7.07 | 6.8% |
| Q5_K_XL DFlash2 n=4 | 31.5 | 0.483s | 220.6 | 12746 | 6.99 | 11.9% |
| Q6_K_XL nospec | 16.5 | 0.442s | 194.2 | 13696 | 11.78 | 3.9% |
| Q6_K_XL MTP n=2 | 31.7 | 0.440s | 199.7 | 14648 | 6.29 | 12.5% |
| Q6_K_XL DFlash2 n=4 | 44.7 | 0.443s | 214.0 | 14992 | 4.79 | 7.5% |
=> DFlash2 wins EVERY cell at short context (32K).
=> Q6_K_XL has the biggest DFlash2 advantage: 2.71× over baseline, +41% over MTP.
=> IQ4_XS DFlash2 is throughput champion at 57.5 tok/s.
=> Combined with long-context finding: method ranking FLIPS — DFlash2 wins short, MTP wins long.
=> VRAM: DFlash2 adds ~350 MiB (draft model), MTP adds ~950 MiB (replicated MTP buffers).

## Worker agentic-steps STARTED (2026-08-28 02:52 UTC)
GPU free after Phase 4. Running T3-style step-count for IQ4_XS and Q5_K_XL.

## Agentic steps COMPLETE (2026-08-28 04:00 UTC)
T3-style step-count profile for IQ4_XS and Q5_K_XL:
| Instance | IQ4_XS | Q5_K_XL | Q6_K_XL (ref) | Q3_K_XL (ref) |
|---|---|---|---|---|
| astropy-12907 | 25 | 32 | ~45 mean | 250 (limit) |
| django-10880 | 19 | 32 | ~45 mean | 250 (limit) |
| django-10973 | 25 | 23 | ~45 mean | 250 (limit) |
| Mean | 23 | 29 | ~45 | 250 |
=> ALL four usable quants converge. IQ4_XS is the FASTEST stepper (mean 23).
=> Q3_K_XL remains DISQUALIFIED (all hit 250-step limit).
=> This settles the model recommendation: Q6_K_XL for best accuracy,
   IQ4_XS for best speed + efficiency. Both converge cleanly in agentic work.
=> Server logs captured: IQ4_XS 293 samples, Q5_K_XL 680 samples.

## Worker updated (2026-08-28 04:06 UTC)
- score-verified50: now uses batch processing (8 instances at a time, prune images between batches)
- nvfp4-ppl: NEW JOB added — vLLM logprobs-based perplexity (Protocol 2, WikiText-2, 20 chunks @4096)
- Disk freed: removed unused Docker images (vllm:latest, cuda-devel, old dflash2 build, llama-perplexity)
- 25 GB -> 65 GB free

## *** E11 — TENSOR-SPLIT REBALANCING: THE DUAL-GPU FINDING (2026-08-29, paper-grade) ***

Setup: host multivac, img `llamacpp-mtp:latest` id `sha256:feb0231976b6…` (0.3.0-dev, build 1,
commit d222767), `-sm layer`, `-ctk/-ctv q4_0`, `-fit off -ctxcp 4 -np 1`, seed 20260829, greedy,
`--spec-type draft-mtp --spec-draft-n-max 2`. Model `Qwen3.8-27B-UD-Q6_K.gguf`
(21,983,677,344 B, HF `unsloth/Qwen3.8-27B-GGUF`), on `/srv/bench/models/`.
Artifacts: `/srv/bench/e11/ceiling-*.json`, `/srv/bench/e11/tsweep-*.json`.

### THE RESULT
| Q6_K + MTP n=2, q4_0, layer split | ctx | decode @ full depth | MTP acc | VRAM GPU0 / GPU1 | idle GPU0 |
|---|---|---|---|---|---|
| default split (no `-ts`) | 196,608 | 7.19 tok/s | n/r | 12,978 / 15,640 | 3,333 MiB |
| **`-ts 58,42`** | **262,144** | **13.85 tok/s** | 0.889 | **15,320 / 15,080** | 991 MiB |
| `-ts 54,46` | 262,144 | FAIL (load) | — | — | — |

=> **Rebalancing the layer split bought +65,536 tokens of context (+33 %) AND +93 % decode speed
at the same time.** The default split left 3,333 MiB stranded on GPU0 while GPU1 OOMed 671 MiB
from its wall; it also gave GPU1 disproportionate attention work, which is why decode was slow.
=> This is a **citable systems finding**: on 2×16 GB without NVLink, llama.cpp's default
`-sm layer` placement is both capacity- and throughput-suboptimal, and a one-flag change recovers
both. It is not a quantization or speculation effect.

### Mechanism (why the two cards are not a pool)
With `--split-mode layer`, each layer's weights **and its slice of the KV cache** live on a single
device; there is no NVLink on RTX 5060 Ti. The binding constraint is therefore **per-card
16,311 MiB**, never the 32,622 MiB aggregate: a run OOMs when the heavier card fills while the
other still holds unreachable free memory. Measured peaks (E11a) show GPU1 binding in **every**
configuration, with 1,955–3,829 MiB idle on GPU0:

| config | ctx | GPU0 | GPU1 | idle GPU0 | free GPU1 |
|---|---|---|---|---|---|
| Q5_K_XL + MTP n2 | 196,608 | 12,482 | 15,792 | 3,829 | 519 |
| Q6_K + MTP n2 | 196,608 | 12,978 | 15,640 | 3,333 | 671 |
| Q6_K + no-spec | 262,144 | 13,910 | 15,192 | 2,401 | 1,119 |
| Q6_K_XL + no-spec | 245,760 | 14,356 | 15,838 | 1,955 | 473 |

Contributing cause, confirmed in the serverlog: MTP creates a **separate draft context against the
target model** (`common_speculative_init_result`), which costs Q6_K_XL 114,688 tokens of window
(245,760 no-spec → 131,072 with MTP). That draft context plus the output/embedding layer land on
the last device. (Placement is inferred from the consistent asymmetry; the log does not state it.)

### E11a — functional context ceilings (supersedes E1's VRAM-gated ceilings)
Success rule: healthy + `/props n_ctx` == requested + a real ~95 %-of-window prefill + a 64-token
generation. VRAM recorded, **never gated**.
| config | ceiling | prefill tok/s | decode @ full depth | MTP acc |
|---|---|---|---|---|
| Q5_K_XL + MTP n2 | 196,608 | 621 | 15.47 | 0.848 |
| Q6_K + MTP n2 | 196,608 | 569 | 7.19 | n/r |
| Q6_K + no-spec | **262,144** | 627 | 3.45 | — |
| Q6_K_XL + no-spec | 245,760 | 650 | 3.53 | — |

1. **UD-Q6_K (21.98 GB) reaches windows the XL tier cannot.** +50 % over Q6_K_XL with MTP
   (196,608 vs 131,072); the full native 262,144 without MTP, which Q6_K_XL cannot reach
   (`failed to allocate compute pp buffers` at 262,144 — a genuine error, so E1 was right there).
2. **E1's Q5_K_XL ceiling (163,840) is WRONG; the true ceiling is 196,608.** E1 rejected the rung
   on a `peak ≤ 15,700 MiB/GPU` gate at 15,794 MiB — yet Q6_K_XL ran correctly at 15,838 MiB.
   The gate sat inside the ±100–200 MiB layer-split noise it was trying to measure and rejected
   working configurations. ⚠️ **Every E1 rung failed on VRAM alone must be re-tested**; E1
   rejections backed by a real error are confirmed.

### ⚠️ MEASUREMENT CORRECTION — decode at depth vs decode into an empty window
Same server, same flags (`Q6_K + MTP n2 @196,608`): **37.22 tok/s at depth 0** (median of 40
HumanEval+ tasks, acceptance 0.986) vs **7.19 tok/s at depth 186,265** — a −81 % penalty.
The `ctx=32768` speed matrix (57.5 / 46.9 / 31.7 …) and E1's ladder (26–32 tok/s) are decode into
a nearly **empty** KV cache in a large *allocated* window. They must never be quoted as
long-context throughput. The 57.5 tok/s headline additionally differs on three axes: IQ4_XS +
DFlash2 n=4 at ctx 32,768.
Historical long-context curves are milder (Q3-embedded 71.6 @40K → 44.6 @250K, −38 %) but were
measured on the **deleted** tensor-split image. E11c now shows a large part of the layer-split
penalty was **imbalance**, not depth: rebalancing took Q6_K from 7.19 → 13.85 tok/s at a *larger*
window. Remaining open question for the paper: how much of the residual gap is `-sm tensor` vs
`-sm layer` attention distribution.

### Method notes required to reproduce (paper appendix)
- **Thinking must be disabled explicitly.** This model reasons by default and returns EMPTY
  content under small `max_tokens`; the widely-cited `/no_think` suffix **does not work** on this
  chat template (130 reasoning chars, empty content). Only
  `"chat_template_kwargs": {"enable_thinking": false}` works.
- **Prefix caching makes depth benchmarking tractable**: `prompt_n 8223 → 516, cache_n 7749`.
  Pads are built to an exact token count via `/tokenize` and cached per depth so every
  configuration sees a byte-identical prompt.
- **VRAM must be read after a deep prefill**, not after load; compute buffers grow with the batch.
- Padding uses **real repository source** (django worktree, `/srv/bench/e11/corpus.txt`); never
  repeated filler, which makes attention trivially easy and inflates results.

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

# ============================================================
# E12 / WAVE 1 + ACCURACY-METHOD DECISIONS (2026-08-30)
# Appended by the build-stream lifecycle. Full record and evidence trail:
#   data/build-stream-docs/docs/build-stream/2026-08-30-quant-bench-trackA.md (ledger L-5, L-6)
#   data/build-stream-docs/docs/paper/PAPER-NOTES.md (PN-1..PN-12)
#   data/build-stream-docs/docs/paper/METHOD-REFERENCES.md (R1..R7, external sources)
# ============================================================

## *** TENSOR SPLIT SETS THE CONTEXT CEILING (supersedes E11a and E1 ceilings) ***
Measured 2026-08-29/30 on llamacpp-mtp:latest (engine 0.3.0-dev d222767, image feb0231976b6...),
q4_0 KV, MTP n=2, -fit off, -ctxcp 4, -np 1, official DEC-2 non-thinking sampling (NOT greedy --
these rows must never share a table with the temp-0 e11 corpus). Prefill to >=0.90 of the window
is now ENFORCED IN CODE (was documented-only; see the pad defect below).

- UD-Q5_K_XL reaches the FULL NATIVE 262,144 window at five ratios (54,46 / 56,44 / 58,42 /
  60,40 / 62,38) and FAILS TO LOAD at the engine default split (compute-buffer-oom, imbalance
  1,530 MiB). Best 54,46: 10.82 tok/s decode at 0.948 depth (median-of-3 12.70), VRAM
  14,660/15,402 MiB, imbalance 742 MiB, MTP acceptance 0.516. 9 of 10 cells ok.
  => Supersedes E11a's 196,608 and E1's 163,840 for this quant. The ceiling is a property of the
  SPLIT, not of the quant. A ceiling published without its -ts value is not reproducible.
- UD-Q6_K_XL rebalanced ceiling = 212,992 at -ts 56,44 (12.98 tok/s at 0.9469 depth); 196,608 at
  the same ratio gives 17.26 tok/s, MTP acceptance 0.8971, VRAM 15,416/15,840, imbalance 424 MiB.
  229,376 failed both attempts. => Against the previously published 131,072 MTP ceiling this is
  +81,920 tokens (+62.5%). CLOSES G21 POSITIVELY.
- METHOD WARNING: the -ts optimum is NOT portable across quants. Q6_K's optimum is 58,42, but on
  Q6_K_XL that ratio OVERSHOOTS (GPU0 15,036 / GPU1 12,276, 2,760 MiB GPU0-heavy) while the
  default split is 1,482 MiB GPU1-heavy; the balance point lies between them and only 56,44 loads.
  Re-sweep -ts on any change of quant, KV dtype or spec setting.
- Balance is NOT speed: on Q5_K_XL the most balanced ratio (58,42, 28 MiB) is the SLOWEST
  (8.50 tok/s) while 54,46 (742 MiB) is the fastest. "Keep the fastest that loads" is the correct
  selection rule; "keep the most balanced" would have cost 21% of decode.
- Q6_K and Q4_K_XL were still sweeping when this was written.

## *** MEASUREMENT DEFECT FOUND AND FIXED -- affects any e12 cell before 2026-08-30T02:46Z ***
The pad builder bisected inside a FIXED bracket using chars-per-token calibrated on the first
200 kB of a corpus that runs ~2.9 chars/tok there and ~4.45 chars/tok after; the true cut fell
outside the bracket, the loop pinned at the edge and kept the LAST probe rather than the CLOSEST,
and returned short WITHOUT RAISING. pad_201830 delivered 169,823 tokens instead of 201,830
(-15.9%). Q4_K_XL cells recorded prefill_frac 0.7973 against Q5_K_XL's 0.948 -- both its speed row
and its ceiling verdict were optimistic AND the two quants were not comparable to each other.
The documented ">=90% of window" gate existed only as a docstring and was never compared to 0.90,
which is why this was invisible. Both are fixed; all 9 ladder pads rebuilt and verified at ~0.945.
Affected cells are QUARANTINED under /srv/bench/e12/quarantine/, not deleted.
=> Any e12 artifact predating 2026-08-30T02:46Z must be checked for prefill_frac before reuse.

## *** ENERGY + THERMAL EXTRACTION (closes the "energy extraction from power-log.csv" open item) ***
/srv/bench/power-log.csv, 1 Hz (nvidia-smi + kernel RAPL powercap), 43,182 consecutive samples,
2026-08-29T16:11:40Z -> 2026-08-30T04:11:41Z (12.00 h, 26% GPU-busy).
- System: mean 149.2 W, median 79.8 W, peak 408.9 W; 1.791 kWh over the window.
  Under GPU load: mean 334.1 W, peak 408.9 W -- an idle-to-loaded swing of ~4.2x.
- GPUs: 1.078 kWh (60% of system). GPU0 mean 47.1 W / GPU1 42.8 W; medians 10.7 / 10.8 W;
  peaks 183.7 / 178.8 W against a 180 W card limit.
- CPU package: 0.172 kWh (10%); mean 14.4 W, peak 142.1 W.
- THERMAL ASYMMETRY: GPU0 peaked 90 C vs GPU1 76 C on physically identical cards (means 46.8 /
  43.6 C) -- the signature of GPU0-weighted -ts ratios, i.e. the ratio chosen for context or
  throughput also selects a thermal operating point. OBSERVATIONAL AND CONFOUNDED: the window mixes
  quants, ratios and rungs, and case airflow asymmetry is an equally plausible contributor.
- CAVEAT: est_system_w is a MODELLED total (GPU telemetry + RAPL + fixed platform allowance), not
  a wall-socket measurement. Only the GPU and CPU-package limbs are directly instrumented. This
  characterises the HOST across a mixed window; per-run J/tok must still be integrated over that
  run's own interval (method 13.73), never derived from this mean.

## *** ACCURACY EVALUATION METHOD -- decision and precedent (2026-08-30) ***
Q6_K_XL is NO LONGER on the delete list: its measured 212,992 ceiling falsified the premise behind
the deletion, and it is the only quant on the ladder whose accuracy has never been measured against
the others. It is retained as the 4th arm and as the FIDELITY REFERENCE for divergence work.
Accuracy will be measured by the Small-Sample Accuracy protocol (~3.5 h, not the 35-47 h task
battery). Rationale, with sources in METHOD-REFERENCES.md:
- Divergence instruments draw statistical power from TOKEN count; task benchmarks from PROBLEM
  count. At n=65,536 tokens/domain/arm the standard error on mean KLD is sigma/256; HumanEval+ at
  n=164 carries +/-4.6 points against arms separated by 1-3 points. The task batteries never could
  rank these quants.
- llama.cpp ships the instrument (llama-perplexity --kl-divergence-base / --kl-divergence, emitting
  mean KLD with uncertainty, PPL ratio, dp percentiles, RMS dp, top-token agreement). Unsloth ranks
  its released Dynamic GGUFs -- the very models under test -- on mean KL divergence. Fireworks uses
  KLD + rejection rate for production quantization with a published threshold of KLD < 0.007, and
  documents perplexity's AVERAGING BIAS (tokens made worse cancelled by tokens made better) as the
  reason not to rank on PPL alone. LocalBench's GGUF benchmark uses ~250k tokens over 6 domains
  reporting KLD on prompt tokens plus top-1 agreement, observing 0.01-0.03 for Q4_K_M.
- Two domains: wikitext-2 (published convention, comparability) and the django code corpus (the
  target workload -- published quant tables measure prose; this measures code). The code domain
  carries the weight for the conclusion because Unsloth warns that wikitext-like evaluation data
  overfits imatrix quants calibrated on wikitext-like data, and these GGUFs' calibration set is
  not published in detail.
- LIMITS TO STATE IN THE PAPER: divergence is measured against Q6_K_XL, not FP16 (no FP16 on the
  host; a 27B F16 GGUF at ~54 GB exceeds free space) -- it is a ladder-relative measure; prompt-
  token divergence is not generation quality; only two domains, no multilingual or tool-calling
  coverage; the single generative task anchor is deliberately small (2 arms, paired per-problem
  per Miller/Anthropic) and reported with its power.
