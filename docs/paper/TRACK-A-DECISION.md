# Track A — coding-agent configuration, decision and evidence

**Deliverable status: DECIDED 2026-08-30.** Derived entirely from measured Wave-1 and SSA data;
no further GPU time was required to reach it.

Decision rule fixed by the owner: **accuracy → context → tok/s**, in that order.
Host: 2× RTX 5060 Ti 16 GB (sm120). Engine `llamacpp-mtp:latest`, image `sha256:feb0231976b6…`.

---

## The recommendation

### Primary — `UD-Q6_K`

```
-m Qwen3.8-27B-UD-Q6_K.gguf -ngl 99 -sm layer -ts 58,42 -c 262144 -fit off -fa on \
   -ctk q4_0 -ctv q4_0 -b 2048 -ub 512 -np 1 -ctxcp 32 \
   --spec-type draft-mtp --spec-draft-n-max 2
```
Full 262,144-token window · code KLD **0.005829 ± 0.000233** · decode **11.90 tok/s** at 95 % depth
(median of 3, Wave-1 `tsweep-v2-Q6_K.json`).

> **`--spec-draft-n-max 2` — Amendment 1's change to n=4 is WITHDRAWN by Amendment 2 (below) on
> 2026-09-01.** The at-depth measurement it rested on timed 17 generated tokens, not 192 (PN-30).
> n=2 is restored because it is the only draft depth with a valid measurement at this window.
> n=4 remains 25.6 % faster at ctx 32,768 on sound data, and S9e will settle the full window.

**Why:** it has the best accuracy of any arm that reaches the full window, and it is the only
non-reference arm whose code divergence stays under Fireworks' published <0.007 high-quality
threshold. Speed costs nothing to choose it — see the finding below.

### Fallback A — maximum fidelity, `UD-Q6_K_XL`, if 212,992 context is enough

```
… -m Qwen3.8-27B-UD-Q6_K_XL.gguf -ts 56,44 -c 212992 …    # or -c 196608 for headroom
```
The least-quantized arm on the ladder and the reference against which all divergence here is
measured. Costs **19 % of the context window**. At 196,608 it also posted the highest single
decode reading of the wave (17.26 tok/s).

### Fallback B — minimum VRAM, `UD-Q4_K_XL`

```
… -m Qwen3.8-27B-UD-Q4_K_XL.gguf -ts 56,44 -c 262144 …
```
Reaches the full window at **17.56 GB** on disk against Q6_K's 21.98 GB. Accept **3.7× Q6_K's
code divergence** (0.021529) — above every published quality threshold we found, and inside
LocalBench's observed Q4_K_M band. **Choose this for memory headroom, not for speed.**

### Not recommended — `UD-Q5_K_XL`

It is **dominated**. Same 262,144 ceiling as Q6_K, **1.76× the code divergence** (0.010285 vs
0.005829), decode statistically indistinguishable, and only 1.1 GB smaller on disk. There is no
operating point at which it is the right choice on this host.

---

## The finding that drives the decision

**Decode speed does not discriminate these arms; accuracy does.**

Measured at each arm's winning ratio at 262,144, every repetition, one statistic for all:

| quant | `-ts` | n | reps (tok/s) | median | within-arm spread |
|---|---|---|---|---|---|
| Q4_K_XL | 56,44 | 6 | 11.81 · 12.01 · 12.10 · 13.12 · 13.33 · 15.96 | 12.61 | **32.9 %** |
| Q5_K_XL | 54,46 | 3 | 10.82 · 12.70 · 12.94 | 12.70 | 16.7 % |
| Q6_K | 58,42 | 3 | 10.75 · 11.90 · 14.16 | 11.90 | 28.6 % |

The three medians span **6.7 %**. Within-arm repetition noise reaches **32.9 %** — five times the
between-arm difference. **The arms are indistinguishable on decode throughput.**

Accuracy, on the same arms, separates them at **3.7–11.8 σ** with non-overlapping intervals:

