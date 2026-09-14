# llamacpp-sidecar

Prometheus exporter for llama.cpp servers (plan `docs/build-stream/2026-09-14-llm-serving-telemetry.md`
§3.2). Replaces `llamacpp_log_exporter.py`. Stdlib only, plus PyYAML for `--config`.

For every server in `targets.yml` it:

- polls `GET /health` and `GET /slots` every `poll_interval_s` and `GET /props` every 60 s. In router
  mode it sends `?model=<alias>` per model. **It never reads upstream `/metrics`**, because each GET
  resets llama.cpp's gauge windows.
- runs `docker inspect <container>` every 5 s. It reads `State.StartedAt` (restarts, start time,
  load duration) and `Args` (launch provenance).
- follows `docker logs -f --timestamps --since <now>` to read per-request `print_timing` / `release`
  lines, log levels and error events.

## Config

`--config /srv/bench/telemetry/etc/targets.yml` reads `servers:` and `sidecar: {listen,
poll_interval_s}`. See `../etc/targets.example.yml`. CLI overrides for side-port testing:

| flag | effect |
|---|---|
| `--listen HOST:PORT` | exposition address (default `127.0.0.1:9900`) |
| `--server NAME` | monitor only this server |
| `--upstream URL`, `--container NAME` | override for the single selected server |
| `--poll-interval S` | poll period |
| `--no-docker` | HTTP polling only (no lifecycle, launch info or logs) |
| `--upstream URL --model ALIAS --name N` | run without any config file |

## Metrics

All series carry `server` and `model`. In router mode, process-level and log-derived series carry
`model=""`, because one process serves several models and its log lines are not attributed to a
model. Slot and `server_info` series carry the queried model.

| metric | type | source / definition |
|---|---|---|
| `llamacpp_server_health{state}` | gauge, one-hot | `/health`: 200 → ok, 503 → loading, other HTTP → error, no connection → down |
| `llamacpp_server_start_time_seconds` | gauge | `State.StartedAt` |
| `llamacpp_server_load_duration_seconds` | gauge | StartedAt → first observed `/health` 200 after a non-ok state. If the server was already healthy when first seen, it is recovered once from `docker logs --timestamps`: the daemon timestamp of the first `llama_server: model loaded` (or `listening on` / `server is listening`) line minus StartedAt |
| `llamacpp_server_restarts_total` | counter | changes of (container Id, StartedAt) after the first observation |
| `llamacpp_server_info{build,model_path,n_ctx,total_slots}` | gauge = 1 | `/props` (`build_info`, `model_path`, `default_generation_settings.n_ctx`, `total_slots`) |
| `llamacpp_server_launch_info{ctx,ctk,ctv,ts,sm,spec_type,draft_n_max,ctxcp,batch,ubatch,np,fa,image}` | gauge = 1 | `docker inspect` Args. Short and long spellings, `--flag=value`, bare boolean flags (→ `on`), last occurrence wins, unset → `""` |
| `llamacpp_slot_processing{slot}` | gauge | `is_processing` |
| `llamacpp_slot_kv_tokens{slot}` | gauge | `n_prompt_tokens + next_token[0].n_decoded` |
| `llamacpp_slot_n_ctx{slot}` | gauge | `n_ctx` |
| `llamacpp_slot_prompt_processed_tokens{slot}` | gauge | `n_prompt_tokens_processed` |
| `llamacpp_slot_prompt_cache_tokens{slot}` | gauge | `n_prompt_tokens_cache` |
| `llamacpp_slot_decoded_tokens{slot}` | gauge | `next_token[0].n_decoded` |
| `llamacpp_prefill_seconds` | histogram | log `prompt eval time` ms / 1000 |
| `llamacpp_prefill_tokens` | histogram (tokens) | log prompt eval tokens (uncached) |
| `llamacpp_decode_time_per_token_seconds` | histogram | eval ms / 1000 / (n − 1), n ≥ 2 |
| `llamacpp_decode_seconds_total`, `llamacpp_decode_steps_total` | counter | eval seconds and n − 1, n ≥ 2 |
| `llamacpp_spec_mean_accept_length` | histogram | log `mean len`, only when drafted (`generated`) ≥ 100 (PN-61) |
| `llamacpp_request_context_depth_tokens` | histogram (tokens) | release `n_tokens` |
| `llamacpp_context_limit_hits_total` | counter | release with `truncated = 1` |
| `llamacpp_log_lines_total{level}` | counter | level letter after the uptime prefix (`I`/`W`/`E`/`D`) |
| `llamacpp_log_events_total{event}` | counter | one event per line, first match wins: `cuda_error` (`CUDA error`), `oom` (`out of memory`, `failed to allocate`, `cudaMalloc`), `alloc_retry` (`retrying without`), then for E-level lines only `slot_error` (contains `slot`) or `other_error` |
| `llamacpp_sidecar_log_follow_up` | gauge | 1 while `docker logs -f` is attached |

