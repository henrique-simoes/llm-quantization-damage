# Reviewer C — full-corpus audit: does the thesis hold across twelve days, or only four?

**Reviewer C**, corpus-completeness and historical integration. Written 2026-09-03.
**Baseline: HEAD `21de94b` (2026-09-03T03:54:18Z).** Read `data/multivac-src/PAPER-REFERENCES.md`
(1,252 L) and `multivac-CLAUDE.md` (1,030 L) in full; extracted and read all 63 files in
`data/archive/experiment-reports/all-reports.tar.gz`; re-derived every number I cite from
`data/raw/e12/**` JSON rather than from prose; read `PAPER-NOTES.md` (PN-1…PN-59),
`OUTLINE.md`, `README.md`, `CLAUDE.md`, `TRACK-A-DECISION.md`, `METHOD-REFERENCES.md`,
`METRIC-CORPUS.md`, `PROVENANCE.md`, `TIMELINE.md`, the build stream (L-1…L-22, DEC-1…DEC-15),
and both prior reviews.

> ### ⚠ The repository moved under this review
> This review was commissioned against a 45-note evidence base. **Five commits landed while it was
> in progress**, the last of them `21de94b` at 03:54:18Z, which added **PN-46…PN-59 and ledger
> L-22** — the historical integration. The occurrence counts in my brief (`SWE-bench` 0, `vLLM` 0,
> `NVFP4` 0, `"Protocol 1"` 0) were **true of the pre-`21de94b` state and are no longer true**;
> they are now 5, 10, 10 and 3.
>
> I have therefore done two jobs rather than one. **§2 is an audit of PN-46…PN-59 against the
> artifacts** — where they are right, where they are wrong, and what they still do not cover —
> plus the orphans that remain after them. The purely additive findings are marked **[C-n]** and
> are, to my checking, in neither prior review nor any paper note.
>
> `manuscript/OUTLINE.md` (mtime 02:57Z) and `README.md` still cite **PN-1…PN-45 only**. Neither
> references a single one of the fourteen new notes. `METRIC-CORPUS.md`, `PROVENANCE.md` and
> `TIMELINE.md` (03:31–03:34Z) were built from "PN-1…PN-44". **The manuscript layer is now
> fourteen notes behind the evidence layer, and every one of the fourteen is about the nine days.**

---

# 1. Verdict on the central question

## 1.1 The answer

**The thesis as currently written in `OUTLINE.md` holds across four days and is *supported* across
twelve — but it is not the thesis the twelve days actually tell, and on two of its load-bearing
statements the historical half of the corpus is evidence *against* the current framing rather than
for it.**

Three separate answers, because "the thesis" is three different claims in the outline:

**(a) "Quantization damage lives in the tail" (PN-35) — holds across four days only, and cannot be
extended.** The quantile decomposition exists for exactly one instrument (`llama-perplexity
--kl-divergence`), one reference arm, one KV dtype, two corpora, and three non-reference arms, all
measured 2026-08-30. Nothing in the first nine days produces a per-token distribution. This is
fine — it is a *new* result and it does not need historical support — but it means the paper's lead
contribution rests on 2.2 hours of GPU inside a twelve-day study, and the honest framing of the
other ten days is *context and corroboration*, not *evidence for the tail*.

**(b) "Task benchmarks bound rather than resolve quantization damage" — this is where the twelve
days matter, and the current outline uses the weakest available evidence for it.** §5.2 argues it
from HellaSwag (n=400), HumanEval+ (n=164, paired, 3 and 5 discordant), and RULER. The first nine
days contain **two much stronger instances that §5.2 does not use**:

- **SWE-bench Verified at n≈50 across three arms inverts the ordering** (IQ4_XS 77.6 % >
  Q5_K_XL 76.0 % > Q6_K 75.5 %; bootstrap [63.27, 87.76] at n=49) — now PN-50. An *inversion*
  is a strictly stronger demonstration than a *null*: it shows the instrument does not merely
  fail to resolve, it actively points the wrong way, on the most expensive and most
  deployment-relevant benchmark in the corpus.
- **Protocol 1 perplexity: the whole four-arm ladder spans 0.033 PPL against a per-point standard
  error of ±0.041** (PN-48). The field's default quantization instrument reproduces the correct
  ranking and cannot certify a single step of it. That is the cleanest single sentence the paper
  has for its thesis and it costs nothing to include.

**(c) "The instrument decides what is visible" — this generalises across twelve days and is
*stronger* over twelve than over four.** Over four days you have three instruments failing to
separate two arms. Over twelve you additionally have: the same checkpoint reading +29 % or +0.8 %
worse depending on protocol alone (PN-49); a thinking-mode accuracy ladder whose entire signal is
the failure-to-terminate rate rather than code correctness (PN-47); a 50-instance agentic benchmark
inverting its own ladder (PN-50); a quantization that is fastest, scores 84.1/81.7 on HumanEval+,
and never once converges on an agentic task (PN-51); and three engines, one of which produced no
number at all (PN-54). **The twelve-day arc is a paper about measurement in which the model is the
apparatus. The four-day arc is a paper about a quantization ladder.** The former is the better
paper and the corpus now supports it.

## 1.2 Where the historical half argues *against* the current framing

Two places, both material.

**(i) The outline's §5.2 ordering claim is contradicted by the study's own agentic data.** §5.2
argues that the three instruments "order themselves by how close the task sits to the model's
limit", and that damage surfaces only where an outcome was already marginal. PN-51 shows the
opposite regime exists: on multi-step agentic work the ladder does not degrade gracefully at the
margin, it *falls off a cliff* — 6 of 6 instances at the step limit for Q3_K_XL against 0 of 6 for
the reference. And PN-52 shows the survivors are **non-monotone** in the other direction (IQ4_XS 23
steps < Q5_K_XL 29 < Q6_K_XL ~45). A paper claiming that instrument sensitivity is governed by
headroom must reconcile with a fourth instrument class in its own corpus where the failure is
categorical rather than marginal. It is a good problem to have — it is the strongest thing in the
study — but §5.2 as drafted does not survive contact with it.

**(ii) The "speed does not discriminate" negative result is an artifact of the estimator, and the
data to fix it is already on disk.** See **[C-1]** below. This is my single most consequential
finding and it changes §5.5 from a null into a mechanism.

## 1.3 What would have to change

1. **Rewrite `OUTLINE.md` against 59 notes.** It cites 42 distinct PN numbers, none above PN-44.
   §Agentic behavior is populated for the first time and has no home in the current section list.
2. **Move PN-49 (protocol reconciliation) to §1 or §4.** The ledger already proposes this; I
   concur emphatically. It is the paper's methodological argument, *measured*, on real weights,
   with the intuitive explanation (tokenizer) tested and falsified. Nothing in §5.2 is as
   persuasive.
3. **Add a §5.x for the agentic axis** carrying PN-50/51/52, and reconcile it with §5.2's
   headroom argument rather than leaving the two adjacent.
4. **Fix §5.5** with the acceptance-normalised re-analysis ([C-1]). The current "speed does not
   discriminate" is true but is reported as unexplained noise; it is explainable, and the
   explanation is a better result.
5. **Withdraw or re-verify three at-depth number sets** that carry the PN-30 signature and were
   never checked: the champion long-context curve ([C-2]), PN-29's DFlash2 at-depth cell ([C-3]),
   and PN-51's "1.000 acceptance at 258,779" ([C-2]).
6. **Update the cost contrast again** — PN-41's 4.8 h omits the 9.36 h mk100 run that produced
   the paper's only separating task result ([C-4]).

---

# 2. The orphaned-findings register

Ranked by how much the paper loses without each. **Status column reads against HEAD `21de94b`.**
"Promote" = deserves a PN entry and a place in the report; "context" = mention with its caveat;
"exclude" = say plainly it is too thin.

## 2.1 Tier 1 — the paper is materially worse without these

### O-1. The perplexity protocol reconciliation — **now PN-49. Audit: correct; promote further.**
*What it shows*: the same NVFP4 checkpoint on the same benchmark corpus reads +29 % worse
(PPL 8.5848) or +0.8 % worse (6.7073) than its comparison ladder depending only on corpus file
(308,707 vs 297,053 tokens), window coverage (602 vs 160 windows) and scoring rule (half-window
with prior context vs all positions from zero). **A 36× swing in the reported effect from
convention alone**, and the intuitive explanation — tokenizer mismatch — was tested and disproven.
*n*: 602 windows / 154,714 scored tokens (P1-matched) vs 160 windows / 77,621 tokens (original).
*Artifact*: `/srv/bench/perplexity/nvfp4-vllm-ppl-protocol1.json` + `nvfp4-p1-token-logprobs.json`
+ `nvfp4-vllm-ppl.json` — **all three host-only; none ships in the repository.**
*Reproducibility*: the vLLM images are deleted but re-pullable by digest (`PROVENANCE.md` §2); the
NVFP4 weights are pinned at `/srv/engines/nvfp4` by sha256. This is the **most reproducible**
historical result in the corpus.
*Recommendation*: **promote to §1 or §4 as the paper's opening empirical argument.** Also: pull the
three artifacts into `data/raw/`. An argument this load-bearing should not have its evidence
exclusively on a host the reader cannot see.

Your assessment is right, and I would put it more strongly than the note does: it is the only place
in the study where a *published-style* comparison is decomposed into its conventions and each
convention's contribution is separately identified. PN-13/PN-35 show a better instrument exists;
PN-49 shows the standard one is not merely blunt but *unanchored*.

### O-2. Q3_K_XL as the thesis in one row — **now PN-51. Audit: three legs sound, one leg invalid.**
*What it shows*: the fastest configuration in the study (116.9 tok/s, MTP n=8) scores 84.1/81.7 on
HumanEval+ with 0 % empties and hits the 250-step agent limit on **6 of 6** instances, against 0 of
6 for the reference.
*n and artifacts, checked individually*:
- **116.9 tok/s — SOUND.** `q3-depth100-20260821-2247.txt` (n=4/6/8 sweep) and
  `n8-repeat-20260822-0008.txt` (three cold restarts: 116.77 / 116.62 / 116.58, spread **0.16 %**).
  Reproducible across cold restarts. Q3_K_XL, tensor split, q4_0 KV, ctx 131,072.
- **84.1/81.7 — SOUND.** `data/archive/ledger-data.json` `humaneval_nonthinking/Q3_K_XL`, n=164,
  0 empties, independently reproduced in `rigor/evalplus-Q3_K_XL.txt` (0.841/0.817).
- **6 of 6 at the step limit — SOUND but n=6.** `rigor/T3-INTERROMPIDO.txt`, corroborated by
  `rigor/swebench-q3.txt` exit status `LimitsExceeded: 6`.
