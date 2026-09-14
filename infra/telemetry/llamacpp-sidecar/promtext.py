"""Minimal thread-safe Prometheus text-exposition registry (format 0.0.4), stdlib only."""
from __future__ import annotations

import math
import threading

LATENCY_BUCKETS = [0.05, 0.1, 0.25, 0.5, 1, 2, 4, 6, 8, 10, 15, 30, 60, 120, 300, 600, 900, 1800, 3600]
TPOT_BUCKETS = [0.005, 0.01, 0.02, 0.03, 0.04, 0.05, 0.075, 0.1, 0.15, 0.2, 0.3, 0.5, 1, 2, 5]
TOKEN_BUCKETS = [16, 64, 256, 1024, 4096, 16384, 32768, 65536, 131072, 196608, 262144, 524288, 1048576]


def escape(v: str) -> str:
    return str(v).replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def fmt(v: float) -> str:
    if math.isinf(v):
        return "+Inf" if v > 0 else "-Inf"
    if math.isnan(v):
        return "NaN"
    return repr(float(v))


class Metric:
    def __init__(self, reg: "Registry", name: str, kind: str, help_: str, labelnames: tuple[str, ...], buckets=None):
        self.reg, self.name, self.kind, self.help = reg, name, kind, help_
        self.labelnames = tuple(labelnames)
        self.buckets = [float(b) for b in buckets] if buckets else None
        self.series: dict[tuple, object] = {}

    def _key(self, labels: dict) -> tuple:
        return tuple(str(labels.get(n, "")) for n in self.labelnames)

    def set(self, labels: dict, value: float) -> None:
        with self.reg.lock:
            self.series[self._key(labels)] = float(value)

    def inc(self, labels: dict, by: float = 1.0) -> None:
        with self.reg.lock:
            k = self._key(labels)
            self.series[k] = self.series.get(k, 0.0) + float(by)

    def observe(self, labels: dict, value: float) -> None:
        with self.reg.lock:
            k = self._key(labels)
            s = self.series.get(k)
            if s is None:
                s = self.series[k] = {"b": [0] * len(self.buckets), "sum": 0.0, "count": 0}
            for i, ub in enumerate(self.buckets):
                if value <= ub:
                    s["b"][i] += 1
            s["sum"] += float(value)
            s["count"] += 1

    def touch(self, labels: dict) -> None:
        """Create the series at zero if absent, so its first real event is a visible step."""
        with self.reg.lock:
            k = self._key(labels)
            if k not in self.series:
                self.series[k] = ({"b": [0] * len(self.buckets), "sum": 0.0, "count": 0}
                                  if self.kind == "histogram" else 0.0)

    def get(self, labels: dict):
        with self.reg.lock:
            return self.series.get(self._key(labels))

    def remove_matching(self, **match: str) -> None:
        """Drop every series whose labels include all of `match`."""
        idx = {n: i for i, n in enumerate(self.labelnames)}
        with self.reg.lock:
            for k in [k for k in self.series if all(k[idx[n]] == str(v) for n, v in match.items())]:
                del self.series[k]

    def render(self) -> list[str]:
        out = [f"# HELP {self.name} {self.help}", f"# TYPE {self.name} {self.kind}"]

        def lab(key, extra=None):
            pairs = [f'{n}="{escape(v)}"' for n, v in zip(self.labelnames, key)]
            if extra:
                pairs.append(extra)
            return "{" + ",".join(pairs) + "}" if pairs else ""

        for key in sorted(self.series):
            val = self.series[key]
            if self.kind == "histogram":
                for ub, c in zip(self.buckets, val["b"]):
                    out.append(f"{self.name}_bucket{lab(key, f'le=\"{fmt(ub)}\"')} {c}")
                out.append(f"{self.name}_bucket{lab(key, 'le=\"+Inf\"')} {val['count']}")
                out.append(f"{self.name}_sum{lab(key)} {fmt(val['sum'])}")
                out.append(f"{self.name}_count{lab(key)} {val['count']}")
            else:
                out.append(f"{self.name}{lab(key)} {fmt(val)}")
        return out


class Registry:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.metrics: list[Metric] = []

    def _add(self, *a, **kw) -> Metric:
        m = Metric(self, *a, **kw)
        self.metrics.append(m)
        return m

    def gauge(self, name, help_, labelnames=()):
        return self._add(name, "gauge", help_, labelnames)

    def counter(self, name, help_, labelnames=()):
        return self._add(name, "counter", help_, labelnames)

    def histogram(self, name, help_, labelnames=(), buckets=LATENCY_BUCKETS):
        return self._add(name, "histogram", help_, labelnames, buckets=buckets)

    def render(self) -> str:
        with self.lock:
            lines: list[str] = []
            for m in self.metrics:
                lines.extend(m.render())
            return "\n".join(lines) + "\n"
