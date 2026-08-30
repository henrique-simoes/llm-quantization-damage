#!/usr/bin/env python3
"""summarize_wave1.py — turn the Wave-1 tsweep cells into the answer they were run for.

Wave 1 asks ONE question: after a proper -ts rebalance sweep (G13: keep the FASTEST ratio
that loads, not the first), what context ceiling and what decode-at-depth does each quant
reach on a surviving image — and does rebalancing lift the highest-fidelity quant into a
usable long-context window (G21)?

It answers Track A priorities (2) usable context and (3) tok/s ONLY. Priority (1) accuracy is
a quant property that this wave does not measure; the summary says so explicitly rather than
letting a speed table imply a winner.

Usage: summarize_wave1.py [--out /srv/bench/e12/wave1-summary.json] [--md]
"""
import argparse
import glob
import json
import os
import sys

E12 = "/srv/bench/e12"

# Prior measurements, each with the artifact that carries it. Default-split unless stated.
BASELINE = {
    "Q4_K_XL": {"default_split_ceiling": 196608, "source": "E1b /srv/bench/ctx-ceilings.json"},
    "Q5_K_XL": {"default_split_ceiling": 196608,
                "source": "E11a (supersedes E1's 163,840, which was a VRAM-gate artifact)"},
    "Q6_K":    {"default_split_ceiling": 196608, "rebalanced_prior": 262144,
                "prior_decode_tok_s": 13.85, "prior_ts": "58,42",
                "source": "E11a/E11c (CLAUDE.md E11 EXECUTION LOG)"},
    "Q6_K_XL": {"default_split_ceiling": 131072,
                "source": "E1 /srv/bench/q6-ceiling.json (MTP n2, q4_0, layer)"},
}
NATIVE_CTX = 262144


def load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def winner_cell(d):
    """The cell the sweep selected, resolved back to the full record."""
    best = d.get("best") or d.get("best_at_ceiling")
    if not best:
        return None
    key = best.get("key")
    for c in d.get("cells", []):
        if c.get("key") == key:
            return c
    return best if "vram_peak_mib" in best else None


def depth_ok(cells):
    """Every ok cell must have met the >=0.90 window-depth gate (enforced 2026-08-30)."""
    bad = [c["key"] for c in cells
           if c.get("ok") and (c.get("prefill_frac") or 0) < 0.90]
    return (not bad), bad


def summarize_quant(q, d):
    cells = d.get("cells", [])
    oks = [c for c in cells if c.get("ok")]
    ceiling = (d.get("ceiling") or {}).get("ctx")
    best = d.get("best") or {}
    wc = winner_cell(d) or {}
    gate_ok, gate_bad = depth_ok(cells)
    base = BASELINE.get(q, {})

    # ratio table at the ceiling rung, rep 1 — the like-for-like ratio comparison
    rung = d.get("best_speed") or ceiling
    ratio_rows = []
    for c in cells:
        if c.get("ctx_requested") != rung or c.get("rep", 1) != 1 or c.get("tag"):
            continue
        ratio_rows.append({
            "ts": c.get("ts") or "default", "ok": c.get("ok"),
            "decode_tok_s": c.get("decode_tok_s"), "prefill_tok_s": c.get("prefill_tok_s"),
            "vram_peak_mib": c.get("vram_peak_mib"), "imbalance_mib": c.get("imbalance_mib"),
            "prefill_frac": c.get("prefill_frac"), "mtp_acceptance": c.get("mtp_acceptance"),
            "failure_mode": c.get("failure_mode"),
        })
    ratio_rows.sort(key=lambda r: (-(r["decode_tok_s"] or 0), r["ts"]))

    dflt = next((r for r in ratio_rows if r["ts"] == "default"), None)
    gain = None
    if dflt and best.get("decode_tok_s") and dflt.get("decode_tok_s"):
        gain = round((best["decode_tok_s"] - dflt["decode_tok_s"]) / dflt["decode_tok_s"], 4)

    return {
        "quant": q,
        "model": d.get("model"),
        "mode": d.get("mode"),
        "complete": bool(d.get("ceiling")),
        "cells_total": len(cells), "cells_ok": len(oks),
        "rebalanced_ceiling_ctx": ceiling,
        "reaches_native_262144": ceiling == NATIVE_CTX,
        "ceiling_note": (d.get("ceiling") or {}).get("note"),
        "default_split_ceiling": base.get("default_split_ceiling"),
        "ceiling_gain_tokens": (ceiling - base["default_split_ceiling"])
                                if ceiling and base.get("default_split_ceiling") else None,
        "best_ts": best.get("ts"),
        "best_decode_tok_s": best.get("decode_tok_s"),
        "best_decode_tok_s_median3": best.get("decode_tok_s_median3"),
        "selected_on": best.get("selected_on", "rep1 (pre-2026-08-30 artifact)"),
        "decode_gain_vs_default_split": gain,
        "best_prefill_tok_s": wc.get("prefill_tok_s"),
        "best_vram_peak_mib": wc.get("vram_peak_mib"),
        "best_imbalance_mib": wc.get("imbalance_mib"),
        "best_mtp_acceptance": wc.get("mtp_acceptance"),
        "best_prefill_frac": wc.get("prefill_frac"),
        "depth_gate_ok": gate_ok, "depth_gate_violations": gate_bad,
        "d2": d.get("d2"), "d3": d.get("d3"), "g21": d.get("g21"),
        "ratio_table_at_ceiling": ratio_rows,
        "image_id": (d.get("env") or {}).get("image", {}).get("image_id"),
        "prior": base,
    }