| quant | code KLD (65,536 tok) | ×Q6_K | top-1 agree | wikitext-2 KLD |
|---|---|---|---|---|
| Q6_K_XL *(reference)* | — | — | — | — |
| Q6_K | 0.005829 ± 0.000233 | 1.00× | 99.142 % | 0.003321 ± 0.000126 |
| Q5_K_XL | 0.010285 ± 0.000458 | 1.76× | 98.870 % | 0.004465 ± 0.000281 |
| Q4_K_XL | 0.021529 ± 0.000834 | 3.69× | 98.430 % | 0.008207 ± 0.000340 |

So the decision rule's first criterion is the only one that resolves anything, which is why the
recommendation follows accuracy almost exclusively.

### The closer the corpus gets to the real task, the worse quantization looks

Adding the HumanEval+ task prompts as a third domain (SSA S5) makes the picture sharper, and it
does not flatter any arm:

| quant | WikiText-2 | django code | HumanEval+ prompts | task ÷ prose |
|---|---|---|---|---|
| Q6_K | 0.003321 | 0.005829 | **0.010403** | 3.13× |
| Q5_K_XL | 0.004465 | 0.010285 | **0.017285** | 3.87× |
| Q4_K_XL | 0.008207 | 0.021529 | **0.036129** | 4.40× |

Against Fireworks' <0.007 threshold: **two of three arms pass on prose, one on generic code, and
none on the actual task distribution.** The prose-to-task amplification also grows as quantization
gets more aggressive, so the cheap arm is penalised twice.

Two consequences for the ladder above:

1. **Fallback A (Q6_K_XL) is stronger than a "nice to have".** For accuracy-critical work the
   19 % context cost buys the only arm not measured as degraded on the task distribution — though
   note it is the reference, so its own distance from FP16 is unmeasured, not zero.
2. **Fallback B (Q4_K_XL) is weaker than its speed story suggests.** At 0.036 on task prompts it
   is five times the threshold, and its top-1 agreement of 95.894 % means roughly **one token in
   24 differs from the reference under greedy decoding** — on function bodies, that is a lot.

**This inverts the usual quantization intuition.** The case for a cheaper quant is normally
"meaningfully faster for slightly less accuracy". On this host at full context, the smaller quant
is **not meaningfully faster** — it is only less accurate. Q4_K_XL earns its place on VRAM
footprint alone.

### The task-benchmark check, and why it changed nothing

HellaSwag at n=400 across all four arms (SSA S7) scores 82.75 / 82.25 / 82.75 / 83.25 % — a
**1.0-point spread**, the most-quantized arm nominally **highest**, and a paired McNemar test on
the identical task set finding Q6_K_XL and Q5_K_XL answering **all 400 items identically**, with
no pair differing on more than 4 items (all p >= 0.13).

This is the control that validates the method. The same four arms are separated at 3.7-11.8 sigma
by divergence. A multiple-choice battery cannot see it, because such scoring depends only on an
argmax over a few candidates and is robust to exactly the distribution shift that alters generated
code. Had the decision been made on a task battery — the conventional approach — it would have
concluded "no meaningful difference between quantizations" and picked the cheapest arm.

## Conditions every line above is contingent on

- **q4_0 KV throughout.** Validated, not assumed: it costs 0.002955 ± 0.000127 KLD versus f16 —
  **51 % of the divergence of dropping a whole quantization level.** Defensible, not free, and it
  must be quoted with any accuracy claim. Measured on the reference arm, code domain, at n_ctx
  2048 — *not* at the 212K–262K depths where the KV cache dominates memory.
- **The `-ts` ratio is part of the configuration, not a tuning detail.** Every ceiling here exists
  only at its ratio; at the engine default split, Q5_K_XL fails to load at 262,144 entirely.
  Re-sweep on any change of quant, KV dtype, or speculative-decoding setting.
- **`-ctxcp 32`** over the default 4: +6.8 % decode and +7.6 % prefill at identical VRAM (n=1 A/B,
  directional).
- **Divergence is ladder-relative**, measured against Q6_K_XL because no FP16 exists on the host.
  These are distances along the ladder, not from the unquantized model.
