# LLM serving telemetry

The telemetry for every model served on llama.cpp on multivac: what is measured, why each metric is
defined the way it is, and where the evidence is.

| you want | go to |
|---|---|
| the plan, decisions (DEC-T1…T9) and ledger (TL-1…TL-4) | [`../build-stream/2026-09-14-llm-serving-telemetry.md`](../build-stream/2026-09-14-llm-serving-telemetry.md) |
| the metric contract (every name, label and definition) | same file, §3 |
| the research, with source tables (fetched or recalled) | [`research/lens-a-llamacpp-surface.md`](research/lens-a-llamacpp-surface.md) · [`lens-b-serving-standards.md`](research/lens-b-serving-standards.md) · [`lens-c-hardware-energy-quality.md`](research/lens-c-hardware-energy-quality.md) |
| the short arXiv-format note | [`article/telemetry-note.tex`](article/telemetry-note.tex) (build: `latexmk -pdf telemetry-note.tex`) |
| the code | [`../../infra/telemetry/`](../../infra/telemetry/): `llm-proxy`, `llamacpp-sidecar`, `gpu-nvml-exporter`, `prometheus`, `grafana`, `power-logger` |

## What runs (deployed 2026-09-14)

| component | role | unit |
|---|---|---|
| llm-proxy | transparent proxy on the client address; per-request TTFT, TTFAT, queue, ITL, finish reason, errors, SLOs, JSONL | `llm-proxy.service` |
| llamacpp-sidecar | `/slots` / `/health` / `/props` poller, log follower, launch provenance | `llamacpp-sidecar.service` |
| gpu-nvml-exporter | NVML energy counter, GPM utilisation, PCIe, XID, per-container VRAM | `gpu-nvml-exporter.service` |
| power-logger v2 | 1 Hz CSV, continuity with the E12 power series | `power-logger.service` |
| Prometheus rules v2 | 51 recording rules, 18 alerts | `tel-prometheus` |
| Grafana | 4 provisioned dashboards in the folder "multivac LLM serving" | `tel-grafana` |

The llama.cpp server listens on loopback; clients reach it only through the proxy.

## Adding a model

Add a `servers:` entry to `/srv/bench/telemetry/etc/targets.yml`, then restart `llm-proxy` and
`llamacpp-sidecar`. For router mode (`--models-dir`), set `router: true` and list the models. Add a
Prometheus `llamacpp` scrape target carrying the `server` label.

## Checks

```bash
cd infra/telemetry/prometheus && /srv/bench/telemetry/.venv/bin/python check_rules_live.py --allow-empty llm:spec_conditional_acceptance --allow-empty llm:gpu_energy_watts:idle_rate1m
```

```bash
cd infra/telemetry/grafana && python3 validate_dashboards.py
```
