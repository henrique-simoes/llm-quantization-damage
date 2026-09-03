# Technical report — outline and evidence map

**Measurement closed 2026-09-02 (L-18). Every claim below names the paper note that carries its
number, interval and caveat.** A section with no PN reference is not yet supported and must not be
written as though it were.

Working title: **Quantization Damage Lives in the Tail: domain-dependent divergence in a 27B
coding model, and what task benchmarks can and cannot bound**

⚠️ **Revised 2026-09-02 after a three-way review round (L-19).** Nine paper notes were corrected or
retracted — PN-36, 37, 39, 40, 41, 42, 43 supersede or qualify PN-19, 34, 6, 28, 8, 15 and the
project's cost contrast. The previous title claimed *saturation*, which PN-37 shows is false for two
of three instruments. Read this file as the post-review plan; anything citing PN-19's 32.9 %,
PN-28's "p = 1.0", the "20 min vs 20 h" contrast, or PN-34's saturation mechanism is stale.

---

## The thesis, in one paragraph — post-review

Quantization damage to a 27B coding model is **concentrated in the tail of the token distribution**:
at the median, code tokens are perturbed 100–200× *less* than prose tokens, the ordering reverses
between the 90th and 95th percentile, and by the 99th code is perturbed 5–8× *more* (PN-35). The
familiar "code is about twice as damaged as prose" is the mean of those two opposite facts. This
structure supplies a mechanism with a numerical prediction: benchmarks score **outcomes**, not
tokens, so a perturbation confined to ~1–5 % of positions changes an outcome only when a tail token
lands somewhere decisive — which predicts the small discordances we measure across three independent
instrument classes (3/164 and 5/164 on generative coding; 2–4 of 400 on multiple-choice). We confirm
Dutta et al. (NeurIPS 2024) independently on a different model family, compression scheme and
hardware class, and bound what a task benchmark can say: **a 3.69× increase in code-prompt divergence
moves HumanEval+ pass@1 by at most about 3 points** (PN-40). We also report the systems findings that
decide a deployment on this hardware, and a register of instrumentation defects offered as method.

**What this thesis no longer claims** (PN-37): that the benchmarks are *saturated*. Two of the three
have real headroom — HellaSwag ~17 points, HumanEval+ ~5 — and MK-NIAH's reference arm turned out to
sit at 89 %, not at ceiling, once measured at n=100. Saturation was an inference, not a measurement,
and the counter-example (`variable_tracking`, the harder task) was excluded from our own study.

## 1. Introduction

The practical question: on two 16 GB consumer GPUs, which quantization of a 27B model should run a
coding agent, and how would you know? The field ranks GGUF quantizations on prose perplexity or on
task batteries. **We show both instruments are the wrong ones, and why.**

Contributions:
1. **The tail structure** (PN-35) — novel, and the paper's lead: damage inverts between the median
   and the 99th percentile, so a mean-only report averages "almost nothing happens" with "something
   drastic happens" and reports neither.
2. **Domain dependence** (PN-14, PN-21): code ~2× prose at the mean, 3.1–4.4× on the actual task
   distribution — with PN-35 explaining *why* the mean understates it.
3. **A measured bound, not a null** (PN-40): three instrument classes each bound the task-level
   effect rather than failing to find one. Independent confirmation of Dutta et al. (R13).
4. On a two-GPU host without a fast interconnect, the tensor split rather than the quantization set
   the reachable window **for two of the four arms measured** (PN-6, scoped by **PN-39** — the
   smallest arm reaches the native maximum at the engine default).
5. Speculative decoding on this engine is **deterministically non-equivalent** to unspeculated
   decoding — reproducible, and reproducibly different (PN-23, PN-26). Scope it to llama.cpp's MTP
   head; DFlash (R12) is motivation, never something we refute.
6. The KV-cache quantization every long-context configuration in this class depends on introduces
   divergence **roughly half the magnitude** of dropping a quantization level (PN-15, qualified by
   **PN-43** — a size comparison, not an additive currency).

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

### 5.2 Three instruments, three bounds — PN-22, PN-28, **PN-40**, PN-33, **PN-37**
**The paper's centre.** Each instrument *bounds* the task-level effect rather than failing to find
one — that reframing is PN-40's, and it is what makes the section a result instead of a null.
- **Multiple-choice** (HellaSwag n=400): 1.0-point spread, the most-quantized arm nominally
  highest, two arms answering all 400 items identically, no pair differing on more than 4.
- **Generative coding** (HumanEval+ n=164, paired): the arms agree on 161 of 164. ⚠️ Report the
  **paired difference and its interval — −0.61 pts, 95 % CI [−2.68, +1.46]** — *not* "McNemar
  p = 1.0", which PN-40 shows could never have reached 0.05 with 3 discordant pairs (minimum
  obtainable p = 0.25). State that explicitly: it is the paper's own instance of the error it
  attributes to the field.
- **Long-context retrieval** (RULER, PN-44): S-NIAH 100.0/100.0 at 8,192 / 32,768 / 131,072 —
  16× more context, zero discrimination. Then MK-NIAH at 131,072, n=100: **89.0 vs 79.0, recovery
  88.76 %, exact McNemar p = 0.0020**, paired difference −10.00 pts [−15.88, −4.12]. Ten discordant
  items, **all in the same direction** — the cheaper arm's failures are a strict superset of the
  reference's. This is the one instrument that *separates* the arms, and it does so only where the
  task is hard enough that the reference itself fails 11 % of the time.
