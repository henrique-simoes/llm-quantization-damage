# Wave 1 — tensor-split rebalance: context ceilings and decode at depth

**Question:** After a full -ts rebalance sweep, what context ceiling and what decode rate at ~95 % window depth does each quant reach on a surviving image?

**Answers Track A priorities:** (2) usable context, (3) tok/s
**Does NOT answer:** (1) accuracy — a quant property this wave does not measure; no NLL/KV-fidelity/NIAH data is produced here, so this summary MUST NOT be read as a Track A config selection

| quant | rebalanced ceiling | default-split ceiling | gain | best -ts | decode tok/s @depth | prefill tok/s | VRAM peak GPU0/GPU1 | imbalance |
|---|---|---|---|---|---|---|---|---|
| Q5_K_XL | 262144 | 196608 | +65,536 | 54,46 | 10.82 | 522 | 14660/15402 | 742 |
| Q6_K_XL | — | 131072 | — | — | — | — | — | — |

**Fastest at the full native 262,144 window:** Q5_K_XL @ `-ts 54,46` — 10.82 tok/s

**Incomplete:** Q4_K_XL, Q6_K, Q6_K_XL

## Caveats
- SAMPLING: every request carries the DEC-2 official non-thinking block (temp 0.7 / top_p 0.80 / top_k 20 / presence 1.5), NOT greedy. Decode and acceptance rows are therefore NOT comparable to the e11 / ctx=32768 tables, which were measured at temperature 0.
- DEPTH: decode is measured after a real prefill to >=0.90 of the window (actual ~0.945). Published 'ctx=32768' speed tables decode into a nearly EMPTY KV cache and are 3-5x faster; the two must never share a table.
- PAD DEFECT (2026-08-30): the first Q4_K_XL pass prefilled only 0.797 of the window because the pad builder's fixed-bracket bisection returned short. Those cells are quarantined under e12/quarantine/ and were re-run; the >=0.90 gate is now enforced in code and covered by regression tests.
- RATIO CHOICE IS NOT MONOTONE-SAFE: a ratio that loads at one ctx may fail at another, and the winner differs per quant. Re-sweep -ts on any change of quant, KV dtype or spec setting.
- ALL CELLS: -sm layer, q4_0 KV, MTP n=2, -fit off, -ctxcp 4, -np 1 on llamacpp-mtp:latest. -sm tensor is dead on both surviving images (E6).
