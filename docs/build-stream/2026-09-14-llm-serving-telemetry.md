# Build Stream — LLM serving telemetry for llama.cpp on multivac

<!-- STATUS BLOCK -->
```yaml
item: llm-serving-telemetry
branch: main
phase: "Deployed and verified. Telemetry stack live; article drafted with validation results."
stage: S3-operate
status: deployed
blocked_on: null
last: { agent: claude-opus-5, at: 2026-09-14T23:25:00Z, ledger: TL-4 }
next_action: "Nothing required. Owner decisions pending: commit infra/ + docs/ changes; whether to publish the telemetry note. Optional follow-ups: Grafana alert notification channel; exercise the sidecar restart path and XID delivery on a real event; router-mode multi-model when a second model is served."
```
<!-- /STATUS BLOCK -->

## 0. Problem and outcome

**Problem.** multivac serves Qwen3.8-27B (UD-Q6_K) from a llama.cpp server. On 2026-09-14 the
server was relaunched with `--metrics` and a log-tailing exporter plus recording rules were
deployed (TL-1). A three-lens research pass against industry standards, serving-engine sources and
lab/academic literature (`docs/telemetry/research/lens-{a,b,c}-*.md`) found that coverage is thin
and that **most of the derived metrics are wrong or never evaluate**.

**Outcome.** A telemetry stack that, for *every* model served on llama.cpp on this host, measures
what production serving systems and the serving literature measure — with definitions that match
the standards — and a Grafana dashboard set to explore it. Purpose: data to optimise model serving,
llama.cpp launch settings and the host, not a paper claim.

**Out of scope.** Changing the served model or its launch configuration (other than the bind
address, D5); distributed tracing backends (Tempo/Jaeger) and log stores (Loki) — deferred on
14 GiB RAM (DEC-T6); quality canaries that originate requests (DEC-T5).

## 1. What the research found (summary; full text and sources in `docs/telemetry/research/`)

Source classes used: OpenTelemetry GenAI semantic conventions; vLLM / SGLang / TGI / NVIDIA Dynamo
/ AIPerf / GenAI-Perf metric definitions and source code; Kubernetes Gateway API Inference
Extension model-server protocol (llm-d); MLPerf Inference rules; llama.cpp server source and PRs;
NVIDIA NVML / DCGM docs; Prometheus docs; Linux PSI docs; papers — PagedAttention (Berkeley),
DistServe (PKU/UCSD), Sarathi-Serve (Georgia Tech/MSR India), Splitwise (Microsoft), Etalon
(Georgia Tech/MSR), Andes (U. Michigan), Mooncake (Moonshot AI), Llumnix (Alibaba), speculative
decoding (Leviathan et al. Google; Chen et al. DeepMind; EAGLE; Medusa), ML.ENERGY / Zeus
(U. Michigan), Part-time Power Measurements (Oxford), Google's 2025 inference-energy paper;
Google SRE golden signals, RED, USE.

### 1.1 Defects in what was deployed on 2026-09-14 (verified on the live stack)

