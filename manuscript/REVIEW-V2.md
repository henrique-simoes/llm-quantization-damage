# REVIEW-V2 — adversarial review of `OUTLINE-V2.md` and `ABSTRACT-V2.md`

*Reviewer: adversarial pass, 2026-09-04. Both files read from disk at their committed-worktree state
(`OUTLINE-V2.md` 1,139 lines / 80,551 bytes; `ABSTRACT-V2.md` 473 lines / 33,047 bytes, both
untracked). Every number below was checked against `docs/paper/PAPER-NOTES.md`, `manuscript/figures/TABLES.md`,
`manuscript/figures/FIGURE-PROGRAMME.md` and `manuscript/STYLE-GUIDE.md`, never against prose in
either file under review.*

---

## 0. Verdict, up front

**The outline is accepted with eleven required changes. The abstract file is accepted as a proposal
set but its recommended draft, V2, must not be submitted as written — it quotes a superseded cost
pair that the outline it ships beside explicitly forbids, and it misdescribes the study's own sigma
range.** Both defects are one-sentence repairs and a corrected V2 is supplied in §6.3 at 1,914
characters.

| question asked | answer |
|---|---|
| Does the new structure solve the owner's complaint? | **Yes, structurally and measurably** — but the weighting table that proves it is arithmetically wrong, and the last wave still outweighs the historical corpus about 2:1 in body words. See §1. |
| Does it overclaim? | The outline is unusually clean on the five traps (PN-60/61/62/64/66) — it catches all five explicitly. **Four other overclaims survive**, three of them in the abstracts. See §2. |
| arXiv moderation risk | Low and correctly managed, with one structural risk the files do not name (§3). §2's 900-word cap is honoured but budgeted to exactly 900 with no room for its own opening. |
| Style-guide compliance | Abstracts: clean on pronouns and bounds. Outline: **systematic use of a banned construction** ("cannot", of an instrument, §1.7) in the very sentences each section must earn, and three title candidates violate the same rule. See §4. |
| Character counts | All four abstracts verified ASCII-clean and under 1,920. The file's self-reported counts are **exact**. See §5. |

---

## 1. Does the structure actually solve the complaint?

### 1.1 The honest answer: yes, and it is checkable

v1's `OUTLINE.md` has a single results section in which §5.2 (`OUTLINE.md:128`) carries HellaSwag,
HumanEval+, RULER, perplexity **and** the entire SWE-bench campaign in one subsection heading, and
PN-46 through PN-59, PN-61 and PN-63…PN-66 appear in the body either not at all or as a clause.
v2 gives the agentic campaign its own 900-word subsection (`OUTLINE-V2.md:553`), the two HumanEval+
ladders their own (`:486`), perplexity its own (`:441`), backends their own (`:750`), and it promotes
F15 and F10 to ESSENTIAL. That is not relabelling; it is a different body. The owner's specific list
— four-day SWE-bench, two HumanEval+ ladders across seven configurations, MTP vs DFlash2, throughput
across quants/methods/depths/backends, eight checkpoints, three backends, three perplexity protocols
— each has a named home, and §7.4 (`:1131-1138`) supplies a falsifiable acceptance test for the draft.

The chronology ban is honoured. No subsection is dated; the twelve-day history enters only as §3.3
provenance and as the correction record in §8 and Appendix B. That is the right disposal.

### 1.2 The weighting table is arithmetically wrong (`OUTLINE-V2.md:170-178`)

Summing the outline's own per-section word targets from §4:

| thread | sections | table says | actually sums to |
|---|---|---|---|
| divergence + quant fidelity | §5.1–5.3, §6.3 | 2,800 | 2,800 ✓ |
| task benchmarks | §5.4–5.7 | 3,000 | 3,000 ✓ |
| speculative decoding | §6.4–6.5 | 1,500 | 1,500 ✓ |
| context/systems/backends/throughput | §6.1, §6.2, §6.6, §6.7 | 2,200 | **2,450** ✗ |
| protocol + threats | §4, §5.8, §7 | 3,100 | 3,100 ✓ |
| framing | §1, §2, §3, §8 | 3,350 | **3,450** ✗ |
| §5 and §6 opening maps | — | not counted | **300** |
| **body** | | **≈15,950** | **16,600** |

