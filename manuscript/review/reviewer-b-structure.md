# Reviewer B — framing, structure, narrative, venue fit

**Blind independent assessment.** I have read `README.md`, `CLAUDE.md`, `manuscript/OUTLINE.md`,
all 34 entries in `docs/paper/PAPER-NOTES.md`, `docs/paper/METHOD-REFERENCES.md` (R1–R10),
`docs/paper/TRACK-A-DECISION.md`, and the decision log and ledger in
`docs/build-stream/2026-08-30-quant-bench-trackA.md`. I also opened the underlying artifacts under
`data/raw/e12/` and recomputed several quantities directly, because a structural review that does
not look at the numbers is worthless. I have deliberately **not** read
`manuscript/review/insider-notes.md` or any other reviewer's file.

I am reviewing this as an ML researcher who has published measurement and systems papers, asking
one question throughout: *if this arrived on arXiv tomorrow, would I read past the abstract, and
would I cite it?*

---

## 1. Verdict on publishability

**Yes, there is a paper here, and it is better than the outline currently believes.** It is not a
marginal paper padded out with a solo researcher's log; it contains at least two results that I
would cite, one of which the outline does not name as a contribution at all because nobody has
plotted it yet.

Three separate verdicts, because they differ:

| question | verdict |
|---|---|
| Is there enough measurement for an arXiv technical report? | **Yes, comfortably.** More than enough. The problem is selection, not sufficiency. |
| Is the current thesis the right one to lead with? | **No.** It is the second-best framing and it is the one most exposed to the obvious reviewer attack. §3 below proposes the replacement. |
| Would this pass peer review at a workshop / benchmarks track? | **Plausibly, after restructuring** — NeurIPS D&B, MLSys, or an ACL "Insights from Negative Results" style venue. Not a main-track ML conference: single model, single host, no new method. arXiv is the right first home regardless. |

**What makes it real.** Three things are genuinely hard to get elsewhere and are done properly here:

1. **A monotone, well-powered, three-domain divergence ladder** measured with the field's own
   instrument, at 65,536 tokens per cell, with adjacent arms separated at 3.7–11.8 σ. This is not a
   small-n result. It is the opposite: it has more statistical power than most published
   quantization tables, and it is measured on **code**, which the published tables are not.
2. **A systems result with a large effect and zero statistical exposure** — the context ceiling is a
   property of the tensor split, not of the quantization (PN-6, PN-7). Q5_K_XL *fails to load* at
   the default split and loads at five different `-ts` ratios. Q6_K_XL's feasible ratio set at
   196,608 is a **single island** (`56,44` loads; `52,48`, `54,46`, `58,42` and the default all
   OOM). That is a load/no-load observation, not a mean with an interval. Nobody can argue with it.
3. **A refuted premise that the field asserts casually** — speculative decoding is not
   output-identical here, and PN-26 upgrades that from "not identical" to *deterministically*
   non-equivalent, which is a much stronger and rarer claim. Byte-identical self-reproduction on
   both arms, byte-different from each other on exactly 33 of 164 problems, both times.

**What is weak, and must not be led with.** The three "the benchmarks cannot see it" nulls are
n=400, n=164 and n=12–25. The outline's defence — *structurally* insensitive, not merely
underpowered — is currently carried by (a) an argmax mechanism that PN-22's own caveat calls "an
interpretation … not a controlled test of it", and (b) one discordant RULER sample out of twelve.
A reader who has reviewed evaluation papers will reach that sentence and stop. §3 fixes this, and
the fix is free: the evidence is already on disk.

---

## 2. The contribution, stated three ways

Ordered by how strongly I believe each would survive review, and how likely I am to cite it.

### Statement 1 — the strongest, and currently unnamed

> **Quantization damage in code is tail-concentrated.** Ninety per cent of code tokens are *less*
> perturbed by quantization than prose tokens are; the top one per cent are up to eight times more.
> The familiar summary — "code is about twice as bad as prose" — is the average of two opposite
> facts, and the crossover sits between the 90th and 95th percentile of the per-token divergence
> distribution. Averaged metrics and argmax-scored benchmarks both integrate that tail away, which
> is why an instrument that separates these arms at 3.7–11.8 σ coexists with three task benchmarks
> that bound their end-to-end difference below four points.

This is not a new experiment. It is already in `data/raw/e12/ssa/ssa-results-parsed.json` and
`ssa-s5-results.json`, in the `median_kld`, `kld_90p`, `kld_95p`, `kld_99p` fields that the paper
notes never mention. Recomputed:

| statistic | UD-Q6_K prose → code | UD-Q5_K_XL prose → code | UD-Q4_K_XL prose → code | code ÷ prose (Q4_K_XL) |
|---|---|---|---|---|
| median KLD | 0.001392 → 0.000007 | 0.001810 → 0.000010 | 0.003509 → 0.000017 | **0.005×** |
| 90th pct | 0.006742 → 0.003029 | 0.008856 → 0.004790 | 0.016333 → 0.010006 | 0.61× |
| 95th pct | 0.010549 → 0.016109 | 0.013936 → 0.026311 | 0.025546 → 0.055800 | 2.18× |
| 99th pct | 0.028639 → 0.142839 | 0.037323 → 0.250389 | 0.069578 → 0.562891 | **8.09×** |
| **mean** | 0.003321 → 0.005829 | 0.004465 → 0.010285 | 0.008207 → 0.021529 | 2.62× |

Read the columns: the code/prose amplification runs **0.005× → 0.61× → 2.18× → 8.09×** across the
quantile axis. The mean lands at 2.62× because it is dragged there by the tail; it sits between the
95th and 99th percentile of its own distribution. And the amplification at the 99th percentile grows
with aggressiveness exactly as the mean does (4.99 → 6.71 → 8.09), so the effect is not an artifact
of one arm.

Why this is the strongest statement available:

- **It explains PN-16 instead of merely reporting it.** PN-16 records the paradox — top-1 agreement
  is *higher* on code (98.4–99.4 %) while mean KLD is *double* — and offers predictability as an
  interpretation. The quantile table turns that interpretation into a measurement: median code KLD
  is ~10⁻⁵, i.e. the typical code token is essentially untouched, which is precisely why top-1
  survives. PN-16 stops being a caution about metric pairs and becomes a mechanism.
- **It supplies the mechanism the saturation thesis is currently missing.** "Benchmarks are
  saturated" is a claim about benchmarks. "Damage occupies ~1 % of positions, and those positions
  are where the model chooses" is a claim about the model, from which the benchmark behaviour
  follows as a prediction rather than an assertion.
- **It makes a prediction the data confirms.** If damage is concentrated in a small fraction of
  branch points, a 164-problem paired coding benchmark should show a *handful* of discordant
  problems, not zero and not many. Observed: **3 of 164** on base tests and **5 of 164** on
  base+extra. The paper currently reports this as a null. It is not a null; it is a confirmed
  quantitative prediction, and it should be written that way.
- **It is well powered.** 65,536 tokens per cell, σ/256 standard errors. It is immune to the "you
  are underpowered" attack that the three task nulls invite.
- **S11 corroborates it from the other direction.** `data/raw/e12/s11/s11-divdepth.json` was
  rejected as an instrument because free greedy generation from a real code prefix diverges between
  adjacent quantization levels at character **2, 5, 10, 14, 62, 71, 126** — the metric floors
  instantly. That failure is itself evidence: in open-ended generation you hit a decision token
  almost immediately, so tail damage manifests immediately. Reported as a rejected instrument it is
  a footnote; reported as corroboration it is a result.

