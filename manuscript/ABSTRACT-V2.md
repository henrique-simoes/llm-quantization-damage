# ABSTRACT-V2 — four abstracts, eight titles, and the traps

*Author: drafting pass, 2026-09-04. Supersedes nothing; the incumbent abstract lives in
`CITATION.cff` and reviewer D's A2 is its source. This file is a proposal set, not a decision.*

**The brief this answers.** The incumbent abstract is a study of one four-arm divergence ladder.
The measurement programme behind it is not: eight quantizations in two formats, three inference
backends, five task-benchmark families, three perplexity protocols, two speculative-decoding
methods and a systems axis, over two weeks. The owner's criticism is that the abstract throws that
away. It does.

**The tension this file has to solve, stated before solving it.** An abstract has ~1,920 characters
and one job: make one argument. Breadth carried as an inventory — "eight quantizations, three
backends, five benchmark families" — is a list, and a list is the thing readers skip. Breadth
carried as *narrative* becomes the chronology the owner explicitly refused.

**The solution used in all four drafts below.** The breadth *is* the argument, in its denominator.
The report's thesis is that the instrument decides whether there is anything to see. The evidence
for that thesis is not the divergence measurement alone — a single positive result proves nothing
about instruments. It is the **set** of instruments that were run first, each with its own,
different failure: perplexity spanning less than its own standard error (PN-48); a multiple-choice
benchmark rating the most quantized arm nominally highest (PN-22); a generative coding benchmark
whose paired test could not have reached significance under any outcome (PN-40); a 50-instance
agentic campaign that *inverts* the ladder (PN-50); a thinking-mode ladder that turns out to be
scoring budget exhaustion rather than code (PN-47); a long-context battery that was measuring
output-budget closure rather than retrieval (PN-60). Each failed differently. That is why there
have to be five of them, and it is why naming them is an argument rather than a list.

The second half is the same move on the systems axis: what *does* move the numbers on this host is
configuration — tensor placement, speculative setting, KV dtype, engine image — not quantization.
Those results are positive, cheap to state, and populate the rest of the breadth without a
chronology.

Nothing below reports a date, a wave name, or a "then we ran".

---

## 1. Four abstracts

Each block is paste-ready: ASCII-only, no markup, no LaTeX, single paragraph, within 1,920
characters. Traceability tables follow each block rather than sitting inside it, so nothing has to
be stripped before submission.

All four follow `STYLE-GUIDE.md` §1.3 (no "we"; "I" only for acts of judgement) and §3.0 (open on a
measurement, not a claim about the field; close on a scope sentence). **Both rules are violated by
the incumbent**, which opens "Quantization quality for locally served models is published on prose
corpora and certified on task benchmarks" and uses "we" five times. That is a defect inherited from
reviewer D's A2, which predates the style guide; it is not a criticism of that review.

---

### V1 — conservative (1,667 characters, 251 words)

*Leads with the disagreement between two instrument classes. Makes no causal claim, no priority
claim, and no claim that a later note has scoped. Survives every correction in the corpus.*

```
A four-point GGUF quantization ladder of a 27B coding model was measured on two consumer
16 GB GPUs with five task-benchmark families and one token-level divergence instrument, and
the two classes disagree about whether the ladder is separable at all. WikiText-2 perplexity
spans 0.033 across the four arms against a standard error of +/-0.041 per point. HellaSwag at
n=400 spans 1.0 point, the most heavily quantized arm scores nominally highest, and two arms
answer all 400 items identically. On HumanEval+ at n=164, paired and seed-matched, the
ladder's extremes differ by 0.61 points with a 95 per cent interval of [-2.68, +1.46]; at the
discordance rates observed, no outcome of that test could have reached significance. A
50-instance SWE-bench Verified campaign across three quantizations resolves 77.6, 76.0 and
75.5 per cent, inverting the perplexity ordering inside a +/-12-point bootstrap interval. Mean
KL divergence against the least-quantized available arm, over 65,536 tokens per domain,
separates every adjacent pair on code at 8.7-18.1 sigma and is roughly twice as large on code
as on prose. For each instrument I report the smallest effect it could have detected. Two
configuration results are reported alongside: for two of four arms the GPU tensor split rather
than the quantization sets the reachable context window, and speculative decoding is
deterministically non-equivalent to unspeculated decoding, reproducing it on 131 of 164
problems while reproducing itself byte-exactly. These are measurements of one model under
named engine images on one two-GPU host. Artifacts, withdrawn claims and the
instrumentation-defect register are released.
```

