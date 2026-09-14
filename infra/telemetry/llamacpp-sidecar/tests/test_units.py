import json
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from logparse import classify_event  # noqa: E402
from parsers import (  # noqa: E402
    format_rfc3339,
    health_state,
    parse_launch_args,
    parse_rfc3339,
    slot_gauges,
    split_docker_timestamp,
)
from promtext import Registry  # noqa: E402
import llamacpp_sidecar as sc  # noqa: E402

LIVE_ARGS = ["-m", "/models2/Qwen3.8-27B-UD-Q6_K.gguf", "--alias", "qwen3.8-27b-ud-q6k", "--host", "100.64.0.10",
             "--port", "8080", "-ngl", "99", "-sm", "layer", "-ts", "58,42", "-c", "262144", "-fit", "off", "-fa", "on",
             "-ctk", "q4_0", "-ctv", "q4_0", "-b", "2048", "-ub", "512", "-np", "1", "-ctxcp", "32", "--spec-type",
             "draft-mtp", "--spec-draft-n-max", "2", "--jinja", "--temp", "0.7", "--top-p", "0.80", "--top-k", "20",
             "--min-p", "0.0", "--presence-penalty", "1.5", "--metrics"]


class LaunchArgsTest(unittest.TestCase):
    def test_short_spellings_live_container(self):
        got = parse_launch_args(LIVE_ARGS, "llamacpp-mtp:latest")
        self.assertEqual(got, {
            "ctx": "262144", "ctk": "q4_0", "ctv": "q4_0", "ts": "58,42", "sm": "layer", "spec_type": "draft-mtp",
            "draft_n_max": "2", "ctxcp": "32", "batch": "2048", "ubatch": "512", "np": "1", "fa": "on",
            "image": "llamacpp-mtp:latest",
        })

    def test_long_spellings_and_equals(self):
        args = ["--ctx-size=131072", "--cache-type-k", "f16", "--cache-type-v=q8_0", "--tensor-split", "56,44",
                "--split-mode", "layer", "--ctx-checkpoints", "4", "--batch-size", "4096", "--ubatch-size", "1024",
                "--parallel", "2", "--flash-attn", "auto", "--spec-type=none", "--spec-draft-n-max=4"]
        got = parse_launch_args(args)
        self.assertEqual(got, {
            "ctx": "131072", "ctk": "f16", "ctv": "q8_0", "ts": "56,44", "sm": "layer", "spec_type": "none",
            "draft_n_max": "4", "ctxcp": "4", "batch": "4096", "ubatch": "1024", "np": "2", "fa": "auto", "image": "",
        })

    def test_bare_flag_negative_number_last_wins_missing(self):
        got = parse_launch_args(["-fa", "-ngl", "99", "-np", "-1", "-c", "4096", "-c", "8192", "-ctk"])
        self.assertEqual(got["fa"], "on")
        self.assertEqual(got["np"], "-1")
        self.assertEqual(got["ctx"], "8192")
        self.assertEqual(got["ctk"], "on")
        self.assertEqual(got["ts"], "")
        # alias values that look like flags are not consumed as values of unrelated flags
        self.assertEqual(parse_launch_args(["--alias", "-c", "-c", "10"])["ctx"], "10")


class TimestampTest(unittest.TestCase):
    def test_rfc3339_nano(self):
        t = parse_rfc3339("2026-09-14T22:03:52.125837787Z")
        self.assertAlmostEqual(t, 1789423432.125837787, places=6)
        self.assertEqual(parse_rfc3339("2026-09-14T23:03:52+01:00"), parse_rfc3339("2026-09-14T22:03:52Z"))
        self.assertIsNone(parse_rfc3339("0001-01-01T00:00:00Z"))
        self.assertIsNone(parse_rfc3339("garbage"))
        self.assertAlmostEqual(parse_rfc3339(format_rfc3339(t)), t, places=6)

    def test_split_docker_prefix(self):
        ts, rest = split_docker_timestamp("2026-09-14T22:33:41.579491886Z 29.46.669.690 I slot release")
        self.assertAlmostEqual(ts, parse_rfc3339("2026-09-14T22:33:41.579491886Z"))
        self.assertEqual(rest, "29.46.669.690 I slot release")
        self.assertEqual(split_docker_timestamp("3.28.417.498 I srv  llama_server: model loaded"),
                         (None, "3.28.417.498 I srv  llama_server: model loaded"))


