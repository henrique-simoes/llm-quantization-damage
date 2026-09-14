# LENS A — llama.cpp serving telemetry on multivac

**Scope and method.** I read the upstream `tools/server` source on master (S2–S5) and the matching PRs and issues (S6–S10). I checked the running `qwen38-serve` read-only, using `/metrics`, `/slots`, `/slots?fail_on_no_slot=1` (HTTP 200), `/props`, `/health`, `--help`, `docker inspect`, and `grep -l` over `/app/*.so` (S24). I also read the live exporter at `/srv/bench/telemetry/llamacpp_log_exporter.py` and `prometheus/etc/rules/llm.rules.yml`.

One disclosure: `GET /metrics` does change server state. Every scrape resets the window behind the two throughput gauges (S3, `metrics_reset_bucket = true`), so my single curl cost at most one 5 s window of those gauges.

**What the running image has (b1-d222767, container started 2026-09-14T22:03:52Z):**
- **`/metrics` matches upstream master line for line.** 10 counters, 5 gauges, and the labelled `spec_decode_num_accepted_tokens_per_pos_total`. There are no histograms and no KV metric; `kv_cache_usage_ratio` does not appear in any `/app` library.
- **These request features are compiled into `libllama-server-impl.so`:** `return_progress`, `prompt_progress`, `timings_per_token`, `draft_n_accepted`, `fail_on_no_slot`, `include_usage`.
- **These flags are present:** `--metrics`, `--slots/--no-slots`, `--props`, `-v`, `-lv N`, `--log-file`, `--log-timestamps`, `--log-prompts-dir`, `--perf/--no-perf`, `--models-dir`, `--models-preset`, `--models-max`, `--models-autoload`, `--sleep-idle-seconds`.
- **`/props` reports** `endpoint_props:false`, `is_sleeping:false`, `build_info:"b1-d222767"`.
- **No `llama-bench` or `llama-batched-bench` binary is in the image.** Only `llama-cli`, `llama-perplexity` and `llama-server` are there.
- **Startup warning in the serverlog:** the first compute-buffer reservation OOMed on CUDA0 (2,169 MiB) and the server retried "without pipeline parallelism". That is worth recording as a load-time event.

---

## 0. Ground truth: what each llama.cpp number actually measures (from source)

| Signal | Exact computation (upstream master, S2–S4) |
|---|---|
| `stats.t_start` | Set when the slot moves from `SLOT_STATE_STARTED` to prompt processing (`update_prompt_start`, server-context.cpp ~3143). This is **after** HTTP parsing, templating, tokenisation, the deferred queue and slot selection. |
| `prompt_ms` / "prompt eval time" | `t_prompt_last − t_start`. `prompt_n` = tokens actually computed; cached tokens are excluded (`cache_n` holds them). |
| `predicted_ms` / "eval time" | `t_gen_last − t_prompt_last`. |
| "ms per token" (eval) | `predicted_ms / (n_gen − 1)`, because "the first token is free, it comes from the logits of the last prompt batch". Check against the sample: 55253.67 / 1470 = 37.59 ✓. |
| "tokens per second" (eval) | `(n_gen − 1) / predicted_s`. |
| "total time" | `prompt_ms + predicted_ms`. It is **not** end-to-end. |
| "draft acceptance" | `n_draft_accepted / n_draft_tokens`. |
| "mean len" | `1 + n_draft_accepted / n_draft_verif_steps`. |
| `truncated` | Set **only** by context shift, or by hitting `n_ctx` when ctx-shift is off (lines ~1887, ~2970). It is **not** set by `max_tokens`; that sets `stop_type:"limit"` / `finish_reason:"length"`. |
| `prompt_tokens_total`, `prompt_seconds_total` | Flushed per decode batch that has output, or when idle. Close to real time. |
| `tokens_predicted_total`, `tokens_predicted_seconds_total`, `spec_decode_*` | Added in `callback_on_reset` → `metrics_on_prediction`, i.e. **once at request end**. |
| `prompt_tokens_seconds`, `predicted_tokens_seconds` gauges | Averages over the window since the **previous scrape by anyone**. The window resets on every `/metrics` GET. |
| `n_tokens_max` (TYPE counter) | `max(slot.prompt.n_tokens())` over every decode since process start. A lifetime high-water mark. |
| `n_busy_slots_per_decode` | `n_busy_slots / n_decode` since process start. |
| `n_decode_total` | `llama_decode()` calls, "excluding speculative decoding and multimodal decoding". |
| Response `timings` | `cache_n, prompt_n, prompt_ms, prompt_per_token_ms, prompt_per_second, predicted_n, predicted_ms, predicted_per_token_ms, predicted_per_second`, plus `draft_n, draft_n_accepted` when drafting (server-common.cpp). Sent on the final response and the final stream chunk; with `timings_per_token:true`, on every chunk. |
| `prompt_progress` (`return_progress:true`) | `{total, cache, processed, time_ms}` streamed during prefill. |
| `/slots` (live) | `id, n_ctx, speculative, is_processing, id_task, n_prompt_tokens, n_prompt_tokens_processed, n_prompt_tokens_cache, params{…}, next_token[{has_next_token, n_remain, n_decoded}]`. `?fail_on_no_slot=1` returns 503 when no slot is free. |
| Router mode | `routes.get_metrics = models_routes->proxy_get`. `/metrics?model=<id>` is proxied to that child; each child keeps its own counters (S1, S5). |