### Statement 2 — the current thesis, demoted to a consequence

> Saturation, not modality and not context length, determines whether a task benchmark can see
> quantization damage. Three independent *scoring modes* — argmax over candidates, free generation
> scored by unit tests, free generation scored by string match — each fail to separate arms that
> divergence separates decisively, and each fails for the same reason: both arms sit against the
> benchmark's ceiling.

Keep it. It is a good organising idea and the three-instrument sweep is real work. But it must
follow from Statement 1 rather than stand alone, and one claim inside it must be softened: **"depth
did not reveal it, difficulty did" rests on a single discordant sample out of twelve** (Wilson
[64.6, 98.5] vs [75.7, 100.0]). As a *contribution bullet* that will not survive contact with a
reviewer. As a *hypothesis raised by a saturated result and consistent with Red Hat's published
band*, stated in one sentence with the interval attached, it is fine and even useful.

### Statement 3 — the systems paper hiding inside this one

> On a multi-GPU consumer host without a fast interconnect, the usable context ceiling is a property
> of the tensor split, not of the quantization. A published ceiling without its split is not a
> reproducible number. The optimum is quant-specific, non-monotone, and in one case a single
> feasible island in the ratio space.

This is the most immediately *useful* result in the repository and the one most likely to be cited
by practitioners rather than researchers. It has a large effect (+33 % context and +93 % decode from
one flag, per the E11c machine log; `131,072 → 212,992` on Q6_K_XL against a previously published
ceiling), it is binary, and it is reproducible from the artifact. It also supports the paper's
broader methodological theme — *a number published without its configuration is not a measurement* —
which is the same theme as the reproducibility register in §9.

**My recommendation: lead with 1, structure around the pairing of 1 and 2, and give 3 its own
results section rather than burying it as "systems findings".**

---

## 3. The single change I would insist on: stop framing the nulls as blindness

This is the most consequential piece of advice in this review, so I am giving it its own section.

`docs/paper/PAPER-NOTES.md` PN-28 reports the generative anchor as "McNemar p = 1.0, no
distinguishable difference", and the outline elevates it to "the generative coding benchmark cannot
separate the ladder's two extremes either." Both are true and both undersell the result badly,
because **a p-value is not the informative statistic for a paired design with three discordant
pairs.** The informative statistic is the interval on the paired difference.

I computed it (Newcombe's score interval for paired proportions, from the discordance counts in
`data/raw/e12/s9/s9-scores.json` `s6_paired`):

| metric | b (Q4 only) | c (Q6XL only) | Δ pass@1 | **95 % CI on the paired difference** | 90 % CI |
|---|---|---|---|---|---|
| HumanEval base | 1 | 2 | −0.61 pts | **[−3.81, +2.41]** | [−3.13, +1.77] |
| HumanEval+ (base+extra) | 2 | 3 | −0.61 pts | **[−4.08, +2.76]** | [−3.41, +2.11] |

For comparison, an *independent* two-arm comparison at n=164 carries roughly ±5.3 points on the
difference; the paired analysis is about 1.7× tighter. So the correct sentence is not "the benchmark
cannot see it." It is:

> **A 3.69× increase in code-prompt KL divergence — the full width of this quantization ladder —
> changes HumanEval+ pass@1 by at most about four points, and most plausibly by under one.**

