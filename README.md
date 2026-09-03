# Divergence Ranks What Benchmarks Bound

*Quantization, context and speculative decoding for a 27B coding model on two 16 GB GPUs.*

**How much does quantization actually cost a coding model, and would you notice with the
instruments the field usually reaches for?**

A measurement study of **Qwen3.8-27B** across four Unsloth GGUF quantizations on **two consumer
16 GB GPUs**, run on a single consumer workstation. Its deliverable is a technical report for arXiv.

The short answer: quantization damage measured on **code** is roughly **twice** what the same
instrument reports on **prose**, the gap widens as quantization gets more aggressive, and a
standard multiple-choice benchmark **cannot see any of it** — it ranked the most heavily quantized
arm nominally highest while a divergence measurement separated the same arms at 3.7–11.8 σ.

- **Deliverable** — [`manuscript/`](manuscript/) · outline and evidence map in
  [`manuscript/OUTLINE.md`](manuscript/OUTLINE.md). **Status: measurement complete, not yet drafted.**
- **Findings, individually cited** — [`docs/paper/PAPER-NOTES.md`](docs/paper/PAPER-NOTES.md) (PN-1…PN-63)
- **The deployment answer** — [`docs/paper/TRACK-A-DECISION.md`](docs/paper/TRACK-A-DECISION.md)
- **How the work was run** — [`docs/build-stream/2026-08-30-quant-bench-trackA.md`](docs/build-stream/2026-08-30-quant-bench-trackA.md)

---

## The setup

| | |
|---|---|
| Model | Qwen3.8-27B, Unsloth Dynamic GGUFs |
| Arms | UD-Q4_K_XL (17.56 GB) · UD-Q5_K_XL (20.88 GB) · UD-Q6_K (21.98 GB) · UD-Q6_K_XL (25.30 GB, reference) |
| Host | `multivac` — 2× RTX 5060 Ti 16 GB (Blackwell sm120, **no NVLink**, 180 W cap), Ryzen 5 8500G, 14 GiB RAM |
| Engine | llama.cpp `llamacpp-mtp:latest`, 0.3.0-dev build 1 (`d222767`), image `sha256:feb0231976b6…` |
| Instrument | `llama-perplexity --kl-divergence`, 65,536 tokens per domain per arm |

Two GPUs of 16 GB are not a 32 GB pool. Under `--split-mode layer` each layer's weights *and its
slice of the KV cache* live on one card, so the binding limit is per-card — and that fact turns out
to drive more of the results than the quantization does.

## What the study found

**1 — Quantization damage is domain-dependent, and the published view is the flattering one.**
Mean KL divergence against the UD-Q6_K_XL reference, 65,536 tokens per cell:

| arm | WikiText-2 (prose) | django (code) | HumanEval+ prompts (task) | task ÷ prose |
|---|---|---|---|---|
| UD-Q6_K | 0.003321 ± 0.000126 | 0.005829 ± 0.000233 | 0.010403 | 3.13× |
| UD-Q5_K_XL | 0.004465 ± 0.000281 | 0.010285 ± 0.000458 | 0.017285 | 3.87× |
| UD-Q4_K_XL | 0.008207 ± 0.000340 | 0.021529 ± 0.000834 | 0.036129 | 4.40× |

Monotone in every domain, adjacent arms separated at 3.7–11.8 σ. Against the <0.007 band published
for high-quality deployment, **two of three arms pass on prose, one on generic code, and none on
the actual task distribution** — and the prose-to-task amplification grows with
aggressiveness (3.13× → 4.40×). ⚠️ That *widening* clause is an **upper bound**, not a
reference-invariant result: it shrinks ~16 % under a plausible reference correction and vanishes in
the limit. The *level* — code roughly twice prose — is invariant. (PN-13, PN-14, PN-21)

**2 — A task battery is structurally insensitive to this, not merely underpowered.**
HellaSwag at n=400 on all four arms: 82.75 / 82.25 / 82.75 / 83.25 % — a 1.0-point spread inside
~7.4-point intervals, with the **most quantized arm scoring nominally highest**. A paired McNemar
analysis on the identical task set finds UD-Q6_K_XL and UD-Q5_K_XL answering **all 400 items
identically**. More tasks would narrow the intervals and fix nothing: multiple-choice scoring
depends only on an argmax over a few candidates, so it is robust to exactly the distribution shift
that changes generated code. **Decided the conventional way, this study would have concluded "no
meaningful difference" and picked the cheapest arm.** (PN-22)

