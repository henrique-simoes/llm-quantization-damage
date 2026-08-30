#!/usr/bin/env python3
"""Small local regression tests for the Wave-1 harness contracts.

These tests deliberately exercise only deterministic seams; GPU/container runs remain
remote acceptance evidence and are not hidden behind mocks here.
"""
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch


HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
import lib_e12 as L
import tsweep_v2 as T
import validate_v2 as V


class Wave1ContractTests(unittest.TestCase):
    def test_tensor_split_argument_is_separate_from_context(self):
        result = SimpleNamespace(returncode=0, stdout="", stderr="")
        with patch.object(L, "sh", return_value=result):
            command, rc, _ = L.launch("/srv/models/model.gguf", 212992, ts="54,46")
        self.assertEqual(rc, 0)
        self.assertIn("-ts 54,46 -c 212992", command)
        self.assertNotIn("54,46-c", command)

    def test_deterministic_argument_failure_precedes_stage_fallback(self):
        self.assertEqual(
            L.classify_failure("error: invalid argument: 212992", "health"),
            "launch-args",
        )

    def test_sampler_can_be_stopped_when_preflight_failed(self):
        sampler = L.VramSampler()
        self.assertEqual(sampler.stop()["samples"], 0)

    def test_c1_requires_explicit_non_truncated_response(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as log:
            log.write("n_slots = 1, n_ctx_slot = 32768\nflash-attn = on\n")
            path = log.name
        try:
            with patch.object(
                L,
                "image_provenance",
                return_value={"image_id": "img", "matches_manifest": True},
            ):
                ok, detail = V.check_c1(
                    32768,
                    "docker run ...",
                    ["-fa", "on", "-sm", "layer", "-fit", "off", "-c", "32768",
                     "-ctk", "q4_0", "-ctv", "q4_0", "-ctxcp", "4", "-np", "1"],
                    True,
                    1,
                    {"serverlog": path},
                    prefill_resp={},
                    live_props={
                        "default_generation_settings": {"n_ctx": 32768},
                        "total_slots": 1,
                    },
                )
            self.assertFalse(ok)
            self.assertIsNone(detail["response_truncated"])
        finally:
            os.unlink(path)

    def test_c4_requires_response_model_source(self):
        env = {
            "image": {"image_id": "img"},
            "model": {"sha256": "sha"},
            "seed": 1,
            "sampling_non_thinking": {"temperature": 0.7},
            "kv_dtype": "q4_0",
            "spec": "mtp2",
            "ctx_requested": 32768,
            "ctxcp": 4,
            "free_bytes": {"/": 1},
            "recorded_utc": "now",
        }
        with patch.object(
            L, "gguf_provenance", return_value={"file": V.MODEL, "sha256": "sha"}
        ), patch.object(L, "props_model_path", return_value="/models/Q.gguf"):
            ok, detail = V.check_c4(V.MODEL, model_resp_field=None, env=env)
        self.assertFalse(ok)
        self.assertFalse(detail["response_model_matches_requested"])

    # ---- pad-depth contract (2026-08-30 bisection defect) --------------------------
    # The corpus is ~2.9 chars/token in its first 200 kB and ~4.45 chars/token after, so
    # cpt calibrated on text[:200_000] badly under-estimates the cut. The OLD build()
    # bisected a FIXED bracket [0.9, 1.15]*cpt*target, could not reach outside it, kept the
    # LAST probe rather than the closest, and returned ~16 % short with no error. These
    # tests reproduce exactly that density profile.
    @staticmethod
    def _piecewise_tokenize(text):
        n = len(text)
        dense = min(n, 200_000)
        return ["t"] * int(dense / 2.9 + max(0, n - 200_000) / 4.45)

    def _build_with_corpus(self, target, tmpdir):
        import pad_e12 as P
        from pathlib import Path
        corpus = Path(tmpdir) / "corpus.txt"
        corpus.write_text("x" * 4_000_000)
        with patch.object(P, "CORPUS_CACHE", corpus), \
             patch.object(P, "PAD_DIR", Path(tmpdir) / "pads"), \
             patch.object(L, "tokenize", self._piecewise_tokenize):
            return P.build(target, with_needles=False)

    def test_pad_reaches_target_when_cpt_calibration_is_wrong(self):
        """The regression: 201,830 tokens must be reached despite the density change."""
        import pad_e12 as P
        with tempfile.TemporaryDirectory() as td:
            _text, n = self._build_with_corpus(201_830, td)
        self.assertLessEqual(abs(n - 201_830), P.tolerance(201_830))

    def test_pad_raises_rather_than_returning_short(self):
        """Corpus too small to reach the target -> RuntimeError, never a short pad."""
        import pad_e12 as P
        from pathlib import Path
        with tempfile.TemporaryDirectory() as td:
            corpus = Path(td) / "corpus.txt"
            corpus.write_text("x" * 50_000)          # ~17 k tokens, target is 200 k
            with patch.object(P, "CORPUS_CACHE", corpus), \
                 patch.object(P, "PAD_DIR", Path(td) / "pads"), \
                 patch.object(P, "_raw_text", lambda _min: corpus.read_text()), \
                 patch.object(L, "tokenize", self._piecewise_tokenize):
                with self.assertRaises(RuntimeError):
                    P.build(200_000, with_needles=False)

    def test_cached_short_pad_is_quarantined_and_rebuilt(self):
        """The two bad pads already on disk must self-heal on read, not be trusted."""
        import pad_e12 as P
        from pathlib import Path
        with tempfile.TemporaryDirectory() as td:
            pads = Path(td) / "pads"
            pads.mkdir()
            (pads / "pad_201830_0.txt").write_text("x" * 648_728)   # the short pad shipped
            corpus = Path(td) / "corpus.txt"
            corpus.write_text("x" * 4_000_000)
            with patch.object(P, "CORPUS_CACHE", corpus), \
                 patch.object(P, "PAD_DIR", pads), \
                 patch.object(L, "tokenize", self._piecewise_tokenize):
                _text, n = P.build(201_830, with_needles=False)
            self.assertLessEqual(abs(n - 201_830), P.tolerance(201_830))
            self.assertTrue(list(pads.glob("pad_201830_0.txt.bad-*")),
                            "short cached pad must be quarantined, not silently reused")

    def test_shallow_prefill_fails_the_cell_instead_of_being_reported(self):
        """A pad below 0.90 of the window must fail the cell as 'pad-too-short'."""
        sweep = T.Sweep.__new__(T.Sweep)
        sweep.q = "Q4_K_XL"
        sweep.cfg = T.QUANTS["Q4_K_XL"]
        sweep.redo = False
        sweep.keys = set()
        sweep.data = {"cells": []}
        sweep.write = lambda: None
        captured = {}

        def fake_finish(_self, rec, lbl, sampler):
            captured.update(rec)
            return rec

        with patch.object(T.Sweep, "finish_cell", fake_finish), \
             patch.object(L, "preflight", lambda *a, **k: []), \
             patch.object(L, "launch", lambda *a, **k: ("cmd", 0, "")), \
             patch.object(L, "image_provenance", lambda *a, **k: {"image_id": "img"}), \
             patch.object(L, "wait_health", lambda *a, **k: (True, 1)), \
             patch.object(L, "props_nctx", lambda: 212992), \
             patch.object(T.P, "build", lambda *a, **k: ("text", 169_823)):
            sweep.run_cell(212992, "56,44")
        self.assertEqual(captured["failure_mode"], "pad-too-short")
        self.assertFalse(captured["ok"])
        self.assertAlmostEqual(captured["prefill_frac"], 0.7973, places=3)

    def test_d2_equal_medians_use_declared_tie_break(self):
        sweep = T.Sweep.__new__(T.Sweep)
        sweep.data = {"cells": []}
        cells = [
            {"ctx_requested": 10, "ts": "54,46", "rep": 1, "tag": None,
             "ok": True, "decode_tok_s": 10.0, "imbalance_mib": 200, "key": "a"},
            {"ctx_requested": 10, "ts": None, "rep": 1, "tag": None,
             "ok": True, "decode_tok_s": 10.0, "imbalance_mib": 100, "key": "b"},
        ]
        self.assertEqual(sweep.pick_best(cells)["ts"], None)


if __name__ == "__main__":
    unittest.main()
