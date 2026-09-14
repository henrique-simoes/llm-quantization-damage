#!/usr/bin/env python3
"""llamacpp-sidecar — Prometheus exporter for llama.cpp servers (plan §3.2).

Per server in targets.yml it polls /health and /slots (1 Hz) and /props (60 s), follows
`docker logs -f --timestamps` for per-request timings and error events, and watches the
container via `docker inspect` for restarts and launch provenance. It never reads the
upstream /metrics endpoint (each GET resets llama.cpp's gauge windows).
"""
from __future__ import annotations

import argparse
import json
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from logparse import LogParser, SidecarLogMetrics, find_load_done  # noqa: E402
from parsers import LAUNCH_LABELS, format_rfc3339, health_state, parse_launch_args, parse_rfc3339, slot_gauges  # noqa: E402
from promtext import Registry  # noqa: E402

HEALTH_STATES = ("ok", "loading", "error", "down")
INSPECT_INTERVAL_S = 5.0
PROPS_INTERVAL_S = 60.0
STOP = threading.Event()


def log(msg: str) -> None:
    print(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), msg, file=sys.stderr, flush=True)


def http_get(url: str, timeout: float = 3.0) -> tuple[int | None, str]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except (urllib.error.URLError, OSError, TimeoutError):
        return None, ""


class Families:
    def __init__(self, reg: Registry):
        L = ("server", "model")
        self.health = reg.gauge("llamacpp_server_health", "One-hot server state from GET /health (ok|loading|error|down).", L + ("state",))
        self.start_time = reg.gauge("llamacpp_server_start_time_seconds", "Container State.StartedAt, unix seconds.", L)
        self.load_duration = reg.gauge("llamacpp_server_load_duration_seconds", "Container start to first /health 200 (or log model-loaded line).", L)
        self.restarts = reg.counter("llamacpp_server_restarts_total", "Container start transitions observed by the sidecar.", L)
        self.info = reg.gauge("llamacpp_server_info", "Server properties from /props.", L + ("build", "model_path", "n_ctx", "total_slots"))
        self.launch = reg.gauge("llamacpp_server_launch_info", "Launch provenance parsed from docker inspect Args.", L + LAUNCH_LABELS)
        S = L + ("slot",)
        self.slot = {
            "processing": reg.gauge("llamacpp_slot_processing", "1 while the slot is processing a task (/slots is_processing).", S),
            "kv_tokens": reg.gauge("llamacpp_slot_kv_tokens", "Tokens held in the slot: n_prompt_tokens + next_token[0].n_decoded.", S),
            "n_ctx": reg.gauge("llamacpp_slot_n_ctx", "Slot context size.", S),
            "prompt_processed_tokens": reg.gauge("llamacpp_slot_prompt_processed_tokens", "Prefill progress of the active request (n_prompt_tokens_processed).", S),
            "prompt_cache_tokens": reg.gauge("llamacpp_slot_prompt_cache_tokens", "Prompt tokens reused from cache for the active request.", S),
            "decoded_tokens": reg.gauge("llamacpp_slot_decoded_tokens", "Tokens decoded so far in the active request.", S),
        }
        self.follow_up = reg.gauge("llamacpp_sidecar_log_follow_up", "1 while a docker logs -f follower is attached.", L)
        self.logs = SidecarLogMetrics(reg)


