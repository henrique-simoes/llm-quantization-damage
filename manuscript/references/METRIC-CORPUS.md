# METRIC-CORPUS — the canonical inventory of every measurement this project produced

> ⚠️ **Correction, 2026-09-03 (PN-60, PN-61, PN-62).** Entries in this file that cite **PN-44**
> or PN-37's mechanism clause as a long-context *retrieval* result are **superseded**: that battery
> measured output-budget closure, not retrieval (`closed-and-wrong` = 0 in every cell; on the 55 of
> 100 unbounded items both arms score 55/55). Entries attributing the divergence tail's **shape** to
> quantization are scoped by PN-62 — the KV-dtype-only control reproduces it. Any **draft acceptance
> of exactly 1.000** is a degenerate-generation artifact (PN-61). Rows are left unedited per the
> append-never-rewrite rule; read them with this banner.


**Compiled 2026-09-02, revised 2026-09-03 after the three-way review round (L-19) and the mk100
run (L-20). Built from a full pass over `docs/paper/PAPER-NOTES.md` (PN-1…PN-44),
`docs/build-stream/2026-08-30-quant-bench-trackA.md` (DEC-1…DEC-15, L-1…L-20),
`docs/paper/TRACK-A-DECISION.md`, all 173 files under `data/raw/e12/`, `data/archive/`, and the
machine records mirrored at `data/multivac-src/`.**

This file exists so that a paper writer never has to re-mine an artifact. Every row was
**cross-checked against the JSON artifact**, not copied from the note. Where a note and its
artifact disagree, the row carries a **⚑ FLAG** and §0 explains it.

---

## How to read this file

| field | meaning |
|---|---|
| **value** | as it appears in the artifact, with the artifact's own uncertainty where one exists |
| **n** | the unit of independence, named. "n=164 problems" and "n=65,536 tokens" are different instruments |
| **protocol** | the instrument, named, so rows from different protocols are never merged |
| **conditions** | quant · ctx · KV dtype · `-ts` · split mode · spec setting · sampling · image |
| **artifact** | repository-relative path, or a host path where the file is gitignored |
| **PN** | the paper note that carries the claim, or `—` if the number has never been written up |
| **STATUS** | one of the seven values below |

### STATUS vocabulary

| status | meaning |
|---|---|
| **CURRENT** | measured on a surviving image under a stated protocol; safe to publish with its caveat |
| **SUPERSEDED** | a later measurement replaced it; the superseding row is named |
| **WITHDRAWN** | the measurement is invalid; the reason is named. Never publish |
| **EXCLUDED** | deliberately kept out of comparison (void run, protocol artifact); retained, never deleted |
| **IRREPRODUCIBLE-ON-CURRENT-IMAGES** | produced on `llamacpp-dflash2-pr27342:1deefcc-sm120-cuda128-abi`, deleted from disk. Cannot be re-run |
| **HISTORICAL-PRE-E12** | from the 2026-08-20…08-29 corpus. Different protocol, usually different image; label in any table |
| **UNWRITTEN** | a valid measurement that exists in an artifact but no PN entry claims it. Usable, but it has had no review pass |

### Supersession map — read this before quoting any pre-2026-09-02 note

Nine notes were corrected in the 2026-09-02 review round (L-19) and one result was replaced by a
larger run (L-20). **Every correction was found by review, not by the authors.** In each case the
*conclusion* survived and the *numbers* changed.

| original | superseded/corrected by | what changed | what survived |
|---|---|---|---|
| **PN-19** (decode noise 32.9 %) | **PN-36** | its n=6 spans four context depths; true within-configuration spread **46.7 %**; Q4_K_XL has **n=1** at 262,144 | decode does not discriminate the arms — *better* supported |
| **PN-34** (saturation mechanism) | **PN-37** | saturation is false for 2 of 3 instruments; broad framing belongs to Dutta et al. (R13) | PN-35's tail structure, which is the real mechanism |
| **PN-33** MK-NIAH half | **PN-44** | n=12's 100.0 reference was a lucky draw; at n=100 it is 89.0 and the effect **separates** | the S-NIAH half (100.0/100.0 at three lengths) |
| **PN-28** (McNemar p = 1.0) | **PN-40** | the test could never reach p<0.05; minimum attainable p was 0.25 / 0.0625 | replaced by a *bound*: −0.61 pts, 95 % CI [−2.68, +1.46] |
| **PN-6** (ceiling belongs to the split) | **PN-39** | holds for 2 of 4 arms; Q4_K_XL loads at the default split; each failure is a single attempt | the rebalance moved two arms to the native window |
| **PN-8** (least-balanced is fastest) | **PN-42** | `54,46` is not the least balanced; `62,38` is, at 1,750 MiB; not monotone | balance and throughput are different objectives |
| **PN-15** ("51 % of a quant level") | **PN-43** | a **label collision** corrupted `metrics_reparsed.ppl`; the ratio is a size comparison, not additive | KLD 0.002955 ± 0.000127 and the PPL contrast, both intact |
| **PN-14 / prose** ("20 min vs 20 h") | **PN-41** | measured 2.15 h vs ≈4.8 h — a **2.2×** ratio. The 60× was fabricated | the *power* ratio, which is what carries the argument |
| **PN-23** mechanism | **PN-26** | float-nondeterminism hypothesis refuted; both arms are individually deterministic | 131/164, and "deterministically non-equivalent" |
| **PN-24** at-depth half · Amendment 1 | **PN-30** | the cells timed 17 generated tokens | the ctx-32,768 half |
| S11 (undocumented) | **PN-38** | now written up as a methodological negative result | free-running greedy generation cannot measure quantization distance |

### Four rules that govern every table built from this file

1. **Never mix protocols.** PPL Protocol 1 / 2 / SSA-KLD are three instruments. Greedy rows and
   DEC-2 official-sampling rows are not comparable. Depth-0 and at-depth decode differ 3–5×.
2. **Divergence here is LADDER-RELATIVE.** The reference arm is UD-Q6_K_XL, not FP16. Every KLD
   figure is a distance along the ladder; UD-Q6_K_XL's own degradation is 0 by construction and
   is unmeasured.
3. **Every context ceiling is a property of its `-ts` ratio.** A ceiling quoted without its ratio
   is not a fact about the quantization.
4. **q4_0 KV is present in every context, speed and long-context row in this corpus.** It costs
   0.002955 ± 0.000127 KLD (§5). Quote it with any accuracy claim.

---

# §0 — FLAG REGISTER: disagreements between notes, documents and artifacts

Found during the cross-check. **Nothing here is smoothed over.** Each item states what the note
says, what the artifact says, and what a paper writer should do.

**Status after the 2026-09-03 revision.** Of the 25 flags raised on 2026-09-02, **twelve are
resolved**, ten stand, and three are partially addressed. **Three new flags (F-26, F-27, F-28) were
raised against the correction round itself** — the corrections were checked as hard as the notes
they corrected.

| resolved | by |
|---|---|
| F-1 (MK-NIAH unevidenced) | synced, **and superseded** by the n=100 run — PN-44, §6.1 |
| F-2 (PN-19 pools four depths) | PN-36 — but see **F-26**, which finds two further problems in the fix |
| F-4 (`s8-scores-reparsed.json` missing) | file now in the repo, verified |
| F-5 (S11 undocumented) | PN-38 |
| F-6 (PN-33 cites R8 for Red Hat) | R-numbering corrected upstream |
| F-7 (LocalBench band inverted) | corrected in R5 and PN-14 |
| F-13 (model identity) | recorded; the multimodal caveat still needs to reach the manuscript |
| F-16, F-17, F-19 | corrected upstream |
| F-22 (R11/R12 attribution) | corrected upstream |
| F-23, F-24, F-25 (PN-35's evidence line, median rounding, dangling L-19) | all three confirmed correct and fixed; L-19 now exists |

| still open | why |
|---|---|
| **F-3** | `wave1-summary.md` still carries the wrong default-split column and the 13.33 tok/s at the wrong context. PN-39 now covers the substance; the file itself is unedited by design |
| **F-8** | the Unsloth Dynamic 2.0 URL is still a 404 |
| **F-9** | the Red Hat date is still impossible, and the source still disclaims the band PN-44 is now compared against |
| **F-10** | superseded in substance by PN-43, which wrote the warning **into** the artifact — the trust inversion is now documented at source |
| **F-11** | PN-7's VRAM figures for `196608:58,42` still disagree with the artifact |
| **F-12** | serverlogs and `power-log.csv` still do not ship |
| **F-14** | Terminal-Bench 2.1 still has no paper |
| **F-18** | S7 χ² vs S6 exact — now sharpened by PN-40 |
| **F-20** | `progress.json` **is** now in the repo; `s11-pads-manifest.json` still is not |
| **F-21** | the three-implementation delineation (§4.0) still needs to reach the manuscript |
| **F-26, F-27, F-28** | **NEW — raised against the correction round itself** |

---

### ⚑ F-26 — **NEW: PN-36 changes the spread estimator without saying so, and its Q6_K group mixes two `-ctxcp` settings**

PN-36 supersedes PN-19's statistics and is right to. But two of its own numbers do not survive the
same scrutiny it applied.

**(a) The estimator changed silently.** PN-19's "32.9 %" is `(max−min)/median`. PN-36's spreads are
`(max−min)/min`. Recomputed both ways on PN-36's own groups:

| group | readings | `(max−min)/min` (PN-36) | `(max−min)/median` (PN-19's rule) |
|---|---|---|---|
| Q5_K_XL `54,46` | 10.82 · 12.70 · 12.94 | **19.6 %** | 16.7 % |
| Q5_K_XL `56,44` | 10.78 · 12.51 · 12.91 | **19.8 %** | 17.0 % |
| Q6_K `58,42` (n=4) | 10.75 · 14.16 · 11.90 · 11.48 | **31.7 %** | 29.2 % |
| Q6_K `56,44` | 10.22 · 14.99 · 11.71 | **46.7 %** | 40.7 % |

So the headline sentence *"true within-configuration spread reaches **46.7 %**, not 32.9 %"*
compares two numbers computed by different formulas. Under PN-19's own definition the corrected
maximum is **40.7 %**. Both statements are individually defensible; the *comparison* is not.
**Pick one estimator, name it in the table, and restate both figures on it.**

**(b) PN-36's Q6_K `58,42` group of four mixes `-ctxcp 4` and `-ctxcp 32`.** The fourth cell is
`262144:58,42:1:ctxcp32` — the *other arm of PN-18's A/B pair*, a deliberately different
configuration. Its inclusion does not change the spread (11.48 is neither max nor min) but it does
change the **median**:

| group | median |
|---|---|
| four cells, `-ctxcp` 4 **and** 32 (PN-36) | **11.69** |
| three cells, `-ctxcp 4` only | **11.90** ← the value `TRACK-A-DECISION.md` cites |

That propagates into PN-36's second headline. The matched-depth between-arm span is:

* **8.64 %** using PN-36's ctxcp-mixed 11.69 (PN-36 reports "about 8.6 %")
* **6.72 %** using the clean n=3 median 11.90 — **which is exactly PN-19's original 6.7 %**

**This is the very defect PN-36 exists to correct, one dimension deeper** — and PN-36 states the
rule it breaks: *"an aggregate is only meaningful if every cell entering it is identical in every
dimension except the one being aggregated over."* Here the varying dimension is `-ctxcp`.
**Neither error touches PN-36's conclusion** — noise still exceeds the between-arm difference by
roughly 5× on any of these definitions — but the specific figures **46.7 %** and **8.6 %** should
not be printed as they stand. Verified against `tsweep-v2-Q6_K.json`, whose cells carry an explicit
`ctxcp` field.

---

### ⚑ F-28 — **NEW: PN-38's pairwise distances cite an artifact that is not in the repository, and do not reproduce from the one that is**

PN-38 reports normalized edit distances of **0.794** (Q6_K_XL/Q6_K, adjacent), **0.779**
(Q6_K_XL/Q4_K_XL, the extremes) and **0.613** (Q5_K_XL/Q4_K_XL, closest), citing
`data/raw/e12/quarantine/s11-divdepth.json.n1-padoverflow-20260901` **and stating that the figures
come from the repaired run**.

**That file is not in the repository.** `quarantine/` contains no `s11-*` entry. The S11 data that
*is* shipped — `s11/s11-divdepth.json` and `s11/s11-gen-c8192.json` — is the **original** run, the
one PN-38 says was superseded by the pad-overflow repair.

Recomputed from the shipped generations (`1 − SequenceMatcher.ratio()`, median over 3 pads):

| pair | ladder | PN-38 | recomputed here |
|---|---|---|---|
| Q6_K_XL / Q6_K | adjacent | 0.794 | **0.947** |
| Q6_K_XL / Q5_K_XL | — | — | 0.861 |
| Q6_K_XL / Q4_K_XL | extremes | 0.779 | **0.951** |
| Q6_K / Q5_K_XL | adjacent | — | 0.933 |
| Q6_K / Q4_K_XL | — | — | **0.860** (closest here) |
| Q5_K_XL / Q4_K_XL | adjacent | 0.613 (closest) | 0.905 |

**Two independent reasons this is not a contradiction, and both need stating rather than resolving
in PN-38's favour:** (i) these are **different generations** — repaired run vs original; (ii) PN-38
does **not state its metric definition**, and "normalized edit distance" is ambiguous (Levenshtein ÷
max-length, ÷ sum-length, or a similarity-ratio complement all give materially different numbers).

**What survives, and it is the note's actual claim:** on *both* computations the distances are
**uniformly high and the ordering is unrelated to ladder distance**. On mine the extremes (0.951)
measure marginally *further* apart than the adjacent pair (0.947), and the closest pair is
Q6_K/Q4_K_XL rather than Q5_K_XL/Q4_K_XL — a different scrambling, but a scrambling. **The
methodological conclusion — free-running greedy generation cannot measure quantization distance —
is independently reproduced.**

**Action:** sync the quarantined repaired-run artifact, and state the metric definition in the
note. Until then PN-38's specific numbers are **not reproducible from the public repository**, and
only its qualitative claim should be printed.

---

### ⚑ F-27 — **NEW: `s12-ruler.json`'s summary blocks were never updated for mk100 or mkmock**

The `cells` array is correct and complete — all twelve cells including `mk100` (89.0 / 79.0, n=100)
and `mkmock` are present and verified. But three top-level summary fields still describe the
original design:

| field | says | should say |
|---|---|---|
| `tasks` | `["niah", "variable_tracking"]` | also `mkniah`, `mkmock`, `mk100` |
| `n_samples` | `25` | 25 / 12 / 100 by cell — it varies |
| `accuracy_recovery` | S-NIAH ×3 and `mkniah` (91.67) only | **no `mk100` entry at all** |

So the study's headline long-context number — **88.76 % recovery** — is *computable* from `cells`
(79.0 / 89.0) but is **not stored anywhere in the artifact**, and the `accuracy_recovery` block a
reader would naturally consult still shows the superseded n=12 value of 91.67 with no marker that
PN-44 replaced it. This is the same class as F-1: the summary a reader trusts lags the data.
**Add an `mk100` entry to `accuracy_recovery` and a `_WARNING_` on the `mkniah` one**, following
the pattern the review round already established in four other artifacts.

---

### ⚑ F-1 — **RESOLVED, then superseded** — the MK-NIAH result

> **Resolved 2026-09-02, and then made moot.** The `ruler/` tree was synced, so the n=12 MK-NIAH
> cells and their predictions are now in the repository. The review also found something worse than
> the missing file: **the generation command existed nowhere** — the harness *read* a pre-generated
> dataset and the `--num_needle_k 4` invocation was ad-hoc, so the dataset was not reproducible
> from a public repo at all. It is now recorded as `harness-src/s12_mkniah_generate.sh`.
> **And the result itself has since been replaced**: PN-44's n=100 run supersedes the n=12 reading
> entirely (§6.1). The original flag text is kept below because it is why the run happened.

*(original 2026-09-02 text)* PN-33 and PN-34 made the study's long-context headline on
**MK-NIAH at 131,072: UD-Q6_K_XL 100.0 vs UD-Q4_K_XL 91.67, accuracy recovery 91.67 %**, citing
`data/raw/e12/ruler/s12-ruler.json` (`accuracy_recovery`).

**That file in this repository does not contain it.** Its `accuracy_recovery` block holds only the
three S-NIAH cells (100 / 100 / 100), its `cells` list has no `mkniah` entry, its `tasks` field
reads `["niah", "variable_tracking"]`, and there is no `s12-preds-*-mkniah-*` prediction file.
`data/raw/e12/logs/s12_chain.log` ends at `PHASE summarize OK` with only the three NIAH recoveries.

**The data exists — on the host, not in the repo.** `/srv/bench/e12/ruler/s12-ruler.json`
(mtime 2026-09-02 15:47, 9,253 B against the repo copy's 8,902 B) carries:

```
"131072": { "mkniah:Q4_K_XL": {"score": 91.67, "baseline": 100.0, "accuracy_recovery_pct": 91.67} }
cells: Q6_K_XL mkniah 131072 → 100.0 (n=12, 0 empty, 2164.6 s, prompt_n median 130,935)
       Q4_K_XL mkniah 131072 →  91.67 (n=12, 0 empty, 1949.1 s, prompt_n median 130,935)
```
plus `s12-preds-Q6_K_XL-mkniah-c131072.json` and `s12-preds-Q4_K_XL-mkniah-c131072.json`, and a
`dedup_note` recording the duplicate-c8192 removal that the repo copy also lacks.

**Action, before the repository is made public:** re-pull `ruler/` from the host with
`./tools/sync-multivac.sh artifact /srv/bench/e12/ruler data/raw/e12/`
(the second argument is a destination **directory**; the tool extracts the basename into it, so
passing `.../ruler` would create `data/raw/e12/ruler/ruler`). Until then the
paper's long-context headline has **no evidence in the released artifact set**, and the repo copy
of `s12-ruler.json` is a stale pre-MK-NIAH snapshot that also still contains the two duplicated
c8192 cells L-18 says were deduplicated.

---

### ⚑ F-2 — **RESOLVED by PN-36** — PN-19's UD-Q4_K_XL decode row pools four different context lengths

> **Resolved 2026-09-02.** Found independently by both blind reviews. PN-36 supersedes PN-19's
> statistics and reaches the same conclusion on correct numbers. ⚠ **But the fix introduced two
> new problems of its own — see ⚑F-26**: the spread estimator changed silently, and PN-36's Q6_K
> group of four mixes `-ctxcp 4` with `-ctxcp 32`. The corrected table is at §3.1.

*(original 2026-09-02 text)* PN-19 and `TRACK-A-DECISION.md` both state the decode comparison was made *"at each arm's winning
ratio **at 262,144**, every repetition"*, and give UD-Q4_K_XL as **n=6, [11.81, 12.01, 12.10,
13.12, 13.33, 15.96], median 12.61, within-arm spread 32.9 %**.

Those six readings are the six `-ts 56,44` cells in `tsweep-v2-Q4_K_XL.json`, and they sit at
**four different context lengths**:

| reading | cell key | ctx |
|---|---|---|
| 15.96 | `212992:56,44:1:base` | 212,992 |
| 13.12 | `212992:56,44:2:base` | 212,992 |
| 13.33 | `212992:56,44:3:base` | 212,992 |
| 11.81 | `229376:56,44:1:base` | 229,376 |
| 12.01 | `245760:56,44:1:base` | 245,760 |
| **12.10** | `262144:56,44:1:base` | **262,144 — the only one** |

UD-Q5_K_XL (n=3) and UD-Q6_K (n=3) are correctly three repetitions of one cell at 262,144.
So the comparison is **not like-for-like**: two arms give repetitions at one depth, one arm gives a
depth sweep.

Consequences the paper must handle:
* UD-Q4_K_XL's only 262,144 readings are **12.10** (`-ts 56,44`) and **12.14** (default split),
  n=1 each — not a median of six.
* The headline **"within-arm repetition noise reaches 32.9 %"** is computed across 49,152 tokens of
  context. Recomputed at a **fixed** configuration the spreads are UD-Q4_K_XL **21.3 %**
  (212,992, n=3: 13.12–15.96), UD-Q5_K_XL **16.7 %**, UD-Q6_K **28.6 %** — max **28.6 %**.
* The qualitative conclusion **survives**: 28.6 % noise against a 6.7 % between-arm span is still
  ~4×, so "decode does not discriminate the arms" stands. Only the number changes.
* Note this is the same class of error PN-5 warns about (decode at depth is strongly
  depth-dependent), occurring inside the note that establishes the noise floor.

**Action:** restate PN-19 with either (a) the three 262,144 medians as
Q5_K_XL 12.70 (n=3) · Q4_K_XL 12.10 (n=1) · Q6_K 11.90 (n=3), or (b) the fixed-configuration
spread of 28.6 %. Do not publish "n=6 at 262,144".

---

### ⚑ F-3 — `wave1-summary.md`'s "default-split ceiling" column is contradicted by its own wave

`data/raw/e12/wave1-summary.md` reports UD-Q4_K_XL default-split ceiling **196,608**, gain
**+65,536**. But `tsweep-v2-Q4_K_XL.json` cell **`262144:default:1:base` is `ok: true`**, decode
12.14 tok/s, prefill 544.98 tok/s, prefill_frac 0.948, VRAM 12,116 / 15,094 MiB.
**UD-Q4_K_XL reaches the full native window at the engine default split.** The 196,608 figure is
inherited from the pre-E12 E1b measurement, not from this wave.

Same error, propagated: `CLAUDE.md` §1 says *"All four fail or fall short at the engine's default
split."* True for UD-Q5_K_XL (262,144 default → compute-buffer-oom), UD-Q6_K (262,144 default →
compute-buffer-oom) and UD-Q6_K_XL (196,608 default → compute-buffer-oom). **False for
UD-Q4_K_XL.** PN-6, which makes the rebalance claim, is correctly scoped to UD-Q5_K_XL only and is
unaffected.

Also in that summary: *"Fastest at the full native 262,144 window: Q4_K_XL @ `-ts 56,44` —
13.33 tok/s."* 13.33 is a **212,992** reading (`212992:56,44:3`). At 262,144 that configuration
measures 12.10. PN-20 diagnoses this file as a mixed-**estimator** defect; it is also a
mixed-**context** defect, which PN-20 does not say.

---

### ⚑ F-4 — `s8-scores-reparsed.json` is referenced three times and is not in the repository

L-15, `CLAUDE.md` §7 and `data/raw/e12/s9/s9-scores.json`'s `parser_note` all cite
`s8-scores-reparsed.json` as the repaired S8 scoring with Wilson intervals. It is **not** under
`data/raw/e12/s8/`. It exists on the host at `/srv/bench/e12/s8/s8-scores-reparsed.json`.
The unrepaired `s8-scores.json` **is** in the repo, and its defect is directly visible:
`"parsed": [["humaneval","1"],["humaneval+","1"]]` — the parser captured the `1` from `pass@1`.
The true scores are recoverable from the same file's `raw_tail` and from the per-arm
`*_eval_results.json`. **Action: pull the reparsed file, or the repo publishes only the broken one.**

---

### ⚑ F-5 — **RESOLVED by PN-38** — S11 ran, produced data, and had no paper note

> **Resolved 2026-09-02.** PN-38 documents it, and goes further than this flag did: the metric did
> not merely saturate, it **scrambled the ordering** — the two arms *adjacent* on the ladder
> measured further apart (0.794) than the two *extremes* (0.779). Full numbers at §6.4. PN-38 also
> discloses a second defect this flag missed: S11 suffered its own pad-sizing failure (PN-5's root
> cause repeated), fixed before the numbers now published.

*(original 2026-09-02 text)*

L-17 and L-18 say S11's *"instrument was measured and rejected on its own data"*, and DEC-15
designed it. **No PN entry records S11 at all.** The artifact
`data/raw/e12/s11/s11-divdepth.json` is real and complete for one rung and shows exactly why it
failed: the metric (index of first differing character vs the reference arm) collapses — median
first divergence is **5 / 62 / 10 characters** for Q6_K / Q5_K_XL / Q4_K_XL at ctx 8,192, and
**0 of 9 arm-pad pairs were identical**. A metric that saturates at "immediately" at the shallowest
rung cannot grade depth. Additionally `self_consistency` is `null` — the mandated control never
ran — and only the 8,192 rung of the planned {8,192 · 65,536 · 196,608} was executed.

**This is a publishable negative result about instrument design and it is currently undocumented.**
The rejection also has a second, unremarked cause: with `presence_penalty 1.5` official sampling
absent (S11 used greedy) the generations still diverge at once, which means *greedy trajectory
divergence is not a graded metric for quantization at any depth* — a cleaner statement than the
memory-limit story PN-31 tells about S10. §9 carries the numbers.

---

### ⚑ F-6 — PN-33 cites the wrong reference number for Red Hat

PN-33: *"beside Red Hat's published 85-88 % recovery for INT W4A16 at 128K **(R8)**"*.
In `METHOD-REFERENCES.md`, **R8 is RULER**; Red Hat is **R9** (jointly with arXiv 2505.20276).
Cosmetic, but it will be caught in review.

---

### ⚑ F-7 — R5 (LocalBench) misattributes the 0.01–0.03 Q4_K_M band, and PN-14 inherits it

`METHOD-REFERENCES.md` R5 states LocalBench *"reports observed KLD ≈ 0.01–0.03 for Q4_K_M"*, and
PN-14 places UD-Q4_K_XL's 0.0215 *"inside LocalBench's observed 0.01–0.03 band for Q4_K_M"*.
Verified against the source (`localbench.substack.com/p/gguf-benchmark-methodology`, oobabooga,
2026-04-14), the passage reads:

> "Most KL divergence benchmarks use Wikipedia with ~2048 token context. It's a lot easier to score
> well there. This benchmark uses real-world inputs up to ~30k tokens across 6 task categories,
> which is much harder on quantized models. If you've seen KL values of 0.01-0.03 for Q4_K_M
> **elsewhere**, that's why."

The author is **disclaiming** that range as an artifact of short-context Wikipedia protocols and
reports **higher** divergence. LocalBench publishes no Q4_K_M value of its own. Citing it as the
source inverts the point.

**This correction strengthens the paper.** LocalBench independently argues that quantization
divergence is protocol- and domain-dependent — which is this study's own thesis. Recommended
rewrite: *"LocalBench argues the widely-quoted 0.01–0.03 band for Q4_K_M is an artifact of
short-context Wikipedia protocols and reports higher divergence on ~30k-token real-world inputs;
our 0.021529 on code at n_ctx 2,048 is consistent with that direction."*

---

### ⚑ F-8 — R3's Unsloth Dynamic 2.0 URL is dead (404)

`https://unsloth.ai/docs/basics/unsloth-dynamic-2.0-ggufs` returns **404**;
`https://docs.unsloth.ai/basics/unsloth-dynamic-2.0-ggufs` 301-redirects to the same 404.
`https://unsloth.ai/docs/basics/dynamic-3.0-ggufs` resolves. A dead URL in an arXiv reference list
is a review finding. Cite 3.0, or add a Wayback snapshot for 2.0.

---

### ⚑ F-9 — R9's Red Hat article: the date is wrong, and the source disclaims the conclusion

The URL slug and page header read **2024-02-03**, but the article evaluates Llama-3.1-Instruct
(released July 2024) using RULER (April 2024). The date is a Neural-Magic→Red-Hat migration
artifact. Use 2025 with an access date; do not print 2024-02-03.

More importantly, the article qualifies the very figure PN-33 leans on:

> "at this extreme length, even unquantized models perform poorly (average scores below 65 for both
> sizes). As a result, accuracy recovery at 128K becomes inherently noisy, making it difficult to
> draw definitive conclusions about quantization's impact at this scale."