**PN-44 is what makes this section an argument rather than a list.** The three instruments do not
merely bound the effect by differing amounts — they order themselves by how close the task sits to
the model's limit. Multiple-choice (82.75 %, far from ceiling) and generative coding (94.5 %) bound
it to a few points; single-needle retrieval at any depth is perfect for both arms and bounds it to
zero; and multi-key retrieval — the only task where the *reference* fails 11 % of the time —
separates the arms decisively. That ordering is what the tail mechanism predicts: damage confined
to ~1–5 % of token positions changes an outcome only where an outcome was already marginal.

**The mechanism is PN-37's, not PN-34's.** Do not claim saturation: HellaSwag has ~17 points of
headroom, HumanEval+ ~5, and MK-NIAH's reference sits at 89 %. Claim instead that damage confined to
~1–5 % of token positions (PN-35) changes an outcome only when a tail token lands decisively, which
predicts the discordance magnitudes above. And disclose in this same subsection that
`variable_tracking` — the *harder* RULER task — was excluded for an output-format artifact (PN-33),
because it is the obvious counter-example to any difficulty-based reading.

### 5.3 What sets the reachable window — PN-6 scoped by **PN-39**, PN-7, PN-8 corrected by **PN-42**
For two of the four arms the tensor split, not the quantization, set the reachable context: Q5_K_XL
and Q6_K both fail at the engine default at 262,144 and load at a swept ratio. ⚠️ **Q4_K_XL loads at
the default split** and Q6_K_XL was never attempted there — so state "for two of the four arms we
measured", and note that each default-split failure is a **single** attempt, short of this project's
own two-attempt bracketing rule. The `-ts` optimum is quant-specific and not monotone-safe (PN-7).
On balance vs throughput: the most balanced ratio was the slowest by 21 %, while the other four
clustered within 3.6 % — inside the 46.7 % noise floor, so only the outlier survives. Report the
practical rule ("keep the fastest that loads") and drop PN-8's "opposing objectives" framing.

### 5.4 Speculative decoding is not free — PN-23, PN-26, PN-29, PN-32, PN-9
Non-identity at greedy (131/164), then PN-26's determinism control upgrading it to *deterministically*
non-equivalent. DFlash2 fastest at 32 K and unable to reach the deployment window. Acceptance falls
with draft depth (12/13 pairs, p = 0.0017). **Report PN-32's clustering lesson explicitly**: pooled
per-event intervals of ±0.02 against a true between-run spread of ±0.3.

### 5.5 Speed does not discriminate — PN-36 (supersedes PN-19), PN-42 (corrects PN-8), PN-18
Over *true* repetition groups: an 8.6 % between-arm span against a within-configuration spread
reaching 46.7 %. PN-19's 32.9 % mixed four context depths and is withdrawn. On splits: the most
balanced ratio was the slowest by 21 %, and among the rest imbalance barely mattered — PN-8's
"balance and throughput oppose" framing is corrected by PN-42. The cheaper arm is not meaningfully faster, only less
accurate; it earns its place on VRAM footprint alone.

### 5.6 KV-cache quantization is not free — PN-15, qualified by PN-43
0.002955 ± 0.000127 KLD, 51 % of a quantization level, with the PPL-vs-KLD contrast on the
identical pair as a worked demonstration of averaging bias.

### 5.7 Systems and energy — PN-11, PN-12
Host power envelope, idle-to-loaded swing, thermal cost of an asymmetric split.

## 6. What the measurements cost — PN-41
Measured from the artifacts, not estimated: **2.15 h of divergence** against **≈4.8 h of task
benchmarking** across three instrument classes. A 2.2× cost ratio — the earlier "20 min vs 20 h"
was generalised from one arm on one domain and is withdrawn. **The power ratio is what carries the
point**: 2.1 hours separated the arms at 3.7–11.8 σ; 4.8 hours bounded them and separated nothing.

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

## 9. Reproducibility appendix — PN-5, 17, 20, 25, 27, 30, 31, 36, 38, 41, 42, 43
Now twelve entries, and they cluster into three families worth naming as such:
**(i) an aggregate computed across cells differing in an untracked variable** — PN-20's three
estimators in one column, PN-30's 17-token throughput, PN-36's four-depth "repetition" spread,
PN-41's generalised cost ratio, PN-42's imbalance ordering. Rule: *an aggregate is meaningful only
if every cell entering it is identical in every dimension except the one aggregated over, and the
cell key is where you check that.*
**(ii) a contract documented but not asserted in code** — PN-5's depth gate, PN-30's missing
generation gate. **(iii) an identifier or binding that is not unique** — PN-25's mis-bound drafter,
PN-27's predicate matching its own supervisor, PN-43's label collision that silently overwrote a
serverlog and left a well-formed file behind.
Plus PN-38: a metric that cannot work in principle (free-running greedy generation forks, so every
pairwise distance saturates), found only by running it.
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