**3 — For most arms, the usable context ceiling is set by the GPU split rather than the
quantization.** UD-Q5_K_XL **fails to load** at 262,144 tokens at the engine's default split and
loads at five different `-ts` ratios (PN-6); UD-Q6_K likewise fails at the default and loads at
`58,42`. ⚠️ **Scope (PN-39): UD-Q4_K_XL loads at 262,144 on the default split**, so the effect is
not universal — it holds for two of the four arms, UD-Q6_K_XL was never attempted at the default
at that length, and each default-split failure is a *single* attempt. UD-Q6_K_XL reaches 212,992 at `56,44` against a previously published
131,072 (PN-7). The default placement had been stranding up to 3,333 MiB on one card while the
other OOMed within 671 MiB of its wall — on this host the binding limit is per-card, and the
earlier rebalance measurement that opened this line of enquiry recovered **+33 % context and +93 %
decode at once** from that one flag (E11c, machine log). The optimum is quant-specific and **not
monotone-safe** — `54,46` fails where `58,42` loads. A ceiling published without its split is a
property of the split, not of the model.

**4 — Speed does not discriminate the ladder.** At the full window the three arms that reach it
over *true* repetition groups (same arm, same context, same split) the arms span
**11.71–12.70 tok/s, about 6.74 %**, against a within-configuration spread reaching **40.7 %**
(PN-45 — PN-36's "46.7 %" silently switched estimator, and its group mixed `-ctxcp 4` and `32`). The usual case for quantizing down ("meaningfully faster for slightly less
accurate") does not hold here: the cheaper arm is **only** less accurate. It earns its place on
VRAM footprint alone. (PN-19)

**5 — Speculative decoding is not output-identical, contrary to the standing assumption.**
At temperature 0 with a fixed seed, MTP reproduces the unspeculated baseline byte-exactly on
**131 of 164** HumanEval+ problems — about one generated function in five differs. The control has since been run and settled it
the other way: **both configurations reproduce *themselves* byte-identically** across runs a day
apart, so the divergence is deterministic and systematic, not numerical noise. Speculation here is
a reproducibly *different* decode path, not an approximation that drifts (PN-26). Either way, **a speculative
configuration is part of the accuracy configuration, not a free speed knob.** (PN-23)

**6 — The KV-cache quantization everything rests on is not free.** `q4_0` KV — the dtype without
which none of these context ceilings exist — costs 0.002955 ± 0.000127 KLD against f16, i.e. **51 %
of the divergence of dropping a whole quantization level**. Defensible; not free; and it must be
quoted with every accuracy claim. Perplexity on the identical pair moves +0.15 %, a clean
demonstration of the averaging bias that makes PPL a poor quantization metric. (PN-15)

**7 — The same weights, measured two defensible ways, differ 36-fold in reported damage.**
One checkpoint scored against the same benchmark corpus reads **+29 % worse** than its comparison
ladder under one perplexity protocol and **+0.8 % worse** under another — a 36× swing in the
estimated effect, attributable to corpus file, window coverage and scoring rule alone. The intuitive
explanation, tokenizer mismatch, was tested and **disproven**: the two tokenizations agree exactly.
Three protocols exist in this study and must never share a table. (PN-49)

**8 — Across twelve days, the instruments the field reaches for did not separate this ladder.**
Corpus perplexity spans **0.033** across four arms against a per-point standard error of **0.041**.
HumanEval+ at n=164 is monotonic but its three upper rungs sit inside a ±4.6-point interval.
SWE-bench Verified at n≈50 **inverts** the ladder outright — 77.6 / 76.0 / 75.5 % — on a ±12-point
bootstrap interval, so the inversion carries no information. And the one arm that leads every cheap
instrument in the study (fastest configuration measured, acceptable HumanEval+) reached the agent
step limit on **6 of 6** instances where the reference converged on 6 of 6. Single-shot benchmarks
did not predict agentic competence. (PN-46, PN-48, PN-50, PN-51)

## Where this report corrects itself

Three headline claims were withdrawn or scoped by this project's own re-analysis, at no GPU cost,
after the measurements were complete. They are listed here rather than in an appendix because the
corpus's central argument is about what instruments can and cannot show:

- **The long-context result was measuring the wrong thing.** A multi-key retrieval battery at
  131,072 tokens appeared to show the 4-bit arm losing 10 points (p = 0.002). Re-analysed: the
  harness ran with a 128-token output budget and reasoning enabled, so **every failure in both arms
  is a truncation** — `closed-and-wrong` is exactly **zero** across all fourteen cells. On the 55 of
  100 items where neither arm's budget bound, **both score 55/55 with zero discordance**. The real,
  still-separated effect is budget closure (77 vs 60, p = 0.0015): reasoning verbosity, not
  retrieval. Retrieval at that depth is now *unanswered*, not answered. (PN-60, PN-63)
- **The tail structure is a corpus property, not a quantization property.** Normalised by its own
  mean, the KV-dtype-only control — no weight quantization at all — shows p99/mean of **22.9** on
  code against **24.3–26.1** for the quantized arms, with prose flat at **8.4–8.6** throughout.
  Quantization moves the *magnitude*; the corpus sets the *shape*. (PN-62)
- **A draft-acceptance figure of 1.000 at 259K tokens was an artifact** of 50-token generations over
  34 draft events. Rows that actually generated 1,024 tokens record 0.92 and 0.55. (PN-61)

## The deployment answer

For this host, prioritising accuracy → context → tok/s:

```bash
-m Qwen3.8-27B-UD-Q6_K.gguf -ngl 99 -sm layer -ts 58,42 -c 262144 -fit off -fa on \
   -ctk q4_0 -ctv q4_0 -b 2048 -ub 512 -np 1 -ctxcp 32 \
   --spec-type draft-mtp --spec-draft-n-max 2
```

Full 262,144-token window at Q6 fidelity, **11.90 tok/s** at 95 % window depth (median of 3).
An earlier revision pinned `n-max 4` at "16.8 tok/s"; that measurement timed **17 generated tokens
rather than 192** and is withdrawn — see `TRACK-A-DECISION.md` Amendment 2. Fallbacks, the evidence
and the conditions it is contingent on: [`docs/paper/TRACK-A-DECISION.md`](docs/paper/TRACK-A-DECISION.md).

This is a **machine-specific operational answer and is kept separate from the report on purpose**.
The report reports trade-off curves per objective; it does not inherit this priority ordering.

## What the study does not show

Stated here rather than buried, because an underpowered result reported as a ranking is worse than
no result:

- **Long-context task accuracy is unmeasured for every arm.** No 100K–250K task outputs exist
  anywhere in the corpus, and the one long-context battery that appeared to separate the arms was
  measuring output-budget exhaustion (PN-60). This is the largest hole.
- **No multiple-comparisons correction is applied across the study's ~19 hypothesis tests.** Under
  Holm and Benjamini–Hochberg all 11 positive results survive, but the weakest separation (3.71 σ)
  does not survive Bonferroni once clustering is allowed for — so "3.7–11.8 σ" quotes a range whose
  lower endpoint is fragile.
- **Divergence is ladder-relative** — measured against UD-Q6_K_XL because no FP16 reference fits
  the host. These are distances along the ladder, not from the unquantized model.
- **Divergence is measured on prompt tokens** — it ranks distribution shift, not generated-code
  quality. The paired generative anchor was never run.
- **Two single-domain corpora**, one model family, one host, one engine image.
- **Absolute scores are not comparable to published numbers**: logprob instruments run greedy,
  while the model's official presets are temp 0.7 (instruct) and 1.0 (thinking).

## Repository layout

```
manuscript/          the arXiv report — the deliverable
docs/
  paper/             findings: PAPER-NOTES (PN-1..63), method references, the Track A decision
  build-stream/      how the work was run: the plan, its decision log (DEC-*) and ledger (L-*)
data/
  raw/e12/           current evidence — artifacts, logs, quarantine, harness source
  archive/           pre-E12 historical evidence, superseded but never deleted
  multivac-src/      read-only mirrors of documents the machine owns
tools/               sync-multivac.sh (active) · retired/ (the halted conductor subsystem)
```

Machine-side: `/srv/bench/e12/` (current wave), `/srv/bench/` (all prior results, never deleted),
`/srv/models` + `/srv/bench/models` (GGUFs), `~/CLAUDE.md` (the machine's own documentation).

## Working in this repository

Read [`CLAUDE.md`](CLAUDE.md) — it holds the ownership map, the hard rules, the configuration facts
that are easy to get wrong, and the live TODO. The rules exist because each one has already cost
this project a wrong number or a near-miss on data loss.

Git syncs to a bare repository on the host and to this public remote. The measurement record,
including withdrawn claims and the instrumentation-defect register, is published in full.