class SlotMathTest(unittest.TestCase):
    def test_active_slot(self):
        slot = {"id": 0, "n_ctx": 262144, "is_processing": True, "n_prompt_tokens": 42000,
                "n_prompt_tokens_processed": 1500, "n_prompt_tokens_cache": 40000,
                "next_token": [{"has_next_token": True, "n_remain": 100, "n_decoded": 321}]}
        self.assertEqual(slot_gauges(slot), {"processing": 1.0, "kv_tokens": 42321.0, "n_ctx": 262144.0,
                                             "prompt_processed_tokens": 1500.0, "prompt_cache_tokens": 40000.0,
                                             "decoded_tokens": 321.0})

    def test_idle_slot_and_legacy_shape(self):
        idle = {"id": 0, "n_ctx": 262144, "is_processing": False, "n_prompt_tokens": 59002,
                "n_prompt_tokens_processed": 0, "n_prompt_tokens_cache": 0, "next_token": [{"n_decoded": 0}]}
        g = slot_gauges(idle)
        self.assertEqual((g["processing"], g["kv_tokens"], g["decoded_tokens"]), (0.0, 59002.0, 0.0))
        self.assertEqual(slot_gauges({"next_token": {"n_decoded": 7}, "n_prompt_tokens": 3})["kv_tokens"], 10.0)

    def test_health_state(self):
        self.assertEqual([health_state(s) for s in (200, 503, 500, 404, None)], ["ok", "loading", "error", "error", "down"])


class EventTest(unittest.TestCase):
    def test_classify(self):
        self.assertEqual(classify_event(None, "CUDA error: an illegal memory access was encountered"), "cuda_error")
        self.assertEqual(classify_event("E", "1.0.0.0 E ggml_backend_cuda_buffer_type_alloc_buffer: cudaMalloc failed: out of memory"), "oom")
        self.assertEqual(classify_event("W", "sched_reserve: compute buffer allocation failed, retrying without pipeline parallelism"), "alloc_retry")
        self.assertEqual(classify_event("E", "1.0.0.0 E slot update_slots: id  0 | task 5 | something broke"), "slot_error")
        self.assertEqual(classify_event("E", "1.0.0.0 E srv  some other failure"), "other_error")
        self.assertIsNone(classify_event("I", "1.0.0.0 I slot print_timing: id  0 | task 1 | eval time = 1 ms / 2 tokens"))
        self.assertIsNone(classify_event("W", "1.0.0.0 W srv  alloc:  - prompt state size exceeds cache size limit"))


class RegistryTest(unittest.TestCase):
    def test_histogram_render(self):
        reg = Registry()
        h = reg.histogram("x_seconds", "help", ("server",), [1, 2])
        for v in (0.5, 1.5, 3):
            h.observe({"server": 'a"b'}, v)
        text = reg.render()
        self.assertIn('x_seconds_bucket{server="a\\"b",le="1.0"} 1', text)
        self.assertIn('x_seconds_bucket{server="a\\"b",le="2.0"} 2', text)
        self.assertIn('x_seconds_bucket{server="a\\"b",le="+Inf"} 3', text)
        self.assertIn('x_seconds_sum{server="a\\"b"} 5.0', text)


class StubUpstream:
    """Tiny llama-server lookalike for /health, /slots, /props (router-aware)."""

    def __init__(self, health_code=200):
        self.health_code = health_code
        self.requests: list[str] = []
        stub = self

        class H(BaseHTTPRequestHandler):
            def do_GET(self):
                stub.requests.append(self.path)
                path, _, query = self.path.partition("?")
                model = query.partition("model=")[2]
                if path == "/health":
                    code, body = stub.health_code, {"status": "ok"} if stub.health_code == 200 else {"error": {"message": "Loading model"}}
                elif path == "/slots":
                    code, body = 200, [
                        {"id": 0, "n_ctx": 4096 if model == "b" else 8192, "is_processing": True, "n_prompt_tokens": 100,
                         "n_prompt_tokens_processed": 60, "n_prompt_tokens_cache": 40, "next_token": [{"n_decoded": 5}]},
                        {"id": 1, "n_ctx": 8192, "is_processing": False, "n_prompt_tokens": 0,
                         "n_prompt_tokens_processed": 0, "n_prompt_tokens_cache": 0, "next_token": [{"n_decoded": 0}]},
                    ]
                elif path == "/props":
                    code, body = 200, {"build_info": "b1-test", "model_path": f"/models/{model or 'x'}.gguf",
                                       "total_slots": 2, "default_generation_settings": {"n_ctx": 8192}}
                elif path == "/metrics":
                    code, body = 500, {"error": "sidecar must never read /metrics"}
                else:
                    code, body = 404, {}
                data = json.dumps(body).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *a):
                pass

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