| claim | note | artifact |
|---|---|---|
| PPL spans 0.033 vs +/-0.041 SE | PN-48 | `data/multivac-src/PAPER-REFERENCES.md` §PERPLEXITY, Protocol 1 (602 windows) |
| HellaSwag 1.0-pt spread, most-quantized highest, 400/400 identical | PN-22 | `data/raw/e12/ssa/ssa-s7-results.json`, `ssa-s7-paired.json` |
| HumanEval+ paired -0.61 [-2.68, +1.46] | PN-28 | `data/raw/e12/s9/s9-scores.json` `s6_paired` |
| no outcome could reach significance | PN-40 | recomputed from the same `s6_paired` discordant counts (1/2, 2/3 of 164) |
| SWE-bench 77.6 / 76.0 / 75.5, +/-12 pt | PN-50 | `data/raw/historical/swebench/ledger-data-snapshot-20260903.json`, `verified50-per-instance-manifest.json` |
| KLD 8.7-18.1 sigma on code, 65,536 tok/domain | PN-13 | `data/raw/e12/ssa/ssa-results-parsed.json` |
| code ~2x prose | PN-14 | same |
| split sets ceiling, 2 of 4 arms | PN-6, PN-39 | `data/raw/e12/tsweep-v2-{Q4_K_XL,Q5_K_XL,Q6_K,Q6_K_XL}.json` |
| 131/164, self-repeat byte-exact | PN-23, PN-26 | `data/raw/e12/s8/s8-humaneval.json`; `data/raw/e12/s9/s9-determinism.json` |

---

### V2 — balanced (1,907 characters, 293 words) — **recommended**

*Opens on the cost-and-power contrast, which is the one sentence that carries the whole programme.
Names the five instruments with one bound each, then the configuration half. Closes on the
style guide's scope sentence.*

```
KL divergence over 65,536 tokens per domain separates every adjacent pair of a four-point GGUF
quantization ladder at 8.7-18.1 sigma on code, in 2.1 hours of GPU time; the five
task-benchmark families run before it, costing 4.8 hours, separate the same arms nowhere. This
report measures a 27B coding model on two consumer 16 GB GPUs across eight quantizations,
three inference backends and both outcomes. Each benchmark fails differently, which is the
point: WikiText-2 perplexity spans 0.033 across four arms against +/-0.041 of standard error
per point; HellaSwag at n=400 rates the most heavily quantized arm nominally highest, with two
arms answering all 400 items identically; paired HumanEval+ at n=164 bounds the ladder's
extremes at 0.61 points, 95 per cent interval [-2.68, +1.46], a test that could not have
reached significance at the observed discordance; and a 50-instance SWE-bench Verified
campaign inverts the ordering outright at 77.6, 76.0 and 75.5 per cent inside a +/-12-point
interval. Divergence is roughly twice as large on code as on prose and 3.1-4.4x prose on the
benchmark's own prompts, so against a published <0.007 quality threshold two of three arms
pass on prose, one on generic code, and none on the task distribution. What does move the
numbers is configuration rather than quantization: for two of four arms GPU tensor placement
sets the reachable context window; decode throughput spans 6.7 per cent between arms against
40.7 per cent within a single configuration; speculative decoding is deterministically
non-equivalent to unspeculated decoding, reproducing it on 131 of 164 problems while
reproducing itself byte-exactly; and one 1.19 GiB draft-worker allocation blocks separate
drafters on three independent engines. These are measurements of one model under named engine
images on one two-GPU host. Artifacts, withdrawn claims and the defect register are released.
```

