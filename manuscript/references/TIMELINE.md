# TIMELINE — twelve days, and how the method changed under measurement

**2026-08-20 → 2026-09-02.** Built from the Ledger (L-1…L-18) and Decision log (DEC-1…DEC-15) in
[`docs/build-stream/2026-08-30-quant-bench-trackA.md`](../../docs/build-stream/2026-08-30-quant-bench-trackA.md),
cross-checked against artifact timestamps and against the machine record at
`data/multivac-src/multivac-CLAUDE.md`.

This is a **methods-evolution story**, not a changelog. What makes it worth a public reader's time
is that the study's central instrument was **chosen after three others failed**, and that four
published results were **withdrawn by the project itself**.

All times UTC. The owner is in Brazil (UTC−3).

---

## The shape of it, in one table

| phase | dates | what happened |
|---|---|---|
| **Prehistory** | 08-20 → 08-29 | a large corpus built on an engine image that was then deleted |
| **Wave 1** | 08-29 → 08-30 | context ceilings and the `-ts` rebalance, on surviving images |
| **SSA** | 08-30 | the accuracy protocol — designed, grounded in literature, and run in 3.5 h |
| **Track A decided** | 08-30 | with **zero additional GPU time** |
| **S8** | 08-30 → 08-31 | speculative decoding is not lossless — a premise falls |
| **S9 campaign** | 08-31 → 09-01 | determinism, the generative anchor, DFlash2 — and a self-inflicted outage |
| **Corrections** | 09-01 | a withdrawal, an infeasibility, and a rejected instrument |
| **S12** | 09-02 | RULER, and the finding that closed the argument |

---

## Prehistory — 2026-08-20 to 2026-08-29

The corpus that everything later had to be measured against, and mostly could not be.

**2026-08-20** — the split-mode matrix (`data/archive/aug20-splitmode-matrix.txt`) and the MTP
ablation (`aug20-mtp-ablation.txt`), on image `llamacpp-nccl231:latest`, ctx 32,768 / 8,192, q8_0
KV. `-sm tensor` fails with a CUDA illegal memory access; `-sm row` fails for lack of split
buffers. **The origin of "`-sm layer` only."**

**2026-08-21 → 08-28** — the bulk of the historical corpus: perplexity ladders (three mutually
incompatible protocols), HumanEval+ thinking and non-thinking, SWE-bench Verified at n≈50, agentic
step counts, the 30-run `champion-20260821` tree, NVFP4 on vLLM, energy integration, cited KL
divergence. An instrumentation audit on 08-28 finds **ten reporting defects** — a first-match regex
over concatenated eval logs, artifacts landing in the wrong cwd, a summary file overwritten by
every batch, and so on. **Every one is a reporting bug, not data loss**: the raw evidence survives.

**Then the image was deleted.** `llamacpp-dflash2-pr27342:1deefcc-sm120-cuda128-abi` — the only
image on which `-sm tensor` ever worked, and the source of **every** tensor-split and **every**
262,144-token figure in that corpus — went from disk **without its digest being recorded**. It
cannot be re-pulled. That single loss is why `env-manifest.json` exists, why every artifact now
carries an image id, and why the whole historical corpus is labelled
**IRREPRODUCIBLE-ON-CURRENT-IMAGES**.

**2026-08-29 (E0/E6/E10/E1/E1b)** — a re-grounding pass on surviving images. Ceilings measured
under the default split; `-sm tensor` confirmed dead on both surviving images; provenance repairs
(the KV dtype of the historical needle runs is **unrecoverable** → labelled KV-UNKNOWN rather than
guessed). Operational lessons recorded the expensive way: vLLM boot takes 13–16 min and failures
fail fast; `gmu 0.99` will not boot on 16 GB cards; `json.loads(urlopen(...))` without `.read()`
loses a measurement *after* the GPU work has happened; `pkill -f` matches your own session.

**2026-08-29, evening (E11)** — two results that reframed everything:

* **vLLM/NVFP4 eliminated from Track A** on measured data — a 51,200-token ceiling against the
  model's native 262,144, and HumanEval+ 85.4/84.1 against Q6_K_XL's 93.9/91.5. Notably **not**
  eliminated for poor GPU splitting: its TP=2 splits *more* evenly than llama.cpp's layer split.
