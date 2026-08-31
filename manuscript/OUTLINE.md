# Technical report — outline and evidence map

Working title: **Quantization Damage Is Domain-Dependent: measuring GGUF quantization of a 27B
coding model on consumer dual-GPU hardware**

Every claim below names the paper note (`PN-n`, in `../docs/paper/PAPER-NOTES.md`) that carries its
number, interval and caveat, and through it the artifact under `../data/raw/e12/`. A section with
no PN reference is not yet supported by evidence and must not be written as though it were.

---

## 1. Introduction

The practical question: on two 16 GB consumer GPUs, which quantization of a 27B model should run a
coding agent, and how would you know? The literature ranks GGUF quantizations on prose perplexity
or on multiple-choice batteries. **We show both instruments are the wrong ones for this question,**
and that a divergence measurement costing 20 minutes of GPU per arm ranks what 20 hours of task
benchmarking cannot.

Contributions:
1. Quantization damage measured on **code** is ~2× the damage the same instrument reports on
   **prose**, and the gap widens as quantization gets more aggressive (PN-14). On the actual task
   distribution it is 3.1–4.4× prose (PN-21).
2. A standard multiple-choice battery is **structurally insensitive** — not merely underpowered —
   to damage that divergence resolves at 3.7–11.8 σ (PN-22).
3. On a two-GPU host without a fast interconnect, the usable context ceiling is a property of the
   **tensor split**, not of the quantization (PN-6, PN-7).
4. Speculative decoding on this engine is **not output-identical** to unspeculated decoding
   (PN-23), retiring an assumption widely treated as structural.
5. The KV-cache quantization that every long-context configuration in this class depends on costs
   **51 % of a quantization level** in divergence (PN-15) — validated, not assumed.

## 2. Background and related work

- KL divergence as the quantization-loss instrument, and the case against perplexity's averaging
  bias — R1, R2, R4 in `../docs/paper/METHOD-REFERENCES.md`.
- Unsloth Dynamic GGUFs and their calibration-contamination warning — R3.
- Production quantization evaluation and the <0.007 band — R4 (Fireworks).
- The closest published analogue and the 0.01–0.03 Q4_K_M band — R5 (LocalBench).
- Error bars, paired differences, power — R6 (Miller / Anthropic, arXiv 2411.00640).
- The task-battery treatment of llama.cpp quantization, read as a caution rather than a template —
  R7 (arXiv 2601.14277).

## 3. Setup

Host, engine, models, and the provenance discipline. Hardware: 2× RTX 5060 Ti 16 GB (sm120), no
NVLink, 180 W cap, Ryzen 5 8500G, 14 GiB RAM. Engine pinned by image digest. Four Unsloth GGUF arms
(UD-Q4_K_XL 17.56 GB · UD-Q5_K_XL 20.88 GB · UD-Q6_K 21.98 GB · UD-Q6_K_XL 25.30 GB).
Evidence: `../data/raw/e12/env-manifest.json`.

**The harness-validation gate belongs here, not in an appendix** — it is a result in its own right:
measured sampling defaults match neither the documented engine defaults nor either official preset
(PN-1); thinking is on by default and the widely-cited disable idiom does not work on this template
(PN-2, PN-3); `-fit`'s documented silent-shrink behaviour did not reproduce on the current image
but still cannot be trusted to bound allocation (PN-4).

## 4. Method — the Small-Sample Accuracy protocol

The design turns on one fact: **divergence instruments draw statistical power from token count;
task benchmarks draw theirs from problem count.** A coding benchmark has 164 problems and cannot be
made bigger cheaply; a divergence run over the same wall-clock has tens of thousands of per-token
observations. Full protocol in
`../docs/build-stream/2026-08-30-quant-bench-trackA.md` §Small-Sample Accuracy protocol.

Steps S0–S8, the reference-arm choice and why it is ladder-relative, the 65,536-token-per-domain
budget, and the pre-registered interpretation bands.

## 5. Results

### 5.1 The quantization ladder, and why the domain matters — PN-13, PN-14, PN-21, PN-16
The three-tier hierarchy (prose < code < task prompts), the monotone ladder in every domain, the
metric-pair argument (top-1 agreement and mean KLD disagree about which domain is hurt more, and a
top-1-only table inverts the conclusion).

### 5.2 Task benchmarks cannot see it — PN-22
HellaSwag n=400 × 4 arms, the paired McNemar analysis, and the structural argument for why more
tasks would not help. **This is the control that validates the method**, and the strongest single
result in the paper.

