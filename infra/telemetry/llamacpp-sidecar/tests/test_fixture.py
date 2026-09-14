"""Feed the saved 2026-09-14 serverlog through the parser and check it against grep/awk
computed independently on the same file."""
import os
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from logparse import LogParser, SidecarLogMetrics, find_load_done  # noqa: E402
from parsers import format_rfc3339  # noqa: E402
from promtext import Registry  # noqa: E402

FIXTURE = os.environ.get(
    "SIDECAR_FIXTURE", "/srv/bench/server-timings/qwen38-serve-pre-metrics-20260914T2203Z.serverlog"
)
LAB = {"server": "s", "model": "m"}


def sh(cmd: str) -> str:
    return subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, check=False).stdout.strip()


def num(cmd: str) -> float:
    out = sh(cmd)
    return float(out) if out else 0.0


def value(metric, labels=LAB):
    v = metric.get(labels)
    return 0.0 if v is None else v


@unittest.skipUnless(os.path.exists(FIXTURE), "fixture serverlog not present")
class FixtureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = Registry()
        cls.m = SidecarLogMetrics(cls.reg)
        cls.p = LogParser(cls.m, "s", "m")
        with open(FIXTURE, errors="replace") as f:
            for line in f:
                cls.p.feed(line)
        cls.F = f"'{FIXTURE}'"

    def test_releases(self):
        expected = num(f"grep -c 'stop processing: n_tokens' {self.F}")
        self.assertEqual(expected, 292)
        self.assertEqual(value(self.m.released), expected)
        self.assertEqual(value(self.m.depth)["count"], expected)
        self.assertEqual(self.p.tasks, {}, "every task in the fixture is released")

    def test_depth_sum_and_truncation(self):
        depth_sum = num(f"grep -o 'stop processing: n_tokens = [0-9]*' {self.F} | awk '{{s+=$NF}} END{{print s}}'")
        self.assertEqual(value(self.m.depth)["sum"], depth_sum)
        self.assertEqual(value(self.m.ctx_hits), num(f"grep -c 'truncated = 1' {self.F}"))

    def test_prefill(self):
        awk = (
            f"grep 'prompt eval time' {self.F} | "
            "awk -F'prompt eval time =' '{split($2,a,\" \"); ms+=a[1]; n+=a[4]; c++} END{printf \"%d %.6f %d\", c, ms, n}'"
        )
        c, ms, toks = sh(awk).split()
        h = value(self.m.prefill_seconds)
        self.assertEqual(h["count"], int(c))
        self.assertEqual(int(c), 278)
        self.assertAlmostEqual(h["sum"], float(ms) / 1000, places=6)
        self.assertEqual(value(self.m.prefill_tokens)["sum"], int(toks))
        self.assertEqual(self.p.totals["prompt_tokens"], int(toks))
        self.assertEqual(value(self.m.released_timed), int(c))

    def test_decode(self):
        # ' | <spaces>eval time' excludes 'prompt eval time'
        awk = (
            f"grep -E '\\| +eval time =' {self.F} | "
            "awk -F'eval time =' '{split($2,a,\" \"); n=a[4]; all+=n; if (n>=2) {steps+=n-1; ms+=a[1]; c++}} "
            "END{printf \"%d %d %.6f %d\", all, steps, ms, c}'"
        )
        all_tokens, steps, ms, c = sh(awk).split()
        self.assertEqual(self.p.totals["eval_tokens"], int(all_tokens))
        self.assertEqual(value(self.m.decode_steps), int(steps))
        self.assertAlmostEqual(value(self.m.decode_seconds), float(ms) / 1000, places=6)
        self.assertEqual(value(self.m.decode_tpt)["count"], int(c))

    def test_speculative(self):
        awk = (
            f"grep 'draft acceptance' {self.F} | "
            "sed -E 's/.*\\( *([0-9]+) accepted \\/ *([0-9]+) generated\\), mean len = *([0-9.]+).*/\\1 \\2 \\3/' | "
            "awk '{acc+=$1; gen+=$2; if ($2>=100) {c++; len+=$3}} END{printf \"%d %d %d %.6f\", acc, gen, c, len}'"
        )
        acc, gen, c, len_sum = sh(awk).split()
        self.assertEqual(self.p.totals["accepted"], int(acc))
        self.assertEqual(self.p.totals["drafted"], int(gen))
        h = value(self.m.spec_len)
        self.assertEqual(h["count"], int(c))
        self.assertAlmostEqual(h["sum"], float(len_sum), places=6)

    def test_levels(self):
        for lvl in "IWED":
            expected = num(f"grep -cE '^[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+ {lvl} ' {self.F}")
            self.assertEqual(value(self.m.log_lines, {**LAB, "level": lvl}), expected, lvl)
        self.assertEqual(value(self.m.log_lines, {**LAB, "level": "E"}), 3)

    def test_events(self):
        cuda = num(f"grep -ci 'CUDA error' {self.F}")
        oom = num(f"grep -viE 'CUDA error' {self.F} | grep -ciE 'out of memory|failed to allocate|cudaMalloc'")
        retry = num(f"grep -viE 'CUDA error|out of memory|failed to allocate|cudaMalloc' {self.F} | grep -c 'retrying without'")
        ev = lambda e: value(self.m.log_events, {**LAB, "event": e})  # noqa: E731
        self.assertEqual(ev("cuda_error"), cuda)
        self.assertEqual(ev("oom"), oom)
        self.assertEqual(ev("alloc_retry"), retry)
        self.assertEqual((oom, retry), (3, 1))
        self.assertEqual(ev("slot_error") + ev("other_error"), 0)


@unittest.skipUnless(os.path.exists(FIXTURE), "fixture serverlog not present")
class TimestampedReplayTest(unittest.TestCase):
    def _lines(self, t0: float):
        with open(FIXTURE, errors="replace") as f:
            raw = [next(f) for _ in range(400)]
        return [f"{format_rfc3339(t0 + i * 0.001)} {line}" for i, line in enumerate(raw)]

    def test_dedupe_on_reconnect(self):
        t0 = 1_800_000_000.0
        lines = self._lines(t0)
        reg = Registry()
        m = SidecarLogMetrics(reg)
        p = LogParser(m, "s", "m")
        for line in lines[:250]:
            p.feed(line, dedupe=True)
        for line in lines[100:]:  # reconnect with an overlapping --since
            p.feed(line, dedupe=True)
        ref = LogParser(SidecarLogMetrics(Registry()), "s", "m")
        for line in lines:
            ref.feed(line)
        self.assertEqual(value(m.released), value(ref.m.released))
        self.assertGreater(value(m.released), 0)
        self.assertEqual(p.totals, ref.totals)
        self.assertEqual(value(m.log_lines, {**LAB, "level": "I"}), value(ref.m.log_lines, {**LAB, "level": "I"}))

    def test_load_duration_from_log(self):
        t0 = 1_800_000_000.0
        lines = self._lines(t0)
        idx = next(i for i, l in enumerate(lines) if "llama_server: model loaded" in l)
        started = t0 - 2.5
        self.assertAlmostEqual(find_load_done(lines, started), idx * 0.001 + 2.5, places=6)
        self.assertIsNone(find_load_done(lines, t0 + 10))  # load line predates this start


if __name__ == "__main__":
    unittest.main()