* **The two cards are not a pool.** Under `-sm layer` each layer's weights and its KV slice live on
  one card, with no NVLink, so the binding limit is per-card. The default placement was stranding
  1,955–3,829 MiB on GPU0 while GPU1 OOMed within 473–1,119 MiB of its wall. One flag —
  `-ts 58,42` — took UD-Q6_K from 196,608 @ 7.19 tok/s to 262,144 @ 13.85 tok/s: **+33 % context
  and +93 % speed together.**
* And a measurement correction that invalidated the reading of every speed table on the host:
  **decode at depth 0 is 37.22 tok/s where decode at depth 186,265 is 7.19** on the identical
  server. The published `ctx=32768` tables are not long-context throughput.

---

## Wave 1 — 2026-08-29 to 2026-08-30

### L-1, L-2, L-3 · planning (08-29 → 08-30)

The plan is drafted from live reconnaissance rather than from documents, and the reconnaissance
immediately contradicts the documents in five places (F-A…F-E): the legacy orchestrator is still
running and one of its jobs removes a container **without saving its logs**; the champion GGUF has
no sha256 in the manifest; the "≥60 GB" disk gate passes in decimal GB and misses by 204 MB in GiB,
so it must be **byte-explicit**; the documented sampling defaults are **not** the measured ones;
and `{"reasoning_effort":"none"}` fails where `{"enable_thinking":false}` works.

**DEC-2 (owner)** settles sampling: task benchmarks run at the model's **official** settings, not
at a hand-tuned candidate. Greedy stays the instrument for logprob work only. This resolves the
comparability problem the historical corpus had — every pre-E12 benchmark used greedy, which
matches neither official preset.

**DEC-4 (owner)** approves the delete list — and it is the decision that later has to be partly
reversed.

### L-4 · 2026-08-29T23:40Z — the harness, and the docs-before-delete gate

The E12 harness is written: `lib_e12.py`, `validate_v2.py`, `tsweep_v2.py`, `pad_e12.py`,
`sweep_v2.sh` with docs→manifest→delete **enforced in code**. The validation gate goes green:
four positive checks pass and a self-test injects four faults, each caught by the intended check.
The delete manifest is written with sha256, bytes and RepoDigests for all five items —
**nothing deleted yet.** That commit *is* the gate. PN-1…PN-4 are appended.

Deletion follows at 23:27:44Z: the IQ4_XS GGUF, the 22 GB duplicated NVFP4 HF cache, and both vLLM
images. The Q6_K_XL GGUF is held back, because a design decision (D1) said to run its `-ts` bracket
**before** deleting it.

### 2026-08-30T02:30–03:10Z — the review pass that changed the wave

A review found eight defects. Three were material:

* **The pad builder silently returned short pads.** A bisection over a *fixed* bracket, calibrated
  on a stretch of corpus running ~2.9 chars/token where the rest runs ~4.45, pinned at the bracket
  edge and returned the *last* probe rather than the closest. `pad_201830` delivered 169,823 tokens
  instead of 201,830 — **−15.9 %**. UD-Q4_K_XL was therefore measured at **0.797** of its window
  while UD-Q5_K_XL was measured at 0.948: both its speed row and its ceiling verdict were
  optimistic, and the two were not comparable. (PN-5)
* **The ≥0.90 depth gate was documented and never asserted** — which is *why* the first defect was
  invisible. (PN-5)
* **The approved `-ts` list for UD-Q6_K_XL pointed the wrong way.** Live measurement showed `58,42`
  already overshooting on that quant. Under the approved list every cell would have failed, the
  sweep would have descended rung by rung, and the wave would have concluded *"rebalance does not
  lift the Q6_K_XL ceiling"* — **a confident false negative on the highest-fidelity arm.**
  → **DEC-7**, an agent correction to an owner-approved plan, flagged rather than applied silently.

Three more were process defects with no data consequence but real wedging risk: a container killed
between `docker run -d` and start sits in state `created` with no log and wedges every later cell;
a sweep in which every cell failed still exited 0 and wrote a `.done`; and two runners raced over
the same GPU lock, producing 32 junk cells. (PN-10)

**DEC-8** — the Compass Forge conductor had halted at 01:57Z with `VERDICT-REPAIR-EXHAUSTED`.
Wave 1 finishes **hand-driven** rather than restarting the pipeline mid-sweep, because a second
runner is exactly the failure already observed.

### L-5, L-6, L-7 · 2026-08-30T03:40–04:35Z — reversal, redesign, and autonomy

