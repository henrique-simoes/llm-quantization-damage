#!/usr/bin/env python3
"""ssa_kld.py -- Small-Sample Accuracy protocol (SSA), steps S0-S4.

Runs `llama-perplexity` inside llamacpp-mtp:latest to produce, per arm per domain:
mean KL divergence + uncertainty, top-1 agreement, dp percentiles, RMS dp, PPL, PPL ratio.

Design and sources: docs/build-stream/2026-08-30-quant-bench-trackA.md (SSA section)
and docs/paper/METHOD-REFERENCES.md (R1-R7).

Reference arm is Q6_K_XL (least-quantized available; no FP16 on the host), so every
divergence figure is LADDER-RELATIVE and every artifact records that in `reference`.

Hard rules inherited from Wave 1:
  * logs are written to disk BEFORE any container is removed (never lose evidence)
  * flock single-instance, so this can never race the Wave-1 runner
  * refuses to start while a GPU experiment is running
  * every artifact carries source / run_ids / image id / seed / sampling / n
"""
import argparse, json, os, re, subprocess, sys, time, hashlib, shutil

E12    = "/srv/bench/e12"
SSA    = f"{E12}/ssa"
LOGS   = "/srv/bench/server-timings"
IMAGE  = "llamacpp-mtp:latest"
CONT   = "ssa-perplexity"
SEED   = 20260830

# Wave-1 configuration held constant across arms. At n_ctx 2048 VRAM pressure is
# negligible, so the DEFAULT split is used for every arm: using each arm's own
# Wave-1 winning ratio would introduce an uncontrolled variable into an accuracy
# comparison for no benefit. Recorded in the artifact so this is auditable.
ARMS = {
    "Q6_K_XL": "/models/Qwen3.8-27B-UD-Q6_K_XL.gguf",     # reference arm
    "Q6_K":    "/models2/Qwen3.8-27B-UD-Q6_K.gguf",
    "Q5_K_XL": "/models/Qwen3.8-27B-UD-Q5_K_XL.gguf",
    "Q4_K_XL": "/models/Qwen3.8-27B-UD-Q4_K_XL.gguf",
}
REFERENCE = "Q6_K_XL"

DOMAINS = {
    # D1: the published convention (llama.cpp / Unsloth), for comparability
    "wikitext2": "/corpus/wikitext2-test.txt",
    # D2: the target workload. Published quant tables measure prose; this measures code.
    "code":      "/e12/corpus.txt",
}

def log(*a):
    print(f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}]", *a, flush=True)

def gpu_busy():
    """Refuse to run while any other GPU experiment holds the box."""
    r = subprocess.run(["pgrep", "-f", "tsweep_v2.py|runner_wave1.sh sweep|llamasrv-e12"],
                       capture_output=True, text=True)
    return r.returncode == 0 and r.stdout.strip() != ""

def image_id():
    r = subprocess.run(["docker", "inspect", "-f", "{{.Id}}", IMAGE],
                       capture_output=True, text=True)
    return r.stdout.strip()

def run_perplexity(arm, domain, n_ctx, chunks, kv, base_file=None, mode="ppl",
                   extra=None, tag=""):
    """One llama-perplexity invocation. mode: 'base' (record logits) | 'kld' | 'ppl'."""
    label = f"ssa-{arm}-{domain}-{mode}{('-' + tag) if tag else ''}"
    serverlog = f"{LOGS}/{label}.serverlog"
    cmd = ["docker", "run", "--rm", "--name", CONT, "--gpus", "all", "--network", "host",
           "-v", "/srv/models:/models:ro", "-v", "/srv/bench/models:/models2:ro",
           "-v", "/srv/bench/corpus:/corpus:ro", "-v", f"{E12}:/e12:ro",
           "-v", f"{SSA}:/ssa",
           "--entrypoint", "/app/llama-perplexity", IMAGE,
           "-m", ARMS[arm], "-f", DOMAINS[domain],
           "-c", str(n_ctx), "--chunks", str(chunks),
           "-ngl", "99", "-fa", "on",
           "-ctk", kv, "-ctv", kv, "-s", str(SEED)]
    if mode == "base":
        cmd += ["--kl-divergence-base", f"/ssa/{base_file}"]
    elif mode == "kld":
        cmd += ["--kl-divergence", "--kl-divergence-base", f"/ssa/{base_file}"]
    if extra:
        cmd += extra

    log(f"RUN {label}: {' '.join(cmd[cmd.index(IMAGE)+1:])}")
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True)
    out = (p.stdout or "") + "\n" + (p.stderr or "")
    # LOG FIRST, always -- hard rule 2. Written before anything else can fail.
    os.makedirs(LOGS, exist_ok=True)
    with open(serverlog, "w") as f:
        f.write(out)
    return {
        "label": label, "arm": arm, "domain": domain, "mode": mode, "kv": kv,
        "n_ctx": n_ctx, "chunks": chunks, "tokens": n_ctx * chunks,
        "rc": p.returncode, "seconds": round(time.time() - t0, 1),
        "serverlog": serverlog, "serverlog_bytes": len(out),
        "command": " ".join(cmd),
        "metrics": parse_metrics(out),
        "ok": p.returncode == 0,
    }

