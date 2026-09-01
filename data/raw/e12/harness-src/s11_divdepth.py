#!/usr/bin/env python3
"""s11_divdepth.py — S11: GREEDY DIVERGENCE AT DEPTH.

THE QUESTION
  Does quantization damage grow with context depth? Every accuracy number in this study sits at
  n_ctx 2048; the deployment configuration runs at 262,144. S10 was to answer this with KL
  divergence and CANNOT: llama-perplexity holds a chunk's logits resident, and measurement on this
  host gives a hard ceiling of n_ctx 8,192 (at 16,384 the host fell to 305 MiB available and wrote
  zero bytes in 13 minutes; at 65,536 it threw std::bad_alloc). A 4x depth range cannot support a
  claim about a 128x deployment. S11 replaces the instrument, not the question.

WHY THIS INSTRUMENT REACHES DEPTH
  It never buffers logits. Each cell is one /completion call returning text, so RAM cost equals any
  ordinary serving run — the same runs we already do at 262,144. The depth ceiling becomes VRAM,
  which we have already mapped, instead of host RAM, which we have not.

WHY THE COMPARISON IS CLEAN — this rests on PN-26
  PN-26 established that no-spec greedy generation on this engine is byte-reproducible: the same
  configuration reproduced its 164 completions md5-identically across runs a day apart. So with
  speculation OFF and temperature 0, ANY text difference between two arms on the same prompt at the
  same depth is attributable to the quantization. Without PN-26 this experiment would be
  uninterpretable; with it, the instrument is exact.
  ⚠️ Speculation MUST stay off: PN-23/PN-26 show MTP alters ~20 % of completions for reasons that
  have nothing to do with the quant, which would swamp the effect being measured.

METRIC — first-divergence position, not exact-match rate
  Greedy decoding is a trajectory: once two arms emit a different token, everything after is on a
  different path and per-position comparison stops meaning anything. Exact-match would therefore be
  a coarse binary. The graded metric is WHERE the paths separate — the index of the first differing
  character against the reference arm's output on the identical prompt. Later divergence = closer
  agreement. If that index falls as depth rises, quantization damage grows with context.

CONTROLS BUILT IN, because this harness family has failed three times
  1. SELF-CONSISTENCY: the reference arm generates the same pad TWICE at the deepest rung. It must
     come back byte-identical. If it does not, the engine is not deterministic at this depth and
     every divergence number is uninterpretable — the run stops rather than reporting noise.
  2. DEPTH GATE: prefill_frac >= 0.90, asserted in code (PN-5).
  3. GENERATION GATE: >= GEN_FLOOR tokens actually produced, asserted in code. This is the gate
     whose absence let a 24-cell sweep report 17-token generations as results (PN-30).
  4. PILOT RUNS THE HARDEST CELL FIRST: reference arm at the deepest rung, where the VRAM estimate
     says RISK (16,426 MiB/GPU predicted against a 15,650 practical ceiling) while E11a measured
     that arm reaching 245,760 no-spec. The estimate and the history disagree, so it is measured
     before any battery runs.
"""
import argparse, json, os, sys, time

sys.path.insert(0, "/srv/bench/e12/experiments")
import lib_e12 as L

E12, OUTD, PADS = "/srv/bench/e12", "/srv/bench/e12/s11", "/srv/bench/e12/pads"
CORPUS = f"{E12}/corpus.txt"

REFERENCE = "Q6_K_XL"
ARMS = {
    "Q6_K_XL": "/srv/models/Qwen3.8-27B-UD-Q6_K_XL.gguf",     # reference
    "Q6_K":    "/srv/bench/models/Qwen3.8-27B-UD-Q6_K.gguf",
    "Q5_K_XL": "/srv/models/Qwen3.8-27B-UD-Q5_K_XL.gguf",
    "Q4_K_XL": "/srv/models/Qwen3.8-27B-UD-Q4_K_XL.gguf",
}
# ONE ratio for every arm. A per-arm ratio would put an uncontrolled variable into an accuracy
# comparison; 56,44 is Wave 1's winner for both Q6_K_XL and Q4_K_XL and is comfortable for the
# other two at these depths.
TS = "56,44"
DEPTHS = [8192, 65536, 196608]      # cheapest first, so each slice is usable if we stop early
N_PADS, GEN_TOKENS, GEN_FLOOR, DEPTH_GATE = 3, 512, 128, 0.90
SUFFIX = "\n\n# Summary:\n"          # tsweep_v2's proven continuation cue (PN-30)