If the paper places MK-NIAH 91.67 % beside Red Hat's 85–88 %, it must carry that caveat.

---

### ⚑ F-10 — `ssa-results-parsed.json`: one `metrics_reparsed` field is contaminated

L-9(e) records that `ssa_kld.py`'s serverlog label omitted the KV dtype, so the **f16** base run
overwrote the **q4_0** base run's log for the same arm+domain. The consequence is visible in the
artifact: cell `ssa-Q6_K_XL-code-base` (`"kv": "q4_0"`) carries
`metrics.ppl = 1.1809` but `metrics_reparsed.ppl = 1.1791` — the f16 value.

**For that one cell use `metrics`, not `metrics_reparsed`.** Every other cell's `metrics_reparsed`
is the authoritative recovery (PN-17). PN-15's PPL contrast 1.1791 (f16) → 1.1809 (q4_0), +0.15 %,
is correct as written.

---

### ⚑ F-11 — PN-7's VRAM figures for `196608:58,42` do not match the artifact

PN-7 and DEC-7 report UD-Q6_K_XL at `-ts 58,42`, 196,608 as **GPU0 15,036 / GPU1 12,276 MiB,
2,760 MiB GPU0-heavy**. The artifact cell `196608:58,42:1:base` records **12,810 / 10,594 MiB,
imbalance 2,216**. PN-7's own *evidence line* quotes 2,216, so the note is internally inconsistent.
Likely explanation: the cell OOMed, so its VRAM peak is a partial allocation captured at the moment
of failure and is not deterministic; the 15,036/12,276 reading is DEC-7's separate live
observation. **Unreconciled.** Publish the artifact value, or publish neither — a failed cell's
VRAM peak is not a measurement of anything stable.

---

### ⚑ F-12 — Three artifacts referenced by the corpus are host-only (gitignored or never pulled)

| referenced by | path | state |
|---|---|---|
| PN-11, PN-12 | `/srv/bench/power-log.csv` | host only; **all energy and thermal numbers rest on it** |
| PN-17, PN-25, PN-30, PN-31, and every ceiling failure-mode classification | `/srv/bench/server-timings/*.serverlog` | host only, gitignored by design |
| PN-31 | `/srv/bench/server-timings/ramprobe-c{2048,8192,16384}.serverlog` | host only |

For a public repository this is a decision, not a defect — but it must be **stated**, because the
paper's provenance chain is *paper note → artifact → serverlog* and the last link will not ship.
See `PROVENANCE.md` §7.

---

### ⚑ F-13 — Model identity: `Qwen3.8-27B` is a multimodal model, and its citation is a blog post

Verified live on Hugging Face 2026-09-02: `Qwen/Qwen3.8-27B` exists (created 2026-08-05,
architecture `qwen3_5`, pipeline tag **`image-text-to-text`**, 18 safetensors shards, ships
`video_preprocessor_config.json`). Two consequences the manuscript does not currently handle:

1. **It is a vision-language model.** Every measurement here is text-only. The paper must say so;
   a reader will otherwise assume the vision path was exercised.
2. **The official citation is not arXiv 2505.09388.** That is the *Qwen3* technical report, an
   earlier generation. The model card publishes `@misc{qwen38, title={Qwen3.8-Max: A New Bar for
   Coding and Cowork}, url={https://qwen.ai/blog?id=qwen3.8}, author={{Qwen Team}}, ...}`.
   There is **no arXiv paper for Qwen3.8** — a stated limitation.

Also verified: `unsloth/Qwen3.8-27B-GGUF` exists and contains every arm used here, **plus a BF16
(2 shards) and a separate `MTP/mtp-Qwen3.8-27B-Q4_0.gguf` drafter**. G20 ("no BF16 reference on
disk → we cannot compute our own KL divergence") is therefore an availability statement about
*this host*, not about the artifact — BF16 is obtainable; 14 GiB RAM and 2×16 GB VRAM are the
binding constraints. Say it that way.

---

### ⚑ F-14 — "Terminal Bench 2.1 (Terminus) 73.0" has no paper behind it

`data/multivac-src/multivac-CLAUDE.md` lists it among the model's official scores. The
Terminal-Bench paper (arXiv 2601.11868) describes **2.0** (89 tasks) and does not mention
"Terminus". The 73.0 is a leaderboard result on a version the paper does not cover. Cite the paper
for the benchmark and the leaderboard for the score, and label the version.

---

### ⚑ F-15 — R7's arXiv ID is real (checked because it looked implausible)

`arXiv 2601.14277` resolves. **Uygar Kurt**, sole author, *"Which Quantization Should I Use? A
Unified Evaluation of llama.cpp Quantization on Llama-3.1-8B-Instruct"*, v1 2026-01-11, cs.LG,
17 pages. R7's characterisation of it is accurate.

---

### Minor / cosmetic

* **F-16** — R1 quotes the llama.cpp perplexity README as "the **full** WikiText-2 test set". The
  README says "the Wikitext-2 test set". Drop "full" if quoting.
* **F-17** — EvalPlus's title ends **"for Code Generation"**, not "…Code Synthesis" (as written in
  the task brief and in some prose). Corrected in `references.bib`.
* **F-18** — PN-22 describes the S7 p-values as "paired McNemar"; `ssa-s7-paired.json` reports a
  χ² McNemar statistic (`chi2` field), while PN-28's S6 p-values are exact binomial
  (`p_two_sided_exact`). Two different tests, both correctly non-significant. Name each in the table.
* **F-19** — `data/raw/e12/README.md` describes the tree as ~20 pulled files; it now holds 173.
* **F-25** — **PN-35 cites ledger entry `L-19`, which does not exist.** The ledger stops at L-18
  (S12/RULER, 2026-09-02T13:00Z). PN-35 is dated 2026-09-02T18:00Z and is a re-analysis of existing
  data rather than a new run, so no GPU work is missing — but by the project's own hard rule
  (*"a finding that is not written down did not happen"*; a stage that produced findings and
  appended no ledger entry is incomplete), **L-19 needs writing before publication**, and until it
  is, PN-35's provenance line points at nothing. The same gap bit S8, which sat undocumented for a
  day (L-13).
* **F-21** — **not minor; stated in full at §4.0.** Three distinct speculative implementations
  appear in this corpus and its references (llama.cpp's built-in MTP head · the DFlash2 drafter on
  the z-lab fork · the published DFlash / `dflash-mlx` port, never run here), and the pre-E12
  tables mix the first two freely. The losslessness argument turns on keeping them apart.
* **F-22** — R12's supplied metadata needed three corrections, all verified 2026-09-02:
  DFlash is **accepted at ICML 2026** (camera-ready), not a preprint; the authors' own code is
  `github.com/z-lab/dflash` — the **same lab** as our `llama-dflash2:latest` fork, which is a
  provenance link worth stating; and the *"bit-for-bit identical to plain target decoding"* wording
  belongs to the third-party **MLX port**, not (as verified) to the paper. Whether the paper makes
  the same claim was **not checked**. R11 likewise: PaperBanana is a **mixed-affiliation** author
  list, not "Google Research", and its open implementation states it is **not affiliated** with the
  original authors.
* **F-20** — the repo lacks `s11-pads-manifest.json`, `state/progress.json` and
  `quarantine/s11-gen-c8192.json`, all present on the host. Low value, but the quarantine register
  is incomplete without the last one.

---

# §1 — Quantization accuracy and divergence

**Instrument (all rows in this section):** `llama-perplexity --kl-divergence-base` /
`--kl-divergence`, the tool shipped in the engine image (R1). Uncertainties are the tool's own,
computed by treating per-token KLD as Gaussian. **Divergence is ladder-relative to UD-Q6_K_XL.**

**Conditions common to §1:** `n_ctx 2048` · engine **default split** (`-ts` unset — VRAM pressure
negligible at 2K, and a per-arm ratio would be an uncontrolled variable) · `-ngl 99 -fa on` ·
`-ctk/-ctv q4_0` · seed **20260830** · image `sha256:feb0231976b6…` (llamacpp-mtp:latest,
0.3.0-dev build 1, d222767) · greedy is not applicable (no generation; prompt tokens only).

### 1.1 Domain D1 — WikiText-2 prose · n = 65,536 tokens/cell (32 chunks × 2,048)

| arm | mean KLD | top-1 agreement % | median KLD | KLD p90 / p95 / p99 | max KLD | mean Δp % | RMS Δp % |
|---|---|---|---|---|---|---|---|
| UD-Q6_K_XL | *reference, 0 by construction* | — | — | — | — | — | — |
| UD-Q6_K | **0.003321 ± 0.000126** | 97.504 ± 0.086 | 0.001392 | 0.006742 / 0.010549 / 0.028639 | 2.639075 | −0.006 ± 0.009 | 1.595 ± 0.044 |
| UD-Q5_K_XL | **0.004465 ± 0.000281** | 97.141 ± 0.092 | 0.001810 | 0.008856 / 0.013936 / 0.037323 | 6.849877 | −0.020 ± 0.010 | 1.776 ± 0.040 |
| UD-Q4_K_XL | **0.008207 ± 0.000340** | 96.215 ± 0.105 | 0.003509 | 0.016333 / 0.025546 / 0.069578 | 7.600239 | −0.072 ± 0.014 | 2.456 ± 0.059 |

Reference-arm perplexity on the same corpus and settings: **5.7898 ± 0.07421**.
Artifact `data/raw/e12/ssa/ssa-results-parsed.json` (`metrics_reparsed`) · PN-13 · **CURRENT**

### 1.2 Domain D2 — Python/django code corpus · n = 65,536 tokens/cell

| arm | mean KLD | top-1 agreement % | median KLD | KLD p90 / p95 / p99 | max KLD | mean Δp % | RMS Δp % |
|---|---|---|---|---|---|---|---|
| UD-Q6_K | **0.005829 ± 0.000233** | 99.142 ± 0.051 | 0.000007 | 0.003029 / 0.016109 / 0.142839 | 1.659922 | −0.038 ± 0.018 | 3.339 ± 0.095 |
| UD-Q5_K_XL | **0.010285 ± 0.000458** | 98.870 ± 0.058 | 0.000010 | 0.004790 / 0.026311 / 0.250389 | 5.568441 | −0.094 ± 0.024 | 4.375 ± 0.121 |
| UD-Q4_K_XL | **0.021529 ± 0.000834** | 98.430 ± 0.069 | 0.000017 | 0.010006 / 0.055800 / 0.562891 | 5.544760 | −0.192 ± 0.034 | 6.238 ± 0.149 |