**OPEN-1 → DEC-9.** The bracket that D1 insisted on running first paid off: under the corrected
ratio list UD-Q6_K_XL loads at **212,992** at `-ts 56,44`, against a published ceiling of 131,072.
The premise behind deleting it — "best accuracy but only 131,072 context" — was measured false.
The owner reverses: *"Do not delete Q6_K_XL, it became interesting with this new test."* It becomes
the **fourth arm** and the **divergence reference**. The disk gate it was going to satisfy is
waived, with the reasons recorded.

**DEC-10.** Wave 3 (accuracy) moves ahead of Wave 2 (speculative tuning), because accuracy is
priority (1) and tuning gates nothing.

**DEC-11 — the decision the paper is built on.** The four-arm accuracy program was 35–47 h of GPU.
The owner: *"we need a much, much smaller version… something that academia and AI Engineers and
Researchers would accept as a good sample, but that won't take 3 or 4 entire days."*

The replacement, the **Small-Sample Accuracy protocol**, rests on one observation:
**divergence instruments draw statistical power from token count; task benchmarks draw it from
problem count.** A coding benchmark has 164 problems and cannot be made bigger cheaply; a
divergence measurement over the same wall-clock has tens of thousands of per-token observations.
It was **grounded, not invented** — llama.cpp ships the instrument, Unsloth ranks its released
quants on it, Fireworks uses it for production decisions with a published threshold — and written
up as `METHOD-REFERENCES.md` R1–R7 with a table mapping each protocol element to the source that
constrains it. Cost: **~3.5 h against 35–47 h.** What the cut costs is recorded, not hidden: no
comparability with the model's published LiveCodeBench score, no agentic evidence, and divergence
measured against Q6_K_XL rather than FP16.

**L-7** — the owner leaves for some hours and the box is set up to continue without a human: a
private git hub (no GitHub, no public remote), an agent-orientation file, and a `supervisor.sh`
whose contract is *a failing step is logged, marked `.failed` and skipped — the chain continues*.
Two safety properties were built in and **verified rather than assumed**: the divergence harness
refuses to start while any GPU experiment is live, and the chain waits on a **condition**, not a
PID — the first version waited on a pid from `pgrep`, which returned the setsid *parent* rather
than the working child, and would have started SSA during the finisher's 60 GB sha256 pass.

### L-8, L-9 · 2026-08-30T12:00–12:30Z — Wave 1 and SSA close

Six of seven unattended steps green, the one failure skipped exactly as designed, 35 commits
pushed. **Every arm reaches the full native 262,144 window once rebalanced except UD-Q6_K_XL at
212,992**; all four gained over their default-split ceilings. `-ctxcp 32` adopted.

**SSA delivers the accuracy ranking the project had never had**: non-overlapping intervals,
monotone in both domains, 3.7–11.8 σ between adjacent arms — in the time one HumanEval+ arm would
have taken, and which still could not have ranked them. The headline: **code degrades ~2× more than
prose, and the gap widens as quantization gets more aggressive.**

E2 closes: **q4_0 KV costs 0.002955 ± 0.000127 KLD — 51 % of a whole quantization level.**
Defensible, not free. And on the identical pair, perplexity moved **+0.15 %** — a clean
demonstration of the averaging bias that disqualifies PPL as the ranker.

**A near miss reported as method (PN-17).** All ten KLD cells exited 0, were marked ok, and parsed
**empty** — the patterns expected ASCII `+/-` and llama.cpp emits Unicode `±`/`Δ`. Every cell was
recovered from the serverlogs **only because the log-preservation rule had written full stdout to
disk before each teardown**. No GPU time was re-spent. Fixed at source, and a KLD cell without a
`mean_kld` is no longer reported ok.

Close-out is done evidence-first: serverlogs pulled and verified **before** 50 GB of reference
logits were deleted; seven empty serverlogs resolved honestly (all inside the 52-second
double-runner race window, all stillborn containers, each registered with `evidence_lost: false`)
**with the check itself left exactly as strict as it was**.

### L-10 · 2026-08-30T12:50Z — Track A decided, and a defect caught first

The recommendation is produced with **zero additional GPU time**. Producing it required correcting
the project's own summary: the Wave-1 decode column mixed **three estimators** — one arm's last
repetition, another's first, a third's median. Recomputed on one statistic the ranking **reverses
for two arms**. (PN-20; and see `METRIC-CORPUS.md` ⚑F-2, which finds the same file also mixes
*contexts*.)

