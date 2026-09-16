# S15 running log — DFlash2 vs MTP (live, updated during the block)

**Purpose:** a durable record of the S15 block while it runs, so no result depends on an agent session staying alive.
Design and decisions: plan §S15, DEC-16, DEC-17. Findings of record: `docs/paper/PAPER-NOTES.md` PN-73…PN-82.
Artifacts on the host: `/srv/bench/e12/s15/results/`, serverlogs `/srv/bench/server-timings/s15-*.serverlog`.

> 🔁 **Resume instructions after the 2026-09-16 reboot: `/srv/bench/e12/s15/RESUME-AFTER-REBOOT.md`** — state, both T5
> failures and their fixes, the commit commands, and the relaunch command. The chain resumes at T5; T1–T3 are done.
>
> ⚠️ **Commit status.** The agent's shell tool has been failing every command since ~00:20Z 2026-09-16, so
> **PN-81, PN-82, L-38 and this file are written to disk but not committed.** Commit them when a shell is available:
> `git add docs/paper/PAPER-NOTES.md docs/build-stream/ && git commit`. Nothing else is blocked; the chain is detached.

## Block timeline (UTC)

| phase | start | end | outcome |
|---|---|---|---|
| chain start, serving stopped, swap cycled (4,084 → 0 MiB) | 19:30 | — | — |
| T1 pilot | 19:33 | 20:10 | ✅ all gates (PN-80) |
| T2 context/KV map | 20:10 | 00:58 | ✅ 12 cells, 71 launches (PN-81, PN-82) |
| T3 speed | 00:58 | running | arm 3 of 14 in the matched-depth probe |
| T5 stability + soak | 10:06 | 10:35 | ❌ **FAILED on the harness host-memory guard** — chain stopped, serving restored |
| T4 paired subsets → full passes | — | — | **not run**; the block halted before any accuracy measurement |

## ⛔ Block halted at T5, 2026-09-16T10:35:10Z — host-memory guard, not a server fault

**What passed.** The first configuration (UD-Q6_K · MTP n=4 · q4_0 · 262,144 · `-ts 58,42`) cleared the stability
half completely: **10 sequential prompts of 107,113 and 120,006 tokens**, each reusing the cached prefix
(444–533 tokens reprocessed), no crash, no CUDA error — i.e. the issue #23210 pattern did **not** reproduce.
The soak then grew a thinking-mode conversation to **252,295 tokens (96 % of the 262,144 target)** with server
anonymous memory at 5,352 MiB, VRAM steady at 15,498 / 15,164 MiB and **zero swap growth**.

**Why it stopped.** `soak.py`'s own guard: `MemAvailable 1493 MiB < 1500` — **7 MiB under an arbitrary threshold**.
T5 returned 1, the chain logged `FAIL t5`, ran its exit trap and restored serving as designed.

**Why free RAM was lower than on 2026-09-15.** That soak peaked at 5,294 MiB anon with ~4.6 GiB free and passed.
Today the host started T5 with ~4 GiB of swap full of pages that never returned after the 19:30Z swap cycle, so the
same server footprint left less headroom. The guard measures the *host*, not the configuration under test.

**Not established by this failure:** anything about q8_0 stability (never reached), about the other three
configurations (never run), or about DFlash2 in service. **T4 accuracy was not started at all.**

**Serving confirmed restored** at 2026-09-16T10:38:07Z by the chain's exit trap: `qwen38-serve=active`,
`llm-proxy=active`. The host is back to its primary role; the GPUs are held by the served model, not by S15.
Resuming S15 therefore requires stopping serving again (`chain.sh` does this itself), and the chain is resumable —
`state/t1.done`, `t2.done`, `t3.done` exist, so a re-run starts at T5 and repeats none of the 14.5 h already spent.

### Resolution — owner decision, 2026-09-16T12:03Z

The owner cycled swap, lowered `soak.py`'s guard **1500 → 1200 MiB** (the value `lib15.MemoryGuard` already uses for the
accuracy tiers) and relaunched `chain.sh` (pid 3135573). The chain skipped T1–T3 on their `.done` markers and resumed at
**T5 at 12:03:13Z**. Verified in the installed copy `/srv/serving/soak/soak.py` (`MEMAVAIL_ABORT_MIB = 1200`); the
repository copy `~/repos/multivac-serving/soak/soak.py` was updated to match, with the reason in a comment, so the next
`install.sh` does not revert it. **A gate was changed after it fired — recorded here as the owner's decision, not an
agent-side adjustment.** Threshold rationale: the soak now aborts at the same level as the accuracy harness, giving
~300 MiB more headroom than the run that failed 7 MiB short.