That is a *bounded, quantitative bridge between the two instruments*, and it is the single number a
practitioner reading this paper most wants. It also repositions the whole paper from a defensive
posture ("your instruments are wrong") to a constructive one ("here is what each instrument can and
cannot tell you, and here is the exchange rate between them"). Reviewers reward the second and
punish the first.

The same treatment applies to HellaSwag (four arms, Wilson intervals ≈ ±3.7 points each, all
overlapping — report the *paired* discordance of 2–4 items out of 400, which is the informative
quantity) and to RULER (12/12 at the deepest rung gives Wilson [75.7, 100.0]; that arm bounds
essentially nothing and the paper should say so plainly rather than presenting it as a null).

The methodological move to make explicit: **report equivalence bounds (TOST-style), not
non-significance.** R6 (Miller, *Adding Error Bars to Evals*) already licenses the paired analysis;
this extends it by one honest step. It costs zero GPU hours — the per-problem outcome vectors are
already in `s9-scores.json` and `ssa-s7-paired.json`.

Consequence for the thesis: the paper's honest closing position becomes stronger, not weaker.

> Quantization damage is real, tail-concentrated and domain-amplified. At the single-turn task
> scale these benchmarks measure, its effect is bounded small. Whether tail damage *compounds* over
> long-horizon agentic work — where a model makes thousands of decisions and each one is a draw
> from the perturbed tail — is the question that matters and is unmeasured, including here.

That last sentence is the paper's best closing line. It is honest, it names the open problem
precisely, and it is the sentence that gets the paper cited by the next person who runs the agentic
experiment.

---

## 4. Recommended full outline, with PN mapping and target lengths

Target: **18–22 pages single-column preprint format**, ≈ 9,000–10,500 words of body text plus
appendices. Six figures, five tables in the body; everything else appendix. Numbers below are body
words, excluding captions.

### Front matter — 350 words
Title, single author, abstract (§8 of this review), keywords. **Include an "Artifacts" line in the
abstract or immediately after it**, with the repository/archive URL, because the artifact register
is one of this paper's genuine strengths and readers must know it exists before page 3.

### §1 Introduction — 900 words
**Frame it as a practitioner question with a measurement answer, not as a critique.**
Opening: a solo researcher with two 16 GB consumer GPUs must choose one quantization of a 27B coding
model. Every instrument the field offers gives a different answer, and three of them give no answer
at all. Which one is right, and why do they disagree?

Contributions, revised (five, in this order):
1. Quantization damage on code is **tail-concentrated**: the code/prose amplification runs 0.005× at
   the median to 8.09× at the 99th percentile, crossing 1.0 between p90 and p95. The mean's "2×" is
   an artifact of that shape. — **PN-13, PN-14, PN-16, PN-21 + the unreported quantile fields**
2. Damage rises monotonically as the corpus approaches the task (prose → generic code → task
   prompts, 3.13–4.40×), and the amplification itself grows with aggressiveness, so quantization
   tables published on prose are the most flattering possible view. — **PN-21, PN-14**
3. Three task benchmarks across three scoring modes bound the end-to-end effect of the full ladder
   width at **≤ ~4 points**, and cannot resolve below that at the sample sizes they have. This is a
   reconciliation, not a failure: it is what tail-concentration predicts. — **PN-22, PN-28, PN-33,
   PN-34**
4. The usable context ceiling on this host is a property of the **tensor split**, not of the
   quantization; the optimum is quant-specific, non-monotone, and in one case a single feasible
   island. — **PN-6, PN-7, PN-8**
5. Speculative decoding on this engine is **deterministically non-equivalent** to unspeculated
   decoding — reproducible, and reproducibly different on one generated function in five. — **PN-23,
   PN-26**

Close the introduction with one paragraph on scope: one model family, one engine image, one host,
ladder-relative reference. Do it here, not only in §7. A reader who finds the limitation themselves
on page 14 distrusts everything before it.

### §2 Background and related work — 1,000 words
Follow the R1–R10 map, which is already good. Structure it as three threads rather than a list:
- **The instrument thread** — PPL's averaging bias and the case for KLD (R2, R4, R10); the tool
  itself (R1); who ranks quantizations on it in practice (R3, R5).
- **The evaluation thread** — task batteries applied to llama.cpp quantization (R7, read as the
  caution it is); error bars, paired differences and power (R6); long-context evaluation (R8).
- **The closest published work** — Red Hat's RULER-at-quantization study and arXiv 2505.20276 (R9);
  say explicitly what they have that this does not (clusters, ~200,000 evaluations) and what this
  has that they do not (code-domain divergence, the quantile decomposition, a consumer host).

Add one paragraph the outline is missing: **benchmark saturation / ceiling effects as a known
problem in LLM evaluation.** This positions §5.2 against an existing conversation instead of
inventing one. See §6 of this review for candidates.

### §3 Setup — 700 words + Table 1
Host, engine pinned by image digest, four arms, the `env-manifest.json` provenance discipline.
Table 1 = arms × file size × sha256 prefix × role. **PN-1 through PN-4 belong here as a short
"harness validation" subsection, framed as a result**: the measured sampling defaults match neither
the documented engine defaults nor either official preset (PN-1); thinking is on by default and the
widely-cited disable idiom raises a Jinja exception (PN-2, PN-3); `-fit` cannot be trusted to bound
allocation (PN-4). Two hundred words, and it earns its place because it tells the reader that every
number downstream was produced under an asserted contract.

PN-31 as a **two-sentence footnote** to the host spec, exactly as the owner directed — with the one
generalisable clause kept: *the standard divergence tooling's resident footprint scales with context
length, which is why the published quantization tables it produces are all measured near 2K.*

### §4 Method — the Small-Sample Accuracy protocol — 900 words + Table 2
The design principle stated once and clearly: **divergence instruments draw power from token count;
task benchmarks draw it from problem count.** Reference-arm choice and the ladder-relative
consequence. The 65,536-token budget. Pre-registered interpretation bands (<0.007 Fireworks;
0.01–0.03 LocalBench) declared as external reference points, not adopted rules.

**Add a subsection the outline does not have: "What we report, and what we refuse to report."**
Three rules — every table names protocol, n and estimator; a comparison is reported as an
equivalence bound rather than a p-value; a claim enters only if the interval separates or the effect
exceeds the interval width. This is the paper's methodological spine and it deserves 150 words in
Method, not only a bullet in a repo README.

Table 2 = the instrument inventory: instrument, unit of power, n, wall-clock, what it resolved.

### §5 Results — ≈ 4,200 words total

#### 5.1 The shape of the damage — 900 words · **Figure 1, Figure 2, Table 3**
**This is now the paper's opening result and its strongest.** The quantile decomposition; the
crossover between p90 and p95; the mean sitting in the tail; the top-1/mean-KLD reconciliation
(PN-16) delivered as a mechanism rather than a caution; RMS Δp as the corroborating measure
(1.60/1.78/2.46 % prose → 3.34/4.38/6.24 % code → 4.71/5.95/8.39 % task).
**PN-13, PN-14, PN-16, PN-21.**

#### 5.2 Domain and the distance to the task — 550 words · **Figure 2, Table 3**
The three-tier hierarchy, monotone in every domain, 3.7–11.8 σ between adjacent arms. The
threshold-crossing statement (two of three arms pass on prose, one on generic code, none on the task
distribution) with the external-band caveat attached in the same sentence.
**PN-21, PN-14, PN-13.**

#### 5.3 What three task benchmarks can and cannot bound — 1,000 words · **Figure 3, Table 4**
Rewritten per §3 of this review. Present all three as *bounds*, not nulls:
HellaSwag (n=400, 4 arms, paired discordance 0–4 items, most-quantized arm nominally highest);
HumanEval+ (n=164 paired, discordance 3 and 5, **95 % CI [−3.81, +2.41] and [−4.08, +2.76] points**);
RULER S-NIAH (100.0/100.0 at 8,192 / 32,768 / 131,072, sixteen-fold context and zero discrimination,
Wilson [75.7, 100.0] at the deepest rung — an arm that bounds nothing, and say so).
Then MK-NIAH in **one paragraph** as a hypothesis with its interval: 100.0 vs 91.67 on one discordant
sample of twelve, overlapping intervals, consistent with R9's published 85–88 % band for INT W4A16 at
128K, *not established here*.
Close with the reconciliation paragraph: the discordance rates are what tail-concentration predicts.
**PN-22, PN-28, PN-33, PN-34.**

#### 5.4 The context ceiling belongs to the split — 700 words · **Figure 4, Table 5**
The same configuration failing at the default split and loading at five ratios; the quant-specific
non-monotone optimum; Q6_K_XL's single feasible island; balance and throughput as opposing
objectives (the most balanced ratio is the slowest by 27 %). State the per-card constraint physically
— weights *and* the KV slice of a layer live on one card, there is no NVLink, so the binding limit is
per-card and not the aggregate. **PN-6, PN-7, PN-8.**

#### 5.5 Speculative decoding is part of the accuracy configuration — 700 words · **Figure 5**
Non-identity at greedy (131/164), then PN-26's determinism control upgrading it to *deterministically*
non-equivalent — byte-identical self-reproduction on both arms across runs a day apart, byte-different
from each other on exactly 33 problems both times. Retract PN-23's own mechanistic speculation in the
text (PN-26 does this correctly; keep that honesty visible, it is a credibility asset). The
context-dependent method ranking: DFlash2 fastest at 32 K, unable to reach the deployment window at
all. Acceptance falls monotonically with draft depth in 12 of 13 adjacent pairs (sign test p = 0.0017).
**PN-23, PN-26, PN-29, PN-32.** Explicitly *do not* report a draft-depth ranking (PN-32 says it is
unanswerable at n=3).

#### 5.6 Speed does not discriminate; KV quantization is not free — 350 words
Two short results kept together because each is one paragraph.
Speed: 6.7 % span across arms against 32.9 % within-arm noise; the cheaper arm is not faster, only
less accurate, and earns its place on VRAM footprint alone (**PN-19**).
KV: q4_0 costs 0.002955 ± 0.000127 KLD against f16 — 51 % of a quantization level — while perplexity
on the identical pair moves +0.15 %, which is the paper's cleanest single demonstration of averaging
bias (**PN-15**). That PPL/KLD contrast deserves to be quoted in the abstract.

### §6 What the measurements cost — 500 words + Table 2 (referenced back)
Keep this section; it is unusual and it is a real contribution for the audience that will actually
read this paper. But **fix the number.** The README and outline claim "~20 minutes of divergence per
arm resolves what ~20 hours of task benchmarking does not." From the artifacts' own
`started_utc`/`finished_utc`:

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

That is **≈ 2.3 h of divergence resolving the ladder against ≈ 11.4 h of task and speculation
benchmarking that does not**. A 5× contrast is entirely sufficient and is defensible from the
artifacts. "20 hours" is not, unless it is counting the historical pre-E12 SWE-bench corpus — in
which case say so, because a reviewer who divides the numbers will find the discrepancy.

### §7 Threats to validity — 900 words
Write this before polishing results, as the outline already says. Keep the outline's eight items;
reorder so the two that matter most come first, and add three:

1. **Ladder-relative reference** (no FP16 fits the host; the reference's own degradation is
   unmeasured and zero by construction). Add the mitigating argument the outline omits: because the
   reference is itself quantized, every arm's true distance from FP16 is *larger* than reported, so
   every quantitative claim is conservative in the direction that matters.
2. **Prompt-token divergence is not generation quality**, with the honest bridge from §5.3 rather
   than a bare disclaimer.
3. **NEW — the compounding question is unmeasured.** Single-turn benchmarks bound the per-problem
   effect; no measurement here says what happens over a thousand agentic decisions. Name it as the
   paper's principal open problem rather than letting a reviewer name it for you.
4. **NEW — one model family, one engine image, one host, two single-domain corpora.**
5. **NEW — the calibration-contamination risk** (R3): Unsloth's imatrix data is not published, so a
   wikitext-favourable bias cannot be excluded — which is itself an argument for weighting the code
   domain.
6. Long-context accuracy bounded, not resolved (PN-33's n=12).
7. PN-9's quant/depth/ratio confound is unresolved and no per-arm best draft depth is reported.
8. Spec-decode results are greedy-only.
9. No per-config energy figure.
10. Not comparable to published scores: logprob instruments run greedy; the official presets are
    temp 0.7/1.0; Qwen publishes LiveCodeBench v6, SWE-bench **Pro** and Terminal Bench, none of
    which are set up here.

### §8 Conclusion — 350 words
Three sentences of result, one of consequence for practice, one of open problem. End on the
compounding question.

### Appendix A — Practitioner configuration — 700 words
`TRACK-A-DECISION.md`, compressed and framed as *what this analysis implies for one concrete
deployment*, explicitly not the paper's recommendation. Include Amendment 2 and the reverted
draft-depth flag as a worked example of a withdrawn claim — one paragraph, not three.

### Appendix B — The reproducibility register — 900 words
**Cut from seven entries to four**, unified by one thesis: *silent success is the dominant failure
mode of automated benchmarking.* Keep the four that are structurally different from each other:
- **PN-17** — a step scored by exit code alone reported a fully successful run that measured nothing
  (Unicode `±` vs ASCII `+/-`; 1.5 h of GPU recovered only because raw output had been preserved).
- **PN-5** — a contract documented in a docstring and never asserted in code is not a contract
  (79.7 % prefill reported as success, making the cell incomparable).
- **PN-30** — a throughput measurement that timed 17 generated tokens and produced 52 tok/s at
  ctx 131,072; asserting the prompt depth does not assert that anything was generated. This one also
  withdrew a published claim, which makes it the most valuable of the four.
- **PN-25** — a drafter mis-bound to the wrong engine build produced a clean `0.000` indistinguishable
  from catastrophic performance.
Keep **PN-20** only if space allows (an unnamed estimator reversing a ranking — it is the only one
that changed a conclusion). **Cut PN-10 and PN-27** (see §9 of this review).

### Appendix C — Full tables — 600 words
Complete KLD tables with every percentile, Δp and RMS Δp field; the RULER departure notes and the
`variable_tracking` exclusion (which is an honest, well-reasoned exclusion and should be visible);
the `-ts` sweep in full; per-repetition decode figures.

### Appendix D — Artifact index — 300 words
Every headline number → paper note → artifact path → serverlog. This mapping already exists and is
the paper's best defence against "we can't check this."

---

## 5. Figure specifications

The study is currently all tables. Six figures carry the argument; every one is buildable from
artifacts already on disk with matplotlib and no new GPU time.

### Figure 1 — *Where the damage is* (the paper's signature figure)
**Type.** Single panel, line plot. **x** = distribution quantile of per-token KL divergence, ordered
categorically: median · p90 · p95 · p99. **y** = code ÷ prose amplification ratio, **log scale**.
**Series** = three lines, one per arm (UD-Q6_K, UD-Q5_K_XL, UD-Q4_K_XL). **Reference** = a heavy
horizontal line at y = 1.0 labelled *"code and prose equally affected"*, and a marker on each line
showing where the **mean** falls (it sits between p95 and p99 for every arm).
**Data.** `data/raw/e12/ssa/ssa-results-parsed.json`, fields `median_kld`, `kld_90p`, `kld_95p`,
`kld_99p`, `mean_kld`, cells `ssa-<arm>-{wikitext2,code}-kld`.
**What it must show at a glance.** Every line starts far below 1.0 and ends far above it, crossing
between p90 and p95, and the three lines are ordered by aggressiveness at the tail. Caption states
the one sentence: *"Ninety per cent of code tokens are less perturbed by quantization than prose
tokens; the top one per cent are up to eight times more. The commonly quoted 2× mean is the average
of these two opposite facts."*
**Optional third series.** Add the HumanEval+ task-prompt domain (`ssa-s5-results.json`) as a dotted
line per arm, or split into a two-panel figure (code/prose, task/prose). The task domain is
uniformly above prose at every quantile above the median, which is a cleaner but less surprising
story — keep it as panel (b) rather than crowding panel (a).

### Figure 2 — *The ladder, three domains, one instrument*
**Type.** Dot plot with error bars (not bars — bars imply a zero baseline that a divergence has no
right to). **x** = mean KLD, **log scale**. **y** = three arms × three domains as nine rows, grouped
by arm. **Error bars** = ± the tool's reported standard error. **Shaded band** = Fireworks' published
<0.007 high-quality region; a second, lighter band for LocalBench's observed 0.01–0.03 Q4_K_M range.
**Data.** `ssa-results-parsed.json` + `ssa-s5-results.json`, `mean_kld` / `mean_kld_err`.
**What it must show.** Monotone in every domain; error bars invisible at this scale (that is the
point — say so in the caption); and the band crossings, so a reader sees two arms pass on prose, one
on code, none on task prompts, without reading a number.
**Caption must carry** n = 65,536 tokens per cell (18,432 for the task domain), the reference arm,
the ladder-relative caveat, and the note that the bands are external reference points.

### Figure 3 — *One axis, two instruments* (the money shot)
**Type.** Two stacked panels sharing an x-axis. **x** = the four arms in ladder order
(UD-Q6_K_XL → UD-Q6_K → UD-Q5_K_XL → UD-Q4_K_XL).
**Top panel (task benchmarks).** y = accuracy %, three series with intervals:
HellaSwag n=400 (Wilson, ≈ ±3.7 pts); HumanEval+ n=164 (Wilson, two arms only — draw the pair and
annotate the *paired* 95 % CI [−4.08, +2.76] as a bracket between them, which is the honest and much
tighter statement); RULER S-NIAH n=12 at 131,072 (two arms, both 100.0, Wilson [75.7, 100.0]).
**Bottom panel (divergence).** y = mean KLD on code, log scale, with ± SE — a clean monotone rise
whose error bars are smaller than the marker.
**Data.** `ssa-s7-results.json`, `s9-scores.json`, `s12-ruler.json`, `ssa-results-parsed.json`.
**What it must show.** Flat lines with wide overlapping intervals above; a monotone staircase with
invisible intervals below. Same x-axis, same arms, same host, same fortnight. This figure *is* the
paper's argument and should be referenced from the abstract.
**Do not** put the two on a shared y-axis or a twin axis — that invites a false visual equivalence.

### Figure 4 — *The ceiling is a property of the split*
**Type.** Categorical matrix / heatmap. **Rows** = the four arms. **Columns** = `-ts` ratio
(`default`, `52,48`, `54,46`, `56,44`, `58,42`, `60,40`, `62,38`). **Cell fill** = loaded (with
decode tok/s printed in the cell) vs failed (hatched, with the classified failure mode:
`compute-buffer-oom`, `init-hang`). **Row annotation** = the context at which the row was swept
(262,144 for Q4_K_XL / Q5_K_XL / Q6_K; 196,608 for Q6_K_XL).
**Data.** `data/raw/e12/tsweep-v2-{Q4_K_XL,Q5_K_XL,Q6_K,Q6_K_XL}.json`, fields `ts`,
`ctx_requested`, `ok`, `failure_mode`, `decode_tok_s`, `imbalance_mib`, `vram_peak_mib`.
**What it must show.** The default column is red for three of four arms. Q5_K_XL's feasible set is
every non-default ratio. Q6_K's is two adjacent ratios. **Q6_K_XL's is a single island at `56,44`
with failures on both sides** — that cell is the figure's punchline and should be annotated
directly.
**Companion inset or panel (b).** Scatter of decode tok/s (y) against VRAM imbalance in MiB (x) for
Q5_K_XL's five loading ratios, showing the *most balanced* ratio (28 MiB imbalance, `58,42`) is the
*slowest* (8.50 tok/s) — balance and throughput are opposing objectives. This is PN-8 and it is a
genuinely counter-intuitive result that deserves the pixels.

### Figure 5 — *Speculation buys speed and spends identity*
**Type.** Paired bar / dumbbell, two panels.
**Panel (a).** Decode tok/s at ctx 32,768, medians over 164 generations: no-spec 18.46 · MTP n=2
37.44 · MTP n=4 47.03 · DFlash2 51.78. Annotate the speedup multiple above each bar.
**Panel (b).** Exact byte-reproduction rate against the no-spec baseline on the same 164 problems:
no-spec self-repeat **164/164 (100 %)** · MTP n=2 **131/164 (79.9 %)** · MTP n=4 **131/164 (79.9 %)**
· DFlash2 132/164 (80.5 %, **hatched and labelled engine-confounded** — different image, per PN-29's
caveat).
**Data.** `data/raw/e12/s8/s8-humaneval.json`, `data/raw/e12/s9/s9-determinism.json`,
`data/raw/e12/s9/s9-dflash.json`.
**What it must show.** The no-spec self-repeat bar at exactly 100 % is what makes the figure a
*determinism* result rather than a noise result. It must be present and visually adjacent to the
79.9 % bars. Caption: *"The engine reproduces itself byte-exactly; speculation reproducibly produces
different output on one generated function in five."*

### Figure 6 — *Acceptance falls with draft depth — and why three repetitions cannot rank anything*
**Type.** Two panels, one per matched depth (131,072 and 196,608).
**x** = draft depth {2, 4, 8}. **y** = MTP draft acceptance. **Series** = four arms.
**Critical detail:** plot the **per-repetition points** as small translucent markers behind the
cell-level line, so the within-cell spread (up to 0.629 within a single cell) is visible against the
pooled Wilson interval (±0.02 over 1,000–4,000 draft events). Draw both intervals: the misleadingly
tight pooled one and the honest between-generation one.
**Data.** `data/raw/e12/s9/s9d-depthsweep.json` (per-cell and per-rep), plus `s9e-n262k.json` for
the n=8 load failure at 262,144 (mark it as an absent point with an annotation, not a zero).
**What it must show.** Monotone decline in 12 of 13 adjacent pairs (annotate the sign test
p = 0.0017), *and* that the ranking question is not answerable — this figure does double duty as the
paper's worked illustration of R6's clustered-standard-error trap. Caption should say both.

### Tables that stay in the body
- **Table 1** — arms: quant, file bytes, sha256 prefix, role, ceiling, winning `-ts`.
- **Table 2** — instrument inventory: instrument, unit of statistical power, n, wall-clock, arms
  separated. (§6 of the paper.)
- **Table 3** — the full divergence matrix: 3 arms × 3 domains × {mean ± SE, median, p90, p95, p99,
  top-1 agreement ± SE, RMS Δp}. This is the paper's core data and belongs in the body at full width.
- **Table 4** — task-benchmark bounds: benchmark, n, scoring mode, per-arm score, paired discordance,
  **equivalence bound**, what it can and cannot resolve.
- **Table 5** — context ceilings: arm, default-split result, best ratio, ceiling, decode at ≥ 0.90
  depth, VRAM peak per card, imbalance.

### Figures I would *not* draw
- Any energy or thermal figure. PN-11's window is dirty (mixed idle and load) and PN-12 is
  explicitly confounded (airflow uncontrolled). One sentence each in Setup, no plot.
- A speed-vs-quant bar chart. PN-19 is a null with 32.9 % within-arm noise; a bar chart of
  12.70/12.61/11.90 would imply a ranking the data does not support. State it in prose.
- Anything from the historical pre-2026-08-29 corpus. Different engine image, `-sm tensor` no longer
  reproducible; it cannot share an axis with current measurements.

---

## 6. Related-work positioning

The R1–R10 map in `METHOD-REFERENCES.md` is unusually good — better than most related-work sections
I review, because each entry already states *what constraint it imposes on our design*. Keep that
structure in the paper. Below is how I would position against each, plus what is missing.

| work | what it establishes | how this paper positions |
|---|---|---|
| **llama.cpp perplexity/KLD tool** (R1) | The instrument itself; emits mean KLD ± uncertainty, Δp percentiles, top-1 agreement in one pass | *We use the field's own shipped instrument, unmodified.* Not a bespoke metric. But we report the **percentile fields it already emits and everyone ignores** — that is the paper's opening result and it costs nothing to obtain. |
| **llama.cpp discussion #4110** (R2) | The engine community's own argument that PPL is a poor quantization-loss metric and KLD is better | Establishes divergence-first as the *norm* in this ecosystem, not a shortcut. Cite early so §4 does not read as methodological invention. |
| **Unsloth Dynamic GGUFs** (R3) | Provenance of the arms; ranks its releases on mean KLD; warns explicitly that calibrating and evaluating on Wikipedia-like data overfits the metric | Position as **both the object of study and the source of the warning we act on.** Their own caution is the argument for our code domain. Be scrupulously fair: we are testing their artifacts on a corpus they did not choose, and we cannot inspect their imatrix data — state it as a limitation, not an insinuation. |
| **Fireworks quantization evaluation** (R4) | Production practice: KLD + rejection rate, prefill/generation split, forced reference completions, published <0.007 threshold, the averaging-bias argument | The forced-completion technique is what makes the task-prompt domain (S5) possible in 22 minutes. Their threshold is our external band. **Differentiator:** they report on prose/general prompts; we show the threshold verdict *flips by domain* — two arms pass on prose, none on the task distribution. That is a direct, respectful extension of their published rule. |
| **LocalBench** (R5) | The closest published analogue: ~250 k tokens, 6 categories, KLD on prompt tokens + top-1 agreement, observed 0.01–0.03 for Q4_K_M | **Concede breadth, claim depth.** They cover 6 domains at ~30 k context; we cover 2 domains but decompose the *distribution* rather than reporting its mean, and pair it with three task instruments on the same arms. Our Q4_K_XL code figure (0.0215) lands inside their observed band, which is a useful external consistency check — say so. |
| **Miller, *Adding Error Bars to Evals*** (R6) | CLT standard errors, clustered SEs, paired differences, power analysis | The statistical backbone. **Extend it by one step**: report equivalence bounds rather than non-significance (§3 of this review). Also cite it as the source of the clustering diagnosis in PN-32 — the draft-acceptance sweep is a clean worked example of exactly the trap the paper warns about, with the pooled interval at ±0.02 against a true between-generation spread of ±0.3. That is a contribution *to* R6's argument, not just a use of it. |
| **arXiv 2601.14277, "Which Quantization Should I Use?"** (R7) | Recent academic llama.cpp quantization evaluation on Llama-3.1-8B via GSM8K/HellaSwag/IFEval/MMLU/TruthfulQA + WikiText PPL | **The most important positioning target: this is the paper that does what we argue against.** It reports no KL divergence, does not state token/chunk counts for its perplexity, and reports standard errors without a minimum-detectable-effect discussion. Position respectfully and precisely: not "they are wrong" but *"a task-battery design at these sample sizes cannot resolve differences of the size these quantizations exhibit, and we measure how small those differences are."* Our §5.3 equivalence bounds are the quantitative version of that critique. |
| **RULER** (R8) | The long-context standard; task categories; `string_match_all` | We use its generators, templates and metric verbatim, unit-checked on five cases. Be explicit about the departure (transport only; their `OpenAIClient` and pinned requirements are unusable here) — that honesty is a strength. |
| **Red Hat quantization-at-long-context + arXiv 2505.20276** (R9) | Published precedents running our exact experiment; accuracy-recovery framing; 85–88 % recovery for INT W4A16 at 128 K; up to 59 % drop for 4-bit on long inputs | Our MK-NIAH 91.67 % sits *beside* their band. **This is the correct use of them**: as a reference frame for a single-sample observation, not as corroboration. Concede power explicitly — they have ~200,000 evaluations and clusters; we have 150. PN-33 already says this; keep that sentence verbatim in the paper. |
| **LongPPL** (R10) | Perplexity is unreliable for long-context evaluation because it averages over all tokens and drowns the few key tokens ability turns on; weighting them yields −0.96 correlation | **This is a much more important citation than the outline treats it as, and it should move from a methodological footnote to the Introduction.** LongPPL's core claim — *the informative signal lives in a small set of key tokens and averaging destroys it* — is structurally the same claim as this paper's tail-concentration result, arrived at independently in a different setting (long context rather than quantization). Position this paper as **the quantization analogue of LongPPL's finding**, and the framing instantly has a published intellectual lineage instead of looking like a solo curiosity. If you take one piece of related-work advice from this review, take this one. |

**What is missing from the related-work map, and should be added:**

1. **Benchmark saturation / ceiling effects in LLM evaluation.** §5.3's whole argument presumes
   saturation is a recognised phenomenon. Cite the existing conversation about saturated benchmarks
   and headroom in LLM evaluation so the paper joins a discussion rather than opening one. Even one
   or two citations changes how §5.3 reads.
2. **The broader quantization-evaluation literature beyond GGUF.** The Red Hat / Neural Magic
   accuracy-vs-performance study of quantized LLMs is the obvious anchor for "how the serious
   version of this evaluation is done at scale" — cite it to show awareness of the standard, then
   state what a consumer-host study can add that a 500,000-evaluation study does not (the
   distribution shape, and the deployment-configuration axis they do not vary).
3. **Speculative decoding's losslessness claim.** PN-23/PN-26 refute a premise the field states
   casually. The paper *must* cite the original speculative-decoding formulation and the standard
   "output-distribution-preserving" claim, so the refutation is clearly scoped as *an empirical
   claim about an implementation, not a rebuttal of the algorithm's specification.* PN-23 already
   phrases it exactly right; put that sentence in the paper and attach the citation.
4. **Code-specific quantization sensitivity.** If prior work exists showing quantization hurts code
   more than natural language, it must be cited — it is the closest prior claim to contribution (2)
   and a reviewer will find it. If it does not exist, say so explicitly ("we are not aware of a
   published measurement of this asymmetry"), which is a stronger position than silence.

---

## 7. arXiv logistics

### Category

**Primary: `cs.LG`. Cross-list: `cs.CL` and `cs.PF`.**

Reasoning:
- **`cs.LG`** is where quantization work lives and where the largest relevant readership is. The
  paper's core object — how a compression scheme perturbs a model's output distribution — is machine
  learning, not linguistics and not systems.
- **`cs.CL`** is a necessary cross-list: the model is a language model, the corpora are text and
  code, and the evaluation instruments (HumanEval+, HellaSwag, RULER) are NLP benchmarks. Much of
  the closest prior work (RULER, LongPPL) sits in `cs.CL`.
- **`cs.PF` (Performance)** is the one most people would skip and I would not. Roughly a third of
  this paper is throughput, memory ceilings, multi-GPU placement and measurement-instrument
  validity. `cs.PF` is a low-volume category where this work would be visible rather than buried,
  and the split-mode result is squarely on-topic.
- **`cs.DC`** is a defensible alternative to `cs.PF` if the tensor-split result is elevated to a
  co-headline. Pick one; do not cross-list both.
- **`cs.AI`** adds nothing here. `cs.SE` is wrong — this is not software-engineering research even
  though the corpus is code.

If the tail-concentration reframe is adopted, `cs.LG` primary becomes stronger still, because the
central object is a distributional claim about a model rather than a benchmark critique.

### Template

Use a plain single-column preprint style, not a conference style file. Reasons specific to this
paper: it is table-heavy and figure-heavy, several tables are naturally full-width, and a
two-column conference style will fight you on every one of them. A conference style also implies a
submission that is not happening.

Concretely, the choices worth considering, in my order of preference for this manuscript:
1. **The community `arxiv.sty` preprint style** (the widely-used NeurIPS-derived single-column
   preprint style, `\usepackage[preprint]{arxiv}` or the `NIPS 2018`-derived variant) — clean,
   single-column, generous margins, good for wide tables.
2. **NeurIPS style with the `preprint` option** (`\usepackage[preprint]{neurips_2024}`) — single
   column, removes anonymisation and the page limit, familiar to the audience, and signals "ML
   technical report" correctly.
3. **`article` with `geometry`, `booktabs`, `siunitx`, `microtype`** — maximum control; a good
   choice given how much of this paper is numeric tables.

Whatever you pick: **`booktabs` for every table, `siunitx` with `S` columns for numeric alignment**
(critical when you are printing 0.003321 ± 0.000126 next to 0.021529 ± 0.000834), `microtype`,
`cleveref`, and vector PDF figures from matplotlib (`savefig(..., format='pdf')`) — never PNG for
line plots.

### Licence

**CC BY 4.0.** The paper's value is in being reused, quoted and built on, and the artifacts are
being released alongside. The arXiv default perpetual non-exclusive licence is more restrictive than
you want here (it does not permit redistribution or derivative works), and the NC/ND variants would
prevent exactly the reuse this work benefits from. Pick CC BY at submission — note that on arXiv the
licence is **selected at submission and cannot be changed downward later**, so decide before you
click.

### Artifacts

The repository is currently private with no public remote, and the TODO already flags this as an
owner call. My opinion: **the artifact release is a substantial fraction of this paper's value and
it should ship.** Three practical points:

1. **A private repository cannot be cited.** A URL that 404s for a reviewer is worse than no URL.
2. **Archive for a DOI, do not rely on a git host.** Deposit a snapshot (artifacts + harness source
   + the paper-notes and ledger documents) and cite the resulting DOI in the paper. A DOI is
   permanent; a repository URL is not.
3. **Decide the scope of the release explicitly.** The serverlogs on the host are the ground truth
   behind every number and are currently gitignored. At minimum, release: the JSON artifacts under
   `data/raw/e12/`, the harness source, the paper notes, and the artifact index (Appendix D). The
   full serverlog tree is a nice-to-have and large; a manifest with sha256s is an acceptable
   substitute if size is a problem.
4. **Put the artifact URL in the arXiv "Comments" field** as well as the paper, in the conventional
   form: `NN pages, N figures. Code and data: <URL>`.

### AI-authorship disclosure — do not skip this

Every entry in `PAPER-NOTES.md` is signed by a model (`claude-opus-5`, `zai/glm-5.3-flash`), the
ledger records agent-driven execution, and the decision log contains an entry explicitly labelled
"agent correction to an owner-approved plan". This is unusually well documented and it is a
methodological asset — but it must be **disclosed in the paper**, not discovered in the artifacts.

arXiv's policy is clear on the principle: generative-AI tools cannot be listed as authors, and
authors are responsible for the content and are expected to disclose the use of such tools where
relevant. Handle it in one short paragraph, ideally at the end of §3 or in a "Notes on conduct of
the work" subsection:

> The measurement campaign was executed by an agent-driven harness under the author's direction; the
> author designed the protocol, approved every experiment, and is responsible for all content. The
> decision log, ledger and per-finding notes recording that process are released with the artifacts.

Written that way it is a strength — full provenance of an experimental campaign, which almost no
paper provides — rather than something a reader stumbles on and distrusts.

### Submission checklist

- [ ] LaTeX source compiles standalone (arXiv rebuilds from source; a PDF-only submission is
      accepted only with a stated reason and is worth avoiding).
- [ ] All figures as vector PDF; no external file dependencies; no `\write18`.
- [ ] Abstract is plain text within the length limit, **no LaTeX macros, no custom commands** — it
      is entered separately into the metadata field.
- [ ] Title, author, abstract in the web form match the PDF exactly.
- [ ] Categories chosen (`cs.LG` primary; `cs.CL`, `cs.PF` cross-list).
- [ ] Licence selected (CC BY 4.0).
- [ ] Comments field: page count, figure count, artifact URL.
- [ ] Endorsement: a first-time submitter without an institutional email address may need an
      endorsement for the primary category. **Resolve this before you finish drafting**, not after —
      it is the single most common way a first arXiv submission stalls for a week. Ask someone who
      has published in `cs.LG` recently.
- [ ] Every table names its protocol, n and estimator *in the table* (the repo's own rule).
- [ ] Every pre-2026-08-29 row labelled *irreproducible-on-current-images*, or excluded.
- [ ] Withdrawn claims appear nowhere except as worked examples in Appendix B.
- [ ] AI-tool disclosure paragraph present.

---

## 8. Title and abstract

### Three candidate titles

**T1 — recommended.**
> **Quantization Damage Lives in the Tail: Domain-Dependent Divergence in a 27B Coding Model, and
> What Task Benchmarks Can and Cannot Bound**

Leads with the positive result, names the domain, and its second clause is honest rather than
accusatory. "Can and cannot bound" is the phrase that makes the paper look careful instead of
combative — and careful is what gets a solo-author measurement paper read.

**T2 — systems-forward, for a `cs.PF`-primary framing.**
> **Two 16 GB GPUs and a 27B Model: Quantization, Context Ceilings, and the Measurement Problem in
> Local LLM Deployment**

Broader appeal to the local-inference audience, weaker as a research claim. Use this if the tensor-
split result is elevated to co-headline.

**T3 — methods-forward.**
> **What the Benchmarks Cannot See: Tail-Concentrated Quantization Damage and the Case for
> Divergence-First Evaluation**

Closest to the current working title. Punchier, and the one most likely to be *shared*; also the one
most likely to draw a hostile reviewer, because it promises a negative claim about other people's
instruments that the data supports only in part. Acceptable if §5.3 is rewritten as bounds rather
than nulls.

I would avoid the current working title, *"The Benchmarks Cannot See It"*, as a standalone. It
commits the paper to its weakest claim in its first five words.

### Draft abstract (218 words)

> Quantization tables for locally served language models are published on prose corpora and
> validated on task benchmarks. We measure a 27B coding model (Qwen3.8-27B, four Unsloth GGUF
> quantizations) on two consumer 16 GB GPUs and show that both instruments mislead, in opposite
> directions.
>
> Measuring KL divergence against the least-quantized arm over 65,536 tokens per domain, damage on
> code is roughly twice that on prose by the mean — but the mean conceals the shape. Ninety per cent
> of code tokens are *less* perturbed than prose tokens (median divergence 1.7×10⁻⁵ against
> 3.5×10⁻³); the top one per cent are up to eight times *more*. Damage is tail-concentrated at
> high-entropy decision points, and it rises again as the corpus approaches the target task
> (3.1–4.4× prose on the benchmark's own prompts). Against a published quality threshold, two of
> three arms pass on prose, one on generic code, and none on the task distribution.
>
> Three task benchmarks spanning three scoring modes — multiple choice, unit-tested generation and
> long-context retrieval — bound the end-to-end effect of the entire ladder at ≤ 4 points and cannot
> resolve below it; that is what tail concentration predicts. We also report that the usable context
> ceiling is set by GPU tensor placement rather than by quantization, and that speculative decoding
> on this engine is deterministically non-equivalent to unspeculated decoding. Artifacts and the
> full measurement record are released.

Notes on the draft: it leads with the mechanism, gives two hard numbers early, states the
threshold-flip in one clause, converts the nulls into a bound, and ends on the two systems findings
plus the artifact release. It contains no LaTeX macros and no unicode that arXiv's abstract field
will mangle — replace `×10⁻⁵` with `1.7e-5` if the metadata field objects.

---

## 9. What to cut

Cutting is the highest-value editing on this manuscript. There is roughly 40 % more material than
the paper can carry, and the excess dilutes rather than supports.

### Cut entirely
- **PN-12 (thermal asymmetry).** Self-described as "observational and confounded"; case airflow is
  an equally plausible cause and was not controlled. It cannot support a claim. One clause in
  limitations at most: *"we observed a 14 °C asymmetry across the two cards under asymmetric splits
  but did not control for case airflow."*
- **PN-27 (the preflight self-match incident).** Genuinely entertaining and genuinely well handled,
  but it affected no measurement and is an operations story. It belongs in the released ledger, not
  in the paper. Including it invites the reader to see the paper as a project diary.
- **PN-10 (orchestration defects).** Same reasoning. The one generalisable rule inside it — *a sweep
  in which every cell failed must not exit 0* — can be a single sentence inside Appendix B's PN-17
  discussion.
- **The entire energy section (§5.7 in the current outline).** DEC-12 cancelled the energy curve, so
  there is no per-config figure; PN-11's window mixes idle and load; PN-12 is confounded. A section
  built from these would be the weakest three paragraphs in the paper. Replace with two sentences in
  Setup (host power envelope) and one line in limitations (no per-config energy figure exists).
- **All pre-2026-08-29 historical results**, except where explicitly framed as *"the observation that
  motivated this study"* with the irreproducibility label attached. The E11c +33 %/+93 % rebalance
  headline is the one worth keeping in that framing, in the Introduction, precisely because it is
  what prompted Wave 1.

### Demote to appendix
- **PN-18 (`-ctxcp` 4 → 32).** n=1 A/B; the note itself says the 6.8 % gain is the same order as
  rep-to-rep noise and "quoting the number would need 3 reps". It belongs in the configuration
  appendix as an adopted default with the caveat, and **the number must not appear in the body.**
- **PN-4 (`-fit` behaviour change between images).** A hazard note. Appendix B or a footnote in
  Setup.
- **PN-20 (unnamed estimator reversed a ranking).** Keep, but in Appendix B, not the body. It is the
  most instructive of the provenance notes because it changed a conclusion, so it earns its place —
  just not in the results.
- **PN-9 (per-quant acceptance).** It is a confounded single observation per quant *by the note's own
  statement*, and S9d was reinstated specifically to resolve it and failed on power. It cannot be a
  result. Move to limitations, stated as an open question with the confound named.
- **PN-24.** The at-depth half is withdrawn (PN-30); the 32 K half survives as one row of Figure 5's
  panel (a). Do not list PN-24 as a finding anywhere.
- **PN-31 (KLD memory ceiling).** Owner has already directed footnote treatment; agreed. Two
  sentences beside the host spec, keeping only the generalisable clause.
- **PN-32's decode/ranking half.** Keep the acceptance trend and the clustering lesson; drop every
  throughput number from that sweep, since the note says the ranking is unanswerable at n=3.
- **PN-11 (host power envelope).** Two sentences in Setup.

### Keep, but rewrite
- **PN-22, PN-28, PN-33, PN-34** — rewrite as *bounds*, per §3 of this review. PN-34's headline claim
  ("difficulty revealed what depth could not") must be softened to a hypothesis with its interval
  attached; it currently reads as established and it is one discordant sample.
- **PN-16** — promote from a "reproducibility & provenance" note to a *results* paragraph, because
  the quantile decomposition converts it from a caution into a mechanism.
- **The reproducibility register** — from seven entries to four (PN-17, PN-5, PN-30, PN-25, plus
  PN-20 if space allows). One thesis, four instances, each structurally different. Seven instances
  of "we found a bug" reads as a confessional; four instances organised under *silent success is the
  dominant failure mode of automated benchmarking* reads as method.

---

## 10. Risks, and what to do about each

| # | risk — why a reader dismisses the paper | severity | mitigation |
|---|---|---|---|
| 1 | **"One model, one engine, one host — this is an anecdote."** | **High** | Do not hide it; make it the frame. Say in the Introduction that this is a *single-configuration measurement study* and that its contribution is the **method and the distribution shape**, both of which are testable on any host in an afternoon. Give the protocol its own named section so someone can rerun it on Llama or Qwen-2.5 in a day. A method that reproduces cheaply survives n=1. |
| 2 | **"Your reference is quantized; you measured nothing absolute."** | **High** | State it, then defuse it with the direction argument: because the reference is itself ~6-bit, every arm's true distance from FP16 is *larger* than reported. Every claim is conservative. Also reframe the quantity: this is *quantization-step* damage along a ladder practitioners actually choose from — arguably the more decision-relevant measure than distance to a checkpoint nobody can run on this hardware. |
| 3 | **"Your nulls are underpowering, not insensitivity."** | **High** | §3 of this review. Report equivalence bounds, not p-values. The bound [−4.08, +2.76] is a *result*; "p = 1.0" is not. Free to fix. |
| 4 | **"The centrepiece rests on one sample."** (PN-34) | **High** | Demote from a contribution bullet to a hypothesis paragraph with its Wilson interval and R9's published band beside it. Or spend the 11 h to run n≈100 — but the paper does not need it if the tail-concentration reframe carries §5.1. |
| 5 | **"Divergence on prompt tokens is not code quality."** | Medium | Already acknowledged. Strengthen by making the prediction explicit: tail concentration predicts a small discordance rate on a single-turn benchmark, and 3/164 and 5/164 is what was observed. A confirmed prediction is much better than an acknowledged gap. |
| 6 | **"Why should I believe an agent-run campaign?"** | Medium | Disclose it up front (§7 of this review) and lean on the artifact register: per-finding notes with evidence paths, a ledger, a decision log, and four documented instrument failures caught *by the process*. Very few papers can show their own error-detection record. Turn the exposure into the credential. |
| 7 | **Internal number inconsistencies found by a checking reader.** | Medium | Two are live right now, both listed in §11 below. Sweep every number against its artifact before submission — a reader who finds one stops checking and starts discounting. |
| 8 | **"No agentic / long-horizon evidence, which is where it would matter."** | Medium | Do not concede it defensively — *claim* it as the paper's named open problem and closing sentence. It is the natural follow-up and framing it as such positions the paper to be cited by whoever runs it. |
| 9 | **Category/venue mismatch: too systems for `cs.CL`, too model-y for `cs.PF`.** | Low | `cs.LG` primary with both cross-lists resolves it. |
| 10 | **Length and self-indulgence.** The source material is 79 KB of machine log plus 2,000 lines of build stream; the temptation to include everything is real. | Medium | The cut list in §9. If a paragraph exists because it was expensive to produce rather than because it supports a claim, it goes to the artifact release. |

### And what would make a reader cite it

Named plainly, because it is the other half of the assessment:

1. **The quantile table.** If §5.1 is written and Figure 1 is drawn, that table is the thing people
   screenshot. It is a fact about quantized code models that I have not seen stated anywhere, it is
   well powered, and it reframes a metric the whole local-inference community uses.
2. **The equivalence bound.** "The full width of a Q4→Q6 GGUF ladder is worth ≤ 4 points of
   HumanEval+ pass@1" is a sentence practitioners will quote in arguments, and researchers will cite
   when justifying a sample size.
3. **`-ts` and the context ceiling.** This gets cited by tooling authors and by anyone publishing a
   ceiling table, because it makes their published numbers incomplete. Large effect, binary
   evidence, immediately actionable.
4. **Deterministic non-equivalence of speculative decoding.** A refuted premise with a clean
   determinism control is a citable correction. Papers asserting exact-equivalence of a speculative
   implementation will have to cite it or address it.
5. **The reproducibility register as method.** Four structurally distinct silent-success failures,
   each with a rule. Anyone writing about benchmark automation or agentic evaluation harnesses can
   use it directly, and there is very little published on this.
6. **The affordability argument.** A protocol that ranks four quantizations in ~2.3 GPU-hours on
   consumer hardware is a genuinely useful contribution to a community that mostly cannot afford
   ~200,000 evaluations. Make sure §6 states the cost as a *contribution*, with the corrected
   numbers.

---

## 11. Two provenance problems found while reviewing

Not framing issues, but they will become framing issues if they reach a reader.

**11.1 — The MK-NIAH evidence is not in the repository.**
PN-33 and PN-34 rest on the multi-key NIAH result (100.0 vs 91.67 at 131,072), and PN-34 is named in
the outline as "the paper's methodological through-line". The committed artifact
`data/raw/e12/ruler/s12-ruler.json` contains **only** the single-key NIAH cells and the excluded
`variable_tracking` cells; the string `91.67` does not appear anywhere under `data/raw/e12/ruler/`.
The data does exist on the host — `/srv/bench/e12/ruler/s12-ruler.json` carries both `mkniah` cells
and the `accuracy_recovery` entry, and the two `s12-preds-*-mkniah-c131072.json` prediction files are
there — but the repository mirror is one sync behind (host file modified after the last artifact
pull). **Pull it before anything cites PN-34.** The repo's own rule is that a headline number traces
paper note → artifact → serverlog; right now this one breaks at the artifact.

**11.2 — The "≈20 hours of task benchmarking" figure is not supported by the artifacts.**
It appears in `README.md`, in `OUTLINE.md`'s thesis paragraph, and in PN-34. Summing
`started_utc`/`finished_utc` across every task and speculation battery in E12 gives ≈ 11.4 h
(HellaSwag 0.5 + S8 1.6 + S9b 1.4 + S9c 0.7 + S9d 3.8 + S12 3.2), against ≈ 2.3 h of divergence
(SSA S1–S4 1.95 + S5 0.4). That is still a 5× contrast and it is entirely sufficient for the
argument. Either restate it at the supported figure or state explicitly that the 20 h includes the
pre-E12 historical corpus — but the current form is a number a checking reader can falsify in five
minutes, and §7 risk 7 says what that costs.

---

## 12. Web sources

*(Research on arXiv submission mechanics, LaTeX templates, empirical/negative-result writing
guidance, artifact-release norms, and the related-work landscape was gathered in parallel with this
review; the consolidated source list with URLs follows.)*
