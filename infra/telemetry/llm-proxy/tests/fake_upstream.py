"""A fake llama.cpp server (aiohttp) emitting realistic response shapes for the proxy tests.

Scenario selection never touches the request body semantics the proxy parses: chat and
messages scenarios are chosen by the first user message text, completion scenarios by the
prompt text.
"""
from __future__ import annotations

import asyncio
import gzip
import json
import time
from typing import Any

from aiohttp import web

CREATED = 1789425673
CHAT_ID = "chatcmpl-fake"
WEBUI = b"<!doctype html><title>llama.cpp</title>" * 20


def timings(prompt_n: int, cache_n: int, predicted_n: int, prompt_ms: float = 40.0,
            predicted_ms: float | None = None, draft: bool = True) -> dict[str, Any]:
    predicted_ms = predicted_ms if predicted_ms is not None else 10.0 * max(predicted_n - 1, 0)
    t = {"cache_n": cache_n, "prompt_n": prompt_n, "prompt_ms": prompt_ms,
         "prompt_per_token_ms": prompt_ms / max(prompt_n, 1), "prompt_per_second": 1000.0,
         "predicted_n": predicted_n, "predicted_ms": predicted_ms,
         "predicted_per_token_ms": 10.0, "predicted_per_second": 100.0}
    if draft:
        t.update({"draft_n": 20, "draft_n_accepted": 15})
    return t


def chunk(delta: dict[str, Any], finish: str | None = None, **extra: Any) -> bytes:
    d = {"choices": [{"finish_reason": finish, "index": 0, "delta": delta}], "created": CREATED,
         "id": CHAT_ID, "model": "fake-alias", "system_fingerprint": "b1-fake",
         "object": "chat.completion.chunk", **extra}
    return b"data: " + json.dumps(d, separators=(",", ":")).encode() + b"\n\n"