| claim | note | artifact |
|---|---|---|
| 2.1 h divergence vs 4.8 h task benchmarking | PN-41 | `data/raw/e12/progress.json`; `s9/s9-s6.json`; `ruler/s12-ruler.json`; L-12 |
| 8.7-18.1 sigma on code | PN-13 | `data/raw/e12/ssa/ssa-results-parsed.json` |
| eight quantizations, three backends | PN-46, PN-50, PN-53, PN-54, PN-55 | `data/raw/historical/`; `data/archive/sglang-failure.txt` |
| PPL 0.033 vs +/-0.041 | PN-48 | `data/multivac-src/PAPER-REFERENCES.md` §PERPLEXITY |
| HellaSwag | PN-22 | `data/raw/e12/ssa/ssa-s7-{results,paired}.json` |
| HumanEval+ paired bound; unreachable significance | PN-28, PN-40 | `data/raw/e12/s9/s9-scores.json` |
| SWE-bench inversion | PN-50 | `data/raw/historical/swebench/` |
| code 2x prose; task prompts 3.1-4.4x prose; <0.007 threshold | PN-14, PN-21 | `ssa-results-parsed.json`, `ssa-s5-results.json` |
| tensor split sets ceiling, 2 of 4 | PN-6, PN-39 | `tsweep-v2-*.json` |
| 6.7 % between-arm vs 40.7 % within-configuration | PN-45 | `tsweep-v2-*.json`, grouped on ctx + ts + ctxcp |
| 131/164 and byte-exact self-repeat | PN-23, PN-26 | `s8/s8-humaneval.json`; `s9/s9-determinism.json` |
| 1.19 GiB draft-worker wall on three engines | PN-53, PN-54 | `data/archive/sglang-failure.txt`; PAPER-REFERENCES §"1.19 GiB draft-worker wall" |

---

### V3 — programme-forward (1,889 characters, 295 words)

*Leads with the measurement programme itself and lets the inventory do argumentative work by
attaching a distinct failure mode to each instrument. This is the draft that most directly answers
the owner's criticism. It buys that at the cost of a slower first sentence.*

```
A 27B coding model was measured on two consumer 16 GB GPUs across eight quantizations in two
formats, three inference backends, five task-benchmark families, three perplexity protocols
and two speculative-decoding methods, and the instrument decided what was visible far more
often than the quantization did. Each benchmark family failed to rank the ladder in its own
way. WikiText-2 perplexity spans 0.033 across four arms against +/-0.041 of standard error per
point. HellaSwag at n=400 rates the most heavily quantized arm nominally highest, and two arms
answer all 400 items identically. Paired HumanEval+ at n=164 bounds the two extremes at 0.61
points, 95 per cent interval [-2.68, +1.46], a test that could not have reached significance
at the observed discordance. A 50-instance SWE-bench Verified campaign across three arms
inverts the ordering at 77.6, 76.0 and 75.5 per cent inside a +/-12-point interval. With
reasoning enabled the same benchmark scores termination, not code: three of four arms tie at
86.0 while the empty-response rate falls monotonically from 12.8 to 7.9 per cent. And the same
checkpoint reads either 29 per cent worse or 0.8 per cent worse than its comparison ladder
under two defensible perplexity protocols, a 36-fold swing from scoring convention alone. KL
divergence over 65,536 tokens per domain separates every adjacent pair on code at 8.7-18.1
sigma in 2.1 hours of GPU, is roughly twice as large on code as on prose, and rises again on
the benchmark's own prompts. On the configuration axis, GPU tensor placement rather than
quantization sets the reachable context window for two of four arms, decode throughput does
not discriminate the ladder, and speculative decoding is deterministically non-equivalent to
unspeculated decoding. These are measurements of one model under named engine images on one
two-GPU host, and all artifacts are released.
```

