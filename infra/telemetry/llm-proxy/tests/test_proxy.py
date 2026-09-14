from __future__ import annotations

import asyncio
import gzip
import json
import socket
import sys
import time
from pathlib import Path
from typing import Any

import aiohttp
import pytest
import pytest_asyncio
from aiohttp import web
from prometheus_client import CollectorRegistry
from yarl import URL

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import llm_proxy as lp  # noqa: E402
from fake_upstream import WEBUI, Fake  # noqa: E402

BASE = {"server": "fake", "model": "fake-alias"}


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


async def start_fake(fake: Fake) -> tuple[web.AppRunner, str]:
    runner = web.AppRunner(fake.app, handler_cancellation=True)
    await runner.setup()
    port = free_port()
    await web.TCPSite(runner, "127.0.0.1", port).start()
    return runner, f"http://127.0.0.1:{port}"


class Env:
    def __init__(self, proxy: lp.Proxy, fake: Fake, url: str, murl: str, rdir: Path):
        self.proxy, self.fake, self.url, self.murl, self.rdir = proxy, fake, url, murl, rdir

    def value(self, name: str, **labels: str) -> float | None:
        return self.proxy.m.registry.get_sample_value(name, labels)

    def records(self) -> list[dict[str, Any]]:
        out = []
        for f in sorted(self.rdir.glob("*.jsonl")):
            out += [json.loads(line) for line in f.read_text().splitlines()]
        return out

    async def wait_records(self, n: int, timeout: float = 5.0) -> list[dict[str, Any]]:
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            recs = self.records()
            if len(recs) >= n:
                return recs
            await asyncio.sleep(0.02)
        raise AssertionError(f"expected {n} records, got {len(self.records())}")


SLO_YAML = """
slos:
  - name: interactive
    clauses:
      - { metric: ttft_seconds, le: 8 }
      - { metric: tpot_seconds, le: 0.075 }
  - name: tight
    clauses:
      - { metric: ttft_seconds, le: 0.2 }
      - { metric: prefill_seconds, le: 0.001, per_token: { metric: prefill_tokens, seconds: 0.001 } }
"""


async def make_env(tmp_path: Path, servers: list[lp.ServerCfg] | None = None,
                   fake: Fake | None = None) -> tuple[Env, list[Any]]:
    fake = fake or Fake()
    frunner, furl = await start_fake(fake)
    slo = tmp_path / "slo.yml"
    slo.write_text(SLO_YAML)
    rdir = tmp_path / "requests"
    cfg = lp.ProxyCfg(servers=servers or [lp.ServerCfg("fake", furl, models=["configured-name"])],
                      listen=f"127.0.0.1:{free_port()}", metrics_listen=f"127.0.0.1:{free_port()}",
                      requests_dir=str(rdir), slo_file=str(slo), health_interval_s=0.1,
                      props_interval_s=0.1)
    for s in cfg.servers:
        if s.upstream == "FAKE":
            s.upstream = furl
    cfg.default_server = cfg.servers[0].name
    proxy = lp.Proxy(cfg, CollectorRegistry())
    runners = await lp.start_servers(proxy)
    await asyncio.sleep(0.3)  # let the props/health loops run once
    env = Env(proxy, fake, f"http://{cfg.listen}", f"http://{cfg.metrics_listen}", rdir)
    return env, [frunner, *runners]


@pytest_asyncio.fixture
async def env(tmp_path: Path):
    e, runners = await make_env(tmp_path)
    async with aiohttp.ClientSession(auto_decompress=False) as s:
        e.s = s  # type: ignore[attr-defined]
        yield e
    for r in runners:
        await r.cleanup()
    await e.proxy.close()


def chat(text: str, stream: bool, **kw: Any) -> dict[str, Any]:
    return {"model": "client-said-this", "stream": stream,
            "messages": [{"role": "user", "content": text}], **kw}


# --------------------------------------------------------------------------- passthrough

