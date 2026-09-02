# Reviewer A — adversarial rigor review

**Venue frame:** systems/measurement track (MLSys / arXiv cs.LG systems report).
**Review basis:** `README.md`, `CLAUDE.md`, `manuscript/OUTLINE.md`, `docs/paper/PAPER-NOTES.md`
(PN-1…PN-34), `docs/paper/METHOD-REFERENCES.md` (R1–R10), `docs/paper/TRACK-A-DECISION.md`
(+ Amendments 1–2), `docs/build-stream/2026-08-30-quant-bench-trackA.md` (DEC-1…DEC-15, L-1…L-18),
and **direct re-derivation from the artifacts** in `data/raw/e12/`, including the mirrored harness
source in `data/raw/e12/harness-src/`.

**Blindness declaration.** `manuscript/review/insider-notes.md` exists in this directory. I did not
open it. Two of its lines surfaced incidentally in a repository-wide `grep` for the string `91.67`;
they are not used as input to any judgement below, and every conclusion here is re-derived from
primary artifacts.

**Method note.** Every quantitative claim in this review was recomputed from the JSON artifacts or
from the harness source. Where I say a number checks out, I computed it. Where I say a number does
not, I show the arithmetic.

---

## 1. Summary verdict

**Recommendation: major revision, and one claim must be withdrawn before submission.**

This is an unusually honest measurement study. The caveat discipline in `PAPER-NOTES.md` is better
than most published systems work: notes routinely retract their own force (PN-9, PN-24, PN-32,
PN-33), withdrawn results are recorded rather than deleted, and the project caught four
instrumentation defects that would have produced publishable-looking garbage (PN-5, PN-17, PN-25,
PN-30). The core empirical contribution — that KL divergence separates these quantizations at
3.7–11.8 σ while three task instruments separate them nowhere — is **real, correctly computed, and
worth publishing**.

But the paper as outlined cannot be submitted, for three reasons of descending severity.

1. **The declared central thesis (PN-34) has no artifact.** The MK-NIAH datum on which it entirely
   depends — "100.0 vs 91.67 at 131,072" — does not exist anywhere in the evidence tree. It is not
   in `data/raw/e12/ruler/s12-ruler.json`; there is no MK-NIAH cell, no MK-NIAH entry in that
   file's `accuracy_recovery`, and no `s12-preds-*-multikey-*.json`. The mirrored harness
   (`s12_ruler.py`) declares `TASKS = ["niah"]` and invokes RULER's generator with
   `--type_needle_k words --type_needle_v numbers` and **no `--num_needle_k`**, i.e. it can only
   produce single-key NIAH. `s12_gen.log` records generation of `niah_*` and `variable_tracking_*`
   only. `s12_chain.log` records four phases (c8192, c32768, c131072, summarize) and no MK-NIAH.
   The string `91.67` appears in **zero** data files and only in prose. **V1** below.

2. **Two load-bearing numbers are pooled across conditions that are not comparable**, and the paper
   does not know it. PN-19's "n=6 repetitions at 262,144" for UD-Q4_K_XL is in fact six readings at
   **four different context depths**; and the code corpus behind the study's headline contribution
   is absent from the repository, undescribed, and — on the model's own perplexity — is very
   largely boilerplate. **V2** and **V3** below.

3. **The study applies its own best statistical insight to one result and not to the others.**
   PN-32 identifies, correctly and valuably, that pooled per-event intervals on clustered
   observations are "misleading" because the unit of independence is the generation, not the token.
   PN-13's headline intervals — the paper's single most important number — have exactly the same
   defect and are presented as "non-overlapping confidence intervals" at "3.7–11.8 σ". **V4** and §4.2.

4. **The speculative-decoding claim is scoped correctly in PN-23 and loses its scope in every
   downstream restatement.** The newly added R12 converts that drift from a wording problem into a
   confrontation the paper cannot win: it prints a competing implementation's correctness claim
   beside a measurement of a different implementation. §11 answers this in full, at the
   coordinator's request, and it is ranked as **V11**.

Everything in categories 3 and 4 is fixable by rewording. Category 2 is fixable by re-analysis plus
one corpus disclosure. Category 1 requires either ~11 GPU-hours of new measurement or the
retraction of the paper's working title.

**What I would accept without further measurement:** PN-13, PN-14, PN-16, PN-21 (with corpus
disclosure and clustered intervals), PN-22 and PN-28 as a *paired-discordance* result rather than a
p-value result, PN-6/PN-7 restated per-quant, PN-23/PN-26 with the mechanism claim narrowed, PN-15,
PN-31, and the reproducibility register.

**What must go or be re-measured:** PN-34 in its entirety; PN-33's MK-NIAH half; PN-9's finding
line; PN-8's imbalance claim; PN-19's noise figure; the "20 hours vs 20 minutes" cost contrast; and
every withdrawn number still live in `README.md` and PN-29.

---

## 2. Claim-by-claim audit table

Legend — **S** supported as stated · **S−** supported but overstated in wording · **W** weak (true
but the evidence cannot carry the stated generality) · **U** unsupported by the cited artifact ·
**E** contains a factual error.