Reference-arm perplexity, code corpus, q4_0 KV: **1.1809 ± 0.00610** (use `metrics`, see ⚑F-10).
Corpus `/srv/bench/e12/corpus.txt`, 9,097,163 B (host; gitignored).
Artifact `ssa-results-parsed.json` · PN-13, PN-14 · **CURRENT**

### 1.3 Domain D3 — the 164 HumanEval+ task prompts · n = 18,432 tokens/cell (9 × 2,048)

Forced-reference method (R4): divergence over task prompts with **no generation at all**.
Corpus 74,220 chars, built from the local EvalPlus HumanEval+ set, prompts only, stable task-id order.

| arm | mean KLD | top-1 agreement % | median KLD | KLD p90 / p95 / p99 | max KLD | mean Δp % | RMS Δp % |
|---|---|---|---|---|---|---|---|
| UD-Q6_K | **0.010403 ± 0.000448** | 98.045 ± 0.144 | 0.000197 | 0.020278 / 0.050149 / 0.189885 | 0.845523 | +0.008 ± 0.049 | 4.710 ± 0.153 |
| UD-Q5_K_XL | **0.017285 ± 0.000703** | 97.339 ± 0.168 | 0.000345 | 0.035139 / 0.082368 / 0.313987 | 1.852491 | −0.059 ± 0.062 | 5.951 ± 0.176 |
| UD-Q4_K_XL | **0.036129 ± 0.001534** | 95.894 ± 0.207 | 0.000685 | 0.077069 / 0.175076 / 0.616163 | 5.406369 | −0.759 ± 0.087 | 8.388 ± 0.220 |

Reference-arm perplexity on the prompt corpus: **1.5220 ± 0.01983**.
Artifact `data/raw/e12/ssa/ssa-s5-results.json` · PN-21 · **CURRENT**
⚠ n is 18,432, not 65,536 — intervals are ~1.9× wider than §1.1/§1.2. Not an equal-n comparison.

### 1.4 Derived ratios — the domain hierarchy

| arm | D1 prose | D2 code | D3 task prompts | code ÷ prose | task ÷ prose |
|---|---|---|---|---|---|
| UD-Q6_K | 0.003321 | 0.005829 | 0.010403 | **1.75×** | **3.13×** |
| UD-Q5_K_XL | 0.004465 | 0.010285 | 0.017285 | **2.30×** | **3.87×** |
| UD-Q4_K_XL | 0.008207 | 0.021529 | 0.036129 | **2.62×** | **4.40×** |

Both amplifications grow monotonically with quantization aggressiveness.
Against Fireworks' published <0.007 band (R4): 2 of 3 arms pass on prose, 1 on code, **0 on the
task distribution**. PN-14, PN-21 · **CURRENT**

### 1.5 Adjacent-arm separation

Computed here from the tabled means and tool errors as
`|Δ| / sqrt(err_a² + err_b²)`; **not** a field in the artifact.

| pair | prose (D1) | code (D2) | task prompts (D3) |
|---|---|---|---|
| Q6_K vs Q5_K_XL | **3.71 σ** ← the minimum | 8.67 σ | 8.26 σ |
| Q5_K_XL vs Q4_K_XL | 8.48 σ | **11.82 σ** ← the maximum | 11.17 σ |

PN-13 states the range as **3.7–11.8 σ with non-overlapping intervals**; the recomputation
reproduces both endpoints exactly (3.71 and 11.82). **CURRENT**
⚠ The uncertainties are the tool's own, which treats per-token KLD as Gaussian; tokens within a
2,048-token chunk are not independent, so these σ are **optimistic in the same way** PN-32 shows
pooled acceptance intervals are. The *ordering* and the *order of magnitude* of the separation are
what the data supports, not a precise σ.

### 1.6 The metric-pair inversion (PN-16)

On **code**, every arm shows **higher** top-1 agreement than on prose (98.43–99.14 % vs
96.22–97.50 %) while simultaneously showing **roughly double** the mean KLD. Reconciliation: the
code corpus is far more predictable (reference PPL **1.1809** vs **5.7898**), so the argmax token
survives quantization even as the distribution around it moves more.
Artifact `ssa-results-parsed.json` · PN-16 · **CURRENT** (mechanism is interpretation, not a
controlled test)

### 1.7 The quantile structure — where the code damage actually lives (PN-35)

**PN-14's "code is ~2× worse than prose" is a mean that averages two opposite facts.** Read by
quantile on the identical cells, the ordering **reverses between p90 and p95** for all three arms.
Code ÷ prose ratio of per-token KL divergence:

| statistic | UD-Q6_K | UD-Q5_K_XL | UD-Q4_K_XL | source |
|---|---|---|---|---|
| median | **0.005×** | **0.006×** | **0.005×** | artifact ✅ |
| 90th pct | 0.449× | 0.541× | 0.613× | artifact ✅ |
| **95th pct** | **1.527×** | **1.888×** | **2.184×** | artifact ✅ |
| 99th pct | **4.988×** | **6.709×** | **8.090×** | artifact ✅ |
| 99.9th pct | 6.35× | 8.53× | 8.45× | **serverlog only** ⚠ |
| *mean (PN-14)* | *1.75×* | *2.30×* | *2.62×* | artifact ✅ |
| maximum | 0.629× | 0.813× | 0.730× | artifact ✅ |

Above the crossover the amplification is **monotone in quantization aggressiveness at every
quantile**. The single worst token is *less* perturbed on code than on prose (max 0.63–0.81×), so
the effect is a bounded **p95–p99.9 band**, not an unbounded tail.
Artifact `ssa-results-parsed.json` (`metrics_reparsed`) · PN-35 · **CURRENT**

> ✅ **INDEPENDENTLY RE-DERIVED 2026-09-02**: every ratio above except the p99.9 row was recomputed
> from the shipped artifact and matches PN-35 to three decimal places
> (e.g. UD-Q4_K_XL p99 = 0.562891 / 0.069578 = **8.090×**).

⚑ **F-23 — PN-35's evidence line is wrong about where its own data lives, in a way that matters
for the public repo.** It states: *"The parsed artifact `ssa-results-parsed.json` carries only
`kld_95p`, `kld_99p` and `max_kld` — the median and decile fields exist ONLY in the raw
serverlogs."* That describes the artifact's **`metrics`** field. The **`metrics_reparsed`** field —
the authoritative one, per PN-17 — carries `median_kld`, `kld_90p`, `kld_95p`, `kld_99p`,
`max_kld`, `mean_kld` ± err, `mean_dp_pct` ± err, `rms_dp_pct` ± err and `top1_agree_pct` ± err for
**every** KLD cell. So **six of PN-35's seven rows are reproducible from the shipped repository**;
only the **99.9th percentile** genuinely requires the host-only serverlogs (verified absent from
the artifact). Correcting this turns the finding from "unevidenced in the public repo" into
"evidenced except for one row" — worth fixing before publication.

⚑ **F-24 — PN-35's median row is rounded in a direction that understates the effect.** Its table
gives 0.01× / 0.01× / 0.005×; the artifact gives **0.005× / 0.006× / 0.005×**. PN-35's *prose*
("100–200× LESS") is correct and matches the artifact (1/0.005 = 200, 1/0.006 = 167); only the
table cells are coarsely rounded. Publish the computed values.

**Why this is the mechanism the corpus was missing.** It explains PN-16's paradox quantitatively:
top-1 agreement is *higher* on code (98.4–99.1 % vs 96.2–97.5 %) precisely because ~90 % of code
tokens are trivially predictable and barely perturbed, while mean KLD is double because a thin band
moves enormously. It also predicts the small paired discordances actually observed in the task
benchmarks (3/164 and 5/164, PN-28): damage concentrated in ~1–5 % of positions changes an outcome
only when a tail token lands somewhere decisive.

⚠ **No intervals exist for these ratios.** The tool attaches its uncertainty estimate to the
**mean only**, not to the quantiles. Report them as measured values, not as estimates with error
bars. The crossover is read off a five-point grid, so *"between the 90th and 95th percentile"* is
the resolution the instrument supports.

### 1.8 Published KL divergence — cited, never measured here

| source | figures |
|---|---|
| Unsloth Dynamic v3 GGUF KLD (read off published figures, approximate) | IQ4_XS ≈ 0.019 · Q4_K_XL ≈ 0.0085 · Q5_K_XL ≈ 0.0038 · Q6_K_XL ≈ 0.0016 |
| NVFP4 KLD (Unsloth, text, verbatim) | zh 0.01628 / 93.55 % · code 0.02600 / 96.68 % · refgen 0.03993 / 94.46 % · chat 0.05818 / 92.15 % |

Artifact `/srv/bench/kl-divergence.json` + `/srv/bench/kl-evidence/` (host only) ·
`data/multivac-src/multivac-CLAUDE.md` · no PN · **HISTORICAL-PRE-E12 (cited, not measured)**
⚠ These are a *different vendor's* measurement against FP16. They are not on the same axis as
§1.1–§1.3, which are ladder-relative to UD-Q6_K_XL. Never place them in one table.

### 1.9 Perplexity — pre-E12 corpus, three mutually incompatible protocols

**Protocol 1** — `llama-perplexity`, 602 chunks, n_ctx 512, batch 512, full WikiText-2 test set,
second half of each window scored:

| arm | PPL ± tool err |
|---|---|
| UD-IQ4_XS | 6.6839 ± 0.04133 |
| UD-Q4_K_XL | 6.6617 ± 0.04116 |
| UD-Q5_K_XL | 6.6556 ± 0.04114 |
| UD-Q6_K_XL | 6.6511 ± 0.04111 |
| NVFP4 (vLLM, Protocol-1-matched windows) | 6.7073 |

**Protocol 2** — 20 chunks @ c4096, tensor split, f16 KV: Q3 5.55 · IQ4 5.53 · Q4_K_M 5.50 ·
Q5 5.51 · Q6 5.51.
**NVFP4 native** — 160 chunks, seq 512, stride 512, 77,621 tokens, all positions, no prior
context: avg NLL 2.149994 → PPL **8.5848**.

Artifacts `/srv/bench/perplexity/` (host) · `data/multivac-src/PAPER-REFERENCES.md` · no PN ·
**HISTORICAL-PRE-E12 · IRREPRODUCIBLE-ON-CURRENT-IMAGES** (Protocol 2 and all tensor-split rows).
⚠ Three protocols, three different absolute scales. The corpus files also differ
(`/srv/bench/corpus/wikitext2-test.txt`, 308,707 tokens vs
`/srv/bench/perplexity/wikitext-2-test.txt`, 297,053 tokens).

---

# §2 — Context ceilings and tensor split

**Protocol (Wave 1, `tsweep_v2.py`):** a rung counts as a ceiling only under a **behavioural** gate,
never a VRAM threshold — server healthy · `/props` `n_ctx` == requested · a real prefill to
**≥ 0.90** of the window (measured 0.9435–0.948) · a 192-token generation completes. VRAM is
recorded at 1 Hz and **never gated**. A failed rung above the ceiling is attempted **twice**.

**Conditions common to §2:** `-sm layer` · `-ngl 99` · `-fit off` · `-fa on` · `-ctk/-ctv q4_0` ·
`-b 2048 -ub 512 -np 1` · `-ctxcp 4` · `--spec-type draft-mtp --spec-draft-n-max 2` · seed 20260830
(cells 20260831) · **DEC-2 official non-thinking sampling** (temp 0.7 / top_p 0.80 / top_k 20 /
min_p 0.0 / presence 1.5 / repeat 1.0) — **not greedy** · image `sha256:feb0231976b6…`.

### 2.1 Ceilings — the headline table

| arm | GGUF bytes | ceiling | winning `-ts` | bracketed? | decode @ depth | prefill tok/s | VRAM peak GPU0/GPU1 | imbalance | MTP acc |
|---|---|---|---|---|---|---|---|---|---|
| UD-Q4_K_XL | 17,559,178,144 | **262,144** | `56,44` (default also loads, ⚑F-3) | no rung above exists | 12.10 tok/s (n=1) | 561.62 | 13,334 / 14,780 | 1,446 | 0.6176 |
| UD-Q5_K_XL | 20,876,938,144 | **262,144** | `54,46` | no rung above exists | 10.82 → median-of-3 **12.70** | 522.25 | 14,660 / 15,402 | 742 | 0.516 |
| UD-Q6_K | 21,983,677,344 | **262,144** | `58,42` | no rung above exists | 10.75 → median-of-3 **11.90** | 468.65 | 15,322 / 15,082 | 240 | 0.592 |
| UD-Q6_K_XL | 25,299,061,664 | **212,992** | `56,44` | **yes** — 229,376 failed twice | 12.98 (n=1) | 559.31 | 15,656 / 15,414 | 242 | 0.5886 |

262,144 is the model's native maximum, so three of four ceilings are *"reaches the maximum"*, not
*"was bracketed"*. Only UD-Q6_K_XL has a failed rung above it.
Artifacts `data/raw/e12/tsweep-v2-{Q4_K_XL,Q5_K_XL,Q6_K,Q6_K_XL}.json` · PN-6, PN-7 · **CURRENT**

### 2.2 UD-Q5_K_XL — the causal demonstration that the split sets the ceiling (PN-6)

All ten cells at 262,144, prefill depth 0.948 (248,522 of 262,144 tokens), one variable:

| `-ts` | ok | decode tok/s | prefill tok/s | VRAM GPU0/GPU1 | imbalance MiB |
|---|---|---|---|---|---|
| **default** | **FAIL — compute-buffer-oom** | — | — | 13,540 / 15,070 | 1,530 |
| `54,46` | ok | **10.82** (reps 2,3: 12.70, 12.94 → median 12.70) | 522.25 | 14,660 / 15,402 | 742 |
| `56,44` | ok | 10.78 (reps 2,3: 12.51, 12.91 → median 12.51) | 521.12 | 14,946 / 15,112 | 166 |
| `58,42` | ok | **8.50** — slowest | 530.76 | 15,498 / 15,470 | **28** — most balanced |
| `60,40` | ok | 10.67 | 499.18 | 15,260 / 14,084 | 1,176 |
| `62,38` | ok | 10.44 | 470.49 | 15,546 / 13,796 | 1,750 |

Nine of ten cells ok. **CURRENT.** Supersedes E11a's 196,608 and E1's 163,840 for this arm.

⚑ **PN-39 SCOPES this claim: "the ceiling belongs to the split" holds for TWO of four arms, not for
the ladder.** Every default-split attempt at 262,144:

| arm | default split at 262,144 | attempts |
|---|---|---|
| UD-Q4_K_XL | **LOADS** — ok, decode 12.14 tok/s | 1 |
| UD-Q5_K_XL | fails (compute-buffer-oom) | **1** |
| UD-Q6_K | fails (compute-buffer-oom) | **1** |
| UD-Q6_K_XL | **never attempted** at this length | 0 |

So the claim is demonstrated for UD-Q5_K_XL and UD-Q6_K, **false for UD-Q4_K_XL** — the smallest
arm is the counter-example — and **untested for UD-Q6_K_XL**. The rebalance finding survives: a
ratio sweep moved two arms from failing to reaching the full native window.

⚠ **A second limitation on the same claim: each default-split failure is a SINGLE attempt.** The
project's own bracketing rule (hard rule 4) requires a failed rung to be attempted **twice**,
because layer-split VRAM carries ±100–200 MiB of noise and single failures lie. PN-6's headline and
the README's non-monotonicity headline (`54,46` fails where `58,42` loads) each rest on **one
unreplicated failure**. Re-testing would cost ~20 minutes of GPU and was not done. Until it is,
write **"failed on the single attempt made"**, not "fails". Nothing here affects the *successes* —
every loading ratio is confirmed by a completed run with a real prefill and generation.

**The defensible sentence (PN-39):** *"on this host the tensor split, not the quantization, set the
reachable window for three of the four arms we measured — including both arms in the middle of the
ladder — while the smallest arm reached the native maximum at the engine default."*

⚑ **PN-42 CORRECTS PN-8: "the least balanced ratio that still loads is the fastest" is factually
wrong.** Ordered by imbalance, the same five loading ratios above:

| `-ts` | imbalance | decode | |
|---|---|---|---|
| `58,42` | **28 MiB** — most balanced | **8.50** | slowest by far |
| `56,44` | 166 MiB | 10.78 | |
| `54,46` | 742 MiB | **10.82** | **fastest** |
| `60,40` | 1,176 MiB | 10.67 | |
| `62,38` | **1,750 MiB** — least balanced | 10.44 | |

`54,46` sits in the **middle** of the imbalance ordering, not at the extreme; `62,38` is the least
balanced and is *not* the fastest. **The relationship is not monotone.** Verified against
`tsweep-v2-Q5_K_XL.json` rep-1 cells.

**What survives, and it is the part that mattered:** the *most balanced* ratio is decisively the
slowest (8.50 vs 10.44–10.82, a 27 % gap), so **balance and throughput are different objectives**,
and the selection rule "keep the fastest that loads" is correct while "keep the most balanced"
would have cost ~21 % of decode. What does not survive is any claim of a monotone
imbalance→throughput relationship.
⚠ These are rep-1 readings; the D2 median-of-3 contest (54,46 → 12.70, 56,44 → 12.51) is the
sturdier comparison, and the rep-to-rep spread on a single cell (10.82 → 12.94) is **larger than
most of the inter-ratio gaps** in the table above.

### 2.3 UD-Q6_K — 262,144 reachable at two ratios only

| `-ts` | ok | decode reps | VRAM GPU0/GPU1 | imbalance |
|---|---|---|---|---|
| default | FAIL compute-buffer-oom | — | 14,024 / 15,624 | 1,600 |
| `54,46` | FAIL compute-buffer-oom | — | 15,188 / 15,848 | 660 |
| `56,44` | ok | 10.22 / 14.99 / 11.71 → median **11.71** | 15,528 / 15,586 | 58 |
| **`58,42`** | ok | 10.75 / 14.16 / 11.90 → median **11.90** | 15,322 / 15,082 | 240 |
| `60,40` | FAIL compute-buffer-oom | — | 11,330 / 8,914 (partial) | — |
| `62,38` | FAIL compute-buffer-oom | — | 11,626 / 8,616 (partial) | — |

⚠ D2 contest recorded `58,42` median-of-3 = 11.902 vs `56,44` = 11.714; the artifact's `d2` block
carries both. **CURRENT**

### 2.4 UD-Q6_K_XL — the non-portable optimum (PN-7, DEC-7)

At 196,608, five ratios, one loads:

| `-ts` | ok | decode | VRAM GPU0/GPU1 | imbalance | direction |
|---|---|---|---|---|---|
| default | FAIL | — | 13,810 / 15,616 | 1,806 | GPU1-heavy |
| `52,48` | FAIL | — | 15,090 / 15,538 | 448 | GPU1-heavy |
| `54,46` | FAIL | — | 15,644 / 14,986 | 658 | GPU0-heavy |
| **`56,44`** | **ok** | **17.26 tok/s**, prefill 591.95, depth 0.9474, acc 0.8971 | 15,416 / 15,840 | 424 | — |
| `58,42` | FAIL | — | 12,810 / 10,594 (partial; ⚑F-11) | 2,216 | GPU0-heavy |