# llama-perplexity prints a block of statistics; capture them generously rather than
# assuming one exact format, so an engine-version change degrades to "field missing"
# instead of a silent wrong number.
PATTERNS = {
    "ppl":              r"(?:Final estimate:\s*)?PPL\s*=\s*([0-9.]+)\s*\+/-\s*([0-9.]+)",
    "mean_kld":         r"Mean KLD:\s*([0-9.eE+-]+)\s*\+/-\s*([0-9.eE+-]+)",
    "max_kld":          r"Maximum KLD:\s*([0-9.eE+-]+)",
    "median_kld":       r"Median KLD:\s*([0-9.eE+-]+)",
    "kld_99p":          r"99\.0%\s*KLD:\s*([0-9.eE+-]+)",
    "kld_95p":          r"95\.0%\s*KLD:\s*([0-9.eE+-]+)",
    "top1_agreement":   r"Same top p:\s*([0-9.]+)\s*%",
    "ppl_ratio":        r"PPL ratio:\s*([0-9.]+)\s*\+/-\s*([0-9.]+)",
    "mean_dp":          r"Mean Delta p:\s*([-0-9.]+)\s*\+/-\s*([0-9.]+)",
    "rms_dp":           r"RMS Delta p:\s*([0-9.]+)\s*\+/-\s*([0-9.]+)",
    "correlation":      r"Delta p correlation:\s*([0-9.]+)",
}

def parse_metrics(out):
    m = {}
    for key, pat in PATTERNS.items():
        hit = re.search(pat, out, re.IGNORECASE)
        if hit:
            g = hit.groups()
            m[key] = float(g[0])
            if len(g) > 1 and g[1] is not None:
                m[key + "_err"] = float(g[1])
    # keep the raw stats block so nothing is lost if a pattern misses
    blk = re.search(r"(Mean KLD.*?)(?:\n\n|\Z)", out, re.S)
    if blk:
        m["_raw_block"] = blk.group(1)[:2000]
    return m

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", required=True,
                    choices=["S0", "S1", "S2", "S3", "S4", "all"])
    ap.add_argument("--n-ctx", type=int, default=2048)
    ap.add_argument("--chunks", type=int, default=32)   # 32 x 2048 = 65,536 tokens
    ap.add_argument("--out", default=f"{SSA}/ssa-results.json")
    a = ap.parse_args()

    os.makedirs(SSA, exist_ok=True)
    lock = open(f"{E12}/state/ssa.lock", "w")
    try:
        import fcntl; fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        log("REFUSING: another SSA run holds the lock"); sys.exit(3)

    if gpu_busy():
        log("REFUSING: a GPU experiment is running (Wave-1 sweep or llamasrv-e12 up).")
        log("SSA must not race it -- wait for state/sweep.done, then re-run.")
        sys.exit(4)

    data = {"experiment": "ssa", "source": "e12-ssa", "run_ids": ["ssa-v1"],
            "protocol": "Small-Sample Accuracy (SSA), DEC-11",
            "reference_arm": REFERENCE,
            "reference_note": ("divergence is LADDER-RELATIVE: measured against the "
                               "least-quantized available arm, not FP16 (no FP16 on host; "
                               "a 27B F16 GGUF at ~54 GB exceeds free space)"),
            "split": "engine default (-ts unset): at n_ctx 2048 VRAM pressure is negligible "
                     "and a per-arm ratio would add an uncontrolled variable",
            "n_ctx": a.n_ctx, "chunks": a.chunks, "tokens_per_cell": a.n_ctx * a.chunks,
            "seed": SEED, "kv_default": "q4_0", "image_id": image_id(),
            "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "cells": []}
    if os.path.exists(a.out):
        data = json.load(open(a.out))           # resumable
        data["cells"] = data.get("cells", [])
    done = {(c["arm"], c["domain"], c["mode"], c["kv"]) for c in data["cells"] if c["ok"]}

    def cell(arm, domain, mode, kv="q4_0", base=None, extra=None, tag=""):
        key = (arm, domain, mode, kv)
        if key in done:
            log(f"skip existing {key}"); return
        c = run_perplexity(arm, domain, a.n_ctx, a.chunks, kv, base, mode, extra, tag)
        data["cells"].append(c)
        json.dump(data, open(a.out, "w"), indent=1)   # persist after every cell
        log(f"  -> ok={c['ok']} {json.dumps(c['metrics'])[:220]}")

    step = a.step
    # S0 -- smoke. 4 chunks end to end on the reference arm; asserts the KLD fields
    # actually populate on THIS engine build before spending the real budget.
    if step in ("S0",):
        log("S0 smoke: 4 chunks, reference arm, both domains")
        for d in DOMAINS:
            c = run_perplexity(REFERENCE, d, a.n_ctx, 4, "q4_0", f"smoke-{d}.kld", "base")
            data["cells"].append(c)
            log(f"  base rc={c['rc']} metrics={json.dumps(c['metrics'])[:200]}")
        json.dump(data, open(a.out, "w"), indent=1)

    if step in ("S1", "all"):
        for d in DOMAINS:
            cell(REFERENCE, d, "base", base=f"base-{d}.kld")
    if step in ("S2", "all"):
        for arm in ("Q6_K", "Q5_K_XL", "Q4_K_XL"):
            cell(arm, "wikitext2", "kld", base="base-wikitext2.kld")
    if step in ("S3", "all"):
        for arm in ("Q6_K", "Q5_K_XL", "Q4_K_XL"):
            cell(arm, "code", "kld", base="base-code.kld")
    if step in ("S4", "all"):
        # E2: KV fidelity. Same instrument, f16 vs q4_0, on the reference arm.
        # Everything this project has measured rests on q4_0 KV and nothing has checked it.
        cell(REFERENCE, "code", "base", kv="f16", base="base-code-f16.kld")
        cell(REFERENCE, "code", "kld", kv="q4_0", base="base-code-f16.kld", tag="e2")

    data["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    json.dump(data, open(a.out, "w"), indent=1)
    nok = sum(1 for c in data["cells"] if c["ok"])
    log(f"SSA {step} done: {nok}/{len(data['cells'])} cells ok -> {a.out}")
    sys.exit(0 if nok else 2)      # a run that measured nothing must not exit 0 (Wave-1 D5)

if __name__ == "__main__":
    main()