- **"1.000 draft acceptance at 258,779 attended tokens" — ⚠ INVALID. See [C-2].** That cell
  generated **55 tokens over 36 draft events**. It is the exact statistic PN-24's caveat forbids
  quoting and PN-30 withdrew four other notes for.
*Recommendation*: **promote — with the acceptance leg replaced.** The claim "draft acceptance is a
speed metric, not an accuracy metric" is worth making and the corpus supports it much better from
two other rows: `mtpdepth-tensor-tensor-20260820-1346.txt` (acceptance falls 0.601 → 0.142 from
n=2 to n=12 while throughput is *non-monotone*: 48.58 → 40.64 → 30.10 → 44.67 → 36.95) and
`mtpdepth-coding-20260821-2213.txt` (acceptance 0.966 → 0.793 across depths while **every single
cell fails its oracle**). Both are sound generations; neither is in any document.
*Honest limit*: n=6, one quant pair, one scaffold, single seed, a truncated run, and the GGUF is
gone with **no sha256 recorded** (`PROVENANCE.md` §3 records a size for Q4_K_M and nothing at all
for Q3_K_XL). It supports a qualitative disqualification and nothing quantitative. PN-51 says this
correctly.

### O-3. SWE-bench Verified inverts the ladder — **now PN-50. Audit: correct, with one unresolved identity problem.**
*What it shows*: 38/49 = 77.6 % (IQ4_XS), 38/50 = 76.0 % (Q5_K_XL), 37/49 = 75.5 % ("Q6_K") — an
inversion of both the HumanEval+ and the perplexity ordering, inside a bootstrap interval of
[63.27, 87.76] (B=10,000, seed 20260825, n=49). I recompute Wilson intervals of [64.1, 87.0],
[62.6, 85.7], [61.9, 85.4] — widths 22.9–23.5 points against a 2.1-point spread.
*Reproducibility*: patches and per-instance `report.json` are on the host; scoring is CPU-only and
repeatable; the *generation* is not (deleted image).
*⚠ **[C-5] Which Q6 produced the 75.5 %?*** PN-50 labels the arm `UD-Q6_K`. But `UD-Q6_K`
(21,983,677,344 B) was downloaded on **2026-08-29** — the E11 log records "Disk after Q6_K: 23 GB
free on `/`" — while the verified50 run generated between 2026-08-22 and 2026-08-28.
`PAPER-REFERENCES.md`'s checkpoint table dated 2026-08-27 lists **only** IQ4_XS, Q4_K_XL, Q5_K_XL,
Q6_K_XL and the drafter. So the arm is either `UD-Q6_K_XL` or the *earlier, separately deleted*
"old UD-Q6_K (≈21.6 GB)" that the machine log lists as gone. **PN-50 asserts an identity the cited
evidence does not establish**, and it is the same ambiguity the machine log already registers as
instrumentation defect 9. Resolve from the run's launch command on the host before publication;
until then write "the Q6 arm".
*Recommendation*: **promote, with the arm identity resolved or hedged.** This is the strongest
single instance of the paper's thesis.

### O-4. The 1.19 GiB draft-worker wall across three engines — **now PN-53/PN-54. Audit: correct; one mechanistic opportunity missed.**
*What it shows*: SGLang 0.5.18, vLLM nightly + z-lab BF16 drafter, and llama.cpp + Q4_K_M GGUF
drafter — the first two fail with an **identically sized** 1.19 GiB allocation at draft-worker
init; the third works at 38.51 tok/s, acceptance 0.714.
*⚠ **[C-6] The note calls the size coincidence "unexplained"; the stack trace names the
allocation.*** `data/archive/sglang-failure.txt` ends at
`vocab_parallel_embedding.py:338 → quant_method.create_weights → torch.empty` — i.e. the failing
allocation is the **draft model's vocabulary embedding**, not a "candidate-selector workspace"
(which is what `PAPER-REFERENCES.md` infers and PN-53 repeats as a hypothesis). Both failing
stacks load a Qwen3.8-27B-family drafter with the *same vocabulary*, and 1.19 GiB is the right
order for a vocab×hidden BF16 embedding at this vocabulary size. That converts a suspicious
coincidence into a plausible, checkable mechanism, and it strengthens the deployment claim: the
binding cost is the drafter's **unquantized vocabulary projection**, which is exactly what the
4-bit GGUF drafter shrinks. It also predicts the fix (a quantized or tied draft embedding), which
"a fixed workspace" does not. State it as a hypothesis supported by the trace, not as established.
*Recommendation*: **promote; add the trace-level attribution as a hypothesis.** This is the most
externally-generalisable systems finding in the corpus.

### O-5. **[C-1] The "unexplained" decode noise is the acceptance lottery — and normalising it recovers a ladder.** *(new; no PN; contradicts PN-19/PN-36/PN-45's framing)*

This is the largest single improvement available to the paper and it costs no GPU time.

Three passes over one measurement have now reported the within-configuration decode spread at
262,144 as **32.9 %** (PN-19), **46.7 %** (PN-36) and **40.7 %** (PN-45), and all three call the
noise unexplained — PN-19 lists "thermal state, background load, and layer-split nondeterminism"
as candidates. The mediator is in the same JSON row.

**Observation 1 — the split does not change the generation.** In `tsweep-v2-*.json`,
`draft_n` and `draft_n_accepted` are **byte-identical across every `-ts` ratio within a
repetition**: Q4_K_XL @212,992 rep 1 records `148/117` for all six ratios *including the default*;
Q5_K_XL @262,144 rep 1 records `188/97` for all five. Under `-sm layer` a ratio change moves whole
layers between two identical cards without changing the arithmetic, so the sampled continuation is
bit-reproducible. **The ratio sweep is therefore a perfectly controlled experiment.**

**Observation 2 — repetitions *do* change the generation.** Q5_K_XL 54,46 across reps 1/2/3:
`188/97`, `160/111`, `154/113`. Same prompt, same `--seed`, temp 0.7 — the seed does not pin the
sample across container restarts. So a "repetition" is a fresh draw from the acceptance
distribution, not a repeat of a measurement.

**Observation 3 — decode is an almost deterministic function of that draw.** Regressing
`decode_tok_s` on `mtp_acceptance`: Q4_K_XL @212,992 gives **r² = 0.9865** (n=10, six ratios ×
three reps); Q6_K @262,144 r² = 0.896 (n=7); all three arms at 262,144 pooled r² = 0.825 (n=18).

**The fix — normalise to verification cycles.** With MTP, tokens emitted per target forward pass is
`n_predict / (n_predict − draft_n_accepted)`. Dividing decode by that gives target-passes per
second, the quantity the hardware actually delivers:

| group | n | raw decode spread | **normalised spread** |
|---|---|---|---|
| Q4_K_XL @212,992, 6 ratios × 3 reps | 10 | 24.0 % | **4.5 %** |
| Q5_K_XL @262,144, 5 ratios × 3 reps | 9 | 52.2 % | 27.4 % → **3.7 %** excluding the `58,42` cell |
| Q6_K @262,144 | 7 | 46.7 % | 13.8 % → **8.2 %** excluding one cell |
| S9e Q6_K n=2 @262,144, 3 reps | 3 | 29.7 % | **3.1 %** |
| S9e Q6_K n=4 @262,144, 3 reps | 3 | 53.0 % | **0.8 %** |

