# Figure and table programme

*Divergence Ranks What Benchmarks Bound: quantization, context and speculative decoding for a 27B
coding model on two 16 GB GPUs.*

**What this file is.** The complete visual programme for the report: 28 figures and 23 tables, each
with the single claim it makes, the paper notes and artifacts behind it, a full encoding
specification, a publication-ready caption, alt text, and the honesty constraints that govern how it
may be drawn. Every figure has a companion data file in [`data/`](data/), generated from the
committed artifacts by [`extract.py`](extract.py) — **not typed by hand.** Tables in publication form
are in [`TABLES.md`](TABLES.md); rendering instructions are in [`RENDERING.md`](RENDERING.md).

**Status.** Specifications and data are complete and render-ready. **No figure has been rendered**,
because PaperBanana (R11) is cloud-dependent and this host has no API keys (verified — see
`RENDERING.md` §1). What is delivered here is everything a keyed machine needs to render without
asking a question.

---

## 0. How to read a spec, and the rules that govern all of them

Each entry carries:

| field | meaning |
|---|---|
| **Tier** | `ESSENTIAL` (6), `CORE` (16), `SUPPORTING` (6) — the paper stands without a supporting figure and is diminished without an essential one |
| **Section** | the `OUTLINE.md` section it serves |
| **Type** | `statistical plot` (PaperBanana's CSV path) or `methodology diagram` (its retriever/stylist path) — never mixed in one request |
| **Claim** | the single sentence the figure exists to make. If a figure needs two sentences it is two figures |
| **Evidence** | paper notes, then the artifact paths the data came from |
| **Data** | the file under `data/`, with the columns the figure consumes |
| **Encoding** | axes with units and scale, series, marks, and what varies with what |
| **Annotations** | text that must appear *inside* the figure |
| **Caption** | publication-ready; carries n, estimator and protocol, per the project's hard rule 5 |
| **Alt text** | for the accessible version; states the finding, not the geometry |
| **Honesty constraints** | what the figure must NOT let a reader conclude. These are not stylistic; a render that violates one is wrong and must be rejected |

### 0.1 Rules that apply to every figure

1. **Protocols never mix inside one panel.** Perplexity Protocol 1, Protocol 2 and the SSA divergence
   protocol are three different instruments; depth-0 and at-depth decode differ 2–3×; greedy and official-sampling rows are not
   comparable. Where a figure must show two protocols, they are separated by panel or by an explicit
   in-figure label, and the caption names both.
2. **Pre-2026-08-29 rows carry `irreproducible-on-current-images`** (PN-57) in the legend or as a
   hatched fill. This is not a footnote; the container image that produced them is gone.
3. **Overlapping intervals are drawn overlapping.** No figure may separate points whose intervals
   overlap by rescaling, jitter, or by dropping the interval. Where the interval is wider than the
   effect, the interval is the message.
4. **Error bars smaller than the marker stay smaller than the marker.** In F1 and F6 that is the
   point: the divergence intervals really are that tight. A stylist "improving" them destroys the
   figure.
5. **No trend line without a fitted model in the data file.** F12 has one (OLS, R² in the caption).
   F4's inset explicitly must not have one.
6. **Withdrawn results appear only in F20** (the correction record) and only labelled as withdrawn.
   They are never plotted as findings.
7. **A count is never rendered as a rate without its denominator visible**, and a rate with n < 30
   carries its interval.

### 0.2 Palette — colour-blind safe and greyscale-legible

Okabe–Ito, which is safe for deuteranopia, protanopia and tritanopia, plus a neutral grey. **Colour
never carries information alone**: every series is also distinguished by marker shape and line style,
because two of these hues (bluish green and vermillion) are close in luminance and merge in
greyscale.

| role | hex | marker | line | greyscale |
|---|---|---|---|---|
| UD-Q6_K_XL (reference arm) | `#000000` black | open circle `○` | solid | black |
| UD-Q6_K | `#0072B2` blue | filled circle `●` | solid | dark |
| UD-Q5_K_XL | `#009E73` bluish green | filled square `■` | dashed | mid |
| UD-Q4_K_XL | `#D55E00` vermillion | filled triangle `▲` | dash-dot | mid |
| KV-dtype-only control | `#CC79A7` reddish purple | filled diamond `◆` | dotted | light |
| divergence instrument | `#0072B2` blue | — | — | — |
| task instrument | `#D55E00` vermillion | — | — | — |
| withdrawn / excluded / not-tested | `#767676` grey | — | — | diagonal hatch |
| external reference band | `#F0E442` yellow at 25 % alpha | — | — | light fill |

Domains use marker fill, not hue: prose = open, code = filled, task prompts = half-filled.
Backgrounds are white; no gradients, no drop shadows, no 3-D.

### 0.3 Provenance classes used in the data files

`measured` (a run on this host, artifact committed) · `recomputed` (derived here from committed
per-item records, zero GPU cost) · `cited` (external, not measured here) · `modelled` (GPU telemetry
+ RAPL + a fixed platform allowance; this host has no wall-socket sensor) · `historical` (measured
before 2026-08-29; *irreproducible-on-current-images*).

---

## 1. The programme at a glance

Ranked by importance. "Claim" is the one sentence the figure makes.

| ID | Tier | § | Figure | Claim |
|---|---|---|---|---|
| **F1** | ESSENTIAL | 5.1 | Divergence ladder × domain | Divergence separates every arm with non-overlapping intervals, and the separation grows as the corpus approaches the task |
| **F2** | ESSENTIAL | 5.1 | The tail, and its control | Quantization damage to code is concentrated in a thin tail; the tail's *shape* is a property of the corpus, not of quantization |
| **F3** | ESSENTIAL | 5.2 | What each instrument bounds | Every task instrument bounds the effect; several could not have reached significance at any outcome |
| **F4** | ESSENTIAL | 5.3 | Ceiling × tensor split | On a two-GPU host without a fast interconnect, the split — not the quantization — set the reachable window for three of four arms |
| **F5** | ESSENTIAL | 5.4 | Speculation: speed bought, identity spent | Speculative decoding buys up to 2.8× and reproducibly changes one generated function in five |
| **F6** | CORE | 1, 5.2 | Two instruments, one axis | The same four arms are flat under three task instruments and monotone under divergence |
| **F7** | CORE | 5.1 | Tail shape by corpus | Distribution shape is flat across the ladder within a corpus and differs ~3× between corpora |
| **F8** | CORE | 5.1, 9 | The metric pair | Top-1 agreement and mean KLD disagree about which domain is hurt; either alone inverts the conclusion |
| **F9** | CORE | 5.2 | RULER budget closure | The published long-context separation is a difference in reasoning length, not in retrieval |
| **F10** | CORE | 1, 4 | The protocol swing | The same weights read as 29 % worse or 0.8 % worse depending on conventions no paper discloses |
| **F11** | CORE | 5.3 | The binding card | Every ceiling was set by the unluckier GPU while the other card held usable memory |
| **F12** | CORE | 5.5 | Speed does not discriminate — and the noise is explainable | Decode regresses on draft acceptance at R² = 0.83; conditioning on it collapses the spread from 41 % to 11 % |
| **F13** | CORE | 5.4 | Divergence rises with completion length | Speculative divergence is a per-character hazard, not a per-problem rate: 2.4 % of short completions, 53.7 % of long ones |
| **F14** | CORE | 5.4 | Draft depth | The acceptance *ratio* must fall with draft depth; the per-token match probability behind it does not |
| **F15** | CORE | 5.2 | HumanEval+ ladders | A monotonic benchmark ordering that separates no adjacent rung; in thinking mode the signal is carried by empty responses |
| **F16** | CORE | Agentic | SWE-bench Verified | The most expensive instrument in the study inverts the ladder, and the inversion is noise |
| **F17** | CORE | 1, Agentic | The Q3 profile | Every cheap instrument rates the disqualified arm well; only the expensive one rates it correctly |
| **F18** | CORE | 5.7 | Cross-backend | Two engines reach the same throughput by opposite routes, and one of them cannot hold the window |
| **F19** | CORE | 6 | What the measurements cost | 2.3 GPU-hours of divergence separated the ladder; 14.3 GPU-hours of task benchmarking bounded it |
| **F20** | CORE | 9 | The correction record | Sixteen corrections in twelve days, fourteen of them at zero GPU cost, because per-item records were kept |
| **F21** | SUPPORTING | 4 | The measurement design | Divergence draws power from token count, task benchmarks from problem count |
| **F22** | SUPPORTING | 5.5 | Throughput vs filled depth | Prefill falls monotonically with depth in every arm; decode's depth trend is not resolvable at three repetitions |
| **F23** | SUPPORTING | 9 | Generation forks | Free-running greedy generation cannot measure quantization distance: every pair saturates |
| **F24** | SUPPORTING | 5.2, 4 | Minimum attainable p | For paired binary data the smallest reachable p is set by the discordant count, not by n |
| **F25** | SUPPORTING | 9 | Defect taxonomy | Twelve instrumentation defects, three families, each one another group would hit |
| **F26** | SUPPORTING | 5.2 | Perplexity cannot certify its own ranking | The ladder spans 0.033 PPL against ±0.041 of standard error on every point |
| **F27** | SUPPORTING | 5.6 | KV quantization is not free | A KV-dtype change moves the token distribution about half as far as dropping a quantization level, and moves perplexity by 0.15 % |
| **F28** | CORE | 5.2, 7 | Multiplicity and clustering | Every divergence separation survives Holm and Benjamini–Hochberg over the whole 19-test family; no task-benchmark test does |

### 1.1 The tables

Full publication-form versions, with n, estimator, interval and protocol inside each table, are in
[`TABLES.md`](TABLES.md). Ranked the same way: `ESSENTIAL` (4), `CORE` (12), `SUPPORTING` (7).

| ID | Tier | § | Table | What it carries that no figure can |
|---|---|---|---|---|
| **T3** | ESSENTIAL | 5.1 | Divergence master table, all ten cells | every quantile, top-1 agreement, RMS Δp and perplexity per cell — the numbers F1, F2, F7, F8 and F27 each show one slice of |
| **T6** | ESSENTIAL | 5.2 | What each instrument bounds | the min-attainable-p column, per comparison |
| **T12** | ESSENTIAL | 5.5 | Decode at the full window, and its variance | three published values for one quantity, the estimator that reconciles them, and the regression |
| **T18** | ESSENTIAL | 5.2 | Perplexity — three protocols, never mixed | the only place all three protocols appear, deliberately in separate blocks |
| T1 | CORE | 3 | Host, engines and arms | sha256 and byte counts, including for two deleted files |
| T2 | CORE | 3 | The four sampling configurations | the measured engine default that matches nothing |
| T4 | CORE | 5.1 | Code-to-prose amplification by quantile | the interval basis per row, and why the median row cannot rank |
| T5 | CORE | 5.1 | Tail shape normalised by own mean | all ten cells including the KV-only control and a third corpus |
| T9 | CORE | 5.2 | RULER, all fourteen cells with closure | the audit that distinguishes a ceiling from a degenerate match |
| T10 | CORE | 5.3 | The complete Wave-1 sweep | every cell, every failure mode, every VRAM pair |
| T11 | CORE | 5.3 | Context ceilings | which ratios load, which failed, and the default-split status per arm |
| T13 | CORE | 5.4 | Speculative decoding at ctx 32,768 | equivalence, acceptance, pass@1 and the length-quartile hazard together |
| T14 | CORE | 5.4 | Draft depth at matched depth | the implied per-token match probability beside the acceptance ratio |
| T15 | CORE | 5.2 | HumanEval+ historical ladders | the empty-response column beside every pass@1 |
| T16 | CORE | Agentic | SWE-bench Verified | all three generations of the same numbers |
| T17 | CORE | 5.7 | Cross-backend | acceptance, mean accepted length, power, VRAM and ceiling in one row each |
| T19 | SUPPORTING | 6 | What the measurements cost | per-experiment GPU hours from the artifacts' own timings |
| T20 | SUPPORTING | 9 | The defect register | twelve defects, their family, and how each was found |
| T21 | SUPPORTING | 9 | Withdrawn and superseded claims | the before/after of all sixteen corrections |
| T7 | SUPPORTING | 5.2 | HellaSwag paired, six pairs | the b/c counts behind the forest plot |
| T8 | SUPPORTING | 5.2 | HumanEval+ paired | the 2×2 tables behind the bound |
| T22 | SUPPORTING | 5.7 | Power and thermal envelope | the modelling caveat, in place of a figure that should not exist |
| T23 | SUPPORTING | 5.2, 7 | Multiplicity across all 19 tests | Holm, Benjamini–Hochberg and the design-effect sensitivity |

### 1.1b Sub-figures and companion data

Some figures render as two requests and are composed afterwards, and some carry a companion data file
that is not a figure of its own. The naming convention is the parent's ID plus a letter, and each is
described inside its parent's spec:

| id | role | rendered separately? |
|---|---|---|
| F1b | adjacent-arm separation in σ, the numbers behind F1's claim | yes — small companion plot, or a table row |
| F4-inset | decode against VRAM imbalance for UD-Q5_K_XL's five loading ratios | yes — composed into F4 as an inset |
| F9b | the three paired 2×2 tables for the RULER n=100 cell | yes — placed beside F9 |
| F12b | raw versus acceptance-adjusted spread per repetition group | yes — F12's panel (b) |
| F13b | the per-problem record (164 rows) behind F13's quartiles | **no** — data only, for checking |
| F14b | per-repetition draft acceptance and decode | **no** — supplies F14's translucent markers |
| F17b | per-instance agentic step counts | **no** — appears as a table beside F17 |
| F27b | the perplexity contrast on the identical KV pair | yes — F27's panel (b) |

### 1.2 The six essential figures

**F1, F2, F3, F4, F5, F16.** F1 and F3 are the title: divergence ranks, benchmarks bound. F2 is the
paper's novel contribution and the only figure that carries its own scoping control. F4 is the
systems result a practitioner acts on. F5 retires the premise three of this project's own documents
asserted for nine days.

**F16 was promoted from CORE on 2026-09-04** (owner review). The programme had all six task-benchmark
and speculative-decoding figures at CORE, which under-represented the balance of what was actually
measured: a four-day SWE-bench Verified campaign across three quantizations, two HumanEval+ ladders
spanning seven configurations, and an MTP-versus-DFlash2 comparison are not supporting material for a
paper whose title claims benchmarks *bound*. F16 is the sharpest single instance of the thesis
anywhere in the corpus — the study's most expensive instrument, four days of GPU time, **inverting**
the ladder that every cheaper instrument ordered correctly, inside a ±12-point interval. A reader who
sees only F1–F5 would conclude this was a quantization study with benchmark asides; it was not.

**F22 was promoted to CORE** in the same pass: token-generation throughput against *filled* context
depth is a headline practitioner number, and the depth-0 tables it corrects are the ones most often
quoted elsewhere. F9 and F12 remain the closest further contenders.

---

## 2. Figure specifications

---

### F1 · The divergence ladder, by domain

**Tier** ESSENTIAL · **§5.1** · **Type** statistical plot · **Data** [`data/fig01-divergence-ladder.csv`](data/fig01-divergence-ladder.csv) (10 rows)

**Claim.** Mean KL divergence against the reference arm is monotone in bit-width in every domain,
separates every adjacent pair with non-overlapping intervals, and rises as the evaluation corpus
moves closer to the actual task — prose < generic code < task prompts.

**Evidence.** PN-13 (the ladder), PN-14 (code ≈ 2× prose), PN-21 (three-tier hierarchy), PN-15 and
PN-43 (the KV-only control row), PN-62 (what the control scopes).
Artifacts: `data/raw/e12/ssa/ssa-kld-tables.json` (all ten cells, extracted verbatim from the
serverlogs by PN-62), cross-checked against `ssa/ssa-results-parsed.json` and `ssa/ssa-s5-results.json`.

**Encoding.** Dot plot with horizontal error bars — **not** a bar chart; bars imply a zero baseline
that a divergence measured against a non-FP16 reference does not have.
- **x**: mean KL divergence (nats), **log scale**, domain 0.002 – 0.05.
- **y**: categorical, 10 rows in three blocks separated by white space. Block order top to bottom:
  UD-Q6_K, UD-Q5_K_XL, UD-Q4_K_XL. Within each block, three rows: WikiText-2 (prose), django (code),
  HumanEval+ prompts (task). A tenth row sits below all blocks, visually detached: the KV-dtype-only
  control.
- **marks**: one point per row with a symmetric horizontal bar of ±1 SE (`mean_kld_se_nats`).
  Marker fill encodes domain (open = prose, filled = code, half-filled = task). Colour encodes arm
  per §0.2.
- **reference bands**: a shaded vertical band from 0 to 0.007 labelled "Fireworks: high-quality
  deployment threshold (external)"; a lighter band 0.01–0.03 labelled "LocalBench: observed Q4_K_M
  range (external, disclaimed by its source)".

**Annotations.**
- Bracket the three task-prompt rows with "no arm passes the external threshold on the actual task
  distribution".
- Label the control row "q4_0 vs f16 KV cache, reference weights — the cache every context result
  here depends on".
- A note at the axis: "reference arm UD-Q6_K_XL is 0 by construction".

**Caption.** *Mean KL divergence against the UD-Q6_K_XL reference, by arm and evaluation domain.
Points are the tool-reported mean; bars are ±1 standard error as emitted by
`llama-perplexity --kl-divergence`, which treats per-token KLD as Gaussian. n = 65,536 tokens per
cell for prose and code, 18,432 for HumanEval+ prompts. Protocol: SSA divergence, n_ctx 2,048,
q4_0 KV, seed 20260830, engine image `sha256:feb0231976b6…`. The bottom row is a control in which
the weights are not quantized at all and the only perturbation is the KV cache dtype. Shaded bands
are external reference points from published practice, not this study's criteria. Divergence is
ladder-relative: no FP16 reference fits this host, so the reference arm's own distance from the
unquantized model is unmeasured and zero by construction.*

**Alt text.** *A dot plot of KL divergence on a logarithmic axis. For each of three quantizations the
divergence rises from prose to generic code to task prompts; the ordering across quantizations is the
same in all three domains, and the error bars are smaller than the markers. A separate control point,
in which only the KV cache dtype changes, sits below the least-divergent quantization.*

**Honesty constraints.**
- The task-prompt cells come from an 18,432-token sample, not 65,536; their intervals are ~1.9×
  wider and the caption must say so. Do not equalise the marker sizes to hide the n difference.
- The external bands are cited, not adopted. LocalBench's own source disclaims the 0.01–0.03 band as
  a short-context Wikipedia-protocol artifact (METHOD-REFERENCES R5 correction) — the label must say
  "external, disclaimed by its source".
- The control row is **not a designed control** (PN-62): it was run for PN-15's KV question and is
  reused here, so it differs from the quantized cells in more than the intended variable.
- Never describe the x-axis as "distance from FP16".

---

### F2 · Where the damage is — the tail, and its control

**Tier** ESSENTIAL · **§5.1** · **Type** statistical plot, two panels · **Data** [`data/fig02-tail-amplification.csv`](data/fig02-tail-amplification.csv) (63 rows, `panel` column)

**Claim.** Quantization damage to code sits far *below* prose at the median, crosses over between the
90th and 95th percentile, and reaches 5–8× prose at the 99th — and the shape that produces this is a
property of the corpus, because a perturbation containing no weight quantization at all produces the
same shape.

**Evidence.** PN-35 (the tail), **PN-64** (median row corrected and its per-arm ordering withdrawn),
**PN-62** (the shape/magnitude separation and the control), PN-14 (the mean this decomposes).
Artifact: `data/raw/e12/ssa/ssa-kld-tables.json`, with the ten verbatim per-cell extracts in
`data/raw/e12/ssa/kld-tables/`.

**Encoding.** Two panels stacked, sharing a categorical x-axis of quantiles.
- **Panel (a) — amplification.** x: categorical, evenly spaced, `median · p90 · p95 · p99 · p99.9`
  (the `mean` and `max` rows are annotations, not x positions). y: code ÷ prose ratio of the
  per-token KL divergence at that quantile, **log scale**, 0.003 – 20. Three connected series, one
  per arm (§0.2 colours and markers). A heavy grey horizontal line at y = 1 labelled inline "code and
  prose equally perturbed"; the region below lightly shaded and labelled once at the left, "code less
  perturbed than prose".
- **Panel (b) — shape.** Same x categories. y: quantile ÷ that cell's own mean, **log scale**. Series:
  the three code cells (solid), the KV-dtype-only control (reddish purple, dotted, diamond), and the
  three prose cells drawn as a single grey band (min–max envelope) labelled "prose cells, all three
  arms".

**Annotations.**
- Panel (a): a vertical dashed rule between p90 and p95 labelled **"crossover"**, with the note
  "p90 below unity on all three arms (0.449 / 0.541 / 0.613); p95 above it on all three
  (1.527 / 1.888 / 2.184)".
- Panel (a): the three mean amplifications (1.76× / 2.30× / 2.62×) drawn as small open markers with
  leader lines, placed between the p95 and p99 ticks, labelled once: "the commonly quoted mean sits
  out in the tail".
- Panel (a), **mandatory**: the median column is drawn as a **single shaded band spanning all three
  arms**, not three separated points, annotated "median: ≈0.005× (about 200× less than prose). Print
  precision is ±3–7 % here and the arms' intervals overlap — this column cannot rank them (PN-64)".
- Panel (b): a bracket spanning the code series and the control, labelled "p99/mean ≈ 24–26 for
  quantized weights, **22.9 for the KV-only control**"; a second bracket on the prose band, "8.4–8.6".

**Caption.** *Where quantization damage lives. **(a)** Code-to-prose amplification of per-token KL
divergence by quantile of the divergence distribution, three arms, reference UD-Q6_K_XL,
n = 65,536 tokens per cell. The ordering reverses between the 90th and 95th percentile; the commonly
quoted mean (open markers) is the average of two opposite facts. The median column is drawn as a band
because the tool prints six decimals and at these magnitudes that is ±3–7 % — the arms cannot be
ranked there. **(b)** The same distributions normalised by their own mean. The code cells and a
control in which the weights are not quantized at all — only the KV cache dtype changes — have the
same tail shape (p99/mean 24.5 / 24.4 / 26.2 against the control's 22.9), while prose is flat at
8.4–8.6 across the whole ladder. Shape is a property of the corpus; magnitude is the property
quantization moves. Quantiles carry no interval: the tool attaches uncertainty to the mean only.*

**Alt text.** *Two panels. The upper shows that at the median, code tokens are perturbed roughly two
hundred times less than prose tokens; the curves cross the equal-perturbation line between the 90th
and 95th percentile and reach five to eight times prose at the 99th. The lower panel shows that this
tail shape is the same for a control perturbation that contains no weight quantization, and that
prose has a much flatter shape regardless of quantization level.*

**Honesty constraints.**
- **The median column must not be drawn as three separated points.** PN-64: the printed values carry
  one to two significant figures, half-ULP propagation gives ±7.2 % / ±5.0 % / ±2.9 %, UD-Q6_K's
  interval overlaps both others, and the only pair that separates does so in the non-monotone
  direction. The data file marks these rows `rankable_across_arms = false`.
- The prose ÷ code median contrast is **"about 200×"**. The published "100–200×" was the reciprocal
  of a rounded table cell and is withdrawn (PN-64); measured values are 199 / 181 / 206.
- Quantile rows carry `interval_basis = print_precision_half_ulp`, the mean row
  `tool_reported_se`. Do not draw them with the same visual weight without saying which is which.
- Panel (b)'s control is reused, not designed (PN-62); the caption's word is "control", the text's
  qualification is "suggestive rather than clean".
- The amplification at p99 divided by the amplification at the mean is a near-constant 2.84–3.08, so
  **the p99 row is not an independent finding** — the figure must not be captioned as though the
  domain gap strengthens with aggressiveness in the tail specifically.

---

### F3 · What each instrument bounds

**Tier** ESSENTIAL · **§5.2** · **Type** statistical plot (forest) · **Data** [`data/fig03-instrument-bounds.csv`](data/fig03-instrument-bounds.csv) (14 rows)

**Claim.** Every task instrument in this study *bounds* the quantization effect rather than
resolving it — and for several of them no outcome could have reached significance, because the
smallest attainable p is set by the discordant count.

**Evidence.** PN-22 (HellaSwag), PN-28 + **PN-40** (HumanEval+, the vacuous-null correction), PN-33 /
PN-44 / **PN-60** / **PN-63** (RULER), PN-50 (SWE-bench Verified), PN-48 (perplexity).
Artifacts: `ssa/ssa-s7-paired.json`, `s9/s9-scores.json` (`s6_paired`), the fourteen
`ruler/s12-preds-*.json` prediction files (recomputed here), `archive/ledger-data.json`.

**Encoding.** Horizontal forest plot.
- **x**: paired difference (cheaper arm − reference), in the unit named per row; **linear**,
  symmetric about 0, roughly −20 to +20 points. A heavy vertical zero line.
- **y**: categorical, one row per comparison, grouped by instrument family with a light rule between
  families: multiple-choice (6 HellaSwag pairs) · generative coding (2) · long-context retrieval (4) ·
  agentic (1) · corpus perplexity (1).
- **marks**: point estimate as a marker sized by n (three discrete sizes: n<50, n<200, n≥200), with a
  95 % interval bar. Rows without an interval (SWE-bench, perplexity — unpaired or no paired estimate
  available) use an open marker and **no bar**, with the label "no paired estimator available".
- **second channel, on the right of the panel**: a small text column per row giving
  `discordant` and `min attainable p`. Rows whose minimum attainable p exceeds 0.05 get a grey
  background stripe and the tag **"could not have reached p<0.05"**.

**Annotations.**
- The RULER MK-NIAH row (as published) is drawn **greyed and struck through**, with a callout: "as
  published: −10.0 pts, p = 0.002. Re-analysis (PN-60): every failure is a truncation; the retrieval
  claim is withdrawn."
- Directly below it, two rows that replace it: "budget-unbound items only: 0.0 pts, 55/55 both arms"
  and "reasoning-block closure: −17.0 pts [−26.6, −7.4], p = 0.0015 — a verbosity effect".
- A single boxed note: "Divergence, on the same arms, separates every pair with non-overlapping
  intervals at 3.7–11.8 σ (F1). This panel is what a task benchmark can say instead."

**Caption.** *Paired differences between the cheaper arm and the reference, with 95 % intervals,
across every task instrument in the study. Estimator: difference in paired proportions with the Wald
interval (PN-40); exact conditional McNemar p-values are given alongside the smallest p the test
could have returned at its discordant count. Six of the eleven paired comparisons could not have
reached p < 0.05 at any outcome. HellaSwag n = 400 (greedy logprob scoring); HumanEval+ n = 164
(official non-thinking preset, no speculation on either arm); RULER n = 12–100 (greedy with reasoning
enabled, 128-token budget); SWE-bench Verified n ≈ 50 with unequal denominators, shown without an
interval because no paired estimator is available; WikiText-2 perplexity Protocol 1, n = 602 windows.
The struck-through row is withdrawn as a retrieval result (PN-60) and replaced by the two rows
beneath it.*

**Alt text.** *A forest plot of paired differences between the cheapest and the reference
quantization across eleven comparisons. Almost every interval crosses zero. Several comparisons are
annotated as unable to reach statistical significance at any outcome because only two to five items
distinguished the arms. The one comparison that does separate is annotated as measuring reasoning
verbosity rather than retrieval.*

**Honesty constraints.**
- **Never print a p-value without its minimum attainable value beside it.** That is the section's
  own methodological claim; committing the error inside the figure would be fatal.
- The SWE-bench and perplexity rows are **not paired** and must be visually distinct (open marker, no
  bar). SWE-bench denominators differ across arms (49/50/49), so the difference is not over a common
  instance set.
- The HellaSwag p-values in the source artifact are chi-square approximations (0.4795, 0.1336); the
  data file carries **exact conditional** values (0.5, 0.125). Use the exact ones and say so.
- Both RULER framings must appear. Showing only the withdrawn one, or only the replacement, misstates
  the record.

---

### F4 · The reachable window is set by the tensor split, not the quantization

**Tier** ESSENTIAL · **§5.3** · **Type** statistical plot (categorical matrix + inset) · **Data** [`data/fig04-ceiling-matrix.csv`](data/fig04-ceiling-matrix.csv) (28 rows), inset from [`data/fig12b-speed-groups.csv`](data/fig12b-speed-groups.csv), summary [`data/fig04c-ceilings-summary.csv`](data/fig04c-ceilings-summary.csv)

**Claim.** On two 16 GB cards without a fast interconnect, which tensor-split ratio you pass decides
whether a context length loads at all — for three of the four arms; the smallest arm is the
counter-example and loads at the engine default.

**Evidence.** PN-6 (the rebalance), **PN-39** (the scoping and the single-attempt caveat), PN-7 (the
optimum is quant-specific and not monotone-safe), PN-42 (balance vs throughput).
Artifacts: `data/raw/e12/tsweep-v2-{Q4_K_XL,Q5_K_XL,Q6_K,Q6_K_XL}.json`.

**Encoding.** Main panel: a 4 × 7 categorical matrix.
- **rows**: the four arms in ladder order, each annotated at the right with the context at which its
  ratio sweep ran: UD-Q6_K_XL 212,992 · UD-Q6_K 262,144 · UD-Q5_K_XL 262,144 · UD-Q4_K_XL 262,144.
- **columns**: `default · 52,48 · 54,46 · 56,44 · 58,42 · 60,40 · 62,38`.
- **cell states**: `loaded` — solid fill, decode tok/s printed inside in 7 pt; `failed` — diagonal
  hatch on grey, with the failure class printed (`oom` = compute-buffer OOM); `not tested` — empty
  with a light outline. **Fill and hatch, never red/green.**

**Inset** (lower right, ~30 % width): scatter of decode throughput (y, 8–13 tok/s) against per-GPU
VRAM imbalance (x, 0–1,800 MiB) for UD-Q5_K_XL's five loading ratios at 262,144, each point labelled
with its ratio. **No trend line.**

**Annotations.**
- A bracket over the `default` column: "the engine default fails at this rung for two of the three
  arms that were tried there, and was never attempted for UD-Q6_K_XL".
- On the UD-Q4_K_XL row: "**counter-example (PN-39): loads at the default split**".
- On the UD-Q6_K_XL row: "one feasible ratio, with failures on both sides".
- Inset: an arrow to `58,42` reading "most balanced (28 MiB) and slowest (8.50 tok/s); the other four
  cluster within 3.6 %, which is inside this host's 40.7 % within-configuration noise".
- A footer strip: "every failure shown is a **single** attempt except UD-Q6_K_XL at 229,376, which
  was attempted twice. This project's own bracketing rule asks for two."

**Caption.** *Load success and decode throughput across tensor-split ratios, each arm at the context
where its ratio sweep ran. `-sm layer`, q4_0 KV cache, MTP draft depth 2, `-fit off`, `-ctxcp 4`,
official non-thinking sampling; each cell is one launch (`rep 1`) and every cell reached ≥ 0.9469 of
its window before decoding. Failure classes are read from the preserved server logs. Inset: decode
throughput against per-GPU VRAM imbalance for UD-Q5_K_XL's five loading ratios at 262,144 tokens; no
trend line is drawn because the relationship is not monotone. Single attempts: the failures are
demonstrated once each, not bracketed.*

**Alt text.** *A four-by-seven grid of quantization arms against tensor-split ratios. Most cells for
the two middle arms fail to load at the engine default and succeed at a swept ratio; the largest arm
has exactly one ratio that works, with failures on either side; the smallest arm loads at the default.
An inset scatter shows that the most balanced split is the slowest of the five that load.*

**Honesty constraints.**
- The claim in the title is **scoped**: "for three of the four arms we measured". PN-6's general form
  overreaches and PN-39 names the counter-example.
- The inset must not imply a monotone relationship between imbalance and throughput; four of its five
  points are single readings inside the noise floor (PN-42, PN-45).
- Decode values printed in cells are `rep 1` single readings under official (temperature 0.7)
  sampling. They are for orientation, not comparison — the comparison figure is F12.
- UD-Q6_K_XL's row is at 212,992, a different context from the other three rows; the row annotation
  must carry that or a reader will compare ratios across unequal windows.

---

### F5 · Speculation buys speed and spends output identity

**Tier** ESSENTIAL · **§5.4** · **Type** statistical plot, two panels · **Data** [`data/fig05-speculation.csv`](data/fig05-speculation.csv) (4 rows)

**Claim.** Speculative decoding on this engine raises throughput by up to 2.8× and *reproducibly*
changes the output on about one generated function in five; the engine itself is byte-deterministic,
so this is a different decode path, not noise.

**Evidence.** PN-23 (non-identity), **PN-26** (the determinism control that makes it deterministic
non-equivalence), PN-25 (why the S8 DFlash2 cells are excluded), PN-29 (DFlash2 measured on its own
build).
Artifacts: `s8/s8-humaneval.json` (`equivalence`, per-config decode medians), `s8/s8-scores-reparsed.json`,
`s9/s9-determinism.json`, `s9/s9-dflash.json`, `s9/s9-scores.json`.

**Encoding.** Two panels side by side over the same four categories in the same order: `no-spec ·
MTP n=2 · MTP n=4 · DFlash2 n=4`.
- **Left — throughput.** y: decode tok/s at ctx 32,768, linear 0–60. Bars at 18.46 / 37.44 / 47.03 /
  51.78, each labelled above with its speedup (1.00× / 2.03× / 2.55× / 2.80×). Axis sub-label:
  "median over 164 generations, greedy".
- **Right — output identity.** y: byte-exact reproduction of the unspeculated baseline (%), linear
  0–105, horizontal reference line at 100 %. Bars at 100.0 / 79.88 / 79.88 / 80.49 with the fraction
  printed inside (`164/164`, `131/164`, `131/164`, `132/164`). Different fill texture from the left
  panel so the two quantities are not read as one.

**Annotations.**
- Right panel, on the no-spec bar: "**self-repeat control**: the same configuration re-run a day
  later reproduced all 164 completions byte-for-byte".
- Right panel, DFlash2 bar: hatched, labelled "**engine-confounded** — baseline produced on a
  different engine build".
- A shared footnote strip: "pass@1 moves 91.5 → 90.2 → 90.9 → 90.2 on HumanEval+, a spread far inside
  ±4.6 points at n = 164. This figure is not a ranking of accuracy."

**Caption.** *Decode throughput and byte-exact reproduction of the unspeculated baseline, 164
HumanEval+ problems, UD-Q6_K at ctx 32,768, `-ts 58,42`, `-ctxcp 32`, q4_0 KV, greedy (temperature 0,
top_p 1, seed 20260830). Left: median decode rate per configuration. Right: the fraction of problems
whose completion is byte-identical to the no-spec baseline. The no-spec bar is a self-repeat control
run a day later on the same configuration, and reproduces itself exactly — so the 20 % divergence in
the speculative arms is deterministic, not stochastic. The DFlash2 bar is hatched because that arm
ran on `llama-dflash2:latest` while the baseline ran on `llamacpp-mtp:latest`, so an engine-version
difference is inseparable from the speculation effect.*

**Alt text.** *Two bar charts. The left shows decode throughput rising from about 18 tokens per second
without speculation to about 52 with the fastest speculative method. The right shows that the
unspeculated configuration reproduces its own output perfectly across runs, while every speculative
configuration reproduces only about 80 % of the 164 completions byte-for-byte.*

**Honesty constraints.**
- The four S8 DFlash2 cells recorded as `0.000 pass@1` are **excluded data** (PN-25) and appear
  nowhere; the DFlash2 bars here are S9c's, measured on the correct engine build.
- The DFlash2 equivalence figure must never be quoted beside MTP's without the engine-confound label.
- Both MTP arms diverge on 33 problems but not on the *same* 33 (Jaccard 0.610); do not let the equal
  bar heights imply an identical divergence set. Put the Jaccard in the caption's companion text if
  the figure is used to argue about mechanism.
- Speedups are against this configuration's own no-spec baseline at ctx 32,768 with a nearly empty KV
  cache. They do not transfer to a filled window (F22).

---

### F6 · The same four arms, under two kinds of instrument

**Tier** CORE · **§1, §5.2** · **Type** statistical plot, two stacked panels · **Data** [`data/fig06-two-instruments.csv`](data/fig06-two-instruments.csv) (12 rows, `panel` column)

**Claim.** The same four arms, on the same host, in the same fortnight: flat and overlapping under
three task instruments, monotone and cleanly separated under divergence.

**Evidence.** PN-22, PN-28, PN-33 (upper panel); PN-13 (lower panel).
Artifacts: `ssa/ssa-s7-results.json`, `s9/s9-scores.json`, `ruler/s12-preds-*-niah-c131072.json`
(recomputed), `ssa/ssa-kld-tables.json`.

**Encoding.** Two panels stacked, sharing a categorical x-axis of the four arms in ladder order
(UD-Q6_K_XL, UD-Q6_K, UD-Q5_K_XL, UD-Q4_K_XL); tick labels drawn only under the lower panel. Heights
roughly 55 % / 45 %.
- **Upper — task instruments.** y: accuracy (%), linear, 74–103. Three series with Wilson 95 %
  intervals: HellaSwag (all four arms), HumanEval+ base+extra (two arms), RULER S-NIAH at 131,072
  (two arms, both at 100.0 with an interval reaching down to 75.75). Marker shape distinguishes the
  series; a compact in-panel legend.
- **Lower — divergence.** y: mean KL divergence on the code corpus (nats), **log scale**. Three points
  with ±1 SE, connected. The reference arm's x position carries an open marker on the axis annotated
  "reference: 0 by construction".
- **Do not** share or twin the y-axes; the panels are comparable in *resolution*, not in magnitude.

**Annotations.**
- Upper panel: a horizontal bracket between the two HumanEval+ points labelled
  "**paired** 95 % CI on the difference: −3.28 to +2.06 points (n = 164)" — the paired interval is far
  tighter than the two independent ones and is the honest statement.
- Upper panel, on the RULER points: "both arms at ceiling; the interval bounds almost nothing at
  n = 12".
- Lower panel: "adjacent arms separated at 3.7–11.8 σ".

**Caption.** *Task-benchmark scores (upper) and code-domain KL divergence (lower) for the same four
arms. Upper: Wilson 95 % intervals; the bracket is the Wald interval on the paired per-problem
difference, which is the powered version of the same question. HellaSwag n = 400, greedy logprob
scoring; HumanEval+ n = 164, official non-thinking preset, no speculation; RULER S-NIAH n = 12 at
131,072 tokens, greedy with reasoning enabled. Lower: ±1 SE, n = 65,536 tokens per cell, SSA protocol.
The two panels use different y-scales and are not comparable in magnitude.*

**Alt text.** *Two stacked panels over the same four quantizations. In the upper panel three task
benchmarks give nearly flat lines with heavily overlapping confidence intervals. In the lower panel
KL divergence rises monotonically and steeply from the least to the most quantized arm, with error
bars smaller than the markers.*

**Honesty constraints.**
- HumanEval+ and RULER cover only two of the four arms. Do not interpolate a line across all four for
  those series.
- The RULER interval must be drawn even though both points sit at 100.0; the width is the finding.
- Never place divergence and accuracy on a twin axis.

---

### F7 · Tail shape is a corpus property

**Tier** CORE · **§5.1** · **Type** statistical plot · **Data** [`data/fig07-tail-shape.csv`](data/fig07-tail-shape.csv) (10 rows)

**Claim.** Normalised by its own mean, every cell's divergence distribution has a shape set by the
corpus and not by the perturbation: three corpora, three shapes, flat across the whole quantization
ladder within each.

**Evidence.** **PN-62** (the finding and its control), PN-35, PN-64.
Artifact: `data/raw/e12/ssa/ssa-kld-tables.json` — all ten cells.

**Encoding.** Grouped dot plot (a "small multiples of one axis" layout).
- **x**: the ratio quantile ÷ own mean, **log scale**, 0.001 – 1,000.
- **y**: categorical, ten rows grouped in three blocks by corpus: prose (3 cells), code (3 quantized
  cells + the KV-only control), task prompts (3 cells).
- **marks**: five points per row, one per statistic (median, p90, p95, p99, p99.9), joined by a thin
  line, with the statistic encoded by marker shape and a shared legend.

**Annotations.**
- Vertical guide lines at the block-median p99/mean values with labels "prose ≈ 8.5", "code ≈ 24–26",
  "task prompts ≈ 17–18".
- The control row labelled "**no weight quantization** — q4_0 vs f16 KV only. p99/mean = 22.9".
- One boxed sentence: "within a corpus the shape is flat across a 7× range of mean divergence".

**Caption.** *Divergence distributions normalised by their own mean, all ten measured cells. Within
each corpus the shape is nearly invariant across the quantization ladder, while the three corpora
differ by roughly a factor of three at the 99th percentile. The code block includes a control in
which the weights are not quantized at all and the only perturbation is the KV cache dtype; it has
the same shape as the quantized code cells. n = 65,536 tokens per cell (18,432 for task prompts).
Quantiles carry no interval — the tool attaches uncertainty to the mean only.*

**Alt text.** *A grouped dot plot showing that the ratio of each divergence quantile to its own mean
depends on which corpus was scored, not on how aggressively the model was quantized, and that a
control perturbation with no weight quantization has the same shape as the quantized cells.*

**Honesty constraints.**
- The task-prompt block is a third corpus **not analysed in PN-62**, derived here from the same
  artifact. Label it as a new derivation from committed data (zero GPU cost), not as a published
  result.
- The `max/mean` column exists in the data and must **not** be plotted: single-token maxima swing over
  three orders of magnitude (257–1,534) and would dominate the axis without carrying information.

---

### F8 · The metric pair — top-1 agreement and KLD disagree

**Tier** CORE · **§5.1, §9** · **Type** statistical plot (scatter) · **Data** [`data/fig08-metric-pair.csv`](data/fig08-metric-pair.csv) (10 rows)

**Claim.** On code, every arm shows *higher* top-1 agreement than on prose while simultaneously
showing roughly double the mean divergence — so a table reporting either metric alone inverts the
conclusion about which domain quantization hurts.

**Evidence.** PN-16, with PN-15/PN-43 supplying the control point.
Artifact: `data/raw/e12/ssa/ssa-kld-tables.json`.

**Encoding.** Scatter.
- **x**: mean KL divergence (nats), log scale, 0.002–0.05.
- **y**: top-1 token agreement (%), linear, 95.5–99.6.
- **marks**: one point per (arm, domain) cell; colour = arm, fill = domain (§0.2). Thin lines connect
  the cells of one arm across domains so the per-arm trajectory is visible.
- A grey annotation region in the upper-right quadrant: "higher agreement *and* higher divergence —
  the region a single-metric table cannot describe".

**Annotations.**
- Arrow from the prose cluster to the code cluster labelled "→ code: agreement +1.6 to +2.2 pts,
  divergence ×1.75 to ×2.62".
- One note: "the code corpus is far more predictable (reference PPL 1.18 vs 5.79), so the argmax
  usually survives while the distribution around it moves".

**Caption.** *Top-1 token agreement against mean KL divergence for every measured cell. Points to the
upper right have higher agreement and higher divergence at once: on code every arm agrees with the
reference on more tokens than it does on prose, while diverging roughly twice as far. n = 65,536
tokens per cell (18,432 for task prompts); SSA protocol, reference UD-Q6_K_XL. The mechanism —
predictability driving argmax stability — is an interpretation consistent with the perplexity gap
(1.18 on code against 5.79 on prose), not a controlled test.*

**Alt text.** *A scatter plot of top-1 agreement against KL divergence. The code-corpus points sit
above and to the right of the prose points for every quantization, meaning the cheaper metric and the
distributional metric disagree about which domain is more damaged.*

**Honesty constraints.**
- The mechanism sentence is an interpretation; the caption must keep it hedged.
- The task-prompt cells have a smaller n; mark them.

---

### F9 · What the long-context battery actually measured

**Tier** CORE · **§5.2** · **Type** statistical plot, two panels · **Data** [`data/fig09-ruler-closure.csv`](data/fig09-ruler-closure.csv) (14 rows), [`data/fig09b-ruler-mk100-paired.csv`](data/fig09b-ruler-mk100-paired.csv) (3 rows)

**Claim.** The study's published long-context separation is a difference in whether the model finished
speaking inside a 128-token budget, not in whether it retrieved the needle: `closed-and-wrong` is
exactly zero in all fourteen cells, and on the 55 items where neither arm's budget bound, both arms
score 55 out of 55.

**Evidence.** **PN-60** (the correction), **PN-63** (the fourteen-cell control), PN-44 (the superseded
result), PN-33.
Artifacts: the fourteen `data/raw/e12/ruler/s12-preds-*.json` files, recomputed here with RULER's own
`string_match_all` (reproduces every published cell score exactly) and a closure classifier on
`</think>`.

**Encoding.**
- **Panel (a) — decomposition.** Horizontal stacked bars, one per (arm, task, length) cell, 14 rows
  grouped by task. Segments, left to right: `closed and correct` (solid), `not closed but correct`
  (light), `closed and wrong` (dark — **zero everywhere, and that is the point**), `not closed and
  wrong` (hatched grey). x: number of items, 0 to n, with n printed at the end of each bar.
- **Panel (b) — the paired view of mk100.** Three 2×2 paired tables rendered as small labelled
  quadrant blocks: retrieval score (79 / 10 / 0 / 11), closure (55 / 22 / 5 / 18), and retrieval among
  budget-unbound items (55 / 0 / 0 / 0), each with its exact McNemar p.

**Annotations.**
- Panel (a): a bracket over the three single-needle rows at 8,192 / 32,768 / 131,072: "100 % correct
  **and** 100 % closed in both arms — a genuine ceiling, not a degenerate string match (PN-63)".
- Panel (a): on `variable_tracking`: "excluded from the study's comparison; 0 of 25 items fully
  correct in either arm, 0 closures — the same defect in its most extreme form".
- Panel (a): on `mkmock` (n = 3): "passes entirely from output that never finished reasoning — a
  direct demonstration that the scoring rule accepts truncated generations".
- Panel (b): "same length, same arms, same 128-token budget — only task difficulty differs".

**Caption.** *RULER outcomes decomposed by whether the model closed its reasoning block. **(a)** All
fourteen committed cells; scored with RULER's own `string_match_all` (which reproduces every published
cell score exactly) and classified by the presence of `</think>`. The `closed and wrong` segment is
zero in every cell: nowhere in this battery did the model finish reasoning and answer wrongly.
**(b)** Paired analysis of the 100-sample multi-key cell at 131,072 tokens. The published retrieval
separation (−10.0 points, exact McNemar p = 0.0020) coincides with a closure separation (−17.0 points,
p = 0.0015); restricted to the 55 items where neither arm's budget bound, the arms are identical.
Greedy with reasoning enabled and `n_predict` 128 — a sampling configuration used nowhere else in the
study.*

**Alt text.** *Stacked bars showing, for each long-context cell, how many items were answered
correctly with the reasoning block closed, correctly without closing, and incorrectly. No item
anywhere finished its reasoning and answered incorrectly. A paired panel shows that the apparent
accuracy gap between the two quantizations disappears entirely on the items where neither arm ran out
of output budget.*

**Honesty constraints.**
- The withdrawn framing must be shown as withdrawn, not deleted. PN-44's numbers are correct
  arithmetic on a compromised outcome variable.
- The comparison to Red Hat's published 85–88 % 4-bit recovery band at 128K is **void** (PN-60) and
  must not appear anywhere near this figure.
- The retrieval question at 131,072 on multi-key is *unanswered*, not answered negatively. A caption
  that reads "4-bit does not hurt retrieval at depth" is wrong.
- n = 3 for `mkmock`: it illustrates, it does not establish.

---

### F10 · The protocol swing

**Tier** CORE · **§1 or §4** · **Type** statistical plot (waterfall) · **Data** [`data/fig10-protocol-swing.csv`](data/fig10-protocol-swing.csv) (7 rows)

**Claim.** The same checkpoint on the same benchmark corpus reads as 29.1 % worse or 0.8 % worse than
its comparison ladder depending only on conventions that no published perplexity number discloses —
a 36-fold swing in the estimated effect.

**Evidence.** PN-49, with PN-48 for the ladder it is compared against.
Artifacts: `data/archive/ledger-data.json` (the GGUF ladder, Protocol 1). ⚠ **The three NVFP4 values
live only in the mirrored machine log** `data/multivac-src/multivac-CLAUDE.md` §Perplexity — the JSON
artifacts PN-49 cites (`/srv/bench/perplexity/nvfp4-vllm-ppl-protocol1.json`,
`nvfp4-vllm-ppl.json`) are **not in this repository**. See §4.1.

**Encoding.** Waterfall / step chart.
- **y**: perplexity, linear, 6.4–8.8.
- **x**: three ordered protocol states, plus a reference band: (1) as first published — corpus file A,
  160 windows, all positions from 0 with no prior context → 8.5848; (2) corpus file and coverage
  aligned to Protocol 1, still scoring all positions ≥ 1 → 8.0775; (3) full Protocol 1, half-window
  rule → 6.7073.
- A horizontal band across the whole panel at 6.6511–6.6839 labelled "the GGUF ladder on the same
  windows (UD-Q6_K_XL … UD-IQ4_XS)".
- Each step annotated with the apparent degradation against UD-Q6_K_XL: **+29.1 % → +21.4 % → +0.8 %**.

**Annotations.**
- A bracket spanning the first and last state: "**36× swing in the estimated effect, same weights**".
- Under state (2): "two conventions changed together — corpus file (297,053 → 308,707 tokens) and
  coverage (160 → 602 windows). They were not varied one at a time, so this step is not decomposable."
- A footnote: "a fourth suspected axis — tokenizer mismatch between the GGUF and HF paths — was
  investigated and **disproven**: the two tokenizations agree exactly on both files."

**Caption.** *One checkpoint, one benchmark corpus, three measurement conventions. The vLLM NVFP4 arm
was first scored at PPL 8.5848 against a GGUF ladder at 6.65–6.68, an apparent 29 % degradation;
re-scored on the ladder's exact 602 windows with its half-window rule (score positions 256… of each
512-token window, first half as context) the same weights return 6.7073, a degradation of 0.8 %. The
intermediate point changes the corpus file and window coverage together and is therefore not a
single-axis decomposition. Protocol 1 throughout the band. Measured 2026-08-28;
irreproducible-on-current-images.*