The finding that decides it: **decode speed does not discriminate these arms** — medians span 6.7 %
against within-arm noise several times larger — while accuracy separates them at 3.7–11.8 σ. So the
usual "smaller quant buys speed" trade **does not hold here**: the cheaper arm is not faster, only
less accurate.

### L-11, L-12 · 2026-08-30T13:00–13:45Z — the domain hierarchy, and the control

**S5** adds the 164 HumanEval+ task prompts as a third domain and produces the study's sharpest
result: divergence rises monotonically **prose → generic code → actual task prompts**, and the
prose-to-task amplification **grows** with quantization aggressiveness (3.13× / 3.87× / 4.40×).
Against the published <0.007 threshold, two of three arms pass on prose, one on generic code, and
**none on the task distribution**.

**S7's pilot gate fires and earns its place** — a 25-task run returns rc=0 with an *unparsed*
score, and the gate stops the run before the full budget is spent. The same class of defect as
PN-17. The cost estimate is corrected **twice, both times by the agent, both recorded rather than
quietly adjusted**: S7 was recommended as "free, already built in" — the *flags* are built in, the
*data* is not; and the pilot then measured the true compute at ~375 min, not "free".

**S7 is the control that validates the method.** Four arms on HellaSwag at n=400: an 1.0-point
spread, the **most heavily quantized arm nominally highest**, and — extracted from the same data at
zero extra GPU cost, because the shared seed makes the observations paired — **UD-Q6_K_XL and
UD-Q5_K_XL answering all 400 items identically**. *Had Track A been decided the conventional way,
on a task battery, it would have concluded "no meaningful difference" and picked the cheapest arm.*

---

## S8 — 2026-08-30T13:37Z to 16:16Z, documented 08-31

Ran to completion unattended, then **sat undocumented for a day** — the data was committed by the
autonomous sync, but no ledger entry, paper note or amendment was written. L-13 closes that gap and
records the finding that contradicts a premise three documents were still asserting.

**Speculative decoding is not output-identical here.** Over 164 HumanEval+ problems at temperature 0
with a fixed seed, `--spec-draft-n-max 2` and `4` each reproduce the no-spec baseline byte-exactly
on **131 of 164 (79.88 %)**. About one generated function in five is not the function the same
configuration would have produced without speculation. pass@1 moves inside the ±4.6-point interval
and ranks nothing — **the equivalence result is the finding, not the score.**

The mechanism was **not established**, and the note said so, offering two candidates and leaning to
the wrong one.

Two more: **draft depth n=4 appeared to beat n=2 at every depth with the gap growing** (→
Amendment 1, later withdrawn), and **all five DFlash2 cells were void** — launched against an
engine that cannot parse the drafter, recording `0.000 pass@1`, a value indistinguishable in a
table from a model that ran and failed completely (PN-25).

---

## The S9 campaign — 2026-08-31 to 2026-09-01

**DEC-12 (owner)** cuts two experiment groups after reviewing them against the objective, and
records **what the cut costs**: PN-9's confound stays unresolved, there is no temperature>0
equivalence check, and there will be **no per-configuration energy figure**. Three limitations
become permanent rather than pending.

**DEC-13** reinstates exactly one item — the MTP depth sweep — on the reasoning that *almost every
cancelled item ADDS a result the paper lacks, while exactly one REPAIRS a claim the paper already
makes.* The reasons the others stay cancelled are recorded so they are not re-litigated. The
runner-up was the presence-penalty probe, and the note on it is candid: the official preset's
`presence_penalty 1.5` penalises every token already emitted, and code repeats `self`, `return` and
indentation constantly, so a measurable harm **would have been the paper's own thesis appearing in
a second dimension.** Cut on cost.

**DEC-14** adds two more and sequences the campaign as four detached chains, each taking a
**blocking** flock on the previous one's lock — no polling for "is the GPU free"; the wait is on
the lock, which is the condition itself.

### L-14 · 2026-08-31T23:35Z — an answer, and a self-inflicted outage

**The determinism control (S9a) settles PN-23's mechanism** — and refutes the note's own guess.
Re-running S8's two configurations unchanged a day later, **the no-spec arm reproduced its own 164
completions byte-identically, and the MTP arm did too**, while both still differ from each other on
exactly 33 of 164. So speculation is not an approximation that occasionally drifts; it is a
**reproducibly different decode path**. PN-23 had argued the partial overlap between the n=2 and
n=4 divergence sets pointed at float nondeterminism. It cannot: both arms are individually
deterministic. **PN-23's numbers stand; its mechanistic speculation is withdrawn.**

