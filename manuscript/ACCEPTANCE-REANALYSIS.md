# The acceptance-conditioned speed re-analysis

*Blocking item 9 of `OUTLINE-V2.md` §7.3. Written 2026-09-04 from committed artifacts only; no GPU
time, no containers, no new measurement. Every number below is recomputed here from
`data/raw/e12/tsweep-v2-*.json` and `data/raw/e12/s9/s9d-depthsweep.json`, and the reconstruction
script is reproduced in Appendix A so any reader can re-derive them.*

---

## 0. What was asked, and the short answer

Two blind reviewers independently observed that the decode-throughput variance this study has called
"unexplained noise" through three correction passes (PN-19 → PN-36 → PN-45) tracks draft acceptance,
and reported it as a regression: reviewer D at r² = 0.827 with within-configuration spread falling
from 16.7–40.7 % to 2.6–11.0 %, the figure-programme agent at r² up to 0.99 with a cost model
`t_pass = 65.1 ms + 0.476 µs × depth`. `OUTLINE-V2.md` §6.7, `TABLES.md` T12 and
`FIGURE-PROGRAMME.md` F12 all already lean on those figures, and no paper note carries them.

Three findings, in order of how much they change the paper.

1. **The regression is an algebraic identity, not an empirical result.** Under llama.cpp's MTP
   verification loop, `decode_tok_s = (1 + n_draft × acceptance) / t_pass`, where `t_pass` is the
   wall time of one target forward pass. Reconstructed over **97 measurements from two independent
   batteries**, the identity holds to a maximum relative error of **1.0 × 10⁻⁴** on Wave 1 (34 cells)
   and **0.69 %** on S9d (63 repetitions). Regressing decode on acceptance therefore explains nothing;
   it restates the definition of the dependent variable. Both reviewers' r² values are correct, and
   both are measuring how nearly constant `t_pass` was inside the subset each of them chose.
2. **The finding those regressions were reaching for survives, and is stronger stated properly.** The
   within-configuration decode spread is **not host noise and not measurement error**: it is variance
   of the *sampled continuation*, transmitted arithmetically. Removing it needs no fitted model —
   dividing each reading by its own tokens-per-pass is parameter-free. Doing so leaves a residual
   hardware term whose spread is **1.3–13.4 %** on Wave 1 and **0.6–13.7 %** (median 2.6 %) across
   S9d's 21 cells, against raw decode spreads of 16.7–40.7 % and 3.7–131.0 %. Within a cell,
   **98.7 % of the variance of log decode is tokens-per-pass and 0.9 % is `t_pass`**.
3. **A separate, genuinely controlled result falls out of the same reconstruction, and it is new.**
   `draft_n` and `draft_n_accepted` are byte-identical across every `-ts` ratio at a fixed repetition
   index in **14 of 14** repetition groups. The tensor-split ratio is generation-neutral: it moves
   layers between cards and changes nothing about the token sequence. Wave 1's ratio sweep is
   therefore a perfectly controlled experiment on the hardware term alone, and read that way it says
   the ratio moves decode by **≤ 5.7 % in 11 of 12 matched-continuation groups**.

The PN-66 objection — that a statistic can be near-tautological and therefore not a finding — applies
here in its sharpest form, and §5 answers it head-on: the identity is not the finding, the
decomposition it licenses is.

---

## 1. Provenance of the inputs

| artifact | what it carries | cells used |
|---|---|---|
| `data/raw/e12/tsweep-v2-{Q4_K_XL,Q5_K_XL,Q6_K,Q6_K_XL}.json` | Wave 1 `-ts` rebalance sweep; per cell `decode_tok_s`, `prefill_tok_s`, `prefill_tokens`, `draft_n`, `draft_n_accepted`, `mtp_acceptance`, `ctxcp`, `seed`, `rep`, `ts`, VRAM peaks | **34** cells with `ok = true` |
| `data/raw/e12/s9/s9d-depthsweep.json` | S9d draft-depth sweep, 4 arms × 2 filled depths × `n_draft` {2,4,8} × 3 reps; per **rep** `decode_tok_s`, `predicted_n`, `draft_n`, `draft_n_accepted`, `prompt_n`, `cache_n` | **21** valid cells, **63** reps |
| `manuscript/figures/data/fig12-decode-acceptance.csv`, `fig12b-speed-groups.csv`, `fig14*.csv`, `fig04b-sweep-full.csv` | the same values already extracted for the figure programme | cross-check only |

Common conditions for both batteries: image `sha256:feb0231976b6…` (`llamacpp-mtp:latest`, 0.3.0-dev
build 1, commit d222767), `-sm layer`, q4_0 KV, `-fa on`, `-b 2048 -ub 512 -np 1`, DEC-2 official
non-thinking sampling (temperature 0.7, top_p 0.80, top_k 20, min_p 0.0, presence_penalty 1.5).
Wave 1 generates 192 tokens per cell at `-ctxcp 4` (one cell at 32) with seeds 20260831/2/3 by
repetition index; S9d generates up to 512 tokens per rep at `-ctxcp 32`, seed 20260830, behind a
gate requiring ≥ 128 generated tokens and ≥ 0.90 of the requested window filled.

The two batteries share no cell. Everything in §3 that is checked on both is checked on independent
data at different generation lengths, different `-ctxcp`, and different draft depths.

---

## 2. Is the sweep controlled? The draft-count invariance

**Question.** Are `draft_n` and `draft_n_accepted` byte-identical across `-ts` ratios within a
repetition index?

**Answer: yes, in every group, including the `default` placement and including the `-ctxcp 32` cell.**

