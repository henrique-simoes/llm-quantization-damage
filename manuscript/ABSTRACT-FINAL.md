# ABSTRACT-FINAL — the submission abstract, the title decision, and what neither may claim

*Author: final pass, 2026-09-04. This file supersedes `ABSTRACT-V2.md` §1-§3 as the decision;
`ABSTRACT-V2.md` remains on disk as the proposal set and its reasoning is not repeated here.
Every number below was re-verified against the artifact its paper note names, not against prose in
any review. `REVIEW-V2.md` §6.3's corrected V2 was the starting point and is **not** what is
recommended: it carries two further wrong figures of its own, found here.*

---

## 0. What changed, and why anyone should read past the abstract

`REVIEW-V2.md` §6.2 rejected V2-as-written for two defects (a superseded cost pair, a sigma range
whose upper endpoint is not an adjacent pair) and supplied a corrected V2 at 1,914 characters.
Both repairs are correct and both are kept.

Verifying the corrected draft character by character against the artifacts turned up **three more
defects that survived four blind reviews and the adversarial pass**:

| # | in the corrected V2 | the artifact says | severity |
|---|---|---|---|
| 1 | "paired HumanEval+ ... 95 per cent interval **[-2.68, +1.46]**" | that interval is the **base**-tests row. The **plus** row — the one the sentence names — is **[-3.28, +2.06]** (PN-40's table; `TABLES.md:184-185`, `:248-249`; T19 quotes the plus row too) | **blocking.** A metric labelled with another metric's interval, in the one text that cannot be amended |
| 2 | "one 1.19 GiB draft-worker allocation **blocks separate drafters on three independent engines**" | it blocks on **two of three**. `PAPER-REFERENCES.md:290-297` and PN-53's own evidence table: SGLang OOM, vLLM OOM, **llama.cpp succeeds** at 38.51 tok/s with a 4-bit GGUF drafter. PN-53's headline sentence ("three independent inference stacks hit the same failure") contradicts its own table and is the source of the error | **blocking.** It converts a two-of-three deployment finding into a false universal |
| 3 | "three inference backends" stated flat | one of the three (SGLang 0.5.18) **produced no measurement of any kind** (PN-54). Counting it silently is the kind of scope inflation the report's own §Threats section forbids | material |

Defect 2 is worth naming as a pattern, because it is the corpus's own failure mode a fourth time:
**a note's headline sentence generalising past its evidence table.** PN-53 says three, shows two.
The abstract inherited the headline, not the table. The same shape produced PN-19 to PN-36 to
PN-45, PN-6 to PN-39, and PN-44 to PN-60.

Defect 3 is repaired by turning the omission into a result: the recommended draft says the wall
blocks "a separate drafter on two of three engines, one of which never served a request." That is
eleven words carrying PN-53, PN-54 and the honest backend count at once.

---

## 1. The recommended abstract

**1,910 characters, 296 words. ASCII-clean (every codepoint in 32-126). Single paragraph, no
markup, no LaTeX, no em dash, no typographic quote. 10 characters of headroom against arXiv's
1,920.** Counts are mechanical: whitespace-joined, `len()`, and a codepoint screen; they are
reproducible from the block below.

```
KL divergence over 65,536 tokens per domain separates the three quantized arms of a GGUF ladder from one another on code at 8.7-18.1 sigma in 2.3 GPU-hours; three task-benchmark instrument classes costing 14.3 hours separate the same arms nowhere. This report measures a 27B coding model on two consumer 16 GB GPUs across eight quantizations, three inference backends and five benchmark families. Each benchmark fails differently, which is the point: WikiText-2 perplexity spans 0.033 across four arms against +/-0.041 of standard error per point; HellaSwag at n=400 rates the most heavily quantized arm nominally highest, two arms answering all 400 items identically; paired HumanEval+ at n=164 bounds the ladder's extremes at 0.61 points, 95 per cent interval [-3.28, +2.06], a test no outcome could have made significant at the observed discordance; and a 50-instance SWE-bench Verified campaign inverts the ordering at 77.6, 76.0 and 75.5 per cent inside +/-12 points. Divergence is roughly twice as large on code as on prose and 3.1-4.4x prose on the benchmark's own prompts, so against a published <0.007 quality threshold two of three arms pass on prose, one on generic code, and none on the task distribution. What moves the numbers is configuration, not quantization: for two of four arms GPU tensor placement sets the reachable context window; decode throughput spans 6.7 per cent between arms against 40.7 per cent within one configuration at three repetitions; speculative decoding is deterministically non-equivalent to unspeculated decoding, reproducing it on 131 of 164 problems while reproducing itself byte-exactly; and one 1.19 GiB draft-worker allocation blocks a separate drafter on two of three engines, one of which never served a request. These are measurements of one model under named engine images on one two-GPU host. Artifacts, withdrawn claims and the defect register are released.
```

### 1.1 Why this shape and not another

The assignment's tension is real: an abstract has one job, and twelve days across eight
quantizations, three backends and six benchmark families is not one job. The previous author's
solution survives scrutiny and is kept — **the breadth is the argument's denominator.** One
instrument separating a ladder establishes nothing about instruments in general; a *set* of
instruments that each failed in a different way, followed by one that did not, is an argument, and
the count is what makes it one. That is why "Each benchmark fails differently, which is the point"
is the hinge sentence and why four bounds follow it rather than a summary.

Two improvements on that reasoning were made here.

**The failures are now genuinely four different mechanisms, and the sentence order makes that
checkable.** Perplexity fails by *resolution* (spread below its own standard error). HellaSwag
fails by *construction* (an argmax over a handful of candidates is insensitive to distribution
shift, which is why the most quantized arm can score nominally highest and two arms can agree on
400 of 400 items). HumanEval+ fails by *power* (the discordant count, not n, sets the smallest
detectable effect, and at 5 discordant pairs no outcome reaches p < 0.05). SWE-bench Verified fails
by *sample size at cost* (2.1 points of spread where one instance is worth two points, on the most
expensive instrument in the study). A reader who checks them finds four distinct failure modes,
not one restated four times.

**The second half is load-bearing, not decoration.** Four configuration results — the split, the
throughput null with its noise floor, the speculative non-equivalence, the draft-worker wall — are
load/no-load or byte-exact findings that survive any future qualification of the accuracy half. If
every divergence claim in the paper were scoped tomorrow, that half of the abstract would stand
unchanged. It is also the half that answers the owner directly: it is where speculative decoding
and token-generation throughput appear, and neither comes from the final wave alone.

### 1.2 What was deliberately left out, and the character cost of putting it back

| omitted | why | cost to add |
|---|---|---|
| the thinking-mode ladder (PN-47: three of four arms tie at 86.0, empty rate 12.8 -> 7.9 %) | one of the study's best results, but it needs the "budget exhaustion, not code" clause to be honest, and that clause is a sentence | ~180 chars |
| the 36-fold perplexity-protocol swing (PN-49) | equally good, equally in need of its "two defensible protocols" qualifier | ~200 chars |
| the tail decomposition (PN-35/PN-62/PN-64) | three live corrections attached; the abstract is the one place a caveat cannot follow the claim | n/a - excluded on principle |
| RULER / long-context (PN-60, PN-63) | the retrieval reading is void and the surviving reading (single-needle saturation) is a null about an instrument, not about the ladder | n/a - excluded on principle |
| draft acceptance figures | degenerate-generation artifacts in the historical corpus (PN-61) | n/a - excluded on principle |
| "twelve days" | the repository carries twelve, thirteen and fifteen for the same span | n/a - counted instruments instead |

Only the first two are recoverable, and only by removing something. With 10 characters of headroom
they are not recoverable here. `ABSTRACT-V2.md`'s V3 is the draft that carries both, and if the
owner wants them the exchange is explicit: V3 with defects 1-3 above repaired, at the price of an
opening sentence that is an inventory rather than a measurement — which is the one thing
`STYLE-GUIDE.md` §3.0 rule 3 and the 2025-10-31 arXiv policy both press against.

---

## 2. Traceability — every claim to its note to its artifact

Each row was checked against the artifact, not against a review. "Verified" means the figure in the
abstract appears in the named artifact or paper note in that exact form.

| # | claim as it appears in the abstract | note | artifact | verified |
|---|---|---|---|---|
| 1 | KL divergence over 65,536 tokens per domain | PN-13 | `data/raw/e12/ssa/ssa-results-parsed.json`, n_ctx 2048 x 32 chunks per cell | yes |
| 2 | separates the three quantized arms **from one another on code** at **8.7-18.1 sigma** | PN-13, PN-67, T23 | `ssa-results-parsed.json`; code means 0.005829 / 0.010285 / 0.021529 with errors 0.000233 / 0.000458 / 0.000834 -> 8.67, 11.82, 18.13 sigma | yes - and see §4 note 1 |
| 3 | in **2.3 GPU-hours** | T19 (supersedes PN-41) | `manuscript/figures/data/fig19-cost.csv`; SSA S0-S4 1.95 h + S5 0.37 h = **2.32 h**, 14 cells | yes |
| 4 | **three task-benchmark instrument classes** costing **14.3 hours** separate the same arms nowhere | T19, PN-67 | same; S7 HellaSwag 0.54 + S6 HumanEval+ 1.29 + S12 RULER 12.34 + excluded VT 0.14 = **14.31 h**, 20 cells. Ratio **6.2x** | yes |
| 5 | eight quantizations | PN-46, PN-50, PN-55, T1 | Q3_K_XL, IQ4_XS, Q4_K_M, Q4_K_XL, Q5_K_XL, Q6_K, Q6_K_XL, NVFP4 | yes - `README.md` corrected to eight |
| 6 | three inference backends, **one of which never served a request** | PN-53, PN-54 | `data/archive/sglang-failure.txt`; `engines/diag-tp{1,2}-ctx8k.log`. SGLang 0.5.18 failed to start at 131,072 / 65,536 / 32,768 / 16,384 | yes |
| 7 | five benchmark families | PN-48, PN-22, PN-28, PN-50, PN-60/63 | perplexity, HellaSwag, HumanEval+, SWE-bench Verified, RULER | yes - distinct from row 4's three *timed* classes; see §4 note 2 |
| 8 | WikiText-2 perplexity spans **0.033** against **+/-0.041** SE per point | PN-48 | `data/multivac-src/PAPER-REFERENCES.md` §PERPLEXITY, Protocol 1, 602 windows: 6.6511 / 6.6556 / 6.6617 / 6.6839, each +/-0.0411-0.0413 | yes |
| 9 | HellaSwag **n=400**, most quantized arm nominally highest, **two arms answering all 400 items identically** | PN-22 | `ssa-s7-results.json` 82.75 / 82.25 / 82.75 / 83.25; `ssa-s7-paired.json` b=0, c=0 for Q6_K_XL vs Q5_K_XL | yes |
| 10 | paired HumanEval+ **n=164**, extremes at **0.61 points**, **[-3.28, +2.06]** | PN-28, PN-40 | `s9/s9-scores.json` `s6_paired`; PN-40's table, **plus** row, 5 discordant (2 vs 3) | **corrected here** - V2 quoted the base row's [-2.68, +1.46] |
| 11 | a test no outcome could have made significant at the observed discordance | PN-40 | minimum achievable exact two-sided p at 5 discordant pairs = **0.0625** | yes |
| 12 | 50-instance SWE-bench Verified inverts the ordering at **77.6, 76.0, 75.5** per cent inside **+/-12 points** | PN-50 | per-instance `report.json` via `swebench_agg.py`; 38/49, 38/50, 37/49; bootstrap B=10,000 seed 20260825: 75.51 [63.27, 87.76] | yes |
| 13 | divergence roughly **twice** as large on code as on prose | PN-14 | ratios 1.75x / 2.30x / 2.62x, same cells | yes - level only, never the widening (§4 note 5) |
| 14 | **3.1-4.4x** prose on the benchmark's own prompts | PN-21 | `ssa-s5-results.json`, 164 HumanEval+ prompts, 18,432 tokens/cell: 3.13 / 3.87 / 4.40 | yes |
| 15 | against a published **<0.007** threshold, two of three pass on prose, one on generic code, **none** on the task distribution | PN-21 (threshold external, Fireworks) | same; cited for interpretation, never adopted as this study's pass/fail rule | yes |
| 16 | **two of four arms**: GPU tensor placement sets the reachable context window | PN-6, **PN-39** | `data/raw/e12/tsweep-v2-{Q4_K_XL,Q5_K_XL,Q6_K,Q6_K_XL}.json` | yes - two, not three (`FIGURE-PROGRAMME.md:99` still says three; fix before D4b) |
| 17 | throughput **6.7 %** between arms against **40.7 %** within one configuration **at three repetitions** | PN-45 | `tsweep-v2-*.json` grouped on arm + ctx + `-ts` + `-ctxcp`; estimator (max-min)/median throughout | yes - the n qualifier is required: two arms are medians of three, one arm is a single reading |
| 18 | speculative decoding deterministically non-equivalent; **131 of 164**; reproduces **itself** byte-exactly | PN-23, PN-26 | `s8/s8-humaneval.json` (79.88 %, median first difference at char 715/730); `s9/s9-determinism.json` (md5 identical, 164/164) | yes |
| 19 | one **1.19 GiB** draft-worker allocation blocks a separate drafter on **two of three** engines | PN-53, PN-54 | `sglang-failure.txt`; `PAPER-REFERENCES.md:290-297` - SGLang OOM, vLLM OOM at every util 0.78-0.97 and every ctx 3K-16K, **llama.cpp succeeds** 38.51 tok/s, acceptance 0.714 | **corrected here** - V2 said three |
| 20 | measurements of one model under named engine images on one two-GPU host | PN-57, T1 | `env-manifest.json`; image `sha256:feb0231976b6...` | yes |
| 21 | artifacts, withdrawn claims and the defect register are released | T20, T21, R14/R15 | `TABLES.md` T20 (twelve register entries), T21 (sixteen corrections) | yes |

---

## 3. `CITATION.cff` — the exact replacement block

`CITATION.cff`'s incumbent `abstract:` violates two binding rules and must not ship: it uses
**"we" five times** (`STYLE-GUIDE.md` §1.3 bans we/our/us outright) and it **opens on a claim about
the field** — "Quantization quality for locally served models is published on prose corpora and
certified on task benchmarks" — where §3.0 rule 3 requires the opening to be a measurement. It also
carries the two figures §0 corrects: "separates **every adjacent pair** on code at 8.7-18.1 sigma"
(PN-67: the 18.13 endpoint skips a rung) and "**cannot** resolve below it" (§1.7 bans "cannot" of
an instrument). It predates the style guide; replacing it is not a criticism of reviewer D's A2.

Replace lines 4-24 of `CITATION.cff` — the `abstract: >-` key and its folded block, up to but not
including `type: dataset` — with exactly this. Two-space indent throughout, uniform; a deeper
indent on any line would make YAML treat it as literal and break the fold.

```yaml
abstract: >-
  KL divergence over 65,536 tokens per domain separates the three quantized arms of a GGUF
  ladder from one another on code at 8.7-18.1 sigma in 2.3 GPU-hours; three task-benchmark
  instrument classes costing 14.3 hours separate the same arms nowhere. This report measures a
  27B coding model on two consumer 16 GB GPUs across eight quantizations, three inference
  backends and five benchmark families. Each benchmark fails differently, which is the point:
  WikiText-2 perplexity spans 0.033 across four arms against +/-0.041 of standard error per
  point; HellaSwag at n=400 rates the most heavily quantized arm nominally highest, two arms
  answering all 400 items identically; paired HumanEval+ at n=164 bounds the ladder's extremes
  at 0.61 points, 95 per cent interval [-3.28, +2.06], a test no outcome could have made
  significant at the observed discordance; and a 50-instance SWE-bench Verified campaign inverts
  the ordering at 77.6, 76.0 and 75.5 per cent inside +/-12 points. Divergence is roughly twice
  as large on code as on prose and 3.1-4.4x prose on the benchmark's own prompts, so against a
  published <0.007 quality threshold two of three arms pass on prose, one on generic code, and
  none on the task distribution. What moves the numbers is configuration, not quantization: for
  two of four arms GPU tensor placement sets the reachable context window; decode throughput
  spans 6.7 per cent between arms against 40.7 per cent within one configuration at three
  repetitions; speculative decoding is deterministically non-equivalent to unspeculated
  decoding, reproducing it on 131 of 164 problems while reproducing itself byte-exactly; and one
  1.19 GiB draft-worker allocation blocks a separate drafter on two of three engines, one of
  which never served a request. These are measurements of one model under named engine images on
  one two-GPU host. Artifacts, withdrawn claims and the defect register are released.
```

Verified: `yaml.safe_load` on this block returns a string identical, character for character, to
the abstract in §1 (1,910 characters).

**Two further `CITATION.cff` defects, flagged and not changed** (out of scope here, both live):
`title:` still carries the untrimmed 20-word incumbent and must take §4's decision; and
`repository-code:` points at `https://github.com/henrique-simoes/llm-quantization-damage`, which
`CLAUDE.md` §3 records as not existing — the repository has no public remote. A CFF pointing at a
URL that 404s is worse than no CFF, and this is an owner decision, not an editorial one.

---

## 4. The title — decision and reasoning

### Decision: **A**, the incumbent with the two-word trim. Confirmed.

> **Divergence Ranks What Benchmarks Bound: quantization, speculation and context for a 27B coding
> model on two 16 GB GPUs**

18 words. `speculative decoding` -> `speculation` is the whole change.

### The owner's question answered directly

What drew the owner in was **quantization, speculative decoding, accuracy and token-generation
speed on this specific model**, and his criticism is that the work over-indexes on the last wave.
Those are two different questions and the title answers them differently.

**On over-indexing: this is an abstract problem, not a title problem, and the abstract now fixes
it.** A title carries one clause of argument and one of scope. Loading it with eight quantizations,
three backends and five benchmark families produces candidate C, whose subtitle is an inventory —
and inventories in titles read as scope-padding to a sceptical reviewer, and to an arXiv moderator
applying the 2025-10-31 policy they read as a survey. The recommended abstract carries that breadth
instead: five instruments each with its own bound, four configuration results, an explicit count of
quantizations and backends, all inside 1,910 characters. The fix belongs where the space is.

One tension is worth stating rather than smoothing, because the owner will find it: **the title's
main clause leads with "Divergence", which is the final wave's instrument.** The defence is that
the sentence is a *comparison between two instrument classes*, and its second half — "What
Benchmarks Bound" — is the historical campaign, named as the thing that did the bounding. Four
blind reviews, two HumanEval+ ladders, a four-day SWE-bench campaign and three perplexity protocols
are what put the word "Bound" there. A title that named only the divergence ladder would read
"Divergence Ranks a Quantization Ladder", and it does not.

**On the four interests: three of the four are in the title, and the fourth is deliberately out.**
Quantization, speculation and context are named; accuracy is the subject of both verbs, "Ranks" and
"Bound". Token-generation speed is absent, and adding it — "quantization, speculation, context and
throughput", 19 words — was considered and rejected on a principle the report applies elsewhere:
**a title should not promise a result that is a null.** The throughput headline is that decode speed
does not discriminate these quantizations (6.7 % between arms against a 40.7 % within-configuration
noise floor, PN-45, after two prior corrections). That belongs in the abstract's second half, where
it has its estimator and its n, and it is there. Putting "throughput" in the title advertises a
ranking the study explicitly declines to make.

### Why not the alternatives

- **B, E, H** are out on a rule, not on taste. All three are negative-instrument titles ("Could Not
  Rank It", "Cannot Separate", "What the Benchmarks Cannot See") and `STYLE-GUIDE.md` §1.7 bans
  "cannot" of an instrument, with **PN-60 given as the reason**: the instrument did resolve
  something, on another construct. `ABSTRACT-V2.md:388-393` argued reviewer C's caution against such
  titles is stale *because* PN-60 voided PN-44 — that inverts the argument. PN-60 is why the rule
  exists. H carries a second, factual blocker: "twelve days" against a repository that says twelve,
  thirteen and fifteen for the same span.
- **C** puts "eight quantizations" in a title. The count is now settled at eight and `README.md` is
  fixed, but the subtitle is still an inventory and it invites "eight of what kind?" — the eight
  span GGUF and NVFP4 and only four carry the divergence comparison.
- **D** abandons the accuracy half, which is the better half and the one carrying the methodological
  argument. It is the right title for a shorter, `cs.PF`-only paper inside this corpus.
- **F**, the untrimmed incumbent, differs from A by two words and is three words longer than it
  needs to be against §3.0's recommended 15.
- **G** (reviewer D's T1) is the safest title available and would be accepted without argument, but
  "a measurement study of a 27B coding model" makes the study sound smaller than it is, which is
  the opposite of this revision's purpose.

### Stability

Nine notes in this corpus correct other notes and four headline claims have been withdrawn or
scoped by re-analysis *after* measurement closed. Every one of those corrections came from
re-analysing a single instrument; **none has moved the contrast between the two instrument
classes.** A title built on that contrast is the only kind that survives this corpus's own
behaviour. If the tail decomposition were withdrawn entirely tomorrow, title A would not move.

### Files that move with this decision

`CITATION.cff` (`title:`), `manuscript/OUTLINE.md` and `manuscript/OUTLINE-V2.md` (title lines and
thesis paragraph), `README.md`'s opening. Not changed here.

---

## 5. Corrected must-not-claim list

Supersedes `ABSTRACT-V2.md` §4. Items 1-15 are that list with three corrected and one added; the
corrections are marked. This is the list the drafter checks the abstract *and* every section
opening against.

1. **Not "nine quantizations."** Settled at **eight** (Q3_K_XL, IQ4_XS, Q4_K_M, Q4_K_XL, Q5_K_XL,
   Q6_K, Q6_K_XL, NVFP4); `README.md` is corrected. Two of the eight are historical-only and one
   (Q4_K_M) no longer exists on disk.
2. **Not "twelve days."** `TIMELINE.md` is titled twelve, spans fifteen calendar days and closes on
   thirteen. Count instruments, not days. "Two weeks" is true under all three readings if a duration
   is needed at all.
3. **Not a draft acceptance of 1.000** as a credential for any arm - degenerate-generation
   artifacts, 50-55 tokens over 34-36 draft events (PN-61). Only 1,024-token rows are usable.
4. **Not the tail's *shape* as a quantization property.** Quantization sets the magnitude; the
   corpus sets the shape, and this study's own KV-dtype-only control reproduces it (PN-62).
5. **Not "the code-to-prose gap widens with aggressiveness"** as a reference-invariant result - it
   is an upper bound, shrinking ~16 % under a plausible reference correction (reviewer D §4.2). The
   *level*, code roughly twice prose, is invariant and is what the abstract states.
6. **Not "100-200x" and never a per-arm median.** "About 200x", unranked; print precision puts
   +/-3-7 % on each cell and the intervals overlap (PN-64).
7. **Not the long-context retrieval separation.** PN-44's 89.0 vs 79.0 at 131,072 measured
   output-budget closure: `closed-and-wrong` is exactly zero across all fourteen cells, and on the
   55 items where neither arm's budget bound, both score 55/55 (PN-60, PN-63). Retrieval at 131,072
   is **unanswered, not negative**. Do not cite PN-44, PN-37's mechanism clause, or
   `s12-ruler.json`'s `accuracy_recovery` for the mk100 entry.
8. ⚠️ **Corrected.** **Not "every adjacent pair at 8.7-18.1 sigma."** PN-67: on **code** the
   adjacent pairs separate at **8.67** and **11.82** sigma and the extremes at **18.13**, which
   skips a rung; on **prose** the three are 3.71, 8.48, 13.48. So **"8.7-18.1" = all three code
   separations** and **"3.7-11.8" = the adjacent separations across both domains**. Both ranges are
   correct only with their own qualifier. The abstract uses the code range and says "the three
   quantized arms from one another", which is true of both endpoints. Also: a four-point ladder
   yields **three** pairwise distances, because the fourth arm is the reference and its distance to
   itself is zero by construction.
9. ⚠️ **Corrected.** **Not "60x cheaper", not "20 minutes against 20 hours", and not PN-41's
   2.1 h / 4.8 h / 2.2x either.** T19 supersedes PN-41: **2.32 GPU-hours** of divergence against
   **14.31 hours** of task benchmarking, a ratio of **6.2x** - and the 14.31 covers **three
   instrument classes only** (HellaSwag, HumanEval+, RULER). Perplexity and the four-day SWE-bench
   Verified campaign are historical and outside it, so "five task-benchmark families costing
   4.8 hours" is wrong twice over. `ABSTRACT-V2.md:443` has been repaired to say this.
10. **Not DFlash2's speed or byte-exactness beside MTP's.** The drafter is bound to its own engine
    build, so that arm ran on a different image than its baseline (PN-25, PN-29). Fastest measured;
    not cleanly comparable.
11. **Not "speed does not discriminate" as equality.** n = 3 to 6 repetitions, single stream, one
    host, and one arm of PN-45's table is a **single reading**: "not separated at this n", never
    "equal".
12. **Not any comparison to the model's published scores.** The card publishes LiveCodeBench v6,
    SWE-bench **Pro** and Terminal Bench, and no HumanEval; this study ran SWE-bench **Verified**.
    Every logprob instrument here is greedy, matching neither official preset.
13. **Not a priority or superlative claim** (`STYLE-GUIDE.md` §3.0 rule 5). The
    divergence-versus-benchmarks framing is **independent confirmation of Dutta et al.**, NeurIPS
    2024 (arXiv 2407.09141), and §1 must say so before a reviewer does.
14. **Not "we", "our" or "us"**, and "I" only for an act of judgement (§1.3). The incumbent
    `CITATION.cff` abstract uses "we" five times; §3 replaces it.
15. **Not an equivalence conclusion without its bounds** (§4.4) - which is why the abstract quotes
    [-3.28, +2.06] rather than "no significant difference".
16. ⚠️ **New.** **Not "the 1.19 GiB draft-worker wall blocks three engines."** It blocks **two of
    three**: SGLang and vLLM OOM at draft-worker init; **llama.cpp succeeds** at 38.51 tok/s with a
    1.1 GB 4-bit GGUF drafter and layer-split pipelining (`PAPER-REFERENCES.md:290-297`). PN-53's
    headline sentence says three and its own evidence table says two - **cite the table**. The
    finding is a *contrast*, and the contrast is the reportable part.
17. ⚠️ **New.** **Not "[-2.68, +1.46]" for HumanEval+.** That is the **base**-tests interval
    (3 discordant). HumanEval**+** is **[-3.28, +2.06]** (5 discordant, minimum achievable
    p = 0.0625). PN-40's row labels read "HumanEval+ base" and "HumanEval+ base+extra", which is
    what invites the substitution; `TABLES.md:184-185` disambiguates them correctly.
18. ⚠️ **New.** **Not "three inference backends" without the qualifier.** One of the three
    (SGLang 0.5.18) produced no measurement of any kind at any context length (PN-54). Say so, in
    the same sentence, and it becomes a finding instead of an inflation.
19. **Not "cannot" of an instrument** (`STYLE-GUIDE.md` §1.7) - in the abstract, in a section
    opening, or in the title. Prescribed forms: "does not resolve", "bounds rather than resolves",
    "did not separate the arms on this construct". This bans title candidates B, E and H and applies
    to the four outline claim sentences `REVIEW-V2.md` §4 lists.

---

## 6. Status

The abstract in §1 is submission-ready: verified against artifacts, style-guide compliant,
1,910 characters against a 1,920 cap, ASCII-clean. The title in §4 is settled at **A**. Three files
still carry stale text and are **not** edited here: `CITATION.cff` (`abstract:` per §3, `title:`
per §4, and the non-existent `repository-code:` URL), `manuscript/OUTLINE.md` and
`OUTLINE-V2.md` (title and thesis paragraph), and `FIGURE-PROGRAMME.md:99` ("three of four arms"
-> "two of four", PN-39). `ABSTRACT-V2.md:443`'s trap item **has** been repaired.