Then 212,992 at `56,44` **ok** (12.98 tok/s, prefill 559.31, depth 0.9469, acc 0.5886,
15,656 / 15,414, imb 242); 229,376 at `56,44` **failed twice** → ceiling bracketed at **212,992**.
17.26 tok/s at 196,608 is the **highest single decode reading of the wave**. **CURRENT**

### 2.5 `-ctxcp` 4 vs 32 — a free throughput gain (PN-18)

A/B at UD-Q6_K, 262,144, `-ts 58,42`, both at depth 0.948, everything else identical:

| `-ctxcp` | decode tok/s | prefill tok/s | VRAM GPU0/GPU1 |
|---|---|---|---|
| 4 | 10.749 | 468.65 | 15,322 / 15,082 |
| 32 | **11.482 (+6.8 %)** | **504.34 (+7.6 %)** | 15,322 / 15,082 (**Δ 0 MiB**) |

Artifact `tsweep-v2-Q6_K.json` `d3` block · verdict in-artifact: *"adopt ctxcp 32 for Waves 2-4"* ·
PN-18 · **CURRENT — directional**. n=1 A/B, one quant, one context; the 6.8 % gain is the same
order as this host's rep-to-rep decode noise, so **adopt the setting, do not quote the number**.

### 2.6 Historical ceilings — superseded or irreproducible

| measurement | value | status |
|---|---|---|
| E1: UD-Q6_K_XL + MTP n2 + q4_0 + layer, default split | 131,072 (OOM-verified at 147,456+) | **SUPERSEDED** by §2.1 (212,992 @ `56,44`) |
| E1: UD-Q6_K_XL no-spec | 245,760 | CURRENT for that config; no-spec, not comparable to §2.1 |
| E1: UD-Q6_K_XL f16 KV | 98,304 | CURRENT for that config |
| E1: UD-Q6_K_XL f16 + MTP | < 65,536 | CURRENT for that config |
| E1b: UD-Q4_K_XL | 196,608 (262,144/229,376 = init-hang, not OOM) | **SUPERSEDED** by §2.1 and ⚑F-3 |
| E1b: UD-Q5_K_XL | 163,840 | **SUPERSEDED** by §2.2 — E1's rejection was a VRAM-gate artifact (15,794 vs a 15,700 MiB gate) |
| E1b: UD-IQ4_XS | 262,144 ✓ (39.5 tok/s, peak 14,474 MiB) | CURRENT; arm dropped from scope (DEC-4) |
| E11a: UD-Q5_K_XL + MTP n2 | 196,608 | **SUPERSEDED** by §2.2 |
| E11a: UD-Q6_K + MTP n2 | 196,608 @ 7.19 tok/s at depth 186,265 | **SUPERSEDED** by §2.3 |
| E11a: UD-Q6_K no-spec | 262,144 @ 3.45 tok/s | superseded on speed by §4.5 (3.431) |
| E11c: UD-Q6_K + MTP n2 `-ts 58,42` | 262,144 @ 13.85 tok/s, acc 0.889 | **SUPERSEDED** by §2.3 (different sampling; E11c was greedy) |
| Every 262,144 result and every `-sm tensor` result before 2026-08-29 | — | **IRREPRODUCIBLE-ON-CURRENT-IMAGES** |
| UD-Q5_K_XL f16 KV | 147,456 (15,198 MiB) | HISTORICAL-PRE-E12 |
| UD-IQ4_XS f16 KV | ~245,760 (bisect, no-spec) | HISTORICAL-PRE-E12 |
| vLLM NVFP4, nightly, gmu 0.97 | KV pool 52,337 tokens → **51,200** bootable | HISTORICAL-PRE-E12; arm eliminated (E11 decision) |
| vLLM NVFP4, stable v0.27.1 | 98,304 (≈48K with MTP) | HISTORICAL-PRE-E12 |

Sources `data/multivac-src/multivac-CLAUDE.md`, `/srv/bench/{q6-ceiling,ctx-ceilings}.json` (host).

### 2.7 Split-mode reproducibility (E6)

| image | `-sm layer` | `-sm tensor` | `-sm row` |
|---|---|---|---|
| `llamacpp-mtp:latest` | ✓ 39.3 tok/s @ ctx 32,768 | ✗ CUDA illegal memory access | ✗ (no split buffers) |
| `llama-dflash2:latest` | ✓ 35.6 tok/s | ✗ CUDA illegal memory access | ✗ |

Artifact `/srv/bench/splitmode-repro.json` (host) + `data/archive/aug20-splitmode-matrix.txt`
(the 2026-08-20 origin of the finding, on image `llamacpp-nccl231:latest`, ctx 32,768, q8_0 KV) ·
no PN · **CURRENT** (E6) / **HISTORICAL-PRE-E12** (the aug20 matrix).
⇒ **`-sm layer` is the only reproducible split mode on this host.** Every `-sm tensor` row anywhere
in this corpus is IRREPRODUCIBLE-ON-CURRENT-IMAGES.

### 2.8 The VRAM model (pre-E12, and its correction)

```
VRAM_per_GPU(MiB) ≈ (file_bytes / 2^30 / 2) · 1024  +  ctx · rate  +  180–420 fixed
rate:  q4_0 = 16.0 KiB/token/GPU      f16 ≈ 34.5 KiB/token/GPU      (both under -sm tensor)
practical ceiling ≈ 15,650 MiB/GPU    card total 16,311 MiB
```
Measured slope: 131,072 → 196,608 → 262,144 gives 13,134 → 14,158 → 15,182 MiB/GPU = exactly
**+1,024 MiB per +65,536 tokens**. Validated against three independent points to ≤0.2 %.
**HISTORICAL-PRE-E12 · IRREPRODUCIBLE-ON-CURRENT-IMAGES** (tensor split).
⚠ E1 measured the **layer-split** q4_0 slope at ~16.5 KiB/token/GPU — i.e. the same as tensor. The
"layer split halves per-GPU KV" hypothesis is **REFUTED**.

**q8_0 KV is broken on this stack** — three independent failures (illegal memory access @c4096;
"failed to allocate" @262K; "FAIL out of memory" @262K). `{f16, q4_0}` are the only viable KV
dtypes. `data/raw/e12/env-manifest.json` `notes` · **CURRENT**

---

# §3 — Speed and throughput

**⚠ The single most abused axis in this corpus.** Three protocols exist and none is comparable to
another:

| protocol | what it measures | typical Q6_K figure |
|---|---|---|
| **P-depth0** | decode into a nearly *empty* KV cache in a large *allocated* window | 37.2–47.0 tok/s |
| **P-atdepth** | decode after a real prefill to ≥0.90 of the window | 3.4–17.3 tok/s |
| **P-32k** | ctx 32,768, real generations, effectively shallow | 16.1–51.8 tok/s |

They differ by 3–5×. Never place two of them in one table.

### 3.1 At-depth decode at 262,144, per arm (Wave 1) — the Track A speed evidence

DEC-2 official sampling · q4_0 KV · MTP n=2 · `-ctxcp 4` · depth 0.948 · 192 generated tokens.

**TRUE repetition groups only** — same arm, same context, same `-ts`, **same `-ctxcp`** — recomputed
here from the cells' own `key` and `ctxcp` fields. Both spread estimators are given, because PN-19
and PN-36 use different ones (⚑F-26):

| arm | `-ts` | `-ctxcp` | n | readings | median | `(max−min)/min` | `(max−min)/median` |
|---|---|---|---|---|---|---|---|
| UD-Q5_K_XL | `54,46` | 4 | 3 | 10.82 · 12.70 · 12.94 | **12.70** | 19.6 % | 16.7 % |
| UD-Q5_K_XL | `56,44` | 4 | 3 | 10.78 · 12.51 · 12.91 | 12.51 | 19.8 % | 17.0 % |
| UD-Q6_K | `58,42` | 4 | 3 | 10.75 · 14.16 · 11.90 | **11.90** | 31.7 % | 28.7 % |
| UD-Q6_K | `56,44` | 4 | 3 | 10.22 · 14.99 · 11.71 | 11.71 | **46.7 %** | **40.7 %** |
| UD-Q6_K | `58,42` | **32** | 1 | 11.48 | — | — | — |
| UD-Q4_K_XL | `56,44` | 4 | **1** | 12.10 | — | not computable | not computable |
| UD-Q4_K_XL | default | 4 | **1** | 12.14 | — | not computable | not computable |