class ServerMonitor:
    def __init__(self, cfg: dict, fam: Families, poll_interval: float, use_docker: bool = True, clock=time.time):
        self.name: str = cfg["name"]
        self.upstream: str = cfg["upstream"].rstrip("/")
        self.container: str | None = cfg.get("container") or None
        self.router: bool = bool(cfg.get("router", False))
        self.models: list[str] = list(cfg.get("models") or [])
        # router mode serves several models from one process: process-level series carry model=""
        self.model = "" if self.router else (self.models[0] if self.models else "")
        self.lab = {"server": self.name, "model": self.model}
        self.fam, self.poll_interval, self.use_docker, self.clock = fam, poll_interval, use_docker and bool(self.container), clock
        self.parser = LogParser(fam.logs, self.name, self.model)
        self.lock = threading.Lock()
        self.prev_state: str | None = None
        self.ok_since: float | None = None  # wall time of the last non-ok -> ok transition
        self.pending_load: float | None = None  # StartedAt awaiting a load-duration value
        self.last_key: tuple | None = None
        self.replay_from: float | None = None
        self.follower: subprocess.Popen | None = None
        self.last_props = 0.0

    # ---------- HTTP polling ----------
    def poll_once(self) -> str:
        status, body = http_get(self.upstream + "/health")
        state = health_state(status, body)
        for s in HEALTH_STATES:
            self.fam.health.set({**self.lab, "state": s}, 1.0 if s == state else 0.0)
        self.on_health(state)

        targets = self.models if self.router else [None]
        for m in targets:
            model_label = m if m is not None else self.model
            for g in self.fam.slot.values():
                g.remove_matching(server=self.name, model=model_label)
            if state == "down":
                continue
            q = "?" + urllib.parse.urlencode({"model": m}) if m else ""
            st, body = http_get(self.upstream + "/slots" + q)
            if st != 200:
                continue
            try:
                slots = json.loads(body)
            except ValueError:
                continue
            for slot in slots if isinstance(slots, list) else []:
                labels = {"server": self.name, "model": model_label, "slot": str(slot.get("id", ""))}
                for key, val in slot_gauges(slot).items():
                    self.fam.slot[key].set(labels, val)

        now = time.monotonic()
        if state != "down" and now - self.last_props >= PROPS_INTERVAL_S:
            ok = all(self.poll_props(m) for m in targets)
            self.last_props = now if ok else now - PROPS_INTERVAL_S + 10
        return state

    def poll_props(self, m: str | None) -> bool:
        q = "?" + urllib.parse.urlencode({"model": m}) if m else ""
        st, body = http_get(self.upstream + "/props" + q)
        if st != 200:
            return False
        try:
            p = json.loads(body)
        except ValueError:
            return False
        model_label = m if m is not None else self.model
        dgs = p.get("default_generation_settings") or {}
        self.fam.info.remove_matching(server=self.name, model=model_label)
        self.fam.info.set(
            {
                "server": self.name,
                "model": model_label,
                "build": p.get("build_info", ""),
                "model_path": p.get("model_path", ""),
                "n_ctx": str(dgs.get("n_ctx", "")),
                "total_slots": str(p.get("total_slots", "")),
            },
            1.0,
        )
        return True

    def poll_loop(self) -> None:
        while not STOP.is_set():
            t0 = time.monotonic()
            try:
                self.poll_once()
            except Exception as e:  # keep polling whatever one response looked like
                log(f"[{self.name}] poll error: {e!r}")
            STOP.wait(max(0.0, self.poll_interval - (time.monotonic() - t0)))

    # ---------- load duration ----------
    def on_health(self, state: str) -> None:
        now = self.clock()
        start_recovery = None
        with self.lock:
            if state == "ok" and self.prev_state is not None and self.prev_state != "ok":
                self.ok_since = now
            self.prev_state = state
            S = self.pending_load
            if S is not None and state == "ok":
                self.pending_load = None
                if self.ok_since is not None and self.ok_since >= S:
                    self.fam.load_duration.set(self.lab, self.ok_since - S)
                else:
                    start_recovery = S  # already healthy when we first looked: ask the log
        if start_recovery is not None and self.use_docker:
            threading.Thread(target=self.recover_load_from_logs, args=(start_recovery,), daemon=True).start()

    def recover_load_from_logs(self, started_at: float) -> None:
        cmd = ["docker", "logs", "--timestamps", "--since", format_rfc3339(started_at - 1), self.container]
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
        except OSError as e:
            log(f"[{self.name}] load recovery failed: {e!r}")
            return
        timer = threading.Timer(120, proc.kill)
        timer.start()
        try:
            val = find_load_done(proc.stdout, started_at)
        finally:
            timer.cancel()
            proc.kill()
            proc.wait()
        if val is not None:
            self.fam.load_duration.set(self.lab, val)
            log(f"[{self.name}] load duration recovered from docker logs: {val:.3f} s")
        else:
            log(f"[{self.name}] load duration: no model-loaded line found in docker logs")

    # ---------- container lifecycle ----------
    def inspect_once(self) -> None:
        r = subprocess.run(["docker", "inspect", self.container], capture_output=True, text=True, timeout=20)
        if r.returncode != 0:
            return
        c = json.loads(r.stdout)[0]
        started = parse_rfc3339(c.get("State", {}).get("StartedAt", ""))
        if started is None:
            return
        key = (c.get("Id"), started)
        launch = parse_launch_args(c.get("Args") or [], (c.get("Config") or {}).get("Image", ""))
        self.fam.launch.remove_matching(server=self.name)
        self.fam.launch.set({**self.lab, **launch}, 1.0)
        self.fam.start_time.set(self.lab, started)
        if self.last_key is None:
            self.fam.restarts.inc(self.lab, 0)
            with self.lock:
                self.pending_load = started
        elif key != self.last_key:
            self.fam.restarts.inc(self.lab)
            log(f"[{self.name}] container start transition: StartedAt={format_rfc3339(started)}")
            with self.lock:
                self.pending_load = started
                self.replay_from = started
                self.parser.reset_tasks()  # task ids restart with the process
            self.fam.load_duration.remove_matching(server=self.name)
            proc = self.follower
            if proc and proc.poll() is None:
                proc.terminate()
        self.last_key = key

    def inspect_loop(self) -> None:
        while not STOP.is_set():
            try:
                self.inspect_once()
            except Exception as e:
                log(f"[{self.name}] docker inspect error: {e!r}")
            STOP.wait(INSPECT_INTERVAL_S)

    # ---------- log follower ----------
    def follow_loop(self) -> None:
        since = self.clock()  # never replay history into counters at sidecar start
        backoff = 1.0
        while not STOP.is_set():
            with self.lock:
                if self.replay_from is not None:
                    since, self.replay_from = self.replay_from, None
            cmd = ["docker", "logs", "-f", "--timestamps", "--since", format_rfc3339(since), self.container]
            t0 = time.monotonic()
            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace", bufsize=1)
            except OSError as e:
                log(f"[{self.name}] cannot start docker logs: {e!r}")
                proc = None
            if proc is not None:
                self.follower = proc
                self.fam.follow_up.set(self.lab, 1.0)
                for line in proc.stdout:
                    with self.lock:
                        self.parser.feed(line, dedupe=True)
                proc.wait()
                self.fam.follow_up.set(self.lab, 0.0)
                self.follower = None
            if STOP.is_set():
                break
            with self.lock:
                replay = self.replay_from is not None
            if replay:
                continue
            if time.monotonic() - t0 > 30:
                backoff = 1.0
            log(f"[{self.name}] log follower exited; reconnecting in {backoff:.0f} s")
            STOP.wait(backoff)
            backoff = min(backoff * 2, 30.0)
            if self.parser.last_ts is not None:
                since = self.parser.last_ts  # lines at or before last_ts are skipped by dedupe

    def start(self) -> list[threading.Thread]:
        fns = [self.poll_loop]
        if self.use_docker:
            self.fam.follow_up.set(self.lab, 0.0)
            fns += [self.inspect_loop, self.follow_loop]
        threads = [threading.Thread(target=f, name=f"{self.name}-{f.__name__}", daemon=True) for f in fns]
        for t in threads:
            t.start()
        return threads

    def shutdown(self) -> None:
        proc = self.follower
        if proc and proc.poll() is None:
            proc.terminate()