| PN | Claim (compressed) | Verdict | Finding |
|---|---|---|---|
| **PN-1** | Engine sampling defaults are temp 1.0 / top_k 20 / top_p 0.95 / min_p 0.05 — a fourth, undocumented configuration | **S** | n=1 launch, self-tested by fault injection (F3). Note the artifact path in the note is the pre-remap `data/bench/…`; the remap banner covers it. Fine as a hazard note. |
| **PN-2** | A 2-token probe discriminates thinking state; `enable_thinking:false` works | **S** | Positive and negative control both green (C3, F2). Good practice; keep. |
| **PN-3** | `reasoning_effort:"none"` raises a Jinja exception | **S** | Error body recorded verbatim. Correctly labelled "not a measurement of no-think equivalence". |
| **PN-4** | `-fit on` did not silently shrink at 262,144 on this image; negative control had to be injected | **S** | Honest negative control. The `caught=false` / `caught=true` pair is the right way to report it. |
| **PN-5** | A documented-but-unasserted gate let a 79.7 % prefill pass as success | **S** | Quarantine artifact present (`tsweep-v2-Q4_K_XL.json.shallow-prefill-79pct`). Root cause traced to `pad_e12.py`'s fixed bracket; the fix is visible in the mirrored source. Strongest of the reproducibility notes. |
| **PN-6** | Q5_K_XL reaches 262,144 at five `-ts` ratios and **fails at the default split** | **S−** | Every cell verified in `tsweep-v2-Q5_K_XL.json`. But the default-split failure — the headline — is **one attempt**, and the project's own hard rule #4 says a single failure lies (±100–200 MiB layer-split noise). Also the generalisation "a ceiling published without its tensor-split is a property of the split" is **false for Q4_K_XL** (V6). Restate per-quant. |
| **PN-7** | The optimal `-ts` is quant-specific and non-monotone; Q6_K_XL loads 196,608 only at `56,44` | **S** | All five cells verified. Caveat correctly flags the in-flight status; 212,992 later bracketed with two failures at 229,376 (`1:base` and `1:retest`). Good. |
| **PN-8** | Minimising VRAM imbalance does not maximise decode; "least balanced that still loads" is fastest; 27 % spread | **E** | **Factually wrong.** 60,40 (1,176 MiB) and 62,38 (1,750 MiB) are *less* balanced than 54,46 (742 MiB) and both load. The imbalance→decode series is 28→8.50, 166→10.78, 742→10.82, 1,176→10.67, 1,750→10.44: a single low outlier, not a trend. Excluding the one 8.50 reading (n=1), the four remaining ratios span 3.6 %. W6 in §9. |
| **PN-9** | MTP acceptance varies strongly by quant (0.897 / 0.564 / 0.516) | **U** | **Refuted by its own artifact.** Within-cell rep-to-rep acceptance at a *fixed* quant/ctx/ratio spans 0.592–0.911 (Q6_K), 0.516–0.734 (Q5_K_XL), 0.592–0.791 (Q4_K_XL) — covering the entire between-quant range claimed. Acceptance is also *identical across `-ts` ratios within a rep index*, i.e. it tracks the generated text, not the configuration. Depth attribution is also wrong: Q4_K_XL's 0.5642 is at 245,760, not 212,992. V5. |
| **PN-10** | Three orchestration defects each produced plausible wrong output | **S−** | Content credible. **Cited evidence missing**: the `*.race-025630` artifacts named in the note are in `quarantine/LISTING.txt` but not in `quarantine/`. |
| **PN-11** | Host power envelope 149.2 W mean / 334.1 W loaded, 1.791 kWh over 12 h | **S** | Caveat correctly labels `est_system_w` as modelled, and the window as mixed-workload. Fine as a host baseline; do not derive per-config J/tok from it (the note says so). |
| **PN-12** | `-ts 5x,4x` has a thermal consequence: GPU0 90 °C vs GPU1 76 °C | **W** | Caveat is exemplary ("OBSERVATIONAL AND CONFOUNDED", airflow uncontrolled). Keep as an observation; never as a result. Consider demoting to one sentence. |
| **PN-13** | KLD over 65,536 tokens separates all three arms, non-overlapping intervals, 3.7–11.8 σ | **S−** | **σ arithmetic verified exactly**: wikitext Q6_K–Q5 = 3.71, Q5–Q4 = 8.48; code Q6_K–Q5 = 8.67, Q5–Q4 = 11.82. Monotone in both domains ✓. **But the intervals are pooled per-token over an autocorrelated, extremely heavy-tailed quantity** (code Q4_K_XL: mean 0.021529, median 1.7e-05 — mean is 1,266× median; ≥26 % of the mass sits in the top 1 % of tokens). This is PN-32's own clustering defect. V4 and §4.2. |
| **PN-14** | Code damage ≈ 2× prose damage, widening with aggressiveness (1.75× / 2.30× / 2.62×) | **S−** | Ratios verified exactly (1.755 / 2.303 / 2.623). **Threatened by corpus composition**: reference-arm PPL on this "code" corpus is 1.1809 = **0.240 bits/token**, against 2.534 for WikiText-2. V3. |
| **PN-15** | q4_0 KV costs 0.002955 ± 0.000127 KLD = 51 % of a quant level; PPL moves only +0.15 % | **S−** | Ratio verified (0.5069 → "51 %"). Design is clean (f16 base vs q4_0 scoring, same model/corpus/seed). **But the artifact self-contradicts on the PPL half**: two cells share the label `ssa-Q6_K_XL-code-base` and therefore one serverlog path; the f16 run overwrote the q4_0 run's log, so the q4_0 cell's `metrics_reparsed.ppl` reads 1.1791 — the f16 value — against its own `metrics.ppl` of 1.1809. §5.5. Also: "51 % of a quantization level" compares a KV-dtype divergence to a weight-quantization divergence as if KL were additive. It is not. |
| **PN-16** | Top-1 agreement and mean KLD disagree about which domain is hurt | **S** | Verified: code top-1 98.4–99.4 % vs prose 96.2–97.5 %, with ~2× the KLD. The metric-pair argument is the most useful methodological point in the paper. Its stated mechanism (predictability drives argmax stability) is correctly labelled an interpretation. |
| **PN-17** | A harness scoring by exit code alone reported ten successful cells that measured nothing | **S−** | True and well documented. **But the note's own headline — "every number was recoverable ONLY because the log-preservation rule had written full stdout to disk" — has a counter-example inside the same artifact**: the label collision above destroyed one cell's log, and the reparse silently substituted another run's number. Report that; it strengthens the lesson. |
| **PN-18** | `-ctxcp` 4→32 gains 6.8 % decode / 7.6 % prefill at identical VRAM | **S** | Verified in the `d3` block (10.749→11.482, 468.65→504.34, ΔVRAM 0/0). Caveat correctly refuses to quote the 6.8 % as an effect. **But Track A pins `-ctxcp 32` and quotes 11.90 tok/s, which is the median of three `-ctxcp 4` reps**; the only `-ctxcp 32` reading is 11.48 (n=1). |
| **PN-19** | Three arms indistinguishable at 262,144: 12.70 / 12.61 / 11.90, 6.7 % span vs 32.9 % within-arm noise | **E** | **The Q4_K_XL "n=6 at 262,144" is six readings at four depths**: 15.96/13.12/13.33 @212,992; 11.81 @229,376; 12.01 @245,760; 12.10 @262,144. The 32.9 % figure is between-depth variation, not repetition noise. V2. The *conclusion* survives (corrected like-for-like: Q5 12.70 n=3, Q4 12.10 n=1, Q6_K 11.90 n=3 — 6.7 % span), but the noise statistic that carries the argument does not. |
| **PN-20** | An aggregator that does not pin its statistic mixed three estimators in one column | **S−** | The defect is real and the note is valuable. **But its own correction is incomplete**: the recomputed median it substitutes for Q4_K_XL (12.61) is itself the median of four different context depths, and `wave1-summary.md` contains two further errors PN-20 does not mention (V6). A note that supersedes a defective file must supersede all of its defects. |
| **PN-21** | Three-tier hierarchy prose < code < task prompts; amplification 3.13× / 3.87× / 4.40× | **S−** | All ratios verified exactly (3.13 / 3.87 / 4.40; task/code 1.785 / 1.681 / 1.678). S5 σ separations verified (8.26 and 11.17 at n=18,432). Strongest result in the paper. Inherits V3 (corpus) and V4 (clustering). |
| **PN-22** | HellaSwag is *structurally* insensitive; two arms answer all 400 identically; all p ≥ 0.13 | **W/E** | Accuracies reconcile exactly (331/329/331/333 of 400). **Three problems.** (a) The paired vectors are **reconstructed** by differencing a cumulative accuracy table (`s7_paired.py`), with no per-item IDs recorded and no verification that the four runs saw the same items — the script's stated justification (same `-s` seed) is an assumption about llama.cpp's internal task-shuffle RNG that was never checked. (b) The test is **chi-square with continuity correction**, not exact McNemar, at b+c = 2–4 where the exact test is mandatory (0.1336 vs exact 0.1250). (c) **Every one of the six pairs has b=0 or c=0** — the four outcome vectors are perfectly nested, Q4_K_XL ⊇ Q5_K_XL = Q6_K_XL ⊇ Q6_K. That is not the signature of an insensitive instrument; it is a systematic, monotone signal running *against* the ladder, and the paper does not remark on it. V9. |
| **PN-23** | MTP is not output-identical: 131/164 byte-exact, first divergence at char 715/730 | **S** | Verified exactly in `s8-humaneval.json.equivalence` (131, 79.88, 715/730) and Jaccard 0.6098 → 0.610 ✓. Excellent result, correctly framed as an equivalence finding rather than a ranking. **PN-23's own finding line is the only correctly scoped statement of this result in the repository** — "with the model's built-in MTP head … on this engine". Every downstream restatement drops one or both qualifiers (V11). |
| **PN-24** | n=4 beats n=2 at every depth; advantage grows with depth | **Partly withdrawn** | ctx-32,768 half (47.03 vs 37.44, +25.6 %) stands over 164 generations. At-depth half withdrawn by PN-30 ✓. **But the withdrawal is not propagated**: PN-29 and `README.md` still cite 16.81 as live (V7), and S9e has since measured the same question properly — n=2 12.474 vs n=4 12.875, a 3.2 % gap — which PN-24 is never updated to acknowledge. |
| **PN-25** | A mis-bound drafter produced a clean 0.000 indistinguishable from catastrophic performance | **S** | Excellent. **But the poisoned row is still live in the artifact**: `s8-humaneval.json.equivalence.dflash4` records `exact_match: 0, lossless: false` for a server that never loaded — precisely the confusion the note forbids. Annotate the artifact or the note's own rule is unenforced. |
| **PN-26** | The engine is deterministic; speculation is a *reproducibly different* decode path | **S−** | Determinism verified (nospec_self and mtp2_self both 164/164 identical, differs=0). **The mechanistic conclusion is a non sequitur.** PN-26 states that determinism "excludes" the batch-shape / float-associativity account. It does not: a different reduction order under a different batch shape is itself deterministic and reproduces perfectly on repeat. PN-26 rules out *run-to-run* nondeterminism only. §5.2. Also: PN-26 says the remaining question "needs engine-level instrumentation rather than output comparison" — **this is false, and the discriminating analysis is free** (§11.2). |
| **PN-27** | A `pgrep` pattern broader than its intent matched the tooling built to supervise it | **S** | An incident report, correctly labelled as such, with the fix verified live under the failing condition. Keep; it is the best-written note in the file. |
| **PN-28** | The generative anchor is null: 93.90 vs 94.51 base; paired discordance 3 and 5; exact McNemar p = 1.0 | **S/E** | **All Wilson intervals verified exactly** ([89.14, 96.65], [89.90, 97.09], [84.03, 93.43], [84.74, 93.91]); discordance arithmetic reconciles (153+1+2+8 = 164; 145+2+3+14 = 164); exact two-sided p = 1.0 for (1,2) and (2,3) ✓. **Two problems.** (a) **The test was incapable of significance by construction**: with 3 discordant pairs the minimum achievable two-sided exact p is 0.25, and with 5 it is 0.0625. Neither could have reached 0.05 under *any* outcome. The paper must say this. (b) **Factual error**: "the SAME two arms that differ by 3.69× in mean KL divergence" and "top-1 agreement … differs by 2.15 points" both describe **Q4_K_XL vs Q6_K**, not the S6 pair Q4_K_XL vs Q6_K_XL. §5.3. |
| **PN-29** | DFlash2 fastest at 32 K (51.78, acc 0.9172), dominated at depth (163,840 max, 8.34, acc 0.4583) | **S−** | All numbers verified. Engine-confound caveat is exemplary. **But it cites the withdrawn 16.81 tok/s as its comparator**, and the "acceptance collapse 0.9172 → 0.4583" compares HumanEval+ generation against pad continuation — different content, and the tsweep data show acceptance is content-dominated (PN-9 above). Depth and task are confounded in the collapse. |
| **PN-30** | A 24-cell sweep timed 17 generated tokens; PN-24's at-depth half and S8's at-depth figures withdrawn | **S** | The single best incident note in the study. Verified against the quarantined artifact. The withdrawal scope is stated precisely and correctly. |
| **PN-31** | KLD at long context is not measurable on 14 GiB; ceiling n_ctx 8,192 | **S** | Measured one rung at a time rather than extrapolated; storage constant cross-checked against the tool's own README. Correctly demoted to footnote by DEC-15. |
| **PN-32** | Acceptance falls with draft depth in 12/13 pairs (sign test p = 0.0017); the design cannot rank | **S−** | p verified: P(X ≥ 12 | n=13, p=0.5) = 0.001709 ✓; the 13 pairs enumerate correctly from the artifact (7 at 131,072 all falling, 6 at 196,608 with Q5_K_XL n4→n8 rising). Spread figures verified (166.1 % max, and 19 of 21 cells above 10 %). **Two problems.** (a) The 13 pairs are **not independent**: within each arm×depth chain, (n2→n4) and (n4→n8) share the n=4 observation; the effective unit count is 8, giving p = 0.0039. (b) **The null is not credible**: acceptance = accepted/drafted decreases in draft length by construction for any imperfect drafter, so a coin-flip null tests a near-identity. §4.4. The *clustering lesson* — the genuinely valuable half — stands. |
| **PN-33** | S-NIAH 100.0 at three lengths for both arms; MK-NIAH 100.0 vs 91.67 at 131,072 | **Half S, half U** | **S-NIAH half fully verified**: 100.0 / 100.0 at 8,192, 32,768 and 131,072, n=25/25/12, 0 empty, prompt_n medians 8,041 / 32,616 / 130,941 ✓. Wilson intervals recomputed: 12/12 → [75.8, 100.0] (note quotes 75.7), 11/12 → [64.6, 98.5] ✓. **MK-NIAH half has no artifact at all.** V1. |
| **PN-34** | Benchmark sensitivity is gated by task headroom, not modality or context length | **U** | The claim's positive evidence is the S-NIAH/MK-NIAH contrast. Without MK-NIAH it reduces to "one saturated task was saturated", which supports nothing about difficulty. The three-instrument arc (PN-22, PN-28, PN-33) establishes that **three benchmarks were blind**; it does not establish **why**, and "headroom" is the study's hypothesis, not its measurement. V1 and §7. |

**Notes without a paper note.** `data/raw/e12/s11/s11-divdepth.json` records 12 measured cells and
appears in **no PN entry**. The project's own protocol (`PAPER-NOTES-PROTOCOL.md`, and hard rule 9
in `CLAUDE.md`) states that "a stage that produced measurements but appended no paper notes is an
incomplete stage (reviewer should raise a finding)". Raised. §6.1.

---

## 3. Top 12 vulnerabilities, ranked by severity

> **Ranking note.** V1–V10 were written before R12 was added to `METHOD-REFERENCES.md` and before
> the harness-source audit completed. V11 and V12 are appended at the end to keep every
> cross-reference stable, but they rank **4th** and **8th** respectively in severity. Read the
> order as V1, V2, V3, **V11**, V4, V5, V6, **V12**, V7, V8, V9, V10.

### V1 — The paper's central thesis rests on a number with no evidence *(fatal as written)*

`PN-34` is the declared methodological contribution, is contribution #2 in the outline, and supplies
the working title's argument. Its entire discriminating datum is MK-NIAH 100.0 vs 91.67. What the
evidence tree actually contains:

```
data/raw/e12/ruler/s12-ruler.json
  "tasks": ["niah", "variable_tracking"]
  "accuracy_recovery": { "8192": {niah:Q4_K_XL 100.0}, "32768": {…100.0}, "131072": {…100.0} }
  cells: niah @8192 ×4 (two duplicated), niah @32768 ×2, niah @131072 ×2
  variable_tracking_excluded_cells: 2 cells @8192
data/raw/e12/ruler/  →  8 prediction files, all `-niah-` or `-variable_tracking-`
data/raw/e12/harness-src/s12_ruler.py
  TASKS = ["niah"]
  cmd += ["--type_needle_k", "words", "--type_needle_v", "numbers"]     # no --num_needle_k
data/raw/e12/logs/s12_gen.log     →  niah_{8192,32768,131072}, variable_tracking_{…}. No multikey.
data/raw/e12/logs/s12_chain.log   →  phases c8192, c32768, c131072, summarize. No MK-NIAH phase.
```

A repository-wide grep for `91.67` returns hits only in prose (`PAPER-NOTES.md`,
`METHOD-REFERENCES.md`, `OUTLINE.md`, the ledger) — **no data file**. RULER's `niah.py` defaults
`num_needle_k=1`; the mirrored harness never overrides it, so it cannot have produced MK-NIAH. L-18's
"MK-NIAH data was pre-generated on CPU while the GPU ran, so the hedge cost nothing until needed" is
consistent with MK-NIAH having been *prepared and never run*.

**Action.** Either (a) locate the run on the host, pull the artifact and the predictions into
`data/raw/e12/ruler/`, and record the exact generator invocation — noting that the chain log and the
harness both argue it does not exist; or (b) **withdraw PN-34 and PN-33's MK-NIAH sentence, change
the working title, and demote the outline's §5.2 diagnostic to a stated hypothesis.** Do not submit with a
headline whose evidence line a reviewer cannot open. This is the failure mode the project's own
rule ("every headline number traces: paper note → artifact → serverlog") exists to prevent.

### V2 — PN-19's noise floor is a depth artifact, and it propagates everywhere

From `tsweep-v2-Q4_K_XL.json`, keyed exactly as stored:

| reading | cell key | actual ctx |
|---|---|---|
| 15.96 | `212992:56,44:1:base` | 212,992 |
| 13.12 | `212992:56,44:2:base` | 212,992 |
| 13.33 | `212992:56,44:3:base` | 212,992 |
| 11.81 | `229376:56,44:1:base` | 229,376 |
| 12.01 | `245760:56,44:1:base` | 245,760 |
| 12.10 | `262144:56,44:1:base` | **262,144** |

PN-19 describes these as "all repetitions at each arm's winning ratio at 262,144". One of six is.
Consequences:

- **32.9 % is not within-arm repetition noise.** It is `(15.96 − 11.81)/12.61`, spanning
  212,992→262,144. The genuine fixed-cell repetition spread at 212,992 is 21.3 %; at 262,144
  UD-Q4_K_XL has **n = 1**.
- The Track A table's `n` column ("6") and the README's "32.9 % within-arm repetition noise" are
  both wrong.
- 32.9 % is then re-used as the host's noise floor in PN-18, PN-24, PN-8 and Amendment 1
  ("the 46.4 % gap exceeds that noise"). Every one of those inherits the error.
