#!/usr/bin/env python3
"""
extract.py — regenerate every figure data file from the committed artifacts.

Runs offline, uses only the Python standard library, is idempotent (same inputs ->
byte-identical outputs), and fails loudly if any artifact it needs is missing.

    python3 manuscript/figures/extract.py            # write manuscript/figures/data/*.csv
    python3 manuscript/figures/extract.py --check    # verify existing files are up to date
    python3 manuscript/figures/extract.py --list     # list figure ids and their sources

Every number written here is read from a file under data/raw/ or data/archive/, or is
computed in this script from those files by a named estimator. Nothing is transcribed
from prose. Where a paper note's published value differs from what the artifact yields,
this script emits the artifact-derived value and the discrepancy is recorded in
FIGURE-PROGRAMME.md under the figure's honesty constraint.

Provenance classes used in the `evidence` columns:
    measured    — produced by a run on this host, artifact committed in this repository
    recomputed  — derived here from committed per-item records (zero GPU cost)
    cited       — external published value, not measured here
    modelled    — derived from a model (GPU telemetry + RAPL + platform allowance)
    historical  — measured before 2026-08-29; irreproducible-on-current-images (PN-57)
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import statistics
import sys
from collections import defaultdict

# --------------------------------------------------------------------------------------
# paths
# --------------------------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir))
OUT = os.path.join(HERE, "data")

RAW = os.path.join(REPO, "data", "raw", "e12")
ARCHIVE = os.path.join(REPO, "data", "archive")

A = {
    "ssa_parsed": f"{RAW}/ssa/ssa-results-parsed.json",
    "ssa_tables": f"{RAW}/ssa/ssa-kld-tables.json",
    "ssa_s5": f"{RAW}/ssa/ssa-s5-results.json",
    "ssa_s7": f"{RAW}/ssa/ssa-s7-results.json",
    "ssa_s7_paired": f"{RAW}/ssa/ssa-s7-paired.json",
    "s8_humaneval": f"{RAW}/s8/s8-humaneval.json",
    "s8_scores_reparsed": f"{RAW}/s8/s8-scores-reparsed.json",
    "s8_atdepth": f"{RAW}/s8/s8-atdepth.json",
    "s8_nospec": f"{RAW}/s8/s8-nospec.jsonl",
    "s8_mtp2": f"{RAW}/s8/s8-mtp2.jsonl",
    "s8_mtp4": f"{RAW}/s8/s8-mtp4.jsonl",
    "s9_scores": f"{RAW}/s9/s9-scores.json",
    "s9_s6": f"{RAW}/s9/s9-s6.json",
    "s9_determinism": f"{RAW}/s9/s9-determinism.json",
    "s9_dflash": f"{RAW}/s9/s9-dflash.json",
    "s9_dflash_jsonl": f"{RAW}/s9/s9-dflash4-he.jsonl",
    "s9_nospec_r2": f"{RAW}/s9/s9-nospec-r2.jsonl",
    "s9_mtp2_r2": f"{RAW}/s9/s9-mtp2-r2.jsonl",
    "s9d": f"{RAW}/s9/s9d-depthsweep.json",
    "s9e": f"{RAW}/s9/s9e-n262k.json",
    "s10": f"{RAW}/s10/s10-ctxdepth.json",
    "s11": f"{RAW}/s11/s11-divdepth.json",
    "s11_gen": f"{RAW}/s11/s11-gen-c8192.json",
    "ruler": f"{RAW}/ruler/s12-ruler.json",
    "tsweep_q4": f"{RAW}/tsweep-v2-Q4_K_XL.json",
    "tsweep_q5": f"{RAW}/tsweep-v2-Q5_K_XL.json",
    "tsweep_q6k": f"{RAW}/tsweep-v2-Q6_K.json",
    "tsweep_q6kxl": f"{RAW}/tsweep-v2-Q6_K_XL.json",
    "env": f"{RAW}/env-manifest.json",
    "progress": f"{RAW}/progress.json",
    "ledger": f"{ARCHIVE}/ledger-data.json",
    "champion": f"{ARCHIVE}/champion-timings.json",
    "specspeed": f"{ARCHIVE}/spec-speed-metrics.jsonl",
}

RULER_PREDS = [
    ("Q6_K_XL", "niah", 8192), ("Q4_K_XL", "niah", 8192),
    ("Q6_K_XL", "niah", 32768), ("Q4_K_XL", "niah", 32768),
    ("Q6_K_XL", "niah", 131072), ("Q4_K_XL", "niah", 131072),
    ("Q6_K_XL", "mkniah", 131072), ("Q4_K_XL", "mkniah", 131072),
    ("Q6_K_XL", "mk100", 131072), ("Q4_K_XL", "mk100", 131072),
    ("Q6_K_XL", "mkmock", 8192), ("Q4_K_XL", "mkmock", 8192),
    ("Q6_K_XL", "variable_tracking", 8192), ("Q4_K_XL", "variable_tracking", 8192),
]
for _arm, _task, _len in RULER_PREDS:
    A[f"preds:{_arm}:{_task}:{_len}"] = f"{RAW}/ruler/s12-preds-{_arm}-{_task}-c{_len}.json"


class MissingArtifact(SystemExit):
    pass


def require(key: str) -> str:
    path = A[key]
    if not os.path.exists(path):
        raise MissingArtifact(
            f"FATAL: required artifact missing: {path}\n"
            f"  (key '{key}'). This script refuses to emit a figure data file it cannot source.\n"
            f"  Recover it with tools/sync-multivac.sh artifact <remote> <local>, or fix A[] in extract.py."
        )
    return path


def load_json(key: str):
    with open(require(key), "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_jsonl_solutions(key: str) -> dict[str, str]:
    out: dict[str, str] = {}
    with open(require(key), "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            out[rec["task_id"]] = rec.get("solution", "")
    return out


# --------------------------------------------------------------------------------------
# statistics helpers (each names its estimator; see TABLES.md)
# --------------------------------------------------------------------------------------

def wilson(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion, in percent."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d
    return (round(100 * max(0.0, centre - half), 2), round(100 * min(1.0, centre + half), 2))


def mcnemar_exact_two_sided(b: int, c: int) -> float:
    """Exact conditional (binomial) two-sided McNemar p-value."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def min_attainable_p(discordant: int) -> float:
    """Smallest two-sided exact McNemar p obtainable at this discordant count (split d/0)."""
    if discordant == 0:
        return 1.0
    return min(1.0, 2 ** (1 - discordant))


def paired_diff_ci(b: int, c: int, n: int) -> tuple[float, float, float]:
    """Paired difference in proportions d=(b-c)/n with the Wald 95 % interval, in points.

    b = successes for arm B only, c = successes for arm A only (see caller for orientation).
    This is the estimator PN-40 prescribes in place of a vacuous McNemar p-value.
    """
    d = (b - c) / n
    var = (b + c - (b - c) ** 2 / n) / (n * n)
    se = math.sqrt(max(var, 0.0))
    return (round(100 * d, 2), round(100 * (d - 1.959963984540054 * se), 2),
            round(100 * (d + 1.959963984540054 * se), 2))


def ols(xs: list[float], ys: list[float]) -> dict:
    """Ordinary least squares y = a + b x, with r, r^2 and residual SD (n-2 denominator)."""
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    b = sxy / sxx
    a = my - b * mx
    r = sxy / math.sqrt(sxx * syy)
    resid = [y - (a + b * x) for x, y in zip(xs, ys)]
    resid_sd = math.sqrt(sum(e * e for e in resid) / (n - 2)) if n > 2 else float("nan")
    raw_sd = math.sqrt(syy / (n - 1)) if n > 1 else float("nan")
    return {"n": n, "a": a, "b": b, "r": r, "r2": r * r, "resid_sd": resid_sd, "raw_sd": raw_sd}


