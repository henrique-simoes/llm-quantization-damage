"""Log-derived series exist at zero before the first event."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from logparse import LogParser, SidecarLogMetrics  # noqa: E402
from promtext import Registry  # noqa: E402


class PreinitTest(unittest.TestCase):
    def test_zero_series_before_events(self):
        reg = Registry()
        LogParser(SidecarLogMetrics(reg), "s1", "m1")
        text = reg.render()
        self.assertIn('llamacpp_context_limit_hits_total{server="s1",model="m1"} 0.0', text)
        self.assertIn('llamacpp_log_events_total{server="s1",model="m1",event="cuda_error"} 0.0', text)
        self.assertIn('llamacpp_prefill_seconds_count{server="s1",model="m1"} 0', text)

    def test_touch_does_not_reset_existing(self):
        reg = Registry()
        metrics = SidecarLogMetrics(reg)
        metrics.ctx_hits.inc({"server": "s1", "model": "m1"})
        LogParser(metrics, "s1", "m1")
        self.assertIn('llamacpp_context_limit_hits_total{server="s1",model="m1"} 1.0', reg.render())


if __name__ == "__main__":
    unittest.main()
