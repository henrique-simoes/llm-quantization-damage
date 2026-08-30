# Wave 1 (E12) — review and repair pass, 2026-08-30

Reviewer: Claude Code session on multivac, 2026-08-30 02:30–03:10 UTC.
Scope: review the in-flight Wave-1 tensor-split rebalance work, repair what was wrong, and
leave the experiments ready to run and to be aggregated into an answer.

**Verdict: the harness design is sound; six defects were found and fixed, one of which was
silently corrupting the measurement and one of which would have produced a false negative on
the highest-fidelity quant. Q5_K_XL's result survives review intact and is a new finding.**

---

## What was in flight when the review started

A chained pipeline (`Q5_K_XL → Q4_K_XL --redo → Q6_K --redo → Q6_K_XL --redo → validate`)
launched 2026-08-30 00:29 UTC. Q5_K_XL had completed; Q4_K_XL was 4 cells into its re-run.
The re-run existed because of a real bug already fixed by the previous session: `launch()`
glued the tensor-split value to `-c` (`-ts 54,46-c 212992`), so every `-ts` cell of the first
pass died on `error: invalid argument: 212992`. That fix is correct and is covered by a test.

---

## Defects found in this review

### D1 — pad builder returned short pads, silently (HIGH, corrupted measurement)
`pad_e12.build()` bisected inside the FIXED bracket `[0.9, 1.15] × cpt × target`, where `cpt`
was calibrated on `text[:200_000]`. The corpus is **~2.9 chars/token in its first 200 kB**
(dense django source) and **~4.45 chars/token thereafter**, so for several targets the true
cut lies **outside** the bracket. The loop then pinned at the bracket edge, assigned
`best, best_n = t, n_tok` **unconditionally** (last probe, not closest), and returned short
with no error.

Measured impact: `pad_201830` delivered **169,823 tokens instead of 201,830 (−15.9 %)**. The
Q4_K_XL cells recorded `prefill_frac 0.7973` — i.e. decode was measured at **79.7 % of the
window**, not the ~94.7 % the harness contract claims, while Q5_K_XL's cells were at 0.948.
Since decode at depth is strongly depth-dependent (37.22 → 7.19 tok/s across depth on Q6_K)
and peak VRAM is sampled across the prefill, **both the speed row and the ceiling verdict were
optimistic, and the two quants were not comparable to each other.**

Two of the five pads on disk were affected (`pad_201830`, `pad_217395`); the other three had
been copied from e11, whose builder used an unbounded proportional seek and was correct.

*Fix:* unbounded proportional seek (converges regardless of `cpt` error), keep the **closest**
candidate, **raise** rather than return short, and validate cached pads on read so the bad
files on disk self-heal. All 9 pads the ladder can need were rebuilt and verified — every one
now lands within tolerance at ~0.945 of its window (`pads-manifest.json`).

### D2 — the ≥90 % depth gate was documented but never enforced (HIGH)
`tsweep_v2.run_cell` documents "deep prefill: >=90 % of the window (behavioural gate)" and
records `prefill_frac`, but nothing ever compared it to 0.90. D1 was therefore invisible.
*Fix:* a cell now FAILS as `pad-too-short` below 0.90, `prefill_frac` is printed in the
per-cell log line, and the rule is recorded in the artifact's `policy` block.

### D3 — Q6_K_XL's ratio list pointed the wrong way (HIGH, false negative)
G21's ratio list was `["58,42", "62,38", "60,40"]` — every entry pushes **more** model onto
GPU0. But the measurement shows 58,42 already **overshoots** for this quant:

| Q6_K_XL | GPU0 | GPU1 | imbalance |
|---|---|---|---|
| default split (E11a @245,760 no-spec) | 14,356 | 15,838 | GPU1 heavy 1,482 |
| `-ts 58,42` (measured here @196,608) | 15,036 | 12,276 | **GPU0 heavy 2,760** |
| `-ts 52,48` (measured here @196,608) | 15,090 | 15,538 | GPU1 heavy **448** |

The balance point lies **between** default and 58,42, and the old list contained no ratio
there — so every cell would have failed, the sweep would have descended rung by rung, and G21
would have concluded *"rebalance does not lift the Q6_K_XL ceiling"*. That is a false negative
on the **highest-fidelity quant**, which is Track A priority (1).

Physically: Q6_K_XL's layers are the largest on the ladder (25.30 GB), so a **smaller**
layer-fraction shift moves the same MiB than on Q6_K (21.98 GB), whose optimum is 58,42. The
correct list brackets both sides.
*Fix:* ratios are now `[default, 52,48, 54,46, 56,44, 58,42]`. First measurements confirm the
direction: 52,48 cut the imbalance from 1,806 to 448 MiB at 196,608.

