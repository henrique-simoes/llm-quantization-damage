#!/usr/bin/env python3
"""Generate the four provisioned Grafana dashboards (plan 2026-09-14 §3.5).

    python3 build_dashboards.py            # writes provisioning/dashboards/json/*.json

stdlib only. Metric names follow the §3 contract (llm_* proxy, llamacpp_* sidecar, llamacpp:*
native, nvml_* NVML exporter) plus existing exporters whose names were verified against the live
TSDB (nvidia_smi_*, node_*, container_*).
"""
from __future__ import annotations

import json
from pathlib import Path

DS = {"type": "prometheus", "uid": "prom-multivac"}
OUT = Path(__file__).resolve().parent / "provisioning" / "dashboards" / "json"
SCHEMA_VERSION = 41

# Selectors reused everywhere. Native llamacpp:* series only carry `server` (attached at scrape).
SM = 'server=~"$server",model=~"$model"'
S = 'server=~"$server"'
RI = "$__rate_interval"
BY = "server, model"
CONTAINERS = 'name=~"qwen.*|llama.*"'
# Legacy nvidia_smi_* series carry only uuid; join index/name from nvidia_smi_gpu_info (value 1).
GPU_INFO = "* on (uuid) group_left (index, name) nvidia_smi_gpu_info"


class Board:
    """Accumulates panels on a 24-column grid, one row at a time."""

    def __init__(self, uid: str, title: str, description: str, tags: list[str]):
        self.uid, self.title, self.description, self.tags = uid, title, description, tags
        self.panels: list[dict] = []
        self.y = 0
        self.x = 0
        self.row_h = 0
        self.next_id = 1

    def _id(self) -> int:
        self.next_id += 1
        return self.next_id - 1

    def row(self, title: str) -> None:
        self._newline()
        self.panels.append({"type": "row", "title": title, "id": self._id(), "collapsed": False,
                            "gridPos": {"h": 1, "w": 24, "x": 0, "y": self.y}, "panels": []})
        self.y += 1

    def _newline(self) -> None:
        if self.x:
            self.y += self.row_h
        self.x, self.row_h = 0, 0

    def add(self, panel: dict, w: int, h: int) -> None:
        if self.x + w > 24:
            self._newline()
        panel["id"] = self._id()
        panel["gridPos"] = {"h": h, "w": w, "x": self.x, "y": self.y}
        panel.setdefault("datasource", DS)
        self.panels.append(panel)
        self.x += w
        self.row_h = max(self.row_h, h)

    def to_json(self, templating: list[dict], annotations: list[dict] | None = None) -> dict:
        return {
            "uid": self.uid,
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "timezone": "utc",
            "editable": True,
            "graphTooltip": 1,
            "refresh": "30s",
            "schemaVersion": SCHEMA_VERSION,
            "version": 1,
            "time": {"from": "now-6h", "to": "now"},
            "timepicker": {},
            "fiscalYearStartMonth": 0,
            "liveNow": False,
            "links": [{"title": "multivac LLM serving", "type": "dashboards", "tags": ["multivac-llm"],
                       "asDropdown": True, "includeVars": True, "keepTime": True}],
            "templating": {"list": templating},
            "annotations": {"list": [BUILTIN_ANNOTATION] + (annotations or [])},
            "panels": self.panels,
        }


BUILTIN_ANNOTATION = {
    "builtIn": 1, "datasource": {"type": "grafana", "uid": "-- Grafana --"}, "enable": True,
    "hide": True, "iconColor": "rgba(0, 211, 255, 1)", "name": "Annotations & Alerts",
    "type": "dashboard",
}

RESTART_ANNOTATION = {
    "name": "llama-server restarts",
    "datasource": DS,
    "enable": True,
    "iconColor": "red",
    "expr": f"changes(llamacpp_server_start_time_seconds{{{S}}}[2m]) > 0",
    "step": "60s",
    "titleFormat": "llama-server restart",
    "textFormat": "{{server}} started (llamacpp_server_start_time_seconds changed)",
    "useValueForTime": False,
}


def var_query(name: str, label: str, query: str, multi: bool = True) -> dict:
    return {
        "name": name, "label": label, "type": "query", "datasource": DS,
        "definition": query, "query": {"query": query, "refId": f"{name}-var"},
        "refresh": 2, "sort": 1, "multi": multi, "includeAll": True, "allValue": ".*",
        "current": {"selected": True, "text": ["All"], "value": ["$__all"]},
        "hide": 0, "regex": "", "options": [],
    }


def serving_vars() -> list[dict]:
    return [
        var_query("server", "server", "label_values(llamacpp_server_info, server)"),
        var_query("model", "model", 'label_values(llamacpp_server_info{server=~"$server"}, model)'),
    ]


def gpu_vars() -> list[dict]:
    return serving_vars() + [var_query("gpu", "GPU (NVML index)", "label_values(nvml_gpu_power_watts, gpu)")]


# ---------------------------------------------------------------------------------------------- panels

def tgt(expr: str, legend: str = "", ref: str = "A", instant: bool = False, fmt: str = "time_series",
        interval: str = "") -> dict:
    t = {"datasource": DS, "expr": expr, "legendFormat": legend or "__auto", "refId": ref,
         "range": not instant, "instant": instant, "format": fmt, "editorMode": "code"}
    if interval:
        t["interval"] = interval
    return t


def refs(targets: list[dict]) -> list[dict]:
    for i, t in enumerate(targets):
        t["refId"] = chr(ord("A") + i)
    return targets


def thresholds(steps: list[tuple[float | None, str]]) -> dict:
    return {"mode": "absolute", "steps": [{"color": c, "value": v} for v, c in steps]}


def timeseries(title: str, desc: str, targets: list[dict], unit: str = "short", *, calcs=None,
               stack: bool = False, thr: dict | None = None, minv=None, maxv=None, draw: str = "line",
               overrides: list | None = None, thr_style: str = "off", fill: int = 10) -> dict:
    return {
        "type": "timeseries", "title": title, "description": desc, "targets": refs(targets),
        "fieldConfig": {
            "defaults": {
                "unit": unit, "min": minv, "max": maxv,
                "color": {"mode": "palette-classic"},
                "custom": {"drawStyle": draw, "lineWidth": 1, "fillOpacity": fill, "showPoints": "auto",
                           "spanNulls": False, "axisBorderShow": False,
                           "stacking": {"mode": "normal" if stack else "none", "group": "A"},
                           "thresholdsStyle": {"mode": thr_style}},
                "thresholds": thr or thresholds([(None, "green")]),
            },
            "overrides": overrides or [],
        },
        "options": {
            "legend": {"displayMode": "table", "placement": "bottom", "showLegend": True,
                       "calcs": calcs if calcs is not None else ["lastNotNull", "mean", "max"]},
            "tooltip": {"mode": "multi", "sort": "desc"},
        },
    }


def stat(title: str, desc: str, targets: list[dict], unit: str = "short", thr: dict | None = None,
         mappings: list | None = None, color_mode: str = "background", decimals=None,
         text_mode: str = "auto", graph: str = "none", reduce: str = "lastNotNull") -> dict:
    d = {"unit": unit, "thresholds": thr or thresholds([(None, "blue")]), "mappings": mappings or [],
         "color": {"mode": "thresholds"}}
    if decimals is not None:
        d["decimals"] = decimals
    return {
        "type": "stat", "title": title, "description": desc, "targets": refs(targets),
        "fieldConfig": {"defaults": d, "overrides": []},
        "options": {"reduceOptions": {"calcs": [reduce], "fields": "", "values": False},
                    "colorMode": color_mode, "graphMode": graph, "justifyMode": "auto",
                    "orientation": "auto", "textMode": text_mode, "wideLayout": True,
                    "showPercentChange": False},
    }


