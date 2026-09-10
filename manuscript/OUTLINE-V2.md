# Technical report — outline v2

**Replaces [`OUTLINE.md`](OUTLINE.md) in full.** Same title, same abstract, same arXiv decisions,
same evidence base; a different body. Written 2026-09-04 in response to the owner's structural
criticism of v1, which is recorded here verbatim in substance so that the design can be checked
against it:

> The draft and its abstract are far too focused on the final experiments — the four-arm
> UD-Q4_K_XL / Q5_K_XL / Q6_K / Q6_K_XL divergence ladder from the last wave — and throw away an
> enormous amount of earlier work. It does not need to be written across what happened day after
> day; it needs reasoning about how this material fits together.

He is right, and the diagnosis is precise. v1 has **one** results section, `§5`, in which the
divergence ladder holds §5.1 and §5.2, and the twelve-day corpus — a four-day SWE-bench Verified
campaign across three quantizations, two HumanEval+ ladders spanning seven configurations, an
MTP-versus-DFlash2 comparison with a byte-identity result, draft-depth sweeps, three perplexity
protocols, three inference backends, agentic step counts, energy and thermals — is distributed
across half-sentences in §5.2, a 400-word §5.5, a 300-word §5.7 and an appendix. That is not a
weighting error; it is a structural one. Sixteen of the sixty-six paper notes were written on
2026-09-03 specifically to bring the historical corpus into the evidence base (PN-46…PN-59), and
v1's section plan predates most of them.

**What is unchanged and not reopened here:** the title, the adopted abstract (reviewer D's A2, live
in `CITATION.cff`), the arXiv compliance table in [`DRAFTING-PLAN.md`](DRAFTING-PLAN.md) §2, every
voice and density rule in [`STYLE-GUIDE.md`](STYLE-GUIDE.md), and the four blind reviews. Where this
outline departs from a review's recommendation it says so and gives the reason (§7 of this file).

**Reading order for a drafter.** §1 argument · §2 organising principle and its cost · §3 weighting ·
§4 the section plan · §5 PN coverage, all sixty-six · §6 figure-programme deltas · §7 what this
supersedes and the open verification items.

---

## 1. The argument, in one paragraph

Choosing a quantization for a 27B coding model on two consumer 16 GB GPUs is a measurement problem
before it is an engineering one, and over twelve days this study ran nine instrument classes at it —
KL divergence, three perplexity protocols, a multiple-choice battery, two generative coding ladders,
a long-context retrieval battery, a fifty-instance agentic suite, throughput and acceptance probes,
and an energy log — on eight quantized checkpoints across three inference backends. **The instrument,
not the quantization, decided whether there was anything to see.** A token-level divergence
measurement separated the three quantized arms of a four-arm ladder from one another on code at
**8.7–18.1 σ** — the adjacent pairs at **8.67 σ** (UD-Q6_K vs UD-Q5_K_XL) and **11.82 σ**
(UD-Q5_K_XL vs UD-Q4_K_XL), the ladder's extremes at **18.13 σ** — with non-overlapping intervals in
**2.32 GPU-hours**, and located the damage precisely: it is concentrated in the tail of the
per-token distribution, where the median code token moves about two orders of magnitude *less* than
the median prose token while the 99th-percentile code token moves 5.0–8.1× *more* — with the
study's own KV-dtype control showing that the tail's **shape** belongs to the corpus and only its
**magnitude** belongs to quantization. Against that, **14.31 GPU-hours** of task benchmarking — T19's
measured total, covering **three instrument classes** (HellaSwag, HumanEval+ and RULER) and not the
perplexity work or the pre-E12 SWE-bench campaign, which sit outside it — bounded the same ladder and
resolved none of it, and five instruments failed to resolve it five different ways for five different
reasons:
corpus perplexity ordered the ladder correctly across a span of 0.033 while carrying ±0.041 of
standard error per point; a multiple-choice battery at n=400 put the most quantized arm nominally
highest and had two arms answering all 400 items identically; a paired generative benchmark at
n=164 disagreed on 3 and 5 problems and ran a test that could not have reached p < 0.05 at any
outcome; a long-context retrieval battery that appeared to separate the arms at p = 0.002 turned out
to be measuring whether the model finished speaking inside a 128-token budget; and a four-day
SWE-bench Verified campaign **inverted** the ladder, ranking the cheapest arm first inside a
±12-point interval. The same twelve days show that the choices *around* the quantization move
deployment outcomes further than the quantization does: the tensor split rather than the quantization
set the reachable context window for two of four arms and moved one configuration from failing to
load to the full native 262,144 tokens; the KV-cache dtype every one of those windows depends on
costs 51 % of a quantization level in divergence while moving perplexity 0.15 %; speculative decoding
is *deterministically* not output-identical to unspeculated decoding, changing about one generated
function in five, which retired a premise this study had used for nine days to skip measurements as
unnecessary; a 1.19 GiB draft-worker allocation stopped three independent stacks at the same point;
and one backend's context ceiling came in 5.1× short of another's on the same weights and hardware.
The report's contribution is therefore not a ranking but a **calibration of instruments against a
known, well-powered ground truth on hardware most readers own** — including sixteen corrections the
study made to its own headline claims at zero GPU cost, which are reported as method because they are
the strongest available evidence for the thesis: *what you can see depends on what you measure with,
and most of the field is measuring with the coarse ones.*

**One sentence, if only one survives.** Divergence ranks this ladder in 2.32 GPU-hours; five task
instruments bound it and none resolves it, three of them alone costing 14.31; and every
deployment decision that mattered on this host — window, split, KV dtype, speculative setting, backend — was made on an axis
the quantization choice does not control.

---

## 2. The organising principle

This is the question the outline exists to answer, so it is argued rather than asserted.

### 2.1 The candidates, and why each fails or wins

**(a) Chronological — twelve days, wave by wave.** *Rejected by the owner, and correctly.* It
guarantees complete coverage and nothing else. It buries the argument under process, forces the
reader to hold sixteen corrections in memory in the order they happened, and makes every section's
claim provisional on a later one. It also reads as a lab notebook, which is the single most likely
arXiv moderation ground (`does not contain original or substantive research`).

**(b) By configuration axis — quantization · context · speculation · backend.** Strong for a
systems report, and it matches the title's subtitle. It has one fatal flaw for *this* corpus: it
gives the study's central finding nowhere to live. "Divergence ranks what benchmarks bound" is not a
statement about a configuration axis; it is a statement about instruments. Under (b), the
HellaSwag / HumanEval+ / RULER / SWE-bench results scatter into "quantization" as a subordinate
clause each — exactly the failure v1 already has, with more sections.

**(c) By claim — one section per headline finding.** Maximum rhetorical force, minimum
navigability. It duplicates evidence (the same divergence table serves four claims), it hides which
instrument produced what, and it makes the coverage guarantee the owner is asking for impossible to
verify: a reader cannot tell whether the SWE-bench campaign is present or absent because there is no
section it *should* be in.

**(d) By instrument class — logprob · multiple-choice · generative · long-context · agentic ·
systems.** This is the thesis's own axis, and it makes the whole corpus body material by
construction: every one of the twelve days ran an instrument, so every day has a home. Its weakness
is symmetric to (b)'s: the context-ceiling, tensor-split, KV-dtype, speculative-decoding and
backend results are not instrument-sensitivity findings at all. Forcing them into "systems, an
instrument class" is a category error that would distort the strongest practitioner results in the
report.

**Chosen: (e) a declared two-part hybrid — (d) for evaluation, (b) for deployment.**

> **§5 — What the instruments can see.** Organised by instrument class, ordered by the *unit of
> observation*: token → candidate set → single generation → long-context generation → multi-step
> trajectory. That ordering is itself the argument. As the unit coarsens, cost per comparison rises
> and resolving power falls, monotonically, and the section closes by pricing it.
>
> **§6 — What the configuration axes do.** Organised by axis: window and split · ratio and
> throughput · KV dtype · speculative equivalence · speculative method and depth · backend ·
> power and thermals. The instruments of §5 are *applied* here rather than assessed, which is what
> makes the two halves one paper rather than two.

### 2.2 Why the ordering inside each half is load-bearing

- **§5 ascends in unit of observation and in cost.** §5.1 divergence (per token, 65,536 per cell,
  2.32 GPU-h, separates everything) → §5.3 perplexity (per token, but averaged, and it certifies
  nothing) → §5.4 multiple choice (per candidate set, n=400, 0.54 GPU-h, separates nothing) → §5.5a/b
  generative (per problem, n=164 paired, 1.29 GPU-h, bounds at ±3 points) → §5.6 long context (per
  generation at depth, n=12–100, 12.34 GPU-h, measures the wrong construct) → §5.7 agentic (per
  trajectory, n≈50, ~four days, *inverts* the ladder). A reader who reads only the subsection
  openers gets the paper's thesis as a monotone sequence. §5.8 then states the price of each.
- **§6 descends in how much a practitioner can act on it.** The window and the split come first
  because they are the difference between a configuration that loads and one that does not, and
  because the effect is load/no-load rather than a mean with an interval. Speculative decoding
  follows because it is the axis a reader is most likely to believe is free. Backends and power
  close it.
- **The bridge sentence between the halves** (drafted at the head of §6): *the instruments of §5 were
  built to compare compressions; applied to the choices around the compression they return effects
  an order of magnitude larger.*

### 2.3 What this structure costs — stated, because every structural choice has a price

1. **The same arms appear in both halves.** A reader who wants "everything about UD-Q4_K_XL" must
   read §5 and §6. *Mitigation:* Appendix D's claim index is arm-searchable, and T1 carries every
   arm's role, ceiling and winning ratio in one place in §3.
2. **The divergence-versus-benchmark contrast — the paper's headline — is split across §5.1 and
   §5.4–5.7,** and is only assembled in §5.8 and F3. *Mitigation:* F3 (the instrument forest) and F6
   (one axis, two instruments) both appear early, and §5's opening map paragraph states the contrast
   before the evidence arrives. This is a real cost; v1 paid the opposite one.
3. **Two-part bodies read as two papers if the bridge is weak.** *Mitigation:* §6.3 (KV dtype)
   deliberately uses §5's divergence instrument on a configuration axis, and §6.5 uses §5's
   generative instrument on a speculative setting. The halves interlock at two points on purpose.
4. **KV-cache quantization is arguably a compression result and sits in §6.** Defensible either way;
   placed in §6 because a practitioner chooses it as a *setting*, and because it is this report's
   cleanest demonstration that the §5 instrument transfers.
5. **Speculative decoding spans two subsections (§6.4 equivalence, §6.5 method and depth)** rather
   than one. This is deliberate: the equivalence result is an accuracy finding and the depth result
   is a throughput finding, and merging them is how v1 ended up with a 750-word section covering
   five paper notes.
6. **The report gets longer** — **13,500 body words against the style guide's 11,350**, a
   **+18.9 %** departure, funded section by section in §3.1 rather than declared (see §3.4). That is
   the price of the owner's instruction not to compress, held to a size the delta actually supports;
   §3.4 names the levers already spent and the ones still in reserve.

---

## 3. Weighting — the concrete answer to "an enormous amount of earlier work was thrown away"

### 3.1 Target shares of the body

**Every figure below is summed from the per-subsection targets in §4, not estimated.** The table
that promises rebalancing has to be auditable, so the audit is printed with it: an earlier draft of
this table under-counted the systems thread by 250 words and the framing thread by 100, omitted the
two section opening blocks entirely, and printed a body total of 15,950 against a true sum of
**16,600** — while §5's own header claimed 5,600 against subsections summing to 5,850 and §6's
claimed 4,200 against 4,600. All five figures are recomputed below and every header now matches its
subsections. Shares are rounded to whole per cent and sum to 100.

| thread | sections | words | share of body |
|---|---|---|---|
| **Task benchmarks** (multiple-choice, two generative ladders, long context, agentic) | §5.4, §5.5a, §5.5b, §5.6, §5.7 | **2,700** | **20 %** |
| **Divergence and quantization fidelity** | §5.1, §5.2, §5.3, §6.3 | 2,250 | 17 % |
| **Framing** (intro, background, setup, conclusion) | §1, §2, §3, §8 | 2,850 | 21 % |
| **Protocol, instrument economics, threats** | §4, §5.8, §7 | 2,550 | 19 % |
| **Context, split, ratio, backends, throughput, power** | §6.1, §6.2, §6.6, §6.7 | 1,900 | 14 % |
| **Speculative decoding** | §6.4, §6.5 | 1,050 | 8 % |
| **Section opening map and bridge** | head of §5, head of §6 | 200 | 1 % |
| **body** | | **13,500** | **100 %** |