| arm | ctx | rep | ratios measured | `(draft_n, draft_n_accepted)` |
|---|---|---|---|---|
| UD-Q4_K_XL | 212,992 | 1 | default · 54,46 · 56,44 · 58,42 · 60,40 · 62,38 (**6**) | (148, 117) |
| UD-Q4_K_XL | 212,992 | 2 | 56,44 · 58,42 | (174, 103) |
| UD-Q4_K_XL | 212,992 | 3 | 56,44 · 58,42 | (174, 103) |
| UD-Q4_K_XL | 229,376 | 1 | 56,44 · default | (192, 95) |
| UD-Q4_K_XL | 245,760 | 1 | 56,44 · default | (179, 101) |
| UD-Q4_K_XL | 262,144 | 1 | 56,44 · default | (170, 105) |
| UD-Q5_K_XL | 262,144 | 1 | 54,46 · 56,44 · 58,42 · 60,40 · 62,38 (**5**) | (188, 97) |
| UD-Q5_K_XL | 262,144 | 2 | 54,46 · 56,44 | (160, 111) |
| UD-Q5_K_XL | 262,144 | 3 | 54,46 · 56,44 | (154, 113) |
| UD-Q6_K | 262,144 | 1 | 56,44 · 58,42 · 58,42 @ `-ctxcp 32` (**3**) | (174, 103) |
| UD-Q6_K | 262,144 | 2 | 56,44 · 58,42 | (135, 123) |
| UD-Q6_K | 262,144 | 3 | 56,44 · 58,42 | (172, 105) |
| UD-Q6_K_XL | 196,608 | 1 | 56,44 | (136, 122) |
| UD-Q6_K_XL | 212,992 | 1 | 56,44 | (175, 103) |

Two consequences, and the second is the one the paper needs.

- **The tensor-split ratio is generation-neutral.** Identical draft and acceptance counts across six
  placements of the same layers imply the same tokens were drafted, verified and accepted in the same
  order. `-ts` selects which card holds which layer; it does not perturb arithmetic enough to change
  a sampled sequence at temperature 0.7 with a fixed seed. Wave 1's ratio sweep is therefore a clean
  single-variable experiment.
- **Repetition index, not repetition, is what varies.** Reps 1/2/3 carry seeds 20260831/2/3, so a
  "repetition group" in PN-19, PN-36 and PN-45 is three *different continuations*, not three runs of
  the same one. Its spread is dominated by which text was generated. Both blind reviews found this;
  the artifacts state it in the `seed` field, which no correction pass read.

---

## 3. The identity: what decode throughput is made of

### 3.1 Derivation

llama.cpp's MTP loop runs the target model once per verification pass. Each pass drafts `n_draft`
tokens, verifies them, and emits **one** guaranteed token plus every accepted draft token. Over a
generation of `N` tokens in `P` passes:

```
draft_n           = n_draft x P                     (tokens drafted)
draft_n_accepted  = A                               (tokens accepted)
N                 = P + A                           (one guaranteed token per pass, plus accepted)
acceptance a      = A / draft_n = A / (n_draft x P)
=>  N / P         = 1 + n_draft x a                 (tokens per pass)
=>  decode_tok_s  = (N / P) / t_pass = (1 + n_draft x a) / t_pass
```

`t_pass` is the wall time of one verification pass — the quantity that actually depends on the
hardware, the weights, the split, the KV depth and the batch shape.

### 3.2 Verification on Wave 1 (n = 34)

Reconstructing `P = draft_n / 2` and `N = P + draft_n_accepted` from the artifacts recovers
**N ∈ {190.0, 190.5, 191.0}** in every one of the 34 cells against a requested `n_predict` of 192
— the residual is the final pass, which drafts fewer than `n_draft` tokens. The identity itself:

> **max | N/P − (1 + 2 × mtp_acceptance) | over 34 cells = 1.0 × 10⁻⁴**, which is the print
> precision of `mtp_acceptance` (4 decimal places) and nothing else.

### 3.3 Verification on S9d, where `n_draft` varies (n = 63 reps)

S9d is the harder test: three draft depths, so the identity's coefficient changes.

> **tokens-per-pass = 1 + n_draft × acceptance: median relative error 0.29 %, maximum 0.69 %**
> across 63 repetitions, 4 arms, 2 filled depths (123,670 and 186,270 tokens) and `n_draft` ∈ {2,4,8}.

The residual is the tail pass and shrinks with generation length, exactly as the derivation predicts:
Wave 1's 192-token generations sit at 10⁻⁴, S9d's 512-token generations at 10⁻³ only because
`predicted_n` is reported as an integer count that includes an EOS-truncated final pass.

### 3.4 What this does to the regressions

Because `decode = (1 + n_draft × a) / t_pass`, an OLS of `decode` on `a` is a straight line through
the identity whenever `t_pass` is close to constant, with slope `n_draft / t_pass` and intercept
`1 / t_pass`. r² is then a measure of **how constant `t_pass` was in the chosen subset** — not of how
much acceptance explains.

Recomputed here, and this reconciles the two reviewers exactly:

| regression subset | n | fit (decode ~ acceptance) | slope SE | **r²** | RMSE |
|---|---|---|---|---|---|
| Wave 1, all `ok` cells (4 arms, 6 depths, both `-ctxcp`) | 34 | `3.925 + 13.678 a` | 1.553 | 0.708 | 1.118 |
| Wave 1, `-ctxcp 4` only | 33 | `3.985 + 13.612 a` | 1.578 | 0.706 | 1.132 |
| **Wave 1, matched depth 262,144, `-ctxcp 4`** | **17** | **`4.526 + 11.316 a`** | 1.339 | **0.827** | 0.676 |
| Wave 1, UD-Q5_K_XL @ 262,144 | 9 | `3.704 + 12.686 a` | 2.517 | 0.784 | 0.749 |
| Wave 1, UD-Q6_K @ 262,144, `-ctxcp 4` | 6 | `4.380 + 11.227 a` | 1.849 | 0.902 | 0.662 |
| Wave 1, UD-Q4_K_XL, all depths | 16 | `4.131 + 14.653 a` | 1.162 | 0.919 | 0.515 |
| **Wave 1, UD-Q4_K_XL @ 212,992** | **10** | **`5.256 + 13.354 a`** | 0.552 | **0.987** | 0.170 |
| Wave 1, one reading per (arm, ctx, rep) | 14 | `4.941 + 12.256 a` | 2.309 | 0.701 | 1.091 |
| **S9d, pooled over `n_draft` {2,4,8}** | **63** | `14.637 + 9.670 a` | — | **0.106** | — |
| S9d, `n_draft = 2` only | 24 | `7.364 + 13.280 a` | — | 0.577 | — |
| S9d, `n_draft = 4` only | 18 | `6.515 + 21.350 a` | — | 0.891 | — |
| S9d, `n_draft = 8` only | 21 | `7.878 + 38.352 a` | — | 0.917 | — |
| S9d, `n_draft = 2`, ctx 131,072 | 12 | `8.279 + 14.208 a` | — | 0.959 | — |

