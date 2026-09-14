#!/usr/bin/env python3
"""llm-proxy: a transparent reverse proxy that instruments llama.cpp inference requests.

Every method and path is relayed unmodified (hop-by-hop headers stripped). POSTs to the
inference endpoints are additionally observed: request JSON is parsed read-only, response
bytes are relayed chunk by chunk as they arrive and parsed on a side buffer afterwards.
Metrics follow the contract in docs/build-stream/2026-09-14-llm-serving-telemetry.md §3.1.
No prompt or completion text is stored.
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import logging
import os
import signal
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import aiohttp
import yaml
from aiohttp import web
from multidict import CIMultiDict
from prometheus_client import (CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Gauge,
                               Histogram, disable_created_metrics, generate_latest)
from yarl import URL

log = logging.getLogger("llm-proxy")
disable_created_metrics()  # no *_created series: they would double the series count

LATENCY_BUCKETS = (0.05, 0.1, 0.25, 0.5, 1, 2, 4, 6, 8, 10, 15, 30, 60, 120, 300, 600, 900,
                   1800, 3600)
TPOT_BUCKETS = (0.005, 0.01, 0.02, 0.03, 0.04, 0.05, 0.075, 0.1, 0.15, 0.2, 0.3, 0.5, 1, 2, 5)
TOKEN_BUCKETS = (16, 64, 256, 1024, 4096, 16384, 32768, 65536, 131072, 196608, 262144, 524288,
                 1048576)

# POST path -> (endpoint label, response dialect)
INSTRUMENTED: dict[str, tuple[str, str]] = {
    "/v1/chat/completions": ("chat", "chat"),
    "/chat/completions": ("chat", "chat"),
    "/v1/completions": ("completions", "oai_completions"),
    "/completions": ("completions", "oai_completions"),
    "/completion": ("completions", "native"),
    "/infill": ("completions", "native"),
    "/v1/responses": ("responses", "responses"),
    "/v1/messages": ("messages", "messages"),
    "/v1/embeddings": ("embeddings", "embeddings"),
    "/embeddings": ("embeddings", "embeddings"),
}

HOP_BY_HOP = frozenset({"connection", "keep-alive", "proxy-connection", "proxy-authenticate",
                        "proxy-authorization", "te", "trailer", "trailers", "transfer-encoding",
                        "upgrade"})
# Set by the HTTP client library itself; forwarding the client's value would be wrong.
REQUEST_DROP = frozenset({"host", "content-length", "expect"})
# Stops aiohttp from adding headers the client did not send (Accept-Encoding matters: the
# llama.cpp WebUI answers GET / with 415 unless the client asked for gzip).
SKIP_AUTO_HEADERS = ("User-Agent", "Accept", "Accept-Encoding", "Content-Type")

MAX_REQUEST_BODY = 1 << 30
MAX_PARSE_BUFFER = 64 << 20
TIMELINE_CAP = 200_000
CONNECT_TIMEOUT_S = 10.0
FINISH_REASONS = ("stop", "length", "tool_calls", "abort", "error", "unknown")
BASE_LABELS = ("server", "model", "endpoint", "stream", "thinking")
ERROR_TYPES = ("upstream_connect", "upstream_timeout", "upstream_disconnect", "http_4xx", "http_5xx",
               "client_disconnect", "stream_error", "parse")
TOKEN_TYPES = ("input", "cached", "prefill", "output", "reasoning")
# Label combinations created at zero on start-up (see Metrics.preinit). Other combinations
# still appear on first use; their very first event is then invisible to rate()/increase().
PREINIT_ENDPOINTS = ("chat", "completions")
PREINIT_FINISH = (("stop", "2xx"), ("length", "2xx"), ("tool_calls", "2xx"), ("unknown", "2xx"),
                  ("abort", "2xx"), ("abort", "none"), ("error", "2xx"), ("error", "4xx"),
                  ("error", "5xx"), ("error", "none"))


# --------------------------------------------------------------------------- configuration

@dataclass
class ServerCfg:
    name: str
    upstream: str
    container: str | None = None
    models: list[str] = field(default_factory=list)
    router: bool = False


@dataclass
class ProxyCfg:
    servers: list[ServerCfg]
    listen: str = "127.0.0.1:18090"
    metrics_listen: str = "127.0.0.1:9901"
    requests_dir: str = "/srv/bench/telemetry/requests"
    default_server: str | None = None
    slo_file: str | None = None
    health_interval_s: float = 5.0
    props_interval_s: float = 60.0

    def server(self, name: str | None) -> ServerCfg:
        for s in self.servers:
            if s.name == name:
                return s
        return self.servers[0]


def load_config(path: str | None, args: argparse.Namespace | None = None) -> ProxyCfg:
    raw: dict[str, Any] = {}
    if path:
        with open(path) as f:
            raw = yaml.safe_load(f) or {}
    servers = [ServerCfg(name=str(s["name"]), upstream=str(s["upstream"]).rstrip("/"),
                         container=s.get("container"), models=[str(m) for m in s.get("models") or []],
                         router=bool(s.get("router", False)))
               for s in raw.get("servers") or []]
    p = raw.get("proxy") or {}
    cfg = ProxyCfg(servers=servers,
                   listen=str(p.get("listen", ProxyCfg.listen)),
                   metrics_listen=str(p.get("metrics_listen", ProxyCfg.metrics_listen)),
                   requests_dir=str(p.get("requests_dir", ProxyCfg.requests_dir)),
                   default_server=p.get("default_server"),
                   slo_file=p.get("slo_file"),
                   health_interval_s=float(p.get("health_interval_s", 5.0)),
                   props_interval_s=float(p.get("props_interval_s", 60.0)))
    if args is not None:
        if args.listen:
            cfg.listen = args.listen
        if args.metrics_listen:
            cfg.metrics_listen = args.metrics_listen
        if args.requests_dir:
            cfg.requests_dir = args.requests_dir
        if args.slo_file:
            cfg.slo_file = args.slo_file
        if args.upstream:
            if not cfg.servers:
                cfg.servers.append(ServerCfg(name="default", upstream=args.upstream.rstrip("/")))
            else:
                cfg.server(cfg.default_server).upstream = args.upstream.rstrip("/")
    if not cfg.servers:
        raise SystemExit("config: no servers defined (servers: [...] or --upstream)")
    if cfg.default_server is None or cfg.default_server not in {s.name for s in cfg.servers}:
        cfg.default_server = cfg.servers[0].name
    return cfg


def split_hostport(s: str) -> tuple[str, int]:
    host, _, port = s.rpartition(":")
    return host.strip("[]") or "0.0.0.0", int(port)


# --------------------------------------------------------------------------- SLO classes

@dataclass
class SloClause:
    metric: str                     # key of Record.slo_inputs()
    le: float                       # seconds (or the metric's unit)
    per_token_metric: str | None = None
    per_token: float = 0.0          # added to `le` per unit of per_token_metric


@dataclass
class Slo:
    name: str
    clauses: list[SloClause]

    def evaluate(self, values: dict[str, float | None]) -> bool | None:
        """True/False for the joint predicate; None when any clause input is missing."""
        ok = True
        for c in self.clauses:
            v = values.get(c.metric)
            if v is None:
                return None
            limit = c.le
            if c.per_token_metric:
                n = values.get(c.per_token_metric)
                if n is None:
                    return None
                limit += c.per_token * n
            ok = ok and v <= limit
        return ok


def load_slos(path: str | None) -> list[Slo]:
    if not path:
        return []
    try:
        with open(path) as f:
            raw = yaml.safe_load(f) or {}
    except FileNotFoundError:
        log.warning("slo file %s not found; SLO counters disabled", path)
        return []
    out = []
    for s in raw.get("slos") or []:
        clauses = []
        for c in s["clauses"]:
            pt = c.get("per_token") or {}
            clauses.append(SloClause(metric=c["metric"], le=float(c["le"]),
                                     per_token_metric=pt.get("metric"),
                                     per_token=float(pt.get("seconds", 0.0))))
        out.append(Slo(name=str(s["name"]), clauses=clauses))
    return out


# --------------------------------------------------------------------------- request parsing

def thinking_label(body: dict[str, Any]) -> str:
    ctk = body.get("chat_template_kwargs")
    if isinstance(ctk, dict):
        et = ctk.get("enable_thinking")
        if isinstance(et, bool):
            return "on" if et else "off"
        if isinstance(ctk.get("reasoning_effort"), str):
            return "off" if ctk["reasoning_effort"].lower() == "none" else "on"
    effort = body.get("reasoning_effort")
    if not isinstance(effort, str) and isinstance(body.get("reasoning"), dict):
        effort = body["reasoning"].get("effort")          # /v1/responses
    if isinstance(effort, str):
        return "off" if effort.lower() == "none" else "on"
    th = body.get("thinking")                               # /v1/messages
    if isinstance(th, dict) and isinstance(th.get("type"), str):
        return "off" if th["type"] == "disabled" else "on"
    return "default"


def requested_max_tokens(body: dict[str, Any]) -> int | None:
    for k in ("max_completion_tokens", "max_tokens", "max_output_tokens", "n_predict"):
        v = body.get(k)
        if isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0:
            return int(v)
    return None


def status_class(status: int | None) -> str:
    return f"{status // 100}xx" if status else "none"


# --------------------------------------------------------------------------- SSE side parser

class SseParser:
    """Incremental text/event-stream parser. Feeding never blocks the relay: it is called
    after the bytes were already written to the client."""

    def __init__(self, on_event: Callable[[str | None, str, float], None]):
        self.buf = bytearray()
        self.scan = 0
        self.on_event = on_event
        self.overflow = False

    def feed(self, chunk: bytes, t: float) -> None:
        self.buf += chunk
        while True:
            i = self.buf.find(b"\n\n", self.scan)
            j = self.buf.find(b"\r\n\r\n", self.scan)
            if i < 0 and j < 0:
                self.scan = max(0, len(self.buf) - 3)
                if len(self.buf) > MAX_PARSE_BUFFER:
                    self.buf.clear()
                    self.scan = 0
                    self.overflow = True
                return
            end, sep = (i, 2) if j < 0 or (0 <= i < j) else (j, 4)
            block = bytes(self.buf[:end])
            del self.buf[:end + sep]
            self.scan = 0
            self._dispatch(block, t)

    def _dispatch(self, block: bytes, t: float) -> None:
        event, data = None, []
        for line in block.decode("utf-8", "replace").split("\n"):
            line = line.rstrip("\r")
            if line.startswith("data:"):
                data.append(line[5:].lstrip(" ") if line[5:6] == " " else line[5:])
            elif line.startswith("event:"):
                event = line[6:].strip()
        if data:
            self.on_event(event, "\n".join(data), t)


# --------------------------------------------------------------------------- per-request record

def _num(d: Any, *keys: str) -> float | None:
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k)
        else:
            return None
    return d if isinstance(d, (int, float)) and not isinstance(d, bool) else None


@dataclass
class Record:
    server: str
    model: str
    endpoint: str
    dialect: str
    stream: bool
    thinking: str
    path: str
    client: str | None
    request_model: str | None = None
    tools: bool = False
    max_tokens: int | None = None
    bytes_in: int = 0
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    t0: float = field(default_factory=time.monotonic)
    wall: dt.datetime = field(default_factory=lambda: dt.datetime.now(dt.timezone.utc))
    t_headers: float | None = None
    t_first_token: float | None = None
    t_first_answer: float | None = None
    t_last: float | None = None
    last_chunk: float | None = None
    gaps: list[float] = field(default_factory=list)
    chunk_ms: list[int] = field(default_factory=list)
    chunk_kind: list[str] = field(default_factory=list)
    timeline_truncated: bool = False
    sse: bool = False
    status: int | None = None
    raw_finish: str | None = None
    finish_reason: str = "unknown"
    stop_type: str | None = None
    truncated: bool | None = None
    error_type: str | None = None
    error_detail: str | None = None
    response_id: str | None = None
    timings: dict[str, Any] | None = None
    usage: dict[str, Any] | None = None
    reasoning_chunks: int = 0
    answer_chunks: int = 0
    tool_chunks: int = 0
    answer_chars: int = 0
    tool_calls: bool = False
    saw_payload: bool = False
    parse_errors: int = 0
    bytes_out: int = 0
    reasoning_tokens: int | None = None
    reasoning_method: str | None = None
    reasoning_text: str | None = None   # non-stream only, in memory until tokenised, never stored

    def labels(self) -> tuple[str, ...]:
        return (self.server, self.model, self.endpoint, "true" if self.stream else "false",
                self.thinking)

    def token_chunk(self, t: float, kind: str) -> None:
        """kind: r=reasoning, a=answer, t=tool call."""
        if self.t_first_token is None:
            self.t_first_token = t
        if kind == "a" and self.t_first_answer is None:
            self.t_first_answer = t
        if self.last_chunk is not None:
            self.gaps.append(t - self.last_chunk)
        self.last_chunk = t
        if len(self.chunk_ms) < TIMELINE_CAP:
            self.chunk_ms.append(round((t - self.t0) * 1000))
            self.chunk_kind.append(kind)
        else:
            self.timeline_truncated = True
        if kind == "r":
            self.reasoning_chunks += 1
        elif kind == "a":
            self.answer_chunks += 1
        else:
            self.tool_chunks += 1

    # ---- derivations (contract §3.1)
    def derive(self) -> dict[str, Any]:
        tm = self.timings or {}
        u = self.usage or {}
        prompt_n, cache_n = _num(tm, "prompt_n"), _num(tm, "cache_n")
        predicted_n, predicted_ms = _num(tm, "predicted_n"), _num(tm, "predicted_ms")
        prompt_ms = _num(tm, "prompt_ms")
        e2e = (self.t_last - self.t0) if self.t_last is not None else None

        ttft, method = None, None
        if self.sse:
            if self.t_first_token is not None:
                ttft, method = self.t_first_token - self.t0, "observed"
        elif e2e is not None and predicted_ms is not None:
            ttft, method = max(0.0, e2e - predicted_ms / 1000.0), "derived"
        ttfat = (self.t_first_answer - self.t0) if self.sse and self.t_first_answer else None
        prefill_s = prompt_ms / 1000.0 if prompt_ms is not None else None
        queue = max(0.0, ttft - prefill_s) if ttft is not None and prefill_s is not None else None
        tpot = (predicted_ms / (predicted_n - 1) / 1000.0
                if predicted_ms is not None and predicted_n is not None and predicted_n >= 2 else None)

        if prompt_n is not None and cache_n is not None:
            inp, cached, prefill = int(prompt_n + cache_n), int(cache_n), int(prompt_n)
        else:
            inp = _num(u, "prompt_tokens") or _num(u, "input_tokens")
            cached = (_num(u, "prompt_tokens_details", "cached_tokens")
                      or _num(u, "input_tokens_details", "cached_tokens")
                      or _num(u, "cache_read_input_tokens"))
            prefill = inp - cached if inp is not None and cached is not None else None
        out = predicted_n if predicted_n is not None else (
            _num(u, "completion_tokens") if _num(u, "completion_tokens") is not None
            else _num(u, "output_tokens"))
        reasoning, rmethod = self.reasoning_tokens, self.reasoning_method
        usage_r = (_num(u, "completion_tokens_details", "reasoning_tokens")
                   or _num(u, "output_tokens_details", "reasoning_tokens"))
        if usage_r is not None:
            reasoning, rmethod = int(usage_r), "usage"
        elif reasoning is None and self.sse and self.finish_reason not in ("abort", "error"):
            reasoning, rmethod = self.reasoning_chunks, "chunks"
        context = int(inp + out) if inp is not None and out is not None else None
        return {
            "headers": self.t_headers - self.t0 if self.t_headers is not None else None,
            "ttft": ttft, "ttft_method": method, "ttfat": ttfat, "queue_wait": queue,
            "prefill": prefill_s,
            "decode": predicted_ms / 1000.0 if predicted_ms is not None else None,
            "tpot": tpot, "e2e": e2e,
            "input": int(inp) if inp is not None else None,
            "cached": int(cached) if cached is not None else None,
            "prefill_tokens": int(prefill) if prefill is not None else None,
            "output": int(out) if out is not None else None,
            "reasoning": reasoning, "reasoning_method": rmethod, "context": context,
            "draft_n": _num(tm, "draft_n"), "draft_n_accepted": _num(tm, "draft_n_accepted"),
        }


# --------------------------------------------------------------------------- dialect handlers

OAI_FINISH = {"stop": "stop", "length": "length", "tool_calls": "tool_calls",
              "function_call": "tool_calls"}
ANTHROPIC_FINISH = {"end_turn": "stop", "stop_sequence": "stop", "max_tokens": "length",
                    "tool_use": "tool_calls", "pause_turn": "stop", "refusal": "stop"}


def _common(rec: Record, d: dict[str, Any]) -> None:
    if isinstance(d.get("timings"), dict):
        rec.timings = d["timings"]
    if isinstance(d.get("usage"), dict):
        rec.usage = d["usage"]
    if isinstance(d.get("id"), str) and rec.response_id is None:
        rec.response_id = d["id"][:128]
    if d.get("error") is not None and rec.error_type is None:
        rec.error_type = "stream_error" if rec.sse else "parse"


def chat_event(rec: Record, d: dict[str, Any], t: float) -> None:
    _common(rec, d)
    for ch in d.get("choices") or []:
        delta = ch.get("delta") or {}
        r = delta.get("reasoning_content") or delta.get("reasoning")
        # A role-only first chunk ({"role":"assistant","content":null}) is not token-bearing.
        if delta.get("content"):
            rec.answer_chars += len(delta["content"])
            rec.token_chunk(t, "a")
        elif r:
            rec.token_chunk(t, "r")
        elif delta.get("tool_calls"):
            rec.tool_calls = True
            rec.token_chunk(t, "t")
        if ch.get("finish_reason"):
            rec.raw_finish = ch["finish_reason"]


def chat_body(rec: Record, d: dict[str, Any]) -> None:
    _common(rec, d)
    for ch in (d.get("choices") or [])[:1]:
        msg = ch.get("message") or {}
        rec.answer_chars = len(msg.get("content") or "")
        if msg.get("tool_calls"):
            rec.tool_calls = True
        r = msg.get("reasoning_content") or msg.get("reasoning")
        if isinstance(r, str) and r:
            rec.reasoning_text = r
        rec.raw_finish = ch.get("finish_reason")


def oai_completions_event(rec: Record, d: dict[str, Any], t: float) -> None:
    _common(rec, d)
    for ch in d.get("choices") or []:
        if ch.get("text"):
            rec.answer_chars += len(ch["text"])
            rec.token_chunk(t, "a")
        if ch.get("finish_reason"):
            rec.raw_finish = ch["finish_reason"]


def oai_completions_body(rec: Record, d: dict[str, Any]) -> None:
    _common(rec, d)
    for ch in (d.get("choices") or [])[:1]:
        rec.answer_chars = len(ch.get("text") or "")
        rec.raw_finish = ch.get("finish_reason")


def native_event(rec: Record, d: dict[str, Any], t: float) -> None:
    _common(rec, d)
    if d.get("content"):
        rec.answer_chars += len(d["content"])
        rec.token_chunk(t, "a")
    if d.get("stop"):
        rec.stop_type = d.get("stop_type")
        rec.truncated = d.get("truncated")


def native_body(rec: Record, d: dict[str, Any]) -> None:
    _common(rec, d)
    rec.answer_chars = len(d.get("content") or "")
    rec.stop_type = d.get("stop_type")
    rec.truncated = d.get("truncated")


def messages_event(rec: Record, d: dict[str, Any], t: float, event: str | None = None) -> None:
    typ = d.get("type") or event
    if isinstance(d.get("timings"), dict):
        rec.timings = d["timings"]
    if typ == "message_start":
        m = d.get("message") or {}
        if isinstance(m.get("usage"), dict):
            rec.usage = dict(m["usage"])
        if isinstance(m.get("id"), str):
            rec.response_id = m["id"][:128]
    elif typ == "content_block_start":
        if (d.get("content_block") or {}).get("type") == "tool_use":
            rec.tool_calls = True
    elif typ == "content_block_delta":
        delta = d.get("delta") or {}
        dt_ = delta.get("type")
        if dt_ == "text_delta" and delta.get("text"):
            rec.answer_chars += len(delta["text"])
            rec.token_chunk(t, "a")
        elif dt_ == "thinking_delta" and delta.get("thinking"):
            rec.token_chunk(t, "r")
        elif dt_ == "input_json_delta" and delta.get("partial_json"):
            rec.tool_calls = True
            rec.token_chunk(t, "t")
    elif typ == "message_delta":
        sr = (d.get("delta") or {}).get("stop_reason")
        if sr:
            rec.raw_finish = sr
        if isinstance(d.get("usage"), dict):
            rec.usage = {**(rec.usage or {}), **d["usage"]}
    elif typ == "error" and rec.error_type is None:
        rec.error_type = "stream_error"


def messages_body(rec: Record, d: dict[str, Any]) -> None:
    _common(rec, d)
    thinking = []
    for block in d.get("content") or []:
        if block.get("type") == "text":
            rec.answer_chars += len(block.get("text") or "")
        elif block.get("type") == "tool_use":
            rec.tool_calls = True
        elif block.get("type") == "thinking" and block.get("thinking"):
            thinking.append(block["thinking"])
    if thinking:
        rec.reasoning_text = "".join(thinking)
    rec.raw_finish = d.get("stop_reason")


def _responses_final(rec: Record, resp: dict[str, Any]) -> None:
    if isinstance(resp.get("usage"), dict):
        rec.usage = resp["usage"]
    if isinstance(resp.get("timings"), dict):
        rec.timings = resp["timings"]
    if isinstance(resp.get("id"), str):
        rec.response_id = resp["id"][:128]
    answer = 0
    for item in resp.get("output") or []:
        if item.get("type") == "function_call":
            rec.tool_calls = True
        for part in item.get("content") or []:
            if part.get("type") == "output_text":
                answer += len(part.get("text") or "")
    if not rec.sse:
        rec.answer_chars = answer
    status = resp.get("status")
    reason = (resp.get("incomplete_details") or {}).get("reason")
    if status == "completed":
        rec.raw_finish = "tool_calls" if rec.tool_calls else "stop"
    elif status == "incomplete":
        rec.raw_finish = "length" if reason in ("max_output_tokens", "max_tokens") else "unknown"
    elif status == "failed":
        rec.raw_finish = "error"


def responses_event(rec: Record, d: dict[str, Any], t: float, event: str | None = None) -> None:
    typ = d.get("type") or event or ""
    if typ == "response.output_text.delta" and d.get("delta"):
        rec.answer_chars += len(d["delta"])
        rec.token_chunk(t, "a")
    elif typ in ("response.reasoning_text.delta", "response.reasoning_summary_text.delta") \
            and d.get("delta"):
        rec.token_chunk(t, "r")
    elif typ == "response.function_call_arguments.delta" and d.get("delta"):
        rec.tool_calls = True
        rec.token_chunk(t, "t")
    elif typ == "response.output_item.added" and (d.get("item") or {}).get("type") == "function_call":
        rec.tool_calls = True
    elif typ in ("response.completed", "response.incomplete", "response.failed"):
        _responses_final(rec, d.get("response") or {})
    elif typ == "error" and rec.error_type is None:
        rec.error_type = "stream_error"


def responses_body(rec: Record, d: dict[str, Any]) -> None:
    _responses_final(rec, d)


def embeddings_body(rec: Record, d: dict[str, Any]) -> None:
    _common(rec, d)
    rec.raw_finish = "stop"


STREAM_HANDLERS = {"chat": chat_event, "oai_completions": oai_completions_event,
                   "native": native_event, "messages": messages_event,
                   "responses": responses_event}
BODY_HANDLERS = {"chat": chat_body, "oai_completions": oai_completions_body,
                 "native": native_body, "messages": messages_body,
                 "responses": responses_body, "embeddings": embeddings_body}


def resolve_finish(rec: Record) -> str:
    if rec.finish_reason in ("abort", "error"):
        return rec.finish_reason
    if rec.error_type in ("stream_error", "upstream_disconnect"):
        return "error"
    if rec.dialect == "native":
        if rec.stop_type == "limit":
            return "length"
        if rec.stop_type in ("eos", "word"):
            return "stop"
        return "length" if rec.truncated else "unknown"
    raw = rec.raw_finish
    if rec.dialect == "messages":
        return ANTHROPIC_FINISH.get(raw or "", "unknown")
    if raw in FINISH_REASONS:
        return raw
    return OAI_FINISH.get(raw or "", "unknown")


# --------------------------------------------------------------------------- metrics

class Metrics:
    def __init__(self, registry: CollectorRegistry):
        r, B = registry, BASE_LABELS
        self.registry = r
        self.requests = Counter("llm_requests_total", "Proxied inference requests at completion",
                                B + ("finish_reason", "status_class"), registry=r)
        self.errors = Counter("llm_request_errors_total", "Inference request errors by type",
                              B + ("error_type",), registry=r)
        self.in_flight = Gauge("llm_requests_in_flight", "Inference requests open at the proxy",
                               B, registry=r)
        self.ttft = Histogram("llm_time_to_first_token_seconds",
                              "Arrival to first token-bearing chunk (observed) or E2E - "
                              "predicted_ms (derived, non-stream)", B + ("method",),
                              buckets=LATENCY_BUCKETS, registry=r)
        self.ttfat = Histogram("llm_time_to_first_answer_token_seconds",
                               "Arrival to first non-empty answer content chunk (stream only)",
                               B, buckets=LATENCY_BUCKETS, registry=r)
        self.queue = Histogram("llm_queue_wait_seconds",
                               "max(0, TTFT - timings.prompt_ms); includes templating and "
                               "tokenisation", B, buckets=LATENCY_BUCKETS, registry=r)
        self.prefill = Histogram("llm_prefill_seconds", "timings.prompt_ms", B,
                                 buckets=LATENCY_BUCKETS, registry=r)
        self.tpot = Histogram("llm_time_per_output_token_seconds",
                              "timings.predicted_ms / (predicted_n - 1), predicted_n >= 2", B,
                              buckets=TPOT_BUCKETS, registry=r)
        self.itl = Histogram("llm_inter_chunk_latency_seconds",
                             "Gap between consecutive token-bearing chunks", B,
                             buckets=TPOT_BUCKETS, registry=r)
        self.e2e = Histogram("llm_request_duration_seconds", "Arrival to last byte to client", B,
                             buckets=LATENCY_BUCKETS, registry=r)
        self.req_tokens = Histogram("llm_request_tokens", "Tokens per request by type",
                                    B + ("type",), buckets=TOKEN_BUCKETS, registry=r)
        self.tokens = Counter("llm_tokens_total", "Tokens by type", B + ("type",), registry=r)
        self.ctx_tokens = Histogram("llm_request_context_tokens", "input + output at completion",
                                    B, buckets=TOKEN_BUCKETS, registry=r)
        self.max_tokens = Histogram("llm_request_max_tokens", "Requested output budget", B,
                                    buckets=TOKEN_BUCKETS, registry=r)
        self.spec_draft = Counter("llm_spec_draft_tokens_total", "timings.draft_n", B, registry=r)
        self.spec_accepted = Counter("llm_spec_accepted_tokens_total", "timings.draft_n_accepted",
                                     B, registry=r)
        self.empty = Counter("llm_empty_answer_total", "Finished with empty answer content", B,
                             registry=r)
        self.tool = Counter("llm_tool_call_responses_total", "Responses containing tool calls", B,
                            registry=r)
        self.slo_evaluated = Counter("llm_slo_evaluated_total", "Requests evaluated per SLO class",
                                     B + ("slo",), registry=r)
        self.slo_good = Counter("llm_slo_good_total", "Requests meeting every clause of the SLO",
                                B + ("slo",), registry=r)
        self.upstream_up = Gauge("llm_proxy_upstream_up", "Last upstream /health probe (1 = 200)",
                                 ("upstream",), registry=r)
        self._preinit_done: set[tuple[str, str]] = set()

    def preinit(self, server: str, model: str, slo_names: list[str]) -> None:
        """Create the common label combinations at zero.

        A counter or histogram child that is born on its first event is first scraped with
        value 1, and Prometheus rate()/increase() never see that step (there is no earlier
        zero sample). Without this, the first abort, the first length stop or the first
        answer-token observation of each combination is silently lost from every ratio and
        quantile rule.
        """
        if (server, model) in self._preinit_done:
            return
        self._preinit_done.add((server, model))
        for endpoint in PREINIT_ENDPOINTS:
            for stream in ("true", "false"):
                for thinking in ("on", "off", "default"):
                    L = (server, model, endpoint, stream, thinking)
                    for finish, sc in PREINIT_FINISH:
                        self.requests.labels(*L, finish, sc)
                    for et in ERROR_TYPES:
                        self.errors.labels(*L, et)
                    for method in ("observed", "derived"):
                        self.ttft.labels(*L, method)
                    for h in (self.ttfat, self.queue, self.prefill, self.tpot, self.itl, self.e2e,
                              self.ctx_tokens, self.max_tokens):
                        h.labels(*L)
                    for typ in TOKEN_TYPES:
                        self.req_tokens.labels(*L, typ)
                        self.tokens.labels(*L, typ)
                    for c in (self.spec_draft, self.spec_accepted, self.empty, self.tool):
                        c.labels(*L)
                    for slo in slo_names:
                        self.slo_evaluated.labels(*L, slo)
                        self.slo_good.labels(*L, slo)


# --------------------------------------------------------------------------- JSONL

class JsonlWriter:
    def __init__(self, directory: str):
        self.dir = Path(directory)

    def write(self, record: dict[str, Any], day: dt.date) -> None:
        try:
            self.dir.mkdir(parents=True, exist_ok=True)
            with open(self.dir / f"{day.isoformat()}.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(record, separators=(",", ":")) + "\n")
                f.flush()
        except OSError as e:
            log.error("jsonl write failed: %s", e)


# --------------------------------------------------------------------------- the proxy

def forward_request_headers(h: Any) -> CIMultiDict[str]:
    named = {t.strip().lower() for v in h.getall("Connection", []) for t in v.split(",")}
    out: CIMultiDict[str] = CIMultiDict()
    for k, v in h.items():
        kl = k.lower()
        if kl in HOP_BY_HOP or kl in named or kl in REQUEST_DROP:
            continue
        out.add(k, v)
    return out


def forward_response_headers(h: Any) -> CIMultiDict[str]:
    named = {t.strip().lower() for v in h.getall("Connection", []) for t in v.split(",")}
    out: CIMultiDict[str] = CIMultiDict()
    for k, v in h.items():
        kl = k.lower()
        if kl in HOP_BY_HOP or kl in named:
            continue
        out.add(k, v)
    return out


class ClientGone(Exception):
    pass


class Proxy:
    def __init__(self, cfg: ProxyCfg, registry: CollectorRegistry | None = None):
        self.cfg = cfg
        self.slos = load_slos(cfg.slo_file)
        self.m = Metrics(registry or CollectorRegistry())
        self.jsonl = JsonlWriter(cfg.requests_dir)
        self.aliases: dict[str, str] = {}
        self.session: aiohttp.ClientSession | None = None
        self.probe: aiohttp.ClientSession | None = None
        self._tasks: list[asyncio.Task[None]] = []
        self._pending: set[asyncio.Task[None]] = set()

    # ---- lifecycle
    async def start(self) -> None:
        self.session = aiohttp.ClientSession(
            auto_decompress=False, cookie_jar=aiohttp.DummyCookieJar(),
            connector=aiohttp.TCPConnector(limit=0, ttl_dns_cache=60),
            timeout=aiohttp.ClientTimeout(total=None, sock_connect=CONNECT_TIMEOUT_S, sock_read=None))
        self.probe = aiohttp.ClientSession(cookie_jar=aiohttp.DummyCookieJar(),
                                           timeout=aiohttp.ClientTimeout(total=4))
        slo_names = [slo.name for slo in self.slos]
        for s in self.cfg.servers:
            self.m.upstream_up.labels(s.name).set(0)
            for model in (s.models if s.router else s.models[:1]) or ["unknown"]:
                self.m.preinit(s.name, model, slo_names)
            self._tasks.append(asyncio.create_task(self._health_loop(s)))
            if not s.router:
                self._tasks.append(asyncio.create_task(self._props_loop(s)))

    async def close(self) -> None:
        if self._pending:
            await asyncio.wait(self._pending, timeout=15)
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        for sess in (self.session, self.probe):
            if sess:
                await sess.close()

    async def _health_loop(self, s: ServerCfg) -> None:
        while True:
            up = 0
            try:
                assert self.probe
                async with self.probe.get(s.upstream + "/health") as r:
                    await r.read()
                    up = 1 if r.status == 200 else 0
            except (aiohttp.ClientError, asyncio.TimeoutError, OSError):
                pass
            self.m.upstream_up.labels(s.name).set(up)
            await asyncio.sleep(self.cfg.health_interval_s)

    async def _props_loop(self, s: ServerCfg) -> None:
        while True:
            try:
                assert self.probe
                async with self.probe.get(s.upstream + "/props") as r:
                    if r.status == 200:
                        d = await r.json(content_type=None)
                        alias = d.get("model_alias") or os.path.basename(d.get("model_path") or "")
                        if alias:
                            self.aliases[s.name] = str(alias)[:128]
                            self.m.preinit(s.name, self.aliases[s.name],
                                           [slo.name for slo in self.slos])
            except (aiohttp.ClientError, asyncio.TimeoutError, OSError, ValueError):
                pass
            await asyncio.sleep(self.cfg.props_interval_s)

    # ---- routing and labels
    def route(self, request_model: str | None) -> ServerCfg:
        if len(self.cfg.servers) > 1 and request_model:
            for s in self.cfg.servers:
                if request_model in s.models:
                    return s
        return self.cfg.server(self.cfg.default_server)

    def model_label(self, s: ServerCfg, request_model: str | None) -> str:
        if s.router:
            return request_model if request_model in s.models else "unknown"
        return self.aliases.get(s.name) or (s.models[0] if s.models else "unknown")

    # ---- handler
    async def handle(self, request: web.Request) -> web.StreamResponse:
        t0 = time.monotonic()
        wall = dt.datetime.now(dt.timezone.utc)
        spec = INSTRUMENTED.get(request.path) if request.method == "POST" else None
        body = await request.read()
        if spec is None:
            model_q = request.query.get("model")
            return await self._relay(request, self.route(model_q), body, None)

        endpoint, dialect = spec
        parsed: Any = None
        try:
            parsed = (await asyncio.to_thread(json.loads, body)) if len(body) > 262_144 \
                else json.loads(body)
        except ValueError:
            pass
        if not isinstance(parsed, dict):
            parsed = {}
        rmodel = parsed.get("model") if isinstance(parsed.get("model"), str) else None
        server = self.route(rmodel)
        rec = Record(server=server.name, model=self.model_label(server, rmodel),
                     endpoint=endpoint, dialect=dialect, stream=parsed.get("stream") is True,
                     thinking=thinking_label(parsed), path=request.path,
                     client=request.headers.get("X-Forwarded-For") or request.remote,
                     request_model=rmodel[:128] if rmodel else None,
                     tools=bool(parsed.get("tools") or parsed.get("functions")),
                     max_tokens=requested_max_tokens(parsed), bytes_in=len(body), t0=t0, wall=wall)
        del parsed
        gauge = self.m.in_flight.labels(*rec.labels())
        gauge.inc()
        try:
            resp = await self._relay(request, server, body, rec)
        except asyncio.CancelledError:
            rec.finish_reason, rec.error_type = "abort", "client_disconnect"
            rec.t_last = time.monotonic()
            self._emit(rec)
            raise
        finally:
            gauge.dec()
        if rec.reasoning_text is not None:
            # The response is complete; tokenise in a detached task so a later close of the
            # keep-alive connection (which cancels this handler) cannot turn it into an abort.
            task = asyncio.create_task(self._finish_later(server, rec))
            self._pending.add(task)
            task.add_done_callback(self._pending.discard)
        else:
            self._emit(rec)
        return resp

    async def _finish_later(self, server: ServerCfg, rec: Record) -> None:
        try:
            await self._tokenize_reasoning(server, rec)
        finally:
            self._emit(rec)

    async def _relay(self, request: web.Request, server: ServerCfg, body: bytes,
                     rec: Record | None) -> web.StreamResponse:
        assert self.session
        url = URL(server.upstream + request.raw_path, encoded=True)
        data = body if body or request.body_exists or request.method in ("POST", "PUT", "PATCH") \
            else None
        try:
            ctx = self.session.request(request.method, url, data=data, allow_redirects=False,
                                       headers=forward_request_headers(request.headers),
                                       skip_auto_headers=SKIP_AUTO_HEADERS)
            up = await ctx.__aenter__()
        except (aiohttp.ServerTimeoutError, asyncio.TimeoutError) as e:
            return self._gateway_error(rec, 504, "upstream_timeout", e)
        except aiohttp.ClientConnectorError as e:
            return self._gateway_error(rec, 502, "upstream_connect", e)
        except aiohttp.ClientError as e:
            return self._gateway_error(rec, 502, "upstream_disconnect", e)

        try:
            return await self._stream_back(request, up, rec)
        except BaseException:
            up.close()
            raise
        finally:
            await ctx.__aexit__(None, None, None)

    async def _stream_back(self, request: web.Request, up: aiohttp.ClientResponse,
                           rec: Record | None) -> web.StreamResponse:
        resp = web.StreamResponse(status=up.status, reason=up.reason)
        for k, v in forward_response_headers(up.headers).items():
            resp.headers.add(k, v)
        observe = rec is not None and 200 <= up.status < 300
        sse_parser: SseParser | None = None
        side = bytearray()
        if rec is not None:
            rec.t_headers = time.monotonic()
            rec.status = up.status
            if up.status >= 400:
                rec.finish_reason = "error"
                rec.error_type = "http_4xx" if up.status < 500 else "http_5xx"
            rec.sse = observe and up.headers.get("Content-Type", "").startswith("text/event-stream")
            if rec.sse:
                handler = STREAM_HANDLERS.get(rec.dialect)
                sse_parser = SseParser(lambda ev, data, t: self._on_sse(rec, handler, ev, data, t))
        try:
            await resp.prepare(request)
        except (ConnectionResetError, RuntimeError) as e:
            self._client_gone(rec, up, e)
            return resp

        try:
            async for chunk in up.content.iter_any():
                t = time.monotonic()
                try:
                    await resp.write(chunk)
                except (ConnectionResetError, RuntimeError) as e:
                    self._client_gone(rec, up, e)
                    return resp
                if rec is not None:
                    rec.bytes_out += len(chunk)
                    if sse_parser is not None:
                        sse_parser.feed(chunk, t)
                    elif observe and len(side) + len(chunk) <= MAX_PARSE_BUFFER:
                        side += chunk
        except (aiohttp.ClientPayloadError, aiohttp.ClientConnectionError) as e:
            # Upstream died mid-response. Headers are already sent: drop the client connection
            # so it cannot mistake a truncated body for a complete one.
            if rec is not None:
                rec.finish_reason, rec.error_type = "error", "upstream_disconnect"
                rec.error_detail = type(e).__name__
                rec.t_last = time.monotonic()
            if request.transport is not None:
                request.transport.close()
            return resp
        try:
            await resp.write_eof()
        except (ConnectionResetError, RuntimeError) as e:
            self._client_gone(rec, up, e)
            return resp
        if rec is not None:
            rec.t_last = time.monotonic()
            if observe and not rec.sse:
                self._parse_body(rec, bytes(side))
            if rec.finish_reason not in ("abort", "error"):
                rec.finish_reason = resolve_finish(rec)
        return resp

    def _client_gone(self, rec: Record | None, up: aiohttp.ClientResponse, e: BaseException) -> None:
        up.close()  # llama.cpp cancels the task when its connection closes
        if rec is not None:
            rec.finish_reason, rec.error_type = "abort", "client_disconnect"
            rec.error_detail = type(e).__name__
            rec.t_last = time.monotonic()

    def _on_sse(self, rec: Record, handler: Any, event: str | None, data: str, t: float) -> None:
        if data.strip() == "[DONE]":
            return
        try:
            d = json.loads(data)
        except ValueError:
            rec.parse_errors += 1
            return
        if not isinstance(d, dict) or handler is None:
            return
        rec.saw_payload = True
        if rec.dialect in ("messages", "responses"):
            handler(rec, d, t, event)
        else:
            handler(rec, d, t)
        if event == "error" and rec.error_type is None:
            rec.error_type = "stream_error"

    def _parse_body(self, rec: Record, raw: bytes) -> None:
        try:
            d = json.loads(raw) if raw else None
        except ValueError:
            d = None
        if not isinstance(d, dict):
            rec.error_type = rec.error_type or "parse"
            return
        rec.saw_payload = True
        BODY_HANDLERS[rec.dialect](rec, d)

    async def _tokenize_reasoning(self, server: ServerCfg, rec: Record) -> None:
        text, rec.reasoning_text = rec.reasoning_text, None
        payload: dict[str, Any] = {"content": text}
        if server.router and rec.request_model:
            payload["model"] = rec.request_model
        try:
            assert self.probe
            async with self.probe.post(server.upstream + "/tokenize", json=payload,
                                       timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status == 200:
                    rec.reasoning_tokens = len((await r.json(content_type=None)).get("tokens") or [])
                    rec.reasoning_method = "tokenize"
        except (aiohttp.ClientError, asyncio.TimeoutError, OSError, ValueError):
            pass

    def _gateway_error(self, rec: Record | None, status: int, error_type: str,
                       e: BaseException) -> web.Response:
        log.warning("upstream %s: %s", error_type, e)
        if rec is not None:
            rec.status, rec.finish_reason, rec.error_type = status, "error", error_type
            rec.error_detail = type(e).__name__
            rec.t_last = time.monotonic()
        return web.json_response({"error": {"code": status, "type": error_type,
                                             "message": f"llm-proxy: {type(e).__name__}: {e}"}},
                                 status=status)

    # ---- emission
    def slo_inputs(self, rec: Record, d: dict[str, Any]) -> dict[str, float | None]:
        return {"ttft_seconds": d["ttft"], "ttfat_seconds": d["ttfat"],
                "queue_wait_seconds": d["queue_wait"], "prefill_seconds": d["prefill"],
                "tpot_seconds": d["tpot"], "e2e_seconds": d["e2e"],
                "prefill_tokens": d["prefill_tokens"], "input_tokens": d["input"],
                "output_tokens": d["output"]}

    def _emit(self, rec: Record) -> None:
        m, L = self.m, rec.labels()
        if rec.finish_reason not in ("abort", "error"):
            rec.finish_reason = resolve_finish(rec)
        d = rec.derive()
        sc = status_class(rec.status)
        m.requests.labels(*L, rec.finish_reason, sc).inc()
        if rec.error_type:
            m.errors.labels(*L, rec.error_type).inc()
        if d["ttft"] is not None:
            m.ttft.labels(*L, d["ttft_method"]).observe(d["ttft"])
        for hist, key in ((m.ttfat, "ttfat"), (m.queue, "queue_wait"), (m.prefill, "prefill"),
                          (m.tpot, "tpot"), (m.e2e, "e2e")):
            if d[key] is not None:
                hist.labels(*L).observe(d[key])
        itl = m.itl.labels(*L)
        for g in rec.gaps:
            itl.observe(g)
        for typ, key in (("input", "input"), ("cached", "cached"), ("prefill", "prefill_tokens"),
                         ("output", "output"), ("reasoning", "reasoning")):
            if d[key] is not None:
                m.req_tokens.labels(*L, typ).observe(d[key])
                m.tokens.labels(*L, typ).inc(d[key])
        if d["context"] is not None:
            m.ctx_tokens.labels(*L).observe(d["context"])
        if rec.max_tokens is not None:
            m.max_tokens.labels(*L).observe(rec.max_tokens)
        if d["draft_n"] is not None:
            m.spec_draft.labels(*L).inc(d["draft_n"])
        if d["draft_n_accepted"] is not None:
            m.spec_accepted.labels(*L).inc(d["draft_n_accepted"])
        ok2xx = rec.status is not None and 200 <= rec.status < 300
        empty = (ok2xx and rec.saw_payload and rec.endpoint != "embeddings"
                 and rec.finish_reason in ("stop", "length") and not rec.tool_calls
                 and rec.answer_chars == 0)
        if empty:
            m.empty.labels(*L).inc()
        if ok2xx and rec.tool_calls:
            m.tool.labels(*L).inc()

        slo_result: dict[str, bool | None] = {}
        server_side_failure = rec.error_type in ("upstream_connect", "upstream_timeout",
                                                 "upstream_disconnect", "stream_error", "http_5xx")
        values = self.slo_inputs(rec, d)
        for slo in self.slos:
            if server_side_failure:
                res: bool | None = False
            elif ok2xx and rec.finish_reason not in ("abort", "error"):
                res = slo.evaluate(values)
            else:
                res = None                  # 4xx, client aborts: not the server's SLO
            slo_result[slo.name] = res
            if res is not None:
                m.slo_evaluated.labels(*L, slo.name).inc()
                if res:
                    m.slo_good.labels(*L, slo.name).inc()

        def r6(x: float | None) -> float | None:
            return round(x, 6) if isinstance(x, float) else x

        record = {
            "ts": rec.wall.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "id": rec.id, "response_id": rec.response_id,
            "server": rec.server, "model": rec.model, "request_model": rec.request_model,
            "endpoint": rec.endpoint, "path": rec.path, "stream": rec.stream,
            "thinking": rec.thinking, "tools": rec.tools, "max_tokens": rec.max_tokens,
            "client": rec.client, "status": rec.status, "status_class": sc,
            "finish_reason": rec.finish_reason, "upstream_finish_reason": rec.raw_finish,
            "stop_type": rec.stop_type, "truncated": rec.truncated,
            "error_type": rec.error_type, "error_detail": rec.error_detail,
            "empty_answer": empty, "tool_calls": rec.tool_calls,
            "intervals_s": {k: r6(d[k]) for k in ("headers", "ttft", "ttfat", "queue_wait",
                                                  "prefill", "decode", "tpot", "e2e")},
            "ttft_method": d["ttft_method"],
            "tokens": {"input": d["input"], "cached": d["cached"], "prefill": d["prefill_tokens"],
                       "output": d["output"], "reasoning": d["reasoning"],
                       "reasoning_method": d["reasoning_method"], "context": d["context"]},
            "chunks": {"reasoning": rec.reasoning_chunks, "answer": rec.answer_chunks,
                       "tool": rec.tool_chunks, "parse_errors": rec.parse_errors},
            "timings": rec.timings, "usage": rec.usage, "slo": slo_result,
            "bytes_in": rec.bytes_in, "bytes_out": rec.bytes_out,
            "chunk_ms": rec.chunk_ms, "chunk_kind": "".join(rec.chunk_kind),
            "chunk_timeline_truncated": rec.timeline_truncated,
        }
        self.jsonl.write(record, rec.wall.date())


# --------------------------------------------------------------------------- servers

REGISTRY_KEY = web.AppKey("registry", CollectorRegistry)


async def metrics_handler(request: web.Request) -> web.Response:
    reg = request.app[REGISTRY_KEY]
    return web.Response(body=generate_latest(reg), headers={"Content-Type": CONTENT_TYPE_LATEST})


async def start_servers(proxy: Proxy) -> list[web.AppRunner]:
    await proxy.start()
    app = web.Application(client_max_size=MAX_REQUEST_BODY)
    app.router.add_route("*", "/{tail:.*}", proxy.handle)
    # handler_cancellation: a client that disconnects while we still wait on upstream (e.g. an
    # 8-minute prefill, no byte to write yet) cancels the handler, which closes the upstream socket.
    runner = web.AppRunner(app, handler_cancellation=True, access_log=None)
    await runner.setup()
    host, port = split_hostport(proxy.cfg.listen)
    await web.TCPSite(runner, host, port).start()

    mapp = web.Application()
    mapp[REGISTRY_KEY] = proxy.m.registry
    mapp.router.add_get("/metrics", metrics_handler)
    mrunner = web.AppRunner(mapp, access_log=None)
    await mrunner.setup()
    mhost, mport = split_hostport(proxy.cfg.metrics_listen)
    await web.TCPSite(mrunner, mhost, mport).start()
    return [runner, mrunner]


async def amain(cfg: ProxyCfg) -> None:
    proxy = Proxy(cfg)
    runners = await start_servers(proxy)
    log.info("listening on %s, metrics on %s, servers: %s", cfg.listen, cfg.metrics_listen,
             ", ".join(f"{s.name}={s.upstream}" for s in cfg.servers))
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)
    await stop.wait()
    for r in runners:
        await r.cleanup()
    await proxy.close()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", help="targets.yml")
    ap.add_argument("--listen", help="host:port for the proxy (overrides proxy.listen)")
    ap.add_argument("--metrics-listen", help="host:port for /metrics (overrides proxy.metrics_listen)")
    ap.add_argument("--upstream", help="base URL of the default server (overrides its upstream)")
    ap.add_argument("--requests-dir", help="JSONL directory (overrides proxy.requests_dir)")
    ap.add_argument("--slo-file", help="SLO class file (overrides proxy.slo_file)")
    ap.add_argument("--log-level", default="INFO")
    args = ap.parse_args()
    logging.basicConfig(level=args.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    asyncio.run(amain(load_config(args.config, args)))


if __name__ == "__main__":
    main()