*(Estimator stated: spread = (max − min)/min, PN-36's convention, applied identically to both
columns. Under PN-19's (max − min)/median the same collapse occurs.)*

**Five consequences.**

1. **§5.5's null becomes a measurement.** At 262,144 the normalised ladder is Q4_K_XL **5.49**
   (n=2), Q5_K_XL **5.30** (n=8, excluding the outlier), Q6_K **5.15** (n=6) target passes s⁻¹ —
   monotone, in the physically expected direction, spanning 6.6 %. Caveat, stated plainly: the unit
   of independence is the *generation*, not the cell (PN-32's own lesson), so this is n=3 per arm
   in the strict sense, and Q6_K's residual spread still overlaps Q5_K_XL's.
2. **A decode-cost model falls out, and it cross-validates across two experiments run two days
   apart with different generation lengths.** Q4_K_XL, MTP n=2, `-ts 56,44`, six depth points from
   S9d (`c131072`, `c196608`; 512-token generations) and Wave 1 (`c212992`, `c229376`, `c245760`,
   `c262144`; 192-token generations):
   **`t_pass = 65.1 ms + 0.476 µs × depth`, r² = 0.991, every residual ≤ 2.6 %.**
   Passes s⁻¹: 8.17 / 6.35 / 6.18 / 5.97 / 5.69 / 5.49.
3. **It explains §5.5 rather than merely reporting it.** At 248,522 attended tokens the KV term is
   118 ms of a 183 ms pass — **64 %** — against 47 % at 124 K. The ladder's 25 % weight-size range
   can therefore only move throughput by ≈9 %, and it moves it by 6.6 %. Feeding GGUF byte counts
   into the weight term predicts 5.46 / 5.11 / 5.01 against the observed 5.49 / 5.30 / 5.15. *The
   arms are indistinguishable on speed because the KV cache, not the weights, dominates decode at
   the deployment window* — a mechanism with a numerical prediction, replacing "noise exceeds the
   effect by six times".
4. **PN-42's outlier becomes attributable.** Q5_K_XL @262,144 rep 1: all five ratios ran the
   *identical* generation (188 drafts, 97 accepted). Four decode at 5.17–5.36 passes s⁻¹; `58,42`
   decodes at **4.21** — −21 % with everything except layer placement held fixed. It also has the
   largest *total* VRAM of the five (30,968 MiB vs 29,342–30,062), consistent with both cards
   sitting nearer the wall. PN-42 calls this "unexplained and untested"; it is in fact the
   best-controlled single observation in Wave 1. Honest limit: n=1, never repeated, and the
   analogous slow cell on Q6_K (`56,44` rep 1) is fast in reps 2 and 3 — so the effect is
   demonstrated once, not twice.
5. **PN-18 is undersold.** Its `-ctxcp 4` vs `32` A/B pair has *identical* draft counts (174/103),
   so the generation is bit-identical and the +6.8 % is measured with the mediator held fixed.
   PN-18's caveat ("directional, NOT a measured 6.8 % effect") is too modest: against a
   generation-matched residual scatter of ~2 %, 6.8 % is a real effect at n=1.

*Recommendation*: **promote to a PN and rewrite §5.5 around it.** Also add `predicted_n` and
`draft_n*` to every future speed artifact — reviewer A already notes `tsweep_v2.py` never records
`predicted_n`, which is what made Wave 1 unauditable against PN-30.

### O-6. **[C-2] The historical long-context speed curve carries the PN-30 defect, unflagged.** *(new; no PN; invalidates part of PN-51 and of METRIC-CORPUS §3.8)*

`data/archive/champion-timings.json` is the artifact behind `PAPER-REFERENCES.md`'s
"*** THE CONTEXT AXIS (this is the paper's 'Context Trade-offs') ***" — described there as
"Clean, monotonic degradation… directly usable as a headline figure" — and behind METRIC-CORPUS
§3.8 and PN-51's acceptance claim. Per-row `gen_tokens` and `draft_n`:

| run | prompt tokens | **gen_tokens** | **draft_n** | acceptance | decode |
|---|---|---|---|---|---|
| q3-embedded … django-cold-258779 | 258,779 | **55** | **36** | **1.000** | 45.17 |
| q3-embedded … context250k | 248,368 | **50** | **34** | **1.000** | 44.61 |
| q3-embedded … context180k | 179,709 | **50** | **34** | **1.000** | 50.12 |
| q3-embedded … context100k | 99,885 | **50** | **34** | **1.000** | 59.27 |
| q5-embedded … context140k | 139,872 | **50** | **34** | **1.000** | 42.86 |
| iq4xs-mtp2 … 37273-prefix-edits-c40k | 40,347 | 430 | 290 | 0.979 | 47.39 |
| mtp2-layer-c180 … 37278-prefix-cold | 168,011 | 1,024 | 719 | 0.922 | 32.62 |
| dflash2-layer-c196 … 37278-prefix-cold | 184,011 | 1,024 | 1,273 | 0.553 | 30.26 |

PN-30's diagnosis, verbatim: *"a decode rate timed over 17 tokens … and acceptance of exactly 1.000
… computed over 36–48 draft events on a trivially predictable continuation."* **The five deep
champion rows are 50–55 tokens over 34–36 draft events at acceptance exactly 1.000.** Same
signature, same magnitude of draft events, three times the token count.

**What this costs and what survives:**
- **Withdraw** the Q3 "context degradation curve" (71.59 → 59.27 → 50.12 → 44.61 → 45.17). It has
  one sound point (40,347, 278–936 generated tokens) and four unsound ones — and it additionally
  mixes two *different tasks* (`prefix-edits-c40k` at 40 K vs `django-cold` at depth), so even the
  shape is confounded.
- **Withdraw** "acceptance 1.000 at 258,779" wherever it appears (PN-51, METRIC-CORPUS §3.8,
  `~/CLAUDE.md` structural fact 2).
- **The MTP-vs-DFlash2 long-context reversal SURVIVES** — those rows generated 162–1,127 tokens
  with realistic acceptance (0.410–0.922). This is the historical finding worth keeping, and S9c
  reproduced it in kind.
- **The champion needle-retrieval passes survive as retrieval results** (they are 50-token JSON
  answers *by design*); only their timings are unusable.

*⚠ Second defect in the same artifact*: those five rows carry `"method": "none"` while recording
34–36 draft events. The `method` field is derived from the run name, and it is **wrong for 5 of 30
rows**. Anyone filtering `method == "mtp2"` silently drops the deepest measurements; anyone
filtering `method == "none"` gets speculative runs. Another instance of the identifier family
(PN-25, PN-27, PN-43).

*Recommendation*: **promote as a defect-register entry and a withdrawal.** It is the sharpest
possible demonstration of the register's value — PN-30's lesson, applied backwards, invalidates a
figure two documents call "the paper's context axis" — and it was found by applying the project's
own rule to its own archive.

### O-7. **[C-3] PN-29's at-depth cell was produced by the same unrepaired probe.** *(new; PN-29 is cited in `OUTLINE.md` §5.4)*

`data/raw/e12/harness-src/s9_final.py` (S9c, DFlash2) posts the raw pad to
`/v1/chat/completions` with `"max_tokens": 192` and no instruction — **byte-for-byte the
construction in `s8_spec.py:156–159` that PN-30 invalidated.** It records no `predicted_n`. S9c ran
2026-09-01T01:42–01:52Z; PN-30 was written at 05:30Z the same day and lists what it withdraws:
PN-24's at-depth half, S8's at-depth figures, and "Wave 1 is entirely unaffected". **PN-29 is not
mentioned.**

Consequence: PN-29's *ceiling* result stands (compute-buffer OOM at 262,144 and 212,992 are load
failures, independent of the probe), but **`8.34 tok/s` and `acceptance 0.4583` at 163,840 are
uncertified**, and they are the numbers `OUTLINE.md` §5.4 uses for "DFlash2 … strictly dominated at
long context". The check is a one-line grep for `eval time = … / N tokens` in
`/srv/bench/server-timings/s9-dflash-atdepth-163840.serverlog` on the host. Zero GPU.

*Recommendation*: **verify before publication; if it is another short generation, restate PN-29 as
a ceiling result only.** Note that PN-29's 32,768 arm (164 real generations, 0 empty, median 51.78
tok/s) is unaffected and is the sound half.

## 2.2 Tier 2 — the paper is better with these

### O-8. HumanEval+ non-thinking ladder — **now PN-46. Audit: sound, with one over-reach.**
Q3_K_XL 84.1/81.7 · IQ4_XS 90.2/87.8 · Q5_K_XL 93.3/90.9 · Q6_K_XL 93.9/91.5, n=164, 0 % empty.
I recompute Wilson half-widths of 5.89 / 5.03 / 4.46 / 4.33 points; only the Q3→IQ4 step (6.1 pts)
clears its interval.
**⚠ [C-7] "Pairs directly with PN-13's divergence ladder, which separates the same arms" is
false.** PN-13's arms are Q4_K_XL / Q5_K_XL / Q6_K vs the Q6_K_XL reference. PN-46's are Q3_K_XL /
IQ4_XS / Q5_K_XL / Q6_K_XL. **The overlap is two arms.** `UD-Q4_K_XL` has *no* non-thinking
HumanEval+ score anywhere in the corpus, and Q3_K_XL and IQ4_XS have no divergence measurement.
The paper cannot join the two ladders; it can say "on two arms common to both instruments,
divergence separates and HumanEval+ does not", which is still true and is what PN-28/PN-40 measure
properly.
**⚠ [C-8] The "cleanest null in the study" rests on two ambiguous keys.** PN-46's context control
(`deep-32768` and `deep-131072`, both 93.3/90.2) uses exactly the keys the machine log flags as
needing "provenance before use" (defect 9), alongside `lcpp-q6k` which scores the same. And if any
of those three is the same quantization as `Q6Kfix` (93.9/91.5), then the same quant scored 0.6–1.3
points apart across runs — **a within-quant spread equal to or larger than the Q5→Q6 between-quant
gap.** That is a *stronger* version of PN-46's point and a *fatal* one for the ladder's top two
rungs. Either way the provenance must be resolved.
*Recommendation*: **promote with both corrections.**

### O-9. Thinking-mode HumanEval+ and the empty-response mechanism — **now PN-47. Audit: sound and under-sold.**
Empty rate falls monotonically with fidelity (12.8 / 12.2 / 11.0 / 7.9 %) while pass@1 is pinned at
86.0 for three of four arms. **The entire fidelity signal in thinking mode is failure-to-terminate,
not code correctness.** This is a first-class measurement-validity finding and belongs in §5.2
beside HellaSwag and HumanEval+, not only in a ladder table: it is a fourth instrument whose signal
is not the thing it appears to measure.
*n*: 164 per arm, 7 arms. *Caveat that must travel*: MTP and DFlash2 rows are not comparable at
fixed quant (PN-23); greedy; pre-2026-08-29.

### O-10. Protocol-1 perplexity ladder — **now PN-48. Audit: sound; the single best sentence for the thesis.**
0.033 PPL of total ladder spread against ±0.041 per point. Promote and put it early: the field's
default instrument reproduces the ranking and certifies none of it.

### O-11. Cross-backend speed and energy — **now PN-55. Audit: correct; two additions.**
vLLM NVFP4 12.44 → 41.21 tok/s (3.31×) vs llama.cpp Q4_K_XL 23.00 → 38.51 (1.67×); the larger
multiplier belongs to the slower engine. MTP acceptance cross-validates at matched depth (0.728 vs
0.709). J/tok 3.60 (vLLM MTP-4) to 9.96 (vLLM no-spec).
**[C-9] Two things to state that PN-55 does not.** (a) **The energy figures here are GPU-pair
energy, measured**, not modelled: `data/archive/spec-speed-metrics.jsonl` gives
`j_per_tok = avg_power_w × wall_s / completion_tokens` from 1 Hz `nvidia-smi` telemetry. Only the
*system* total is modelled (GPU + RAPL + a fixed platform allowance). The paper must not flatten
"energy is modelled" across both. (b) **The n=3 medians hide 27–50 % spreads** —
`MTP4_clean` is `[32.54, 41.21, 41.24]`, an earlier `MTP4` set is `[28.84, 43.30, 38.86]`. The
cross-backend speedup ratios are as underpowered as everything else in the study and carry no
intervals. Say so.

### O-12. vLLM/NVFP4 context ceiling — **now PN-56. Audit: correct; the caveat is the finding.**
Nightly KV pool 52,337 tokens at gmu 0.97 → 51,200 bootable; stable image historically 98,304; MTP
halves it again. PN-56 correctly labels this **boot-verified, not behaviourally verified** — no
deep prefill was ever run — which makes it *not comparable* to the llama.cpp ceilings, which are
behaviourally gated. That asymmetry should be in the sentence, not only the caveat: the paper's
largest single cross-backend number is measured to a weaker standard than the numbers it is
compared against.

### O-13. SGLang produced nothing — **now PN-54. Audit: correct. Keep it short.** One version, one
configuration, no results; the honest form is "attempted and could not be brought up".

### O-14. The deleted image — **now PN-57. Audit: correct and important.** One addition worth a
sentence: PN-57 notes that the surviving images *advertise* `-sm tensor` in `--help`. That is the
generalisable lesson — **flag availability is not capability** — and it is why the historical rows
were produced in good faith.

### O-15. The ten-defect instrumentation audit — **now PN-58. Audit: correct.** The observation that
all ten were repairable at zero GPU cost *because per-instance records were retained* is the
argument for the project's preservation rule and should be stated as such.

### O-16. **[C-10] `coding-battery-20260821-2153.txt` — the study's only validated code-edit oracle matrix, cited by nothing.** *(new; no PN; in no document at all)*

Five quantizations × three django issues, ctx 131,072, q4_0 KV, MTP n=2, with the oracle
**validated first** in `oracle-validation-20260821-2123.txt` (G0 baseline / G1 imports / G2 fails
on pristine / G3 passes with the real fix — all PASS for all three issues):

