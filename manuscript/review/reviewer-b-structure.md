# Reviewer B — framing, structure, narrative, venue fit

**Blind independent assessment.** I have read `README.md`, `CLAUDE.md`, `manuscript/OUTLINE.md`, all
34 entries in `docs/paper/PAPER-NOTES.md`, `docs/paper/METHOD-REFERENCES.md` (R1–R12, including the R11/R12 additions of 2026-09-02),
`docs/paper/TRACK-A-DECISION.md`, and the decision log and ledger in
`docs/build-stream/2026-08-30-quant-bench-trackA.md`. I opened the underlying artifacts under
`data/raw/e12/` and recomputed several quantities directly, because a structural review that does
not look at the numbers is worthless. I also surveyed the surrounding literature and arXiv's current
submission rules (§9, sources in §14). I have deliberately **not** read `manuscript/review/insider-notes.md` or any
other reviewer's file.

I am reviewing as an ML researcher who has published measurement and systems papers, asking one
question throughout: *if this arrived on arXiv tomorrow, would I read past the abstract, and would I
cite it?*

**Bottom line up front.** Yes, there is a paper — a good one. But the thesis in `OUTLINE.md` has
three problems that must be fixed before drafting, and all three are fixable from data already on
disk:

1. **The saturation thesis is factually wrong for two of its three instruments.** HellaSwag at
   82.75 % and HumanEval+ at 94.5 % are not sitting against a ceiling. Only RULER S-NIAH is
   saturated. §3.
2. **The paper's stated headline — "task benchmarks cannot see damage that divergence detects" — was
   published by Microsoft Research in 2024** (*Accuracy is Not All You Need*, NeurIPS 2024). As
   written, contribution 2 is not novel. §4.
3. **The strongest result in the repository is not in the outline at all.** The quantile fields the
   divergence tool already emitted show quantization damage in code is *tail-concentrated*, and that
   single fact reframes and rescues everything else. §2.

---

## 1. Verdict on publishability

| question | verdict |
|---|---|
| Enough measurement for an arXiv technical report? | **Yes, comfortably.** The problem is selection and framing, not sufficiency. |
| Is the current thesis the right one to lead with? | **No.** It is partly wrong (§3) and partly pre-empted (§4). §2 proposes the replacement. |
| Would this pass peer review somewhere? | **Plausibly, after restructuring** — NeurIPS Evaluations & Datasets, MLSys, or the ACL *Insights from Negative Results* workshop. Not a main-track ML conference: one model, one host, no new method. arXiv is the right first home regardless. |
| Precedent that arXiv accepts this genre from a solo author? | **Yes, directly.** arXiv:2601.14277 (Uygar Kurt, 2026-01-11, cs.LG) is a single-author unified evaluation of llama.cpp quantization on Llama-3.1-8B. Same genre, same ecosystem, narrower scope. |

**What makes this real.** Four things are hard to get elsewhere and are done properly here:

1. **A monotone, well-powered, three-domain divergence ladder** at 65,536 tokens per cell, adjacent
   arms separated at 3.7–11.8 σ. Not a small-n result — it has *more* power than most published
   quantization tables, and it is measured on **code**, which they are not.
2. **A systems result with a large effect and zero statistical exposure** — the context ceiling is a
   property of the tensor split, not the quantization. UD-Q5_K_XL *fails to load* at the default
   split and loads at five different `-ts` ratios. UD-Q6_K_XL's feasible ratio set at 196,608 is a
   **single island** (`56,44` loads; `52,48`, `54,46`, `58,42` and the default all OOM). Load /
   no-load, not a mean with an interval.
3. **A refuted premise the field asserts casually**, with a determinism control almost nobody runs:
   byte-identical self-reproduction on both arms across runs a day apart, byte-different from each
   other on exactly 33 of 164 problems both times. And the premise is not folklore — a published
   implementation of this same drafter family claims to be "bit-for-bit identical to plain target
   decoding" (R12), which gives the section a specific, citable foil rather than a strawman (§4.3).
4. **An artifact and provenance discipline** — per-finding notes with evidence paths, a decision
   log, a ledger, four documented instrument failures caught *by the process*. Very few papers can
   show their own error-detection record.

**What is weak.** The three "the benchmarks cannot see it" nulls are n=400, n=164 and n=12–25, and
the outline's defence of them is currently carried by an argmax mechanism that PN-22's own caveat
calls "an interpretation … not a controlled test", plus one discordant RULER sample out of twelve. A
reader who reviews evaluation papers will reach that and stop. §2 and §5 fix it, free.

---

## 2. The contribution, stated three ways

Ordered by how strongly each survives review, and how likely I am to cite it.

### Statement 1 — the strongest, and currently unnamed anywhere in the repository

> **Quantization damage in code is tail-concentrated.** Ninety per cent of code tokens are *less*
> perturbed by quantization than prose tokens are; the top one per cent are up to eight times more.
> The familiar summary — "code is about twice as bad as prose" — is the average of two opposite
> facts, and the crossover sits between the 90th and 95th percentile of the per-token divergence
> distribution. Averaged metrics and argmax-scored benchmarks both integrate that tail away.

This is not a new experiment. It is sitting in
`data/raw/e12/ssa/ssa-results-parsed.json` and `ssa-s5-results.json`, in the `median_kld`,
`kld_90p`, `kld_95p`, `kld_99p` fields that no paper note mentions. Recomputed:

| statistic | UD-Q6_K prose → code | UD-Q5_K_XL prose → code | UD-Q4_K_XL prose → code | code ÷ prose, per arm |
|---|---|---|---|---|
| median KLD | 0.001392 → 0.000007 | 0.001810 → 0.000010 | 0.003509 → 0.000017 | **0.005× / 0.006× / 0.005×** |
| 90th pct | 0.006742 → 0.003029 | 0.008856 → 0.004790 | 0.016333 → 0.010006 | 0.45× / 0.54× / 0.61× |
| 95th pct | 0.010549 → 0.016109 | 0.013936 → 0.026311 | 0.025546 → 0.055800 | 1.53× / 1.89× / 2.18× |
| 99th pct | 0.028639 → 0.142839 | 0.037323 → 0.250389 | 0.069578 → 0.562891 | **4.99× / 6.71× / 8.09×** |
| **mean** | 0.003321 → 0.005829 | 0.004465 → 0.010285 | 0.008207 → 0.021529 | 1.76× / 2.30× / 2.62× |

Read across: the code/prose amplification runs **0.005× → 0.6× → 2.2× → 8.1×** along the quantile
axis, crossing 1.0 between p90 and p95. The mean lands at 2.6× because the tail drags it there; it
sits between the 95th and 99th percentile of its own distribution. And the tail amplification grows
with aggressiveness exactly as the mean does (4.99 → 6.71 → 8.09), so it is not an artifact of one
arm. The task-prompt domain (`ssa-s5-results.json`) is uniformly above prose at every quantile above
the median (p99 0.190 / 0.314 / 0.616), which is the cleaner but less surprising half.

Why this is the strongest statement available:

- **It explains PN-16 instead of reporting it.** PN-16 records the paradox — top-1 agreement is
  *higher* on code (98.4–99.4 %) while mean KLD is double — and offers predictability as an
  interpretation. The quantile table turns that interpretation into a measurement: median code KLD
  is ~10⁻⁵, so the typical code token is essentially untouched, which is exactly why top-1 survives.
- **It supplies the mechanism the outline's thesis is missing.** "Benchmarks are saturated" is a
  claim about benchmarks — and §3 shows it is false for two of the three. "Damage occupies ~1 % of
  positions, and those positions are where the model chooses" is a claim about the *model*, from
  which limited benchmark sensitivity follows as a prediction rather than an assertion.
- **It makes a prediction the data confirms.** If damage concentrates in a small fraction of branch
  points, a 164-problem paired coding benchmark should show a *handful* of discordant problems — not
  zero, not many. Observed: **3 of 164** on base tests, **5 of 164** on base+extra. The paper
  currently reports this as a null. It is a confirmed quantitative prediction and should be written
  that way.
- **It is well powered and immune to the obvious attack.** 65,536 tokens per cell, σ/256 standard
  errors. Nobody can call it underpowered.
- **It is, as far as I can establish, new.** The KLD-beats-accuracy argument is published (§4); the
  *distributional decomposition by domain* is not. Neither Unsloth, Fireworks, LocalBench, oobabooga
  nor arXiv:2601.14277 reports quantile structure — every one of them reports a mean.
- **S11 corroborates it from the other direction.** `data/raw/e12/s11/s11-divdepth.json` was rejected
  as an instrument because free greedy generation from a real code prefix diverges between adjacent
  quantization levels at character **2, 5, 10, 14, 62, 71, 126** — the metric floors instantly. As a
  rejected instrument that is a footnote. As corroboration that you hit a decision token almost
  immediately in open-ended code generation, it is a result.

### Statement 2 — the current thesis, corrected and demoted to a consequence

> Task benchmarks lack the *resolution* to rank these quantizations, and they lack it for three
> different reasons: the wrong domain scored by argmax over candidates (HellaSwag), a near-ceiling
> benchmark whose discordance rate is what tail concentration predicts (HumanEval+), and a
> genuinely saturated retrieval task (RULER S-NIAH).

Keep the three-instrument sweep — it is real work and the breadth is a genuine asset. But the
outline's unifying claim ("the common cause is saturation, not modality and not context length")
does not survive contact with the numbers. See §3. Rewrite the unifier as **resolution**, supply the
common cause on the *model* side via Statement 1, and the section becomes both true and stronger.

### Statement 3 — the systems paper hiding inside this one

> On a multi-GPU consumer host without a fast interconnect, the usable context ceiling is a property
> of the tensor split, not of the quantization. A published ceiling without its split is not a
> reproducible number. The optimum is quant-specific, non-monotone, and in one case a single
> feasible island in the ratio space.

The most immediately *useful* result here and the one most likely to be cited by practitioners and
tooling authors rather than researchers. Large effect (+33 % context and +93 % decode from one flag
in the motivating E11c measurement; 131,072 → 212,992 on Q6_K_XL against a previously published
ceiling), binary evidence, reproducible from the artifact. It also carries the paper's broader theme
— *a number published without its configuration is not a measurement* — which is the same theme as
the reproducibility register.

**Recommendation: lead with 1, pair 1 and 2 as the paper's argument, and give 3 its own results
section rather than burying it under "systems findings".**

---

## 3. The saturation thesis is wrong for two of its three instruments — fix this first

This is my sharpest structural criticism and it must be resolved before a word is drafted.

`OUTLINE.md` states: *"The common cause is not modality and not context length but saturation: each
benchmark has a ceiling, and a quantization difference cannot be seen while both arms sit against
it."* PN-34 repeats it: *"every one of these instruments has a ceiling, and a quantization difference
is invisible whenever both arms sit against it."*

Check it against the measured scores:

| instrument | score | headroom to ceiling | saturated? |
|---|---|---|---|
| HellaSwag (n=400) | 82.25–83.25 % | **~17 points** — frontier models exceed 95 % | **No.** Not remotely. |
| HumanEval+ base (n=164) | 93.90 / 94.51 % | ~5 points | Near-ceiling, not at it. |
| RULER S-NIAH (n=12–25) | 100.0 / 100.0 | **zero** | **Yes.** Genuinely saturated. |

Only one of three is saturated. A reader who knows HellaSwag will spot this immediately, and it
discredits the paper's declared methodological through-line. Worse, the paper's own PN-22 already
gives the *correct* explanation for HellaSwag — argmax over a handful of candidate continuations,
plus the fact that it measures commonsense reasoning and not coding at all — which is a
*scoring-mode and domain* argument, not a ceiling argument. The outline overwrote a correct
mechanism with an incorrect unifier.

**The recent literature supplies the exact vocabulary to fix this.** arXiv:2602.16763 (*When AI
Benchmarks Plateau*, 2026-02-18) defines **saturation** as (1) statistically alike performance among
top models **and** (2) performance approaching the benchmark's empirically inferred ceiling —
whereas **stagnation** is (1) *without* (2). By that definition:

- HellaSwag here shows **stagnation without saturation**, and for a domain reason.
- HumanEval+ shows **stagnation**, near but not at ceiling.
- RULER S-NIAH shows **true saturation**.

Adopting saturation-vs-stagnation costs one sentence and converts a falsifiable overclaim into a
precise, citable one. It also lets the paper make a *sharper* point than it currently does: three
instruments fail to resolve the ladder for **three different reasons**, which is a better finding
than one reason, because it means there is no single benchmark fix. Raising sample size fixes none
of them; raising difficulty fixes only the saturated one; changing domain fixes only HellaSwag.

The complementary tool is Item Response Theory / Fisher information (arXiv:2505.15055): items solved
or failed by every arm carry no information about ability differences. On HumanEval+ the paper has
the per-problem outcome vectors in `s9-scores.json` and could report **how many of the 164 items are
discriminating at all** (answer: 3 on base, 5 on plus). That is the formal version of the paper's
intuition and it is one afternoon of analysis with zero GPU time.

---

## 4. Novelty, priority, and the one hook worth building on

I checked the literature specifically for prior claims. Three findings are serious — one novelty
threat, one priority problem, one direct challenge to the primary instrument — and one is a gift.
None is fatal; all four change how the paper must be positioned.

### 4.1 The "benchmarks can't see it, divergence can" claim is already published

**Dutta, Krishnan, Kwatra, Ramjee (Microsoft Research India), *Accuracy is Not All You Need*,
NeurIPS 2024 — https://arxiv.org/abs/2407.09141.** Shows that even when baseline and compressed
accuracy match, behaviour differs; introduces "flips" (answers changing correct↔incorrect); and
shows **KL divergence correlates with flips** while accuracy hides generative degradation.

That is contribution 2 of the current outline, published two years earlier, at NeurIPS, at scale.
**As written, the outline's headline is not novel.** Fireworks (2024-08) makes the same argument
industrially, and Unsloth's own documentation states it verbatim: *"Using perplexity is incorrect
since output token values can cancel out, so we must use KLD or harder benchmarks."*

Consequences, in order of importance:

- **Statement 1 (tail concentration) becomes the load-bearing contribution**, because it is the part
  Dutta et al. do not have. They show divergence detects what accuracy misses; this paper shows
  *where in the distribution the divergence lives*, that it is domain-dependent, and that its shape
  inverts between the median and the tail.
