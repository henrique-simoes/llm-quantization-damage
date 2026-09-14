"""Parse llama-server log lines into the sidecar's per-request histograms and counters.

Line shape (llama.cpp common log, uptime prefix then level letter):
    4012.47.472.536 I slot print_timing: id  0 | task 89000 |        eval time =   55253.67 ms /  1471 tokens (...)
optionally preceded by docker's RFC3339Nano timestamp when read via `docker logs --timestamps`.

Per-request values are accumulated keyed by (server, task id) and emitted on the
`release ... stop processing: n_tokens = N, truncated = T` line.
"""
from __future__ import annotations

import re
import time

from parsers import split_docker_timestamp
from promtext import LATENCY_BUCKETS, TOKEN_BUCKETS, TPOT_BUCKETS, Registry

SPEC_LEN_BUCKETS = [1, 1.25, 1.5, 1.75, 2, 2.25, 2.5, 2.75, 3, 3.5, 4, 5, 6, 8, 9, 17]
SPEC_MIN_DRAFTED = 100  # PN-61: shorter generations give degenerate acceptance statistics
STALE_TASK_S = 3600.0

RE_LEVEL = re.compile(r"^\s*\d+\.\d+\.\d+\.\d+ ([IWED]) ")
RE_TASK = re.compile(r"\|\s*task (-?\d+)\s*\|")
RE_PROMPT = re.compile(r"prompt eval time\s*=\s*([\d.]+) ms /\s*(\d+) tokens")
RE_EVAL = re.compile(r"\|\s+eval time\s*=\s*([\d.]+) ms /\s*(\d+) tokens")
RE_TOTAL = re.compile(r"total time\s*=\s*([\d.]+) ms /\s*(\d+) tokens")
RE_GRAPHS = re.compile(r"graphs reused\s*=\s*(\d+)")
RE_DRAFT = re.compile(
    r"draft acceptance\s*=\s*([\d.]+)\s*\(\s*(\d+) accepted /\s*(\d+) generated\)(?:,\s*mean len\s*=\s*([\d.]+))?"
)
RE_RELEASE = re.compile(r"stop processing: n_tokens = (\d+), truncated = (\d+)")

RE_CUDA = re.compile(r"CUDA error", re.I)
RE_OOM = re.compile(r"out of memory|failed to allocate|cudaMalloc", re.I)
RE_ALLOC_RETRY = re.compile(r"retrying without")
RE_SLOT = re.compile(r"\bslot\b")

LOAD_DONE = re.compile(r"llama_server: model loaded|llama_server: listening on |server is listening")


def classify_event(level: str | None, msg: str) -> str | None:
    """One event per line, most specific first. cuda/oom/alloc_retry match at any level
    (a CUDA abort may print without the level prefix); slot/other errors need level E."""
    if RE_CUDA.search(msg):
        return "cuda_error"
    if RE_OOM.search(msg):
        return "oom"
    if RE_ALLOC_RETRY.search(msg):
        return "alloc_retry"
    if level == "E":
        return "slot_error" if RE_SLOT.search(msg) else "other_error"
    return None


class SidecarLogMetrics:
    """The log-derived metric families, registered once per registry."""

    def __init__(self, reg: Registry):
        L = ("server", "model")
        self.prefill_seconds = reg.histogram("llamacpp_prefill_seconds", "Prefill wall time per request (log prompt eval time).", L, LATENCY_BUCKETS)
        self.prefill_tokens = reg.histogram("llamacpp_prefill_tokens", "Uncached prompt tokens evaluated per request (log prompt eval).", L, TOKEN_BUCKETS)
        self.decode_tpt = reg.histogram("llamacpp_decode_time_per_token_seconds", "Decode seconds per step: eval ms / (n - 1), requests with n >= 2.", L, TPOT_BUCKETS)
        self.decode_seconds = reg.counter("llamacpp_decode_seconds_total", "Decode wall seconds (log eval time), requests with n >= 2.", L)
        self.decode_steps = reg.counter("llamacpp_decode_steps_total", "Decode steps (n - 1 per request), unbiased decode-rate basis.", L)
        self.spec_len = reg.histogram("llamacpp_spec_mean_accept_length", "Speculative mean acceptance length per request, requests with >= 100 drafted tokens.", L, SPEC_LEN_BUCKETS)
        self.depth = reg.histogram("llamacpp_request_context_depth_tokens", "Context depth at release (log n_tokens).", L, TOKEN_BUCKETS)
        self.ctx_hits = reg.counter("llamacpp_context_limit_hits_total", "Releases with truncated = 1 (context window exhausted).", L)
        self.log_lines = reg.counter("llamacpp_log_lines_total", "Server log lines by level.", L + ("level",))
        self.log_events = reg.counter("llamacpp_log_events_total", "Pattern-matched warning/error events in the server log.", L + ("event",))
        # additions beyond the §3.2 contract (see README)
        self.released = reg.counter("llamacpp_requests_released_total", "Slot releases seen in the log (every finished or cancelled task).", L)
        self.released_timed = reg.counter("llamacpp_requests_timed_total", "Releases that carried print_timing lines (cancelled tasks do not).", L)
        self.stale_evicted = reg.counter("llamacpp_sidecar_tasks_evicted_total", "Per-task parser state dropped after 1 h without a release.", L)