**The audit, section by section, so the sum can be checked without re-reading §4.** Each row is the
sum of its own subsection targets, each subsection appears exactly once, and every §4 header carries
the same number as its row here.

| section | subsection targets | total |
|---|---|---|
| §1 Introduction | 150 + 125 + 100 + 325 + 75 + 75 | **850** |
| §2 Background | 270 + 270 + 270 + 90 opening | **900** |
| §3 Setup | 300 + 250 + 150 + 50 | **750** |
| §4 Method | 175 + 250 + 225 + 125 + 75 | **850** |
| §5 Instruments | 100 map + 750 + 800 + 350 + 350 + 400 + 600 + 450 + 900 + 300 | **5,000** |
| §6 Axes | 100 bridge + 700 + 150 + 350 + 600 + 450 + 750 + 300 | **3,400** |
| §7 Threats | — | **1,400** |
| §8 Conclusion | — | **350** |
| **body** | | **13,500** |

Appendices, likewise summed rather than estimated: A 700 + B 1,000 + C 700 + D 500 = **2,900**. The
"≈ 3,800" that appeared here before matched no appendix target in §4.

### 3.2 Why this split, and not another

- **Task benchmarks take the largest single results share (20 %) — larger than divergence's 17 %.**
  This is the correction the owner asked for, and it is defensible on three independent grounds.
  *Cost:* three of their instrument classes consumed **14.31 GPU-hours** in the E12 wave alone (T19,
  and the 14.31 covers HellaSwag, HumanEval+ and RULER only), plus roughly four days of pre-E12
  SWE-bench evaluation that sits outside that total, against divergence's **2.32** — a **6.2×** ratio
  on the three classes T19 measures. *Breadth:* five instruments, five distinct
  reasons for failing to resolve — a section that treats them as one null wastes four of the five.
  *Argument:* the title claims benchmarks *bound*; a paper that spends 8 % of its body on the
  bounding evidence has not earned the claim. F16, promoted to ESSENTIAL on 2026-09-04, is the
  sharpest instance of the thesis anywhere in the corpus and it currently has no section of its own.
- **Divergence keeps its novelty premium in figures rather than in word count.** F1 and F2 stay
  ESSENTIAL, T3 stays the master table, and the tail result (PN-35 as scoped by PN-62 and corrected
  by PN-64) is the only place in the report where a novel mechanism is claimed. But the mechanism is
  compact: it is one quantile table and one control. Seventeen per cent buys it a full argument
  without letting it colonise the paper, which is precisely what happened in v1.
- **Speculative decoding at 8 %** is up from v1's effective ~6 % and reflects what it actually
  covers: an equivalence result that retired a nine-day-old premise (PN-23, PN-26, PN-59), a
  method comparison on the correct engine build (PN-29), a matched-depth draft-depth sweep across
  four arms (PN-32, scoped by PN-66), a withdrawn at-depth claim (PN-24 → PN-30) and a
  degenerate-acceptance correction (PN-61). Six notes, two subsections.
- **Systems at 14 %** is roughly v1's share, redistributed: v1 gave the split result 700 words and
  the backends nothing. PN-53/54/55/56 — the 1.19 GiB wall, SGLang producing zero measurements, the
  cross-backend probe and the 5.1×-short vLLM ceiling — are four notes that appear in v1's body not
  at all.
- **Protocol and threats at 19 %** is high for a measurement paper and is the report's second
  contribution. Sixteen corrections, twelve register entries covering twenty-one defects in three
  named families, a
  multiplicity analysis across ~19 tests, and an explicit statement of what each instrument could
  never have shown. This is the material reviewers A, C and D each independently called the most
  reusable part of the corpus.

### 3.3 What is *not* rebalanced

Background stays under 900 words (hard cap, moderation risk). The conclusion stays at 350. Neither
grows to accommodate breadth; breadth goes in §5 and §6 or it goes in an appendix.

### 3.4 Length, honestly, and the compression levers

**Target: 13,500 body words** (≈ 26 single-column pages), appendices 2,900 (≈ 7 pages), total
≈ 34 pages. This departs from `STYLE-GUIDE.md` §2.8's 11,350 / 30-page budget by **+18.9 %**, and the
departure is *earned rather than declared*: nineteen paper notes that carried no body weight in v1
carry `LEAD` or `BODY` weight here, which is the delta the extra 2,150 words buy. An earlier draft of
this outline asked for 15,950 — a +40 % departure from a budget written against the same corpus, and
more than nineteen notes support.

**The levers already spent, from the audited 16,600 to 13,500 — a net 3,100 words.** The starting
point is the *true* sum of v2's own §4 targets, not the 15,950 the old table printed; cutting from a
figure that was already wrong is how a budget stays wrong. Each lever is named so the owner can
reverse a specific one rather than the whole reduction.

| # | lever | from → to | saved |
|---|---|---|---|
| 1 | §6.7 throughput, power and thermals compressed onto T12 and T22 | 700 → 300 | 400 |
| 2 | §6.5 draft depth: the four ⚠️ scopes stay, the narration goes | 800 → 450 | 350 |
| 3 | §5.6 long context: the withdrawal arc held to three sentences | 750 → 450 | 300 |
| 4 | §5.3 perplexity reduced to the span and the protocol swing | 600 → 350 | 250 |
| 5 | §6.2 reduced to the PN-42 correction, the outlier and `-ctxcp` | 400 → 150 | 250 |
| 6 | §4 method tightened across all five subsections | 1,300 → 850 | 450 |
| 7 | §1 tightened; seven contributions kept, each shorter | 1,200 → 850 | 350 |
| 8 | §3 setup tightened | 1,000 → 750 | 250 |
| 9 | §6.3 KV dtype tightened; the external comparisons stay | 500 → 350 | 150 |
| 10 | §5.1 divergence — REVIEW-V2 §1.3's funding for the §5.5 split | 900 → 750 | 150 |
| 11 | §6.4 equivalence — REVIEW-V2 §1.3's funding for §6.6 | 700 → 600 | 100 |
| 12 | §5.4 multiple choice | 450 → 350 | 100 |
| 13 | §5.8 instrument economics, leaning harder on T19 and F19 | 400 → 300 | 100 |
| 14 | §6.1 window and split | 750 → 700 | 50 |
| 15 | the two section opening blocks | 150 + 150 → 100 + 100 | 100 |
| 16 | **§5.5 split into 5.5a + 5.5b** (REVIEW-V2 §1.3, item 5) | 900 → 400 + 600 | **−100** |
| 17 | **§6.6 backends raised** (REVIEW-V2 §1.3, item 5) | 600 → 750 | **−150** |
| | **net** | **16,600 → 13,500** | **3,100** |

Unchanged at their v2 targets: §2 (900, hard cap), §5.2 (800), §5.7 (900), §7 (1,400), §8 (350) —
the four protected sections plus the capped one.

Appendix B additionally moves from prose to a table with two-sentence rows (1,300 → 1,000) without
dropping an entry, which is a page saving that costs no claim.

**Levers still in reserve, if a page budget bites again** — cut in this order and stop as soon as it
fits: (1) §6.2 folded into §6.1 entirely; (2) §5.8 to 200 words, leaning entirely on T19 and F19;
(3) §6.7 to 150 words plus T22; (4) Appendix C's per-repetition rows moved to the artifact.
**Never cut** §5.7, §6.4, §5.2 or §7 — the first two are the corrections the owner is protecting, the
third is the only novel mechanism, and the fourth is the report's credibility. §5.5b is added to that
protected list: it is the historical corpus, and it is the half that compresses first by default.

---

## 4. The section plan

Conventions for every entry below: **Claim** — the sentence the section must earn. **Evidence** —
paper notes, in the order they should be cited. **Figures/tables**. **Words** — target, excluding
captions. **Failure mode** — the specific way this section goes wrong. A subsection with no PN
reference is marked **NO PN SUPPORT** and may not be written as though it were measured.

---

### §1 Introduction — 850 words

**Claim.** A practitioner with two 16 GB consumer GPUs must choose one quantization of a 27B coding
model; the instruments available to make that choice disagree, several give no answer at all, and
which one is used determines the answer more than the model does.

**Structure.**
- **Opening (150 w).** The practitioner question, concretely: four candidate checkpoints, one host,
  one decision. Not a critique of the field; a decision under measurement uncertainty. Follow
  `STYLE-GUIDE.md` §7's worked opening.
- **The scope statement (125 w) — new in v2, and the direct answer to the owner's criticism.** State
  the size of the study in its second paragraph, not in an appendix: twelve days, eight quantized
  checkpoints in two formats, three inference backends, nine instrument classes, ~19 hypothesis
  tests, sixteen self-corrections. Then the narrowing: a four-arm ladder carries the controlled
  divergence comparison, and the report says explicitly why those four and what the other four
  checkpoints are used for. A reader must not reach §5.7 and discover a four-day campaign they were
  not told about. **Evidence:** T1, F21-scope (new, §6 of this file), `env-manifest.json`, PN-57.
- **Prior work in one paragraph (100 w).** Dutta et al. (NeurIPS 2024, R13) established that
  accuracy hides compression damage; cite it *before* the contributions, not after. What this report
  adds: the shape of the damage, its domain dependence, a quantified task-level bound, and the same
  question asked of the configuration axes.
- **Contributions — seven, in this order (325 w).**
  1. **Tail structure.** Code damage is tail-concentrated; the median/p99 ordering inverts; the
     familiar "2× worse on code" is the mean of two opposite facts — **and the shape is a corpus
     property, demonstrated by the study's own KV-only control.** *(PN-35, PN-62, PN-64, PN-14,
     PN-16)*
  2. **Domain dependence.** Divergence rises monotonically as the corpus approaches the task,
     3.13–4.40× prose→task, with the amplification itself growing with aggressiveness. *(PN-21,
     PN-13)*
  3. **Five instruments, five bounds, five distinct reasons.** Not one null. *(PN-22, PN-28, PN-40,
     PN-46, PN-47, PN-48, PN-50, PN-60, PN-63)*
  4. **The most expensive instrument inverts the ladder.** SWE-bench Verified at n≈50, four days of
     GPU, ranks the cheapest arm first inside ±12 points. *(PN-50, PN-51, PN-52)*
  5. **The window belongs to the split.** For two of four arms the tensor split, not the
     quantization, set the reachable context. *(PN-6 scoped by PN-39, PN-7)*
  6. **Speculative decoding is deterministically non-equivalent** — and the premise that it was
     lossless had been used to *skip* measurements for nine days. *(PN-23, PN-26, PN-59)*
  7. **Protocol dependence is first-order.** The same weights on the same corpus read as 29 % worse
     or 0.8 % worse depending on conventions no published perplexity number discloses. *(PN-49)*
- **Status statement (75 w).** Independent practitioner, professional master's candidate at USP,
  **not** a peer-reviewed paper, no institutional team. `STYLE-GUIDE.md` §1.4 has the exact wording;
  do not soften it and do not repeat it more than the two required places.
- **Scope and limits paragraph (75 w).** Ladder-relative reference, one model family, one engine
  image, one host, two single-domain corpora — on page 2, not on page 26.

**Failure mode.** Promising the divergence result and delivering it in §5.1, then letting §5.4–5.7
read as leftovers. The contributions list above is ordered so that 3 and 4 are load-bearing promises.

---

### §2 Background and related work — **≤ 900 words, hard cap**

**Claim.** Three literatures meet here — the instrument literature, the evaluation literature and
the consumer-hardware inference literature — and each leaves open exactly the question this report
measures.

**Budget — 810 + 90, not 3 x 300.** Three threads at 270 words each leaves **90 words** for the
section's own claim sentence and the two transitions between threads, which 3 x 300 did not. The cap
is 900 and it is hard; a section budgeted to its cap with nothing left for its opening overruns on
the first draft.

**Structure — three threads, every paragraph ending on what this report measures differently.**
- **Instruments (270 w).** Perplexity's averaging bias and the case for KL divergence (R1, R2, R4,
  R10); Dutta et al. (R13) as the direct predecessor and the honest statement that contribution 3 is
  *independent confirmation on a different model family, compression scheme and hardware class*;
  who ranks quantizations in practice and on what (R3, R5); the near-baseline ranking-power objection
  (arXiv:2606.19558) answered here rather than in threats.