def gauge(title: str, desc: str, targets: list[dict], unit: str, thr: dict, minv=0, maxv=1) -> dict:
    return {
        "type": "gauge", "title": title, "description": desc, "targets": refs(targets),
        "fieldConfig": {"defaults": {"unit": unit, "min": minv, "max": maxv, "thresholds": thr,
                                     "color": {"mode": "thresholds"}}, "overrides": []},
        "options": {"reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                    "showThresholdLabels": False, "showThresholdMarkers": True},
    }


def bargauge(title: str, desc: str, targets: list[dict], unit: str, thr: dict, minv=0, maxv=None) -> dict:
    return {
        "type": "bargauge", "title": title, "description": desc, "targets": refs(targets),
        "fieldConfig": {"defaults": {"unit": unit, "min": minv, "max": maxv, "thresholds": thr,
                                     "color": {"mode": "thresholds"}}, "overrides": []},
        "options": {"reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                    "orientation": "horizontal", "displayMode": "gradient", "showUnfilled": True,
                    "valueMode": "color", "namePlacement": "auto", "sizing": "auto"},
    }


def heatmap(title: str, desc: str, bucket_metric: str, sel: str, unit: str) -> dict:
    expr = f"sum by (le) (increase({bucket_metric}{{{sel}}}[{RI}]))"
    return {
        "type": "heatmap", "title": title, "description": desc,
        "targets": refs([tgt(expr, "{{le}}", fmt="heatmap")]),
        "fieldConfig": {"defaults": {"custom": {"scaleDistribution": {"type": "linear"},
                                                "hideFrom": {"legend": False, "tooltip": False, "viz": False}}},
                        "overrides": []},
        "options": {
            "calculate": False, "cellGap": 1, "yAxis": {"axisPlacement": "left", "unit": unit, "reverse": False},
            "rowsFrame": {"layout": "auto"}, "color": {"mode": "scheme", "scheme": "Oranges", "fill": "dark-orange",
                                                        "scale": "exponential", "exponent": 0.5, "steps": 64,
                                                        "reverse": False},
            "cellValues": {"unit": "short"}, "showValue": "never",
            "tooltip": {"mode": "single", "yHistogram": True, "showColorScale": False},
            "legend": {"show": True}, "filterValues": {"le": 1e-9}, "exemplars": {"color": "rgba(255,0,255,0.7)"},
        },
    }


def table(title: str, desc: str, targets: list[dict], hide: list[str] | None = None,
          unit: str = "short") -> dict:
    exclude = {k: True for k in (hide or [])}
    return {
        "type": "table", "title": title, "description": desc, "targets": refs(targets),
        "fieldConfig": {"defaults": {"unit": unit, "custom": {"align": "auto", "cellOptions": {"type": "auto"}}},
                        "overrides": []},
        "options": {"showHeader": True, "cellHeight": "sm", "footer": {"show": False, "reducer": ["sum"]}},
        "transformations": [{"id": "merge", "options": {}},
                            {"id": "organize", "options": {"excludeByName": exclude}}],
    }


def text(title: str, content: str) -> dict:
    return {"type": "text", "title": title, "description": "Static notes on how to read this dashboard.",
            "options": {"mode": "markdown", "content": content,
                        "code": {"language": "plaintext", "showLineNumbers": False, "showMiniMap": False}},
            "datasource": None}


def alertlist(title: str) -> dict:
    return {
        "type": "alertlist", "title": title,
        "description": "Prometheus-managed alerts from rules/llm.rules.yml (no Alertmanager on this "
                       "host; alerts surface only here). The table next to it reads ALERTS directly.",
        "options": {"viewMode": "list", "groupMode": "default", "groupBy": [], "maxItems": 30,
                    "sortOrder": 1, "dashboardAlerts": False, "alertName": "", "alertInstanceLabelFilter": "",
                    "datasource": "Prometheus (multivac)",
                    "stateFilter": {"firing": True, "pending": True, "noData": False, "normal": False,
                                    "error": True, "recovering": True},
                    "folder": None},
        "datasource": None,
    }


def alerts_table() -> dict:
    return table("Active alerts (ALERTS series)",
                 "ALERTS{alertstate=~\"firing|pending\"}: Prometheus' own alert-state series, one row per "
                 "active alert instance. Independent of the alert-list panel's rule-source support.",
                 [tgt('ALERTS{alertstate=~"firing|pending"}', instant=True, fmt="table")],
                 hide=["Time", "Value", "__name__", "host"])


def q3(metric: str, sel: str, legend: str, window: str = RI, by: str = BY) -> list[dict]:
    """p50/p95/p99 of a histogram, grouped by server and model."""
    return [tgt(f"histogram_quantile({q}, sum by (le, {by}) (rate({metric}_bucket{{{sel}}}[{window}])))",
                f"p{int(q * 100)} {{{{server}}}}/{{{{model}}}}")
            for q in (0.5, 0.95, 0.99)]


PCT_THR_HIGH_GOOD = thresholds([(None, "red"), (0.9, "orange"), (0.95, "green")])
PCT_THR_LOW_GOOD = thresholds([(None, "green"), (0.02, "orange"), (0.05, "red")])
UNHEALTHY_MAP = [{"type": "value", "options": {"1": {"text": "OK", "color": "green"},
                                                "0": {"text": "NOT OK", "color": "red"}}}]


# ---------------------------------------------------------------------------------------------- 1

def overview() -> dict:
    b = Board("llm-overview", "LLM Serving — Overview",
              "Golden signals (latency, traffic, errors, saturation) and RED view of every llama.cpp server "
              "behind llm-proxy. Latency is timed from request arrival at the proxy (OTel GenAI / vLLM "
              "definitions), not from llama.cpp slot start.", ["multivac-llm", "llm", "overview"])

    b.row("Server state")
    b.add(stat("Health", "llamacpp_server_health{state=\"ok\"}: one-hot health state from the sidecar's 1 Hz "
               "/health probe (ok | loading | error | down). OK = /health returned 200.",
               [tgt(f'max by (server) (llamacpp_server_health{{{S},state="ok"}})', "{{server}}")],
               mappings=UNHEALTHY_MAP, thr=thresholds([(None, "red"), (1, "green")])), 3, 4)
    b.add(stat("Proxy → upstream", "llm_proxy_upstream_up: the proxy's last /health probe of each upstream "
               "(no inference). 0 means clients get errors even if Prometheus can scrape the server.",
               [tgt("max by (upstream) (llm_proxy_upstream_up)", "{{upstream}}")],
               mappings=UNHEALTHY_MAP, thr=thresholds([(None, "red"), (1, "green")])), 3, 4)
    b.add(stat("Uptime", "time() − llamacpp_server_start_time_seconds (container State.StartedAt).",
               [tgt(f"time() - max by (server) (llamacpp_server_start_time_seconds{{{S}}})", "{{server}}")],
               unit="s", color_mode="none"), 3, 4)
    b.add(stat("Load duration", "llamacpp_server_load_duration_seconds: container start → first /health 200 "
               "(model load). Grows with model size and page-cache state on the 14 GiB host.",
               [tgt(f"max by (server) (llamacpp_server_load_duration_seconds{{{S}}})", "{{server}}")],
               unit="s", color_mode="none"), 3, 4)
    b.add(stat("Restarts (range)", "increase(llamacpp_server_restarts_total[$__range]): container start "
               "transitions observed by the sidecar in the selected time range.",
               [tgt(f"sum by (server) (increase(llamacpp_server_restarts_total{{{S}}}[$__range]))", "{{server}}",
                    instant=True)],
               thr=thresholds([(None, "green"), (1, "orange")]), decimals=0), 3, 4)
    b.add(table("Model and build", "llamacpp_server_info labels from /props: build string, model file, "
                "context size and slot count.",
                [tgt(f"llamacpp_server_info{{{SM}}}", instant=True, fmt="table")],
                hide=["Time", "Value", "__name__", "job", "instance", "host"]), 9, 4)
    b.add(table("Launch configuration", "llamacpp_server_launch_info: flags parsed from `docker inspect` Args "
                "(ctx, KV dtypes, -ts, split mode, speculative type and depth, -ctxcp, batch sizes, -np, flash "
                "attention, image). Launch provenance for every measurement on this dashboard.",
                [tgt(f"llamacpp_server_launch_info{{{S}}}", instant=True, fmt="table")],
                hide=["Time", "Value", "__name__", "job", "instance", "host"]), 24, 4)

    b.row("Saturation")
    b.add(stat("In flight (proxy)", "llm_requests_in_flight: requests currently open at the proxy, queued or "
               "running. With -np 1 anything above 1 is waiting.",
               [tgt("sum(llm_requests_in_flight)", "in flight")],
               thr=thresholds([(None, "green"), (2, "orange"), (4, "red")]), graph="area"), 4, 5)
    b.add(stat("Processing", "llamacpp:requests_processing: requests llama-server is running now (native).",
               [tgt(f"sum by (server) (llamacpp:requests_processing{{{S}}})", "{{server}}")],
               color_mode="none", graph="area"), 4, 5)
    b.add(stat("Queued (deferred)", "llamacpp:requests_deferred: requests llama-server has deferred because "
               "no slot is free (native gauge).",
               [tgt(f"sum by (server) (llamacpp:requests_deferred{{{S}}})", "{{server}}")],
               thr=thresholds([(None, "green"), (1, "orange"), (3, "red")]), graph="area"), 4, 5)
    b.add(gauge("KV fill (current)", "llm:kv_fill_ratio = llamacpp_slot_kv_tokens / llamacpp_slot_n_ctx per slot: "
                "tokens the active request holds over the slot window. Current value, not a high-water mark "
                "(cf. vLLM kv_cache_usage_perc).",
                [tgt(f"max by (server, slot) (llm:kv_fill_ratio{{{S}}})", "{{server}} slot {{slot}}")],
                "percentunit", thresholds([(None, "green"), (0.8, "orange"), (0.95, "red")])), 4, 5)
    b.add(timeseries("KV fill and slot activity", "llm:kv_fill_ratio per slot (left) and "
                     "llamacpp_slot_processing (1 while the slot runs a request).",
                     [tgt(f"llm:kv_fill_ratio{{{S}}}", "kv fill {{server}} slot {{slot}}"),
                      tgt(f"llamacpp_slot_processing{{{S}}}", "processing {{server}} slot {{slot}}")],
                     "percentunit", minv=0, maxv=1, calcs=["lastNotNull", "max"]), 8, 5)

    b.row("Traffic and errors")
    b.add(timeseries("Request rate by finish reason", "sum by (finish_reason) rate(llm_requests_total): "
                     "completed inference requests per second. finish_reason from the proxy: stop, length "
                     "(max_tokens exhausted), tool_calls, abort (client disconnect), error, unknown.",
                     [tgt(f"sum by (finish_reason) (rate(llm_requests_total{{{SM}}}[{RI}]))", "{{finish_reason}}")],
                     "reqps", stack=True, draw="bars", fill=80, calcs=["sum", "mean", "max"]), 12, 8)
    b.add(timeseries("Error / abort / length / empty ratios", "Recorded 5 m ratios over completed requests: "
                     "llm:error_ratio (finish_reason=error), llm:abort_ratio (client disconnect), "
                     "llm:length_finish_ratio (max_tokens exhaustion, PN-60), llm:empty_answer_ratio "
                     "(no content). Absent when there was no traffic.",
                     [tgt(f"llm:error_ratio:rate5m{{{SM}}}", "error {{server}}/{{model}}"),
                      tgt(f"llm:abort_ratio:rate5m{{{SM}}}", "abort {{server}}/{{model}}"),
                      tgt(f"llm:length_finish_ratio:rate5m{{{SM}}}", "length {{server}}/{{model}}"),
                      tgt(f"llm:empty_answer_ratio:rate5m{{{SM}}}", "empty {{server}}/{{model}}")],
                     "percentunit", minv=0, thr=PCT_THR_LOW_GOOD), 12, 8)
    b.add(timeseries("Errors by type", "rate(llm_request_errors_total) by error_type: upstream_connect, "
                     "upstream_timeout, http_4xx, http_5xx, client_disconnect, parse. Golden signal #3.",
                     [tgt(f"sum by (error_type) (rate(llm_request_errors_total{{{SM}}}[{RI}]))", "{{error_type}}")],
                     "reqps", stack=True, draw="bars", fill=80, calcs=["sum", "max"]), 12, 7)
    b.add(timeseries("HTTP status classes", "rate(llm_requests_total) by status_class as returned to clients.",
                     [tgt(f"sum by (status_class) (rate(llm_requests_total{{{SM}}}[{RI}]))", "{{status_class}}")],
                     "reqps", stack=True, calcs=["sum", "max"]), 12, 7)

    b.row("Latency (arrival-based)")
    b.add(timeseries("TTFT p50 / p95 / p99", "Time to first token: request arrival at the proxy → first "
                     "token-bearing chunk (observed for streams; E2E − predicted_ms for non-stream). Includes "
                     "queueing, templating and prefill. OTel gen_ai.server.time_to_first_token / vLLM "
                     "time_to_first_token_seconds.",
                     q3("llm_time_to_first_token_seconds", SM, ""), "s", minv=0), 12, 8)
    b.add(timeseries("Time to first answer token p50 / p95 / p99", "TTFAT: arrival → first delta.content that is "
                     "not reasoning_content (streams only). For reasoning models this is the user-visible wait; "
                     "the gap to TTFT is thinking time.",
                     q3("llm_time_to_first_answer_token_seconds", SM, ""), "s", minv=0), 12, 8)
    b.add(timeseries("E2E p50 / p95 / p99", "llm_request_duration_seconds: arrival → last byte to the client. "
                     "vLLM e2e_request_latency_seconds; OTel gen_ai.server.request.duration.",
                     q3("llm_request_duration_seconds", SM, ""), "s", minv=0), 12, 8)
    b.add(timeseries("Queue wait p50 / p95 / p99", "llm_queue_wait_seconds = max(0, TTFT − timings.prompt_ms): "
                     "time not spent in prefill before the first token — slot wait plus HTTP, templating and "
                     "tokenisation. vLLM request_queue_time_seconds analogue.",
                     q3("llm_queue_wait_seconds", SM, ""), "s", minv=0), 12, 8)

    b.row("Throughput")
    b.add(timeseries("Output and decode tokens/s", "llm:output_tokens_per_second:rate5m = rate of output tokens "
                     "delivered (proxy, incl. reasoning). llm:decode_tokens_per_second:rate5m = decode steps "
                     "(n − 1 per request) / decode seconds from the server log: the unbiased per-stream decode "
                     "speed (tokens/time over-states it by n/(n−1)).",
                     [tgt(f"llm:output_tokens_per_second:rate5m{{{SM}}}", "output tok/s {{server}}/{{model}}"),
                      tgt(f"llm:decode_tokens_per_second:rate5m{{{SM}}}", "decode tok/s {{server}}/{{model}}")],
                     "short", minv=0), 12, 8)
    b.add(timeseries("TPOT p50 / p95 / p99", "Time per output token = timings.predicted_ms / (predicted_n − 1) "
                     "per request with ≥ 2 tokens. vLLM time_per_output_token_seconds; MLPerf TPOT.",
                     q3("llm_time_per_output_token_seconds", SM, ""), "s", minv=0), 12, 8)

    b.row("SLO and goodput")
    b.add(timeseries("Joint SLO attainment", "llm:slo_attainment:rate5m{slo}: share of requests meeting EVERY "
                     "bound of the SLO class at once, evaluated per request by the proxy (DistServe joint "
                     "attainment). interactive = TTFT ≤ 8 s ∧ TPOT ≤ 75 ms; depth_normalised = queue ≤ 2 s ∧ "
                     "prefill ≤ 2 s + 2.5 ms × prefill tokens ∧ TPOT ≤ 100 ms (host targets, not MLPerf).",
                     [tgt(f"llm:slo_attainment:rate5m{{{SM}}}", "{{slo}} {{server}}/{{model}}")],
                     "percentunit", minv=0, maxv=1, thr=PCT_THR_HIGH_GOOD, thr_style="line"), 12, 8)
    b.add(timeseries("Goodput", "llm:goodput_rps:rate5m{slo}: requests per second that met the joint SLO "
                     "(DistServe goodput) next to the total request rate.",
                     [tgt(f"llm:goodput_rps:rate5m{{{SM}}}", "goodput {{slo}} {{server}}/{{model}}"),
                      tgt(f"llm:request_rate:rate5m{{{SM}}}", "all requests {{server}}/{{model}}")],
                     "reqps", minv=0), 12, 8)

    b.row("Energy and alerts")
    b.add(stat("J / output token", "llm:joules_per_output_token:rate5m: all GPU energy from the NVML "
               "cumulative counter over 5 m / output tokens in the same window (idle power included). "
               "Traffic-gated: absent below 0.05 output tok/s.",
               [tgt("llm:joules_per_output_token:rate5m", "J/token")], unit="joule", decimals=2,
               color_mode="none", graph="area"), 4, 7)
    b.add(stat("GPU power (energy counter)", "llm:gpu_energy_watts:rate5m{scope=\"total\"}: rate of "
               "nvml_gpu_energy_joules_total summed over GPUs.",
               [tgt('llm:gpu_energy_watts:rate5m{scope="total"}', "W")], unit="watt", decimals=0,
               color_mode="none", graph="area"), 4, 7)
    b.add(alertlist("Alerts"), 8, 7)
    b.add(alerts_table(), 8, 7)

    return b.to_json(serving_vars(), [RESTART_ANNOTATION])


# ---------------------------------------------------------------------------------------------- 2

def anatomy() -> dict:
    b = Board("llm-request-anatomy", "LLM Serving — Request anatomy",
              "Where a request's time and tokens go: latency distributions, prefill vs queue, depth effects, "
              "token shapes, prefix cache, speculative decoding and live slot state.",
              ["multivac-llm", "llm", "anatomy"])

    b.row("Latency distributions (heatmaps of histogram buckets)")
    b.add(heatmap("TTFT distribution", "llm_time_to_first_token_seconds buckets, increase per interval: "
                  "arrival → first token (OTel gen_ai.server.time_to_first_token / vLLM). Buckets reach "
                  "3600 s so full-window prefills are not clipped into +Inf.",
                  "llm_time_to_first_token_seconds_bucket", SM, "s"), 8, 9)
    b.add(heatmap("Inter-chunk latency distribution", "llm_inter_chunk_latency_seconds: one observation per gap "
                  "between consecutive token-bearing SSE chunks (AIPerf/GenAI-Perf inter_token_latency). With "
                  "speculative decoding a chunk can carry several tokens, so gaps are bimodal.",
                  "llm_inter_chunk_latency_seconds_bucket", SM, "s"), 8, 9)
    b.add(heatmap("TPOT distribution", "llm_time_per_output_token_seconds: predicted_ms / (predicted_n − 1) per "
                  "request (vLLM time_per_output_token_seconds, MLPerf TPOT).",
                  "llm_time_per_output_token_seconds_bucket", SM, "s"), 8, 9)
    b.add(timeseries("ITL p50 / p95 / p99", "Quantiles of llm_inter_chunk_latency_seconds (gap-weighted: long "
                     "requests contribute more observations). Recorded 5 m p95/p99: llm:itl_seconds.",
                     q3("llm_inter_chunk_latency_seconds", SM, ""), "s", minv=0), 12, 8)
    b.add(timeseries("Recorded quantiles (5 m and 30 m)", "llm:ttft_seconds:p95, llm:e2e_seconds:p95 and "
                     "llm:tpot_seconds:p95 at both recorded windows. 30 m is steadier under sparse single-slot "
                     "traffic; 5 m reacts faster.",
                     [tgt(f"llm:ttft_seconds:p95{{{SM}}}", "TTFT p95 {{window}} {{server}}"),
                      tgt(f"llm:e2e_seconds:p95{{{SM}}}", "E2E p95 {{window}} {{server}}"),
                      tgt(f"llm:tpot_seconds:p95{{{SM}}}", "TPOT p95 {{window}} {{server}}")],
                     "s", minv=0), 12, 8)

    b.row("Prefill vs queue decomposition")
    b.add(timeseries("Mean TTFT = queue + prefill", "Mean per request over the interval: "
                     "rate(x_sum)/rate(x_count) for llm_queue_wait_seconds and llm_prefill_seconds "
                     "(timings.prompt_ms), stacked; the line is mean TTFT. Queue dominates at -np 1 under "
                     "concurrency; prefill dominates for long, uncached prompts.",
                     [tgt(f"sum by ({BY}) (rate(llm_queue_wait_seconds_sum{{{SM}}}[{RI}])) / sum by ({BY}) "
                          f"(rate(llm_queue_wait_seconds_count{{{SM}}}[{RI}]))", "queue {{server}}/{{model}}"),
                      tgt(f"sum by ({BY}) (rate(llm_prefill_seconds_sum{{{SM}}}[{RI}])) / sum by ({BY}) "
                          f"(rate(llm_prefill_seconds_count{{{SM}}}[{RI}]))", "prefill {{server}}/{{model}}"),
                      tgt(f"sum by ({BY}) (rate(llm_time_to_first_token_seconds_sum{{{SM}}}[{RI}])) / sum by "
                          f"({BY}) (rate(llm_time_to_first_token_seconds_count{{{SM}}}[{RI}]))",
                          "TTFT mean {{server}}/{{model}}")],
                     "s", minv=0, stack=False, calcs=["mean", "max"]), 12, 8)
    b.add(timeseries("Prefill p50 / p95 / p99 and prefill tokens/s", "llm_prefill_seconds quantiles "
                     "(timings.prompt_ms, uncached tokens only) and llm:prefill_tokens_per_second:rate5m "
                     "(native prompt_tokens_total / prompt_seconds_total) on the right axis.",
                     q3("llm_prefill_seconds", SM, "") +
                     [tgt(f"llm:prefill_tokens_per_second:rate5m{{{S}}}", "prefill tok/s {{server}}")],
                     "s", minv=0,
                     overrides=[{"matcher": {"id": "byRegexp", "options": "prefill tok/s.*"},
                                 "properties": [{"id": "unit", "value": "short"},
                                                {"id": "custom.axisPlacement", "value": "right"}]}]), 12, 8)

    b.row("Depth")
    b.add(timeseries("Context depth vs TPOT", "Mean context held at request end "
                     "(llamacpp_request_context_depth_tokens, log release n_tokens; left) against TPOT p50 "
                     "(right). Decode slows with attended depth (3–5× at a full window on this host).",
                     [tgt(f"sum by ({BY}) (rate(llamacpp_request_context_depth_tokens_sum{{{SM}}}[{RI}])) / "
                          f"sum by ({BY}) (rate(llamacpp_request_context_depth_tokens_count{{{SM}}}[{RI}]))",
                          "mean depth {{server}}/{{model}}"),
                      tgt(f"histogram_quantile(0.5, sum by (le, {BY}) "
                          f"(rate(llm_time_per_output_token_seconds_bucket{{{SM}}}[{RI}])))",
                          "TPOT p50 {{server}}/{{model}}")],
                     "short", minv=0,
                     overrides=[{"matcher": {"id": "byRegexp", "options": "TPOT.*"},
                                 "properties": [{"id": "unit", "value": "s"},
                                                {"id": "custom.axisPlacement", "value": "right"}]}]), 12, 8)
    b.add(heatmap("Context depth distribution", "llamacpp_request_context_depth_tokens buckets: tokens in the "
                  "slot when each request released it (input + output).",
                  "llamacpp_request_context_depth_tokens_bucket", SM, "short"), 6, 8)
    b.add(stat("Context-limit hits (range)", "increase(llamacpp_context_limit_hits_total[$__range]): requests "
               "whose release line reported truncated = 1 (context window exhausted, not max_tokens).",
               [tgt(f"sum(increase(llamacpp_context_limit_hits_total{{{SM}}}[$__range]))", "hits", instant=True)],
               thr=thresholds([(None, "green"), (1, "red")]), decimals=0), 6, 8)

    b.row("Token shapes")
    b.add(timeseries("Mean tokens per request by type", "rate(llm_request_tokens_sum)/rate(llm_request_tokens_count) "
                     "per type: input (= prompt_n + cache_n, ISL), cached, prefill (uncached), output (OSL, incl. "
                     "reasoning), reasoning.",
                     [tgt(f"sum by (type) (rate(llm_request_tokens_sum{{{SM}}}[{RI}])) / sum by (type) "
                          f"(rate(llm_request_tokens_count{{{SM}}}[{RI}]))", "{{type}}")],
                     "short", minv=0, calcs=["mean", "max"]), 12, 8)
    b.add(timeseries("Token p50 / p95 by type", "histogram_quantile over llm_request_tokens by type "
                     "(ISL = input, OSL = output).",
                     [tgt(f"histogram_quantile(0.5, sum by (le, type) (rate(llm_request_tokens_bucket{{{SM}}}[{RI}])))",
                          "p50 {{type}}"),
                      tgt(f"histogram_quantile(0.95, sum by (le, type) (rate(llm_request_tokens_bucket{{{SM}}}[{RI}])))",
                          "p95 {{type}}")],
                     "short", minv=0), 12, 8)
    b.add(heatmap("ISL distribution (input tokens)", "llm_request_tokens{type=\"input\"} buckets: full input "
                  "length per request, cached + uncached.",
                  "llm_request_tokens_bucket", f'{SM},type="input"', "short"), 6, 8)
    b.add(heatmap("OSL distribution (output tokens)", "llm_request_tokens{type=\"output\"} buckets.",
                  "llm_request_tokens_bucket", f'{SM},type="output"', "short"), 6, 8)
    b.add(timeseries("Reasoning share and requested budget", "llm:reasoning_token_share:rate5m = reasoning / "
                     "output tokens (left). Mean requested max_tokens (llm_request_max_tokens, right).",
                     [tgt(f"llm:reasoning_token_share:rate5m{{{SM}}}", "reasoning share {{server}}/{{model}}"),
                      tgt(f"sum by ({BY}) (rate(llm_request_max_tokens_sum{{{SM}}}[{RI}])) / sum by ({BY}) "
                          f"(rate(llm_request_max_tokens_count{{{SM}}}[{RI}]))", "mean max_tokens {{server}}/{{model}}")],
                     "percentunit", minv=0,
                     overrides=[{"matcher": {"id": "byRegexp", "options": "mean max_tokens.*"},
                                 "properties": [{"id": "unit", "value": "short"},
                                                {"id": "custom.axisPlacement", "value": "right"}]}]), 12, 8)

    b.row("Prefix cache")
    b.add(timeseries("Prefix-cache hit ratio", "llm:prefix_cache_hit_ratio:rate5m = cached / (cached + evaluated) "
                     "prompt tokens from native llamacpp:prompt_tokens_cached_total and prompt_tokens_total "
                     "(token-weighted; vLLM prefix_cache_hits / prefix_cache_queries).",
                     [tgt(f"llm:prefix_cache_hit_ratio:rate5m{{{S}}}", "{{server}}")],
                     "percentunit", minv=0, maxv=1), 12, 8)
    b.add(timeseries("Cached vs evaluated prompt tokens/s", "rate(llamacpp:prompt_tokens_cached_total) and "
                     "rate(llamacpp:prompt_tokens_total), stacked.",
                     [tgt(f"sum by (server) (rate(llamacpp:prompt_tokens_cached_total{{{S}}}[{RI}]))", "cached {{server}}"),
                      tgt(f"sum by (server) (rate(llamacpp:prompt_tokens_total{{{S}}}[{RI}]))", "evaluated {{server}}")],
                     "short", stack=True, minv=0), 12, 8)

    b.row("Speculative decoding")
    b.add(timeseries("Acceptance rate and mean acceptance length τ", "llm:spec_acceptance_rate:rate5m = accepted "
                     "/ drafted tokens (left). llm:spec_mean_accept_length:rate5m = 1 + accepted / drafts: tokens "
                     "emitted per verification step (τ, EAGLE/Medusa; vLLM mean acceptance length) on the right. "
                     "Native counters advance at request end.",
                     [tgt(f"llm:spec_acceptance_rate:rate5m{{{S}}}", "acceptance {{server}}"),
                      tgt(f"llm:spec_mean_accept_length:rate5m{{{S}}}", "τ {{server}}")],
                     "percentunit", minv=0,
                     overrides=[{"matcher": {"id": "byRegexp", "options": "τ.*"},
                                 "properties": [{"id": "unit", "value": "short"},
                                                {"id": "custom.axisPlacement", "value": "right"}]}]), 12, 8)
    b.add(bargauge("Per-position conditional acceptance α_k", "llm:spec_conditional_acceptance{position=k}: "
                   "α_0 = accepted at position 0 / drafts; α_k = accepted at k / accepted at k−1 (probability "
                   "position k is accepted given k−1 was). Leviathan et al. / vLLM per-position acceptance.",
                   [tgt(f"llm:spec_conditional_acceptance{{{S}}}", "α_{{position}} {{server}}", instant=True)],
                   "percentunit", thresholds([(None, "red"), (0.5, "orange"), (0.75, "green")]), maxv=1), 6, 8)
    b.add(timeseries("Drafted vs accepted tokens/s", "rate(llamacpp:spec_decode_num_draft_tokens_total) and "
                     "rate(llamacpp:spec_decode_num_accepted_tokens_total).",
                     [tgt(f"sum by (server) (rate(llamacpp:spec_decode_num_draft_tokens_total{{{S}}}[{RI}]))", "drafted {{server}}"),
                      tgt(f"sum by (server) (rate(llamacpp:spec_decode_num_accepted_tokens_total{{{S}}}[{RI}]))", "accepted {{server}}")],
                     "short", minv=0), 6, 8)
    b.add(heatmap("Per-request mean acceptance length", "llamacpp_spec_mean_accept_length: log `mean len` per "
                  "request with ≥ 100 drafted tokens (shorter requests give degenerate 1.000 values, PN-61).",
                  "llamacpp_spec_mean_accept_length_bucket", SM, "short"), 12, 8)
    b.add(timeseries("Proxy-side draft acceptance", "rate(llm_spec_accepted_tokens_total) / "
                     "rate(llm_spec_draft_tokens_total) from per-request timings.draft_n / draft_n_accepted, by "
                     "server and model (cross-check of the native ratio).",
                     [tgt(f"sum by ({BY}) (rate(llm_spec_accepted_tokens_total{{{SM}}}[{RI}])) / sum by ({BY}) "
                          f"(rate(llm_spec_draft_tokens_total{{{SM}}}[{RI}]))", "{{server}}/{{model}}")],
                     "percentunit", minv=0, maxv=1), 12, 8)

    b.row("Live slot state")
    b.add(bargauge("Prefill progress", "llamacpp_slot_prompt_processed_tokens / (prompt tokens of the active "
                   "request, approximated by llamacpp_slot_kv_tokens − llamacpp_slot_decoded_tokens) from /slots.",
                   [tgt(f"max by (server, model, slot) (llamacpp_slot_prompt_processed_tokens{{{SM}}}) / "
                        f"clamp_min(max by (server, model, slot) (llamacpp_slot_kv_tokens{{{SM}}}) - "
                        f"max by (server, model, slot) (llamacpp_slot_decoded_tokens{{{SM}}}), 1)",
                        "{{server}} slot {{slot}}", instant=True)],
                   "percentunit", thresholds([(None, "blue")]), maxv=1), 8, 7)
    b.add(timeseries("Slot tokens", "/slots gauges per slot: llamacpp_slot_prompt_processed_tokens (prefill "
                     "progress), llamacpp_slot_prompt_cache_tokens (reused from cache), "
                     "llamacpp_slot_decoded_tokens (generated so far), llamacpp_slot_kv_tokens (held).",
                     [tgt(f"llamacpp_slot_prompt_processed_tokens{{{SM}}}", "prefilled slot {{slot}}"),
                      tgt(f"llamacpp_slot_prompt_cache_tokens{{{SM}}}", "cache reused slot {{slot}}"),
                      tgt(f"llamacpp_slot_decoded_tokens{{{SM}}}", "decoded slot {{slot}}"),
                      tgt(f"llamacpp_slot_kv_tokens{{{SM}}}", "held slot {{slot}}")],
                     "short", minv=0, calcs=["lastNotNull", "max"]), 16, 7)

    return b.to_json(serving_vars(), [RESTART_ANNOTATION])


# ---------------------------------------------------------------------------------------------- 3

def gpu_energy() -> dict:
    b = Board("llm-gpu-energy", "GPU & Energy",
              "USE view per card. Under -sm layer each layer's weights and KV slice live on one card; GPU1 "
              "holds the output layer and draft context and is the binding card. Energy comes from the NVML "
              "cumulative counter, never from integrating sampled power.",
              ["multivac-llm", "gpu", "energy"])
    G = 'gpu=~"$gpu"'

    b.row("Energy")
    b.add(timeseries("GPU power from the energy counter, per card", "rate(nvml_gpu_energy_joules_total) per GPU "
                     "(nvmlDeviceGetTotalEnergyConsumption / 1000), stacked; dashed line = enforced power limit "
                     "sum. Counter-based rates do not miss sub-sample spikes (ML.ENERGY / Zeus method).",
                     [tgt(f"sum by (gpu) (rate(nvml_gpu_energy_joules_total{{{G}}}[{RI}]))", "GPU{{gpu}}"),
                      tgt(f"sum(nvml_gpu_power_limit_watts{{{G}}})", "power limit (sum)")],
                     "watt", stack=True, minv=0,
                     overrides=[{"matcher": {"id": "byName", "options": "power limit (sum)"},
                                 "properties": [{"id": "custom.stacking", "value": {"mode": "none"}},
                                                {"id": "custom.fillOpacity", "value": 0},
                                                {"id": "custom.lineStyle", "value": {"fill": "dash", "dash": [10, 10]}}]}]),
          12, 8)
    b.add(timeseries("Cumulative GPU energy (range)", "increase(nvml_gpu_energy_joules_total[$__range]) / 3600 "
                     "per GPU over the dashboard time range, in watt-hours.",
                     [tgt(f"sum by (gpu) (increase(nvml_gpu_energy_joules_total{{{G}}}[$__range])) / 3600",
                          "GPU{{gpu}}", instant=True)],
                     "watth", draw="bars", fill=80, calcs=["lastNotNull"]), 6, 8)
    b.add(stat("Idle GPU power (1 h)", "llm:gpu_idle_watts:avg1h: mean energy-counter power over the last hour "
               "while llamacpp:requests_processing stayed 0 (both cards; the baseline J/token includes).",
               [tgt("llm:gpu_idle_watts:avg1h", "idle W")], unit="watt", decimals=1, color_mode="none"), 6, 4)
    b.add(stat("Wh per 1k requests (1 h)", "llm:wh_per_1k_requests:rate1h: GPU Wh over the last hour × 1000 / "
               "requests completed in that hour (idle included). Needs ≥ 1 request.",
               [tgt("llm:wh_per_1k_requests:rate1h", "Wh/1k")], unit="watth", decimals=1, color_mode="none"), 6, 4)
    b.add(timeseries("J per output token and J per request", "llm:joules_per_output_token:rate5m (left) and "
                     "llm:joules_per_request:rate5m (right): GPU energy in 5 m / output tokens or completed "
                     "requests in the same window. Traffic-gated (absent below 0.05 output tok/s), so gaps mean "
                     "idle, not zero.",
                     [tgt("llm:joules_per_output_token:rate5m", "J/token"),
                      tgt("llm:joules_per_request:rate5m", "J/request")],
                     "joule", minv=0,
                     overrides=[{"matcher": {"id": "byName", "options": "J/request"},
                                 "properties": [{"id": "custom.axisPlacement", "value": "right"}]}]), 12, 8)
    b.add(timeseries("GPU vs CPU package power", "llm:gpu_energy_watts:rate5m{scope=\"total\"} (NVML counter) and "
                     "llm:cpu_package_watts:rate5m (RAPL package counter). No wall meter exists on this host.",
                     [tgt('llm:gpu_energy_watts:rate5m{scope="total"}', "GPU total"),
                      tgt("llm:cpu_package_watts:rate5m", "CPU package (RAPL)")],
                     "watt", minv=0), 12, 8)

    b.row("Activity: GPM vs legacy utilisation")
    b.add(timeseries("Streaming-multiprocessor activity (GPM sm_util) vs nvidia-smi util", "nvml_gpu_gpm_ratio"
                     "{metric=\"sm_util\"}: fraction of the ~1 s window CUDA kernels actually ran on the SMs "
                     "(NVML GPM, DCGM PROF_SM_ACTIVE analogue). nvidia_smi_utilization_gpu_ratio (legacy): "
                     "fraction of time at least one kernel was running — saturates near 100 % on light work. "
                     "Compare the two per card.",
                     [tgt(f'max by (gpu) (nvml_gpu_gpm_ratio{{{G},metric="sm_util"}})', "GPU{{gpu}} GPM sm_util"),
                      tgt(f"max by (index) (nvidia_smi_utilization_gpu_ratio {GPU_INFO})",
                          "GPU{{index}} nvidia-smi util (legacy)")],
                     "percentunit", minv=0, maxv=1,
                     overrides=[{"matcher": {"id": "byRegexp", "options": ".*legacy.*"},
                                 "properties": [{"id": "custom.lineStyle", "value": {"fill": "dash", "dash": [10, 10]}},
                                                {"id": "custom.fillOpacity", "value": 0}]}]), 12, 8)
    b.add(timeseries("GPM occupancy, graphics and memory bandwidth", "nvml_gpu_gpm_ratio: sm_occupancy "
                     "(fraction of SMs in use), graphics_util (engine activity) and mem_bandwidth_util (memory "
                     "bus activity — the decode bottleneck) per card.",
                     [tgt(f'max by (gpu, metric) (nvml_gpu_gpm_ratio{{{G},metric=~"sm_occupancy|graphics_util|mem_bandwidth_util"}})',
                          "GPU{{gpu}} {{metric}}")],
                     "percentunit", minv=0, maxv=1), 12, 8)
    b.add(timeseries("GPM compute precision mix", "nvml_gpu_gpm_ratio{metric=~\"fp16_util|fp32_util|integer_util\"}.",
                     [tgt(f'max by (gpu, metric) (nvml_gpu_gpm_ratio{{{G},metric=~"fp16_util|fp32_util|integer_util"}})',
                          "GPU{{gpu}} {{metric}}")],
                     "percentunit", minv=0, maxv=1), 12, 7)
    b.add(stat("GPM supported", "nvml_exporter_gpm_supported: 1 if GPM sampling works on the card.",
               [tgt("nvml_exporter_gpm_supported", "GPM")], mappings=UNHEALTHY_MAP,
               thr=thresholds([(None, "red"), (1, "green")])), 4, 7)
    b.add(timeseries("Power draw per card (display)", "nvml_gpu_power_watts: instantaneous NVML power per GPU "
                     "(display only; energy rules use the counter).",
                     [tgt(f"max by (gpu) (nvml_gpu_power_watts{{{G}}})", "GPU{{gpu}}")], "watt", minv=0), 8, 7)

    b.row("Memory: VRAM vs the 15,650 MiB wall")
    b.add(timeseries("VRAM used per card", "nvidia_smi_memory_used_bytes per GPU; red line = 15,650 MiB practical "
                     "wall (card total 16,311 MiB). Under layer split the heavier card OOMs first. NVML framebuffer "
                     "use (nvml_gpu_memory_used_bytes) overlaid when the exporter is up.",
                     [tgt(f"max by (index) (nvidia_smi_memory_used_bytes {GPU_INFO})", "GPU{{index}} nvidia-smi"),
                      tgt(f"max by (gpu) (nvml_gpu_memory_used_bytes{{{G}}})", "GPU{{gpu}} NVML")],
                     "bytes", minv=0, thr_style="line",
                     thr=thresholds([(None, "green"), (15650 * 1024 * 1024, "red")])), 12, 8)
    b.add(bargauge("Headroom to the wall", "(15,650 MiB − used) per card from nvidia_smi_memory_used_bytes. "
                   "Below ~500 MiB a deeper prefill can fail to allocate compute buffers.",
                   [tgt(f"15650 * 1024 * 1024 - max by (index) (nvidia_smi_memory_used_bytes {GPU_INFO})",
                        "GPU{{index}}", instant=True)],
                   "bytes", thresholds([(None, "red"), (300 * 1048576, "orange"), (800 * 1048576, "green")]),
                   minv=None), 6, 8)
    b.add(table("Per-process VRAM", "nvml_gpu_process_memory_bytes: framebuffer used by each compute process, "
                "with its container resolved from the cgroup.",
                [tgt(f"nvml_gpu_process_memory_bytes{{{G}}}", instant=True, fmt="table")],
                hide=["Time", "__name__", "job", "instance", "host", "uuid"], unit="bytes"), 6, 8)

    b.row("PCIe")
    b.add(timeseries("PCIe TX / RX per card", "nvml_gpu_pcie_tx_bytes_per_second (positive) and "
                     "nvml_gpu_pcie_rx_bytes_per_second (negative) from GPM. Layer split sends activations "
                     "between cards over PCIe every token.",
                     [tgt(f"max by (gpu) (nvml_gpu_pcie_tx_bytes_per_second{{{G}}})", "GPU{{gpu}} TX"),
                      tgt(f"-max by (gpu) (nvml_gpu_pcie_rx_bytes_per_second{{{G}}})", "GPU{{gpu}} RX")],
                     "Bps"), 12, 8)
    b.add(table("PCIe link", "nvidia_smi_pcie_link_gen_current / _width_current against the maxima. Idle cards "
                "downtrain the link generation, so read it under load.",
                [tgt(f"max by (index) (nvidia_smi_pcie_link_gen_current {GPU_INFO})", instant=True, fmt="table"),
                 tgt(f"max by (index) (nvidia_smi_pcie_link_gen_max {GPU_INFO})", instant=True, fmt="table"),
                 tgt(f"max by (index) (nvidia_smi_pcie_link_width_current {GPU_INFO})", instant=True, fmt="table"),
                 tgt(f"max by (index) (nvidia_smi_pcie_link_width_max {GPU_INFO})", instant=True, fmt="table")],
                hide=["Time"]), 6, 8)
    b.add(stat("PCIe replays (range)", "increase(nvml_gpu_pcie_replay_total[$__range]) per GPU: link-level "
               "retransmissions; non-zero means a marginal riser or slot.",
               [tgt(f"sum by (gpu) (increase(nvml_gpu_pcie_replay_total{{{G}}}[$__range]))", "GPU{{gpu}}", instant=True)],
               thr=thresholds([(None, "green"), (1, "orange")]), decimals=0), 6, 8)

    b.row("Thermal, throttling, errors")
    b.add(timeseries("Temperature", "nvidia_smi_temperature_gpu per card; dashed = slowdown limit reported by "
                     "the driver as temperature_gpu_tlimit (degrees below the limit).",
                     [tgt(f"max by (index) (nvidia_smi_temperature_gpu {GPU_INFO})", "GPU{{index}}")],
                     "celsius", thr_style="line", thr=thresholds([(None, "green"), (80, "orange"), (88, "red")])), 8, 8)
    b.add(timeseries("Throttle time share", "rate() of the nvidia-smi clock-event counters per card: fraction of "
                     "wall time under SW power cap (expected at 180 W), HW/SW thermal slowdown and HW power brake.",
                     [tgt(f"max by (index) (rate(nvidia_smi_clocks_event_reasons_counters_sw_power_cap_seconds[{RI}]) {GPU_INFO})",
                          "GPU{{index}} sw_power_cap"),
                      tgt(f"max by (index) (rate(nvidia_smi_clocks_event_reasons_counters_hw_thermal_slowdown_seconds[{RI}]) {GPU_INFO})",
                          "GPU{{index}} hw_thermal"),
                      tgt(f"max by (index) (rate(nvidia_smi_clocks_event_reasons_counters_sw_thermal_slowdown_seconds[{RI}]) {GPU_INFO})",
                          "GPU{{index}} sw_thermal"),
                      tgt(f"max by (index) (rate(nvidia_smi_clocks_event_reasons_counters_hw_power_brake_slowdown_seconds[{RI}]) {GPU_INFO})",
                          "GPU{{index}} hw_power_brake")],
                     "percentunit", minv=0), 8, 8)
    b.add(stat("XID events (range)", "increase(nvml_gpu_xid_events_total[$__range]) by GPU and XID code: "
               "driver-reported critical errors (e.g. 79 fallen off the bus, 13/31 app faults).",
               [tgt(f"sum by (gpu, xid) (increase(nvml_gpu_xid_events_total{{{G}}}[$__range]))",
                    "GPU{{gpu}} XID {{xid}}", instant=True)],
               thr=thresholds([(None, "green"), (1, "red")]), decimals=0), 4, 8)
    b.add(alertlist("GPU alerts"), 4, 8)

    return b.to_json(gpu_vars(), [RESTART_ANNOTATION])


# ---------------------------------------------------------------------------------------------- 4

def host() -> dict:
    b = Board("llm-host", "Host",
              "USE view of the serving host (host RAM smaller than the mmap'd model): CPU and RAPL, memory, "
              "swap, faults, PSI, disk IO, serving containers, exporter health.",
              ["multivac-llm", "host"])
    N = 'job="node"'

    b.row("CPU")
    b.add(timeseries("CPU utilisation by mode", "1 − idle, split by mode: rate(node_cpu_seconds_total) averaged "
                     "over the 12 threads.",
                     [tgt(f'sum by (mode) (rate(node_cpu_seconds_total{{{N},mode!="idle"}}[{RI}])) / scalar(count(count by (cpu) (node_cpu_seconds_total{{{N}}})))',
                          "{{mode}}")],
                     "percentunit", stack=True, minv=0, maxv=1), 8, 8)
    b.add(timeseries("Load average", "node_load1/5/15 against the thread count.",
                     [tgt(f"node_load1{{{N}}}", "load1"), tgt(f"node_load5{{{N}}}", "load5"),
                      tgt(f"node_load15{{{N}}}", "load15"),
                      tgt(f"count(count by (cpu) (node_cpu_seconds_total{{{N}}}))", "threads")],
                     "short", minv=0), 8, 8)
    b.add(timeseries("RAPL power", "rate(node_rapl_package_joules_total) and rate(node_rapl_core_joules_total): "
                     "CPU package and core power from the RAPL energy counters. A counter wrap reads as a reset.",
                     [tgt(f"sum(rate(node_rapl_package_joules_total{{{N}}}[{RI}]))", "package"),
                      tgt(f"sum(rate(node_rapl_core_joules_total{{{N}}}[{RI}]))", "core")],
                     "watt", minv=0), 8, 8)

    b.row("Memory, swap, faults")
    b.add(timeseries("Memory", "MemTotal − MemAvailable (used), MemAvailable, and swap used "
                     "(SwapTotal − SwapFree). The mmap'd model lives in page cache, so 'available' is the number "
                     "that matters.",
                     [tgt(f"node_memory_MemTotal_bytes{{{N}}} - node_memory_MemAvailable_bytes{{{N}}}", "used"),
                      tgt(f"node_memory_MemAvailable_bytes{{{N}}}", "available"),
                      tgt(f"node_memory_SwapTotal_bytes{{{N}}} - node_memory_SwapFree_bytes{{{N}}}", "swap used")],
                     "bytes", minv=0), 8, 8)
    b.add(timeseries("Swap in / out", "rate(node_vmstat_pswpin) and rate(node_vmstat_pswpout) × 4096: bytes "
                     "per second swapped in (positive) and out (negative).",
                     [tgt(f"rate(node_vmstat_pswpin{{{N}}}[{RI}]) * 4096", "swap in"),
                      tgt(f"-rate(node_vmstat_pswpout{{{N}}}[{RI}]) * 4096", "swap out")],
                     "Bps"), 8, 8)
    b.add(timeseries("Page faults", "rate(node_vmstat_pgmajfault): major faults (disk read to satisfy a page — "
                     "model pages evicted from cache and re-read); rate(node_vmstat_pgfault) minor+major on the "
                     "right axis.",
                     [tgt(f"rate(node_vmstat_pgmajfault{{{N}}}[{RI}])", "major faults/s"),
                      tgt(f"rate(node_vmstat_pgfault{{{N}}}[{RI}])", "all faults/s")],
                     "short", minv=0,
                     overrides=[{"matcher": {"id": "byName", "options": "all faults/s"},
                                 "properties": [{"id": "custom.axisPlacement", "value": "right"}]}]), 8, 8)

    b.row("Pressure stall information (PSI)")
    b.add(timeseries("PSI cpu / memory / io", "rate() of node_pressure_*_seconds_total: share of wall time tasks "
                     "were stalled. 'waiting' = some tasks stalled; 'stalled' = all non-idle tasks stalled (full). "
                     "Linux PSI (kernel docs, Facebook).",
                     [tgt(f"rate(node_pressure_cpu_waiting_seconds_total{{{N}}}[{RI}])", "cpu some"),
                      tgt(f"rate(node_pressure_memory_waiting_seconds_total{{{N}}}[{RI}])", "memory some"),
                      tgt(f"rate(node_pressure_memory_stalled_seconds_total{{{N}}}[{RI}])", "memory full"),
                      tgt(f"rate(node_pressure_io_waiting_seconds_total{{{N}}}[{RI}])", "io some"),
                      tgt(f"rate(node_pressure_io_stalled_seconds_total{{{N}}}[{RI}])", "io full")],
                     "percentunit", minv=0, thr_style="line",
                     thr=thresholds([(None, "green"), (0.2, "red")])), 16, 8)
    b.add(stat("IO full-stall (5 m)", "rate(node_pressure_io_stalled_seconds_total[5m]); HostIoPressureHigh fires "
               "above 20 % for 15 m.",
               [tgt(f"rate(node_pressure_io_stalled_seconds_total{{{N}}}[5m])", "io full")],
               unit="percentunit", thr=thresholds([(None, "green"), (0.05, "orange"), (0.2, "red")]),
               graph="area"), 8, 8)

    b.row("Disk IO")
    b.add(timeseries("Disk throughput", "rate(node_disk_read_bytes_total) (positive) and "
                     "rate(node_disk_written_bytes_total) (negative) per device. /srv/models is sda; / is sdb.",
                     [tgt(f"rate(node_disk_read_bytes_total{{{N}}}[{RI}])", "{{device}} read"),
                      tgt(f"-rate(node_disk_written_bytes_total{{{N}}}[{RI}])", "{{device}} write")],
                     "Bps"), 12, 8)
    b.add(timeseries("Disk busy time", "rate(node_disk_io_time_seconds_total) per device: fraction of time the "
                     "device had IO in flight.",
                     [tgt(f"rate(node_disk_io_time_seconds_total{{{N}}}[{RI}])", "{{device}}")],
                     "percentunit", minv=0, maxv=1), 12, 8)

    b.row("Serving containers (cAdvisor)")
    b.add(timeseries("Container CPU", f"sum by (name) rate(container_cpu_usage_seconds_total{{{CONTAINERS}}}): "
                     "CPU cores used per serving container.",
                     [tgt(f"sum by (name) (rate(container_cpu_usage_seconds_total{{{CONTAINERS}}}[{RI}]))", "{{name}}")],
                     "short", minv=0), 12, 8)
    b.add(timeseries("Container memory", f"container_memory_working_set_bytes and container_memory_rss for "
                     f"{CONTAINERS}. Working set includes the page cache charged to the container.",
                     [tgt(f"max by (name) (container_memory_working_set_bytes{{{CONTAINERS}}})", "{{name}} working set"),
                      tgt(f"max by (name) (container_memory_rss{{{CONTAINERS}}})", "{{name}} rss")],
                     "bytes", minv=0), 12, 8)

    b.row("Exporter health")
    b.add(stat("Scrape targets", "up by job: 1 = Prometheus scraped the target at the last attempt.",
               [tgt("max by (job) (up)", "{{job}}")], mappings=UNHEALTHY_MAP,
               thr=thresholds([(None, "red"), (1, "green")])), 16, 5)
    b.add(stat("Sidecar log follower", "llamacpp_sidecar_log_follow_up: 1 while the sidecar has a `docker logs -f` "
               "follower attached (log-derived metrics stall at 0).",
               [tgt("max by (server) (llamacpp_sidecar_log_follow_up)", "{{server}}")], mappings=UNHEALTHY_MAP,
               thr=thresholds([(None, "red"), (1, "green")])), 4, 5)
    b.add(alertlist("Host alerts"), 4, 5)

    # No template variables on this board: match every server in the restart annotation.
    host_restart = dict(RESTART_ANNOTATION, expr="changes(llamacpp_server_start_time_seconds[2m]) > 0")
    return b.to_json([], [host_restart])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    boards = {"llm-overview.json": overview(), "llm-request-anatomy.json": anatomy(),
              "llm-gpu-energy.json": gpu_energy(), "llm-host.json": host()}
    for name, dash in boards.items():
        path = OUT / name
        path.write_text(json.dumps(dash, indent=2, ensure_ascii=False) + "\n")
        n = sum(1 for p in dash["panels"] if p["type"] != "row")
        print(f"wrote {path} ({n} panels)")


if __name__ == "__main__":
    main()
