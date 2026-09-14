# Lens B: how the standards define LLM-serving metrics, and how multivac compares

Source IDs in brackets refer to the table in §4. "Host" means facts I read on multivac: the exporter source, `llm.rules.yml`, live `/metrics`, `/slots` and `docker logs`. The llama.cpp source I read is current `master`, not the host's build d222767. The host log matches it in the one place I could check: `eval time = 539.29 ms / 10 tokens (59.92 ms per token)` gives 539.29/9 = 59.92, so the host also divides by n−1.

## 0. Definitions every source agrees on

- **TTFT is timed from when the request arrives or is sent, so it includes queueing.**
  - vLLM: from frontend `arrival_time` ("starts when tokenization begins") to the first token [S1].
  - OTel `gen_ai.server.time_to_first_token`: "helps measure the time spent in the queue and the prefill phase" [S11]. The WebFetch summariser reported the opposite; the raw markdown says this.
  - GenAI-Perf and AIPerf: from `request.start_perf_ns` to the first response [S6][S7].
  - MLPerf LoadGen: TTFT per query, judged at the Server-scenario `target_latency_percentile = 99` [S12][S13].
- **Queue time and prefill time are separate intervals.** vLLM has `request_queue_time_seconds` (QUEUED → SCHEDULED) and `request_prefill_time_seconds` (SCHEDULED → first NEW_TOKENS) [S1]. TGI has `tgi_request_queue_duration` [S5].
- **TPOT and ITL are different things.**
  - Per-request mean TPOT = (e2e − TTFT)/(OSL − 1). This is OTel `gen_ai.server.time_per_output_token` [S11], vLLM `request_time_per_output_token_seconds` [S3], AIPerf's "ITL" formula [S7], and MLPerf TPOT ("average interval between all the tokens generated") [S12].
  - Per-gap ITL is one sample for each gap between tokens: vLLM `inter_token_latency_seconds` [S3], Dynamo `dynamo_frontend_inter_token_latency_seconds` [S8], AIPerf `inter_chunk_latency` [S7], OTel client `gen_ai.client.operation.time_per_output_chunk` [S11].
- **Goodput counts requests that meet all SLOs at once.**
  - DistServe: "the maximum request rate that can be served adhering to the SLO attainment goal (say, 90%)", where SLO attainment is "the proportion of requests that meet the SLOs" [S19].
  - AIPerf: `goodput = good_request_count / benchmark_duration_seconds` [S7].
  - A request is either good or not. Neither source multiplies separate per-SLO fractions.