async def test_webui_gzip_passthrough(env: Env) -> None:
    s = env.s  # type: ignore[attr-defined]
    async with s.get(env.url + "/", skip_auto_headers=["Accept-Encoding"]) as r:
        assert r.status == 415
    async with s.get(env.url + "/", headers={"Accept-Encoding": "gzip"}) as r:
        assert r.status == 200
        assert r.headers["Content-Encoding"] == "gzip"
        raw = await r.read()
    assert gzip.decompress(raw) == WEBUI
    assert env.value("llm_requests_total", **BASE, endpoint="other", stream="false",
                     thinking="default", finish_reason="unknown", status_class="2xx") is None


async def test_generic_passthrough_headers_body_status(env: Env) -> None:
    s = env.s  # type: ignore[attr-defined]
    async with s.put(URL(env.url + "/echo?x=1&y=%2F", encoded=True), data=b"raw-body",
                     headers={"X-Custom": "keep", "Connection": "keep-alive, X-Hop",
                              "X-Hop": "drop"}) as r:
        assert r.status == 201
        assert r.headers.getall("Set-Cookie") == ["a=1", "b=2"]
        assert r.headers["X-Upstream"] == "yes"
        d = await r.json()
    assert d["method"] == "PUT" and d["path_qs"] == "/echo?x=1&y=%2F" and d["body"] == "raw-body"
    assert d["headers"]["X-Custom"] == "keep"
    assert "X-Hop" not in d["headers"]
    for path in ("/health", "/props", "/v1/models", "/slots", "/metrics"):
        async with s.get(env.url + path) as r:
            assert r.status == 200, path
    async with s.post(env.url + "/tokenize", json={"content": "a b c"}) as r:
        assert (await r.json())["tokens"] == [0, 1, 2]
    async with s.get(env.url + "/nonexistent") as r:
        assert r.status == 404
    assert not env.records()


# --------------------------------------------------------------------------- chat

async def test_stream_reasoning(env: Env) -> None:
    s = env.s  # type: ignore[attr-defined]
    body = json.dumps(chat("reason", True, max_tokens=64,
                           chat_template_kwargs={"enable_thinking": True})).encode()
    async with s.post(env.url + "/v1/chat/completions", data=body,
                      headers={"Content-Type": "application/json"}) as r:
        assert r.status == 200
        raw = await r.read()
    assert raw.count(b"data: ") == 10 and raw.endswith(b"data: [DONE]\n\n")
    assert env.fake.bodies[-1] == body  # request body forwarded byte-for-byte
    (rec,) = await env.wait_records(1)
    L = dict(BASE, endpoint="chat", stream="true", thinking="on")
    assert rec["model"] == "fake-alias" and rec["request_model"] == "client-said-this"
    assert rec["finish_reason"] == "stop" and rec["status"] == 200
    assert rec["chunk_kind"] == "rrrraaa"          # role-only chunk excluded
    assert rec["tokens"] == {"input": 12, "cached": 2, "prefill": 10, "output": 9, "reasoning": 4,
                             "reasoning_method": "chunks", "context": 21}
    iv = rec["intervals_s"]
    assert rec["ttft_method"] == "observed" and iv["ttfat"] > iv["ttft"]
    assert iv["queue_wait"] == pytest.approx(max(0, iv["ttft"] - 0.005), abs=1e-6)
    assert iv["tpot"] == pytest.approx(0.080 / 8)
    assert len(rec["chunk_ms"]) == 7 and rec["chunk_ms"] == sorted(rec["chunk_ms"])
    text = json.dumps(rec)
    assert " need" not in text and '"The"' not in text  # no reasoning or answer text stored
    assert env.value("llm_requests_total", **L, finish_reason="stop", status_class="2xx") == 1
    assert env.value("llm_time_to_first_token_seconds_count", **L, method="observed") == 1
    assert env.value("llm_time_to_first_answer_token_seconds_count", **L) == 1
    assert env.value("llm_inter_chunk_latency_seconds_count", **L) == 6
    assert env.value("llm_tokens_total", **L, type="reasoning") == 4
    assert env.value("llm_tokens_total", **L, type="input") == 12
    assert env.value("llm_request_max_tokens_sum", **L) == 64
    assert env.value("llm_spec_draft_tokens_total", **L) == 20
    assert env.value("llm_spec_accepted_tokens_total", **L) == 15
    assert env.value("llm_slo_evaluated_total", **L, slo="interactive") == 1
    assert env.value("llm_slo_good_total", **L, slo="interactive") == 1
    assert env.value("llm_slo_evaluated_total", **L, slo="tight") == 1
    # tight: prefill 5 ms <= 1 ms + 10 prefill tokens x 1 ms, TTFT well under 0.2 s -> good
    assert env.value("llm_slo_good_total", **L, slo="tight") == 1
    assert env.value("llm_requests_in_flight", **L) == 0


