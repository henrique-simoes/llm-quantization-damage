# Reviewer D — adversarial review: statistics, identification, positioning

**Venue frame:** arXiv cs.LG / cs.PF systems-measurement report, read as if for MLSys or the
NeurIPS Datasets & Benchmarks track.

**Basis.** `README.md`, `CLAUDE.md`, `manuscript/OUTLINE.md`, `docs/paper/PAPER-NOTES.md`
(PN-1…PN-45), `docs/paper/METHOD-REFERENCES.md` (R1–R13), `docs/paper/TRACK-A-DECISION.md` and both
amendments, `docs/build-stream/2026-08-30-quant-bench-trackA.md` (DEC-1…DEC-15, L-1…L-22),
`manuscript/references/{METRIC-CORPUS,PROVENANCE,TIMELINE}.md`, `references.bib`,
`data/multivac-src/*`, and **direct recomputation from `data/raw/e12/`**. I read
`reviewer-a-rigor.md`, `reviewer-b-structure.md` and `insider-notes.md` first, deliberately, and
this review is written to go past them rather than to repeat them. Where I restate one of their
findings it is because a *later* artifact changed its status, and I say so.

**Mandate.** Statistical validity, causal identification, related-work positioning, and whether the
central claims survive a hostile read. Every number below was recomputed from the JSON. Where my
arithmetic disagrees with the prose I show the work.

**Scope note on timing.** Reviewers A and B were written against PN-1…PN-34. Six paper notes have
landed since (PN-39…PN-45), including **PN-44, which is now the paper's headline long-context
result and which no prior reviewer has seen.** My first and largest objection is about PN-44, and
it is new.

---

## 1. Verdict

### Recommendation: **major revision.** One headline result must be re-analysed before it can be stated at all; two others must be re-scoped. I would not reject this paper, and I would fight to keep it out of the reject pile if a co-reviewer wanted it there.

Let me say the good part first, because it is unusual and I do not want it lost in what follows.

This corpus does something I almost never see: **it corrects itself, in public, against its own
rules, nine times, and the corrections get sharper each round.** PN-45 is a correction to a
correction (PN-36) of a correction (PN-19) — and it is right, and I verified it to the third
decimal. The `_WARNING_label_collision` field written into `ssa-results-parsed.json` inverts the
file's own trust rule for exactly the two cells that need it, and says so. `corpus-manifest.json`
carries a `stated_limitation` field that volunteers the single most damaging fact about the code
corpus (0.240 bits/token; mean 1,266× median) rather than hiding it. `s12_mkniah_generate.sh` was
written *after* two reviewers found the dataset present but its generating command absent. The
quarantine convention — supersede, never delete — is honoured. `CITATION.cff` validates cleanly
against the schema in `cff.json`. The divergence ladder itself (PN-13, PN-14, PN-21) is correctly
computed, monotone in three domains, and I could not break it.

That discipline is the paper's real contribution and it should be the thing the reader remembers.
It is also why the objections below land as hard as they do: **this project has written down the
exact rule that each of its remaining errors violates.**

### The three objections most likely to sink the paper

---

#### **D1. The paper's long-context headline (PN-44) measures output-budget exhaustion, not retrieval. On the items where the budget did not bind, both arms score 55/55 with zero discordance.**

This is the objection I would lead a review with, and it is fatal to §5.2 as currently drafted.

`s12_ruler.py` serves RULER's MK-NIAH prompts to `/completion` with `n_predict = 128`, RULER's
budget for `niah`. The model is Qwen3.8-27B with **thinking on** — the harness cannot disable it,
because `chat_template_kwargs` is a `/v1/chat/completions` parameter and this code path uses
`/completion`. Every one of the 200 predictions in
`s12-preds-{Q6_K_XL,Q4_K_XL}-mk100-c131072.json` opens with `<think>` and enumerates candidate
magic numbers before answering.

Recomputed from those two files:

| | UD-Q6_K_XL (reference) | UD-Q4_K_XL |
|---|---|---|
| scored correct | 89/100 | 79/100 |
| `</think>` closed within budget | **77/100** | **60/100** |
| closed **and** wrong | **0** | **0** |
| unclosed and wrong | 11 | 21 |
| unclosed but answer emitted before cutoff | 12 | 19 |

**Not one item in either arm was scored wrong after the model finished reasoning.** Every failure,
in both arms, is a generation truncated at the token cap. Three of the reference's eleven failures
and three of Q4's twenty-one *end in a strict prefix of the correct number* — item 34's reference
output terminates at `...brawny-engineer is: 889043` against a gold answer of `8890439`. The needle
was retrieved; the budget expired one character early; the item scored zero.

Decompose the effect:

| analysis | n | reference | Q4_K_XL | discordant | exact McNemar |
|---|---|---|---|---|---|
| **as reported (PN-44)** | 100 | 89 | 79 | 10 (0 vs 10) | p = 0.00195 |
| **the actual mechanism** — did the model finish inside 128 tokens? | 100 | 77 | 60 | **27 (5 vs 22)** | **p = 0.00151** |
| **retrieval, conditional on the budget not binding in either arm** | **55** | **55/55** | **55/55** | **0** | — |

On the 55 items where neither arm's budget bound, multi-key retrieval at 131,072 tokens is
**perfect for both arms and perfectly concordant**. The entire 10-point gap is carried by items
where at least one arm was still enumerating distractors when the budget ran out.

The finding that survives is real, separated, and worth reporting — *the 4-bit arm exhausts a fixed
output budget 17 points more often, and the paired closure test separates at p = 0.0015* — but it
is a finding about **answer latency and reasoning verbosity under a fixed budget**, not about
long-context retrieval accuracy. Three consequences follow immediately:

1. **The Red Hat comparison is void.** PN-44 places 88.76 % recovery "inside the band Red Hat
   publishes for INT W4A16 at 128K (85–88 %, R9)". Red Hat's models answer directly; theirs is a
   retrieval measurement and this one is not. Two numbers that measure different constructs
   agreeing to two significant figures is a coincidence, and printing it as external corroboration
   is the most quotable error in the paper.
2. **PN-37's inference collapses.** PN-37 calls PN-44 "the cleanest confirmation of the tail
   mechanism the study has" and reads it as "damage surfaces where the task already sits near the
   model's limit." The 11 items the reference fails are not near the model's retrieval limit; they
   are items where the model chose to enumerate four keys before answering. The tail mechanism
   predicts nothing about that.
3. **This is the project's own signature defect, for the sixth time, on its headline.** The
   harness's only output-validity gate is `n_empty`, and `n_empty = 0` is *exactly* what a
   uniformly-truncated arm produces. PN-30's rule — "a benchmark harness must assert that the model
   produced the output it was asked for, not merely that the input reached it" — is violated
   verbatim. PN-5's rule — publish the enforced gate, not the intended one — likewise.

And the asymmetry a hostile reviewer will not let go of: **`variable_tracking` was excluded from
this same battery for this same defect.** `s12-ruler.json`'s `variable_tracking_exclusion` reads
"this measures output verbosity against a fixed budget, not long-context ability", and the
justification for keeping `niah` was "its 128-token budget is ample for a short numeric answer, and
both arms scored 100.0 at 8,192." That check was performed on **single-needle retrieval at 8,192**
and never re-run when the task was made harder and the context sixteen times deeper. At 8,192 both
arms close `</think>` on 25/25. At 131,072 on MK-NIAH they close on 77 and 60. The budget check did
not transfer, and nobody re-checked it. So the study excluded the task where the artifact ran
*against* its thesis and retained the task where the same artifact runs *with* it. That sentence
will appear in a review whether or not it is fair, and the only way to prevent it is to disclose
the decomposition above in the paper's own voice.

**What would answer this objection.** Three options, in increasing cost:

- **Free, today, zero GPU.** Re-analyse the committed predictions exactly as above and rewrite
  §5.2's third instrument as two results: (i) *retrieval at 131,072 is indistinguishable between
  the ladder's extremes on the 55 % of items where the output budget does not bind (55/55 vs
  55/55)*; (ii) *the 4-bit arm exhausts a 128-token budget on 40 % of items against the
  reference's 23 %, paired p = 0.0015* — a measured behavioural cost of quantization that is
  genuinely novel and that nothing in Red Hat or Mekala reports. Drop the accuracy-recovery framing
  and the R9 comparison. This is a *better* paper than the current draft, and it costs nothing.