| quant | #37273 | #37274 | #37278 | resolved | decode tok/s |
|---|---|---|---|---|---|
| Q3_K_XL | ✗ | ✗ | ✗ | **0/3** | 78.4 / 64.0 / 69.1 |
| IQ4_XS | **✓** | ✗ | ✗ | 1/3 | 75.3 / 61.2 / 67.2 |
| Q4_K_M | ✗ | ✗ (fmt fail) | ✗ | **0/3** | 64.8 / 54.5 / 58.0 |
| Q5_K_XL | **✓** | ✗ | ✗ | 1/3 | 57.0 / 48.4 / 51.3 |
| Q6_K | **✓** | ✗ | ✗ | 1/3 | 59.4 / 50.3 / 53.7 |

This is the only place in twelve days where **quantization, a real code-edit task, and a
gate-validated oracle** meet in one table, and it is the second independent instrument on which
Q3_K_XL is the sole total failure. It also has, in one line, the paper's whole argument: the
fastest arm (78.4 tok/s) resolves nothing and the slowest (57.0) resolves as much as any.
*Honest limit*: n=3 tasks, one run each, and 4 of 5 arms are at 1/3 — the instrument is **saturated
at the floor**, so it cannot rank the survivors. It supports exactly one claim: Q3_K_XL and Q4_K_M
resolved zero where three others resolved one.
*Recommendation*: **promote as a supporting row for PN-51, explicitly as an n=3 floor-saturated
instrument.** Not as a ranking.

### O-17. **[C-11] `mtp-compare-n1` vs `mtp-compare-n8` — pre-existing falsifying evidence for the losslessness premise, mis-filed as calibration.** *(new; no PN)*

Two SWE-bench Verified runs on the **same three astropy instances**, same quant, same scaffold,
differing only in MTP draft depth (2026-08-23):

| run | generations | tokens | mean tok/s | wall | resolved |
|---|---|---|---|---|---|
| `mtp-n1` | 122 | 105,163 | 31.56 | 1:02:35 | 2/3 |
| `mtp-n8` | **161** | **137,677** | **61.12** | 0:50:08 | **3/3** |

Under the greedy-losslessness premise the study carried from 2026-08-21, a change of draft depth
could not alter the trajectory. It altered the generation count by **32 %**, the token count by
**31 %**, and the resolve count. **PN-59 says the premise "suppressed measurements for nine days
before being refuted by the first experiment that tested it" — but an experiment that contradicted
it was already on disk seven days earlier, recorded in `ledger-data.json` as `mtp-n1-calib` and
`mtp-n8-calib` and read as calibration noise.** That is a better and more uncomfortable version of
PN-59's point: the premise did not merely suppress experiments, it made the corpus unreadable.
*Honest limit*: n=3 instances; a mini-swe-agent trajectory embeds environment output, so
non-determinism from sources other than speculation is not excluded. It is suggestive, not
conclusive — **and it is cheap to settle**: both trajectory trees are on the host
(`/srv/bench/swebench-results/mtp-n{1,8}/*/​*.traj.json`) and a diff of the first divergent turn
on a shared instance costs zero GPU.
*Recommendation*: **promote as a §Threats/§Method note attached to PN-59.**

### O-18. **[C-12] The historical "high prompt-dependent variance" is a cold-start artifact.** *(new; no PN)*

`PAPER-REFERENCES.md` reports `rigor/recalib-newbuild.txt` as "Q6_K 9 reps: mean 50.77, median
43.53, min 27.82, max 97.02 (sd 23.81) → HIGH prompt-dependent variance". The nine "reps" are
**three different prompts × three repetitions**, and rep 0 is systematically the slowest:

| file | prompt | rep0 → rep1 → rep2 |
|---|---|---|
| `recalib-newbuild` (Q6) | p0 | 32.37 → 87.74 → 97.02 |
| `var-Q3-seed20260822` | p1 | 31.78 → 39.99 → **40.10** |
| `var-Q3-seed20260822` | p2 | 53.70 → 66.87 → **66.77** |
| `var-Q6-seed424242` | p1 | 25.67 → 30.52 → **30.44** |

Held at one prompt and warm, this host is reproducible to **≤0.5 %**. The published "sd 23.81"
pools three prompts and a cold start — the same "aggregate over an untracked variable" family as
PN-20/PN-30/PN-36/PN-45, in the historical corpus, uncaught. Six files
(`rigor/var-Q{3,6}-seed{20260822,424242,987654}.txt`) are cited by **no document in the
repository**.
*Recommendation*: **context, one sentence**, in §5.5 beside [C-1]: run-to-run decode variance on
this host is small when prompt and warm state are fixed, and the large published spreads come from
pooling.

## 2.3 Tier 3 — mention as context, do not build on

- **The 2026-08-20 split-mode matrix** (`data/archive/aug20-splitmode-matrix.txt`) — `-sm row`
  fails with `device CUDA0 does not support split buffers`; `-sm tensor` fails with CUDA illegal
  memory access on two quants with and without MTP. **No PN.** It is the origin of "`-sm layer`
  only", it ships in the repo, and E6 confirmed it on both surviving images. One sentence in
  §Setup with both error strings. (Note the E6 split-mode reproducibility result *also* has no PN
  — METRIC-CORPUS's own UNWRITTEN register lists it.)
- **The 2026-08-20 MTP ablation** (`aug20-mtp-ablation.txt`) — the **embedded MTP head beats a
  separate draft model** (30.64 vs 28.98 tok/s) *and* uses ~776 MiB less on the binding card, and
  depth 3 on the separate drafter is worse than depth 2 with a 19.64–33.10 tok/s spread. **No PN.**
  It is the cleanest justification in the corpus for why MTP is the right speculative method on
  16 GB cards, and it pairs with PN-53. Promote to one row.
- **The ngram/spec-stack ablation** (`specstack-20260820-1523.txt`) — stacking an ngram cache onto
  MTP costs 23 % throughput (63.81 → 49.12); `p-min` and `n-min` do nothing. Context only.
- **The MTP depth-optimum ablations** — n=2 optimal at ctx 32,768 (48.58, acceptance 0.601, falling
  to 0.142 at n=12) but n=8 optimal on a long-context coding task (92.63). Together with S9d/S9e
  this says the optimum is context- *and* quant-dependent, which is the honest version of PN-24 and
  PN-32. Context, with both artifacts named.
- **`ctxcurve-20260820-1500.txt`** — a prefix-cached, calibrated fill curve (34,558 → 258,779
  filled tokens, decode 65.47 → 41.92, prefill 887 → 401, TTFT to 147 s). Independent of the
  champion curve and **not** subject to [C-2] in the same way (it is a different probe), but the
  generation length is not recorded, and it is on the deleted image with f16 KV. Context only —
  and note it disagrees with the champion curve on the same model and split (45.17 vs 41.92 at the
  identical 258,779 filled tokens), which is itself worth one sentence.
- **The disk-exhaustion incident (2026-08-25)** — `dflash2-bench.log` truncated by
  `No space left on device`; Docker at 100.1 GB with 44.62 GB of build cache; the standing warning
  that `docker image prune -a` would have deleted `llama-dflash2:latest`. **No PN.** Context, one
  sentence in §Reproducibility beside PN-57: the image that *was* deleted and the image that was
  nearly deleted are the same lesson.
- **The cited Unsloth KL table** (IQ4_XS ≈0.019 … Q6_K_XL ≈0.0016; NVFP4 code 0.02600). **No PN**,
  cited-not-measured, on a different axis (vs FP16) from PN-13's ladder-relative numbers, and
  METRIC-CORPUS ⚑F-8 records that one of the two source URLs now **404s**. Context only, and fix
  or drop the dead citation — a dead URL in an arXiv reference list is a review finding.
- **Per-benchmark energy** (`/srv/bench/energy-per-benchmark.json`): HumanEval thinking runs
  288–564 GPU Wh each; agentic T3 window 208 Wh; PPL runs 14–33 Wh; **the `nvfp4-ppl` failed-retry
  tax 377 GPU Wh / 1.18 kWh system across 22 failed startups.** **No PN.** The retry-tax figure is
  the only quantified "cost of a defect" in the corpus and belongs in §6 next to PN-41. Everything
  else here is depth-0 and pre-dates the power logger's start (2026-08-27T16:21Z), so **the first
  seven days have no energy instrumentation at all** — state that rather than implying coverage.

## 2.4 Exclude, with reason

- **The grammar-constrained battery** (`grammar-test-20260821-2331.txt` +
  `grammar-rest-20260822-0012.txt`). Q3_K_XL 1/5 and Q4_K_M 1/5 against IQ4_XS/Q5_K_XL/Q6_K 4/5
  looks like a strong result. It is not usable: **the two files use different transports** — the
  first runs `response_format: json_object` through the chat endpoint, the second runs through
  `/completion`. Arm and harness are perfectly confounded. Worse, issue `#37262` records
  `base=False` for IQ4_XS and Q5_K_XL but `base=True` for Q6_K on the same pristine tree, so the
  oracle baseline is not stable. **Exclude, and quarantine with this note** — it is a textbook
  instance of the family the paper's §9 is about, and it is more useful as a defect than as a
  result.
- **`nvfp4-20260822-1029.txt`** ("NVFP4 ctx=262,144, tensor split, q4_0 KV") — internally
  contradictory (those are llama.cpp flags; NVFP4 caps far below 262 K on vLLM). G12/E10 resolved
  it as a llama.cpp NVFP4-GGUF run whose weights are gone. **Exclude**; do not let the row into any
  table.
- **Protocol 2 perplexity** (20 chunks @ c4096: Q4_K_M 5.5031 beating both Q5 and Q6). Non-monotone,
  all five arms inside ±0.062 of each other, tensor split on the deleted image. **Exclude as a
  ranking**; it is usable only as a third data point for PN-49's protocol argument — three
  protocols, three absolute scales, one set of weights.
- **The three-instance SWE-bench "thinking" calibration set.** `mtp-IQ4_XS` is n=1 (two empty
  patches) and the machine log says so; the rest are 2/3 or 3/3 at n=3. **Exclude from any
  ordering**; it is already on the study's own hygiene list.

---

# 3. Contradictions and drift across waves

Numbered for citation. **Live** = present in a current reader-facing document at HEAD `21de94b`.

**D-1 — `OUTLINE.md` and `README.md` are fourteen notes behind.** Both cite PN-1…PN-45 only; the
README's repository map still says "PAPER-NOTES (PN-1..25)" in two places. §Agentic behavior has
been populated for the first time and has no section in the outline. **Live, and the largest
single drift.**

**D-2 — the champion at-depth curve vs PN-30.** [C-2]. `PAPER-REFERENCES.md` calls it "directly
usable as a headline figure"; METRIC-CORPUS §3.8 reproduces it; PN-51 quotes its acceptance. Every
deep row is a 50-token generation with acceptance exactly 1.000 — the signature PN-30 used to
withdraw four claims. **Live, in three documents.**

**D-3 — PN-29's at-depth cell vs PN-30.** [C-3]. Same probe, same day, not withdrawn, cited in
`OUTLINE.md` §5.4. **Live.**

**D-4 — PN-26 vs PN-59 on the same mechanism, and PN-26's argument is invalid.** PN-26 says the
determinism control *refutes* PN-23's hypothesis (b) — "both arms are individually deterministic,
so nondeterminism is excluded". But hypothesis (b) was **deterministic**: a changed decode batch
shape changes the order of float reductions, which produces a different-but-reproducible result.
Determinism across runs does not bear on it. PN-59 (written today) restates the Jaccard argument as
if PN-26 had not withdrawn it. So the corpus now asserts both positions. **My reading: PN-59 is
right and PN-26's retraction should itself be retracted.** Reviewer A reached the same conclusion
independently (its item 30). **Live, and now doubled.**
*The discriminating experiment is cheap and nobody has proposed it*: run **no-spec against no-spec
with a different `-b`/`-ub`**, i.e. change the batch shape without speculation. If ~20 % of
completions change, the finding generalises from "speculation is not lossless" to "**batch shape
changes greedy output on this stack**", which is a larger and more useful claim. ~40 min GPU.

**D-5 — PN-41's cost contrast is stale by 9.4 hours, and four different figures are now in
circulation.** [C-4]. PN-41 (2026-09-02T22:30Z) reports 2.15 h divergence vs ≈4.8 h task
benchmarking = 2.2×. The mk100 run (PN-44, 2026-09-03) added **9.357 h** of task benchmarking —
and it is the *only* task instrument that separated the arms. Recomputed from
`ruler/s12-ruler.json` `cells[].seconds`, `s9/s9-s6.json`, `ssa/ssa-s7-results.json` and
`progress.json`:

| | hours |
|---|---|
| SSA divergence S0–S4 (wall, `progress.json`) | 2.15 |
| — SSA cells S1–S4 alone | 1.95 |
| — S5 task-prompt divergence | 0.37 |
| S6 generative HumanEval+ | 1.29 |
| S7 HellaSwag | 0.54 |
| S12 RULER niah + mkniah | 2.97 |
| **S12 mk100** | **9.36** |
| S12 `variable_tracking` + smoke/mock | 0.17 |
| **task benchmarking total** | **14.33** |

The defensible statement is **≈2.2 h of divergence against ≈14.3 h of task benchmarking, a ratio
near 6×** — and the sharper one: *the single task instrument that did separate the arms cost 9.4
hours, more than four times the entire divergence protocol, to deliver one bounded comparison at
one length.* Meanwhile reviewer A published 5.20 h, reviewer B published 11.4 h, and PN-41
published 4.8 h. **Live in `OUTLINE.md` §6 at 2.2×.** This is the estimator-drift disease applied
to the paper's own cost claim, for the third time.

**D-6 — `TRACK-A-DECISION.md` is stale in three places.** (a) Its decode table still carries
PN-19's superseded "Q4_K_XL n=6, spread 32.9 %", which PN-36 and PN-45 both corrected to n=1 at
262,144. (b) It twice says "SSA S6 (generative, paired, two arms) remains unrun" — S6 ran, and is
PN-28/PN-40. (c) Amendment 2's "What is open" says S9e "re-runs those three cells" — **S9e ran**
(`s9e-n262k.json`: n=2 → 12.474, n=4 → 12.875, n=8 fails to load), and its own artifact carries a
`_WARNING_best_n_per_arm_per_depth` saying the 3 % gap is inside the noise. The document reads as
though the question is open when it is closed as indistinguishable. **Live.**

**D-7 — the STATUS block in the build stream says `last: L-13`, `status: campaign-running`** against
a final ledger entry of L-22 dated 2026-09-03 declaring measurement closed. `AGENTS.md` and
`CLAUDE.md` §1 both direct readers to that block as "the live answer". **Live** (reviewer A flagged
it as V7/§5.6; unrepaired).

**D-8 — PN-35's median row is wrong by ~2× for two of three arms, and the outline's headline
understates the effect.** Recomputed from `ssa/ssa-results-parsed.json` `median_kld`:

| arm | code median | prose median | ratio | PN-35 prints | true "× less" |
|---|---|---|---|---|---|
| UD-Q6_K | 0.000007 | 0.001392 | 0.00503 | 0.01× | **199×** |
| UD-Q5_K_XL | 0.000010 | 0.001810 | 0.00552 | 0.01× | **181×** |
| UD-Q4_K_XL | 0.000017 | 0.003509 | 0.00484 | 0.005× | **206×** |

`OUTLINE.md`'s thesis paragraph and `README.md` both say "**100–200×**". The measured range is
**181–207×**. Every other row of PN-35's table recomputes exactly (p90 0.449/0.541/0.613; p95
1.527/1.888/2.184; p99 4.987/6.709/8.090; max 0.629/0.813/0.729; mean 1.755/2.303/2.623), so this
is an isolated rounding error — but it is in the sentence the title is built on.
*Precision caveat PN-35 does not state*: `llama-perplexity` prints the median at six decimal
places, so the code medians are **one significant figure**. The honest form is "roughly two orders
of magnitude" with the tool's print precision named, not a two-digit ratio. **Live.**