**Alt text.** *A step chart showing a perplexity estimate falling from 8.58 to 6.71 as measurement
conventions are aligned, against a shaded band showing the comparison ladder at 6.65 to 6.68. The
apparent degradation shrinks from twenty-nine per cent to under one per cent without the model
changing.*

**Honesty constraints.**
- **Three conventions, two measured steps.** The figure must not present a clean three-way
  decomposition; the middle step bundles corpus file and coverage.
- The corrected figure still places NVFP4 *below* every GGUF arm. The figure rehabilitates the
  magnitude, not the ranking.
- The original artifact self-labels `"protocol": 2`, which is wrong and unrelated to this study's
  Protocol 2. That naming collision must not propagate into the figure.
- Cross-backend: engine differences beyond quantization remain in the residual.

---

### F11 · The binding card

**Tier** CORE · **§5.3** · **Type** statistical plot (paired bars) · **Data** [`data/fig11-vram-asymmetry.csv`](data/fig11-vram-asymmetry.csv) (45 rows)

**Claim.** With layer-wise splitting and no interconnect, the limit is per-card, not aggregate: every
run failed when the heavier card filled while the lighter card still held memory that could not be
reached.

**Evidence.** PN-6, PN-7 (the mechanism, and the draft context that MTP builds against the target
model), PN-12 (the thermal consequence of an asymmetric split).
Artifacts: the four `tsweep-v2-*.json` files; card capacity 16,311 MiB from `env-manifest.json`.