**Both reviewers are right about their own subsets and neither figure generalises.**
Reviewer D's **0.827** is the matched-depth 262,144 `-ctxcp 4` set, n = 17 (recomputed 0.8265). The
figure agent's **"up to 0.99"** is UD-Q4_K_XL at 212,992, n = 10 (recomputed 0.9865) — the subset in
which `t_pass` varies least, 4.8 % end to end. The same regression on S9d, where `n_draft` is not
held fixed, collapses to **r² = 0.106**, because the identity's slope is `n_draft / t_pass` and
pooling three slopes into one line is a specification error. Regressing on tokens-per-pass instead of
acceptance restores it (pooled r² = 0.890; 0.901 at 131,072 and 0.968 at 186,270, with implied
`t_pass` of 202 and 230 ms from the reciprocal slopes).

The honest reading: **r² here is a diagnostic of subset homogeneity, and quoting any single value as
"acceptance explains X % of decode variance" would be a category error.**

---

## 4. The decomposition, done parameter-free

Dividing each reading by its own `1 + n_draft × acceptance` needs no fitted model, no subset choice
and no estimator convention. It yields `t_pass` in milliseconds, which is the quantity a systems
reader wants anyway.

### 4.1 Wave 1 — PN-45's true repetition groups, re-expressed

Estimator held to PN-45's `(max − min) / median` throughout.

| arm | ctx | `-ts` | n | acceptances | decode spread | **`t_pass` spread** | `t_pass` readings (ms) |
|---|---|---|---|---|---|---|---|
| UD-Q5_K_XL | 262,144 | 54,46 | 3 | 0.516 · 0.694 · 0.734 | 16.7 % | **1.6 %** | 187.73 · 187.93 · 190.68 |
| UD-Q5_K_XL | 262,144 | 56,44 | 3 | 0.516 · 0.694 · 0.734 | 17.1 % | **1.3 %** | 188.54 · 190.79 · 191.08 |
| UD-Q4_K_XL | 212,992 | 56,44 | 3 | 0.791 · 0.592 · 0.592 | 21.3 % | **2.9 %** | 161.73 · 166.50 · 163.83 |
| UD-Q4_K_XL | 212,992 | 58,42 | 3 | 0.791 · 0.592 · 0.592 | 22.6 % | **4.4 %** | 162.54 · 169.67 · 163.88 |
| UD-Q6_K | 262,144 | 58,42 | 3 | 0.592 · 0.911 · 0.611 | 28.6 % | **8.3 %** | 203.17 · 199.34 · 186.60 |
| UD-Q6_K | 262,144 | 56,44 | 3 | 0.592 · 0.911 · 0.611 | **40.7 %** | **13.4 %** | 213.69 · 188.25 · 189.59 |

**Raw 16.7–40.7 % → 1.3–13.4 % conditioned.** For comparison, `fig12b-speed-groups.csv`'s
`acceptance_adjusted_spread_pct_over_median` — computed by adjusting each reading to its group's mean
acceptance along a *fitted* line — gives 2.7 · 2.9 · 4.2 · 5.4 · 9.5 · 10.2 %, i.e. **2.7–10.2 %**,
and reviewer D's reported 2.6–11.0 % is a near-identical fitted variant. The three versions agree on
the conclusion and differ by a few points because two of them carry a fitted parameter. **The paper
should use the parameter-free version and say why.**

### 4.2 S9d — the independent replication, 21 cells and 63 reps

S9d's three reps within a cell are the same launch, the same server, the same pad and the same
`n_draft`: the only thing that differs is the sampled continuation. It is the cleanest available test
and it is much larger than Wave 1's.

| cell (arm · ctx · `n_draft`) | acceptances | decode spread | **`t_pass` spread** |
|---|---|---|---|
| Q4_K_XL · 131,072 · 2 | 0.753 · 0.551 · 0.752 | 17.0 % | 1.9 % |
| Q4_K_XL · 131,072 · 4 | 0.573 · 0.418 · 0.574 | 19.3 % | 0.9 % |
| Q4_K_XL · 131,072 · 8 | 0.386 · 0.457 · 0.375 | 17.0 % | 3.4 % |
| Q4_K_XL · 196,608 · 2 | 0.585 · 0.788 · 0.643 | 19.9 % | 2.6 % |
| Q4_K_XL · 196,608 · 8 | 0.438 · 0.448 · 0.205 | 42.9 % | 4.8 % |
| Q5_K_XL · 131,072 · 2 | 0.869 · 0.646 · 0.971 | 23.9 % | 3.0 % |
| Q5_K_XL · 131,072 · 4 | 0.530 · 0.389 · 0.588 | 26.3 % | 6.9 % |
| Q5_K_XL · 131,072 · 8 | 0.315 · 0.390 · 0.794 | **89.9 %** | 4.4 % |
| Q5_K_XL · 196,608 · 2 | 0.679 · 0.654 · 0.944 | 25.9 % | 3.0 % |
| Q5_K_XL · 196,608 · 4 | 0.427 · 0.417 · 0.442 | **3.7 %** | 0.6 % |
| Q5_K_XL · 196,608 · 8 | 0.453 · 0.820 · 0.538 | 58.3 % | 3.2 % |
| Q6_K · 131,072 · 2 | 0.736 · 0.580 · 0.952 | 30.6 % | 2.6 % |
| Q6_K · 131,072 · 4 | 0.651 · 0.713 · 0.388 | 40.9 % | **13.7 %** |
| Q6_K · 131,072 · 8 | 0.195 · 0.204 · 0.428 | 71.5 % | 1.5 % |
| Q6_K · 196,608 · 2 | 0.828 · 0.976 · 0.968 | 11.2 % | 1.6 % |
| Q6_K · 196,608 · 4 | 0.608 · 0.907 · 0.920 | 29.9 % | 4.7 % |
| Q6_K · 196,608 · 8 | 0.265 · 0.894 · 0.759 | 72.8 % | 2.1 % |
| Q6_K_XL · 131,072 · 2 | 0.690 · 0.670 · 0.954 | 24.7 % | 2.4 % |
| Q6_K_XL · 131,072 · 8 | 0.290 · 0.209 · 0.734 | **131.0 %** | 4.5 % |
| Q6_K_XL · 196,608 · 2 | 0.622 · 0.960 · 0.593 | 33.6 % | 2.3 % |
| Q6_K_XL · 196,608 · 4 | 0.372 · 0.905 · 0.550 | 66.7 % | 1.2 % |