**D-9 — README says the generative anchor was never run.** "*Divergence is measured on prompt
tokens … The paired generative anchor was never run.*" It ran (PN-28) and `OUTLINE.md` §7 says so
in the same repository. **Live.**

**D-10 — the same 258,779-token point has two incompatible decode values.** Champion:
45.17 tok/s (Q3, tensor, c262144, KV unrecorded). `ctxcurve-20260820-1500`: 41.92 tok/s (Q3,
tensor, c262144, **f16 KV**, prefix-cached fill). `PAPER-REFERENCES.md` presents both, the second
as "the authoritative context curve", without reconciling them. Given [C-2], the champion value is
the unsound one. **Live in the mirror.**

**D-11 — `PROVENANCE.md` vs the `-embedded` naming.** PROVENANCE §3: "All four active GGUFs carry
the MTP head… **There was never a separate 'embedded-MTP' build.**" METRIC-CORPUS §3.8 and §4.8,
`PAPER-REFERENCES.md` and `champion-timings.json` all use `q3-embedded` / `q5-embedded` as if it
were a distinct build. G9 resolved this on 2026-08-29; the naming survived the resolution.
**Live**, cosmetic but confusing in a table.

**D-12 — three day-counts for one study.** `TIMELINE.md` is titled "twelve days", spans 08-20 →
09-03 (fifteen calendar days), and closes with "What the thirteen days actually demonstrate".
**Live.**

**D-13 — the note timestamps in `21de94b` are in the future.** PN-46…PN-59 carry
`2026-09-03T14:10:00Z` … `14:46:00Z` and L-22 carries `14:50:00Z`; the commit is timestamped
`2026-09-03 03:54:18 +0000`. In an append-only log whose protocol says "PN IDs are global and
monotonic (read the last entry before appending)", timestamps that are not recorded but estimated
break the only ordering guarantee the file offers. **Live**; trivial to fix and worth fixing before
the artifacts are published.

**D-14 — the historical arm set is not the paper's arm set, and no document says so.** The report's
four arms are Q4_K_XL / Q5_K_XL / Q6_K / Q6_K_XL. The historical task corpus covers Q3_K_XL,
IQ4_XS, Q4_K_M, Q5_K_XL, Q6_K_XL and an ambiguously-labelled "Q6_K" — **overlap with the paper's
ladder: two arms, possibly three.** Every "the same arms" phrase joining a historical result to an
E12 result needs checking. [C-5], [C-7].

---

# 4. Coverage map

**E** = evidence exists · **PN** = has a paper note at HEAD `21de94b` · **§** = appears in
`OUTLINE.md`. Shaded rows (marked ▲) are axes with evidence and no outline home.