- **Cite Dutta et al. in the second paragraph of the introduction**, not in related work. A reviewer
  who finds it themselves on page 9 concludes the author did not read the field.
- **Reframe the three-instrument sweep** from "we discovered benchmarks are blind" to "we tested,
  at consumer scale and on the target domain, whether the published warning applies to the GGUF
  ladder practitioners actually choose from — and quantified how large the resulting task-level
  bound is." That is a legitimate and useful contribution. Overclaiming it is not.

### 4.2 PN-23 was independently reported six weeks before the S8 measurement

**llama.cpp Issue #25618 — "Speculative decoding (draft-mtp / draft-dspark): greedy output diverges
from vanilla on quantized targets" — https://github.com/ggml-org/llama.cpp/issues/25618**, opened
**2026-07-13**, still open with no maintainer reply. S8 ran **2026-08-30**. The finding here is
therefore *independent* but **not first**, and the paper must say so plainly. A reviewer who finds
the issue after reading a priority claim will discount the whole paper.

But this is far more opportunity than threat, for one reason: **the issue reports that the same
setups match on a bf16 target and diverge on a quantized one**, with ngram speculation as a control
that stays lossless on the same quantized target. That is a mechanism hypothesis — *quantized target
compute under the changed multi-token batch shape of a model-drafted speculative path* — which is
precisely what PN-23 records as "NOT established" and PN-26 leaves open as "where in the verification
the difference arises."

Three consequences:

1. **The spec-decode result stops being a detached curiosity and joins the paper's thesis.** If
   non-equivalence is a *quantization* phenomenon, then §5.5 is no longer a separate finding — it is
   the same finding in a second dimension: quantization perturbs exactly the marginal decisions that
   a speculative verifier must reproduce.
2. **Report the priority honestly and claim the right thing.** #25618 has anecdotes and an
   accept-count table. This study has 164 paired problems, a byte-exact determinism control across
   two runs a day apart, first-divergence position distributions, and the **Jaccard 0.610 overlap
   between the n=2 and n=4 divergence sets** — a datum nobody else reports and the single best piece
   of evidence distinguishing "broken verification rule" from "batch-shape-dependent numerics."
   Frame as *independent quantitative characterisation of an open engine defect*.
3. **Note the contradictory published result.** arXiv:2606.25097 (*Speculative Decoding at
   Temperature Zero*, 2026-06-23) runs 16,783 + 44,066 samples on fp16/bf16 and **GPTQ-4bit**
   variants on vLLM stacks with byte-identity evidence plus TOST equivalence at ±3 pp, and finds
   invariance **holds**. So the literature now contains a stack where it holds and two independent
   reports of a stack where it does not. That is a genuinely interesting state of affairs and the
   paper is well placed to describe it — much better than asserting a universal violation.

There is also an "everyone builds on the untested assumption" citation available: arXiv:2604.26469
(*An Empirical Study of Speculative Decoding on Software Engineering Tasks*) assumes losslessness
throughout and never tests it. That is why the operational conclusion — *a speculative setting is
part of the accuracy configuration, not a free speed knob* — is worth publishing even without
priority.