Two further internal contradictions: **§5's header says 5,600 words** (`:384`) while its nine
subsections sum to **5,850**; **§6's header says 4,200** (`:606`) while its eight sum to **4,600**.

*Remedy.* Recompute the table from the §4 targets, or cut §5 and §6 to their stated headers. The
conclusion survives repair — task benchmarks 18.1 % against divergence 16.9 % of a 16,600-word body —
so the owner's correction is genuinely delivered. Do not let a reviewer find the arithmetic first;
this corpus has already published three different values for one throughput spread (PN-19 → PN-36 →
PN-45), and a wrong sum in the document that promises rebalancing is the worst possible place for a
fourth instance of the same failure.

### 1.3 The residual imbalance the outline does not state

Classifying each subsection by which wave produced its lead evidence:

- **E12-wave lead** (§5.1, §5.2, §5.4, §5.6, §6.1–§6.5, most of §6.7, §5.8): ≈ 6,150 body words.
- **Historical-corpus lead** (§5.3, §5.5 items 2–3, §5.7, §6.6, part of §6.7): ≈ 2,700 body words.

The final wave still holds roughly **2.3×** the pre-E12 corpus in body space. That is defensible —
the controlled four-arm comparison is where the causal claims live — but it is not what §3.2's prose
implies, and the owner will do this count himself. Two cheap moves close most of the gap without
touching the argument:

1. **Split §5.5** into **§5.5a the paired anchor (400 w)** and **§5.5b the two historical ladders
   (600 w)**. As written, one 900-word subsection carries an E12 paired test *and* seven
   configurations across two ladders and a context control; the historical half will be compressed
   first when drafting bites, which reproduces exactly the failure being corrected.
2. **Raise §6.6 backends from 600 to 750** — PN-53/54/55/56 is four notes, one of them a
   cross-engine wall and one an engine that produced nothing, and 600 words is thinner per note than
   §6.2 spends on a single ratio sweep.

Fund both from §5.1 (900 → 750) and §6.4 (700 → 600); neither loses a claim.

### 1.4 PN coverage — spot-checked, and it is real

Eighteen entries checked line-for-line against `docs/paper/PAPER-NOTES.md`. All eighteen describe
their note correctly and route it to a section where that evidence belongs.

| PN | outline's one-liner (`:946-1011`) | verified against PAPER-NOTES | verdict |
|---|---|---|---|
| PN-6 | ceiling belongs to the split, five loading ratios | five ratios 54,46…62,38; default split fails | ✓ |
| PN-13 | the divergence ladder, 3.7–11.8 σ | exact phrase in the note | ✓ (but see §2.2) |
| PN-15 | q4_0 KV costs 51 % of a quantization level | 0.002955 ± 0.000127 vs 0.005829 | ✓ |
| PN-19 | speed does not discriminate — numbers superseded | superseded by PN-36, then PN-45 | ✓ |
| PN-21 | three-tier hierarchy, prose < code < task | 3.13–4.40× prose→task | ✓ |
| PN-22 | HellaSwag structurally insensitive at n=400 | 82.75/82.25/82.75/83.25, b=0 c=0 pair | ✓ |
| PN-23 | MTP not output-identical, 131/164 | 79.88 %, median char 715/730 | ✓ |
| PN-26 | determinism control, both arms self-reproduce | md5 identical, 164/164 | ✓ |
| PN-29 | DFlash2 fastest, cannot reach depth | 51.78 tok/s; ceiling 163,840 | ✓ |
| PN-32 | acceptance falls with depth; n=3 cannot rank | 166 % spread, 12/13 → repaired to 10/11 | ✓ |
| PN-39 | the split claim holds for 2 of 4 arms | Q4_K_XL loads at default; Q6_K_XL never attempted | ✓ |
| PN-40 | McNemar could not have reached 0.05 | min p 0.25 / 0.0625 | ✓ |
| PN-45 | 6.74 % between arms against 40.7 % within | exact | ✓ |
| PN-46 | non-thinking ladder + context control | 84.1/81.7 … 93.9/91.5; 93.3/90.2 both windows | ✓ |
| PN-50 | SWE-bench inverts the ladder | 38/49, 38/50, 37/49 | ✓ |
| PN-53 | 1.19 GiB wall across three stacks | SGLang + vLLM identical size; llama.cpp succeeds | ✓ |
| PN-60 | long-context result measured budget closure | zero closed-and-wrong; 55/55 on unbound items | ✓ |
| PN-64 | median row corrected; 18 of 20 cells verify | 199/181/206; intervals overlap | ✓ |