- **Divergence is measured on prompt tokens.** It ranks how far each quant's predicted
  distribution moves. It is not a measurement of generated-code quality; SSA S6 (generative,
  paired, two arms) remains unrun.
- Sampling is the DEC-2 official non-thinking block, not greedy. Decode figures are at ~95 %
  window depth and are 3–5× slower than the widely published depth-0 numbers.

## Provenance

`data/raw/e12/tsweep-v2-*.json` (ceilings, ratios, decode reps) ·
`data/raw/e12/ssa/ssa-results-parsed.json` (divergence, top-1, E2) ·
`/srv/bench/server-timings/` (raw tool output every number was parsed from; serverlogs are gitignored and live on the host) ·
paper notes PN-13, PN-14, PN-15, PN-18, PN-19, PN-20, PN-21 · ledger L-8, L-9, L-10, L-11.
`data/raw/e12/ssa/ssa-s5-results.json` (task-prompt divergence).


---

## Amendment 1 — 2026-08-31, after S8 (spec-decode battery)

Two changes. One is a configuration change; the other is a **correction to a premise** that this
document, `~/CLAUDE.md` and PAPER-REFERENCES.md had all carried, and that had been used to justify
not testing speculative decoding for accuracy at all.

### 1. The premise was wrong: speculative decoding is not output-identical here

The study had assumed, and stated as a structural fact, that speculative decoding is
*greedy-lossless* — that accepted draft tokens are by construction exactly the target model's
greedy output, so the speculation method could only affect speed, and accuracy was purely a
property of the quantization. **On this engine that is false.**

164 HumanEval+ problems, UD-Q6_K, greedy (temperature 0, top_p 1, fixed seed), everything else held
constant:

| config | exact match vs no-spec | first divergence (median char) | pass@1 HE / HE+ | decode @32 K |
|---|---|---|---|---|
| no-spec | — (baseline) | — | 94.5 / 91.5 | 18.46 tok/s |
| MTP n=2 | **131/164 (79.9 %)** | 715 | 93.9 / 90.2 | 37.44 tok/s |
| MTP n=4 | **131/164 (79.9 %)** | 730 | 93.9 / 90.9 | 47.03 tok/s |

About **one generated function in five is not the function the same configuration would have
produced without speculation.** The pass@1 differences are inside the ±4.6-point interval at n=164
and rank nothing — the *equivalence* result is the finding, not the score.

**The mechanism is not established, and the honest reading matters for how much this should worry
you.** Two candidates: the verification step may not implement exact greedy equivalence; or
speculation changes the batch shape of every decode step, floating-point reductions are not
associative, and the logits are therefore not bit-identical even when the rule is correct. The
evidence leans to the second — the n=2 and n=4 divergence *sets* overlap only partially (25 shared
problems, 8 unique to each, Jaccard 0.610), whereas a systematic rule error should produce nearly
identical sets. A no-spec-vs-no-spec repeat control (~40 min GPU) would settle it and has not been
run.

Either way the operational consequence is the same and it is the reason this amendment exists:
**a speculative configuration is part of the accuracy configuration, not a free speed knob.** If a
result must be exactly reproducible, run without speculation and accept 3.43 tok/s at full depth.

### 2. Draft depth n=4 replaces n=2

Measured on the same arm at both depths:

| depth | no-spec | MTP n=2 | MTP n=4 | n=4 vs n=2 |
|---|---|---|---|---|
| ctx 32,768 (median of 164) | 18.46 | 37.44 (2.03×) | **47.03 (2.55×)** | +25.6 % |
| ctx 262,144, filled to 93.9 % | 3.43 | 11.48 (3.35×) | **16.81 (4.90×)** | **+46.4 %** |

Applying the decision rule: n=2 and n=4 are equally output-faithful (both 131/164), both reach the
same 262,144 ceiling at `-ts 58,42`, so criteria (1) accuracy and (2) context are tied and (3)
tok/s decides. **n=4.**

