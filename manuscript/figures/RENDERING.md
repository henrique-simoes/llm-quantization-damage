# Rendering these figures with PaperBanana

Figures for this report are to be produced with **PaperBanana** (R11: paper arXiv 2601.23265, Zhu,
Meng, Song, Wei, Li, Pfister & Yoon; community open implementation
`github.com/llmsresearch/paperbanana`, MIT, which states it is **not affiliated** with the original
authors). This file is what a person with API keys needs in order to render the programme in
[`FIGURE-PROGRAMME.md`](FIGURE-PROGRAMME.md) without asking a question.

---

## 1. What I verified, and what I did not

**Verified**, by fetching `https://raw.githubusercontent.com/llmsresearch/paperbanana/main/README.md`
on 2026-09-03 and reading it in full:

- Installation (`pip install paperbanana`, Python 3.10+), and a Docker path.
- The command set: `generate` (methodology diagrams), `plot` (statistical plots), `batch` and
  `plot-batch` (manifest-driven), `composite`, `evaluate`, `polish`, `studio`, `setup`, `venues`,
  `data`, `orchestrate`, `batch-report`, `sweep`, `sweep-report`.
- The flags tabulated in §3 and §4 below, including the manifest key names for both batch paths.
- Provider requirements: OpenAI (`gpt-5.2` + `gpt-image-1.5`, the default), Google Gemini
  (`gemini-2.5-flash` + `gemini-3-pro-image-preview`, free tier), Atlas Cloud, Azure OpenAI/Foundry
  (`OPENAI_API_KEY` + `OPENAI_BASE_URL`), OpenRouter.
- **That statistical plots need only a VLM provider**: the README states plots are "rendered via
  VLM-generated matplotlib code — no image-generation provider or credentials are required." Diagrams
  need both a VLM and an image provider.
- Venue style packs: built-in `neurips`, `icml`, `acl`, `ieee`, plus user packs under
  `~/.config/paperbanana/venues/`.
- Output layout: `outputs/run_<timestamp>/final_output.png` with intermediate iterations and metadata;
  batches under `outputs/batch_<id>/run_<id>/` with `batch_report.json`.

