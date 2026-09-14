# Grafana provisioning — LLM serving dashboards

Plan: `docs/build-stream/2026-09-14-llm-serving-telemetry.md` §3.5.

## Files

| file | purpose |
|---|---|
| `provisioning/datasources/prometheus.yml` | datasource uid `prom-multivac`, `http://host.docker.internal:9091`, default, `timeInterval` 15s |
| `provisioning/dashboards/provider.yml` | file provider → folder "multivac LLM serving", path `/etc/grafana/provisioning/dashboards/json`, `allowUiUpdates: true` |
| `provisioning/dashboards/json/*.json` | generated. Do not hand-edit; change `build_dashboards.py` and regenerate |
| `build_dashboards.py` | stdlib generator for the four dashboards |
| `validate_dashboards.py` | checks every PromQL expression against live Prometheus; optional throwaway import into Grafana |
| `compose-grafana.patch.md` | the exact compose change for D3 (mount + `extra_hosts`) |

## Dashboards (uid → title)

1. `llm-overview` — **LLM Serving — Overview**: health, build and launch config, saturation (in-flight,
   deferred, KV fill), traffic and errors, TTFT / TTFAT / E2E / queue p50-p95-p99, output and decode
   tok/s, TPOT, joint SLO attainment and goodput, J/token, alert list.
2. `llm-request-anatomy` — **LLM Serving — Request anatomy**: TTFT / ITL / TPOT heatmaps, queue + prefill
   decomposition, depth vs TPOT, ISL / OSL / reasoning / cached token shapes, prefix-cache hit ratio,
   speculative decoding (acceptance, τ, α_k, drafted/accepted, per-request τ heatmap), context-limit
   hits, live slot state.
3. `llm-gpu-energy` — **GPU & Energy**: per-card energy-counter power, cumulative Wh, J/token, J/request,
   Wh/1k requests, idle W, GPU vs RAPL; GPM `sm_util` against legacy `nvidia_smi_utilization_gpu_ratio`;
   occupancy and memory bandwidth; VRAM vs the 15,650 MiB wall with per-card headroom; per-process VRAM;
   PCIe TX/RX, link gen and width, replays; temperature, throttle share, XID.
4. `llm-host` — **Host**: CPU by mode, load, RAPL, memory, swap in/out, major faults, PSI cpu/memory/io,
   disk IO, per-container CPU and memory for `name=~"qwen.*|llama.*"`, scrape-target health.

Variables: `server` and `model` come from `label_values(llamacpp_server_info, …)`, plus `gpu` from
`nvml_gpu_power_watts` on the GPU board. Server restarts are drawn as annotations from
`changes(llamacpp_server_start_time_seconds[2m]) > 0`. Every panel has a description giving the
metric definition and its standard source. Legacy `nvidia_smi_*` series carry only `uuid`, so
panels join `index` from `nvidia_smi_gpu_info`.

## Run / test

```bash
cd infra/telemetry/grafana
python3 build_dashboards.py
python3 validate_dashboards.py                   # 0 parse errors required; empty results are OK pre-deploy
python3 validate_dashboards.py --grafana-import  # also import into folder zz-validation, then delete it
```

## Deploy (lead, phase D3)

Follow `compose-grafana.patch.md`, then recreate `tel-grafana` alone.