Note the direction: the speculative advantage **grows** with context depth here (2.55× → 4.90×),
the opposite of the DFlash2 behaviour recorded in the historical corpus. Lower acceptance at n=4
(0.8922 vs 0.9536 at 32 K) does not offset the larger number of tokens each accepted draft carries
— acceptance alone is a poor predictor of throughput.

**Caveats on the depth figures:** n=1 per configuration with a 192-token generation, against a
documented within-arm decode noise of up to 32.9 % (PN-19). The 46.4 % gap exceeds that noise but
has not been replicated. Draft acceptance reads exactly 1.000 for *both* arms at depth, which at
that sample size is not a stable estimate and should not be quoted. The 32 K medians, over 164
generations each, are the sturdier pair. Both are one quant at one `-ts` ratio, and PN-9 shows
acceptance is quant-specific — do not carry this ordering to Q4_K_XL or Q5_K_XL without measuring.

### 3. DFlash2 was not measured

All five DFlash2 cells were launched against `llamacpp-mtp:latest`, which cannot parse the DFlash2
drafter (`done_getting_tensors: wrong number of tensors; expected 81, got 58`); the required engine
is the fork `llama-dflash2:latest` (v0.1.2-dev build 50, f7aadef, which also needs
`--entrypoint /app/llama-server`). The cells recorded 0.000 pass@1 — a value indistinguishable in a
table from a model that ran and failed completely. **They are excluded data.** DFlash2 remains
unmeasured under this protocol and is not part of the recommendation either way.

### What does not change

The quant choice. Accuracy still decides it, speed still does not discriminate the arms (PN-19),
and nothing in S8 touches the divergence ladder. **UD-Q6_K remains the primary**, Q6_K_XL the
maximum-fidelity fallback at 212,992, Q4_K_XL the minimum-VRAM fallback, Q5_K_XL still dominated.

Evidence: `data/raw/e12/s8/s8-humaneval.json` · `s8-atdepth.json` · `s8-scores.json` ·
`s8-{nospec,mtp2,mtp4}.jsonl` (per-problem completions) ·
`/srv/bench/server-timings/s8-*.serverlog` · paper notes PN-23, PN-24, PN-25 · ledger L-13.


---

## Amendment 2 — 2026-09-01, withdrawing Amendment 1's speed evidence

**Amendment 1 changed the pinned draft depth from n=2 to n=4 on the strength of a 46.4 % speed lead
at the full 262,144-token window. That measurement is invalid.** It timed **17 generated tokens**,
not the 192 requested: the probe posted the raw pad to the chat endpoint with no instruction, the
model answered briefly and stopped, and the engine's own log records it plainly —
`eval time = 951.92 ms / 17 tokens` and `draft acceptance = 1.00000 (16 accepted / 16 generated)`.
Full diagnosis in PN-30.

**The config line reverts to `--spec-draft-n-max 2`**, because it is the only draft depth with a
sound measurement at this window: **11.90 tok/s**, median of three repetitions, from the Wave-1
sweep, whose cells generated their full 192 tokens with realistic acceptance (0.495–0.911).

### What is *not* affected

- **The quantization decision is untouched.** UD-Q6_K remains the primary; the ladder, the KLD
  numbers, the context ceilings and the fallbacks all come from Wave 1 and SSA, neither of which
  used the broken construction.
- **PN-19 stands** — decode speed does not discriminate the arms at the full window — and with it
  the reasoning that accuracy, not speed, decides this configuration. That is why this correction
  changes a flag and not the recommendation.
- **The 32,768-token speed ordering stands**: no-spec 18.46 → MTP n=2 37.44 → MTP n=4 47.03 →
  DFlash2 51.78 tok/s, all medians over 164 real generations.
- **Amendment 1's *other* findings stand.** Speculative decoding is not output-identical (PN-23),
  and PN-26 has since strengthened that to *deterministically* non-equivalent.

### What is open

Whether n=4 (or n=8) beats n=2 **at 262,144** is now unmeasured. S9e re-runs those three cells with
the corrected probe — `/completion` plus a continuation cue, official sampling, and a gate that
fails any cell generating less than 90 % of what it asked for. If n=4 or n=8 wins on sound data the
line changes again, and this time the number will carry a median of three.