class MonitorPollTest(unittest.TestCase):
    def setUp(self):
        self.up = StubUpstream()

    def tearDown(self):
        self.up.close()

    def test_single_model_poll(self):
        fam = sc.Families(Registry())
        mon = sc.ServerMonitor({"name": "srv", "upstream": self.up.url, "models": ["m1"]}, fam, 1, use_docker=False)
        self.assertEqual(mon.poll_once(), "ok")
        L0 = {"server": "srv", "model": "m1", "slot": "0"}
        self.assertEqual(fam.slot["kv_tokens"].get(L0), 105.0)
        self.assertEqual(fam.slot["prompt_processed_tokens"].get(L0), 60.0)
        self.assertEqual(fam.slot["processing"].get({**L0, "slot": "1"}), 0.0)
        self.assertEqual(fam.health.get({"server": "srv", "model": "m1", "state": "ok"}), 1.0)
        self.assertEqual(fam.health.get({"server": "srv", "model": "m1", "state": "down"}), 0.0)
        self.assertIn('build="b1-test"', fam.info.reg.render())
        self.assertNotIn("/metrics", self.up.requests)

    def test_router_mode_queries_per_model(self):
        fam = sc.Families(Registry())
        mon = sc.ServerMonitor({"name": "r", "upstream": self.up.url, "models": ["a", "b"], "router": True}, fam, 1, use_docker=False)
        mon.poll_once()
        self.assertIn("/slots?model=a", self.up.requests)
        self.assertIn("/props?model=b", self.up.requests)
        self.assertEqual(fam.slot["n_ctx"].get({"server": "r", "model": "b", "slot": "0"}), 4096.0)
        self.assertEqual(fam.slot["n_ctx"].get({"server": "r", "model": "a", "slot": "0"}), 8192.0)
        self.assertEqual(fam.health.get({"server": "r", "model": "", "state": "ok"}), 1.0)

    def test_down_clears_slots(self):
        fam = sc.Families(Registry())
        mon = sc.ServerMonitor({"name": "srv", "upstream": self.up.url, "models": ["m1"]}, fam, 1, use_docker=False)
        mon.poll_once()
        mon.upstream = "http://127.0.0.1:9"  # nothing listens on the discard port
        self.assertEqual(mon.poll_once(), "down")
        self.assertIsNone(fam.slot["kv_tokens"].get({"server": "srv", "model": "m1", "slot": "0"}))


class LoadDurationTest(unittest.TestCase):
    def make(self):
        self.now = 1000.0
        fam = sc.Families(Registry())
        mon = sc.ServerMonitor({"name": "s", "upstream": "http://x", "models": ["m"]}, fam, 1, use_docker=False,
                               clock=lambda: self.now)
        return fam, mon

    def test_observed_loading_then_ok(self):
        fam, mon = self.make()
        mon.pending_load = 990.0
        mon.on_health("loading")
        self.now = 1042.0
        mon.on_health("ok")
        self.assertEqual(fam.load_duration.get({"server": "s", "model": "m"}), 52.0)

    def test_already_ok_asks_the_log(self):
        fam, mon = self.make()
        called = []
        mon.use_docker = True
        mon.recover_load_from_logs = lambda s: called.append(s)
        mon.pending_load = 500.0
        mon.on_health("ok")
        for _ in range(50):
            if called:
                break
            threading.Event().wait(0.01)
        self.assertEqual(called, [500.0])
        self.assertIsNone(fam.load_duration.get({"server": "s", "model": "m"}))


if __name__ == "__main__":
    unittest.main()