> **21 cells. Decode spread: median 29.9 %, range 3.7–131.0 %. `t_pass` spread: median 2.6 %,
> range 0.6–13.7 %.** The single largest decode spread in the corpus — 131.0 % on Q6_K_XL at
> `n_draft` 8 — carries a `t_pass` spread of 4.5 %. Nothing about the machine changed between those
> three reps; the model wrote three different continuations, one of which speculation predicted
> nearly three times better than another.

### 4.3 Variance decomposition

Writing `log decode = log(tokens-per-pass) − log(t_pass)` and decomposing the variance:

| set | n | var(log decode) | share: tokens/pass | share: `t_pass` | share: −2·cov |
|---|---|---|---|---|---|
| S9d, within-cell deviations (21 cells, each centred on its own mean) | 63 | 0.04037 | **98.7 %** | **0.9 %** | 0.4 % |
| S9d, pooled across cells | 63 | 0.08058 | 142.0 % | 23.7 % | −65.7 % |
| Wave 1, matched depth 262,144, `-ctxcp 4` | 17 | 0.01726 | 61.2 % | 23.1 % | 15.7 % |
| Wave 1, all 34 cells | 34 | 0.02436 | 44.7 % | 33.9 % | 21.4 % |

Read the first row and stop: **inside a cell — same binary, same weights, same split, same depth,
same draft depth — 98.7 % of the variance in decode throughput is which text the model happened to
sample.** The pooled rows have shares above 100 % and a large negative cross term because across
cells the two factors are anti-correlated by construction (deeper contexts and larger `n_draft` raise
`t_pass` and lower acceptance at once); that anti-correlation is the reason the naive pooled
regression in §3.4 reads r² = 0.106.

---

## 5. Is this the PN-66 objection again? Yes — and here is the answer

PN-66's lesson is that `acceptance = accepted / drafted` falls with draft depth for any per-token
match probability below 1, so "acceptance declines with `n_draft`" is near-tautological and must not
be reported as a discovery. The objection applies here **more sharply**, because §3 is not
"near-tautological" — it is an exact identity. Three things follow, and the paper must state all
three or it repeats the study's signature failure.

1. **"Decode regresses on acceptance at r² = 0.83" must not be printed as a finding.** It is the
   definition of decode throughput, observed through a subset in which the other factor was nearly
   constant. Printing it would be the fourth time this corpus reported an arithmetic consequence as a
   measurement.
2. **What is *not* tautological is the size and structure of the residual.** The identity says decode
   is `(1 + n·a)/t_pass`; it says nothing about how variable `t_pass` is. That `t_pass` varies by
   0.6–13.7 % (median 2.6 %) inside a cell while decode varies by 3.7–131.0 % is a measurement, and
   it is the one that matters: it establishes that this host's decode readings are **reproducible to
   a few per cent** once the continuation is accounted for, and that every "±40 % noise" caveat in
   PN-19, PN-36 and PN-45 was describing the benchmark's own sampling, not the machine.
3. **The consequence is a protocol rule, and that is a genuine contribution.** Speculative decoding
   makes throughput a function of the *text*. A throughput number measured under sampling is not a
   property of a configuration; a comparison of two configurations under sampling with different
   continuations is not a comparison. The rule the report should give: **report `t_pass` and
   tokens-per-pass separately, or measure throughput greedy.** Both are free — `t_pass` is
   recoverable from `draft_n`, `draft_n_accepted` and `decode_tok_s`, all three of which llama.cpp
   already emits, so the corpus already on disk can be re-read at zero GPU cost.

The same logic bounds §6's claims. `1 + n_draft × a` rising while `a` falls is exactly PN-66's
tautology seen from the speed side, so the draft-depth axis must be argued on tokens-per-pass:

| UD-Q4_K_XL @ 131,072 (S9d, 3 reps each) | `n_draft` 2 | 4 | 8 |
|---|---|---|---|
| pooled acceptance (`fig14-draftdepth.csv`) | 0.6727 | 0.5123 | 0.4036 |
| median tokens-per-pass (per-rep) | 2.500 | 3.300 | 4.100 |
| median `t_pass` (ms) | 129.39 | 162.02 | 152.89 |
| median decode (tok/s) | 19.124 | 20.252 | 26.028 |

Acceptance falls by 40 % across the axis while tokens-per-pass rises by 64 % and decode rises by
36 %. Reporting the acceptance column alone would invert the sign of the conclusion.

---

## 6. What the residual term says, now that it is visible

Everything in this section is a claim about `t_pass`, the term the identity leaves behind. It is
observational — nothing here was randomised — and every n is small.

