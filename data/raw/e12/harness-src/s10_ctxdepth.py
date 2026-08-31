#!/usr/bin/env python3
"""s10_ctxdepth.py — does quantization damage grow with CONTEXT DEPTH?

THE HOLE THIS FILLS
  Every accuracy number this study has produced was measured at n_ctx 2048: the KLD ladder
  (PN-13), the domain hierarchy (PN-14, PN-21), the q4_0-KV verdict (PN-15). The deployment
  configuration runs at 262,144. That is a 128x extrapolation, and PN-15 says so itself:
  "measured ... at n_ctx 2048 -- NOT at the 212K-262K depths where the KV cache actually
  dominates memory and where the effect could differ materially."

WHY IT IS AFFORDABLE
  KLD cost scales with the TOKEN BUDGET, not with context length. Scoring 65,536 tokens at
  -c 2048 gives 32 chunks; scoring the same 65,536 tokens at -c 65536 gives one. Same number
  of per-token observations, same ~11 GB logits file -- each token merely conditioned on 32x
  more context. Only the attention work grows.

DESIGN — budget-matched at 65,536 tokens on every rung, so ONLY context varies
    rung        n_ctx    chunks   tokens    comparable to
    (S3)         2,048       32   65,536    already measured -- this is the anchor
    A           16,384        4   65,536    8x deeper
    B           65,536        1   65,536    32x deeper
  Domain: CODE only. The target workload, and the domain the Track A conclusion rests on.
  Wikitext is skipped to halve the cost; that is a scope choice, not an oversight.
  Arms: Q6_K, Q5_K_XL, Q4_K_XL scored against the Q6_K_XL reference, exactly as in S3.
  KV: q4_0 on BOTH base and arms, exactly as in S2/S3 -- the KV error is then present on both
  sides and largely cancels, so the divergence that remains is quant-attributable.

  Plus the KV axis at rung B: reference arm, f16 base vs q4_0 scoring, which is S4's design
  moved to depth. At 65,536 the KV cache holds 32x more quantized keys and values than S4
  measured over, and whether its error accumulates is the open half of PN-15.

READING THE RESULT
  If mean KLD is flat across rungs, quantization damage is depth-independent and every
  published 2K-context quality table transfers to long-context work unchanged. If it RISES,
  then those tables -- Unsloth's, Fireworks', LocalBench's, all measured near 2K -- understate
  the cost of quantization for long-context work, which is structurally the same finding this
  study already makes about prose-vs-code, in a second dimension.

CAVEAT THAT MUST TRAVEL WITH RUNG B
  Budget-matching forces chunks down as n_ctx rises: 32 chunks at 2,048 but ONE at 65,536.
  The deep rung's 65,536 observations therefore come from a single contiguous passage rather
  than 32 scattered ones, so they are more correlated and less representative of the corpus,
  even though the token count is identical. The tool's Gaussian interval does not know this.
  Any rung-to-rung difference smaller than the S3 arm-to-arm separation should be treated as
  suggestive, not established.
"""
import argparse, json, os, subprocess, sys, time

sys.path.insert(0, "/srv/bench/e12/experiments")
import ssa_kld as K          # reuse the PROVEN runner and the fixed +/- parser

E12  = "/srv/bench/e12"
OUTD = f"{E12}/s10"
SSA  = f"{E12}/ssa"          # run_perplexity mounts this as /ssa for the .kld files
DOMAIN = "code"

# Rungs: (tag, n_ctx, chunks). Budget = n_ctx * chunks = 65,536 on every rung.
RUNGS = {"A": (16384, 4), "B": (65536, 1)}

# At n_ctx 2048 the SSA runs used the DEFAULT split, because VRAM pressure was negligible and
# a per-arm ratio would have put an uncontrolled variable into an accuracy comparison. At
# 65,536 that is no longer true: the KV cache is 32x larger and the default split is the one
# that OOMed Q5_K_XL at 262,144 in Wave 1. A SINGLE FIXED ratio is used for every arm at the
# deep rungs -- still controlled, because it does not vary with the arm, but no longer relying
# on the default placement being survivable.
DEEP_TS = "56,44"
TS_FROM_NCTX = 16384         # apply the fixed ratio at or above this n_ctx