**Encoding.** Horizontal paired bars ("tornado" layout).
- **y**: categorical, one row per cell, grouped by arm, sorted by context descending. Show the
  ceiling-relevant subset: every cell at each arm's headline rung (≈ 20 rows), not all 45.
- **x**: peak VRAM per card (MiB), 0–16,500, drawn as two bars per row growing from a shared centre
  line: GPU0 to the left, GPU1 to the right.
- A vertical rule at 16,311 MiB on both sides labelled "card capacity"; a second dashed rule at
  15,650 labelled "highest stable observation".
- Failed cells are hatched.

**Annotations.**
- On the widest-imbalance loading cell (UD-Q4_K_XL default, 262,144: 12,116 / 15,094): "**2,978 MiB
  stranded** on the lighter card — physically present, unreachable".
- On UD-Q6_K at `58,42` (15,322 / 15,082, imbalance 240): "rebalanced: 991 MiB of headroom recovered
  and the full native window reached".
- A boxed note: "with `-sm layer` each layer's weights **and its slice of the KV cache** live on one
  card; MTP additionally builds a separate draft context against the target model, which is why
  enabling it costs window."

**Caption.** *Peak per-GPU memory at each arm's headline context, from the 1 Hz sampler in the launch
harness, measured after a deep prefill (≥ 0.9469 of the window) rather than at load. The two RTX 5060
Ti cards have no NVLink, so with layer-wise splitting the binding constraint is the fuller card's
16,311 MiB, never the 32,622 MiB aggregate. Hatched rows failed to allocate compute buffers.*