- **Speculative decoding has three separate quantities.**
  - Per-draft-token acceptance rate = accepted/drafted (vLLM counters [S3]).
  - Leviathan's α is the expected per-token acceptance probability, with E[#tokens per step] = (1−α^(γ+1))/(1−α) [S26].
  - Mean acceptance length τ = 1 + accepted/drafts, "conventionally including bonus token" (vLLM `spec_decode/metrics.py` [S3]; EAGLE's τ [S28]).
  - Speedup is wall-clock against no-spec and needs a paired baseline [S26][S28][S29].
- **The load-balancer contract (Gateway API Inference Extension, used by llm-d)** requires three gauges: TotalQueuedRequests, TotalRunningRequests and KVCacheUtilization. vLLM maps them to `vllm:num_requests_waiting`, `vllm:num_requests_running`, `vllm:kv_cache_usage_perc`; SGLang to `sglang:num_queue_reqs`, `num_running_reqs`, `token_usage` [S10]. llama.cpp is not in the mapping table. Its nearest equivalents are `requests_deferred`, `requests_processing`, and nothing for KV usage.

## 1. Metric inventory

Status is judged against the coverage block I was given, corrected where host inspection disagreed.

### Latency

| Metric (canonical; engine names) | Definition / unit | Defined by | multivac | How to get it on this llama.cpp | Pri |
|---|---|---|---|---|---|
| **TTFT** (vllm:time_to_first_token_seconds; sglang:time_to_first_token_seconds; dynamo_frontend_time_to_first_token_seconds; gen_ai.server.time_to_first_token) | s, arrival or send → first token; includes queue, tokenisation and prefill | S1 S4 S6 S7 S8 S11 S12 | **PARTIAL, mislabelled.** The exporter "TTFT" is slot `t_start` (`update_prompt_start()` when the slot begins the prompt) → first token sampled. Queue, HTTP and template/tokenise are excluded. | Not available natively. A proxy timestamp at arrival → first SSE byte (streaming), or → response (non-stream). | P0: headline SLO, and currently understated whenever a request waits |
| **Queue time** (vllm:request_queue_time_seconds; tgi_request_queue_duration) | s, arrival → scheduled | S1 S5 | ABSENT | Proxy TTFT − response `timings.prompt_ms`. `/metrics requests_deferred` gives a count only. | P0: with `-np 1` every concurrent request queues |
| **Prefill time** (vllm:request_prefill_time_seconds) | s, scheduled → first token | S1 | **PRESENT, under the wrong name** (it is the current "ttft") | log `prompt eval time`; response `timings.prompt_ms` | P1: rename only |
| **TPOT, per-request mean** (vllm:request_time_per_output_token_seconds; sglang:time_per_output_token_seconds; tgi_request_mean_time_per_token_duration; gen_ai.server.time_per_output_token) | s/token = decode time/(OSL−1) | S3 S4 S5 S7 S11 S12 | PRESENT and correct. llama.cpp `t_gen_us` = `t_gen_last − t_prompt_last`, and `n_gen_steps = n_gen−1`. | log `eval time`; `timings.predicted_ms / (predicted_n−1)` | — |
| **ITL, per-gap distribution** (vllm:inter_token_latency_seconds; dynamo …inter_token_latency_seconds; AIPerf inter_chunk_latency; gen_ai.client.operation.time_per_output_chunk) | s per gap between consecutive tokens or chunks | S3 S7 S8 S11 | ABSENT | Client/proxy: timestamp each SSE chunk. The server does not emit it. | P1: MTP n=2 delivers tokens in bursts, and a mean TPOT hides stalls |
| Time to second token (TTST) | s, first → second chunk | S6 S7 | ABSENT | Proxy on SSE | P2 |
| **Time to first output (non-reasoning) token** (AIPerf TTFO) | s, send → first non-reasoning token | S7 | ABSENT | Proxy: first SSE delta carrying `content` rather than `reasoning_content` | P1: thinking is on by default; for an agent, TTFT is time-to-thought |
| **E2E latency** (vllm:e2e_request_latency_seconds; tgi_request_duration; gen_ai.server.request.duration) | s, arrival → last token or byte | S1 S5 S11 | **PARTIAL.** It is the server `total time` = prompt + eval, excluding queue, HTTP and detokenise. | Proxy | P0: same queue blind spot as TTFT |
| Decode phase (vllm:request_decode_time_seconds) / inference time (…request_inference_time_seconds) | s | S1 S3 | PRESENT (decode) / derivable | log / `timings` | — |
| Client-side duration / TTFC (gen_ai.client.operation.duration, …time_to_first_chunk) | s, measured in the client | S11 | ABSENT | Instrument the agent client, or a synthetic probe | P1: the user-visible number, network included |
| Fluidity-index / fluid token generation rate | fraction of per-token deadlines met; max sustainable playback rate | S22 | ABSENT | Offline, from per-chunk timestamps | P2 |
| QoE (Andes) | token-delivery timeline against expected reading pace | S23 | ABSENT | Offline, from per-chunk timestamps | P2 |
| Model load / cold start | s, container start → healthy | (none standard; Dynamo exposes model config only [S8]) | ABSENT | Log timestamps of `load_tensors`/`server is listening`, or poll `/health` | P1: a restart here is risky and slow |

### Throughput

| Metric | Definition / unit | Defined by | multivac | How to get it | Pri |
|---|---|---|---|---|---|
| **System output token throughput** (AIPerf output_token_throughput; sglang:gen_throughput; rate(vllm:generation_tokens)) | tokens/s of wall time | S3 S4 S7 | PRESENT (`llm:output_tokens_per_second:rate5m`) | exporter counter | — |
| **Per-user decode speed** (AIPerf output_token_throughput_per_user = 1/ITL) | tokens/s excluding TTFT | S7 | **PARTIAL, biased.** `rate(tokens_predicted_total)/rate(tokens_predicted_seconds_total)` divides n tokens by n−1 steps of time (`predict.count` vs `t_gen`), inflating by n/(n−1). | exporter `sum decode_s` / `sum (outtok−1)` | P0: fix the bias |
| Prefill throughput (AIPerf prefill_throughput_per_user = ISL/TTFT) | tokens/s | S7 | PRESENT (server-side, uncached tokens) | `/metrics` | — |
| Request throughput | req/s | S6 S7 | PRESENT (req/min) | — | — |
| Iteration tokens / batch (vllm:iteration_tokens_total; tgi_batch_current_size) | tokens per engine step | S3 S5 | PARTIAL (`n_busy_slots_per_decode`); irrelevant at `-np 1` | `/metrics` | P2 |

### Goodput and SLOs

| Metric | Definition / unit | Defined by | multivac | How to get it | Pri |
|---|---|---|---|---|---|
| **SLO attainment (joint)** | fraction of requests meeting TTFT ≤ x **and** TPOT ≤ y | S19 | **INCORRECT**: product of two marginals (§2.3) | Per-request boolean in the exporter → `slo_good_total` / `finished_total` | P0 |
| **Goodput** | good requests/s [S7], or the maximum rate held at an attainment target [S19] | S7 S19 | ABSENT (the "goodput ratio" is attainment, not goodput) | `rate(slo_good_total)`; capacity version only offline | P1 |
| Energy-normalised goodput (good-req/s/W) | good req/s ÷ W | AIPerf goodput tutorial, search snippet only (not opened) | ABSENT | Joint counter ÷ average power | P2 |

### Scheduling and queueing

| Metric | Definition / unit | Defined by | multivac | How to get it | Pri |
|---|---|---|---|---|---|
| Queued requests gauge (GIE TotalQueuedRequests) | count | S10 | PRESENT natively (`requests_deferred`), no alert or rule | `/metrics` | P1 |
| Running requests gauge (GIE TotalRunningRequests) | count | S10 | PRESENT (`requests_processing`) | `/metrics` | — |
| Preemptions (vllm:num_preemptions, request_num_preemptions) | count | S3 | Not applicable: llama.cpp does not preempt with `-np 1`. Context-shift/prompt truncation is the closest event (`slot.truncated`). | log `truncated = 1` | P2 |

### Cache

| Metric | Definition / unit | Defined by | multivac | How to get it | Pri |
|---|---|---|---|---|---|
| **KV cache usage** (vllm:kv_cache_usage_perc; sglang:token_usage; trtllm_kv_cache_utilization) | current fraction of KV capacity in use, 0–1 | S3 S4 S10 | **INCORRECT** (§2.4) | Poll `/slots`: `(n_prompt_tokens + next_token.n_decoded)/n_ctx` while `is_processing` | P0 |
| **Prefix cache hits/queries** (vllm:prefix_cache_hits/queries in tokens; sglang:cache_hit_rate) | tokens reused ÷ prompt tokens | S2 S3 S4 | PARTIAL: native `prompt_tokens_cached_total` exists, but there is no rule and no per-request value. The exporter's `cache_tok` is declared but never incremented. | `/metrics` ratio; per request `timings.cache_n` or `/slots n_prompt_tokens_cache` | P1: the agentic workload depends on it |
| Cached tokens per request (dynamo_frontend_cached_tokens) | tokens | S8 | ABSENT | `timings.cache_n` | P1 |
| Context depth at release | tokens | (host-specific) | PRESENT | log `n_tokens` | — |

### Speculative decoding

| Metric | Definition / unit | Defined by | multivac | How to get it | Pri |
|---|---|---|---|---|---|
| Draft tokens, accepted, drafts (vllm:spec_decode_num_draft_tokens/…accepted_tokens/…drafts) | counters | S3 | PRESENT natively (`llamacpp:spec_decode_*`) | `/metrics` | — |
| Draft acceptance rate | accepted/drafted | S3 | PRESENT | rule | — |
| **Mean acceptance length τ** | 1 + accepted/drafts | S3 S28 | ABSENT from rules; printed in the log as `mean len` | `rate(accepted)/rate(drafts) + 1` | P1: the quantity that tracks speedup |
| **Per-position acceptance** (vllm:spec_decode_num_accepted_tokens_per_pos) | conditional α_k = pos_k / pos_(k−1) | S3 S26 | Scraped, not used | `/metrics{position}` | P1: tells a drafter collapse apart from a depth effect |
| Speedup against no-spec | ratio of wall time | S26 S27 S28 S29 | ABSENT; offline only (PN-23 context) | Paired offline battery | P2 |

### Reliability and errors

| Metric | Definition / unit | Defined by | multivac | How to get it | Pri |
|---|---|---|---|---|---|
| **Finish reason** (vllm:request_success{finished_reason=stop/length/abort}) | counter | S1 S3 | **INCORRECT** (§2.2) | Response `finish_reason` (proxy), or log `stop_type` at debug level | P0 |
| **HTTP status / errors** (http_requests_total{status}; tgi_request_failure; dynamo_component_errors_total; OTel `error.type`) | counter by class or type | S1 S8 S11 | ABSENT | Proxy | P0: invisible today |
| Client disconnects / aborts (dynamo_frontend_disconnected_clients; finished_reason=abort) | counter | S1 S8 | ABSENT | Proxy detects a closed stream | P1 |
| Corrupted (NaN) requests (vllm:corrupted_requests) | counter | S2 S3 | ABSENT | Not possible | P2 |

### Request shape

| Metric | Definition / unit | Defined by | multivac | How to get it | Pri |
|---|---|---|---|---|---|
| **ISL** (vllm:request_prompt_tokens; tgi_request_input_length; gen_ai.client.token.usage{type=input}) | tokens in the full prompt | S3 S5 S11 S30 | **PARTIAL, wrong**: logs processed (uncached) tokens only | `timings.prompt_n + cache_n`; response `usage.prompt_tokens` | P1 |
| OSL (vllm:request_generation_tokens) | tokens | S3 S30 | PRESENT | — | — |
| Requested max_tokens (vllm:request_params_max_tokens; tgi_request_max_new_tokens) | tokens | S3 S5 | ABSENT | `/slots params.max_tokens`, or proxy | P1: needed to explain `length` stops |
| **Reasoning vs answer tokens** (AIPerf reasoning_token_count) | tokens | S7 | ABSENT | Proxy: tokenize `reasoning_content` via `/tokenize`, or count deltas | P1 |
| Interarrival / burstiness, conversation turns | s; distribution | S30 S31 | ABSENT | Proxy arrival timestamps | P2 |
| Per-request labels (model, endpoint, client, thinking) | attributes | S11 (`gen_ai.request.model`, `gen_ai.operation.name`) | ABSENT | Proxy; add the `?model=` label in router mode [S15] | P1 |

## 2. Correctness problems in the current implementation

1. **"TTFT" excludes queueing, so it is prefill time.**
   - In llama.cpp, `stats.t_start` is set by `update_prompt_start()` when the slot enters `SLOT_STATE_PROCESSING_PROMPT` [S16]. The first token sets `t_prompt_last` through `update_prompt_last()`.
   - Waiting in `queue_tasks` (reported as `n_tasks_deferred`), HTTP parsing, chat templating and tokenisation all fall outside that interval.
   - Every standard counts from arrival [S1][S7][S11][S12].
   - At `-np 1`, a second request that waits 10 minutes behind a 250K prefill still records a small "TTFT", and the "goodput" rule counts it as good.
   - Rename it to `prefill_seconds` and measure real TTFT at a proxy.
2. **Finish reason is wrong: `truncated` does not mean `length`.**
   - In llama.cpp source, `slot.truncated = true` is set only in two places:
     - context exhaustion when context shift is disabled;
     - prompt truncation or context shift.
   - A request that runs out of `max_tokens`/`n_predict` sets `STOP_TYPE_LIMIT` with `truncated` still false. The indentation limit and `t_max_predict_ms` behave the same way.
   - The API maps every stop that is not EOS or WORD to `finish_reason: "length"` [S16].
   - So `llm:truncation_ratio:5m` and `TruncationRateHigh` **miss the PN-60 failure mode (budget exhaustion)**, which is exactly what the rule's comment says it tracks. They record a max_tokens stop as `stop`.
3. **"Goodput" multiplies marginals instead of measuring joint attainment.** `P(TTFT≤8)·P(TPOT≤75ms)` equals the joint fraction only if the two are independent. At depth both rise together (long context slows prefill and decode). With positive correlation the joint fraction is at least the product, so this rule understates attainment and can fire `GoodputDegraded` falsely. Two more defects:
   - The denominators differ: TPOT is not observed for requests with OSL ≤ 1.
   - The quantity is SLO attainment [S19], not goodput [S7][S19].
4. **"KV utilization" is a lifetime high-water mark.**
   - `metrics.n_tokens_max = std::max(...)` is never reset and is exposed with `# TYPE … counter` (host `/metrics`).
   - Dividing by a hardcoded 262144 gives the largest sequence ever seen, so the value only ever rises.
   - GIE, vLLM and SGLang define a *current* gauge [S10].
   - It will also break in router mode, where each model has a different `n_ctx`.
5. **The decode tok/s rule is biased upward.** `tokens_predicted_total` = `predict.count` = n, but `tokens_predicted_seconds_total` = `t_gen`, which covers only n−1 steps [S16]. Across many short agent turns (10–30 tokens) the inflation is 3–11 %.
6. **"E2E" is not end-to-end.** It is server `total time` = prompt + eval, and has the same queue and HTTP blind spot as item 1.
7. **The ISL histogram is actually the uncached-prefill histogram.** The `prompt eval time … N tokens` line counts `n_prompt_processed`. On a cache hit ISL is badly understated, so request-shape comparisons against Azure or BurstGPT traces [S30][S31] would be wrong. The exporter's `cache_tok` counter is dead code.
8. **J/token has problems with windows and idle periods.** An instantaneous power gauge is divided by a 5 m rate. When idle, `clamp_min(…,0.001)` makes the ratio explode to values like 60 W/0.001, about 60 kJ/token. It also charges all prefill energy to output tokens without saying so. Use `avg_over_time(power[5m])`, gate on a minimum token rate, and label the metric "J per output token, prefill included".
9. **The TPOT percentile is not an ITL percentile.** The exporter docstring promises "inter-token-latency percentiles", but the histogram holds per-request means. That is fine for MLPerf/OTel TPOT, but it cannot show MTP burst/stall jitter, which vLLM, Dynamo and AIPerf capture per gap.
10. **Speculative-decoding metrics do not track speedup.** `accepted/drafted` is correct as an acceptance rate, but it is neither α nor τ. The per-request acceptance histogram weights a 10-token reply the same as a 1,000-token one, which is the PN-61 degenerate-acceptance artifact.
11. **Minor issues:**
    - Quantile rules use 10 m windows while goodput uses 5 m, so they cannot be read side by side.
    - The TTFT buckets bottom out at 0.25 s, so short-prompt p50s are coarse.
    - The `docker logs -f` pipe ends when the container restarts (the stdin loop exits), and log-format coupling is build-specific. Plausible from the code; not tested.

## 3. Recommendations for this host

1. **Add a thin measuring reverse proxy in front of :8080.** This is the only way to get standard TTFT, queue, E2E, ITL, errors and labels, because llama.cpp exposes no arrival timestamp.
   - It should record: arrival; first byte; the first non-reasoning delta (TTFO); each chunk's timestamp (ITL/ICL); last byte; HTTP status; client disconnect; `finish_reason`; `usage`; and the response `timings` object (`prompt_n`, `cache_n`, `prompt_ms`, `predicted_n`, `predicted_ms`, `draft_n`, `draft_n_accepted` [S16]).
   - Derived values: queue ≈ proxy TTFT − `timings.prompt_ms` (this includes tokenisation, which is acceptable if labelled); ISL = `prompt_n + cache_n`.
   - Name metrics after OTel [S11], translated to Prometheus, e.g. `gen_ai_server_time_to_first_token_seconds`, with a low-cardinality label set: `gen_ai.request.model`, `gen_ai.operation.name`, `thinking=on|off`, `error.type`.
   - Adopting the proxy changes the client path, so it is an owner decision. I have not deployed anything.
2. **Fix the exporter in place.** It is small and read-only.
   - Rename `ttft` to `prefill_seconds` and `e2e` to `server_compute_seconds`.
   - Compute the joint SLO boolean per request and export `llamacpp_req_slo_good_total`.
   - Add `decode_seconds_total` and `decode_steps_total` counters so the decode rate is unbiased.
   - Drop `truncated` as the finish reason. Either take `finish_reason` from the proxy, or label the metric `context_truncated` and stop calling it length.
3. **Rewrite the rules.**
   - `llm:slo_attainment:5m = rate(slo_good_total)/rate(finished_total)`
   - `llm:goodput_rps:5m = rate(slo_good_total[5m])`
   - `llm:spec_mean_accept_len = 1 + rate(accepted)/rate(drafts)`
   - `llm:spec_alpha_pos{position}` as conditional ratios of the per-position counters
   - `llm:prefix_cache_hit_ratio = rate(prompt_tokens_cached_total)/(rate(prompt_tokens_total)+rate(prompt_tokens_cached_total))`
   - a queued-requests alert on `requests_deferred > 0 for 2m`
   - put all quantiles and ratios on one window
4. **Replace the KV utilisation rule with a 1 Hz `/slots` poller** that exports the current `(n_prompt_tokens + n_decoded)/n_ctx` with an `n_ctx` label. `/slots` is enabled by default [S15] and returns `n_ctx`, `n_prompt_tokens`, `n_prompt_tokens_cache` and `n_decoded` (verified live). This also gives the GIE contract triple, which matters if llm-d or router mode ever arrives.
5. **Make SLOs depth-aware.** A fixed 8 s TTFT cannot hold at 250K on this host (about 7–8 minutes of prefill, per the historical record). Report attainment per ISL bucket, or use a normalised prefill SLO (s per 1K prompt tokens). Record the thresholds as host-specific, not as MLPerf targets (MLPerf Server TTFT is 2–6 s, TPOT 80–200 ms [S12]).
6. **Build a Grafana LLM dashboard in four rows:** latency (TTFT/queue/prefill/TPOT/ITL), throughput and goodput, cache and depth, spec decode, plus a reliability row (status codes, finish reasons, disconnects).
7. **Defer:** fluidity-index [S22] and QoE [S23], computed offline from proxy chunk logs; OTel tracing spans; logprob/entropy signals (they need `n_probs`, which costs decode speed, so sample them).

## 4. Sources

| ID | Title | Authors / affiliation | Year | URL | Type | Status |
|---|---|---|---|---|---|---|
| S1 | vLLM Metrics design doc | vLLM project | 2025–26 | https://docs.vllm.ai/en/latest/design/metrics.html (raw `docs/design/metrics.md`) | engine design doc | FETCHED |
| S2 | vLLM Production Metrics | vLLM project | 2026 | https://docs.vllm.ai/en/latest/usage/metrics.html | engine docs | FETCHED |
| S3 | vLLM `v1/metrics/loggers.py`, `v1/spec_decode/metrics.py` | vLLM project | 2026 | https://github.com/vllm-project/vllm (main) | source code | FETCHED |
| S4 | SGLang Production Metrics | SGLang project | 2026 | https://docs.sglang.io/references/production_metrics.html | engine docs | FETCHED |
| S5 | TGI Metrics | Hugging Face | 2025 | https://huggingface.co/docs/text-generation-inference/reference/metrics | engine docs | FETCHED |
| S6 | GenAI-Perf README | NVIDIA | 2025 | https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/perf_analyzer/genai-perf/README.html | vendor docs | FETCHED |
| S7 | AIPerf Metrics Reference | NVIDIA | 2026 | https://docs.nvidia.com/aiperf/reference/ai-perf-metrics-reference | vendor docs | FETCHED |
| S8 | Dynamo Metrics Catalog | NVIDIA | 2026 | https://docs.nvidia.com/dynamo/reference/observability/metrics-catalog | vendor docs | FETCHED |
| S9 | trtllm-serve (/metrics) | NVIDIA | 2026 | https://nvidia.github.io/TensorRT-LLM/commands/trtllm-serve/trtllm-serve.html | vendor docs | FETCHED (iteration-stats JSON only; no trtllm_* names listed there) |
| S10 | Model Server Protocol (proposal 003) | Kubernetes SIG gateway-api-inference-extension | 2025 | https://github.com/kubernetes-sigs/gateway-api-inference-extension/blob/main/docs/proposals/003-model-server-protocol/README.md | standard / proposal | FETCHED |
| S11 | Semantic conventions for GenAI metrics (Development status) | OpenTelemetry | 2026 | https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-metrics.md | standard | FETCHED (raw file) |
| S12 | MLPerf Inference Rules | MLCommons | 2026 | https://github.com/mlcommons/inference_policies/blob/master/inference_rules.adoc | benchmark rules | FETCHED |
| S13 | LoadGen `mlperf.conf` | MLCommons | 2026 | https://github.com/mlcommons/inference/blob/master/loadgen/mlperf.conf | benchmark config | FETCHED |
| S14 | LLMPerf (archived 2025-12-17) | Anyscale / Ray project | 2023–25 | https://github.com/ray-project/llmperf | tool | FETCHED (README gives no formal ITL definition) |
| S15 | llama.cpp server README | ggml-org | 2026 | https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md | engine docs | FETCHED |
| S16 | llama.cpp `server-context.cpp`, `server-common.h/.cpp`, `server-task.cpp` | ggml-org | 2026 (master, not d222767) | https://github.com/ggml-org/llama.cpp/tree/master/tools/server | source code | FETCHED |
| S17 | Efficient Memory Management for LLM Serving with PagedAttention | Kwon et al., UC Berkeley (affiliation recalled) | SOSP 2023 | https://arxiv.org/abs/2309.06180 | paper | FETCHED |
| S18 | Orca: A Distributed Serving System for Transformer-Based Generative Models | Yu et al., Seoul National University / FriendliAI | OSDI 2022 | https://www.usenix.org/conference/osdi22/presentation/yu | paper | RECALLED (HTTP 403) |
| S19 | DistServe | Zhong et al., Peking University, StepFun, UC San Diego | OSDI 2024 | https://arxiv.org/abs/2401.09670 | paper | FETCHED |
| S20 | Taming Throughput-Latency Tradeoff … Sarathi-Serve | Agrawal et al., Georgia Tech, Microsoft Research India | 2024 (OSDI recalled) | https://arxiv.org/abs/2403.02310 | paper | FETCHED |
| S21 | Splitwise | Patel et al., Microsoft (affiliation recalled) | ISCA 2024 | https://arxiv.org/abs/2311.18677 | paper | FETCHED |
| S22 | Etalon: fluidity-index | Agrawal et al. (Georgia Tech / MSR India, recalled) | 2024 | https://arxiv.org/abs/2407.07000 | paper | FETCHED |
| S23 | Andes: QoE in LLM text streaming | Liu et al., University of Michigan | 2024 | https://arxiv.org/abs/2404.16283 | paper | FETCHED |
| S24 | Mooncake | Qin et al., Moonshot AI / Tsinghua (recalled) | 2024 | https://arxiv.org/abs/2407.00079 | paper | FETCHED |
| S25 | Llumnix | Sun et al., Alibaba (recalled) | OSDI 2024 | https://arxiv.org/abs/2406.03243 | paper | FETCHED |
| S26 | Fast Inference from Transformers via Speculative Decoding | Leviathan, Kalman, Matias, Google Research | ICML 2023 | https://arxiv.org/abs/2211.17192 | paper | FETCHED |
| S27 | Accelerating LLM Decoding with Speculative Sampling | Chen et al., DeepMind (recalled) | 2023 | https://arxiv.org/abs/2302.01318 | paper | FETCHED |
| S28 | EAGLE | Li et al., Peking University, Microsoft Research, University of Waterloo, Vector Institute | ICML 2024 | https://arxiv.org/abs/2401.15077 | paper | FETCHED |
| S29 | Medusa | Cai et al., Princeton, Together AI, UIUC, CMU and others | 2024 | https://arxiv.org/abs/2401.10774 | paper | FETCHED |
| S30 | Azure LLM Inference Dataset 2023 | Microsoft Azure (Splitwise authors) | 2023 | https://github.com/Azure/AzurePublicDataset/blob/master/AzureLLMInferenceDataset2023.md | trace | FETCHED |
| S31 | BurstGPT | Wang et al. (affiliations not verified) | 2024 | https://arxiv.org/abs/2401.17644 | trace / paper | FETCHED |
| S32 | Host evidence: `/srv/bench/telemetry/llamacpp_log_exporter.py`, `/srv/bench/telemetry/prometheus/etc/rules/llm.rules.yml`, live `/metrics`, `/slots`, `docker logs qwen38-serve` | multivac | 2026-09-14 | local | primary host evidence | READ |