**Additions beyond the contract:** `llamacpp_requests_released_total` (every release),
`llamacpp_requests_timed_total` (releases that carried timings; cancelled tasks do not), and
`llamacpp_sidecar_tasks_evicted_total` (per-task state dropped after 1 h without a release).

Buckets: latency, TPOT and token bucket lists from plan §3.3. Mean accept length uses
`1 1.25 1.5 1.75 2 2.25 2.5 2.75 3 3.5 4 5 6 8 9 17`. `le` labels are rendered as Python floats
(`8.0`), which is how Prometheus 3 normalises them.

## Log follower semantics

- On sidecar start it follows from *now*, so history is never replayed into counters.
- When the follower exits, it reconnects with exponential backoff (1 → 30 s) from the last daemon
  timestamp consumed. Lines at or before that timestamp are skipped, so reconnects neither
  double-count nor leave gaps.
- On a detected container start transition it resets per-task state (task ids restart with the
  process), terminates the follower and replays from the new `StartedAt`. Load-time `oom` /
  `alloc_retry` events of the new process are therefore counted.
- A task is emitted on its `release` line. Cancelled tasks release without `print_timing`: they count
  in `released` and `context_depth`, not in the prefill or decode families. Progress lines
  (`n_gen = …, tg = …`) are ignored.

## Run

```bash
/srv/bench/telemetry/.venv/bin/python llamacpp_sidecar.py --config /srv/bench/telemetry/etc/targets.yml
# side port against a live server, no config file:
python llamacpp_sidecar.py --listen 127.0.0.1:19900 --upstream http://HOST:8080 --container qwen38-serve --model qwen3.8-27b-ud-q6k --name qwen38-serve
```

The user needs the `docker` group (the unit sets `SupplementaryGroups=docker`). `KillMode=control-group`
stops the `docker logs` children with the service.

## Test

```bash
python -m unittest discover -s tests -v
```

- `tests/test_fixture.py` feeds
  `/srv/bench/server-timings/qwen38-serve-pre-metrics-20260914T2203Z.serverlog` (read-only; override
  with `SIDECAR_FIXTURE`) through the parser. It compares every count and sum with grep/awk run in the
  test on the same file: 292 releases; prefill count, seconds and tokens (278 timed); eval tokens,
  decode steps, seconds and count; accepted and drafted sums and mean-len observations (≥ 100
  drafted); depth sum; truncations; level counts (E = 3); events (oom = 3, alloc_retry = 1). It also
  covers timestamped replay with an overlapping reconnect (dedupe) and load-duration recovery from
  timestamped lines.
- `tests/test_units.py` covers the Args parser (live container argv, long spellings, `=`, bare flags,
  last-wins), RFC3339Nano parsing, slot gauge math, health mapping, event classification, histogram
  rendering, a stub upstream (single-model and router-mode polling, never touching `/metrics`, slots
  cleared when down) and load-duration resolution.

## Known limitations

- `kv_tokens` follows the contract formula. When idle, llama.cpp leaves `n_prompt_tokens` at the last
  task's size, so an idle slot still reports the tokens of its retained cache. It ignores `-ctxcp`
  checkpoint memory.
- 1 Hz polling: during decode at ~30 tok/s the slot gauges lag a direct read by up to one poll.
- Load duration from `/health` has poll resolution (1 s). Restarts faster than the 5 s inspect period
  are still caught (StartedAt changes), but the loading window may be missed; the log recovery then
  supplies the value.
- Launch provenance reads Args only. Flags passed as `LLAMA_ARG_*` environment variables are not
  parsed.
- Router mode is implemented from the documented `?model=` API and tested against a stub only; no
  router-mode server exists on the host.
