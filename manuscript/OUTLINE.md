# Technical report — outline and evidence map

**Measurement closed 2026-09-02 (L-18). Every claim below names the paper note that carries its
number, interval and caveat.** A section with no PN reference is not yet supported and must not be
written as though it were.

Working title: **The Benchmarks Cannot See It: quantization damage to a coding model is
domain-dependent, and the instruments used to certify quantizations are saturated**

---

## The thesis, in one paragraph

Quantization damage to a 27B coding model is real, rises as the evaluation corpus approaches the
target task, and is **invisible to three independent classes of task benchmark** — multiple-choice,
generative coding, and long-context retrieval. The common cause is not modality and not context
length but **saturation**: each benchmark has a ceiling, and a quantization difference cannot be
seen while both arms sit against it. Divergence measurement has no ceiling, which is why twenty
minutes of KL divergence per arm separates these quantizations at 3.7–11.8 σ where roughly twenty
hours of task benchmarking across three modalities separates them nowhere. We also report the
systems findings that decide a deployment on this class of hardware, and a register of
instrumentation defects offered as method.

## 1. Introduction

The practical question: on two 16 GB consumer GPUs, which quantization of a 27B model should run a
coding agent, and how would you know? The field ranks GGUF quantizations on prose perplexity or on
task batteries. **We show both instruments are the wrong ones, and why.**

Contributions:
1. Quantization damage measured on **code** is ~2× the damage the same instrument reports on
   **prose**, widening with aggressiveness; on the actual task distribution it is 3.1–4.4× prose
   (PN-14, PN-21).
2. **Three independent task instruments cannot see it**, and the reason is saturation, not
   modality or depth (PN-22, PN-28, PN-33, **PN-34**).
3. On a two-GPU host without a fast interconnect, the usable context ceiling is a property of the
   **tensor split**, not of the quantization (PN-6, PN-7).
4. Speculative decoding on this engine is **deterministically non-equivalent** to unspeculated
   decoding — reproducible, and reproducibly different (PN-23, PN-26).
5. The KV-cache quantization every long-context configuration in this class depends on costs
   **51 % of a quantization level** (PN-15).

## 2. Background and related work
KL divergence as the quantization-loss instrument and the case against perplexity's averaging bias
(R1, R2, R4). Unsloth Dynamic GGUFs and calibration contamination (R3). Production quantization
evaluation and the <0.007 band (R4). The closest published analogue (R5). Error bars, paired
differences, power (R6). Task-battery treatments of llama.cpp quantization, read as a caution (R7).
RULER and the long-context protocol (R8), the two published quantization-at-depth studies (R9), and
why an averaged token-level metric is the wrong instrument for long context (R10).

## 3. Setup
Host: 2× RTX 5060 Ti 16 GB (sm120, no NVLink, 180 W), Ryzen 5 8500G, **14 GiB RAM**. Engine pinned
by image digest. Four Unsloth GGUF arms. Evidence: `env-manifest.json`.

**The harness-validation gate belongs here, as a result**: measured sampling defaults match neither
the documented engine defaults nor either official preset (PN-1); thinking is on by default and the
widely-cited disable idiom fails on this template (PN-2, PN-3); `-fit` cannot be trusted to bound
allocation (PN-4).

**Footnote, not a feature (owner direction):** the 14 GiB RAM figure is load-bearing for one
negative result — KL divergence at long context is not measurable here, because the tool holds a
chunk's logits resident and the host caps at n_ctx 8,192 (PN-31). One or two sentences beside the
host specification. The only clause with bearing on the argument: *the standard divergence tooling's
footprint scales with context length, which is itself why published quantization tables are all
measured near 2K.*

## 4. Method — the Small-Sample Accuracy protocol
Divergence instruments draw power from **token count**; task benchmarks from **problem count**.
Full protocol in `../docs/build-stream/2026-08-30-quant-bench-trackA.md` §SSA. Reference-arm choice
and its ladder-relative consequence; the 65,536-token budget; pre-registered interpretation bands.

## 5. Results

### 5.1 The ladder, and why the domain decides — PN-13, PN-14, PN-21, PN-16
Three-tier hierarchy (prose < code < task prompts); monotone in every domain; adjacent arms at
3.7–11.8 σ with non-overlapping intervals. The metric-pair argument: top-1 agreement and mean KLD
disagree about which domain is hurt, and a top-1-only table inverts the conclusion.