- **Evaluation (270 w).** Task batteries applied to llama.cpp quantization, read as the nearest
  neighbour and the caution (arXiv:2601.14277, R7); paired differences, power and equivalence bounds
  (R6); benchmark saturation and stagnation; RULER and the long-context protocol (R8); the two
  published quantization-at-depth studies that reach *opposite* conclusions (R9).
- **Consumer-hardware inference (270 w).** Speculative decoding and the specific published
  losslessness claim this report answers (R12) — cited as motivation and foil, never as something
  refuted; KV-cache quantization literature (currently absent from the bibliography per reviewer D
  §5.2 — **must be added**); the same-GPU benchmark report (arXiv:2601.09527).

**Evidence.** **NO PN SUPPORT** — this section is external sources only, by construction. Every
sentence traces to `METHOD-REFERENCES.md` R1–R15 or `references.bib`.

**Failure mode.** Growing past 900 words. An assertive title over a long multi-thread background is
the shape an arXiv moderator declines.

---

### §3 Setup, provenance and harness validation — 750 words + T1, T2

**§3.1 Host, engines, arms (300 w · T1).** 2× RTX 5060 Ti 16 GB, sm120, no NVLink, 180 W, Ryzen 5
8500G, 14 GiB RAM. Engine pinned by image digest. The eight checkpoints and which four carry the
controlled comparison. Two GPUs of 16 GB are not a 32 GB pool — state the physical constraint here
because §6.1 depends on it. **PN-31 as a two-sentence footnote**, keeping only the generalisable
clause: the standard divergence tooling's resident footprint scales with context length, which is
why the published quantization tables it produces are all measured near 2K. *Evidence:* T1, PN-31.

**§3.2 Harness validation, as a result (250 w · T2).** Measured server sampling defaults match
neither the documented engine defaults nor either official preset — an undocumented fourth
configuration (PN-1); thinking is on by default and the widely-cited disable idiom raises a Jinja
exception (PN-2, PN-3); `-fit` did not shrink the context here but still cannot be trusted to bound
allocation (PN-4). This earns its place because it tells the reader every downstream number was
produced under an asserted contract. *Evidence:* PN-1, PN-2, PN-3, PN-4.

**§3.3 Provenance discipline, and one irreversible loss (150 w).** `env-manifest.json`, sha256 and
byte counts for every checkpoint including two that no longer exist; the deleted engine image that
retroactively made every tensor-split and every 262,144-token result before 2026-08-29
irreproducible, and the labelling rule that follows (*irreproducible-on-current-images*). This is
where the historical corpus is admitted to the report with its scope stated, once, so that §5 and §6
can use it without re-litigating. *Evidence:* PN-57, PN-65.

**§3.4 AI-conduct and artifact availability (50 w).** Per `STYLE-GUIDE.md` §1.5 and §3.10.
**NO PN SUPPORT** — policy statement.

**Failure mode.** Letting §3.3 become a lament. It is a labelling rule with one sentence of cause.

---

### §4 Method — instruments, the SSA protocol, and what is refused — 850 words + T2, F21

**§4.1 The design principle (175 w).** Divergence instruments draw statistical power from **token
count**; task benchmarks draw it from **problem count**. Everything in §5's ordering follows from
that one asymmetry. *Evidence:* PN-13 (65,536-token budget), F21.

**§4.2 The Small-Sample Accuracy protocol (250 w).** Reference-arm choice and its ladder-relative
consequence; the 65,536-token budget (18,432 for task prompts, and why the intervals are ~1.9×
wider there); pre-registered interpretation bands declared as external reference points, never
adopted rules. *Evidence:* PN-13, PN-21, PN-16.

**§4.3 Instruments considered and rejected — 225 w. New in v2, and it belongs in Method.** Three
instruments were built, run, and did not answer the question, and each rejection is a
transferable result rather than a failure: free-running greedy generation **does not resolve**
quantization distance — trajectories fork within 2–126 characters and every pairwise distance
saturates, so the metric returns the same value for every arm (PN-38); KL divergence at long context
**did not run** on a 14 GiB host, the tool holding a chunk's logits resident and capping at
`n_ctx` 8,192 (PN-31); and RULER's `variable_tracking` was excluded on an
output-format artifact — an exclusion that must be *visible*, because it is the harder task and a
reader will ask (see §7). *Evidence:* PN-38, PN-31, PN-63 (closure classifier), METRIC-CORPUS §6.2.

**§4.4 What is reported, and what is refused (125 w).** Four rules, stated once and obeyed
everywhere: every table names protocol, n, estimator and interval *inside the table*; a comparison
is reported as an equivalence bound, never as a bare p-value; where a test could not have reached
significance at any outcome, the minimum attainable p is given instead (PN-40); an aggregate is
meaningful only if every cell entering it is identical in every dimension except the one aggregated
over — with the cell key as the check (PN-20, PN-45). *Evidence:* PN-40, PN-20, PN-45, PN-66.

**§4.5 The instrument inventory (75 w · T2, F21-scope).** One table: instrument, unit of power, n
and its unit, arms covered, wall-clock, arms separated. This is the map the reader navigates §5 by.
*Evidence:* T19, PN-41 as superseded by T19's recomputation, PN-65.

**Failure mode.** Writing §4.3 as an apology. Each rejected instrument tells the next group what not
to spend GPU-hours on, which is worth more than a fourth confirmatory measurement.

---

### §5 What the instruments can see — 5,000 words (an opening map and nine subsections)

**Opening map (100 w).** Three sentences naming the six instrument classes and the ordering
principle: the unit of observation coarsens from a token to a multi-step trajectory, cost per
comparison rises by three orders of magnitude, and resolving power falls monotonically. Not a
summary of results — a map. Then §5.1 begins.

---

**§5.1 The divergence ladder and the domain hierarchy — 750 w · F1, F1b, F8 · T3**

**Claim.** KL divergence over 65,536 tokens per domain separates the three quantized arms of the
ladder from one another on code at 8.7–18.1 σ with non-overlapping intervals, and the separation
grows monotonically as the evaluation corpus approaches the real task.

Three-tier hierarchy (prose < generic code < task prompts), monotone in every domain.
**One σ range is quoted in this report and it is the code-domain one**: adjacent pairs at **8.67 σ**
(UD-Q6_K vs UD-Q5_K_XL) and **11.82 σ** (UD-Q5_K_XL vs UD-Q4_K_XL), extremes at **18.13 σ** —
so "8.7–18.1" names all three code separations and only the middle of it is adjacent. The prose
figures (3.71 / 8.48 / 13.48) belong in T23 and in §7 item 2, reported there as *the prose adjacency
at 3.71 σ is not separated once clustering at design effect 1.5 is allowed for*; they are never used
as the report's headline range and are never blended with the code range into a single "3.7–11.8".
The threshold-crossing statement — two of three arms pass the external <0.007 band on
prose, one on generic code, none on the task distribution — with the external-band caveat in the same
sentence. **PN-16 delivered as mechanism, not caution:** top-1 agreement is *higher* on code
(98.4–99.4 %) while mean KLD is double, so a top-1-only table inverts the conclusion; the
reconciliation is that the code corpus is far more predictable (PPL 1.18 vs 5.79) and the argmax
survives a distribution shift that the tail does not. ⚠️ The *widening* of the prose→task
amplification is an upper bound, not a reference-invariant result (reviewer D §4.2); the *level* is
invariant. **Evidence:** PN-13, PN-21, PN-14, PN-16.

**Failure mode.** Reporting the ladder as a ranking of products. It is a ladder-relative distance
with no FP16 anchor, and that belongs in this section's second paragraph, not only in §7.

---

**§5.2 Where the damage lives — the tail, and the control that scopes it — 800 w · F2, F7 · T4, T5**

**Claim.** Quantization damage to code is concentrated in the tail of the per-token distribution;
the tail's *shape* is a property of the corpus and its *magnitude* is a property of quantization.

The quantile decomposition: median code/prose ratio ~0.005×, p90 0.449/0.541/0.613 (below unity on
all three arms), p95 1.527/1.888/2.184 (above unity on all three), p99 4.99/6.71/8.09. The crossover
sits between p90 and p95, the mean lands between p95 and p99, and PN-14's "code is 2× worse" is that
mean. ⚠️ **PN-64 governs the median row**: two of three cells were overstated ~2×, the measured
ratios are 199 / 181 / 206, print precision leaves the per-arm intervals overlapping, and the row
therefore **cannot rank the arms** — say "about 200×", never tabulate it per arm. ⚠️ **PN-62 is the
section's best moment and must not be buried**: normalising each cell by its own mean gives p99/mean
of 26.1 / 24.3 / 24.5 on code for the quantized arms and **22.9 for the KV-dtype-only cell**, in
which no weight is quantized at all; on prose the ratio is flat at 8.4–8.6 throughout. The study had
its own control and did not use it until adversarial review; report that.

**Then the prediction, which is what makes this a mechanism rather than a description:** if damage
occupies ~1–5 % of positions and those positions are where the model chooses, a 164-problem paired
coding benchmark should show a *handful* of discordant problems — not zero, not many. Observed: 3 of
164 and 5 of 164 (§5.5a). State it as a confirmed quantitative prediction, forward-referenced.

**Evidence:** PN-35, PN-62, PN-64, PN-16.
**Failure mode.** Presenting the quantile table as the headline without the control — the version an
adversarial reader breaks in ten minutes, and did.

---

**§5.3 Perplexity: the right ranking, no certification, and a 36-fold protocol swing — 350 w · F10,
F26 · T18**

**Claim.** Corpus perplexity reproduced the correct ordering of the ladder while being unable to
certify a single step of it — and the same weights, scored two defensible ways, differ 36-fold in
reported damage.

Protocol 1 over the full 602-window WikiText-2 test set: 6.6511 / 6.6556 / 6.6617 / 6.6839 ± ~0.041
each. **The ladder spans 0.033 against ±0.041 per point** — every adjacent pair overlaps and even the
extremes are not separated. Then the protocol result, which is the best-provenanced single finding in
the corpus and reviewer C's recommended abstract lead: one NVFP4 checkpoint on the same benchmark
corpus read **+29 % worse** under one protocol and **+0.8 % worse** under another, a 36× swing in the
estimated effect produced entirely by corpus file, window coverage and scoring rule — none of which a
published perplexity number discloses. The intuitive explanation, tokenizer mismatch, was tested and
**disproven**: the two tokenizations agree exactly. Three protocols exist in this study and appear in
three separated blocks of T18, never in one table.

**Evidence:** PN-48, PN-49, PN-15 (the PPL-vs-KLD contrast is forward-referenced to §6.3, not
duplicated here).
**Failure mode.** Letting the protocol swing read as an attack on NVFP4. It is a statement about
measurement conventions; the corrected figure still places the checkpoint below every GGUF arm.

---

**§5.4 Multiple choice: structurally insensitive, not merely underpowered — 350 w · F3 · T6, T7**

**Claim.** A standard multiple-choice reasoning benchmark resolves this ladder no finer than
7.4 points at n=400 while the effect on it is 1.0 point, and the limit is structural rather than one
more items would move.

HellaSwag n=400 on four arms: 82.75 / 82.25 / 82.75 / 83.25 %, a 1.0-point spread inside ~7.4-point
intervals, **the most heavily quantized arm nominally highest**, and UD-Q6_K_XL and UD-Q5_K_XL
answering **all 400 items identically** (b=0, c=0), with no pair disagreeing on more than 4 items.
⚠️ Report paired differences and intervals, **never** the six McNemar p-values: with a maximum
discordant count of 4 the minimum attainable p is 0.125, so none could have reached 0.05 at any
outcome. The mechanism: argmax over a handful of candidate continuations is robust to exactly the
distribution shift §5.2 measures — and the same arms differ by 3.7× in mean KLD. ⚠️ **Not
saturation** — 82.75 % leaves ~17 points of headroom (PN-37); the earlier saturation framing is
withdrawn and the withdrawal is stated here, once.

**Evidence:** PN-22, PN-37, PN-40 (the min-attainable-p rule).
**Failure mode.** "We could not find an effect." Rewrite until it reads "this instrument resolves no
finer than 7.4 points, and the effect is 1.0."

