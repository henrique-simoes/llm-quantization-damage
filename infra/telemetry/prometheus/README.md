# Prometheus config and rules v2 — LLM serving telemetry

Plan: `docs/build-stream/2026-09-14-llm-serving-telemetry.md` §3.4. Grafana side: `../grafana/README.md`.

## Files

| file | purpose |
|---|---|
| `prometheus.yml` | full config. Existing jobs (prometheus, node, gpu, cadvisor, netdata) unchanged. `llamacpp` → `127.0.0.1:18080` with `server="qwen38-serve"`; `llamacpp-req` removed; `llm-proxy` :9901, `llamacpp-sidecar` :9900, `gpu-nvml` :9836 added |
| `rules/llm.rules.yml` | 51 recording rules (33 distinct names: every §3.4 name, plus the helper `llm:gpu_energy_watts:idle_rate1m`; the extra rules are 30 m quantile variants, per-position α and per-gpu/total energy) + 18 alerts |
| `tests/llm.rules.test.yml` | promtool unit tests |
| `check_rules_live.py` | query a live Prometheus for every rule; exit non-zero on errors or on empty recording rules while there is traffic |

## Conventions in the rules

- **No `le` selectors.** Prometheus 3 stores `le="8"` as `"8.0"`. SLOs come from the proxy's joint
  per-request counters `llm_slo_good_total` / `llm_slo_evaluated_total`.
- **Quantiles** = `histogram_quantile(q, sum by (le, server, model) (rate(x_bucket[5m]))) >= 0`.
  The `>= 0` drops NaN, so an idle window gives an empty result. Every quantile also exists at 30 m.
  Same rule name, told apart by `window="5m"|"30m"`.
- **Ratios** divide by `(denominator > 0)`, so no traffic gives an empty result. Numerators use
  `or denominator * 0`, so "no error series yet" reads 0 while traffic flows.
- **Energy** comes from `rate(nvml_gpu_energy_joules_total)`, with explicit `on()` joins.
  J/token and J/request are gated with `and on() (sum(rate(llm_tokens_total{type="output"}[5m])) > 0.05)`.
  Idle GPU watts = `avg_over_time` of a recorded 1 m energy rate, kept only while
  `sum(max_over_time(llamacpp:requests_processing[2m])) == 0`.
- **τ** = `1 + rate(accepted) / rate(drafts)`. **α_k** = `rate(pos k) / rate(pos k−1)` and
  α_0 = `rate(pos 0) / rate(drafts)`. PromQL cannot do arithmetic on label values, so positions
  0..7 are enumerated, using `ignoring(position) group_left()` plus a static `position` label.
- `llm:gpu_energy_watts:rate5m` carries `scope="gpu"` (per card) or `scope="total"`.

Alerts beyond the §3.4 list: `TelemetryExporterDown` (node, gpu, cadvisor, netdata, prometheus).

## Test

```bash
cd infra/telemetry/prometheus
# config + rules, with the rules mounted where rule_files points
docker run --rm -v "$PWD":/w:ro -v "$PWD/rules":/etc/prometheus/rules:ro -w /w \
  --entrypoint promtool prom/prometheus:latest check config prometheus.yml
docker run --rm -v "$PWD":/w:ro -w /w --entrypoint promtool prom/prometheus:latest \
  test rules tests/llm.rules.test.yml
python3 check_rules_live.py --expr     # pre-deploy: evaluate rule expressions
python3 check_rules_live.py            # post-deploy: query recorded names
python3 check_rules_live.py --allow-empty llm:spec_conditional_acceptance   # e.g. a no-spec server
```

promtool 3.x compares floats exactly, so the tests assert on `round(expr * 1000)`.

## Deploy (lead, phase D2)

```bash
T=/srv/bench/telemetry/prometheus/etc
sudo cp $T/prometheus.yml $T/prometheus.yml.bak-v1-$(date -u +%Y%m%dT%H%MZ)
sudo cp $T/rules/llm.rules.yml $T/llm.rules.yml.v1.bak    # outside rules/ so the *.yml glob skips it
sudo cp prometheus.yml $T/prometheus.yml
sudo cp rules/llm.rules.yml $T/rules/llm.rules.yml
docker exec tel-prometheus promtool check config /etc/prometheus/prometheus.yml
curl -X POST localhost:9091/-/reload
```

Deploy D2 together with D5 or after it. Until the server moves to `127.0.0.1:18080`, the
`llamacpp` job is down. The same goes for `llm-proxy` and the sidecar until D1/D5, and
`LlmProxyDown` / `LlamaServerUnhealthy` will fire in the meantime. If you apply the config
before the cut-over, keep a temporary second target `<CLIENT_ADDRESS>:8080` in the `llamacpp` job.
Never have two readers of llama.cpp `/metrics`.