**Alt text.** *Paired horizontal bars showing memory use on each of two GPUs for every configuration.
In the default split the second card sits at its capacity limit while the first has up to three
gigabytes free; after rebalancing both cards sit near the limit and a larger context loads.*

**Honesty constraints.**
- VRAM is **measured after a deep prefill**; load-time VRAM understates the peak. Say so.
- The layer-placement account (output layers and the draft context landing on the last device) is an
  inference from the consistent asymmetry — the server log does not state it (PN-6).
- Layer-split VRAM carries ±100–200 MiB of run-to-run noise; do not draw ranks between cells that
  differ by less.

---

### F12 · Speed does not discriminate — and the noise is not unexplained

**Tier** CORE · **§5.5** · **Type** statistical plot, two panels · **Data** [`data/fig12-decode-acceptance.csv`](data/fig12-decode-acceptance.csv) (34 rows), [`data/fig12b-speed-groups.csv`](data/fig12b-speed-groups.csv) (22 rows)

**Claim.** Between-arm decode differs by 6.7 % at the full window while within-configuration spread
reaches 40.7 % — and that spread is not host noise: decode regresses on draft acceptance at
R² = 0.83, and conditioning on acceptance collapses it to 2.7–11.2 %.

**Evidence.** PN-19 → PN-36 → **PN-45** (three passes over one measurement), PN-42, PN-18, PN-20; and
the acceptance re-analysis that reviewers C and D reached independently (`reviewer-c-corpus.md` §O-5,
`reviewer-d-adversarial.md` §3.1), reproduced here from the artifacts.

**Encoding.**
- **Panel (a) — the regression.** Scatter: x = MTP draft acceptance (0.45–0.95, linear); y = decode
  tok/s (8–17, linear). Points: all 34 successful cells with an acceptance value; the 17 cells in the
  fitted set (262,144 tokens, `-ctxcp 4`) filled, the rest open. One OLS line **with** its equation
  and R² printed inside the panel. Colour = arm, marker = arm (§0.2).
- **Panel (b) — spread, raw and conditioned.** Dumbbell chart: y = the four true repetition groups
  (arm + context + ratio + `-ctxcp`); x = spread (%), 0–45. Each row has two markers joined by a line:
  raw `(max−min)/median` and acceptance-adjusted, with the reduction printed.

**Annotations.**
- Panel (a): "`decode = 4.53 + 11.32 × acceptance` · r = 0.909 · R² = 0.827 · residual SD 0.68 tok/s
  against a raw SD of 1.57 (n = 17)".