---

**§5.5a Generative coding, the paired anchor — 400 w · F15 (panel a) · T8**

**Claim.** The generative instrument the field trusts most for coding models bounds the ladder's
extremes at −0.61 points, 95 % interval [−2.68, +1.46] at n=164 paired, on a pair of arms that
differ 3.69× in code-prompt KL divergence.

**Split from v2's single 900-word §5.5, and the split is the point.** One subsection carried an E12
paired test *and* seven historical configurations across two ladders and a context control; under a
page squeeze the historical half compresses first, which reproduces exactly the imbalance this
outline exists to correct. Two subsections make that impossible: 5.5a is the controlled anchor at
400 words, 5.5b is the corpus at 600, and neither shrinks without the loss showing in the table of
contents. §5.5b is on §3.4's protected list for the same reason.

**The measurement (SSA S6 / S9b), n=164, official non-thinking preset, no-spec on both arms.**
UD-Q4_K_XL − UD-Q6_K_XL = **−0.61 points** on both metrics; 95 % CI **[−2.68, +1.46]** on
HumanEval (base) and **[−3.28, +2.06]** on HumanEval+ (base+extra); discordant **3 of 164** and
**5 of 164**. ⚠️ Label the rows correctly — in evalplus `base` is HumanEval and `base+extra` is
HumanEval+, and v1 quoted the base row under a HumanEval+ label. ⚠️ **Do not report "McNemar
p = 1.0"**: at 3 and 5 discordant pairs the minimum attainable p is 0.25 and 0.0625, so the test
had no power to say anything. Say so explicitly — it is this report's own instance of the error it
attributes to the field. **The publishable sentence:** a 3.69× increase in code-prompt KL
divergence moves HumanEval+ pass@1 by at most about 3 points. Both arms ran no-spec because PN-23
would otherwise confound the comparison — say that in the sentence, it is the interlock with §6.4.

**Evidence:** PN-28, PN-40.
**Failure mode.** Reporting the bound as an equality. It is an equivalence bound at ±3 points, not a
demonstration that the arms code equally well.

---

**§5.5b The two historical ladders — seven configurations — 600 w · F15 (panels b, c) · T15**

**Claim.** Two HumanEval+ ladders spanning seven configurations order the arms exactly as perplexity
does and separate only their bottom rung, and the thinking-mode ladder's fidelity signal is carried
by failure to terminate rather than by code quality.

1. **The historical non-thinking ladder, four checkpoints, greedy, n=164 each.** UD-Q3_K_XL
   84.1/81.7, UD-IQ4_XS 90.2/87.8, UD-Q5_K_XL 93.3/90.9, UD-Q6_K_XL 93.9/91.5 — **monotonic in
   bit-width and matching the perplexity ordering exactly**, and still unable to separate its upper
   rungs: three rungs span 3.7 points against a ±4.6-point Wilson half-width, so only the Q3→IQ4 step
   (6.1 points) exceeds the interval and the Q5→Q6 step is one problem. A **context-length control**
   in the same series scores identically at ctx 32,768 and 131,072 (93.3/90.2 both): window size does
   not move short-prompt accuracy. Two rows of this table are on the exclusion list and are named as
   excluded, never deleted.
2. **The thinking ladder, seven configurations across MTP and DFlash2 arms.** Every arm scores
   *lower* with reasoning enabled, and the fidelity signal is carried almost entirely by
   **failure to terminate**: empty-response rate falls monotonically with fidelity (12.8 → 12.2 →
   11.0 → 7.9 %) while three of four arms score *identically* at 86.0 on HumanEval+. A thinking-mode
   benchmark is partly measuring a budget process — which is the same mechanism §5.6 finds at depth,
   and the two must be cross-referenced.

**Evidence:** PN-46, PN-47.
**Failure mode.** Presenting (1) as a ranking because it is monotone. Monotonicity is not separation,
and the report's own thesis forbids the slide.

---

**§5.6 Long context: what the battery actually measured, and the withdrawal — 450 w · F9, F9b · T9**

**Claim.** On single-needle retrieval the instrument is genuinely at ceiling and sixteen-fold more
context buys no discrimination; the one long-context result that appeared to separate the arms was
measuring output-budget closure, not retrieval.

S-NIAH: **100.0 / 100.0** at 8,192 / 32,768 / 131,072, both ladder extremes, zero empty responses —
and PN-63's closure audit establishes these are **genuine ceilings, not degenerate string matches**:
those cells close their reasoning block on 100 % of samples in both arms (25/25, 25/25, 12/12).
⚠️ **The MK-NIAH result is withdrawn as a retrieval finding.** The battery ran through `/completion`
with `n_predict=128` and reasoning enabled, so every generation is a `<think>` block competing with
the answer for 128 tokens; **not one item in either arm was closed-and-wrong**, and on the **55 of
100 items where neither arm's budget bound, both arms score 55/55 with zero discordance**. What
separates is **budget closure** — 77 vs 60, discordance 22/5, exact McNemar **p = 0.001514** — i.e.
reasoning verbosity. The Red Hat 85–88 % accuracy-recovery comparison is **void**. PN-63 supplies the
mechanism for the withdrawal itself: at the same depth, same arms, same budget, single-needle closes
12/12 while multi-key closes 77/100, so the truncation is driven by **task difficulty lengthening
the reasoning**, not by depth. Report the full arc — PN-33's n=12 reading, PN-44's n=100
"separation", PN-60's re-analysis — in three sentences, because it is the report's clearest worked
example of a null that was not a null and a positive that was not a positive.

**Evidence:** PN-33, PN-44, PN-60, PN-63, PN-34 and PN-37 for the retracted saturation mechanism.
**Failure mode.** Reporting the withdrawal without reporting what still stands. The S-NIAH ceiling is
a real, audited result and it is the cleanest "sixteen-fold context, zero discrimination" statement
in the corpus.

---

**§5.7 The agentic instrument — four days, fifty instances, and an inverted ladder — 900 w · F16,
F17, F17b · T16**

**Claim.** The most expensive instrument in this study ranked the ladder backwards, and the arm that
led every cheap instrument in the study failed every multi-step task outright.

Two results, and they cut in opposite directions on purpose:

1. **SWE-bench Verified, non-thinking, n ≈ 50 per arm, scored from per-instance `report.json`.**
   UD-IQ4_XS **38/49 = 77.6 %**, UD-Q5_K_XL **38/50 = 76.0 %**, UD-Q6_K **37/49 = 75.5 %** — an
   ordering that **inverts** the HumanEval+ and perplexity ranking of the same three arms. The
   inversion is **not a finding, it is noise**: three arms spanning 2.1 points where one instance is
   worth ~2, against a bootstrap interval of [63.27, 87.76] on one arm alone. Roughly four days of
   agentic evaluation, and the deliverable is a ±12-point band. **Three superseded generations of
   these numbers exist** — a first-match regex publishing batch 1 of 7, and an ARM64 scoring host
   silently under-counting instances whose evaluation images have no `linux/arm64` manifest — and all
   three are shown in T16, because the correction is part of the result.
2. **The disqualified arm.** UD-Q3_K_XL is the throughput leader in the entire study (116.9 tok/s at
   draft depth 8), scores 84.1/81.7 on HumanEval+ with zero empty responses, and hit the 250-step
   agent limit on **6 of 6** instances where the reference converged 6 of 6 with a mean of 45 steps.
   ⚠️ Its 1.000 draft acceptance at 258,779 tokens is **not** admissible as evidence — PN-61 shows
   those figures come from 50-token generations over ~34 draft events. Among the arms that *do*
   converge, step count is **inversely** related to fidelity (23 / 29 / ~45 steps), so step count is
   not a quality proxy in either direction. ⚠️ **The ~45-step column is cross-experiment**: PN-52's
   own caveat records that the UD-Q6_K_XL mean is carried over from a **different instance set** than
   the 23 and 29, so the three figures are not a within-design comparison —
   `FIGURE-PROGRAMME.md` already flags the same scope for F17b, and the clause must appear wherever
   the triple is printed. n=3–6, single scaffold, single seed: this supports a
   qualitative disqualification, not a ranking, and must be written that way.

**Evidence:** PN-50, PN-51, PN-52, PN-58 (provenance of the corrected totals), PN-61 (the acceptance
caveat), PN-65 (why these numbers now exist as a committed artifact rather than as prose).
**Failure mode.** Letting (1) and (2) collapse into "benchmarks are bad". (1) is an instrument with
insufficient resolution; (2) is an instrument detecting something no cheap instrument could. Both
are needed and they are not the same claim.

---

**§5.8 What each instrument cost, and what it bought — 300 w · F19 · T19**

**Claim.** **2.32 GPU-hours** of divergence measurement separated the ladder; **14.31 GPU-hours** of
task benchmarking across three instrument classes bounded it and separated nothing on its intended
construct — a **6.2×** cost ratio, with the four-day SWE-bench campaign outside the comparison
entirely.

The measured table, from each artifact's own per-cell timings: divergence 2.32 GPU-h across 14 cells
(all three arms separated); task benchmarks 14.31 across 20 cells (nothing separated on the intended
construct, of which the 100-sample MK-NIAH cell alone is 9.4 h). ⚠️ **State the scope of the 14.31 in
the sentence that prints it:** T19 sums **HellaSwag, HumanEval+ and RULER only** — three instrument
classes, not five families. The perplexity work and the pre-E12 SWE-bench campaign are **not** in it,
so "five task-benchmark families costing 14.31 hours" is false on both halves. The campaign is the
larger cost and it is uncounted, which makes 6.2× a **lower bound** on the contrast; say that, it is
the honest direction. Also: equivalence batteries 2.67 across 6
cells (a nine-day-old premise retired). ⚠️ **Two withdrawals belong in this section, in the same
paragraph as the numbers:** the "20 minutes versus 20 hours" contrast has no basis in any artifact
and is withdrawn (PN-41), and PN-41's own replacement figures (2.15 h vs ≈4.8 h, 2.2×) predate the
MK-NIAH n=100 cell and are superseded by T19's 2.32 / 14.31 / 6.2× (PN-67). The power ratio, not the cost ratio,
carries the point. These are wall-clock, single measurements, model loads included — say so.

**Evidence:** PN-41 as superseded by T19; T19's per-cell sums.
**Failure mode.** Quoting any cost contrast not currently in T19. This number has been wrong twice.

---

### §6 What the configuration axes do — 3,400 words (an opening bridge and seven subsections)

**Opening bridge (100 w).** The instruments of §5 were built to compare compressions. Applied to the
choices *around* the compression — window, split, KV dtype, speculative setting, backend — they
return effects an order of magnitude larger, and several of them are load/no-load rather than a mean
with an interval.

---

**§6.1 The window belongs to the split — 700 w · F4, F4-inset, F11 · T10, T11**

**Claim.** On a two-GPU host with no fast interconnect, the tensor split rather than the quantization
set the reachable context window for two of the four arms measured.

Physical mechanism first: under `--split-mode layer` each layer's weights *and its slice of the KV
cache* live on one card, there is no NVLink, so the binding limit is per-card 16,311 MiB and never
the 32,622 MiB aggregate — every ceiling in this study was set by the unluckier card while the other
held 1,955–3,829 MiB that is physically unreachable. Then the causal demonstration: UD-Q5_K_XL fails
to load at 262,144 at the engine default split and loads at **five different `-ts` ratios**; UD-Q6_K
likewise fails at the default and loads at `58,42`. ⚠️ **Scope it exactly as PN-39 does**: UD-Q4_K_XL
**loads at the default split**, UD-Q6_K_XL was never attempted there at that length, and each
default-split failure is a **single** attempt against this project's own two-attempt bracketing rule.
Write "for two of the four arms measured", never the README's unscoped form. The optimum is
quant-specific and **not monotone-safe** — `54,46` fails where `58,42` loads, and on UD-Q6_K_XL
`58,42` overshoots and only `56,44` loads, taking it to 212,992 against a previously published
131,072. Cite Heiser's unfair-competitor benchmarking crime to justify per-arm winning ratios as the
methodologically correct comparison.

**Evidence:** PN-6, PN-39, PN-7, PN-5 (the depth-gate defect that makes one early cell's ceiling
optimistic, cross-referenced to Appendix B).
**Failure mode.** The unscoped claim. PN-39 exists because the claim overreached once already.

