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
Full 262,144-token window · code KLD **0.005829 ± 0.000233** · decode ~11.9 tok/s at 95 % depth.

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
`data/raw/e12/serverlogs/` (raw tool output every number was parsed from) ·
paper notes PN-13, PN-14, PN-15, PN-18, PN-19, PN-20, PN-21 · ledger L-8, L-9, L-10, L-11.
`data/raw/e12/ssa/ssa-s5-results.json` (task-prompt divergence).