def log(*a):
    print(f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}]", *a, flush=True)


def build_pads(ctx, n=N_PADS):
    """n non-overlapping excerpts of the corpus, each sized for this ctx.

    Character length is taken from the VERIFIED pad for this rung where one exists, so the token
    count is known-good; otherwise from the measured ~4.45 chars/token of this corpus. The
    prefill_frac gate is what actually protects the measurement, so an approximate size is safe."""
    raw = open(CORPUS).read()
    ref = {8192: None, 65536: None, 131072: f"{PADS}/pad_124006_0.txt",
           196608: f"{PADS}/pad_186265_0.txt"}.get(ctx)
    if ref and os.path.exists(ref):
        nchars = len(open(ref).read())
    else:
        nchars = int(ctx * 0.945 * 4.45)
    pads, off = [], 0
    for i in range(n):
        if off + nchars > len(raw):          # wrap rather than truncate
            off = 0
        pads.append(raw[off:off + nchars])
        off += nchars
    return pads


def generate(arm, ctx, pad, tag):
    """One greedy no-spec completion at depth. Returns the record."""
    body = {"prompt": pad + SUFFIX, "n_predict": GEN_TOKENS, "cache_prompt": False,
            "temperature": 0, "top_p": 1, "top_k": 1, "seed": L.SEED}
    try:
        r = L.post("/completion", body, timeout=7200)
    except Exception as e:
        return {"tag": tag, "ok": False, "error": str(e)[:300]}
    tm = r.get("timings", {}) or {}
    txt = r.get("content", "") or ""
    rec = {"tag": tag, "ok": True, "text": txt, "chars": len(txt),
           "predicted_n": tm.get("predicted_n"), "prompt_n": tm.get("prompt_n"),
           "prefill_frac": round((tm.get("prompt_n") or 0) / ctx, 4),
           "prefill_tok_s": tm.get("prompt_per_second"),
           "decode_tok_s": tm.get("predicted_per_second")}
    rec["valid"] = (rec["prefill_frac"] >= DEPTH_GATE
                    and (rec["predicted_n"] or 0) >= GEN_FLOOR)
    if not rec["valid"]:
        rec["invalid_reason"] = (f"prefill_frac {rec['prefill_frac']} < {DEPTH_GATE}"
                                 if rec["prefill_frac"] < DEPTH_GATE
                                 else f"generated {rec['predicted_n']} tokens < floor {GEN_FLOOR}")
    return rec


def serve(arm, ctx):
    """Launch one arm at one depth, no-spec. Returns (ok, launch_cmd, detail)."""
    cmd, rc, err = L.launch(ARMS[arm], ctx, kv="q4_0", spec="none", sm="layer",
                            ts=TS, ctxcp=32, extra="")
    if rc != 0:
        L.save_and_kill(f"s11-{arm}-c{ctx}-launchfail")
        return False, cmd, f"launch-rc-{rc}: {err[:200]}"
    ok, secs = L.wait_health(900)
    if not ok:
        L.save_and_kill(f"s11-{arm}-c{ctx}-health")
        slog = f"{L.TIMINGS_DIR}/s11-{arm}-c{ctx}-health.serverlog"
        cls = L.classify_failure(open(slog).read() if os.path.exists(slog) else "", "load", err)
        return False, cmd, f"load-failed after {secs}s ({cls})"
    n = L.props_nctx()
    if n != ctx:
        L.save_and_kill(f"s11-{arm}-c{ctx}-nctx")
        return False, cmd, f"n_ctx mismatch: reported {n}, requested {ctx}"
    return True, cmd, "ok"


def first_divergence(a, b):
    """Index of the first differing character; None if identical."""
    if a == b:
        return None
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return i
    return min(len(a), len(b))