---

**§6.2 Ratio, imbalance and throughput — 150 w · F4-inset · T10, T12**

**Claim.** Balance and throughput are not opposed, but the relationship is not monotone and the most
balanced ratio was the slowest.

All five loading ratios for UD-Q5_K_XL at 262,144, ordered by imbalance: 28 MiB → 8.50 tok/s
(slowest); 166 → 10.78; 742 → 10.82 (fastest); 1,176 → 10.67; 1,750 → 10.44. ⚠️ **PN-8's "the least
balanced ratio that loads is the fastest" is factually wrong and is corrected by PN-42**: `54,46` is
the *middle* of the imbalance range, `62,38` is 2.4× more imbalanced and also loads, and decode peaks
near 742 MiB then declines. The four non-outlier ratios cluster within 3.6 %, inside this host's
40.7 % within-configuration noise floor (§6.7), so **only the outlier survives** as a claim. The
practical rule is "sweep, and keep the fastest that loads, reporting the imbalance alongside" — and
the sweep tool's own defect (it stopped at the first ratio that loaded, which is why the Q5-vs-Q6
speed comparison is ratio-confounded) is named here, not hidden. `-ctxcp` 4 → 32 is a directional
free gain: +6.8 % decode, +7.6 % prefill, identical peak VRAM, n=1 A/B — adopt it, do not quote the
percentage as a measured effect.

**Evidence:** PN-8 corrected by PN-42, PN-18, PN-45 (the noise floor this is measured against).
**Failure mode.** Quoting 6.8 % as an effect. It is the same order as the rep-to-rep noise.

---

**§6.3 KV-cache quantization is not free — and here the §5 instrument transfers — 350 w · F27,
F27b · T3**

**Claim.** The KV dtype on which every context ceiling in this study depends moves the token
distribution about half as far as dropping a whole quantization level, while moving perplexity by
0.15 %.

q4_0 against f16 on the same model and corpus: mean KLD **0.002955 ± 0.000127**, top-1 agreement
99.401 ± 0.043 %, below the external <0.007 band — defensible, and **not free**. Against the
reference arm's own quantization step on code (0.005829) that is **51 %**; ⚠️ PN-43 qualifies this as
a *size comparison, not an additive currency*, and the phrasing must not imply that divergences add.
The same pair moves perplexity **+0.15 %** — the report's cleanest self-contained demonstration of
averaging bias, and the reason §5.3's ladder could not certify itself. Two external comparisons must
appear because a reader will find them: QLLM-Eval's finding that at context ≥ 4K most models are
*more* sensitive to KV-cache than to weight-only quantization at the same bit-width (which is exactly
why the "measured at n_ctx 2048, not at depth" caveat is a live risk rather than a formality), and
oobabooga's published q4_0 KV KLD for a Qwen-family model an order of magnitude above this one —
different model version, corpus and truncation, so **not in one table**, but the qualitative
agreement is real corroboration. ⚠️ Carry PN-43's second half too: a label collision gave two cells
one serverlog path and contaminated one reparsed PPL field. It is disclosed here and detailed in
Appendix B.

**Evidence:** PN-15, PN-43, PN-62 (the same cell serves as §5.2's control — say so, it is the
interlock between the halves).
**Failure mode.** "51 % of a quantization level" read as additive.

---

**§6.4 Speculative decoding is part of the accuracy configuration — 600 w · F5, F13, F13b · T13**

**Claim.** Speculative decoding on this engine is deterministically, reproducibly *not*
output-identical to unspeculated decoding — and the assumption that it was had been used to skip
measurements for nine days.

At temperature 0 with a fixed seed on UD-Q6_K over 164 HumanEval+ problems, `--spec-draft-n-max` 2
and 4 each reproduce the no-spec baseline byte-exactly on **131 of 164 (79.88 %)**, diverging on 33
with the first differing character at a median of 715 / 730. Then the control that upgrades the
claim: re-run a day later, unchanged, **both configurations reproduce themselves byte-identically**
(no-spec md5 identical across runs; MTP 164/164) while continuing to differ from each other on
exactly the same 33 problems. This is not an approximation that drifts; it is a reproducibly
different decode path. ⚠️ Retract PN-23's own mechanistic speculation in the text — it proposed
float non-associativity and PN-26 refutes it — because that visible self-correction is a credibility
asset. Then the divergence structure: it is a **per-character hazard, not a per-problem rate**
(2.4 % of short completions, 53.7 % of long ones), which matters enormously for an agentic workload.
Then the meta-finding, which is this section's reason to exist beyond the number: the losslessness
premise was recorded as settled fact in the project's own reference log with the instruction
"document this rather than running them", propagated into a configuration recommendation, and stood
for nine days until the first experiment that tested it (PN-59). Frame the whole section as a
**per-stack verification claim** — "losslessness is a property to verify per stack" — never as a
refutation of speculative decoding or of DFlash (R12), which is cited as motivation and foil.