def load_config(path: str | None) -> dict:
    if not path:
        return {}
    import yaml

    with open(path) as f:
        return yaml.safe_load(f) or {}


def split_listen(s: str) -> tuple[str, int]:
    host, _, port = s.rpartition(":")
    return host or "127.0.0.1", int(port)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--config", help="targets.yml")
    ap.add_argument("--listen", help="host:port for /metrics (overrides sidecar.listen)")
    ap.add_argument("--server", help="only monitor this targets.yml server name")
    ap.add_argument("--upstream", help="override upstream base URL (single selected server)")
    ap.add_argument("--container", help="override container name (single selected server)")
    ap.add_argument("--model", help="served alias when running without --config")
    ap.add_argument("--name", default="default", help="server name when running without --config")
    ap.add_argument("--poll-interval", type=float, help="seconds between /health+/slots polls")
    ap.add_argument("--no-docker", action="store_true", help="disable docker inspect/logs (HTTP polling only)")
    a = ap.parse_args(argv)

    cfg = load_config(a.config)
    servers = list(cfg.get("servers") or [])
    if not servers:
        if not a.upstream:
            ap.error("no servers: pass --config or --upstream")
        servers = [{"name": a.name, "upstream": a.upstream, "container": a.container, "models": [a.model] if a.model else []}]
    if a.server:
        servers = [s for s in servers if s["name"] == a.server]
        if not servers:
            ap.error(f"server {a.server!r} not in config")
    if (a.upstream or a.container) and len(servers) != 1:
        ap.error("--upstream/--container need exactly one server (use --server)")
    if a.upstream:
        servers[0]["upstream"] = a.upstream
    if a.container:
        servers[0]["container"] = a.container

    sc = cfg.get("sidecar") or {}
    host, port = split_listen(a.listen or sc.get("listen", "127.0.0.1:9900"))
    interval = a.poll_interval or float(sc.get("poll_interval_s", 1))

    reg = Registry()
    fam = Families(reg)
    monitors = [ServerMonitor(s, fam, interval, use_docker=not a.no_docker) for s in servers]
    for mon in monitors:
        mon.start()
        log(f"monitoring {mon.name} upstream={mon.upstream} container={mon.container} model={mon.model!r} router={mon.router}")

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = self.path.split("?")[0]
            if path == "/metrics":
                body, ctype, code = reg.render().encode(), "text/plain; version=0.0.4; charset=utf-8", 200
            elif path in ("/", "/healthz"):
                body, ctype, code = b"ok\n", "text/plain", 200
            else:
                body, ctype, code = b"not found\n", "text/plain", 404
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    httpd = ThreadingHTTPServer((host, port), Handler)
    httpd.daemon_threads = True

    def stop(*_):
        STOP.set()
        for mon in monitors:
            mon.shutdown()
        threading.Thread(target=httpd.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    log(f"listening on http://{host}:{port}/metrics")
    httpd.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
