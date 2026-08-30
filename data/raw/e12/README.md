# `data/raw/e12/` — Wave-1 (E12) evidence, pulled from multivac

Selective evidence pull under DEC-5 (`sync-multivac.sh artifact`): the documentation sync carries
docs only, so measurement artifacts are copied here per-need and cited by paper notes and the
ledger. Source of record remains `/srv/bench/e12/` on multivac.

**Pulled 2026-08-30T03:35Z (ledger L-5)** — read-only `cat` over ssh; no checksums recomputed on
the host, because the T4/T5 sweep was live and disk I/O perturbs a running measurement.

| file | what it is | status when pulled |
|---|---|---|
| `WAVE1-REVIEW.md` | review-and-repair pass 02:30–03:10Z; 8 defects (D1–D8) with root causes and fixes | final |
| `wave1-summary.json` / `.md` | aggregator output (`summarize_wave1.py`): per-quant ceiling, best ratio, decode at depth, gain vs default split | **partial** — Q5_K_XL only; regenerate when the sweep ends |
| `tsweep-v2-Q5_K_XL.json` | full `-ts` sweep, 10 cells | **complete and valid** |
| `tsweep-v2-Q6_K_XL.json` | `-ts` sweep + G21 bracket | **IN-FLIGHT SNAPSHOT** — 5 cells at 196,608; the 212,992 bracket had not landed |
| `validate-v2.json` / `-selftest.json` | Phase-2 harness gate: C1–C4 positive run + F1–F4 negative controls | final, gate green |
| `pads-manifest.json` | all 9 ladder pads rebuilt after the PN-5 defect, each verified at ~0.945 of its window | final |
| `env-manifest.json` | provenance: GGUF sha256/sizes, image ids, `deleted_items[]` with `deleted_utc` | live (delete-1b pending) |
| `sweep-v2.json`, `quiesce-state.json` | disk-sweep state; legacy-orchestrator quiesce pids + restore command | live |
| `quarantine/` | evidence kept, never deleted: shallow-prefill cells (PN-5), wrong-direction ratio cells (DEC-7), runner-race cells (PN-10) | final |
| `logs/` | runner + supervisor logs for the whole wave | live |

`tsweep-v2-Q6_K_XL.json` and anything marked *live* are snapshots of files still being written.
Re-pull before citing them as final; cite `WAVE1-REVIEW.md` and `tsweep-v2-Q5_K_XL.json` as-is.

## `harness-src/`

The repaired Wave-1 harness as it stood at the pull (`lib_e12.py`, `pad_e12.py`, `tsweep_v2.py`,
`validate_v2.py`, `summarize_wave1.py`, `test_wave1.py`, runners and sweep scripts). Kept as
**evidence of method**, so a paper claim can be traced to the code that produced it.

> Deliberately NOT placed in a top-level `experiments/` directory. `sync-multivac.sh push` copies
> `$REPO/experiments` onto `/srv/bench/e12` — creating that directory here would make any later
> push overwrite the live harness, and the sweep is running against it. If the harness ever needs
> to be edited from this repo, quiesce the runner first.