- The conclusion survives — corrected like-for-like at 262,144, Q5_K_XL 12.70 (n=3), Q4_K_XL 12.10
  (n=1), Q6_K 11.90 (n=3), a 6.7 % span — but must be restated with n=1 for Q4_K_XL and with the
  honest noise figure. S9d's independent measurement puts rep-to-rep decode spread at up to **166 %**
  (median 34 %), which is the number the paper should be quoting.

### V3 — The code corpus is not in the repository, is not described, and is probably boilerplate

The code-domain divergence result is the study's stated contribution ("quantization damage measured
on code is ~2× prose"). Three facts about the corpus it rests on:

1. **It is absent.** `find . -name "corpus*"` returns nothing. `/srv/bench/e12/corpus.txt` is not
   mirrored, not characterised (no file list, token count, deduplication statement, or licence),
   and appears in no manifest.
2. **The builder repeats and does not deduplicate.** `pad_e12.py::_raw_text` walks
   `sorted(REPO.rglob("*"))` over a django worktree, filtered to `.py/.rst/.txt/.md/.toml`, and
   loops `while n < min_chars: pas += 1; for p in files: …`, prefixing `===== PASS {pas}: … =====`.
   Path-sorted, no shuffle, whole-corpus repetition on shortfall.
3. **The model says it is trivial.** Reference-arm PPL on this corpus is **1.1809 = 0.240
   bits/token**, against 2.534 bits/token on WikiText-2 and 0.606 on the HumanEval+ prompts. The
   per-token KLD distribution agrees: median 1.7e-05 against a mean of 0.021529 (Q4_K_XL, code) —
   the mean is **1,266× the median** — with a 90th percentile of 0.010006 and ≥26 % of the total
   divergence mass in the top 1 % of tokens.

A path-sorted django tree puts `django/conf/locale/*/formats.py` and similar near-identical
boilerplate very early. 0.24 bits/token is not what real source code costs a 27B model; it is what
repeated boilerplate costs.

This does not make PN-14 false, but it changes what it means. The honest reading of the current data
is: *on a corpus that is mostly trivially predictable, the small minority of high-entropy tokens
move far more under quantization than prose tokens do.* That is still interesting — arguably more
interesting — but it is a claim about the tail, not about "code".

**Action.** Publish the corpus manifest (file list, bytes, tokens, dedup fraction, pass count,
licence) in the artifact and the paper; report the KLD distribution, not only its mean (the artifact
already carries median / p90 / p95 / p99 / max — use them); and either show the result survives
deduplication or replicate on a second, non-boilerplate code corpus. Without this, the paper's
central contribution has an open, cheap, and obvious attack.

### V4 — The clustering lesson is applied to one result and not to the headline

PN-32 is right and it is the paper's best statistical insight: "draft events within one generation
are strongly correlated, so the effective sample size is the 3 generations, not the events… A study
reporting per-event binomial intervals on speculative acceptance would claim ±0.02 where the true
run-to-run spread is ±0.3."