def build(out_path):
    quants, missing = {}, []
    for q in ("Q4_K_XL", "Q5_K_XL", "Q6_K", "Q6_K_XL"):
        d = load(f"{E12}/tsweep-v2-{q}.json")
        if d is None:
            missing.append(q)
            continue
        quants[q] = summarize_quant(q, d)

    done = [q for q, s in quants.items() if s["complete"]]
    at_native = [q for q, s in quants.items() if s["reaches_native_262144"]]
    # fastest at the full native window, among quants that actually reach it
    ranked = sorted(
        [s for s in quants.values() if s["reaches_native_262144"] and s["best_decode_tok_s"]],
        key=lambda s: -(s["best_decode_tok_s_median3"] or s["best_decode_tok_s"]))

    pads = load(f"{E12}/pads-manifest.json") or {}
    art = {
        "artifact": "e12-wave1-summary",
        "source": "e12-wave1",
        "run_ids": [f"tsweep-v2-{q}" for q in quants],
        "question": "After a full -ts rebalance sweep, what context ceiling and what decode "
                    "rate at ~95 % window depth does each quant reach on a surviving image?",
        "answers_track_a_priorities": ["(2) usable context", "(3) tok/s"],
        "does_not_answer": ["(1) accuracy — a quant property this wave does not measure; "
                            "no NLL/KV-fidelity/NIAH data is produced here, so this summary "
                            "MUST NOT be read as a Track A config selection"],
        "complete_quants": done,
        "incomplete_or_missing": missing + [q for q, s in quants.items() if not s["complete"]],
        "reach_native_262144": at_native,
        "fastest_at_native_window": (
            {"quant": ranked[0]["quant"], "ts": ranked[0]["best_ts"],
             "decode_tok_s": ranked[0]["best_decode_tok_s_median3"]
                             or ranked[0]["best_decode_tok_s"]}
            if ranked else None),
        "context_speed_frontier": [
            {"quant": s["quant"], "ceiling": s["rebalanced_ceiling_ctx"],
             "ts": s["best_ts"],
             "decode_tok_s": s["best_decode_tok_s_median3"] or s["best_decode_tok_s"],
             "prefill_tok_s": s["best_prefill_tok_s"],
             "vram_peak_mib": s["best_vram_peak_mib"]}
            for s in sorted(quants.values(),
                            key=lambda s: -(s["rebalanced_ceiling_ctx"] or 0))],
        "caveats": [
            "SAMPLING: every request carries the DEC-2 official non-thinking block "
            "(temp 0.7 / top_p 0.80 / top_k 20 / presence 1.5), NOT greedy. Decode and "
            "acceptance rows are therefore NOT comparable to the e11 / ctx=32768 tables, "
            "which were measured at temperature 0.",
            "DEPTH: decode is measured after a real prefill to >=0.90 of the window "
            "(actual ~0.945). Published 'ctx=32768' speed tables decode into a nearly EMPTY "
            "KV cache and are 3-5x faster; the two must never share a table.",
            "PAD DEFECT (2026-08-30): the first Q4_K_XL pass prefilled only 0.797 of the "
            "window because the pad builder's fixed-bracket bisection returned short. Those "
            "cells are quarantined under e12/quarantine/ and were re-run; the >=0.90 gate is "
            "now enforced in code and covered by regression tests.",
            "RATIO CHOICE IS NOT MONOTONE-SAFE: a ratio that loads at one ctx may fail at "
            "another, and the winner differs per quant. Re-sweep -ts on any change of quant, "
            "KV dtype or spec setting.",
            "ALL CELLS: -sm layer, q4_0 KV, MTP n=2, -fit off, -ctxcp 4, -np 1 on "
            "llamacpp-mtp:latest. -sm tensor is dead on both surviving images (E6).",
        ],
        "pads": {"all_ok": pads.get("all_ok"), "rule": pads.get("rule"),
                 "n": len(pads.get("pads", []))},
        "quants": quants,
    }
    with open(out_path, "w") as f:
        json.dump(art, f, indent=1)
    return art