**Matched-depth between-arm span** (each arm's winning ratio, `-ctxcp 4` only):
UD-Q5_K_XL 12.70 · UD-Q4_K_XL 12.10 (n=1) · UD-Q6_K 11.90 → **6.7 %**.
⚠ PN-36 reports **8.6 %**, which comes from a UD-Q6_K median of 11.69 computed over a group that
includes the `-ctxcp 32` cell. See ⚑F-26 — the clean figure is 6.7 %, and it is also what
`TRACK-A-DECISION.md` cites.

**The conclusion, on any of these definitions:** within-configuration noise (**19.6–46.7 %**)
exceeds the between-arm difference (**6.7–8.6 %**) by roughly **5×**. The arms are **not separated
on decode throughput.** PN-36 is right that the corrected numbers support this *better* than the
originals did.

⚑ **UD-Q4_K_XL has no repetition group at 262,144 at all** — a single reading. Any three-arm speed
comparison at the full window is two arms with medians of three and one arm with **n=1**, and must
be reported that way.

**A separately reportable observation** that contaminated the original figure: on UD-Q4_K_XL decode
falls with depth — ~13.3 tok/s at 212,992 → 12.10 at 262,144 (§2.1 cells).

Artifacts `tsweep-v2-*.json` · **PN-36 supersedes PN-19** · PN-20 · **CURRENT**

### 3.2 Prefill at depth (Wave 1, ~0.948 of window, 248,522 prompt tokens)

| arm | `-ts` | prefill tok/s @262,144 |
|---|---|---|
| UD-Q4_K_XL | `56,44` | 561.62 · default 544.98 |
| UD-Q5_K_XL | `54,46` | 522.25 (reps 524.34, 524.16) |
| UD-Q6_K | `58,42` | 468.65 (`-ctxcp 32`: 504.34) |
| UD-Q6_K_XL | `56,44` @212,992 (201,672 tok) | 559.31 · @196,608 (186,265 tok) 591.95 |

Prefill falls monotonically with depth within an arm (UD-Q4_K_XL: 630.16 @212,992 → 606.97
@229,376 → 582.12 @245,760 → 561.62 @262,144).
No PN carries the prefill-vs-depth curve. · **UNWRITTEN — CURRENT**

### 3.3 Decode at ctx 32,768 (P-32k), greedy, UD-Q6_K, `-ts 58,42`, `-ctxcp 32`

Medians over 164 real HumanEval+ generations, `max_tokens` 1024, seed 20260830:

| config | decode tok/s | × no-spec | draft acceptance | n |
|---|---|---|---|---|
| no-spec | **18.463** | 1.00× | — | 164 |
| MTP n=2 | **37.429** | 2.03× | 0.9536 | 164 |
| MTP n=4 | **47.024** | 2.55× | 0.8922 | 164 |
| DFlash2 n=4 (impl. **B**, `llama-dflash2:latest`) | **51.780** | 2.80× | 0.9172 | 164 |

Artifacts `data/raw/e12/s8/s8-humaneval.json`, `data/raw/e12/s9/s9-dflash.json` · PN-24, PN-29 ·
**CURRENT**. ⚠ The first three rows are **implementation A**; the fourth is **implementation B on
a different engine image** (§4.0). A table printing all four must say so in the table, because the
2.80× is partly an engine comparison and partly a drafter comparison and the data cannot separate
them.
Repeat measurement a day later (S9a): no-spec **18.485**, MTP n=2 **37.837**
(`s9-determinism.json`) — a 0.1 % and 1.1 % difference, and the completions were byte-identical.

### 3.4 Decode at ctx 32,768, DEC-2 official sampling, no-spec (S6)

| arm | decode tok/s median | n | wall s |
|---|---|---|---|
| UD-Q4_K_XL | **22.153** | 164 | 1,874.4 |
| UD-Q6_K_XL | **16.063** | 164 | 2,780.2 |

Artifact `data/raw/e12/s9/s9-s6.json` · **UNWRITTEN** (L-15 deliberately withheld the note).
A 37.9 % gap between ladder extremes at 32,768, against 6.7 % at 262,144 (§3.1) — suggesting the
inter-quant speed gap *shrinks* with depth. **Confounded**: the two measurements differ in spec
setting, sampling and `-ts`. S9d was to resolve it and failed on power (§4.6). Report as
"suggestive, confounded, unresolved" or not at all.

### 3.5 Decode at ctx 8,192, greedy, no-spec, `-ts 56,44` (S11) — monotone in quant size

| arm | decode tok/s (3 pads) | median | prefill tok/s |
|---|---|---|---|
| UD-Q6_K_XL | 13.978 · 14.408 · 14.548 | 14.408 | 939–1,212 |
| UD-Q6_K | 15.554 · 16.160 · 16.348 | 16.160 | 995–1,165 |
| UD-Q5_K_XL | 16.228 · 17.068 · 17.146 | 17.068 | 1,037–1,244 |
| UD-Q4_K_XL | 18.989 · 18.592 · 18.962 | 18.962 | 868–1,313 |

Artifact `data/raw/e12/s11/s11-divdepth.json` · **UNWRITTEN — CURRENT**.
Cleanest cross-quant speed comparison in the corpus: **one fixed `-ts` for all four arms**, one
depth, no spec, greedy, identical prompts. Spread 14.4 → 19.0 tok/s = **31.6 %**, monotone in file
size, and rep-to-rep spread within a cell is only **1.9–4.1 %** — far below the at-depth noise.
This is the row that shows the 6.7 % at-262,144 null is a *depth* effect, not a general one.

### 3.6 Decode at matched depth, 4 arms × 3 draft depths (S9d) — see §4.6 for the caveat

Medians of 3, 512-token generations, prompt_n held identical per rung, DEC-2 sampling, `-ctxcp 32`,
each arm at its own Wave-1 `-ts`:

| arm | 131,072 n2 / n4 / n8 | 196,608 n2 / n4 / n8 |
|---|---|---|
| UD-Q4_K_XL `56,44` | 19.124 / 20.252 / 26.320 | 14.721 / *(invalid)* / 23.588 |
| UD-Q5_K_XL `54,46` | 19.764 / 17.699 / 24.701 | 14.254 / 13.862 / 26.199 |
| UD-Q6_K `58,42` | 18.507 / 20.111 / 15.331 | 18.749 / 24.997 / 33.985 |
| UD-Q6_K_XL `56,44` | 17.948 / *(invalid)* / 17.695 | 13.870 / 17.983 / *(load fail)* |

Artifact `data/raw/e12/s9/s9d-depthsweep.json` · PN-32 · **CURRENT but UNRANKABLE**.
Rep-to-rep spread reaches **166.1 %** (median 33.8 %, 74.8 % for n=8 cells). **These cells cannot
rank anything.** Publish them as a demonstration of the noise, not as a result.

### 3.7 Historical speed — depth-0, deleted image

| config | ctx | tok/s | J/tok |
|---|---|---|---|
| IQ4_XS DFlash2 n=4 | 32,768 | **57.5** | 3.70 |
| Q6_K_XL DFlash2 n=4 | 32,768 | 44.7 | 4.79 |
| IQ4_XS MTP n=2 | 32,768 | 46.9 | 4.35 |
| Q6_K_XL MTP n=2 | 32,768 | 31.7 | 6.29 |
| IQ4_XS no-spec | 32,768 | 27.2 | 7.46 |
| Q6_K_XL no-spec | 32,768 | 16.5 | 11.78 |
| Q3_K_XL MTP n=8 | — | 116.9 | — |
| vLLM NVFP4 no-spec (TP=2, fp8 KV, eager) | — | 12.44 | — |
| vLLM NVFP4 MTP ns=2 | — | 28.11 (2.26×) | — |
| vLLM NVFP4 MTP ns=4 | — | 41.21 (3.31×) | — |
| vLLM NVFP4 DFlash2 | — | **INFEASIBLE — OOM on 2×16 GB** | — |

`data/multivac-src/multivac-CLAUDE.md` · `data/archive/spec-speed-metrics.jsonl` (12 rows) ·
**HISTORICAL-PRE-E12 · IRREPRODUCIBLE-ON-CURRENT-IMAGES · P-depth0**.

### 3.8 Historical long-context decode (tensor split, deleted image)

| config | served ctx | actual ctx | decode tok/s | acceptance |
|---|---|---|---|---|
| Q3_K_XL-embedded + MTP n2 | 262,144 | 258,779 | 45.17 | 1.000 |
| Q3_K_XL-embedded + MTP n2 | 262,144 | 248,368 | 44.61 | 1.000 |
| Q3_K_XL-embedded + MTP n2 | 262,144 | 179,709 | 50.12 | 1.000 |
| Q3_K_XL-embedded + MTP n2 | 262,144 | 99,885 | 59.27 | 1.000 |
| Q5_K_XL-embedded + MTP n2 | 147,456 | 139,872 | 42.86 | 1.000 |
| IQ4_XS + MTP n2 (layer) | 184,320 | 168,011 | 32.62 / 29.53 / 28.55 | 0.922 / 0.801 / 0.752 |
| IQ4_XS + DFlash2 n4 (layer) | 196,608 | 184,011 | 30.26 / 23.88 / 22.91 | 0.553 / 0.410 / 0.434 |
| Q4_K_M + MTP n2 (layer) | 163,840 | 152,011 | 28.65 / 28.60 | 0.882 / 0.876 |
| IQ4_XS no-spec (layer) | 184,320 | 40,347 | 23.22 / 23.11 | — |

**HISTORICAL-PRE-E12 · IRREPRODUCIBLE-ON-CURRENT-IMAGES.** The Q3_K_XL and Q4_K_M GGUFs are also
gone from disk. KV dtype of these runs is **unrecorded** (G11 → labelled KV-UNKNOWN, E10).

### 3.9 The depth-0 vs at-depth correction (E11)

Same server, same flags, UD-Q6_K + MTP n=2 @196,608 (greedy, default split):
**depth 0 → 37.22 tok/s** (median over 40 tasks, MTP acceptance 0.986) ·
**depth 186,265 → 7.19 tok/s (−81 %)**.
`/srv/bench/e11/depthbench-Q6K-mtp196.json` (host) · **HISTORICAL-PRE-E12** but the *lesson* is
CURRENT and load-bearing: it is why every Wave-1 row is measured at ≥0.90 depth.

---

# §4 — Speculative decoding

## §4.0 — WHICH IMPLEMENTATION IS BEING MEASURED (read before using any row here)

**The paper's losslessness argument turns on not conflating these.** Three distinct speculative
implementations appear in this corpus and in its references, with three different verification
paths. A row from one says nothing about another.

| # | implementation | what it is | engine | measured here? | rows |
|---|---|---|---|---|---|
| **A** | **llama.cpp built-in MTP head** (`--spec-type draft-mtp`) | the model's own multi-token-prediction head; **no separate draft model**. The engine builds a *separate draft context against the target model* (`common_speculative_init_result` in the serverlog), which is why enabling it costs window | `llamacpp-mtp:latest` `sha256:feb0231976b6…` | **YES — this is what PN-23 and PN-26 measure** | §4.1 (n=2, n=4), §4.2, §4.3, §4.5 (withdrawn), §4.6, and every Wave-1 ceiling in §2 |
| **B** | **DFlash2 drafter** on the z-lab llama.cpp fork | a separate 1.14 GB block-diffusion draft model (`Qwen3.8-27B-DFlash2-Q4_K_M.gguf`) verified by the target | `llama-dflash2:latest` `sha256:22bb8b7fed8b…` (0.1.2-dev build 50, f7aadef) — **requires `--entrypoint /app/llama-server`** | **YES, but only in S9c** | §4.4, and the 51.78 tok/s row in §3.3 |
| **C** | **DFlash reference / `dflash-mlx` port** | the published method (`chen2026dflash`, ICML 2026) and a third-party Apple-Silicon port | not on this host | **NO — never run here** | reference only |

**Rules that follow, and they are not optional:**

1. **PN-23's and PN-26's non-equivalence result is about implementation A only.** It is
   `--spec-type draft-mtp` on `llamacpp-mtp:latest`. Do not state it as a result about
   "speculative decoding" without naming the implementation, and do not state it as a result
   about DFlash.
2. **The DFlash2 equivalence figure (132/164, §4.4) is ENGINE-CONFOUNDED and must never appear
   beside MTP's 131/164.** Its no-spec baseline was generated on `llamacpp-mtp:latest` while the
   arm ran on `llama-dflash2:latest`, so an engine-version difference is inseparable from the
   speculation effect. The two numbers look comparable and are not.
3. **The "bit-for-bit identical to plain target decoding" claim (R12) is made by the `dflash-mlx`
   port** — implementation C — describing a verification rule of *longest matching prefix plus one
   bonus correction token*. Whether the ICML paper itself uses that wording was **not verified**.
   Our counter-measurement is on implementation **A**. The honest statement is therefore:
   *"speculative decoding is lossless" is an implementation property that must be verified per
   stack, not inherited from the algorithm's specification* — **not** "DFlash's losslessness claim
   is false", which we did not test.
4. **All five S8 DFlash cells are EXCLUDED (PN-25)**, because they were launched on implementation
   A's engine with implementation B's drafter — a mis-binding that produced `0.000 pass@1` and
   `generate-failed`, values indistinguishable in a table from a model that ran and failed. S9c
   (§4.4) is the only valid DFlash2 measurement in the corpus.
5. **Acceptance rates are not comparable across A and B**, both because the drafters differ and
   because the sampling differs between Wave 1 (DEC-2 official) and S8/S9 (greedy).

⚑ **F-21** — `data/multivac-src/multivac-CLAUDE.md` and the pre-E12 tables mix A and B freely
(e.g. "IQ4_XS DFlash2 n=4 57.5 tok/s" beside "IQ4_XS MTP n=2 46.9"). Those rows are additionally
**IRREPRODUCIBLE-ON-CURRENT-IMAGES** and depth-0. They may be reported as historical context; they
may not be used to compare A against B under the current protocol. The only current-protocol A-vs-B
comparison is §3.3 at ctx 32,768 — and even there the arms sit on **two different engine images**,
which the table must say.

---

### 4.1 Output equivalence at greedy (S8) — the premise this study retired
**Implementation A (llama.cpp built-in MTP head), except the last row.**

164 HumanEval+ problems · UD-Q6_K · ctx 32,768 · `-ts 58,42` · `-ctxcp 32` · q4_0 KV ·
**greedy (temperature 0, top_p 1), seed 20260830** — a deliberate departure from DEC-2, because
exact-match equivalence is only meaningful at greedy · `max_tokens` 1024 · image `feb0231976b6…`.

| arm vs no-spec baseline | exact match | differs | % identical | first divergence, median char |
|---|---|---|---|---|
| MTP n=2 | **131 / 164** | 33 | **79.88 %** | 715 |
| MTP n=4 | **131 / 164** | 33 | **79.88 %** | 730 |
| DFlash2 n=4 (⚠ different engine image) | 132 / 164 | 32 | 80.49 % | 730 |

Divergence-set overlap between MTP n=2 and n=4: **Jaccard 0.6098** (25 shared, 8 unique each).
Artifacts `s8-humaneval.json` (`equivalence`), `s9-determinism.json` (`comparisons`,
`set_overlap`), per-problem completions in `s8-{nospec,mtp2,mtp4}.jsonl` and `s9-dflash4-he.jsonl`.
The 33 divergent `task_id`s are listed per arm in `s9-determinism.json`. PN-23, PN-26, PN-29 ·
**CURRENT**

### 4.2 The determinism control (S9a) — what it settled and what it withdrew

Re-ran S8's two configurations unchanged a day later:

| comparison | n | exact match | differs | verdict |
|---|---|---|---|---|
| S8 no-spec vs S9 no-spec-r2 | 164 | 164 | **0** | byte-identical |
| S8 MTP n=2 vs S9 MTP n=2-r2 | 164 | 164 | **0** | byte-identical |
| S8 no-spec vs S8 MTP n=2 | 164 | 131 | 33 | different |
| S8 no-spec vs S8 MTP n=4 | 164 | 131 | 33 | different |

Wall/throughput across the repeat: no-spec 2,441.4 s / 18.463 tok/s → 2,499.0 s / 18.485 tok/s.
MTP n=2 → 1,243.9 s / 37.837 tok/s.
Independent confirmation through a second pipeline: `nospec-r2` scores **0.945 / 0.915** and
`mtp2-r2` **0.939 / 0.902**, identical to their S8 originals.
Artifact `s9-determinism.json` · PN-26 · **CURRENT**

⇒ **The engine is deterministic; speculation is a reproducibly different decode path.**
⇒ **PN-23's proposed mechanism (float nondeterminism from a changed decode batch shape) is
WITHDRAWN.** PN-23's numbers stand. Where in verification the difference arises is unresolved and
needs engine-level instrumentation.

> ✅ **INDEPENDENTLY RE-DERIVED 2026-09-02 from the raw completions, and every figure reproduces
> exactly.** Recomputed from `s8-{nospec,mtp2,mtp4}.jsonl` and `s9-{nospec-r2,mtp2-r2}.jsonl`
> without reading any summary field:
> `nospec` self-identity **164/164, differs 0** · `mtp2` self-identity **164/164, differs 0** ·
> `nospec` vs `mtp2` **131 identical / 33 differ** · `nospec` vs `mtp4` **131 / 33** ·
> divergence-set overlap **25 shared, 8 unique to each, Jaccard 0.6098**.
> **PN-26's md5 `37616d8911fb4792fb76cadf0806511c` is confirmed**: it is the md5 of the raw
> `.jsonl` file, and `s8-nospec.jsonl` and `s9-nospec-r2.jsonl` hash to it **identically**. The
> hash is not a field in any artifact — it is a property of the shipped files, and it holds.
> **This is the most thoroughly verified result in the corpus.**

### 4.3 Draft acceptance — per quant, and its confounds

| source | arm | ctx | `-ts` | n_draft | acceptance | note |
|---|---|---|---|---|---|---|
| Wave 1 | UD-Q6_K_XL | 196,608 | `56,44` | 2 | **0.8971** | PN-9 |
| Wave 1 | UD-Q6_K_XL | 212,992 | `56,44` | 2 | 0.5886 | |
| Wave 1 | UD-Q5_K_XL | 262,144 | `54,46` | 2 | **0.516** (reps 2,3: 0.6937, 0.7338) | PN-9 |
| Wave 1 | UD-Q6_K | 262,144 | `58,42` | 2 | **0.592** (reps 2,3: 0.9111, 0.6105) | |
| Wave 1 | UD-Q4_K_XL | 262,144 | `56,44` | 2 | 0.6176 | |
| Wave 1 (quarantined) | UD-Q4_K_XL | 212,992 | — | 2 | 0.5642 | PN-9 cites this — from cells later quarantined for shallow prefill |
| S8 | UD-Q6_K | 32,768 | `58,42` | 2 | 0.9536 | |
| S8 | UD-Q6_K | 32,768 | `58,42` | 4 | 0.8922 | |
| S9c | UD-Q6_K | 32,768 | `58,42` | DFlash2 n4 | 0.9172 | different image |
| S9c | UD-Q6_K | 163,840 | `58,42` | DFlash2 n4 | **0.4583** | acceptance halves with depth |

⚑ **PN-9's three-quant acceptance comparison (0.897 / 0.564 / 0.516) is confounded three ways** —
the cells differ in context (196,608 / 212,992 / 262,144), in `-ts` ratio, and one of them comes
from quarantined data. PN-9 states this itself. **S9d was reinstated to resolve it and did not
(§4.6). The confound is permanent and must be a stated limitation.**

Also note the strong **within-cell** instability: UD-Q6_K at 262,144 `58,42` reads 0.592 / 0.9111 /
0.6105 across three identical repetitions. A single-rep acceptance figure on this host is not an
estimate.

### 4.4 DFlash2 (S9c) — measured at last, on its correct engine
**Implementation B. The only valid DFlash2 measurement in this corpus.**

Engine `llama-dflash2:latest` (`sha256:22bb8b7fed8b…`, 0.1.2-dev build 50, f7aadef) with
`--entrypoint /app/llama-server`; drafter `Qwen3.8-27B-DFlash2-Q4_K_M.gguf`, 1,143,006,752 B,
sha256 `18a380efc9b7ed8d88677fc895f5c11ae170653434ee378f7348f715c14d0594`.

| ctx | ok | decode tok/s | prefill tok/s | prefill_frac | acceptance |
|---|---|---|---|---|---|
| 32,768 | ok | **51.780** (median of 164) | — | — | 0.9172 |
| 262,144 | **FAIL — compute-buffer-oom** | — | — | — | — |
| 212,992 | **FAIL — compute-buffer-oom** | — | — | — | — |
| 163,840 | ok | **8.343** | 581.61 | 0.9978 | **0.4583** |

pass@1 at 32,768: **93.29 / 90.24**, Wilson 95 % [88.39, 96.21], 164 items, 0 empty.
The "1.19 GiB draft-worker wall": the Track A config peaks at 15,322 / 15,082 MiB — ~330 MiB of
headroom on the binding card against a ~1,090 MiB drafter.
Artifact `data/raw/e12/s9/s9-dflash.json` · PN-29 · **CURRENT**
⚠ 262,144 and 212,992 are **single attempts**, not the two-attempt bracket the ceiling rule
requires. "163,840 is DFlash2's ceiling" is a demonstrated lower bound, not a bracketed ceiling.
⚠ The equivalence figure (132/164) is **engine-confounded** — the baseline was produced on
`llamacpp-mtp:latest`. Never quote it beside MTP's 131/164.

### 4.5 At-depth speed by spec method (S8 phase 3) — **WITHDRAWN**

| config | ctx | decode tok/s | prefill tok/s | prompt_n | prefill_frac |
|---|---|---|---|---|---|
| no-spec | 262,144 | 3.431 | 594.52 | 246,176 | 0.9391 |
| MTP n=2 | 262,144 | 11.481 | 506.09 | 246,176 | 0.9391 |
| MTP n=4 | 262,144 | 16.808 | 485.55 | 246,176 | 0.9391 |
| DFlash2 n=4 | 262,144 / 212,992 / 163,840 / 131,072 | all `generate-failed` | — | — | — |

**STATUS: WITHDRAWN (PN-30).** Every one of these cells timed **17 generated tokens**, not the
192 requested: the probe posted the pad to `/v1/chat/completions` with no instruction, so the model
acknowledged briefly and stopped. The engine's own log says so:
`eval time = 951.92 ms / 17 tokens (59.49 ms per token, 16.81 tokens per second)` and
`draft acceptance = 1.00000 (16 accepted / 16 generated)`. Acceptance reads exactly 1.000 for both
MTP arms, which is the tell.
The **four DFlash2 rows are separately EXCLUDED (PN-25)** — they ran on `llamacpp-mtp:latest`,
which cannot parse the drafter (`done_getting_tensors: wrong number of tensors; expected 81,
got 58`); the server exited during load, hence `Connection refused`.
Artifact `data/raw/e12/s8/s8-atdepth.json` · retained, never deleted.

### 4.6 Draft depth at matched depth (S9d, re-run) and at the deployment window (S9e)

**S9d design:** 4 arms × 2 depths {131,072 · 196,608} × n_draft {2,4,8} = 24 cells, 3 × 512-token
generations each, prompt_n held **identical** at each rung (123,670 and 186,270), each arm at its
own Wave-1 `-ts`, DEC-2 sampling, q4_0 KV, `-ctxcp 32`. Gate: `prefill_frac ≥ 0.90` **and** an
absolute floor of 128 generated tokens per rep, both asserted in code.
Outcome: **21 valid · 2 caught by the generation gate (shortest rep 55 and 124 tokens) · 1 load
failure** (UD-Q6_K_XL @196,608 n=8).

**Acceptance vs draft depth** (the one result that survives):

| arm | 131,072 n2 / n4 / n8 | 196,608 n2 / n4 / n8 |
|---|---|---|
| UD-Q4_K_XL | 0.6727 / 0.5123 / 0.4036 | 0.6662 / *(invalid)* / 0.3725 |
| UD-Q5_K_XL | 0.8139 / 0.4925 / 0.4485 | 0.7461 / 0.4286 / **0.5734 ↑** |
| UD-Q6_K | 0.7747 / 0.5578 / 0.2510 | 0.9198 / 0.7899 / 0.5168 |
| UD-Q6_K_XL | 0.7590 / *(invalid)* / 0.3316 | 0.7044 / 0.5558 / *(fail)* |

**Acceptance fell in 12 of 13 adjacent draft-depth pairs; one-sided sign test p = 0.0017**
(verified independently: 14/8192 = 0.001709). Range 0.6662–0.9198 at n=2 → 0.2510–0.5734 at n=8.
The single rise is UD-Q5_K_XL @196,608 n4→n8.

**S9e — UD-Q6_K at the deployment window**, 262,144, `-ts 58,42`, `-ctxcp 32`, 3 × 512 tokens,
prompt_n 248,527, prefill_frac 0.9481, prefix cache confirmed:

| n_draft | decode reps | median | spread | acceptance | VRAM GPU0/GPU1 |
|---|---|---|---|---|---|
| 2 | 12.017 · 15.584 · 12.474 | **12.474** | 29.7 % | 0.7381 | 15,322 / 15,082 |
| 4 | 11.806 · 12.875 · 18.067 | **12.875** | 53.0 % | 0.4915 | 15,506 / 15,194 |
| 8 | — | — | — | — | **FAILS TO LOAD** — draft context does not fit |

n=4 leads n=2 by **3.2 %** against a 29.7–53.0 % rep spread → **not separated**.
Artifacts `s9d-depthsweep.json`, `s9e-n262k.json` · PN-32 · **CURRENT for acceptance; UNRANKABLE
for speed**

⚠ **The clustered-interval trap, stated for the methods section.** Pooled Wilson intervals on
acceptance are ±0.02 over 1,000–4,000 draft events, and are **misleading**: draft events within one
generation are strongly correlated, so the effective n is the **3 generations**, not the events.
Verified from the raw reps: **19 of 21 valid cells** have a within-cell per-rep acceptance range
exceeding 0.10, with a **maximum range of 0.6293**. This is R6's clustered-standard-error warning
reproduced on our own data.

⚠ **S9d did not achieve its purpose.** DEC-13 reinstated it specifically to repair PN-9's confound
and to test PN-24's generality. Neither is resolved: differences of 20–30 % sit inside noise of up
to 166 %. Resolving either needs ~30 repetitions per cell, not 3.

### 4.7 Quarantined: the first S9d run

Every one of 69 repetitions generated exactly **17 tokens** (min = median = max); decode read
**52.27 tok/s at ctx 131,072** — faster than most configurations reach at depth 0 — and acceptance
read **exactly 1.000 in all 23 cells**.
`data/raw/e12/quarantine/s9d-depthsweep.json.degenerate-17tok-20260901` +
`quarantine/README-s9d-degenerate.md` · PN-30 · **WITHDRAWN**. Cost: ~3.3 h of GPU.

### 4.8 Historical speculative-decoding results

| finding | value | status |
|---|---|---|
| MTP depth optimum is quant-dependent | Q3 peaks at n=8 (116.9 tok/s); Q6 at n=2 (40.9; n=8 gives 37.5) | HISTORICAL-PRE-E12 · IRREPRODUCIBLE |
| Spec-method ranking flips with context | DFlash2 wins ≤32K (57.5 vs 46.9); MTP wins ≥100K (32.6 vs 22.9 @168K) | HISTORICAL-PRE-E12; **reproduced in kind** by S9c (§4.4) |
| DFlash2 acceptance collapse at depth | 0.41–0.55 @ ~184K | HISTORICAL; reproduced on a surviving image: 0.9172 @32,768 → 0.4583 @163,840 |
| MTP builds a **separate draft context against the target model** (`common_speculative_init_result`) | costs UD-Q6_K_XL 114,688 tokens of window (245,760 no-spec → 131,072 with MTP) | HISTORICAL-PRE-E12 · mechanism is inference from serverlog |
| 2026-08-20 MTP ablation, Q4_K_M, layer, ctx 8,192, q8_0 KV | no-spec 23.99 · embedded MTP n2 30.64 (acc 0.495–0.667) · separate-draft n2 28.98 (acc 0.442–0.503) · separate-draft n3 26.20 | **HISTORICAL-PRE-E12** — `data/archive/aug20-mtp-ablation.txt`, image `llamacpp-nccl231:latest` |

---

# §5 — KV cache

### 5.1 q4_0 vs f16 — the gating measurement (SSA S4 = E2)

Same instrument as §1, same model (UD-Q6_K_XL), same code corpus, same seed, same image;
`-ctk/-ctv f16` records the reference logits, `q4_0` is scored against them. n = 65,536 tokens,
n_ctx 2,048.

| metric | value |
|---|---|
| **mean KLD (q4_0 vs f16 KV)** | **0.002955 ± 0.000127** |
| top-1 agreement | **99.401 ± 0.043 %** |
| median KLD | 0.000004 |
| KLD p90 / p95 / p99 | 0.001529 / 0.008188 / 0.067592 |
| max KLD | 1.317717 |
| mean Δp | −0.048 ± 0.013 % |
| RMS Δp | 2.392 ± 0.072 % |
| PPL, f16 KV | 1.1791 ± 0.00605 |
| PPL, q4_0 KV | 1.1809 ± 0.00610 (**+0.15 %**) |

**Interpretation — and PN-43 qualifies how it may be phrased.** 0.002955 is **51 %** of the
divergence of dropping a whole quantization level (UD-Q6_K_XL → UD-Q6_K on code = 0.005829). It
sits below Fireworks' <0.007 threshold, so q4_0 KV is **defensible but not free** and must be
declared with every accuracy claim.

⚠ **"51 % of a quantization level" is a comparison of sizes, NOT a currency conversion.** The
arithmetic is sound — both quantities are KL from the same reference arm on the same corpus — but
the phrasing reads as though the two perturbations were commensurable and additive, so that two KV
steps would equal one quant step. **Nothing here establishes that.** KL divergences from a common
reference do not add, and no experiment in this study applies both perturbations together to check.
The defensible sentence is: *"the divergence introduced by q4_0 KV is roughly half the magnitude of
the divergence introduced by dropping one quantization level, measured against the same
reference."* (PN-43)

⚑ **A LABEL COLLISION corrupted part of this artifact — the trust rule inverts for two cells.**
The f16 and q4_0 reference-arm base runs on the code domain were given the **identical label**
`ssa-Q6_K_XL-code-base`, hence one serverlog path. The f16 run executed second and **overwrote**
the q4_0 run's log, so when `ssa_reparse.py` repopulated `metrics_reparsed` from the surviving log
it wrote the **f16 value into both cells**. The q4_0 cell now reads `metrics_reparsed.ppl = 1.1791`
against its own run-time `metrics.ppl = 1.1809`.

> **For these two cells only, trust `metrics`, NOT `metrics_reparsed`** — the reverse of the rule
> everywhere else in this file, where `metrics_reparsed` is the repaired one (PN-17). A reader
> trusting the reparsed block would conclude PPL moved by 0.00 % and that PN-15's contrast is
> fabricated. The warning is now written **into the artifact** as `_WARNING_label_collision`.

**What survives:** PN-15's PPL figures (1.1791 → 1.1809, **+0.15 %**) come from the run-time
`metrics` field and are **correct**. The headline KLD **0.002955 ± 0.000127 is unaffected** — it
comes from a separately-labelled cell (`ssa-Q6_K_XL-code-kld-e2`) with its own intact serverlog.
Only these two cells collide; every other label in the file was checked and is unique. (PN-43,
superseding ⚑F-10)

**The lesson, and it is a new member of this corpus's defect family:** *an identifier that is not
unique silently destroys evidence, and the destruction is invisible because the surviving file is
well-formed.* It pairs with the log-preservation rule — **preserving raw output only helps if each
run's output has somewhere of its own to go.** A label must include every dimension that varies;
here the KV dtype was varied and not named. Found by adversarial review; nothing in the harness
would have caught it.

**The PPL contrast is itself a result**: the per-token distribution demonstrably moved (KLD
0.002955, one token in 168 changing its argmax) while the mean perplexity moved 0.15 %. This is a
worked demonstration of the averaging bias that disqualifies PPL as the quantization ranker (R2, R4).

Artifact `ssa-results-parsed.json`, cell `Q6_K_XL-code-kld-e2` against base `Q6_K_XL-code` (kv
f16) · PN-15 · **CURRENT**
⚠ Measured on the **reference arm only**, the **code domain only**, at **n_ctx 2,048** — not at
the 212K–262K depths where the KV cache dominates memory. A per-arm, at-depth version is
**unmeasured and will remain so** (S10 infeasible, §9.4).

### 5.2 KV dtype viability

| dtype | status |
|---|---|
| `f16` | works; roughly halves the reachable window |
| `q4_0` | works; used by every context/speed/long-context row in this corpus |
| `q8_0` | **BROKEN on this stack** — illegal memory access @c4096; "failed to allocate" @262K; "FAIL out of memory" @262K |

`data/raw/e12/env-manifest.json` `notes` · **CURRENT**. `-fa on` is required for a quantized
V cache (`validate-v2.json` C1 records this as behavioural evidence).

### 5.3 KV rates and f16 ceilings — historical

f16 ≈ 34.5 KiB/token/GPU vs q4_0 = 16.0 (tensor split, §2.8). Measured f16 ceilings:
UD-Q6_K_XL 98,304 · UD-Q5_K_XL 147,456 (15,198 MiB) · UD-IQ4_XS ~245,760.
**HISTORICAL-PRE-E12.** The KV dtype of the 100K–258K historical needle runs is **unrecorded** →
those rows are labelled **KV-UNKNOWN** (G11, resolved by E10 as "label, do not guess").

### 5.4 Untested KV axes

`-ctkd` / `-ctvd` (draft-model KV dtype) are confirmed present on the image and were **never
tested** — cancelled by DEC-12 and not reinstated. **NOT MEASURED.**

---

# §6 — Long-context accuracy

### 6.1 RULER (S12) — the study's only long-context accuracy measurement

**Instrument:** RULER (R8). Data generated by RULER's **own** reference generators
(`scripts/data/synthetic/niah.py`) with its official templates, answer prefixes and prompt
construction (`input + answer_prefix`); scored with its own `string_match_all` metric reproduced
verbatim and **unit-checked against the reference implementation on five cases** including
partial-match and case-folding, before any GPU time. Only *transport* is this project's harness.

**Conditions:** arms UD-Q6_K_XL (reference) and UD-Q4_K_XL · **greedy (temperature 0, top_k 1)** ·
**no speculation** (PN-23/PN-26: speculation alters ~20 % of completions independently of quant) ·
one fixed **`-ts 56,44` for both arms** · q4_0 KV · `-ctxcp 32` · `-fit off -fa on` · seed 20260830 ·
image `feb0231976b6…` · `tokens_to_generate` 128.

**S-NIAH (single-needle retrieval):**

| length | n | UD-Q6_K_XL | UD-Q4_K_XL | accuracy recovery | prompt_n median | empties |
|---|---|---|---|---|---|---|
| 8,192 | 25 | **100.0** | **100.0** | 100 % | 8,041 | 0 / 0 |
| 32,768 | 25 | **100.0** | **100.0** | 100 % | 32,616 | 0 / 0 |
| 131,072 | 12 | **100.0** | **100.0** | 100 % | 130,941 | 0 / 0 |

**MK-NIAH (four keys planted, one queried, three hard distractors — `num_needle_k=4,
num_needle_v=1, num_needle_q=1`), 131,072 — PN-44, ⚠ SUPERSEDED BY PN-60:**

> ⚠ **Read the supersession note below this table before using any number in it.** The scores are
> arithmetically correct and reproduce exactly, but their *interpretation* as retrieval accuracy —
> including the "accuracy recovery" column — was retired by PN-60 on 2026-09-03, after this
> document was compiled.

| arm | n | score | Wilson 95 % | accuracy recovery | prompt_n median | empties | wall s |
|---|---|---|---|---|---|---|---|
| UD-Q6_K_XL | **100** | **89.0** | **[81.4, 93.7]** | — (baseline) | 130,936 | 0 | 17,490.9 |
| UD-Q4_K_XL | **100** | **79.0** | **[70.0, 85.8]** | **88.76 %** | 130,936 | 0 | 16,195.0 |

**Paired, and this is the striking part:**

| both correct | reference only | Q4_K_XL only | neither |
|---|---|---|---|
| 79 | **10** | **0** | 11 |

**Every one of the ten discordant items runs the same way** — there is no case where the cheaper
arm succeeded and the reference failed. UD-Q4_K_XL's failures are a **strict superset** of the
reference's. Exact McNemar **p = 0.0020**, which is also the *minimum attainable* with 10 discordant
pairs, so the test returned the most extreme outcome its design permits. Paired difference
**−10.00 points, 95 % CI [−15.88, −4.12]**.

Dataset generated by RULER's own generator via `harness-src/s12_mkniah_generate.sh`; the analysis
script `harness-src/mk100_analyse.py` was **written and committed before the second arm finished**,
so the test was fixed in advance of the data. 9.4 h of GPU, 200 full prefills.
Artifacts `s12-ruler.json` cells `mk100`, predictions in `s12-preds-*-mk100-c131072.json` ·
PN-44 · ⚠ **SUPERSEDED BY PN-60**

> ✅ **INDEPENDENTLY RE-DERIVED 2026-09-03 from the raw predictions**, with RULER's
> `string_match_all` reimplemented from its definition rather than read from the artifact:
> 89.0 / 79.0 · both 79 · reference-only 10 · Q4-only **0** · neither 11 · exact McNemar
> **p = 0.0020** · paired difference **−10.00 [−15.88, −4.12]** · Wilson **[81.4, 93.7]** and
> **[70.0, 85.8]** · recovery **88.76 %** · 0 empty predictions in either arm.
> **Every figure in PN-44 reproduces exactly.**

⚠ **SUPERSEDED BY PN-60 (2026-09-03T15:30Z), which post-dates this document's compilation.** This
corpus was built from PN-1…PN-44 and L-1…L-20; PN-60 landed at L-23 and PN-63 at L-24. The battery
ran through `/completion` with `n_predict=128` and reasoning enabled — the harness cannot disable
thinking on that endpoint — so every generation was a `<think>` block competing with the answer for
128 tokens. Re-analysed: **not one item in either arm was closed-and-wrong**; every failure is a
truncation. Restricted to the **55 of 100 items where neither arm's budget bound, both arms score
55/55 with zero discordance**. What separates the arms is **budget closure** — 77 of 100 against 60,
discordance 22/5, exact McNemar **p = 0.001514**.
Consequences for anything drawing on this table: the **88.76 % "accuracy recovery" must not be used
as a retrieval figure**, the comparison against Red Hat's 85–88 % 4-bit recovery band at 128K (R9)
is **void**, and the 89.0/79.0 separation must be restated as a reasoning-verbosity difference.
PN-63 adds the control: at the same length, same arms, same budget, single-needle closes 12/12 in
both arms while multi-key closes 77/100 and 60/100 — so the truncation is driven by **task
difficulty, not depth**. Retrieval at 131,072 is **unanswered**, pending a re-run at a generous
`n_predict` with thinking disabled.

⚠ **This SUPERSEDES PN-33's MK-NIAH half.** The n=12 reading (100.0 vs 91.67) had a reference
score that was a **lucky draw** — P(12/12 | p = 0.89) ≈ 0.25. It was not merely imprecise: it
implied a ceiling that does not exist and pointed the wrong way. The n=12 cells remain in the
artifact and are **SUPERSEDED**, not deleted.
⚠ **`s12-ruler.json`'s `accuracy_recovery` block still shows only the superseded 91.67** and has no
`mk100` entry — see ⚑**F-27**.
⚠ One task variant, one length, one pair of arms. **S-NIAH at the same length remains 100.0/100.0**
(PN-33), so this is a statement about *multi-key retrieval at depth*, not about long-context
behaviour generally. RULER's own protocol uses 500 samples per length; ours is 100.

**Where it sits against published work:** inside Red Hat's 85–88 % band for INT W4A16 at 128K (R9),
reached independently on a different model, compression family and hardware class. ⚠ But see
⚑**F-9** — that source explicitly disclaims conclusions at 128K, *"even unquantized models perform
poorly… making it difficult to draw definitive conclusions"*. Cite the agreement and the caveat
together.

**Mechanism (PN-37, superseding PN-34).** The earlier "saturation" story is **withdrawn**: it is
false for two of the three instruments — HellaSwag scores 82.75 % (~17 points of headroom),
HumanEval+ 94.5 % (~5 points); only S-NIAH is genuinely at ceiling. What replaces it is PN-35's
**tail structure** (§1.7): damage confined to ~1–5 % of token positions changes an *outcome* only
when a tail token lands somewhere decisive. That predicts the discordance rates actually observed
— 3/164 and 5/164 (PN-28), 0/12 and 1/12 (PN-33) — and it predicts PN-44: on a task where 21 % of
items are hard enough that even the reference fails, the cheaper arm fails on all of those **and
ten more**. ⚠ PN-37 also discloses the counter-example inside this study: `variable_tracking` is
the *harder* task and was **excluded** (§6.2); if difficulty were the gate it should have shown
the effect most clearly. **That disclosure must appear in the same paragraph as the claim.**
⚠ The tail mechanism is *"consistent with, and predicts the magnitude of"* — not *"explains"*. No
experiment here manipulates the tail and observes benchmark movement.

### 6.2 `variable_tracking` — EXCLUDED, and why (a reportable instrument failure)

| attempt | token budget | UD-Q6_K_XL | UD-Q4_K_XL | apparent "recovery" |
|---|---|---|---|---|
| 1 | 30 (RULER's own budget) | 16.8 | 18.4 | 109 % |
| 2 | 120 | 27.2 | 36.8 | 135 % |

RULER budgets `variable_tracking` at 30 generated tokens, which assumes a model that continues the
answer prefix directly. **This instruct-tuned model writes a markdown step-by-step trace instead**:
at 30 tokens it named 1 of 5 variables; at 120 it still truncated mid-way through the second. The
tracking itself is **correct** — the named variables match the references in order — so the metric
measures **output verbosity against a fixed budget**, not long-context ability. Both attempts put
the *reference* arm **below** the cheaper arm, which is the signature of a floor-scored comparison.
Artifact `s12-ruler.json` `variable_tracking_excluded_cells` + `variable_tracking_exclusion` ·
**EXCLUDED — data retained, never deleted.**
This is a **publishable methodological finding** and currently has no PN entry. **UNWRITTEN.**

### 6.3 What RULER coverage this study does **not** have

RULER's QA and aggregation categories were **never run**. Only two of RULER's task families were
attempted and one was excluded. MK-NIAH exists at one length only. **NOT MEASURED.**

### 6.4 S11 — greedy divergence at depth: the instrument that failed (see ⚑F-5)

Only the 8,192 rung of {8,192 · 65,536 · 196,608} ran. Metric = index of the first differing
character against the reference arm on the identical prompt; a *falling* index with depth would
mean damage grows with context.

| arm | first-divergence char, 3 pads | median | identical pads |
|---|---|---|---|
| UD-Q6_K | 2 · 5 · 71 | **5** | 0 / 3 |
| UD-Q5_K_XL | 2 · 62 · 126 | **62** | 0 / 3 |
| UD-Q4_K_XL | 2 · 10 · 14 | **10** | 0 / 3 |

**Pairwise normalized edit distance between arms — the number that actually killed the metric:**

| pair | ladder distance | distance |
|---|---|---|
| Q6_K_XL / Q6_K | **adjacent** | **0.794** |
| Q6_K_XL / Q4_K_XL | **the extremes** | **0.779** |
| Q5_K_XL / Q4_K_XL | adjacent | **0.613** (closest pair) |

Every pair sits at **0.61–0.79 regardless of ladder distance, with the ordering scrambled** — the
two arms *adjacent* on the ladder measure **further apart** than the two *extremes*. Visible
directly in the outputs: the reference opens `- Files scanned: 1000` while all three other arms
open `- Total files: 1000`, so the reference is the odd one out and "distance from the reference"
is a poor proxy for quantization distance.

**Root cause is structural, not statistical.** Greedy decoding is a trajectory: after the first
differing token the two arms are continuing *different texts*, and the comparison stops being about
the models. More samples would not have helped.

Artifacts `data/raw/e12/quarantine/s11-divdepth.json.n1-padoverflow-20260901` and the generations
sidecar; pairwise distances recomputed offline from the preserved texts · **PN-38** ·
**CURRENT — a methodological negative result**

⚠ S11 also suffered a **separate** pad-sizing defect — a fixed chars-per-token constant against a
corpus running 2.86–4.63 chars/token, so two of three prompts overflowed the context and were
rejected. That is **PN-5's root cause repeated**. It was found and fixed, and the numbers above come
from the repaired run at n=3 per cell. The metric failure is independent of it.
⚠ One depth only (8,192); the deeper slices were never run, because the metric had already failed
at the cheapest rung. `self_consistency: null` — the mandated control never ran.

**The pairing that makes this worth publishing:** it is the counterpart to PN-35. **Divergence must
be measured on distributions at fixed context, not on emitted trajectories** — free generation
destroys the comparison it is meant to make. And the failure was not foreseeable: S11 was designed
on the strength of a *correct* determinism result (PN-26) and still failed.

### 6.5 Historical long-context retrieval (Code-NIAH probes)

3-needle verbatim-marker retrieval over a real django corpus, machine-checked via
`"retrieval_pass": true`. **Passes at 99,885 / 179,709 / 248,368 / 258,779 tokens (Q3-embedded) and
139,872 (Q5-embedded).**
`/srv/bench/champion-20260821/raw/*.json` (host) · **HISTORICAL-PRE-E12 ·
IRREPRODUCIBLE-ON-CURRENT-IMAGES · KV-UNKNOWN**.
⚠ Weak evidence: verbatim marker strings only, depths 25 % / 50 % / ~100 % only, no code semantics,
**n=1**, and the KV dtype is unrecorded. Does **not** license "accuracy holds at 250K".

### 6.6 The G1 hole, precisely stated

There are **no 100K–250K task outputs** in the pre-E12 corpus to score. Every `.diff` in
`champion-20260821` came from a **40,347-token** prompt; the 100K–258K runs generated **50–55-token
JSON needle answers**, not code edits. Long-context *task* accuracy is closed only to the extent
S12 closes it: **retrieval, two task variants, two arms, three lengths.**

---

# §7 — Energy and thermal

**Instrument:** `/srv/bench/power-log.csv` — 1 Hz sampling, `nvidia-smi` for GPUs + kernel RAPL
powercap for the CPU package, cumulative-Wh columns differenced across the window. **Host-only
file; not in the repository (⚑F-12).**

### 7.1 Host power envelope (PN-11)

Window: **43,182 consecutive 1 Hz samples**, 2026-08-29T16:11:40Z → 2026-08-30T04:11:41Z
(exactly 12.00 h), containing **26 % GPU-busy time**.

| quantity | value |
|---|---|
| system mean / median / peak | **149.2 W / 79.8 W / 408.9 W** |
| system energy over the window | **1.791 kWh** |
| of which the two GPUs | **1.078 kWh (60 %)** |
| of which the CPU package | **0.172 kWh (10 %)** |
| mean system draw **under GPU load** | **334.1 W** (idle→loaded swing ≈ **4.2×**) |
| GPU0 mean / median / peak power | 47.1 W / 10.7 W / 183.7 W |
| GPU1 mean / median / peak power | 42.8 W / 10.8 W / 178.8 W |
| CPU package mean / peak | 14.4 W / 142.1 W |

PN-11 · **CURRENT**
⚠ `est_system_w` is a **modelled** total (GPU telemetry + RAPL package + a fixed platform
allowance), **not a wall-socket measurement** — there is no BMC/IPMI on this host. Only the GPU and
CPU-package limbs are directly instrumented. The window mixes idle, the Wave-1 `-ts` sweep, and
container load/teardown, so it characterises the **host**, not any experiment.

### 7.2 Thermal asymmetry (PN-12)

Same 43,182-sample window:

| | GPU0 | GPU1 |
|---|---|---|
| temperature mean / median / max | 46.8 / 35 / **90 °C** | 43.6 / 37 / **76 °C** |
| VRAM mean / peak | 5,109 / 15,658 MiB | 5,421 / 15,848 MiB |

A **14 °C asymmetry on physically identical cards**, consistent with the `-ts 5x,4x` family placing
more layers on GPU0 (winning ratios in the window: Q5_K_XL `54,46`, Q6_K_XL `56,44`, both
GPU0-weighted). PN-12 · **CURRENT — OBSERVATIONAL AND CONFOUNDED**: the window mixes quants, ratios
and rungs; case airflow asymmetry is an equally plausible contributor and was not controlled. 90 °C
is within the card's operating range; no throttling was observed **or looked for**.

### 7.3 Per-configuration energy — **NOT MEASURED, and will not be**

Wave 4's speed/energy curve was **CANCELLED by DEC-12**. There is **no J/tok figure for any E12
configuration**. The historical J/tok table (§3.7) is depth-0 and from the deleted image and
**cannot substitute**. This is a permanent, stated limitation.

### 7.4 Historical energy

Spec decoding cuts J/tok ~2–2.5× at every quant (Q6_K_XL no-spec 11.78 → DFlash2 n4 4.79);
best measured **IQ4_XS DFlash2 n=4 = 3.70 J/tok**. Benchmark energies (GPU Wh): HumanEval thinking
288–564 · agentic T3 window 208 · PPL runs 14–33 · the `nvfp4-ppl` failed-retry tax **377 GPU Wh /
1.18 kWh system across 22 failed startups**.
`/srv/bench/energy-per-benchmark.json` (host) · **HISTORICAL-PRE-E12 · P-depth0**.
⚠ The power logger covers 2026-08-27T16:21Z onward only; earlier benchmarks are uncoverable and are
listed explicitly in that artifact.

---

# §8 — Task benchmarks

### 8.1 HellaSwag (SSA S7) — the control that validates the method

**Instrument:** `llama-perplexity --hellaswag --hellaswag-tasks 400`, logprob-scored, **no
generation**. `-c 2048 -ngl 99 -fa on -ctk/-ctv q4_0 -s 20260830`, engine default split, image
`feb0231976b6…`. Data: `hellaswag_val_full.txt`, 7,770,677 B, sha256
`d572539320eb2050e858ca34b495bbe2103e3b3f1391a9c3bcdf215b0bb93bd1`, from
`raw.githubusercontent.com/klosax/hellaswag_text_data`. Because every arm ran at the same seed the
tool selects the **same 400 tasks**, making these **paired** observations.

| arm | correct / 400 | acc_norm % | tool CI95 | load s | wall s |
|---|---|---|---|---|---|
| UD-Q6_K_XL | 331 | **82.75** | [78.74, 86.14] | 228.1 | 440.0 |
| UD-Q6_K | 329 | **82.25** | [78.20, 85.68] | 264.3 | 564.9 |
| UD-Q5_K_XL | 331 | **82.75** | [78.74, 86.14] | 228.6 | 503.4 |
| UD-Q4_K_XL | **333** | **83.25** | [79.28, 86.59] | 205.6 | 432.1 |

**Paired McNemar (χ²), from per-task vectors recovered by differencing the tool's cumulative
accuracy table at zero extra GPU cost:**

| pair | b | c | Δ pts | χ² | p | verdict |
|---|---|---|---|---|---|---|
| Q6_K_XL vs Q5_K_XL | 0 | 0 | 0.0 | 0.0 | **1.0** | **IDENTICAL on all 400 items** |
| Q6_K_XL vs Q6_K | 2 | 0 | +0.5 | 0.5 | 0.4795 | not distinguishable |
| Q6_K_XL vs Q4_K_XL | 0 | 2 | −0.5 | 0.5 | 0.4795 | not distinguishable |
| Q6_K vs Q5_K_XL | 0 | 2 | −0.5 | 0.5 | 0.4795 | not distinguishable |
| Q6_K vs Q4_K_XL | 0 | 4 | −1.0 | 2.25 | **0.1336** | not distinguishable |
| Q5_K_XL vs Q4_K_XL | 0 | 2 | −0.5 | 0.5 | 0.4795 | not distinguishable |

1.0-point spread inside ~7.4-point independent intervals; **the most heavily quantized arm scores
nominally highest**; no pair disagrees on more than 4 of 400 items.
Artifacts `ssa-s7-results.json`, `ssa-s7-paired.json`, `s7-data-provenance.json` · PN-22 ·
**CURRENT**
⚠ HellaSwag measures commonsense reasoning, **not coding**. Face validity only; never a Track A
input. Winogrande was fetched (`winogrande-debiased-eval.csv`, 155,325 B, sha256
`6726173ef65ffdc4abb0d28b755375d288ffb3eb41633bd833288c411c8ebf7c`) and **never run** — dropped as
disproportionate (~69 min/arm) for a second benchmark that also cannot rank the arms.

### 8.2 HumanEval+ generative, paired, ladder extremes (SSA S6 / S9b)

**Conditions:** all 164 problems · **DEC-2 official non-thinking sampling** (temp 0.7 / top_p 0.80 /
top_k 20 / min_p 0.0 / presence_penalty 1.5) · seed 20260830 · **no speculation on both arms**
(deliberate: PN-23) · ctx 32,768 · each arm at its Wave-1 `-ts` (`56,44` for both) ·
`max_tokens` 1024 · image `feb0231976b6…` · scored through the standard
`evalplus.sanitize → evalplus.evaluate` pipeline.

| arm | base pass | base % | Wilson 95 % | plus pass | plus % | Wilson 95 % | empties | decode median |
|---|---|---|---|---|---|---|---|---|
| UD-Q4_K_XL | 154/164 | **93.90** | [89.14, 96.65] | 147/164 | **89.63** | [84.03, 93.43] | 0 | 22.153 tok/s |
| UD-Q6_K_XL | 155/164 | **94.51** | [89.90, 97.09] | 148/164 | **90.24** | [84.74, 93.91] | 0 | 16.063 tok/s |

**Paired per-problem — REPORT AS A BOUND, NOT AS A NULL (PN-40 corrects PN-28):**

| metric | both pass | neither | Q4-only | Q6-only | discordant | Δ (Q4 − Q6) | **95 % CI** | McNemar p | **minimum p obtainable** |
|---|---|---|---|---|---|---|---|---|---|
| base | 153 | 8 | 1 | 2 | **3** | **−0.61 pts** | **[−2.68, +1.46]** | 1.0 | **0.25** |
| plus | 145 | 14 | 2 | 3 | **5** | **−0.61 pts** | **[−3.28, +2.06]** | 1.0 | **0.0625** |

⚑ **PN-28's "McNemar p = 1.0" could never have reached significance.** With 3 discordant pairs the
smallest two-sided exact p obtainable — even from the most extreme possible split, 0 vs 3 — is
**0.25**; with 5 discordant pairs it is **0.0625**. Neither can cross 0.05 under *any* outcome. So
"p = 1.0" says nothing about the arms; it says the test had **no power to say anything**.
**This is precisely the error the paper accuses the field of, committed in the paper's own
generative anchor**, and it was found only under adversarial review.

**The repair converts a vacuous null into a quantitative bound**, using the paired difference in
proportions `d = (b−c)/n`, `SE = sqrt((b+c−(b−c)²/n)/n²)`. The publishable sentence becomes:
**"a 3.69× increase in code-prompt KL divergence moves HumanEval+ pass@1 by at most about 3 points,
with the point estimate at −0.6."** That is a measured relation between two instruments, not an
admission that a benchmark found nothing.

> ✅ **Re-derived 2026-09-03**: minimum two-sided exact p at 3 and 5 discordant pairs = **0.25** and
> **0.0625**; both intervals reproduce to the stated precision.

Artifacts `s9-scores.json` (`s6_paired`, `arms.s6-*`), `s9-s6.json`,
`s9-s6-{Q4_K_XL,Q6_K_XL}.jsonl` · **PN-40 supersedes PN-28's statistics** · **CURRENT**
⚠ The interval is the Wald form for a paired difference — standard, but approximate at these
discordant counts. An exact conditional interval would be slightly wider and is the more
conservative choice if a reviewer presses.
⚠ The bound is on *this* task under DEC-2 sampling at one seed; it does not generalise to other
tasks or across seeds. The arms remain separated at 3.7–11.8 σ on divergence, which is why both
are reported.
⚠ **General rule for the report: before reporting a null, state the smallest effect the test could
have detected.** For paired binary data that is set by the **discordant count**, not by n.

### 8.3 HumanEval+ across speculative settings (S8 / S9)

**Greedy** (temperature 0, top_p 1, seed 20260830), UD-Q6_K, ctx 32,768, `-ts 58,42`, `-ctxcp 32`,
q4_0 KV. Wilson intervals from `s9-scores.json` where a repeat exists.

| config | HumanEval | HumanEval+ | Wilson 95 % (base) | n | image |
|---|---|---|---|---|---|
| no-spec | **0.945** (155/164) | **0.915** (150/164) | [89.90, 97.09] | 164 | mtp |
| no-spec, repeat (S9a) | 0.945 | 0.915 | [89.90, 97.09] | 164 | mtp |
| MTP n=2 | **0.939** (154/164) | **0.902** (148/164) | [89.14, 96.65] | 164 | mtp |
| MTP n=2, repeat (S9a) | 0.939 | 0.902 | [89.14, 96.65] | 164 | mtp |
| MTP n=4 | **0.939** | **0.909** | — | 164 | mtp |
| DFlash2 n=4 (S9c) | **0.933** (153/164) | **0.902** (148/164) | [88.39, 96.21] | 164 | **dflash2** |
| ~~DFlash2 n=4 (S8)~~ | ~~0.000~~ | ~~0.000~~ | — | — | **EXCLUDED (PN-25)** |

The whole spread (0.933–0.945 / 0.902–0.915) sits far inside the **±4.6-point** interval at n=164
and **ranks nothing**. The equivalence result (§4.1), not the score, is the finding.
Artifacts `s8-humaneval.json`, `s8-scores.json` (⚠ its `parsed` field is broken — ⚑F-4),
`s9-scores.json`, `s8-*.jsonl`, `s9-*.jsonl` · PN-23, PN-24, PN-25, PN-29 · **CURRENT**

### 8.4 Statistical power, stated once

| instrument | n | 95 % interval width (independent) | arm separation |
|---|---|---|---|
| KL divergence | 65,536 tokens/cell | SE = σ/256 | **3.7–11.8 σ, non-overlapping** |
| HumanEval+ | 164 problems | **±4.6 pts** | 0.6–1.0 pts |
| HellaSwag | 400 tasks | **±3.7–4.0 pts** (~7.4 wide) | 0.5–1.0 pts |
| RULER MK-NIAH | 12 samples | **[64.6, 98.5]** | 8.3 pts |
| SWE-bench Verified (historical) | 49–50 | **±12 pts** | 1–3 pts |

### 8.4b MEASURED cost of each instrument — and the correction of a fabricated contrast

⚑ **PN-41: the "≈20 minutes of divergence versus ≈20 hours of task benchmarking" contrast used
throughout this project's prose is NOT supported by its own artifacts.** The "20 minutes" described
one arm on one domain and was silently generalised to the whole protocol; **the "20 hours" figure
has no basis in any artifact.** Measured wall-clock, summed from the records:

| instrument | measured | source |
|---|---|---|
| **SSA divergence, S0–S4** (4 arms × 2 domains + KV) | **2.15 h** | `progress.json` step timestamps |
| SSA S6 — generative HumanEval+, 2 arms | 1.29 h | `s9-s6.json` `runs[].seconds` |
| S12 RULER — 8 cells | 2.97 h | `s12-ruler.json` `cells[].seconds` |
| S7 HellaSwag — 4 arms | ≈0.53 h | ledger L-12 |
| **task benchmarking total** | **≈4.8 h** | |
| **cost ratio** | **2.2×**, not 60× | |

> ✅ **Re-derived 2026-09-03**: SSA 08:18:50Z→10:27:35Z = **2.146 h**; S6 = **1.29 h**;
> RULER 8 niah+mkniah cells = **2.97 h**. All three reproduce.
> *(The mk100 run adds a further **9.36 h**, so post-PN-44 the task-benchmark total is ≈14.2 h and
> the ratio ≈6.6× — but that run is the one that finally* separated *the arms, so it belongs on the
> other side of the argument.)*

**The argument survives, restated on measured numbers:** *2.1 hours of divergence measurement
separated the arms at 3.7–11.8 σ with non-overlapping intervals, while 4.8 hours of task
benchmarking across three instrument classes separated them nowhere.* The **cost** ratio is modest;
the **power** ratio is what carries the point — and a 2.2× stated honestly is more persuasive than a
60× a reader can falsify in five minutes from this repository.

⚠ Wall-clock including model loads, and not perfectly comparable: the divergence runs process a
fixed **token** budget while the task runs process a fixed **problem** count — which is the very
asymmetry SSA was designed around. Single measurements, one host, no repetition. Quote as
"approximately", framed as *what each instrument bought for a few hours of the same machine*, not
as a controlled efficiency benchmark. (PN-41)

**The through-line, corrected:** divergence draws power from **token count**, task benchmarks from
**problem count** — and at roughly comparable cost on this host, only the first separated the arms.

### 8.5 Historical task benchmarks

| benchmark | results | status |
|---|---|---|
| HumanEval+ non-thinking greedy | Q3_K_XL 84.1/81.7 · IQ4_XS 90.2/87.8 · Q5_K_XL 93.3/90.9 · Q6_K_XL 93.9/91.5 (monotone) | **HISTORICAL-PRE-E12** |
| HumanEval+ thinking (max_tokens 4096) | mtp-IQ4_XS 86.6/86.0 (12.8 % empty) · mtp-Q4_K_XL 87.8/86.0 (12.2) · mtp-Q5_K_XL 89.0/86.0 (11.0) · **mtp-Q6_K_XL 90.9/88.4 (7.9)** · dflash-IQ4_XS 89.0/87.8 (10.4) · dflash-Q4_K_XL 90.2/87.2 (8.5) · NVFP4 85.4/84.1 (12.8) | **HISTORICAL-PRE-E12** |
| SWE-bench Verified, 50 instances | Q6_K **37/49 = 75.5 %** · IQ4_XS **38/49 = 77.6 %** · Q5_K_XL **38/50 = 76.0 %** | **HISTORICAL-PRE-E12** ⚠ host-architecture caveat: `django-10097` resolves only on x86_64 |
| SWE-bench thinking, 3-instance calibration | mtp-Q6_K_XL 3/3 · mtp-Q4_K_XL 2/3 · mtp-Q5_K_XL 2/3 · dflash-IQ4_XS 2/3 · dflash-Q4_K_XL 2/3 · vllm-NVFP4 2/3 · ⚠ **mtp-IQ4_XS is n=1, not n=3** (2 of 3 empty patches) | **HISTORICAL-PRE-E12** |
| Agentic step counts (T3-style, 3 instances) | Q3_K_XL **250 — ALL hit limit** · IQ4_XS 23 · Q5_K_XL 29 · Q6_K_XL ~45 | **HISTORICAL-PRE-E12** |

⚠ `ledger-data.json` SWE-bench rows carry known parser defects (first-match regex over a
concatenated `eval.log`); the corrected aggregation is `swebench_agg.py` per-instance
`report.json`. See `data/multivac-src/multivac-CLAUDE.md` §"Known instrumentation defects" (10
entries) — every one is a reporting bug, not data loss.

### 8.6 Official published scores for the model — for comparison, never for validation

| benchmark | published |
|---|---|
| LiveCodeBench v6 | 90.3 |
| SWE-bench **Pro** | 61.7 |
| Terminal Bench 2.1 (Terminus) | 73.0 (⚑F-14 — no paper covers 2.1) |
| HumanEval / HumanEval+ | **NOT PUBLISHED** |

⚠ Our SWE-bench work is **Verified**, a different benchmark from **Pro** — 75.5 % is **not**
comparable to 61.7. Neither LiveCodeBench v6 nor SWE-bench Pro is set up on this host (G19).
⚠ Every pre-E12 benchmark on this host used **greedy temperature 0**, which matches neither
official preset — so absolute historical scores are not comparable to published numbers (G16).
E12 task benchmarks use the DEC-2 official settings and are.

---

# §9 — Harness, validation and instrument findings

These are results, not housekeeping. They are the paper's method contribution.

### 9.1 Measured server defaults ≠ any documented set (PN-1)

| source | temp | top_k | top_p | min_p | presence |
|---|---|---|---|---|---|
| **measured on `llamacpp-mtp:latest`** | **1.0** | **20** | **0.95** | **0.05** | **0.0** |
| upstream llama.cpp documented launch defaults | 0.80 | 40 | 0.95 | 0.05 | — |
| Qwen3.8 official **thinking** | 1.0 | 20 | 0.95 | 0.0 | 0.0 |
| Qwen3.8 official **non-thinking** | 0.7 | 20 | 0.80 | 0.0 | 1.5 |

A server launched without an explicit per-request sampling block runs an **undocumented fourth
configuration**. Directly assertable because `/completion` echoes the effective per-request
sampling in `generation_settings`.
Artifacts `validate-v2-selftest.json` fault F3 (readback), `validate-v2.json` C2 (DEC-2 blocks read
back field-exact modulo f32 rounding: 0.7 → 0.699999988079071, 0.8 → 0.800000011920929) · PN-1 ·
**CURRENT** (n=1 image; f32 readback needs 1e-3 tolerance in any re-implementation).

### 9.2 Thinking-mode control (PN-2, PN-3)

* A **2-token** `/v1/chat/completions` probe is a ~1 s discriminator of thinking state: with no
  control, `content` is empty, `reasoning_content` is non-empty, `finish_reason` is `length`.
* `chat_template_kwargs {"enable_thinking": false}` **works** (non-empty content, empty reasoning).
* `chat_template_kwargs {"reasoning_effort": "none"}` raises a **Jinja exception**:
  *"Unexpected reasoning effort none. Supported types are xhigh (default), medium, and low."*
  → G17 answered **negatively for the value `none`** at the template level. Consistent with the
  model card, which lists `xhigh | medium | low` and not `none`.
Artifact `validate-v2.json` C3 (both directions green; the error body recorded verbatim) ·
`validate-v2-selftest.json` F2 (omitting the control reproduces the leak exactly: content `""`,
`reasoning_len` 8, `finish_reason` `length`) · PN-2, PN-3 · **CURRENT**

### 9.3 `-fit on` did not shrink the context — and is still not trustworthy (PN-4)

`-fit on` at a requested 262,144 on UD-Q4_K_XL **loaded and `/props` reported the full 262,144**
within the 600 s health window. The E1 "silent shrink" class did **not** reproduce on this engine.
The negative control had to be injected with an un-fittable request (999,999,999 tokens), which the
context contract check caught.
⇒ **Rule that follows anyway:** launch every measurement with `-fit off` and assert
reported == requested. Load success does **not** prove the context is usable at depth.
Artifact `validate-v2-selftest.json` F1 · PN-4 · **CURRENT**

### 9.4 KL divergence cannot be measured at long context on this host (PN-31)

Measured one rung at a time, never extrapolated:

| n_ctx | host memory available | outcome |
|---|---|---|
| 2,048 | 9,061 MiB | writes logits normally |
| 8,192 | 1,338 MiB | writes logits normally — **the usable ceiling** |
| 16,384 | **305 MiB** | **zero bytes written in 13 minutes**, killed |
| 65,536 | — | immediate `std::bad_alloc` |

Storage constant measured from the real `.kld` files: **248,085 B/token** (508 MB at 2,048 tokens,
2.03 GB at 8,192), consistent with the 2-byte-per-vocab-entry format the tool's README documents.
Host: 14 GiB RAM, ~10 GiB available with the model mmapped.
⇒ A **4× range** cannot support a claim about a **128×** deployment context, so S10 was cancelled
(DEC-15).
Artifacts `/srv/bench/server-timings/ramprobe-c{2048,8192,16384}.serverlog` (host only) · PN-31 ·
**CURRENT — marked FOOTNOTE MATERIAL by owner direction.** The only clause with bearing on the
paper's argument: *the standard divergence tooling's footprint scales with context length, which is
itself why published quantization tables are all measured near 2K.*

### 9.5 The defect register — six failure modes, each producing plausible wrong output

| # | defect | consequence | PN | fix |
|---|---|---|---|---|
| 1 | **Unicode parser mismatch** — patterns expected ASCII `+/-`, llama.cpp emits `±`/`Δ` | 10 KLD cells, ~1.5 h GPU, exited 0, marked ok, **metrics empty** | PN-17 | patterns accept both; a kld cell without `mean_kld` is no longer `ok`. Every cell recovered from serverlogs — possible **only** because logs were preserved before teardown |
| 2 | **Documented-but-unasserted depth gate** — `prefill_frac ≥ 0.90` lived in a docstring | UD-Q4_K_XL prefilled **0.7973** of the window while reporting success; both its decode figure and its ceiling verdict were optimistic and incomparable to UD-Q5_K_XL at 0.948 | PN-5 | gate asserted in code; all 9 ladder pads rebuilt to ~0.945 |
| 2b | root cause: pad-builder bisection over a **fixed** bracket [0.9, 1.15] × chars-per-token, calibrated on the first 200 kB of a corpus running ~2.9 chars/token there and ~4.45 thereafter; the loop pinned at the bracket edge and assigned the **last** probe rather than the closest | `pad_201830` delivered 169,823 tokens instead of 201,830 (**−15.9 %**) | PN-5 | `pads-manifest.json`: all 9 pads within tolerance, `all_ok: true` |
| 3 | **Three orchestration defects** — a container killed between `docker run -d` and start sits in state `created` with no log and wedges every later cell; a sweep in which every cell failed still exited 0 and wrote a `.done`; a `nohup setsid` runner with no single-instance lock let two runners race | 32 junk cells across three quants | PN-10 | stillborn-container discriminator; non-zero exit when no cell succeeded; `flock` guard verified to refuse a second runner with exit 3 |
| 4 | **Mis-bound drafter** — DFlash2 launched on `llamacpp-mtp:latest` (`expected 81, got 58`) | 5 cells recorded **0.000 pass@1** and `generate-failed` — indistinguishable in a table from a model that ran and failed | PN-25 | measured on `llama-dflash2:latest` (§4.4); the 5 cells are EXCLUDED |
| 5 | **Unnamed estimator** — the Wave-1 summary's decode column mixed three statistics (last rep / first rep / median-of-3) | **reversed the apparent speed ranking of two arms**; would have driven the wrong configuration recommendation | PN-20 | recomputed on one statistic. ⚑F-2 and ⚑F-3 show the file also mixes **contexts** |
| 6 | **Unasserted generation contract** — the depth probe posted a pad to a chat endpoint with no instruction | all 69 reps generated exactly **17 tokens**; decode read 52.27 tok/s at ctx 131,072 and acceptance exactly 1.000; **PN-24's at-depth half and Track A Amendment 1 both withdrawn** | PN-30 | `/completion` + continuation cue; absolute 128-token floor per rep (a fraction-of-`n_predict` rule wrongly failed a cell that stopped at 258 on EOS) |
| 7 | **Safety check broader than its intent** — `preflight()` used `pgrep -af "watchdog.sh\|worker.sh"`, unanchored, and the campaign monitor was named `campaign_watchdog.sh` | an 11-hour campaign — 3 batteries, 31 GPU cells, 4 chained runners — **cascaded to failure in 8 minutes**. No corruption, no GPU consumed | PN-27 | pattern path-anchored to `orchestrator/watchdog[.]sh\|orchestrator/worker[.]sh`; monitor renamed `campaign_sentinel.sh`. A **second** instance found while fixing the first: the sentinel's `chains_alive()` used `[s]9_chain.sh`, whose unescaped `.` sat one character from matching its own `tail -f .../s9_chain.log` |

**The generalisation the paper should make:** *the instrument is part of the experiment.* Six
distinct defects, each of which produced **plausible-looking output rather than an obvious
failure**, and every one caught by a rule rather than by luck. The rules that caught them:
preserve raw tool output before teardown; assert that a **measurement exists**, not that a process
exited 0; assert the **generation** contract as well as the input contract; name the estimator and
the n in the table itself; anchor process-matching predicates to a path.

### 9.6 Validation gate (T2) — what green means

`validate_v2.py` runs four positive checks and a self-test that injects four faults and requires
each to be caught:

| check | asserts |
|---|---|
| C1 | server healthy · `/props n_ctx` == requested (`-fit off`) · single slot · argv complete · `-fa on` behavioural evidence (`-ctv q4_0` loaded) · image id == manifest |
| C2 | the DEC-2 sampling block reads back field-exact in `generation_settings` |
| C3 | thinking-control both directions |
| C4 | requested-model identity |

| fault | injected | caught by |
|---|---|---|
| F1 | `-fit on` at an unfittable 999,999,999 | C1 |
| F2 | no `chat_template_kwargs` (thinking leaks on) | C3 |
| F3 | request carries no sampling fields | C2 |
| F4 | requested-model mismatch | C4 |

Artifacts `validate-v2.json` (`ok: true`, C1–C4 all true), `validate-v2-selftest.json`
(`ok: true`, all four faults caught) · PN-1…PN-4 · **CURRENT**

### 9.7 Pads — the depth instrument

Rule: `target = int(ctx*0.95) − 512`; a pad is valid iff `|actual − target| ≤ max(64, 0.005·target)`
**and** `actual/ctx ≥ 0.90`. Tokenized with `/srv/models/Qwen3.8-27B-UD-Q4_K_XL.gguf` on the pinned
image. Corpus `/srv/bench/e12/corpus.txt`, 9,097,163 B.

| ctx | target | actual | chars | prefill_frac | err |
|---|---|---|---|---|---|
| 262,144 | 248,524 | 248,522 | 1,000,208 | 0.9480 | −2 |
| 245,760 | 232,960 | 232,933 | 935,425 | 0.9478 | −27 |
| 229,376 | 217,395 | 217,140 | 864,938 | 0.9467 | −255 |
| 212,992 | 201,830 | 201,672 | 794,918 | 0.9469 | −158 |
| 196,608 | 186,265 | 186,265 | 721,749 | 0.9474 | 0 |
| 180,224 | 170,700 | 170,481 | 651,701 | 0.9459 | −219 |
| 163,840 | 155,136 | 155,098 | 581,691 | 0.9466 | −38 |

`all_ok: true`. Artifact `data/raw/e12/pads-manifest.json` · **CURRENT**
**Prefix caching is what makes depth testing affordable** — a 123,666-token pad re-prefills in
~3.5 s on reps 2–3 (`prompt_n` 4, `cache_n` 248,523 at the 262,144 rung), against ~490 s cold.

### 9.8 Quarantine register — data excluded, never deleted

| item | reason |
|---|---|
| `tsweep-v2-Q4_K_XL.json.shallow-prefill-79pct` · `.superseded-shallow` | prefill_frac 0.7973 (PN-5) |
| `tsweep-v2-{Q4_K_XL,Q6_K,Q6_K_XL}.json.race-025630` | double-runner race, 32 junk cells (PN-10) |
| `tsweep-v2-Q6_K_XL.json.badratios` | pre-DEC-7 ratio list that pointed the wrong way |
| `pad_201830_0.txt.bisection-bug` · `pad_217395_0.txt.bisection-bug` | short pads (PN-5) |
| `pad_e12.py.orig` · `tsweep_v2.py.orig` | pre-fix harness source, kept for diff |
| `s9d-depthsweep.json.degenerate-17tok-20260901` + its README | 17-token generations (PN-30) |
| `empty-serverlogs/` + `REGISTER.json` | 7 empty serverlogs, all inside 02:55:04–02:55:52Z (the D6 race window), 4 of them the recovery path's own `e12-stale-recover-*`. Classified as **stillborn containers** (killed between `docker run -d` and start) with `evidence_lost: false` for each. **A2's check was left exactly as strict** — it will still fail on a genuinely empty log from a container that ran |
| *(host only, ⚑F-20)* `quarantine/s11-gen-c8192.json` | not pulled |

`data/raw/e12/quarantine/LISTING.txt` · `WAVE1-REVIEW.md` (full defect register D1–D8) · PN-5,
PN-10, PN-30 · **EXCLUDED — retained**

### 9.9 Data on the pre-E12 exclusion list

1. `Q6_K_openai_temp_0.0` — 51 % empty, dirty run
2. `NVFP4_openai_temp_0.0.jsonl` — 1 solution, aborted
3. all `humaneval-thinking/` v1 — `max_new_tokens` 768, superseded by v2
4. `vllm-NVFP4-mtp/` — context-limited partial
5. `verified50` / `q3-verified50` with no `eval.log`
6. `power-dflash2-bench.csv` — header mislabeled
7. old non-thinking SWE runs with different instance sets

`data/multivac-src/multivac-CLAUDE.md` · **EXCLUDED**

### 9.10 Measurements that do not exist and will not

Recorded so nobody re-derives them as open work (DEC-12, DEC-13, DEC-15):

| not measured | why |
|---|---|
| `reasoning_effort` equivalence (G17) | cancelled; half-answered by PN-3 |
| Losslessness at temperature > 0 (G8) | cancelled — a weak instrument by construction; speculation consumes the sampler's RNG differently, so outputs diverge whether or not verification is exact. **PN-23/PN-26 are greedy-only, permanently** |
| Presence-penalty probe (does `presence_penalty 1.5` harm code generation?) | cancelled on cost. **Genuinely open** — and it is arguably the paper's thesis in a second dimension |
| Draft-KV dtype (`-ctkd`/`-ctvd`) | never tested |
| Per-configuration energy / J-per-token curve | Wave 4 cancelled; PN-11 is the host baseline only |
| KL divergence at depth | infeasible on 14 GiB (§9.4) |
| Absolute divergence vs FP16 | no FP16 on host; a 27B F16 GGUF ≈ 54 GB. **All divergence is ladder-relative** |
| LiveCodeBench v6 · SWE-bench Pro | never set up (G19) — so no comparability with the model's published scores |
| Multilingual, tool-calling, agentic domains | out of scope; two corpora only (English prose, Python) |
| PN-9's quant/depth/ratio confound | S9d was reinstated to close it and failed on power (§4.6). **Permanent limitation** |
| Where in MTP verification the divergence arises | needs engine-level instrumentation, not output comparison |

---

# Appendix A — Track A decision, and its two amendments

| version | date | pinned draft depth | basis | status |
|---|---|---|---|---|
| original | 2026-08-30 | `--spec-draft-n-max 2` | Wave 1 + SSA | **CURRENT** |
| Amendment 1 | 2026-08-31 | n=4 | S8's at-depth 46.4 % lead | **WITHDRAWN by Amendment 2** |
| Amendment 2 | 2026-09-01 | **n=2 restored** | PN-30: the at-depth measurement timed 17 tokens | **CURRENT** |

**The configuration of record:**
```
-m Qwen3.8-27B-UD-Q6_K.gguf -ngl 99 -sm layer -ts 58,42 -c 262144 -fit off -fa on \
   -ctk q4_0 -ctv q4_0 -b 2048 -ub 512 -np 1 -ctxcp 32 \
   --spec-type draft-mtp --spec-draft-n-max 2
```
Full 262,144 window · code KLD **0.005829 ± 0.000233** · decode **11.90 tok/s** at 95 % depth
(median of 3).
Fallback A (max fidelity): UD-Q6_K_XL `-ts 56,44 -c 212992`.
Fallback B (min VRAM): UD-Q4_K_XL `-ts 56,44 -c 262144` — 17.56 GB on disk, **3.69×** Q6_K's code
divergence.
**UD-Q5_K_XL is dominated** and recommended against: same ceiling as UD-Q6_K, **1.76×** the code
divergence, decode indistinguishable, only 1.1 GB smaller.
`docs/paper/TRACK-A-DECISION.md` · PN-13…PN-21, L-8…L-10, L-16.

S9e later put n=2 and n=4 at **12.474 vs 12.875 tok/s** at 262,144 (3.2 % apart, 30–53 % rep
spread) — so Amendment 2's revert now rests on *"indistinguishable"* rather than on a withdrawn
measurement, which is firmer ground. **n=8 does not load at 262,144.**

---

# Appendix B — PN index, with status

| PN | one line | §here | status |
|---|---|---|---|
| PN-1 | measured server sampling defaults match no documented set | 9.1 | CURRENT |
| PN-2 | 2-token probe discriminates thinking state | 9.2 | CURRENT |
| PN-3 | `reasoning_effort: none` raises a Jinja exception | 9.2 | CURRENT |
| PN-4 | `-fit on` did not shrink at 262,144 on this engine | 9.3 | CURRENT |
| PN-5 | documented-but-unasserted depth gate → 0.797 prefill | 9.5 | CURRENT |
| PN-6 | the tensor split, not the quant, sets the ceiling (Q5_K_XL) | 2.2 | **SCOPED by PN-39** — holds for 2 of 4 arms |
| PN-7 | the optimal `-ts` is quant-specific and non-portable | 2.4 | CURRENT ⚑F-11 |
| PN-8 | minimum imbalance ≠ maximum throughput | 2.2 | **CORRECTED by PN-42** — the relation is not monotone |
| PN-9 | MTP acceptance varies across quants | 4.3 | CURRENT but **confounded, permanently** |
| PN-10 | three orchestration defects producing plausible wrong output | 9.5 | CURRENT |
| PN-11 | host power envelope, 12 h, 43,182 samples | 7.1 | CURRENT |
| PN-12 | 14 °C thermal asymmetry under GPU0-weighted splits | 7.2 | CURRENT — confounded |
| PN-13 | KLD separates the ladder at 3.7–11.8 σ | 1.1, 1.2 | CURRENT |
| PN-14 | code degrades ~2× prose, widening with aggressiveness | 1.4 | CURRENT ⚑F-7 |
| PN-15 | q4_0 KV costs 51 % of a quantization level | 5.1 | **QUALIFIED by PN-43** — label collision; size comparison, not additive |
| PN-16 | top-1 and KLD disagree about which domain is hurt | 1.6 | CURRENT |
| PN-17 | exit-code-only success reports a run that measured nothing | 9.5 | CURRENT |
| PN-18 | `-ctxcp 32` is free throughput | 2.5 | CURRENT — directional |
| PN-19 | decode does not discriminate the arms at 262,144 | 3.1 | **STATISTICS SUPERSEDED by PN-36** — conclusion stands |
| PN-20 | an unnamed estimator reversed a ranking | 9.5 | CURRENT — incomplete ⚑F-3 |
| PN-21 | three-tier domain hierarchy; none passes on the task distribution | 1.3, 1.4 | CURRENT |
| PN-22 | a multiple-choice battery cannot see quantization damage | 8.1 | CURRENT |
| PN-23 | speculative decoding is not output-identical (131/164) | 4.1 | CURRENT — **mechanism withdrawn by PN-26** |
| PN-24 | n=4 beats n=2, and the gap grows with depth | 3.3, 4.5 | **at-depth half WITHDRAWN (PN-30)**; 32 K half CURRENT |
| PN-25 | a mis-bound drafter produces a clean silent zero | 9.5 | CURRENT — the 5 cells EXCLUDED |
| PN-26 | the divergence is deterministic and systematic | 4.2 | CURRENT |
| PN-27 | the supervision killed the campaign it was built to protect | 9.5 | CURRENT — incident |
| PN-28 | a generative coding benchmark cannot see it either | 8.2 | **STATISTICS CORRECTED by PN-40** — report the bound, not p=1.0 |
| PN-29 | DFlash2: fastest at 32 K, strictly dominated at depth | 4.4 | CURRENT — equivalence engine-confounded |
| PN-30 | a throughput measurement is only as valid as the generation it timed | 9.5, 4.5, 4.7 | CURRENT — **withdraws PN-24 at depth + Amendment 1** |
| PN-31 | KLD is not measurable at long context on 14 GiB | 9.4 | CURRENT — footnote material |
| PN-32 | acceptance falls with draft depth (p=0.0017); the sweep cannot rank | 4.6 | CURRENT for acceptance; UNRANKABLE for speed |
| PN-33 | 4-bit costs nothing on S-NIAH to 131,072 | 6.1 | S-NIAH half **CURRENT**; **MK-NIAH half SUPERSEDED by PN-44** |
| PN-34 | benchmark sensitivity is gated by task headroom | 6.1 | **MECHANISM SUPERSEDED by PN-37** — saturation is false for 2 of 3 instruments |
| PN-35 | code damage lives in the p95–p99.9 tail; the code/prose ordering reverses between p90 and p95 | 1.7 | **CURRENT — the study's headline.** Re-derived from the artifact |
| PN-36 | supersedes PN-19's statistics: n=6 spanned four depths; true spread 46.7 %; Q4_K_XL n=1 | 3.1 | **CURRENT** — but see ⚑F-26 (estimator switch, `-ctxcp` mixing) |
| PN-37 | supersedes PN-34's mechanism: saturation false for 2 of 3 instruments; framing is Dutta et al. (R13) | 6.1 | CURRENT |
| PN-38 | free-running greedy generation cannot measure quantization distance | 6.4 | CURRENT — methodological negative result |
| PN-39 | scopes PN-6: the split sets the ceiling for 2 of 4 arms; failures are single attempts | 2.2 | CURRENT |
| PN-40 | corrects PN-28: its McNemar could not reach p<0.05; use the paired bound | 8.2 | CURRENT |
| PN-41 | corrects the cost contrast: 2.15 h vs ≈4.8 h, a 2.2× ratio — the 60× was fabricated | 8.4b | CURRENT |
| PN-42 | corrects PN-8: `54,46` is not the least balanced ratio; not monotone | 2.2 | CURRENT |
| PN-43 | qualifies PN-15: a label collision corrupted `metrics_reparsed.ppl`; "51 %" is a size comparison | 5.1 | CURRENT |
| PN-44 | **supersedes PN-33's MK-NIAH**: n=100 gives 89.0 vs 79.0, p = 0.0020, −10.00 pts [−15.88, −4.12] | 6.1 | **CURRENT — the long-context result.** Re-derived from raw predictions |

**Measurements with no PN entry (UNWRITTEN), after the review round:** §3.2 prefill-vs-depth ·
§3.4 S6 decode medians · §3.5 the S11 fixed-ratio cross-quant speed ladder · §6.2 the
`variable_tracking` exclusion · §2.7 E6 split-mode reproducibility.

S11's rejection — the largest gap on 2026-09-02 — **is now written up as PN-38**. The
`variable_tracking` exclusion (§6.2) is now the largest remaining one, and it has become
**load-bearing**: PN-37 requires it to be disclosed *in the same paragraph* as the difficulty
claim, because it is the one harder task this study ran and excluded. It still has no note of its
own.