| # | defect | evidence |
|---|---|---|
| F1 | "TTFT" is llama.cpp prefill wall time: starts at slot prompt start, excludes queue, HTTP, templating, tokenisation. Every standard (OTel, vLLM, AIPerf, MLPerf) times from arrival. With `-np 1` queueing is the dominant user-visible delay. | server-context.cpp `update_prompt_start` |
| F2 | "length" finish reason comes from `truncated`, which llama.cpp sets only on context-window exhaustion. `max_tokens` exhaustion is counted as `stop`. The PN-60 failure mode is invisible; `TruncationRateHigh` can never fire. | only `reason="stop"` series exists |
| F3 | Goodput rule never evaluates: Prometheus 3 normalises `le="8"` to `le="8.0"`. It is also a product of marginals, not joint SLO attainment (DistServe), and a ratio, not goodput. | rule returns `[]` |
| F4 | Both J/token rules never evaluate (label-less `sum()` divided by labelled vector without `on()`); once fixed they give ~22 kJ/token at idle (clamp), mix an instant sample with a 5 m rate, and integrate a sampled power gauge instead of the energy counter. | rule returns `[]` |
| F5 | "KV utilization" = `n_tokens_max / 262144` is a lifetime high-water mark with a hard-coded window. Upstream removed the real KV gauge (PR #13660). | `/metrics` TYPE and source |
| F6 | Decode tok/s rule is biased by n/(n−1) (tokens vs steps) and `tokens_predicted_*` / `spec_decode_*` only advance at request end. | server-context.cpp `metrics_on_prediction` |
| F7 | "e2e" is `prompt_ms + predicted_ms` — not end-to-end. ISL histogram counts uncached tokens only; `cache_tok` counter never incremented. | exporter source |
| F8 | Histogram ceilings clip the real tail: a full-window prefill (~460 s) lands in `+Inf`; output buckets stop at 65,536. | bucket lists |
| F9 | Exporter is coupled to one container name, timestamps are process uptime (not joinable to GPU data), in-flight state lost on restart; exporter death pages as "server down". | exporter + rules |
| F10 | GPU "utilisation" panels would use `nvidia-smi` util (≥1 kernel running), not SM activity; `GpuThrottling` fires on the expected 180 W power cap; no error-rate signal exists at all (golden signal #3). | NVML struct docs, rules |
| F11 | The 1 Hz power logger has been dead since the 2026-09-05 AC power loss (started by hand, no unit), and carries the RAPL counter-wrap defect recorded in POWER-LOG.md. | last CSV row 2026-09-05T16:45:32Z |
| F12 | Grafana has no data source and no dashboard. | Grafana API |

### 1.2 Coverage against the standard taxonomy (before → after this stream)

| family | metrics (standard name) | before | after | instrument |
|---|---|---|---|---|
| Latency | TTFT (arrival→first token), time-to-first-answer-token (reasoning models), queue time, prefill time, TPOT, ITL per gap, E2E, decode time | prefill + TPOT only, mislabelled | all | proxy + sidecar |
| Traffic | request rate by endpoint/model/outcome, interarrival | completions only | all | proxy |
| Errors | HTTP status class, error type, client aborts, upstream failures, empty answers | none | all | proxy |
| Finish | stop / length / tool_calls / abort; context-window hits | wrong | correct | proxy + sidecar |
| Goodput / SLO | joint SLO attainment, goodput (good req/s), depth-normalised SLO | broken | correct | proxy |
| Saturation | running/queued requests, KV fill (current), prefill progress, slot state | high-water only | current | native + sidecar `/slots` |
| Cache | prefix-cache hit ratio (tokens), cached tokens per request | none | all | native + proxy |
| Speculative decoding | draft/accepted counters, acceptance rate, mean acceptance length τ, per-position conditional acceptance | counters + per-request ratio | + τ, per-position α | native + sidecar |
| Request shape | ISL (full), OSL, reasoning vs answer tokens, requested max_tokens, context depth | partial | all | proxy + sidecar |
| Model lifecycle | health state, load duration, restarts, build + launch-config provenance | none | all | sidecar |
| GPU (USE) | energy counter, power, SM activity/occupancy, graphics activity, memory bandwidth, PCIe TX/RX, replay counter, XID, per-process VRAM, throttle, thermal, VRAM vs wall | power/util/temp only | all | NVML exporter + existing exporter |
| Energy | J/output-token (counter-based, traffic-gated), J/request, Wh/1k requests, idle W, CPU RAPL | broken | correct | rules |
| Host (USE) | PSI cpu/mem/io, swap in/out, major faults, disk IO, RAPL | collected, not used | dashboards + rules | node_exporter/cAdvisor |

### 1.3 Deliberately not adopted

- **Native Prometheus histograms** — need protobuf exposition; classic histograms with explicit
  long-context buckets are enough at this scale (DEC-T4).
- **DCGM / dcgm-exporter** — NVIDIA does not document PROF fields on GeForce; NVML GPM answers on
  both cards (probed) and covers the same ratios without a second GPM consumer (DEC-T3).
- **Logprob / entropy canaries, tool-call schema validation** — no lab-published production
  standard found; a canary needs synthetic requests that queue behind real ones at `-np 1`
  (DEC-T5). The proxy records tool-call presence only.
- **Fluidity-index (Etalon) and QoE (Andes)** — computed offline from the proxy's per-request JSONL
  chunk timelines, not live.

## 2. Architecture

```
clients ──► llm-proxy (client address :8080) ──► llama-server (127.0.0.1:18080, --metrics)
               │  per-request metrics :9901            ▲  /metrics  /slots  /health  /props
               │  JSONL request records                │
               ▼                                       │
         Prometheus (:9091) ◄── llamacpp-sidecar (:9900) ── docker logs -f --timestamps, docker inspect
               ▲          ◄── gpu-nvml-exporter (:9836) ── NVML energy / GPM / PCIe / XID / processes
               │          ◄── node_exporter, cAdvisor, nvidia_gpu_exporter (existing)
               ▼
            Grafana (:3000, provisioned datasource + 4 dashboards)
```

- **Transparent cut-over.** The server moves to loopback; the proxy takes over the address clients
  already use, so no client changes (DEC-T1). All paths and methods pass through byte-for-byte;
  only inference endpoints are instrumented. Streams are relayed chunk by chunk, never buffered.
- **Multi-model by configuration.** `/srv/bench/telemetry/etc/targets.yml` lists every llama.cpp
  server (name, upstream URL, container, models). The proxy routes by request `model` when more
  than one upstream exists; the sidecar polls each; router mode (`--models-dir`) is handled with
  `?model=` queries. Adding a model = one YAML entry (DEC-T2).
- **Privacy.** No prompt or completion text is stored anywhere — only sizes, timings, labels.
- **Code of record:** `infra/telemetry/` in this repository; deployed to `/srv/bench/telemetry/`
  by `infra/telemetry/deploy.sh`. Host-specific values (addresses, credentials) live only in
  `/srv/bench/telemetry/etc/` on the host; the repo carries `*.example` files.

## 3. Metric contract (the names T2–T4 must use)

Label set, low cardinality: `server` (targets.yml name), `model` (served alias), `endpoint`
(`chat`|`completions`|`responses`|`messages`|`embeddings`|`other`), `stream` (`true`|`false`),
`thinking` (`on`|`off`|`default`). Buckets in seconds unless stated.

### 3.1 llm-proxy (`:9901`, job `llm-proxy`)

| metric | type | extra labels | definition |
|---|---|---|---|
| `llm_requests_total` | counter | `finish_reason`, `status_class` | every proxied inference request at completion; `finish_reason` ∈ stop, length, tool_calls, abort, error, unknown |
| `llm_request_errors_total` | counter | `error_type` | upstream_connect, upstream_timeout, http_4xx, http_5xx, client_disconnect, parse |
| `llm_requests_in_flight` | gauge | — | requests currently open at the proxy |
| `llm_time_to_first_token_seconds` | histogram | `method`=observed\|derived | arrival → first SSE chunk carrying a token (observed, stream); non-stream: E2E − `timings.predicted_ms` (derived) |
| `llm_time_to_first_answer_token_seconds` | histogram | — | arrival → first `delta.content` (not `reasoning_content`); stream only |
| `llm_queue_wait_seconds` | histogram | — | max(0, TTFT − `timings.prompt_ms`); includes templating/tokenisation (documented) |
| `llm_prefill_seconds` | histogram | — | `timings.prompt_ms` |
| `llm_time_per_output_token_seconds` | histogram | — | `timings.predicted_ms / (predicted_n − 1)`, requests with predicted_n ≥ 2 |
| `llm_inter_chunk_latency_seconds` | histogram | — | one observation per gap between consecutive token-bearing SSE chunks |
| `llm_request_duration_seconds` | histogram | — | arrival → last byte to client |
| `llm_request_tokens` | histogram (tokens) | `type`=input\|cached\|prefill\|output\|reasoning | per request; input = prompt_n + cache_n |
| `llm_tokens_total` | counter | `type` as above | sums of the same |
| `llm_request_context_tokens` | histogram (tokens) | — | input + output at completion |
| `llm_request_max_tokens` | histogram (tokens) | — | requested budget, when set |
| `llm_spec_draft_tokens_total`, `llm_spec_accepted_tokens_total` | counter | — | from `timings.draft_n`, `draft_n_accepted` |
| `llm_empty_answer_total` | counter | — | finished with empty `content` (reasoning-only or nothing) |
| `llm_tool_call_responses_total` | counter | — | responses containing tool calls |
| `llm_slo_evaluated_total`, `llm_slo_good_total` | counter | `slo` | joint per-request predicate per SLO class in `etc/slo.yml` |
| `llm_proxy_upstream_up` | gauge | `upstream` | last upstream health probe (proxy-local, `/health`, no inference) |

Buckets — latency: 0.05 0.1 0.25 0.5 1 2 4 6 8 10 15 30 60 120 300 600 900 1800 3600;
TPOT/ITL: 0.005 0.01 0.02 0.03 0.04 0.05 0.075 0.1 0.15 0.2 0.3 0.5 1 2 5;
tokens: 16 64 256 1024 4096 16384 32768 65536 131072 196608 262144 524288 1048576.

SLO classes (`etc/slo.yml`, host-specific, not MLPerf targets): `interactive` = TTFT ≤ 8 s ∧ TPOT ≤
75 ms; `depth_normalised` = queue ≤ 2 s ∧ prefill ≤ 2 s + 2.5 ms × prefill tokens ∧ TPOT ≤ 100 ms.

JSONL: one record per request in `/srv/bench/telemetry/requests/YYYY-MM-DD.jsonl` (UTC): ids,
labels, wall-clock arrival, all derived intervals, token counts, `timings`, finish reason, status,
and the relative chunk-emission timeline in ms (for offline ITL/fluidity/QoE). No content.

### 3.2 llamacpp-sidecar (`:9900`, job `llamacpp-sidecar`) — replaces `llamacpp_log_exporter`

| metric | type | definition |
|---|---|---|
| `llamacpp_server_health` | gauge, `state`=ok\|loading\|error\|down | one-hot, `/health` at 1 Hz |
| `llamacpp_server_start_time_seconds` | gauge | container `State.StartedAt` |
| `llamacpp_server_load_duration_seconds` | gauge | container start → first `/health` 200 (or log `server is listening`) |
| `llamacpp_server_restarts_total` | counter | container start transitions observed |
| `llamacpp_server_info` | gauge=1, labels `build`, `model_path`, `n_ctx`, `total_slots` | `/props` |
| `llamacpp_server_launch_info` | gauge=1, labels `ctx`, `ctk`, `ctv`, `ts`, `sm`, `spec_type`, `draft_n_max`, `ctxcp`, `batch`, `ubatch`, `np`, `fa`, `image` | parsed from `docker inspect` Args — launch provenance |
| `llamacpp_slot_processing` | gauge, `slot` | `/slots` is_processing |
| `llamacpp_slot_kv_tokens` | gauge, `slot` | n_prompt_tokens + next_token.n_decoded (tokens held in the slot) |
| `llamacpp_slot_n_ctx` | gauge, `slot` | slot context size |
| `llamacpp_slot_prompt_processed_tokens` | gauge, `slot` | prefill progress of the active request |
| `llamacpp_slot_prompt_cache_tokens` | gauge, `slot` | tokens reused from cache for the active request |
| `llamacpp_slot_decoded_tokens` | gauge, `slot` | tokens decoded so far in the active request |
| `llamacpp_prefill_seconds` | histogram | log `prompt eval time` |
| `llamacpp_prefill_tokens` | histogram (tokens) | log prompt eval tokens (uncached) |
| `llamacpp_decode_time_per_token_seconds` | histogram | log eval ms / (n − 1) |
| `llamacpp_decode_seconds_total`, `llamacpp_decode_steps_total` | counter | unbiased decode-rate basis (n − 1 steps) |
| `llamacpp_spec_mean_accept_length` | histogram | log `mean len`, requests with ≥ 100 drafted tokens (PN-61) |
| `llamacpp_request_context_depth_tokens` | histogram (tokens) | log release `n_tokens` |
| `llamacpp_context_limit_hits_total` | counter | release lines with `truncated = 1` |
| `llamacpp_log_lines_total` | counter, `level`=I\|W\|E\|D | log volume by level |
| `llamacpp_log_events_total` | counter, `event`=cuda_error\|oom\|alloc_retry\|slot_error\|other_error | pattern-matched warnings/errors |
| `llamacpp_sidecar_log_follow_up` | gauge | 1 while a `docker logs -f` follower is attached |

All `llamacpp_*` sidecar series carry `server` and `model`.

### 3.3 gpu-nvml-exporter (`:9836`, job `gpu-nvml`)

Labels: `gpu` (index), `uuid`, `name`.

| metric | type | definition |
|---|---|---|
| `nvml_gpu_energy_joules_total` | counter | `nvmlDeviceGetTotalEnergyConsumption` / 1000 |
| `nvml_gpu_power_watts` | gauge | `nvmlDeviceGetPowerUsage` (display only) |
| `nvml_gpu_power_limit_watts` | gauge | enforced limit |
| `nvml_gpu_gpm_ratio` | gauge, `metric`=graphics_util\|sm_util\|sm_occupancy\|mem_bandwidth_util\|fp16_util\|fp32_util\|integer_util | NVML GPM over a ~1 s window, 0–1 |
| `nvml_gpu_pcie_tx_bytes_per_second`, `..._rx_...` | gauge | GPM PCIe per-second (converted to bytes/s) |
| `nvml_gpu_pcie_replay_total` | counter | replay counter |
| `nvml_gpu_xid_events_total` | counter, `xid` | NVML critical-XID events (fallback: kernel log follower) |
| `nvml_gpu_process_memory_bytes` | gauge, `pid`, `container` | per compute process; container resolved via cgroup |
| `nvml_gpu_memory_used_bytes`, `nvml_gpu_memory_total_bytes` | gauge | framebuffer |
| `nvml_exporter_gpm_supported` | gauge | 1 if GPM sampling works |

### 3.4 Recording rules (`llm.rules.yml` v2) — names

`llm:ttft_seconds:p50|p95|p99`, `llm:ttfat_seconds:p95`, `llm:queue_wait_seconds:p95`,
`llm:tpot_seconds:p50|p95`, `llm:itl_seconds:p95|p99`, `llm:e2e_seconds:p95`,
`llm:request_rate:rate5m`, `llm:error_ratio:rate5m`, `llm:abort_ratio:rate5m`,
`llm:length_finish_ratio:rate5m`, `llm:empty_answer_ratio:rate5m`,
`llm:slo_attainment:rate5m{slo}`, `llm:goodput_rps:rate5m{slo}`,
`llm:output_tokens_per_second:rate5m`, `llm:decode_tokens_per_second:rate5m` (unbiased),
`llm:prefill_tokens_per_second:rate5m`, `llm:prefix_cache_hit_ratio:rate5m`,
`llm:reasoning_token_share:rate5m`, `llm:spec_acceptance_rate:rate5m`,
`llm:spec_mean_accept_length:rate5m`, `llm:spec_conditional_acceptance{position}`,
`llm:kv_fill_ratio` (current), `llm:gpu_energy_watts:rate5m` (per gpu and total),
`llm:joules_per_output_token:rate5m` and `llm:joules_per_request:rate5m` (traffic-gated),
`llm:wh_per_1k_requests:rate1h`, `llm:gpu_idle_watts:avg1h`, `llm:cpu_package_watts:rate5m`.
All ratios and quantiles use the same 5 m window (quantiles additionally 30 m for sparse traffic).

Alerts: `LlmProxyDown`, `LlamaServerUnhealthy`, `LlamacppSidecarDown`, `GpuNvmlExporterDown`,
`LlmErrorRateHigh`, `LlmRequestsQueued`, `LlmLengthFinishHigh`, `LlmEmptyAnswersHigh`,
`LlmSloAttainmentLow`, `MtpAcceptanceCollapsed` (traffic-gated), `KvFillNearWindow`,
`GpuThermalSlowdown` (warning) / `GpuPowerCapped` (info), `GpuXid`, `VramNearWall` (15,650 MiB),
`HostIoPressureHigh`, `HostSwapping`. No Alertmanager exists; alerts surface in Grafana.

### 3.5 Dashboards (provisioned, folder "multivac LLM serving")

1. **LLM Serving — Overview** (golden signals / RED): health, model, build, launch config; in-flight,
   queued, KV fill; request rate, error and abort ratios; TTFT / TTFAT / E2E / queue p50-p95-p99;
   output and decode tok/s; SLO attainment and goodput; finish-reason stack; J/token; restarts as
   annotations.
2. **LLM Serving — Request anatomy**: TTFT, ITL, TPOT heatmaps; prefill vs queue decomposition;
   depth vs TPOT; ISL / OSL / reasoning / cached token distributions; prefix-cache hit ratio;
   speculative decoding (acceptance, τ, per-position α, drafted tokens); context-limit hits;
   live slot state (prefill progress, decoded tokens).
3. **GPU & Energy** (USE per card): energy rate and cumulative Wh, J/token, J/request, Wh/1k req,
   idle W; SM activity/occupancy vs legacy util; memory bandwidth; VRAM vs 15,650 MiB wall;
   per-process VRAM; PCIe TX/RX with link gen/width; temperature, throttle seconds, XID.
4. **Host**: CPU and RAPL, memory, swap in/out, major faults, PSI cpu/mem/io, disk IO, per-container
   CPU/memory for serving containers, exporter health.

## 4. Phases

| phase | goal | acceptance | status |
|---|---|---|---|
| T1 | Research + gap analysis + this plan | three lens reports with source tables in `docs/telemetry/research/`; this file | **done** (TL-2) |
| T2 | `llm-proxy` (aiohttp): transparent pass-through, streaming relay, instrumentation per §3.1, JSONL records, targets.yml routing, systemd unit | unit tests + smoke against the live server on a side port: stream/non-stream, thinking on/off, `max_tokens` exhaustion → `length` + empty answer, client disconnect → abort, 404 passthrough, WebUI `GET /` passthrough | **done** (TL-4) — 22 tests |
| T3 | `llamacpp-sidecar` (§3.2) and `gpu-nvml-exporter` (§3.3), systemd units | sidecar parses the saved serverlog fixture exactly; `/slots` gauges match a live read; NVML exporter energy delta agrees with `nvidia-smi` power within 10 % over 30 s; GPM values present | **done** (TL-4) — 26 + 4 tests |
| T4 | Rules v2 + alert set (§3.4), `promtool test rules` fixtures, live rule checker; Grafana provisioning (datasource + 4 dashboards generated by a script) | `promtool check` + `promtool test` green; every panel query parses against Prometheus | **done** (TL-4) |
| D1 | Deploy NVML exporter + sidecar (no serving disruption); retire the log exporter unit | both targets up; old unit disabled, not deleted | **done** (TL-4) |
| D2 | Deploy rules v2 (keep v1 as `.bak`) | `promtool check config` green; reload; rules loaded | **done** (TL-4) — 69 rules |
| D3 | Grafana provisioning mount in compose; recreate `tel-grafana` only | datasource healthy; 4 dashboards listed | **done** (TL-4) — Grafana moved to host network (DEC-T8) |
| D4 | Power logger as a systemd unit with RAPL wrap handling; note appended to POWER-LOG.md | service active; no delta > 1 kW | **done** (TL-3) |
| A1 | Short arXiv-format note on serving telemetry and this adaptation (no personal/host/network detail) | `docs/telemetry/article/telemetry-note.tex` compiles; validation section filled from D6 | draft compiled; §5 validation pending |
| D5 | Cut-over: server logs saved; relaunch server on loopback; start proxy on the client address | `/health` via proxy; inference via proxy; Prometheus `llm-proxy` up | **done** (TL-4) |
| D6 | Verification battery V1–V8 (below); ledger entry; commit | all green or recorded as a known limitation | **done** (TL-4) — commit awaits owner |

### Verification battery (D6) — small requests only, `max_tokens` ≤ 256

- **V1** non-stream chat, thinking off → `finish_reason=stop`, derived TTFT, tokens counted.
- **V2** stream chat, thinking on → observed TTFT < TTFAT; reasoning tokens > 0; ITL observations.
- **V3** stream, thinking on, `max_tokens=16` → `finish_reason=length`, `llm_empty_answer_total` +1.
- **V4** two concurrent requests → second shows queue wait > 0; `requests_deferred` seen.
- **V5** client disconnect mid-stream → `error_type=client_disconnect`, finish `abort`.
- **V6** `GET /nonexistent` → 404 passed through, `status_class=4xx` not counted as inference.
- **V7** rule checker: every recording rule non-empty after V1–V5 traffic (energy rules included).
- **V8** dashboards: every panel query returns data or is explicitly traffic-gated; GPM `sm_util`
  > 0.5 on at least one card during V2 decode (validates GPM on GeForce under load).

## 5. Decision log

- **DEC-T1 — transparent proxy on the existing client address.** Only a proxy can observe arrival,
  first chunk, first answer token, per-chunk gaps, HTTP status and disconnects (llama.cpp exposes
  none of them). Moving the server to loopback keeps every client unchanged. Cost: one extra hop
  (sub-ms) and a new single point of failure, mitigated by `Restart=always` and `LlmProxyDown`.
- **DEC-T2 — multi-model via `targets.yml`, not per-model code.** The owner's goal is telemetry for
  every model served on llama.cpp; router mode and additional servers are configuration.
- **DEC-T3 — NVML (incl. GPM) instead of DCGM.** GPM and the energy counter were probed working on
  both GeForce cards; DCGM PROF support on GeForce is undocumented.
- **DEC-T4 — classic histograms with long-context buckets**, not native histograms (text exposition).
- **DEC-T5 — no synthetic traffic in steady state.** With `-np 1` every synthetic request delays a
  real one. The verification battery runs once, at deployment.
- **DEC-T6 — no Tempo/Loki.** Per-request JSONL covers trace-like analysis at zero RAM cost.
- **DEC-T7 — the log exporter is superseded, not deleted.** Its unit is disabled and its file kept.
- **DEC-T8 — Grafana on the host network.** From the compose bridge network the container could not
  reach Prometheus on the host (connection timed out); Prometheus already runs `network_mode: host`,
  so Grafana does too. The datasource URL is `http://localhost:9091`. The compose backup is
  `docker-compose.yml.bak-20260914`.
- **DEC-T9 — pre-create label combinations at zero.** A counter or histogram child born on its
  first event is scraped at 1, and `rate()`/`increase()` never see that step. The proxy creates the
  common combinations at zero (2 endpoints × 2 stream × 3 thinking, ≈3.7 k series); the sidecar
  creates all of its log-derived series at zero.

## 6. Risks

- **R1 cut-over outage** — a server relaunch can fail near the VRAM wall. Mitigation: logs saved
  first; the same flags loaded twice on 2026-09-14; fallbacks `-ts 56,44`, `-c 229376`.
- **R2 proxy correctness** — a buffering or header bug breaks clients. Mitigation: smoke tests on a
  side port before cut-over; a one-command rollback (`rollback-proxy.sh`) restores the direct bind.
- **R3 GPM contention** — a second GPM consumer could perturb readings. Only one is deployed.
- **R4 RAM** — 14 GiB with a 22 GB mmap'd model. Each new process is stdlib/aiohttp, budget
  < 80 MiB RSS each; measured at D6.

## 7. Ledger

- **TL-1 — 2026-09-14T22:03Z.** Server relaunched with `--metrics` (same flags otherwise; logs saved
  to `server-timings/qwen38-serve-pre-metrics-20260914T2203Z.serverlog`); Prometheus config + 24
  rules from the staged set activated (v1 kept as `prometheus.yml.bak-20260914`); log exporter unit
  installed. Verified: 7/7 targets up, inference through the relaunched server.
- **TL-2 — 2026-09-14T22:40Z.** Research T1 complete (three lenses, 165 tool uses, sources in
  `docs/telemetry/research/`). Host probes: NVML energy counter, PCIe throughput and GPM answer on
  both GeForce cards; power logger dead since 2026-09-05; Grafana unprovisioned; four v1 rules
  return empty vectors (F2–F4). This plan written.
- **TL-3 — 2026-09-14T22:40Z.** D4 done. The power logger's `est_system_w` spikes were traced to a
  failed RAPL read returning 0 (the rollover itself was already handled). v2 repeats the previous
  reading on failure and rejects CPU deltas above 250 W; the CSV schema is unchanged; v1 is kept as
  `/srv/bench/power-logger.sh.bak-20260914-v1`. Installed as `power-logger.service` (enabled, active);
  first rows plausible (CPU package 11–20 W, GPUs 21.5 W idle). The CSV has a gap from
  2026-09-05T16:45:32Z to 2026-09-14T22:39:50Z, recorded in `data/raw/e12/POWER-LOG.md`. Host I/O
  pressure check (30 m): stall about 9 %, swap in/out about 40 pages/s. That is lower than the
  research snapshot's 27–33 %; the Host dashboard tracks it. A1 drafted and compiled (9 pages,
  41 references, 16 arXiv entries checked against the arXiv API). TeX Live, lmodern and poppler-utils
  installed through apt so it builds locally. PaperBanana is not installed on the host, so the
  architecture figure is TikZ.
- **TL-4 — 2026-09-14T23:25Z.** T2–T4 built by three parallel Opus 5 agents (medium effort) and
  deployed. D1–D3, D5 and D6 done.
  - **Cut-over.** Logs saved to `server-timings/qwen38-serve-pre-proxy-20260914T2259Z.serverlog`. The
    server relaunched on `127.0.0.1:18080` with identical flags and was healthy after 4 m 39 s. The
    proxy took over the client address; the sidecar measured the load at 276.7 s.
  - **Prometheus.** 9/9 targets up, 69 rules loaded; v1 backups are `prometheus.yml.bak-v1-*` and
    `llm.rules.yml.v1.bak-*`.
  - **V1–V6.** All pass:
    - non-stream `timings` parsed;
    - stream with reasoning: TTFT 1.10 s, TTFAT 9.40 s, 176/78 reasoning/answer chunks, 268 ITL gaps;
    - `max_tokens=16` gave `length` plus an empty answer;
    - of two concurrent requests, the second queued 3.32 s against 0.87 s and failed `depth_normalised`;
    - disconnect gave `abort`/`client_disconnect`;
    - 404 passed through and was not counted.
  - **V7.** 44/69 return data. The 25 empty are 18 alerts not firing, 6 unreachable acceptance
    positions (draft n=2) and the idle helper, which is empty during traffic by design.
  - **V8.** 156 dashboard queries, 0 errors, 150 with data. GPM `sm_util` peaked at 0.503 on GPU0
    during a 256-token decode (bar 0.5, passed narrowly); GPU1 peaked at 0.44.
  - **Overhead.** The proxy adds a median 0.12 ms on `/health`. RSS: proxy 47 MiB, sidecar 28 MiB, NVML
    exporter 17 MiB. VRAM unchanged at 15,294 / 15,030 MiB.
  - **Defects found during D6, fixed and re-verified.**
    1. Duplicate slot series from the pre-reload `llamacpp-req` job name broke a dashboard join and
       doubled `llm:kv_fill_ratio`. Both now aggregate `max by (server, model, slot)`.
    2. `llm:ttfat_seconds:p95` was empty because of first-event invisibility (DEC-T9). After the fix it
       reads 0.475 s.
  - **Transients during the reload.** The 22 GB model reload on 14 GiB RAM drove swap to about
    1,100 pages/s and IO stall to 23 %. `HostSwapping` and `HostIoPressureHigh` went pending and then
    cleared, which is the intended behaviour.
  - **Not exercised.** Sidecar restart detection, XID event delivery, router mode. Grafana alerts
    have no notification channel.