class LogParser:
    def __init__(self, metrics: SidecarLogMetrics, server: str, model: str, clock=time.monotonic):
        self.m = metrics
        self.labels = {"server": server, "model": model}
        self.clock = clock
        self.tasks: dict[str, dict] = {}
        self.last_sweep = clock()
        self.last_ts: float | None = None  # newest docker timestamp consumed (dedupe on reconnect)
        self.graphs_reused_last: int | None = None
        # raw sums at release, for tests and debugging (not exported)
        self.totals: dict[str, float] = {"prompt_tokens": 0, "eval_tokens": 0, "accepted": 0, "drafted": 0}
        # Create every series at zero: a series born on its first event is first scraped at 1 and
        # rate()/increase() never see that step (e.g. the first context-limit hit or CUDA error).
        m, lab = metrics, self.labels
        for fam in (m.prefill_seconds, m.prefill_tokens, m.decode_tpt, m.decode_seconds, m.decode_steps,
                    m.spec_len, m.depth, m.ctx_hits, m.released, m.released_timed, m.stale_evicted):
            fam.touch(lab)
        for level in ("I", "W", "E", "D"):
            m.log_lines.touch({**lab, "level": level})
        for ev in ("cuda_error", "oom", "alloc_retry", "slot_error", "other_error"):
            m.log_events.touch({**lab, "event": ev})

    def reset_tasks(self) -> None:
        self.tasks.clear()

    def feed(self, raw: str, dedupe: bool = False) -> None:
        line = raw.rstrip("\n")
        ts, line = split_docker_timestamp(line)
        if ts is not None:
            if dedupe and self.last_ts is not None and ts <= self.last_ts:
                return
            if self.last_ts is None or ts > self.last_ts:
                self.last_ts = ts
        if not line.strip():
            return
        lab = self.labels
        lm = RE_LEVEL.match(line)
        level = lm.group(1) if lm else None
        if level:
            self.m.log_lines.inc({**lab, "level": level})
        ev = classify_event(level, line)
        if ev:
            self.m.log_events.inc({**lab, "event": ev})

        if "print_timing" in line or "stop processing" in line:
            self._request_line(line)

        now = self.clock()
        if now - self.last_sweep > 60:
            self.last_sweep = now
            for k in [k for k, v in self.tasks.items() if now - v["t"] > STALE_TASK_S]:
                del self.tasks[k]
                self.m.stale_evicted.inc(lab)

    def _request_line(self, line: str) -> None:
        tm = RE_TASK.search(line)
        if not tm:
            return
        task = tm.group(1)
        st = self.tasks.setdefault(task, {})
        st["t"] = self.clock()
        if m := RE_PROMPT.search(line):
            st["prompt_ms"], st["prompt_n"] = float(m.group(1)), int(m.group(2))
        elif m := RE_EVAL.search(line):
            st["eval_ms"], st["eval_n"] = float(m.group(1)), int(m.group(2))
        elif m := RE_TOTAL.search(line):
            st["total_ms"], st["total_n"] = float(m.group(1)), int(m.group(2))
        elif m := RE_GRAPHS.search(line):
            st["graphs_reused"] = self.graphs_reused_last = int(m.group(1))
        elif m := RE_DRAFT.search(line):
            st["draft_rate"], st["accepted"], st["drafted"] = float(m.group(1)), int(m.group(2)), int(m.group(3))
            if m.group(4) is not None:
                st["mean_len"] = float(m.group(4))
        elif m := RE_RELEASE.search(line):
            self._release(st, int(m.group(1)), int(m.group(2)))
            del self.tasks[task]

    def _release(self, st: dict, n_tokens: int, truncated: int) -> None:
        m, lab = self.m, self.labels
        for key, src in (("prompt_tokens", "prompt_n"), ("eval_tokens", "eval_n"), ("accepted", "accepted"), ("drafted", "drafted")):
            self.totals[key] += st.get(src, 0)
        m.released.inc(lab)
        m.depth.observe(lab, n_tokens)
        if truncated:
            m.ctx_hits.inc(lab)
        if "prompt_ms" in st or "eval_ms" in st:
            m.released_timed.inc(lab)
        if "prompt_ms" in st:
            m.prefill_seconds.observe(lab, st["prompt_ms"] / 1000.0)
            m.prefill_tokens.observe(lab, st["prompt_n"])
        n = st.get("eval_n", 0)
        if n >= 2:
            secs = st["eval_ms"] / 1000.0
            m.decode_tpt.observe(lab, secs / (n - 1))
            m.decode_seconds.inc(lab, secs)
            m.decode_steps.inc(lab, n - 1)
        if st.get("drafted", 0) >= SPEC_MIN_DRAFTED and "mean_len" in st:
            m.spec_len.observe(lab, st["mean_len"])


def find_load_done(lines, started_at: float) -> float | None:
    """Scan `docker logs --timestamps` output for the first model-loaded/listening line
    at or after started_at; return its daemon timestamp minus started_at."""
    for raw in lines:
        ts, rest = split_docker_timestamp(raw.rstrip("\n"))
        if ts is None or ts < started_at:
            continue
        if LOAD_DONE.search(rest):
            return ts - started_at
    return None
