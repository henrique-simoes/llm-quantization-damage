# `data/archive/` — pre-E12 evidence

Historical run data from the waves that preceded the E12 harness (roughly 2026-08-20 to
2026-08-29). Kept because the technical report's prior-work sections cite it and because the
project's preservation rule forbids deleting measurements. **Nothing here is authoritative for a
current claim** — the E12 corpus in `../raw/e12/` supersedes it on every axis it touches.

Consolidated here 2026-08-31 from loose files scattered at the top of `data/`. Paths in ledger
entries and paper notes written before that date use the old locations; the remap is below.

| now | was | what it is |
|---|---|---|
| `aug20-mtp-ablation.txt` | `data/` | 2026-08-20 MTP variant ablation @ctx 8192 |
| `aug20-splitmode-matrix.txt` | `data/` | 2026-08-20 split-mode matrix @ctx 32768 — the origin of "`-sm layer` only" |
| `champion-timings.json` | `data/` | 30 structured agentic run timings from `champion-20260821` |
| `ledger-data.json` | `data/` | machine-readable metric snapshot; **carries known defects** — see `../multivac-src/multivac-CLAUDE.md` §"Known instrumentation defects" |
| `spec-speed-metrics.jsonl` | `data/` | speculative-decoding speed rows, depth-0 |
| `sglang-failure.txt` | `data/` | the 2026-08-23 SGLang bring-up failure, kept as a negative result |
| `experiment-reports/all-reports.tar.gz` | `data/experiment-reports/` | bundled early experiment reports |
| `orchestrator-snapshot/` | `data/orchestrator/` | one-off snapshot of the legacy durable worker (`worker.sh`, `lib.sh`, `watchdog.sh`) |

## Two warnings that travel with this directory

1. **Every number produced before 2026-08-29 came from a deleted engine image**
   (`llamacpp-dflash2-pr27342:1deefcc-sm120-cuda128-abi`), which is also the only image on which
   `-sm tensor` ever worked. Those rows are **irreproducible-on-current-images** and must carry
   that label in any table.
2. **Depth-0 vs at-depth.** Speed rows here measure decode into a nearly empty KV cache in a large
   allocated window. At a genuinely full window the same configuration is 3–5× slower. Never place
   these in a table with the E12 at-depth figures.

The legacy orchestrator that produced much of this is **quiesced**, not removed; restore state and
command are in `../raw/e12/quiesce-state.json`.