def levenshtein(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
        prev = cur
    return prev[-1]


def first_diff_char(a: str, b: str) -> int:
    i = 0
    while i < min(len(a), len(b)) and a[i] == b[i]:
        i += 1
    return i


def implied_q(acceptance: float, n_draft: int) -> float:
    """Invert acceptance(n) = q(1-q^n) / (n(1-q)) for the per-token draft-match probability q.

    Under stop-at-first-mismatch verification the acceptance RATIO falls with draft depth for
    every q < 1, so q is the quantity that carries information about the drafter (reviewer D,
    §3.3; reproduced here from the artifact's own acceptance values).
    """
    lo, hi = 1e-9, 1 - 1e-12
    f = lambda q: q * (1 - q ** n_draft) / (n_draft * (1 - q))
    for _ in range(200):
        mid = (lo + hi) / 2
        if f(mid) < acceptance:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def ruler_string_match_all(preds: list[str], refs: list[list[str]]) -> float:
    """RULER's own metric, reproduced verbatim: mean over items of the fraction of reference
    strings present (case-insensitive) in the prediction, x100."""
    total = 0.0
    for pred, ref in zip(preds, refs):
        total += sum(1.0 if r.lower() in pred.lower() else 0.0 for r in ref) / len(ref)
    return round(100 * total / len(preds), 2)


# --------------------------------------------------------------------------------------
# csv writer (deterministic formatting -> idempotent output)
# --------------------------------------------------------------------------------------

WRITTEN: list[tuple[str, int, str]] = []
INDEX_ROWS: list[dict] = []


def fmt(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        if v != v:
            return ""
        s = f"{v:.10g}"
        return s
    return str(v)


def emit(fig_id: str, name: str, header: list[str], rows: list[list], sources: list[str],
         pn: str, note: str = "") -> None:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    for r in rows:
        w.writerow([fmt(x) for x in r])
    payload = buf.getvalue()
    path = os.path.join(OUT, name)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    if CHECK_ONLY:
        old = open(path, "r", encoding="utf-8").read() if os.path.exists(path) else None
        status = "OK  " if old == payload else ("DIFF" if old is not None else "MISS")
        if status != "OK  ":
            CHECK_FAILURES.append(name)
        print(f"  [{status}] {name}  ({len(rows)} rows)")
    else:
        os.makedirs(OUT, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(payload)
        print(f"  wrote {name:38s} {len(rows):5d} rows  sha256:{digest}")
    WRITTEN.append((name, len(rows), digest))
    INDEX_ROWS.append({
        "figure_id": fig_id, "data_file": name, "rows": len(rows), "sha256_16": digest,
        "paper_notes": pn, "source_artifacts": " | ".join(sources), "note": note,
    })


# --------------------------------------------------------------------------------------
# shared loaders
# --------------------------------------------------------------------------------------

ARMS_LADDER = ["Q6_K_XL", "Q6_K", "Q5_K_XL", "Q4_K_XL"]      # least -> most quantized
ARMS_QUANT = ["Q6_K", "Q5_K_XL", "Q4_K_XL"]                   # the three measured against the reference
DOMAINS = [("wikitext2", "prose"), ("code", "code"), ("humaneval", "task prompts")]

SSA_PROTOCOL = "SSA divergence (llama-perplexity --kl-divergence), n_ctx 2048, q4_0 KV, seed 20260830"


def kld_cells() -> dict[str, dict]:
    return {c["label"]: c for c in load_json("ssa_tables")["cells"]}


def tsweep_cells() -> list[dict]:
    out = []
    for key in ("tsweep_q4", "tsweep_q5", "tsweep_q6k", "tsweep_q6kxl"):
        d = load_json(key)
        for c in d["cells"]:
            rec = dict(c)
            rec["arm"] = d["quant"]
            rec["ts_label"] = c["ts"] or "default"
            out.append(rec)
    return out


def ruler_preds(arm: str, task: str, length: int):
    d = load_json(f"preds:{arm}:{task}:{length}")
    return d["preds"], d["refs"]


def ruler_item_scores(preds, refs) -> list[float]:
    return [sum(1.0 if r.lower() in p.lower() else 0.0 for r in ref) / len(ref)
            for p, ref in zip(preds, refs)]


# --------------------------------------------------------------------------------------
# F1 — the divergence ladder x domain
# --------------------------------------------------------------------------------------

def fig01():
    cells = kld_cells()
    s5 = load_json("ssa_s5")
    n_tok = {"wikitext2": 65536, "code": 65536, "humaneval": s5["tokens_per_cell"]}
    rows = []
    for arm in ARMS_QUANT:
        for dom, dom_label in DOMAINS:
            c = cells[f"ssa-{arm}-{dom}-kld"]
            rows.append([
                f"UD-{arm}", dom, dom_label, n_tok[dom],
                c["kld_mean"], c["kld_mean_err"],
                round(c["kld_mean"] - 1.959963984540054 * c["kld_mean_err"], 6),
                round(c["kld_mean"] + 1.959963984540054 * c["kld_mean_err"], 6),
                c["same_top_p"], c["rms_dp"], c["ppl_base"], c["ppl_q"],
                "weights", "measured", SSA_PROTOCOL, c["label"],
            ])
    ctl = cells["ssa-Q6_K_XL-code-kld-e2"]
    rows.append([
        "UD-Q6_K_XL (KV-only control)", "code", "code", 65536,
        ctl["kld_mean"], ctl["kld_mean_err"],
        round(ctl["kld_mean"] - 1.959963984540054 * ctl["kld_mean_err"], 6),
        round(ctl["kld_mean"] + 1.959963984540054 * ctl["kld_mean_err"], 6),
        ctl["same_top_p"], ctl["rms_dp"], ctl["ppl_base"], ctl["ppl_q"],
        "kv_dtype_q4_0_vs_f16", "measured", SSA_PROTOCOL, ctl["label"],
    ])
    emit("F1", "fig01-divergence-ladder.csv",
         ["arm", "domain", "domain_label", "n_tokens", "mean_kld_nats", "mean_kld_se_nats",
          "ci95_lo_nats", "ci95_hi_nats", "top1_agreement_pct", "rms_delta_p_pct",
          "ppl_reference", "ppl_arm", "perturbation", "evidence", "protocol", "source_cell"],
         rows, [A["ssa_tables"], A["ssa_s5"]], "PN-13, PN-14, PN-21, PN-15/PN-43, PN-62",
         "reference arm UD-Q6_K_XL; divergence is ladder-relative, not distance from FP16")


# --------------------------------------------------------------------------------------
# F2 / F7 — tail structure
# --------------------------------------------------------------------------------------

QUANTILES = [("kld_median", "median"), ("kld_p90", "p90"), ("kld_p95", "p95"),
             ("kld_p99", "p99"), ("kld_p999", "p99.9"), ("kld_mean", "mean"), ("kld_max", "max")]

PRINT_ULP = 5e-7   # llama-perplexity prints 6 decimals; half-ULP bound on any printed value


def fig01b():
    """Adjacent-pair separation in units of the combined standard error."""
    cells = kld_cells()
    s5 = load_json("ssa_s5")
    n_tok = {"wikitext2": 65536, "code": 65536, "humaneval": s5["tokens_per_cell"]}
    rows = []
    for dom, dom_label in DOMAINS:
        for a, b in [("Q6_K_XL", "Q6_K"), ("Q6_K", "Q5_K_XL"), ("Q5_K_XL", "Q4_K_XL")]:
            if a == "Q6_K_XL":
                continue  # the reference has no measured divergence of its own
            ca, cb = cells[f"ssa-{a}-{dom}-kld"], cells[f"ssa-{b}-{dom}-kld"]
            diff = cb["kld_mean"] - ca["kld_mean"]
            se = math.sqrt(ca["kld_mean_err"] ** 2 + cb["kld_mean_err"] ** 2)
            rows.append([dom, dom_label, f"UD-{a}", f"UD-{b}", n_tok[dom],
                         ca["kld_mean"], ca["kld_mean_err"], cb["kld_mean"], cb["kld_mean_err"],
                         round(diff, 6), round(se, 6), round(diff / se, 2),
                         "true" if (ca["kld_mean"] + ca["kld_mean_err"] <
                                    cb["kld_mean"] - cb["kld_mean_err"]) else "false",
                         "measured"])
    emit("F1b", "fig01b-adjacent-separation.csv",
         ["domain", "domain_label", "arm_a", "arm_b", "n_tokens", "mean_kld_a", "se_a",
          "mean_kld_b", "se_b", "difference_nats", "combined_se_nats", "sigma",
          "intervals_disjoint_at_1se", "evidence"],
         rows, [A["ssa_tables"], A["ssa_s5"]], "PN-13, PN-21",
         "separation in units of the combined standard error; this is the 3.7-11.8 sigma range the paper quotes")


def fig02():
    cells = kld_cells()
    rows = []
    # panel a: code / prose amplification by quantile
    for arm in ARMS_QUANT:
        code = cells[f"ssa-{arm}-code-kld"]
        prose = cells[f"ssa-{arm}-wikitext2-kld"]
        for field, label in QUANTILES:
            cv, pv = code[field], prose[field]
            ratio = cv / pv
            if label == "mean":
                # the tool reports an SE for the mean only; propagate it
                ce, pe = code["kld_mean_err"], prose["kld_mean_err"]
                basis = "tool_reported_se"
                lo, hi = (cv - ce) / (pv + pe), (cv + ce) / (pv - pe)
            else:
                # every other statistic is printed to 6 decimals with no interval at all;
                # the only bound available is half an ULP of the printed value (PN-64)
                basis = "print_precision_half_ulp"
                lo, hi = (cv - PRINT_ULP) / (pv + PRINT_ULP), (cv + PRINT_ULP) / (pv - PRINT_ULP)
            rel = 100 * (hi - lo) / (2 * ratio)
            rows.append(["a", f"UD-{arm}", label, cv, pv, round(ratio, 4),
                         round(lo, 4), round(hi, 4), round(rel, 2), basis,
                         "false" if label == "median" else "true", 65536, "measured"])
    # panel b: shape = quantile / own mean, code cells + the KV-only control + prose reference
    for label, cell in [("UD-Q6_K", "ssa-Q6_K-code-kld"),
                        ("UD-Q5_K_XL", "ssa-Q5_K_XL-code-kld"),
                        ("UD-Q4_K_XL", "ssa-Q4_K_XL-code-kld"),
                        ("KV-only control (no weight quantization)", "ssa-Q6_K_XL-code-kld-e2"),
                        ("UD-Q6_K (prose)", "ssa-Q6_K-wikitext2-kld"),
                        ("UD-Q5_K_XL (prose)", "ssa-Q5_K_XL-wikitext2-kld"),
                        ("UD-Q4_K_XL (prose)", "ssa-Q4_K_XL-wikitext2-kld")]:
            c = cells[cell]
            m = c["kld_mean"]
            for field, qlabel in QUANTILES:
                if qlabel == "mean":
                    continue
                rows.append(["b", label, qlabel, c[field], m, round(c[field] / m, 4),
                             "", "", "", "", "true", 65536, "measured"])
    emit("F2", "fig02-tail-amplification.csv",
         ["panel", "series", "quantile", "code_or_cell_kld_nats", "prose_or_mean_kld_nats",
          "ratio", "ratio_lo", "ratio_hi", "interval_halfwidth_pct", "interval_basis",
          "rankable_across_arms", "n_tokens", "evidence"],
         rows, [A["ssa_tables"]], "PN-35 (corrected by PN-64), PN-62, PN-14",
         "panel a = code/prose by quantile; panel b = quantile/own-mean shape incl. the KV-only control")


def fig07():
    cells = kld_cells()
    rows = []
    corpus_of = {"wikitext2": "prose (WikiText-2)", "code": "code (django)",
                 "humaneval": "task prompts (HumanEval+)"}
    for c in sorted(cells.values(), key=lambda x: x["label"]):
        label = c["label"]
        arm = label.split("-")[1] if not label.startswith("ssa-Q6_K_XL-code-kld-e2") else "Q6_K_XL"
        dom = "code" if "-code-" in label else ("wikitext2" if "wikitext2" in label else "humaneval")
        pert = "kv_dtype_q4_0_vs_f16" if label.endswith("-e2") else "weights"
        m = c["kld_mean"]
        n_tok = 18432 if dom == "humaneval" else 65536
        rows.append([label, f"UD-{arm}", corpus_of[dom], pert, n_tok, m,
                     round(c["kld_median"] / m, 4), round(c["kld_p90"] / m, 3),
                     round(c["kld_p95"] / m, 3), round(c["kld_p99"] / m, 2),
                     round(c["kld_p999"] / m, 2), round(c["kld_max"] / m, 1),
                     c["same_top_p"], "measured"])
    emit("F7", "fig07-tail-shape.csv",
         ["source_cell", "arm", "corpus", "perturbation", "n_tokens", "mean_kld_nats",
          "median_over_mean", "p90_over_mean", "p95_over_mean", "p99_over_mean",
          "p999_over_mean", "max_over_mean", "top1_agreement_pct", "evidence"],
         rows, [A["ssa_tables"]], "PN-62, PN-35, PN-64",
         "shape is flat within a corpus and differs ~3x between corpora; the KV-only control sits with the code cells")


# --------------------------------------------------------------------------------------
# F3 — what each instrument bounds
# --------------------------------------------------------------------------------------

def fig03():
    rows = []

    # HellaSwag, all six pairs (PN-22)
    s7p = load_json("ssa_s7_paired")
    for pair, v in s7p["paired"].items():
        a, b = pair.split("_vs_")
        n = 400
        # orientation: b = a_only? artifact records b and c relative to the named pair
        diff, lo, hi = paired_diff_ci(v["c"], v["b"], n)
        d = v["b"] + v["c"]
        rows.append(["HellaSwag (multiple choice)", f"UD-{b} - UD-{a}", n, "accuracy pts",
                     diff, lo, hi, d, min_attainable_p(d),
                     round(mcnemar_exact_two_sided(v["b"], v["c"]), 4),
                     "paired difference, Wald 95 %", "greedy logprob scoring, llama-perplexity --hellaswag",
                     "measured", "bounded, not separated"])

    # HumanEval+ paired, S6 (PN-28 / PN-40)
    s9 = load_json("s9_scores")
    for t in s9["s6_paired"]["tests"]:
        n = t["n_paired"]
        diff, lo, hi = paired_diff_ci(t["a_only"], t["b_only"], n)
        d = t["discordant"]
        metric = "HumanEval base" if t["metric"] == "base" else "HumanEval+ (base+extra)"
        rows.append([f"{metric} (generative coding)", "UD-Q4_K_XL - UD-Q6_K_XL", n, "pass@1 pts",
                     diff, lo, hi, d, min_attainable_p(d),
                     round(t["p_two_sided_exact"], 4),
                     "paired difference, Wald 95 %",
                     "DEC-2 official non-thinking (temp 0.7/top_p 0.80/top_k 20/presence 1.5), no-spec both arms",
                     "measured", "bounded, not separated"])

    # RULER (PN-33 / PN-44 / PN-60 / PN-63) — recomputed from committed predictions
    for task, length, label in [("niah", 131072, "RULER S-NIAH @131,072 (retrieval)"),
                                ("mk100", 131072, "RULER MK-NIAH @131,072 (retrieval, as published)")]:
        rp, rr = ruler_preds("Q6_K_XL", task, length)
        qp, qr = ruler_preds("Q4_K_XL", task, length)
        ref = [1 if s == 1.0 else 0 for s in ruler_item_scores(rp, rr)]
        cheap = [1 if s == 1.0 else 0 for s in ruler_item_scores(qp, qr)]
        n = len(ref)
        b = sum(1 for x, y in zip(ref, cheap) if y and not x)   # cheap only
        c = sum(1 for x, y in zip(ref, cheap) if x and not y)   # reference only
        diff, lo, hi = paired_diff_ci(b, c, n)
        rows.append([label, "UD-Q4_K_XL - UD-Q6_K_XL", n, "accuracy pts", diff, lo, hi, b + c,
                     min_attainable_p(b + c), round(mcnemar_exact_two_sided(b, c), 6),
                     "paired difference, Wald 95 %",
                     "greedy, thinking ON, n_predict 128 — a fourth sampling configuration",
                     "recomputed",
                     "bounded, not separated" if b + c == 0 or min_attainable_p(b + c) > 0.05
                     else "separated on OUTPUT BUDGET, not retrieval (PN-60)"])

    # RULER mk100 restricted to items where neither arm's budget bound (PN-60)
    rp, rr = ruler_preds("Q6_K_XL", "mk100", 131072)
    qp, qr = ruler_preds("Q4_K_XL", "mk100", 131072)
    ref_s = [1 if s == 1.0 else 0 for s in ruler_item_scores(rp, rr)]
    che_s = [1 if s == 1.0 else 0 for s in ruler_item_scores(qp, qr)]
    ref_c = [1 if "</think>" in p else 0 for p in rp]
    che_c = [1 if "</think>" in p else 0 for p in qp]
    idx = [i for i in range(len(rp)) if ref_c[i] and che_c[i]]
    b = sum(1 for i in idx if che_s[i] and not ref_s[i])
    c = sum(1 for i in idx if ref_s[i] and not che_s[i])
    diff, lo, hi = paired_diff_ci(b, c, len(idx))
    rows.append(["RULER MK-NIAH @131,072, budget-unbound items only", "UD-Q4_K_XL - UD-Q6_K_XL",
                 len(idx), "accuracy pts", diff, lo, hi, b + c,
                 min_attainable_p(b + c), round(mcnemar_exact_two_sided(b, c), 6),
                 "paired difference, Wald 95 %",
                 "greedy, thinking ON, n_predict 128; items where both arms closed </think>",
                 "recomputed", "no difference observable (55/55 both arms)"])
    # RULER closure (the effect that IS separated)
    b = sum(1 for x, y in zip(ref_c, che_c) if y and not x)
    c = sum(1 for x, y in zip(ref_c, che_c) if x and not y)
    diff, lo, hi = paired_diff_ci(b, c, len(ref_c))
    rows.append(["RULER MK-NIAH @131,072 — reasoning-block closure", "UD-Q4_K_XL - UD-Q6_K_XL",
                 len(ref_c), "closure pts", diff, lo, hi, b + c,
                 min_attainable_p(b + c), round(mcnemar_exact_two_sided(b, c), 6),
                 "paired difference, Wald 95 %",
                 "greedy, thinking ON, n_predict 128", "recomputed",
                 "SEPARATED — but the construct is verbosity, not retrieval"])

    # SWE-bench Verified (PN-50) — unpaired, different instance sets
    rows.append(["SWE-bench Verified (agentic, n~=50)", "UD-IQ4_XS - UD-Q6_K", 49, "resolve-rate pts",
                 round(100 * (38 / 49 - 37 / 49), 2), "", "", "", "", "",
                 "unpaired difference of rates; denominators differ (49/50/49)",
                 "greedy temp 0, mini-swe-agent 2.4.6, x86_64-corrected scoring",
                 "historical", "bounded, not separated (bootstrap CI +/-12 pts on one arm alone)"])

    # WikiText-2 perplexity, Protocol 1 (PN-48)
    led = load_json("ledger")["perplexity"]
    lo_ = led["IQ4_XS"]["ppl"] - led["Q6_K_XL"]["ppl"]
    rows.append(["WikiText-2 perplexity, Protocol 1 (n=602 windows)", "UD-IQ4_XS - UD-Q6_K_XL",
                 602, "perplexity", round(lo_, 4), "", "", "", "", "",
                 "difference of point estimates; tool-reported SE +/-0.041 on each",
                 "Protocol 1: llama-perplexity, 602 chunks @ n_ctx 512, half-window scoring",
                 "historical", "ladder ordering correct, no adjacent pair separated"])

    emit("F3", "fig03-instrument-bounds.csv",
         ["instrument", "comparison", "n", "unit", "effect", "ci95_lo", "ci95_hi",
          "discordant", "min_attainable_p", "observed_p", "estimator", "protocol",
          "evidence", "verdict"],
         rows, [A["ssa_s7_paired"], A["s9_scores"], A["ruler"], A["ledger"]] +
               [A["preds:Q6_K_XL:mk100:131072"], A["preds:Q4_K_XL:mk100:131072"]],
         "PN-22, PN-28, PN-40, PN-33, PN-44, PN-60, PN-63, PN-50, PN-48",
         "min_attainable_p is the smallest two-sided exact McNemar p reachable at that discordant count")


def fig24():
    rows = []
    examples = {3: "HumanEval+ base (PN-40)", 5: "HumanEval+ base+extra (PN-40)",
                4: "HellaSwag, largest pair (PN-22)", 10: "RULER MK-NIAH score (PN-44)",
                27: "RULER MK-NIAH closure (PN-60)"}
    for d in range(0, 31):
        rows.append([d, min_attainable_p(d),
                     "true" if min_attainable_p(d) <= 0.05 else "false",
                     examples.get(d, "")])
    emit("F24", "fig24-minimum-p.csv",
         ["discordant_pairs", "min_attainable_two_sided_p", "can_reach_0.05", "instance_in_this_study"],
         rows, ["derived: exact binomial at the extreme split (d,0)"],
         "PN-40, PN-22", "the smallest p a paired binary test can return is set by the discordant count, not by n")


# --------------------------------------------------------------------------------------
# F4 — context ceiling x tensor split
# --------------------------------------------------------------------------------------

HEADLINE_CTX = {"Q4_K_XL": 262144, "Q5_K_XL": 262144, "Q6_K": 262144, "Q6_K_XL": 196608}


def fig28():
    """The full family of inferential tests, with Holm and Benjamini-Hochberg, and the
    design-effect sensitivity of each divergence separation.

    Family definition (post-PN-60): nine divergence z-separations (3 domains x 3 arm pairs),
    six HellaSwag paired tests, two HumanEval+ paired tests, the RULER MK-NIAH closure test, and
    the draft-depth sign test = 19 tests. The withdrawn MK-NIAH *retrieval* test is carried as a
    20th row, marked, so both family definitions can be read off one table.
    """
    cells = kld_cells()
    tests = []
    for dom, lab in [("wikitext2", "prose"), ("code", "code"), ("humaneval", "task prompts")]:
        for a, b in [("Q6_K", "Q5_K_XL"), ("Q5_K_XL", "Q4_K_XL"), ("Q6_K", "Q4_K_XL")]:
            ca, cb = cells[f"ssa-{a}-{dom}-kld"], cells[f"ssa-{b}-{dom}-kld"]
            d = cb["kld_mean"] - ca["kld_mean"]
            se = math.sqrt(ca["kld_mean_err"] ** 2 + cb["kld_mean_err"] ** 2)
            z = d / se
            tests.append({"test": f"KLD {lab}: UD-{a} vs UD-{b}", "family": "divergence",
                          "sigma": round(z, 2), "p": math.erfc(abs(z) / math.sqrt(2)),
                          "in_family": True})
    for pair, v in load_json("ssa_s7_paired")["paired"].items():
        a, b = pair.split("_vs_")
        tests.append({"test": f"HellaSwag paired: UD-{a} vs UD-{b}", "family": "task benchmark",
                      "sigma": None, "p": mcnemar_exact_two_sided(v["b"], v["c"]), "in_family": True})
    for t in load_json("s9_scores")["s6_paired"]["tests"]:
        tests.append({"test": f"HumanEval+ paired ({t['metric']}): UD-Q4_K_XL vs UD-Q6_K_XL",
                      "family": "task benchmark", "sigma": None,
                      "p": mcnemar_exact_two_sided(t["a_only"], t["b_only"]), "in_family": True})
    rp, _ = ruler_preds("Q6_K_XL", "mk100", 131072)
    qp, _ = ruler_preds("Q4_K_XL", "mk100", 131072)
    rc = [1 if "</think>" in p else 0 for p in rp]
    qc = [1 if "</think>" in p else 0 for p in qp]
    b = sum(1 for x, y in zip(rc, qc) if y and not x)
    c = sum(1 for x, y in zip(rc, qc) if x and not y)
    tests.append({"test": "RULER MK-NIAH @131,072: reasoning-block closure", "family": "task benchmark",
                  "sigma": None, "p": mcnemar_exact_two_sided(b, c), "in_family": True})
    tests.append({"test": "MTP acceptance falls with draft depth (10 of 11 adjacent pairs, one-sided)",
                  "family": "speculative decoding", "sigma": None,
                  "p": sum(math.comb(11, k) for k in range(10, 12)) / 2 ** 11, "in_family": True})
    tests.append({"test": "RULER MK-NIAH @131,072: retrieval score (WITHDRAWN as retrieval, PN-60)",
                  "family": "task benchmark", "sigma": None,
                  "p": mcnemar_exact_two_sided(10, 0), "in_family": False})

    core = sorted([t for t in tests if t["in_family"]], key=lambda t: t["p"])
    m = len(core)
    holm_ok = True
    bh_cut = 0
    for i in range(m - 1, -1, -1):
        if core[i]["p"] <= 0.05 * (i + 1) / m:
            bh_cut = i + 1
            break
    rows = []
    for i, t in enumerate(core):
        ht = 0.05 / (m - i)
        if holm_ok and t["p"] > ht:
            holm_ok = False
        zb = 3.0233  # two-sided Bonferroni z at alpha=0.05, m=19
        rows.append([i + 1, t["test"], t["family"], t["sigma"] if t["sigma"] else "",
                     t["p"], ht, "pass" if holm_ok else "fail",
                     round(0.05 * (i + 1) / m, 5), "y" if i < bh_cut else "n",
                     round((t["sigma"] / 1.96) ** 2, 2) if t["sigma"] else "",
                     round((t["sigma"] / zb) ** 2, 2) if t["sigma"] else "",
                     "in family (m=19)", "recomputed"])
    w = [t for t in tests if not t["in_family"]][0]
    rows.append(["-", w["test"], w["family"], "", w["p"], "", "", "", "", "", "",
                 "excluded from the family: withdrawn as a retrieval result (PN-60)", "recomputed"])
    emit("F28", "fig28-multiplicity.csv",
         ["rank", "test", "family", "sigma", "p_value", "holm_threshold", "holm",
          "bh_threshold", "bh", "deff_to_drop_below_z1.96", "deff_to_drop_below_bonferroni_z",
          "membership", "evidence"],
         rows, [A["ssa_tables"], A["ssa_s7_paired"], A["s9_scores"],
                A["preds:Q6_K_XL:mk100:131072"], A["preds:Q4_K_XL:mk100:131072"], A["s9d"]],
         "PN-13, PN-21, PN-22, PN-28, PN-32, PN-40, PN-60",
         "Holm and Benjamini-Hochberg over the whole 19-test family at alpha 0.05; DEFF columns give the "
         "design effect that would drop each divergence separation below the named critical value")


def fig04():
    cells = tsweep_cells()
    rows = []
    ratios = ["default", "52,48", "54,46", "56,44", "58,42", "60,40", "62,38"]
    by = {}
    for c in cells:
        if c["rep"] != 1 or c.get("tag") not in (None, "", "base"):
            continue
        by[(c["arm"], c["ctx_requested"], c["ts_label"])] = c
    for arm in ARMS_LADDER:
        ctx = HEADLINE_CTX[arm]
        for ts in ratios:
            c = by.get((arm, ctx, ts))
            if c is None:
                rows.append([f"UD-{arm}", ctx, ts, "not_tested", "", "", "", "", "", "", 1, "measured"])
                continue
            vram = c.get("vram_peak_mib") or [None, None]
            rows.append([f"UD-{arm}", ctx, ts, "loaded" if c["ok"] else "failed",
                         round(c["decode_tok_s"], 2) if c.get("decode_tok_s") else "",
                         c.get("failure_mode") or "", vram[0], vram[1], c.get("imbalance_mib"),
                         c.get("mtp_acceptance"), c["rep"], "measured"])
    emit("F4", "fig04-ceiling-matrix.csv",
         ["arm", "ctx_requested_tokens", "tensor_split", "status", "decode_tok_s",
          "failure_mode", "vram_peak_gpu0_mib", "vram_peak_gpu1_mib", "imbalance_mib",
          "mtp_acceptance", "rep", "evidence"],
         rows, [A["tsweep_q4"], A["tsweep_q5"], A["tsweep_q6k"], A["tsweep_q6kxl"]],
         "PN-6, PN-7, PN-39",
         "each arm shown at its headline rung; every failure is a SINGLE attempt (PN-39) except Q6_K_XL@229,376")


def fig04b():
    rows = []
    for c in sorted(tsweep_cells(), key=lambda x: (x["arm"], -x["ctx_requested"], x["ts_label"], x["rep"])):
        vram = c.get("vram_peak_mib") or [None, None]
        rows.append([f"UD-{c['arm']}", c["key"], c["ctx_requested"], c["ts_label"], c["rep"],
                     c.get("tag") or "base", c.get("ctxcp"), "true" if c["ok"] else "false",
                     c.get("failure_mode") or "", c.get("n_ctx_reported"),
                     round(c["decode_tok_s"], 4) if c.get("decode_tok_s") else "",
                     round(c["prefill_tok_s"], 1) if c.get("prefill_tok_s") else "",
                     c.get("prefill_frac"), c.get("prefill_tokens"),
                     vram[0], vram[1], c.get("imbalance_mib"), c.get("mtp_acceptance"),
                     c.get("draft_n"), c.get("draft_n_accepted"), "measured"])
    emit("T10", "fig04b-sweep-full.csv",
         ["arm", "cell_key", "ctx_requested_tokens", "tensor_split", "rep", "tag", "ctxcp",
          "ok", "failure_mode", "n_ctx_reported", "decode_tok_s", "prefill_tok_s",
          "prefill_frac", "prefill_tokens", "vram_peak_gpu0_mib", "vram_peak_gpu1_mib",
          "imbalance_mib", "mtp_acceptance", "draft_n", "draft_n_accepted", "evidence"],
         rows, [A["tsweep_q4"], A["tsweep_q5"], A["tsweep_q6k"], A["tsweep_q6kxl"]],
         "PN-6, PN-7, PN-8, PN-18, PN-19, PN-36, PN-39, PN-42, PN-45",
         "the complete Wave-1 sweep, all cells, for the appendix table")


def fig04c():
    """Per-arm bracketed ceiling, every ratio that reaches it, and the fastest of them.

    Restricted to base cells at -ctxcp 4 so that no group mixes an untracked variable
    (PN-45's lesson, applied to this aggregate).
    """
    all_cells = tsweep_cells()
    cells = [c for c in all_cells
             if c.get("ctxcp") == 4 and (c.get("tag") in (None, "", "base"))]
    ok = [c for c in cells if c["ok"]]
    rows = []
    for arm in ARMS_LADDER:
        arm_cells = [c for c in ok if c["arm"] == arm]
        ceiling = max(c["ctx_requested"] for c in arm_cells)
        at = [c for c in arm_cells if c["ctx_requested"] == ceiling]
        by_ts = defaultdict(list)
        for c in at:
            by_ts[c["ts_label"]].append(c["decode_tok_s"])
        meds = {t: statistics.median(v) for t, v in by_ts.items()}
        win = max(meds, key=lambda t: meds[t])
        wcells = [c for c in at if c["ts_label"] == win]
        vram = wcells[0].get("vram_peak_mib") or [None, None]
        failed_at = sorted({c["ts_label"] for c in cells
                            if c["arm"] == arm and not c["ok"] and c["ctx_requested"] == ceiling})
        fails_above = [c for c in all_cells if c["arm"] == arm and not c["ok"]
                       and c["ctx_requested"] > ceiling]
        default_at_ceiling = [c for c in all_cells if c["arm"] == arm and c["ts_label"] == "default"
                              and c["ctx_requested"] == ceiling]
        dflt = ("loads" if (default_at_ceiling and default_at_ceiling[0]["ok"])
                else (f"fails ({len(default_at_ceiling)} attempt(s))" if default_at_ceiling
                      else "never attempted"))
        spread = 100 * (max(meds.values()) - min(meds.values())) / min(meds.values())
        rows.append([f"UD-{arm}", ceiling,
                     " ".join(sorted(by_ts, key=lambda t: -meds[t])), len(by_ts),
                     " ".join(failed_at) or "-", win, len(by_ts[win]), round(meds[win], 3),
                     round(spread, 1),
                     "false" if spread < 40.7 else "true",
                     vram[0], vram[1], wcells[0].get("imbalance_mib"),
                     wcells[0].get("mtp_acceptance"), wcells[0].get("prefill_frac"),
                     len(fails_above),
                     "native maximum, no rung above" if ceiling == 262144
                     else f"bracketed by {len(fails_above)} failed attempt(s) above",
                     dflt, "measured"])
    emit("T11", "fig04c-ceilings-summary.csv",
         ["arm", "ceiling_tokens", "ratios_that_load_fastest_first", "n_ratios_loading",
          "ratios_that_failed_at_this_rung", "fastest_ratio", "n_reps_at_fastest",
          "decode_tok_s_median", "spread_across_loading_ratios_pct",
          "ratio_difference_exceeds_noise_floor", "vram_peak_gpu0_mib", "vram_peak_gpu1_mib",
          "imbalance_mib", "mtp_acceptance", "prefill_frac", "failed_attempts_above",
          "bracketing", "engine_default_split_at_this_rung", "evidence"],
         rows, [A["tsweep_q4"], A["tsweep_q5"], A["tsweep_q6k"], A["tsweep_q6kxl"]],
         "PN-6, PN-7, PN-39, PN-42, PN-45",
         "MTP n=2 + q4_0 KV + -sm layer, base cells at -ctxcp 4 only; the noise floor is PN-45's 40.7 % "
         "within-configuration spread, so a smaller between-ratio spread is not a measured ordering")


def fig11():
    rows = []
    for c in tsweep_cells():
        vram = c.get("vram_peak_mib") or [None, None]
        if vram[0] is None:
            continue
        binding = "GPU1" if vram[1] >= vram[0] else "GPU0"
        headroom = 16311 - max(vram)
        stranded = abs(vram[0] - vram[1])
        rows.append([f"UD-{c['arm']}", c["ctx_requested"], c["ts_label"], c["rep"],
                     "true" if c["ok"] else "false", c.get("failure_mode") or "",
                     vram[0], vram[1], stranded, binding, headroom,
                     round(c["decode_tok_s"], 2) if c.get("decode_tok_s") else "", "measured"])
    rows.sort(key=lambda r: (r[0], -r[1], r[2], r[3]))
    emit("F11", "fig11-vram-asymmetry.csv",
         ["arm", "ctx_requested_tokens", "tensor_split", "rep", "ok", "failure_mode",
          "vram_peak_gpu0_mib", "vram_peak_gpu1_mib", "stranded_on_lighter_card_mib",
          "binding_card", "headroom_on_binding_card_mib", "decode_tok_s", "evidence"],
         rows, [A["tsweep_q4"], A["tsweep_q5"], A["tsweep_q6k"], A["tsweep_q6kxl"], A["env"]],
         "PN-6, PN-7, PN-12",
         "card total 16,311 MiB (env-manifest); with -sm layer each layer's weights AND its KV slice sit on one card")


# --------------------------------------------------------------------------------------
# F5 / F13 — speculative decoding
# --------------------------------------------------------------------------------------

def fig05():
    s8 = load_json("s8_humaneval")
    s8s = load_json("s8_scores_reparsed")
    det = load_json("s9_determinism")
    dfl = load_json("s9_dflash")
    cfg = {c["config"]: c for c in s8["configs"]}
    base = cfg["nospec"]["decode_tok_s_median"]
    rows = []

    def row(name, decode, acc, exact, n, image, conf, base_pass, plus_pass, note):
        lo_b, hi_b = wilson(base_pass, n) if base_pass is not None else ("", "")
        lo_p, hi_p = wilson(plus_pass, n) if plus_pass is not None else ("", "")
        rows.append([name, decode, round(decode / base, 3), acc, exact, n,
                     round(100 * exact / n, 2), image, conf,
                     round(100 * base_pass / n, 2) if base_pass is not None else "",
                     lo_b, hi_b,
                     round(100 * plus_pass / n, 2) if plus_pass is not None else "",
                     lo_p, hi_p, note, "measured"])

    a = s8s["arms"]
    row("no-spec (baseline; identity vs its own repeat)", base, "",
        det["comparisons"]["nospec_self"]["exact_match"], 164, "llamacpp-mtp:latest", "false",
        a["nospec"]["base_pass"], a["nospec"]["plus_pass"],
        "self-repeat control run one day later: 164/164 byte-identical, "
        f"decode {det['runs'][0]['decode_tok_s_median']} tok/s on the repeat")
    row("MTP n=2", cfg["mtp2"]["decode_tok_s_median"], cfg["mtp2"]["acceptance"],
        s8["equivalence"]["mtp2"]["exact_match"], 164, "llamacpp-mtp:latest", "false",
        a["mtp2"]["base_pass"], a["mtp2"]["plus_pass"], "identity measured against the no-spec baseline")
    row("MTP n=4", cfg["mtp4"]["decode_tok_s_median"], cfg["mtp4"]["acceptance"],
        s8["equivalence"]["mtp4"]["exact_match"], 164, "llamacpp-mtp:latest", "false",
        a["mtp4"]["base_pass"], a["mtp4"]["plus_pass"], "identity measured against the no-spec baseline")
    s9sc = load_json("s9_scores")["arms"]["dflash4-he"]
    row("DFlash2 n=4", dfl["runs"][0]["decode_tok_s_median"], dfl["runs"][0]["acceptance"],
        dfl["equivalence"]["exact_match"], 164, "llama-dflash2:latest", "true",
        s9sc["base_pass"], s9sc["plus_pass"],
        "ENGINE-CONFOUNDED: baseline produced on llamacpp-mtp:latest, this arm on llama-dflash2:latest")
    emit("F5", "fig05-speculation.csv",
         ["config", "decode_tok_s_median", "speedup_vs_nospec", "draft_acceptance",
          "byte_exact_vs_baseline_n", "n_problems", "byte_exact_pct", "engine_image",
          "engine_confounded", "pass1_base_pct", "pass1_base_wilson_lo", "pass1_base_wilson_hi",
          "pass1_plus_pct", "pass1_plus_wilson_lo", "pass1_plus_wilson_hi", "note", "evidence"],
         rows, [A["s8_humaneval"], A["s8_scores_reparsed"], A["s9_determinism"], A["s9_dflash"], A["s9_scores"]],
         "PN-23, PN-25, PN-26, PN-29",
         "UD-Q6_K, ctx 32,768, -ts 58,42, -ctxcp 32, q4_0 KV, greedy temp 0 / top_p 1 / seed 20260830")


def fig13():
    ns = load_jsonl_solutions("s8_nospec")
    arms = {
        "MTP n=2": load_jsonl_solutions("s8_mtp2"),
        "MTP n=4": load_jsonl_solutions("s8_mtp4"),
        "DFlash2 n=4 (engine-confounded)": load_jsonl_solutions("s9_dflash_jsonl"),
        "no-spec self-repeat (control)": load_jsonl_solutions("s9_nospec_r2"),
    }
    ids = sorted(ns, key=lambda k: int(k.split("/")[1]))
    lengths = [len(ns[k]) for k in ids]
    cuts = statistics.quantiles(lengths, n=4)
    rows, per = [], []
    for name, other in arms.items():
        diverged = {k: (ns[k] != other[k]) for k in ids}
        firsts = {k: first_diff_char(ns[k], other[k]) for k in ids if diverged[k]}
        n_div = sum(diverged.values())
        # constant-hazard MLE with right censoring at the baseline completion length
        exposure = sum(firsts.values()) + sum(len(ns[k]) for k in ids if not diverged[k])
        h = n_div / exposure if exposure else float("nan")
        for qi in range(4):
            lo = -1 if qi == 0 else cuts[qi - 1]
            hi = cuts[qi] if qi < 3 else float("inf")
            sub = [k for k in ids if lo < len(ns[k]) <= hi]
            dv = [k for k in sub if diverged[k]]
            wl, wh = wilson(len(dv), len(sub))
            rows.append([name, f"Q{qi+1}", round(lo if qi else 0), round(hi if qi < 3 else max(lengths)),
                         len(sub), len(dv), round(100 * len(dv) / len(sub), 1), wl, wh,
                         n_div, round(100 * n_div / len(ids), 2),
                         round(statistics.median(list(firsts.values())), 1) if firsts else "",
                         round(h, 8), round(1 / h) if h else "", "recomputed"])
    for k in ids:
        per.append([k, len(ns[k]),
                    *[("true" if ns[k] != other[k] else "false") for other in arms.values()],
                    *[(first_diff_char(ns[k], other[k]) if ns[k] != other[k] else "")
                      for other in arms.values()]])
    emit("F13", "fig13-divergence-length.csv",
         ["config", "quartile", "len_lo_chars", "len_hi_chars", "n_problems", "n_divergent",
          "divergence_rate_pct", "wilson_lo", "wilson_hi", "total_divergent", "total_rate_pct",
          "median_first_divergence_char", "hazard_per_char", "chars_per_divergence", "evidence"],
         rows, [A["s8_nospec"], A["s8_mtp2"], A["s8_mtp4"], A["s9_dflash_jsonl"], A["s9_nospec_r2"]],
         "PN-23, PN-26, PN-29",
         "quartiles are of the NO-SPEC baseline completion length; hazard is a constant-rate MLE with right censoring")
    emit("F13b", "fig13b-divergence-perproblem.csv",
         ["task_id", "baseline_len_chars"] +
         [f"diverged_{s}" for s in ("mtp2", "mtp4", "dflash4", "nospec_repeat")] +
         [f"first_div_char_{s}" for s in ("mtp2", "mtp4", "dflash4", "nospec_repeat")],
         per, [A["s8_nospec"], A["s8_mtp2"], A["s8_mtp4"], A["s9_dflash_jsonl"], A["s9_nospec_r2"]],
         "PN-23, PN-26", "per-problem record behind F13; 164 rows")


def fig14():
    d = load_json("s9d")
    e = load_json("s9e")
    cells, reps = [], []
    for src in (d, e):
        for c in src["cells"]:
            valid = bool(c.get("valid"))
            acc = c.get("acceptance")
            cells.append([f"UD-{c['arm']}", c["ctx"], c["n_draft"], c["ts"],
                          "true" if valid else "false", c.get("failure_mode") or "",
                          acc if acc is not None else "",
                          round(implied_q(acc, c["n_draft"]), 4) if (valid and acc) else "",
                          c.get("decode_tok_s_median", ""), c.get("decode_spread_pct", ""),
                          c.get("draft_n_total", ""), c.get("draft_accepted_total", ""),
                          c.get("prefill_frac", ""), c.get("prompt_n", ""),
                          c.get("predicted_n_min", ""), len(c.get("reps") or []), "measured"])
            for r in (c.get("reps") or []):
                racc = (r["draft_n_accepted"] / r["draft_n"]) if r.get("draft_n") else ""
                reps.append([f"UD-{c['arm']}", c["ctx"], c["n_draft"], r["rep"],
                             round(r["decode_tok_s"], 3), r.get("predicted_n"),
                             r.get("draft_n"), r.get("draft_n_accepted"),
                             round(racc, 4) if racc != "" else "",
                             "true" if valid else "false", "measured"])
    cells.sort(key=lambda r: (r[1], r[0], r[2]))
    reps.sort(key=lambda r: (r[1], r[0], r[2], r[3]))
    emit("F14", "fig14-draftdepth.csv",
         ["arm", "ctx_tokens", "n_draft", "tensor_split", "valid", "failure_mode",
          "acceptance_pooled", "implied_per_token_match_q", "decode_tok_s_median",
          "decode_spread_pct", "draft_n_total", "draft_accepted_total", "prefill_frac",
          "prompt_n", "predicted_n_min", "n_reps", "evidence"],
         cells, [A["s9d"], A["s9e"]], "PN-32, PN-9, PN-24",
         "3 reps x 512 tokens per cell; the pooled acceptance interval is NOT the honest one (clustering)")
    emit("F14b", "fig14b-draftdepth-reps.csv",
         ["arm", "ctx_tokens", "n_draft", "rep", "decode_tok_s", "predicted_n", "draft_n",
          "draft_n_accepted", "acceptance_rep", "cell_valid", "evidence"],
         reps, [A["s9d"], A["s9e"]], "PN-32",
         "per-repetition values: the unit of independence is the generation, not the draft event")


# --------------------------------------------------------------------------------------
# F6 — two instruments, one axis
# --------------------------------------------------------------------------------------

def fig06():
    rows = []
    s7 = load_json("ssa_s7")
    for c in s7["cells"]:
        sc = c["score"]
        rows.append(["upper", f"UD-{c['arm']}", "HellaSwag (n=400)", sc["acc_pct"],
                     round(sc["ci95_lo_pct"], 2), round(sc["ci95_hi_pct"], 2), sc["n"],
                     "Wilson 95 %", "greedy logprob scoring", "measured"])
    s9 = load_json("s9_scores")["arms"]
    for key, arm in (("s6-Q6_K_XL", "Q6_K_XL"), ("s6-Q4_K_XL", "Q4_K_XL")):
        a = s9[key]
        rows.append(["upper", f"UD-{arm}", "HumanEval+ base+extra (n=164, paired)", a["plus_pct"],
                     a["plus_wilson95"][0], a["plus_wilson95"][1], a["n"], "Wilson 95 %",
                     "DEC-2 official non-thinking, no-spec", "measured"])
    for arm in ("Q6_K_XL", "Q4_K_XL"):
        p, r = ruler_preds(arm, "niah", 131072)
        s = ruler_string_match_all(p, r)
        k = sum(1 for x in ruler_item_scores(p, r) if x == 1.0)
        lo, hi = wilson(k, len(p))
        rows.append(["upper", f"UD-{arm}", "RULER S-NIAH @131,072 (n=12)", s, lo, hi, len(p),
                     "Wilson 95 %", "greedy, thinking ON, n_predict 128", "recomputed"])
    cells = kld_cells()
    for arm in ARMS_QUANT:
        c = cells[f"ssa-{arm}-code-kld"]
        rows.append(["lower", f"UD-{arm}", "mean KL divergence, code (n=65,536 tokens)",
                     c["kld_mean"], round(c["kld_mean"] - c["kld_mean_err"], 6),
                     round(c["kld_mean"] + c["kld_mean_err"], 6), 65536, "+/-1 SE (tool-reported)",
                     SSA_PROTOCOL, "measured"])
    rows.append(["lower", "UD-Q6_K_XL", "mean KL divergence, code (n=65,536 tokens)", 0.0, "", "",
                 65536, "reference arm: 0 by construction", SSA_PROTOCOL, "measured"])
    emit("F6", "fig06-two-instruments.csv",
         ["panel", "arm", "instrument", "value", "ci_lo", "ci_hi", "n", "estimator",
          "protocol", "evidence"],
         rows, [A["ssa_s7"], A["s9_scores"], A["ssa_tables"]] +
               [A["preds:Q6_K_XL:niah:131072"], A["preds:Q4_K_XL:niah:131072"]],
         "PN-22, PN-28, PN-33, PN-13",
         "upper panel accuracy (%), lower panel divergence (nats, log scale) — the panels share only the x categories")


def fig08():
    cells = kld_cells()
    rows = []
    for arm in ARMS_QUANT:
        for dom, label in DOMAINS:
            c = cells[f"ssa-{arm}-{dom}-kld"]
            rows.append([f"UD-{arm}", dom, label, c["kld_mean"], c["kld_mean_err"],
                         c["same_top_p"], c["rms_dp"], c["ppl_base"], c["ppl_q"],
                         round(100 * (c["ppl_q"] / c["ppl_base"] - 1), 3),
                         18432 if dom == "humaneval" else 65536, "measured"])
    ctl = cells["ssa-Q6_K_XL-code-kld-e2"]
    rows.append(["UD-Q6_K_XL (KV-only control)", "code", "code", ctl["kld_mean"], ctl["kld_mean_err"],
                 ctl["same_top_p"], ctl["rms_dp"], ctl["ppl_base"], ctl["ppl_q"],
                 round(100 * (ctl["ppl_q"] / ctl["ppl_base"] - 1), 3), 65536, "measured"])
    emit("F8", "fig08-metric-pair.csv",
         ["arm", "domain", "domain_label", "mean_kld_nats", "mean_kld_se_nats",
          "top1_agreement_pct", "rms_delta_p_pct", "ppl_reference", "ppl_arm",
          "ppl_change_pct", "n_tokens", "evidence"],
         rows, [A["ssa_tables"]], "PN-16, PN-15, PN-43",
         "top-1 agreement is HIGHER on code while mean KLD is roughly double: a top-1-only table inverts the conclusion")


# --------------------------------------------------------------------------------------
# F9 — RULER closure audit
# --------------------------------------------------------------------------------------

def fig09():
    r = load_json("ruler")
    published = {(c["arm"], c["task"], c["length"]): c for c in r["cells"]}
    rows = []
    for arm, task, length in RULER_PREDS:
        preds, refs = ruler_preds(arm, task, length)
        item = ruler_item_scores(preds, refs)
        full = [1 if s == 1.0 else 0 for s in item]
        closed = [1 if "</think>" in p else 0 for p in preds]
        n = len(preds)
        cell = published.get((arm, task, length))
        pub = cell["score"] if cell else ""
        lo, hi = wilson(sum(full), n)
        rows.append([f"UD-{arm}", task, length, n,
                     ruler_string_match_all(preds, refs), pub, sum(full), lo, hi,
                     sum(closed), round(100 * sum(closed) / n, 1),
                     sum(1 for s, c in zip(full, closed) if c and not s),
                     sum(1 for s, c in zip(full, closed) if s and not c),
                     round(statistics.median([len(p) for p in preds])),
                     cell["prompt_n_median"] if cell else "", "recomputed"])
    emit("F9", "fig09-ruler-closure.csv",
         ["arm", "task", "context_tokens", "n_samples", "string_match_all_recomputed",
          "string_match_all_published", "items_fully_correct", "wilson_lo", "wilson_hi",
          "items_closed_think_block", "closure_pct", "closed_and_wrong",
          "correct_without_closing", "median_output_chars", "prompt_n_median", "evidence"],
         rows, [A["ruler"]] + [A[f"preds:{a}:{t}:{l}"] for a, t, l in RULER_PREDS],
         "PN-33, PN-44, PN-60, PN-63",
         "closed_and_wrong is 0 in every cell: no item in this battery finished reasoning and answered wrongly")


def fig09b():
    rp, rr = ruler_preds("Q6_K_XL", "mk100", 131072)
    qp, qr = ruler_preds("Q4_K_XL", "mk100", 131072)
    ref_s = [1 if s == 1.0 else 0 for s in ruler_item_scores(rp, rr)]
    che_s = [1 if s == 1.0 else 0 for s in ruler_item_scores(qp, qr)]
    ref_c = [1 if "</think>" in p else 0 for p in rp]
    che_c = [1 if "</think>" in p else 0 for p in qp]
    n = len(rp)
    rows = []

    def block(label, x, y, subset=None):
        idx = subset if subset is not None else range(n)
        both = sum(1 for i in idx if x[i] and y[i])
        aonly = sum(1 for i in idx if x[i] and not y[i])
        bonly = sum(1 for i in idx if y[i] and not x[i])
        neither = sum(1 for i in idx if not x[i] and not y[i])
        d = aonly + bonly
        diff, lo, hi = paired_diff_ci(bonly, aonly, len(list(idx)))
        rows.append([label, len(list(idx)), both, aonly, bonly, neither, d,
                     round(mcnemar_exact_two_sided(aonly, bonly), 6),
                     min_attainable_p(d), diff, lo, hi, "recomputed"])

    block("retrieval score, all items", ref_s, che_s)
    block("reasoning-block closure, all items", ref_c, che_c)
    block("retrieval score, both arms closed (budget-unbound)", ref_s, che_s,
          [i for i in range(n) if ref_c[i] and che_c[i]])
    emit("F9b", "fig09b-ruler-mk100-paired.csv",
         ["comparison", "n", "both", "reference_only", "cheaper_arm_only", "neither",
          "discordant", "exact_mcnemar_p", "min_attainable_p", "paired_diff_pts",
          "ci95_lo", "ci95_hi", "evidence"],
         rows, [A["preds:Q6_K_XL:mk100:131072"], A["preds:Q4_K_XL:mk100:131072"]],
         "PN-44, PN-60, PN-63",
         "the published retrieval separation and the closure separation, side by side, plus the budget-unbound subset")


# --------------------------------------------------------------------------------------
# F10 — the protocol swing
# --------------------------------------------------------------------------------------

def fig10():
    """PN-49. NOTE: these three readings are the only ones that exist; the three conventions
    were not varied one at a time, so the decomposition below is TWO measured steps, not three."""
    rows = [
        ["as first published", "/srv/bench/perplexity/wikitext-2-test.txt (297,053 tokens)",
         160, "all positions from 0, no prior context", 77621, 2.149994, 8.5848,
         round(100 * (8.5848 / 6.6511 - 1), 1), "measured", "historical",
         "nvfp4-vllm-ppl.json (self-labels protocol 2 — that label is wrong and unrelated)"],
        ["corpus + coverage aligned to Protocol 1", "/srv/bench/corpus/wikitext2-test.txt (308,707 tokens)",
         602, "all positions >= 1, no half-window rule", "", "", 8.0775,
         round(100 * (8.0775 / 6.6511 - 1), 1), "measured", "historical",
         "cross-check reported alongside nvfp4-vllm-ppl-protocol1.json"],
        ["+ half-window scoring rule (full Protocol 1)", "/srv/bench/corpus/wikitext2-test.txt (308,707 tokens)",
         602, "positions 256.. of each 512-token window, first half as context", 154714,
         1.903193, 6.7073, round(100 * (6.7073 / 6.6511 - 1), 1), "measured", "historical",
         "nvfp4-vllm-ppl-protocol1.json"],
    ]
    led = load_json("ledger")["perplexity"]
    for arm in ("Q6_K_XL", "Q5_K_XL", "Q4_K_XL", "IQ4_XS"):
        rows.append([f"GGUF ladder reference: UD-{arm}", "/srv/bench/corpus/wikitext2-test.txt",
                     602, "positions 256.. of each 512-token window", "", "",
                     led[arm]["ppl"], 0.0, "measured", "historical",
                     "ledger-data.json perplexity (Protocol 1)"])
    emit("F10", "fig10-protocol-swing.csv",
         ["step", "corpus_file", "windows_scored", "scoring_rule", "tokens_scored",
          "avg_nll", "perplexity", "apparent_degradation_vs_Q6_K_XL_pct", "evidence",
          "reproducibility", "source"],
         rows, [A["ledger"], "data/multivac-src/PAPER-REFERENCES.md (host artifact paths recorded there)"],
         "PN-49, PN-48",
         "same weights throughout; 36x swing in the estimated effect comes only from measurement convention")


def fig26():
    led = load_json("ledger")["perplexity"]
    order = ["Q6_K_XL", "Q5_K_XL", "Q4_K_XL", "IQ4_XS"]
    rows = []
    best = led["Q6_K_XL"]["ppl"]
    for arm in order:
        v = led[arm]
        rows.append([f"UD-{arm}", v["ppl"], v["err"], round(v["ppl"] - v["err"], 5),
                     round(v["ppl"] + v["err"], 5), round(v["ppl"] - best, 4),
                     round(100 * (v["ppl"] / best - 1), 3), 602,
                     "tool-reported standard error", "Protocol 1", "historical"])
    rows.append(["vLLM NVFP4 (cross-backend, re-scored)", 6.7073, "", "", "",
                 round(6.7073 - best, 4), round(100 * (6.7073 / best - 1), 3), 602,
                 "no SE reported for the re-score", "Protocol 1 (matched windows)", "historical"])
    emit("F26", "fig26-perplexity-ladder.csv",
         ["arm", "perplexity", "standard_error", "se_lo", "se_hi", "delta_vs_best",
          "delta_pct", "n_windows", "estimator", "protocol", "reproducibility"],
         rows, [A["ledger"]], "PN-48, PN-49",
         "the whole ladder spans 0.033 PPL while each point carries +/-0.041 SE")


# --------------------------------------------------------------------------------------
# F12 / F22 — speed
# --------------------------------------------------------------------------------------

def fig12():
    cells = [c for c in tsweep_cells() if c["ok"] and c.get("decode_tok_s") and c.get("mtp_acceptance")]
    fit_set = [c for c in cells if c["ctx_requested"] == 262144 and c.get("ctxcp") == 4]
    fit = ols([c["mtp_acceptance"] for c in fit_set], [c["decode_tok_s"] for c in fit_set])
    rows = []
    for c in sorted(cells, key=lambda x: (x["arm"], -x["ctx_requested"], x["ts_label"], x["rep"])):
        pred = fit["a"] + fit["b"] * c["mtp_acceptance"]
        in_fit = c["ctx_requested"] == 262144 and c.get("ctxcp") == 4
        rows.append([f"UD-{c['arm']}", c["ctx_requested"], c["ts_label"], c["rep"], c.get("ctxcp"),
                     c["mtp_acceptance"], round(c["decode_tok_s"], 4), round(pred, 4),
                     round(c["decode_tok_s"] - pred, 4), "true" if in_fit else "false",
                     c.get("draft_n"), c.get("draft_n_accepted"), c.get("imbalance_mib"), "measured"])
    emit("F12", "fig12-decode-acceptance.csv",
         ["arm", "ctx_tokens", "tensor_split", "rep", "ctxcp", "mtp_acceptance", "decode_tok_s",
          "fitted_decode_tok_s", "residual_tok_s", "in_regression_set", "draft_n",
          "draft_n_accepted", "imbalance_mib", "evidence"],
         rows, [A["tsweep_q4"], A["tsweep_q5"], A["tsweep_q6k"], A["tsweep_q6kxl"]],
         "PN-19, PN-36, PN-45 (+ reviewer C/D re-analysis)",
         f"OLS on the 262,144 / ctxcp-4 cells: decode = {fit['a']:.3f} + {fit['b']:.3f} x acceptance, "
         f"r = {fit['r']:.4f}, R2 = {fit['r2']:.4f}, residual SD {fit['resid_sd']:.3f} vs raw SD {fit['raw_sd']:.3f} (n = {fit['n']})")

    # panel b: repetition groups, raw and acceptance-adjusted spread
    groups = defaultdict(list)
    for c in cells:
        groups[(c["arm"], c["ctx_requested"], c["ts_label"], c.get("ctxcp"))].append(c)
    grows = []
    for k, v in sorted(groups.items()):
        ds = [x["decode_tok_s"] for x in v]
        accs = [x["mtp_acceptance"] for x in v]
        med = statistics.median(ds)
        raw_med = 100 * (max(ds) - min(ds)) / med
        raw_min = 100 * (max(ds) - min(ds)) / min(ds)
        mean_acc = sum(accs) / len(accs)
        adj = [x["decode_tok_s"] - fit["b"] * (x["mtp_acceptance"] - mean_acc) for x in v]
        adj_med = 100 * (max(adj) - min(adj)) / statistics.median(adj)
        grows.append([f"UD-{k[0]}", k[1], k[2], k[3], len(v),
                      " | ".join(f"{x:.2f}" for x in ds),
                      " | ".join(f"{a:.4f}" for a in accs), round(med, 3),
                      round(raw_med, 1), round(raw_min, 1), round(adj_med, 1),
                      "true" if len(v) >= 3 else "false", "measured"])
    emit("F12b", "fig12b-speed-groups.csv",
         ["arm", "ctx_tokens", "tensor_split", "ctxcp", "n_reps", "decode_readings_tok_s",
          "acceptance_readings", "median_tok_s", "spread_pct_over_median", "spread_pct_over_min",
          "acceptance_adjusted_spread_pct_over_median", "is_true_repetition_group", "evidence"],
         grows, [A["tsweep_q4"], A["tsweep_q5"], A["tsweep_q6k"], A["tsweep_q6kxl"]],
         "PN-19, PN-36, PN-45",
         "spread_pct_over_median is PN-19's estimator (PN-45's corrected column); over_min is PN-36's")


def fig22():
    """Decode and prefill against filled context depth, at ONE protocol (S9d/S9e)."""
    rows = []
    for key in ("s9d", "s9e"):
        d = load_json(key)
        for c in d["cells"]:
            if not c.get("valid"):
                continue
            rows.append([f"UD-{c['arm']}", c["ctx"], c["n_draft"], c["ts"], c["prompt_n"],
                         c["prefill_frac"], round(c["decode_tok_s_median"], 3),
                         round(c["prefill_tok_s"], 1), c["acceptance"], c["decode_spread_pct"],
                         len(c["reps"]), 32,
                         "DEC-2 official non-thinking, /completion + continuation cue, 512 tokens",
                         "measured"])
    # depth-0 reference points, explicitly at a DIFFERENT protocol
    s8 = load_json("s8_humaneval")
    for c in s8["configs"]:
        if not c["ok"] or c["config"] == "dflash4":
            continue
        nd = {"nospec": 0, "mtp2": 2, "mtp4": 4}[c["config"]]
        rows.append(["UD-Q6_K", 32768, nd, "58,42", "", "", round(c["decode_tok_s_median"], 3),
                     "", c.get("acceptance") or "", "", 164, 32,
                     "REFERENCE ONLY — greedy temp 0, HumanEval+ prompts, near-empty KV cache; "
                     "not comparable to the rows above", "measured"])
    emit("F22", "fig22-depth-decode.csv",
         ["arm", "ctx_tokens", "n_draft", "tensor_split", "prompt_n_tokens", "prefill_frac",
          "decode_tok_s_median", "prefill_tok_s", "acceptance", "decode_spread_pct",
          "n_reps_or_problems", "ctxcp", "protocol", "evidence"],
         rows, [A["s9d"], A["s9e"], A["s8_humaneval"]],
         "PN-32, PN-24 (at-depth half withdrawn by PN-30), PN-30",
         "the at-depth rows share one protocol; the ctx-32,768 rows are a different protocol and are labelled so")


# --------------------------------------------------------------------------------------
# F15 / F16 / F17 — the historical corpus
# --------------------------------------------------------------------------------------

def fig15():
    led = load_json("ledger")
    rows = []
    ladder = [("Q3_K_XL", "UD-Q3_K_XL"), ("IQ4fix", "UD-IQ4_XS"), ("Q5_K_XL", "UD-Q5_K_XL"),
              ("Q6Kfix", "UD-Q6_K_XL")]
    for key, arm in ladder:
        v = led["humaneval_nonthinking"][key]
        n = v["n"]
        rows.append(["non-thinking (greedy)", arm, "none", v["base"], v["plus"],
                     *wilson(round(v["plus"] * n / 100), n), v["empty"]["pct"], n,
                     "Wilson 95 % on the plus metric", key, "historical"])
    for key, label in [("deep-32768", "UD-Q6_K_XL @ ctx 32,768"),
                       ("deep-131072", "UD-Q6_K_XL @ ctx 131,072")]:
        v = led["humaneval_nonthinking"][key]
        n = v["n"]
        rows.append(["non-thinking, context control", label, "none", v["base"], v["plus"],
                     *wilson(round(v["plus"] * n / 100), n), v["empty"]["pct"], n,
                     "Wilson 95 % on the plus metric", key, "historical"])
    thinking = [("UD-IQ4_XS", "MTP", 86.6, 86.0, 12.8), ("UD-Q4_K_XL", "MTP", 87.8, 86.0, 12.2),
                ("UD-Q5_K_XL", "MTP", 89.0, 86.0, 11.0), ("UD-Q6_K_XL", "MTP", 90.9, 88.4, 7.9),
                ("UD-IQ4_XS", "DFlash2", 89.0, 87.8, 10.4), ("UD-Q4_K_XL", "DFlash2", 90.2, 87.2, 8.5),
                ("vLLM NVFP4", "none", 85.4, 84.1, 12.8)]
    for arm, spec, base, plus, empty in thinking:
        rows.append(["thinking (greedy, max_tokens 4096)", arm, spec, base, plus,
                     *wilson(round(plus * 164 / 100), 164), empty, 164,
                     "Wilson 95 % on the plus metric",
                     "multivac-CLAUDE.md completed table (ledger row incomplete)", "historical"])
    # the excluded rows, retained and labelled
    v = led["humaneval_nonthinking"]["Q6_K"]
    rows.append(["EXCLUDED — dirty run", "UD-Q6_K_XL (old)", "none", v["base"], v["plus"], "", "",
                 v["empty"]["pct"], v["n"], "not scored — on the exclusion list", "Q6_K", "historical"])
    emit("F15", "fig15-humaneval-ladders.csv",
         ["mode", "arm", "spec_method", "humaneval_pass1", "humaneval_plus_pass1",
          "plus_wilson_lo", "plus_wilson_hi", "empty_response_pct", "n_problems",
          "estimator", "ledger_key", "reproducibility"],
         rows, [A["ledger"], "data/multivac-src/multivac-CLAUDE.md (thinking table)"],
         "PN-46, PN-47", "all rows pre-2026-08-29: irreproducible-on-current-images (PN-57)")


def fig16():
    rows = [
        ["UD-IQ4_XS", 38, 49, round(100 * 38 / 49, 1), *wilson(38, 49), "final (x86_64-corrected)",
         "per-instance report.json via swebench_agg.py", "historical"],
        ["UD-Q5_K_XL", 38, 50, round(100 * 38 / 50, 1), *wilson(38, 50), "final (x86_64-corrected)",
         "per-instance report.json via swebench_agg.py", "historical"],
        ["UD-Q6_K", 37, 49, round(100 * 37 / 49, 1), *wilson(37, 49), "final (x86_64-corrected)",
         "per-instance manifest, 49 unique instances", "historical"],
    ]
    led = load_json("ledger")["swebench"]
    rows += [
        ["UD-IQ4_XS", int(led["iq4_xs-verified50"]["resolved"]), int(led["iq4_xs-verified50"]["completed"]),
         round(100 * int(led["iq4_xs-verified50"]["resolved"]) / int(led["iq4_xs-verified50"]["completed"]), 1),
         "", "", "superseded generation 1 (ARM64-scored)", "ledger-data.json swebench", "historical"],
        ["UD-Q5_K_XL", int(led["q5_k_xl-verified50"]["resolved"]), int(led["q5_k_xl-verified50"]["completed"]),
         round(100 * int(led["q5_k_xl-verified50"]["resolved"]) / int(led["q5_k_xl-verified50"]["completed"]), 1),
         "", "", "superseded generation 1 (ARM64-scored)", "ledger-data.json swebench", "historical"],
        ["UD-IQ4_XS", 37, 49, round(100 * 37 / 49, 1), "", "", "superseded generation 2 (§13.66)",
         "multivac-CLAUDE.md", "historical"],
        ["UD-Q5_K_XL", 37, 50, 74.0, "", "", "superseded generation 2 (§13.66)",
         "multivac-CLAUDE.md", "historical"],
    ]
    rows.append(["UD-Q6_K (bootstrap)", 37, 49, 75.51, 63.27, 87.76,
                 "bootstrap B=10,000, seed 20260825", "bootstrap-ci.json (host)", "historical"])
    emit("F16", "fig16-swebench-verified.csv",
         ["arm", "resolved", "instances_scored", "resolve_rate_pct", "ci_lo", "ci_hi",
          "generation", "source", "reproducibility"],
         rows, [A["ledger"], "data/multivac-src/multivac-CLAUDE.md §SWE-bench"],
         "PN-50, PN-58",
         "denominators differ across arms, so the rates are NOT over a common instance set; the ordering carries no information")


def fig17():
    led = load_json("ledger")
    q3 = led["humaneval_nonthinking"]["Q3_K_XL"]
    q6 = led["humaneval_nonthinking"]["Q6Kfix"]
    rows = [
        ["peak decode throughput (MTP n=8, ctx 32,768)", "tok/s", 116.9, "", "UD-Q3_K_XL leads",
         "historical", "n8-ctx-ceiling-20260822-0938 (host)", "cheap instrument"],
        ["decode throughput @262,144", "tok/s", 54.64, "", "UD-Q3_K_XL leads", "historical",
         "quant x context matrix (host)", "cheap instrument"],
        ["HumanEval pass@1 (non-thinking, greedy)", "%", q3["base"], q6["base"],
         "acceptable, 6.1 pts below the reference", "historical", "ledger-data.json", "cheap instrument"],
        ["HumanEval+ pass@1 (non-thinking, greedy)", "%", q3["plus"], q6["plus"],
         "acceptable, 9.8 pts below the reference", "historical", "ledger-data.json", "cheap instrument"],
        ["empty responses", "%", q3["empty"]["pct"], q6["empty"]["pct"], "clean run",
         "historical", "ledger-data.json", "cheap instrument"],
        ["WikiText-2 perplexity, Protocol 2 (20 chunks @ c4096)", "PPL", 5.55, 5.51,
         "essentially tied with the reference", "historical", "ppl-allquants-20260821-2213 (host)",
         "cheap instrument"],
        ["draft acceptance at 258,779 attended tokens", "ratio", 1.0, "",
         "WITHDRAWN by PN-61: 55 generated tokens over 36 draft events, a degenerate probe",
         "historical", "champion-timings.json", "withdrawn"],
        ["agentic instances converged (SWE-bench-style, 250-step limit)", "of 6", 0, 6,
         "0 of 6 converged; mean 250 steps, median 250, max 250", "historical",
         "rigor/T3-INTERROMPIDO.txt (host)", "expensive instrument"],
        ["mean steps to convergence", "steps", 250, 45,
         "hit the harness limit on every instance", "historical",
         "rigor/T3-INTERROMPIDO.txt (host)", "expensive instrument"],
    ]
    emit("F17", "fig17-q3-profile.csv",
         ["instrument", "unit", "q3_k_xl_value", "reference_value", "verdict_for_q3",
          "reproducibility", "source", "instrument_class"],
         rows, [A["ledger"], A["champion"], "data/multivac-src/PAPER-REFERENCES.md §T3"],
         "PN-51, PN-61, PN-46",
         "every cheap instrument rates UD-Q3_K_XL well or best; only the expensive multi-step one rates it correctly")


def fig17b():
    rows = [
        ["astropy__astropy-12907", 25, 32, "", "250 (limit)"],
        ["django__django-10880", 19, 32, "", "250 (limit)"],
        ["django__django-10973", 25, 23, "", "250 (limit)"],
        ["mean (n=3 instances)", 23, 29, "~45 (n=6, different instance set)", "250"],
    ]
    emit("F17b", "fig17b-agentic-steps.csv",
         ["instance", "UD-IQ4_XS_steps", "UD-Q5_K_XL_steps", "UD-Q6_K_XL_steps", "UD-Q3_K_XL_steps"],
         rows, ["data/multivac-src/PAPER-REFERENCES.md §Agentic steps COMPLETE (2026-08-28)"],
         "PN-52, PN-51",
         "n=3 instances; the Q6_K_XL column is an approximate mean carried from a different run and instance set")


def fig18():
    led = load_json("ledger")["speed"]
    rows = []
    spec = {
        "NOSPEC": ("vLLM NVFP4 (nightly)", "no-spec", None, None, 51200),
        "MTP2_clean": ("vLLM NVFP4 (nightly)", "MTP n=2", 0.709, None, 49152),
        "MTP4_clean": ("vLLM NVFP4 (nightly)", "MTP n=4", 0.559, None, 49152),
        "llamacpp_nospec": ("llama.cpp UD-Q4_K_XL", "no-spec", None, None, 262144),
        "llamacpp_mtp_n2": ("llama.cpp UD-Q4_K_XL", "MTP n=2", 0.728, 2.46, 262144),
        "llamacpp_dflash2_n4": ("llama.cpp UD-Q4_K_XL", "DFlash2 n=4", 0.714, 3.86, 262144),
    }
    baselines = {"vLLM NVFP4 (nightly)": led["NOSPEC"]["decode_tok_s"],
                 "llama.cpp UD-Q4_K_XL": led["llamacpp_nospec"]["decode_tok_s"]}
    for key, (backend, cfg, acc, mlen, ceiling) in spec.items():
        v = led[key]
        rows.append([backend, cfg, v["decode_tok_s"], round(v["decode_tok_s"] / baselines[backend], 2),
                     acc if acc is not None else "", mlen if mlen is not None else "",
                     v["ttft_s"], v["avg_power_w"], v["peak_vram_mib"], v["j_per_tok"],
                     v["n_runs"], ceiling, "measured (speed) / modelled (power, J/tok)", "historical"])
    rows.append(["vLLM NVFP4 (nightly)", "DFlash2", "", "", "", "", "", "", "", "", 0, 51200,
                 "INFEASIBLE — OOM 'Tried to allocate 1.19 GiB' at every utilisation 0.78-0.97", "historical"])
    rows.append(["SGLang 0.5.18", "EAGLE", "", "", "", "", "", "", "", "", 0, "",
                 "NEVER STARTED — OOM 1.19 GiB at EagleDraftWorker init, at 16K/32K/64K/131K", "historical"])
    emit("F18", "fig18-cross-backend.csv",
         ["backend", "config", "decode_tok_s_median", "speedup_vs_own_nospec", "draft_acceptance",
          "mean_accepted_len", "ttft_s", "avg_power_w", "peak_vram_mib", "j_per_token",
          "n_runs", "context_ceiling_tokens", "evidence", "reproducibility"],
         rows, [A["ledger"], A["specspeed"],
                "data/multivac-src/PAPER-REFERENCES.md §CROSS-BACKEND SPEED TABLE"],
         "PN-53, PN-54, PN-55, PN-56",
         "different quantizations on different engines: backend, quantization, KV dtype and spec method all vary at once; "
         "depth-0 decode into a near-empty KV cache; power is modelled, not wall-socket measured")


# --------------------------------------------------------------------------------------
# F19 — what the measurements cost
# --------------------------------------------------------------------------------------

def fig19():
    ssa = load_json("ssa_parsed")
    s5 = load_json("ssa_s5")
    s7 = load_json("ssa_s7")
    ruler = load_json("ruler")
    s6 = load_json("s9_s6")
    s8 = load_json("s8_humaneval")
    det = load_json("s9_determinism")
    dfl = load_json("s9_dflash")

    def total(cells, field="seconds"):
        return sum(c.get(field) or 0 for c in cells)

    rows = [
        ["divergence", "SSA S0-S4: KL divergence, prose + code, 4 arms",
         round(total(ssa["cells"]) / 3600, 2), len(ssa["cells"]), 65536, "tokens per cell",
         "separated all three arms at 3.7-11.8 sigma, non-overlapping intervals", "measured"],
        ["divergence", "SSA S5: KL divergence over HumanEval+ task prompts",
         round(total(s5["cells"]) / 3600, 2), len(s5["cells"]), 18432, "tokens per cell",
         "third domain tier; no arm passes the <0.007 band on the task distribution", "measured"],
        ["task benchmark", "SSA S7: HellaSwag n=400, 4 arms",
         round(total(s7["cells"]) / 3600, 2), len(s7["cells"]), 400, "items per arm",
         "1.0-point spread; two arms answered all 400 identically", "measured"],
        ["task benchmark", "SSA S6 / S9b: generative HumanEval+, paired, 2 arms",
         round(total(s6["runs"]) / 3600, 2), len(s6["runs"]), 164, "problems per arm",
         "paired difference -0.61 pts, 95 % CI [-3.28, +2.06]", "measured"],
        ["task benchmark", "S12 RULER: S-NIAH + MK-NIAH (12 cells incl. n=100 at 131,072)",
         round(total(ruler["cells"]) / 3600, 2), len(ruler["cells"]), "8192-131072", "context tokens",
         "S-NIAH saturated; MK-NIAH separated on output budget, not retrieval (PN-60)", "measured"],
        ["task benchmark", "S12 RULER: variable_tracking cells, excluded",
         round(total(ruler["variable_tracking_excluded_cells"]) / 3600, 2),
         len(ruler["variable_tracking_excluded_cells"]), 25, "items per arm",
         "excluded for an output-format artifact; 0 items fully correct in either arm", "measured"],
        ["equivalence", "S8: speculative equivalence + speed at ctx 32,768",
         round(total(s8["configs"]) / 3600, 2), len([c for c in s8["configs"] if c["ok"]]), 164,
         "problems per arm", "MTP is not output-identical: 131/164 byte-exact", "measured"],
        ["equivalence", "S9a: determinism control (re-run of two S8 arms)",
         round(total(det["runs"]) / 3600, 2), len(det["runs"]), 164, "problems per arm",
         "both arms reproduced themselves byte-exactly: the divergence is deterministic", "measured"],
        ["equivalence", "S9c: DFlash2 on its own engine build",
         round(total(dfl["runs"]) / 3600, 2), len(dfl["runs"]), 164, "problems",
         "fastest at 32 K, cannot reach the deployment window", "measured"],
    ]
    div = sum(r[2] for r in rows if r[0] == "divergence")
    task = sum(r[2] for r in rows if r[0] == "task benchmark")
    equiv = sum(r[2] for r in rows if r[0] == "equivalence")
    rows.append(["TOTAL divergence", "", round(div, 2), "", "", "",
                 "ranked the ladder", "measured"])
    rows.append(["TOTAL task benchmark", "", round(task, 2), "", "", "",
                 "bounded the effect; resolved nothing on its intended construct", "measured"])
    rows.append(["TOTAL equivalence", "", round(equiv, 2), "", "", "",
                 "retired the losslessness premise the study had carried for nine days", "measured"])
    emit("F19", "fig19-cost.csv",
         ["class", "experiment", "gpu_hours", "cells", "sample_size", "sample_unit",
          "what_it_resolved", "evidence"],
         rows, [A["ssa_parsed"], A["ssa_s5"], A["ssa_s7"], A["s9_s6"], A["ruler"],
                A["s8_humaneval"], A["s9_determinism"], A["s9_dflash"]],
         "PN-41",
         "summed from each artifact's own per-cell `seconds`; PN-41's 4.8 h for task benchmarking predates the n=100 MK-NIAH cell")


# --------------------------------------------------------------------------------------
# F20 — the correction record
# --------------------------------------------------------------------------------------

def fig20():
    rows = [
        ["2026-08-30", "PN-23", "9 days of prior notes", "speculative decoding is greedy-lossless",
         "MTP reproduces the baseline on 131/164 problems", "1 experiment (S8, ~1.3 h)",
         "first experiment that tested the premise", "premise refuted"],
        ["2026-08-31", "PN-26", "PN-23's mechanism", "float nondeterminism from batch shape",
         "both arms are individually deterministic; speculation is a different decode path",
         "1 control run (~1.0 h)", "planned control", "mechanism narrowed"],
        ["2026-09-01", "PN-30", "PN-24 at-depth, S8 at-depth",
         "MTP n=4 leads n=2 by 46 % at 262,144 and the margin grows with depth",
         "withdrawn: every rep generated 17 tokens", "0 (re-read of the artifact)",
         "author re-reading a serverlog", "claim withdrawn"],
        ["2026-09-02", "PN-36", "PN-19", "within-arm repetition noise reaches 32.9 %",
         "the n=6 group spanned four context depths", "0 (regrouped from cell keys)",
         "two independent blind reviews", "numbers corrected"],
        ["2026-09-02", "PN-37", "PN-34", "benchmark insensitivity is explained by saturation",
         "saturation is false for two of three instruments; the framing is Dutta et al. 2024",
         "0", "review", "mechanism retracted"],
        ["2026-09-02", "PN-39", "PN-6", "the ceiling is a property of the split, not the quant",
         "holds for 2 of 4 arms; the smallest arm loads at the engine default", "0",
         "review", "claim scoped"],
        ["2026-09-02", "PN-40", "PN-28", "McNemar p = 1.0 shows the arms are indistinguishable",
         "that test could not have reached p<0.05: min attainable p = 0.25",
         "0", "adversarial review", "null converted to a bound"],
        ["2026-09-02", "PN-41", "the project's cost contrast", "20 minutes vs 20 hours",
         "2.15 h vs 4.8 h, recomputed from timestamps", "0", "review", "headline ratio corrected"],
        ["2026-09-02", "PN-42", "PN-8", "balance and throughput are opposing objectives",
         "the most balanced ratio is the slowest; the rest cluster within 3.6 %", "0",
         "review", "framing corrected"],
        ["2026-09-02", "PN-43", "PN-15", "the reparsed block is the repaired one everywhere",
         "a label collision overwrote one serverlog; trust `metrics` for those two cells", "0",
         "adversarial review", "artifact annotated"],
        ["2026-09-03", "PN-45", "PN-36 (itself a correction)",
         "within-configuration spread 46.7 %", "estimator was switched silently; 40.7 % under PN-19's rule",
         "0", "archivist re-verification", "correction corrected"],
        ["2026-09-03", "PN-60", "PN-44", "4-bit costs 10 points of retrieval accuracy at 131,072",
         "every failure is a truncation; the separated effect is reasoning-block closure", "0",
         "adversarial review", "headline restated"],
        ["2026-09-03", "PN-61", "PN-51's acceptance clause",
         "1.000 draft acceptance at 258,779 attended tokens",
         "degenerate: 50-55 tokens over 34-36 draft events", "0", "review", "clause struck"],
        ["2026-09-03", "PN-62", "PN-35", "the tail structure is something quantization does",
         "shape is a corpus property; magnitude is the quantization property", "0",
         "adversarial review (using this study's own KV control)", "claim scoped"],
        ["2026-09-03", "PN-63", "PN-60", "the long-context result is confounded",
         "single-needle at the same depth is genuinely saturated; the defect is task difficulty",
         "0", "integrity audit", "correction narrowed"],
        ["2026-09-03", "PN-64", "PN-35's median row", "code is perturbed 100-200x less at the median",
         "about 200x; the per-arm ordering is an artifact of print precision", "0",
         "verification pass", "precision withdrawn"],
    ]
    emit("F20", "fig20-correction-record.csv",
         ["date", "note", "corrects", "claim_before", "claim_after", "gpu_cost_to_correct",
          "found_by", "outcome"],
         rows, [os.path.join(REPO, "docs/paper/PAPER-NOTES.md")],
         "PN-23, PN-26, PN-30, PN-36, PN-37, PN-39, PN-40, PN-41, PN-42, PN-43, PN-45, PN-60, PN-61, PN-62, PN-63, PN-64",
         "fourteen of the sixteen corrections cost zero GPU time because per-item records were retained")


def fig23():
    gen = load_json("s11_gen")
    arms = ["Q6_K_XL", "Q6_K", "Q5_K_XL", "Q4_K_XL"]
    ladder_pos = {a: i for i, a in enumerate(arms)}
    pads = sorted(gen[arms[0]].keys())
    rows = []
    for i in range(len(arms)):
        for j in range(i + 1, len(arms)):
            a, b = arms[i], arms[j]
            for p in pads:
                x, y = gen[a][p], gen[b][p]
                d = levenshtein(x, y) / max(len(x), len(y))
                rows.append([f"UD-{a} / UD-{b}", abs(ladder_pos[a] - ladder_pos[b]), int(p),
                             len(x), len(y), round(d, 4), first_diff_char(x, y), "recomputed"])
    emit("F23", "fig23-generation-saturation.csv",
         ["pair", "ladder_distance_steps", "prompt_index", "len_a_chars", "len_b_chars",
          "normalised_edit_distance", "first_divergence_char", "evidence"],
         rows, [A["s11_gen"], A["s11"]], "PN-38",
         "estimator: character-level Levenshtein divided by the longer string; PN-38's own values are not "
         "reproducible under this or three other normalisations, but its conclusion is")


def fig27():
    cells = kld_cells()
    ssa = {c["label"]: c for c in load_json("ssa_parsed")["cells"]}
    ctl = cells["ssa-Q6_K_XL-code-kld-e2"]
    rows = [["q4_0 KV cache vs f16 KV cache (weights identical)", "kv_dtype", ctl["kld_mean"],
             ctl["kld_mean_err"], ctl["same_top_p"], ctl["kld_p99"], 65536, "measured"]]
    for arm in ARMS_QUANT:
        c = cells[f"ssa-{arm}-code-kld"]
        rows.append([f"UD-{arm} vs UD-Q6_K_XL (KV dtype identical)", "weights", c["kld_mean"],
                     c["kld_mean_err"], c["same_top_p"], c["kld_p99"], 65536, "measured"])
    emit("F27", "fig27-kv-quantization.csv",
         ["perturbation", "perturbation_class", "mean_kld_nats", "mean_kld_se_nats",
          "top1_agreement_pct", "kld_p99_nats", "n_tokens", "evidence"],
         rows, [A["ssa_tables"]], "PN-15, PN-43, PN-62",
         "sizes are comparable because all four are KL from the same reference on the same corpus; "
         "they are NOT additive and no experiment applies both perturbations together")

    # PN-43: TWO cells share the label 'ssa-Q6_K_XL-code-base'. Indexing this artifact by label
    # silently returns whichever came last (the f16 run) — which is exactly the failure the note
    # documents. Select on (label, kv) instead.
    base_cells = [c for c in load_json("ssa_parsed")["cells"]
                  if c["label"] == "ssa-Q6_K_XL-code-base"]
    assert len(base_cells) == 2, "expected the PN-43 label collision: two cells share this label"
    c_q4 = next(c for c in base_cells if c["kv"] == "q4_0")
    c_f16 = next(c for c in base_cells if c["kv"] == "f16")
    ppl_q4 = c_q4["metrics"]["ppl"]            # run-time field: the only uncorrupted value here
    ppl_f16 = c_f16["metrics_reparsed"]["ppl"]
    rows2 = [
        ["f16 KV", ppl_f16, c_f16["metrics_reparsed"]["ppl_err"],
         "metrics_reparsed — this cell's own serverlog survived the collision", "measured"],
        ["q4_0 KV", ppl_q4, c_q4["metrics"]["ppl_err"],
         "metrics (run-time) — this cell's metrics_reparsed is CORRUPTED by the label collision "
         "and reads the f16 value (PN-43)", "measured"],
        ["change", round(100 * (ppl_q4 / ppl_f16 - 1), 3), "", "percent", "recomputed"],
        ["q4_0 KV, as metrics_reparsed WOULD report it", c_q4["metrics_reparsed"]["ppl"], "",
         "DO NOT USE — the corrupted field, shown so the defect is visible in the record", "measured"],
    ]
    emit("F27b", "fig27b-kv-ppl-contrast.csv",
         ["cell", "perplexity_or_change_pct", "standard_error", "which_field", "evidence"],
         rows2, [A["ssa_parsed"]], "PN-15, PN-43",
         "the same perturbation that moves KL divergence by 0.002955 moves perplexity by +0.15 %")


# --------------------------------------------------------------------------------------
# setup / reference tables emitted as data too
# --------------------------------------------------------------------------------------

def fig21_setup():
    env = load_json("env")
    rows = []
    role = {
        "Qwen3.8-27B-UD-Q6_K_XL.gguf": ("UD-Q6_K_XL", "divergence reference arm"),
        "Qwen3.8-27B-UD-Q6_K.gguf": ("UD-Q6_K", "arm"),
        "Qwen3.8-27B-UD-Q5_K_XL.gguf": ("UD-Q5_K_XL", "arm"),
        "Qwen3.8-27B-UD-Q4_K_XL.gguf": ("UD-Q4_K_XL", "arm"),
        "Qwen3.8-27B-UD-IQ4_XS.gguf": ("UD-IQ4_XS", "historical corpus only"),
        "Qwen3.8-27B-DFlash2-Q4_K_M.gguf": ("DFlash2 drafter", "speculative drafter sidecar"),
    }
    for m in env["gguf_models"]:
        base = os.path.basename(m["file"])
        arm, r = role.get(base, (base, ""))
        rows.append([arm, r, base, m["bytes"], round(m["bytes"] / 2**30, 2), m["sha256"], "measured"])
    emit("T1", "fig21-arms-manifest.csv",
         ["arm", "role", "file", "bytes", "gib", "sha256", "evidence"],
         rows, [A["env"]], "PN-57, PN-13",
         "byte counts and hashes are the identity of record; two of these files have since been deleted and are recoverable by hash")


def fig21_sampling():
    rows = [
        ["measured engine default", 1.0, 0.95, 20, 0.05, 0.0,
         "no explicit sampling block sent", "PN-1",
         "matches neither the documented engine defaults nor either official preset", "measured"],
        ["documented llama.cpp launch default", 0.80, 0.95, 40, 0.05, 0.0,
         "upstream documentation", "PN-1", "not what the server actually ran", "cited"],
        ["Qwen official non-thinking (DEC-2)", 0.7, 0.80, 20, 0.0, 1.5,
         "task benchmarks: Wave 1, SSA S6, S9d/S9e", "PN-16, DEC-2",
         "the preset the model card publishes for instruct use", "cited"],
        ["Qwen official thinking", 1.0, 0.95, 20, 0.0, 0.0,
         "not used for any measurement here", "PN-16", "listed for completeness", "cited"],
        ["greedy", 0.0, 1.0, "", "", 0.0,
         "logprob and equivalence instruments: SSA divergence, S7, S8, S9a/S9c, S11, S12",
         "PN-23, PN-26", "required for byte-exact comparison; not comparable to published scores", "measured"],
        ["greedy with reasoning enabled", 0.0, 1.0, "", "", 0.0,
         "S12 RULER only", "PN-60, PN-63",
         "a fourth configuration; the 128-token budget then bounds the answer (PN-60)", "measured"],
    ]
    emit("T2", "fig21b-sampling-configurations.csv",
         ["configuration", "temperature", "top_p", "top_k", "min_p", "presence_penalty",
          "used_for", "paper_notes", "note", "evidence"],
         rows, [A["env"], os.path.join(REPO, "docs/paper/PAPER-NOTES.md")],
         "PN-1, PN-2, PN-3, PN-16",
         "four distinct sampling configurations were used across the study; absolute scores are not comparable across them")


def fig19b_energy():
    rows = [
        ["12-hour host window (26 % GPU-busy)", "mean system power", 149.2, "W", "modelled",
         "GPU telemetry + RAPL package + fixed platform allowance; no wall-socket sensor"],
        ["12-hour host window", "median system power", 79.8, "W", "modelled", ""],
        ["12-hour host window", "peak system power", 408.9, "W", "modelled", ""],
        ["12-hour host window", "mean system power under GPU load", 334.1, "W", "modelled", ""],
        ["12-hour host window", "energy consumed", 1.791, "kWh", "modelled", ""],
        ["12-hour host window", "of which the two GPUs", 1.078, "kWh", "measured (nvidia-smi 1 Hz)", ""],
        ["12-hour host window", "of which the CPU package", 0.172, "kWh", "measured (RAPL)", ""],
        ["12-hour host window", "GPU0 mean / peak temperature", 90.0, "C peak", "measured",
         "GPU1 peaked at 76 C on physically identical cards; observational and confounded (PN-12)"],
    ]
    emit("T22", "fig19b-energy-envelope.csv",
         ["window", "quantity", "value", "unit", "evidence", "note"],
         rows, ["/srv/bench/power-log.csv (host, 43,182 samples, gitignored)"],
         "PN-11, PN-12",
         "host-level only: no per-configuration J/tok figure exists for the E12 arms (DEC-12 cancelled Wave 4)")


# --------------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------------

FIGURES = [
    ("F1", fig01), ("F1b", fig01b), ("F2", fig02), ("F3", fig03), ("F28", fig28), ("F4", fig04), ("F4b", fig04b), ("T11", fig04c),
    ("F5", fig05), ("F6", fig06), ("F7", fig07), ("F8", fig08), ("F9", fig09),
    ("F9b", fig09b), ("F10", fig10), ("F11", fig11), ("F12", fig12), ("F13", fig13),
    ("F14", fig14), ("F15", fig15), ("F16", fig16), ("F17", fig17), ("F17b", fig17b),
    ("F18", fig18), ("F19", fig19), ("F20", fig20), ("F22", fig22), ("F23", fig23),
    ("F24", fig24), ("F26", fig26), ("F27", fig27), ("T1", fig21_setup),
    ("T2", fig21_sampling), ("T22", fig19b_energy),
]

CHECK_ONLY = False
CHECK_FAILURES: list[str] = []


def main() -> int:
    global CHECK_ONLY
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="verify the committed data files match the artifacts")
    ap.add_argument("--list", action="store_true", help="list figure ids and exit")
    args = ap.parse_args()
    if args.list:
        for fid, fn in FIGURES:
            print(f"{fid:6s} {fn.__name__}")
        return 0
    CHECK_ONLY = args.check

    missing = [k for k, p in A.items() if not os.path.exists(p)]
    if missing:
        print("FATAL: missing artifacts:", file=sys.stderr)
        for k in missing:
            print(f"  {k}: {A[k]}", file=sys.stderr)
        return 2

    print(f"repo:   {REPO}")
    print(f"output: {OUT}")
    print(f"mode:   {'check' if CHECK_ONLY else 'write'}\n")
    for fid, fn in FIGURES:
        fn()

    # index
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["figure_id", "data_file", "rows", "sha256_16", "paper_notes", "source_artifacts", "note"])
    for r in INDEX_ROWS:
        w.writerow([r["figure_id"], r["data_file"], r["rows"], r["sha256_16"], r["paper_notes"],
                    r["source_artifacts"].replace(REPO + os.sep, ""), r["note"]])
    idx_path = os.path.join(OUT, "INDEX.csv")
    if CHECK_ONLY:
        old = open(idx_path, encoding="utf-8").read() if os.path.exists(idx_path) else None
        ok = old == buf.getvalue()
        print(f"\n  [{'OK  ' if ok else 'DIFF'}] INDEX.csv")
        if not ok:
            CHECK_FAILURES.append("INDEX.csv")
    else:
        with open(idx_path, "w", encoding="utf-8") as fh:
            fh.write(buf.getvalue())
        print(f"\n  wrote {'INDEX.csv':38s} {len(INDEX_ROWS):5d} rows")

    print(f"\n{len(WRITTEN)} data files, {sum(n for _, n, _ in WRITTEN)} rows total")
    if CHECK_ONLY and CHECK_FAILURES:
        print(f"CHECK FAILED for {len(CHECK_FAILURES)} file(s): {', '.join(CHECK_FAILURES)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