def as_md(a):
    L = []
    L.append("# Wave 1 — tensor-split rebalance: context ceilings and decode at depth\n")
    L.append(f"**Question:** {a['question']}\n")
    L.append("**Answers Track A priorities:** " + ", ".join(a["answers_track_a_priorities"]))
    L.append("**Does NOT answer:** " + a["does_not_answer"][0] + "\n")
    L.append("| quant | rebalanced ceiling | default-split ceiling | gain | best -ts | "
             "decode tok/s @depth | prefill tok/s | VRAM peak GPU0/GPU1 | imbalance |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for s in sorted(a["quants"].values(), key=lambda s: -(s["rebalanced_ceiling_ctx"] or 0)):
        v = s["best_vram_peak_mib"] or []
        dec = s["best_decode_tok_s_median3"] or s["best_decode_tok_s"]
        L.append("| {q} | {c} | {d} | {g} | {t} | {dec} | {p} | {v} | {i} |".format(
            q=s["quant"],
            c=s["rebalanced_ceiling_ctx"] or "—",
            d=s["default_split_ceiling"] or "—",
            g=(f"+{s['ceiling_gain_tokens']:,}" if s["ceiling_gain_tokens"] else "—"),
            t=s["best_ts"] or "—",
            dec=(f"{dec:.2f}" if dec else "—"),
            p=(f"{s['best_prefill_tok_s']:.0f}" if s["best_prefill_tok_s"] else "—"),
            v=("/".join(str(x) for x in v) if v else "—"),
            i=s["best_imbalance_mib"] if s["best_imbalance_mib"] is not None else "—"))
    L.append("")
    if a["fastest_at_native_window"]:
        f = a["fastest_at_native_window"]
        L.append(f"**Fastest at the full native 262,144 window:** {f['quant']} "
                 f"@ `-ts {f['ts']}` — {f['decode_tok_s']:.2f} tok/s\n")
    if a["incomplete_or_missing"]:
        L.append(f"**Incomplete:** {', '.join(a['incomplete_or_missing'])}\n")
    L.append("## Caveats")
    for c in a["caveats"]:
        L.append(f"- {c}")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=f"{E12}/wave1-summary.json")
    ap.add_argument("--md", action="store_true")
    args = ap.parse_args()
    a = build(args.out)
    if args.md:
        md = as_md(a)
        print(md)
        with open(args.out.replace(".json", ".md"), "w") as f:
            f.write(md + "\n")
    else:
        print(json.dumps({k: v for k, v in a.items() if k != "quants"}, indent=1))
    print(f"\n-> {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