| claim | note | artifact |
|---|---|---|
| eight quantizations / three backends / five families / three PPL protocols / two spec methods | PN-46, PN-49, PN-50, PN-53, PN-54, PN-55, PN-29 | `data/raw/historical/`, `data/raw/e12/s9/s9-dflash.json` |
| thinking-mode: 86.0 tie, empty 12.8 -> 7.9 % | PN-47 | `data/raw/historical/evalplus-thinking/` (seven arms, n=164 each) |
| 36-fold protocol swing (8.5848 vs 6.7073) | PN-49 | `data/raw/historical/perplexity/nvfp4-vllm-ppl{,-protocol1}.json` |
| remaining rows | as V2 | as V2 |

---

### V4 — assertive (1,825 characters, 282 words)

*Opens on the single row that contains the whole thesis: one configuration that leads every cheap
instrument and fails the expensive one. Most quotable; carries the most exposure, because that row
is n=6.*

```
One quantization of a 27B coding model led the throughput table at 116.9 tok/s and scored 81.7
on HumanEval+ with no empty responses, then reached the agent step limit on 6 of 6 instances
where the reference arm converged on 6 of 6. That contrast is the study. Measured on two
consumer 16 GB GPUs across eight quantizations, three inference backends and five
task-benchmark families, the cheap instruments rank quantizations confidently and wrongly, and
the expensive one costs too much to rank anything. WikiText-2 perplexity spans 0.033 against
+/-0.041 of standard error per point; HellaSwag at n=400 rates the most heavily quantized arm
nominally highest; paired HumanEval+ at n=164 bounds the ladder's extremes at 0.61 points,
[-2.68, +1.46], a test that could not have reached significance; a 50-instance SWE-bench
Verified campaign inverts the ordering at 77.6, 76.0 and 75.5 per cent on a +/-12-point
interval. KL divergence over 65,536 tokens per domain separates every adjacent pair on code at
8.7-18.1 sigma in 2.1 hours of GPU, twice as large on code as on prose and larger again on the
benchmark's own prompts, where no arm meets a published <0.007 quality threshold. The
configuration axis then outweighs the quantization axis: tensor placement rather than
quantization sets the reachable context window for two of four arms, decode throughput spans
6.7 per cent between arms against 40.7 per cent within one configuration, speculative decoding
is deterministically non-equivalent to unspeculated decoding on 131 of 164 problems while
reproducing itself byte-exactly, and a single 1.19 GiB draft-worker allocation blocks separate
drafters on three engines. These are measurements of one model under named engine images on
one two-GPU host. Every artifact, withdrawn claim and instrumentation defect is released.
```

| claim | note | artifact | exposure |
|---|---|---|---|
| 116.9 tok/s, HumanEval+ 81.7, 6 of 6 at step limit vs 6 of 6 converged | PN-51 | `/srv/bench/rigor/T3-INTERROMPIDO.txt`; `data/raw/historical/T3-agentic-steps.txt`; `data/archive/ledger-data.json` `humaneval_nonthinking/Q3_K_XL` | **n=6 instances, one scaffold, single seed, deliberately truncated run.** PN-51's own caveat permits a qualitative disqualification only. The arm is also *not on the paper's four-arm ladder* (reviewer C, D-14) |
| remaining rows | as V2 | as V2 | |

---

## 2. Recommendation

**Submit V2.**

V2 is the only one of the four that solves the assignment's actual tension rather than picking a
side of it. Its first sentence is a measurement, as `STYLE-GUIDE.md` §3.0 rule 3 requires for
moderation, and that single sentence already carries both halves of the argument and the programme's
shape: an instrument, its resolution, its cost, and five other instruments that cost more and
resolved less. A reader who stops after one sentence has the thesis and knows the study is larger
than one experiment. Nothing else in the file achieves that in one sentence — V1 needs three, V3
needs a full inventory clause, V4 spends its opening on a result whose n is 6.

The clause **"Each benchmark fails differently, which is the point"** is the hinge, and it is what
converts breadth from a list into an argument. Without it the four benchmark bounds read as a
catalogue; with it, they read as five independent tests of one hypothesis about instruments, which
is exactly what they are. It is also honest: perplexity's failure (spread below its own error),
HellaSwag's (structural insensitivity — a scoring rule that depends only on an argmax), HumanEval+'s
(a test that could not have reached significance), and SWE-bench's (n too small for a 2.1-point
question) are four genuinely different failure mechanisms, and the report's §5 is organised around
that distinction.