- Panel (a): a callout on the four Q5_K_XL points sharing acceptance 0.516 — "acceptance is identical
  across every `-ts` ratio within a repetition index: it is a property of the generated continuation,
  not of the configuration".
- Panel (a): a single labelled outlier — Q5_K_XL `58,42`, 8.50 tok/s — "the one reading that survives
  conditioning: a genuine ratio effect of about −2.2 tok/s (PN-42)".
- Panel (b) header: "between-arm span at matched depth: **6.74 %**".
- A footer: "the speed probe ran under official sampling (temperature 0.7), which makes the generated
  text — and therefore acceptance — vary between repetitions. Running it greedy would have removed
  most of this variance at no cost."

**Caption.** *Decode throughput against speculative draft acceptance at the full 262,144-token window.
Estimator: ordinary least squares over the 17 successful cells at `-ctxcp 4` (three arms, five split
ratios, one to three repetitions each); the line is that fit. Panel (b): within-configuration spread
over true repetition groups — matched on arm, context, split ratio **and** `-ctxcp` — as
`(max − min)/median`, before and after adjusting each reading to its group's mean acceptance. All
cells: `-sm layer`, q4_0 KV, MTP draft depth 2, official non-thinking sampling, at ≥ 0.948 of the
window. UD-Q4_K_XL has no repetition group at this context (n = 1) and is absent from panel (b).*

**Alt text.** *A scatter plot showing decode throughput rising almost linearly with speculative draft
acceptance, explaining about eighty-three per cent of the variance. A companion panel shows that the
apparent run-to-run noise of up to forty-one per cent falls to under twelve per cent once acceptance
is accounted for.*

**Honesty constraints.**
- Three published values exist for the same quantity — 32.9 %, 46.7 %, 40.7 % — differing by
  estimator and by which cells were grouped. **Name the estimator in the figure** and use PN-45's
  `(max−min)/median`. The data file carries both.
- Do not claim the conditioned analysis resolves the arms: after adjustment the between-arm residual
  means differ by well under a tok/s, and one arm has a single reading.
- The regression is observational. Acceptance is not manipulated; it is a recorded property of each
  generation.
- These are at-depth decode rates. They must never share an axis with a depth-0 table.

---

### F13 · Speculative divergence is a hazard, not a rate

**Tier** CORE · **§5.4** · **Type** statistical plot · **Data** [`data/fig13-divergence-length.csv`](data/fig13-divergence-length.csv) (16 rows), [`data/fig13b-divergence-perproblem.csv`](data/fig13b-divergence-perproblem.csv) (164 rows)

**Claim.** "One function in five" is a fact about HumanEval+'s output-length distribution; the
transferable fact is a per-character hazard of about 3.0 × 10⁻⁴ — one divergence per ~950 generated
tokens — which means a long agentic trajectory almost certainly diverges.

**Evidence.** PN-23, PN-26 (determinism, which makes the hazard interpretable), PN-29; the
length-quartile analysis is reviewer D's §4.5, recomputed here from the committed completions.
Artifacts: `s8/s8-{nospec,mtp2,mtp4}.jsonl`, `s9/s9-dflash4-he.jsonl`, `s9/s9-nospec-r2.jsonl`.

**Encoding.** Grouped bar chart with an overlaid model line.
- **x**: quartile of the *no-spec baseline* completion length, four categories, labelled with their
  character ranges (≤464 · 465–700 · 701–989 · >989).
- **y**: divergence rate (%), linear 0–70, with Wilson 95 % intervals.
- **series**: MTP n=2, MTP n=4, DFlash2 n=4 (hatched — engine-confounded), and the no-spec self-repeat
  control at 0 % in every quartile.
- **overlay**: the constant-hazard prediction `1 − exp(−h·L)` at the quartile midpoints, drawn as a
  thin grey line, labelled "constant-hazard fit, h = 3.0 × 10⁻⁴ / char".

**Annotations.**
- On Q1 and Q4 for MTP n=2: "2.4 %" and "53.7 %".
- A callout on the fit: "observed rates fall **below** the fit at short lengths and **above** it at
  long ones — the hazard rises with position, which is what progressive numerical drift predicts and
  a verification-rule error does not".
- The control series labelled "no-spec re-run: 0 of 164, all quartiles".

**Caption.** *Divergence from the unspeculated baseline by completion length. Problems are grouped
into quartiles of the baseline completion's character count; bars are the fraction of problems in each
quartile whose speculative completion differs, with Wilson 95 % intervals; n = 41 problems per
quartile. The grey line is a constant-hazard model fitted by maximum likelihood with right censoring
at each problem's baseline length (h ≈ 3.0 × 10⁻⁴ per character, one divergence per ≈ 3,300
characters ≈ 950 tokens). The DFlash2 series is hatched because it ran on a different engine build.
The flat zero series is the no-spec self-repeat control. UD-Q6_K, ctx 32,768, greedy, seed 20260830.*

**Alt text.** *A bar chart showing that speculative decoding changes the output on about two per cent
of the shortest completions and about half of the longest, with a fitted constant-hazard curve that
under-predicts at long lengths, and a control series that is zero everywhere.*

**Honesty constraints.**
- The hazard is fitted to 164 observations with only 33 events; report it as an order of magnitude,
  not to three significant figures in the prose.
- The "hazard rises with position" reading is *evidence for* a numerical account, not a demonstration
  of it. PN-26 withdrew a mechanism once already.
- DFlash2's series is engine-confounded and must stay hatched and labelled.
- Divergence is measured on emitted text, not on logits.

---

### F14 · Draft depth: the ratio must fall, the drafter does not degrade

**Tier** CORE · **§5.4 (or appendix)** · **Type** statistical plot, two panels · **Data** [`data/fig14-draftdepth.csv`](data/fig14-draftdepth.csv) (27 rows), [`data/fig14b-draftdepth-reps.csv`](data/fig14b-draftdepth-reps.csv) (75 rows)

**Claim.** Draft acceptance falls as draft depth rises in ten of eleven genuinely adjacent pairs — but
that fall is a property of the ratio's definition, and the per-token match probability behind it is
approximately invariant, so the sweep's ranking question remains unanswerable at three repetitions.

**Evidence.** PN-32 (the sweep and the clustering lesson), PN-9 (the confound it was built to
resolve), PN-24; the arithmetic corrections (11 adjacent pairs, not 13; p = 0.0059, not 0.0017) and
the implied-q inversion are reviewer D's §3.3, recomputed here.
Artifacts: `s9/s9d-depthsweep.json`, `s9/s9e-n262k.json`.

**Encoding.** Two panels side by side, one per matched depth (131,072 and 196,608), shared y-axis.
- **x**: draft depth, categorical {2, 4, 8}.
- **y (left axis)**: draft acceptance, 0–1.
- **series**: four arms (§0.2). Behind each cell-level point, plot the **three individual repetitions**
  as small translucent markers.
- **second series, dashed, on the same axis**: the implied per-token match probability *q*, one line
  per arm, in the same colour at 50 % alpha.
- Absent cells (invalid or failed to load) marked with an open marker **on the axis** and a label —
  never plotted as zero.

**Annotations.**
- On one representative cell, two intervals drawn side by side: a thin cap of ±0.02 labelled "pooled
  over draft events (misleading)" and a wide bracket of ±0.3 labelled "between generations (honest)".
- Panel header: "acceptance falls in 10 of 11 adjacent draft-depth pairs (one-sided sign test
  p = 0.0059); the implied per-token match probability is flat to within ±0.19".
- Absent cells: "UD-Q6_K_XL at 196,608, n=8: failed to load — the draft context does not fit";
  "two cells invalidated by the generation gate (55 and 124 tokens of 512)".

**Caption.** *Speculative draft acceptance against draft depth at two matched context depths (prompt
lengths held identical at 123,670 and 186,270 tokens), four arms, each at its own Wave-1 split ratio,
q4_0 KV, `-ctxcp 32`, official non-thinking sampling, three 512-token generations per cell. Small
markers are individual repetitions. Dashed lines are the per-token draft-match probability q implied
by inverting acceptance(n) = q(1−qⁿ)/(n(1−q)), the expected acceptance ratio under
stop-at-first-mismatch verification: the ratio is bound to fall with depth for every q < 1, and q is
what carries information about the drafter. The two intervals drawn on one cell contrast a binomial
interval pooled over ~1,000–4,000 draft events with the observed spread between the three
generations; the unit of independence is the generation.*

**Alt text.** *Acceptance rates falling from about 0.8 at draft depth two to about 0.4 at depth eight
across four quantizations and two context depths, with individual repetitions scattered widely around
each point, and a dashed line showing that the underlying per-token match probability stays roughly
constant.*

**Honesty constraints.**
- **PN-32's "12 of 13 pairs, p = 0.0017" counts two non-adjacent transitions** (UD-Q6_K_XL at 131,072
  and UD-Q4_K_XL at 196,608 each skip n=4). The figure reports 10 of 11 and p = 0.0059. The data file
  contains all cells so a reader can check.
- The pooled acceptance interval must appear **only** as the labelled bad example.
- No per-arm best draft depth may be read off this figure: rep-to-rep decode spread reaches 166 %.
- The `_WARNING_best_n_per_arm_per_depth` field in the source artifact is superseded; do not use it.

---

### F15 · The HumanEval+ ladders

**Tier** CORE · **§5.2** · **Type** statistical plot, two panels · **Data** [`data/fig15-humaneval-ladders.csv`](data/fig15-humaneval-ladders.csv) (14 rows)

**Claim.** In non-thinking mode the benchmark orders the ladder correctly and separates only its
largest step; with reasoning enabled accuracy falls for every arm and the remaining fidelity signal is
carried almost entirely by how often the model emits nothing at all.

**Evidence.** PN-46 (non-thinking ladder + the context control), PN-47 (thinking mode and the empty
rate).
Artifacts: `data/archive/ledger-data.json` (`humaneval_nonthinking`, and four of seven thinking rows);
⚠ three thinking rows and the completed `mtp-Q6_K_XL` scores exist only in
`data/multivac-src/multivac-CLAUDE.md` — see §4.1.

**Encoding.** Two panels.
- **Panel (a) — non-thinking.** x: arm, ordered by bit-width (UD-Q3_K_XL, UD-IQ4_XS, UD-Q5_K_XL,
  UD-Q6_K_XL). y: pass@1 (%), 78–100. Two series (HumanEval, HumanEval+), Wilson 95 % intervals.
  Two extra points, offset and open, for the context control at ctx 32,768 and 131,072, joined by a
  bracket labelled "identical scores at 4× the window".
- **Panel (b) — thinking.** Same x extended with the vLLM NVFP4 arm; twin encoding: bars for
  HumanEval+ pass@1 (left axis, 80–92) and a line with square markers for empty-response rate (right
  axis, 0–15 %, inverted so that "better" is up on both). Series split by speculative method (MTP,
  DFlash2) with different marker shapes.

**Annotations.**
- Panel (a): "the only step larger than the interval is UD-Q3_K_XL → UD-IQ4_XS (6.1 pts against a
  ±4.6-pt half-width)".
- Panel (b): "three of four MTP arms score **identically** at 86.0 and are distinguished only by how
  often they produce nothing".
- Panel (b): a warning strip: "MTP and DFlash2 rows are not comparable at fixed quantization —
  speculation is not output-identical here (PN-23)".
- Both panels: a corner badge "pre-2026-08-29 · irreproducible-on-current-images".

**Caption.** *HumanEval+ pass@1 across the quantization ladder. **(a)** Non-thinking, greedy: the
ordering is monotone in bit-width and matches the perplexity ordering, but only the largest step
exceeds the Wilson interval at n = 164. Open markers are a context-length control — the same
quantization evaluated with a 32,768- and a 131,072-token window returned bit-identical scores.
**(b)** With reasoning enabled and a 4,096-token budget, every arm scores lower, and three of the four
MTP arms score identically on HumanEval+; the monotone signal is in the empty-response rate (right
axis, inverted), i.e. in how often the model exhausted its budget inside the reasoning block. n = 164
problems per arm; greedy temperature 0, which matches neither of the model's two documented sampling
presets, so absolute values are not comparable to published numbers. Measured 2026-08-21…28;
irreproducible-on-current-images.*

**Alt text.** *Two panels of HumanEval+ scores. The first shows a monotone rise with bit-width whose
steps are mostly smaller than the confidence intervals. The second shows that with reasoning enabled
three quantizations score identically and differ only in how often they returned an empty answer.*

**Honesty constraints.**
- Two rows are **excluded data** and must not be plotted as results: the dirty `Q6_K` run
  (43.3/43.3, 51.2 % empty) and an aborted NVFP4 run with one solution. The data file carries the
  dirty row labelled `EXCLUDED`.
- Empty responses count as failures in pass@1, so panel (b) conflates two failure modes; the empty
  column must always be visible.
- The thinking arms are confounded by speculative method.
- Wilson intervals in the data file are computed from pass counts **reconstructed** from rounded
  percentages (e.g. 90.9 % × 164 → 149); this is exact to ±1 problem and is marked in the file.

---

### F16 · The most expensive instrument inverts the ladder

**Tier** ESSENTIAL · **§Agentic behaviour** · **Type** statistical plot · **Data** [`data/fig16-swebench-verified.csv`](data/fig16-swebench-verified.csv) (8 rows)

**Claim.** SWE-bench Verified at roughly 50 instances per arm places the cheapest quantization first
— and the inversion carries no information, because a single instance is worth two points and the
interval on one arm alone spans twenty-four.

**Evidence.** PN-50, PN-58 (the ten reporting defects, including the ARM64 scoring defect that
produced two superseded generations of these numbers).
Artifacts: `data/archive/ledger-data.json` (the **superseded** ARM64 aggregates); ⚠ the final
x86_64-corrected totals and the bootstrap interval exist only in `data/multivac-src/multivac-CLAUDE.md`
— see §4.1.

**Encoding.** Dot plot with intervals.
- **y**: categorical, three arms plus a fourth row for the bootstrap estimate.
- **x**: resolve rate (%), 55–95.
- **marks**: point + Wilson 95 % interval for the final generation (filled); the two superseded
  generations shown as small grey open markers on the same rows, connected by a thin arrow to the
  final value, labelled "ARM64-scored → §13.66 → x86_64 final".