**Evidence:** PN-23, PN-26, PN-59, PN-25 (why one arm's equivalence figure is engine-confounded).
**Failure mode.** Reading as a refutation of an algorithm. It is a measurement of one engine build.

---

**§6.5 Speculative method and draft depth — 450 w · F5, F14, F14b · T13, T14**

**Claim.** The ranking of speculative methods reverses with context, deeper drafting is not reliably
faster, and this host's decode variance — reaching 166 % rep-to-rep — does not separate draft depths
at three repetitions.

- **Method comparison at ctx 32,768** on 164 problems: no-spec 18.46 tok/s; MTP n=2 37.44 (2.03×,
  acceptance 0.954); MTP n=4 47.03 (2.55×, 0.892); **DFlash2 n=4 51.78 (2.81×, 0.917)** — the fastest
  configuration measured on the ladder. ⚠️ The DFlash2 row is **engine-confounded**: a drafter is
  bound to the engine build that can parse it, and this arm necessarily ran on a different image than
  its baseline, so its byte-identity figure (132/164) must not be tabulated beside MTP's.
- **The reversal.** DFlash2 fails to load at 262,144 and at 212,992 with compute-buffer OOM; its
  highest reachable rung is 163,840 — **37.5 % less context than MTP reaches** — where decode falls
  to 8.34 tok/s and acceptance halves to 0.4583. Fastest at short context, unable to reach the
  deployment window at all.
- **Draft depth at matched depth**, 4 arms × 2 depths × n_draft {2,4,8} with prompt lengths held
  identical: acceptance falls with draft depth in 10 of 11 adjacent pairs (⚠️ PN-32 printed 12 of 13;
  two of those "adjacent" pairs skip a rung, and PN-66 repairs the count to 10/11 with a one-sided
  sign-test p of 0.00586 — which survives Holm at rank 1 or 2 and not at rank 3, so its survival is
  **rank-dependent, not robust**). Decode does *not* improve monotonically: on UD-Q6_K the n=8 arm is
  slower than n=2 at acceptance 0.251. ⚠️ **Report no per-arm best draft depth** — decode rep-to-rep
  spread reached 166 % and the design does not separate the depths at n=3. ⚠️ PN-9's per-quant acceptance figures
  (0.897 / 0.564 / 0.516) are **confounded** across depth and `-ts` ratio; the sweep built to resolve
  that failed on power, so the confound stands and must be stated. ⚠️ PN-24's at-depth half is
  **withdrawn** (it timed 17 generated tokens — PN-30); its ctx-32,768 half over 164 real generations
  stands.

**Evidence:** PN-29, PN-32, PN-66, PN-9, PN-24 scoped by PN-30, PN-61, PN-25.
**Failure mode.** Publishing a draft-depth recommendation. Two documents in this project already did
and both were withdrawn.

---

**§6.6 Backends: three stacks, one wall, and a 5.1× context gap — 750 w · F18 · T17**

**Claim.** The largest single configuration effect measured in the study is a backend property, not a
model property — and a 1.19 GiB draft-worker allocation stopped three independent stacks at the same
point.

- **Context.** The same weights reach the full native 262,144 under llama.cpp with q4_0 KV and a
  rebalanced split; the vLLM NVFP4 path measured a KV pool of **52,337 tokens** at the highest
  GPU-utilisation setting that boots (0.97), a working ceiling of **51,200** — **5.1× short** — with
  MTP roughly halving it again. ⚠️ The battery was **aborted before completion**; three harness
  defects were identified and documented and the run was not repeated, so the figure is a bootable
  ceiling from one image and the historical 98,304 on the stable image suggests it is image-dependent.
  Say all of that in the sentence that reports it.
- **The 1.19 GiB wall.** SGLang 0.5.18's `EagleDraftWorker`, and vLLM nightly with a BF16 DFlash2
  drafter at *every* utilisation setting from 0.78 to 0.97 and every context from 3K to 16K, both
  fail with an identically sized 1.19 GiB allocation; llama.cpp with a 1.14 GiB 4-bit GGUF drafter
  succeeds, and MTP sidesteps the problem entirely because its predictor lives inside the checkpoint.
  ⚠️ The identical size across two unrelated stacks is **unexplained** and is reported as an
  observation, never as a mechanism.
- **One backend produced nothing at all.** SGLang failed to start at 131,072 / 65,536 / 32,768 /
  16,384; no SGLang throughput, accuracy or context figure exists anywhere in the corpus and none can
  be constructed. A negative result about one version on one hardware configuration — and a
  non-speculative SGLang configuration was not proven impossible, it was not tried. Two sentences,
  and it earns them: a reader planning this hardware needs it.
- **Cross-backend throughput, one probe.** vLLM NVFP4 12.44 → 41.21 tok/s with MTP depth 4 (3.31×);
  llama.cpp UD-Q4_K_XL 23.00 → 38.51 with DFlash2 depth 4 (1.67×). Best absolute figures within 7 %
  despite speedup ratios differing 2× — because `--enforce-eager` cripples the vLLM baseline. **A
  speculative speedup ratio is meaningless without its baseline.** MTP acceptance cross-validates
  across engines at matched depth (0.728 vs 0.709), the best evidence in the corpus that acceptance
  is a property of the draft head rather than of either implementation. ⚠️ Backend, quantization
  scheme, KV dtype and speculative method all vary at once — no single-variable conclusion.

**Evidence:** PN-56, PN-53, PN-54, PN-55.
**Failure mode.** A cross-backend ranking. Four variables move at once and the table says so.

---

**§6.7 Throughput at depth, power and thermals — 300 w · F12, F12b, F22 · T12, T22**

**Claim.** Decode throughput does not discriminate the ladder, the variance that hides the difference
is explainable rather than mysterious, and the depth-0 tables the field quotes are 3–5× optimistic.

- **The span.** Over *true* repetition groups (same arm, same context, same `-ts`) the arms span
  **6.74 %** against a within-configuration spread reaching **40.7 %**. ⚠️ Use PN-45's figures.
  PN-19's 32.9 % pooled four context depths and is withdrawn; PN-36's replacement 46.7 % silently
  switched estimator from `(max−min)/median` to `(max−min)/min` and mixed `-ctxcp` 4 and 32 in one
  group. Three published values for one quantity, reconciled in T12 — a worked example of §4.4's
  aggregation rule, and one of the report's most useful pages.
- **Explain the noise, do not report it.** `draft_n` and `draft_n_accepted` are byte-identical across
  `-ts` ratios within a repetition index, decode regresses on acceptance at r² = 0.83–0.99, and
  conditioning on acceptance collapses within-configuration spread from 17–41 % to 3–11 %. Three
  correction passes missed this; two blind reviews found it independently. Say that the noise figure
  is an **upper bound** and that a greedy re-measurement would tighten it at no GPU cost.
- **Depth.** Prefill falls monotonically with filled depth in every arm; decode at a *filled* window
  is 3–5× slower than the depth-0 tables that are most often quoted elsewhere (37.22 tok/s at depth 0
  against 7.19 at depth 186,265 before rebalancing, and 13.85 after). ⚠️ Historical depth-0 rows and
  at-depth rows never share a table.
- **Power and thermals — modelled, not measured, and say so first.** 149.2 W mean / 408.9 W peak over
  a representative 12-hour window with 26 % GPU-busy time, 1.791 kWh of which the GPUs are 60 %; an
  idle-to-loaded swing of ~4.2×. GPU0 peaked 14 °C above GPU1 on physically identical cards — the
  expected signature of `-ts 5x,4x` placing more layers on GPU0, so the ratio chosen for context or
  throughput also selects a thermal operating point. ⚠️ Observational and confounded (the window
  mixes quants, ratios and rungs); `est_system_w` is modelled from GPU telemetry plus RAPL plus a
  fixed platform allowance, with no wall-socket sensor. **No per-configuration J/tok figure exists
  and none will** — the energy wave was cancelled, and the historical J/tok table is depth-0 and from
  the deleted image.

**Evidence:** PN-45 (superseding PN-36, which superseded PN-19), PN-19, PN-36, PN-30, PN-11, PN-12,
PN-20.
**Failure mode.** Using a null under high variance as a finding here while criticising exactly that
inference in §5.4. The two must be argued the same way.

---

### §7 Threats to validity — 1,400 words · **written before §5 and §6 are polished**

**Structure.** Two labelled groups, per `STYLE-GUIDE.md` §3.7: **limitations** (conscious scope
decisions, reported as choices with reasons) and **threats** (issues that could move a number,
reported with what bounds them and how wrong they would have to be). Each item in four moves: the
objection in the strongest form a critic would state it; what bounds it; what survives, scoped; what
removing it would cost. Reviewer D §6 is the base text and its ordering is adopted.

**Threats — ordered by what an informed reader attacks first.**
1. **Ladder-relative reference.** No FP16 fits the host; the reference's own degradation is
   unmeasured and zero by construction. Mitigation to state: because the reference is itself ~6-bit,
   every arm's true distance from FP16 is *larger* than reported, so the claims are conservative in
   the direction that matters. Reframe the quantity as quantization-*step* damage along a ladder
   practitioners actually choose from. *(PN-13 caveat, reviewer D §4.2)*
2. **Multiplicity.** No correction was applied across ~19 tests. All nine divergence separations pass
   Holm and Benjamini–Hochberg; the weakest (3.71 σ) does **not** survive Bonferroni once clustering
   at design effect 1.5 is allowed for, and PN-32's acceptance result survives Holm only
   rank-dependently. This is where the prose figures are reported, and where the body's code-only
   range is reconciled with them: the weakest of the nine, the prose adjacency at **3.71 σ**, is the
   one separation that does not survive clustering — which is the reason the body quotes the
   code-domain **8.7–18.1 σ** and never a blended "3.7–11.8".
   *(PN-66, T23, F28)*
3. **Prompt-token divergence is not generation quality.** The paired generative anchor bounds it at
   ±3 points but does not establish equality. *(PN-28, PN-40)*
4. **The divergence metric loses ranking power in the near-baseline band** (arXiv:2606.19558) —
   which is where these arms sit. Concede, then give the joint reading with §5.1's separations.
5. **KV fidelity measured at n_ctx 2048, not at depth**, on the reference arm and the code domain
   only — with QLLM-Eval making it a live risk. *(PN-15, PN-31)*
6. **Long-context task accuracy is unresolved for every arm.** Task outputs at 131K *do* exist —
   248 items across six RULER cells — but the one battery that appeared to separate the arms
   measured budget exhaustion, not retrieval: `closed-and-wrong` is exactly zero across the whole
   battery, and across the 55 items where neither arm's budget bound both arms score 55/55 with
   zero discordance. Retrieval at 131K is **unanswered, not answered negatively**; a re-run at a
   generous `n_predict` with thinking disabled would settle it. This is the largest hole.
   *(PN-60, PN-63)*
7. **Single-attempt failures under a rule requiring two.** Every default-split failure in §6.1 was
   attempted once; re-testing would cost ~20 minutes of GPU and was not done. *(PN-39)*
8. **PN-9's quant/depth/ratio confound is unresolved**, and the sweep built to resolve it failed on
   power. No per-arm best draft depth is reported. *(PN-9, PN-32)*
9. **One engine image, one host, one model family, two single-domain corpora**; the code corpus is
   django and may be memorised. A second held-out code corpus is the single most valuable missing
   measurement and costs about one GPU-hour — say that, because it is checkable.
10. **Calibration contamination.** Unsloth's imatrix data is not published, so a wikitext-favourable
    bias cannot be excluded — itself an argument for weighting the code domain.
11. **Historical rows are irreproducible on current images.** *(PN-57)*
12. **Every evidence chain terminates in a serverlog that `.gitignore` excludes.** The honest artifact
    claim is *Artifacts Available*, not *Functional* (R14/R15). *(PN-62's provenance caveat, PN-65)*

**Limitations — conscious choices.**
13. Spec-decode equivalence is **greedy-only**; the temp > 0 test was cancelled under DEC-12.
14. No per-configuration energy figure; the energy wave was cancelled.
15. `reasoning_effort` equivalence, the presence-penalty probe and the draft-KV dtype axis were
    cancelled and are named, not silently absent.
16. Six quantizations in the Q4–Q6 band were never tested and are listed by name and size.
17. Absolute scores are **not comparable to published numbers**: logprob instruments run greedy while
    the official presets are temp 0.7 / 1.0, and the model's publisher reports LiveCodeBench v6,
    SWE-bench **Pro** and Terminal Bench — none set up here, and no HumanEval at all.
18. **`variable_tracking` was excluded post hoc** and it is the harder long-context task. The
    exclusion is defensible (an output-format artifact, 0 items fully correct in either arm) and it is
    reported in the body, with its reasoning, because a reader who finds it in a JSON field will
    distrust everything else.

**Close on item 19, the open problem** — not on the weakest item: whether damage confined to ~1–5 %
of token positions **compounds** over a long-horizon agentic trajectory, where a model makes
thousands of decisions and each is a draw from a perturbed distribution, is unmeasured, including
here. §5.7's 6-of-6 step-limit result is the only hint the corpus contains and it is n=6.

---

### §8 Conclusion — 350 words

**Unchanged in intent from v1, which correctly identified that no conclusion exists yet.** Three
sentences of result, one of consequence for practice, one of open problem. No new numbers, no
recapitulation of the abstract.

Result: divergence ranked the ladder in 2.32 GPU-hours; five task instruments bounded it and none
resolved it on its intended construct, three of them costing 14.31 GPU-hours between them; and the configuration axes around the quantization
moved the deployment outcome further than the quantization did. Consequence: a practitioner choosing
a quantization on a task battery at these sample sizes is reading noise, and should sweep the split,
declare the KV dtype and verify speculative equivalence before arguing about bit-width. Open problem:
`STYLE-GUIDE.md` §3.8's closing sentence on compounding, used verbatim.

Then one paragraph the style guide does not currently require and this structure earns: **the
measurement record itself.** Sixteen headline claims were withdrawn or scoped by this study's own
re-analysis, fourteen of them at zero GPU cost, because the evidence was kept per-item rather than
summarised. That is not an apology; it is the strongest available demonstration of the thesis.

---

### Appendices

**Appendix A — Practitioner configuration (700 w).** `TRACK-A-DECISION.md` compressed, framed as
*what this analysis implies for one concrete deployment* and explicitly not the report's
recommendation. The pinned command line, the fallback ladder, the conditions it is contingent on, and
Amendment 2 — the reverted draft-depth flag — in **one** paragraph as a worked example of a withdrawn
claim. *(PN-6, PN-7, PN-18, PN-23, PN-30)*

**Appendix B — The reproducibility register (1,000 w · T20, F20, F25).** **Twelve register entries
covering twenty-one defects**, in three named families — write the count that way once, here, because
T20 holds twelve entries of which entry 12 is PN-58's ten historical reporting defects, and "twelve
defects" beside PN-58's "ten-defect audit" reads as an arithmetic error to anyone checking. The
register is delivered as a **table with two-sentence rows** rather than as prose, which is what pays
for the reduction from 1,300 words to 1,000 without dropping an entry. Unified by one thesis in the
first sentence: *silent success is the dominant failure
mode of automated benchmarking.* Each written as a trap another group would fall into — the general
first, the instance second. ⚠️ **v2 departs from reviewer B here.** B recommended cutting from seven
entries to four and dropping PN-10 and PN-27. This outline keeps all twelve, because the owner's
binding instruction is that nothing measured is thrown away and because the register is, on three
reviewers' assessment, the most reusable part of the corpus. The cost is 100 words at table density
and it is paid
knowingly; if the page budget bites, cut PN-10 and PN-27 first, exactly as B suggested.
*(PN-5, PN-10, PN-17, PN-20, PN-25, PN-27, PN-30, PN-31, PN-38, PN-43, PN-57, PN-58, PN-59, PN-65)*

**Appendix C — Full tables (700 w + tables).** Every percentile and Δp of the divergence corpus; the
complete `-ts` sweep with every failure mode; per-repetition decode figures; all fourteen RULER cells
with the closure audit; all three generations of the SWE-bench totals; the `variable_tracking`
exclusion in full; the six untested quantizations by name and size. *(T3, T5, T9, T10, T15, T16, T21,
T23)*

**Appendix D — Claim index (500 w + table).** Every numeric claim → section → paper note → artifact
path → serverlog. The report's best answer to "this cannot be checked", and it is cheap because the
mapping already exists. Includes the provenance repair record: seven families of numbers existed in
the repository only as prose until 2026-09-03 and are now committed artifacts. *(PN-65)*

---

## 5. Coverage — every one of PN-1…PN-66

**Weight** column: `LEAD` = the note carries a subsection's headline claim · `BODY` = cited in the
body as supporting evidence · `CAVEAT` = appears in the body only as a scoping or correction clause ·
`APPX` = appendix only. Nothing is unused; where a note appears in more than one place the primary
home is listed first.

| PN | one-line subject | section(s) | weight |
|---|---|---|---|
| PN-1 | measured sampling defaults match no documented set | §3.2, T2 | LEAD |
| PN-2 | thinking on by default; the 2-token discriminator | §3.2 | BODY |
| PN-3 | `reasoning_effort:none` raises a Jinja exception | §3.2 | BODY |
| PN-4 | `-fit` did not shrink here and still cannot be trusted | §3.2 | BODY |
| PN-5 | a depth gate documented but never asserted | App B; §6.1 caveat | APPX |
| PN-6 | the ceiling belongs to the split (5 loading ratios) | §6.1 | LEAD |
| PN-7 | the `-ts` optimum is quant-specific, non-portable | §6.1; App A | LEAD |
| PN-8 | imbalance vs decode — **superseded by PN-42** | §6.2 | CAVEAT |
| PN-9 | acceptance varies by quant — confounded | §6.5; §7 item 8 | BODY |
| PN-10 | three orchestration defects, each plausible-wrong | App B | APPX |
| PN-11 | host power envelope, 4.2× idle-to-loaded | §6.7, T22 | BODY |
| PN-12 | 14 °C thermal asymmetry from the split | §6.7, T22 | BODY |
| PN-13 | the divergence ladder (the note's own phrase is 3.7–11.8 σ; **the report quotes the code-domain 8.7–18.1 σ**, §5.1) | §5.1, §1, §4.2 | LEAD |
| PN-14 | code ≈ 2× prose, widening with aggressiveness | §5.1, §5.2 | LEAD |
| PN-15 | q4_0 KV costs 51 % of a quantization level | §6.3 | LEAD |
| PN-16 | top-1 agreement and mean KLD disagree | §5.1, §5.2 | BODY |
| PN-17 | exit-code scoring reported a run that measured nothing | App B, T20 | APPX |
| PN-18 | `-ctxcp` 4 → 32, free directional gain | §6.2; App A | BODY |
| PN-19 | speed does not discriminate — **numbers superseded** | §6.7 | CAVEAT |
| PN-20 | an aggregator that never named its estimator | §4.4, App B | BODY |
| PN-21 | three-tier domain hierarchy, prose < code < task | §5.1, §1 | LEAD |
| PN-22 | HellaSwag: structurally insensitive at n=400 | §5.4 | LEAD |
| PN-23 | MTP is not output-identical: 131/164 | §6.4, §1 | LEAD |
| PN-24 | draft depth n=4 > n=2 — **at-depth half withdrawn** | §6.5 | CAVEAT |
| PN-25 | a drafter mis-bound to the wrong engine build | App B; §6.5 caveat | APPX |
| PN-26 | the determinism control: both arms self-reproduce | §6.4 | LEAD |
| PN-27 | a safety predicate matching its own supervisor | App B, T20 | APPX |
| PN-28 | generative anchor: −0.61 pts, 3 and 5 discordant | §5.5a | LEAD |
| PN-29 | DFlash2 on its correct build: fastest, cannot reach depth | §6.5 | LEAD |
| PN-30 | a throughput measurement that timed 17 tokens | App B; §6.5, §6.7, App A | APPX |
| PN-31 | KL divergence infeasible at long context on 14 GiB | §4.3; §3.1 footnote | BODY |
| PN-32 | acceptance falls with draft depth; n=3 cannot rank | §6.5 | LEAD |
| PN-33 | RULER S-NIAH saturated at three lengths | §5.6 | BODY |
| PN-34 | difficulty gates sensitivity — **mechanism superseded** | §5.6 | CAVEAT |
| PN-35 | damage is tail-concentrated (the novel result) | §5.2, §1 | LEAD |
| PN-36 | PN-19's spread was a depth artifact — **itself corrected** | §6.7, T12 | CAVEAT |
| PN-37 | saturation is false for two of three instruments | §5.4, §5.6 | BODY |
| PN-38 | free-running generation cannot measure distance | §4.3, App B | BODY |
| PN-39 | the split claim holds for 2 of 4 arms | §6.1, §7 item 7 | LEAD |
| PN-40 | the McNemar tests could not have reached 0.05 | §5.5a, §5.4, §4.4, T6 | LEAD |
| PN-41 | the cost contrast — **superseded by T19** | §5.8 | CAVEAT |
| PN-42 | imbalance vs decode is not monotone | §6.2 | LEAD |
| PN-43 | a label collision corrupted one reparsed field | §6.3, App B | CAVEAT |
| PN-44 | MK-NIAH separates at n=100 — **superseded by PN-60** | §5.6 | CAVEAT |
| PN-45 | 6.74 % between arms against 40.7 % within | §6.7, T12 | LEAD |
| PN-46 | non-thinking HumanEval+ ladder + context control | §5.5b | LEAD |
| PN-47 | thinking mode: the signal is empty responses | §5.5b | LEAD |
| PN-48 | perplexity spans 0.033 against ±0.041 | §5.3 | LEAD |
| PN-49 | the 36-fold protocol swing | §5.3, §1 | LEAD |
| PN-50 | SWE-bench Verified inverts the ladder | §5.7, §1 | LEAD |
| PN-51 | the disqualified arm that every cheap instrument rates well | §5.7 | LEAD |
| PN-52 | step count is inversely related to fidelity | §5.7 | BODY |
| PN-53 | the 1.19 GiB draft-worker wall across three stacks | §6.6 | LEAD |
| PN-54 | SGLang produced no measurements at all | §6.6 | BODY |
| PN-55 | cross-backend: same peak by opposite routes | §6.6 | LEAD |
| PN-56 | vLLM NVFP4 ceiling 5.1× short of native | §6.6 | LEAD |
| PN-57 | one deleted image invalidated the historical matrix | §3.3, §7 item 11 | BODY |
| PN-58 | the ten-defect reporting audit (entry 12 of App B's twelve) | App B; §5.7 provenance | APPX |
| PN-59 | an assumption that suppressed measurement for nine days | §6.4 | BODY |
| PN-60 | the long-context result measured budget closure | §5.6, §1 | LEAD |
| PN-61 | acceptance of exactly 1.000 is a degenerate artifact | §6.5; §5.7 caveat | CAVEAT |
| PN-62 | tail *shape* is a corpus property (the KV-only control) | §5.2, §6.3 | LEAD |
| PN-63 | the closure audit clears S-NIAH and explains the defect | §5.6, §4.3 | LEAD |
| PN-64 | PN-35's median row corrected; 18 of 20 cells verify | §5.2 | CAVEAT |
| PN-65 | seven families of numbers existed only as prose | App D, §3.3, §5.7 | BODY |
| PN-66 | PN-32 fails Holm once its pair count is repaired | §7 item 2, §6.5 | BODY |

**Not used: none.** Sixty-six of sixty-six have a home. Counting by weight: 27 `LEAD`, 18 `BODY`,
12 `CAVEAT`, 9 `APPX`. **Nineteen notes that appear in v1's body not at all or only as a
half-sentence** — PN-46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 61, 63, 64, 65, 66 —
carry `LEAD` or `BODY` weight here. That is the measurable form of the owner's complaint, and the
measurable form of its fix.

---

## 6. What changes in the figure programme

The programme is sound and mostly survives; the changes are re-tiering, three additions and four
demotions. `FIGURE-PROGRAMME.md` should be amended rather than rewritten.

### 6.1 Tier changes

| figure | v1 tier | v2 tier | reason |
|---|---|---|---|
| **F15** HumanEval+ ladders | CORE | **ESSENTIAL** | §5.5a/§5.5b carry two ladders across seven configurations and 328+ problems of paired data; neither subsection's headline claim has another figure. F15 gains a panel split to match: (a) the paired anchor, (b) the non-thinking ladder, (c) the thinking ladder. It is the second-most-cited instrument in the report. |
| **F10** the protocol swing | CORE | **ESSENTIAL** | Reviewer C ranks it the best-provenanced single result in the corpus and led an abstract with it; it is contribution 7 and it is the only figure that makes a claim about *measurement conventions* rather than about models. |
| **F12** speed and its explainable noise | CORE | CORE (unchanged) | §6.7 is budgeted at 300 words and leans on T12 and T22, so the figure carries the span, the noise floor and the depth curve rather than the prose |
| **F27** KV quantization is not free | SUPPORTING | **CORE** | §6.3 is now a subsection with its own claim and the interlock to §5.2's control |
| **F26** perplexity does not certify its own ranking | SUPPORTING | **CORE** | §5.3 is now a 350-word subsection with its own claim, not a clause; at that budget the figure carries the 0.033-against-±0.041 comparison |
| **F22** throughput vs filled depth | CORE | CORE | already promoted 2026-09-04; confirmed |
| **F21** the measurement design | SUPPORTING | **CORE**, and re-scoped — see 6.2 | it becomes the scope inventory §1 needs |
| **F7** tail shape by corpus | CORE | **SUPPORTING**, folded into F2 as panel (c) | F2 already carries the control; two figures making one claim is the density rule inverted |
| **F6** two instruments, one axis | CORE | **SUPPORTING** | F3 does this better and F6 duplicates it; keep it only if §1 needs a graphical opener |
| **F20** the correction record | CORE | **SUPPORTING** (Appendix B) | it is method, and Appendix B is where method lives; it stays in full |
| **F24** minimum attainable p | SUPPORTING | SUPPORTING (Appendix C) | T6's column carries the claim in the body |

**The six ESSENTIAL become eight:** F1, F2, F3, F4, F5, F16 (unchanged) **+ F15, F10**. Eight is
defensible at 40 pages and it fixes the specific imbalance the owner identified: under v1's six, a
reader who saw only the essential figures would conclude this was a quantization study with benchmark
asides.

### 6.2 Additions

- **F21-scope (re-scoped F21) — the study's coverage matrix.** Rows: the eight quantized checkpoints
  plus the drafter. Columns: the nine instrument classes and three backends. Cells: measured /
  historical-irreproducible / not attempted / failed-to-start. This single figure answers "how much
  of this study is in this paper" on page 2, and it is the direct structural answer to the owner's
  criticism. Data exists: `fig21-arms-manifest.csv` plus T19, T15, T16, T17. **New data file
  required** (`fig21c-coverage-matrix.csv`), generated by `extract.py`, not hand-typed.
- **F16b — the three generations of the SWE-bench totals**, as a small companion to F16: pre-fix
  36/47 and 35/48, the §13.66 correction, and the x86_64-corrected finals, with the ARM64 manifest
  cause annotated. Data exists in `fig16-swebench-verified.csv` (8 rows). It makes the correction
  visible rather than footnoted, which §5.7 requires.
- **F19 gains a separation column.** Cost alone is half the argument; cost against *arms separated*
  is the whole of it. No new data — T19 already carries both.

### 6.3 Demotions and one deletion candidate

- **F23** (generation forks) and **F25** (defect taxonomy) move to Appendix B/C with their specs
  unchanged. They remain in the programme; they leave the body.
- **F17** (the Q3 profile) stays CORE and moves from §1 to §5.7, where its evidence now lives. Its
  1.000-acceptance panel must be **redrawn or annotated** under PN-61 — that value is a degenerate
  artifact and must not be plotted as a measurement.
- **F28** (multiplicity) stays CORE but moves from §5.2/§7 to §7 only.
- **No figure is deleted.** F6 is the only genuine candidate and it is retained as a possible §1
  opener; the decision is deferred to D7 when the introduction is drafted.

### 6.4 Caption discipline that this structure adds

Because §5 is ordered by instrument and §6 by axis, **every caption in §5 must name the instrument
and its n in the first clause**, and every caption in §6 must name the axis and the arms it varies
over. A reader jumping into the middle — the second of `STYLE-GUIDE.md` §2.5's three readers — needs
to know which half of the paper they landed in from the caption alone.

---

## 7. What this supersedes, and what still has to be checked

### 7.1 Superseded by this file

- `OUTLINE.md` in full. It is retained unedited (hard rule 6: append, never rewrite) as the record of
  the pre-rebalance plan and of the review round that produced it.
- `STYLE-GUIDE.md` §2.8's length budget (11,350 body words, ~30 pages) → **13,500 body words /
  ~26 pages of body, ~34 pages with appendices**, per the audited allocation in §3.1 and the named
  levers in §3.4. This is a **+18.9 % departure**, not the +40 % v2 first proposed, and it is
  justified item by item rather than declared: nineteen paper notes that carried no body weight in
  v1 carry `LEAD` or `BODY` weight here (§5), and eight sections are cut from their v2 targets to pay
  for them. **Nothing else in the style guide is touched**; voice, density technique, sentence
  conventions, caption rules and the checklist all stand.
- `STYLE-GUIDE.md` §3.5's seven-subsection §5 → §5 (ten blocks: an opening map and nine subsections,
  by instrument) + §6 (eight blocks: an opening bridge and seven subsections, by axis). The per-subsection craft notes there remain valid; they attach to the
  corresponding v2 subsection, listed in §4 above.
- Reviewer B's §6 outline, on two points only, both stated with reasons: the body is longer than his
  9,000–10,500 words (13,500 against a 10,500 ceiling, +28.6 %), and Appendix B keeps twelve register
  entries rather than four — though it now delivers them as a table, which is half of what B was
  asking for. Everything else of B's —
  the equivalence-bound rule, the Dutta positioning, the arXiv logistics, the Heiser citation, the
  §2 structure — is adopted.

### 7.2 Drafting-order constraints, confirmed intact

- **§7 is written before §5 and §6 are polished** (D3 before D4). Unchanged, and more important now
  that the results body is two sections: a threat discovered while polishing gets softened, and there
  are twice as many opportunities.
- **§2 stays under 900 words.** Hard cap, moderation risk, unchanged.
- **The conclusion is §8.** Unchanged; appendices are lettered, not numbered.
- Drafting order D0–D9 in `DRAFTING-PLAN.md` needs **two** edits, not one. **D4 becomes "D4a §5
  Results — instruments" and "D4b §6 Results — axes"**, drafted in that order, because §6.3 and §6.5
  depend on instruments established in §5.1 and §5.5a. **And D5 must be renumbered with it**: as
  written it names "§6 Cost, §8 Practitioner appendix, §9 Reproducibility appendix", section numbers
  v2 has reassigned — §6 is now the configuration axes, cost is §5.8, and the appendices are lettered
  A–D. D5 therefore becomes "§5.8 instrument economics · Appendix A practitioner configuration ·
  Appendix B reproducibility register". Both edits are applied in `DRAFTING-PLAN.md` as of
  2026-09-04; see this file's repair log.

### 7.3 Open verification items — resolve before or during drafting, none needs GPU

1. **The checkpoint count.** The owner's brief says "nine quantizations", and names eight:
   Q3_K_XL, IQ4_XS, Q4_K_M, Q4_K_XL, Q5_K_XL, Q6_K, Q6_K_XL, NVFP4. `fig21-arms-manifest.csv` lists
   five GGUFs plus the DFlash2 drafter. **Fix the number once, in T1 and F21-scope, and use it
   everywhere** — this outline says "eight quantized checkpoints" provisionally. Candidates for the
   ninth: the deleted pre-E12 UD-Q6_K build (~21.6 GB, distinct from the current 21.98 GB file), or
   the DFlash2 drafter counted as a checkpoint.
2. **The cost contrast — settled, and now enforced.** T19's **2.32 / 14.31 GPU-hours, a 6.2× ratio**
   is the only pair this report quotes, and PN-67 records the supersession of PN-41's 2.15 / ≈4.8.
   The 14.31 covers **three instrument classes only** — HellaSwag, HumanEval+ and RULER — so the
   perplexity work and the four-day pre-E12 SWE-bench campaign sit **outside** it, and that scope
   clause travels with the figure wherever it is printed (§1, §5.8, §8, Appendix D). Remaining task:
   `README.md`'s "about two GPU-hours" and any residual PN-41 phrasing in `ABSTRACT-V2.md`'s trap
   list. This number has been wrong twice; it must not be wrong a third time in the paper itself.
3. **PN-29's at-depth DFlash2 cell** is not yet verified against the PN-30 degenerate-generation
   defect, and §6.5 cites it. Verify from the artifact or scope the claim before D4b.
4. **The acceptance-conditioned speed re-analysis** (r² 0.83–0.99, spread 41 % → 11 %) exists in two
   reviews and in no paper note. §6.7 depends on it. It costs no GPU time and needs a PN entry before
   it can be cited under hard rule "every number comes from an artifact".
5. **KV-cache quantization literature is absent from `references.bib`** (reviewer D §5.2) and §6.3
   now leans on it. Add QLLM-Eval and at least one KV-quantization method paper.
6. **`fig21c-coverage-matrix.csv` does not exist.** It is the one new data file this structure
   requires; generate it with `extract.py` from committed artifacts, never by hand.
7. **F4's claim line still overstates the split result.** `FIGURE-PROGRAMME.md:99` says the split set
   the window "for three of four arms"; PN-39 says **two of four** — UD-Q4_K_XL loads at the engine
   default and UD-Q6_K_XL was never attempted there at that length. The outline is correct at §6.1
   and §5's coverage table, and the abstracts are correct, but F4's caption is a binding artifact and
   the caption is what gets read. **Correct `FIGURE-PROGRAMME.md:99` to "two of four" before D4b**,
   and check F4-inset and T10's note for the same phrasing while there.
8. **The sigma range is now single-sourced to the code domain** (8.67 / 11.82 / 18.13 σ, §5.1). Sweep
   `README.md`, `CITATION.cff`, `TABLES.md` T23 and the figure captions for any surviving blended
   "3.7–11.8" used as a headline; T23 and §7 item 2 keep the prose figures, and those are the only
   two places they belong.

### 7.4 The test this outline must pass

A reader who reads only the eight essential figures and the subsection openers of §5 and §6 should be
able to say, unprompted: *this study ran nine instrument classes over eight checkpoints on three
backends for twelve days; the cheap token-level one separated the ladder in 2.32 GPU-hours and the
five expensive outcome-level ones did not; and most of the deployment leverage was on axes other
than the quantization.* If a draft section cannot be summarised into that sentence, it is in the wrong half of
the paper.

---

## 8. Repair log — 2026-09-04

*Applied against `REVIEW-V2.md` §6.4, items 2–8 and 11 plus the two non-blocking additions, and
against its §6.4 item 1 for every occurrence of the cost pair inside this file. Nothing protected by
`REVIEW-V2.md` §6.5 was touched: the two-part hybrid stands, §5 still orders by unit of observation,
§6 still orders by actionability, Appendix B still keeps all twelve register entries, §7 is still
drafted before §5 and §6 are polished, the eight ESSENTIAL figures are unchanged, and the coverage
table still routes all sixty-six notes.*

### What changed, and why

**Item 2 — one sigma range, and it is the code-domain one.** §1's argument paragraph and §5.1's
claim and first paragraph now quote **8.7–18.1 σ** for the three code-domain separations, with the
adjacent pairs named in the sentence (**8.67 σ** UD-Q6_K vs UD-Q5_K_XL, **11.82 σ** UD-Q5_K_XL vs
UD-Q4_K_XL) and the **18.13 σ** extreme identified as skipping a rung. The banned phrasing "every
adjacent pair … 8.7–18.1" is not used anywhere. The prose figures (3.71 / 8.48 / 13.48) survive in
exactly two places — T23 and §7 threat 2 — where the 3.71 adjacency is reported as the one
separation that does not survive clustering at design effect 1.5. §7 threat 2 now explains the
relationship between the two ranges rather than asserting a third. PN-13's row in the coverage table
keeps the note's own phrase, annotated, because rewriting it would misquote the note. New §7.3 item 8
sends the same sweep through `README.md`, `CITATION.cff`, T23 and the figure captions.

**Item 3 — four claim sentences rewritten out of "cannot" (STYLE-GUIDE §1.7).**

| where | was | is |
|---|---|---|
| §5.4 claim | "cannot see this damage for a structural reason" | "resolves this ladder no finer than 7.4 points at n=400 while the effect on it is 1.0 point, and the limit is structural" |
| §6.5 claim | "this host's variance cannot rank draft depths" | "this host's decode variance — reaching 166 % rep-to-rep — does not separate draft depths at three repetitions" |
| §4.3 | "free-running greedy generation cannot measure quantization distance" | "**does not resolve** quantization distance — … the metric returns the same value for every arm" |
| §4.3 | "KL divergence cannot be measured at long context on a 14 GiB host" | "KL divergence at long context **did not run** on a 14 GiB host, the tool … capping at `n_ctx` 8,192" |

§6.5's body sentence "the design cannot rank at n=3" became "does not separate the depths at n=3",
and §4.3's framing "found incapable of answering the question" became "did not answer the question".
The table shorthand at the coverage and figure-delta rows is left as the reviewer directed, with one
exception: F26's row is retitled because a figure title is a claim line, not shorthand.

**Item 4 — the weighting table recomputed, and the audit printed with it.** Every figure was
re-derived by summing §4's own targets rather than trusting the table. The as-written v2 document
was wrong in five places at once: the systems thread summed to 2,450 not 2,200, framing to 3,450 not
3,350, the two section opening blocks (300 w) were uncounted, the body totalled **16,600** not
15,950, and §5's header claimed 5,600 against subsections summing to 5,850 while §6's claimed 4,200
against 4,600. The appendix line was wrong too — "≈ 3,800" against §4's own A+B+C+D of 3,200. §3.1
now carries two tables: thread shares, and a section-by-section audit in which every §4 header
carries the same number as its row. Both sum exactly.

**Item 6 — a 13,500-word body target, with the levers named.** §2.3 item 6, §3.4 and §7.1 now say
**13,500 body words / ≈26 pages of body, ≈34 pages with appendices** — a **+18.9 %** departure from
`STYLE-GUIDE.md` §2.8's 11,350, not the +46 % v2 asked for by declaring the guide superseded. §3.4
prints all seventeen levers spent to get from the audited **16,600** to 13,500, each reversible on
its own, and keeps four in reserve. Appendix B moves from prose to a table with two-sentence rows
(1,300 → 1,000) without dropping an entry. §7.1 states the departure as earned by the nineteen notes
that carry body weight here and carried none in v1, rather than as a supersession.

**Item 5 — §5.5 split, §6.6 raised, both funded as the reviewer specified.** §5.5a *Generative
coding, the paired anchor* (400 w, F15 panel a, T8) carries the SSA S6 / S9b measurement and the
no-spec interlock with §6.4. §5.5b *The two historical ladders — seven configurations* (600 w, F15
panels b and c, T15) carries the non-thinking ladder with its context control and the seven-config
thinking ladder, and is added to §3.4's protected list because it is the half that compresses first
by default. §6.6 backends goes 600 → 750 for its four notes. Funded from §5.1 (900 → 750) and §6.4
(700 → 600), exactly as `REVIEW-V2.md` §1.3 prescribed; F15 gains a matching panel split. PN-28,
PN-40, PN-46 and PN-47 are re-routed in the coverage table, as are §2.2's ordering list and §5.2's
forward reference.

**Item 7 — §2 budgeted 810 + 90.** Three threads at 270 words, plus 90 for the section's own claim
sentence and its two transitions. The 900-word cap is unchanged and still hard.

**Item 8 — F4's claim line.** Added as §7.3 item 7: `FIGURE-PROGRAMME.md:99` says the split set the
window "for three of four arms" and PN-39 says **two of four**; the correction is scheduled before
D4b, with F4-inset and T10's note checked for the same phrasing.

**Item 11 — `DRAFTING-PLAN.md` D4 *and* D5.** D4 splits into **D4a** (§5, instruments) and **D4b**
(§6, axes); D6 and D7 now depend on D4b. D5 is renumbered off the v1 section numbers it still
carried — "§6 Cost, §8 Practitioner appendix, §9 Reproducibility appendix" becomes "§5.8 instrument
economics · Appendix A practitioner configuration · Appendix B reproducibility register", because §6
is now the configuration axes and the appendices are lettered A–D. A dated note above the table
explains the renumbering, and the companion-document map now names `OUTLINE-V2.md` as the live
structure with `OUTLINE.md` retained as the superseded record. This is the only file other than this
one that was edited.

**Item 1, this file's share — the cost pair.** Every occurrence inside this file is now T19's
**2.32 / 14.31 GPU-hours, 6.2×**, with the scope clause travelling with it: the 14.31 covers
**three instrument classes** — HellaSwag, HumanEval+ and RULER — and the perplexity work and the
four-day pre-E12 SWE-bench campaign sit **outside** it, which makes 6.2× a lower bound. Repaired at
§1's argument paragraph, §1's one-sentence summary ("five task instruments … three of them alone
costing 14.31"), §2.2's cost annotation, §3.2, §5.8's claim and body, §7.3 item 2, §7.4's acceptance
test and §8's conclusion. PN-67 is
cited as the supersession record. `ABSTRACT-V2.md`'s trap list is the abstract agent's item, not
this one.

**Non-blocking, both applied.** §5.7 now carries PN-52's cross-instance-set caveat on the ~45-step
column, flagged the way `FIGURE-PROGRAMME.md` already flags it for F17b. Appendix B's count is
written once as **"twelve register entries covering twenty-one defects"**, with the reason stated —
entry 12 *is* PN-58's ten historical defects, so "twelve defects" beside "the ten-defect audit"
reads as an arithmetic error. PN-58's coverage row is annotated to match, and §3.2's "twelve
instrumentation defects" is corrected to the same form.

### The corrected totals

| | as written in v2 | repaired |
|---|---|---|
| body | 15,950 claimed / **16,600** actual | **13,500** claimed and actual |
| §5 | 5,600 claimed / 5,850 actual | **5,000** claimed and actual |
| §6 | 4,200 claimed / 4,600 actual | **3,400** claimed and actual |
| appendices | ≈3,800 claimed / 3,200 actual | **2,900** claimed and actual |
| task benchmarks share | 3,000 / 19 % | **2,700 / 20 %** |
| divergence share | 2,800 / 18 % | **2,250 / 17 %** |
| systems share | 2,200 claimed / 2,450 actual | **1,900 / 14 %** |
| framing share | 3,350 claimed / 3,450 actual | **2,850 / 21 %** |
| speculative decoding share | 1,500 / 9 % | **1,050 / 8 %** |
| protocol and threats share | 3,100 / 19 % | **2,550 / 19 %** |
| section opening blocks | uncounted | **200 / 1 %** |

Task benchmarks still take the largest single results share and still exceed divergence — 20 %
against 17 % — so the owner's correction survives the repair rather than depending on the
arithmetic error. Every thread total is the sum of its subsections, every section header equals the
sum of its own subsections, the thread column sums to 13,500, and the share column sums to 100.

### Not changed, deliberately

- **Item 9** (write PN-67 for the acceptance-conditioned re-analysis before §6.7 cites it) and
  **item 10** (settle the checkpoint count at eight) are not this pass's items and remain open in
  §7.3. Note that PN-67 has since been taken for the sigma-range and cost-supersession record, so
  item 9's note needs the next free number, **PN-68**.
- Reviewer §2.5 item 4 (§6.5 quotes DFlash2 at 2.81× where T13 and PN-29 say 2.80×) was not in this
  pass's assignment and is left for the drafting pass; it is a one-character fix in §6.5.
- The compression levers were chosen so that §5.7, §6.4, §5.2 and §7 keep their v2 targets exactly,
  and §5.5b joins them on the protected list.