async def test_stream_is_not_buffered(env: Env) -> None:
    s = env.s  # type: ignore[attr-defined]
    t0 = time.monotonic()
    async with s.post(env.url + "/v1/chat/completions", json=chat("gap", True)) as r:
        first = await r.content.readuntil(b"\n\n")
        t_first = time.monotonic() - t0
        await r.read()
    assert b"assistant" in first and t_first < 0.5  # the upstream holds the rest for 1 s


async def test_length_empty_answer(env: Env) -> None:
    s = env.s  # type: ignore[attr-defined]
    async with s.post(env.url + "/v1/chat/completions", json=chat("length16", True, max_tokens=16)) as r:
        await r.read()
    (rec,) = await env.wait_records(1)
    L = dict(BASE, endpoint="chat", stream="true", thinking="default")
    assert rec["finish_reason"] == "length" and rec["empty_answer"] is True
    assert rec["tokens"]["reasoning"] == 16 and rec["intervals_s"]["ttfat"] is None
    assert env.value("llm_empty_answer_total", **L) == 1
    assert env.value("llm_requests_total", **L, finish_reason="length", status_class="2xx") == 1


async def test_non_stream_derived_ttft_and_tokenize(env: Env) -> None:
    s = env.s  # type: ignore[attr-defined]
    async with s.post(env.url + "/v1/chat/completions",
                      json=chat("think", False, max_completion_tokens=100)) as r:
        d = await r.json()
    assert d["choices"][0]["message"]["content"] == "Answer."
    (rec,) = await env.wait_records(1)
    iv = rec["intervals_s"]
    assert rec["ttft_method"] == "derived"
    assert iv["ttft"] == pytest.approx(iv["e2e"] - 0.110, abs=1e-6)
    assert iv["queue_wait"] == pytest.approx(max(0.0, iv["ttft"] - 0.050), abs=1e-6)
    assert iv["tpot"] == pytest.approx(0.110 / 11)
    assert rec["tokens"]["reasoning"] == 5 and rec["tokens"]["reasoning_method"] == "tokenize"
    assert rec["chunk_ms"] == [] and rec["empty_answer"] is False and rec["max_tokens"] == 100
    L = dict(BASE, endpoint="chat", stream="false", thinking="default")
    assert env.value("llm_time_to_first_token_seconds_count", **L, method="derived") == 1


async def test_thinking_off_label_and_tools(env: Env) -> None:
    s = env.s  # type: ignore[attr-defined]
    async with s.post(env.url + "/chat/completions",
                      json=chat("noreason", False, chat_template_kwargs={"enable_thinking": False})) as r:
        await r.read()
    async with s.post(env.url + "/v1/chat/completions",
                      json=chat("tools", True, tools=[{"type": "function"}])) as r:
        await r.read()
    a, b = await env.wait_records(2)
    assert a["thinking"] == "off" and a["finish_reason"] == "stop" and a["tokens"]["reasoning"] is None
    assert b["finish_reason"] == "tool_calls" and b["tools"] is True and b["empty_answer"] is False
    assert env.value("llm_tool_call_responses_total", **BASE, endpoint="chat", stream="true",
                     thinking="default") == 1