**Original decision options, for the record** (superseded by the above): whether to (a) cycle swap and re-run T5
unchanged, (b) lower the soak guard (e.g. 1,200 MiB, matching the T4 harness) and re-run, (c) reduce the soak target
below 250K for the S15 gate, or (d) proceed to T4 accepting the stability evidence already gathered. Any change to a
gate after it has fired must be recorded as a decision, not applied silently.

## T1 — pilot (PN-80)

Gates: G1 loads + 1,024-token generations (6 cells) · G2 xhigh present in the rendered prompt · G3 DFlash2 mean accepted
length 5.65 (Q6_K) / 5.14 (Q4_K_XL) ≥ 3.5 · G4 AA-LCR prefix reuse (2nd question: prompt_n 506, cache_n 87,385).

| quant | no-spec | MTP n=3 | DFlash2 n=7 |
|---|---|---|---|
| UD-Q6_K | 16.1 tok/s (pp 1,026) | 34.0 (845) | 42.0 (830) |
| UD-Q4_K_XL | 19.0 (1,251) | 33.8 (1,062) | 55.9 (949) |

xhigh reasoning length (the budget driver): AA-LCR 3,174 and 6,141 generated tokens (255 s, 282 s at ~22 tok/s, 88K prompt);
GPQA 492 / 721 / 1,841 / 4,485 tokens (14–153 s), 4/4 correct.

## T2 — context × KV map (PN-81; failure mode PN-82)

Ceiling = loads · `/props n_ctx` == requested · ≥ 94 % prefill · 512 generated tokens, with a failed rung above attempted twice.

| quant | KV | MTP: ceiling (`-ts`, VRAM peak MiB) | DFlash2: ceiling (`-ts`, `-devd`, VRAM peak) |
|---|---|---|---|
| UD-Q6_K | q4_0 | 262,144 (58,42 · 15,400/15,106) | 262,144 (58,42 · CUDA1 · 15,614/14,388) |
| UD-Q6_K | q8_0 | 196,608 (56,44 · 15,552/15,722) | 196,608 (56,44 · CUDA1 · 15,754/15,532) |
| UD-Q6_K | f16 | 131,072 (56,44 · 15,696/15,144) | 98,304 (58,42 · CUDA1 · 15,664/14,246) |
| UD-Q4_K_XL | q4_0 | 262,144 (56,44 · 13,408/14,814) | 262,144 (58,42 · CUDA1 · 14,116/13,606) |
| UD-Q4_K_XL | q8_0 | **262,144** (56,44 · 15,710/15,702) | **262,144** (58,42 · CUDA1 · 15,610/14,588) |
| UD-Q4_K_XL | f16 | 196,608 (54,46 · 15,620/15,340) | 163,840 (58,42 · CUDA1 · 15,396/14,182) |

Consequences already fixed for the accuracy tier (gentlest KV **both** drafters hold, DEC-17 item 2):
**AA-LCR @262,144** → UD-Q6_K `q4_0`, UD-Q4_K_XL `q8_0`. **GPQA @131,072** → UD-Q6_K `q8_0`, UD-Q4_K_XL `f16`.

## T3 — speed, matched depth (greedy, paired continuations, 1,024 tokens each; k=4 at 32K, k=8 deeper)

UD-Q6_K, decode tok/s median (prefill tok/s in parentheses); mean accepted length τ per arm:

**UD-Q6_K complete (all 7 arms), decode tok/s median (prefill tok/s):**

| filled context | no-spec | MTP n=2 | MTP n=3 | MTP n=4 | DFlash2 n=3 | DFlash2 n=5 | DFlash2 n=7 |
|---|---|---|---|---|---|---|---|
| 32,768 | 11.7 (486) | 26.7 (396) | 29.4 (396) | 29.4 (396) | 28.6 (423) | 29.9 (424) | **48.4** (423) |
| 131,072 | 5.6 (309) | 19.2 (208) | 21.8 (209) | 22.9 (209) | 22.9 (280) | 23.8 (280) | **31.5** (281) |
| 246,415 | 3.5 (216) | 14.1 (133) | 16.0 (135) | 17.3 (135) | 17.5 (200) | 20.2 (200) | **25.7** (201) |