PN-13 reports `0.003321 ± 0.000126` over 65,536 tokens taken as 32 contiguous 2,048-token windows of
a single document, computed by a tool that (R1, quoted in the paper's own reference file) "treats
per-token KLD as Gaussian". Tokens within a window are strongly correlated; windows within a
document are correlated; and the quantity is heavy-tailed to the point that the mean is three orders
of magnitude above the median. The effective n is nearer 32 (or, honestly, nearer the number of
distinct source files) than 65,536.

The paper cannot simultaneously teach the clustered-standard-error lesson and rest its headline on a
pooled per-token interval. Either compute a chunk-level interval (32 chunk means → t-interval or
bootstrap; this costs no GPU time, only a re-parse of the per-token `.kld` outputs) or state
explicitly that the ± is a nominal per-token SE and that the separations are reported in units of it
rather than as calibrated confidence intervals.

I expect the separations survive — 3.7 σ nominal against a design effect of, say, 5–10 would fall
below significance, but 8.7 σ and 11.8 σ would not. **Compute it.** It is the cheapest way to
convert the paper's biggest exposure into its second-best methods point.

### V5 — PN-9 is contradicted by the artifact it cites

`tsweep-v2-Q6_K.json`, cell `262144:58,42`, three repetitions of an **identical** configuration:
acceptance **0.592, 0.9111, 0.6105**. `tsweep-v2-Q5_K_XL.json`, `262144:54,46`: **0.516, 0.6937,
0.7338**. `tsweep-v2-Q4_K_XL.json`, `212992:56,44`: **0.7905, 0.592, 0.592**.

PN-9's between-quant range is 0.516–0.897. The within-cell range on a *single quant* is 0.592–0.911.
The claim "acceptance varies strongly across quantization levels" is not merely confounded with
depth and ratio (which the caveat concedes) — it is **smaller than the variation within one cell**.

Worse, acceptance is *identical across `-ts` ratios within a rep index* (Q6_K rep 2 reads 0.9111 at
both 58,42 and 56,44; rep 3 reads 0.6105 at both; Q4_K_XL rep 1 reads 0.7905 at all six ratios).
Acceptance is therefore a property of the sampled continuation, not of the configuration. That is
itself a publishable observation — *speculative acceptance at depth is content-dominated, not
config-dominated* — and it is far more defensible than PN-9's current finding line.

PN-9's stated depth for Q4_K_XL is also wrong (0.5642 is `245760:56,44`, not 212,992), so even the
caveat's confound description is inaccurate.

### V6 — "The ceiling belongs to the split" is false for one of the four arms

`tsweep-v2-Q4_K_XL.json` contains `262144:default:1:base` with `ok: true`, decode 12.14 tok/s,
prefill_frac 0.948, VRAM [12,116 / 15,094] — and also `229376:default` and `245760:default`, both
`ok: true`. **UD-Q4_K_XL reaches the full native window at the engine's default split.** There is no
rebalance gain for it.

`wave1-summary.md` nonetheless reports for Q4_K_XL: "default-split ceiling 196608 | gain +65,536 |
decode 13.33", and concludes "**Fastest at the full native 262,144 window:** Q4_K_XL @ `-ts 56,44` —
13.33 tok/s" — a reading taken at **212,992**. PN-20 supersedes this file for mixing estimators and
does not mention either error.

README finding #3 ("the usable context ceiling belongs to the GPU split, not the quantization") is
therefore a claim about two of four arms. Restate it as such; the correct and still-strong form is
that *for the arms near the per-card wall*, the split is the binding constraint — which is the
physically sensible statement anyway.

### V7 — Withdrawn and refuted claims are live in reader-facing documents

| location | claim | status |
|---|---|---|
| `README.md:98` | Track A config line pins `--spec-draft-n-max 4` | **withdrawn** by Amendment 2; the doc of record pins n=2 |
| `README.md:101` | "16.8 tok/s at 94 % window depth" | **withdrawn** by PN-30 — the 17-token measurement |
| `README.md:80-81` | Jaccard 0.610 "points at numerical nondeterminism from the changed decode batch shape", "the control that would settle it has not been run" | **refuted** by PN-26; the control *was* run |
| `README.md:120` | "The paired generative anchor was never run" | run — PN-28 |
| `README.md:118` | "No 100K–250K task outputs exist anywhere in the corpus" | superseded — PN-33 measured at 131,072 |
| `README.md:14` | "PAPER-NOTES.md (PN-1…PN-25)" | stale — PN-1…PN-34 |
| `PAPER-NOTES.md:73` (PN-29) | "Against MTP n=4's 16.81 tok/s at the full 262,144…" | **withdrawn number in a live note**; §5.4 of the outline cites PN-29 |
| `TRACK-A-DECISION.md:203, 209` | Amendment 1's table (3.43 / 11.48 / **16.81** / +46.4 % / 2.55×→4.90×) and the refuted mechanism paragraph | withdrawn by Amendment 2, but with no inline banner on Amendment 1 §2 itself |
| `CLAUDE.md:151,159,160` | PN-1…PN-25, DEC-1…DEC-11, L-1…L-13 | stale (…PN-34, …DEC-15, …L-18) |
| plan STATUS block | `status: campaign-running`, `last: L-13`, `next_action:` S9 chains | stale; `AGENTS.md` directs readers here as "the live answer" |
| `data/raw/e12/README.md` | documents no artifact after S8 | stale by four batteries |

The README is the repository's front door and its deployment recommendation currently prints a
retracted flag and a retracted number. The outline's own submission checklist requires that
withdrawn claims "appear nowhere except as worked examples in §9"; today they appear in the abstract
of the repository.

### V8 — Both McNemar tests were incapable of significance by construction

Exact two-sided binomial, computed:

| n discordant | minimum achievable two-sided p |
|---|---|
| 2 | 0.5000 |
| 3 | 0.2500 |
| 4 | 0.1250 |
| 5 | 0.0625 |
| 6 | 0.0312 |

PN-28 base has 3 discordant pairs; PN-28 plus has 5; PN-22's largest pair has 4. **None of these
tests could have produced p < 0.05 under any assignment of the discordant pairs.** Reporting
"p = 1.0" and "p ≥ 0.13" as evidence of no difference is, in this regime, reporting the arithmetic
of the sample size rather than a result.

PN-28's caveat gets close ("the informative quantity is the DISCORDANCE, not the p-value") and
should be promoted to the finding line, with the minimum-detectable-effect number stated. PN-22
should drop its p-values entirely and report discordance counts.

Separately, PN-22 uses the continuity-corrected chi-square (`s7_paired.py`: `chi2 = (|B−C|−1)²/(B+C)`,
`p = erfc(√(chi2/2))`), which is the asymptotic form, at b+c = 2–4. Exact is mandatory there; the
difference is 0.1336 vs 0.1250 — immaterial numerically, material to a reviewer's confidence.

### V9 — PN-22's paired data is reconstructed, unverified, and structurally anomalous

`s7_paired.py` recovers per-task outcomes by differencing llama.cpp's running accuracy table:
`correct(n) = round(acc(n)·n − acc(n−1)·(n−1))`, then `out.append(1 if c >= 1 else 0)`. Two issues.

- **The pairing is assumed, not verified.** The script's docstring asserts "every arm was run with
  the same seed (20260830), the tool selects the SAME randomized tasks for each". No per-item
  identifier is recorded in `ssa-s7-paired.json` or `ssa-s7-results.json`, and llama.cpp's
  HellaSwag task shuffle is not necessarily driven by `-s`. The totals reconcile (331/329/331/333),
  which validates the *counts*, not the *alignment*. The headline "answering all 400 items
  identically" is an alignment claim.
- **The structure is extraordinary and unremarked.** Across all six pairs, either b=0 or c=0. The
  four correct-sets are perfectly nested: Q4_K_XL ⊇ Q5_K_XL = Q6_K_XL ⊇ Q6_K. An *insensitive*
  instrument produces discordance in both directions; a *perfectly ordered* one does not. And the
  order runs against the ladder — the most quantized arm is a strict superset of every other. The
  paper presents this as "the most heavily quantized arm scores NOMINALLY HIGHEST", which
  under-describes it: it is not nominally highest, it is *dominant on every item*.

Either this is a genuine and striking anomaly deserving investigation (a length-normalisation
interaction with logit scale is the obvious hypothesis), or it is an artifact of the reconstruction.
The paper cannot leave it unexamined while resting a section on it.

### V10 — The affordability contrast is roughly 4× overstated

The outline (§6) and PN-34 both trade on "~20 minutes of divergence per arm versus roughly 20 hours
of task benchmarking across three modalities". Computed from the artifacts' own timestamps:

| instrument | measured | source |
|---|---|---|
| SSA S2/S3/S4 (KLD, 2 domains, 4 arms + KV control) | **1.95 h** wall (1.19 h of it reference-logits recording) | `ssa-results-parsed.json` |
| SSA S5 (task-prompt KLD) | **0.37 h** | `ssa-s5-results.json` |
| **divergence total** | **2.32 h** ⇒ ~35 min/arm all-in | |
| S7 HellaSwag ×4 arms | **0.54 h** | `ssa-s7-results.json` |
| S9b generative HumanEval+ ×2 arms | **1.43 h** | `s9-s6.json` |
| S12 RULER ×2 arms ×3 lengths | **3.23 h** | `s12-ruler.json` |
| **three-modality task total** | **5.20 h** | |

PN-13's "under 20 minutes of GPU per arm" is true of the *scoring* cells alone (10.6–17.0 min per
arm across both domains) and excludes the 1.19 h of reference-logits recording, which is not
optional and amortises to ~24 min/arm. The honest contrast is **~2.3 h against ~5.2 h — a factor of
~2.2, not ~60.** That is still a real argument (divergence ranks the arms; five hours of task
benchmarking does not), but the current framing will not survive a reviewer with a calculator, and
the outline promises exactly the accounting that refutes it ("Wall-clock and GPU-hours per
instrument").

### V11 — Scope drift on the speculative-decoding claim *(severity rank 4)*

PN-23's own finding line is scoped exactly right: *"Speculative decoding **with the model's
built-in MTP head** is NOT output-identical to unspeculated decoding **on this engine**."* Every
restatement downstream loses one or both qualifiers:

| location | text | qualifiers lost |
|---|---|---|
| `README.md:77` | "**Speculative decoding is not output-identical, contrary to the standing assumption.**" | drafter **and** engine |
| `manuscript/OUTLINE.md:35` (contribution 4) | "Speculative decoding on this engine is **deterministically non-equivalent** to unspeculated decoding" | drafter |
| `OUTLINE.md:92` (§5.4 heading) | "Speculative decoding is not free" | both (a heading, but it reinforces the reading) |
| `TRACK-A-DECISION.md:163` | "the premise was wrong: speculative decoding is not output-identical here" | drafter |
| PN-23 *Use-as* | "the correction of record for **every prior statement** that speculative decoding 'affects speed only'" | scope implied unbounded |

What was actually measured is **one drafter** (the model's own MTP head) at **two draft depths**, on
**one engine build**, on **one quantization**, at **one context length**, on **164 problems**. The
same engine exposes `--spec-type draft-dflash`, and the one time this study ran it, it ran on a
*different* engine build and produced an equivalence figure PN-29 itself declares unquotable. So
even within this study, "speculative decoding on this engine" has exactly one measured instance.

R12 raises the cost of this drift sharply. It is now planned that the paper will cite a competing
implementation's claim of bit-for-bit identity beside this measurement. Full analysis in §11.

### V12 — The code that computes the paper's intervals and p-values is not in the repository *(severity rank 8)*

`s9_chain.sh:93` invokes `bash "$E12/s9_score.sh"`, and the chain's own `sync_git` never copies it.
**`s9_score.sh` produces every Wilson interval and every McNemar p-value that PN-28 and PN-29
report**, and it is absent from `data/raw/e12/harness-src/`. So are `s11_prebuild_pads.py` (required
by `s11_divdepth.py`) and `s8-scores-reparsed.json`. The mirror's own README states its purpose is
"evidence of method, so a paper claim can be traced to the code that produced it"; for the paper's
two inferential results, it cannot.

I verified the *outputs* independently and they are correct (§4.1), so this is a provenance failure
rather than a numerical one. But under the ACM artifact-badging criteria (R-web-7) a
*Functional* badge requires artifacts that are "documented, consistent, **complete**, exercisable";
an artifact set that omits the scripts computing the paper's statistics is not complete, and
*Reusable* is out of reach. Two further statistics — PN-32's sign test and PN-33's Wilson intervals
— have **no code anywhere**; they were computed ad hoc. Both are arithmetically correct; neither is
reproducible from the repository.

---

## 4. Statistical audit

### 4.1 What is computed correctly

Recomputed and confirmed exactly:

- **Wilson intervals.** PN-28: 154/164 → [89.14, 96.65]; 155/164 → [89.90, 97.09]; 147/164 →
  [84.03, 93.43]; 148/164 → [84.74, 93.91]. All four match the notes to 2 dp. PN-33: 11/12 →
  [64.6, 98.5] exact. (12/12 → [75.8, 100.0]; the note says 75.7 — a 0.1 pt rounding difference,
  cosmetic.) The intervals are genuine Wilson score intervals, not Wald.
- **Exact McNemar.** (b=1, c=2) → p = 1.0; (b=2, c=3) → p = 1.0. Correct.
- **σ separations.** wikitext 3.71 / 8.48; code 8.67 / 11.82 → the stated "3.7–11.8 σ" range is the
  min and max, correctly reported.
- **Ratios.** code/prose 1.755 / 2.303 / 2.623 (PN-14 ✓); task/prose 3.13 / 3.87 / 4.40 and
  task/code 1.785 / 1.681 / 1.678 (PN-21 ✓); KV 0.002955/0.005829 = 0.5069 → "51 %" (PN-15 ✓).
- **Sign test.** P(X ≥ 12 | n = 13, p = 0.5) = 0.001709 → "0.0017" ✓.
- **Spread statistics.** 32.9 % is `(max−min)/median`; 6.7 % is `(12.70−11.90)/11.90`. Both
  reproduce.
- **HellaSwag chi-square.** `(|b−c|−1)²/(b+c)` with `erfc(√(χ²/2))` reproduces 0.4795 and 0.1336.

The arithmetic is sound throughout. The problems are in what is being averaged and what the intervals
assume, not in the formulas.

### 4.2 Clustered observations — applied once, needed four times

PN-32 identifies the defect. It is present, unaddressed, in:

1. **PN-13/PN-14/PN-21/PN-15** — per-token KLD SEs over autocorrelated, heavy-tailed tokens from 32
   contiguous windows of one document. *Fix: chunk-level bootstrap over the 32 chunk means, or a
   stated design effect. No GPU time.*
2. **PN-33** — RULER samples are independently generated haystacks, so these *are* close to
   independent; the Wilson intervals are appropriate. The clustering problem here is different: at
   n=12 the interval is [75.8, 100.0] wide, and the note says so. Good.
3. **PN-19/PN-8/PN-18** — decode "repetitions" that are 1 cold-prefill + 2 prefix-cached runs
   (`s9e-n262k.json` reps 2–3 read `prompt_n: 4, cache_n: 248523`). These are not exchangeable
   replicates and should not be pooled into a median without saying so.
4. **PN-22** — the four HellaSwag runs share the same items, which is the *point* (that is what makes
   McNemar valid), but the reconstructed vectors carry an unverified alignment assumption. See V9.

### 4.3 Nulls reported as absence of evidence vs evidence of absence

The study is unusually careful here and mostly gets it right. The caveats in PN-19 ("This is 'not
separated at this n', NOT proof of equality"), PN-28 ("a null is not proof of equality"), PN-32
("unanswerable at this sample size") and PN-33 ("consistent with published results, not established
here") are exactly the right register, and better than most published work.

The failures are at the **propagation** layer, where the caveats do not travel:

- README §4: "**Speed does not discriminate the ladder.** … The usual case for quantizing down …
  does not hold here: the cheaper arm is **only** less accurate." That is an assertion of equality
  from a null at n = 3–6 with 166 % noise. PN-19's caveat says the powered version needs n ≥ 30 per
  arm.
- Outline §5.5 repeats it: "The cheaper arm is not meaningfully faster, only less accurate."
- Outline §5.2 heading: "Three instruments, one blind spot" and "16× more context, zero
  discrimination". "Zero discrimination" is a ceiling effect on a saturated metric; the correct
  statement is that the instrument had no headroom in which to discriminate.
- PN-22's finding line: "not merely underpowered — it is structurally INSENSITIVE". The paired data
  shows the arms are *not* answering randomly with respect to each other; they are perfectly nested
  (V9). "Structurally insensitive" is a mechanism claim the caveat itself downgrades to "an
  interpretation consistent with the paired result, not a controlled test of it". The finding line
  and the caveat contradict each other.

**Minimum detectable effect should be stated for every null.** None currently is. Concretely, for
PN-28: with an observed discordance rate of ~2 % (base) and no consistent direction, detecting a
true 1-point paired difference at 80 % power requires roughly n ≈ 1,500–2,000 problems — ten times
what HumanEval+ contains. Say that number; it converts the null from a shrug into a result.

### 4.4 The sign test in PN-32

Three separate objections, in increasing order of seriousness.

1. **Arithmetic is right.** 12/13, one-sided, p = 0.001709.
2. **Independence is wrong.** The pairs enumerate as: 131,072 — Q4 (n2→n4, n4→n8), Q5 (×2), Q6_K
   (×2), Q6_K_XL (n2→n8, its n4 cell was invalidated) = 7; 196,608 — Q4 (n2→n8, its n4 invalidated),
   Q5 (×2, one rising), Q6_K (×2), Q6_K_XL (n2→n4, its n8 failed to load) = 6. Within each arm×depth
   chain of three, the two adjacent differences **share the middle observation** and are mechanically
   anti-correlated. Treating them as independent Bernoulli trials inflates n from ~8 to 13. At 8
   independent units all falling, p = 0.0039 — still significant, but the reported figure is
   anticonservative by a factor of ~2.3.
3. **The null is not a live hypothesis.** Acceptance is defined as `draft_n_accepted / draft_n`
   (verified: 913/1237 = 0.7381; 1015/2065 = 0.4915). For any drafter with per-token match
   probability < 1, `E[min(A, n)]/n` is non-increasing in `n` by construction. The sign test is
   therefore testing whether a mechanically monotone quantity is monotone. A reviewer will read
   p = 0.0017 in the finding line and ask what hypothesis it discriminated against. The correct
   framing is descriptive — *the acceptance decay is steep and quant-dependent in magnitude* — with
   the observed decay rates, not a p-value.

Two secondary imprecisions in the same note, both checkable against the artifact:

- **"12 of 13 adjacent draft-depth pairs" — two of the thirteen are not adjacent.**
  `Q4_K_XL@196,608` and `Q6_K_XL@131,072` contribute **n2→n8 spans**, because their n=4 cells were
  gated out. The rule actually applied is "adjacent in the sorted list of *valid* draft depths",
  which is not the same thing and should be stated.
- **"the two invalid ones were caught by the generation gate"** — 24 − 21 = **3**. Two were gated
  (55 and 124 tokens); the third, `Q6_K_XL@196,608 n=8`, is a `load-or-health-failed`, a different
  failure class that the note elsewhere reports separately.

Every *descriptive* statistic in PN-32 reproduces exactly from the artifact — 13 pairs, 12/1,
166.1 % max spread, 33.8 % median, 74.8 % median for n=8 cells, 0.6293 max within-cell acceptance
range, 19/21 cells above 0.10. The **valuable** half of PN-32 is the clustering demonstration, which
is genuinely instructive (±0.02 pooled against ±0.3 between-run). Lead with it.

### 4.5 Sample sizes, at a glance

| result | n | unit | powered for the stated question? |
|---|---|---|---|
| PN-13 KLD | 65,536 tokens (32 chunks) | token (should be chunk) | yes at chunk level, almost certainly |
| PN-21 S5 KLD | 18,432 tokens (9 chunks) | token | intervals 1.9× wider; effect is ~8–11 σ nominal |
| PN-22 HellaSwag | 400 items | item (paired) | **no** — max 4 discordant, min p = 0.125 |
| PN-28 HumanEval+ | 164 problems | problem (paired) | **no** — max 5 discordant, min p = 0.0625 |
| PN-33 S-NIAH | 25 / 25 / 12 | sample | no; but the result is a ceiling, not a null |
| PN-33 MK-NIAH | 12 | sample | **no artifact** |
| PN-19 speed | 3–6 | repetition (mixed depths) | **no** — needs n ≥ 30 |
| PN-32 draft depth | 3 reps × 21 cells | generation | **no** — needs ~30 reps |
| PN-23/26 equivalence | 164 problems | problem | **yes** — 131/164 is far from 164/164 |
| PN-18 ctxcp | 1 A/B pair | — | no; correctly labelled directional |

The single strongest thing this paper can say about its own statistics is: **every task instrument
we ran was underpowered by design, and we can show exactly what it would have cost to power it.**
That is a contribution. Make it explicit with numbers, in a table, in §7.

### 4.6 Estimator drift: the same word means three different things in three files

An audit of the mirrored harness source found that four quantities the paper reports under a single
name are computed by more than one rule. None of these changes a conclusion; every one of them will
cost the paper credibility if a referee recomputes.

**"Median" — three implementations.**

| file | code | behaviour |
|---|---|---|
| `s9d_depthsweep.py:151` | `statistics.median(ds)` | correct interpolated median ✓ |
| `s8_spec.py:101`, `s9_final.py:141`, `s11_divdepth.py:261`, `s12_ruler.py:173` | `sorted(x)[len(x)//2]` | **upper of the two middle values at even n** — an upward-biased pseudo-median, labelled `*_median` in the artifacts |
| `tsweep_v2.py:479–493` | `median_of_3`, but **only when the top two ratios are within 10 %**; otherwise rep 1 | the conditional estimator PN-20 documents |

The pseudo-median affects `decode_tok_s_median` over 164 HumanEval+ generations (PN-24, PN-29),
`first_divergence_char_median` (PN-23's 715/730, PN-29's 730) and `prompt_n_median` (PN-33). The
bias is small at n=164 and material at n=3. Replace with `statistics.median` or rename the fields.

**"Spread" — two definitions.** PN-19's 32.9 % is `(max−min)/median`; `s9d_depthsweep.py:153`
computes `(max−min)/min`. On the same Q4_K_XL data these give 32.9 % and 35.1 %. Worse,
`s9d_depthsweep.py:33` cites PN-19's 32.9 % as the justification for its 3-repetition design —
comparing a `/median` figure against a harness that reports `/min` figures. Define it once, in the
table, and recompute both notes on the same denominator.

**"McNemar" — two tests.** `s7_paired.py:48–52` uses Edwards' continuity-corrected χ² evaluated
against χ²₁ (`p = erfc(√(χ²/2))` — correct closed form, and it avoids a scipy dependency);
`s9_score.sh` uses the exact binomial. **PN-22's "all p ≥ 0.13" is true only under the χ² variant:
the exact two-sided p for its (b=0, c=4) pair is 0.1250 < 0.13.** The claim is therefore
test-dependent, and the paper never names the test. At b+c ≤ 4 the exact form is mandatory
(conventional threshold b+c < 25).

**Multiple comparisons.** `s7_paired.py:42` runs all 6 pairs of 4 arms with no correction of any
kind and a hard-coded `p < 0.05` verdict string. Harmless here (min p = 0.125), but the family must
be declared: *6 pairwise comparisons, uncorrected*.

**Two structural gaps that make Wave 1 unauditable.** `tsweep_v2.py` never records `predicted_n` —
only the *requested* `n_predict = 192`. The success condition is
`rec["ok"] = (not truncated) and bool(content or predicted_per_second)`. So **the PN-30
degenerate-generation failure mode cannot be ruled out post hoc for any Wave-1 cell**, and PN-6,
PN-7, PN-8, PN-18, PN-19 and the Track A decision all rest on those cells. The build-stream's
argument that Wave 1 is safe (it used `/completion` + a continuation cue) is mechanistically sound
but is reasoning, not evidence, and the evidence was never captured. Separately, the 128-token
generation floor exists only in `s9d_depthsweep.py` and `s11_divdepth.py`; **`s8_spec.py` and
`s9_final.py` — the two files whose at-depth output PN-30 withdrew — still compute `prefill_frac`
and never compare it, and set `ok: True` unconditionally.** Anyone re-running them reproduces the
void.

**Where the ± on KLD comes from, confirmed numerically.** Back-computing the implied dispersion from
`mean ± err` at n = 65,536 gives a coefficient of variation of ≈ 9.7–11.0 across cells; computed
against 32 chunks instead it gives ≈ 0.21–0.24. A distribution with median 7×10⁻⁶, mean 5.8×10⁻³
and max 1.66 has a CV of order 10, not 0.2. **The ± is therefore σ/√N with N = tokens** — a
per-token standard error of the mean, exactly as §4.2 assumes. The parsing itself is correct
(`ssa_reparse.py:19`, `mean_kld: Mean\s+KLD:\s*NUM\s*±\s*NUM`), with one latent hazard: it uses
`re.search`, i.e. first-match, which is safe only because each invocation emits one statistics
block.

**One RULER scoping overstatement.** `s12_ruler.py:103–106` reproduces RULER's `string_match_all`
**exactly** — same case folding, same substring containment, same `round(..., 2)` at the same point;
and `prompt = row["input"] + row.get("answer_prefix", "")` matches RULER's `call_api.py`. But
RULER's official `evaluate.py` applies `postprocess_pred` (strip, map control characters to
newlines) before scoring, and the local pipeline does not. For substring matching on numeric needles
this cannot flip a result, so the numbers are safe — but `METHOD-REFERENCES.md` R8's "its metric —
reproduced verbatim and unit-checked against the reference implementation" over-scopes: the *metric*
is verbatim, the *pipeline* is not, and **the claimed five-case unit check has no artifact** (no test
file, no assertion, no recorded output).

---

## 5. Consistency audit

### 5.1 Withdrawn claims that reappear as live

Checked exhaustively by grep against `README.md`, `CLAUDE.md`, `manuscript/OUTLINE.md`,
`docs/paper/*.md`. Results in **V7** above. The four that matter most:

- `README.md` prints `--spec-draft-n-max 4` and "16.8 tok/s at 94 % window depth" as **the**
  deployment answer. Both were withdrawn on 2026-09-01 (Amendment 2 / PN-30).
- `README.md` finding #5 asserts PN-23's refuted mechanism *and* states the settling control "has
  not been run". PN-26 ran it on 2026-08-31.
- **PN-29, a live note the outline cites in §5.4, uses the withdrawn 16.81 tok/s as its comparator.**
  PN-29 predates PN-30 by 3.5 hours and was never superseded. Under the append-only protocol this is
  legal and dangerous: the correct fix is a new note (PN-35) restating the DFlash2-vs-MTP at-depth
  comparison against S9e's sound numbers (8.34 @163,840 vs 12.88 @262,144).
- `TRACK-A-DECISION.md` Amendment 1 §2 still prints the full withdrawn table with no inline banner.
  The outline plans to keep it as a worked example (§8) — good — but it must be visually marked at
  the point of the table, not only three sections later.

### 5.2 PN-23's mechanism vs PN-26

PN-26's caveat states: *"That note argued the partial overlap … pointed at floating-point
nondeterminism from the changed decode batch shape. It does not: both arms are individually
deterministic, so nondeterminism is excluded."*

**This does not follow.** The batch-shape mechanism is: speculation changes the decode batch shape →
FP reductions occur in a different order → logits differ in the last bits → argmax occasionally
flips. Every step of that is deterministic. Re-running the same speculative configuration reproduces
the same batch shapes and therefore the same output — exactly what S9a observed. PN-26 has excluded
**run-to-run nondeterminism**, which was never the interesting hypothesis, and has not touched the
numerical account.

PN-26's own replacement explanation ("different draft lengths place verification boundaries at
different token positions, so each diverges from no-spec deterministically but at a different set of
problems") is, in fact, *the same mechanism* described without the floating-point step.

**Fix:** PN-26 keeps its result (determinism, byte-exact self-reproduction) and its upgraded claim
("deterministically non-equivalent"). It must **withdraw the sentence claiming the numerical account
is excluded**, and restate the open question as: *whether the divergence originates in the
verification rule or in batch-shape-dependent numerics remains open, and both are deterministic; only
engine-level logit instrumentation distinguishes them.* This is a small edit that removes a logical
error a referee will certainly find.

### 5.3 The 3.69× attribution error

PN-28: "These are the SAME two arms that differ by **3.69× in mean KL divergence on code**
(0.021529 vs the reference) and whose top-1 agreement on task prompts differs by **2.15 points**."
PN-34 and L-15 repeat it; the outline inherits it.

The S6 arms are **UD-Q4_K_XL and UD-Q6_K_XL**. UD-Q6_K_XL is the divergence *reference*: its own KLD
is 0 by construction. The ratio 3.69 is `0.021529 / 0.005829` — Q4_K_XL over **Q6_K**, a third arm
(the `×Q6_K` column of the Track A table). Likewise 2.15 points is `98.045 − 95.894` — Q6_K minus
Q4_K_XL on task-prompt top-1. Against the actual reference the figures are: code KLD **0.021529**,
task-prompt KLD **0.036129**, top-1 gap **100 − 95.894 = 4.106 points**.

Note the direction: **the error understates the study's own case.** Fixing it makes PN-28's contrast
stronger. Fix it anyway — a reviewer who catches an arithmetic misattribution in a headline sentence
stops trusting the rest.

### 5.4 Artifacts cited but absent, and artifacts that contradict their notes

| cited in | artifact | status |
|---|---|---|
| PN-10 | `quarantine/*.race-025630` (Q4_K_XL, Q6_K, Q6_K_XL) | in `LISTING.txt`, **not in the repo** |
| PN-5 (root cause) | `quarantine/pad_*.txt.bisection-bug` | in `LISTING.txt`, **not in the repo** |
| L-15, `CLAUDE.md` §7 | `s8/s8-scores-reparsed.json` (the repaired pass@1 with Wilson intervals) | **not in the repo** |
| PN-13/14/15/16/21 | `/srv/bench/e12/corpus.txt` | **not in the repo**, not in any manifest |
| PN-33 | MK-NIAH cells and predictions | **do not exist** (V1) |
| PN-25 | `s8-humaneval.json.equivalence.dflash4` | present, and still records `lossless: false` for a server that never loaded — the exact confusion PN-25 forbids |
| PN-32 | `s9e-n262k.json.summary.best_n_per_arm_per_depth` | present, and still declares `"n": 4` **best**, which PN-32 says is unanswerable |
| PN-32 | `s9d-depthsweep.json.summary.best_n_per_arm_per_depth` | declares n=8 best in 4 of 8 cells — contradicting Track A's n=2 pin |
| PN-17, PN-15 | `ssa-results-parsed.json` | contains a wrong value (§5.5) |
| L-18 | "two duplicate c8192 cells … deduped with a note" | the duplicates are **still present** in `s12-ruler.json` (4 niah c8192 cells) |
| — | `s10-ctxdepth.json` | two byte-identical cells, same label, same serverlog path |

The `best_*` fields are the PN-20 defect class recurring in three artifacts *after* PN-20 was
written. An aggregator that "should refuse to emit a row whose statistic it cannot name" is still
emitting rankings the corresponding notes disown.

### 5.5 The SSA label collision

Two cells in `ssa-results-parsed.json` carry the label `ssa-Q6_K_XL-code-base` — one at `-ctk q4_0`
(1,516.4 s, `--kl-divergence-base /ssa/base-code.kld`) and one at `-ctk f16` (1,371.7 s,
`/ssa/base-code-f16.kld`). Both record the **same** serverlog path,
`/srv/bench/server-timings/ssa-Q6_K_XL-code-base.serverlog`. The f16 run ran last and overwrote it.
`ssa_reparse.py` reads logs by label, so the q4_0 cell's `metrics_reparsed.ppl` is **1.1791** — the
f16 number — against its own original `metrics.ppl` of **1.1809**.

Consequences:
- PN-15's "+0.15 % PPL" (1.1791 → 1.1809) is correct *only if you read the pre-reparse field*. In
  the artifact PN-17 nominates as the recovered source of truth, the delta reads as **zero**.
- PN-17's headline — "Every number was recoverable after the fact ONLY because the log-preservation
  rule had written full stdout to disk before each container was removed" — has a counter-example
  inside the very artifact it cites.

This is not fatal (the KLD numbers are unaffected; each `-kld` cell has a unique label), but it must
be fixed in the artifact and reported. Reported honestly it *strengthens* the reproducibility
appendix: preservation is necessary but insufficient without namespace uniqueness.

### 5.6 Stale navigation documents

`AGENTS.md` instructs every reader to "read the STATUS block and the final ledger entry … Together
they tell you exactly where the last agent stopped." The STATUS block reads
`status: campaign-running`, `last: { ledger: L-13 }`, and a `next_action` describing two detached S9
chains as if in flight. The final ledger entry is L-18 and says measurement is closed. `CLAUDE.md`
cites PN-1…PN-25, DEC-1…DEC-11, L-1…L-13, and its programme table has no S10/S11/S12 rows. The plan
has **no S12 design section at all** — S12 exists only in L-18 and `METHOD-REFERENCES.md`, which is
awkward given it produced two of the paper's four headline contributions.

---

## 6. Selective reporting and researcher degrees of freedom

These are the questions a hostile reviewer asks second, after the numbers.

### 6.1 S11 produced 12 measured cells and no paper note

`s11-divdepth.json` measured 4 arms × 3 corpus excerpts at n_ctx 8,192, greedy, no-spec, one fixed
`-ts 56,44`, with the stated metric "index of first differing character vs the reference arm".
Result:

| arm | first-divergence char, per excerpt | median |
|---|---|---|
| Q6_K | 2, 5, 71 | **5** |
| Q5_K_XL | 2, 62, 126 | **62** |
| Q4_K_XL | 2, 10, 14 | **10** |

The metric is **non-monotone in the ladder**: the least-divergent arm by KLD (Q6_K) separates from
the reference *earliest*. The same experiment run twice, hours apart, on the same configuration gave
medians of 131 / 77 / 97 in the first pass (1 valid excerpt/arm) and 5 / 62 / 10 in the second (3
valid). `self_consistency` in the artifact is **`null`** — the design declared this control
mandatory ("Not identical → the experiment is void and stops") and it was never recorded. The
65,536 and 196,608 depths never ran.

The instrument was abandoned *after* seeing the ordering. L-17's only record is a half-sentence:
"S11's instrument was measured and rejected (see below)" — and "below" (L-18) does not explain it.
There is no PN, no threats-to-validity mention, and no appearance in the outline.

Two things follow. First, this is a **protocol violation by the project's own rules** and a reviewer
should raise it (the protocol says so explicitly). Second, and more importantly: **the S11 data is
informative and free.** At only 8,192 tokens of context, greedy and unspeculated, *every* arm
diverges from the reference within 2–126 characters, and 0 of 9 completions were identical. Set
beside PN-28 — the two extreme arms agreeing on 161 of 164 HumanEval+ problems — that is a clean
demonstration of the paper's own thesis in a fourth dimension: *the text changes essentially
immediately; the pass/fail label does not.* Report it, with the instrument's instability stated.

### 6.2 `variable_tracking` was excluded post hoc, and it is the only long-context task that separated the arms

From `s12-ruler.json.variable_tracking_excluded_cells` and `s12_chain.log`:

| budget | Q6_K_XL (reference) | Q4_K_XL | apparent recovery |
|---|---|---|---|
| 30 tokens (RULER default) | 16.8 | 18.4 | 109 % |
| 120 tokens (raised) | 27.2 | 36.8 | **135 %** |

The exclusion rationale — the instruct-tuned model writes a markdown trace and truncates against a
fixed budget, so the score measures verbosity — is technically sound, and the note that both attempts
put the reference *below* the cheaper arm is exactly the right diagnostic. Two problems remain.

- **The decision was made after seeing the direction**, and it removed the only long-context task
  with a material between-arm gap. Also removed: `variable_tracking` at 32,768 and 131,072, which
  were generated (`s12_gen.log`) and never run.
- **The direction is the same as HellaSwag's** (V9): the more-quantized arm scores higher. That is
  now twice, on two unrelated instruments. The paper attributes HellaSwag's version to "nominal"
  noise and RULER's version to a scoring artifact. A reviewer will ask whether there is a common
  cause — e.g. quantization increasing output verbosity or reducing early-EOS — and the study has the
  data to check it cheaply (`n_empty`, `predicted_n`, character counts are all recorded).

Report the excluded numbers in the paper, in the table, greyed. An exclusion the reader cannot see is
an exclusion the reader will assume was convenient.

### 6.3 The generative anchor ran under a sampling preset the project itself flagged as suspect

`s9-s6.json` records `presence_penalty: 1.5` (DEC-2 official non-thinking). DEC-13, in the same
repository, says of the cancelled presence-penalty probe: *"the official preset's
`presence_penalty 1.5` penalises every token already emitted, and code repeats `self`, `return` and
indentation constantly, so a measurable harm would be the paper's own thesis appearing in a second
dimension."*

PN-28 — the study's **only** generative anchor — therefore runs both arms under a setting the study
believes may harm code generation and then declined to test. Both arms land at ~94 % base pass@1, so
this is a *ceiling*, not a floor, and the saturation argument holds. But the paper must state that
its generative null was measured under an untested preset it had itself identified as a risk. It
should also note the asymmetry with §6.2: `variable_tracking` was excluded for being score-compressed
by an output-budget artifact, while the generative anchor's own possible compression by a sampling
artifact was not examined.

### 6.4 Single-attempt failures under a rule requiring two

`CLAUDE.md` hard rule 4: *"Bracket and re-test every ceiling. A ceiling needs a failed rung above it,
attempted twice — layer-split VRAM carries ±100–200 MiB of noise and single failures lie."*

Single-attempt failures currently carrying headline claims:

| failure | attempts | carries |
|---|---|---|
| Q5_K_XL @262,144, default split | **1** | PN-6's headline; README finding #3 |
| Q6_K @262,144, `-ts 54,46` | **1** | README's "`54,46` fails where `58,42` loads" non-monotonicity headline |
| DFlash2 @262,144 and @212,992 | **1** each | PN-29 (correctly disclosed in its caveat) |
| S9e Q6_K @262,144 n=8 | **1** | PN-32 (correctly disclosed) |

PN-29 and PN-32 disclose; PN-6 and the README do not. Two of the four are the ones the paper leans
on hardest. Note also that both DFlash2 failures and the S9e n=8 failure are recorded as
`failure_mode: "load-or-health-failed"` with `error: ""`, and the causal classification
(`compute-buffer-oom`, "the draft context does not fit") is derived from serverlogs that are
gitignored and absent from this repository. From the evidence tree alone, those attributions are not
checkable.

### 6.5 Implausible at-depth throughput passes the repaired gate

After the PN-30 repair, S9d cells still produce readings that cannot be right:

| cell | reps (tok/s) | context filled |
|---|---|---|
| Q6_K @196,608 n=8 | 14.893 · **39.637** · 33.985 | 186,270 tokens |
| Q5_K_XL @131,072 n=8 | 20.176 · 24.701 · **42.375** | 123,670 tokens |
| Q6_K_XL @131,072 n=8 | 17.695 · 14.952 · **38.137** | 123,670 tokens |
| Q5_K_XL @196,608 n=8 | 22.229 · **37.506** · 26.199 | 186,270 tokens |

For scale, PN-24's *sound* depth-0 medians over 164 generations are MTP n=2 = 37.44 and n=4 = 47.03
tok/s at ctx 32,768. A 39.6 tok/s reading at 186,270 filled tokens is depth-0-class throughput at
93 % window depth, which contradicts the study's own central systems observation that decode at depth
is 3–5× slower. The pattern — always one rep of three, always at n=8, always with an anomalously
high value — is the PN-30 signature in milder form: the gate now asserts that ≥128 tokens were
generated, but not that what was generated was non-degenerate (e.g. the model echoing the pad, which
would drive both acceptance and throughput up).

The study treats this as "noise" (166 % spread) rather than as a content-dependent measurement
artifact. Given that the same artifact shows acceptance tracking the generated text rather than the
configuration (V5), the more likely reading is that these are **different measurements, not noisy
copies of the same one**. PN-30's lesson needs one more clause: *assert that the generation is what
you asked for, and record enough of it to check.*

---

## 7. Is the central thesis (PN-34) supported?

**No — not by the cited evidence, and only partially by the strongest possible reading of it.**

PN-34 asserts: *"A benchmark's sensitivity to quantization damage is gated by its task difficulty,
not by its context length or its modality."* The argument has two limbs.

**Limb 1 — three instruments were blind.** This is supported, with the corrections above.

- PN-22 (HellaSwag, n=400, 4 arms): spread 1.0 pt, ≤4 discordant items per pair. Blind ✓ — though
  "blind" is the wrong word for a perfectly nested outcome structure (V9).
- PN-28 (HumanEval+, n=164, paired, 2 arms): 3 and 5 discordant of 164. Blind ✓ — and the test could
  not have detected anything (V8).
- PN-33 (S-NIAH, 3 lengths, 2 arms): 100.0 everywhere. Blind ✓ — and unambiguously a ceiling.

**Limb 2 — the cause is headroom, and difficulty (not depth) reveals it.** This is **unsupported**.

The only evidence offered for limb 2 is the S-NIAH/MK-NIAH contrast, and MK-NIAH does not exist in
the evidence tree (V1). Remove it and the argument becomes: *we ran a saturated retrieval task at
three lengths and it stayed saturated.* That shows depth alone did not discriminate. It says nothing
about whether difficulty would have.

Three further problems even if MK-NIAH is recovered:

1. **A single discordant sample cannot carry a mechanism claim.** 12/12 vs 11/12, Wilson [75.8,
   100.0] and [64.6, 98.5] — near-total overlap. PN-33 says so; PN-34 then builds the paper's
   methodological through-line on it and calls it "a direction, not a magnitude". A direction from
   n=1 discordance is not a direction.
2. **"Headroom" is not measured; it is inferred.** The study has three benchmarks near ceiling and
   one instrument without a ceiling. That is consistent with the headroom hypothesis and also with
   at least two others: that argmax-style scoring is robust to distributional shift regardless of
   headroom (PN-22's own stated mechanism, which is about *modality* and directly contradicts
   PN-34's "not modality"); and that the effect size is simply small relative to task noise. The
   study has an internal contradiction here: PN-22 attributes blindness to *modality* ("multiple-
   choice scoring depends only on an argmax over a handful of candidates"), PN-34 attributes it to
   *headroom and not modality*. Both are in the paper. They cannot both be the finding.
3. **The counter-example is inside the study and excluded.** `variable_tracking` is the harder RULER
   task, it was run at the same depth, it produced a 9.6-point gap — **in the wrong direction** — and
   it was excluded (§6.2). "Harder tasks reveal quantization damage" is not what that datum says.
   PN-34's own caveat anticipates this ("It does not follow that harder tasks always reveal
   quantization damage — only that saturated ones cannot"), which is a much weaker and defensible
   claim. Make that the claim.

**Recommended replacement thesis**, which the data does support:

> Three task benchmarks spanning multiple-choice, generative coding and long-context retrieval fail
> to separate quantizations whose token-level distributions are separated at 8–12 σ. In every case
> the instrument is at or near its ceiling for both arms, and in two of the three the sample size
> makes a significant result arithmetically impossible. A divergence measurement has no ceiling and
> draws its power from token count rather than problem count, which is why it ranks the ladder in a
> fraction of the wall-clock. Whether raising task difficulty restores sensitivity is a natural
> hypothesis that we were not able to test at adequate power.

That version costs the paper its title and keeps its integrity. It is also, in my judgement, a
stronger paper: "three standard instruments cannot see a real effect, and here is exactly why and
what it would have cost to see it" is a more useful contribution than an under-evidenced law about
difficulty.

---

## 8. The reproducibility appendix (PN-5, 17, 20, 25, 27, 30, 31) — strength or liability?

**Strength, if reframed; liability as currently outlined.**

The outline (§9) frames it as "Offered as method, not confession. Each is a trap another group would
fall into." That instinct is right, and the material is genuinely good — PN-30 in particular (a
throughput measurement that timed 17 tokens, caught by a standing red-flag check, with the working
construction already on disk) is the kind of thing the field under-reports and would benefit from.
PN-27 (a safety predicate matching the tooling built to supervise it) is publishable on its own.

But at seven entries and its own numbered section, it currently reads as **a defect register with a
paper attached**, and three specific things will read badly to a referee:

1. **Two of the seven affected published claims and one is still uncorrected.** PN-30 withdrew a
   Track A configuration change; PN-25 voided an entire arm. That is not "a trap another group would
   fall into" — that is this study's own results being wrong for a day. Say so plainly. Owning it is
   fine; framing it as pure pedagogy is not.
2. **The register is incomplete.** Three defects of the same family are present and unregistered:
   the SSA label collision (§5.5), the PN-19 depth pooling (V2), and the `wave1-summary.md` errors
   PN-20 did not catch (V6). A defect register that a reviewer can extend by reading the artifacts
   for two hours undercuts the claim that the register is the method.
3. **PN-31 is already correctly demoted** by DEC-15 to a footnote, and the outline honours that.
   Keep it there. It is a fact about a tool's memory footprint, and its one generalisable clause —
   that published quantization tables are all measured near 2K because the tooling cannot go
   deeper — is genuinely useful and belongs in §2 or §3, not §9.

**Recommendation.** Cut §9 from seven entries to **three**, each with a one-line generalisable rule,
and move the rest into a table in an appendix:

- **PN-30** — *assert that the model produced what you asked for, not merely that the input arrived.*
  (The 17-token measurement; the strongest.)
- **PN-25** — *a results table must distinguish "measured badly" from "never ran".*
  (The 0.000 pass@1; still live in the artifact, which is itself the point.)
- **PN-17 + §5.5** — *preserve raw output, and make its namespace unique.* (The `±` parser, plus the
  label collision that shows preservation alone is insufficient — the pairing is more instructive
  than either alone.)

Then add one sentence of self-audit: *"A reviewer re-deriving our numbers from the artifacts found
three further instances of the same families; they are listed in Appendix B."* That converts the
section from confession into a demonstrated methodology, which is what the outline wants it to be.

---

## 9. Recommended claim wording changes (before → after)

**W1 — the working title.**
- **Before:** "The Benchmarks Cannot See It: quantization damage to a coding model is
  domain-dependent, and the instruments used to certify quantizations are saturated"
- **After:** "The Benchmarks Cannot See It: quantization damage to a coding model is
  domain-dependent, and three standard instruments cannot resolve it at the sample sizes they have"
- **Why:** "saturated" is the paper's hypothesis about *why*, and it is exactly the part MK-NIAH was
  supposed to establish. The revised title claims only what PN-22/PN-28/PN-33 support.

**W2 — PN-34's finding line.**
- **Before:** "A benchmark's sensitivity to quantization damage is gated by its task difficulty, not
  by its context length or its modality."
- **After:** "Across three instruments — multiple-choice, generative coding and long-context
  retrieval — no task benchmark we ran separated arms that divergence separates at 8–12 σ. In every
  case both arms scored at or near the instrument's ceiling, and in two of the three the observed
  discordance made a significant result arithmetically impossible. Saturation is our hypothesis for
  the common cause; we were not able to test it, because the harder-task contrast that would have
  tested it was not measured."
- **Why:** V1, and the PN-22/PN-34 modality contradiction (§7).

**W3 — PN-33's MK-NIAH sentence.** Delete, or replace with the S-NIAH result alone plus: "A
multi-key variant at the same depth was designed as the difficulty contrast and was not run."

**W4 — PN-19's finding line.**
- **Before:** "…medians 12.70, 12.61 and 11.90 tok/s, spanning 6.7 % — while repetition-to-repetition
  noise within a single arm at a fixed configuration reaches 32.9 %, roughly five times the
  between-arm difference"
- **After:** "…at 262,144 tokens filled to ≥94 %, UD-Q5_K_XL 12.70 (median of 3), UD-Q6_K 11.90
  (median of 3) and UD-Q4_K_XL 12.10 (**n = 1**) — a 6.7 % span. Repetition-to-repetition decode
  spread at a fixed configuration on this host is 12–166 % (median 34 %, n = 21 cells, S9d), so this
  design cannot separate the arms; a powered comparison would need roughly n ≥ 30 per arm."
- **Why:** V2. The corrected version is *stronger*, because 166 % noise makes the null far more
  robust than 32.9 % did.

**W5 — PN-9's finding line.**
- **Before:** "MTP draft acceptance at near-full context depth varies strongly across quantization
  levels of the same model…"
- **After:** "MTP draft acceptance at depth is dominated by the content being generated rather than
  by the configuration: at a fixed quantization, context and `-ts` ratio, three repetitions of the
  same cell span 0.592–0.911 (UD-Q6_K), 0.516–0.734 (UD-Q5_K_XL) and 0.592–0.791 (UD-Q4_K_XL) —
  a range as wide as any between-quant difference we observed — and acceptance is identical across
  `-ts` ratios within a repetition index. Acceptance must therefore be reported with its
  repetition count, and single-cell acceptance values cannot be compared across configurations."
- **Why:** V5. This turns a dead claim into a live and more interesting one.

**W6 — PN-8's finding line.**
- **Before:** "…the least balanced ratio that still loads (`54,46`, 742 MiB imbalance) is the fastest
  at 10.82 tok/s — a 27 % decode difference across ratios that all load the same window."
- **After:** "…the most balanced ratio tested (`58,42`, 28 MiB imbalance) is anomalously slow at
  8.50 tok/s, while the other four loading ratios — spanning 166 to 1,750 MiB of imbalance — are
  flat at 10.44–10.82 tok/s (a 3.6 % span, inside this host's repetition noise). Minimising VRAM
  imbalance is therefore not a throughput objective, but neither is maximising it; on n = 1 per
  ratio we can say only that the single most balanced ratio was slowest."
- **Why:** V6. `60,40` and `62,38` are less balanced than `54,46` and both load.

**W7 — PN-6's headline and README finding #3.**
- **Before:** "a ceiling published without its tensor-split is a property of the split, not of the
  quant" / "The usable context ceiling belongs to the GPU split, not the quantization."
- **After:** "For the two arms whose weights bring the heavier card within ~700 MiB of its wall
  (UD-Q5_K_XL, UD-Q6_K), the full 262,144-token window is reachable only after tensor-split
  rebalancing and fails at the engine default. UD-Q4_K_XL reaches the same window at the default
  split, and UD-Q6_K_XL does not reach it at any ratio. The split is the binding constraint where
  the model is close to the per-card limit, and irrelevant where it is not."
- **Why:** V6 / §6.3 — `262144:default:1:base` for Q4_K_XL is `ok: true` at 12.14 tok/s.

**W8 — PN-26's mechanism sentence.**
- **Before:** "It does not: both arms are individually deterministic, so nondeterminism is excluded."
- **After:** "This excludes *run-to-run* nondeterminism only. A batch-shape-dependent difference in
  floating-point reduction order is itself deterministic and reproduces exactly on repeat, so it
  remains open alongside a verification-rule difference. What the control establishes is that the
  divergence is a stable property of the decode path, not a stochastic one; distinguishing the two
  remaining accounts requires engine-level logit instrumentation."
- **Why:** §5.2.

**W9 — PN-28's contrast sentence.**
- **Before:** "These are the SAME two arms that differ by 3.69× in mean KL divergence on code
  (0.021529 vs the reference) and whose top-1 agreement on task prompts differs by 2.15 points"
- **After:** "UD-Q4_K_XL's divergence from this exact reference arm is 0.021529 ± 0.000834 on code
  and 0.036129 ± 0.001534 on the task prompts themselves, where its top-1 agreement with the
  reference is 95.894 % — roughly one token in 24 differs under greedy decoding."
- **Why:** §5.3. The 3.69× and 2.15 pt figures describe Q4_K_XL vs Q6_K, a different pair.

**W10 — PN-28's null.**
- **Before:** "giving exact McNemar p = 1.0 on both metrics and no distinguishable difference"
- **After:** "The arms disagree on 3 of 164 problems (1 vs 2) on base tests and 5 of 164 (2 vs 3) on
  base+extra. With 3 discordant pairs the smallest two-sided exact p attainable is 0.25, and with 5
  it is 0.0625: **no assignment of these discordances could have produced a significant result**.
  The informative quantity is the discordance rate of 2–3 %, from which detecting a one-point paired
  difference at 80 % power would require of order 10× the problems HumanEval+ contains."
- **Why:** V8.

**W11 — PN-22's finding line.**
- **Before:** "is not merely underpowered for ranking quantizations — it is structurally INSENSITIVE"
- **After:** "does not separate the four arms, and its paired structure is anomalous rather than
  noisy: the four outcome vectors are perfectly nested (Q4_K_XL ⊇ Q5_K_XL = Q6_K_XL ⊇ Q6_K), with
  no pair disagreeing in both directions on any of 400 items. Multiple-choice scoring reduces to an
  argmax over a handful of candidate continuations, which is one candidate explanation; a systematic
  interaction between quantization and length-normalised scoring is another. We report the paired
  counts and do not adjudicate between them."
- **Why:** V9, and the PN-22/PN-34 mechanism contradiction.

**W12 — PN-14/PN-21's corpus.** Add to both: "The code corpus is a path-ordered concatenation of a
single django worktree (`.py/.rst/.txt/.md/.toml`), assembled without deduplication or shuffling;
its manifest is published as Appendix C. The reference arm's perplexity on it is 1.1809
(0.240 bits/token) against 2.534 bits/token on WikiText-2, and the per-token KLD distribution is
strongly right-skewed (median 1.7×10⁻⁵ against a mean of 2.15×10⁻²). The domain effect we report is
therefore concentrated in a minority of high-entropy tokens; we report the full distribution
alongside the mean."

**W13 — the affordability claim (outline §6, PN-34).**
- **Before:** "twenty minutes of KL divergence per arm separates these quantizations at 3.7–11.8 σ
  where roughly twenty hours of task benchmarking across three modalities separates them nowhere"
- **After:** "2.3 GPU-hours of divergence measurement — ~35 minutes per arm including the shared
  reference-logits pass — separates these quantizations at 3.7–11.8 σ, where 5.2 GPU-hours across
  three task modalities separates them nowhere."
- **Why:** V10. Both halves are recomputed from the artifacts' own timestamps.

**W14 — README §4 and outline §5.5.**
- **Before:** "Speed does not discriminate the ladder… the cheaper arm is only less accurate."
- **After:** "We could not separate the arms on decode throughput at this sample size, and the
  design was never powered to. The common expectation that a smaller quantization buys meaningful
  speed is not supported by what we measured, and would need n ≥ 30 repetitions per arm to test."

**W15 — the speculative-decoding contribution bullet (outline §35, README finding 5).**
- **Before:** "Speculative decoding is not output-identical, contrary to the standing assumption." /
  "Speculative decoding on this engine is deterministically non-equivalent to unspeculated decoding."
- **After:** "Speculation with this engine's built-in MTP head is **reproducibly non-equivalent** to
  unspeculated decoding at the level of emitted text: on 164 HumanEval+ problems at temperature 0
  with a fixed seed, each configuration reproduces itself byte-exactly across repeats while the two
  differ on the same 33 problems every time. The verification rule is lossless in exact arithmetic;
  the implementation is not. **Losslessness is therefore a property to verify per stack, not to
  inherit from the algorithm.**"
- **Why:** V11 / §11.1. Names the drafter, names the level at which non-equivalence was measured,
  concedes the rule, and keeps the generalisable proposition.

**W16 — PN-26's open question.**
- **Before:** "What remains genuinely open is WHERE in the verification the difference arises, which
  needs engine-level instrumentation rather than output comparison."
- **After:** "What remains open is whether the difference originates in the verification rule or in
  batch-shape-dependent floating-point reduction order. **Both are deterministic, so the determinism
  control does not distinguish them.** Two tests would: the distribution of first-divergence token
  positions relative to the draft-chunk boundary, which is a re-analysis of data already on disk and
  costs nothing; and a no-spec-vs-no-spec comparison at two different `-b`/`-ub` settings, ~40 min of
  GPU. We report the first below."
- **Why:** §11.2. The current sentence declines a question the study can answer for free.

**W17 — the R12 related-work sentence.** Delete R12's opening gloss ("a clean, citable instance of
the assumption our measurements refute") and keep only its closing one. Use the framing in §11.3,
which concedes the rule, names the implementations on both sides, and states the falsifier not run.

---

## 10. What must be measured or retracted before submission

### Retract or restate (no GPU time)

1. **PN-34, in full**, and **PN-33's MK-NIAH sentence** — unless the artifact is produced (V1).
2. **PN-9's finding line** — replace with the content-dominance result (W5).
3. **PN-8's imbalance claim** — the "least balanced that still loads" statement is false (W6).
4. **PN-19's 32.9 % noise figure**, everywhere it appears, including PN-18, PN-24, PN-8 and
   Amendment 1 (W4).
5. **PN-6's generalisation** and README finding #3 — restate per-quant (W7).
6. **PN-26's exclusion of the numerical account** (W8).
7. **PN-28/PN-34's "3.69×" and "2.15 points"** — wrong pair (W9).
8. **The "20 h vs 20 min" contrast** (W13).
9. **README's Track A config line and 16.8 tok/s**, and its refuted PN-23 mechanism paragraph (V7).
10. **PN-29's use of 16.81 tok/s** — supersede with a new note against S9e's 12.88 (V7).

### Compute from data already on disk (no GPU time)

11. **Chunk-level intervals for every KLD figure.** Bootstrap over the 32 chunk means (9 for S5), or
    report a design effect. This is the single highest-value change in the list (V4).
12. **The full KLD distribution**, not only the mean — the artifact already carries median, p90,
    p95, p99 and max for every cell. Publishing them pre-empts the heavy-tail objection and makes
    PN-16's metric-pair argument sharper.
13. **A corpus manifest** for the code domain: file list, bytes, tokens, pass count, duplicate
    fraction, licence (V3 / W12).
14. **Minimum detectable effect for every null** — PN-19, PN-22, PN-28, PN-32, PN-33 (§4.3).
15. **Per-instrument GPU-hour accounting** — the outline promises it; the numbers are in §3/V10.
16. **The S11 result written up as a paper note**, including the instrument's instability and its
    non-monotone ordering (§6.1). Add it to threats-to-validity.
17. **The `variable_tracking` numbers in the paper**, greyed, with the exclusion rationale (§6.2).
18. **Repair the artifacts**: the SSA label collision, the three `best_*` fields that emit
    unsupported verdicts, the `dflash4` equivalence row, the duplicate c8192 and s10 cells. Under
    the append-never-rewrite rule, add a sidecar correction file rather than editing.
19. **Pull the missing artifacts** into the repo: `s8-scores-reparsed.json`, the `*.race-025630`
    quarantine files, the pad `.bisection-bug` files, `corpus.txt`. Or delete their citations.
20. **Refresh the navigation layer**: STATUS block, `CLAUDE.md`'s PN/DEC/L ranges and programme
    table, `data/raw/e12/README.md`, and add an S12 design section to the plan (§5.6).

### Requires GPU time — in priority order

21. **MK-NIAH at 131,072, n ≈ 100, both arms (~11 h).** This is the only measurement that saves
    PN-34. PN-33 already costs it correctly. If the owner will not spend it, take W1/W2 and submit
    the honest version — which is a good paper.
22. **`variable_tracking` at 32,768 and 131,072 with an adequate output budget (~2 h).** The data is
    already generated. It is the study's only long-context task with a between-arm gap, and it is
    currently a hole the reviewer will find.
23. **A second code corpus for the divergence ladder (~1 h).** Deduplicated, non-boilerplate — e.g.
    a stratified sample across several repositories. This is cheap insurance on the paper's central
    contribution (V3).
24. **Q4_K_XL at 262,144, reps 2 and 3 (~20 min).** Removes the n=1 from the paper's speed table.
25. **Re-attempt the four single-attempt ceiling failures (~1 h)** so PN-6 and the non-monotonicity
    headline satisfy the project's own two-attempt rule (§6.4).

Items 11–20 cost no GPU time and fix most of the review. Item 21 decides whether the paper keeps its
title.

---

## 11. Scope of the speculative-decoding claim (R12, DFlash, and PN-23/26/29)

*Addressed at the coordinator's request. R12 is external literature, not reviewer opinion, so this
does not compromise the blind pass. My answer is adversarial in the direction requested: I am
stress-testing scope, not defending the finding.*

### 11.1 Does the wording stay scoped to what was measured? — **No. PN-23 is scoped; nothing downstream is.**

What was actually measured: **one drafter** (the model's own MTP head, `--spec-type draft-mtp`), at
**two draft depths** (n=2, n=4), on **one engine build** (`llamacpp-mtp:latest`, 0.3.0-dev, image
`sha256:feb0231976b6…`), on **one quantization** (UD-Q6_K), at **one context** (32,768), on **164
HumanEval+ problems**, at temperature 0 with one seed. That is a single cell of a five-dimensional
space, replicated once.

PN-23's finding line respects all of that:

> "Speculative decoding **with the model's built-in MTP head** is NOT output-identical to
> unspeculated decoding **on this engine** …"

Every restatement loses a qualifier. The sentences at risk, exactly:

1. `README.md:77` — **"Speculative decoding is not output-identical, contrary to the standing
   assumption."** No drafter, no engine, no quantization. This is the headline the paper would
   inherit as a contribution bullet, and it is a claim about the category.
2. `manuscript/OUTLINE.md:35`, contribution 4 — "Speculative decoding **on this engine** is
   deterministically non-equivalent to unspeculated decoding". Engine qualified, **drafter not**.
   The same engine exposes `--spec-type draft-dflash`; the study never measured it on this build.
3. `TRACK-A-DECISION.md:163` — "the premise was wrong: speculative decoding is not output-identical
   **here**". "Here" is doing a lot of work and will not survive extraction into a paper.
4. `OUTLINE.md:92`, §5.4 heading — "Speculative decoding is not free". Fine as a heading about
   cost; hazardous adjacent to bullet 2.
5. PN-23 *Use-as* — "the correction of record for **every prior statement** that speculative
   decoding 'affects speed only'". Scoped to this project's own documents in intent; unbounded in
   wording.
6. `CLAUDE.md:137` / `AGENTS.md:26` — "not lossless **here** / **on this stack**". Correctly scoped;
   these are internal and fine.

This is textbook **"claims not appropriately scoped" / implied generality** in the SIGPLAN sense —
their worked example is "'works for all Java', but actually only on a static subset". The fix is
mechanical: **name the drafter in every sentence that makes the claim**, and reserve the
unqualified form for the *methodological* proposition, which the study genuinely has earned:
*losslessness is an implementation property and must be verified per stack.*

### 11.2 Is "deterministically non-equivalent" the strongest defensible phrasing? — **Yes as an observation, no as an explanation. And the mechanism is cheaper to isolate than the paper claims.**

What S9a establishes, precisely: `nospec` reproduces itself 164/164 byte-identically across two
runs a day apart; `mtp2` reproduces itself 164/164; both differ from each other on exactly the same
33 problems. That supports "reproducibly different decode path" at the level of **emitted text**.

Three residual overreaches:

- **"Deterministic" rests on n=2 repeats under unchanged conditions.** PN-26's caveat says so, which
  is good. But GPU nondeterminism in this class is typically occupancy- and scheduling-dependent; it
  can be perfectly stable across two runs at `-np 1` and unstable at a different concurrency. Say
  "reproducible under identical conditions (two repeats)", not "the engine is deterministic".
- **"Non-equivalent" is measured on text, not on the decision the rule makes.** PN-23's own caveat
  concedes this ("divergence is measured on generated text, not on logits"). It matters more than
  the note lets on: if the target's logits are not bit-identical between a batched verification pass
  and a sequential decode pass, then a *correct* verification rule operating on the logits it
  actually sees will still emit different text. Under that account the speculative **algorithm** is
  faithful and the non-equivalence is a property of the numerics. The claim would be true but about
  a different object than a reader assumes.
- **PN-26's exclusion of that account is a non sequitur** (§5.2): batch-shape-dependent reduction
  order is *itself* deterministic and reproduces perfectly on repeat. PN-26 excluded run-to-run
  nondeterminism, which was never the interesting hypothesis.

**PN-26 says the remaining question "needs engine-level instrumentation rather than output
comparison". That is not true, and the discriminating analysis costs nothing.** Two tests:

1. **Free, from data already on disk.** Convert each divergent problem's first-differing *character*
   offset to a *token* offset and test its position against the draft-chunk lattice. If a
   verification-rule error is responsible, divergences should concentrate at positions congruent to
   the draft boundary (mod n_draft, or at the bonus-token position); if numerics are responsible,
   they should be uniform with respect to that lattice and should instead concentrate where the
   target's top-2 logit margin is small. n=2 and n=4 impose *different* lattices on the same
   problems, which makes this a genuinely discriminating test. The completions are in
   `s8-{nospec,mtp2,mtp4}.jsonl`; PN-23 already computed the character offsets. **This is a
   re-analysis, not an experiment.**
2. **~40 min of GPU, no instrumentation.** Run `nospec` twice with different `-b`/`-ub` (or `-np 2`)
   at temperature 0. If the output changes, batch-shape-dependent numerics are demonstrated on this
   engine *independently of speculation*, which settles the mechanism from the outside.

One weak signal already in the data points at numerics: the n=2 and n=4 first-divergence medians are
**715 and 730 characters** — essentially identical. A rule error that fires per draft chunk would be
expected to bite earlier at n=4, which proposes more tokens per verification.

**Recommended phrasing**, which is both stronger and safer than the current one:

> Speculation with this engine's MTP head is **reproducibly non-equivalent** to unspeculated
> decoding at the level of emitted text: each configuration reproduces itself byte-exactly across
> repeats, and the two differ on the same 33 of 164 problems every time. Whether the difference
> originates in the verification rule or in batch-shape-dependent floating-point reduction order is
> unresolved — **both accounts are deterministic**, so determinism does not distinguish them. The
> operational consequence does not depend on which: a reproducible pipeline must fix the
> speculative setting, not merely the seed.

That last sentence is the fully supported, mechanism-independent, practitioner-relevant result. It
is currently buried in PN-26's *Use-as* field. It should lead.

### 11.3 Should the paper cite DFlash's losslessness claim at all? — **Yes, as motivation. Never as refutation. And R12 currently frames it both ways in adjacent sentences.**

The hostile reading writes itself: *you cite a published claim of bit-for-bit identity, you did not
measure that implementation, the one arm that could have approached it was first voided by an
engine-image error (PN-25) and then re-run on a different engine build with an equivalence figure
you yourself declare unquotable (PN-29) — so you have manufactured a contrast you cannot support.*

That charge is answerable, but only with a specific framing.

**Indefensible:** "DFlash claims bit-for-bit identity; we measure 131/164." Different drafter,
different verification rule, different engine, different hardware. This is Heiser's crime 4.3 in
spirit — evaluating a competitor's claim on a system that is not the competitor's.

**Defensible:** cite it as evidence that *the assumption is live in the literature*, which is
precisely what makes a negative result publishable under NeurIPS 2026's Negative Results rubric
("runs counter to a popularly held understanding"). Something like:

> Losslessness is routinely asserted for speculative decoding. The verification rule — accept the
> longest matching prefix, plus one bonus correction token — is lossless for greedy decoding **in
> exact arithmetic**, and implementations state the property directly: an MLX port of DFlash
> describes its decoding as "bit-for-bit identical to plain target decoding" [R12]. We do not
> dispute that rule, and we did not measure that implementation. We show that on one production
> stack the property does not hold in practice, deterministically and at a rate of roughly one
> generated function in five — so it is an implementation property to be verified per stack, not a
> consequence of the algorithm's specification.

Note what this concedes and what it keeps: it concedes that the *rule* is correct, which it is, and
keeps the finding that the *implementation* is not, which is the interesting part.

**Three guardrails the paper must add:**

1. **Firewall the citation from the DFlash2 number.** PN-29 already forbids quoting 132/164 beside
   MTP's; the same firewall must apply, harder, to R12. A reader who sees "DFlash claims bit-for-bit
   identical" and "our DFlash2 arm: 132/164" within three lines will read a refutation whatever the
   prose says. Put them in different sections.
2. **State the falsifier you did not run**: measuring the DFlash reference implementation against
   its own unspeculated baseline on its own stack. One sentence, and it immunises the paper.
3. **Check the source of the quotation.** R12 attributes "bit-for-bit identical" to the *MLX port's*
   documentation, citing the arXiv paper alongside. A community port's README is a weak source for a
   formal correctness claim. If the arXiv paper makes the claim, cite the paper; if only the port
   does, say "an independent MLX port states…" — a referee who checks and finds the paper more
   careful than the port will treat the whole related-work paragraph as adversarially constructed.

**One correction to R12 itself.** Its opening gloss says the DFlash claim is *"a clean, citable
instance of the assumption our measurements refute."* Its closing gloss says *"We are not
contradicting DFlash's own implementation … we are showing that 'speculative decoding is lossless'
is an implementation property that must be verified per stack."* **These are different claims and
the second is the correct one.** The first sentence is the one that will end up compressed into a
related-work paragraph. Delete it.

**And one opportunity the study is discarding.** Two different drafters, two different verification
paths, two different engine builds — and both land at ~80 % exact reproduction (MTP 131/164 =
79.88 %, DFlash2 132/164 = 80.49 %). PN-29 says only that the DFlash2 figure "must not be quoted
beside MTP's". True for a *ranking*. But the coincidence is itself informative: two substantially
different speculative rules producing the same divergence rate is weak evidence **against** a
rule-specific error and **for** a shared, stack-level cause — which is the numerics hypothesis. That
can be reported honestly, with the confound stated, in one sentence, and it extracts real value from
an arm the study currently treats as spoiled.

**Verdict on scope: V11, severity rank 4.** Not fatal, entirely fixable by wording, but it converts
a defensible result into an attackable one, and R12 as currently drafted makes the attack easier
rather than harder.

---

## 12. Sources consulted

*(Web research on peer-review standards, benchmarking-paper failure modes, null-result reporting and
statistical reporting for ML evaluation was commissioned in parallel with this audit and is recorded
below.)*

<!-- WEB-SOURCES -->

---

## 13. Closing note to the authors

The failures I have listed are, with two exceptions, failures of *propagation* rather than of
measurement: caveats that exist in `PAPER-NOTES.md` and do not reach `README.md`; a clustering
insight applied to one result and not the others; a pooled median whose cells were never checked
against their own keys. The measurement culture here is better than the write-up.

The two exceptions matter. A thesis with no artifact behind it (V1) and a headline corpus that is
absent, undescribed, and self-evidently atypical (V3) are the two things a referee will find first,
because they are the two things a referee checks first: *can I open the evidence, and do I believe
the sample?* Fix those two and address the clustering, and this is a paper I would argue to accept.
