# Lens C: hardware, energy, host, output-quality and workload telemetry for multivac

I checked the live stack read-only on 2026-09-14, around 22:20 UTC. The server was idle, with one request served since it started. Every "Probed" claim below comes from a command I ran on multivac this session; the rest cite sources listed in section 4.

**Headline:** 4 of the 7 derived recording rules I queried return nothing today, or can never return anything:
- **J/token, both variants:** always empty (vector matching).
- **Goodput:** always empty (the `le` label is normalised).
- **Truncation ratio:** never measures budget exhaustion (wrong log field).

The fifth, `kv_cache_utilization_ratio`, returns a value, but it is a high-water mark rather than current usage (section 2, item 7). Separately, the energy fix is already available on this hardware: the NVML energy counter and GPM profiling both answer on the GeForce RTX 5060 Ti.

## 1. Metric inventory

Status is PRESENT / PARTIAL / ABSENT against the coverage you described, corrected where the probe disagreed.

### 1a. Serving: latency, traffic, errors, saturation

| metric (canonical · engine names) | definition / unit | source | multivac | how to get it here | pri |
|---|---|---|---|---|---|
| **TTFT** · OTel `gen_ai.server.time_to_first_token` · vLLM `vllm:time_to_first_token_seconds` | Histogram, s. Time from request arrival to the first output token, successful responses only. vLLM measures it from frontend arrival, so queueing is included. | S1, S2 | PARTIAL: the exporter's "ttft" is `prompt eval time`, which excludes queue, HTTP, templating and tokenisation | Server side: `timings.prompt_ms` plus queue time (not logged, S3). The correct value needs a proxy that timestamps the arrival and the first SSE chunk. | P0: the user-facing SLO, and it is mis-defined today |
| **Time to first *answer* token** (thinking models) | s. Time from arrival to the first `content` token after reasoning ends | No standard. OpenAI exposes the reasoning/answer split (S16). | ABSENT | Proxy on a streaming response: the first delta carrying `content` rather than `reasoning_content` (llama-server `--reasoning-format deepseek`, probed) | P0: thinking is on by default, so TTFT alone says nothing about when the user sees an answer |
| **TPOT** · OTel `gen_ai.server.time_per_output_token` | Histogram, s. Time per output token after the first, successful responses, one observation per request | S1 | PRESENT (`decode_ms/(n_out-1)`), with a caveat in section 2 | Log line, or `timings.predicted_ms / predicted_n` | P0 |
| **ITL** · vLLM `vllm:inter_token_latency_seconds` · OTel client `gen_ai.client.operation.time_per_output_chunk` | Histogram, s. Gap between consecutive tokens or chunks, one observation per gap | S2, S1 | ABSENT | Client-side streaming probe or SSE proxy. llama.cpp can also emit per-token timings (`timings_per_token`, visible in `/slots` params). | P1: MTP n=2 emits tokens in bursts, so the mean TPOT hides a bimodal ITL |
| **E2E latency** · OTel `gen_ai.server.request.duration` · `vllm:e2e_request_latency_seconds` | Histogram, s. Arrival to last token | S1, S2 | PARTIAL: the exporter uses the server's `total time`, which is `t_prompt + t_gen` only (S3 source) | Proxy | P0 |
| **Queue time** · `vllm:request_queue_time_seconds` | Histogram, s | S2 | ABSENT. llama.cpp does not measure it (server-context.cpp, S3). | Proxy (arrival minus `prompt_ms` start is not exposed), or `requests_deferred` as a gauge | P1: with `-np 1`, any concurrency means queueing |
| **Prefill / decode time** · `vllm:request_prefill_time_seconds`, `..._decode_time_seconds` | Histogram, s | S2 | PARTIAL: captured per request but only exported as ttft/tpot | Log line | P2 |
| **Request rate** (Traffic, RED "Rate") | req/s by outcome | S4, S5 | PARTIAL: counts completed requests only | Exporter plus proxy | P1 |
| **Errors** (golden signal / RED) · `vllm:request_success_total{finished_reason="abort"}`, OTel `error.type` | count/s of 4xx, 5xx, aborts, client disconnects | S4, S5, S2, S1 | ABSENT | Proxy only. llama.cpp logs no per-request HTTP status in `print_timing`. | **P0**: SRE S4 also counts "HTTP 200 but wrong content", which on this server is the empty-answer case |
| **Finish reason** · `vllm:request_success_total{finished_reason}` · OpenAI `finish_reason` / `incomplete_details.reason` | counter, stop / length / abort | S2, S16 | **WRONG**: see section 2, item 1 | Response `stop_type` (`eos`, `word`, `limit`, `none`) or OAI `finish_reason`, via a proxy | **P0** |
| **Running / waiting** · `vllm:num_requests_running/_waiting` | gauge | S2 | PRESENT (`llamacpp:requests_processing`, `requests_deferred`) | native | P1 |
| **KV cache usage** · `vllm:kv_cache_usage_perc` | gauge, 0–1, current | S2 | **WRONG**: `n_tokens_max` is a high-water mark since start | `/slots`: `n_prompt_tokens` + `n_decoded` per slot (probed, the endpoint is on by default) | P1 |
| **Prefix-cache hit** · `vllm:prefix_cache_hits` / `_queries` | counters, tokens | S2 | PARTIAL: `llamacpp:prompt_tokens_cached_total` is native; the exporter's `cache_tok` counter is never incremented | `timings.cache_n` per request, native ratio `cached/(prompt+cached)` | P1: decides whether agent turns re-prefill 200 K tokens |
| **Spec-decode acceptance** · `vllm:spec_decode_num_accepted_tokens/_draft_tokens` | ratio | S2 | PRESENT (native per-position counters, plus a per-request histogram) | native | P1 |
| **Context depth at request** | tokens histogram | none (host-specific) | PRESENT | log `n_tokens` at release | P1: decode speed at depth varies 3–5× (PN corpus) |
| **Model load / cold start** | s from start to `/health` 200 | none standard | ABSENT | Serverlog timestamps (`--log-timestamps`), or a `/health` probe in a blackbox exporter | P2 now; P1 once router/llama-swap arrives |
| **Per-request labels** (model, client, thinking on/off) · OTel `gen_ai.request.model`, `gen_ai.provider.name` | attributes | S1 | ABSENT | Proxy only | P1: required before multi-model |