def load_out(path):
    return json.load(open(path)) if os.path.exists(path) else {
        "experiment": "s11-divdepth", "source": "e12-s11", "run_ids": ["s11"],
        "question": "does quantization divergence grow with context depth?",
        "replaces": ("S10's KL-divergence design, infeasible here: llama-perplexity holds a "
                     "chunk's logits resident and this host tops out at n_ctx 8,192 "
                     "(16,384 -> 305 MiB available and zero bytes written in 13 min; "
                     "65,536 -> std::bad_alloc)"),
        "reference": REFERENCE, "arms": list(ARMS), "depths": DEPTHS, "ts": TS,
        "kv": "q4_0", "spec": "NONE — mandatory",
        "spec_rationale": ("PN-23/PN-26: MTP alters ~20 % of completions for reasons unrelated to "
                           "the quant and would swamp the effect being measured"),
        "determinism_basis": ("PN-26 — no-spec greedy generation on this engine is byte-"
                              "reproducible, so any text difference between arms is attributable "
                              "to the quantization"),
        "metric": ("index of first differing character vs the reference arm on the identical "
                   "prompt; later divergence = closer agreement. Exact-match would be binary "
                   "because greedy decoding is a trajectory: after the first differing token the "
                   "sequences are on different paths"),
        "gates": {"prefill_frac_min": DEPTH_GATE, "generated_tokens_min": GEN_FLOOR},
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cells": [], "self_consistency": None}


def save(out, path):
    json.dump(out, open(path, "w"), indent=1)


def phase_pilot(path):
    """Hardest cell first: the reference arm at the deepest rung, plus the self-consistency
    control that the whole experiment's interpretability depends on."""
    out = load_out(path)
    ctx = DEPTHS[-1]
    log(f"PILOT: hardest cell — {REFERENCE} @ {ctx} no-spec, -ts {TS}")
    log("  VRAM estimate says RISK (16,426 MiB/GPU vs 15,650); E11a measured this arm at 245,760 "
        "no-spec. Measuring.")
    ok, cmd, detail = serve(REFERENCE, ctx)
    if not ok:
        out["pilot"] = {"ok": False, "stage": "load", "detail": detail, "launch_cmd": cmd,
                        "verdict": f"FAIL — {REFERENCE} cannot serve {ctx}. Drop the deepest rung "
                                   f"to 163,840 and re-pilot."}
        save(out, path); log("PILOT FAIL: " + detail); return False

    pad = build_pads(ctx)[0]
    r1 = generate(REFERENCE, ctx, pad, "pilot-run1")
    r2 = generate(REFERENCE, ctx, pad, "pilot-run2")     # the self-consistency control
    L.save_and_kill(f"s11-pilot-{REFERENCE}-c{ctx}")

    same = r1.get("ok") and r2.get("ok") and r1["text"] == r2["text"]
    out["self_consistency"] = {
        "arm": REFERENCE, "ctx": ctx, "identical": bool(same),
        "run1": {k: r1.get(k) for k in ("predicted_n", "prefill_frac", "chars", "valid")},
        "run2": {k: r2.get(k) for k in ("predicted_n", "prefill_frac", "chars", "valid")},
        "why": ("if the reference arm cannot reproduce itself at this depth, every divergence "
                "number below is noise and the experiment is void")}
    good = bool(same and r1.get("valid") and r2.get("valid"))
    out["pilot"] = {"ok": good, "launch_cmd": cmd,
                    "verdict": ("PASS — serves the deepest rung, generates past the floor, and "
                                "reproduces itself byte-exactly"
                                if good else
                                f"FAIL — identical={same} valid1={r1.get('valid')} "
                                f"valid2={r2.get('valid')} "
                                f"({r1.get('invalid_reason') or r2.get('invalid_reason') or ''})")}
    save(out, path)
    log(f"  run1: {r1.get('predicted_n')} tok, prefill_frac {r1.get('prefill_frac')}")
    log(f"  run2: {r2.get('predicted_n')} tok, prefill_frac {r2.get('prefill_frac')}")
    log("PILOT: " + out["pilot"]["verdict"])
    return good


def phase_depth(path, ctx):
    """One depth slice: every arm on the same N pads, compared to the reference."""
    out = load_out(path)
    pads = build_pads(ctx)
    log(f"=== depth {ctx}: {len(ARMS)} arms x {len(pads)} pads ===")
    texts = {}
    for arm in [REFERENCE] + [a for a in ARMS if a != REFERENCE]:
        ok, cmd, detail = serve(arm, ctx)
        if not ok:
            out["cells"].append({"arm": arm, "ctx": ctx, "ok": False, "detail": detail,
                                 "launch_cmd": cmd})
            save(out, path); log(f"  {arm}: LOAD FAILED — {detail}"); continue
        for i, pad in enumerate(pads):
            r = generate(arm, ctx, pad, f"{arm}-c{ctx}-p{i}")
            r.update({"arm": arm, "ctx": ctx, "pad": i, "launch_cmd": cmd})
            texts.setdefault(arm, {})[i] = r.get("text", "") if r.get("valid") else None
            r.pop("text", None)                       # generations go to a sidecar, not the JSON
            out["cells"].append(r)
            log(f"  {arm} pad{i}: {r.get('predicted_n')} tok  "
                f"frac {r.get('prefill_frac')}  valid={r.get('valid')}")
            save(out, path)
        L.save_and_kill(f"s11-{arm}-c{ctx}")

    # sidecar with the raw generations, so any metric can be recomputed later
    side = f"{OUTD}/s11-gen-c{ctx}.json"
    json.dump({a: {str(i): t for i, t in d.items()} for a, d in texts.items()},
              open(side, "w"), indent=1)

    # divergence against the reference on the identical prompt
    ref = texts.get(REFERENCE, {})
    for arm in ARMS:
        if arm == REFERENCE:
            continue
        idxs = []
        for i in ref:
            a, b = ref.get(i), texts.get(arm, {}).get(i)
            if a is None or b is None:
                continue
            d = first_divergence(a, b)
            idxs.append({"pad": i, "first_div_char": d, "identical": d is None,
                         "ref_chars": len(a), "arm_chars": len(b)})
        fin = [x["first_div_char"] for x in idxs if x["first_div_char"] is not None]
        out.setdefault("divergence", {}).setdefault(str(ctx), {})[arm] = {
            "per_pad": idxs, "n_pads": len(idxs),
            "n_identical": sum(1 for x in idxs if x["identical"]),
            "first_div_char_median": (sorted(fin)[len(fin) // 2] if fin else None),
            "first_div_char_all": sorted(fin)}
        log(f"  DIVERGENCE {arm} @{ctx}: median first-div char "
            f"{out['divergence'][str(ctx)][arm]['first_div_char_median']} "
            f"({out['divergence'][str(ctx)][arm]['n_identical']}/{len(idxs)} identical)")
    save(out, path)
    return sum(1 for c in out["cells"] if c.get("ctx") == ctx and c.get("valid"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True,
                    choices=["pilot"] + [f"d{d}" for d in DEPTHS] + ["summarize"])
    a = ap.parse_args()
    os.makedirs(OUTD, exist_ok=True)
    L.preflight()
    path = f"{OUTD}/s11-divdepth.json"

    if a.phase == "pilot":
        sys.exit(0 if phase_pilot(path) else 2)
    if a.phase.startswith("d"):
        n = phase_depth(path, int(a.phase[1:]))
        log(f"depth {a.phase[1:]}: {n} valid cells")
        sys.exit(0 if n else 2)
    if a.phase == "summarize":
        out = load_out(path)
        dv = out.get("divergence", {})
        log("FIRST-DIVERGENCE CHARACTER INDEX vs " + REFERENCE + " (higher = closer agreement)")
        for arm in [x for x in ARMS if x != REFERENCE]:
            row = {d: (dv.get(d, {}).get(arm, {}) or {}).get("first_div_char_median")
                   for d in sorted(dv, key=int)}
            log(f"  {arm:9s} " + "  ".join(f"c{d}={row[d]}" for d in row))
        out["verdict_note"] = ("read the trend across depths per arm: a FALLING first-divergence "
                               "index means the arm departs from the reference sooner as context "
                               "grows, i.e. quantization damage grows with depth")
        save(out, path)
        sys.exit(0 if dv else 2)


if __name__ == "__main__":
    main()