**Then the supervision killed the campaign it was built to protect (PN-27).** `preflight()` refuses
to launch while the legacy orchestrator runs, implemented as
`pgrep -af "watchdog.sh|worker.sh"` — unanchored, matching **any** such process. The sentinel armed
to supervise the campaign had been named `campaign_watchdog.sh`. Every phase launched after 22:32Z
failed preflight; three batteries, 31 GPU cells and four chained runners **cascaded to failure in
eight minutes.** Nothing was corrupted and no GPU was consumed — the check did exactly what it was
written to do, on a false positive it could not distinguish from a true one.

Fixed two independent ways, **both tested under the live failing condition**. And while fixing the
first, a second instance of the same family was found: the sentinel's own `chains_alive()` used
`[s]9_chain.sh`, whose unescaped `.` is a regex wildcard sitting one character away from matching
the monitor's own `tail -f .../s9_chain.log`.

### L-15 · 2026-09-01T02:00Z — the generative anchor is null, and that is the finding

**SSA S6.** The ladder's two extremes on all 164 HumanEval+ problems, official sampling,
seed-matched, no-spec on both arms: **93.90 % vs 94.51 %** on base tests. Analysed *paired*, the
arms agree on **161 of 164** problems, exact McNemar **p = 1.0**, direction inconsistent across
metrics. These are the same arms that differ **3.69×** in mean KL divergence on code.

**This is the generative counterpart of S7.** PN-22 showed a multiple-choice battery cannot see
quantization damage; PN-28 shows a *generative coding* benchmark — the closest thing to the target
workload the field routinely runs — cannot see it either, at the sample size the benchmark has.
The informative quantity is the **discordance** (3 and 5 of 164), not the p-value.

**DFlash2 measured properly for the first time**, repairing PN-25: at ctx 32,768 it is the fastest
method on the host (51.78 tok/s, 2.80× no-spec), and pass@1 **93.29/90.24** — indistinguishable
from every other arm, against the 0.000 S8 had recorded. At depth it is strictly dominated: OOM at
262,144 *and* 212,992, highest reachable rung **163,840** where acceptance **halves to 0.4583**.
The historical acceptance collapse is reproduced on a surviving image.

One claim is deliberately **not** written: S6's decode medians suggest the inter-quant speed gap
shrinks with depth, but the two measurements differ in spec setting, sampling and ratio. The note
waits for the sweep designed to measure it cleanly.

### L-16 · 2026-09-01T05:35Z — the withdrawal

S9d's 24-cell sweep completed reporting 23/24 valid. **Every cell reported acceptance exactly
1.000** — a red flag on the standing 20-minute check — so the artifact was inspected before any
note was written.

**It is invalid, and so is more than the sweep.** The probe posted a 123,666-token pad to
`/v1/chat/completions` as a user message with `max_tokens: 512`. Given a corpus and no instruction
the model answered briefly and stopped: **all 69 repetitions generated exactly 17 tokens**
(min = median = max). Decode was timed over 17 tokens — yielding **52.27 tok/s at ctx 131,072**,
faster than most configurations reach at depth 0. The gate asserted `prefill_frac ≥ 0.90` and
asserted **nothing about generation**. *PN-5's lesson recurring inside the harness written to
honour it: prefill contract in code, generation contract in the docstring.*

**The reach was wider than the sweep.** The same construction is used by S8's at-depth phase, and
the engine's own log confirms it: `eval time = 951.92 ms / 17 tokens`. **PN-24's at-depth half is
withdrawn. Track A Amendment 1 is withdrawn** and the pinned draft depth reverts to n=2.

**Wave 1 was checked, not assumed** — every cell records `n_predict = 192` with realistic
acceptance, because the working construction was already on disk. The quantization decision is
untouched: the recommendation changed a flag, not the model.

The repair was **piloted on one cell before re-running 24**, and the pilot corrected the gate
itself: an initial "every rep ≥ 90 % of `n_predict`" rule failed a *good* cell whose middle rep
stopped naturally on EOS, so the gate became an absolute 128-token floor. Cost: ~3.3 h of GPU on
the invalid sweep, plus the re-run. *The 20-minute check earned its place here — the sweep would
otherwise have been written up as a result.*

### L-17 · 2026-09-01T20:00Z — both closing sweeps come back underpowered

