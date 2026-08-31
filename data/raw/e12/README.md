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

---

## Added after the Wave-1 pull

The table above describes the 2026-08-30T03:35Z pull only. Everything below landed later; all of it
is **final**, none of it is an in-flight snapshot.

| path | what it is |
|---|---|
| `tsweep-v2-Q4_K_XL.json`, `-Q6_K.json`, `-Q6_K_XL.json` | the remaining three `-ts` sweeps, complete — Q5_K_XL's was already final at the first pull |
| `wave1-summary.{json,md}` | regenerated over all four arms. ⚠️ **Its decode column mixes three estimators** (PN-20) — superseded, kept as-is, not silently edited |
| `ssa/ssa-results-parsed.json` | SSA S2/S3/S4: KLD + top-1 + PPL per arm per domain, recovered by `ssa_reparse.py` after the `±` parser defect (PN-17) |
| `ssa/ssa-results.json` | the raw harness output, with the empty metric fields the defect produced — kept as the evidence for PN-17 |
| `ssa/ssa-s5-results.json` | S5, divergence over the 164 HumanEval+ task prompts (forced-completion method) |
| `ssa/ssa-s7-results.json`, `ssa-s7-paired.json` | S7 HellaSwag n=400 × 4 arms, plus the recovered per-task vectors and McNemar analysis |
| `s8/s8-humaneval.json` | S8 phase 1: 164 problems × 4 spec configs, with the `equivalence` block (PN-23) |
| `s8/s8-{nospec,mtp2,mtp4,dflash4}.jsonl` | **the per-problem completions** — the primary evidence for PN-23; the equivalence claim is re-derivable from these alone |
| `s8/s8-*-sanitized*.json*` | evalplus sanitize + evaluate output per arm |
| `s8/s8-scores.json` | pass@1 per arm. ⚠️ `dflash4` reads 0.000 — **that is a load failure, not a score** (PN-25) |
| `s8/s8-atdepth.json` | S8 phase 3: each spec config at 262,144 filled to 93.9 % |
| `s7-data-provenance.json` | HellaSwag/Winogrande fetch with sha256 pins |
| `quarantine/empty-serverlogs/REGISTER.json` | 7 race-residue empty logs, quarantined rather than deleted |
| `harness-src/{ssa_kld,ssa_s5,ssa_s7,s7_paired,ssa_reparse,s8_spec}.py`, `s8_chain.sh` | the code that produced all of the above |

**Serverlogs are not here.** `*.serverlog` is gitignored (they reach hundreds of MB); the raw tool
output every number was parsed from lives at `/srv/bench/server-timings/` on the host, and each
artifact's per-cell metadata records its log path and byte count. That preservation rule is the
only reason PN-17's lost metrics were recoverable and PN-25's five load failures were diagnosable.