**History of the KV metric.** `llamacpp:kv_cache_usage_ratio` (= `used_cells / n_ctx`) and `llamacpp:kv_cache_tokens` were removed by **PR #13660** "kv-cache : simplify the interface" (ggerganov, merged 2025-05-21). The PR says they were "too internal and implementation-specific and should not be exposed to the public", and deprecates `llama_kv_self_n_tokens` and `llama_kv_self_used_cells` (S7). The README went stale and was corrected by PR #22879 (merged 2026-05-11, S6). Issue #23632 (2026-05-25) asked for the metric back; its linked PR #24010 was closed as not planned and the issue is labelled stale (S8).

**Open upstream work.** PR #27012 (open) adds the first histogram, `llamacpp:request_context_tokens`, with a `--metrics-ctx-buckets` flag and `model_name`/`model_alias` labels (S9). The only OpenTelemetry work found is PR #23188 "ggml-rpc: opt-in OpenTelemetry tracing" (open, RPC backend only, not the server) (S10). I found no merged work on latency histograms or OTel for the server. Issue #27572 (open) reports draft-MTP acceptance collapsing to 0.0 under `-np N` because of a device→host copy race (S10 listing). That matters if `-np` is ever raised.

---

## 1. Metric inventory

Status is judged against the coverage block you gave. "Proxy" means the transparent OpenAI-compatible proxy recommended in §3.