Cite the original guarantee properly: Leviathan, Kalman & Matias (https://arxiv.org/abs/2211.17192)
and Chen et al. (https://arxiv.org/abs/2302.01318) prove distribution preservation *in exact
arithmetic*. The gap between the theorem and the shipped quantized implementation is the result —
not a rebuttal of the theorem. PN-23 already phrases this exactly right; put that sentence in the
paper.

### 4.3 The sharpest hook the paper has: a published, specific losslessness claim (R12)

The general form — "speculative decoding is lossless" — is folklore, and folklore is hard to cite
and easy to be accused of strawmanning. **R12 removes that problem.** The MLX port of DFlash
(https://github.com/Aryagm/dflash-mlx, implementing Chen, Liang & Liu, *DFlash: Block Diffusion for
Flash Speculative Decoding*, https://arxiv.org/abs/2602.06036) states in its own documentation that
its speculative decoding is **"bit-for-bit identical to plain target decoding"**, and describes the
verification rule concretely — accept the longest matching prefix plus one bonus correction token.

That is a specific, attributable, checkable claim about a shipped implementation, made about the
same drafter family this study benchmarks (PN-29). It is the ideal foil, and it should be quoted
verbatim in §5.5's opening paragraph. The structure of the argument then writes itself:

> A published implementation of this drafter family states that its speculative decoding is
> bit-for-bit identical to plain target decoding. On the engine and quantization measured here, the
> built-in MTP path is not: it reproduces the unspeculated baseline on 131 of 164 problems, and
> both paths reproduce *themselves* byte-identically, so the difference is deterministic and
> systematic rather than noise.

**The precision that makes this defensible, and it must not be skipped.** We did not measure
DFlash's own implementation losslessly — PN-25 and PN-29 record that the DFlash2 arm ran on a
*different engine build*, so its 132/164 equivalence figure is engine-confounded and must never be
quoted beside MTP's. **This study therefore does not contradict DFlash's claim.** The claim it
supports is one level up and is stronger for being carefully bounded:

> **Losslessness is an implementation property that must be verified per stack. It is not inherited
> from the algorithm's specification, and a claim of bit-exactness in one implementation licenses
> nothing about another.**

Three reasons this is the best framing available for §5.5:

1. **It converts a negative result into a methodological rule** — the same move that makes the
   reproducibility register work. "This engine diverges" is a bug report; "verify per stack, here is
   the cheap instrument that does it, and here is what it costs" is method.
2. **It resolves the priority problem in §4.2** without awkwardness. #25618 has priority on the
   *observation* in llama.cpp. Nobody has priority on the *general claim*, because nobody has run
   the paired-problem comparison with a determinism control against a specific published assertion.
   That is what this study has.
3. **The evidence set is now unusually complete for a claim of this shape**: a published assertion
   of bit-exactness (R12), an independent open defect report on a different backend (#25618), a
   published study finding invariance *does* hold on a third stack with TOST at ±3 pp
   (arXiv:2606.25097), a widely-used downstream study that assumes losslessness and never tests it
   (arXiv:2604.26469), and this study's 164 paired problems with byte-exact self-reproduction. Five
   independent points, three verdicts, one clear conclusion about what may be inferred from which.
   Very few sections in this paper are that well supported.

**One concrete recommendation.** Add a short table to §5.5: *implementation · target precision ·
verification path · claim made · claim verified how · verdict*, with rows for DFlash-MLX (claimed
bit-exact, unverified here), llama.cpp MTP on UD-Q6_K (measured, 131/164), llama.cpp MTP self-repeat
(measured, 164/164), llama.cpp draft-dspark/draft-mtp on quantized targets per #25618 (reported,
diverges), the same on bf16 per #25618 (reported, matches), and vLLM/GPTQ-4bit per arXiv:2606.25097
(measured, invariant). That table is the section, and it is the kind of synthesis a reader cites.

### 4.4 The dangerous paper, which must be cited and answered

**Nikolić, Zadeh, Torres Sanchez, Moshovos (Toronto), *Displacement Is Not Direction: Evaluating
Fidelity Metrics for Quantized LLM Deployment*, 2026-06-17 —
https://arxiv.org/abs/2606.19558.** Across a 28-quant cohort of Qwen3.6-35B-A3B and a 41-quant
cohort of Devstral-Small-2-24B, KLD correlates strongly with benchmark score **over the full
cohort** (ρ = −0.72 / −0.86, p < 0.001) — **but the relationship collapses to non-significance in
the near-baseline "silent zone"** (ρ = +0.00 on Qwen; ρ = −0.24, p = 0.36 on Devstral).

**This study's entire ladder lives in that silent zone** (code KLD 0.0058–0.0215; task-prompt KLD
0.0104–0.0361). A hostile reviewer will use this paper to argue that the divergence ladder does not
license any ranking claim at all.

They are right, and the paper should agree with them out loud. Handled well this is a gift, because
the two results are complementary rather than contradictory:

- They show KLD does not predict *benchmark score* in the near-baseline band.
- This paper shows *why*: in that band the benchmarks themselves have no resolution (3 discordant
  items out of 164), so there is no score signal for KLD to correlate with. Their null is this
  paper's finding viewed from the other side.
- The correct joint conclusion — and it is a good one — is that **in the near-baseline band, neither
  instrument ranks, and the honest output of a small-sample quantization study is a divergence
  measurement plus an equivalence bound, not a ranking.**

This makes §5 of this review (equivalence bounds instead of p-values) not merely advisable but
**necessary**. It also imposes a hard discipline on the paper's language: it must never say
UD-Q6_K is *better for your coding agent* than UD-Q4_K_XL. It may say the distributions differ by
3.69×, that the single-turn task effect is bounded at ≤ 4 points, and that whether the difference
compounds over long horizons is unmeasured. Those three sentences are defensible against
arXiv:2606.19558. Anything stronger is not.

---

## 5. Report equivalence bounds, not p-values — the highest-value free change

PN-28 reports the generative anchor as "McNemar p = 1.0, no distinguishable difference", and the
outline elevates it to "the generative coding benchmark cannot separate the ladder's two extremes
either." Both are true and both undersell the result badly, because **a p-value is not the
informative statistic for a paired design with three discordant pairs.** The informative statistic
is the interval on the paired difference.

I computed it (Newcombe score interval for paired proportions, from the discordance counts in
`data/raw/e12/s9/s9-scores.json` `s6_paired`):

| metric | b (Q4 only) | c (Q6XL only) | Δ pass@1 | **95 % CI on the paired difference** | 90 % CI |
|---|---|---|---|---|---|
| HumanEval base | 1 | 2 | −0.61 pts | **[−3.81, +2.41]** | [−3.13, +1.77] |
| HumanEval+ (base+extra) | 2 | 3 | −0.61 pts | **[−4.08, +2.76]** | [−3.41, +2.11] |

An *independent* two-arm comparison at n=164 carries roughly ±5.3 points; the paired analysis is
about 1.7× tighter. So the correct sentence is not "the benchmark cannot see it." It is:

> **A 3.69× increase in code-prompt KL divergence — the full width of this quantization ladder —
> changes HumanEval+ pass@1 by at most about four points, and most plausibly by under one.**

That is a *bounded, quantitative bridge between the two instruments*, and it is the single number a
practitioner reading this paper most wants. It repositions the paper from a defensive posture
("your instruments are wrong") to a constructive one ("here is what each instrument can tell you,
and here is the exchange rate between them"). Reviewers reward the second and punish the first — and
after §4.4, it is the only defensible posture available.

Method references, all directly applicable and all cited in §12:
- **Wilson rather than Wald** at small n — Brown, Cai & DasGupta, *Statistical Science* 16(2), 2001.
- **McNemar for paired per-problem comparison** — Dietterich, *Neural Computation* 10(7), 1998,
  which specifically endorses it as the only acceptable test when each algorithm can be run once.
  That is exactly this study's regime.
- **TOST / equivalence testing**, or a Bayesian ROPE (Benavoli et al., JMLR 18, 2017) reporting
  P(A better) / P(within ROPE) / P(B better). Note arXiv:2606.25097 already uses TOST at ±3 pp for
  a speculative-decoding equivalence claim, so this is established practice in the immediate
  neighbourhood.
- **Minimum detectable effect** — Card et al., *With Little Power Comes Great Responsibility*,
  EMNLP 2020. Compute and state the MDE for HumanEval+ at n=164 and HellaSwag at n=400 *as a
  designed result*, not as an apology.

Apply the same treatment to HellaSwag (report the paired discordance of 2–4 items out of 400, which
is the informative quantity, not four overlapping Wilson intervals) and to RULER (12/12 gives Wilson
[75.7, 100.0] — that arm bounds essentially nothing, and the paper should say so plainly).

**Consequence for the closing argument.** The honest final position becomes stronger, not weaker:

> Quantization damage is real, tail-concentrated and domain-amplified. At the single-turn task scale
> these benchmarks measure, its effect is bounded small. Whether tail damage *compounds* over
> long-horizon agentic work — where a model makes thousands of decisions and each is a draw from the
> perturbed tail — is the question that matters, and it is unmeasured, including here.

That is the paper's best closing line. It is honest, it names the open problem precisely, and it is
the sentence that gets the paper cited by whoever runs the agentic experiment next.

---

## 6. Recommended full outline, with PN mapping and target lengths

Target: **18–22 pages single-column preprint format**, ≈ 9,000–10,500 words of body plus appendices.
Six figures, five tables in the body. Word counts below exclude captions.

### Front matter — 350 words
Title, single author, abstract (§9), keywords. **Artifact DOI on page 1 as a footnote** — see §8;
arXiv's format policy requires that any code/data link resolve to a *publicly available* repository.

### §1 Introduction — 950 words
Frame as a practitioner question with a measurement answer, not as a critique. Opening: a solo
researcher with two 16 GB consumer GPUs must choose one quantization of a 27B coding model; the
available instruments disagree, and three of them give no answer at all.

**Cite Dutta et al. (2407.09141) in the second paragraph** — the field already knows accuracy hides
compression damage. State what this paper adds: the shape of the damage, its domain dependence, and
a quantified bound on its task-level consequence at consumer scale.

Contributions, revised — five, in this order:
1. Quantization damage on code is **tail-concentrated**: code/prose amplification runs 0.005× at the
   median to 8.09× at the 99th percentile, crossing 1.0 between p90 and p95. The familiar "2× worse
   on code" is an artifact of that shape. — **PN-13, PN-14, PN-16, PN-21 + the unreported quantile
   fields**
2. Damage rises monotonically as the corpus approaches the task (prose → generic code → task
   prompts, 3.13–4.40×), and the amplification itself grows with aggressiveness. — **PN-21, PN-14**
3. Three task instruments spanning three scoring modes bound the end-to-end effect of the full
   ladder at **≤ ~4 points**, and lack resolution for three *different* reasons — domain and argmax
   scoring, near-ceiling stagnation, and true saturation. — **PN-22, PN-28, PN-33, PN-34**
4. The usable context ceiling on this host is a property of the **tensor split**, not the
   quantization; the optimum is quant-specific, non-monotone, and in one case a single feasible
   island. — **PN-6, PN-7, PN-8**
5. Speculative decoding on this engine is **deterministically non-equivalent** to unspeculated
   decoding, independently corroborating an open engine defect report with paired-problem
   statistics and a byte-exact determinism control. — **PN-23, PN-26**

Close with one paragraph of scope: one model family, one engine image, one host, ladder-relative
reference. Here, not only in §8. A reader who finds the limitation themselves on page 14 distrusts
everything before it.

### §2 Background and related work — 1,100 words
Three threads, not a list:
- **The instrument thread** — PPL's averaging bias and the case for KLD (R2, R4, R10, Dutta et al.);
  the tool (R1); who ranks quantizations on it in practice (R3, R5). **Include arXiv:2606.19558
  here and answer it** (§4.4) — do not leave it to threats-to-validity, because it is a claim about
  the primary instrument.
- **The evaluation thread** — task batteries applied to llama.cpp quantization (arXiv:2601.14277,
  read as the nearest neighbour and the caution); error bars, paired differences and power (R6, Card
  et al., Dietterich); benchmark saturation and stagnation (arXiv:2602.16763, arXiv:2607.01254,
  IRT/Fisher information via arXiv:2505.15055); long-context evaluation (R8).
- **The closest published work** — Red Hat's RULER-at-quantization study and arXiv:2505.20276 (R9),
  which reach *opposite* conclusions about whether quantization survives long context; say so, and
  position this study's bounded S-NIAH result relative to both.

### §3 Setup — 750 words + Table 1
Host, engine pinned by image digest, four arms, the `env-manifest.json` provenance discipline.
Table 1 = arm × file size × sha256 prefix × role × ceiling × winning `-ts`.

**PN-1 through PN-4 belong here as a short "harness validation" subsection, framed as results**:
measured sampling defaults match neither the documented engine defaults nor either official preset
(PN-1); thinking is on by default and the widely-cited disable idiom raises a Jinja exception (PN-2,
PN-3); `-fit` cannot be trusted to bound allocation (PN-4). 200 words, and it earns its place
because it tells the reader every downstream number was produced under an asserted contract.

PN-31 as a **two-sentence footnote** to the host spec, per owner direction, keeping the one
generalisable clause: *the standard divergence tooling's resident footprint scales with context
length, which is why the published quantization tables it produces are all measured near 2K.*

**Add the AI-conduct disclosure paragraph here** (§8).

### §4 Method — the Small-Sample Accuracy protocol — 950 words + Table 2
The design principle once and clearly: **divergence instruments draw power from token count; task
benchmarks draw it from problem count.** Reference-arm choice and its ladder-relative consequence.
The 65,536-token budget. Pre-registered interpretation bands (<0.007 Fireworks; 0.01–0.03
LocalBench) declared as external reference points, not adopted rules.

**Add a subsection the outline lacks: "What we report, and what we refuse to report."** Three rules
— every table names protocol, n and estimator; a comparison is reported as an equivalence bound
rather than a p-value; a claim enters only if the interval separates or the effect exceeds the
interval width. This is the paper's methodological spine and deserves 150 words in Method, not just
a bullet in a repo README.

Table 2 = the instrument inventory: instrument, unit of power, n, wall-clock, arms separated.

### §5 Results — ≈ 4,300 words

**5.1 The shape of the damage — 900 words · Figure 1, Figure 2, Table 3.**
The paper's opening result. Quantile decomposition; the p90–p95 crossover; the mean sitting in the
tail; the top-1/mean-KLD reconciliation (PN-16) delivered as mechanism rather than caution; RMS Δp
corroborating (1.60/1.78/2.46 % prose → 3.34/4.38/6.24 % code → 4.71/5.95/8.39 % task).
**PN-13, PN-14, PN-16, PN-21.**

**5.2 Domain and the distance to the task — 550 words · Figure 2, Table 3.**
Three-tier hierarchy, monotone in every domain, 3.7–11.8 σ between adjacent arms. The
threshold-crossing statement (two of three arms pass on prose, one on generic code, none on the task
distribution) with the external-band caveat in the same sentence. **PN-21, PN-14, PN-13.**

**5.3 What three task instruments can and cannot bound — 1,050 words · Figure 3, Table 4.**
Rewritten per §5 of this review. All three as *bounds*, with the three distinct mechanisms of §3:
HellaSwag (n=400, 4 arms, paired discordance 0–4 items, most-quantized arm nominally highest — wrong
domain, argmax scoring, **stagnation not saturation**);
HumanEval+ (n=164 paired, discordance 3 and 5, **95 % CI [−3.81, +2.41] and [−4.08, +2.76] points**,
near-ceiling stagnation);
RULER S-NIAH (100.0/100.0 at 8,192 / 32,768 / 131,072 — sixteen-fold context, zero discrimination,
Wilson [75.7, 100.0] at the deepest rung; **true saturation**).
MK-NIAH in **one paragraph** as a hypothesis with its interval: 100.0 vs 91.67 on one discordant
sample of twelve, overlapping intervals, consistent with Red Hat's published 85–88 % band for INT
W4A16 at 128K, *not established here*.
Close with the reconciliation: the discordance rates are what tail concentration predicts.
**PN-22, PN-28, PN-33, PN-34.**

**5.4 The context ceiling belongs to the split — 700 words · Figure 4, Table 5.**
The same configuration failing at the default split and loading at five ratios; the quant-specific
non-monotone optimum; Q6_K_XL's single feasible island; balance and throughput as opposing
objectives (the most balanced ratio is the slowest by 27 %). State the constraint physically —
weights *and* a layer's KV slice live on one card, no NVLink, so the binding limit is per-card, not
the aggregate. **PN-6, PN-7, PN-8.**
*Cite Heiser's benchmarking crime 4.3 here*: comparing quants at the engine default split, when each
quant has a different optimal ratio, is unfair-competitor evaluation. Per-arm winning ratios are the
methodologically correct choice and the paper should say why.

**5.5 Speculative decoding is part of the accuracy configuration — 750 words · Figure 5.**
Non-identity at greedy (131/164); PN-26's determinism control upgrading it to *deterministically*
non-equivalent. Retract PN-23's own mechanistic speculation in the text — PN-26 does this correctly
and that visible self-correction is a credibility asset. **Cite llama.cpp #25618 for independent
corroboration and priority, and adopt its quantized-target hypothesis** (§4.2), which connects this
section to the paper's thesis instead of leaving it orphaned. Note the contradicting published
result (arXiv:2606.25097). The context-dependent method ranking: DFlash2 fastest at 32 K, unable to
reach the deployment window at all. Acceptance falls monotonically with draft depth in 12 of 13
adjacent pairs (sign test p = 0.0017). **PN-23, PN-26, PN-29, PN-32.** Explicitly do **not** report
a draft-depth ranking — PN-32 says it is unanswerable at n=3.

**5.6 Speed does not discriminate; KV quantization is not free — 400 words.**
Speed: 6.7 % span across arms against 32.9 % within-arm noise; the cheaper arm is not faster, only
less accurate, and earns its place on VRAM footprint alone (**PN-19**).
KV: q4_0 costs 0.002955 ± 0.000127 KLD against f16 — 51 % of a quantization level — while perplexity
on the identical pair moves +0.15 %, the paper's cleanest single demonstration of averaging bias
(**PN-15**). That PPL/KLD contrast belongs in the abstract.
**Two external comparisons must appear here**, because a reader will find them: QLLM-Eval (ICML
2024) reports that for context ≥ 4K most LLMs are *more* sensitive to KV-cache quantization than to
weight-only quantization at the same bit-width — which is the strongest reason PN-15's "measured at
n_ctx 2048" caveat matters; and oobabooga's published KV-cache KLD for Qwen 3.6 27B at q4_0 is
0.087–0.117, an order of magnitude above this study's 0.002955. Different model version, corpus,
top-K truncation and possibly reference, so **do not put them in one table** — but the qualitative
agreement (q4_0 KV is usable on Qwen-family models, unlike Gemma) is real corroboration and worth a
sentence. Likewise note that a practitioner report on the *same GPU and engine* (InventiveHQ) claims
q4_0 KV "severely damaged output quality"; a blog-grade claim with no reference model or interval
against a measured KLD with a CI is a comparison the paper wins, but only if it makes it.

### §6 What the measurements cost — 500 words, referencing Table 2
Keep this — it is unusual and it matters to this paper's actual audience. But **fix the number.**
`README.md`, `OUTLINE.md` and PN-34 all claim "~20 minutes of divergence per arm resolves what
~20 hours of task benchmarking does not." From the artifacts' own `started_utc`/`finished_utc`:

| instrument | wall clock | arms separated |
|---|---|---|
| SSA S1–S4 divergence, 2 domains + KV control (10 cells) | 1 h 57 m | **3 of 3** |
| SSA S5 task-prompt divergence (4 cells) | 22 m | **3 of 3** |
| SSA S7 HellaSwag, n=400 × 4 arms | 32 m | 0 |
| S8 HumanEval+, 4 spec configs × 164 | 1 h 38 m | 0 (ranks spec, not quants) |
| S9b generative anchor, 2 arms × 164 paired | 1 h 26 m | 0 (bounds at ±4 pts) |
| S9c DFlash2 | 42 m | 0 |
| S9d draft-depth sweep, 24 cells | 3 h 47 m | 0 (unanswerable at n=3) |
| S12 RULER, 8 cells | 3 h 14 m | 0 |

≈ **2.3 h of divergence resolving the ladder against ≈ 11.4 h of task and speculation benchmarking
that does not**. A 5× contrast is entirely sufficient and defensible from the artifacts. "20 hours"
is not, unless it counts the pre-E12 SWE-bench corpus — in which case say so. This is a number a
checking reader can falsify in five minutes.

### §7 Threats to validity — 950 words
Write before polishing results. Reorder so the two that matter most come first, and add four:

1. **Ladder-relative reference.** No FP16 fits the host; the reference's own degradation is
   unmeasured and zero by construction. Add the mitigating argument the outline omits: because the
   reference is itself ~6-bit, every arm's true distance from FP16 is *larger* than reported, so
   every claim is conservative in the direction that matters. Also reframe the quantity — this is
   *quantization-step* damage along a ladder practitioners actually choose from, arguably the more
   decision-relevant measure.
2. **NEW — the divergence metric loses ranking power in the near-baseline band** (arXiv:2606.19558),
   which is where these arms sit. Concede it explicitly, then give the joint reading of §4.4.
3. **Prompt-token divergence is not generation quality** — with the §5 bridge rather than a bare
   disclaimer.
4. **NEW — the compounding question is unmeasured.** Name it as the paper's principal open problem
   rather than letting a reviewer name it.
5. **NEW — one model family, one engine image, one host, two single-domain corpora.**
6. **NEW — calibration contamination** (R3): Unsloth's imatrix data is not published, so a
   wikitext-favourable bias cannot be excluded — itself an argument for weighting the code domain.
7. **KV fidelity measured at n_ctx 2048, not at depth** — with the QLLM-Eval citation that makes it
   a live risk rather than a formality.
8. Long-context accuracy bounded, not resolved (PN-33's n=12).
9. PN-9's quant/depth/ratio confound unresolved; no per-arm best draft depth reported.
10. Spec-decode results greedy-only.
11. No per-config energy figure.
12. Not comparable to published scores: logprob instruments run greedy; official presets are temp
    0.7/1.0; Qwen publishes LiveCodeBench v6, SWE-bench **Pro** and Terminal Bench, none set up here.

### §8 Conclusion — 350 words
Three sentences of result, one of consequence for practice, one of open problem. End on compounding.

### Appendix A — Practitioner configuration — 700 words
`TRACK-A-DECISION.md`, compressed, framed as *what this analysis implies for one concrete
deployment* and explicitly not the paper's recommendation. Amendment 2 and the reverted draft-depth
flag as a worked example of a withdrawn claim — one paragraph, not three.

### Appendix B — The reproducibility register — 900 words
**Cut from seven to four**, unified by one thesis: *silent success is the dominant failure mode of
automated benchmarking.* Keep the four that are structurally distinct:
- **PN-17** — a step scored by exit code alone reported a fully successful run that measured nothing
  (Unicode `±` vs ASCII `+/-`; 1.5 h of GPU recovered only because raw output was preserved). The
  SIGSOFT Benchmarking standard names this antipattern directly: *collecting aggregated measurements
  instead of persisting raw results for offline analysis.*
- **PN-5** — a contract documented in a docstring and never asserted in code is not a contract.
- **PN-30** — a throughput measurement that timed 17 generated tokens and produced 52 tok/s at
  ctx 131,072. Also withdrew a published claim, which makes it the most valuable of the four.
- **PN-25** — a drafter mis-bound to the wrong engine build produced a clean `0.000`
  indistinguishable from catastrophic performance.
Keep **PN-20** if space allows (an unnamed estimator reversing a ranking — the only one that changed
a conclusion). **Cut PN-10 and PN-27** (§10).

### Appendix C — Full tables — 600 words
Complete KLD tables with every percentile, Δp and RMS Δp; RULER departure notes and the
`variable_tracking` exclusion (an honest, well-reasoned exclusion that should be visible); the full
`-ts` sweep; per-repetition decode figures.

### Appendix D — Artifact index — 300 words
Every headline number → paper note → artifact path → serverlog. The mapping already exists and is
the paper's best defence against "we can't check this."

---

## 7. Figure specifications — written for PaperBanana's planner

**Constraint (R11).** Figures are to be produced with PaperBanana (arXiv:2601.23265,
`github.com/llmsresearch/paperbanana`), which is cloud-dependent and has no keys on this host.
Rendering therefore happens elsewhere. Each spec below is written to be pasted directly into the
pipeline's planner, and gives three things the planner needs:

- **(a) Description** — the figure in prose, at the detail level the planner expects: panel layout,
  what is on each axis, series, scales, annotations, reference lines, and the single sentence the
  figure must communicate.
- **(b) Data** — the artifact path under `data/raw/e12/`, the exact JSON field for every axis and
  series, and the shape of the flat file to extract.
- **(c) Type** — **methodology diagram** or **statistical plot**. PaperBanana treats these
  differently: diagrams go through the retriever/stylist path against reference exemplars, plots go
  through the CSV/JSON plotting path. Do not mix the two in one request.

**Prerequisite step, and it is not optional.** Every source artifact here is nested JSON, and
PaperBanana's plotting path wants **flat CSV or flat JSON**. Before any figure is requested,
extract each figure's data into a small file — I would put them in `manuscript/figures/data/` as
`figN-<name>.csv` — using the field paths given below. Extraction is a few lines of Python per
figure and no GPU time. Ship those CSVs with the artifact release too; they are what makes the
figures checkable.

**Two rules for every request.** First, the caption text belongs in the request, because the
critic loop will otherwise invent one — and every caption here must carry n, the estimator and the
protocol label, per the project's own rule. Second, state the colour and accessibility constraints
once per batch: colourblind-safe palette, no red/green as the only distinction, greyscale-legible,
and no reliance on colour alone to separate arms (use marker shape as well).

---

### Figure 1 — the measurement design
**(c) Type: methodology diagram.** *(New; the paper currently has no schematic, and this is the
figure that makes §4 legible. PaperBanana's diagram path is the reason to add it.)*

**(a) Description.** A single-panel schematic, landscape, reading left to right in three columns.

*Left column, "Arms":* four stacked boxes labelled UD-Q6_K_XL (25.30 GB, **reference**), UD-Q6_K
(21.98 GB), UD-Q5_K_XL (20.88 GB), UD-Q4_K_XL (17.56 GB), ordered top to bottom from least to most
quantized, with a vertical arrow beside them labelled "increasing quantization". Mark the reference
arm distinctly (a filled box or a small anchor icon) and annotate it "all divergence is measured
relative to this arm — no FP16 fits the host".

*Middle column, "Instruments", split into two groups separated by a horizontal rule:*
Group A, **divergence** (one box): "KL divergence vs reference · `llama-perplexity --kl-divergence`
· 3 domains · 65,536 tokens per cell · power from **token count**".
Group B, **task benchmarks** (three boxes): "HellaSwag · n=400 · argmax over candidates";
"HumanEval+ · n=164 paired · unit-tested generation"; "RULER S-NIAH / MK-NIAH · n=12–25 ·
string match at 8K/32K/131K". Label the group "power from **problem count**".

*Right column, "Result":* one box per instrument row. Group A's reads "separates all 3 arms,
3.7–11.8 sigma, non-overlapping intervals". Group B's three read "1.0-pt spread, most-quantized arm
nominally highest", "paired difference bounded [-4.1, +2.8] pts", "100.0 vs 100.0 at every length".

*Bottom band, spanning the full width:* a horizontal cost bar comparing 2.3 GPU-hours (Group A)
against 11.4 GPU-hours (Group B), drawn to scale.

The sentence the figure must communicate: **divergence instruments draw statistical power from
token count and task benchmarks from problem count, which is why one resolves this ladder in a
fraction of the other's GPU time.**

Style: clean academic schematic, thin rules, no drop shadows, no gradients, no 3D. Boxes with
1-pt borders and generous internal padding. Sans-serif labels. Two accent colours at most — one for
the divergence path, one for the task path — plus greys.

**(b) Data.** No plotted data; all values are literals given above. They trace to
`data/raw/e12/ssa/ssa-results-parsed.json`, `ssa/ssa-s7-results.json`, `s9/s9-scores.json`,
`ruler/s12-ruler.json`, and the wall-clock table in §6 of this review.

---

### Figure 2 — where the damage is *(the paper's signature figure)*
**(c) Type: statistical plot.**

**(a) Description.** Single panel, line plot with markers. The x-axis is a **categorical quantile
axis** with four evenly spaced positions labelled "median", "p90", "p95", "p99" — these are
quantiles of the per-token KL-divergence distribution, not numeric values, so spacing is uniform.
The y-axis is the **code ÷ prose amplification ratio** on a **log scale**, spanning roughly 0.003 to
20.

Three series, one per quantization arm: UD-Q6_K, UD-Q5_K_XL, UD-Q4_K_XL. Distinguish by both colour
and marker shape (circle, square, triangle). Each series is a connected line through its four
points.

A heavy horizontal reference line at **y = 1.0**, drawn in a neutral grey, labelled inline at the
right-hand edge: "code and prose equally affected". Shade the region below it very lightly and
annotate the shaded band once, at the left, "code less affected than prose"; annotate above the
line, at the right, "code more affected".

On each series, add a small open marker with a short leader line showing where that arm's **mean**
amplification falls on the y-axis (1.76×, 2.30×, 2.62×), positioned horizontally between the p95
and p99 ticks, labelled "mean" on the topmost series only. This is the point of the figure: the
commonly quoted mean sits out in the tail.

The sentence the figure must communicate: **ninety per cent of code tokens are less perturbed by
quantization than prose tokens; the top one per cent are up to eight times more; the commonly
quoted 2x mean is the average of these two opposite facts.**

Caption to render with it: "Code-to-prose amplification of per-token KL divergence, by quantile of
the divergence distribution. Reference arm UD-Q6_K_XL; n = 65,536 tokens per cell; uncertainties as
emitted by `llama-perplexity --kl-divergence`. Protocol: SSA, n_ctx 2048 x 32 chunks, q4_0 KV."

**(b) Data.** Source: `data/raw/e12/ssa/ssa-results-parsed.json`, list `cells`, entries keyed by
`label`. For each arm A in {Q6_K, Q5_K_XL, Q4_K_XL}, take the prose cell `ssa-{A}-wikitext2-kld`
and the code cell `ssa-{A}-code-kld`, and read from each cell's `metrics_reparsed` object the
fields `median_kld`, `kld_90p`, `kld_95p`, `kld_99p`, `mean_kld`. The plotted value at each
quantile is `code[field] / prose[field]`.

Extract to `fig2-tail-amplification.csv` with columns `arm, quantile, code_kld, prose_kld, ratio`
and one row per (arm, quantile) — 12 rows, plus 3 rows with `quantile = "mean"`. The ratios are:

| arm | median | p90 | p95 | p99 | mean |
|---|---|---|---|---|---|
| UD-Q6_K | 0.005 | 0.45 | 1.53 | 4.99 | 1.76 |
| UD-Q5_K_XL | 0.006 | 0.54 | 1.89 | 6.71 | 2.30 |
| UD-Q4_K_XL | 0.005 | 0.61 | 2.18 | 8.09 | 2.62 |

**Optional panel (b).** Same construction with the HumanEval+ task-prompt domain in place of code:
source `data/raw/e12/ssa/ssa-s5-results.json`, cells `ssa-{A}-humaneval-kld`, same five fields,
divided by the same prose cells. That series is uniformly above 1.0 from p90 upward — cleaner but
less surprising, so keep it as a second panel rather than crowding panel (a). Note n = 18,432
tokens per cell there, not 65,536, and say so in the caption.

---

### Figure 3 — the ladder, three domains, one instrument
**(c) Type: statistical plot.**

**(a) Description.** Single panel, **dot plot with horizontal error bars** — explicitly *not* a bar
chart, because bars imply a zero baseline that a divergence has no right to.

The x-axis is **mean KL divergence on a log scale**, spanning roughly 0.002 to 0.05. The y-axis is
categorical: nine rows, grouped into three blocks of three by quantization arm (UD-Q6_K at the top,
then UD-Q5_K_XL, then UD-Q4_K_XL), and within each block one row per domain in the order WikiText-2
(prose), django (code), HumanEval+ prompts (task). Label the blocks on the left with the arm name
and the rows with the domain name. Insert visible whitespace between blocks.

Each point carries a symmetric horizontal error bar of ± the reported standard error. At this scale
the bars will be smaller than the markers for most rows — that is the point, and the caption must
say so.

Two shaded vertical bands behind the data: a darker one from 0 to 0.007 labelled "Fireworks:
high-quality deployment", and a lighter one from 0.01 to 0.03 labelled "LocalBench: observed Q4_K_M
range". Label both bands at the top of the panel. These are external reference points, not this
study's pass/fail rule, and the caption must say that too.

Use one marker shape per domain (circle for prose, square for code, diamond for task) so the domain
pattern is readable in greyscale.

The sentence the figure must communicate: **divergence is monotone in every domain and rises as the
corpus approaches the task, and the published quality verdict flips with the domain — two of three
arms pass on prose, one on generic code, none on the actual task distribution.**

Caption: "Mean KL divergence against the UD-Q6_K_XL reference, by arm and domain. Error bars are
±1 SE as emitted by the tool. n = 65,536 tokens per cell (18,432 for HumanEval+ prompts). Bands are
external reference points from published practice, not this study's criteria. Divergence is
ladder-relative: the reference arm's own distance from FP16 is unmeasured."

**(b) Data.** Sources: `data/raw/e12/ssa/ssa-results-parsed.json` (prose cells
`ssa-{A}-wikitext2-kld`, code cells `ssa-{A}-code-kld`) and `data/raw/e12/ssa/ssa-s5-results.json`
(task cells `ssa-{A}-humaneval-kld`), for A in {Q6_K, Q5_K_XL, Q4_K_XL}. From each cell's
`metrics_reparsed`, read `mean_kld` (x position) and `mean_kld_err` (error bar half-width).

Extract to `fig3-ladder.csv` with columns `arm, domain, mean_kld, mean_kld_err, n_tokens` — 9 rows.
Values: prose 0.003321±0.000126 / 0.004465±0.000281 / 0.008207±0.000340; code 0.005829±0.000233 /
0.010285±0.000458 / 0.021529±0.000834; task 0.010403±0.000448 / 0.017285±0.000703 /
0.036129±0.001534.

---

### Figure 4 — one axis, two instruments *(the money shot)*
**(c) Type: statistical plot, multi-panel composite.**

**(a) Description.** Two panels **stacked vertically and sharing a single categorical x-axis**, with
the x tick labels drawn only under the lower panel. The x-axis is the four arms in ladder order,
left to right: UD-Q6_K_XL, UD-Q6_K, UD-Q5_K_XL, UD-Q4_K_XL. Panel heights roughly 55 % / 45 %.

*Upper panel — task instruments.* y-axis "accuracy (%)", linear, spanning about 75 to 102. Three
series:
1. HellaSwag, all four arms, with Wilson 95 % intervals as vertical error bars — the four points
   are nearly flat with heavily overlapping intervals.
2. HumanEval+ (base+extra), two arms only (UD-Q6_K_XL and UD-Q4_K_XL). Draw the two points, then —
   and this is the important annotation — draw a **horizontal bracket between them labelled with the
   paired 95 % confidence interval on the difference, "[-4.08, +2.76] pts (paired, n=164)"**. The
   paired interval is much tighter than the two independent intervals and is the honest statement;
   the figure must show that distinction rather than hide it.
3. RULER S-NIAH at 131,072, two arms, both at 100.0, with Wilson intervals [75.7, 100.0] — draw the
   intervals so the reader sees they bound almost nothing.
Distinguish the three series by marker shape and colour; put a compact legend inside the panel.

*Lower panel — divergence.* y-axis "mean KL divergence (code)", **log scale**. Three points
(UD-Q6_K, UD-Q5_K_XL, UD-Q4_K_XL) connected by a line, with ±SE error bars that are smaller than
the markers. The reference arm's x position is present but carries no point — annotate it "reference
(0 by construction)" with a small open marker on the axis.

**Do not** use a twin or shared y-axis across the panels; that would invite a false visual
equivalence between the two scales.

The sentence the figure must communicate: **the same four arms, the same host, the same fortnight —
flat and overlapping under three task instruments, monotone and cleanly separated under divergence.**

Caption: "Task-benchmark scores (upper) and code-domain KL divergence (lower) for the same four
arms. Upper: Wilson 95 % intervals; the bracket is the Newcombe 95 % interval on the paired
per-problem difference. Lower: ±1 SE, n = 65,536 tokens per cell. Note the different y-scales; the
panels are not comparable in magnitude, only in resolution."

**(b) Data.** Four sources.
- HellaSwag: `data/raw/e12/ssa/ssa-s7-results.json` — per-arm accuracy, n = 400. Values 82.75 /
  82.25 / 82.75 / 83.25 %; Wilson intervals [78.74, 86.14], [78.20, 85.68], [78.74, 86.14],
  [79.28, 86.59].
- HumanEval+: `data/raw/e12/s9/s9-scores.json`, block `arms.s6-Q6_K_XL` and `arms.s6-Q4_K_XL`
  (`scores.humaneval+`), plus block `s6_paired.tests[1]` for the discordance counts
  (`a_only` = 2, `b_only` = 3, `n_paired` = 164) from which the bracket interval is computed.
  Values 90.24 % and 89.63 %; paired interval [-4.08, +2.76] pts.
- RULER: `data/raw/e12/ruler/s12-ruler.json`, `cells` filtered to `task == "niah"` and
  `length == 131072`; both arms `score` = 100.0, `n` = 12.
- Divergence: `ssa-results-parsed.json` code cells as in Figure 3.

Extract to `fig4-instruments.csv` with columns `arm, instrument, value, ci_lo, ci_hi, n, panel`.

⚠️ **The RULER MK-NIAH row is deliberately absent from this figure** — see §13.1; the artifact is
not yet in the repository, and the result rests on one discordant sample. Do not add it here.

---

### Figure 5 — the context ceiling is a property of the split
**(c) Type: statistical plot, matrix/heatmap composite with a scatter inset.**

**(a) Description.** Main panel: a **categorical matrix**, four rows by seven columns.

Rows are the four arms, top to bottom in ladder order, each annotated on the right with the context
at which it was swept: UD-Q6_K_XL (196,608), UD-Q6_K (262,144), UD-Q5_K_XL (262,144), UD-Q4_K_XL
(262,144). Columns are the tensor-split ratio: `default`, `52,48`, `54,46`, `56,44`, `58,42`,
`60,40`, `62,38`.

Each cell is one of three states: **loaded** (filled, with the decode throughput in tok/s printed
inside in a small font), **failed** (hatched diagonally, with a compact failure-mode label —
`oom` for compute-buffer OOM, `hang` for init hang), or **not tested** (left empty with a light
grey outline). Use fill and hatch rather than red/green so the figure survives greyscale and
colourblind viewing.

Annotate the UD-Q6_K_XL row directly with a callout: **"a single feasible ratio, with failures on
both sides"** — that row is the punchline and must not be left for the reader to find. Annotate the
`default` column with a bracket labelled "the engine default fails for three of four arms".

Inset or second panel: a small **scatter plot**, x = VRAM imbalance between the two GPUs in MiB
(0 to 1,800), y = decode tok/s (8 to 12), showing UD-Q5_K_XL's five loading ratios, each point
labelled with its ratio. It must be visible that the *most balanced* ratio (`58,42`, 28 MiB
imbalance) is the *slowest* (8.50 tok/s). Draw no trend line — there is no monotone relationship and
implying one would be wrong.

The sentence the figure must communicate: **the usable context ceiling is set by GPU tensor
placement, not by the quantization; the optimum is quant-specific and not monotone-safe; and
balance and throughput are opposing objectives.**

Caption: "Load success and decode throughput across tensor-split ratios, each arm at the context
named on its row. Cells are single launches; failure modes are classified from the server log.
Inset: decode throughput against VRAM imbalance for UD-Q5_K_XL at 262,144, all five loading ratios.
Sampling: official non-thinking preset; q4_0 KV; MTP n=2; measured at >= 0.90 window depth."

**(b) Data.** Sources: `data/raw/e12/tsweep-v2-Q4_K_XL.json`, `tsweep-v2-Q5_K_XL.json`,
`tsweep-v2-Q6_K.json`, `tsweep-v2-Q6_K_XL.json`. Each has a `cells` list; per cell read `ts` (the
ratio string, `null` means the engine default), `ctx_requested`, `ok`, `failure_mode`,
`decode_tok_s`, `imbalance_mib`, `vram_peak_mib` (a two-element list, GPU0 and GPU1), and `rep`.
Filter to `rep == 1` and to each arm's swept context so the matrix has one cell per (arm, ratio).

Extract to `fig5-ceilings.csv` with columns
`arm, ctx_requested, ts, ok, failure_mode, decode_tok_s, imbalance_mib, vram_gpu0, vram_gpu1`.
The inset uses the UD-Q5_K_XL rows only, columns `ts, imbalance_mib, decode_tok_s` — 5 rows:
`54,46` 742 MiB / 10.82 · `56,44` 166 / 10.78 · `58,42` 28 / 8.50 · `60,40` 1,176 / 10.67 ·
`62,38` 1,750 / 10.44.

---

### Figure 6 — speculation buys speed and spends output identity
**(c) Type: statistical plot, two-panel composite.**

**(a) Description.** Two panels side by side, each a vertical bar chart over the same four
categories in the same order: `no-spec`, `MTP n=2`, `MTP n=4`, `DFlash2`.

*Left panel — speed.* y-axis "decode throughput (tok/s)" at ctx 32,768, linear, 0 to 60. Bars at
18.46, 37.44, 47.03, 51.78, each annotated above with its speedup against no-spec (1.00x, 2.03x,
2.55x, 2.80x). Sub-label the axis "median over 164 generations".

*Right panel — output identity.* y-axis "exact byte reproduction of the no-spec baseline (%)",
linear, 0 to 105, with a horizontal reference line at 100 %. Bars at 100.0 (no-spec self-repeat,
164/164), 79.9 (MTP n=2, 131/164), 79.9 (MTP n=4, 131/164), 80.5 (DFlash2, 132/164). Print the
fraction (e.g. "131/164") inside or above each bar.

Two annotations are load-bearing and must both appear. First, the DFlash2 bar in the right panel is
**hatched and labelled "engine-confounded"** — it ran on a different engine image, so an engine
difference is inseparable from the speculation effect. Second, the no-spec bar at exactly 100 % gets
a callout: **"the engine reproduces itself byte-exactly across runs a day apart"** — that control is
what makes this a determinism result rather than a noise result, and it must sit visually adjacent
to the 79.9 % bars.

Use a different fill for the right panel's bars than the left, so the two quantities are not read as
one.

The sentence the figure must communicate: **speculation raises throughput by up to 2.8x and
reproducibly changes the output on about one generated function in five; the engine itself is
deterministic, so this is a different decode path, not noise.**

Caption: "Decode throughput and byte-exact reproduction of the unspeculated baseline, 164 HumanEval+
problems, UD-Q6_K, ctx 32,768, greedy (temperature 0, top_p 1, fixed seed). The no-spec bar in the
right panel is a self-repeat control run a day later. The DFlash2 bar is hatched because it ran on a
different engine build and is not directly comparable."

**(b) Data.** Sources: `data/raw/e12/s8/s8-humaneval.json` (per-config decode medians over 164
problems, and the `equivalence` block giving 131/164 for both MTP arms);
`data/raw/e12/s9/s9-determinism.json` (`comparisons.nospec_self` and `comparisons.mtp2_self`, both
`differs` = 0, `n` = 164 — the 100 % bar; and `comparisons.s8_mtp2_vs_nospec` / `s8_mtp4_vs_nospec`,
both `differs` = 33); `data/raw/e12/s9/s9-dflash.json` (`runs[0].decode_tok_s_median` = 51.78 and
the 132/164 equivalence figure).

Extract to `fig6-speculation.csv` with columns
`config, decode_tok_s, speedup, exact_match_n, n_total, exact_match_pct, engine_image, confounded`.

---

### Appendix figure A1 — acceptance falls with draft depth, and why three repetitions rank nothing
**(c) Type: statistical plot, two-panel composite.** *(Appendix, not body — it concerns a secondary
thread, but it earns its place because it doubles as the paper's worked illustration of clustered
standard errors.)*

**(a) Description.** Two panels side by side, one per matched context depth: 131,072 (prompt length
123,670) and 196,608 (prompt length 186,270). Shared y-axis, labelled only on the left panel.

x-axis: draft depth, categorical, three positions {2, 4, 8}. y-axis: MTP draft acceptance rate,
linear, 0 to 1.0. Four series, one per arm (UD-Q4_K_XL, UD-Q5_K_XL, UD-Q6_K, UD-Q6_K_XL),
distinguished by colour and marker.

The critical rendering detail: behind each cell-level point, plot the **individual repetitions** as
small translucent markers, so the within-cell spread is visible. Then draw two intervals on one
representative cell — the pooled per-event Wilson interval (±0.02, drawn as a thin cap) and the
between-generation spread (±0.3, drawn as a wide bracket) — side by side, labelled "pooled over
draft events (misleading)" and "between generations (honest)". That contrast is the figure's
methodological payload.

Annotate the panel group once with "acceptance falls in 12 of 13 adjacent draft-depth pairs;
one-sided sign test p = 0.0017". Mark the UD-Q6_K n=8 cell at 262,144 as an **absent point** with a
small open marker on the axis and the label "fails to load — draft context does not fit"; never
plot it as zero.

The sentence the figure must communicate: **draft acceptance falls monotonically as draft depth
rises, consistently across the ladder — and the throughput ranking this sweep was built to produce
is unanswerable at three repetitions, because the unit of independence is the generation, not the
draft event.**

**(b) Data.** Source: `data/raw/e12/s9/s9d-depthsweep.json`, list `cells`, filtered to
`valid == true` (21 of 24). Per cell read `arm`, `ctx`, `n_draft`, `acceptance`,
`decode_tok_s_median` and `decode_spread_pct`. The per-repetition markers come from the cell's
`reps` list, where each entry has `rep`, `decode_tok_s`, `draft_n` and `draft_n_accepted` — the
per-repetition acceptance to plot is `draft_n_accepted / draft_n`, computed per rep, **not** the
cell's pooled `acceptance` field. That distinction is the whole point of the figure. Plus
`data/raw/e12/s9/s9e-n262k.json` for the UD-Q6_K 262,144 cells, including the n=8 load failure.

Extract to `figA1-draftdepth.csv` (cell level: `arm, ctx, n_draft, acceptance, decode_tok_s_median,
decode_spread_pct, n_reps`) and `figA1-draftdepth-reps.csv` (repetition level: `arm, ctx, n_draft,
rep, draft_n, draft_n_accepted, acceptance_rep, decode_tok_s`). Cell-level acceptance values, for
checking the render:

| arm | 131,072: n=2 / 4 / 8 | 196,608: n=2 / 4 / 8 |
|---|---|---|
| UD-Q4_K_XL | 0.673 / 0.512 / 0.404 | 0.666 / — / 0.373 |
| UD-Q5_K_XL | 0.814 / 0.493 / 0.449 | 0.746 / 0.429 / 0.573 |
| UD-Q6_K | 0.775 / 0.558 / 0.251 | 0.920 / 0.790 / 0.517 |
| UD-Q6_K_XL | 0.759 / — / 0.332 | 0.704 / 0.556 / — |

---

### Figures I would *not* request
- **Any energy or thermal figure.** PN-11's 12-hour window mixes idle and load; PN-12 is explicitly
  confounded (case airflow uncontrolled). One sentence each in Setup, no plot.
- **A speed-versus-quantization bar chart.** PN-19 is a null with 32.9 % within-arm noise; bars at
  12.70 / 12.61 / 11.90 would imply a ranking the data does not support. Prose only. This is
  Heiser's benchmarking crime 2.4 — no indication of variance — and drawing it would commit it.
- **Anything from the pre-2026-08-29 corpus.** Different engine image, `-sm tensor` no longer
  reproducible; it cannot share an axis with current measurements.
- **A figure for MK-NIAH.** One discordant sample of twelve, overlapping intervals, and the artifact
  is not yet in the repository (§13.1). A plot would give it a visual authority the evidence does
  not have. One sentence of prose with the interval attached.

### A caution about the pipeline itself
PaperBanana's critic loop optimises for *looking like* published figures, retrieved from reference
exemplars. That is exactly wrong for two things this paper needs: **error bars smaller than the
markers** (Figures 3 and 4 — a stylist may "improve" them away or rescale to make them visible, and
either would destroy the point), and **the deliberate absence of a trend line** in Figure 5's inset.
State both as hard constraints in the request, and check the rendered output against the source CSV
before accepting it. This is the same class of hazard the paper's own reproducibility register is
about: a tool that returns a plausible-looking artifact when it has silently changed the claim.

## 8. Related-work positioning

The R1–R10 map in `METHOD-REFERENCES.md` is better than most related-work sections I review, because
each entry states *what constraint it imposes on our design*. Keep that structure. Below is how to
position, with what is missing added.

| work | what it establishes | how this paper positions |
|---|---|---|
| **Dutta et al., *Accuracy is Not All You Need*** — https://arxiv.org/abs/2407.09141 (MSR India, NeurIPS 2024) | Even when accuracy matches, compressed models behave differently; introduces "flips"; **KLD correlates with flips** | **The novelty threat (§4.1). Cite in the introduction, not related work.** They own "divergence sees what accuracy hides." This paper adds the *shape* (tail concentration), the *domain dependence*, the GGUF/consumer setting, and a quantified task-level bound. |
| **Nikolić et al., *Displacement Is Not Direction*** — https://arxiv.org/abs/2606.19558 (Toronto, 2026-06) | KLD↔benchmark correlation ρ = −0.72/−0.86 across a wide cohort but **collapses to ρ ≈ 0 in the near-baseline "silent zone"** | **The dangerous paper (§4.4). Must be cited and answered in §2, not buried.** Their null and this paper's bound are the same fact from two sides. Concede that KLD does not license a ranking in this band; report a divergence measurement plus an equivalence bound instead. |
| **arXiv:2601.14277, *Which Quantization Should I Use?*** (Uygar Kurt, 2026-01, cs.LG, solo author) | llama.cpp 3–8 bit K-quant ladder on Llama-3.1-8B; reasoning/knowledge/IF/truthfulness benchmarks + WikiText PPL + CPU throughput | **The nearest neighbour and the venue precedent. Read it in full before drafting.** Novelty by exclusion is clean: it has no GPU, no multi-GPU / VRAM ceiling / split-mode, no long context, no KV-cache quantization, no KL divergence, no speculative decoding, no code focus, 8B not 27B, and no power discussion. Position generously and explicitly — a reviewer will find it. |
| **Fireworks, quantization evaluation** — https://fireworks.ai/blog/fireworks-quantization | KLD + rejection rate, prefill/generation split, forced reference completions, published **<0.007** threshold, the averaging-bias argument. Also shows MMLU *failing* (quantized sometimes beats reference) | The forced-completion technique makes the task-prompt domain possible in 22 minutes. Their threshold is the external band. **Differentiator:** they measure prose/general prompts at short context with no window constraint; this shows the threshold verdict **flips by domain** — two arms pass on prose, none on the task distribution. A respectful extension of their published rule. |
| **Unsloth Dynamic GGUFs** — https://unsloth.ai/docs/basics/dynamic-3.0-ggufs | Provenance of the arms; ranks releases on mean KLD; **states verbatim that PPL is incorrect because token values cancel**; warns that calibrating and evaluating on Wikipedia-like data overfits the metric | Both the object of study and the source of the warning acted on. Be scrupulously fair: these artifacts are tested on a corpus their authors did not choose, and their imatrix data cannot be inspected — a limitation, not an insinuation. Note their Dynamic 3.0 "Divergence-300 @32" (greedy agreement over 32 tokens on held-out agentic examples) is convergent with this study's byte-exact divergence instrument. Also note this study's host-specific pick (UD-Q6_K) differs from their general default (UD-Q4_K_XL) — a useful, concrete disagreement. |
| **LocalBench (GGUF quality)** — https://localbench.substack.com/p/gguf-benchmark-methodology | ~250 k tokens, 6 categories, KLD on prompt tokens + top-1 agreement, observed 0.01–0.03 for Q4_K_M | **Concede breadth, claim depth.** They cover 6 domains; this covers 2 but decomposes the *distribution* rather than reporting its mean, and pairs it with three task instruments on the same arms. Q4_K_XL's 0.0215 landing inside their band is a useful external consistency check. ⚠️ **Disambiguate the name** — arXiv:2511.10459 "LocalBench" is county-level civic-knowledge QA and is unrelated. |
| **oobabooga, KV-cache quantization KLD** — https://localbench.substack.com/p/kv-cache-quantization-benchmark | BF16 + f16-KV reference, top-40 token distributions; **Qwen 3.6 27B q4_0 KV 0.087–0.117**; q8_0 "practically lossless" is false for Gemma | The closest published precedent to PN-15, and it agrees qualitatively (q4_0 KV is usable on Qwen-family, not on Gemma). **Different protocol, so never in the same table** — but the order-of-magnitude gap to this study's 0.002955 must be acknowledged, or a reader will assume it was missed. |
| **QLLM-Eval** — https://arxiv.org/abs/2402.18158 (Tsinghua, ICML 2024) | PTQ across weight, activation **and KV cache**, 11 model families, five task types incl. long context; reports that at ≥4K most LLMs are **more sensitive to KV-cache quantization than to weight quantization at the same bit-width** | The strongest reason PN-15's "measured at n_ctx 2048, not at depth" caveat is a live risk rather than a formality. Cite in §5.6 and in threats-to-validity. |
| **Miller, *Adding Error Bars to Evals*** — https://arxiv.org/abs/2411.00640 | CLT standard errors, clustered SEs, paired differences, power analysis | The statistical backbone. **Extend by one step**: equivalence bounds rather than non-significance (§5). Also cite as the source of PN-32's clustering diagnosis — the draft-acceptance sweep is a clean worked example of exactly the trap, pooled ±0.02 against a true between-generation spread of ±0.3. A contribution *to* the argument, not just a use of it. |
| **Card et al., *With Little Power…*** — https://aclanthology.org/2020.emnlp-main.745/ ·<br>**Dietterich 1998** — https://direct.mit.edu/neco/article-abstract/10/7/1895/6224/ ·<br>**Brown/Cai/DasGupta 2001** — https://projecteuclid.org/journals/statistical-science/volume-16/issue-2/… | MDE and power for small test sets; McNemar as the correct paired test when each system runs once; Wilson over Wald at small n | The three citations that convert the nulls from apologies into designed results. Dietterich's endorsement of McNemar for run-once systems is precisely this study's regime and should be quoted. |
| **RULER** — https://arxiv.org/abs/2404.06654 (NVIDIA, COLM 2024) | The long-context standard; retrieval / multi-hop / aggregation / QA; `string_match_all`; the notion of **effective context length** | Generators, templates and metric used verbatim, unit-checked. Be explicit about the departure (transport only). **Consider adopting and extending "effective context length"** — theirs is capability-bound at fixed precision; here it is jointly capability- *and* VRAM-bound, and moves ±33 % with a placement flag. "The real context size of your quantized model on your hardware" is a defensible citable extension they never ask. |
| **Red Hat / Neural Magic** — https://arxiv.org/abs/2411.02355 (ACL 2025) and the RULER long-context article | >500,000 evaluations; FP8 effectively lossless; INT W4A16 competitive; ~200,000 long-context RULER evaluations with 85–88 % recovery for INT W4A16 at 128 K | **The scale reference to concede rather than contest.** Lead with the contrast: a team with datacenter hardware versus a solo researcher for whom GPU hours are the binding constraint — which *forces* the instrument-efficiency question their budget lets them ignore. Then note three things they structurally cannot see: they keep the KV cache high-precision (here q4_0 KV is the enabling condition for the window existing at all); their INT4-at-128K degradation is confounded with model capability by their own admission; and they never hit a VRAM ceiling. ⚠️ **Verify the article's date** — the byline reads 2024-02-03 but it uses RULER (April 2024) and says "now part of Red Hat"; almost certainly 2025. |
| **arXiv:2505.20276** (UMass, EMNLP 2025 Main) | 9.7K examples, 5 methods × 5 models: 8-bit ≈ 0.8 % drop, **4-bit up to 59 % on long inputs**; effects depend heavily on method, model and task | The peer-reviewed counterweight to Red Hat. **Use the pair to establish that the literature does not agree**, then position this study as adjudicating on a third axis neither covers: GGUF K-quants (absent from all five of their methods) with a quantized KV cache on consumer multi-GPU. Their "depends heavily on method, model, task" also supports the refusal to generalise `-ts` ratios across configurations. |
| **LongPPL** — https://arxiv.org/abs/2410.23771 (ICLR 2025) | PPL is unreliable for long context because averaging drowns the few **key tokens** ability turns on; weighting them gives Pearson −0.96 | **Move from methodological footnote to the introduction.** LongPPL's core claim — the informative signal lives in a small set of key tokens and averaging destroys it — is structurally the same claim as this paper's tail-concentration result, reached independently in a different setting. Positioning this work as *the quantization analogue of LongPPL's finding* gives the framing a published intellectual lineage instead of the appearance of a solo curiosity. **If you take one related-work suggestion from this review, take this one.** |
| **Benchmark saturation** — https://arxiv.org/abs/2602.16763 · https://arxiv.org/abs/2607.01254 · IRT: https://arxiv.org/abs/2505.15055 | Formal saturation-vs-stagnation definitions and an uncertainty-aware index; the shrinking-discriminating-fraction mechanism; Fisher information as a per-item discrimination measure | **Missing from the current map and required by §3.** These supply the vocabulary that makes §5.3's claim precise instead of false, and they turn the "no benchmark here can rank these arms" statement from a limitation into a cited methodological position. |
| **Speculative decoding** — Leviathan et al. https://arxiv.org/abs/2211.17192 · Chen et al. https://arxiv.org/abs/2302.01318 · **llama.cpp #25618** https://github.com/ggml-org/llama.cpp/issues/25618 · arXiv:2606.25097 · arXiv:2510.22876 · arXiv:2604.26469 | The distribution-preservation guarantee *in exact arithmetic*; an open, independent report of the same divergence on quantized targets (2026-07-13); a published TOST-based study finding invariance **holds** on vLLM/GPTQ-4bit; batch-speculative correctness failures; an SE-tasks study that assumes losslessness and never tests it | §4.2. Cite the theorem, then show the gap between it and the shipped quantized implementation. **Report priority honestly** and claim the right thing: paired-problem statistics, a byte-exact determinism control, first-divergence distributions, and the Jaccard-0.610 datum nobody else has. |
| **R12 — DFlash and its bit-exactness claim** — https://arxiv.org/abs/2602.06036 (Chen, Liang & Liu, 2026) · MLX port https://github.com/Aryagm/dflash-mlx | The origin of the DFlash2 drafter benchmarked in PN-29. The MLX port states its speculative decoding is **"bit-for-bit identical to plain target decoding"**, with verification described as longest-matching-prefix plus one bonus correction token | **The sharpest related-work hook in the paper (§4.3).** A specific, attributable, checkable losslessness claim about the same drafter family — which removes the strawman risk of arguing against folklore. Quote it verbatim to open §5.5, then give the measurement. **Be precise about scope:** DFlash's own implementation was not measured losslessly here (PN-25/PN-29 — different engine build, engine-confounded), so the paper does *not* contradict their claim. It supports the level-up claim: *losslessness is an implementation property requiring per-stack verification, not a property inherited from the algorithm's specification.* |
| **R11 — PaperBanana** — https://arxiv.org/abs/2601.23265 (Google Research) · https://github.com/llmsresearch/paperbanana | Multi-agent figure-generation pipeline: retriever → planner → stylist → visualizer → critic, ~3 rounds. Methodology diagrams, statistical plots from CSV/JSON, multi-panel composites. Figures only — no LaTeX, no prose | Not related work; a **project prerequisite** for producing this paper's figures. Cloud-dependent with no keys on this host, so specs are authored here and rendered elsewhere — §7 is written to be consumed directly by its planner. If the paper acknowledges tool use (and per arXiv's generative-AI policy it should), name it there alongside the harness disclosure. |
| **Heiser, *Systems Benchmarking Crimes*** — https://gernot-heiser.org/benchmarking-crimes.html · **ACM SIGSOFT Empirical Standards** — https://www2.sigsoft.org/EmpiricalStandards/ | A self-audit taxonomy for systems measurement; a Benchmarking standard with essential attributes, antipatterns and *invalid criticisms* | Not related work — **a pre-submission checklist.** Crimes 2.4 (no variance indication), 4.1 (no proper baseline), 4.3 (unfair competitor evaluation — the default-split issue) and 5.1 (missing platform spec) are all live here, and this paper passes all four if it says so. The standard's "invalid criticisms" list is useful ammunition: *"the benchmark is not widely adopted"* and *"no independent replication is reported"* are explicitly not valid objections to a bespoke protocol. |

**One more gap.** If prior work exists showing quantization damages code generation more than natural
language, it must be cited — it is the closest prior claim to contribution 2. Candidates worth
checking (I could not verify that any makes the domain-comparison claim directly): arXiv:2601.02563,
arXiv:2303.05378, arXiv:2410.14766. If none does, **say so explicitly** — "we are not aware of a
published measurement of this asymmetry" is a stronger position than silence.

---

## 9. arXiv logistics

Every rule below is from arXiv's own documentation; URLs in §12. Several changed recently — the
endorsement policy in January 2026, `.bbl` handling in November 2025 — so older advice is stale.

### Category

**Primary `cs.LG`. Cross-list `cs.PF`. That is the full list — two, not three.**

- **`cs.LG`** — "Papers on all aspects of machine learning research … including also robustness,
  explanation, fairness, and methodology." Quantization is squarely ML, it is where the readership
  is, and the nearest-neighbour paper (arXiv:2601.14277) is cs.LG. If the tail-concentration reframe
  is adopted, this gets stronger — the central object becomes a distributional claim about a model.
- **`cs.PF`** — "Covers **performance measurement and evaluation**, queueing, and simulation." That
  is literally this study's method, and it is a low-volume category where a rigorous measurement
  paper is visible rather than buried. A `cs.PF`-primary framing is defensible if Statement 3 is
  elevated to co-headline; I would not, because it costs readership.
- **`cs.CL`** is tempting (language model, text and code corpora, NLP benchmarks) but is the third
  cross-list, and arXiv is explicit: *"It is rarely appropriate to add more than one or two
  cross-lists … Bad cross-lists will be removed."* Pick `cs.PF` over `cs.CL` — the systems half is
  the more distinctive and the less well served.
- **`cs.AI` is wrong by arXiv's own definition**: it "covers all areas of AI **except** … Machine
  Learning … and Computation and Language." Do not use it.
- **`cs.DC`** is defensible for the layer-split findings but would be a third cross-list.
- **ACM-class field** (cs only, semicolon-separated): `D.4.8; I.2.6`.

### Endorsement — the gating item, and it got harder in January 2026

**This is the single most likely thing to stall the submission for weeks, and it should be started
before drafting is finished.** As of **2026-01-21**, arXiv no longer accepts an institutional email
address as the sole qualifier for a new author in *any* category. Auto-endorsement now requires
**both** an institutional email **and** prior claimed authorship in the endorsement domain. A solo
researcher with a personal email address has neither, so **personal endorsement is the only route**,
and arXiv staff cannot waive it or provide one.

Practically:
1. Start a submission and pick the category — arXiv emails a six-character endorsement code.
2. Find candidates on the abstract page of a recent paper you cite, via **"Which authors of this
   paper are endorsers?"**; the submitter's email is under Submission history.
3. Contact them individually with the code, a link to a scholarly profile, and ideally the draft.
   arXiv states it is *"inappropriate to email large numbers of potential endorsers at once."*
4. **`cs` is a single endorsement domain** — any active `cs.*` author qualifies to endorse for
   `cs.LG` or `cs.PF`. That widens the candidate pool considerably.
5. Net endorsement must stay positive; negative endorsements are recorded.

Best candidates given this paper's citations: authors of recent cs.LG/cs.PF quantization or
inference-measurement papers the report cites. The author of arXiv:2601.14277 is an obvious,
topically ideal ask.

### Format and submission

- **Submit LaTeX source, not PDF.** arXiv: *"a PDF file created from a TeX/LaTeX file will typically
  be rejected."* PDF-only also forfeits the accessible HTML version **and forfeits ancillary
  files**, which are the natural home for the JSON artifacts.
- **`.bbl` is no longer required** — since **2025-11-05** arXiv processes `.bib` directly. Older
  template READMEs still say otherwise.
- Figures: `.pdf`/`.png`/`.jpg` for pdfLaTeX. Vector PDF for all line plots. No on-the-fly
  conversion; no external dependencies; no embedded JavaScript.
- Flatten the directory; compilation runs from the submission root.
- Size: budget ≤ 50 MB (the only arXiv-stated figure, from 2020; current help pages give no number).
  From **February 2026** arXiv warns on images above 34 megapixels.
- Format policy requires: title and authorship (no anonymous submissions), complete references,
  single-spaced 10–14 pt text, ≥ 1″ margins, no line numbers, no watermarks.

### The blocker you must resolve: the repository is private

arXiv's format requirements state, verbatim: **"Links to code or data sets must resolve to a
publicly available repository."** A private URL in the paper or the Comments field is a format
violation, and every artifact-badging and journal policy I checked treats "available on request" as
non-compliant.

The workable release, and I would do it:
1. **Deposit a scrubbed snapshot on Zenodo for a DOI** — the `e12` harness source, the JSON
   artifacts under `data/raw/e12/**`, `env-manifest.json` with sha256s and image digests, the paper
   notes and the ledger. That is exactly the set that makes the ceilings and intervals checkable.
   Zenodo mints a **concept DOI** covering all versions plus a per-version DOI.
2. **Add a Software Heritage SWHID** for the exact tree state (SWHIDs became ISO/IEC 18670 in
   2025-04). Convention: cite the DOI for the artifact as a whole and the SWHID for the exact code
   state you ran.
3. **Print both in the paper**, in a page-1 footnote and an "Artifact availability" section, along
   with the engine image digest. The paper body is the only channel guaranteed to survive — the
   arXiv "Code, Data, Media" tab was powered by Papers with Code, which **Meta shut down in July
   2025**, so it is effectively dormant. Do not rely on it.
4. **Ship the JSON artifacts as arXiv ancillary files** in an `anc/` directory — arXiv explicitly
   lists "Raw data for tables and plots" and "Program code" as intended contents, and this is
   another reason PDF-only is not an option.

### Licence

**CC BY 4.0.** The value here is in reuse — figures quoted, tables rebuilt, the protocol re-run. The
arXiv perpetual non-exclusive licence limits re-use by others, NC/ND variants block exactly the
practitioner audience this serves, and CC0 surrenders copyright and would conflict with a later
publisher transfer. Note: **the licence is irrevocable per version** and chosen at submission —
decide before clicking. (A later version may carry a different licence.)

### Moderation risk, honestly

The realistic rejection ground for this manuscript is arXiv's clause on submissions that *"do not
contain original or substantive research, including course projects, research proposals…"*
Moderation is not peer review and gives no feedback; a decline is appealed through the support
portal only, resolved typically in two weeks, and *"decisions upon appeal are final."*

What separates this from an engineering write-up in a moderator's read is exactly what §6 of this
review recommends: a named protocol, stated sample sizes and intervals, a threats-to-validity
section, and a contribution list that makes falsifiable claims. Written as a *study*, it is fine.
Written as a project log, it is at risk.

### AI-authorship disclosure — mandatory, and an asset

arXiv requires reporting *"any significant use of sophisticated tools, such as instruments and
software; we now include in particular text-to-text generative AI,"* holds authors fully responsible
for content regardless of how it was generated, and states such tools **may not be listed as
authors**. Every entry in `PAPER-NOTES.md` is signed by a model, the ledger records agent-driven
execution, and DEC-7 is explicitly labelled an agent correction to an owner-approved plan. This must
be **disclosed in the paper**, not discovered in the artifacts. One paragraph in §3:

> The measurement campaign was executed by an agent-driven harness under the author's direction; the
> author designed the protocol, approved every experiment, and is responsible for all content. The
> decision log, ledger and per-finding notes recording that process are released with the artifacts.

Written that way it is a strength — full provenance of an experimental campaign, which almost no
paper provides.

### Template

**`arxiv.sty` from https://github.com/kourgeorge/arxiv-style.** Single column (a 7–9 column table
with config · n · estimate · CI · protocol label fits at `\small` without `\resizebox`), MIT
licensed, NeurIPS-derived but deliberately distinct so it is not mistaken for a NeurIPS paper, two
dependencies (`geometry`, `fancyheader` — do not re-import them). Second choice: `acmart` with
`[manuscript,screen]` for a single-column journal feel. Third: NeurIPS style with `[preprint]`, which
stamps "Preprint. Work in progress." — the wrong signal for a finished report. Avoid two-column
styles (ICML, ACL, IEEE); they will fight every table.

Packages: `booktabs` (never `\hline`), **`siunitx` with `S` columns** to decimal-align estimates
against CI bounds, `threeparttable` for the per-table protocol/n/estimator note the repo's own rules
require, `makecell`, `longtable` for the full ratio sweeps, `microtype`, `cleveref`.

### Timing

Announcement is Sunday–Thursday at 20:00 US Eastern; a submission received Thursday 14:00 → Friday
14:00 does not announce until **Sunday 20:00**. First submissions typically sit 1–4 days in quality
checks. The arXiv identifier cannot be obtained in advance. Do not resubmit while on hold.

### Submission checklist

- [ ] Endorsement secured for `cs.LG` — **start this weeks early**
- [ ] Artifacts deposited publicly (Zenodo DOI + SWHID); the private-repo blocker resolved
- [ ] LaTeX source compiles standalone; `.bib` included; flattened directory
- [ ] JSON artifacts in `anc/`
- [ ] Figures rendered via PaperBanana on a keyed machine (R11); each checked against its source CSV
- [ ] Figure-source CSVs under `manuscript/figures/data/` and included in the artifact release
- [ ] All figures vector PDF
- [ ] Abstract ≤ 1920 characters, **ASCII only**, no LaTeX macros (the metadata field rejects
      unicode; en-dashes and curly quotes pasted from a PDF are the usual culprit)
- [ ] Title, authors, abstract in the web form match the PDF exactly
- [ ] Categories: `cs.LG` primary, `cs.PF` cross-list; `ACM-class: D.4.8; I.2.6`
- [ ] Licence CC BY 4.0 selected (irrevocable)
- [ ] Comments field: `NN pages, 6 figures, 5 tables. Artifacts: <DOI URL>`
- [ ] AI-tool disclosure paragraph present
- [ ] Self-audit against Heiser's benchmarking crimes and the SIGSOFT Benchmarking standard
- [ ] Every table names protocol, n and estimator *in the table*
- [ ] Pre-2026-08-29 rows labelled *irreproducible-on-current-images*, or excluded
- [ ] Withdrawn claims appear nowhere except as worked examples in Appendix B
- [ ] Threats-to-validity written before results were polished

---

## 10. Title and abstract

### Three candidate titles

**T1 — recommended.**
> **Quantization Damage Lives in the Tail: Domain-Dependent Divergence in a 27B Coding Model, and
> What Task Benchmarks Can and Cannot Bound**

Leads with the positive, novel result; names the domain; and its second clause is honest rather than
accusatory. "Can and cannot bound" makes the paper look careful instead of combative — and careful
is what gets a solo-author measurement paper read. It also survives §4.1, because it does not claim
the already-published finding.

**T2 — systems-forward, for a `cs.PF`-primary framing.**
> **Two 16 GB GPUs and a 27B Model: Quantization, Context Ceilings, and the Measurement Problem in
> Local LLM Deployment**

Broader appeal to the local-inference audience, weaker as a research claim. Use if Statement 3 is
elevated to co-headline.

**T3 — methods-forward.**
> **What the Benchmarks Cannot See: Tail-Concentrated Quantization Damage and the Case for
> Divergence-First Evaluation**

Punchiest and most shareable, and the most likely to draw a hostile reviewer — because §4.1 shows
the "benchmarks cannot see it" claim is already published and §4.4 shows divergence-first has a
published limitation in exactly this band. Acceptable only if §5.3 is rewritten as bounds and both
papers are cited in the introduction.

**Do not use the current working title, *"The Benchmarks Cannot See It"*, standing alone.** It
commits the paper to its weakest and least novel claim in its first five words.

### Draft abstract — 245 words, 1,552 characters, ASCII-clean (arXiv limit 1,920)

> Quantization tables for locally served language models are published on prose corpora and
> validated on task benchmarks. We measure a 27B coding model (Qwen3.8-27B, four Unsloth GGUF
> quantizations) on two consumer 16 GB GPUs and show that the mean of the standard divergence metric
> conceals the shape of the damage. Measuring KL divergence against the least-quantized arm over
> 65,536 tokens per domain, damage on code is roughly twice that on prose by the mean -- but 90% of
> code tokens are LESS perturbed than prose tokens (median divergence 1.7e-5 against 3.5e-3), while
> the top 1% are up to eight times MORE. Damage is tail-concentrated at high-entropy decision points,
> and it rises again as the corpus approaches the target task (3.1-4.4x prose on the benchmark's own
> prompts). Against a published quality threshold, two of three arms pass on prose, one on generic
> code, and none on the task distribution. Three task benchmarks spanning three scoring modes --
> multiple choice, unit-tested generation, and long-context retrieval -- bound the end-to-end effect
> of the entire ladder at no more than 4 points of pass@1 and cannot resolve below it, which is what
> tail concentration predicts. We also report that the usable context ceiling on this host is set by
> GPU tensor placement rather than by quantization, and that speculative decoding on this engine is
> deterministically non-equivalent to unspeculated decoding, reproducing the unspeculated output on
> 131 of 164 problems at temperature zero. Artifacts and the full measurement record are released.

Notes: leads with the mechanism, gives two hard numbers early, states the threshold flip in one
clause, converts the nulls into a bound, ends on the two systems findings plus the artifact release.
No LaTeX macros, no unicode — it will paste into arXiv's metadata field unmodified.

---

## 11. What to cut

Cutting is the highest-value editing available. There is roughly 40 % more material than the paper
can carry, and the excess dilutes rather than supports.

### Cut entirely
- **PN-12 (thermal asymmetry).** Self-described as "observational and confounded"; case airflow is
  an equally plausible cause and was not controlled. One clause in limitations at most.
- **PN-27 (the preflight self-match incident).** Well handled and genuinely entertaining, but it
  affected no measurement. It belongs in the released ledger. Including it invites the reader to see
  the paper as a project diary.
- **PN-10 (orchestration defects).** Same reasoning. The one generalisable rule — *a sweep in which
  every cell failed must not exit 0* — becomes a sentence inside Appendix B's PN-17 discussion.
- **The entire energy section (§5.7 of the current outline).** DEC-12 cancelled the energy curve, so
  no per-config figure exists; PN-11's window mixes idle and load; PN-12 is confounded. A section
  built from these would be the weakest three paragraphs in the paper. Two sentences in Setup, one
  line in limitations.
- **All pre-2026-08-29 historical results**, except the E11c rebalance headline framed explicitly as
  *"the observation that motivated this study"* with the irreproducibility label attached.

### Demote to appendix
- **PN-18 (`-ctxcp` 4 → 32).** n=1 A/B; the note itself says the 6.8 % gain is the same order as
  rep-to-rep noise and "quoting the number would need 3 reps." Configuration appendix only, **and
  the number must not appear in the body.**
- **PN-4 (`-fit` behaviour change).** A hazard note. Appendix B or a Setup footnote.
- **PN-20 (unnamed estimator reversed a ranking).** Keep — it is the most instructive of the
  provenance notes because it changed a conclusion — but in Appendix B, not results.
- **PN-9 (per-quant acceptance).** A confounded single observation per quant *by its own statement*;
  S9d was reinstated to resolve it and failed on power. Limitations, not results.
- **PN-24.** The at-depth half is withdrawn (PN-30); the 32 K half survives as one row of Figure 5(a).
  Do not list PN-24 as a finding anywhere.
- **PN-31 (KLD memory ceiling).** Footnote, per owner direction, keeping only the generalisable
  clause.
- **PN-32's decode/ranking half.** Keep the acceptance trend and the clustering lesson; drop every
  throughput number from that sweep.
- **PN-11 (host power envelope).** Two sentences in Setup.

### Keep, but rewrite
- **PN-22, PN-28, PN-33, PN-34** — as *bounds* (§5), with the three distinct mechanisms (§3). PN-34's
  headline ("difficulty revealed what depth could not") must become a hypothesis with its interval;
  it currently reads as established and rests on one discordant sample.
- **PN-16** — promote from "reproducibility & provenance" to a *results* paragraph; the quantile
  decomposition turns it from a caution into a mechanism.
- **The reproducibility register** — seven entries to four, unified by *silent success is the
  dominant failure mode of automated benchmarking.* Seven instances of "we found a bug" reads as a
  confessional; four structurally distinct instances under one thesis reads as method.

---

## 12. Risks, and what would make a reader cite it

| # | risk | severity | mitigation |
|---|---|---|---|
| 1 | **"The headline was published at NeurIPS in 2024."** (Dutta et al.) | **Critical** | §4.1. Cite in the introduction; move the novelty to tail concentration; reframe the sweep as a consumer-scale, code-domain quantification of a published warning. |
| 2 | **"Your saturation claim is false — HellaSwag at 82.75 % is nowhere near a ceiling."** | **Critical** | §3. Adopt saturation-vs-stagnation; give the three instruments three mechanisms. Costs one sentence, converts an overclaim into a sharper finding. |
| 3 | **"KLD does not rank in your band."** (Nikolić et al.) | **High** | §4.4. Cite it in §2 and agree. Report divergence + equivalence bound, never a "better for your agent" ranking. |
| 4 | **"An open llama.cpp issue reported your spec-decode finding six weeks earlier."** | **High** | §4.2. Report priority honestly, claim the quantitative characterisation, and adopt their quantized-target hypothesis — which strengthens the paper by connecting §5.5 to the thesis. |
| 5 | **"One model, one engine, one host — this is an anecdote."** | **High** | Make it the frame. A *single-configuration measurement study* whose contribution is the method and the distribution shape, both testable on any host in an afternoon. Give the protocol its own named section. A method that reproduces cheaply survives n=1. |
| 6 | **"Your reference is quantized; you measured nothing absolute."** | **High** | State it, then defuse: the reference is itself ~6-bit, so every arm's true FP16 distance is *larger* than reported — every claim is conservative. Reframe as *quantization-step* damage along a ladder practitioners actually choose from. |
| 7 | **"Your nulls are underpowering, not insensitivity."** | **High** | §5. Equivalence bounds, MDE, Dietterich/Card/Wilson. Free to fix. |
| 8 | **"The centrepiece rests on one sample."** (PN-34) | **High** | Demote to a hypothesis paragraph with its Wilson interval and Red Hat's band beside it. Not needed as a contribution once §5.1 carries the paper. |
| 9 | **"Why should I believe an agent-run campaign?"** | Medium | Disclose up front (§9) and lean on the artifact register. Very few papers can show their own error-detection record. Turn exposure into credential. |
| 10 | **Internal number inconsistencies.** | Medium | Two are live now (§13). Sweep every number against its artifact — a reader who finds one stops checking and starts discounting. |
| 11 | **"You didn't compare against the practitioner reports on the same hardware."** | Medium | Address InventiveHQ (same GPU, same engine, opposite q4_0-KV verdict) and oobabooga (order-of-magnitude different KV KLD) in §5.6. Winning those comparisons requires making them. |
| 12 | **"No agentic / long-horizon evidence, which is where it would matter."** | Medium | Do not concede defensively — *claim* it as the named open problem and closing sentence. |
| 13 | **Length and self-indulgence.** | Medium | §11. If a paragraph exists because it was expensive to produce rather than because it supports a claim, it goes to the artifact release. |
| 14 | **Endorsement stalls the submission.** | Medium | §9. Start now, not after drafting. |
| 15 | **Figure production is blocked on infrastructure.** PaperBanana (R11) is a stated prerequisite and is cloud-dependent; no API keys exist on this host. | Medium | Author the specs here (§7) and the extracted CSVs, then render on a machine with keys. Gemini's free tier is listed as sufficient. Sequence it early: figures drive how §5 is written, so blocked figures block the results sections, not just the layout. |
| 16 | **The figure pipeline silently changes a claim.** Its critic loop optimises for resembling published exemplars, which is wrong for error bars smaller than the markers (Figs 3–4) and for the deliberately absent trend line (Fig 5 inset). | Medium | State both as hard constraints in every request and diff the rendered output against the source CSV before accepting. This is the reproducibility register's own lesson applied to the paper's own tooling. |

### What would make a reader cite it

1. **The quantile table.** If §5.1 is written and Figure 1 drawn, that table is what people
   screenshot. It is a fact about quantized code models I have not seen stated anywhere, it is well
   powered, and it reframes a metric the whole local-inference community uses as a scalar.
2. **The equivalence bound.** "The full width of a Q4→Q6 GGUF ladder is worth ≤ 4 points of
   HumanEval+ pass@1" is a sentence practitioners will quote in arguments and researchers will cite
   when justifying a sample size.
3. **`-ts` and the context ceiling.** Cited by tooling authors and by anyone publishing a ceiling
   table, because it makes their published numbers incomplete. Large effect, binary evidence,
   immediately actionable.
4. **Deterministic non-equivalence of speculative decoding, characterised quantitatively.** The
   evidence set is unusually complete for a claim of this shape: a published bit-exactness assertion
   (R12), an open independent defect report on a different backend (#25618), a published study
   finding invariance *holds* on a third stack (arXiv:2606.25097), a downstream SE study that
   assumes losslessness and never tests it (arXiv:2604.26469), and 164 paired problems here with
   byte-exact self-reproduction. The rule that falls out — *verify losslessness per stack; it is not
   inherited from the specification* — is the citable output.
5. **The reproducibility register as method.** Four structurally distinct silent-success failures,
   each with a rule. Anyone writing about benchmark automation or agentic evaluation harnesses can
   use it directly, and there is very little published on this.
6. **The affordability argument.** A protocol that ranks four quantizations in ~2.3 GPU-hours on
   consumer hardware is genuinely useful to a community that cannot afford 200,000 evaluations.
   State the cost as a contribution — with the corrected numbers.

---

## 13. Two provenance problems found while reviewing

Not framing issues, but they become framing issues if they reach a reader.

**13.1 — The MK-NIAH evidence is not in the repository.**
PN-33 and PN-34 rest on the multi-key NIAH result (100.0 vs 91.67 at 131,072), and PN-34 is named in
the outline as "the paper's methodological through-line." The committed artifact
`data/raw/e12/ruler/s12-ruler.json` contains **only** the single-key NIAH cells and the excluded
`variable_tracking` cells; the string `91.67` appears nowhere under `data/raw/e12/ruler/`. The data
*does* exist on the host — `/srv/bench/e12/ruler/s12-ruler.json` carries both `mkniah` cells and the
`accuracy_recovery` entry, and the two `s12-preds-*-mkniah-c131072.json` prediction files are there —
but the repository mirror is one sync behind. **Pull it before anything cites PN-34.** The repo's own
rule is that a headline number traces paper note → artifact → serverlog; this one currently breaks at
the artifact.

**13.2 — The "≈20 hours of task benchmarking" figure is not supported by the artifacts.**
It appears in `README.md`, in `OUTLINE.md`'s thesis paragraph, and in PN-34. Summing
`started_utc`/`finished_utc` across every task and speculation battery in E12 gives ≈ 11.4 h against
≈ 2.3 h of divergence (table in §6). That is still a 5× contrast and entirely sufficient. Either
restate at the supported figure or say explicitly that the 20 h includes the pre-E12 historical
corpus. As written it is falsifiable in five minutes.

---

## 14. Web sources

All URLs verified during this review.

### arXiv submission mechanics
- Submission overview — https://info.arxiv.org/help/submit/index.html
- Submit TeX/LaTeX — https://info.arxiv.org/help/submit_tex.html
- Submit a PDF (and why PDF-from-TeX is typically rejected) — https://info.arxiv.org/help/submit_pdf.html
- Why submit TeX? (accessibility / HTML) — https://info.arxiv.org/help/faq/whytex.html
- Oversized submissions; the Feb-2026 34-megapixel warning — https://info.arxiv.org/help/sizes.html
- 50 MB limit announcement (2020-07-23) — https://x.com/arxiv/status/1286381643893268483
- **Format requirements** (incl. *"Links to code or data sets must resolve to a publicly available repository"*) — https://info.arxiv.org/help/policies/format_requirements.html
- Metadata fields; 1920-character ASCII abstract; Comments conventions — https://info.arxiv.org/help/prep.html
- **Endorsement** — https://info.arxiv.org/help/endorsement.html
- **Endorsement policy change, 2026-01-21** — https://blog.arxiv.org/2026/01/21/attention-authors-updated-endorsement-policy/
- Endorsement, legacy mirror text (net-positive rule) — https://arxiv.org/mirrorhelp/endorsement.html
- Content moderation (incl. the generative-AI clause and the "not substantive research" ground) — https://info.arxiv.org/help/moderation/index.html
- Appealing a moderation decision — https://info.arxiv.org/help/moderation/appeals.html
- Availability and the announcement schedule — https://info.arxiv.org/help/availability.html
- Submission status — https://info.arxiv.org/help/submit_status.html
- Licences (irrevocable per version) — https://info.arxiv.org/help/license/index.html
- Submission agreement — https://info.arxiv.org/help/policies/submission_agreement.html
- Category taxonomy (verbatim cs.LG / cs.CL / cs.PF / cs.AI / cs.DC / cs.SE definitions) — https://arxiv.org/category_taxonomy
- Cross-listing etiquette ("rarely appropriate to add more than one or two") — https://info.arxiv.org/help/cross.html
- Replacing / versioning — https://info.arxiv.org/help/replace.html
- Withdrawal — https://info.arxiv.org/help/withdraw.html
- **Ancillary files** (not supported for PDF submissions) — https://info.arxiv.org/help/ancillary_files.html
- Text overlap detection — https://info.arxiv.org/help/overlap.html
- arXivLabs showcase (the "Code, Data, Media" tab) — https://info.arxiv.org/labs/showcase.html
- `.bib` processed directly since 2025-11-05 — https://blog.arxiv.org/2025/11/05/attention-authors-updates-for-bib-file-processing-and-tex-in-arxiv-submissions/
- Local time / next announcement deadline — https://arxiv.org/localtime

### LaTeX templates
- **`arxiv.sty` (recommended)** — https://github.com/kourgeorge/arxiv-style
- NeurIPS style files — https://neurips.cc/Conferences/2023/PaperInformation/StyleFiles
- ICLR master template — https://github.com/ICLR/Master-Template
- JMLR format instructions — https://www.jmlr.org/format/format.html · style file https://github.com/JmlrOrg/jmlr-style-file
- ACM `acmart` — https://ctan.org/pkg/acmart · https://www.acm.org/publications/proceedings-template
- ACL style files — https://github.com/acl-org/acl-style-files
- IEEEtran — https://ctan.org/pkg/ieeetran

### Writing empirical, benchmarking and negative-result papers
- **Heiser, *Systems Benchmarking Crimes*** — https://gernot-heiser.org/benchmarking-crimes.html
- van der Kouwe et al., *Benchmarking Crimes: An Emerging Threat in Systems Security* — https://arxiv.org/abs/1801.02381
- **ACM SIGSOFT Empirical Standards** — https://www2.sigsoft.org/EmpiricalStandards/ · standards index https://www2.sigsoft.org/EmpiricalStandards/docs/standards · paper https://arxiv.org/abs/2010.03525
- Hasselbring, *Benchmarking as Empirical Standard in SE* — https://arxiv.org/abs/2105.00272
- Raasveldt et al., *Fair Benchmarking Considered Difficult* — https://hannes.muehleisen.org/publications/DBTEST2018-performance-testing.pdf
- NeurIPS 2026 Evaluations & Datasets CFP (accepts negative results, evaluation methodology, benchmark saturation) — https://neurips.cc/Conferences/2026/CallForEvaluationsDatasets
- NeurIPS 2025 Datasets & Benchmarks CFP — https://neurips.cc/Conferences/2025/CallForDatasetsBenchmarks
- BetterBench — https://arxiv.org/abs/2411.12990 · https://betterbench.stanford.edu/
- ML Reproducibility Checklist (Pineau) — https://www.cs.mcgill.ca/~jpineau/ReproducibilityChecklist.pdf · JMLR paper https://www.jmlr.org/papers/v22/20-303.html
- Dodge et al., *Show Your Work* — https://aclanthology.org/D19-1224/
- MLPerf inference rules (quantization reporting) — https://github.com/mlcommons/inference_policies/blob/master/inference_rules.adoc
- Henderson et al., energy/carbon reporting — https://jmlr.org/papers/v21/20-312.html
- Peyton Jones, *How to write a great research paper* — https://www.microsoft.com/en-us/research/academic-program/write-great-research-paper/
- Levin & Redell, *How (and How Not) to Write a Good Systems Paper* — https://www.usenix.org/conferences/author-resources/how-and-how-not-write-good-systems-paper
- Irene Zhang, *Hints on how to write an SOSP paper* — https://irenezhang.net/blog/2021/06/05/hints.html
- **Insights from Negative Results in NLP** workshop — https://insights-workshop.github.io/ · 2025 CFP https://insights-workshop.github.io/2025/cfp/
- ICBINB (*I Can't Believe It's Not Better*) — https://i-cant-believe-its-not-better.github.io/neurips2020/mission/
- NetNeg, SIGCOMM 2026 (negative results in measurement) — https://conferences.sigcomm.org/sigcomm/2026/netneg/
- Karl et al., *Position: Embracing Negative Results in ML* (ICML 2024) — https://arxiv.org/abs/2406.03980
- Schaeffer et al., *Refutations and Critiques track* — https://arxiv.org/pdf/2506.19882

### Statistics for underpowered comparisons
- Card et al., *With Little Power Comes Great Responsibility* — https://aclanthology.org/2020.emnlp-main.745/
- Miller, *Adding Error Bars to Evals* — https://arxiv.org/abs/2411.00640
- Dietterich, *Approximate Statistical Tests…* (McNemar for run-once systems) — https://direct.mit.edu/neco/article-abstract/10/7/1895/6224/
- Brown, Cai & DasGupta, *Interval Estimation for a Binomial Proportion* (Wilson over Wald) — https://projecteuclid.org/journals/statistical-science/volume-16/issue-2/Interval-Estimation-for-a-Binomial-Proportion/10.1214/ss/1009213286.full
- Dror et al., *Hitchhiker's Guide to Testing Significance in NLP* — https://aclanthology.org/P18-1128/
- Benavoli et al., Bayesian comparison / ROPE — http://www.jmlr.org/papers/v18/16-305.html
- TOST practical guide — https://aaroncaldwell.us/TOSTERpkg/articles/IntroTOSTt.html
- Madaan et al., *Quantifying Variance in Evaluation Benchmarks* — https://arxiv.org/abs/2406.10229

### Benchmark saturation
- **Akhtar, Reuel, Soni et al., *When AI Benchmarks Plateau*** (saturation vs stagnation) — https://arxiv.org/abs/2602.16763
- *The Benchmark Ceiling* — https://arxiv.org/abs/2607.01254
- *Lost in Benchmarks? Rethinking LLM Benchmarking with IRT* — https://arxiv.org/abs/2505.15055
- Bowman & Dahl, *What Will it Take to Fix Benchmarking in NLU?* — https://arxiv.org/abs/2104.02145
- Ott et al., *Mapping global dynamics of benchmark creation and saturation* — https://www.nature.com/articles/s41467-022-34591-0

### Quantization evaluation
- **Dutta et al., *Accuracy is Not All You Need*** (NeurIPS 2024) — https://arxiv.org/abs/2407.09141
- **Nikolić et al., *Displacement Is Not Direction*** — https://arxiv.org/abs/2606.19558
- *A KL Lens on Quantization* — https://arxiv.org/abs/2604.13440
- **Kurt, *Which Quantization Should I Use?*** (nearest neighbour) — https://arxiv.org/abs/2601.14277
- Kurtić et al., *"Give Me BF16 or Give Me Death"?* (ACL 2025) — https://arxiv.org/abs/2411.02355
- Red Hat, quantized models on long-context tasks — https://developers.redhat.com/articles/2024/02/03/how-well-do-quantized-models-handle-long-context-tasks
- Mekala et al., *Does quantization affect long-context performance?* (EMNLP 2025) — https://arxiv.org/abs/2505.20276
- Li et al., *Evaluating Quantized LLMs* (QLLM-Eval, ICML 2024) — https://arxiv.org/abs/2402.18158
- Fireworks, quantization evaluation — https://fireworks.ai/blog/fireworks-quantization
- Unsloth Dynamic 3.0 GGUFs — https://unsloth.ai/docs/basics/dynamic-3.0-ggufs
- LocalBench GGUF methodology — https://localbench.substack.com/p/gguf-benchmark-methodology
- oobabooga, KV-cache quantization KLD — https://localbench.substack.com/p/kv-cache-quantization-benchmark
- McLeod, measuring quantization quality with KL divergence — https://smcleod.net/2026/04/measuring-model-quantisation-quality-with-kl-divergence/
- InventiveHQ, local LLM benchmarks on an RTX 5060 Ti 16 GB — https://inventivehq.com/blog/local-llm-benchmarks
- llama.cpp perplexity/KLD tool — https://github.com/ggml-org/llama.cpp/blob/master/tools/perplexity/README.md
- llama.cpp discussion #4110 (PPL is a poor quantization metric) — https://github.com/ggml-org/llama.cpp/discussions/4110

### Long context
- RULER — https://arxiv.org/abs/2404.06654 · https://github.com/NVIDIA/RULER
- LongPPL — https://arxiv.org/abs/2410.23771 · https://github.com/PKU-ML/LongPPL

### Speculative decoding
- Leviathan, Kalman & Matias (the guarantee) — https://arxiv.org/abs/2211.17192
- Chen et al., accelerating decoding with speculative sampling — https://arxiv.org/abs/2302.01318
- **llama.cpp Issue #25618** (independent report of the same divergence on quantized targets, open) — https://github.com/ggml-org/llama.cpp/issues/25618
- *Speculative Decoding at Temperature Zero* (TOST equivalence; finds invariance holds) — https://arxiv.org/abs/2606.25097
- *Correctness Forensics for Batch Speculative Decoding* — https://arxiv.org/abs/2510.22876
- *Lossless but Not Free* (consumer hardware; 3 of 5 configs net slowdowns) — https://arxiv.org/abs/2607.17283
- *An Empirical Study of Speculative Decoding on SE Tasks* (assumes losslessness, never tests it) — https://arxiv.org/abs/2604.26469
- **DFlash: Block Diffusion for Flash Speculative Decoding** (R12) — https://arxiv.org/abs/2602.06036
- **dflash-mlx**, the port claiming "bit-for-bit identical to plain target decoding" (R12) — https://github.com/Aryagm/dflash-mlx

### Figure production
- **PaperBanana: Automating Academic Illustration for AI Scientists** (R11) — https://arxiv.org/abs/2601.23265
- PaperBanana implementation — https://github.com/llmsresearch/paperbanana

### Consumer-hardware inference measurement
- ConsumerBench — https://arxiv.org/abs/2506.17538
- Silicon Showdown (the "VRAM Wall") — https://arxiv.org/abs/2605.00519

### Artifact release
- ACM Artifact Review and Badging v1.1 — https://www.acm.org/publications/policies/artifact-review-and-badging-current
- USENIX OSDI '26 Call for Artifacts — https://www.usenix.org/conference/osdi26/call-for-artifacts
- MLSys 2026 CFP (ACM badging) — https://mlsys.org/Conferences/2026/CallForResearchPapers
- Zenodo–GitHub integration and DOI versioning — https://blog.zenodo.org/2017/05/30/doi-versioning-launched
- Software Heritage SWHIDs (ISO/IEC 18670) — https://docs.softwareheritage.org/devel/swh-model/persistent-identifiers.html
- Papers with Code shutdown, July 2025 — https://hyper.ai/en/news/42900
