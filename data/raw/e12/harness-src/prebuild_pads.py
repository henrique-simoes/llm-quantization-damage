#!/usr/bin/env python3
"""prebuild_pads.py — build & VERIFY every context pad the Wave-1 sweep can need, once,
against a cheap small-ctx server, so no sweep cell ever pays for a pad build or inherits a
short one. Validates the pads already cached (the 2026-08-30 bisection defect left two on
disk that were ~16 % short; build() now quarantines and rebuilds any such file on read).

Targets are exactly what tsweep_v2.run_cell asks for: int(ctx * 0.95) - 512 for every rung
on the LADDER that any quant can visit.
"""
import json
import sys
import time

sys.path.insert(0, "/srv/bench/e12/experiments")
import lib_e12 as L
import pad_e12 as P

LADDER = [262144, 245760, 229376, 212992, 196608, 180224, 163840, 147456, 131072]
TOKENIZER_MODEL = "/srv/models/Qwen3.8-27B-UD-Q4_K_XL.gguf"   # tokenizer is identical across quants
OUT = "/srv/bench/e12/pads-manifest.json"


def main():
    L.preflight()
    cmd, rc, err = L.launch(TOKENIZER_MODEL, 8192, kv="q4_0", spec="none")
    print("launch rc", rc, cmd[:150], flush=True)
    assert rc == 0, err
    ok, secs = L.wait_health(600)
    assert ok, "tokenizer server never became healthy: " + L.container_err(800)
    print(f"tokenizer server up in {secs}s", flush=True)

    rows = []
    try:
        for ctx in LADDER:
            target = int(ctx * 0.95) - 512
            t0 = time.time()
            text, n = P.build(target, with_needles=False)
            frac = n / ctx
            rows.append({"ctx": ctx, "target_tokens": target, "actual_tokens": n,
                         "chars": len(text), "prefill_frac": round(frac, 4),
                         "err_tokens": n - target, "tol": P.tolerance(target),
                         "gate_0p90_ok": frac >= 0.90, "build_s": round(time.time() - t0, 1)})
            print("  ctx %-7d target %-7d actual %-7d err %+5d frac %.4f gate %s (%.0fs)" % (
                ctx, target, n, n - target, frac, "OK" if frac >= 0.90 else "FAIL",
                time.time() - t0), flush=True)
    finally:
        L.save_and_kill("e12-prebuild-pads")
        L.gpu_lock_release()

    art = {"experiment": "e12-pads-prebuild", "source": "e12-wave1",
           "run_ids": ["prebuild-pads"], "when_utc": L.utcnow(),
           "tokenizer_model": TOKENIZER_MODEL,
           "image": L.image_provenance(),
           "corpus": {"path": str(P.CORPUS_CACHE), "bytes": P.CORPUS_CACHE.stat().st_size},
           "rule": "target = int(ctx*0.95)-512; a pad is valid iff |actual-target| <= "
                   "max(64, 0.005*target) AND actual/ctx >= 0.90",
           "all_ok": all(r["gate_0p90_ok"] and abs(r["err_tokens"]) <= r["tol"] for r in rows),
           "pads": rows}
    with open(OUT, "w") as f:
        json.dump(art, f, indent=1)
    print("\nall_ok:", art["all_ok"], "->", OUT, flush=True)
    return 0 if art["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