- One row shows the bootstrap interval (B = 10,000, seed 20260825) as a wider bar for comparison with
  the Wilson interval.

**Annotations.**
- A vertical band spanning the three point estimates labelled "**2.0 points** separates the arms".
- A horizontal bar labelled "**24.5 points**: the bootstrap interval on one arm alone".
- Note: "denominators differ (49 / 50 / 49) — the rates are not over a common instance set".
- Note: "SWE-bench **Verified**, not **Pro**; Qwen publishes 61.7 on Pro for this model and the two
  are not comparable".

**Caption.** *SWE-bench Verified resolve rates, non-thinking greedy, mini-swe-agent 2.4.6. Filled
markers are the final x86_64-corrected totals with Wilson 95 % intervals; grey markers are two earlier
generations of the same numbers, superseded by a host-architecture scoring defect in which three
evaluation images have no `linux/arm64` manifest and were silently under-counted. The bootstrap
interval (B = 10,000, seed 20260825) on the UD-Q6_K arm alone spans 63.3–87.8, which contains all
three point estimates several times over. Denominators differ across arms because empty patches and
infrastructure errors were excluded case by case. Measured 2026-08-26…28;
irreproducible-on-current-images.*

**Alt text.** *Three quantizations with resolve rates within two points of each other and confidence
intervals more than twenty points wide, with the cheapest quantization nominally first. Grey markers
show two earlier, superseded versions of the same measurements.*

**Honesty constraints.**
- All three generations of these numbers must be visible. Showing only the final ones hides a defect
  the paper reports as method.
- Never present the ordering as a finding, and never compare to SWE-bench Pro.
- The correction was a **scoring-host** defect, not a model effect.

---

### F17 · The thesis in one arm

**Tier** CORE · **§1, §Agentic behaviour** · **Type** statistical plot (slope/parallel-coordinates) · **Data** [`data/fig17-q3-profile.csv`](data/fig17-q3-profile.csv) (9 rows), [`data/fig17b-agentic-steps.csv`](data/fig17b-agentic-steps.csv) (4 rows)

**Claim.** One quantization is the throughput leader, scores acceptably on a standard code benchmark
and ties on perplexity — and fails every multi-step agentic task outright; only the most expensive
instrument rates it correctly.

**Evidence.** PN-51 (the T3 run), PN-52 (step counts among converging arms), **PN-61** (the withdrawn
acceptance clause), PN-46.
Artifacts: `data/archive/ledger-data.json`, `data/archive/champion-timings.json` (the degenerate
rows behind the withdrawn clause); ⚠ throughput, Protocol-2 perplexity and the step counts exist in
this repository only as prose — see §4.1.

**Encoding.** Two-column slope chart.
- **left column**: UD-Q3_K_XL's value on each instrument, normalised to the reference arm = 100 % on
  that instrument.
- **right column**: the reference arm at 100 %.
- **rows/lines**: one line per instrument, coloured by instrument class — cheap instruments
  (throughput, HumanEval, HumanEval+, perplexity, empty rate) in one colour, the expensive agentic
  instrument in another, and the withdrawn acceptance row in grey, dashed and struck through.
- The agentic line drops to 0 % and is drawn markedly thicker.

**Annotations.**
- "0 of 6 instances converged; mean 250 steps, median 250, max 250 — the harness limit. The reference
  arm converged on 6 of 6, mean 45 steps."
- On the struck-through row: "**withdrawn (PN-61)**: 1.000 acceptance at 258,779 tokens was 55
  generated tokens over 36 draft events".
- "the run was deliberately stopped at 6 of 50 instances: the remaining 44 would have cost ≈ 88 h for
  no new information".

**Caption.** *UD-Q3_K_XL against the reference arm on every instrument that measured it, each
normalised so the reference reads 100 %. The quantization leads on raw throughput, scores 84.1/81.7 on
HumanEval/HumanEval+ with zero empty responses, and ties on perplexity — and hits the 250-step agent
limit on 6 of 6 instances attempted, where the reference converged on 6 of 6 with a mean of 45 steps.
n = 6 instances, one scaffold, single seed, deliberately truncated; this supports a qualitative
disqualification, not a magnitude. The struck-through row is a withdrawn claim retained as a worked
example. UD-Q3_K_XL is not one of the paper's four arms and its GGUF is no longer on disk;
irreproducible-on-current-images.*

**Alt text.** *A slope chart in which one quantization matches or beats the reference on every cheap
benchmark and drops to zero on the single expensive agentic measure.*

**Honesty constraints.**
- n = 6, one scaffold, one seed, truncated. **No quantitative statement** about how much worse Q3 is,
  and no claim about where on the ladder failure begins — no intermediate arm was tested under this
  protocol.
- The 250-step ceiling is a harness parameter, not a model property.
- The acceptance row is withdrawn and must be drawn as withdrawn, not deleted (it is the study's
  cleanest example of a degenerate probe).
- F17b's UD-Q6_K_XL column is an approximate mean from a *different* instance set; it must be labelled
  as across-experiment.

---

### F18 · Cross-backend

**Tier** CORE · **§5.7** · **Type** statistical plot, three panels · **Data** [`data/fig18-cross-backend.csv`](data/fig18-cross-backend.csv) (8 rows)

**Claim.** Two engines reach nearly the same peak throughput by opposite routes — the larger
speculative multiplier belongs to the slower baseline — while only one of them can hold the model's
native window, and a fixed 1.19 GiB draft-worker allocation stops the same configuration on three
independent stacks.

**Evidence.** PN-55 (the speed/energy table), PN-56 (the 5.1× context gap), PN-53 (the wall), PN-54
(SGLang produced nothing).
Artifacts: `data/archive/ledger-data.json` (`speed`), `data/archive/spec-speed-metrics.jsonl`,
`data/archive/sglang-failure.txt`; ⚠ acceptance and mean-accepted-length come from prose — see §4.1.

**Encoding.** Three panels.
- **(a) throughput**: grouped bars, backend × configuration, y = decode tok/s 0–45, each bar labelled
  with its own-baseline speedup.
- **(b) energy**: same categories, y = J per token, 0–11, **modelled** — a hatched pattern reserved
  for modelled quantities plus a legend entry saying so.
- **(c) context ceiling**: horizontal bars, y = backend/configuration, x = tokens, 0–262,144, with a
  dashed rule at the model's native 262,144 and the ratio printed ("5.1× short").

**Annotations.**
- Panel (a): "vLLM's `--enforce-eager` requirement cripples its own baseline and thereby manufactures
  speculative headroom; the best absolute figures differ by 7 %".
- Panel (a): "MTP acceptance cross-validates across engines at matched depth: 0.728 (llama.cpp) vs
  0.709 (vLLM)".
- Panel (c): two zero-length bars with text — "vLLM + DFlash2: OOM, 1.19 GiB, at every utilisation
  0.78–0.97" and "SGLang 0.5.18: never started, same 1.19 GiB allocation at draft-worker init".
- A banner across all panels: "**different quantizations on different engines** — NVFP4 (W4A4, fp8 KV)
  against UD-Q4_K_XL (q4_0 KV). Backend, quantization, KV dtype and speculative method all vary at
  once."

**Caption.** *Cross-backend comparison on one probe (greedy, 3-run median, 1,024-token generation,
single stream). Panel (a): decode throughput with each configuration's speedup over its own
unspeculated baseline. Panel (b): energy per token — **modelled** from 1 Hz GPU telemetry plus RAPL
package power and a fixed platform allowance; this host has no wall-socket sensor. Panel (c): the
context each stack could actually serve, against the model's native 262,144 tokens; the vLLM figure is
a boot-verified KV-pool ceiling, not a behaviourally verified one. No single-variable conclusion can
be drawn from any pairwise comparison here. Decode is measured into a nearly empty KV cache and must
not be read as long-context throughput. Measured 2026-08-23…29;
irreproducible-on-current-images.*

**Alt text.** *Three panels comparing two inference engines: throughput, where both reach about forty
tokens per second by different speedup factors; energy per token, where the vLLM speculative
configuration is lowest; and context ceiling, where the llama.cpp path reaches the model's full native
window and the vLLM path reaches about a fifth of it.*

**Honesty constraints.**
- The 51,200-token vLLM ceiling is **boot-verified only** — no deep prefill and generation was
  performed at that window, and the battery was aborted (PN-56). The bar must be annotated
  accordingly.
- The identical 1.19 GiB figure across two unrelated stacks is **unexplained**; report it as an
  observation, not a mechanism.
- SGLang must be described as "attempted and could not be brought up", never as benchmarked and lost.
- Energy is modelled; the hatch and the legend entry are mandatory.

---

### F19 · What the measurements cost

**Tier** CORE · **§6** · **Type** statistical plot · **Data** [`data/fig19-cost.csv`](data/fig19-cost.csv) (12 rows)

**Claim.** 2.3 GPU-hours of divergence measurement separated the ladder at 3.7–11.8 σ; 14.3 GPU-hours
of task benchmarking across three instrument classes bounded it and separated nothing on its intended
construct.

**Evidence.** PN-41 (the corrected cost contrast) — **recomputed here from each artifact's own
per-cell `seconds`**, which now includes the 9.36-hour MK-NIAH cell that postdates PN-41.

**Encoding.** Horizontal stacked bar, one bar per class (divergence · task benchmark · equivalence),
segmented by experiment, x = GPU-hours 0–15. Each segment labelled with its experiment and hours.
A second, narrow column to the right of each bar carries the outcome in words.

**Annotations.**
- "divergence: 2.32 h → all three arms separated, non-overlapping intervals".
- "task benchmarks: 14.31 h → every comparison bounded, none resolved on its intended construct".
- On the RULER segment: "9.4 h of this is the single 100-sample cell at 131,072 tokens, whose
  separation turned out to be a difference in reasoning length".
- A footnote: "PN-41's published contrast (2.15 h vs ≈4.8 h) predates that cell; recomputed from the
  artifacts the ratio is 6.2×, not 2.2×".

**Caption.** *GPU wall-clock hours by instrument class, summed from each experiment artifact's own
per-cell timings (`seconds` fields in `ssa-results-parsed.json`, `ssa-s5-results.json`,
`ssa-s7-results.json`, `s9-s6.json`, `s12-ruler.json`, `s8-humaneval.json`, `s9-determinism.json`,
`s9-dflash.json`). Figures include model loading and are single measurements on one host with no
repetition; divergence runs process a fixed token budget while task runs process a fixed problem
count, which is the asymmetry the protocol was designed around. The comparison is what each
instrument bought for a few hours of the same machine, not a controlled efficiency benchmark.*

**Alt text.** *Stacked bars of GPU hours by instrument class: about two and a third hours of
divergence measurement against about fourteen hours of task benchmarking, with a note that the
divergence measurement separated every arm and the task benchmarks separated none.*

**Honesty constraints.**
- **This supersedes PN-41's published numbers** because the corpus grew after PN-41 was written. The
  figure must say so; the paper cannot print PN-41's 2.2× and this figure's 6.2× in the same document
  without reconciling them.
- Wall-clock, including model loads. Not a controlled efficiency benchmark.
- The equivalence class is shown but must not be folded into either side of the contrast: it answered
  a different question.

---

### F20 · The correction record

**Tier** CORE · **§9** · **Type** methodology diagram (timeline) · **Data** [`data/fig20-correction-record.csv`](data/fig20-correction-record.csv) (16 rows)

**Claim.** The study corrected itself sixteen times in twelve days, fourteen of them at zero GPU cost,
because per-item records were retained — and one of the corrections corrected a correction.

**Evidence.** the PAPER-NOTES corpus itself: PN-23, 26, 30, 36, 37, 39, 40, 41, 42, 43, 45, 60, 61,
62, 63, 64.

**Encoding.** Horizontal timeline, 2026-08-30 → 2026-09-03.
- **x**: date.
- **y**: three lanes — *claim withdrawn* · *claim scoped or restated* · *numbers corrected*.
- **marks**: one node per correction, labelled with the note id; an arrow from each node back to the
  note it corrects (curving left). Node fill encodes GPU cost to correct (solid = zero, outlined =
  non-zero).
- One node is drawn with a double outline: PN-45, which corrects PN-36, which was itself a correction.

**Annotations.**
- "fourteen of sixteen cost **zero GPU time** — the evidence was already on disk".
- "PN-19 → PN-36 → PN-45: three passes over one measurement produced 32.9 %, 46.7 % and 40.7 %; only
  the third named its estimator over matched cells".
- "found by: adversarial review (6) · blind structural review (3) · the author re-reading an artifact
  (3) · an integrity audit (2) · a planned control (2)".

**Caption.** *Every correction the study made to its own published notes, by date, kind and cost.
Arrows point from a correction to the claim it corrects. Fourteen of the sixteen were made at no GPU
cost, because the underlying per-item records — completions, predictions, per-cell timings, server
logs — were retained rather than only their summaries. One node corrects an earlier correction.*

**Alt text.** *A timeline of sixteen self-corrections over five days, arranged in three lanes by
whether a claim was withdrawn, scoped, or renumbered, with arrows back to the claims they correct and
a marker showing that almost all cost no additional GPU time.*

**Honesty constraints.**
- This is offered as method, not confession; the caption's tone matters, but it must not soften the
  facts. Every node names a real claim that was published inside this project and later changed.
- Do not aggregate the count into "the study was mostly right". The count is the finding.

---

### F21 · The measurement design

**Tier** SUPPORTING · **§4** · **Type** **methodology diagram** · **Data** none (all literals below; each traces to a figure above)

**Claim.** Divergence instruments draw statistical power from token count and task benchmarks from
problem count, which is why one resolves this ladder in a fraction of the other's GPU time.

**Encoding.** Single-panel schematic, landscape, three columns left to right.
- **Left — "Arms"**: four stacked boxes, least to most quantized: UD-Q6_K_XL (25.30 GB, **reference**),
  UD-Q6_K (21.98 GB), UD-Q5_K_XL (20.88 GB), UD-Q4_K_XL (17.56 GB), with a vertical arrow labelled
  "increasing quantization". The reference box is filled and annotated "all divergence is measured
  relative to this arm — no FP16 fits the host".
