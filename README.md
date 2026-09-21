# What Benchmarks Miss

*What quantization and speculative decoding really cost Qwen3.8-27B in accuracy, context length and
generation speed — measured on two 16 GB consumer GPUs.*

## Read the papers

| | |
|---|---|
| 📄 **The report** (39 pages) | **[`manuscript/tex/main.pdf`](manuscript/tex/main.pdf)** · LaTeX source in [`manuscript/tex/`](manuscript/tex/) |
| 📄 **Companion note: serving telemetry for local LLM inference** (12 pages) | **[`docs/telemetry/article/telemetry-note.pdf`](docs/telemetry/article/telemetry-note.pdf)** · source alongside it |

The report is the study. The note is a short companion on how to measure a local llama.cpp server the
way production serving systems are measured (latency decomposition, goodput, speculative-decoding
counters, GPU energy), written from the telemetry built for this host.

> **Honest disclosure of AI assistance.** Both documents are solo, **non-peer-reviewed** technical
> writing. The measurement campaign was run by an agent-driven harness under the author's direction.
> The report was drafted with **Claude Fable 5.1** (Anthropic), numerically audited against the
> committed artifacts by a separate Claude Fable 5.1 session, and adversarially reviewed by **OpenAI
> Astra 6**; those passes led to the zero-GPU re-analysis in paper notes PN-100 to PN-103. No human
> expert has reviewed either document. The author, Luiz Henrique Simões, is responsible for all
> content. Commits co-authored by an AI assistant are marked as such. The same statement is in the
> report, Section 6.5.

## What this is

A month of measurements of one open-weight model, **Qwen3.8-27B** in Unsloth Dynamic GGUF builds,
on one desktop machine: **two RTX 5060 Ti 16 GB cards with no NVLink and 14 GiB of system RAM**. It
asks what a person running this model locally actually gives up, and gains, when choosing a
quantization, a KV-cache precision, a context length, a GPU split and a speculative decoder.

Every number is specific to this model, this machine and these llama.cpp builds. What should
transfer is the method and the failure modes.

## What it found

**Accuracy.** Task benchmarks did not resolve an accuracy ordering between a 4-bit and a 6-bit
build. HellaSwag (n=400), HumanEval+ (n=164), SWE-bench Verified (n=50), GPQA Diamond (n=198) and
the AA-LCR long-document set (n=100) all return overlapping intervals, and the nominal order flips
between instruments. Paired, HumanEval+ bounds the 4-bit to 6-bit difference at −0.6 points with a
95 % score interval of [−4.2, +2.7]. Mean KL divergence from a 6-bit reference, by contrast, orders
every adjacent pair of builds in 30 to 32 of 32 paired windows, in about two GPU-hours. It is about
twice as large on code as on prose and strongly right-skewed: most tokens barely move and a thin
tail moves a lot. **Divergence is a distance from a quantized reference, not a measure of lost
quality**; the task benchmarks are the only evidence here about whether it matters, and at their
sample sizes they bound the difference without ranking it.

**Context.** The model's native 262,144-token window fits on 2×16 GB, but for three of four builds
only after rebalancing llama.cpp's layer split by hand (`-ts`); the best ratio does not transfer
between neighbouring builds. The KV cache costs exactly 64 / 34 / 18 KiB per token at f16 / q8_0 /
q4_0 on this hybrid-attention model. The 4-bit build holds the full window with an 8-bit cache; the
6-bit build only with a 4-bit cache. Three distinct failure modes were seen (out of memory at load,
a hang during initialisation, and death at the first speculative draft after a complete prefill),
and the only serving outage was caused by **host RAM**, not VRAM: context checkpoints grow to about
1.1 GiB each at 252K tokens.

**Speed.** At the full window a smaller build is not measurably faster. Speculative decoding is
worth 3.4–4.2× at 32K filled tokens and 7.4–7.7× at 246K. On one upstream llama.cpp build, the
DFlash2 block-diffusion drafter at its design depth (7) decodes 45–65 % faster than the model's
built-in multi-token-prediction head at every depth measured, and uses 3.6 GiB less host RAM; at a
shared shallow depth the two are indistinguishable.

**Speculative decoding is not output-identical here.** At temperature 0 with a fixed seed it changes
33 of 164 HumanEval+ completions, and both configurations reproduce themselves byte-for-byte a day
later. Task accuracy does not move. The mechanism is not established; batch-shape numerics is the
leading explanation. Treat the speculative setting as part of the configuration under test.

**Protocol decides the number.** One checkpoint scored "29 % worse" or "0.8 % worse" in perplexity
than the same comparison ladder depending only on corpus file, window count and scoring rule. A
"significant" long-context retrieval loss turned out to measure a 128-token output budget, not
retrieval. A drafter looked dominated until it ran on the right engine build, at the right depth,
for more than 17 tokens.

**The study corrected itself sixteen times**, fourteen at no GPU cost because per-item records were
kept. The retractions, and the three families of harness defect behind them, are Section 14 of the
report and are offered as method.

## The configuration that came out of it

For this host, prioritising accuracy, then usable context, then speed (report Section 13):

```bash
llama-server -m Qwen3.8-27B-UD-Q4_K_XL.gguf -ngl 99 -sm layer -ts 58,42 \
  -c 262144 -fit off -fa on -ctk q8_0 -ctv q8_0 -b 2048 -ub 512 \
  -np 1 -ctxcp 4 -cram 0 \
  --spec-type draft-dflash -md Qwen3.8-27B-DFlash2-Q4_K_M.gguf \
  -ngld 99 --spec-draft-n-max 7 -devd CUDA1
```

