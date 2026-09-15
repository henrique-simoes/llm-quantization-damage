# LLM serving telemetry

The telemetry that observes multivac lives in its own repository, **`multivac-telemetry`** (private).
It holds the model-serving proxy, the exporters, Prometheus, Grafana, the compose stack, the build
plan and the research reports. It was built here and moved there on 2026-09-15 (see the remap note
below).

What stays in this repository:

| you want | go to |
|---|---|
| the short arXiv-format note on serving telemetry | [`article/telemetry-note.tex`](article/telemetry-note.tex) · [`article/telemetry-note.pdf`](article/telemetry-note.pdf) (build: `latexmk -pdf telemetry-note.tex`) |
| the 1 Hz power logger behind the published energy series | [`../../infra/telemetry/power-logger/`](../../infra/telemetry/power-logger/) and [`../../data/raw/e12/POWER-LOG.md`](../../data/raw/e12/POWER-LOG.md) |

## Remap note (2026-09-15)

At commit `339a7af` this repository contained the whole telemetry stack. Those paths moved as follows,
and the originals remain readable in history at that commit:

| was (multivac-paper) | now (multivac-telemetry) |
|---|---|
| `infra/telemetry/{llm-proxy,llamacpp-sidecar,gpu-nvml-exporter}/` | `services/…` |
| `infra/telemetry/{prometheus,grafana,etc}/`, `infra/telemetry/requirements.txt` | `prometheus/`, `grafana/`, `etc/`, `requirements.txt` |
| `docs/build-stream/2026-09-14-llm-serving-telemetry.md` | `docs/BUILD-STREAM-2026-09-14.md` |
| `docs/telemetry/research/lens-{a,b,c}-*.md` | `docs/research/` |
| `infra/telemetry/power-logger/` | **stays here** |
| `docs/telemetry/article/` | **stays here** |