- **Middle — "Instruments"**, two groups divided by a rule.
  *Group A, divergence* (one box): "KL divergence vs reference · `llama-perplexity --kl-divergence` ·
  3 domains · 65,536 tokens per cell (18,432 for task prompts) · power from **token count**".
  *Group B, task benchmarks* (four boxes): "HellaSwag · n = 400 · argmax over candidates";
  "HumanEval+ · n = 164 paired · unit-tested generation"; "RULER S-NIAH / MK-NIAH · n = 12–100 · string
  match at 8K/32K/131K"; "SWE-bench Verified · n ≈ 50 · multi-step agent". Group label: "power from
  **problem count**".
- **Right — "Result"**: one box per instrument row. Group A: "separates all three arms, 3.7–11.8 σ,
  non-overlapping intervals". Group B: "1.0-pt spread, most-quantized arm nominally highest";
  "paired difference −0.61 pts, 95 % CI [−3.28, +2.06]"; "100.0 vs 100.0 at every length; the one
  separation is a budget effect"; "2.0-pt spread on a ±12-pt interval, ordering inverted".
- **Bottom band**, full width: a cost bar to scale, 2.32 GPU-hours (Group A) against 14.31 (Group B).

**Annotations.** A single sentence beneath: "the same arms, the same host, the same fortnight".

**Caption.** *The measurement design. Divergence is measured on prompt tokens against the least
quantized arm available, so its precision grows with the token budget; task benchmarks resolve
outcomes, so their precision grows with the problem count, and at the sample sizes these benchmarks
actually contain that precision is coarser than the effect. Sample sizes, intervals and costs are
those reported in Figures 1, 3, 6 and 19.*

**Alt text.** *A schematic with three columns: four quantization arms on the left, two groups of
instruments in the middle — one divergence instrument and four task benchmarks — and their outcomes on
the right, with a cost bar at the bottom showing about two and a third GPU-hours for divergence
against about fourteen for the task benchmarks.*

**Honesty constraints.**
- Every literal in this diagram must match the figure it comes from. If a number changes upstream,
  this diagram changes.
- The reference arm is not FP16; the annotation saying so is mandatory.

---

### F22 · Throughput against filled context depth

**Tier** CORE · **§5.5** · **Type** statistical plot, two panels · **Data** [`data/fig22-depth-decode.csv`](data/fig22-depth-decode.csv) (26 rows)

**Claim.** Prefill throughput falls monotonically with filled depth in every arm and at every draft
depth; decode's depth trend is not resolvable at three repetitions — and both are far below the
depth-0 rates that speed tables report.

**Evidence.** PN-32 (the sweep this uses), PN-30 (why the earlier at-depth figures were withdrawn),
PN-24 (whose ctx-32,768 half stands).
Artifacts: `s9/s9d-depthsweep.json`, `s9/s9e-n262k.json`, `s8/s8-humaneval.json`.

**Encoding.** Two panels sharing an x-axis.
- **x**: filled context depth (prompt tokens), linear, 0–260,000, with ticks at the three measured
  depths (123,670 · 186,270 · 248,527).
- **Panel (a)**: y = prefill tok/s, 450–800. One line per arm at draft depth 2 (solid), with n=4 and
  n=8 as lighter lines.
- **Panel (b)**: y = decode tok/s, 10–35. Same series. Individual repetitions plotted as small
  markers behind each point.
- A horizontal band at the top of panel (b), 18.5–47.0, hatched and labelled "**ctx 32,768,
  near-empty cache, greedy — a different protocol**".

**Annotations.**
- Panel (a): "prefill falls in every arm and at every draft depth: 782 → 650 → 507 tok/s".
- Panel (b): "at draft depth 2, decode falls with depth in three of four arms; at higher draft depths
  the acceptance lottery (F12) dominates and no trend is resolvable at n = 3".

**Caption.** *Prefill and decode against filled context depth, four arms, matched prompt lengths at
each rung (123,670 and 186,270 tokens; 248,527 for UD-Q6_K alone), each arm at its own split ratio,
q4_0 KV, `-ctxcp 32`, official non-thinking sampling, three 512-token generations per cell with
individual repetitions shown. The hatched band is the same model at ctx 32,768 with a nearly empty
cache under greedy sampling — a different protocol, shown for scale only.*

**Alt text.** *Two panels against context depth. Prefill throughput declines steadily for every
configuration; decode throughput is scattered with no clean trend, and both sit well below a shaded
band showing the much higher rates measured with an almost empty cache.*

**Honesty constraints.**
- The ctx-32,768 band is a **different sampling protocol and a different workload**; it is shown for
  scale and must be hatched and labelled, never joined to the depth series by a line.
- Do not draw a decode trend line. Three repetitions and up to 166 % spread do not support one.
- The withdrawn at-depth figures (PN-30) are not in this figure and must not be reinstated into it.

---

### F23 · Free-running generation cannot measure quantization distance

**Tier** SUPPORTING · **§9** · **Type** statistical plot · **Data** [`data/fig23-generation-saturation.csv`](data/fig23-generation-saturation.csv) (18 rows)

**Claim.** Greedy generation is a trajectory: after the first differing token the arms are continuing
different texts, so every pairwise distance saturates and the ladder ordering scrambles.

**Evidence.** PN-38.
Artifacts: `s11/s11-gen-c8192.json` (the committed generations), `s11/s11-divdepth.json`.

**Encoding.** Scatter with a categorical x.
- **x**: ladder distance between the two arms being compared (1, 2 or 3 steps).
- **y**: normalised edit distance, 0–1, with a dashed rule at the pooled mean.
- **marks**: one point per (pair, prompt) — 18 points — with the pair label; colour by pair.
- A second, small panel to the right: first-divergence character position per pair, log scale 1–1,000,
  showing every value between 2 and 126 against completion lengths of 1,093–1,918 characters.

**Annotations.**
- "the two arms **adjacent** on the ladder measure further apart (0.739 mean) than the two
  **extremes** (0.731)".
- "the reference arm opens `- Files scanned: 1000` while all three other arms open
  `- Total files: 1000` — the reference is the odd one out, which makes 'distance from the reference'
  a poor proxy for quantization distance".
- "divergence occurs at characters 2–126 of ~1,300–1,900".

**Caption.** *Pairwise distance between free-running greedy generations from a fixed prompt, four
arms, three prompts, 512 tokens each, ctx 8,192, no speculation, on an engine verified byte-reproducible
beforehand — so any difference is attributable to the quantization. Estimator: character-level
Levenshtein distance divided by the longer string. Every pair saturates in the 0.39–0.82 band and the
ordering does not track ladder distance. This is a negative methodological result: divergence must be
measured on distributions at fixed context, not on emitted trajectories.*

**Alt text.** *A scatter plot showing that the text distance between generations from different
quantizations is large and roughly constant regardless of how far apart the quantizations are on the
ladder, with divergence beginning within the first few characters.*

**Honesty constraints.**
- **PN-38's published pairwise values (0.794 / 0.779 / 0.613) are not reproducible** from the
  committed generations under this normalisation or three others tested (÷max, ÷min, ÷mean,
  1 − difflib ratio). PN-38 does not state its normalisation. The figure uses the estimator named in
  the caption and the data file; the *conclusion* reproduces under all four. Say this in the text.
- n = 3 prompts per pair, one depth. The metric failed at the cheapest rung, so no deeper slice exists.
- S11 also had a pad-sizing defect, fixed before the run these generations come from.

---

### F24 · The smallest p a paired test can return

**Tier** SUPPORTING · **§5.2, §Methods** · **Type** statistical plot · **Data** [`data/fig24-minimum-p.csv`](data/fig24-minimum-p.csv) (31 rows)

**Claim.** For paired binary outcomes the minimum attainable p-value is set by the number of
discordant pairs, not by n — so a null reported without it says nothing about the arms.

**Evidence.** PN-40, PN-22.

**Encoding.** Step plot. x = number of discordant pairs, 0–30 (linear); y = minimum attainable
two-sided exact p, **log scale**, 1 → 1e-9. Horizontal rule at 0.05, shaded region above it labelled
"no outcome in this region can reach significance". Five labelled points mark this study's own
instances: 3 (HumanEval+ base), 4 (HellaSwag, largest pair), 5 (HumanEval+ plus), 10 (RULER MK-NIAH
score), 27 (RULER closure).

**Annotations.** "with 3 discordant pairs the smallest obtainable two-sided p is 0.25; with 5 it is
0.0625; six of this study's eleven paired comparisons sit in the shaded region".

**Caption.** *The smallest two-sided exact McNemar p-value obtainable as a function of the discordant
count, with this study's own paired comparisons marked. Below six discordant pairs no outcome can
reach p < 0.05. The rule this implies: before reporting a null for paired binary data, state the
smallest effect the test could have detected — which is set by the discordant count, not by the sample
size.*

**Alt text.** *A descending step curve of the minimum achievable p-value against the number of
discordant pairs, with a shaded region marking counts too small for any outcome to reach significance,
and five of this study's comparisons falling inside it.*

**Honesty constraints.** None beyond accuracy — this figure is a mathematical fact. It must be placed
where a reader meets it *before* the study's own nulls, not in an appendix after them.

---

### F25 · The defect taxonomy

**Tier** SUPPORTING · **§9** · **Type** **methodology diagram** · **Data** none (literals from T20 in `TABLES.md`)

**Claim.** Twelve instrumentation defects cluster into three families, each of which produces
plausible-looking output rather than an obvious failure.

**Evidence.** PN-5, 10, 17, 20, 25, 27, 30, 31, 36, 38, 41, 42, 43, 45, 58.

**Encoding.** Three labelled columns, each a stack of boxes.
- **(i) an aggregate computed across cells differing in an untracked variable** — PN-20 (three
  estimators in one column), PN-30 (17-token throughput), PN-36 (four depths in one "repetition"
  group), PN-41 (a cost ratio generalised from one arm), PN-42 (an imbalance ordering), PN-45 (a
  switched estimator, inside a correction).
- **(ii) a contract documented but not asserted in code** — PN-5 (a depth gate in a docstring),
  PN-30 (a missing generation gate), PN-17 (a harness scoring a subprocess by exit code).
- **(iii) an identifier or binding that is not unique** — PN-25 (a drafter bound to the wrong engine
  build), PN-27 (a safety predicate matching its own supervisor), PN-43 (a label collision that
  silently overwrote a server log and left a well-formed file behind).
- A fourth, single box below: **PN-38 — a metric that cannot work in principle, found only by running
  it.**
- Along the bottom, a rule per family, in a distinct band: *"an aggregate is meaningful only if every
  cell entering it is identical in every dimension except the one aggregated over — and the cell key is
  where you check that"* · *"publish the enforced gate, not the intended one; assert that the
  measurement exists, not that the process exited 0"* · *"a label must include every dimension that
  varies"*.

**Caption.** *The study's instrumentation defects, grouped by mechanism. Each family produced
plausible output rather than an error: a value in the right range, a file that parses, a process that
exits zero. Offered as method — each is a trap another group would fall into.*

**Alt text.** *Three columns of defect cards grouped by mechanism — aggregates over untracked
variables, contracts not asserted in code, and identifiers that are not unique — with a rule stated
beneath each column.*

**Honesty constraints.** The register is an audit of **known** defects; it establishes that twelve
were found and fixed, not that none remain (PN-58). The diagram must carry that sentence.

---

### F26 · Perplexity cannot certify its own ranking

**Tier** SUPPORTING · **§5.2** · **Type** statistical plot · **Data** [`data/fig26-perplexity-ladder.csv`](data/fig26-perplexity-ladder.csv) (5 rows)

**Claim.** WikiText-2 perplexity reproduces the correct ladder ordering while being unable to certify
any single step of it: the whole ladder spans 0.033 and every point carries ±0.041.

**Evidence.** PN-48, with PN-49 for the cross-backend row.
Artifact: `data/archive/ledger-data.json` (`perplexity`).

**Encoding.** Dot plot: y = arm (four GGUF arms plus the re-scored NVFP4 row, visually separated);
x = perplexity, linear, 6.60–6.75, with ±SE bars. A horizontal span annotation showing the full ladder
range (0.033) drawn against a single point's interval width (0.082 = ±0.041).

**Annotations.** "ladder span 0.033 · one point's interval 0.082 · every adjacent pair overlaps, and
so do the extremes". The NVFP4 row labelled "cross-backend, re-scored on matched windows (F10); no SE
reported".

**Caption.** *WikiText-2 perplexity, Protocol 1: `llama-perplexity`, 602 chunks at n_ctx 512, batch
512, scoring the second half of each window with the first half as context; ± is the tool's own
reported standard error. The ordering is correct and no step in it is separated. The fifth row is the
vLLM NVFP4 arm re-scored on the identical windows (Figure 10). Protocol 1 only — this study contains
two other perplexity protocols that return different absolute values on the same weights and must
never share a table with these. Measured 2026-08-21; irreproducible-on-current-images.*

**Alt text.** *Four perplexity values within 0.033 of each other, each with an error bar wider than
the entire spread, plus a fifth cross-backend value slightly above them.*

**Honesty constraints.**
- **Protocol label in the figure, not only the caption.** Three protocols exist.
- Do not add Protocol 2's values (5.50–5.55) to this axis under any circumstances.

---

### F27 · KV-cache quantization is not free

**Tier** SUPPORTING · **§5.6** · **Type** statistical plot, two panels · **Data** [`data/fig27-kv-quantization.csv`](data/fig27-kv-quantization.csv) (4 rows), [`data/fig27b-kv-ppl-contrast.csv`](data/fig27b-kv-ppl-contrast.csv) (3 rows)

**Claim.** The KV-cache dtype on which every context result in this study depends moves the token
distribution about half as far as dropping a whole quantization level — while moving perplexity on the
identical pair by 0.15 %.

**Evidence.** PN-15, qualified by **PN-43** (a size comparison, not an additive currency; and the
label collision that corrupted one field), PN-62.
Artifacts: `ssa/ssa-kld-tables.json`, `ssa/ssa-results-parsed.json`.