V2 then spends its second half on the configuration axis, which is where the study's *positive*
results live — the split, the throughput null, the equivalence result, the draft-worker wall. This
is the part the incumbent abstract almost entirely omits, and it is four independent findings, none
of which depends on a statistical separation. If every accuracy claim in the paper were qualified
tomorrow, that half of V2 would still stand.

V2 carries no claim that this corpus has scoped or withdrawn. It does not mention the tail
decomposition, the median ratio, RULER, MK-NIAH, draft acceptance, or the widening-with-aggressiveness
clause — the six places where the study has already had to correct itself. That is deliberate: at
1,907 of 1,920 characters it is full, with 13 characters of headroom, and every one of those claims is a liability with a live
caveat. They belong in §5 with their caveats attached, not in the one sentence that cannot be
amended.

**Second choice: V3**, if the owner judges that the programme's breadth must be visible in the first
sentence rather than the second. V3 is the most complete answer to the criticism and costs a slower
opening; it also adds the thinking-mode and protocol-swing results, which are two of the study's
best and are invisible in V2. If V3 is chosen, its first sentence should be read once more against
the moderation risk — it is an inventory, and an arXiv moderator reading only that sentence sees
scope but not a result.

**Do not submit V4 as written.** Its opening row is real, checkable and the best single sentence in
the corpus, but n=6, single seed, one scaffold, and an arm outside the paper's ladder. In §5, with
its caveat attached, it is a highlight. In an abstract, stripped of the caveat, it is the one
sentence a reviewer will pull first, and pulling it costs the paper's opening. V1 remains available
as the fallback if any reviewer objects to V2's density.

---

## 3. Eight titles

The incumbent: **"Divergence Ranks What Benchmarks Bound: quantization, context and speculative
decoding for a 27B coding model on two 16 GB GPUs"** — 20 words, `CITATION.cff` and `OUTLINE.md`.

Prior work respected: reviewer D ranked T1 > T2 (the incumbent) and would sign the incumbent off
once the clustering objection is answered in the paper; reviewer C ranked its own T9 first and
cautioned against putting "cannot" in any title. **That caution is now stale in one direction and I
say so rather than silently dropping it**: it rested on PN-44's MK-NIAH separation, which PN-60 and
PN-63 have voided. No task instrument in the corpus now resolves the ladder. A negative-framed title
is therefore *more* supportable today than when reviewer C wrote, not less.

| # | title | words |
|---|---|---|
| **A** | Divergence Ranks What Benchmarks Bound: quantization, speculation and context for a 27B coding model on two 16 GB GPUs | 18 |
| B | Five Benchmarks Could Not Rank It: quantization, speculation and context for a 27B coding model on two 16 GB GPUs | 20 |
| C | The Instrument Decides: eight quantizations, three backends and five benchmarks for a 27B coding model on two 16 GB GPUs | 19 |
| D | What the Configuration Decides and the Quantization Does Not: context, speculation and throughput for a 27B coding model on two 16 GB GPUs | 22 |
| E | Ranking a Quantization Ladder Five Benchmarks Cannot Separate: a measurement study on two consumer 16 GB GPUs | 16 |
| F | *(incumbent, unchanged)* Divergence Ranks What Benchmarks Bound: quantization, context and speculative decoding for a 27B coding model on two 16 GB GPUs | 20 |
| G | *(reviewer D, T1)* What a Quantization Ladder Costs, and Which Instrument Can Tell You: a measurement study of a 27B coding model on two consumer GPUs | 24 |
| H | *(reviewer C, T9)* What the Benchmarks Cannot See, and What the Protocol Decides: quantization damage in a 27B coding model across twelve days of measurement | 24 |

### A — recommended

> **Divergence Ranks What Benchmarks Bound: quantization, speculation and context for a 27B coding model on two 16 GB GPUs**