### 6.1 The `-ts` ratio, at a genuinely fixed continuation

Because §2 shows the draft counts are identical across ratios within a repetition index,
tokens-per-pass is *exactly* constant inside these groups, and the decode spread **is** the `t_pass`
spread. This is the cleanest single-variable estimate of the split ratio's speed effect in the corpus.

| arm · ctx · rep | ratios | acceptance | decode readings (tok/s) | spread |
|---|---|---|---|---|
| Q4_K_XL · 212,992 · 1 | 6 | 0.7905 | 15.85 · 15.96 · 15.88 · 15.60 · 15.88 · 15.70 | **2.2 %** |
| Q4_K_XL · 212,992 · 2 | 2 | 0.5920 | 13.12 · 12.87 | 1.9 % |
| Q4_K_XL · 212,992 · 3 | 2 | 0.5920 | 13.33 · 13.33 | 0.0 % |
| Q4_K_XL · 229,376 · 1 | 2 | 0.4948 | 11.81 · 11.83 | 0.2 % |
| Q4_K_XL · 245,760 · 1 | 2 | 0.5642 | 12.01 · 12.02 | 0.1 % |
| Q4_K_XL · 262,144 · 1 | 2 | 0.6176 | 12.10 · 12.14 | 0.3 % |
| **Q5_K_XL · 262,144 · 1** | **5** | 0.5160 | 10.82 · 10.78 · **8.50** · 10.67 · 10.44 | **21.8 %** |
| Q5_K_XL · 262,144 · 2 | 2 | 0.6937 | 12.70 · 12.51 | 1.5 % |
| Q5_K_XL · 262,144 · 3 | 2 | 0.7338 | 12.94 · 12.91 | 0.2 % |
| Q6_K · 262,144 · 1 | 2 | 0.5920 | 10.22 · 10.75 | 5.0 % |
| Q6_K · 262,144 · 2 | 2 | 0.9111 | 14.99 · 14.16 | 5.7 % |
| Q6_K · 262,144 · 3 | 2 | 0.6105 | 11.71 · 11.90 | 1.6 % |

**In 11 of 12 groups the split ratio moves decode by ≤ 5.7 %, and in 6 of them by ≤ 1.6 %.** The one
exception is PN-42's outlier, UD-Q5_K_XL at `-ts 58,42`, whose `t_pass` is **238.97 ms** against
187.73–194.63 ms for the four other ratios *at an identical continuation* — a 24 % per-pass penalty,
n = 1, measured in repetition 1 only and never re-attempted. It should be reported as an anomaly
worth one confirmation run, not as a ratio effect.

This does not contradict the headline `-ts` result, and the report must be explicit about why. E11's
"+33 % context and +93 % decode from one flag" compares a ratio that **loads at 262,144** against a
default that does not; the gain is a *ceiling* effect, and PN-6/PN-7 own it. At a context both
placements reach, the ratio is worth a few per cent of speed. Two different claims, both true, and
the paper has so far printed only the loud one.

### 6.2 `-ctxcp 32` (PN-18) is uncontaminated

The `-ctxcp` A/B pair sits inside a matched-continuation group: `56,44`/`58,42`/`58,42 @ ctxcp 32`
all carry `(174, 103)` at repetition 1. Decode moves 10.749 → 11.482 tok/s (**+6.82 %**), which in the
residual term is 203.17 → 190.21 ms (**−6.38 % per pass**). PN-18's number is therefore a clean
single-variable measurement, not a draw from the noise — a correction worth making, since T12
currently qualifies it as "a directional adopt-it verdict, not a measured 6.8 % effect, since the
gain is the same order as the noise". The noise it was being compared against was continuation
variance that this pair does not contain. It remains n = 1 and should stay labelled as such.

### 6.3 Per-pass latency is linear in filled depth

| arm | filled depth (tokens) | median `t_pass` (ms) | n |
|---|---|---|---|
| UD-Q4_K_XL | 201,672 | 163.85 | 10 |
| UD-Q4_K_XL | 217,140 | 168.38 | 2 |
| UD-Q4_K_XL | 232,933 | 177.18 | 2 |
| UD-Q4_K_XL | 248,522 | 184.42 | 2 |
| UD-Q5_K_XL | 248,522 | 190.58 | 8 |
| UD-Q6_K | 248,522 | 194.47 | 6 |
| UD-Q6_K_XL | 186,265 | 161.88 | 1 |
| UD-Q6_K_XL | 201,672 | 167.71 | 1 |

*(Wave 1, `-ctxcp 4`, excluding the PN-42 outlier cell.)*

UD-Q4_K_XL is the only arm measured at four depths:

> **`t_pass` = 71.93 ms + 0.4511 µs × depth · r² = 0.9868 · n = 4 depth medians ·
> SE(slope) = 0.0369 µs/token.**

S9d supplies nine independent two-point slopes at `-ctxcp 32` over a completely different depth pair
(123,670 → 186,270) and different generation length:

| arm · `n_draft` | `t_pass` 123,670 → 186,270 (ms) | slope (µs/token) | implied fixed cost (ms) | depth share at 186,270 |
|---|---|---|---|---|
| Q4_K_XL · 2 | 129.39 → 156.27 | 0.4295 | 76.27 | 51.2 % |
| Q5_K_XL · 2 | 135.70 → 162.53 | 0.4286 | 82.70 | 49.1 % |
| Q6_K · 2 | 130.60 → 157.06 | 0.4228 | 78.31 | 50.1 % |
| Q6_K_XL · 2 | 131.05 → 159.10 | 0.4481 | 75.64 | 52.5 % |
| Q5_K_XL · 4 | 167.16 → 194.97 | 0.4443 | 112.21 | 42.4 % |
| Q6_K · 4 | 158.02 → 186.57 | 0.4561 | 101.61 | 45.5 % |
| Q5_K_XL · 8 | 174.48 → 203.31 | 0.4605 | 117.53 | 42.2 % |
| Q4_K_XL · 8 | 152.89 → 187.78 | 0.5574 | 83.96 | 55.3 % |
| Q6_K · 8 | 173.40 → 208.88 | 0.5668 | 103.30 | 50.5 % |