The "**Not used: none**" claim at `:1013` is therefore credible. Two small corrections to the table
itself:

- **PN-58 is described as "the ten-defect reporting audit"** (`:1002`) while Appendix B (`:914`) says
  "twelve defects". Both are right and they count different things: T20 has **twelve register
  entries**, of which entry 12 *is* PN-58's ten historical defects. Write "twelve register entries,
  covering twenty-one defects" once, in Appendix B, or the count will read as an error.
- **PN-52's ~45-step column is cross-experiment.** PN-52's caveat says the UD-Q6_K_XL mean is carried
  over from a different instance set; `FIGURE-PROGRAMME.md:1141` already flags the same thing for
  F17b. §5.7 (`:576`) quotes "23 / 29 / ~45" without that scope. Add it — it is one clause.

---

## 2. Overclaims

### 2.1 ⚠️ The recommended abstract quotes a superseded cost pair — and the file's own trap list defends it

`ABSTRACT-V2.md:101-103` (V2), `:161` (V3) and `:197` (V4) all state **"2.1 hours of GPU"** against
**"4.8 hours"**, sourced to PN-41 at `:126` and defended at `:443` ("**Not** '60x cheaper'… the
measured figures are 2.1 hours and 4.8 hours").

`TABLES.md` T19 (`:696-720`) says, in the table's own note: *"**This supersedes PN-41's published
contrast (2.15 h vs ≈4.8 h, a 2.2× ratio)**, which was computed before the 9.4-hour 100-sample
MK-NIAH cell existed."* The current figures are **2.32 and 14.31 GPU-hours, a ratio of 6.2×**, and
`TABLES.md:776` records the supersession explicitly. `OUTLINE-V2.md:598` and `:1118` both forbid
quoting anything else — "**Quoting any cost contrast not currently in T19**" is named as §5.8's
failure mode.

So the two files under review disagree on the study's most-corrected number, and the abstract takes
the withdrawn side. **This is the single most serious defect in either file**: it is the third
generation of a figure that has been wrong twice, in the one text that cannot be amended after
submission.

*Remedy.* Use **2.3 h and 14.3 h**, and attribute the 14.3 to **three instrument classes**, not five
families — T19's 14.31 sums HellaSwag, HumanEval+ and RULER only. Perplexity and the SWE-bench
campaign are outside it, so "five task-benchmark families … costing 4.8 hours" is false twice over.

### 2.2 ⚠️ "Separates every adjacent pair on code at 8.7-18.1 sigma" — the upper endpoint is not an adjacent pair

All four abstracts use this phrasing (`:69`, `:101`, `:161`, `:197`). Recomputing from PN-13's own
code-domain means and errors, and confirmed against reviewer D's table (`reviewer-d-adversarial.md:331-340`)
and T23 (`TABLES.md:828-836`):

| code-domain pair | σ | adjacent? |
|---|---|---|
| Q6_K vs Q5_K_XL | 8.67 | yes |
| Q5_K_XL vs Q4_K_XL | 11.82 | yes |
| Q6_K vs Q4_K_XL | **18.13** | **no — skips a rung** |

The adjacent range on code is **8.7–11.8**. Reviewer D's phrasing ("the code-domain separations
(8.7–18.1 σ)") is correct because it says *separations*, not *adjacent pairs*; `README.md:15` is
likewise correct. The abstracts inserted "every adjacent pair" and kept the all-pairs range.

*Remedy.* "separates the three quantized arms from one another on code at 8.7-18.1 sigma" — true,
no longer, and it also disposes of the second problem: a **four-point ladder has four arms and the
divergence family contains three pairs**, because the fourth arm is the reference and its distance
to itself is zero by construction (PN-13 caveat). "Every adjacent pair of a four-arm ladder"
(`OUTLINE-V2.md:42`) invites the same objection and needs the same repair.

### 2.3 The two files disagree on which sigma range is the headline

`OUTLINE-V2.md:42` and `:400` lead with **3.7–11.8 σ**; `ABSTRACT-V2.md` deliberately uses the
code-only **8.7–18.1** and explains why at `:439-442`. Reviewer D's instruction was explicit: *"the
paper's signature phrase '3.7–11.8 σ' quotes a range whose lower endpoint is the single claim that
does not survive. Drop it"* (`reviewer-d-adversarial.md:353`). The outline keeps it in the
argument paragraph and defers the qualification to §7 item 2 (`:838-842`).

*Remedy.* One range, everywhere. Recommend the abstract's: quote **code-domain separations**, report
the prose adjacency as "not separated once clustering is accounted for", and keep the full nine-test
table in §7/T23. The outline's §1 and §5.1 must change, not the abstract.

### 2.4 The five withdrawal traps — the outline passes all five, the abstracts avoid all five

Checked individually, because these were the assignment's stated traps:

| trap | outline | abstracts |
|---|---|---|
| **PN-60** MK-NIAH is budget closure, not retrieval | §5.6 (`:525-551`) withdraws it explicitly, keeps S-NIAH, reports the arc in three sentences, marks the Red Hat comparison void | not mentioned in any draft — correct |
| **PN-61** acceptance 1.000 is degenerate | §5.7 (`:571`) and §6.5 bar it; figure delta orders F17's panel redrawn (`:1067`) | V4's thesis row correctly omits the acceptance clause; `:433` bars it |
| **PN-62** tail *shape* is a corpus property | §5.2 (`:415-422`) makes the KV-only control the section's best moment | not claimed |
| **PN-64** median row cannot rank arms | §5.2 (`:411`) — "say 'about 200×', never tabulate it per arm" | not claimed |
| **PN-66** PN-32 fails Holm on repair | §6.5 (`:733`) gives 10/11, p 0.00586, rank-dependent survival; §7 item 2 repeats it | not claimed |

This is the strongest part of both files and it should be said plainly: no withdrawn claim is
resurrected anywhere in either document.

### 2.5 Four remaining overclaims, smaller

1. **`FIGURE-PROGRAMME.md:99` still says the split set the window "for three of four arms."** PN-39
   says **two**. The outline is right everywhere (`:615`, `:625`) and the abstracts are right, but
   the figure programme is a binding artifact for F4's caption and the outline's §6 figure deltas do
   not catch it. *Remedy:* add to §7.3's verification list; fix F4's claim line before D4b.
2. **V2's throughput clause carries no n.** "6.7 per cent between arms against 40.7 per cent within a
   single configuration" (`:113`) omits what PN-45's caveat insists on: the 6.74 % span rests on two
   arms with medians of three readings and **one arm with a single reading**. `STYLE-GUIDE.md` §4.4
   requires the claim to carry its own bound. *Remedy:* "…within one configuration at three
   repetitions" — five words, and it is in the corrected draft in §6.3.
3. **"The five task-benchmark families run before it"** (`ABSTRACT-V2.md:101`). Three of the five ran
   *after* the divergence measurement (S6 on 2026-09-01, S7 and S12 later still; SSA S2/S3 was
   2026-08-30). It is also a chronological claim in a document whose whole premise is that chronology
   was refused. *Remedy:* delete the clause.
4. **§6.5 quotes DFlash2 at "2.81×"** (`:726`); T13 and PN-29 say **2.80×**. Trivial, but T13 is the
   table that will be printed beside it.

### 2.6 One number in the outline with no artifact behind it — correctly self-flagged

§6.7 (`:798-802`) leans on the acceptance-conditioned re-analysis (r² 0.83–0.99, spread 17–41 % →
3–11 %), and §7.3 item 4 (`:1123`) admits it exists in two reviews and **no paper note**. That is
honest, and the fix is cheap. But note the consequence the outline does not draw: §6.7's claim
sentence ("the variance … is explainable rather than mysterious") is *carried entirely* by that
un-noted analysis. Until PN-67 exists, §6.7 must claim only the span and the noise floor.

---

## 3. arXiv moderation

**The framing is safe, and safer than v1's.** The 2025-10-31 policy declines review and position
papers and submissions without "original or substantive research". v2 leads on measurement in every
section opener, keeps background to a hard cap, and its §1 contributions list is seven measured
results rather than seven observations about the field. The instrument-calibration frame is the one
place a moderator could hesitate — "a paper about benchmarks" is adjacent to a survey — and the
outline defends it correctly by making §6 (four positive, load/no-load configuration results) half
the body. Keep that balance; it is load-bearing for moderation, not only for the owner's complaint.

Three findings.

1. **§2 is capped at 900 and budgeted at exactly 900** — three threads at 300 words each
   (`:296`, `:301`, `:305`), leaving nothing for the section's claim sentence or its transitions.
   It will overrun on the first draft. *Remedy:* budget 3 × 270 + 90 for the opening.
2. **The recommended abstract does open on a measurement** (`STYLE-GUIDE.md` §3.0 rule 3) — V2's
   first clause is an instrument, an n, a result and a cost. V3's opens on an inventory and V4's on
   an n=6 result; both are worse on this axis, and the file says so itself.
3. **Length is the unaddressed risk.** 16,600 body words plus 3,800 of appendix is ≈40 pages,
   against `STYLE-GUIDE.md` §2.8's 11,350/30. §7.1 (`:1088`) declares the style guide superseded —
   a document the brief treats as binding. The justification (nineteen more notes carry body weight)
   is real, but 46 % growth over a budget written for the same corpus is more than the delta
   supports, and every added page is more surface for the kind of arithmetic error found in §1.2.
   *Remedy:* target **13,500 body words**. Apply compression levers 1, 3 and 5 from §3.4 (§6.7 → 150 w,
   §6.2 folded into §6.1, §6.6 held at 600), take §5.1 to 750 and §6.4 to 600 per §1.3 above, and
   move Appendix B's twelve entries to a table with two-sentence rows. No claim is lost.

---

## 4. Style-guide compliance

**Abstracts: pass.** No "we", "our" or "us" in any of the four blocks (the only matches are inside
"hours"). "I" appears once, in V1, for an act of reporting judgement — within §1.3's "sparingly".
Every comparative claim carries its interval inside the sentence ([-2.68, +1.46], ±0.041, ±12
points, 8.7-18.1 sigma). "Significance" appears only in its statistical sense, as §1.7's own
prescribed alternative phrasing. The status/scope sentence closes every draft.

**Outline: one systematic violation.** `STYLE-GUIDE.md` §1.7 bans **"cannot" of an instrument**,
with PN-60 given as the reason (*the instrument did see something, on another construct*), and
prescribes "does not resolve" / "bounds rather than resolves" / "did not separate the arms on this
construct". The outline uses it sixteen times, and — the part that matters — in the **claim
sentences a section must earn**:

- `:467` §5.4 claim: "A standard multiple-choice reasoning benchmark **cannot** see this damage…"
- `:721` §6.5 claim: "…this host's variance **cannot** rank draft depths at three repetitions."
- `:361-363` §4.3: "free-running greedy generation **cannot** measure quantization distance";
  "KL divergence **cannot** be measured at long context…"
- `:974`, `:977`, `:983`, `:1034` in the coverage and figure tables.

Some of these are defensible — PN-38's fork saturation *is* a structural impossibility, and §5.4's
own failure-mode note (`:481`) already prescribes the right rewrite ("this instrument resolves no
finer than 7.4 points, and the effect is 1.0"). But a claim sentence written with a banned word will
be copied into the draft verbatim. *Remedy:* rewrite the four claim sentences; leave the table
shorthand.

**Three title candidates violate the same rule.** B ("Could Not Rank It"), E ("Cannot Separate") and
H ("What the Benchmarks Cannot See") are negative-instrument titles. `ABSTRACT-V2.md:388-393` argues
reviewer C's caution is stale because it rested on PN-44, which PN-60 voided — **this inverts the
argument.** PN-60 is precisely why the style guide bans the construction: the instrument *did*
resolve something, and a title saying it could not is the claim PN-60 shows to be the wrong reading.
The style guide postdates reviewer C and is binding. B, E and H are out on a rule, not on taste.

**One more, correctly flagged and out of scope:** `CITATION.cff`'s incumbent abstract uses "we" five
times and opens on a claim about the field (`ABSTRACT-V2.md:44-48`). Confirmed; it must be replaced
whichever draft wins.

---

## 5. Character counts — mechanical verification

Each fenced block extracted programmatically, whitespace-joined, counted, and screened for any
codepoint outside 32–126.

| draft | file lines | characters | words | ASCII-clean | ≤ 1,920 | file's own claim | match |
|---|---|---|---|---|---|---|---|
| **V1** conservative | `:58-76` | **1,667** | 251 | yes | yes (253 spare) | 1,667 / 251 w | ✓ exact |
| **V2** balanced | `:100-120` | **1,907** | 293 | yes | yes (13 spare) | 1,907 / 293 w | ✓ exact |
| **V3** programme-forward | `:147-167` | **1,889** | 295 | yes | yes (31 spare) | 1,889 / 295 w | ✓ exact |
| **V4** assertive | `:186-205` | **1,825** | 282 | yes | yes (95 spare) | 1,825 / 282 w | ✓ exact |

No non-ASCII characters, no em dashes, no typographic quotes, no LaTeX, single paragraph each. The
counting in `ABSTRACT-V2.md` is trustworthy; this is the one part of the file that needs no repair.

⚠️ **But V2's 13 characters of headroom cannot absorb the §2 repairs.** The corrected V2 below is
1,914 characters — six spare. Any further edit must be counted, not estimated.

---

## 6. Recommendation

### 6.1 Title: **A**, the incumbent with the two-word trim

> **Divergence Ranks What Benchmarks Bound: quantization, speculation and context for a 27B coding
> model on two 16 GB GPUs**

Agreed with `ABSTRACT-V2.md`, and for a reason it under-argues. B, E and H are excluded by
`STYLE-GUIDE.md` §1.7 (§4 above), which removes the negative-framed branch entirely. C is excluded
by its own count — it puts "eight quantizations" in a title while `README.md:11` says nine, and a
title should not carry a number the repository disagrees with itself about. G understates the study,
which is the opposite of this revision's purpose. D abandons the accuracy half. That leaves A and F,
which differ by two words, and A is shorter. **Changing the title was never the fix**; the file is
right about that and right about why "What Benchmarks Bound" already names the campaign.

### 6.2 Abstract: **V2, corrected**. Not V2 as written.

V2 is the right choice on the merits — one sentence that carries instrument, resolution, cost and
the contrast, and a second half of four configuration findings that survive any accuracy
qualification. The hinge clause "Each benchmark fails differently, which is the point" does convert
a list into an argument, and that is the assignment's actual tension solved. But it ships two
defects (§2.1, §2.2) and one missing bound (§2.5 item 2), and its 13-character headroom means those
cannot be patched in place without recounting.

### 6.3 The corrected V2 — paste-ready, 1,914 characters, ASCII-clean, verified

```
KL divergence over 65,536 tokens per domain separates the three quantized arms of a GGUF
ladder from one another on code at 8.7-18.1 sigma, in 2.3 hours of GPU time; three
task-benchmark instrument classes costing 14.3 hours separate the same arms nowhere. This
report measures a 27B coding model on two consumer 16 GB GPUs across eight quantizations,
three inference backends and five benchmark families. Each benchmark fails differently, which
is the point: WikiText-2 perplexity spans 0.033 across four arms against +/-0.041 of standard
error per point; HellaSwag at n=400 rates the most heavily quantized arm nominally highest,
with two arms answering all 400 items identically; paired HumanEval+ at n=164 bounds the
ladder's extremes at 0.61 points, 95 per cent interval [-2.68, +1.46], a test that could not
have reached significance at the observed discordance; and a 50-instance SWE-bench Verified
campaign inverts the ordering at 77.6, 76.0 and 75.5 per cent inside a +/-12-point interval.
Divergence is roughly twice as large on code as on prose and 3.1-4.4x prose on the benchmark's
own prompts, so against a published <0.007 quality threshold two of three arms pass on prose,
one on generic code, and none on the task distribution. What does move the numbers is
configuration rather than quantization: for two of four arms GPU tensor placement sets the
reachable context window; decode throughput spans 6.7 per cent between arms against 40.7 per
cent within one configuration at three repetitions; speculative decoding is deterministically
non-equivalent to unspeculated decoding, reproducing it on 131 of 164 problems while
reproducing itself byte-exactly; and one 1.19 GiB draft-worker allocation blocks separate
drafters on three independent engines. These are measurements of one model under named engine
images on one two-GPU host. Artifacts, withdrawn claims and the defect register are released.
```

Changes from V2, all four traceable: **(a)** "every adjacent pair … 8.7-18.1" → "the three quantized
arms … from one another" (§2.2); **(b)** "2.1 hours … the five task-benchmark families run before
it, costing 4.8 hours" → "2.3 hours … three task-benchmark instrument classes costing 14.3 hours"
(§2.1, T19); **(c)** "and both outcomes" — an unclear phrase — replaced by "and five benchmark
families", which restores the countable breadth claim the owner asked for; **(d)** "within a single
configuration" → "within one configuration at three repetitions" (§2.5 item 2, PN-45 caveat).
Nothing else moved. The five withdrawal traps remain untouched, as V2 intended.

If the owner prefers breadth in the first clause, **V3 with the same (a) and (b) repairs** is the
fallback; it costs a slower opening and gains the thinking-mode and protocol-swing results, both of
which are among the study's best and are absent from V2.

### 6.4 What must change in the outline before drafting starts

Ordered by cost of getting it wrong. Items 1–4 are blocking.

1. **Fix the cost pair everywhere to T19's 2.32 / 14.31**, and delete PN-41's figures from
   `ABSTRACT-V2.md:443`'s trap list — that item currently prescribes the withdrawn number. (§2.1)
2. **Pick one sigma range.** Recommend code-domain 8.7–18.1 with the adjacent pairs named, and
   rewrite `OUTLINE-V2.md:42` and `:400`. (§2.2, §2.3)
3. **Rewrite the four claim sentences that use "cannot" of an instrument** (`:467`, `:721`, `:361`,
   `:363`) into `STYLE-GUIDE.md` §1.7's prescribed forms. (§4)
4. **Repair the §3.1 weighting table and the §5/§6 header word counts** (`:170-178`, `:384`, `:606`)
   so the document that promises rebalancing can be audited without finding an error. (§1.2)
5. **Split §5.5 into 5.5a/5.5b and raise §6.6 to 750**, funded from §5.1 and §6.4. (§1.3)
6. **Set a 13,500-word body target** and name which levers get it there, rather than declaring
   `STYLE-GUIDE.md` §2.8 superseded at +46 %. (§3 item 3)
7. **Budget §2 at 810 + 90**, not 3 × 300. (§3 item 1)
8. **Add the F4 claim-line correction** ("three of four" → "two of four",
   `FIGURE-PROGRAMME.md:99`) to §7.3's verification list. (§2.5 item 1)
9. **Write PN-67 for the acceptance-conditioned re-analysis before §6.7 cites it**, or scope §6.7's
   claim to the span and the noise floor only. (§2.6 — already item 4 of §7.3, promoted to blocking
   because a claim sentence depends on it)
10. **Settle the checkpoint count at eight and fix `README.md:11`**, so T1, F21-scope, the abstract
    and the README agree. (§7.3 item 1; also `ABSTRACT-V2.md:426`)
11. **Update `DRAFTING-PLAN.md` D5 as well as D4.** §7.2 (`:1106`) splits D4 into D4a/D4b but D5
    still names "§6 Cost, §8 Practitioner appendix, §9 Reproducibility appendix" — section numbers
    v2 has reassigned (§6 is now the axes; the appendices are lettered A–D).

Two small additions, non-blocking: add PN-52's cross-instance-set caveat to §5.7 (`:576`), and write
Appendix B's count as "twelve register entries covering twenty-one defects" (§1.4).

### 6.5 What not to change

The two-part hybrid, §5's ordering by unit of observation, §6's ordering by actionability, the
decision to keep all twelve register entries against reviewer B's four, §7 before §5/§6 in drafting
order, the eight ESSENTIAL figures, and the coverage table. Those are the parts that answer the
owner's criticism, and they are sound. The eleven items above are repairs to a good structure, not
an argument against it.