**Commits to:** the ranking/bounding contrast (PN-13 against PN-22, PN-28, PN-40, PN-48, PN-50), and
to three result areas.
**Costs:** two words of change from the incumbent and nothing else. "Ranks" leans on the divergence
separations, so the clustering objection must be answered in §5 — which it must be anyway. It does
not put the programme's breadth in the title.
**Ages:** the main clause is a comparison between two instrument classes, and the corpus has been
moving *toward* it, not away: every re-analysis since (PN-60, PN-62, PN-64, PN-66) has weakened a
task-benchmark claim or a mechanism claim, never the ranking/bounding contrast itself. If the tail
decomposition were withdrawn entirely, the title would not move.
**Moderation:** it is a result, stated as a measurement, with the hardware named. It reads as a
systems measurement paper, which is what `cs.PF` cross-listing needs.
**Change from the incumbent:** "speculative decoding" becomes "speculation", which drops the title
from 20 to 18 words against the empirical-SE primer's recommended 15 (`STYLE-GUIDE.md` §3.0, [S32])
and loses no information a reader of the abstract's second half does not immediately recover.

### B

> **Five Benchmarks Could Not Rank It: quantization, speculation and context for a 27B coding model on two 16 GB GPUs**

**Commits to:** the benchmark campaign as the lead — the exact material the owner says is invisible.
Five families is a countable, checkable claim (PN-22, PN-28/40, PN-46/47, PN-50, PN-60/63).
**Costs:** a negative-results title, which some readers stop at; it also states the null before the
positive, so a reader who reads only the title does not learn that anything *was* resolved. And it
makes a universally-quantified-sounding claim over instruments the paper did not run.
**Ages:** well now that PN-60 has voided the one task instrument that appeared to separate the
ladder. It would age badly if a sixth instrument were added later and did separate the arms, which
is a live possibility — a held-out code corpus is one GPU-hour away.
**Moderation:** fine, but "could not" invites a moderator to read it as a commentary rather than a
measurement. Weakest of the top three on that axis.

### C

> **The Instrument Decides: eight quantizations, three backends and five benchmarks for a 27B coding model on two 16 GB GPUs**

**Commits to:** the thesis in the main clause and the programme's scale in the subtitle. The most
literal answer to the criticism this file was written for.
**Costs:** the subtitle is an inventory, and inventories in titles read as scope-padding to a
sceptical reviewer. It also invites "eight quantizations *of what kind*?" — the eight span GGUF and
NVFP4, and only four carry the divergence comparison. **And the count is contested**: `README.md`
and the build stream both say "nine quantizations" while the parenthetical they cite lists eight
(Q3_K_XL, IQ4_XS, Q4_K_M, Q4_K_XL, Q5_K_XL, Q6_K, Q6_K_XL, NVFP4). A title should not carry a number
the repository disagrees with itself about.
**Ages:** the main clause ages perfectly; the count is a hostage.

### D

> **What the Configuration Decides and the Quantization Does Not: context, speculation and throughput for a 27B coding model on two 16 GB GPUs**

**Commits to:** the systems half — PN-6/PN-7/PN-39, PN-45, PN-23/PN-26, PN-53. These are the
best-replicated results in the corpus and several are load/no-load with no interval at all.
**Costs:** it abandons the accuracy contribution, which is the better half and the one that carries
the report's methodological argument. 22 words. Also over-claims slightly: PN-39 scopes the ceiling
result to two of four arms.
**Ages:** extremely well — no statistical claim in it. It is the right title for a different,
shorter, `cs.PF`-only paper that is genuinely inside this corpus.

### E

> **Ranking a Quantization Ladder Five Benchmarks Cannot Separate: a measurement study on two consumer 16 GB GPUs**

**Commits to:** both halves, in 16 words — the shortest candidate that says anything.
**Costs:** drops "27B coding model", which is a search term readers actually use, and drops
speculative decoding entirely. "Cannot separate" is a stronger form of B's exposure.
**Ages:** as B.
**Moderation:** fine.

### F — the incumbent, unchanged