The repaired harness worked: depth matching exact, generations real, and the new gate caught two
cells at 55 and 124 tokens.

**Acceptance falls monotonically with draft depth in 12 of 13 adjacent pairs (one-sided sign test
p = 0.0017).** That is the result.

**The ranking question is unanswerable at n=3.** Decode rep-spread reached **166 %**; per-rep
acceptance ranged up to 0.629 *within a single cell*. And the pooled Wilson intervals — ±0.02 over
1,000–4,000 draft events — are **misleading**: draft events inside one generation are correlated,
so the effective n is the **3 generations**, not the 4,000 events. **That is R6's
clustered-standard-error trap reproduced on our own data, and it is the most useful thing this
sweep produced.**

So **DEC-13's purpose was not achieved**: PN-9's confound stays unresolved and PN-24's generality
stays unanswered. Resolving either needs ~30 repetitions per cell rather than 3. Track A's revert
to n=2 now stands on the firmer ground that n=2 and n=4 are **indistinguishable** at 262,144
(12.47 vs 12.88 tok/s) rather than on a withdrawn measurement — and **n=8 does not load at all** at
the full window.

### 2026-09-01 — DEC-15: an instrument declared infeasible, and its replacement rejected

S10 was to answer the study's largest stated hole — *does quantization damage grow with context
depth?* — with KL divergence at depth. Its pilot failed with `std::bad_alloc`.

The ceiling was then established **empirically, one rung at a time rather than extrapolated**:
n_ctx 2,048 leaves 9,061 MiB free; 8,192 leaves 1,338 MiB; **16,384 drives the host to 305 MiB and
writes zero bytes in 13 minutes before being killed**; 65,536 dies immediately. The usable ceiling
is **n_ctx 8,192** — a 4× range against a 262,144 deployment context, which is 128× the 2,048 at
which every accuracy number in this study was measured. **A 4× range cannot support a claim about
128×.**

The owner's ruling is characteristic of the project: *"S10 is actually important… If it's not
possible to perform the test reliably, say so"* — and the OOM findings are **footnote material,
not a paper feature**, because the report is about serving models, quantization and configuration.

**S11 replaced it** — greedy trajectory divergence at depth, specified with the memory/VRAM
arithmetic stated **before the harness existed**, the hardest cell piloted first, and both output
gates asserted in code. It ran the 8,192 rung and **was rejected on its own data**: the metric
(index of the first differing character against the reference arm) collapses immediately — median
first divergence at characters 5, 62 and 10 for the three arms, with **no** identical pairs at the
*shallowest* rung. A metric that saturates at "diverges at once" cannot grade depth.

> ⚠ **S11's rejection is the one stage that produced measurements and no paper note.** The ledger
> records it in a clause; there is no PN entry. See `METRIC-CORPUS.md` ⚑F-5 — it is a publishable
> negative result about instrument design, and it is currently undocumented.

---

## L-18 · 2026-09-02T13:00Z — S12, and the finding that closed the argument

With two instruments rejected, the approach changed: **research what the field actually does rather
than improvise.** RULER is the standard, and two published studies run our exact experiment with
it. The harness uses RULER's **own** generators, templates, prompt construction and metric — the
metric unit-checked against the reference implementation on five cases **before any GPU time**.
Only transport is ours.

**S-NIAH is saturated at 100.0 for both arms at 8,192, 32,768 and 131,072.** Accuracy recovery
100 % at every length, zero empty responses. **Sixteen-fold more context bought no discrimination
whatsoever.**

Holding depth fixed at 131,072 and adding four distractor keys — **MK-NIAH** — gives **100.0 vs
91.67**. Depth alone did not reveal the effect; **difficulty did.**

**That is the finding that completes the paper's through-line.** PN-22: a multiple-choice battery
cannot see quantization damage. PN-28: a generative coding benchmark cannot see it either.
PN-33/34: a retrieval benchmark cannot see it at any depth **while the task remains easy**, and
begins to only when difficulty is raised. **The common factor is headroom — not modality, and not
length.** Every one of these instruments has a ceiling, and a quantization difference is invisible
whenever both arms sit against it. Divergence measurement has no such ceiling, which is why twenty
minutes of KL divergence separates these arms at 3.7–11.8 σ where roughly twenty hours of task
benchmarking across three modalities separates them nowhere.