**Median slope 0.4481 µs/token, range 0.4228–0.5668 across nine (arm, `n_draft`) pairs**, against
0.4511 from an independent battery. The slope is remarkably stable in the arm at `n_draft` 2
(0.4228–0.4481 across four checkpoints spanning 17.56–25.30 GB), which is what a KV-attention term
should look like: it depends on cache size, and the q4_0 cache is the same size in every arm.

On the figure agent's model: pooling all eight arm × depth medians reproduces its slope almost
exactly — **`t_pass` = 69.82 ms + 0.4761 µs × depth, r² = 0.8959** against its 65.1 ms + 0.476 µs —
but pooling arms is confounded, since the intercept has to absorb weight-dependent compute (residuals
−4.8 to +6.3 ms, ordered by file size). Its "KV at 64 % of decode cost at depth" is the depth term
evaluated at 248,522 tokens with the pooled intercept. Recomputed honestly, the depth-dependent share
is **42–55 % at 186,270 tokens** and **61 % at 248,522** using the single-arm fit. The report should
quote a range with the depth attached, never a bare "64 %".

### 6.4 Between-arm per-pass latency, at matched depth

With the continuation removed, the three arms measured at 262,144 order by weight — which decode
throughput does not do.

| arm | file | n | median decode (tok/s) | median tokens/pass | **median `t_pass` (ms)** | `t_pass` range |
|---|---|---|---|---|---|---|
| UD-Q4_K_XL | 17.56 GB | 2 | 12.121 | 2.235 | **184.42** | 184.17–184.67 |
| UD-Q5_K_XL | 20.88 GB | 8 | 11.669 | 2.210 | **190.58** | 187.73–194.63 |
| UD-Q6_K | 21.98 GB | 6 | 11.808 | 2.221 | **194.47** | 186.60–213.69 |

