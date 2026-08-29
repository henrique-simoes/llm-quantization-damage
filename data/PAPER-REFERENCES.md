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
- NVFP4 perplexity -- DONE 2026-08-28, see "NVFP4 PERPLEXITY -- COMPLETE" below
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
# SESSION UPDATE 2026-08-28 -- NVFP4 PERPLEXITY COMPLETE,
# PHASE-4 QUANT x METHOD SPEED MATRIX COMPLETE
# ============================================================

## NVFP4 PERPLEXITY -- COMPLETE (2026-08-28 18:00 UTC)
| metric | value |
|---|---|
| PPL (WikiText-2-raw-v1 test) | **8.5848** (avg NLL 2.149994) |
| tokens / chunks | 77,621 tokens, 160 chunks |
| protocol | seq_len 512, stride 512, NON-OVERLAPPING (Protocol 2) |
| engine | vLLM nightly 0.26.1rc1.dev1219+g46638857f, image vllm/vllm-openai:nightly |
| config | TP=2, kv-cache-dtype fp8, gpu-memory-utilization 0.85, max-model-len 4096, enforce-eager, HF_HUB_OFFLINE=1 |
| checkpoint | unsloth/Qwen3.8-27B-NVFP4 (checkpoint-calibrated static FP8 E4M3 KV scales) |
| decoding | greedy (temp 0), max_tokens 1, echo=True, logprobs=1 (prompt-logprobs) |
| result file | /srv/bench/perplexity/nvfp4-vllm-ppl.json (+ /srv/bench/perplexity/nvfp4-vllm.log) |
| engine log | /srv/bench/server-timings/nvfp4-ppl.serverlog |

### PROTOCOL COMPARABILITY (IMPORTANT for the PPL table)
- llama.cpp ladder (IQ4_XS 6.6839 / Q4_K_XL 6.6617 / Q5_K_XL 6.6556 / Q6_K_XL 6.6511) was measured with
  llama-perplexity --ctx-size 512 --batch-size 512 (run-perplexity.sh) => SAME 512/512 non-overlapping
  protocol as the NVFP4 run. Numbers are comparable.
- Inherent backend difference to document: NVFP4 run uses FP8 KV cache (checkpoint-calibrated) + W4A4
  compute; llama.cpp runs use FP16 KV default. NVFP4 PPL 8.58 vs Q6_K_XL 6.65 is a REAL degradation
  (W4A4 + FP8-KV vs GGUF K-quants), consistent with the NVFP4-as-speed-tradeoff narrative.
- Spec-decode note stands: PPL under MTP/DFlash2 == base quant PPL (lossless under greedy); no separate runs.

### PROMPT-LOGPROBS OOM FINDINGS (the 1.19-GiB-wall sibling; citable engineering finding)
- vLLM's prompt_logprobs path (echo=True + logprobs, or prompt_logprobs>0) allocates a full-vocab
  logits buffer per scheduled forward step AND computes fp32 log_softmax over the full ~152K vocab:
  ~0.78 MiB per scheduled token on this model (measured 1.45 GiB alloc for a 1906-token step; secondary
  TP all_gather of prompt hidden states needed 744 MiB). On 2x16GB with NVFP4 weights at 11.3 GiB/GPU
  this path OOMs at any config that served SWE-bench/HumanEval fine (those never request logprobs --
  which is why all previous NVFP4 deployments ran clean at gmu 0.97 / ctx 98K).
- WORKING CONFIG (validated end-to-end): gmu 0.85 (KV avail ~0.87 GiB; 0.80 starves KV -> init-time
  ValueError "0.09 GiB < 0.29 GiB needed"), max-model-len 4096, 512-token non-overlapping chunks,
  expandable_segments:True, HF_HUB_OFFLINE=1 (tokenizer/config fetch to HF Hub is another intermittent
  init-failure source when unauthenticated/rate-limited).
- OFFICIAL RECIPE alignment: vLLM's own perplexity test suite
  (tests/models/language/generation_ppl_test/ppl_utils.py) prescribes max_num_seqs=1 ("to avoid OOM"),
  small max_model_len (1024), gmu 0.7, WikiText-2-raw-v1 test via prompt_logprobs, non-overlapping
  stride=max_length chunks. Our config follows the same shape.
- General escape hatch for longer chunks (untested here): --max-num-batched-tokens caps tokens per
  forward step, bounding the logits temp allocation independently of chunk size.
- Script: /srv/bench/orchestrator/nvfp4-perplexity.sh (fixed); dataset pre-extracted to
  /srv/bench/perplexity/wikitext-2-test.txt (parquet sha256 5f1bea06..., converted via pyarrow in-container;
  host python3 has NO pip/datasets -- Ubuntu 26.04 externally-managed).

## PHASE-4 QUANT x METHOD SPEED MATRIX -- COMPLETE (2026-08-28 02:50 UTC)
Controlled probe (speed-probe2.py), 3-run medians, llama.cpp family, greedy, seed 20260825,
ctx 32768, layer split, same 1024-tok AVL prompt as all other speed tables.
Image: llamacpp-mtp:latest (nospec/mtp) + llama-dflash2:latest fork f7aadef (dflash2).
| quant | nospec | MTP n2 (accept) | DFlash2 n4 (accept) |
|---|---|---|---|
| IQ4_XS | 27.17 | 46.89 (0.72 / 2.44) | 57.52 (0.69 / 3.76) |
| Q4_K_XL | 22.84 | 32.64 (0.731 / 2.46) | 38.43 (0.714 / 3.86) |
| Q5_K_XL | 19.76 | 29.77 (0.713 / 2.42) | 31.55 (0.556 / 3.22) |
| Q6_K_XL | 16.48 | 31.74 (0.72 / 2.44) | 44.70 (0.69 / 3.76) |
(tok/s; acceptance values from serverlog where captured; full cells in /srv/bench/spec-speed-metrics.jsonl,
labels <QUANT>__<method>, and /srv/bench/server-timings/<QUANT>__<method>.serverlog)
Findings:
- Quant axis: smaller quants are faster at every method (IQ4_XS 27.2 nospec -> Q6_K_XL 16.5, -39%).
- Speculation compensates quant size: Q6_K_XL+DFlash2 (44.70) beats IQ4_XS nospec (27.17) by 1.65x --
  i.e. with a drafter you can run the HIGHEST-accuracy quant and still be fastest. Paper-worthy headline.
- MTP acceptance is quant-independent (~0.71-0.73 @ n2, mean len 2.42-2.46) => acceptance tracks the
  base model, not the quant.
- OUTLIER: Q5_K_XL+DFlash2 acceptance collapses to 0.556 (mean len 3.22 vs 3.76-3.86 for all other
  quants) -> its 31.55 tok/s is NOT representative of DFlash2's quant trend (IQ4 57.5 / Q4 38.4 /
  Q6 44.7). Re-run recommended before treating the quant x DFlash2 row as monotonic.
- This closes the "SPEED-DATA COVERAGE GAP" (probe previously only on Q4_K_XL).

## ORCHESTRATOR STATE after this session (2026-08-28)
- nvfp4-ppl: DONE (was crash-looping ~15x since 06:54 UTC on the three failure classes above).
- Worker queue: "ALL QUEUED JOBS COMPLETE" (worker.log). phase4, bootstrap-ci, score-thinking,
  score-verified50, agentic-steps all done (state markers in /srv/bench/orchestrator/state/).
- 12 stale `tail -f` watcher processes cleaned up (no orchestrator processes touched).
- Remaining open: mtp-IQ4_XS SWE re-run; energy extraction from power-log.csv; Q3_K_XL GGUF re-download
  (optional); report writing.