τ (median): MTP n=2 2.55 / 2.57 / 2.62 at 32K / 128K / 246K · n=3 3.00 / 3.16 / 3.20 · n=4 3.34 / 3.56 / 3.66 ·
DFlash2 n=3 2.79 / 3.14 / 3.21 · n=5 3.37 / 3.65 / 4.03 · **n=7 4.36 / 4.31 / 4.55**.

**Matched-depth drafter comparison, UD-Q6_K (q4_0 KV, identical prompts, 8 paired continuations, greedy).**
- **At equal draft depth (n=3) the drafters tie on decode** at every fill (28.6 vs 29.4 at 32K, 22.9 vs 21.8 at 128K,
  17.5 vs 16.0 at 246K) — so the drafters are not intrinsically different at a shared, off-design setting.
- **At each drafter's own best depth, DFlash2 wins clearly and the margin holds at depth**: MTP n=4 vs DFlash2 n=7 is
  29.4 vs 48.4 (+65 %) at 32K, 22.9 vs 31.5 (+38 %) at 128K, 17.3 vs 25.7 (**+49 %**) at 246,415.
- **DFlash2's accepted length rises with depth** (4.36 → 4.55 from 32K to 246K) rather than collapsing. This contradicts
  the historical corpus's "DFlash2 acceptance collapses at depth" claim, which PN-72 had already withdrawn as a
  17-token artefact; S15 now has the positive measurement to replace it.
- **Prefill:** MTP 396 / 209 / 135 tok/s vs DFlash2 423 / 280 / 201 at 32K / 128K / 246K — DFlash2 is also faster to
  ingest, by ~34 % at 128K and ~49 % at 246K.
- Caveat: 8 paired continuations per cell on one code pad, greedy; the pre-registered drafter decision uses T3(a)'s
  thinking-mode ~100K workload, not this probe.

**UD-Q4_K_XL, partial (no-spec and MTP complete; DFlash2 arms pending), decode tok/s median (prefill tok/s):**

**UD-Q4_K_XL complete (all 7 arms), decode tok/s median (prefill tok/s):**

| filled context | no-spec | MTP n=2 | MTP n=3 | MTP n=4 | DFlash2 n=3 | DFlash2 n=5 | DFlash2 n=7 |
|---|---|---|---|---|---|---|---|
| 32,768 | 13.1 (531) | 27.9 (424) | 30.3 (425) | 29.6 (421) | 29.1 (453) | 30.7 (452) | **44.0** (456) |
| 131,072 | 5.9 (330) | 20.2 (218) | 21.5 (219) | 22.1 (218) | 21.6 (298) | 22.6 (298) | **34.0** (297) |
| 246,415 | 3.6 (228) | 14.7 (140) | 16.9 (139) | 16.5 (139) | 17.0 (211) | 21.8 (211) | **28.3** (211) |

τ (median): MTP n=2 2.44 / 2.61 / 2.61 at 32K / 128K / 246K · n=3 3.09 / 3.10 / 3.35 · n=4 3.47 / 3.48 / 3.51 ·
DFlash2 n=3 2.88 / 2.97 / 3.13 · n=5 3.50 / 3.45 / 4.33 · **n=7 3.48 / 4.03 / 4.57**.

✅ **The drafter verdict is NOT quant-dependent — it is draft-depth-dependent.** The caution recorded at 08:31Z (that
UD-Q4_K_XL was not reproducing Q6_K's DFlash2 advantage) is **withdrawn by the n=7 cell**: at 246,415 DFlash2 n=7 reaches
28.3 tok/s against MTP's best 16.5 (**+71 %**, larger than Q6_K's +49 %), and at 131,072 34.0 vs 22.1 (+54 %). At n=3 and
n=5 the drafters really are level on this quant; the advantage appears only at DFlash2's design point, draft depth 7
(its `block_size` is 8, so 7 is its maximum). Accepted length again **rises** with depth (3.48 → 4.57).
DFlash2's prefill lead holds on both quants (+37 % at 131,072, +52 % at 246,415 here).

## T3(a) — Artificial Analysis-style thinking workloads (the pre-registered drafter decision basis)

Thinking on, xhigh, official sampling, output capped at 2,048 tokens, 3 prompts per input size sharing a cached prefix.
Decode tok/s median (TTFT seconds for the first, uncached prompt):