*(262,144 tokens, `-ctxcp 4`, PN-42's `58,42` cell excluded from UD-Q5_K_XL.)*

- Decode span 3.83 % over the median, **and out of weight order** (Q4 > Q6 > Q5).
- `t_pass` span **5.27 %**, in weight order.
- **This is suggestive and is not a ranking.** UD-Q4_K_XL has n = 2 and separates cleanly from both
  others; UD-Q5_K_XL and UD-Q6_K overlap heavily (187.73–194.63 against 186.60–213.69) and do not
  separate. The correct sentence is that per-pass latency is the term in which a weight effect would
  appear, that it is ordered here, and that only the lightest arm is distinguishable at this n.

This also revises the PN-45 headline, without overturning it. PN-45's between-arm span of 6.74 %
compares medians of decode readings taken over *different continuations* — UD-Q5_K_XL's three reps
averaged acceptance 0.648, UD-Q6_K's 0.705. Recomputed on the same cells with the continuation
divided out, the span is 5.27 % on `t_pass` and 3.83 % on decode. **The conclusion is unchanged and
better founded: decode throughput does not discriminate these quantizations at the full window.**
What changes is the reason. It is not that the difference is buried under 40 % of noise; it is that
the difference is genuinely about 4–5 %, and the 40 % was the benchmark's own sampling.

---

## 7. What this licenses, and what it does not

**Licensed.**

1. `-ts` ratio does not change the generated sequence: 14 of 14 groups, up to 6 ratios each.
2. `decode_tok_s = (1 + n_draft × acceptance) / t_pass`, verified to 10⁻⁴ (Wave 1, n = 34) and
   0.69 % (S9d, n = 63).
3. Within-cell decode variance is 98.7 % continuation, 0.9 % per-pass latency (S9d, 21 cells).
4. Conditioning is parameter-free and collapses spread from 16.7–40.7 % to 1.3–13.4 % (Wave 1) and
   from 3.7–131.0 % (median 29.9 %) to 0.6–13.7 % (median 2.6 %) (S9d).
5. The split ratio moves decode ≤ 5.7 % in 11 of 12 matched-continuation groups.
6. `t_pass` is linear in filled depth at 0.4228–0.5668 µs/token (median 0.4481, nine pairs) and
   0.4511 ± 0.0369 µs/token in the one arm with four depths; the depth term is 42–61 % of pass cost
   between 186,270 and 248,522 filled tokens.
7. PN-18's `-ctxcp 32` A/B is a matched-continuation pair and its +6.82 % is a clean single-variable
   reading, still n = 1.
8. A protocol rule: throughput under sampling with speculation is a property of the text, not the
   configuration. Report `t_pass` and tokens-per-pass, or measure greedy.

**Not licensed.**

1. **"Acceptance explains 83 % of decode variance."** It is the identity. Do not print an r² as
   evidence of explanation anywhere in the report.
2. **Any single r².** The value ranges 0.106 to 0.987 by subset; it measures subset homogeneity.
3. **A `t_pass` ranking of the ladder.** Q4_K_XL separates; Q5_K_XL and Q6_K do not.
4. **PN-42's ratio penalty as a ratio effect.** n = 1, one repetition index, never re-attempted.
5. **"64 % of decode cost is KV."** It is 42–61 % depending on depth and on which intercept is used.
6. **Weakening PN-45's conclusion.** Its conclusion stands; only its account of *why* changes.
7. **Any statement that a greedy re-measurement is needed.** It is not. The residual term is
   recoverable from artifacts already on disk. A greedy re-run would be a confirmation, not a
   requirement, and this study's own standing constraint is that GPU hours are the scarce resource.

**Threats.** All small-n and observational. Wave 1 gives 2–3 readings per matched group and
UD-Q4_K_XL still has n = 1 at 262,144 (PN-36, PN-45). S9d's gate admits reps that stopped early on
EOS, so three of 63 reps carry `predicted_n` below 512 (248, 258, 441) and their `t_pass` is
correspondingly noisier. `t_pass` is a derived quantity: it inherits any error in llama.cpp's own
`decode_tok_s` timer, and it assumes every verification pass has equal cost, which is exact only if
the target is invoked once per pass — consistent with the reconstruction recovering `N` to within one
token in all 34 Wave 1 cells, but not independently instrumented. The two batteries differ in
`-ctxcp` (4 against 32), which §6.2 shows is worth about 6 % of pass time, so their absolute `t_pass`
values are not interchangeable; only their slopes are compared here.

---

## 8. Paper note, ready to paste

*Append under **§Efficiency** in `docs/paper/PAPER-NOTES.md`. PN-67 is the last number in use.*

```
- PN-68 | 2026-09-04T00:00:00Z | S3-report/re-analysis (no GPU) | claude-opus-5 | L-25
  Finding: **Decode throughput under speculative decoding is an identity, and the "unexplained" ±40 % noise in PN-19/PN-36/PN-45 is the benchmark's own sampling.** llama.cpp's MTP loop makes `decode_tok_s = (1 + n_draft x acceptance) / t_pass`, where `t_pass` is the wall time of one target verification pass; reconstructed from `draft_n`, `draft_n_accepted` and `decode_tok_s` the identity holds to a maximum relative error of 1.0e-4 over Wave 1's 34 cells and 0.69 % over S9d's 63 repetitions (4 arms x 2 filled depths x n_draft {2,4,8}). Three consequences. (a) **The tensor-split ratio is generation-neutral**: `draft_n` and `draft_n_accepted` are byte-identical across every `-ts` ratio at a fixed repetition index in 14 of 14 groups, up to six ratios per group, so Wave 1's sweep is a clean single-variable experiment and at a context every placement reaches, the ratio moves decode by <= 5.7 % in 11 of 12 matched-continuation groups (0.0-5.7 %; the twelfth is PN-42's `58,42` outlier, 21.8 %, n=1). (b) **Dividing each reading by its own `1 + n_draft x acceptance` is parameter-free conditioning** and collapses within-configuration spread from 16.7-40.7 % to 1.3-13.4 % on Wave 1's six true repetition groups, and from a median 29.9 % (range 3.7-131.0 %) to a median 2.6 % (range 0.6-13.7 %) across S9d's 21 cells. Inside a cell, 98.7 % of the variance of log decode is tokens-per-pass and 0.9 % is `t_pass`. (c) **`t_pass` is linear in filled depth** at 0.4511 +/- 0.0369 us/token (UD-Q4_K_XL, four depths, r2 = 0.9868) and a median 0.4481 us/token across nine independent (arm, n_draft) two-point slopes in S9d; the depth-dependent share of pass cost is 42-55 % at 186,270 filled tokens and 61 % at 248,522. At matched depth 262,144 the three arms order by weight on `t_pass` (UD-Q4_K_XL 184.42 ms, n=2 | UD-Q5_K_XL 190.58, n=8 | UD-Q6_K 194.47, n=6; 5.27 % span) where decode does not (12.121 / 11.669 / 11.808 tok/s, 3.83 % span, out of weight order). PN-45's conclusion is unchanged and better founded: decode does not discriminate these quantizations, not because the difference is buried under 40 % of noise but because the difference is about 4-5 % and the 40 % was sampling variance of the generated text.
  Evidence: `data/raw/e12/tsweep-v2-{Q4_K_XL,Q5_K_XL,Q6_K,Q6_K_XL}.json` (34 cells with ok=true) and `data/raw/e12/s9/s9d-depthsweep.json` (21 valid cells, 63 reps); full derivation, per-cell tables, regression diagnostics and the reconstruction script in `manuscript/ACCEPTANCE-REANALYSIS.md`. Reconstruction recovers N = passes + accepted in {190.0, 190.5, 191.0} against n_predict 192 in all 34 Wave 1 cells. Regression of decode on acceptance, recomputed: r2 = 0.8265 at matched depth 262,144 `-ctxcp 4` (n=17), 0.9865 for UD-Q4_K_XL at 212,992 (n=10), 0.1058 pooled over S9d's three draft depths (n=63) - the two blind reviewers' 0.827 and "up to 0.99" are these first two subsets, and neither figure generalises.
  Use as: §Efficiency, replacing the regression framing in T12 and F12 and supplying §6.7's missing citation. Also §Reproducibility - this is the fifth defect in the corpus caused by an aggregate over cells that differ in an untracked variable (cf. PN-19 depth, PN-36 `-ctxcp`, PN-20 estimator, PN-30 generation length), and the first where the untracked variable is the generated text itself. The transferable rule: **under speculative decoding, throughput measured with sampling on is a property of the continuation, not of the configuration; report `t_pass` and tokens-per-pass separately, or measure greedy.** Both are free - llama.cpp already emits all three fields, so the recovery costs no GPU time.
  Caveat: an identity is not an explanation. **Do not print "decode regresses on acceptance at r2 = 0.83" as a finding** - it restates the definition of the dependent variable, and the same objection PN-66 raises about acceptance falling with draft depth applies here in exact rather than approximate form. What is measured, and not tautological, is the size of the residual: `t_pass` spread of 0.6-13.7 % against decode spread of 3.7-131.0 %. All n are small and nothing was randomised: 2-3 readings per matched Wave-1 group, UD-Q4_K_XL still n=1 at 262,144, and the between-arm `t_pass` ordering separates only the lightest arm (UD-Q5_K_XL 187.73-194.63 ms overlaps UD-Q6_K 186.60-213.69 ms). `t_pass` is derived, inherits llama.cpp's own decode timer, and assumes one target invocation per verification pass. Wave 1 ran `-ctxcp 4` and S9d `-ctxcp 32`, worth about 6 % of pass time (PN-18), so absolute values are not interchangeable between the two batteries - only slopes are compared. PN-42's 24 % per-pass penalty at UD-Q5_K_XL `-ts 58,42` (238.97 ms against 187.73-194.63 at an identical continuation) is now the corpus's cleanest single-variable anomaly and is still n=1. This note also removes T12's qualification of PN-18: that A/B pair sits inside a matched-continuation group (both arms carry draft counts 174/103), so its +6.82 % decode / -6.38 % pass time is a clean single-variable reading rather than a draw from the noise, though still n=1.
```

---

## 9. What §6.7, T12 and F12 should say once this lands

*Recommendations for the main thread. Nothing below is applied here.*

### `OUTLINE-V2.md` §6.7 — replace the second bullet

The current bullet reads "decode regresses on acceptance at r² = 0.83–0.99, and conditioning on
acceptance collapses within-configuration spread from 17–41 % to 3–11 %. … Say that the noise figure
is an **upper bound** and that a greedy re-measurement would tighten it at no GPU cost."

Replacement, same length:

> **Explain the noise, do not report it.** `draft_n` and `draft_n_accepted` are byte-identical across
> every `-ts` ratio at a fixed repetition index — 14 of 14 groups — so the sweep is perfectly
> controlled and the *continuation* is the confound. Decode throughput under MTP is the identity
> `(1 + n_draft × acceptance) / t_pass`, verified to 10⁻⁴ over 34 cells and 0.69 % over 63
> repetitions, so the r² of decode on acceptance measures subset homogeneity, not explanation, and
> ranges 0.11 to 0.99 accordingly. Dividing each reading by its own tokens-per-pass needs no fitted
> model and collapses within-configuration spread from 16.7–40.7 % to 1.3–13.4 % (Wave 1) and from a
> median 29.9 % to a median 2.6 % (S9d, 21 cells); inside a cell 98.7 % of decode variance is which
> text was sampled. The residual, per-pass latency, is linear in depth at ~0.45 µs/token and orders
> the arms by weight where decode does not. Three correction passes missed this; two blind reviews
> found it independently; the recovery cost no GPU time, because the engine already emits every field
> it needs.

Also amend the section's **Claim** line: the variance is not merely "explainable rather than
mysterious", it is *arithmetic*, and the ±40 % figure describes HumanEval-style sampling variance
rather than the host. And add PN-68 to the **Evidence** line, before PN-45.

### `TABLES.md` T12 — three changes

1. Keep the six-row spread table and PN-45's estimator. **Add a `t_pass` column** (the parameter-free
   conditioning) beside the existing fitted `spread, acceptance-adjusted` column, and label which is
   which. Values: 1.6 · 1.3 · 2.9 · 4.4 · 8.3 · 13.4 %.