async def test_slo_not_evaluated_when_tpot_missing(env: Env) -> None:
    s = env.s  # type: ignore[attr-defined]
    async with s.post(env.url + "/v1/chat/completions", json=chat("crlf", True)) as r:
        await r.read()
    (rec,) = await env.wait_records(1)
    assert rec["chunk_kind"] == "a" and rec["tokens"]["output"] == 1   # CRLF + split event parsed
    assert rec["slo"]["interactive"] is None and rec["slo"]["tight"] is False
    L = dict(BASE, endpoint="chat", stream="true", thinking="default")
    # not evaluated: the series is pre-initialised at zero (Metrics.preinit), never incremented
    assert not env.value("llm_slo_evaluated_total", **L, slo="interactive")


# --------------------------------------------------------------------------- disconnects & errors

async def test_client_disconnect_mid_stream(env: Env) -> None:
    async with aiohttp.ClientSession() as s:
        r = await s.post(env.url + "/v1/chat/completions", json=chat("slow", True))
        await r.content.readuntil(b"\n\n")
        await r.content.readuntil(b"\n\n")
        t_close = time.monotonic()
        r.close()
    (rec,) = await env.wait_records(1)
    assert rec["finish_reason"] == "abort" and rec["error_type"] == "client_disconnect"
    for _ in range(40):
        if env.fake.disconnects:
            break
        await asyncio.sleep(0.05)
    assert env.fake.disconnects and env.fake.disconnects[0][1] - t_close < 1.0
    L = dict(BASE, endpoint="chat", stream="true", thinking="default")
    assert env.value("llm_request_errors_total", **L, error_type="client_disconnect") == 1
    assert env.value("llm_requests_total", **L, finish_reason="abort", status_class="2xx") == 1
    assert env.value("llm_requests_in_flight", **L) == 0
    # not evaluated: the series is pre-initialised at zero (Metrics.preinit), never incremented
    assert not env.value("llm_slo_evaluated_total", **L, slo="interactive")


async def test_client_disconnect_before_headers_closes_upstream(env: Env) -> None:
    async with aiohttp.ClientSession() as s:
        task = asyncio.create_task(s.post(env.url + "/v1/chat/completions",
                                          json=chat("slowheaders", True)))
        await asyncio.sleep(0.4)
        t_close = time.monotonic()
        task.cancel()
    (rec,) = await env.wait_records(1)
    assert rec["finish_reason"] == "abort" and rec["status_class"] == "none"
    for _ in range(40):
        if env.fake.disconnects:
            break
        await asyncio.sleep(0.05)
    assert env.fake.disconnects and env.fake.disconnects[0][1] - t_close < 1.0


async def test_upstream_errors(env: Env) -> None:
    s = env.s  # type: ignore[attr-defined]
    async with s.post(env.url + "/v1/chat/completions", json=chat("error500", False)) as r:
        assert r.status == 500 and (await r.json())["error"]["message"] == "boom"
    async with s.post(env.url + "/v1/chat/completions", json=chat("error400", False)) as r:
        assert r.status == 400
    async with s.post(env.url + "/v1/chat/completions", json=chat("streamerror", True)) as r:
        await r.read()
    a, b, c = await env.wait_records(3)
    L = dict(BASE, endpoint="chat", stream="false", thinking="default")
    assert env.value("llm_requests_total", **L, finish_reason="error", status_class="5xx") == 1
    assert env.value("llm_request_errors_total", **L, error_type="http_5xx") == 1
    assert env.value("llm_request_errors_total", **L, error_type="http_4xx") == 1
    assert a["slo"]["interactive"] is False and b["slo"]["interactive"] is None
    assert c["error_type"] == "stream_error" and c["finish_reason"] == "error"