| input size | Q6_K MTP n=4 | Q6_K DFlash2 n=7 | Q4_K_XL MTP n=4 | Q4_K_XL DFlash2 n=7 |
|---|---|---|---|---|
| ~1K | 22.1 (1.7–2.2 s) | 32.0 (1.8–2.7 s) | 24.7 (1.5–2.0 s) | 37.7 (1.6–3.0 s) |
| ~10K | 24.5 (10.3 s) | 31.6 (11.0 s) | 22.9 (9.0 s) | 34.3 (9.8 s) |
| ~100K | 16.3 (137.2 s) | 20.4 (142.2 s) | 17.4 (123.6 s) | 29.8 (128.8 s) |

Selection (`results/t3-speed.json`, written 10:06:34Z): best draft depth **MTP n=4, DFlash2 n=7 on both quants**;
winner **DFlash2 on both**. Decode medians at ~100K with bootstrap 95 % intervals (k=3 prompts):
Q6_K MTP 16.28 [16.13, 16.56] vs DFlash2 20.41 [19.82, 22.70] — **intervals separate, rule satisfied**;
Q4_K_XL MTP 17.44 [15.87, 22.09] vs DFlash2 29.83 [23.80, 51.35] — **separate, but only just** (23.80 > 22.09).

⚠️ **The rule is satisfied on both quants; the weakness on UD-Q4_K_XL is sample size, not logic.** DEC-17 item 3 requires
non-overlapping bootstrap intervals, and `select()` tests exactly that (`dflash2_ci_low > mtp_ci_high`). On UD-Q6_K the
separation is wide (19.82 > 16.56). On UD-Q4_K_XL it is marginal: the bounds clear each other by 1.7 tok/s, with MTP's
interval inflated by a 22.1 tok/s first prompt and DFlash2's by a 51.3 tok/s outlier, over **k=3 prompts** — a fragile
bootstrap. The choice therefore stands and T4 is configured from this file, but the paper must report the UD-Q4_K_XL
selection as resting on 3 prompts with a wide interval, and cite the matched-depth probe (8 paired continuations,
+71 % at 246,415) as the stronger evidence for the same conclusion.

**The quant barely moves speed; the drafter and the KV dtype do.** UD-Q4_K_XL's MTP arms sit within ~5 % of UD-Q6_K's at
every matched depth and draft length (n=3 at 246,415: 16.9 vs 16.0 tok/s; n=4 at 131,072: 22.1 vs 22.9; no-spec at
246,415: 3.6 vs 3.5), despite a 4.4 GB difference in weights. Decode at depth is dominated by reading the KV cache, so
the practical levers on this host are the drafter (up to +49 % at 246K, PN-83 pending) and which KV dtype each quant can
hold at the target window (PN-81) — not the quantization level.

Speculative speedup over no-spec: **2.3–2.5× at 32K · 3.4–3.9× at 128K · 4.0–4.6× at 246K**. Accepted length does **not**
decay with depth for MTP — it rises slightly. Draft depth pays diminishing returns: n=2 → n=3 is worth ~13 % at 128K and
~13 % at 246K, while n=3 → n=4 adds nothing measurable at 32K–128K so far (τ rises but decode does not).
Within-depth spread over 8 paired continuations: ±0.7 tok/s at 32K–128K, ±2 tok/s at 246K.

Remaining T3 arms: MTP n=4, DFlash2 n=3/5/7 on UD-Q6_K, then the seven arms on UD-Q4_K_XL, then the
Artificial Analysis-style workloads (~1K/10K/100K input, thinking on) that decide which drafter runs each full accuracy pass.

## Health

Chain healthy; no phase failures. Host: free RAM drifting down with depth (7.0 → 4.4 GiB; harness aborts below 1.2 GiB),
swap full of idle pages with negligible swap-in, GPUs ~15.3/15.0 GiB in use. Projected block total **35–40 h**
(vs the 78 h estimate) because measured xhigh reasoning is 2–3× shorter than budgeted.

## 2026-09-16T21:00Z — T4 halt and relaunch (L-41)

GPQA Q6_K+MTP subset halted at 21/50 on the cumulative swap-growth guard (+524 MiB over 3 h 20 min, MemAvailable 8.3 GiB).
Guard made per-item with absolute SwapFree/MemAvailable floors; `bc` dependency and median-based budget projection fixed.
Relaunched 20:51Z, resumed at item 22. GPQA pace: median 3.2 min, mean ~8 min, max 51 min (75K-token reasoning).