### 1b. Output quality and behaviour

| metric | definition / unit | source | multivac | how here | pri |
|---|---|---|---|---|---|
| **Output length distribution** · OTel `gen_ai.client.token.usage{gen_ai.token.type=output}` | histogram, tokens; buckets are powers of 4 up to 67 M | S1 | PRESENT (`llamacpp_req_output_tokens`), but the buckets stop at 65,536 | log line | P1 |
| **Reasoning-token share** · OpenAI `output_tokens_details.reasoning_tokens` | reasoning / total output tokens | S16 | ABSENT. llama.cpp `usage` has only `completion_tokens` (S3 source). | Proxy: tokenise `reasoning_content` against `/tokenize`, or count reasoning deltas in the stream | **P0**: the empty-answer failure mode on this host (PN-60) is reasoning consuming the budget |
| **Empty-answer rate** | fraction of responses with `finish_reason=length` and empty `content` | OpenAI documents "incomplete before any visible output" (S16) | ABSENT | Proxy | **P0** |
| **Truncation / budget closure** | fraction of responses where `stop_type=limit` | S3, S16 | WRONG (section 2) | Proxy | P0 |
| **Context-full truncation** | llama.cpp `truncated=true`: context filled while `ctx_shift` is off | S3 source | PRESENT, but mislabelled "length" | log | P1 |
| **Tool-call parse failure** | count of tool-call JSON failing the schema | none found in primary docs this session (RECALLED only) | ABSENT | Proxy validates `tool_calls` | P1 once agents use it |
| **Logprob / entropy drift** | mean token logprob and top-k entropy on a fixed canary prompt | Engines expose logprobs (`n_probs`, `post_sampling_probs`, S3). No lab-published production-monitoring standard found this session. | ABSENT | Periodic canary: greedy, `n_probs:5`, fixed prompt, off-peak; alert on a shift in mean NLL | P2: cheap drift detector for a silent image or GGUF change |