### 5.2 Three instruments, one blind spot — PN-22, PN-28, PN-33, **PN-34**
**The paper's centre.** Multiple-choice (HellaSwag n=400: 1.0-point spread, most-quantized arm
nominally highest, two arms answering all 400 identically). Generative coding (HumanEval+ n=164
paired: agreement on 161 of 164, McNemar p=1.0). Long-context retrieval (S-NIAH: 100.0/100.0 at
8,192 / 32,768 / 131,072 — **16× more context, zero discrimination**). Then the diagnostic: hold
depth at 131,072 and raise *difficulty* — MK-NIAH gives 100.0 vs 91.67. **Difficulty revealed what
depth could not.** State the MK-NIAH caveat in the same breath: one failed sample of twelve,
intervals overlapping, consistent with R9's published band but not established here.

### 5.3 The context ceiling belongs to the split — PN-6, PN-7, PN-8
The same configuration failing at the default split and loading at five ratios; the quant-specific,
non-monotone optimum; balance and throughput as opposing objectives.

### 5.4 Speculative decoding is not free — PN-23, PN-26, PN-29, PN-32, PN-9
Non-identity at greedy (131/164), then PN-26's determinism control upgrading it to *deterministically*
non-equivalent. DFlash2 fastest at 32 K and unable to reach the deployment window. Acceptance falls
with draft depth (12/13 pairs, p = 0.0017). **Report PN-32's clustering lesson explicitly**: pooled
per-event intervals of ±0.02 against a true between-run spread of ±0.3.

### 5.5 Speed does not discriminate — PN-19, PN-18
6.7 % span against 32.9 % within-arm noise. The cheaper arm is not meaningfully faster, only less
accurate; it earns its place on VRAM footprint alone.

### 5.6 KV-cache quantization is not free — PN-15
0.002955 ± 0.000127 KLD, 51 % of a quantization level, with the PPL-vs-KLD contrast on the
identical pair as a worked demonstration of averaging bias.

### 5.7 Systems and energy — PN-11, PN-12
Host power envelope, idle-to-loaded swing, thermal cost of an asymmetric split.

## 6. What the measurements cost
Wall-clock and GPU-hours per instrument; the argument that this protocol is reproducible on one
consumer machine in an afternoon. **The affordability is a contribution**, and the contrast is the
point: ~20 min of divergence per arm resolves what ~20 h of task benchmarking does not.

## 7. Threats to validity — write this BEFORE polishing results
1. **Ladder-relative divergence.** No FP16 reference fits the host; Q6_K_XL's own degradation is
   unmeasured and zero by construction (G20).
2. **Prompt-token divergence is not generation quality.** PN-28 is the generative anchor and it is
   a null at n=164.
3. **Long-context accuracy is bounded, not resolved.** PN-33 covers two retrieval tasks at three
   lengths with n=12 at the deepest; QA and aggregation were never run.
4. **PN-9's quant/depth/ratio confound is unresolved** — S9d was reinstated to close it and failed
   on power (PN-32). No per-arm best draft depth is reported.
5. **Spec-decode results are greedy-only.** A powered temp>0 equivalence test was not affordable.
6. **No per-config energy figure.** PN-11 is the host baseline; the historical J/tok table is
   depth-0 and from a deleted image.
7. Two single-domain corpora, one model family, one host, one engine image; n=3–6 speed reps
   against ~30 % noise.
8. **Not comparable to published scores**: logprob instruments run greedy while the official
   presets are temp 0.7/1.0; Qwen publishes LiveCodeBench v6, SWE-bench **Pro** and Terminal Bench,
   none set up here, and no HumanEval at all (G19).

## 8. Practitioner appendix — the configuration
`TRACK-A-DECISION.md` verbatim, framed as *what this analysis implies for one concrete deployment*
and explicitly not as the paper's recommendation. Include Amendment 2 and why the draft-depth flag
reverted — a worked example of a withdrawn claim.

## 9. Reproducibility appendix — PN-5, PN-17, PN-20, PN-25, PN-27, PN-30, PN-31
Offered as method, not confession. Each is a trap another group would fall into:
a documented contract not asserted in code; a harness scoring a subprocess by exit code alone; an
aggregator that never names its estimator; a drafter bound to its engine build; a safety check
whose pattern matched the tooling built to supervise it; a throughput measurement that timed 17
generated tokens; and an instrument whose memory scales with a parameter its own docs never mention.

---

## Before submission
- [ ] Every headline number traced to a PN entry and through it to an artifact
- [ ] Every table names its protocol, n and estimator **in the table**
- [ ] Pre-2026-08-29 rows labelled *irreproducible-on-current-images*, or excluded
- [ ] Withdrawn claims (PN-24 at-depth, S8 at-depth, Track A Amendment 1) appear nowhere except
      as worked examples in §9
- [ ] Threats-to-validity written before results are polished
- [ ] Owner call on releasing artifacts — the repo is private and has no public remote