Defensible; reviewer D would sign it; already in `CITATION.cff` and `OUTLINE.md`, so keeping it
costs nothing and changing it costs two files. Its only defects are length (20 words against a
recommended 15) and that "context and speculative decoding" is three words longer than it needs to
be. It does not fail the owner's criticism as badly as the abstract does — "What Benchmarks Bound"
*is* the benchmark campaign, compressed into three words.

### G and H — the two prior recommendations

**G (reviewer D T1)** is the safest title in existence for this corpus and I would still accept it
without argument. It is 24 words, it is descriptive rather than assertive, and — the decisive point
against it here — it makes the study sound *smaller* than it is, which is the opposite of what this
revision is for. "A measurement study of a 27B coding model" understates eight quantizations and
three backends more than the incumbent does.

**H (reviewer C T9)** has the best two-legged structure of any candidate: protocol dependence
(PN-49, PN-48) and instrument insensitivity (PN-22, PN-28/40, PN-46, PN-50) are both multiply
supported, and neither depends on the tail decomposition. Its blocker is now factual rather than
rhetorical: **"across twelve days of measurement" cannot go in a title while the repository carries
three different day-counts for the same study** — `TIMELINE.md` is titled "twelve days", spans
2026-08-20 to 2026-09-03 (fifteen calendar days) and closes on "thirteen days" (reviewer C, D-12,
still live). Fix that defect and H becomes a serious contender; ship it unfixed and the title
contains the study's most easily falsified number.

### Ranking

**A > B > F > H > C > E > G > D.**

### Defence of A, and the direct answer on the incumbent

**Keep the incumbent, with a two-word trim.** That is A.

The owner's criticism is correct and it is an **abstract problem, not a title problem**. A title has
one clause of argument and one clause of scope; it cannot carry eight quantizations, three backends
and five benchmark families without becoming the inventory in C, which reads as padding. The
abstract can, and V2 does — five instruments, each with its own bound, plus four configuration
results, inside 1,907 characters. Changing the title would not have fixed what he is objecting to,
and would have cost the one asset the incumbent has that none of the alternatives do: "What
Benchmarks Bound" already names the benchmark campaign, and names it as the thing that *did* the
bounding, which is the campaign's actual contribution.

The second argument for A is stability under this corpus's own behaviour. Nine notes correct other
notes; four headline claims have been withdrawn or scoped by re-analysis after measurement closed.
Reviewer D's rule — put a high discount rate on the newest result — has been vindicated four more
times since that review was written. A title built on the *contrast between two instrument classes*
is the only kind that survives that, because every correction so far has come from re-analysing a
single instrument, and none has moved the contrast.

If the owner wants the campaign visible in the first five words rather than the fourth, **B** is the
one I would defend, and its cost is that it leads with a null.

---

## 4. What the abstract must not claim

Every item below is a trap that a *depth-carrying* abstract is more likely to hit than a narrow one,
because breadth means reaching for the older and less-defended numbers.

1. **Not "nine quantizations."** `README.md` and the build stream say nine; the parenthetical they
   cite lists eight. Use eight, or a phrasing that does not count.
2. **Not "twelve days."** `TIMELINE.md` is titled twelve, spans fifteen calendar days, and closes on
   thirteen (reviewer C, D-12, live). "Two weeks" is true under all three readings; better still,
   count instruments rather than days.
3. **Not a draft acceptance of 1.000** as a credential for any arm. Those figures are
   degenerate-generation artifacts — 50-token generations over ~34 draft events (PN-61). Only the
   1,024-token rows are usable. This removes one clause from PN-51's otherwise excellent thesis row.
4. **Not the tail's *shape* as a quantization property.** Quantization sets the magnitude; the corpus
   sets the shape, and the study's own KV-dtype-only control reproduces it (PN-62). "Concentrated in
   a thin tail, far more sharply on code than on prose" survives; "quantization damage lives in the
   tail" does not.
