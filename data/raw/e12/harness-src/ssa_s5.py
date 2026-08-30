#!/usr/bin/env python3
"""ssa_s5.py — SSA step S5: divergence over the HumanEval+ task prompts.

Same instrument as S2/S3, pointed at the ACTUAL task distribution instead of a generic
corpus. This is the Fireworks method (METHOD-REFERENCES R4): run divergence over the task
prompts with the quantized model following the reference, no generation at all — so it costs
prefill only, minutes rather than the hours a generative benchmark would take.

Builds the corpus from evalplus's local HumanEval+ set, then reuses ssa_kld.run_perplexity
verbatim so the protocol is identical to S2/S3 and the numbers sit in the same table.
"""
import json, os, sys, time
sys.path.insert(0, "/srv/bench/e12/experiments")
import ssa_kld as K

CORPUS = "/srv/bench/corpus/humanevalplus-prompts.txt"
OUT    = "/srv/bench/e12/ssa/ssa-s5-results.json"
N_CTX  = 2048

def build_corpus():
    from evalplus.data import get_human_eval_plus
    probs = get_human_eval_plus()
    # prompts only, in stable task-id order: this measures the distribution the model is
    # asked to continue, not any completion we might have generated.
    keys = sorted(probs, key=lambda k: int(k.split("/")[1]))
    text = "\n\n".join(probs[k]["prompt"] for k in keys)
    os.makedirs(os.path.dirname(CORPUS), exist_ok=True)
    with open(CORPUS, "w") as f:
        f.write(text)
    print(f"corpus: {len(keys)} HumanEval+ prompts, {len(text):,} chars -> {CORPUS}")
    return len(keys), len(text)

def main():
    n_probs, n_chars = build_corpus()
    # ~4 chars/token on this code-like text; use every whole chunk the corpus supports
    chunks = max(1, (n_chars // 4) // N_CTX)
    print(f"using n_ctx={N_CTX} x {chunks} chunks (~{N_CTX*chunks:,} tokens)")

    K.DOMAINS["humaneval"] = "/corpus/humanevalplus-prompts.txt"

    if K.gpu_busy():
        print("REFUSING: a GPU experiment is running"); sys.exit(4)

    data = {"experiment": "ssa-s5", "source": "e12-ssa", "run_ids": ["ssa-s5"],
            "protocol": "SSA S5 — divergence over HumanEval+ task prompts (forced reference, no generation)",
            "reference_arm": K.REFERENCE,
            "reference_note": "ladder-relative: measured against the least-quantized available arm, not FP16",
            "n_ctx": N_CTX, "chunks": chunks, "tokens_per_cell": N_CTX * chunks,
            "n_problems": n_probs, "corpus_chars": n_chars,
            "seed": K.SEED, "kv": "q4_0", "image_id": K.image_id(),
            "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "cells": []}

    base = K.run_perplexity(K.REFERENCE, "humaneval", N_CTX, chunks, "q4_0",
                            "base-humaneval.kld", "base")
    data["cells"].append(base)
    json.dump(data, open(OUT, "w"), indent=1)
    print(f"base rc={base['rc']} ok={base['ok']}")
    if not base["ok"]:
        print("base logits failed — cannot score arms"); sys.exit(2)

    for arm in ("Q6_K", "Q5_K_XL", "Q4_K_XL"):
        c = K.run_perplexity(arm, "humaneval", N_CTX, chunks, "q4_0",
                             "base-humaneval.kld", "kld")
        data["cells"].append(c)
        json.dump(data, open(OUT, "w"), indent=1)
        m = c.get("metrics", {})
        print(f"  {arm}: ok={c['ok']} mean_kld={m.get('mean_kld')} top1={m.get('top1_agree_pct')}")

    data["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    json.dump(data, open(OUT, "w"), indent=1)
    nok = sum(1 for c in data["cells"] if c["ok"])
    print(f"S5 done: {nok}/{len(data['cells'])} cells ok -> {OUT}")
    sys.exit(0 if nok == len(data["cells"]) else 2)

if __name__ == "__main__":
    main()
