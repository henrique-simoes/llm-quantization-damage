# llm-proxy

A transparent reverse proxy that sits between clients and one or more llama.cpp servers and
instruments inference requests. Plan: `docs/build-stream/2026-09-14-llm-serving-telemetry.md`,
§2 (architecture) and §3.1 (the metric contract).

```
clients ──► llm-proxy (<CLIENT_ADDRESS>:8080) ──► llama-server (127.0.0.1:18080)
               ├─ /metrics on 127.0.0.1:9901  (Prometheus job llm-proxy)
               └─ /srv/bench/telemetry/requests/YYYY-MM-DD.jsonl  (one record per request)
```

## What it does

- **Pass-through.** Every method and path is relayed: the WebUI (`GET /`, assets), `/v1/models`,
  `/props`, `/slots`, `/health`, `/tokenize`, `/metrics` (llama.cpp's own), and so on. Status,
  headers and body bytes are unchanged; only hop-by-hop headers are stripped (`Connection` and the
  headers it names, `Keep-Alive`, `TE`, `Trailer`, `Transfer-Encoding`, `Upgrade`, `Proxy-*`).
  The upstream client never adds headers of its own (`Accept-Encoding` matters, because the llama.cpp
  WebUI answers `GET /` with 415 unless gzip was requested). It never decompresses and keeps no cookie jar.
- **No total timeouts.** Only the TCP connect has a timeout (10 s). A full-window prefill (~8 min
  before the first byte) and hour-long streams are fine.
- **Streaming.** Upstream bytes are written to the client as soon as they arrive (`iter_any` →
  `write`, TCP_NODELAY, headers flushed at once). SSE is parsed afterwards, on a side buffer.
- **Instrumented endpoints (POST).** These are `/v1/chat/completions` and `/chat/completions` (chat),
  `/v1/completions`, `/completions`, `/completion` and `/infill` (completions), `/v1/responses`, `/v1/messages`,
  and `/v1/embeddings` and `/embeddings`. The request JSON is parsed read-only; the body is forwarded byte-for-byte and
  nothing is injected (no `timings_per_token`, `n_probs`, `stream_options`).
- **Privacy.** No prompt or completion text is written anywhere. Non-stream reasoning text is held in
  memory only long enough to count its tokens.
- **Client disconnect.** The server runs with `handler_cancellation=True`. A client that goes away
  while the proxy waits on upstream (for example during prefill), or whose socket fails on write,
  makes the proxy close the upstream connection immediately. llama.cpp then cancels the task. The
  request is recorded as `finish_reason=abort`, `error_type=client_disconnect`.
- **Upstream failures.** A refused connect returns 502 with a JSON error; a connect timeout returns 504. A non-2xx upstream response is
  passed through untouched and labelled `http_4xx` / `http_5xx`. If upstream dies mid-stream, the
  client connection is closed so a truncated body cannot look complete.

## Measurement definitions

All times are monotonic and relative to **arrival**, which is when the request headers were
parsed, before the body is read. Wall-clock arrival is recorded in the JSONL.

| quantity | definition |
|---|---|
| token-bearing chunk | an SSE event with non-empty `delta.content`, `delta.reasoning_content` or `delta.tool_calls` (Anthropic: `text_delta` / `thinking_delta` / `input_json_delta`; Responses: `output_text` / `reasoning_text` / `function_call_arguments` deltas; native `/completion`: non-empty `content`). llama.cpp's first chunk is role-only (`{"role":"assistant","content":null}`) and is **excluded** (observed live, see below) |
| TTFT, observed | arrival → first token-bearing chunk (streamed responses) |
| TTFT, derived | E2E − `timings.predicted_ms` (non-stream) |
| TTFAT | arrival → first non-empty answer chunk (streamed only) |
| queue wait | max(0, TTFT − `timings.prompt_ms`); includes HTTP parsing, templating and tokenisation |
| prefill | `timings.prompt_ms` |
| TPOT | `predicted_ms / (predicted_n − 1)` when `predicted_n ≥ 2` |
| ITL | every gap between consecutive token-bearing chunks. Under MTP, accepted drafts arrive as bursts of events in one read, so many gaps are ~0 ms (live: 72 of 128) |
| E2E | arrival → last byte written to the client |
| input / cached / prefill / output tokens | `prompt_n + cache_n` / `cache_n` / `prompt_n` / `predicted_n`; `usage` fields when there are no `timings` |
| reasoning tokens | `usage…reasoning_tokens` if the server sends it; streamed: count of reasoning chunks; non-stream: `POST /tokenize` on the reasoning text after the response is complete |
| empty answer | finished `stop`/`length`, 2xx, no tool calls, empty answer content (non-embeddings) |
| finish_reason | `stop`, `length`, `tool_calls`, `abort`, `error`, `unknown`. Anthropic `end_turn`→stop, `max_tokens`→length, `tool_use`→tool_calls. Native `/completion` `stop_type` `limit`→length, `eos`/`word`→stop. Responses `incomplete`+`max_output_tokens`→length. Successful embeddings→stop |

**Reasoning-token method (evidence, 2026-09-14, live `qwen38-serve` b1-d222767, MTP n=2).**
A streamed thinking-on request with `max_tokens=128` produced 1 role-only chunk, 87
`reasoning_content` chunks, 39 `content` chunks and `timings.predicted_n=128`. The 2-token gap is
the `</think>` boundary, which is emitted in no delta. `POST /tokenize` on the concatenated reasoning
text returned **87 tokens**, exactly the chunk count. So each streamed reasoning chunk carries
one token, even under speculative decoding, and chunks are counted. `/tokenize` was timed during an
active generation: 0.9–1.1 ms, the same as idle (0.9–1.2 ms), so it does not block behind the
slot. It is used for non-stream bodies, where no chunks exist.

**SLO evaluation** (`etc/slo.yml`, example in `../etc/slo.example.yml`). Each class is a
conjunction of clauses `value ≤ le + per_token.seconds × value(per_token.metric)`. The plan does not
say that a clause with a missing input counts as satisfied, so a 2xx request missing **any** input
is **not evaluated**. An example is TPOT with `predicted_n < 2`. Server-side failures (5xx,
upstream connect/timeout/disconnect, in-stream error) are evaluated as not good. 4xx responses and
client aborts are not evaluated.

## Labels

`server` (targets.yml name), `model`, `endpoint` (`chat|completions|responses|messages|embeddings`),
`stream` (the request's `stream` flag), `thinking` (`on|off|default`). The thinking label resolves
in this order: `chat_template_kwargs.enable_thinking`, then `chat_template_kwargs.reasoning_effort`,
then top-level `reasoning_effort`, then Responses `reasoning.effort`, then Anthropic `thinking.type`.
An effort of `none` means off. `default` means nothing was set, and this server's default is
thinking **on**.

`model`: in single-server non-router mode it is the alias fetched from upstream `/props` every 60 s
(not the client's string); before the first fetch it is the first configured alias. In router mode
it is the request's `model` if it is listed in `models`, else `unknown`. With more than one server,
requests are routed by request `model` (or `?model=` on non-inference paths), falling back to
`default_server`. Non-inference paths are relayed and not counted.

## Metrics (`metrics_listen`, default 127.0.0.1:9901)

The metric names, types and buckets match the contract in §3.1: `llm_requests_total`,
`llm_request_errors_total`, `llm_requests_in_flight`, `llm_time_to_first_token_seconds{method}`,
`llm_time_to_first_answer_token_seconds`, `llm_queue_wait_seconds`, `llm_prefill_seconds`,
`llm_time_per_output_token_seconds`, `llm_inter_chunk_latency_seconds`,
`llm_request_duration_seconds`, `llm_request_tokens{type}`, `llm_tokens_total{type}`,
`llm_request_context_tokens`, `llm_request_max_tokens`, `llm_spec_draft_tokens_total`,
`llm_spec_accepted_tokens_total`, `llm_empty_answer_total`, `llm_tool_call_responses_total`,
`llm_slo_evaluated_total{slo}`, `llm_slo_good_total{slo}` and `llm_proxy_upstream_up{upstream}`
(`/health` every 5 s).

Two `error_type` values are **added** beyond the contract: `upstream_disconnect` (upstream closed
mid-response, or before sending headers) and `stream_error` (an `error` object inside a 2xx SSE
stream). A request that never received upstream headers has `status_class="none"`.

## JSONL record

One line per inference request, appended and flushed to `requests_dir/YYYY-MM-DD.jsonl`, keyed by
the arrival date (UTC). Fields:

- `ts`, `id`, `response_id`
- labels, `request_model`, `path`, `tools`, `max_tokens`, `client`
- `status`, `status_class`, `finish_reason`, `upstream_finish_reason`, `stop_type`, `truncated`
- `error_type`, `error_detail`, `empty_answer`, `tool_calls`
- `intervals_s` {headers, ttft, ttfat, queue_wait, prefill, decode, tpot, e2e}, `ttft_method`
- `tokens` {input, cached, prefill, output, reasoning, reasoning_method, context}
- `chunks` {reasoning, answer, tool, parse_errors}
- raw `timings` and `usage` (numbers only), per-class `slo` result (true/false/null)
- `bytes_in` / `bytes_out`
- `chunk_ms` (integer ms after arrival for each token-bearing chunk, capped at 200,000), `chunk_kind`
  (`r`/`a`/`t` per chunk), `chunk_timeline_truncated`

## Configuration

`--config targets.yml` (schema in `../etc/targets.example.yml`; only `servers` and `proxy` are
read). CLI overrides: `--listen`, `--metrics-listen`, `--upstream` (overrides the default server's
upstream), `--requests-dir`, `--slo-file`, `--log-level`. Optional `proxy.health_interval_s` (5)
and `proxy.props_interval_s` (60).

## Run

```bash
python3 -m venv .venv && .venv/bin/pip install -r ../requirements.txt
.venv/bin/python llm_proxy.py --config targets.yml --listen 127.0.0.1:18090 \
    --metrics-listen 127.0.0.1:19901 --upstream http://127.0.0.1:18080
```

Deployment uses `llm-proxy.service` (runs as `multivac`, `Restart=always`). The cut-over and rollback
scripts are in `scripts/`:

- `scripts/run-qwen38-loopback.sh [LABEL]` saves `docker inspect` and `docker logs` to
  `/srv/bench/server-timings/qwen38-serve-<label>-<UTC>.{inspect.json,serverlog}`. It then relaunches
  the container with its exact inspected arguments, image ID, binds, network, GPUs, restart policy and
  extra env, changing only `--host 127.0.0.1 --port 18080`. It waits for `/health` and asserts that
  `/props` `n_ctx` equals `-c`. `scripts/relaunch_args.py` refuses (exit 3) to rebuild a container
  that uses settings it does not reproduce.
- `scripts/rollback-proxy.sh ADDRESS [PORT] [LABEL]` (or `ORIG_HOST`/`ORIG_PORT`) stops
  `llm-proxy.service`, then relaunches the server on the original address with the same log-saving rule.

## Test

```bash
.venv/bin/python -m pytest -q          # from this directory; fake llama.cpp upstream in tests/
```

The fake upstream (`tests/fake_upstream.py`) emits OpenAI chat SSE with a role-only first chunk and
`reasoning_content` deltas, final chunks with `finish_reason` and `timings`, non-stream bodies, native
`/completion`, an Anthropic messages stream, the Responses API, embeddings, 4xx/5xx errors, CRLF-framed
and split events, an in-stream error, a stream that dies mid-way, a slow stream, and a slow-headers
("prefill") request for the disconnect tests.

## Known limitations

- WebSocket upgrades are not proxied; llama.cpp does not use them.
- ITL is per SSE event and cannot separate tokens within an MTP burst. The timeline is kept in JSONL
  for offline analysis.
- On client disconnect there is no final `timings`, so output tokens and TPOT are not recorded
  for aborted requests.
- Request bodies are read fully before forwarding (limit 1 GiB); the request is not streamed upstream.