| # | Axis | E | PN | § | note |
|---|---|---|---|---|---|
| 1 | Quant ladder — KL divergence, prose | ✔ | PN-13 | 5.1 | |
| 2 | Quant ladder — KL divergence, code | ✔ | PN-14/21 | 5.1 | |
| 3 | Quant ladder — KL divergence, task prompts | ✔ | PN-21 | 5.1 | |
| 4 | Quant ladder — divergence **quantiles** | ✔ | PN-35 | 1, 5.2 | median row wrong, D-8 |
| 5 | Quant ladder — top-1 agreement | ✔ | PN-16 | 5.1 | |
| 6 ▲ | Quant ladder — perplexity, Protocol 1 | ✔ | **PN-48** | ✗ | |
| 7 ▲ | Quant ladder — perplexity, Protocol 2 | ✔ | ✗ | ✗ | exclude as ranking |
| 8 ▲ | Quant ladder — **cross-protocol reconciliation** | ✔ | **PN-49** | ✗ | belongs in §1/§4 |
| 9 ▲ | Quant ladder — cited Unsloth KLD | ✔(cited) | ✗ | ✗ | one source URL 404s |
| 10 | Quant ladder — HellaSwag | ✔ | PN-22 | 5.2 | |
| 11 | Quant ladder — HumanEval+ paired, E12 arms | ✔ | PN-28/40 | 5.2 | |
| 12 ▲ | Quant ladder — HumanEval+ non-thinking, 4 historical arms | ✔ | **PN-46** | ✗ | arm overlap = 2, D-14 |
| 13 ▲ | Quant ladder — HumanEval+ thinking + empty rate | ✔ | **PN-47** | ✗ | |
| 14 ▲ | Quant ladder — SWE-bench Verified n≈50 | ✔ | **PN-50** | ✗ | arm identity open, [C-5] |
| 15 ▲ | Quant ladder — SWE-bench thinking n=3 | ✔ | ✗ | ✗ | exclude |
| 16 ▲ | **Agentic — step counts / convergence** | ✔ | **PN-51/52** | ✗ | **no outline section exists** |
| 17 ▲ | Agentic — validated code-edit oracle battery | ✔ | ✗ | ✗ | [C-10], floor-saturated |
| 18 ▲ | Agentic — grammar-constrained battery | ✔ | ✗ | ✗ | exclude, confounded |
| 19 | Context — ceilings, rebalanced `-ts` | ✔ | PN-6/7/39 | 5.3 | |
| 20 | Context — ceilings, default split | ✔ | PN-39 | 5.3 | single attempts |
| 21 ▲ | Context — ceilings, historical (E1/E1b/E11a) | ✔ | ✗ | ✗ | superseded; label only |
| 22 | Context — decode vs depth | ✔ | PN-36/45 | 5.5 | **[C-1] model available** |
| 23 ▲ | Context — decode vs depth, historical curve | ✔ | ✗ | ✗ | **withdraw, [C-2]** |
| 24 | Context — RULER S-NIAH | ✔ | PN-33 | 5.2 | |
| 25 | Context — RULER MK-NIAH n=100 | ✔ | PN-44 | 5.2 | |
| 26 | Context — RULER `variable_tracking` | ✔ | (in artifact) | 5.2 | excluded post hoc; **no PN** |
| 27 ▲ | Context — champion needle retrieval | ✔ | ✗ | ✗ | KV-UNKNOWN, n=1 |
| 28 | Context — **long-context task accuracy** | ✗ | — | 7 | the standing hole |
| 29 | KV — q4_0 vs f16 fidelity | ✔ | PN-15/43 | 5.6 | n_ctx 2048 only |
| 30 ▲ | KV — dtype viability (q8_0 broken) | ✔ | ✗ | ✗ | three independent failures |
| 31 ▲ | KV — rates / VRAM model | ✔ | ✗ | ✗ | tensor-split, superseded |
| 32 | KV — fidelity **at depth** | ✗ | — | 7 | infeasible (PN-31) |
| 33 ▲ | Split mode layer/tensor/row | ✔ | ✗(E6) / **PN-57**(image) | 5.3 partial | aug20 matrix has no PN |
| 34 | `-ts` optimum, portability | ✔ | PN-7/8/42 | 5.3, 5.5 | |
| 35 | `-ctxcp` | ✔ | PN-18 | 5.5 | undersold, [C-1].5 |
| 36 | Spec — greedy equivalence | ✔ | PN-23 | 5.4 | |
| 37 | Spec — determinism | ✔ | PN-26 | 5.4 | mechanism disputed, D-4 |
| 38 | Spec — draft depth, matched | ✔ | PN-32 | 5.4 | underpowered; **[C-1] recovers it** |
| 39 | Spec — draft depth at 262 K | ✔ | PN-32 (S9e) | ✗ | Track A stale, D-6 |
| 40 | Spec — DFlash2 on its own engine | ✔ | PN-29 | 5.4 | **at-depth uncertified, [C-3]** |
| 41 ▲ | Spec — embedded vs separate drafter | ✔ | ✗ | ✗ | aug20 ablation |
| 42 ▲ | Spec — method ranking flips with context | ✔ | ✗ | ✗ | historical; S9c reproduces |
| 43 ▲ | Spec — ngram stacking | ✔ | ✗ | ✗ | context only |
| 44 ▲ | Spec — **cross-engine draft-worker wall** | ✔ | **PN-53** | ✗ | mechanism hypothesis [C-6] |
| 45 | Spec — temperature > 0 | ✗ | — | 7 | cancelled (DEC-12) |
| 46 ▲ | Backend — llama.cpp vs vLLM context | ✔ | **PN-56** | ✗ | boot-verified only |
| 47 ▲ | Backend — llama.cpp vs vLLM speed/energy | ✔ | **PN-55** | ✗ | n=3, no intervals |
| 48 ▲ | Backend — SGLang | ✔(null) | **PN-54** | ✗ | |
| 49 | Sampling — measured server defaults | ✔ | PN-1 | 3 | |
| 50 | Sampling — thinking control | ✔ | PN-2/3 | 3 | |
| 51 | Sampling — greedy vs official presets | ✔ | (DEC-2) | 7 | **no PN** |
| 52 | Energy — host envelope | ✔ | PN-11 | 5.7 | modelled system total |
| 53 | Energy — thermal asymmetry | ✔ | PN-12 | 5.7 | confounded |
| 54 ▲ | Energy — per-config J/tok, depth-0 | ✔ | (in PN-55) | ✗ | GPU-pair, measured [C-9] |
| 55 ▲ | Energy — per-benchmark Wh + retry tax | ✔ | ✗ | ✗ | 377 Wh defect tax |
| 56 | Energy — per-config J/tok at depth | ✗ | — | 7 | cancelled (DEC-12) |
| 57 | Reproducibility — E12 defect register | ✔ | ×12 | 9 | |
| 58 ▲ | Reproducibility — historical defect audit | ✔ | **PN-58** | ✗ | |
| 59 ▲ | Reproducibility — deleted image / GGUFs | ✔ | **PN-57** | ✗ | |
| 60 ▲ | Reproducibility — disk exhaustion 2026-08-25 | ✔ | ✗ | ✗ | one sentence |