def log(*a):
    print(f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}]", *a, flush=True)


def extra_for(n_ctx):
    return ["-ts", DEEP_TS] if n_ctx >= TS_FROM_NCTX else None


def kld_of(cell):
    return (cell.get("metrics") or {}).get("mean_kld")


def free_gb(path="/"):
    st = os.statvfs(path)
    return round(st.f_bavail * st.f_frsize / 2**30, 1)


def drop(base_file):
    """The .kld logits files are ~11 GB each. Delete as soon as the rung that needs them is
    done -- the SSA runs filled `/` to 87 % and had to reclaim 50 GB afterwards."""
    p = f"{SSA}/{base_file}"
    if os.path.exists(p):
        gb = round(os.path.getsize(p) / 2**30, 1)
        os.remove(p)
        log(f"    dropped {base_file} ({gb} GB), free now {free_gb()} GB")


def run_rung(rung, out, kv="q4_0", arms=None, base_file=None, reuse_base=False):
    """Record the reference logits at this rung, then score each arm against them."""
    n_ctx, chunks = RUNGS[rung]
    arms = arms or [a for a in K.ARMS if a != K.REFERENCE]
    base_file = base_file or f"s10-{rung}-{DOMAIN}-{kv}.kld"
    extra = extra_for(n_ctx)
    log(f"=== rung {rung}: n_ctx={n_ctx} chunks={chunks} tokens={n_ctx*chunks} "
        f"kv={kv} ts={extra} ===")

    if not reuse_base:
        if free_gb() < 25:
            log(f"    ABORT rung {rung}: only {free_gb()} GB free, need ~11 GB for logits")
            return False
        c = K.run_perplexity(K.REFERENCE, DOMAIN, n_ctx, chunks, kv,
                             base_file=base_file, mode="base", extra=extra, tag=f"s10{rung}")
        c["rung"], c["tokens_budget"] = rung, n_ctx * chunks
        out["cells"].append(c)
        json.dump(out, open(f"{OUTD}/s10-ctxdepth.json", "w"), indent=1)
        log(f"    base rc={c['rc']} ok={c['ok']} {c['seconds']}s")
        if not c["ok"]:
            log(f"    rung {rung} ABORTED: reference logits failed")
            return False

    for arm in arms:
        c = K.run_perplexity(arm, DOMAIN, n_ctx, chunks, kv,
                             base_file=base_file, mode="kld", extra=extra, tag=f"s10{rung}")
        c["rung"], c["tokens_budget"] = rung, n_ctx * chunks
        out["cells"].append(c)
        json.dump(out, open(f"{OUTD}/s10-ctxdepth.json", "w"), indent=1)
        log(f"    {arm}: ok={c['ok']} mean_kld={kld_of(c)} top1={(c.get('metrics') or {}).get('top1_agree')} "
            f"({c['seconds']}s)")
    return True