**Not verified.** I did not install or run the tool — it is not installed on this host and must not be
(owner constraint), and no credential exists here. Specifically I did **not** verify: the arXiv
paper's method beyond the README's description; the critic loop's actual behaviour; the planner's
preferred prompt structure (the intents below are written as ordinary, complete figure descriptions,
which is what the README's examples use); whether `paperbanana plot` accepts `--venue` and
`--aspect-ratio` — the README lists those for `plot-batch` and `polish` but **not** in the `plot` flag
table, so §4 uses `plot-batch` when a venue is wanted; per-call cost; and version pinning behaviour.
**Nothing in this file invents an API detail.** If a flag below is rejected, prefer the README over
this file and tell the owner.

**Reproducibility caveat that belongs in the paper.** These figures are not reproducible from this
repository alone: generation depends on third-party hosted models whose versions change, and it is not
deterministic. The *measurements* are unaffected — every figure draws on a CSV in
[`data/`](data/) which does ship, and [`extract.py`](extract.py) regenerates those from the artifacts
offline. Ship the specification and the CSV beside each figure so a reader can regenerate it with any
tool. (This is already recorded in `manuscript/references/PROVENANCE.md` §8.)

---

## 2. Prerequisites

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install paperbanana                 # add [studio] for the local web UI
export GOOGLE_API_KEY=...               # free tier is sufficient for the plot path
# or: export OPENAI_API_KEY=...         # required for the diagram path's image model
paperbanana setup                       # optional interactive wizard for Gemini
```

Then, from the repository root:

```bash
python3 manuscript/figures/extract.py --check   # MUST pass before rendering anything
```

If `--check` reports `DIFF` or `MISS`, the CSVs are out of step with the artifacts. Re-run without
`--check`, review the diff, and only then render — a figure rendered from a stale CSV is worse than no
figure.

---

## 3. Which path each figure takes

PaperBanana treats the two paths differently and they must not be mixed in one request.

| path | command | figures |
|---|---|---|
| **statistical plot** (CSV → VLM-generated matplotlib; VLM provider only) | `paperbanana plot` / `plot-batch` | F1, F1b, F2, F3, F4, F4-inset, F5, F6, F7, F8, F9, F9b, F10, F11, F12, F12b, F13, F14, F15, F16, F17, F18, F19, F22, F23, F24, F26, F27, F27b, F28 — 30 items in `plots.yaml` |
| **methodology diagram** (text → planner → stylist → visualizer → critic; needs an image provider) | `paperbanana generate` / `batch` | F20, F21, F25 |

Two figures are natural composites and can be produced either as one request with a `panel` column in
the CSV, or as two plots stitched with `paperbanana composite`: **F2** (panels a/b), **F6** (upper /
lower), **F9** (decomposition / paired), **F12** (regression / spread), **F18** (three panels), **F22**
(prefill / decode), **F28** (family / sensitivity). Prefer the single request first; fall back to
`composite --layout 1x2` if the model crowds the panels.

---

## 4. Rendering

### 4.1 The whole plot programme in one batch

```bash
paperbanana plot-batch \
  --manifest manuscript/figures/paperbanana/plots.yaml \
  --venue multivac --iterations 3 --optimize --format png \
  --output-dir manuscript/figures/rendered
paperbanana batch-report --batch-dir manuscript/figures/rendered/batch_<id> --format markdown
```

`plots.yaml` carries one item per figure: `id`, `data` (relative to the manifest's own directory) and
`intent`. The intents are written out in full there — each states the chart type, the axes with units
and scale, the series and their encodings, the annotations that must appear, the caption to render,
and the constraints that must not be violated.

### 4.2 A single figure

```bash
paperbanana plot \
  --data manuscript/figures/data/fig02-tail-amplification.csv \
  --intent "$(python3 - <<'EOF'
import yaml,sys
m=yaml.safe_load(open('manuscript/figures/paperbanana/plots.yaml'))
print(next(i['intent'] for i in m['items'] if i['id']=='F2'))
EOF
)" \
  --iterations 3 --output manuscript/figures/rendered/F2.png
```

### 4.3 The three diagrams

```bash
paperbanana batch \
  --manifest manuscript/figures/paperbanana/diagrams.yaml \
  --venue multivac --iterations 3 --optimize --format png \
  --output-dir manuscript/figures/rendered