2. **Replace the three-row regression sub-table.** It currently presents r² as explanation. Replace
   with the identity, its verification error on both batteries, and one line noting that r² over the
   same data ranges 0.106 to 0.987 by subset. If a regression table is kept for the reviewers'
   benefit, it must be captioned as a homogeneity diagnostic.
3. **Amend the two footnotes.** The greedy-re-measurement sentence should become: the conditioning is
   recoverable from the committed artifacts at no cost, and greedy would be a confirmation. The PN-18
   footnote's "the same order as the noise above" is wrong — that pair shares its continuation and
   contains none of the noise above; state +6.82 % decode / −6.38 % per pass, n = 1.

Optionally add a row to the between-arm block: `t_pass` at 262,144, 184.42 / 190.58 / 194.47 ms
(n = 2 / 8 / 6), span 5.27 %, ordered by weight, with the overlap caveat in the same cell.

### `FIGURE-PROGRAMME.md` F12 — re-encode panel (a), keep panel (b)

- **Panel (a) is currently a scatter with an OLS line, which draws the identity and calls it a fit.**
  Re-encode as decode against **tokens-per-pass** (`1 + n_draft × acceptance`), with the identity
  drawn as a *family of constant-`t_pass` reference lines* (say 160, 180, 200, 220 ms) rather than a
  fitted line. Each point then reads off its own `t_pass` against the grid, the ratio groups collapse
  onto single lines, and PN-42's outlier is visibly on a different isoline instead of merely low. The
  data file already carries every field this needs; add a `t_pass_ms` column.
- **Panel (b) stands**, with the dumbbell's conditioned end switched to the parameter-free `t_pass`
  spread (1.3–13.4 %) and the fitted variant kept as a faint third marker if space allows.
- **Add S9d as a third panel or a companion figure.** It is the stronger evidence — 21 cells, 63
  reps, one launch per cell, three draft depths — and shows decode spread up to 131.0 % against
  `t_pass` spread of 4.5 % in the same cell. If F12 must stay two panels, this belongs in F14's
  draft-depth treatment, where the tokens-per-pass framing is also what keeps PN-66's tautology from
  inverting the conclusion.
- **Rewrite the claim and the alt text.** "Explaining about eighty-three per cent of the variance" is
  the sentence this whole re-analysis exists to remove.
- **Add an honesty constraint**: the relationship in panel (a) is definitional; the figure's content
  is the *spread of the isolines*, not the slope.

---

## Appendix A — reconstruction

```python
# t_pass and tokens-per-pass from any llama.cpp MTP timing record
passes         = draft_n / n_draft                 # target forward passes
N              = passes + draft_n_accepted         # tokens emitted (== predicted_n)
tokens_per_pass= N / passes                        # == 1 + n_draft * acceptance
t_pass_ms      = 1000 * N / (decode_tok_s * passes)
```

Wave 1 has `n_draft = 2` throughout (`--spec-draft-n-max 2`); S9d carries `n_draft` per cell.
Acceptance is `draft_n_accepted / draft_n`, which is what `mtp_acceptance` records. Spread is
`(max − min) / median` throughout, per PN-45. Regressions are ordinary least squares with no
weighting; r² is `1 − SS_res/SS_tot`; SE(slope) is `sqrt(SS_res/(n−2)/S_xx)`. The variance
decomposition is over `log` values with population variance, and the within-cell rows centre each
cell on its own mean before pooling.