And the caveat is stated in the same breath: **MK-NIAH is one failed sample of twelve**, Wilson
intervals overlap almost entirely, and separating an 8-point drop needs n ≈ 100 ≈ 11 h at this
depth. *"Consistent with published results, not established here."*

Cost control applied mid-run: a flat n=25 design was 8.0 h with ~75 % in the deepest rung, so
sample counts went per-length; `variable_tracking` was dropped after two measured attempts for an
**output-format artifact** — RULER budgets it at 30 generated tokens, and this instruct-tuned model
writes a markdown step-by-step trace instead, so the metric was measuring verbosity against a fixed
budget rather than long-context ability. Both attempts put the *reference* arm **below** the
cheaper arm, which is the signature of a floor-scored comparison. Data retained, never deleted.
MK-NIAH data was pre-generated on CPU while the GPU ran, so the hedge cost nothing until needed.

**Measurement closed.** No GPU work is queued and none is required.

---

## Coda · 2026-09-02T18:00Z — a re-analysis, with no new GPU time

Prompted by an independent structural review of the corpus, the SSA cells were re-read **by
quantile** rather than by mean — and the study's most-quoted accuracy sentence turned out to be an
average of two opposite facts.

**PN-14 says code degrades ~2× more than prose. At the median, code tokens are perturbed
100–200× *less*.** The ordering **reverses between the 90th and 95th percentile**, and by the 99th
percentile code is perturbed 5–8× more. The crossover sits in the same place for all three arms,
and above it the amplification is monotone in quantization aggressiveness at every quantile. The
single worst token is *less* perturbed on code than on prose, so the effect is a bounded
**p95–p99.9 band**, not an unbounded tail. (PN-35)

**This is the mechanism the corpus had been missing**, and it explains two earlier results that had
only been described. PN-16's paradox — top-1 agreement *higher* on code while mean KLD is *double* —
follows directly: ~90 % of code tokens are trivially predictable and barely move, while a thin band
moves enormously. And it predicts the small paired discordances the task benchmarks actually
produced (3 of 164, 5 of 164 in PN-28): damage concentrated in ~1–5 % of positions changes an
outcome only when a tail token lands somewhere decisive.

The generalisable sentence, and it is the sharpest one the project has: **a mean-only report of
quantization damage — which is what the field publishes — is the average of "almost nothing
happens" and "something drastic happens", and reports neither.**

Two things to fix before this ships, both in `METRIC-CORPUS.md`: PN-35's evidence line understates
where its own data lives (six of its seven rows *are* in the shipped artifact, ⚑F-23), and its
median row is rounded in the direction that understates the effect (⚑F-24). And **PN-35 cites a
ledger entry `L-19` that has not been written** (⚑F-25) — the same gap that left S8 undocumented
for a day.

*No GPU time was spent. The finding was in the preserved data the whole time, and was reachable
because hard rule 1 had written the raw tool output to disk before every teardown — which is, once
more, the thing this project keeps rediscovering.*

---

## What the twelve days actually demonstrate

**Four published results were withdrawn by the project itself**: PN-23's mechanism (by PN-26),
PN-24's at-depth half and Track A Amendment 1 (by PN-30), and S10/S11 as instruments (by DEC-15 and
by S11's own data). None was withdrawn by an outside reviewer. Each was caught by a **rule** —
a standing red-flag list, a pilot gate, a preserved log — rather than by luck.

**The instrument was chosen after three alternatives failed.** A task battery cannot rank these
arms (S7, S6). KL divergence at depth is not measurable on this host (S10). Greedy trajectory
divergence does not grade depth (S11). What remained — divergence at 2K plus a standard long-context
benchmark — is the study's method, and the failures are *why* it is the method.

**Seven instrumentation defects, each producing plausible-looking wrong output rather than an
obvious failure**: a Unicode parser mismatch, an unasserted depth gate, a short-pad bisection, three
orchestration races, a mis-bound drafter, an unnamed estimator, an unasserted generation contract,
and an over-broad safety predicate that killed its own campaign. The generalisation the paper
should make from them is one sentence: **the instrument is part of the experiment.**

**The scarce resource was GPU hours, and saying so changed the design.** DEC-11 cut 35–47 h to
3.5 h and got a *better* answer. DEC-12 cut two programmes and recorded what the cut cost. DEC-15
declared an experiment infeasible rather than running a weakened version of it. That preference —
prefer the instrument that answers the question at the lowest cost, and state plainly what a
measurement cannot support — is itself one of the study's findings.