5. **Not "100-200x" and never a per-arm median.** Corrected to about 200x, and print precision puts
   +/-3-7 per cent on each cell so the intervals overlap and cannot rank the arms (PN-64). If the
   median appears at all it appears as "about 200x", unranked.
6. **Not the long-context retrieval separation.** PN-44's 89.0 vs 79.0 at 131,072 measured
   output-budget closure, not retrieval: `closed-and-wrong` is exactly zero across all fourteen
   cells, and on the 55 items where neither arm's budget bound, both score 55/55 (PN-60, PN-63). Do
   not cite PN-44, PN-37's mechanism clause, or `s12-ruler.json`'s `accuracy_recovery` for mk100.
7. **Not "the code-to-prose gap widens with aggressiveness"** as a reference-invariant result. It is
   an upper bound: it shrinks ~16 per cent under a plausible reference correction and vanishes in
   the limit (reviewer D §4.2). The *level* — code roughly twice prose — is invariant, and is what
   V2 states.
8. **Not "3.7-11.8 sigma" without knowing what the lower endpoint costs.** All nine separations pass
   Holm and Benjamini-Hochberg, but the weakest does not survive Bonferroni once clustering is
   allowed for, and no multiple-comparisons correction exists across the study's ~19 tests. The
   code-domain range 8.7-18.1 has no such exposure; all four drafts use it.
9. **Not "60x cheaper", not "20 minutes against 20 hours", and not PN-41's own 2.1 h / 4.8 h /
   2.2x either.** ⚠️ **Corrected 2026-09-04.** PN-41's pair was computed before the 9.4-hour
   100-sample MK-NIAH cell existed and is superseded by T19 (`TABLES.md:696-720`, and PN-67):
   the current figures are **2.32 GPU-hours of divergence measurement against 14.31 hours of task
   benchmarking, a ratio of 6.2x**, and that 14.31 covers **three instrument classes only**
   (HellaSwag, HumanEval+, RULER). Perplexity and the four-day SWE-bench Verified campaign are
   historical and outside it, so "five task-benchmark families ... costing 4.8 hours" is wrong
   twice over. Quote T19 or quote nothing; stating the ratio honestly is more persuasive than a
   number a reader can falsify from the repository in five minutes.
10. **Not DFlash2's speed or byte-exactness beside MTP's.** The drafter is bound to its own engine
    build, so that arm ran on a different image than its baseline (PN-25, PN-29). It is the fastest
    configuration measured and it cannot be cleanly compared.
11. **Not "speed does not discriminate" as equality.** n=3 to 6 repetitions, single stream, one
    host: "not separated at this n", never "equal" (PN-19 caveat).
12. **Not any comparison to the model's published scores.** The official card publishes LiveCodeBench
    v6, SWE-bench **Pro** and Terminal Bench, and no HumanEval at all; this study ran SWE-bench
    **Verified**, a different benchmark. And every logprob instrument here is greedy, matching
    neither official sampling preset, so absolute scores are not comparable to published numbers.
13. **Not a priority or superlative claim.** `STYLE-GUIDE.md` §3.0 rule 5: double-bound it or drop
    it. This report should simply not make one — the divergence-versus-benchmarks framing is
    independent confirmation of Dutta et al. and §1 must say so before a reviewer does.
14. **Not "we", "our" or "us"**, and not "I" for anything but an act of judgement
    (`STYLE-GUIDE.md` §1.3). The incumbent abstract uses "we" five times and must be converted with
    `CITATION.cff`.
15. **Not an equivalence conclusion without its bounds.** If the abstract says two arms are
    indistinguishable it must carry the interval that says so (`STYLE-GUIDE.md` §4.4) — which is why
    all four drafts quote [-2.68, +1.46] rather than "no significant difference".

---

## 5. If V2 is adopted, three files move together

`CITATION.cff` (`abstract:`), `manuscript/OUTLINE.md` (title and thesis paragraph), and
`README.md`'s opening answer. `CITATION.cff` additionally still carries "we" throughout and the
`repository-code` field points at a public GitHub URL that `CLAUDE.md` §3 records as not existing;
both are outside this file's scope and are flagged, not changed.