**Read at a glance: 27 of 60 axes have evidence and no outline home; 14 of those now have a paper
note written today and still no outline home; 11 have neither.** Two axes have no evidence at all
and are correctly listed as limitations (#28, #32); three more were cancelled by decision (#45,
#56, and the presence-penalty probe).

---

# 5. Reproducibility audit of the historical half

## 5.1 What a reader could reproduce

**Nothing that requires the engine.** `llamacpp-dflash2-pr27342:1deefcc-sm120-cuda128-abi` was
deleted **without its digest recorded** (`PROVENANCE.md` §2: "gone from disk; no digest recorded
before deletion"), and `llamacpp-nccl231:latest` — which produced the 2026-08-20 split-mode matrix
and MTP ablation — has no id recorded either. Two of the study's twelve days therefore have *no
identified engine at all*.

**What is recoverable in principle:**

| item | status |
|---|---|
| vLLM images (stable 0.27.1, nightly) | deleted but **re-pullable by digest** — the NVFP4 arm is the most reproducible historical work |
| NVFP4 weights | pinned by sha256 at `/srv/engines/nvfp4`; HF revision `57926ba` recorded |
| UD-IQ4_XS GGUF | deleted, **sha256 + bytes recorded** → re-obtainable |
| UD-Q4_K_M GGUF | gone; **size only** (16,464,440,224 B) from `download.log`; no sha256 |
| UD-Q3_K_XL GGUF | gone; **neither sha256 nor size recorded anywhere** |
| `mtp-Qwen3.8-27B-Q4_0.gguf` (separate drafter) | gone; not in any manifest |
| SWE-bench eval images | all 49 pruned 2026-08-29; re-pullable from Docker Hub |
| SWE-bench **scoring** | CPU-only and fully repeatable from the retained per-instance `report.json` |

**So: the Q3_K_XL story — the corpus's most vivid result — rests on a weight file with no recorded
digest, on an engine image with no recorded digest.** That is not a reason to drop it; it is a
reason to state it in the same sentence as the finding.

## 5.2 The Evidence-chain problem

`PROVENANCE.md` states the chain as **paper note → artifact → serverlog** and then records that the
last link does not ship: `*.serverlog` and `power-log.csv` are gitignored. For the historical half
the situation is worse — **the middle link does not ship either.** Not in the repository, and cited
by paper notes as `/srv/bench/...`:

`q6-ceiling.json` · `ctx-ceilings.json` · `splitmode-repro.json` · `provenance-repairs.json` ·
`env-manifest.json` (the E0 one) · `e11/*.json` · `kl-divergence.json` + `kl-evidence/` ·
`energy-per-benchmark.json` · `bootstrap-ci.json` · `nvfp4-vllm-context.json` ·
`perplexity/*` including **all three files behind PN-49** · `evalplus_results/**` ·
`swebench-results/**` including `verified50/per-instance-manifest.json` ·
`champion-20260821/**` (2.2 GB) · `rigor/**` including `T3-INTERROMPIDO.txt`, on which PN-51 rests.

What *does* ship for the nine days is `data/archive/`: nine files plus a 72 KB tarball of 63
experiment reports. **That tarball is the only primary evidence for the historical half in the
public repository, and nothing in the repository references its contents** — I found
`coding-battery`, the grammar batteries, `mtp-compare-n{1,8}` and the six `var-*` seed files by
extracting it, and none of the six is named in any document.

## 5.3 What it costs, and how to say it

The cost is asymmetric and should be stated that way:

- **Systems claims survive.** "`-sm layer` is the only working split mode", "q8_0 KV is broken on
  this stack", "MTP costs context", "a separate BF16 drafter does not fit on 16 GB" are each
  supported by *multiple independent runs across multiple images*, and two of them were re-verified
  on surviving images (E6, S9c). Irreproducibility of one image does not touch them.
- **Accuracy claims survive scoring but not generation.** HumanEval+, SWE-bench and the agentic
  step counts were produced on a lost engine but scored from retained per-item records; a reader
  can re-verify the *scoring* exactly and cannot re-verify the *generation* at all.
- **Speed and ceiling numbers do not survive.** Every tensor-split and every 262,144-token figure
  is irreproducible, and E11a/Wave 1 showed the difference is material (Q5_K_XL's historical
  262,144 did not reproduce until rebalanced).

**Recommended wording for the paper**, in §Setup rather than an appendix:

> The study spans twelve days and two engine generations. Results before 2026-08-29 were produced
> on a container image that was subsequently deleted without its digest being recorded; it is the
> only image on which llama.cpp's `-sm tensor` ever worked on this hardware, and it produced every
> tensor-split and every 262,144-token figure in that period. Two model checkpoints from the same
> period are also gone, one of them with no recorded digest or size. We therefore label every
> pre-2026-08-29 row *irreproducible-on-current-images* and never place one in a table with a
> current measurement. We report those rows because the alternative — omitting the first nine days
> of a twelve-day study — would misrepresent both what was measured and what it cost to learn that
> the measurement had to be redone. Raw tool output (`docker logs`) for every run is retained on
> the host and is not distributed; the artifact metadata records each log's path and byte count.

And the sentence the incident actually earns, which is stronger than the caveat:

> The single most expensive event in this study was not a failed experiment. It was deleting one
> container image.

---

# 6. Title proposals

Nine candidates, conservative to assertive. For each: what it commits to, what it costs, and how it
ages if one finding is qualified. **All are evaluated against the 59-note corpus, not the 45-note
one — which changes the ranking, as §6.2 explains.**

---

**T1 (incumbent, `CITATION.cff` + `OUTLINE.md`).**
*Quantization Damage Lives in the Tail: domain-dependent divergence in a 27B coding model, and what
task benchmarks can and cannot bound*
- **Commits to**: PN-35's quantile decomposition as the lead result; PN-14/21's domain effect;
  PN-40's bound.
- **Costs**: the entire first nine days, both engines, all four task instruments, the systems work,
  and PN-49 — none is visible in the title. It also commits to "tail" as the mechanism when PN-37
  itself calls the tail story "a hypothesis with one supporting quantitative prediction".
- **Ages**: badly if the tail decomposition is challenged, because it is one instrument, one
  reference arm, two corpora, 2.2 h of GPU, and D-8 shows one of its rows is already misprinted.
  There is no second leg.

**T2 (conservative-descriptive).**
*Measuring Quantization Damage in a 27B Coding Model on Two Consumer GPUs: divergence, task
benchmarks, and long-context behaviour*
- **Commits to**: almost nothing beyond having measured.
- **Costs**: it is forgettable, and it invites "so what?" It also under-sells PN-49 and PN-35.
- **Ages**: perfectly. Nothing in it can be falsified.

**T3 (protocol-first — the full-corpus framing).**
*The Same Weights, Twice as Bad: protocol choices dominate reported quantization damage, and what a
sensitive instrument shows instead*
- **Commits to**: PN-49 (36× swing from convention alone) as the lead; PN-48 and PN-46/50 as the
  supporting inability of conventional instruments; PN-13/35 as the alternative.
- **Costs**: leads with a cross-backend result on a checkpoint that is not one of the paper's four
  arms; a reader may expect a broader protocol survey than one reconciliation.
- **Ages**: very well. PN-49 is arithmetically decomposed, its rival explanation was tested and
  falsified, and its evidence is the most reproducible in the corpus (weights sha256-pinned, images
  re-pullable). If the tail result were withdrawn entirely, this title still stands.

**T4 (instrument-inventory, twelve-day framing).**
*Four Instruments, One Ladder: what perplexity, multiple-choice, generative coding and agentic
benchmarks each failed to see about a quantized 27B model*
- **Commits to**: PN-48, PN-22, PN-28/40, PN-50/51 — one instrument per clause, all measured.
- **Costs**: it is a negative-results title; some readers stop there. It also buries PN-35, which
  is the paper's only positive mechanism.
- **Ages**: excellently. Four independent legs; losing one leaves three.

**T5 (systems-forward, `cs.PF`).**
*Two 16 GB GPUs and a 27B Model: context ceilings, tensor splits, and why speed stops
discriminating quantization at depth*
- **Commits to**: PN-6/7/39/42, PN-45, and — if [C-1] is adopted — the decode-cost model
  (`t_pass = 65 ms + 0.476 µs × depth`, KV = 64 % of pass time at 248 K).
- **Costs**: abandons the accuracy contribution, which is the better half.
- **Ages**: well; these are the most mechanical and best-replicated results in the study. It is the
  right title for a *different, shorter* paper, and that paper is genuinely inside this corpus.

**T6 (mechanism + bound, reviewer-A's revision, extended).**
*The Benchmarks Cannot Resolve It: tail-concentrated quantization damage in a coding model, and the
sample sizes four standard instruments would need*
- **Commits to**: PN-35 plus the power argument across four instruments (adding SWE-bench to the
  outline's three).
- **Costs**: "cannot resolve" is a claim about *every* benchmark, which the corpus does not
  support — PN-44's MK-NIAH at n=100 *does* resolve it, and that is the paper's best long-context
  result. The title argues against its own §5.2.
- **Ages**: poorly for that reason.

**T7 (assertive, deployment-facing).**
*Fast, Cheap, and Useless: a quantization can lead every benchmark you can afford and fail every
task you care about*
- **Commits to**: PN-51 and PN-52 as the lead, PN-46/48/50 as the "benchmarks you can afford".
- **Costs**: the lead result is **n=6, one quant pair, one scaffold, single seed**, on a checkpoint
  with no recorded digest, and the arm is not on the paper's ladder. A title that stakes everything
  on it is a reviewer magnet.
- **Ages**: badly. One reviewer asking "n?" removes the title.

**T8 (measurement-as-subject, twelve-day arc).**
*Twelve Days, Four Instruments, One Deleted Image: measuring quantization damage when the
measurement is the hard part*
- **Commits to**: the full corpus — the instrument inventory, the defect register (12 E12 + 10
  historical), PN-57, PN-59, PN-49.
- **Costs**: it is a *methods* paper title, and it foregrounds the study's mistakes. Some venues
  read that as weakness; arXiv `cs.PF`/`cs.SE` readers read it as candour.
- **Ages**: extremely well — it is the one title that *cannot* be falsified by a finding being
  qualified, because withdrawals are part of its subject. But it under-sells PN-35.

**T9 (the synthesis I would actually submit).**
*What the Benchmarks Cannot See, and What the Protocol Decides: quantization damage in a 27B coding
model across twelve days of measurement*
- **Commits to**: the two legs that survive the whole corpus — protocol dependence (PN-49, PN-48,
  the three-protocol perplexity family) and instrument insensitivity (PN-22, PN-28/40, PN-46,
  PN-50, PN-33/44) — with the tail structure (PN-35) as the mechanism inside, not the load-bearing
  claim.
- **Costs**: two clauses is one more than ideal; "twelve days" is unusual in a title and needs the
  abstract to justify it immediately.
- **Ages**: best of the nine. Both legs are multiply supported; the tail result can be qualified
  without touching the title; the systems findings sit naturally under "protocol".

## 6.1 Ranking

**T9 > T3 > T4 > T8 > T1 > T5 > T2 > T6 > T7.**

## 6.2 Defence of the top choice — and why the full corpus changes it

I would submit **T9**, and I would accept **T3** as a shorter alternative.

The incumbent T1 was a rational choice against a 45-note evidence base built entirely from the E12
wave: within that base, PN-35 is the only novel positive result, everything else is a null, and
Dutta et al. (R13) already owns the broad framing. Leading with the tail was the only way to have a
contribution.

**Against the 59-note base that now exists, that reasoning no longer holds, for three reasons.**

*First*, PN-35 is thinner than a title should be. It is one instrument, one reference arm, two
corpora, three arms, 2.2 GPU-hours, no interval on any quantile (the tool attaches uncertainty to
the mean only), a crossover located on a five-point grid, and — D-8 — a median row whose printed
values are wrong by 2× for two of three arms and whose underlying statistic has one significant
figure. PN-37's own caveat calls the mechanism "a hypothesis with one supporting quantitative
prediction". A title should not be more confident than the note it rests on.

*Second*, PN-49 is stronger by every measure a reviewer applies. It has more data (602 windows,
154,714 scored tokens), a decomposed causal account (three named conventions, each with its
contribution), a **falsified rival hypothesis** (tokenizer mismatch, tested and disproven), and the
best provenance in the corpus (weights sha256-pinned, images re-pullable by digest). It is also the
finding a practitioner can act on tomorrow, and it makes the paper's broader argument *without*
needing the reader to accept a mechanism.

*Third — and this is the crux — the twelve-day arc tells a different story from the four-day arc.*
Over four days the story is "a better instrument found something the benchmarks missed." Over
twelve it is: *the study spent nine days running the field's standard instruments — perplexity,
HumanEval+, SWE-bench Verified, agentic step counts, on two engines and three backends — and every
one of them either failed to separate the ladder, inverted it, or reported an effect that moved by
36× when a scoring convention changed. Only then was a divergence protocol adopted, and it
separated the same arms at 3.7–11.8 σ in two hours.* That is a stronger and more honest paper, and
it is the paper the corpus now supports. T9 names both halves of it. T1 names neither.

The practical test: if PN-35 were withdrawn tomorrow, T1 would have to be rewritten and the paper
restructured. T9 would lose a subsection.

One caution, which applies to any title here: **do not put "saturated" in it** (PN-37 shows that is
false for two of three instruments), and **do not put "cannot" in it** (PN-44 resolves the ladder
at n=100 and that is the paper's best long-context result). "Cannot see" survives in T9 only
because it is paired with "what the protocol decides", which is where PN-44 lives.

---

# 7. Abstract proposals

Three complete abstracts, ASCII-clean, arXiv convention. Every number is annotated with its source.
Word counts are exact.

---

## A1 — leads with protocol dependence (my recommendation). **224 words.**

> We report a twelve-day measurement study of a 27B code model (Qwen3.8-27B) across four
> llama.cpp GGUF quantizations on two consumer 16 GB GPUs, and find that what a quantization
> "costs" depends as much on the measurement convention as on the quantization. Scoring one
> checkpoint against the same benchmark corpus under two defensible perplexity protocols reports it
> as either 29% or 0.8% worse than its comparison ladder — a 36-fold difference in the estimated
> effect, attributable to corpus file, window coverage and scoring rule alone. On the ladder
> itself, corpus perplexity spans 0.033 across four arms against a per-point standard error of
> 0.041, and four task instruments — HumanEval+ at n=164, HellaSwag at n=400, SWE-bench Verified at
> n=49-50, and single-needle retrieval at 131,072 tokens — separate no adjacent pair; the
> 50-instance agentic benchmark inverts the ladder outright. Token-level KL divergence over 65,536
> tokens per domain separates the same arms at 3.7-11.8 sigma in 2.2 GPU-hours, and shows damage on
> code to be roughly twice that on prose, rising to 3.1-4.4x on the task distribution. The damage
> is concentrated in a thin band of token positions, which quantitatively predicts the small
> per-problem discordances the task benchmarks show. We also report the systems findings that
> govern deployment at this scale, and a register of twenty-two instrumentation defects, seven of
> which corrupted a published number in this study.

*Sources.* 36-fold / 29% / 0.8%: PN-49 (`nvfp4-vllm-ppl-protocol1.json` 6.7073 vs
`nvfp4-vllm-ppl.json` 8.5848 against 6.6511–6.6839). 0.033 vs 0.041: PN-48 (`ledger-data.json`
`perplexity`). n=164 / n=400 / n=49-50 / 131,072: PN-28+PN-40, PN-22, PN-50, PN-33. Inversion:
PN-50 (38/49, 38/50, 37/49). 3.7–11.8 sigma, 65,536 tokens: PN-13 (`ssa-results-parsed.json`).
**2.2 GPU-hours: `progress.json` ssa_S0→ssa_S4, 2.15 h — replaces PN-41's superseded contrast; see
D-5.** 2x code/prose and 3.1–4.4x: PN-14, PN-21. Thin band: PN-35 (p95 1.53–2.18x, p99 4.99–8.09x),
prediction of 3/164 and 5/164: PN-37. Twenty-two defects: 12 E12 paper notes + 10 historical
(PN-58); seven corrupted a published number (PN-5, PN-17, PN-20, PN-25, PN-30, PN-36, PN-43).

---

## A2 — leads with the tail structure (closest to the incumbent). **221 words.**

> Quantization damage to a 27B code model is not uniform across tokens: it is concentrated in a
> thin band of positions. Measuring token-level KL divergence between llama.cpp GGUF quantizations
> and a higher-fidelity reference over 65,536 tokens per domain, we find that at the median a code
> token is perturbed roughly 200 times less than a prose token, that the ordering reverses between
> the 90th and 95th percentile, and that by the 99th percentile code is perturbed 5.0-8.1 times
> more. The familiar summary that code is about twice as damaged as prose is the mean of those two
> opposite facts. This structure predicts why benchmarks miss the effect: benchmarks score
> outcomes, and a perturbation confined to a few percent of positions changes an outcome only when
> a perturbed token lands somewhere decisive. Across four instrument classes we measure exactly
> that. Paired on identical problems, the ladder's extremes disagree on 3 of 164 HumanEval+
> problems and 2-4 of 400 multiple-choice items, bounding the task-level effect at about 3 points;
> single-needle retrieval is perfect for both arms at every length to 131,072 tokens; and only
> multi-key retrieval at that length, where the reference itself fails 11% of the time, separates
> them (89.0 against 79.0, exact McNemar p=0.002). Divergence separates the same arms at 3.7-11.8
> sigma in 2.2 GPU-hours against 14.3 hours of task benchmarking.

*Sources.* ~200x median: **recomputed, D-8** — `ssa-results-parsed.json` `median_kld` gives
0.00503 / 0.00552 / 0.00484, i.e. 199x / 181x / 206x (PN-35's table misprints two of three; do not
use "100-200x"). Crossover, p99 5.0–8.1x: PN-35. 2x mean: PN-14. 3/164, 2-4/400, ~3 points:
PN-40, PN-22. Retrieval: PN-33, PN-44 (89/100 vs 79/100, p=0.0020, `s12-ruler.json` `mk100`).
3.7–11.8 sigma: PN-13. **2.2 h vs 14.3 h: recomputed, D-5** — `progress.json` plus
`s9-s6.json` 1.29 h, `ssa-s7-results.json` 0.54 h, `s12-ruler.json` 12.34 h.

---

## A3 — leads with the twelve-day arc and the deployment setting. **224 words.**

> We report what it took to measure quantization damage to a 27B code model on two consumer 16 GB
> GPUs, and what the measurement turned out to depend on. Over twelve days we ran the instruments
> the field ordinarily reaches for — corpus perplexity, HumanEval+, HellaSwag, SWE-bench Verified,
> and agentic step counts — across three inference backends. None separated adjacent quantizations:
> perplexity spans 0.033 across four arms against a 0.041 standard error; HumanEval+ at n=164 and
> HellaSwag at n=400 bound the effect at about 3 points; SWE-bench Verified at n=49-50 inverts the
> ordering inside a 24-point interval. One backend produced no measurement at all, and one
> quantization that leads every cheap instrument in the study — the fastest configuration measured,
> 116.9 tokens per second, and 84.1 pass@1 on HumanEval — reached the step limit on 6 of 6 agentic
> instances where the reference converged on 6 of 6. Token-level KL divergence separates the same
> arms at 3.7-11.8 sigma in 2.2 GPU-hours, locates the damage in a thin band of token positions,
> and shows it to be roughly twice as large on code as on prose. We further show that a single
> checkpoint's reported degradation moves 36-fold under two defensible perplexity protocols. We
> report the deployment findings for this hardware class, and a defect register of twenty-two
> instrumentation faults, offered as method rather than confession.

*Sources.* 0.033 vs 0.041: PN-48. n=164 / n=400 / ~3 points: PN-40, PN-22. n=49-50 inversion and
24-point interval: PN-50 (bootstrap [63.27, 87.76]; Wilson widths 22.9–23.5 recomputed). Backend
producing nothing: PN-54. 116.9 tok/s: PN-51 (`n8-repeat-20260822-0008.txt`, three cold reps,
0.16% spread). 84.1: PN-46. 6 of 6 / 0 of 6: PN-51 (`rigor/T3-INTERROMPIDO.txt`, **n=6**).
3.7–11.8 sigma, 2.2 h: PN-13, `progress.json`. Thin band, 2x: PN-35, PN-14. 36-fold: PN-49.
Twenty-two defects: as A1.
**⚠ If this abstract is used, the n=6 must appear in the abstract's own sentence or in the first
paragraph of §1** — it is the single most attackable number in the paper.

---

## Recommendation

**Use A1.** It leads with the finding that is best evidenced, best provenanced, most reproducible,
and hardest to attack; it reaches the tail structure by the end without staking the paper on it;
and it is the only one of the three whose first sentence is true of all twelve days rather than of
four. A2 is the right abstract if the owner decides the tail result must lead — but it should be
adopted **only with D-8 fixed**, because its opening number is currently misprinted in three
documents. A3 is the most interesting to read and the most dangerous to defend: an n=6 result in
the fourth sentence of an abstract will be the first thing a reviewer tests.

---

# 8. What I would do next — one week, no GPU

Ordered by value per hour. Items 1–6 are corrections to things a reader can currently falsify from
the repository.

1. **Rewrite `OUTLINE.md` against 59 notes** (~4 h). Add a §5 subsection for the agentic axis
   (PN-50/51/52 + [C-10]); move PN-49 to §1/§4; fold PN-46/47/48 into §5.1; put PN-53/54/55/56 in a
   systems/backend subsection; add PN-57/58 to §9. Update `README.md`'s two "PN-1..25" strings.
   **This is the single highest-value item: fourteen notes written today are invisible to the
   manuscript.**

2. **Withdraw the three at-depth number sets that carry the PN-30 signature** (~2 h).
   [C-2] the champion curve (five rows, `gen_tokens` 50–55, acceptance 1.000) — write the paper
   note, annotate `champion-timings.json` with a `_WARNING` block as was done for the SSA label
   collision, and remove the acceptance leg from PN-51. [C-3] grep
   `/srv/bench/server-timings/s9-dflash-atdepth-163840.serverlog` for `eval time = … / N tokens`
   and either certify or withdraw PN-29's 8.34 tok/s and 0.4583. Fix `champion-timings.json`'s
   `method` field for the five mislabelled rows.

3. **Adopt the acceptance-normalised re-analysis [C-1]** (~4 h). One paper note; one table in §5.5;
   the decode-cost model `t_pass = 65.1 ms + 0.476 µs × depth` (r² = 0.991) as a figure; PN-42's
   outlier restated as a controlled −21 % observation; PN-18 upgraded from "directional" to
   measured. This turns the paper's weakest section into one with a mechanism, at zero GPU cost.

4. **Recompute the cost contrast and fix D-5** (~30 min). ≈2.2 h vs ≈14.3 h; add the sharper
   sentence about mk100's 9.4 h. Supersede PN-41 rather than editing it.

5. **Fix D-8** (~30 min): PN-35's median row to 0.005 / 0.006 / 0.005, the headline to "roughly two
   orders of magnitude (181–207×)", and add the one-significant-figure precision caveat. Then
   re-read the outline's thesis paragraph and `README.md` for the same string.

6. **Resolve the two identity questions** (~2 h, host access, no GPU). [C-5] which Q6 checkpoint
   produced the verified50 SWE-bench arm — read the run's launch command or `props.json` on the
   host. [C-8] the provenance of `deep-32768` / `deep-131072` / `lcpp-q6k`; if any shares a quant
   with `Q6Kfix`, the same-quant run-to-run spread on HumanEval+ is itself a finding and PN-46
   should carry it.

7. **Settle the speculative-decoding mechanism argument on paper** (~2 h). D-4: PN-26's retraction
   of PN-23's hypothesis (b) is logically invalid and PN-59 now contradicts it. Write the
   superseding note; specify the ~40-minute experiment that would settle it (no-spec vs no-spec at
   a different `-b`/`-ub`) as the paper's named cheapest open question; and re-do the free
   first-divergence analysis on `s8-{nospec,mtp2,mtp4}.jsonl` that reviewer A also asked for.

8. **Mine the two unreferenced batteries** (~3 h). [C-10] `coding-battery` + `oracle-validation`
   into a supporting row for PN-51, explicitly as a floor-saturated n=3 instrument. [C-11]
   `mtp-compare-n{1,8}` into a note attached to PN-59, and diff the two trajectory trees on a
   shared instance to see where they fork. Quarantine the grammar batteries with the
   cross-endpoint-confound note.

9. **Pull the missing historical artifacts into `data/raw/`** (~2 h, bandwidth only). Priority
   order: the three PN-49 perplexity files; `T3-INTERROMPIDO.txt` and `swebench-q3.txt` (PN-51);
   `verified50/per-instance-manifest.json` and the per-instance `report.json` set (PN-50);
   `splitmode-repro.json`, `ctx-ceilings.json`, `q6-ceiling.json`, `energy-per-benchmark.json`,
   `bootstrap-ci.json`, `kl-divergence.json`. Every one is small. **No paper note whose evidence
   line points only at `/srv/bench/` should survive to submission.**

10. **Repair the navigation layer** (~1 h). D-7 the STATUS block (L-13 → L-22, `campaign-running` →
    closed); D-6 `TRACK-A-DECISION.md`'s three stale passages; D-9 the README's "generative anchor
    was never run"; D-12 the day-count; D-13 the future-dated timestamps; D-11 the `-embedded`
    naming; and METRIC-CORPUS ⚑F-8's dead Unsloth URL.

11. **Add one row to `METRIC-CORPUS.md`'s UNWRITTEN register per item still lacking a note**
    (~1 h). As currently structured the register cannot surface pre-E12 material at all, because
    `HISTORICAL-PRE-E12` is a separate status from `UNWRITTEN` — which is precisely why nine days
    went unnoticed. Make the two orthogonal.

12. **Write §7 (threats) before polishing §5**, as the outline already instructs, and add four
    threats the current list lacks: the historical arm set overlaps the paper's by two arms (D-14);
    the historical corpus has no energy instrumentation before 2026-08-27T16:21Z; two engine images
    and two checkpoints have no recorded digest; and the paper's own cost contrast has now been
    published at four different values.

---

## Closing

The measurement culture in this project is better than its write-up, and the write-up is improving
faster than the manuscript. In the six hours before this review was filed, the corpus gained
fourteen paper notes covering the nine days it had been ignoring, and they are careful, correctly
caveated, and — where I checked them against artifacts — accurate in all but the four places listed
above. The remaining gap is not knowledge. It is that `OUTLINE.md` still describes a four-day
paper, and the evidence base is now a twelve-day one.

The most useful thing I can leave is this: **the study's own defect register, applied backwards to
its own archive, invalidates a figure that two documents call the paper's context axis.** That is
not an embarrassment. It is the best possible advertisement for keeping the register — and it is
the argument the paper should make about itself.