### D4 — a never-started container wedged the whole sweep (MEDIUM)
A container killed between `docker run -d` and start sits in docker state `created` with no
log. `save_and_kill` raised "serverlog is EMPTY — refusing to remove", `preflight()` then
re-raised on the same corpse, and **every subsequent cell would have failed**.
*Fix:* `never_started()` distinguishes a stillborn container from evidence loss; a stillbirth
is recorded in the serverlog and the container may be removed. A container that **did** start
still cannot be removed without a persisted log (hard rule 2 intact).

### D5 — a sweep with zero successful cells still exited 0 (MEDIUM)
The runner then wrote a `sweep-<quant>.done` marker for a sweep that measured nothing. Observed
live: all 6 Q6_K cells failed on lock contention and Q6_K was marked done.
*Fix:* `tsweep_v2.main()` returns 2 when no cell succeeded; `sweep_speed` no longer asserts a
ceiling when every ratio failed.

### D6 — no single-instance guard on the runner (MEDIUM)
`nohup setsid bash runner...` can leave a setsid parent **and** a child. Killing one PID left
the sibling alive; it advanced to the next quant while a second runner was started, and two
tsweeps fought over `gpu.lock` and the container name, producing 32 junk cells across three
quants. (This was triggered during the review; no valid data was lost.)
*Fix:* `flock` on a per-phase lock file makes a second runner refuse with exit 3 (verified),
and the runner now propagates SIGTERM to its child so stopping it stops the GPU work.

### D7 — reporting nit: `best.decode_tok_s` was the rep-1 value (LOW)
Selection used the median-of-3 in a D2 contest but the published field was rep 1.
*Fix:* `decode_tok_s_median3` and `selected_on` are now emitted alongside.

### D8 — no aggregator existed (MEDIUM, blocked the answer)
Nothing turned the four `tsweep-v2-*.json` into the wave's answer. `verify-sweep.sh` verifies
the *disk* sweep (deletions), not the measurement.
*Fix:* `experiments/summarize_wave1.py` → `wave1-summary.json` / `.md`: per-quant rebalanced
ceiling, best ratio, decode at depth, VRAM/imbalance, gain vs the default split, plus the
depth-gate audit and the comparability caveats. It states explicitly that the wave answers
Track A priorities (2) and (3) only.

---

## Result that survives review

**Q5_K_XL reaches the full native 262,144 window on a surviving image — but only when
rebalanced.** 9 of 10 cells ok, all at prefill depth 0.948:

| `-ts` | decode tok/s @depth | VRAM GPU0/GPU1 | imbalance |
|---|---|---|---|
| default | **FAILS — compute-buffer-oom** | 13,540/15,070 | 1,530 |
| 54,46 | 10.82 (median-of-3: 12.70) | 14,660/15,402 | 742 |
| 56,44 | 10.78 (median-of-3: 12.51) | 14,946/15,112 | 166 |
| 58,42 | 8.50 | 15,498/15,470 | 28 |
| 60,40 | 10.67 | 15,260/14,084 | 1,176 |
| 62,38 | 10.44 | 15,546/13,796 | 1,750 |

This supersedes **E11a's 196,608** and **E1's 163,840** for Q5_K_XL, and it is a clean causal
demonstration that the rebalance — not the quant — sets the ceiling: the identical
configuration fails at the default split and loads at five different ratios.

Note the ratio with the **smallest imbalance (58,42, 28 MiB) is the SLOWEST** (8.50 tok/s).
Balance and speed are not the same objective; G13's "keep the fastest that loads" rule is
right, and `tsweep_v2` implements it.

---

## Status and what remains

* Q5_K_XL — **complete and valid** (marked done; not re-run).
* Q6_K_XL, Q6_K, Q4_K_XL — running under the repaired harness, in that order (highest-fidelity
  and least-known first). Q4_K_XL's earlier cells are quarantined, not deleted.
* Quarantined evidence lives in `e12/quarantine/`; nothing was discarded.
* `verify-sweep.sh --stage 1a` has **not** been re-run — it sha256s ~60 GB of GGUFs and the
  disk I/O would perturb a running measurement. Run it after the sweep finishes.

**This wave does not measure accuracy.** Track A's priority (1) is a quant property, and no
NLL / KV-fidelity / code-NIAH data is produced here. The Wave-1 summary must not be read as a
config selection: it answers "how much context, and how fast at that context", not "which
quant is most accurate". E2 (f16 vs q4_0 KV fidelity) remains the gating experiment, because
**every** configuration on this ladder depends on q4_0 KV.