- **~1 h GPU.** Re-run both arms through `/v1/chat/completions` with
  `chat_template_kwargs {"enable_thinking": false}` (PN-2's own validated control) at 131,072.
  Note the structural constraint the authors should state either way: with `prompt_n` median
  130,936 in a 131,072 window there are **136 tokens of headroom**, so the budget *cannot* be
  raised at this rung. Disabling thinking is the only available fix, and that is itself a
  reportable interaction between instruction-tuned reasoning models and RULER's constants.
- **~9 h GPU.** Both, and report the three-way comparison.

**Minor, same result.** The n=100 sample is not independent of the n=12 pilot that motivated it:
`--random_seed 42` in `s12_mkniah_generate.sh` means the first twelve `refs` of the mk100 file are
byte-identical to the mkniah file, and one of the ten discordant items (index 9) is inherited from
the pilot. Dropping the twelve gives 77 vs 68 on n=88, 9 discordant, all one-directional,
p = 0.0039, −10.23 points. **The conclusion survives**, and the paper should report the fresh-88
figure so that a reviewer cannot raise it.

---

#### **D2. PN-35's tail structure — the paper's declared lead contribution — is a property of the corpus, not of quantization. A perturbation that is not weight quantization at all reproduces it exactly.**

PN-35's table is arithmetically correct. I reproduced every cell from `ssa-results-parsed.json`
(median 0.0050/0.0055/0.0048 — the note rounds two of these to 0.01× where 0.005× is closer;
p90 0.4493/0.5409/0.6126; p95 1.5271/1.8880/2.1843; p99 4.9876/6.7087/8.0901; max
0.6290/0.8129/0.7296; mean 1.7552/2.3035/2.6232). No dispute about the arithmetic.

The dispute is about attribution, and the study contains its own control without realising it.

`ssa-Q6_K_XL-code-kld-e2` is the PN-15 cell: the **reference arm against itself**, with the only
difference being the KV cache dtype (f16 base, q4_0 scoring). No weight quantization. A completely
different physical perturbation. Same corpus, same instrument, same token budget, same seed.

Normalise every cell's quantiles by its own mean — this strips the magnitude and leaves the
*shape* of the damage distribution:

| cell | perturbation | mean | median/mean | p90/mean | p95/mean | **p99/mean** |
|---|---|---|---|---|---|---|
| Q6_K prose | weights | 0.003321 | 0.419 | 2.030 | 3.176 | **8.62** |
| Q5_K_XL prose | weights | 0.004465 | 0.405 | 1.983 | 3.121 | **8.36** |
| Q4_K_XL prose | weights | 0.008207 | 0.428 | 1.990 | 3.113 | **8.48** |
| Q6_K code | weights | 0.005829 | 0.0012 | 0.520 | 2.764 | **24.50** |
| Q5_K_XL code | weights | 0.010285 | 0.00097 | 0.466 | 2.558 | **24.35** |
| Q4_K_XL code | weights | 0.021529 | 0.00079 | 0.465 | 2.592 | **26.15** |
| **Q6_K_XL code (PN-15)** | **KV dtype only** | 0.002955 | **0.00135** | **0.517** | **2.771** | **22.87** |

The last row is not a quantization arm. It is the reference model perturbed by changing a cache
dtype, and its normalised tail shape is indistinguishable from the weight-quantization arms on the
same corpus, and completely different from the same weights on the other corpus. Mass concentration
tells the same story: ≥24.5 / 24.3 / 26.1 % of total divergence sits in the top 1 % of tokens on
code for the three quantization arms, ≥22.9 % for the KV-only cell, and ≥8.6 / 8.4 / 8.5 % on prose.

**Shape is set by the corpus; magnitude is set by the perturbation.** "Quantization damage to code
lives in the tail" is, on the study's own artifacts, "*any* distributional perturbation on this code
corpus lands in the tail, because ~90 % of the corpus's tokens are near-deterministic." Reference-arm
perplexity on this corpus is 1.1809 — **0.240 bits/token** — on a path-sorted django tree that is
among the most heavily trained-on Python in existence. That is a memorisation-saturated corpus, and
a bimodal KL distribution is what a memorisation-saturated corpus produces under any perturbation.

The apparent monotonicity in aggressiveness above the crossover is also thinner than it looks.
Divide the p99 code/prose ratio by the mean code/prose ratio for each arm: **2.84, 2.91, 3.08.**
Essentially constant. PN-35's headline p99 row (4.99 → 6.71 → 8.09) is PN-14's mean row
(1.76 → 2.30 → 2.62) multiplied by a near-constant shape factor. Beyond PN-14, the tail table
contributes roughly one new number — that the code/prose shape factor is ~0.25 at p90 and ~2.9 at
p99 — and that number is reproduced by a non-quantization perturbation.

I want to be precise about what survives, because a lot does:

- **Survives:** the *measurement* that mean KLD on code is a poor summary of a distribution whose
  median is 1,266× smaller. That is a real and useful methodological point, and PN-16's metric-pair
  argument is its correct expression.
- **Survives:** that the crossover between p90 and p95 occurs for all three arms. It is arithmetically
  forced once code's normalised p90 (0.47–0.52) is below prose's (~2.0) while the mean ratio is
  1.76–2.62, so it is one fact observed three times, not three confirmations — but it is a fact.
- **Does not survive:** "*quantization* damage to code lives in the tail" as a claim about
  quantization, and PN-37's contribution ordering that puts it first as "what is actually ours".
- **Does not survive:** the mechanistic prediction chain. PN-37 claims the tail structure "predicts"
  the 3/164 and 5/164 discordances. It cannot, because the same tail structure is produced by a
  perturbation whose task-level effect is never measured. A mechanism that predicts the same
  outcome for two perturbations of very different magnitude is not making a prediction.

**What would answer this objection.** (a) Report the KV-only cell in the same table as the
quantization arms — it is already in the artifact — and state plainly that the shape is
perturbation-invariant and corpus-determined. That converts a contested causal claim into an
uncontested and more interesting measurement: *the corpus, not the compression, decides where
damage lands, which is why quantization tables built on any single corpus are non-transferable.*
(b) Add a second code corpus that the model does not predict at 0.24 bits/token — a held-out or
recent repository, ~1 h GPU — and show whether the shape moves. If the shape is corpus-invariant
too, the finding is much bigger than the paper currently claims. If it moves, the paper has
measured the thing it says it measured. Either outcome is publishable; the current framing is the
only one that is not.

---

#### **D3. The provenance chain terminates outside the repository for every headline number, and the reproducibility register is the part of the paper that must be reproducible.**

`.gitignore` excludes `*.serverlog` and `server-timings/`. The corpus contains **72 distinct
serverlog paths cited as evidence** and **zero serverlogs**. `corpus.txt` is gitignored; `*.kld` is
gitignored; `pads/` is gitignored. For a paper whose thesis is that the field's instruments cannot
be trusted and whose Appendix B is a register of instrument failures, this is the one structural
weakness that a reviewer can verify in ninety seconds and that no amount of prose will fix.

Concretely, what an external reader cannot check:

- **PN-35's 99.9th-percentile row is serverlog-only** by the note's own admission. That is one row
  of the paper's declared lead table which exists nowhere a reader can reach.
- **Every `failure_mode` attribution** — `compute-buffer-oom`, `load-or-health-failed`,
  "the draft context does not fit" — is derived by `classify_failure()` from a serverlog. Every
  context-ceiling claim (PN-6, PN-7, PN-29, PN-39, and the S9e n=8 ceiling) rests on a
  classification the reader cannot see.
- **PN-25's five DFlash2 loader errors** are cited to five serverlogs, none present. The poisoned
  `dflash4` row is still live in `s8-scores.json` with `pass@1 0.000`.
- **PN-27's cascade** cites `data/raw/e12/logs/preflight-selfmatch-20260831/` — the directory does
  not exist in the repository.
- **PN-38's evidence** cites `quarantine/s11-divdepth.json.n1-padoverflow-20260901` — absent
  (`s11/s11-divdepth.json` is present, but it is not the file cited).
- **The quarantine manifest indicts itself.** `quarantine/LISTING.txt` enumerates ten quarantined
  artifacts. **Two are present** (`tsweep-v2-Q4_K_XL.json.shallow-prefill-79pct` and
  `tsweep-v2-Q6_K_XL.json.badratios`). Missing: both `.bisection-bug` pads, `pad_e12.py.orig`,
  `tsweep_v2.py.orig`, `tsweep-v2-Q4_K_XL.json.superseded-shallow`, and all three
  `*.race-025630` files that PN-10 cites as its evidence. A committed manifest of eight absent files
  is worse than no manifest: it documents that the quarantine convention was not actually applied to
  the public artifact. (Two later items — the s9d degenerate sweep and its README — *are* present and
  post-date the listing, so the convention is being followed going forward and the gap is historical.)

**On artifact badging** — since `acmtxt.md` at the repository root is a 76 KB scrape of ACM's
current badging policy, complete with its cookie-consent banner, `[#IABV2SETTINGS#]` template
placeholders and sixteen `blob:http://localhost/` image URLs, and `acm.html` (45 KB) and `cff.json`
(64 KB, the CFF *schema*, not a citation) sit beside it, all four tracked in git:

- **Delete all three scraped files before publication.** They are not evidence, they are browser
  detritus, and in a repository whose entire argument is provenance discipline they are the first
  thing a reader will notice. Cite the policy URL in the paper if it is needed.
- **Which badge is honestly claimable?** *Artifacts Available* — and only that, and only after a
  Zenodo deposit with a DOI (and ideally a Software Heritage SWHID). `CITATION.cff` currently
  declares `repository-code: https://github.com/henrique-simoes/multivac-paper`, which does not
  exist; the only remote is a local bare repo. That is a public claim of availability that is
  presently false and must be fixed or removed.
- ***Artifacts Evaluated — Functional* is not claimable**, and the paper should not imply it.
  ACM's Functional criteria require artifacts to be *complete*: "all components relevant to the
  paper in question are included". The serverlogs, the code corpus, the `.kld` reference logits,
  the pads, eight of ten quarantine items, and `s9_score.sh` — the script that computes PN-28's and
  PN-40's paired statistics, and which `s9_chain.sh` line 93 still invokes — are all absent. Add to
  that a host requirement of 2× RTX 5060 Ti and an engine image that no longer exists for the
  historical arm. (`s8-scores-reparsed.json`, which reviewer A recorded as missing, has since been
  added; the fix rate on this class of gap is good, which is why the remainder is worth naming.)
- ***Reusable*, *Results Reproduced*, *Results Replicated*: not claimable**, and the last two
  require an independent party by definition.

**What would answer this objection.** (a) Ship the serverlogs. They are the single highest-value
missing artifact and the whole point of hard rule 1; if size is the concern, ship them gzipped, or
ship the `classify_failure()`-relevant tail of each. (b) Ship `corpus.txt` (9.1 MB — trivial) or,
if licensing forbids, ship the file list plus per-file sha256 so the corpus is reconstructible.
(c) Ship the eight missing quarantine items or amend `LISTING.txt` to say what was not published
and why. (d) Add an explicit "what is not in this release, and why" section — the paper's own
honesty conventions make that section a strength rather than an apology. (e) Delete `acmtxt.md`,
`acm.html`, `cff.json`; keep the validation, drop the scrape.

---

## 2. Statistical audit

### 2.1 Multiple comparisons: the correction does not change the conclusions, and the paper should say so out loud

A repository-wide search for `bonferroni|holm|family-wise|false discovery|benjamini` returns nothing
across ~14,000 lines of documentation, and `references.bib` contains no multiple-comparison
reference of any kind. A reviewer of a paper about statistical care will notice.

So I did the correction. I enumerated **every inferential test in the corpus** — nine divergence
z-separations (three domains × three arm pairs), six HellaSwag McNemars, two HumanEval+ McNemars,
the MK-NIAH McNemar, and PN-32's sign test — **nineteen tests**, and applied Holm and
Benjamini–Hochberg to the whole family.

| rank | test | σ | p | Holm threshold | Holm | BH threshold | BH |
|---|---|---|---|---|---|---|---|
| 1 | KLD code Q6_K vs Q4_K_XL | 18.13 | 1.8e-73 | 2.6e-03 | **pass** | 2.6e-03 | y |
| 2 | KLD task Q6_K vs Q4_K_XL | 16.10 | 2.6e-58 | 2.8e-03 | **pass** | 5.3e-03 | y |
| 3 | KLD prose Q6_K vs Q4_K_XL | 13.48 | 2.2e-41 | 2.9e-03 | **pass** | 7.9e-03 | y |
| 4 | KLD code Q5_K_XL vs Q4_K_XL | 11.82 | 3.2e-32 | 3.1e-03 | **pass** | 1.1e-02 | y |
| 5 | KLD task Q5_K_XL vs Q4_K_XL | 11.17 | 5.9e-29 | 3.3e-03 | **pass** | 1.3e-02 | y |
| 6 | KLD code Q6_K vs Q5_K_XL | 8.67 | 4.3e-18 | 3.6e-03 | **pass** | 1.6e-02 | y |
| 7 | KLD prose Q5_K_XL vs Q4_K_XL | 8.48 | 2.2e-17 | 3.8e-03 | **pass** | 1.8e-02 | y |
| 8 | KLD task Q6_K vs Q5_K_XL | 8.26 | 1.5e-16 | 4.2e-03 | **pass** | 2.1e-02 | y |
| 9 | **KLD prose Q6_K vs Q5_K_XL** | **3.71** | **2.0e-04** | **4.6e-03** | **pass** | 2.4e-02 | y |
| 10 | acceptance falls with draft depth (12/13) | — | 1.7e-03 | 5.0e-03 | **pass** | 2.6e-02 | y |
| 11 | RULER mk100 MK-NIAH @131,072 | — | 2.0e-03 | 5.6e-03 | **pass** | 2.9e-02 | y |
| 12 | HellaSwag Q6_K vs Q4_K_XL | — | 1.25e-01 | 6.3e-03 | fail | 3.2e-02 | n |
| 13–17 | HellaSwag, remaining five pairs | — | 0.50–1.00 | — | fail | — | n |
| 18–19 | HumanEval+ base / plus | — | 1.00 | — | fail | — | n |

**All eleven positive results survive both Holm and Benjamini–Hochberg across the full 19-test
family.** Bonferroni's threshold at m = 19 is z = 3.008; the weakest separation is 3.71. This is a
credit to the study and the paper should print this table rather than leave a reviewer to compute
it. *The absence of multiple-comparisons treatment is a presentational failure, not a substantive
one — for the tests actually reported.*

Three qualifications, in increasing severity.

**(a) The correction and the clustering problem interact, and one claim dies.** Reviewer A's V4 is
right that PN-13's `±` is a per-token Gaussian SE over 32 contiguous 2,048-token windows of one
document. What A did not do is quantify where each separation fails. Under a design effect DEFF the
reported σ falls by √DEFF:

| comparison | σ at DEFF=1 | DEFF that drops it below z=1.96 | **DEFF that drops it below the Bonferroni z=3.008** |
|---|---|---|---|
| **prose Q6_K ~ Q5_K_XL** | **3.71** | **3.6** | **1.5** |
| prose Q5_K_XL ~ Q4_K_XL | 8.48 | 18.7 | 8.0 |
| prose Q6_K ~ Q4_K_XL | 13.48 | 47.3 | 20.1 |
| code Q6_K ~ Q5_K_XL | 8.67 | 19.6 | 8.3 |
| code Q5_K_XL ~ Q4_K_XL | 11.82 | 36.4 | 15.4 |
| code Q6_K ~ Q4_K_XL | 18.13 | 85.6 | 36.3 |
| task Q6_K ~ Q5_K_XL | 8.26 | 17.7 | 7.5 |
| task Q5_K_XL ~ Q4_K_XL | 11.17 | 32.5 | 13.8 |
| task Q6_K ~ Q4_K_XL | 16.10 | 67.5 | 28.6 |

Cluster size is 2,048 tokens, so DEFF = 1 + 2047·ICC. **DEFF = 1.5 corresponds to ICC = 0.00024** —
an autocorrelation so small that assuming it away is not defensible for per-token KL divergence
within a single 2,048-token passage. So under multiplicity correction, **the prose adjacent pair
Q6_K vs Q5_K_XL does not survive any plausible clustering.** Everything else needs ICC in the
range 0.003–0.017 to fail, which is possible but not assumed.

The operational consequence is precise and easy to fix: **the paper's signature phrase "3.7–11.8 σ"
quotes a range whose lower endpoint is the single claim that does not survive.** Drop it. Quote the
code-domain separations (8.7–18.1 σ), which are robust to DEFF up to 8–36 under Bonferroni, and
report the prose adjacency as "not separated once clustering is accounted for."

The honest instrument is available at zero GPU cost: `llama-perplexity` scores in chunks, so a
**chunk-level paired t-test on 32 observations** (9 for the task domain) is computable from the
tool's own per-chunk output. With 31 df a t-interval is ~4 % wider than the normal, so this costs
almost nothing in power if the clustering really is negligible — and settles the question if it is
not. The `.kld` files that would permit an ICC estimate were not retained; the per-chunk numbers in
the serverlogs would suffice and are also not in the repository (see D3).

**(b) The real multiplicity risk is not the FWER of the reported tests. It is the forking paths.**
The corpus ran, by my count from the artifacts: 21 valid `tsweep` cells across 4 arms × 5+ ratios ×
several rungs; 24 `s9d` cells; 10 SSA cells; 12 RULER cells; 4 S8 arms; plus the S9/S9e batteries.
Nineteen tests were reported. The selection of which comparisons to report — and, in one case,
which to *escalate to n=100* — was made after seeing the data. That is not fraud, it is normal
exploratory measurement, and the correct remedy is not Bonferroni but a **declared
confirmatory/exploratory split**:

> *Confirmatory* (fixed before the data): the SSA divergence ladder under DEC-11, and MK-NIAH at
> n=100 whose analysis script was committed before the second arm finished.
> *Exploratory* (selected after inspection): everything else, reported with intervals and no
> significance claims.

The paper can make this split honestly, because the ledger records the order of every decision.
Very few papers can. Use it.

**(c) MK-NIAH's escalation is selected, and the paper must say so.** Two RULER tasks were run.
S-NIAH showed nothing; `variable_tracking` was excluded; MK-NIAH showed a hint at n=12 and was
escalated to n=100. Pre-registering the *analysis* (which PN-44 correctly did, and correctly
advertises) is not the same as pre-registering the *task selection*. State it in one sentence and
the objection evaporates; leave it unstated and it becomes an accusation.

### 2.2 Power: the minimum detectable effect for every headline claim

The paper's own best insight (PN-40) is: *before reporting a null, state the smallest effect the
test could have detected.* PN-40 applies it to PN-28 and to nothing else. Here is the full table.

For paired binary outcomes the floor is set by the **discordant count**, not by n. The smallest
discordant count that can reach two-sided exact p < 0.05 is **m = 6** (min p = 0.03125).

| claim | instrument | n | discordant | min attainable p | MDE at 80 % power | claim exceeds MDE? |
|---|---|---|---|---|---|---|
| PN-13/21 divergence ladder | KLD, 65,536 tok | 32 chunks | — | ~1e-16 | Δmean ≈ 0.0007 at DEFF 1 | **yes**, by 2–30× (except prose adjacency, §2.1a) |
| **PN-22 HellaSwag, all six pairs** | multiple choice | 400 | 0–4 | **0.125 – 1.00** | **unbounded — no outcome could reach 0.05** | **no test was possible** |
| PN-28/40 HumanEval+ base | generative | 164 | 3 | 0.25 | ≥ 6 discordant, i.e. ~3.7 pts | no |
| PN-28/40 HumanEval+ plus | generative | 164 | 5 | 0.0625 | ≥ 6 discordant, i.e. ~3.7 pts | no |
| PN-33 S-NIAH ×3 lengths | retrieval | 25/25/12 | 0 | 1.00 | unbounded | no test was possible |
| PN-44 MK-NIAH | retrieval | 100 | 10 | 0.00195 | π ≥ 0.9 at m=10 gives power 0.74 | **yes** — but see D1 |
| PN-32 draft depth | sign test | 11–13 pairs | — | — | — | tests a tautology (§3.3) |
| PN-19/36/45 decode speed | throughput | 1–3 reps | — | — | ~7 % vs stated 40.7 % noise | **no** — but the noise is misattributed (§3.1) |
| PN-18 `-ctxcp` | A/B | 1 | — | — | — | correctly labelled directional |

**The row that matters, and that PN-40 missed.** PN-40 was written specifically to fix the "report
a null whose test had no power" error, and it fixed it in PN-28 only. **PN-22 — the other half of
the paper's central argument — contains six McNemar tests, and not one of them could have reached
p < 0.05 under any outcome.** The largest discordant count in `ssa-s7-paired.json` is 4, whose
minimum attainable two-sided exact p is 0.125. PN-22's finding line calls HellaSwag "structurally
INSENSITIVE… not merely underpowered," and cites six p-values as the evidence. The p-values are
evidence of nothing. The *discordance counts* — 0, 2, 2, 2, 2, 4 out of 400 — are the informative
quantity and they support a bounded statement, not a structural one.

Two further defects in the same file, both new:

- The reported p-values are **Edwards' continuity-corrected χ²**, which is invalid at b+c ≤ 4. The
  exact values differ: 0.4795 → **0.5000**, and 0.1336 → **0.1250**. PN-22's claim "all p ≥ 0.13" is
  therefore false on the exact test by 0.005; trivial numerically, but the paper elsewhere insists
  on naming the estimator, and here it names the wrong one.
- The four arms' correct-sets are **perfectly nested**: Q6_K ⊂ Q6_K_XL = Q5_K_XL ⊂ Q4_K_XL, so
  every one of the six pairs has b = 0 or c = 0. Reviewer A flagged the nesting; the statistical
  consequence nobody has drawn is that **six pairwise tests on four nested sets carry at most three
  independent bits**, so treating them as six tests inflates the apparent evidence and any
  correction applied to them is the wrong correction.

**Remedy for §5.2's first instrument**, at zero cost: replace the six p-values with one sentence —
*"On HellaSwag at n = 400 the four arms' correct-answer sets are perfectly nested and differ by at
most four items; with a maximum discordant count of 4 the smallest p-value the design could produce
is 0.125, so this instrument bounds the ladder-wide effect at roughly ±1 point and cannot test it."*

### 2.3 Every null in the paper, adjudicated

The mandate asks whether each null is real or underpowered, and specifically whether the project
criticises underpowered nulls in PN-32 while relying on one in PN-36/PN-19. My adjudication:

| null | status |
|---|---|
| PN-22 HellaSwag | **Underpowered, and the paper's language overreaches.** "Structurally insensitive" is a mechanism claim supported by an interpretation, not by a test that could have failed. Retreat to the bound. |
| PN-28/40 HumanEval+ | **Correctly handled after PN-40.** The paired interval [−2.68, +1.46] is the right object and the note says so. This is the model the other nulls should follow. |
| PN-33 S-NIAH | **A real ceiling, not an underpowered null** — 100/100 in both arms at three lengths with zero empties and (I checked) zero truncations. This is the sturdiest null in the corpus and the paper undersells it. |
| PN-19 → PN-36 → PN-45 speed | **Underpowered *and* misattributed.** See §3.1: 83 % of the "noise" has an identified cause sitting in the same JSON row. The insider notes' objection #2 is correct — the paper cannot criticise a null-under-high-variance in §5.4 while resting on one in §5.5 — but the resolution is not more repetitions. It is to control the variable. |
| PN-32 draft-depth ranking | **Correctly declared unanswerable.** The best-handled null in the corpus. |
| PN-9 acceptance-by-quant | **Not a null; an unresolved confound reported as a finding.** Its own caveat says so. |

**The direct adjudication requested.** The project does apply an inconsistent standard, but not in
the way the insider notes describe. PN-32 refuses to rank on n=3 against 166 % spread — correct.
PN-36/PN-45 conclude "speed does not discriminate" on n=1–3 against 40.7 % spread — and that is
the *same inference* PN-32 refuses, made in the opposite direction. The asymmetry is defensible only
if the paper states it: **a null under high variance can support "we could not detect a difference"
and cannot support "there is no difference."** README currently says "the cheaper arm is **only**
less accurate", which is the forbidden form. §5.5 must say: *decode throughput at the full window
differs by 6.74 % across arms against a within-configuration spread of up to 40.7 %; we cannot
resolve a difference of this size, and we do not claim there is none.* And then §3.1 below shows
how to resolve it for free.

### 2.4 Independence assumptions

- **Per-token KLD (PN-13/14/15/21/35).** Treated as 65,536 independent Gaussian draws. They are 32
  contiguous windows of a single document. Quantified in §2.1a.
- **Shared reference logits.** All three arms are scored against one `base-*.kld` file computed once
  from Q6_K_XL. The three divergences are therefore positively correlated through the shared
  reference, and they are computed on the *same* tokens — so the comparisons are **paired but
  analysed as unpaired**. This is conservative (a paired analysis would be tighter), and the paper
  should say so; it is one of the few places where the study's statistics are *understating* its
  case, and a reviewer who spots it unaided will assume the authors did not know.
- **HumanEval+ items (PN-23/26/28).** 164 problems that share prompt style, docstring conventions
  and, in several families, near-identical structure. Treating them as independent Bernoulli trials
  is the field's convention and I will not penalise it, but the paired analysis is doing the real
  work and the paper is right to lead with discordance.
- **RULER items (PN-33/44).** Independently generated haystacks with unique needles — genuinely
  independent, and Wilson intervals are appropriate. The one violation is the pilot/confirmatory
  overlap (§D1).
- **Speculative acceptance events (PN-32).** Correctly diagnosed by the study itself as clustered
  within generations. Best statistical passage in the corpus.
- **`tsweep` "repetitions" (PN-19/36/45).** Rep 1 is a cold prefill; reps 2–3 reuse the prefix cache
  (`prompt_n: 4, cache_n: 123666` in the s9d cells, and the same construction in Wave 1). They are
  not exchangeable replicates and should not be pooled into a median without saying so.

---

## 3. Causal identification

### 3.1 The "unexplained" decode noise is not noise, and the explanation is one column over

This is the finding I would put second in a review after D1, because three separate passes over the
same measurement (PN-19 → PN-36 → PN-45) all treated the variance as irreducible host noise, and it
is not.

Two facts, both read directly from `tsweep-v2-*.json`:

1. **`mtp_acceptance` is identical across every `-ts` ratio at the same rep index** — Q5_K_XL rep 1
   reads 0.5160 at 54,46 / 56,44 / 58,42 / 60,40 / 62,38; rep 2 reads 0.6937 at both repeated
   ratios; rep 3 reads 0.7338. Q6_K rep 1 reads 0.5920 at 56,44, at 58,42, **and at `-ctxcp 32`**.
   Acceptance is a property of the *generated continuation*, not of the configuration. (Reviewer A
   noticed this; nobody drew the consequence.)
2. **Decode throughput is 83 % explained by acceptance.** Regressing `decode_tok_s` on
   `mtp_acceptance` across all 17 `ok` cells at ctx 262,144 with `-ctxcp 4`, three arms and five
   ratios: `decode = 4.53 + 11.32 × acceptance`, **r = 0.909, R² = 0.827**, residual SD 0.62 tok/s
   against a raw SD of 1.48.

Condition on acceptance and the paper's noise floor collapses:

| arm | `-ts` | n | raw readings | raw spread | **acceptance-adjusted spread** |
|---|---|---|---|---|---|
| Q5_K_XL | 54,46 | 3 | 10.82 · 12.70 · 12.94 | 16.7 % | **2.7 %** |
| Q5_K_XL | 56,44 | 3 | 10.78 · 12.51 · 12.91 | 17.1 % | **2.6 %** |
| Q6_K | 58,42 | 3 | 10.75 · 14.16 · 11.90 | 28.6 % | **9.6 %** |
| Q6_K | 56,44 | 3 | 10.22 · 14.99 · 11.71 | 40.7 % | **11.0 %** |

PN-45's "40.7 % within-configuration spread", the number the paper's §5.5 argument rests on, is
mostly the sampled continuation. The Wave-1 speed cells run under DEC-2 official sampling
(temp 0.7), which makes the generated text vary between reps, which makes draft acceptance vary,
which makes throughput vary. **Running the speed probe greedy — as S8, S9a, S11 and S12 all do —
would have removed ~83 % of the variance at zero additional cost.**

This does not overturn §5.5's conclusion, and I want to be fair about that: after adjustment the
between-arm residual means are Q4_K_XL +0.61, Q5_K_XL +0.005, Q6_K −0.21 tok/s, and Q4_K_XL has
n = 1 repetition group, so nothing is resolvable either way. But it changes what the paper can say
about *why*, and it changes the cost of fixing it from "n ≥ 30 per arm, never in scope" to "three
greedy reps per arm, ~1 h GPU." A reviewer will ask why a study this careful about instruments let
its own throughput measurement be driven by an uncontrolled sampling variable that it recorded in
the same row.

**Credit where due:** the one reading that *survives* the adjustment is PN-42's outlier. Q5_K_XL at
`-ts 58,42` decodes at 8.50 tok/s with acceptance 0.516, against 10.44–10.82 for four other ratios
at the *same* acceptance. That is a genuine ratio effect of about −2.2 tok/s, and PN-42's surviving
claim — "the most balanced split was the slowest, by 21 %; among the rest, imbalance made almost no
difference" — is *strengthened* by conditioning on acceptance, because the four clustered readings
become genuinely comparable rather than accidentally so.

### 3.2 The MK-NIAH design is clean; the outcome variable is not

Unusually for this corpus, the S12 design isolates the variable properly: one `-ts` ratio for both
arms (56,44 — not each arm's own optimum, which is the *right* choice here and against Heiser's
crime 4.3 only in appearance), same KV dtype, same greedy sampling, no speculation, same prompts,
paired. There is no confound in the *manipulation*. The failure is entirely in the *measurement*
(D1). Say so in the paper — a clean design with a compromised outcome variable is a more
instructive story than a messy design, and it is another entry for Appendix B.

### 3.3 PN-32 tests a property of its own metric

`acceptance = draft_n_accepted / draft_n`. Under the standard stop-at-first-mismatch verification,
with per-token match probability q, expected acceptance at draft depth n is

  acceptance(n) = q(1 − qⁿ) / (n(1 − q)),

which is **strictly decreasing in n for every q < 1.** "Acceptance falls monotonically as draft
depth rises" is therefore a theorem about the ratio, not a measurement about the model. Reviewer A
reached the same conclusion; here is the quantitative version that makes it actionable. Backing q
out of each cell:

| depth | arm | acc n=2 / n=4 / n=8 | **implied q: n=2 / n=4 / n=8** | q spread |
|---|---|---|---|---|
| 131,072 | Q4_K_XL | 0.673 / 0.512 / 0.404 | 0.763 / 0.750 / 0.793 | 0.043 |
| 131,072 | Q5_K_XL | 0.814 / 0.493 / 0.449 | 0.870 / 0.736 / 0.818 | 0.134 |
| 131,072 | Q6_K | 0.775 / 0.558 / 0.251 | 0.841 / 0.780 / 0.678 | 0.164 |
| 196,608 | Q4_K_XL | 0.666 / — / 0.373 | 0.758 / — / 0.774 | 0.016 |
| 196,608 | Q5_K_XL | 0.746 / 0.429 / 0.573 | 0.820 / 0.689 / 0.875 | 0.186 |
| 196,608 | Q6_K | 0.920 / 0.790 / 0.517 | 0.946 / 0.908 / 0.851 | 0.095 |
| 196,608 | Q6_K_XL | 0.704 / 0.556 / — | 0.788 / 0.778 / — | 0.010 |

**q is approximately invariant to draft depth within an (arm, depth) cell**, which is exactly what
the theory predicts and is a *positive control on the instrument*. That is the reportable result:
"the per-token draft-match probability is stable across draft depths, so the observed fall in the
acceptance *ratio* is definitional; the quantity that carries information about the drafter is q (or
`mean_accepted_len`, which the Wave-1 harness records and this one does not)."

Two arithmetic corrections to PN-32 while I am here. **The 13 "adjacent" pairs include two that are
not adjacent** — Q6_K_XL @131,072 and Q4_K_XL @196,608 each skip n=4, and their n=2→n=8 transitions
were counted as adjacent. There are **11 genuinely adjacent pairs, of which 10 fall**, giving a
one-sided sign-test p of **0.0059**, not 0.0017. And the invalid-cell count is 3, not 2 (24 − 21).
Neither changes the direction; both change a number that is printed.

### 3.4 Confounds nobody has named

- **`-ctxcp` recurrence check (requested).** PN-45 caught `-ctxcp 4` and `32` mixed in one Q6_K
  group. I checked every other grouped comparison in the corpus for the same defect. It does **not**
  recur: the S12 cells are uniformly `-ctxcp 32`; the S8/S9 arms are uniformly `-ctxcp 32`; the s9d
  cells are uniformly `-ctxcp 32`; the SSA `llama-perplexity` cells do not take the flag. The single
  `:ctxcp32` cell in `tsweep-v2-Q6_K.json` is the only instance and PN-45 has it. **Clean.** But
  note the second-order problem: the Track A configuration pins `-ctxcp 32` and README quotes
  **11.90 tok/s**, which is the median of three **`-ctxcp 4`** reps. The only `-ctxcp 32` reading at
  that configuration is 11.48, n = 1. The recommended configuration's headline throughput has never
  been measured three times at the setting it recommends.
- **Thinking mode is uncontrolled across instruments.** S8/S9a/S9b/S11 run `/completion` or explicit
  sampling; S12 runs `/completion` with thinking left on (D1); PN-2 established the control and it
  is applied in the validation battery and nowhere in the measurement batteries. The paper's own
  §3 will present PN-2 as a harness-validation *result*; a reviewer will then ask where it was
  applied. Answer that question before it is asked.
- **PN-28's sampling preset is a live confound and its variance component is unmeasured.** The
  generative anchor runs at DEC-2 official non-thinking sampling — temp 0.7, top_p 0.80, top_k 20,
  **presence_penalty 1.5** — with a **single sample per problem** and a single seed. The paired
  interval [−2.68, +1.46] treats the only randomness as *which* items are discordant. It ignores
  that a re-draw would produce a different discordance set entirely. This matters more than it
  sounds: under a model where both arms have identical per-problem success probability p_i and
  mean pass ≈ 0.94, the *expected* discordance from resampling alone would be
  2·Σp_i(1−p_i) ≈ 18 of 164 if the p_i were near 0.94 — six times the 3 observed. Observing 3
  implies the per-problem outcomes are nearly deterministic even at temp 0.7. That may well be true,
  but **the study cannot know, because it ran a determinism control for its greedy instruments
  (PN-26) and never ran one for the sampled instrument that is its only generative anchor.** A
  same-arm repeat of S9b at a second seed costs ~1.3 h and is the cheapest remaining experiment in
  the project. Until it is run, PN-40's bound rests on an unverified assumption, and PN-26 —
  the enabling result the insider notes correctly identify as load-bearing — does not cover it.
- **Seed diversity is effectively one.** `lib_e12.py` hard-codes `SEED = 20260830`; it appears in
  249 places across 39 artifacts. Seeds 20260831/32/33 appear 57/8/8 times (chain bookkeeping, not
  independent draws). RULER's *data generator* uses `--random_seed 42`, so the haystacks are one
  draw too. Crucially, **for every greedy instrument the seed is a no-op**, so "seed 20260830" is
  decoration on PN-13, PN-23, PN-26, PN-35, PN-38, PN-44 and every S-NIAH cell — its presence in
  those Evidence lines implies a robustness that does not exist. The seed is load-bearing in exactly
  three places (Wave-1 `tsweep`, S9b, S9d), all at temp 0.7, all n = 1 seed. **Every variance claim
  in this paper is a within-seed claim.** State it once, plainly, in Methods.
- **Prefix-cache reuse inside "repetitions."** Reps 2–3 of every multi-rep cell run against a warm
  KV cache (`cache_n` ≈ prompt length, `prompt_n` = 4). Prefill throughput differs by two orders of
  magnitude between rep 1 and reps 2–3 (782 vs 5.98 tok/s in the s9d cell I inspected), and
  generation lengths differ (415 vs 512 tokens). Pooling these into a "median of 3" mixes three
  different measurements.

---

## 4. Construct validity

### 4.1 Does KL divergence on next-token distributions measure what the paper says it measures?

Partly, and the gap matters more than the caveat admits.

`llama-perplexity --kl-divergence` computes, per token, the divergence between the reference model's
and the test model's **next-token distribution conditioned on the true prefix**. This is
teacher-forced. It measures *pointwise distributional agreement under an oracle context*. The paper
uses it as a proxy for "quantization damage" to a **coding agent**, which is a system that
(a) conditions on its own outputs, (b) runs for thousands of tokens, and (c) is scored on whether a
trajectory reaches a goal.

The gap between those constructs is not a caveat, it is the paper's central open question, and
PN-38 is the study's own evidence that it is unbridgeable with the tools to hand: free-running
generation forks within 2–126 characters, so no trajectory-level distance is measurable. The paper
should own this as its principal limitation and its principal call for future work, rather than
listing it third in threats-to-validity.

Two narrower construct problems:

- **"Damage" is the wrong word for a symmetric-looking quantity.** KL(ref ‖ arm) measures
  *difference from a 6-bit reference*, not *loss relative to ground truth*. The reference is itself
  quantized and its own error is 0 by construction (see §4.2). Whenever the paper writes "damage" it
  is asserting a direction the instrument does not supply. "Divergence" is what was measured and is
  a perfectly good word.
- **The code corpus is a memorisation probe.** 0.240 bits/token on path-sorted django is not
  "generic code" — it is text the model has effectively memorised. Every domain claim in the paper
  is therefore, strictly, *prose vs memorised-code*, and the tail structure of §D2 is what
  memorisation looks like. `corpus-manifest.json` says most of this already; the paper must say it
  in the results section, not the appendix, and preferably alongside a second corpus.

### 4.2 The reference arm: which claims are invariant, formally

The mandate asks for a formal answer. Here it is.

Write D(A) = mean KL of arm A from the reference R = UD-Q6_K_XL, and let δ = the reference's own
(unmeasured) divergence from FP16 on the same corpus.

**Claim 1 — the arm ordering (PN-13). INVARIANT.** To first order, adding the reference's own error
contributes a common non-negative offset to every arm on a given corpus, and a strictly increasing
series remains strictly increasing under addition of a constant. Under the second-order
(Fisher-metric) approximation KL(A‖R) ≈ ½(θ_A−θ_R)ᵀF(θ_A−θ_R), the arms lie approximately along a
ladder and R sits at one end, so the ordering is preserved whether the true origin is collinear with
the ladder or orthogonal to it. **The ranking survives the reference choice and the paper can say so
with an argument rather than a hope.** The insider notes' intuition here is correct; it just needs
writing down.

**Claim 2 — the code/prose ratio (PN-14, "code is ~2× prose"). ROBUST.** Applying the study's own
domain amplification to the reference's own error (δ_code = 1.76·δ_prose) and sweeping δ_prose:

| δ_prose | code/prose ratios (Q6_K, Q5, Q4) | widening (Q4 − Q6) |
|---|---|---|
| 0 (as reported) | 1.755 · 2.303 · 2.623 | **0.868** |
| 0.0008 | 1.756 · 2.221 · 2.547 | 0.790 |
| **0.0016** (Unsloth's cited Q6_K_XL KLD) | 1.757 · 2.160 · 2.482 | **0.726** |
| 0.0032 | 1.758 · 2.077 · 2.381 | 0.624 |
| 0.0128 | 1.759 · 1.901 · 2.097 | 0.338 |

The *level* is rock-solid: the Q6_K ratio moves by 0.004 across a 16-fold sweep.

**Claim 3 — "and the gap widens as quantization gets more aggressive" (PN-14, second clause,
contribution 2 of the outline). NOT INVARIANT.** At the most plausible δ the widening shrinks by
16 %, and in the limit of a large reference error every arm's ratio converges to the reference's own
domain amplification and the widening vanishes entirely. The direction of the bias is systematic —
adding a common offset to numerator and denominator pulls all ratios toward the offset's own ratio —
so the reported widening is an **upper bound**, not an estimate. The paper must present it that way.
The same argument applies to PN-21's 3.13 → 3.87 → 4.40 prose-to-task amplification (which under
δ = 0.0016 becomes 3.13 → 3.68 → 4.19).

**Claim 4 — PN-35's tail quantiles. INVARIANT, and that is the problem.** Because the normalised
tail shape is perturbation-invariant on a given corpus (§D2), adding the reference's own error
contributes a distribution of the same shape, and the quantile ratios are approximately preserved.
So PN-35 is the *most* reference-robust claim in the paper — for exactly the reason that makes it
not a claim about quantization. That is worth a sentence in the paper: the property that protects
the tail result from the reference-arm criticism is the property that undermines its attribution.

**Claim 5 — PN-15's "51 % of a quantization level". NOT INVARIANT, and PN-43 half-fixes it.** PN-43
correctly retreats from additivity to "a comparison of sizes." But the denominator (0.005829) is
itself ladder-relative and would grow by δ under correction, while the numerator (a KV-dtype
divergence measured against the same reference) would not. At δ_code = 0.0028 the ratio falls from
51 % to **34 %**. Report it as a range, or report the two divergences side by side and let the
reader form the ratio.

### 4.3 Does the RULER result generalise beyond retrieval?

No, and after D1 the question is moot for the current analysis. But the framing point stands for
whatever replaces it: synthetic needle retrieval measures *whether a specific span survived the
attention path*, which is close to the weakest possible long-context capability. RULER's own paper
exists precisely because NIAH over-reports. The paper runs 2 of RULER's 13 tasks, excludes one of
those, and reports zero of the QA and aggregation categories. A single retrieval variant at a single
length cannot support any statement about "long-context behaviour", and PN-44's caveat says so —
that caveat should be promoted into the claim sentence.

### 4.4 Is the greedy / official-sampling split defensible?

**Yes, and the paper defends it badly.** The defensible version:

- Logprob instruments (KLD, PPL) require teacher forcing; sampling is irrelevant to them by
  construction. Calling them "greedy" is a category error the paper repeats — there is no decoding
  happening. Fix the wording.
- Equivalence instruments (PN-23/26) *must* be greedy, because a stochastic decoder makes byte
  comparison meaningless. Correct, and correctly caveated as greedy-only (G8).
- Task instruments at the official preset (PN-28) are the right choice for external comparability,
  and were correctly run no-spec on both arms to avoid PN-23's confound. Good design.
- **The unjustified case is S12.** RULER runs greedy while the model's documented setting is
  temp 0.7, *and* with thinking on, which is neither preset. That is a fourth configuration, exactly
  the hazard PN-1 was written to warn about, and it is the configuration behind the paper's
  long-context number.

So the split is defensible for three of four instrument families and undocumented for the fourth.
And the meta-point the paper should make and does not: **it ran benchmarks under four distinct
sampling configurations (measured engine default, DEC-2 official, greedy, and greedy-with-thinking),
and the reason absolute scores in this literature are incomparable is that everyone does this and
nobody reports it.** That is a stronger version of PN-1 than PN-1 currently makes.

### 4.5 A free re-analysis that improves the paper's most novel result

PN-23 reports that MTP reproduces no-spec on 131/164 problems — "roughly one generated function in
five." That framing does not transfer to any other workload. From `s8-{nospec,mtp2,mtp4}.jsonl`,
already committed:

| | baseline completion length (chars), median | divergence rate by baseline-length quartile |
|---|---|---|
| identical problems (n=131) | **590** | Q1 (<469 ch) **2.4 %** |
| divergent problems (n=33) | **1286** | Q2 **4.9 %** · Q3 **19.5 %** · Q4 (>994 ch) **53.7 %** |

Divergence is strongly length-dependent, and the n=4 arm reproduces the pattern (2.4 / 2.4 / 26.8 /
48.8 %). A constant-hazard MLE with right-censoring gives **h ≈ 3.0 × 10⁻⁴ per character ≈ one
divergence per ~930 generated tokens** — and the fit is *poor in an informative direction*: observed
rates are below prediction at short lengths and above it at long ones, i.e. **the hazard rises with
position.** A verification-rule error would produce a hazard flat in position. Progressive numerical
drift in a diverging KV cache would produce exactly what is observed.

Two consequences:

1. **PN-23 should report a rate, not a proportion.** "One function in five" is a fact about
   HumanEval+'s output-length distribution. "Roughly one divergence per thousand generated tokens,
   rising with position" is a fact about the stack, and it transfers: on an agentic trajectory of
   10k tokens, essentially every trajectory diverges. That is the practitioner sentence the paper
   is missing, and it connects directly to the compounding question.
2. **PN-26's withdrawal of the numerical account was premature.** Reviewer A argued this logically
   (a different reduction order under a different batch shape is itself deterministic). The
   length-dependent hazard is *positive* evidence for it. PN-26 should be amended to say the
   determinism control excludes run-to-run nondeterminism and does **not** exclude deterministic
   numerical divergence, and that the position-dependence of the hazard favours the latter.

---

## 5. Related work

The bib has 48 entries, all internally consistent (I checked every arXiv ID's year prefix against
its claimed year; none is anomalous), with genuinely good provenance discipline — self-flagged
UNVERIFIED markers, sha256-pinned dataset artifacts, and a correction round on R5 and R12. That is
better than most.

But the coverage map has a hole a domain reviewer will find in thirty seconds.

### 5.1 There is not one peer-reviewed quantization paper in the bibliography

Every quantization-methods citation is a vendor blog, a vendor doc, or a community post:
`unsloth_dynamic3`, `unsloth_qwen38_gguf`, `nvidia_nvfp4`, `fireworks2024quantization`,
`localbench2026gguf`, `kalomaze2023ppl`. **Absent:** GPTQ (Frantar), AWQ (Lin), SmoothQuant (Xiao),
LLM.int8() (Dettmers), SpQR, QuIP, OmniQuant, ZeroQuant, Atom, OWQ, and Dettmers & Zettlemoyer's
k-bit inference scaling laws / "The case for 4-bit precision" — the last of which is the single most
obvious omission, because it is the canonical empirical study of exactly this trade-off.

For a paper whose title contains the word "quantization", this is a first-order problem. It is also
easy to fix: three paragraphs of §2 and eight entries.

### 5.2 There is no KV-cache quantization literature at all

`q4_0` KV is load-bearing for **every** context ceiling, speed figure and long-context result in the
study, and PN-15 is an entire section about it. **Absent:** KIVI, KVQuant, GEAR, and (per reviewer
B's find) QLLM-Eval, which reports that at ≥4K context most LLMs are *more* sensitive to KV-cache
quantization than to weight quantization at the same bit-width. That last one does not just belong
in related work — it makes PN-15's "measured at n_ctx 2048" caveat a live threat rather than a
formality, and the paper should say so itself.

### 5.3 The compression-behaviour lineage is one citation deep

`dutta2024accuracy` is present and correctly promoted by PN-37. Its ancestors are not: **Hooker,
"What Do Compressed Deep Neural Networks Forget?"** is the origin of the "compression damage is
concentrated in a subpopulation and invisible to top-line accuracy" argument, and this paper's
entire tail story is that argument at token granularity. **Jaiswal, "Compressing LLMs: The Truth is
Rarely Pure and Never Simple"** is the LLM-era restatement. **Kurtić et al., "Give Me BF16 or Give
Me Death?"** is absent while the same author's *blog post* is cited — a reviewer who knows the field
will read that as citing the accessible source over the peer-reviewed one.

Also absent and expected: **Liu, "Lost in the Middle"** and **Kamradt's needle-in-a-haystack**, both
required background for any MK-NIAH result; **MMLU**; and every multiple-comparison reference
(Bonferroni/Dunn, Holm, Benjamini–Hochberg), which §2.1 now makes necessary.

### 5.4 Novelty: what is new, what is confirmation, what is neither

PN-37 already does most of this honestly. My adjudication, after the analysis above:

| contribution | verdict |
|---|---|
| **Divergence separates quantizations that task benchmarks cannot** | **Independent confirmation** of Dutta et al. (NeurIPS 2024), on a different model family, compression scheme and hardware class, across three instrument classes. Worth publishing as confirmation; PN-37 credits it correctly and the paper must keep doing so in the abstract, not only in §2. |
| **Domain dependence: code diverges ~2× prose, and the task distribution more still** | **Novel in this form**, and the strongest surviving empirical claim in the paper. I could not find prior work making the domain comparison directly, and reviewer B could not either. Say "we are not aware of a published measurement of this asymmetry" — that is a stronger position than silence. Caveat with §4.1's memorisation problem. |
| **Tail structure (PN-35)** | **Neither, as currently framed.** The *measurement* is novel; the *attribution to quantization* fails its own internal control (§D2); and the general claim "the average of a compression-damage distribution hides its shape" is Hooker's, at a different granularity. Reframe as "the corpus decides where divergence lands" and it becomes novel again. |
| **Deterministic non-equivalence of speculative decoding, with a self-repeat control** | **The most novel single result in the paper**, and it is buried at §5.4. Reviewer B found a prior llama.cpp issue reporting the phenomenon (priority: not first), but the *characterisation* — byte-level self-reproduction on both arms, partially-overlapping divergence sets with Jaccard 0.610, and (new, §4.5) a position-dependent per-token hazard — is nobody else's. Lead with it more than the outline does. |
| **The context ceiling is a property of the tensor split** | **Novel and practitioner-valuable**, correctly scoped by PN-39 to two of four arms. Zero statistical exposure (load / no-load). This will be the most-cited result in the paper. |
| **The reproducibility register** | **Novel as a genre contribution.** Six instrumentation defects, each with a stated rule, each preserved rather than deleted. If §D1 is disclosed in the paper's own voice it becomes seven, and the register becomes the most persuasive thing in the document. |
| **Long-context retrieval (PN-44)** | **Currently not a contribution** (§D1). Re-analysed as an output-budget result it becomes a small novel one that nobody else reports. |

**Against Dutta et al. specifically:** the paper's defensible novelty claim is *not* "accuracy hides
compression damage" — it is (i) the domain axis, (ii) the systems axis, and (iii) the equivalence
axis. State that in the introduction's second paragraph, exactly as PN-37 instructs, and the
priority objection is dead on arrival.

---

## 6. Threats to validity — a full draft

The section is unwritten. Here is a draft to write against. I have ordered it by what a reviewer
will actually attack, not by topic, and every item names the artifact that bounds it.

**1. The reference arm is quantized, and all divergence is ladder-relative.**
No FP16 or BF16 reference fits this host (54.7 GB against 2× 16 GB VRAM and 14 GiB system RAM), so
every divergence is measured against UD-Q6_K_XL, whose own distance from the unquantized model is
unmeasured and zero by construction. The arm *ordering* is invariant to this choice: adding the
reference's own error contributes a common non-negative offset per corpus, and a monotone series
stays monotone. The *level* of the code-to-prose ratio is likewise robust (it moves by 0.004 across
a sixteen-fold sweep of plausible reference error). What is **not** invariant is the claim that the
code-to-prose gap widens with quantization aggressiveness: under a reference error equal to
Unsloth's published figure for this arm the widening shrinks by 16 %, and in the limit it vanishes.
We therefore report that widening as an upper bound.

**2. The code corpus is highly predictable and probably memorised.**
The code domain is a path-sorted, non-deduplicated django tree (`corpus-manifest.json`,
sha256 `049d12ef…`, 9,097,163 B) on which the reference model achieves 1.1809 perplexity —
0.240 bits/token, against 2.534 for WikiText-2. This is among the most-trained-on Python in
existence. Every "code" claim in this paper is strictly a claim about *this* corpus, and the shape
of its per-token divergence distribution (median 1,266× below the mean) is what a
memorisation-saturated corpus produces. A second, held-out code corpus is the single most valuable
missing measurement in the study and would cost approximately one GPU-hour.

**3. The shape of the divergence distribution is set by the corpus, not by the perturbation.**
Normalising each cell's quantiles by its own mean shows that the tail concentration we report on
code (p99/mean 24–26) is reproduced almost exactly by a perturbation that is not weight
quantization at all — changing only the KV-cache dtype on the reference arm gives p99/mean 22.9 on
the same corpus, against 8.4–8.6 for weight quantization on prose. We therefore do not claim that
*quantization* damage is tail-concentrated; we claim that *this corpus* concentrates any
distributional perturbation into its tail, which is itself the reason single-corpus quantization
tables do not transfer.

**4. Divergence intervals assume token-level independence that the design does not provide.**
The tool's `±` is a per-token Gaussian standard error over 65,536 tokens drawn from 32 contiguous
2,048-token windows of one document (9 windows for the task domain). We estimate no
intraclass correlation and cannot, because the per-token `.kld` files were not retained. Under a
design effect of only 1.5 — ICC ≈ 0.00024 — the weakest separation we report (UD-Q6_K vs
UD-Q5_K_XL on prose, 3.71 σ) fails a Bonferroni correction over this paper's nineteen tests. The
remaining eight separations require design effects of 7.5–36 to fail. We therefore quote the
code-domain separations (8.7–18.1 σ) as the paper's ranking evidence and do not claim the prose
adjacency.

**5. Multiple comparisons.** This paper reports nineteen inferential tests. All eleven positive
results survive Holm and Benjamini–Hochberg at α = 0.05 over the full family; the table is in
Appendix C. Separately, we distinguish confirmatory analyses fixed before the data (the SSA
divergence protocol under DEC-11; the MK-NIAH paired analysis, whose script was committed before
the second arm finished) from exploratory analyses selected after inspection (everything else),
and we report the latter with intervals and without significance claims. The escalation of MK-NIAH
from n = 12 to n = 100 was itself prompted by the pilot, and its confirmatory sample re-uses the
pilot's twelve items; the result is unchanged on the 88 fresh items (−10.23 points, 9 discordant,
all one-directional, p = 0.0039).

**6. Every variance claim is a within-seed claim.** One server seed (20260830) is used throughout,
and one data-generation seed (42) for RULER. For the greedy instruments — divergence, equivalence,
determinism, retrieval — the seed is a no-op and its presence in a protocol line implies a
robustness we did not test. For the three sampled instruments (the Wave-1 throughput sweep, the
generative HumanEval+ anchor, the draft-depth sweep) we ran one seed, so sampling variance is
confounded with everything we report from them. We ran a byte-level determinism control for the
greedy path (PN-26) and none for the sampled path.

**7. Throughput variance is partly an uncontrolled sampling artifact, not host noise.** The Wave-1
speed cells run under official sampling, so the generated continuation differs between repetitions;
draft acceptance is a property of that continuation (it is identical across every tensor-split ratio
at a fixed repetition index), and decode throughput regresses on acceptance with R² = 0.83.
Conditioning on acceptance reduces within-configuration spread from 16.7–40.7 % to 2.6–11.0 %. Our
conclusion that decode does not discriminate the arms is unchanged, but the noise floor we quote is
an upper bound and a greedy re-measurement would tighten it substantially.

**8. Prompt-token divergence is not generation quality, and we could not bridge the gap.**
Divergence is measured under teacher forcing. Our attempt to measure distance on emitted
trajectories (S11) failed on its own evidence: greedy generation forks within 2–126 characters and
every pairwise distance saturates. We therefore report a bound relating the two instruments — a
3.69× increase in code-prompt divergence moves HumanEval+ pass@1 by at most about 3 points — and
not a translation between them.

**9. The generative anchor's interval omits a variance component.** PN-28's paired interval treats
the discordance set as the only source of randomness. Single-sample pass@1 at temperature 0.7 adds
a second component that we did not measure, and that a same-arm repeat at a second seed (≈1.3 h)
would bound.

**10. Long-context accuracy is measured on one synthetic retrieval variant, at one length, under a
fixed output budget that binds.** [Rewrite per §D1 once the re-analysis is done. At minimum: two of
RULER's thirteen tasks were run, one of those excluded, and the retained task's 128-token generation
budget was exhausted on 23 % of reference and 40 % of 4-bit generations, so the scored outcome
conflates retrieval with reasoning length. On the 55 items where the budget bound neither arm, both
scored 55/55.]

**11. Speculative-decoding results are greedy-only and stack-specific.** Non-equivalence is measured
on emitted text for one quantization, one context length, one engine image and one drafter
(llama.cpp's built-in MTP head). A temperature > 0 equivalence test was not affordable. The DFlash2
arm ran on a different engine build and its equivalence figure is engine-confounded and is never
quoted beside MTP's. We do not claim that any other implementation's losslessness claim is false; we
claim that losslessness is a property to verify per stack.

**12. Ceiling failures are single attempts.** This project's own bracketing rule requires a failed
rung to be attempted twice, because layer-split VRAM carries ±100–200 MiB of noise. Four
load-failure claims rest on one attempt each: UD-Q5_K_XL at the default split at 262,144;
UD-Q6_K at `-ts 54,46`; DFlash2 at 262,144 and 212,992. Re-testing costs roughly twenty minutes and
was not done.

**13. Energy is modelled, not measured.** There is no wall-socket instrumentation on this host.
`est_system_w` is GPU telemetry plus RAPL package power plus a fixed platform allowance; only the
GPU and CPU-package limbs are instrumented. No per-configuration J/tok figure exists; the historical
table is depth-0 and from a deleted engine image.

**14. The GGUF KL-divergence comparison table is cited, not measured.** Per-quant KLD figures for
the Unsloth ladder are read from published figures, not reproduced here, and the imatrix calibration
data for these GGUFs is not published in detail, so a calibration-favourable bias toward
Wikipedia-like text cannot be excluded — which is itself an argument for weighting the code domain.

**15. Absolute scores are not comparable to published numbers.** Logprob instruments are
teacher-forced; the equivalence and retrieval instruments run greedy; only the generative anchor
runs at an official preset. Qwen publishes LiveCodeBench v6, SWE-bench **Pro** and Terminal Bench
for this model and no HumanEval at all; none of the three is set up on this host.

**16. One model family, one engine image, one host, one operator.** The historical corpus
(pre-2026-08-29) came from an engine image that no longer exists and is labelled
*irreproducible-on-current-images* throughout. Nothing here is a claim about quantization in
general; it is a claim about what a careful measurement of one ladder on one machine can and cannot
establish, and about which instrument answers that question at what cost.

**17. The artifact release is incomplete by design.** Server logs (72 cited, 0 released), the code
corpus, the reference logit files, the generated pads and eight of eleven quarantined artifacts are
excluded for size or licensing. We claim only ACM's *Artifacts Available* badge and explicitly not
*Functional*, because completeness is a Functional criterion this release does not meet.

**18. The compounding question is unmeasured, and it is the one that matters.** Every instrument
here scores a single turn. Whether damage confined to a small fraction of token positions compounds
over a long-horizon agentic trajectory — where a model makes thousands of decisions and each is a
draw from a perturbed distribution — is unmeasured, including by us. Our own speculative-decoding
hazard estimate (~1 divergence per 10³ generated tokens, rising with position) suggests the answer
is not obviously "no", and it is the natural next experiment.

---

## 7. Title proposals

Ranked by defensibility. The study has corrected nine of its own notes and my analysis puts a tenth
correction in front of it, so a title that over-commits to the newest result is the largest
avoidable liability in the submission. **The current working title —
"Quantization Damage Lives in the Tail" — commits the paper's first five words to precisely the
claim §D2 attacks, on a result that is eight days old and has one internal control that contradicts
its attribution.** That title should not survive this round. Note also that `CITATION.cff` has
already adopted it, so the fix has to reach two files.

---

**T1 — recommended.**
> **What a Quantization Ladder Costs, and Which Instrument Can Tell You: a measurement study of a 27B coding model on two consumer GPUs**

*Commits to:* that a ladder was measured; that instruments differ in what they can resolve; that
the setting is consumer hardware.
*Costs:* modest. It is descriptive rather than assertive and will not go viral.
*Survives:* every single finding being qualified. There is no result whose retraction falsifies it —
if the tail attribution goes, if MK-NIAH is re-analysed, if the domain widening is an upper bound,
the title is still exactly what the paper does. It also correctly signals a measurement paper to a
systems reviewer, which is the venue where this belongs.

**T2 — the strongest assertive title I would defend.**
> **Divergence Ranks What Benchmarks Bound: quantization, context and speculative decoding for a 27B coding model on two 16 GB GPUs**

*Commits to:* the ranking/bounding contrast (PN-13 vs PN-22/28/40), and to three result areas.
*Costs:* "ranks" leans on the divergence separations, so the clustering objection (§2.1a) must be
answered in the paper — which it should be anyway. Credits Dutta implicitly rather than explicitly,
so §1 must do that work.
*Survives:* the tail retraction entirely; the MK-NIAH re-analysis entirely (a re-analysed MK-NIAH
still *bounds*, and in one decomposition *separates*); the reference-arm objection (ranking is
invariant, §4.2).

**T3 — systems-forward.**
> **The Ceiling Belongs to the Split: context, quantization and speculative decoding on two 16 GB GPUs without NVLink**

*Commits to:* PN-6/PN-7/PN-39 as the lead.
*Costs:* buries the paper's methodological contribution and invites the (correct) scoping objection
that it holds for two of four arms; a reviewer who reads PN-39 will feel the title over-claims.
*Survives:* every accuracy finding being qualified — this is the most measurement-robust result in
the corpus (load/no-load, no interval). Good insurance title; wrong emphasis.

**T4 — methods-forward, honest about the negative results.**
> **Instruments Before Answers: what three task benchmarks and one divergence measurement can establish about a quantization ladder**

*Commits to:* the instrument-comparison framing only.
*Costs:* reads as a survey; understates real positive results (the split, the equivalence result).
*Survives:* everything. This is the safest title in the list and I would accept it without argument.

**T5 — leads with the most novel single result.**
> **Speculation Is Part of the Accuracy Configuration: deterministic non-equivalence, quantization divergence, and context ceilings on a two-GPU host**

*Commits to:* PN-23/PN-26, which are the best-verified results in the corpus (I reproduced the
byte-identity and the Jaccard 0.610 independently).
*Costs:* priority — a prior llama.cpp issue reports the phenomenon, so §2 must credit it; and the
result is one quant, one context, one image.
*Survives:* the tail retraction, the MK-NIAH re-analysis, the reference-arm objection, and
clustering — none of them touch a byte-comparison.

**T6 — the domain claim, scoped.**
> **Prose Flatters Quantization: domain-dependent divergence in a 27B coding model, and what task benchmarks can bound**

*Commits to:* PN-14/PN-21 as the lead — the strongest surviving empirical claim.
*Costs:* exposed to §4.1's memorisation problem (the "code" corpus is 0.24 bits/token) and to
§4.2's finding that the *widening* clause is an upper bound. Both are answerable in the paper; the
title survives either way because it claims the level, not the trend.
*Survives:* the tail retraction and the MK-NIAH re-analysis.

**T7 — the cost/power framing.**
> **Two Hours of Divergence, Five Hours of Benchmarks: measuring a quantization ladder when GPU time is the binding constraint**

*Commits to:* PN-41's corrected cost contrast.
*Costs:* the ratio is only ~2.2× on the authors' own accounting (or ~5× on reviewer B's wider
accounting), which is a weak hook; and it invites "so what?" from a reader with a cluster.
*Survives:* every technical claim. But it sells the paper as an anecdote about one machine.

**T8 — the practitioner title.**
> **Which GGUF for a Coding Agent on 2× 16 GB? a measured answer and the measurements that do not support one**

*Commits to:* Track A's deliverable, honestly hedged.
*Costs:* the paper explicitly refuses to inherit Track A's priority ordering, so this title fights
the paper's own structure; also invites "one host, n=1".
*Survives:* everything; it is a title about a decision procedure.

**T9 — assertive, high-risk.**
> **Accuracy Is Still Not All You Need: independent confirmation, and the domain and tail structure the mean hides**

*Commits to:* an explicit relationship to Dutta et al., which neutralises the priority objection in
the title itself — a genuinely clever move.
*Costs:* it announces "we are a confirmation paper", which some reviewers read as low novelty; and
it commits to the tail structure, which §D2 attacks.
*Survives:* the priority objection completely. Fails the D2 objection.

**T10 — the register as the contribution.**
> **Silent Success: six ways an automated benchmark reported numbers it had not measured, and what they cost a quantization study**

*Commits to:* Appendix B as the lead, which is a real and unusual contribution.
*Costs:* it is not a quantization paper any more, and the measurement results become supporting
material. A different (probably smaller) audience.
*Survives:* everything, trivially — but only if §D1 is included as the seventh instance, which
would be a remarkable and self-serving-in-the-right-way move.

---

### Ranking and defence of the top choice

**T1 > T2 > T4 > T6 > T5 > T3 > T9 > T8 > T10 > T7.**

I would submit under **T1**, and here is the argument.

This paper's demonstrated failure mode — nine times over, and a tenth in §D1 — is that its
strongest-sounding claim at any given moment turns out to be the one that moves. PN-19's noise
figure moved twice. PN-34's saturation mechanism lasted eight hours. PN-33's MK-NIAH lasted a day.
PN-35 is four days old and is the current lead. A title is the one sentence that cannot be amended
by a paper note, and it will be read by people who never open the appendix. Under those conditions
the correct discount rate on the newest result is very high.

T1 has three properties nothing else in the list has together: it is true under every combination of
the qualifications above; it accurately describes a *measurement study*, which is what this is and
what its venue should be; and it names the two things a reader actually searches for — the ladder
and the hardware. The paper's own most interesting sentence — *the instrument you choose decides
whether there is anything to see* — is in the subtitle's "which instrument can tell you", where it
costs nothing if a single result is qualified.

If the authors want more assertion than that, **T2** is the most I would sign off on, and only after
the chunk-level intervals in §2.1a are computed. If the MK-NIAH re-analysis (§D1) is done and comes
back as I predict, T2 becomes clearly correct and I would prefer it.

---

## 8. Abstract proposals

All three are ASCII-clean and within arXiv's 1,920-character limit. Numbers are annotated with their
source; the annotations are for the authors and come out before submission.

---

### A1 — conservative (212 words, 1,328 chars net of annotations). Survives every objection in this review.

> Quantization tables for locally served language models are published on prose corpora and
> validated on task benchmarks. We measure a 27B coding model across four llama.cpp GGUF
> quantizations on two consumer 16 GB GPUs and ask which instrument can answer which question.
> Measuring KL divergence against the least-quantized available arm over 65,536 tokens per domain,
> the arms separate monotonically on a Python corpus at 8.7 to 18.1 sigma [PN-13, code domain only],
> and divergence on code is roughly twice that on prose [PN-14: 1.76x/2.30x/2.62x]. Three task
> benchmarks spanning multiple choice, unit-tested generation and long-context retrieval bound the
> ladder-wide effect rather than resolving it: on the closest instrument to the target workload the
> two extremes agree on 161 of 164 problems, giving a paired difference of -0.61 points with a 95%
> interval of [-2.68, +1.46] [PN-40]. We report the minimum effect each instrument could have
> detected, which for two of the three was larger than any effect they could have found. We also
> report that the usable context ceiling on this host is set by GPU tensor placement rather than by
> quantization for two of four arms [PN-6/PN-39], and that speculative decoding on this engine is
> deterministically non-equivalent to unspeculated decoding, reproducing it on 131 of 164 problems
> at temperature zero while reproducing itself byte-exactly [PN-23/PN-26]. All artifacts released.

---

### A2 — balanced (249 words, 1,555 chars net of annotations). My recommendation, assuming §D1's free re-analysis is done.

> Quantization quality for locally served models is published on prose corpora and certified on task
> benchmarks. We measure a 27B coding model across four llama.cpp GGUF quantizations on two consumer
> 16 GB GPUs, and find that the instrument decides whether there is anything to see. KL divergence
> against the least-quantized available arm, over 65,536 tokens per domain, separates every adjacent
> pair on code at 8.7-18.1 sigma [PN-13] and is roughly twice as large on code as on prose, rising
> again to 3.1-4.4x prose on the benchmark's own prompts [PN-14, PN-21]. Against a published quality
> threshold, two of three arms pass on prose, one on generic code, and none on the task
> distribution. Three task benchmarks -- multiple choice, unit-tested generation, and long-context
> retrieval -- bound the whole ladder's effect at about three points of pass@1 and cannot resolve
> below it [PN-40]; for two of them, no outcome could have reached significance at the discordance
> rates observed. The divergence distribution explains why: on this code corpus the median token is
> perturbed 100-200x less than on prose while the top percentile is perturbed 5-8x more [PN-35] --
> a shape we show is set by the corpus rather than by the compression, since changing only the
> KV-cache dtype reproduces it [PN-15]. We also report that GPU tensor placement rather than
> quantization sets the reachable context window on this host, and that speculative decoding is
> deterministically non-equivalent to unspeculated decoding at a rate that grows with generation
> length. Artifacts and the full measurement record are released.

---

### A3 — assertive (219 words, 1,380 chars net of annotations). What I suspect the authors want to write. I would not accept it as-is.

> The instruments the field uses to certify quantized models cannot see the damage they certify
> against. We measure a 27B coding model across four GGUF quantizations on two consumer 16 GB GPUs.
> KL divergence separates every arm at 3.7-11.8 sigma in two hours of GPU time; five hours of task
> benchmarking across three instrument classes separates them nowhere [PN-13, PN-41]. The reason is
> structural: quantization damage to code lives in the tail. At the median, code tokens are
> perturbed 100-200x less than prose tokens; the ordering reverses between the 90th and 95th
> percentile; by the 99th, code is perturbed 5-8x more [PN-35]. Benchmarks score outcomes, not
> tokens, so a perturbation confined to 1-5% of positions changes an outcome only when a tail token
> lands somewhere decisive -- which quantitatively predicts the 3-of-164 and 5-of-164 discordances
> we observe. Only at 131,072 tokens on multi-key retrieval, where the reference model itself fails
> 11% of the time, does a task benchmark separate the arms at all: 89.0 against 79.0, paired
> difference -10.0 points, exact McNemar p = 0.0020 [PN-44]. We further report that the usable
> context ceiling is a property of GPU tensor placement rather than of quantization, and that
> speculative decoding is deterministically non-equivalent to unspeculated decoding. A
> divergence-first protocol ranks a quantization ladder at a fraction of a task battery's cost.

**Which I would accept as a reviewer: A2** — and A1 without argument. A2 is the only one of the
three that states the tail finding *and* its own control, which converts the paper's most attackable
claim into a demonstration of care. It also drops the "3.7 sigma" lower endpoint that does not
survive §2.1a.

**Which I suspect the authors want: A3.** It is the most quotable and it is the shape of the
project's internal narrative. It also contains three claims this review disputes — the 3.7 sigma
endpoint, the causal attribution of the tail, and the MK-NIAH sentence — and one it does not
(the cost contrast, which PN-41 already corrected honestly and which A3 states correctly at 2 h
vs 5 h). If A3 goes out unchanged, the MK-NIAH sentence is the one a reviewer will pull, because it
is the newest, the most specific, and the easiest to falsify from the released predictions in about
ten minutes.

---

## 9. The single sentence

> **Your headline long-context result is that the four-bit arm more often failed to finish speaking inside a 128-token budget: on the 55 of 100 items where neither arm's budget bound, both arms retrieved the needle 55 times out of 55, not one wrong answer in either arm came from a model that had finished reasoning, and you excluded RULER's other task from this very battery for exactly this defect.**

---

## Appendix — recomputation log

Everything above was recomputed from the committed artifacts. Confirmed as stated:
PN-44's contingency table (79 / 10 / 0 / 11), exact McNemar p = 0.0019531, paired difference
−10.00 [−15.88, −4.12], Wilson [81.37, 93.75] and [70.02, 85.83], recovery 88.76 %;
PN-35's entire quantile table to four decimals; PN-13's sigma separations (3.71 / 8.48 / 8.67 /
11.82, plus non-adjacent 13.48 / 18.13 / 16.10);
PN-14's ratios (1.7552 / 2.3035 / 2.6232); PN-26's byte-identity (164/164 on both self-repeats) and
the divergence sets (33 / 33, 25 shared, Jaccard 0.6098); PN-45's corrected speed table
(12.70 / 11.90 / 11.71 medians, 16.7 / 28.6 / 40.7 % spreads, 6.74 % between-arm span);
PN-40's paired intervals; `CITATION.cff` against `cff.json`.

Recomputed and found to differ from the prose:
PN-32's "13 adjacent pairs" (11 are adjacent; 10 fall; p = 0.0059 not 0.0017) and its
"two invalid cells" (three);
PN-22's chi-square p-values against the exact test (0.4795 → 0.5000; 0.1336 → 0.1250);
PN-35's median-ratio row (0.005× / 0.006× / 0.005×, reported as 0.01× / 0.01× / 0.005×, and the
"100-200x" range is 181-206x).

New quantities introduced here: the MK-NIAH truncation decomposition (§D1); the normalised-shape
invariance table and its KV-only control (§D2); the Holm/BH table over all 19 tests and the
design-effect sensitivity table (§2.1); the minimum-attainable-p / MDE table (§2.2); the
decode-on-acceptance regression, R² = 0.827, and acceptance-adjusted spreads (§3.1); the per-token
draft-match probability q backed out of every s9d cell (§3.3); the reference-arm sensitivity sweep
(§4.2); and the length-dependent speculative divergence hazard (§4.5).