```

`diagrams.yaml` points at three source-context files in the same directory
(`diagram-F20.txt`, `diagram-F21.txt`, `diagram-F25.txt`), each of which is the figure's full
description written as prose for the planner, with its caption supplied separately as the manifest's
`caption` field.

### 4.4 House style — use the venue pack, not repetition

The per-figure intents in `plots.yaml` carry only figure-specific instructions and constraints; the
house style is **not** repeated in every intent. It lives in a venue pack in this repository, which is
the mechanism PaperBanana provides for exactly this:

```bash
mkdir -p ~/.config/paperbanana/venues/multivac
cp manuscript/figures/paperbanana/venue-multivac/* ~/.config/paperbanana/venues/multivac/
paperbanana venues list                      # confirm "multivac" is listed as a user pack
paperbanana plot-batch --manifest manuscript/figures/paperbanana/plots.yaml --venue multivac ...
paperbanana batch      --manifest manuscript/figures/paperbanana/diagrams.yaml --venue multivac ...
```

The pack contains `plot_style_guide.md` (palette, marker and line assignments per arm, the
greyscale rule, and seven non-negotiable rules including "do not rescale to make small error bars
visible" and "do not add a trend line unless asked"), `methodology_style_guide.md` for the three
diagrams, and `venue.yaml`. `paperbanana venues init` is **not** needed — the files are already
written; copying them into the user venue directory is enough. If the installed version rejects a
user pack, fall back to `--venue multivac` and paste the palette block from
`plot_style_guide.md` into each request.

---

## 5. Verification checklist

Run this against **every** rendered figure before it enters the manuscript. A figure that fails any
item is rejected and re-requested, not patched by hand — except where noted, since the plot path emits
matplotlib code that can be edited directly.

**Per figure**

- [ ] Every plotted value matches the source CSV. Spot-check at least the extremes and one middle
      value of each series against `data/figNN-*.csv`.
- [ ] No series, row or category present in the CSV is missing from the figure, and none has been
      invented.
- [ ] Axis scales are as specified (several figures are explicitly **log**: F1, F2, F6 lower, F7, F26
      x-range, F28 both).
- [ ] Units appear in the axis labels.
- [ ] n appears in the caption or the legend for every series.
- [ ] The estimator is named (Wilson / Wald paired / ±1 SE / median-of-3 / OLS).
- [ ] The protocol label appears **in the figure**, not only in the caption, wherever two protocols
      could be confused (F5, F9, F10, F22, F26, T18's figures).
- [ ] Pre-2026-08-29 rows carry `irreproducible-on-current-images` (F10, F15, F16, F17, F18, F26).
- [ ] Colour-blind check: render to greyscale and confirm every series is still distinguishable by
      shape or line style alone.
- [ ] The caption is the one in `FIGURE-PROGRAMME.md`, not one the critic invented.

**Honesty constraints — check the specific ones for the figure, and always these**

- [ ] **F2**: the median column is a single band across all three arms, not three separated points.
- [ ] **F3, F24**: no p-value appears without its minimum attainable value.
- [ ] **F4**: the inset has **no** trend line.
- [ ] **F1, F6**: error bars smaller than the markers have not been enlarged or rescaled away.
- [ ] **F5, F13**: the DFlash2 series is hatched and labelled engine-confounded.
- [ ] **F9**: both the withdrawn framing and its replacement are present.
- [ ] **F14**: the pooled acceptance interval appears only as the labelled bad example.
- [ ] **F17**: the withdrawn acceptance row is struck through, not removed.
- [ ] **F18**: modelled quantities (power, J/token) are hatched and the legend says "modelled".
- [ ] **F22**: the ctx-32,768 band is hatched, labelled as a different protocol, and not joined to the
      depth series.
- [ ] **F28**: panel (b) is labelled a sensitivity analysis, not an estimate.
- [ ] No figure plots a withdrawn result as a finding (only F20 and F17 show withdrawn material, both
      labelled).

**Per batch**

- [ ] `extract.py --check` passed immediately before rendering.
- [ ] `batch_report.json` retained beside the images, and the provider and model names recorded in the
      manuscript's tool-disclosure note (arXiv's generative-AI policy).
- [ ] The rendered files, the CSVs and this specification travel together in the artifact release.

---

## 6. If the tool fights a constraint

The plot path emits matplotlib code, so three of the constraints above are cheaper to enforce by
editing the emitted script than by re-prompting:

1. **Error-bar rescaling** (F1, F6). If the stylist has expanded the axis so the ±SE bars are visible,
   fix the axis limits in the emitted code and re-run it locally.
2. **An unrequested trend line** (F4 inset, F22 panel b). Delete the line; do not accept "it looks
   better with it".
3. **A rewritten caption.** Replace with the caption from `FIGURE-PROGRAMME.md` verbatim.

If a *diagram* comes back with an invented number, discard it — do not correct it in an image editor.
Every literal in F20, F21 and F25 traces to a figure or table, and a diagram that has drifted from
them is evidence of a planner hallucination that will recur.

`paperbanana polish --input <figure>.png --venue multivac` is available for style-only touch-ups; it
requires an image-edit-capable provider (Gemini image models) and must not be used on a figure whose
values have already been checked, because a guided edit can move rendered text.