class Fake:
    def __init__(self, alias: str = "fake-alias"):
        self.alias = alias
        self.bodies: list[bytes] = []
        self.headers: list[dict[str, str]] = []
        self.disconnects: list[tuple[str, float]] = []
        self.app = web.Application()
        r = self.app.router
        r.add_get("/", self.webui)
        r.add_get("/health", lambda _: web.json_response({"status": "ok"}))
        r.add_get("/props", lambda _: web.json_response({"model_alias": self.alias,
                                                         "model_path": "/m/x.gguf"}))
        r.add_get("/v1/models", lambda _: web.json_response({"data": [{"id": self.alias}]}))
        r.add_get("/slots", lambda _: web.json_response([{"id": 0, "is_processing": False}]))
        r.add_get("/metrics", lambda _: web.Response(text="llamacpp:requests_processing 0\n"))
        r.add_post("/tokenize", self.tokenize)
        r.add_route("*", "/echo", self.echo)
        r.add_post("/v1/chat/completions", self.chat)
        r.add_post("/chat/completions", self.chat)
        r.add_post("/completion", self.native)
        r.add_post("/v1/completions", self.oai_completions)
        r.add_post("/v1/messages", self.messages)
        r.add_post("/v1/responses", self.responses)
        r.add_post("/v1/embeddings", self.embeddings)

    # ---- plain endpoints
    async def webui(self, request: web.Request) -> web.Response:
        if "gzip" not in request.headers.get("Accept-Encoding", ""):
            return web.Response(status=415, text="gzip required")
        return web.Response(body=gzip.compress(WEBUI, mtime=0),
                            headers={"Content-Encoding": "gzip",
                                     "Content-Type": "text/html; charset=utf-8"})

    async def tokenize(self, request: web.Request) -> web.Response:
        d = await request.json()
        return web.json_response({"tokens": list(range(len(d["content"].split())))})

    async def echo(self, request: web.Request) -> web.Response:
        body = await request.read()
        resp = web.json_response({"method": request.method, "path_qs": request.raw_path,
                                  "headers": dict(request.headers), "body": body.decode()},
                                 status=201)
        resp.headers.add("Set-Cookie", "a=1")
        resp.headers.add("Set-Cookie", "b=2")
        resp.headers["X-Upstream"] = "yes"
        return resp

    # ---- helpers
    async def _record(self, request: web.Request) -> dict[str, Any]:
        raw = await request.read()
        self.bodies.append(raw)
        self.headers.append(dict(request.headers))
        return json.loads(raw)

    async def _sse(self, request: web.Request) -> web.StreamResponse:
        resp = web.StreamResponse(headers={"Content-Type": "text/event-stream"})
        await resp.prepare(request)
        return resp

    async def _send(self, request: web.Request, resp: web.StreamResponse, data: bytes,
                    tag: str) -> bool:
        try:
            await resp.write(data)
            return True
        except (ConnectionResetError, RuntimeError):
            self.disconnects.append((tag, time.monotonic()))
            return False

    # ---- chat
    async def chat(self, request: web.Request) -> web.StreamResponse:
        # The fake runs with handler_cancellation=True, like llama.cpp cancelling its task when
        # the connection closes: a proxy-side close surfaces here as CancelledError.
        try:
            return await self._chat(request)
        except asyncio.CancelledError:
            self.disconnects.append(("cancelled", time.monotonic()))
            raise

    async def _chat(self, request: web.Request) -> web.StreamResponse:
        body = await self._record(request)
        text = body["messages"][-1]["content"]
        scen = text.split()[0]
        stream = body.get("stream") is True

        if scen == "error500":
            return web.json_response({"error": {"code": 500, "message": "boom"}}, status=500)
        if scen == "error400":
            return web.json_response({"error": {"code": 400, "message": "bad"}}, status=400)
        if scen == "slowheaders":
            # Emulates a long prefill before any byte; detect the proxy closing the socket.
            for _ in range(100):
                await asyncio.sleep(0.05)
                if request.transport is None or request.transport.is_closing():
                    self.disconnects.append(("slowheaders", time.monotonic()))
                    return web.Response(status=499)
            return web.json_response({})
        if scen == "delay":
            await asyncio.sleep(float(text.split()[1]))

        if not stream:
            if scen == "noreason":
                msg = {"role": "assistant", "content": "Hello there."}
                tm = timings(20, 5, 4, predicted_ms=30.0)
            else:
                msg = {"role": "assistant", "content": "Answer.",
                       "reasoning_content": "one two three four five"}
                tm = timings(30, 0, 12, prompt_ms=50.0, predicted_ms=110.0)
            await asyncio.sleep(0.15)
            return web.json_response({
                "choices": [{"finish_reason": "stop", "index": 0, "message": msg}],
                "created": CREATED, "model": "fake-alias", "object": "chat.completion",
                "usage": {"completion_tokens": tm["predicted_n"],
                          "prompt_tokens": tm["prompt_n"] + tm["cache_n"],
                          "total_tokens": 0}, "id": CHAT_ID, "timings": tm})

        resp = await self._sse(request)
        role = chunk({"role": "assistant", "content": None})
        if scen == "reason":
            # role chunk arrives with the first reasoning token in one read, as observed live
            await self._send(request, resp, role + chunk({"reasoning_content": "We"}), scen)
            for w in ["need", "to", "think"]:
                await asyncio.sleep(0.02)
                await self._send(request, resp, chunk({"reasoning_content": " " + w}), scen)
            for w in ["The", "answer", "."]:
                await asyncio.sleep(0.02)
                await self._send(request, resp, chunk({"content": w}), scen)
            await self._send(request, resp,
                             chunk({}, "stop", timings=timings(10, 2, 9, prompt_ms=5.0,
                                                               predicted_ms=80.0)), scen)
            await self._send(request, resp, b"data: [DONE]\n\n", scen)
        elif scen == "length16":
            out = role
            for i in range(16):
                out += chunk({"reasoning_content": f" r{i}"})
            await self._send(request, resp, out, scen)
            await self._send(request, resp,
                             chunk({}, "length", timings=timings(10, 0, 16, predicted_ms=150.0)),
                             scen)
            await self._send(request, resp, b"data: [DONE]\n\n", scen)
        elif scen == "tools":
            await self._send(request, resp, role, scen)
            await self._send(request, resp, chunk({"tool_calls": [{"index": 0, "id": "c1",
                                                                    "function": {"name": "f", "arguments": ""}}]}), scen)
            await self._send(request, resp, chunk({"tool_calls": [{"index": 0,
                                                                    "function": {"arguments": "{}"}}]}), scen)
            await self._send(request, resp, chunk({}, "tool_calls", timings=timings(5, 0, 3)), scen)
            await self._send(request, resp, b"data: [DONE]\n\n", scen)
        elif scen == "slow":
            await self._send(request, resp, role, scen)
            for i in range(200):
                if not await self._send(request, resp, chunk({"content": f"w{i} "}), scen):
                    return resp
                await asyncio.sleep(0.05)
        elif scen == "gap":
            await self._send(request, resp, role + chunk({"content": "first"}), scen)
            await asyncio.sleep(1.0)
            await self._send(request, resp, chunk({}, "stop", timings=timings(1, 0, 2)), scen)
        elif scen == "crlf":
            # CRLF separators, one event split across two network writes
            ev = chunk({"content": "x"}).replace(b"\n\n", b"\r\n\r\n")
            await self._send(request, resp, role.replace(b"\n\n", b"\r\n\r\n") + ev[:15], scen)
            await asyncio.sleep(0.02)
            await self._send(request, resp, ev[15:], scen)
            await self._send(request, resp, chunk({}, "stop", timings=timings(1, 0, 1)), scen)
        elif scen == "upstreamdie":
            await self._send(request, resp, role + chunk({"content": "partial"}), scen)
            await asyncio.sleep(0.05)
            assert request.transport is not None
            request.transport.close()
        elif scen == "streamerror":
            await self._send(request, resp, role, scen)
            await self._send(request, resp, b'data: {"error":{"code":500,"message":"x"}}\n\n', scen)
        return resp

    # ---- native /completion
    async def native(self, request: web.Request) -> web.StreamResponse:
        body = await self._record(request)
        if body.get("stream"):
            resp = await self._sse(request)
            for w in ["a", "b", "c"]:
                await self._send(request, resp, b"data: " + json.dumps(
                    {"content": w, "stop": False, "tokens": [1]}).encode() + b"\n\n", "native")
                await asyncio.sleep(0.01)
            final = {"content": "", "stop": True, "stop_type": "limit", "truncated": False,
                     "timings": timings(7, 0, 3, draft=False), "tokens_predicted": 3}
            await self._send(request, resp, b"data: " + json.dumps(final).encode() + b"\n\n", "native")
            return resp
        return web.json_response({"content": "", "stop": True, "stop_type": "eos",
                                  "truncated": False, "timings": timings(7, 3, 1, draft=False)})

    async def oai_completions(self, request: web.Request) -> web.Response:
        await self._record(request)
        return web.json_response({"choices": [{"text": "hi", "index": 0, "finish_reason": "length"}],
                                  "usage": {"prompt_tokens": 4, "completion_tokens": 2},
                                  "timings": timings(4, 0, 2, draft=False)})

    # ---- Anthropic /v1/messages
    async def messages(self, request: web.Request) -> web.StreamResponse:
        body = await self._record(request)
        if not body.get("stream"):
            return web.json_response({
                "id": "msg_1", "type": "message", "role": "assistant",
                "content": [{"type": "thinking", "thinking": "hmm ok"},
                            {"type": "tool_use", "id": "t1", "name": "f", "input": {}}],
                "stop_reason": "tool_use", "usage": {"input_tokens": 11, "output_tokens": 6}})
        resp = await self._sse(request)

        def ev(name: str, d: dict[str, Any]) -> bytes:
            return f"event: {name}\ndata: {json.dumps(d)}\n\n".encode()
        seq = [
            ev("message_start", {"type": "message_start", "message": {
                "id": "msg_2", "usage": {"input_tokens": 9, "output_tokens": 0}}}),
            ev("content_block_start", {"type": "content_block_start", "index": 0,
                                       "content_block": {"type": "thinking", "thinking": ""}}),
            ev("content_block_delta", {"type": "content_block_delta", "index": 0,
                                       "delta": {"type": "thinking_delta", "thinking": "hm"}}),
            ev("content_block_delta", {"type": "content_block_delta", "index": 0,
                                       "delta": {"type": "thinking_delta", "thinking": "m"}}),
            ev("content_block_start", {"type": "content_block_start", "index": 1,
                                       "content_block": {"type": "text", "text": ""}}),
            ev("content_block_delta", {"type": "content_block_delta", "index": 1,
                                       "delta": {"type": "text_delta", "text": "Hi"}}),
            ev("message_delta", {"type": "message_delta", "delta": {"stop_reason": "max_tokens"},
                                 "usage": {"output_tokens": 3}}),
            ev("message_stop", {"type": "message_stop"}),
        ]
        for s in seq:
            await self._send(request, resp, s, "messages")
            await asyncio.sleep(0.01)
        return resp

    # ---- /v1/responses
    async def responses(self, request: web.Request) -> web.StreamResponse:
        body = await self._record(request)
        final = {"id": "resp_1", "status": "incomplete",
                 "incomplete_details": {"reason": "max_output_tokens"},
                 "output": [{"type": "message", "content": [{"type": "output_text", "text": "ok"}]}],
                 "usage": {"input_tokens": 8, "output_tokens": 4,
                           "output_tokens_details": {"reasoning_tokens": 2}}}
        if not body.get("stream"):
            final = {**final, "status": "completed", "incomplete_details": None}
            return web.json_response(final)
        resp = await self._sse(request)

        def ev(d: dict[str, Any]) -> bytes:
            return f"event: {d['type']}\ndata: {json.dumps(d)}\n\n".encode()
        for d in [{"type": "response.created", "response": {"id": "resp_1"}},
                  {"type": "response.reasoning_text.delta", "delta": "x"},
                  {"type": "response.reasoning_text.delta", "delta": "y"},
                  {"type": "response.output_text.delta", "delta": "ok"},
                  {"type": "response.incomplete", "response": final}]:
            await self._send(request, resp, ev(d), "responses")
            await asyncio.sleep(0.01)
        return resp

    async def embeddings(self, request: web.Request) -> web.Response:
        await self._record(request)
        return web.json_response({"data": [{"embedding": [0.1, 0.2], "index": 0}],
                                  "usage": {"prompt_tokens": 5, "total_tokens": 5}})