def summarize(out):
    """Assemble the depth curve, and pull S3's n_ctx-2048 anchor in from the SSA artifact."""
    curve = {}
    for c in out["cells"]:
        if c.get("mode") != "kld" or not c.get("ok"):
            continue
        curve.setdefault(str(c["n_ctx"]), {})[c["arm"]] = {
            "mean_kld": kld_of(c), "top1_agree": (c.get("metrics") or {}).get("top1_agree"),
            "chunks": c["chunks"], "tokens": c["tokens_budget"], "kv": c["kv"]}
    # the 2,048 anchor, read from S3 rather than re-run
    try:
        s3 = json.load(open(f"{SSA}/ssa-results-parsed.json"))
        cells = s3.get("cells", s3) if isinstance(s3, dict) else s3
        anchor = {}
        for c in cells:
            if (c.get("domain") == "code" and c.get("mode") == "kld"
                    and c.get("n_ctx") == 2048 and "e2" not in c.get("label", "")):
                anchor[c["arm"]] = {"mean_kld": (c.get("metrics") or {}).get("mean_kld"),
                                    "top1_agree": (c.get("metrics") or {}).get("top1_agree"),
                                    "chunks": c.get("chunks"), "tokens": 65536,
                                    "kv": c.get("kv"), "source": "SSA S3"}
        if anchor:
            curve["2048"] = anchor
    except Exception as e:
        out["anchor_error"] = str(e)[:200]
    out["depth_curve"] = dict(sorted(curve.items(), key=lambda kv: int(kv[0])))

    # direction, per arm, 2048 -> deepest rung that produced a number
    trend = {}
    depths = sorted((int(d) for d in curve), key=int)
    if len(depths) >= 2:
        lo, hi = str(depths[0]), str(depths[-1])
        for arm in curve[hi]:
            a, b = curve.get(lo, {}).get(arm, {}).get("mean_kld"), curve[hi][arm]["mean_kld"]
            if a and b:
                trend[arm] = {"n_ctx_lo": lo, "n_ctx_hi": hi, "kld_lo": a, "kld_hi": b,
                              "ratio": round(b / a, 3), "delta": round(b - a, 6)}
        out["depth_trend"] = trend
        rs = [t["ratio"] for t in trend.values()]
        if rs:
            out["verdict"] = (
                f"mean KLD changes by {min(rs):.2f}x-{max(rs):.2f}x from n_ctx {lo} to {hi}. "
                + ("DAMAGE GROWS WITH DEPTH: published 2K-context quantization tables understate "
                   "the cost for long-context work." if min(rs) > 1.15 else
                   "DAMAGE SHRINKS WITH DEPTH." if max(rs) < 0.87 else
                   "DEPTH-INDEPENDENT within this resolution: the 2K measurement transfers."))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True, choices=["pilot", "rungA", "rungB", "kv", "summarize"])
    a = ap.parse_args()
    os.makedirs(OUTD, exist_ok=True)
    if K.gpu_busy():
        log("REFUSING: another GPU experiment is running"); sys.exit(3)

    path = f"{OUTD}/s10-ctxdepth.json"
    out = (json.load(open(path)) if os.path.exists(path) else {
        "experiment": "s10-ctxdepth", "source": "e12-s10", "run_ids": ["s10"],
        "question": "does quantization damage grow with context depth?",
        "closes": "PN-15's stated caveat (measured at n_ctx 2048 only); the largest gap in the accuracy program",
        "domain": DOMAIN, "reference": K.REFERENCE, "image_id": K.image_id(),
        "kv_note": ("q4_0 on BOTH base and arms, as in S2/S3: the KV error is present on both "
                    "sides and largely cancels, so the divergence is quant-attributable"),
        "split_note": (f"default split at n_ctx < {TS_FROM_NCTX}; a SINGLE FIXED -ts {DEEP_TS} "
                       "at and above it, identical for every arm, so it is controlled rather "
                       "than an uncontrolled per-arm variable"),
        "budget_note": "every rung scores exactly 65,536 tokens; only n_ctx and chunks vary",
        "chunk_caveat": ("budget-matching drives chunks down as n_ctx rises (32 at 2,048, ONE at "
                         "65,536), so the deep rung's observations come from a single contiguous "
                         "passage and are more correlated than the shallow rung's. The tool's "
                         "Gaussian interval does not account for this."),
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "cells": []})

    if a.phase == "pilot":
        # Hard gate AND real work: this records rung B's reference logits and scores one arm
        # against them. If --kl-divergence cannot run at -c 65536 on this stack, or the
        # reference does not fit, that is known in ~30 min instead of hours. On success the
        # base file is REUSED by rungB, so the pilot costs nothing extra.
        log("PILOT: rung B (n_ctx 65,536, 1 chunk) — reference logits + one arm")
        ok = run_rung("B", out, arms=["Q4_K_XL"])
        cells = [c for c in out["cells"] if c.get("mode") == "kld" and c.get("rung") == "B"]
        good = ok and cells and cells[-1]["ok"] and kld_of(cells[-1]) is not None
        out["pilot_verdict"] = ("PASS — --kl-divergence runs at n_ctx 65,536 and the fields populate"
                                if good else "FAIL — see the serverlog; do not run the battery")
        json.dump(out, open(path, "w"), indent=1)
        log(f"PILOT: {out['pilot_verdict']}")
        sys.exit(0 if good else 2)

    if a.phase == "rungA":
        ok = run_rung("A", out)
        drop(f"s10-A-{DOMAIN}-q4_0.kld")
        json.dump(summarize(out), open(path, "w"), indent=1)
        sys.exit(0 if ok else 2)

    if a.phase == "rungB":
        # the pilot already recorded the base and scored Q4_K_XL -> only the other two remain
        done = {c["arm"] for c in out["cells"] if c.get("rung") == "B" and c.get("mode") == "kld"}
        rest = [x for x in K.ARMS if x != K.REFERENCE and x not in done]
        base = f"s10-B-{DOMAIN}-q4_0.kld"
        if not os.path.exists(f"{SSA}/{base}"):
            log("rung B base logits are gone — re-recording"); ok = run_rung("B", out, arms=rest)
        else:
            log(f"reusing the pilot's base logits; remaining arms: {rest}")
            ok = run_rung("B", out, arms=rest, base_file=base, reuse_base=True) if rest else True
        json.dump(summarize(out), open(path, "w"), indent=1)
        sys.exit(0 if ok else 2)

    if a.phase == "kv":
        # S4's design moved to depth: same model, f16 logits vs q4_0 scoring, so the only
        # variable is the KV dtype. Closes the open half of PN-15.
        n_ctx, chunks = RUNGS["B"]
        base = f"s10-B-{DOMAIN}-f16.kld"
        extra = extra_for(n_ctx)
        log(f"=== KV axis at n_ctx {n_ctx}: f16 base vs q4_0 scoring, reference arm ===")
        if free_gb() < 25:
            log(f"ABORT: only {free_gb()} GB free"); sys.exit(2)
        c1 = K.run_perplexity(K.REFERENCE, DOMAIN, n_ctx, chunks, "f16",
                              base_file=base, mode="base", extra=extra, tag="s10kv")
        c1["rung"], c1["tokens_budget"] = "B-kv", n_ctx * chunks
        out["cells"].append(c1); json.dump(out, open(path, "w"), indent=1)
        if not c1["ok"]:
            log("KV axis ABORTED: f16 reference logits failed (likely VRAM at this depth)")
            json.dump(summarize(out), open(path, "w"), indent=1); sys.exit(2)
        c2 = K.run_perplexity(K.REFERENCE, DOMAIN, n_ctx, chunks, "q4_0",
                              base_file=base, mode="kld", extra=extra, tag="s10kv")
        c2["rung"], c2["tokens_budget"] = "B-kv", n_ctx * chunks
        out["cells"].append(c2)
        out["kv_at_depth"] = {
            "n_ctx": n_ctx, "tokens": n_ctx * chunks, "mean_kld": kld_of(c2),
            "top1_agree": (c2.get("metrics") or {}).get("top1_agree"),
            "compare_to_s4_at_2048": 0.002955,
            "note": ("S4 measured 0.002955 +/- 0.000127 at n_ctx 2048. If this is materially "
                     "larger, q4_0 KV error ACCUMULATES with depth and every long-context "
                     "configuration in this study inherits more error than PN-15 states.")}
        if kld_of(c2):
            out["kv_at_depth"]["ratio_vs_2048"] = round(kld_of(c2) / 0.002955, 3)
        drop(base)
        json.dump(summarize(out), open(path, "w"), indent=1)
        log("KV AT DEPTH: " + json.dumps(out["kv_at_depth"]))
        sys.exit(0 if c2["ok"] else 2)

    if a.phase == "summarize":
        out = summarize(out)
        out["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        json.dump(out, open(path, "w"), indent=1)
        log("DEPTH CURVE: " + json.dumps(out.get("depth_curve", {})))
        log("TREND: " + json.dumps(out.get("depth_trend", {})))
        log("VERDICT: " + str(out.get("verdict")))
        sys.exit(0 if out.get("depth_curve") else 2)


if __name__ == "__main__":
    main()