async def test_upstream_dies_mid_stream(env: Env) -> None:
    s = env.s  # type: ignore[attr-defined]
    with pytest.raises(aiohttp.ClientPayloadError):
        async with s.post(env.url + "/v1/chat/completions", json=chat("upstreamdie", True)) as r:
            await r.read()
    (rec,) = await env.wait_records(1)
    assert rec["error_type"] == "upstream_disconnect" and rec["finish_reason"] == "error"


async def test_upstream_connect_failure(tmp_path: Path) -> None:
    dead = f"http://127.0.0.1:{free_port()}"
    e, runners = await make_env(tmp_path, servers=[lp.ServerCfg("dead", dead, models=["m"])])
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(e.url + "/v1/chat/completions", json=chat("x", True)) as r:
                assert r.status == 502
                assert (await r.json())["error"]["type"] == "upstream_connect"
            async with s.get(e.url + "/health") as r:
                assert r.status == 502
        (rec,) = await e.wait_records(1)
        L = dict(server="dead", model="m", endpoint="chat", stream="true", thinking="default")
        assert rec["error_type"] == "upstream_connect" and rec["status"] == 502
        assert e.value("llm_request_errors_total", **L, error_type="upstream_connect") == 1
        assert e.value("llm_proxy_upstream_up", upstream="dead") == 0
    finally:
        for r in runners:
            await r.cleanup()
        await e.proxy.close()


# --------------------------------------------------------------------------- other dialects

async def test_native_completion(env: Env) -> None:
    s = env.s  # type: ignore[attr-defined]
    async with s.post(env.url + "/completion", json={"prompt": "p", "stream": True, "n_predict": 3}) as r:
        await r.read()
    async with s.post(env.url + "/completion", json={"prompt": "p", "n_predict": -1}) as r:
        await r.read()
    async with s.post(env.url + "/v1/completions", json={"prompt": "p", "max_tokens": 2}) as r:
        await r.read()
    a, b, c = await env.wait_records(3)
    assert a["finish_reason"] == "length" and a["stop_type"] == "limit" and a["truncated"] is False
    assert a["chunk_kind"] == "aaa" and a["max_tokens"] == 3
    assert b["finish_reason"] == "stop" and b["empty_answer"] is True and b["max_tokens"] is None
    assert b["tokens"]["input"] == 10 and b["intervals_s"]["tpot"] is None
    assert c["finish_reason"] == "length" and c["endpoint"] == "completions"


async def test_messages_and_responses_and_embeddings(env: Env) -> None:
    s = env.s  # type: ignore[attr-defined]
    async with s.post(env.url + "/v1/messages", json={"model": "m", "stream": True, "max_tokens": 3,
                                                      "thinking": {"type": "enabled"}}) as r:
        await r.read()
    async with s.post(env.url + "/v1/messages", json={"model": "m", "max_tokens": 50}) as r:
        await r.read()
    async with s.post(env.url + "/v1/responses", json={"stream": True, "max_output_tokens": 4,
                                                       "reasoning": {"effort": "none"}}) as r:
        await r.read()
    async with s.post(env.url + "/v1/responses", json={}) as r:
        await r.read()
    async with s.post(env.url + "/v1/embeddings", json={"input": "abc"}) as r:
        await r.read()
    m1, m2, r1, r2, e1 = await env.wait_records(5)
    assert m1["finish_reason"] == "length" and m1["chunk_kind"] == "rra" and m1["thinking"] == "on"
    assert m1["tokens"]["input"] == 9 and m1["tokens"]["output"] == 3
    assert m2["finish_reason"] == "tool_calls" and m2["tool_calls"] is True
    assert m2["tokens"]["reasoning"] == 2 and m2["tokens"]["reasoning_method"] == "tokenize"
    assert r1["finish_reason"] == "length" and r1["chunk_kind"] == "rra" and r1["thinking"] == "off"
    assert r1["tokens"]["reasoning"] == 2 and r1["tokens"]["reasoning_method"] == "usage"
    assert r2["finish_reason"] == "stop" and r2["empty_answer"] is False
    assert e1["endpoint"] == "embeddings" and e1["tokens"]["input"] == 5 and e1["empty_answer"] is False