### 1c. GPU (USE: utilisation, saturation, errors) and energy

| metric | definition / unit | source | multivac | how here | pri |
|---|---|---|---|---|---|
| **GPU energy counter** · NVML `nvmlDeviceGetTotalEnergyConsumption` · DCGM `DCGM_FI_DEV_TOTAL_ENERGY_CONSUMPTION` (field 156) | mJ since driver reload, Volta and newer | S6, S7, S8, S9 | **ABSENT from Prometheus; probed and working** on both 5060 Ti cards (rc=0; GPU0 5.90 GJ; a 5 s delta gave 11.39 W, which agrees with nvidia-smi's 11.2 W) | Small NVML exporter (ctypes, no install needed), or dcgm-exporter (field in its default CSV) | **P0**: the correct basis for J/token |
| Power, instantaneous and averaged · `nvidia_smi_power_draw_instant_watts` / `_average_watts` · `DCGM_FI_DEV_POWER_USAGE` | W | S6, S10 | PRESENT | exporter | P1, display only, never integrate |
| **Legacy util** · `nvidia_smi_utilization_gpu_ratio` · `DCGM_FI_DEV_GPU_UTIL` | % of the sample period during which *one or more kernels* ran | S11 | PRESENT | exporter | P2: a 100 % reading says nothing about how much of the GPU is doing work |
| **Graphics-engine activity** · `DCGM_FI_PROF_GR_ENGINE_ACTIVE` | ratio averaged over an interval | S7, S8 | ABSENT | NVML GPM metric 1 `gract` (**probed rc=0 on GeForce**) | P1 |
| **SM activity / occupancy** · `DCGM_FI_PROF_SM_ACTIVE`, `DCGM_FI_PROF_SM_OCCUPANCY` | fraction of time at least one warp is active on a streaming multiprocessor, and fraction of warps resident; "0.8 or greater is necessary, but not sufficient" | S8 | ABSENT | NVML GPM 2 `smutil`, 3 `smocc` (**probed rc=0**) | P1: this is what "utilisation" should mean. There is **no** field named `DCGM_FI_PROF_GPU_UTIL` (S12). |
| **Memory bandwidth** · `DCGM_FI_PROF_DRAM_ACTIVE`, GPM `dmmautil`/`dram` | ratio of cycles the memory interface is active | S7, S8 | ABSENT | GPM 10 `dram` (probed rc=0) | P1: decode at depth is memory-bound |
| **PCIe TX/RX** · `DCGM_FI_PROF_PCIE_TX/RX_BYTES` · NVML `nvmlDeviceGetPcieThroughput` · GPM `pcitx` | bytes/s including headers | S7, S8, S6 | ABSENT (the exporter only reports link gen/width) | NVML PcieThroughput (probed: GPU0 1,754 / 1,291 KB/s at idle) or GPM 20 `pcitx` (0.29 MiB/s) | **P1**: layer split with no NVLink sends activations over PCIe |
| PCIe link gen/width | current vs max | S6 | PRESENT | exporter. **Probed:** both cards at Gen1 x4 at idle, capability Gen4 x8. Check under load. | P1 |
| PCIe replay counter · `DCGM_FI_DEV_PCIE_REPLAY_COUNTER` | counter | S7 | ABSENT | NVML `nvmlDeviceGetPcieReplayCounter` (probed rc=0, value 0) | P2 |
| **XID errors** · `DCGM_FI_DEV_XID_ERRORS` | last XID code | S7, S12 | ABSENT | dcgm-exporter, or kernel log (`NVRM: Xid`) through a node_exporter textfile / log alert | **P1**: the CUDA illegal-memory-access failures in this study surface as XIDs |
| Throttle / clock-event reasons | bitmask, plus cumulative seconds | S12 | PRESENT | exporter | P1 |
| Thermal, fan, pstate, ECC | — | S7 | PRESENT | exporter | P2 |

On energy methodology:
- **Energy per output token / per request / per response** · ML.ENERGY and Zeus (S13, S9), MLPerf Power (S14), AI Energy Score in Wh/1,000 queries, GPU-only, CodeCarbon (S15), Google full-stack Wh per prompt (S17). Defined as J = Δenergy counter over a window ÷ Δtokens (or Δrequests), **with idle energy stated separately**. Status: **BROKEN** (section 2). Obtain from the NVML counter plus CPU RAPL. **P0.**
- **Idle / static power** · Google counts idle machine capacity explicitly (S17). W at zero load. Status: ABSENT. Obtain as the counter rate while `requests_processing==0`. **P1**, because it dominates J/token at low traffic.

### 1d. Host

| metric | definition | source | multivac | how here | pri |
|---|---|---|---|---|---|
| PSI cpu / memory / io, `some` and `full` | share of time some or all non-idle tasks stalled; avg10/60/300; `total` in µs | S18 | PRESENT (node_exporter, cAdvisor). **Probed:** system IO `full avg300 = 27–33 %` while idle; per-container IO full ≤4 %; 1.2 GiB swap used; `pswpout` 2.73 M pages. | `rate(node_pressure_io_stalled_seconds_total[5m])` | **P0 investigate**: large host-level IO stall not attributable to any container, with 14 GiB RAM and a 22 GB GGUF |
| Swap in/out, major faults | pages/s | S19 (USE: memory saturation) | PRESENT in node_exporter (`node_vmstat_pswpin/out`, `pgmajfault`); not in rules | node_exporter | P1 |
| Disk read throughput during model load | bytes/s | S19 | PRESENT (node_disk_*), not correlated with loads | annotate Grafana with container start events | P2 |
| CPU package energy (RAPL) | J counter | Zeus / S9 (RECALLED for AMD scope) | PRESENT as `node_rapl_package_joules_total` (package-0 domain on the Ryzen) | node_exporter | P1. Package only: no DRAM, board, PSU or fans; wall power is unmeasurable (no BMC). |

## 2. Correctness problems in the current implementation

Items 1–3 were verified against live Prometheus 3.14.0 and llama.cpp source.

1. **Finish-reason "length" is taken from the wrong flag.**
   - What the source does: in `server-context.cpp`, `slot.truncated = true` is set only when `!ctx_shift && n_tokens+1 >= n_ctx`, i.e. the context window filled. `STOP_TYPE_LIMIT` is also set when `n_predict`/`max_tokens` is exhausted (`!slot.has_budget()`), and that path leaves `truncated=0`. The OAI layer maps anything other than EOS/WORD to `finish_reason="length"` (S3 source).
   - Consequence: every budget-exhausted response is counted as `reason="stop"`. That is exactly the PN-60 failure mode (reasoning consuming a 128-token budget) the alert was written for. A client disconnect or cancellation also releases the slot and is counted as "stop".
   - The live series confirms it: only `reason="stop"` exists, so `llm:truncation_ratio:5m` returns an **empty vector** and `TruncationRateHigh` can never fire.
2. **Both J/token rules return an empty result forever.**
   - Cause: `sum(nvidia_smi_power_draw_instant_watts)` has no labels, while `clamp_min(rate(llamacpp_req_output_tokens_total[5m]),…)` carries `{instance,job}`. A vector/vector operation without `on()` matches nothing. Verified: `llm:joules_per_output_token:rate5m` gives `result: []`.
   - Adding `on()` exposes the second bug: at idle the rule gives **22,350 J/token**, because 22.35 W is divided by the clamped rate 0.001. That is the idle-division hazard you flagged.
   - Methodological problems remain even after both fixes:
     - (a) An instant 1-scrape sample divided by a 5-minute rate is a window mismatch.
     - (b) nvidia-smi and NVML power are sampled. On A100/H100 only about 25 % of runtime is covered, and correcting the method reduced energy error by an average of 35 % (S10, Univ. of Oxford). Energy should come from the counter (S6, S9, S13).
     - (c) The denominator is output tokens only, while prefill energy for 200 K-token prompts sits in the numerator. Report J/request, and J/token split by phase or labelled "all energy ÷ output tokens".
     - (d) Idle power is folded in with no way to separate it (Google counts idle capacity as its own term, S17).
     - (e) Gate the result on traffic, e.g. `and on() rate(tokens[5m]) > 0.1`, instead of `clamp_min`.
3. **Goodput can never evaluate.** Prometheus 3.x normalises classic-histogram `le` values on ingest. The stored buckets are `le="8.0"` (verified with `count by (le)`), so the selector `{le="8"}` matches nothing and the rule is empty. The TPOT bucket `0.075` happens to survive, but the product is empty anyway. Two further problems:
   - **Product of marginals ≠ joint.** Goodput is the rate of requests meeting *both* SLOs (DistServe, RECALLED, arXiv 2401.09670). TTFT and TPOT are positively correlated through context depth, so the product under-states the joint pass rate whenever failures co-occur. Compute the joint pass in the exporter per request (`llamacpp_req_slo_pass_total{ttft_ok,tpot_ok}`).
   - It is a *ratio*, not goodput. Goodput is a rate (req/s meeting SLO).
4. **TTFT is prefill wall time, not TTFT.** It excludes queue (unmeasured, S3), HTTP, chat templating and tokenisation. vLLM and OTel measure from arrival (S1, S2). For a thinking model, the first *answer* token can arrive thousands of tokens later. Rename the metric to `prefill_seconds` and measure TTFT and TTFAT at a proxy.
5. **"e2e" is `t_prompt + t_gen`**, missing queue and I/O. Rename it `server_processing_seconds`.
6. **TPOT divisor.** `eval time` covers `n_gen` tokens. Dividing by `n_out-1` is only correct if the first token's sampling time sits inside prompt eval. I did not confirm that in source, so verify it against `timings.predicted_ms/predicted_n` on a known request. TPOT is also one observation per request, so it is a mean that hides MTP burst jitter; ITL is the distribution (S2).
7. **"KV utilization" = `n_tokens_max/262144`** is a monotone high-water mark since process start, with a hardcoded window. Once any long request happens it stays high forever. Use `/slots` current tokens ÷ `n_ctx` (both fields are present in `/slots`).
8. **Bucket ceilings clip the real tail.**
   - TTFT tops out at 300 s, but a full-window prefill at ~570 tok/s (PN-measured) takes about 460 s. The observation lands in `+Inf`, and `histogram_quantile` then reports the highest finite bound (S20), so p99 reads **300 s**.
   - E2E tops out at 640 s and output-token buckets at 65,536.
   - Add buckets up to 900 s and 3,600 s, or move to native histograms. They are stable since Prometheus 3.8 but need protobuf exposition, which the stdlib text exporter cannot produce (S21).
9. **Exporter details.**
   - The `cache_tok` counter is declared but never incremented.
   - The acceptance histogram observes at `print_timing`, before release.
   - Lines without a `task` share the `"_"` bucket.
   - A container restart ends `docker logs -f`; systemd restarts the pipe (Restart=always, probed), so counters reset. `rate()` tolerates that, but requests in flight are lost.
   - `requests_per_minute` counts completions only.
10. **Utilisation.** Any panel built on `nvidia_smi_utilization_gpu_ratio` measures "one or more kernels executing" (S11), not how much of the GPU is doing work. Use GPM `smutil`/`gract` (S8).
11. **Alert hygiene.**
    - `GpuThrottling` fires on `sw_power_cap`, which is expected at a 180 W limit during prefill. Split it into thermal/HW-slowdown (warning) and power-cap (info).
    - `VramNearWall` uses 15,900 MiB while its own annotation calls 15,650 the practical ceiling. Live usage is 15,302 / 15,044 MiB.
    - There is no error-rate alert (SRE's third golden signal, S4).

## 3. Implementation recommendations for this host

1. **Fix the four dead rules first; no GPU time needed.**
   - `le="8.0"` / `le="0.075"`.
   - `/ on()` for J/token, gated on traffic rather than `clamp_min`.
   - A joint SLO counter in the exporter.
   - Finish reason from `stop_type`. That field is not in the log, so this needs item 3.
   - Add a unit test that queries every recording rule and fails on an empty vector while traffic exists. That would have caught all four.
2. **Replace power-based energy with the NVML counter.** Probed: the energy API, PCIe throughput, the replay counter and **GPM profiling all return success on GeForce Blackwell sm120**.
   - A ~60-line ctypes exporter (the same approach I used to probe) can expose `gpu_energy_joules_total` (mJ/1000, counter), `gpu_pcie_{tx,rx}_bytes_per_second`, and `gpu_gpm_{gract,smutil,smocc,dram}_ratio`.
   - Then: `llm:joules_per_output_token = sum(rate(gpu_energy_joules_total[5m])) / on() sum(rate(output_tokens_total[5m]))`, gated on traffic.
   - Also `llm:gpu_idle_watts` = counter rate while `requests_processing==0`.
   - Report J/request and Wh/1,000 requests (the AI Energy Score unit, S15), GPU-only, with CPU RAPL shown separately and a note that wall power is unmeasurable.
   - Caveats:
     - **DCGM PROF on GeForce is not confirmed by NVIDIA.** DCGM docs say "limited DCGM functionality is available on non-datacenter GPUs" (S22). The open GitHub issues on 4090/5090 and 3090 have no maintainer answer (S23, S24).
     - The NVML GPM path returning rc=0 with idle zeros plus a non-zero `pcitx` proves the API answers. It does **not** prove the activity ratios are correct under load. Validate once against a known decode (expect `smutil` near 0.8–1.0 on the active card during layer-split decode).
     - Do not run dcgm-exporter alongside the serving container without testing; a GPM consumer in a second process is untested here.
3. **Add a thin reverse proxy** in front of `<CLIENT_ADDRESS>:8080`. It is the only way to get queue time, true TTFT, time to first answer token, ITL, HTTP errors, aborts, `finish_reason`, reasoning-token share, empty-answer rate, tool-call validity and per-request labels (model, client, thinking on/off). It also stays valid when llama-server router mode or llama-swap arrives (`--models-dir` and `--models-max` exist in this build, probed).
   - Emit OTel-named histograms with the OTel bucket sets (S1), extended for long context.
   - Keep the log exporter for server-side prefill/decode and depth.
4. **Dashboard layout, one row per method.**
   - Golden signals / RED (S4, S5): request rate by outcome, error and abort rate, TTFT / TTFAT / ITL / E2E p50/p95/p99 (vLLM's own dashboard panels are E2E, TTFT, ITL percentiles and TPS, S25), queue depth.
   - USE per resource (S19), per card, because layer split makes GPU1 the binding card: GPM `smutil`, `dram`, VRAM used vs wall, throttle seconds, XID; PCIe TX/RX with link gen/width; host PSI memory and IO `full`, swap in/out, RAPL.
   - LLM-specific: tokens/s at depth (scatter of TPOT vs `context_depth`, since depth-0 and at-depth decode differ 3–5×), MTP acceptance by position, prefix-cache hit ratio, reasoning share, finish-reason stack, empty-answer rate.
   - Energy: counter-based J/request, J/output-token gated on traffic, idle W, cumulative Wh.
5. **Investigate the host IO pressure now.** System-wide `io full avg300 ≈ 27–33 %` while idle, 1.2 GiB swapped out, and under 4 % attributable to any container. That points at host-level reclaim or swap, and is plausibly page-cache churn from the mmap'd 22 GB GGUF on a 14 GiB host. Correlate `node_pressure_io_stalled_seconds_total` with `node_vmstat_pswpout` and `pgmajfault`. If it spikes during prefill or reloads, it is a latency source no GPU metric will show.
6. **Check the PCIe link under load.** Both cards read Gen1 x4 at idle (normal ASPM downtraining) against a Gen4 x8 capability. If the link stays at x4 under load, record it as a host constraint on layer-split activation transfer.
7. **Canary for quality drift (P2):** a fixed greedy prompt every N hours off-peak with `n_probs`, storing mean NLL and first-token entropy. It flags image, GGUF or template changes cheaply. Skip it if it would ever contend with user traffic under `-np 1`.

## 4. Sources

| ID | title | authors / org | year | URL | type | status |
|---|---|---|---|---|---|---|
| S1 | GenAI metrics semantic conventions | OpenTelemetry | 2025–26 | https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/main/docs/gen-ai/gen-ai-metrics.md | spec | FETCHED |
| S2 | vLLM Metrics (design doc) | vLLM project | 2026 | https://docs.vllm.ai/en/latest/design/metrics.html | engine docs | FETCHED |
| S3 | llama.cpp server README, `server-context.cpp`, `server-task.cpp` | ggml-org | 2026 | https://github.com/ggml-org/llama.cpp/tree/master/tools/server | engine docs + source | FETCHED |
| S4 | Monitoring Distributed Systems (SRE Book ch. 6) | R. Ewaschuk, ed. B. Beyer, Google | 2016 | https://sre.google/sre-book/monitoring-distributed-systems/ | book | FETCHED |
| S5 | The RED Method: How to Instrument Your Services | T. Wilkie, Grafana Labs | 2018 | https://grafana.com/blog/the-red-method-how-to-instrument-your-services/ | eng. post | RECALLED (search result only) |
| S6 | NVML API Reference: Device Queries | NVIDIA | 2026 | https://docs.nvidia.com/deploy/nvml-api/latest/api/group__nvmlDeviceQueries.html | spec | FETCHED |
| S7 | dcgm-exporter `default-counters.csv` | NVIDIA | 2026 | https://github.com/NVIDIA/dcgm-exporter/blob/main/etc/default-counters.csv | source | FETCHED |
| S8 | DCGM Feature Overview (profiling metrics) | NVIDIA | 2026 | https://docs.nvidia.com/datacenter/dcgm/latest/user-guide/feature-overview.html | docs | FETCHED |
| S9 | Zeus: Measuring GPU energy | ML.ENERGY, U. Michigan | 2024–26 | https://ml.energy/zeus/measure/ | tool docs | FETCHED |
| S9b | Measuring GPU Energy: Best Practices | J.-W. Chung, U. Michigan | 2023 | https://ml.energy/blog/energy/measurement/measuring-gpu-energy-best-practices/ | eng. post | FETCHED |
| S10 | Part-time Power Measurements: nvidia-smi's Lack of Attention (arXiv 2312.02741) | Z. Yang, K. Adamek, W. Armour, Univ. of Oxford (affiliation RECALLED) | 2023/24 | https://arxiv.org/abs/2312.02741 | arXiv | FETCHED |
| S11 | `nvmlUtilization_t` struct | NVIDIA | 2026 | https://docs.nvidia.com/deploy/nvml-api/latest/api/structnvmlUtilization__t.html | spec | FETCHED |
| S12 | DCGM Field IDs | NVIDIA | 2026 | https://docs.nvidia.com/datacenter/dcgm/latest/dcgm-api/dcgm-api-field-ids.html | spec | FETCHED (the page rendered some PROF names with a `_RATIO` suffix that differs from dcgm-exporter's names; treat the exporter CSV names as canonical) |
| S13 | The ML.ENERGY Benchmark (arXiv 2505.06371), NeurIPS D&B 2025 | J.-W. Chung, J. J. Ma, R. Wu, J. Liu, O. J. Kweon, Y. Xia, Z. Wu, M. Chowdhury, U. Michigan | 2025 | https://arxiv.org/abs/2505.06371 | paper | FETCHED (abstract only) |
| S14 | MLPerf Power (arXiv 2410.12032), HPCA 2025 | A. Tschand et al., MLCommons | 2024 | https://arxiv.org/abs/2410.12032 | paper | RECALLED (search result only) |
| S15 | AI Energy Score | Hugging Face (S. Luccioni et al.) | 2025 | https://huggingface.github.io/AIEnergyScore/ | methodology | FETCHED |
| S16 | Reasoning models guide | OpenAI | 2026 | https://developers.openai.com/api/docs/guides/reasoning | vendor docs | FETCHED |
| S17 | Measuring the environmental impact of delivering AI at Google Scale (arXiv 2508.15734) | C. Elsworth, K. Huang, D. Patterson, …, J. Dean, A. Vahdat, B. Gomes, J. Manyika, Google | 2025 | https://arxiv.org/abs/2508.15734 | paper | FETCHED |
| S18 | PSI: Pressure Stall Information | Linux kernel docs | — | https://docs.kernel.org/accounting/psi.html | spec | FETCHED |
| S19 | The USE Method | B. Gregg | 2012 | https://www.brendangregg.com/usemethod.html | method | FETCHED |
| S20 | Histograms and summaries | Prometheus | 2026 | https://prometheus.io/docs/practices/histograms/ | docs | FETCHED |
| S21 | Native histograms specification | Prometheus | 2026 | https://prometheus.io/docs/specs/native_histograms/ | spec | FETCHED |
| S22 | DCGM Getting Started: supported platforms | NVIDIA | 2026 | https://docs.nvidia.com/datacenter/dcgm/latest/user-guide/getting-started.html | docs | FETCHED |
| S23 | DCGM issue #234: GeForce 4090/5090 PROF metrics (no maintainer answer) | GitHub | 2025 | https://github.com/NVIDIA/DCGM/issues/234 | issue | FETCHED |
| S24 | dcgm-exporter issue #152: PROF on RTX 3090 | GitHub | — | https://github.com/NVIDIA/dcgm-exporter/issues/152 | issue | FETCHED |
| S25 | vLLM Monitoring Dashboards | vLLM project | 2026 | https://docs.vllm.ai/en/latest/examples/observability/dashboards/ | docs | FETCHED |
| S26 | DynamoLLM (arXiv 2408.00741) | J. Stojkovic et al., UIUC + Microsoft (affiliation RECALLED) | 2024 | https://arxiv.org/abs/2408.00741 | paper | RECALLED (search result only) |
| S27 | POLCA: Power Oversubscription in LLM Cloud Providers (arXiv 2308.12908) | P. Patel et al., Microsoft (RECALLED) | 2023 | https://arxiv.org/abs/2308.12908 | paper | RECALLED (search result only) |
| S28 | llm-d monitoring docs | llm-d project | 2026 | https://github.com/llm-d/llm-d/blob/main/docs/monitoring/README.md | docs | RECALLED (search result only; panel list not opened) |
| S29 | DistServe (goodput definition), arXiv 2401.09670 | Y. Zhong et al., PKU / UCSD | 2024 | https://arxiv.org/abs/2401.09670 | paper | RECALLED |

Not covered this session: Microsoft's POLCA and DynamoLLM characterisation numbers, the NVIDIA DCGM Grafana dashboard 12239 panel list (the page shows no panels without importing it), and llm-d panel titles. I found no lab-published standard for logprob/entropy drift monitoring or tool-call parse-failure metrics, so treat those rows as host-design recommendations rather than standards.

Host evidence (all read-only): the rules file `/srv/bench/telemetry/prometheus/etc/rules/llm.rules.yml`, the exporter `/srv/bench/telemetry/llamacpp_log_exporter.py`, and its unit `/srv/bench/telemetry/staging/llamacpp-log-exporter.service`.