| Metric (canonical / engine names) | Definition, unit | Defined by | multivac | How to obtain here | Pri |
|---|---|---|---|---|---|
| **Client TTFT** — `gen_ai.client.operation.time_to_first_chunk`; GenAI-Perf TTFT | s, from client send to first streamed chunk | S13, S21 | ABSENT | Proxy: time from request accepted to first SSE `data:` byte | **P0**: the latency the user feels; server TTFT misses queueing, which is real with `-np 1` |
| **Server TTFT** — `gen_ai.server.time_to_first_token`; `vllm:time_to_first_token_seconds` | s. vLLM measures from frontend **arrival** to first token (S16 `_time_since(arrival_time)`) | S13, S15, S16 | PARTIAL (exporter's `ttft` = `prompt_ms`, excludes queue) | Proxy (arrival→first chunk). Log/`timings.prompt_ms` is only the **prefill** part | P0 |
| **Time to first answer token** (after reasoning) | s, request→first `delta.content` (not `reasoning_content`) | none standard; OTel has only first chunk | ABSENT | Proxy: first non-empty `content` delta. Server uses `reasoning_format:"deepseek"`, so reasoning and content arrive in separate delta fields | **P0**: thinking is on by default here; first *chunk* can be seconds before first answer |
| **Queue time** — `vllm:request_queue_time_seconds` | s, QUEUED→SCHEDULED | S15, S16 | ABSENT | Proxy: `arrival→first chunk − timings.prompt_ms` (upper bound; includes tokenise/template). Live view: `llamacpp:requests_deferred` and `/slots` `is_processing` | P0 |
| **Prefill time** — `vllm:request_prefill_time_seconds` | s, SCHEDULED→first token | S15, S16 | PRESENT (as "ttft") | `timings.prompt_ms`, or the log `prompt eval time`. Rename it | P1 |
| **TPOT** — `gen_ai.server.time_per_output_token`; `vllm:request_time_per_output_token_seconds` | s/token, per request, `decode_time/(n_gen−1)` (S16); MLPerf: excludes first token (S19) | S13, S16, S19, S20 | PRESENT, correct denominator | Log or `timings.predicted_ms/(predicted_n−1)` | P0 |
| **ITL** — `vllm:inter_token_latency_seconds`; `gen_ai.client.operation.time_per_output_chunk` | s, gap between successive token/chunk emissions; one observation per gap | S13, S16, S21 | ABSENT | Proxy: timestamp every SSE chunk. GenAI-Perf divides the gap by the tokens in the later chunk. With MTP n=2 emissions are bursts of 1–3 tokens, so report per-chunk gaps **and** tokens per chunk | P1: jitter and stall detection. Bimodal under MTP, so do not substitute TPOT |
| **E2E latency** — `gen_ai.server.request.duration`, `gen_ai.client.operation.duration`, `vllm:e2e_request_latency_seconds` | s, arrival→last token or last byte | S13, S15 | PARTIAL (exporter "e2e" = prompt+gen, no queue) | Proxy: request→final byte | P0 |
| **Decode time** — `vllm:request_decode_time_seconds` | s, first→last token | S16 | PARTIAL | `timings.predicted_ms` | P2 |
| **Prompt tokens per request** — `vllm:request_prompt_tokens`; `gen_ai.usage.input_tokens` | tokens | S13, S14, S15 | PARTIAL: exporter logs `prompt_n`, which **excludes cached tokens** | `timings.prompt_n + timings.cache_n`, or `usage.prompt_tokens` via proxy | P1 |
| **Output tokens per request** — `vllm:request_generation_tokens`; `gen_ai.usage.output_tokens` | tokens | S13, S15 | PRESENT | Log, `timings.predicted_n`, or `usage.completion_tokens` | P1 |
| **Reasoning vs answer tokens** — `gen_ai.usage.reasoning.output_tokens` | tokens | S14 | ABSENT | Proxy: count chunks/tokens per delta field (with `timings_per_token`, per-chunk `predicted_n` deltas give exact counts). Whether llama.cpp's `usage` carries a reasoning-token field is **unverified** | P1 |
| **Prefix-cache hit per request** — `gen_ai.usage.cache_read.input_tokens`; `vllm:prefix_cache_hits` / `_queries` | tokens; hit ratio = cached/(cached+computed) | S14, S16 | ABSENT (the exporter's `cache_tok` counter is **never incremented**) | `timings.cache_n` per request; aggregate as `rate(prompt_tokens_cached_total)/(rate(...cached_total)+rate(prompt_tokens_total))`. `/slots.n_prompt_tokens_cache` | P1: agentic workloads live on prefix reuse |
| **Finish reason** — `vllm:request_success_total{finished_reason}`; `gen_ai.response.finish_reasons` | stop / length / tool_calls / abort | S14, S15 | **WRONG** (see §2.1) | Proxy: `finish_reason` in the final chunk. `stop_type` in `/completion` responses | P0 |
| **Errors and aborts** | HTTP status counts; client-cancelled requests; `error.type` | S14; vLLM `http_requests_total` (S15) | ABSENT | Proxy only. Whether `print_timing` fires on disconnect is **unverified** | P0 |
| **Requests running / waiting** — `vllm:num_requests_running` / `_waiting` | gauge | S15 | PRESENT | `llamacpp:requests_processing`, `llamacpp:requests_deferred` | P1 |
| **KV cache usage** — `vllm:kv_cache_usage_perc` | fraction of KV blocks in use | S15 | **WRONG** (high-water mark) | Removed upstream (S7). Best available: `/slots` → `(n_prompt_tokens + next_token.n_decoded)/n_ctx` for the active slot, polled at 1 Hz (inference: with `-np 1` this equals the sequence's cells; it ignores `-ctxcp 32` checkpoint memory) | P0: depth drives decode speed 3–5× here |
| **Context depth at completion** | tokens | PR #27012 (S9) | PRESENT | Log `stop processing: n_tokens` | P1 |
| **Decode throughput** | tok/s | llama.cpp (S2) | PRESENT, lumpy (§2.5) | `rate(tokens_predicted_total)/rate(tokens_predicted_seconds_total)` over whole-request windows | P1 |
| **Prefill throughput** | tok/s | S2 | PRESENT | Counter ratio. Live prefill: `prompt_progress` or `/slots.n_prompt_tokens_processed` deltas | P1 |
| **Spec decode** — `vllm:spec_decode_num_draft_tokens` / `_num_accepted_tokens` / `_num_drafts` / `_num_accepted_tokens_per_pos` | counters | S16 (same names as llama.cpp) | PRESENT | Native counters; per request via `timings.draft_n` / `draft_n_accepted` | P1 |
| **Mean acceptance length** | `1 + accepted/drafts` | S3 | PARTIAL (in log, not exported) | `1 + rate(accepted)/rate(drafts)` from native counters | P1: better tells whether MTP n is paying off than the acceptance ratio does |
| **Goodput** | requests/s (or share) meeting **both** TTFT and TPOT SLOs **per request** | DistServe (S20); MLPerf constraints (S19) | **WRONG** (product of marginals) | Exporter or proxy: per-request joint predicate → counter | P0 |
| **Energy per output token** | J/token = ΔE_GPU(+CPU)/Δtokens over the same window | none standard; method only | **WRONG** (§2.4) | Increase of an energy counter (NVML backend "total energy counter", S23) / increase of tokens | P1 |
| **Model load / cold start** | s, container start→`/health` 200; `model loaded` log line | none standard | ABSENT | Poll `/health` (503 "Loading model" → 200) and derive; log `llama_server: model loaded` | P1: router or llama-swap makes it per-request latency |
| **Sleep state** — `vllm:engine_sleep_state` | 0/1 | S16 | ABSENT | `/props.is_sleeping` | P2 |
| **Prompt progress during prefill** | processed/total, ms | S2 | ABSENT | `return_progress:true` (present in image) | P2: 262K-token prefill lasts minutes |
| **Logprobs / entropy** | nats | none standard | ABSENT | `n_probs:k` (+ `post_sampling_probs`) per request. Proxy may compute top-k entropy **only on requests that already asked for it**; never inject (adds sampling cost and changes the client payload) | P2 |
| **Batch efficiency** | busy slots per decode | S2 | PRESENT | native gauge; constant 1 with `-np 1` | P2 |
| **Graphs reused** | count | log only | ABSENT | log line (lifetime counter from `llama_perf_context`) | P2 |
| **Tracing / request labels** | span `{operation} {model}` with `gen_ai.request.model`, `server.address`, `error.type`, usage attributes, `gen_ai.response.time_to_first_chunk` | S14 | ABSENT | Proxy emits OTel spans. llama.cpp has no server-side OTel (S10) | P1 |

---

## 2. Correctness problems in the current implementation

1. **The finish-reason counter is wrong, and the `length` label mislabels the failure mode that matters most.** The exporter sets `reason="length" if truncated else "stop"`. In source, `truncated` means context shift or the `n_ctx` wall (S3). A request that exhausts `max_tokens` has `truncated = 0` and is counted as **stop**. As a result:
   - `llm:truncation_ratio:5m` and the `TruncationRateHigh` alert **cannot see budget exhaustion**, which is exactly the PN-60 failure mode the rule's comment cites.
   - `tool_calls` and aborts are invisible.
   - The log line never carries `stop_type`. The fix needs the response body (`finish_reason`), i.e. the proxy.
   - Rename the existing signal to `context_limit_hits`.

2. **"TTFT" is prefill time, not TTFT.** `prompt_ms` starts at slot prompt start (S4), after HTTP parsing, chat templating, tokenisation and the deferred queue. OTel and vLLM define TTFT from request arrival (S13, S16); GenAI-Perf defines it from client send (S21). With `-np 1`, a second request waits for the whole first request, so p95 "TTFT" can look fine while users wait minutes. With thinking on, the first *answer* token also arrives after the whole reasoning phase. Rename it to `prefill_seconds`.

3. **"e2e" is not end-to-end.** It is `prompt_ms + predicted_ms` and excludes queue, template, tokenisation and response write. Call it `server_compute_seconds`.

4. **Goodput is computed as a product of marginals, and over two different populations.** DistServe defines attainment per request against **both** SLOs (S20). `P(TTFT≤8)·P(TPOT≤75ms)` equals the joint probability only if the two are independent. They are not: both degrade with context depth, so the product **overstates** failure correlation effects in an unknown direction. The TPOT histogram also only receives requests with `outtok > 1`, while TTFT receives all, so the two fractions do not share a denominator. Emit `llamacpp_req_slo_met_total` / `_slo_evaluated_total` from the per-request record.

5. **J/output-token mixes instruments and silently includes prefill and idle.**
   - An instantaneous power gauge, sampled at rule-evaluation time, is divided by a 5-minute token rate. Numerator and denominator cover different windows, and the ratio spikes towards `W/0.001` when idle (the clamp gives ~1.4e5 J/token at 140 W).
   - All prefill energy and idle floor are attributed to output tokens, so the number rises with context depth for reasons unrelated to decoding.
   - Use `increase(energy_joules_total[w]) / increase(output_tokens_total[w])`, or at least `avg_over_time(power[w])`, and publish prefill-inclusive and idle-subtracted variants separately.
   - The GPU exporter's NVML flavour advertises a total energy counter (S23). NVML's `nvmlDeviceGetTotalEnergyConsumption` is RECALLED, not fetched.
   - The RAPL term (`rate(node_rapl_package_joules_total)`) is correctly a rate; the GPU term is not.

6. **Decode-rate counters only move at request end.** `tokens_predicted_*` and `spec_decode_*` are added in `metrics_on_prediction` on slot reset (S3). A 55 s request contributes nothing for 55 s and then arrives as one step:
   - `llm:decode_tokens_per_second:rate5m` reads zero during long generations.
   - `llm:mtp_acceptance:rate5m < 0.45 for 15m` can fire, or fail to fire, according to request boundaries rather than acceptance.
   - Prompt counters are near-real-time, so prefill and decode rates are not comparable on the same panel.

7. **`llm:kv_cache_utilization_ratio` is not utilisation.**
   - `n_tokens_max` is a lifetime maximum sequence length that never decreases, even though its TYPE says counter; a single 250K request pins the panel at ~0.95 until restart.
   - The 262144 is hardcoded (breaks under router mode or another `-c`).
   - It counts tokens, not KV memory, so it misses `-ctxcp 32` checkpoints and the draft context.
   - Real KV occupancy is not exposed upstream by design (S7).

8. **Two gauges are unsafe with more than one reader.** `prompt_tokens_seconds` and `predicted_tokens_seconds` are averaged since the *last scrape by anyone* (S3). Any second reader (a debug curl, Netdata's Prometheus collector if it is ever pointed there, llama-swap) steals windows from Prometheus. Do not chart them; use counter ratios.

9. **Quantile error at the SLO edge.** TTFT buckets `…4, 8, 15…`: `histogram_quantile(0.95)` interpolates linearly inside a bucket, so a p95 in (8, 15] carries up to ±3.5 s of error (S17). The goodput thresholds (8 s, 75 ms) sit on bucket edges, which is correct. Keep them there, and add 6 and 10 for resolution.

10. **The per-request acceptance histogram is unweighted.** A mean of per-request ratios is not the rate. The rate rule is correctly token-weighted; label the histogram as a per-request distribution. Also, historical acceptance values of exactly 1.000 on short generations are degenerate (PN-61), so exclude requests with `draft_n < ~100` from the histogram.

11. **The exporter has no supervision.**
    - `docker logs -f` exits when the container stops. The pipeline is a bare `bash -c` (PID 3821541, started 22:07:59Z, four minutes after the container's 22:03:52Z start, so it was relaunched by hand).
    - All in-memory histograms reset on restart. `rate()` tolerates that, but gaps are silent.
    - The `pending` dict leaks entries for tasks that never print timings.
    - `LlamaServerDown` covers `llamacpp.*`, so an exporter death pages as "server down".

12. **The clock is not wall time.** Log prefixes are time since process start (S24 sample `3.48.865.894`). The exporter stamps nothing, so per-request events cannot be joined to GPU power or to the CSV logger. `docker logs --timestamps` prefixes daemon wall-clock RFC3339 (RECALLED).

13. **Naming.** The names `llamacpp:*` contain colons, which the Prometheus data model reserves for recording rules (RECALLED, not fetched). That is upstream's choice, but do not copy it. The exporter's `ttft/tpot/e2e` names claim standard semantics (OTel/vLLM) that they do not have (items 2–3).

---

## 3. Recommendations for this host

**Decision: use a transparent streaming proxy as the primary per-request instrument. Join it to the server's own `timings`, keep log-tailing as a cross-check, and poll `/slots` for live state.**

| Method | Sees queue, TTFT, ITL, errors, finish_reason, reasoning split | Server-internal splits | Risk |
|---|---|---|---|
| Log tail (current) | none of them | prefill/decode/draft/depth | clock, supervision, no finish reason |
| `/slots` polling (1 Hz) | in-flight only, no history | live depth, `n_decoded`, cache hit | 1 s resolution; exposes sampling params |
| **Proxy** | **all** | yes, via the final chunk's `timings` (sent automatically on streams, S2) | one hop of latency; must be crash-transparent |

Concrete plan:

1. **Proxy (P0).** A small async reverse proxy (e.g. aiohttp/uvicorn) on a new client-facing port; clients move to it, and llama.cpp stays bound as-is.
   - **Timestamps per request:** arrival, upstream-connect, first chunk, first `reasoning_content`, first `content`, every chunk (for ITL and tokens per chunk), last byte, HTTP status, client disconnect.
   - **Parsed:** `finish_reason`, `usage`, `timings{cache_n, prompt_n, prompt_ms, predicted_n, predicted_ms, draft_n, draft_n_accepted}`.
   - **Derived:** queue ≈ first_chunk − arrival − prompt_ms.
   - **Labels:** `model` (from body), `endpoint`, `client` (API key or source IP), `thinking` (`chat_template_kwargs.enable_thinking`), `stream`.
   - **Emit** OTel GenAI metric names and buckets (S13) as Prometheus histograms, plus one OTel span per request (S14). A Tempo/Jaeger backend is optional; spans can simply go to JSONL.
   - **Joint SLO counter:** the per-request predicate from §2.4.
   - **Pass bytes through unmodified.** Never inject `timings_per_token`, `n_probs` or `include_usage` into client requests: that changes client payloads, and `n_probs` adds cost.
   - **Never originate requests.** With `-np 1`, any synthetic probe request queues behind, or blocks, a real one.

2. **Exporter fixes (keep it, as a cross-check).**
   - Rename `ttft`→`prefill_seconds` and `e2e`→`server_compute_seconds`, and `reason=length`→`context_limit`.
   - Read `docker logs -f --timestamps` and stamp wall time.
   - Increment `cache_tok` from `/slots` or drop it.
   - Parse `mean len` into a histogram.
   - Run it under a systemd unit with `Restart=always` and a retry loop around `docker logs`.
   - Give it its own `up` alert.

3. **`/slots` poller (P0 for KV).** At 1 Hz, export gauges:
   - `llamacpp_slot_sequence_tokens = n_prompt_tokens + n_decoded`
   - `.../n_ctx` as the "KV fill (tokens)" gauge
   - `is_processing`
   - `n_prompt_tokens_cache`

   Replace `llm:kv_cache_utilization_ratio` with it. Keep `n_tokens_max` only as "max depth since start". Do **not** use `?fail_on_no_slot=1` from monitoring; it is a load-balancer readiness probe.

4. **Rules.**
   - Joint goodput from counters.
   - `J/token = increase(gpu_energy_joules_total[5m]) / increase(output_tokens_total[5m])` (switch nvidia_gpu_exporter to its NVML flavour for the energy counter, S23), plus an idle-subtracted variant.
   - Mean acceptance length `1 + rate(accepted)/rate(drafts)`.
   - Prefix hit ratio from native counters.
   - Add a `for:` guard or `increase(tokens_predicted_total[15m]) > N` to the acceptance alert, so request-end lumps and short generations do not trigger it.
   - Stop charting the two scrape-window gauges.

5. **Router / multi-model.** Under `llama-server --models-dir/--models-preset`, `/metrics` needs `?model=<id>` and proxies to that child (S1, S5).
   - Configure one Prometheus job per model (`params: {model: [...]}`) and relabel `model`.
   - Expect counter resets on every load/unload, and serve-from-cache during `--sleep-idle-seconds`.
   - Model load time becomes user latency: measure `/health` 503→200 and label the first request after a load `cold=true` in the proxy.
   - llama-swap documents `/metrics` as "system and GPU metrics for prometheus", `/running`, and `/logs/stream/{model_id}` (S22). Its Prometheus exposure of *token/latency* metrics is **not confirmed**, so the proxy stays necessary. If llama-swap is adopted, put the proxy in front of it.

6. **Offline instruments.**
   - `llama-bench` measures pp/tg at `-d <depth>`, `-r` repetitions, `-o json/jsonl/sql` output, and "do[es] not include the times for tokenization and for sampling" (S11).
   - Neither it nor `llama-batched-bench` is in `llamacpp-mtp:latest`, and neither can run while the server holds both GPUs. They are benchmarking tools, not telemetry.
   - `--perf` enables libllama internal timings. I found no documented GGML/CUDA *profiling* environment variable in `docs/build.md` (only `GGML_CUDA_ENABLE_UNIFIED_MEMORY`, `GGML_CUDA_P2P`, `GGML_CUDA_CUBLAS_COMPUTE_TYPE`, `CUDA_SCALE_LAUNCH_QUEUES`, S12). For kernel profiling use Nsight Systems (RECALLED) on a dedicated run, never on the serving container.
   - `-v` / `-lv` and `--log-prompts-dir` write prompts to disk. That is a privacy and disk hazard on a 43 GB root; do not enable them for telemetry.

7. **Upstream to track.** PR #27012 (first native histogram), issue #23632 (KV usage, stalled), issue #27572 (MTP acceptance race at `-np > 1`, relevant before ever raising `-np`).

---

## 4. Sources

| ID | Title | Authors / org | Year | URL | Type | Status |
|---|---|---|---|---|---|---|
| S1 | llama.cpp HTTP Server README | ggml-org / llama.cpp contributors | 2026 | https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md | engine docs | FETCHED |
| S2 | `server-task.cpp` (`to_metrics`, timings, `prompt_progress`, finish_reason) | ggml-org | 2026 | https://github.com/ggml-org/llama.cpp/blob/master/tools/server/server-task.cpp | source | FETCHED |
| S3 | `server-context.cpp` (metrics accounting, bucket reset, truncated, print_timings) | ggml-org | 2026 | https://github.com/ggml-org/llama.cpp/blob/master/tools/server/server-context.cpp | source | FETCHED |
| S4 | `server-common.h` / `server-common.cpp` (`server_slot_stats`) | ggml-org | 2026 | https://github.com/ggml-org/llama.cpp/tree/master/tools/server | source | FETCHED |
| S5 | `server.cpp` (routes; router `/metrics` proxy) | ggml-org | 2026 | https://github.com/ggml-org/llama.cpp/blob/master/tools/server/server.cpp | source | FETCHED |
| S6 | PR #22879 "docs: fix metrics endpoint description in server README" | llama.cpp contributor | 2026 | https://github.com/ggml-org/llama.cpp/pull/22879 | PR | FETCHED (API) |
| S7 | PR #13660 "kv-cache : simplify the interface" | Georgi Gerganov (ggml-org) | 2025 | https://github.com/ggml-org/llama.cpp/pull/13660 | PR + diff | FETCHED (API) |
| S8 | Issue #23632 "Feature Request: expose KV cache utilization for /metrics endpoint" | EJainDev | 2026 | https://github.com/ggml-org/llama.cpp/issues/23632 | issue | FETCHED |
| S9 | PR #27012 "server : add Prometheus histogram for request context sizes" (open) | boxcee | 2026 | https://github.com/ggml-org/llama.cpp/pull/27012 | PR | FETCHED (API) |
| S10 | GitHub search listings: PR #23188 (ggml-rpc OTel tracing), issue #27572 (draft-mtp acceptance race) | ggml-org contributors | 2026 | https://github.com/ggml-org/llama.cpp/pull/23188 · /issues/27572 | PR/issue titles only | FETCHED (titles only) |
| S11 | llama-bench README | ggml-org | 2026 | https://github.com/ggml-org/llama.cpp/blob/master/tools/llama-bench/README.md | engine docs | FETCHED |
| S12 | llama.cpp `docs/build.md` (CUDA env vars) | ggml-org | 2026 | https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md | engine docs | FETCHED |
| S13 | Semantic conventions for generative AI metrics | OpenTelemetry (CNCF) | 2026 | https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-metrics.md | spec (Development) | FETCHED |
| S14 | Semantic conventions for generative AI spans | OpenTelemetry (CNCF) | 2026 | https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-spans.md | spec | FETCHED |
| S15 | vLLM design doc: Metrics | vLLM project | 2026 | https://github.com/vllm-project/vllm/blob/main/docs/design/metrics.md | engine docs | FETCHED |
| S16 | vLLM `v1/metrics/stats.py`, `loggers.py`, `v1/spec_decode/metrics.py` | vLLM project | 2026 | https://github.com/vllm-project/vllm/tree/main/vllm/v1/metrics | source | FETCHED |
| S17 | Histograms and summaries | Prometheus authors (CNCF) | 2026 | https://prometheus.io/docs/practices/histograms/ | official docs | FETCHED |
| S18 | Metric and label naming | Prometheus authors (CNCF) | 2026 | https://prometheus.io/docs/practices/naming/ | official docs | FETCHED |
| S19 | Llama 2 70B: An MLPerf Inference Benchmark for Large Language Models | Atta-fosu (Intel), Arunkumar (d-Matrix), Lokhmotov (KRAI), Nanjappa (NVIDIA), Hubara & Szutenberg (Intel Habana), Hodak (AMD), Rasquinha (Google), Jiang (NVIDIA) — MLCommons | 2024 | https://mlcommons.org/2024/03/mlperf-llama2-70b/ | benchmark body post | FETCHED |
| S20 | DistServe: Disaggregating Prefill and Decoding for Goodput-optimized LLM Serving, arXiv:2401.09670 | Zhong, Liu, Chen, Hu, Zhu, Liu, Jin, Zhang — Peking University, StepFun, UC San Diego | 2024 | https://arxiv.org/abs/2401.09670 | paper (OSDI'24) | FETCHED |
| S21 | GenAI-Perf README (metrics table) | NVIDIA | 2025 | https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/perf_analyzer/genai-perf/README.html | vendor docs | FETCHED |
| S22 | llama-swap README | mostlygeek (project maintainer) | 2026 | https://github.com/mostlygeek/llama-swap | project docs (not a lab) | FETCHED |
| S23 | nvidia_gpu_exporter README | utkuozdemir (project maintainer) | 2026 | https://github.com/utkuozdemir/nvidia_gpu_exporter | project docs | FETCHED |
| S24 | Live inspection of `qwen38-serve` (b1-d222767): `/metrics`, `/slots`, `/props`, `/health`, `--help`, `docker inspect`, `/app/*.so` string checks; `/srv/bench/telemetry` exporter and rules | this host | 2026-09-14 | <CLIENT_ADDRESS>:8080 | primary observation | FETCHED |
| R1 | NVML `nvmlDeviceGetTotalEnergyConsumption` | NVIDIA | — | https://docs.nvidia.com/deploy/nvml-api/ | API docs | RECALLED |
| R2 | Prometheus data model: colons reserved for recording rules | Prometheus authors | — | https://prometheus.io/docs/concepts/data_model/ | official docs | RECALLED |
| R3 | `docker logs --timestamps` | Docker Inc. | — | https://docs.docker.com/reference/cli/docker/container/logs/ | official docs | RECALLED |