**Encoding.**
- **Panel (a)**: horizontal dot plot on a log x-axis (0.002–0.03), four rows: the KV-only perturbation
  (0.002955) and the three weight-quantization steps (0.005829 / 0.010285 / 0.021529), each with ±1 SE.
- **Panel (b)**: two points with ±SE — reference perplexity on the code corpus under f16 KV (1.1791 ±
  0.00605) and under q4_0 KV (1.1809 ± 0.0061) — on a y-axis tight enough that the ±SE bars visibly
  overlap, annotated "+0.15 %".

**Annotations.**
- Panel (a): a bracket between the KV row and the UD-Q6_K row: "**≈ half the magnitude** of one
  quantization level, against the same reference and corpus".
- Panel (a), mandatory: "**not additive** — two KV steps do not equal one quantization step; no
  experiment here applies both perturbations together (PN-43)".
- Panel (b): "the same perturbation, seen by an averaged corpus metric".

**Caption.** *What a KV-cache dtype change costs. **(a)** Mean KL divergence on the code corpus for a
q4_0-versus-f16 KV cache with identical weights, against the three weight-quantization steps, all
measured against the same reference arm on the same corpus, n = 65,536 tokens per cell, ±1 SE.
Top-1 agreement under the KV-only perturbation stays at 99.401 ± 0.043 %. **(b)** Perplexity on the
identical pair moves from 1.1791 to 1.1809, +0.15 %: the per-token distribution demonstrably moved
while the corpus mean barely did. Measured on the reference arm only, on the code domain only, at
n_ctx 2,048 — not at the 200K+ depths where the KV cache dominates memory.*

**Alt text.** *A dot plot showing that switching the KV cache to four-bit produces about half the
divergence of dropping one whole weight-quantization level, beside a second panel showing that the
same change moves perplexity by less than two tenths of a per cent.*

**Honesty constraints.**
- **"Half the magnitude", never "51 % of a quantization level"** as a currency (PN-43). The
  "not additive" annotation is mandatory.
- Panel (b) reads the **`metrics`** field, not `metrics_reparsed`, for these two cells — the reverse
  of the rule everywhere else in that artifact, because a label collision overwrote one server log
  (PN-43). The data file records which field each value came from.
- The measurement is at n_ctx 2,048 on one domain and one arm; it does not license a claim about q4_0
  at depth.

---

### F28 · Multiplicity, and how far the intervals can be wrong before a claim dies

**Tier** CORE · **§5.2, §7** · **Type** statistical plot, two panels · **Data** [`data/fig28-multiplicity.csv`](data/fig28-multiplicity.csv) (20 rows)

**Claim.** All nine divergence separations survive Holm and Benjamini–Hochberg over the study's entire
family of nineteen inferential tests, and no task-benchmark test does — but the weakest divergence
separation dies at a clustering design effect of only 1.5.

**Evidence.** PN-13, PN-21 (the separations), PN-22, PN-28, PN-40 (the task tests), PN-32 (the sign
test), PN-60 (which test belongs in the family). The multiplicity treatment is reviewer D's §2
(`reviewer-d-adversarial.md`), **recomputed here** — with one consequential difference, below.
Artifacts: `ssa/ssa-kld-tables.json`, `ssa/ssa-s7-paired.json`, `s9/s9-scores.json`,
`ruler/s12-preds-*-mk100-*.json`, `s9/s9d-depthsweep.json`.

**Encoding.** Two panels.
- **Panel (a) — the family.** Rank-ordered dot plot: x = p-value on a **log scale**, 1e-75 to 1;
  y = the 19 tests in ascending p order. Two step lines across the panel: the Holm threshold
  `0.05/(m−i+1)` and the Benjamini–Hochberg threshold `0.05·i/m`. Points coloured by family
  (divergence / task benchmark / speculative decoding); a marker outline distinguishes pass from fail
  under Holm. The withdrawn MK-NIAH retrieval test is drawn as a 20th, greyed, off-family row.
- **Panel (b) — clustering sensitivity.** For the nine divergence separations: x = design effect
  (DEFF), log scale 1–100; y = effective σ = σ/√DEFF, log scale. One line per separation, plus two
  horizontal rules at z = 1.96 and at the Bonferroni z = 3.02 (m = 19). Mark where each line crosses.

**Annotations.**
- Panel (a): "**all nine divergence separations pass Holm**; every HellaSwag and HumanEval+ test
  fails, and could not have passed at any outcome (F24)".
- Panel (a), on rank 11: "**the draft-depth sign test fails Holm once its pair count is corrected**
  (10 of 11 adjacent pairs, p = 0.0059, threshold 0.0056); it passes Benjamini–Hochberg. Under
  PN-32's uncorrected 12-of-13 count it passed both."
- Panel (b): "the weakest separation — prose, UD-Q6_K vs UD-Q5_K_XL at 3.71 σ — falls below the
  Bonferroni threshold at **DEFF 1.5** and below z = 1.96 at DEFF 3.6. The code-domain separations
  survive to DEFF 8–36."
- Panel (b): "the tool's ± is a per-token Gaussian standard error over 32 contiguous 2,048-token
  windows of one document, so DEFF > 1 is expected and is not estimated anywhere in this study."

**Caption.** *Multiple-comparison treatment of every inferential test in the study. **(a)** The
nineteen tests ranked by p-value against the Holm and Benjamini–Hochberg thresholds at α = 0.05. All
nine divergence separations pass both; the six HellaSwag and two HumanEval+ paired tests fail both,
as they must — their minimum attainable p-values are 0.125 to 1.0 (Figure 24). The greyed twentieth
row is the withdrawn MK-NIAH retrieval test, shown outside the family. **(b)** How far the divergence
intervals can be understated before each separation dies: effective σ against a clustering design
effect, with the conventional and the Bonferroni-corrected critical values marked. The divergence
uncertainties are per-token Gaussian standard errors over contiguous windows of a single document, so
the true design effect exceeds one and is not estimated here — which is why the weakest separation is
reported as the study's most fragile claim.*

**Alt text.** *Two panels. The first ranks nineteen statistical tests by p-value against
multiple-comparison thresholds: the nine divergence separations sit far to the left and pass, while
the task-benchmark tests sit at the right and fail. The second shows how much the divergence
uncertainty would have to be understated for each separation to stop being significant, ranging from
a factor of 1.5 for the weakest to 36 for the strongest.*

**Honesty constraints.**
- **This figure reports one result reviewer D's version could not**: with PN-32's adjacent-pair count
  corrected from 12/13 to 10/11 (F14), the sign test's p rises from 0.0017 to 0.0059 and it **fails
  Holm** at its rank while still passing BH. The paper must print the corrected value.
- The DEFF panel is a **sensitivity analysis, not an estimate**. No design effect was measured; the
  panel says how fragile each claim is, not how fragile it actually is.
- The family definition must be stated. Including or excluding the withdrawn retrieval test changes
  m from 19 to 20 and moves every threshold; the sign test fails Holm under both.
- Do not present "all divergence separations survive multiplicity correction" without panel (b). The
  correction is the easy half; clustering is the hard half.

---

## 3. Figures I do not recommend, and why

Recorded so nobody re-derives them as open work.

| candidate | why not |
|---|---|
| **A per-configuration energy / J-per-token chart for the four E12 arms** | It does not exist. Wave 4 was cancelled (DEC-12); PN-11 is a host envelope over a 12-hour window mixing idle, sweeps and container cycles, and the historical J/tok table is depth-0 on a deleted image. T22 reports the envelope as a table with the modelling caveat; a chart would imply a per-arm comparison the data cannot support. |
| **Thermal asymmetry as a figure** | PN-12 is observational and confounded: the window mixes quants, ratios and rungs, and case airflow between the two slots was never controlled. One sentence in Setup, plus the T22 row. |
| **A bare speed-versus-quantization bar chart** | It would imply a ranking the data does not support (6.74 % between arms against 40.7 % within). F12 is the correct treatment, because it explains the variance rather than hiding it. |
| **Anything joining pre- and post-2026-08-29 measurements on one axis** | Different engine image; `-sm tensor` no longer reproducible on any surviving build (PN-57). Historical figures are shown in their own panels with the label. |
| **A "context ceiling by quantization" line chart** | Three of four arms reach the same native maximum, so the line is flat by construction and the interesting variable is the split (F4). |
| **The withdrawn at-depth speculative speedups (PN-24/S8)** | 17-token generations (PN-30). They appear only as a node in F20. |
| **KL divergence versus context depth** | Infeasible on this host: the tool holds a chunk's logits resident and 14 GiB caps it at n_ctx 8,192 (PN-31). One or two sentences beside the host specification, per owner direction. |
| **A RULER accuracy-recovery chart against Red Hat's published band** | The comparison is void (PN-60): their band is retrieval accuracy and this battery measured budget closure. |

---

## 4. Where the data cannot support a figure the outline seems to want

These are gaps, stated plainly, because the outline or a reviewer's expectation implies a figure that
should not be drawn.

1. **§5.1 asks for divergence at deployment depth. There is none.** Every divergence number in the
   paper is at n_ctx 2,048 — 128× smaller than the deployment window whose configuration the paper
   recommends. S10 established the instrument cannot reach further on 14 GiB (PN-31) and S11's
   replacement metric failed structurally (PN-38, F23). No figure can bridge that; the honest device
   is F23 plus an explicit limitation.
2. **§5.2's long-context leg has no retrieval result at 131,072.** PN-60 withdrew it and PN-63
   narrowed the withdrawal, but the question is *unanswered*, not answered negatively. F9 shows what
   was measured; nothing shows what a properly budgeted re-run would show.
3. **Accuracy versus context, per arm, does not exist for any arm.** The outline's threats section
   says so (item 3). There is no accuracy-vs-context figure in this programme and there cannot be one.
4. **No temperature > 0 equivalence measurement exists** (G8, cancelled under DEC-12), so F5 and F13
   are greedy-only. A figure implying speculative behaviour under the model's documented sampling
   presets would be fabricated.
5. **Per-arm best draft depth is unanswerable** (PN-32). F14 shows the acceptance relationship and the
   noise; it deliberately does not rank.
6. **The three-way protocol decomposition in F10 has only two measured steps.** A clean
   one-axis-at-a-time waterfall would require re-running the NVFP4 scoring in four configurations,
   which is not possible (vLLM images deleted).
7. **UD-Q4_K_XL has no repetition group at 262,144** (n = 1). Any three-arm speed comparison at the
   full window is two medians and one single reading, and F12's panel (b) omits it rather than drawing
   a spread of zero.

### 4.1 Provenance gaps — numbers that live in this repository only as prose

This is the most actionable finding of the extraction pass. **Seven figure/table families rest on
values that exist here only inside the mirrored machine log, not in any committed JSON or CSV
artifact.** This is the same defect PN-62 fixed for PN-35's quantile tables — a headline number whose
evidence was not in the public repository — and it should be fixed the same way, by pulling the
artifacts with `tools/sync-multivac.sh artifact` before the paper ships.

| figure / table | prose-only values | where the artifact lives on the host |
|---|---|---|
| **F10**, T18 | NVFP4 perplexity 8.5848 · 8.0775 · 6.7073, and the token/window counts | `/srv/bench/perplexity/nvfp4-vllm-ppl-protocol1.json`, `nvfp4-vllm-ppl.json`, `nvfp4-p1-token-logprobs.json` |
| **F15**, T15 | three of seven thinking-mode rows (`mtp-Q6_K_XL` completed, `dflash-IQ4_XS`, `dflash-Q4_K_XL`); the ledger's `mtp-Q6_K_XL` row is an incomplete 59-task run | `/srv/bench/evalplus_results/humaneval-thinking-v2/` |
| **F16**, T16 | the final x86_64-corrected totals 38/49 · 38/50 · 37/49 and the bootstrap interval; the ledger holds only the **superseded** ARM64 aggregates | `/srv/bench/swebench-results/verified50/per-instance-manifest.json`, `/srv/bench/bootstrap-ci.json` |
| **F17**, T17 | UD-Q3_K_XL throughput (116.9 · 54.64 tok/s), Protocol-2 perplexity, the T3 step-count table | `/srv/bench/rigor/T3-INTERROMPIDO.txt`, `n8-ctx-ceiling-20260822-0938`, `ppl-allquants-20260821-2213` |
| **F17b**, T17 | per-instance agentic step counts | `/srv/bench/rigor/` (T3 agentic data) |
| **F18**, T17 | cross-backend draft acceptance (0.728 / 0.709 / 0.714) and mean accepted length (2.46 / 3.86) — `ledger-data.json` and `spec-speed-metrics.jsonl` carry speed, power and VRAM but **not** these two columns | `/srv/bench/` speed-probe outputs |
| **T22** | the whole power/thermal envelope | `/srv/bench/power-log.csv` (gitignored by design) |

Until those are pulled, each affected figure's data file records `evidence = historical` and names the
mirrored machine log as its source. A reader of the public repository cannot check them.

### 4.2 Two published values this extraction could not reproduce

Both are recorded in the relevant figure's honesty constraints and should be resolved in the text.

1. **PN-38's pairwise edit distances** (0.794 / 0.779 / 0.613) do not reproduce from
   `s11-gen-c8192.json` under ÷max (0.739 / 0.731 / 0.562), ÷min, ÷mean, or 1 − difflib ratio. The
   note does not state its normalisation. The *conclusion* — saturation, scrambled ordering — holds
   under all four. **Fix**: state the estimator in the paper and use the recomputed values.
2. **PN-29's DFlash2 first-divergence median** is 730 in the artifact and 722.5 when recomputed from
   the committed completions (32 divergent problems, so the median is the mean of two middle values).
   Immaterial to any claim, but the paper should quote one of them consistently.

---

## 5. Data files

Thirty-eight files under [`data/`](data/), listed with row counts, hashes, source artifacts and paper
notes in [`data/INDEX.csv`](data/INDEX.csv). Regenerate with:

```bash
python3 manuscript/figures/extract.py          # write
python3 manuscript/figures/extract.py --check  # verify against the artifacts (exit 1 on drift)
```

The script is offline, stdlib-only, deterministic, and exits non-zero with a named path if any
artifact is missing. Every column carries its unit in the header; every table carries an `evidence`
column using the classes in §0.3.