# --------------------------------------------------------------------------- labels, routing, metrics

async def test_router_and_multi_server_routing(tmp_path: Path) -> None:
    fake2 = Fake(alias="second-alias")
    r2, url2 = await start_fake(fake2)
    servers = [lp.ServerCfg("a", "FAKE", models=["model-a"]),
               lp.ServerCfg("b", url2, models=["model-b", "model-c"], router=True)]
    e, runners = await make_env(tmp_path, servers=servers)
    try:
        async with aiohttp.ClientSession() as s:
            for model in ("model-b", "model-a", "nope"):
                async with s.post(e.url + "/v1/chat/completions",
                                  json={**chat("noreason", False), "model": model}) as r:
                    await r.read()
        b, a, nope = await e.wait_records(3)
        assert (b["server"], b["model"]) == ("b", "model-b") and len(fake2.bodies) == 1
        assert (a["server"], a["model"]) == ("a", "fake-alias")      # alias from /props
        assert (nope["server"], nope["model"]) == ("a", "fake-alias")  # default server
        assert e.value("llm_proxy_upstream_up", upstream="a") == 1
    finally:
        for r in runners:
            await r.cleanup()
        await r2.cleanup()
        await e.proxy.close()


async def test_metrics_endpoint(env: Env) -> None:
    s = env.s  # type: ignore[attr-defined]
    async with s.post(env.url + "/v1/chat/completions", json=chat("reason", True)) as r:
        await r.read()
    await env.wait_records(1)
    async with s.get(env.murl + "/metrics") as r:
        text = await r.text()
    for name in ("llm_requests_total", "llm_request_errors_total", "llm_requests_in_flight",
                 "llm_time_to_first_token_seconds_bucket", "llm_queue_wait_seconds_bucket",
                 "llm_time_per_output_token_seconds_bucket", "llm_request_tokens_bucket",
                 "llm_slo_good_total", "llm_proxy_upstream_up"):
        assert name in text, name
    assert 'le="3600.0"' in text and 'le="1.048576e+06"' in text


def test_thinking_label() -> None:
    assert lp.thinking_label({}) == "default"
    assert lp.thinking_label({"chat_template_kwargs": {"enable_thinking": False}}) == "off"
    assert lp.thinking_label({"chat_template_kwargs": {"enable_thinking": True},
                              "reasoning_effort": "none"}) == "on"
    assert lp.thinking_label({"reasoning_effort": "low"}) == "on"
    assert lp.thinking_label({"chat_template_kwargs": {"reasoning_effort": "none"}}) == "off"
    assert lp.thinking_label({"thinking": {"type": "disabled"}}) == "off"


def test_sse_parser_boundaries() -> None:
    seen: list[tuple[str | None, str]] = []
    p = lp.SseParser(lambda ev, data, t: seen.append((ev, data)))
    stream = b"event: a\ndata: 1\n\ndata: {\"x\":\r\ndata: 2}\r\n\r\n: comment\n\ndata: [DONE]\n\n"
    for i in range(len(stream)):
        p.feed(stream[i:i + 1], 0.0)
    assert seen == [("a", "1"), (None, '{"x":\n2}'), (None, "[DONE]")]


def test_slo_evaluate() -> None:
    slo = lp.Slo("d", [lp.SloClause("prefill_seconds", 2, "prefill_tokens", 0.0025)])
    assert slo.evaluate({"prefill_seconds": 4.4, "prefill_tokens": 1000}) is True
    assert slo.evaluate({"prefill_seconds": 4.6, "prefill_tokens": 1000}) is False
    assert slo.evaluate({"prefill_seconds": 1.0}) is None