### 5.3 The context ceiling belongs to the split, not the quant — PN-6, PN-7, PN-8
The `-ts` rebalance; the same configuration failing at the default split and loading at five
ratios; the quant-specific, non-monotone optimum; balance and throughput as opposing objectives.

### 5.4 Speculative decoding — PN-23, PN-24, PN-9, PN-25
Non-identity at greedy with the mechanism honestly left open; draft depth n=4 over n=2 with the
margin growing with depth; acceptance as a per-quant property and a poor predictor of throughput;
the DFlash2 arm excluded with its reason.

### 5.5 Speed does not discriminate — PN-19, PN-18
Medians spanning 6.7 % against within-arm noise of 32.9 %; `-ctxcp` as a free gain. The
consequence: **the cheaper quantization is not meaningfully faster, only less accurate** — which
inverts the usual case for quantizing down.

### 5.6 KV-cache quantization is not free — PN-15
0.002955 ± 0.000127 KLD, 51 % of a quantization level, and the PPL-vs-KLD contrast on the identical
pair (PPL moves +0.15 % while the distribution demonstrably moves) as a worked demonstration of
averaging bias.

### 5.7 Systems and energy — PN-11, PN-12
Host power envelope, idle-to-loaded swing, and the thermal cost of an asymmetric split.

## 6. What the measurements cost
Wall-clock and GPU-hours per instrument; the argument that this protocol is reproducible on one
consumer machine in an afternoon. This is a contribution — the protocol's *affordability* is the
reason it is worth publishing.

## 7. Threats to validity — write this section honestly and early
1. **Ladder-relative divergence.** No FP16 reference fits the host (54.7 GB against 2× 16 GB VRAM
   and 14 GiB RAM). Q6_K_XL's own degradation is unmeasured (G20).
2. **Prompt-token divergence is not generation quality.** The generative anchor (SSA S6, paired
   two-arm HumanEval+) was never written.
3. **Long-context task accuracy is unmeasured for every arm** (G1) — the largest hole. No
   100K–250K task outputs exist anywhere in the corpus; the deep runs produced 50–55-token needle
   answers, not code edits.
4. **Two single-domain corpora** (English prose, Python/django). No multilingual, tool-calling or
   multi-turn coverage.
5. **Calibration contamination cannot be excluded** — the GGUFs' imatrix data is not published.
6. **One host, one engine image, one model family.** n=1 to 6 repetitions on the speed rows against
   ~30 % noise.
7. **Not comparable to published scores.** Logprob instruments run greedy; the official presets are
   temp 0.7/1.0. Qwen publishes LiveCodeBench v6, SWE-bench **Pro** and Terminal Bench, none of
   which is set up here — and no HumanEval at all (G19).

## 8. Practitioner appendix — the configuration
The Track A decision and its ladder, verbatim from `../docs/paper/TRACK-A-DECISION.md`, framed as
"what this analysis implies for one concrete deployment" and explicitly **not** as the paper's
recommendation. Track B must not inherit Track A's accuracy → context → tok/s priority ordering.

## 9. Reproducibility appendix — PN-5, PN-17, PN-20, PN-25
The instrumentation-defect register, offered as method rather than as confession, because each one
is a trap another group would fall into:
- a documented contract that is not asserted in code is not a contract (a depth gate in a docstring
  let a 79.7 %-filled window report success);
- a harness that scores a subprocess by exit code alone will report a fully successful run that
  measured nothing (a `±`-vs-`+/-` parser mismatch, 1.5 h of GPU, recovered only because raw
  output was preserved before teardown);
- an aggregator that does not name its estimator will put three different statistics in one
  comparison column, and it reversed a ranking here;
- a mis-bound drafter produces a clean 0.000 that is indistinguishable in a table from a model that
  ran and failed.

---

## Before submission

- [ ] Every headline number traced to a PN entry and through it to an artifact
- [ ] Every table names its protocol, n and estimator **in the table**
- [ ] Pre-2026-08-29 rows labelled *irreproducible-on-current-images*, or excluded
- [ ] Threats-to-validity written before the results are polished, not after
- [ ] Decide whether to run the two cheap experiments that would close real gaps: the
      no-spec-vs-no-spec determinism control (~40 min, attributes PN-23) and SSA S6 (~2 h, the
      generative anchor)
- [ ] Owner call on releasing the artifacts alongside the paper — the repository is private by
      design and has no public remote