Full 262K window, about 28 tok/s at 246K filled tokens in the matched-depth probe, 1.7 GiB of host RAM under a 252K-token
multi-turn soak. The tested fallback is UD-Q6_K with a q4_0 cache and MTP at depth 4. This selects a
complete serving configuration for one machine, not "the better quantization". Its history, including
the configurations it replaced, is in [`docs/paper/TRACK-A-DECISION.md`](docs/paper/TRACK-A-DECISION.md).

## What it does not show

- **No full-precision reference.** BF16 weights do not fit the host, so every divergence is a
  distance from a 6-bit build, on prompt tokens, at 2K tokens of context, on two corpora.
- **Long-context task accuracy is thinly measured.** RULER's multi-key retrieval question at 131K is
  open; AA-LCR covers about 100K tokens at n=100; no code-editing task was evaluated at depth.
- **The 4-bit KV cache is validated only at short context**, and outside evidence suggests much
  larger effects at depth. In the second battery, build and cache precision change together.
- **Nulls are not equality.** A one- or two-point accuracy difference could exist and would be
  invisible to every task instrument run here.
- **Everything before 2026-08-29 is marked historical**: the engine image that produced it was
  deleted, so those rows cannot be reproduced on current builds and are never mixed with later ones.
- One model, one machine, one engine family, mostly one seed, single-stream speed only, no wall-power
  sensor. The model card's own benchmarks (LiveCodeBench, SWE-bench Pro, Terminal-Bench) were not run.

## Where things are

```
manuscript/tex/            the report: LaTeX source and main.pdf
manuscript/arxiv-submission/   the flat arXiv upload package
docs/telemetry/article/    the companion telemetry note: source and PDF
docs/paper/                findings, one note each: PAPER-NOTES.md (PN-1..PN-103), method references,
                           the configuration decision and its amendments
docs/build-stream/         how the work was run: plan, decision log (DEC-*), ledger (L-*)
data/raw/e12/              evidence: per-cell artifacts, harness source, quarantined data,
                           s15/ (second battery), ssa/ (divergence)
data/raw/historical/       per-instance evidence from before 2026-08-29
data/archive/, data/multivac-src/   superseded summaries and read-only mirrors of the host's own logs
tools/analysis/            re-analysis scripts
```

The trail from any number in the report runs: report section → paper note → artifact. Notes that turned
out wrong are still there, marked as superseded by the note that corrected them.

## Data availability

Everything the report's claims rest on is in this repository, with one class of exception named below (raw server logs). What is not here is either
regenerable from what is, or too large to distribute — and in both cases it is pinned by checksum,
so a third party can verify they hold the same bytes.

| layer | where | what it is |
|---|---|---|
| **Item-level results** | `data/raw/e12/`, `data/raw/historical/` | Per-cell JSON: metrics, return code, wall-clock seconds, context depth, KV dtype, tensor split. RULER carries per-prediction files. |
| **Evaluation harness** | `data/raw/e12/harness-src/` | The exact scripts that produced the cells — not a cleaned-up rewrite. |
| **Figure data** | `manuscript/figures/data/` | One CSV per figure, plus `INDEX.csv` and `extract.py`, which regenerates every CSV from the raw layer. |
| **Environment provenance** | `data/raw/e12/env-manifest.json` | Engine images by RepoDigest; GGUFs by sha256 and byte count. |
| **Second battery** | `data/raw/e12/s15/` | Context × KV map, matched-depth speed probe, soak records, three judge outputs, and `answers-meta/`: 756 AA-LCR and GPQA answer records with all benchmark and model text removed (ids, configuration, timings, energy, correctness). |
| **Re-analysis** | `tools/analysis/`, `data/raw/e12/ssa/ssa-kld-paired-windows.json` | The paired window-level divergence analysis (PN-100) and its script. |
| **Energy series** | `data/raw/e12/power-log.csv.gz` | 778,727 rows at 1 Hz, 2026-08-27 to 2026-09-05. Datasheet alongside it. |
| Model weights | *not distributed* | Published Unsloth GGUFs, 17–25 GB each; pinned by sha256 in the env manifest. |
| Divergence bases | *not distributed* | `.kld` logit files, ~11 GB each; regenerable with the harness. |
| Server logs | *not distributed* | Path and byte count recorded per cell in the tsweep and SSA JSONs. |

**Reproducing a cell.** Every cell records the full `docker run` invocation that produced it —
image digest, model path, context length, KV dtype, seed, tensor split. Pull the pinned image,
fetch the GGUF whose sha256 matches the manifest, re-issue the command.

**Irreproducible-on-current-images.** Results before 2026-08-29 are labelled as such and are never
mixed into a table with current ones: the engine image behind every tensor-split and every
262,144-token result was deleted, along with two GGUFs (PN-57).

**Paths in raw logs.** Raw artifacts contain absolute paths of the form `/home/multivac/…` and
`/srv/bench/…`. `multivac` is the name of the measurement host and of its Linux account. Raw artifacts
are published as they were written and are not edited after the fact.

## Citing and licence

See [`CITATION.cff`](CITATION.cff). Text and data are CC BY 4.0; code is under the licence in
[`LICENSE-CODE`](LICENSE-CODE). Correspondence: luizhenriquesimoes@usp.br · simoeshz@gmail.com.
