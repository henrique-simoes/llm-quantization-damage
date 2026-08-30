# Build Stream — Multivac Quant Bench Track A: Q4_K_XL / Q5_K_XL / Q6_K coding-agent configuration

<!-- STATUS BLOCK -->
```yaml
item: quant-bench-trackA
branch: main
cf: { spec: CF-SPEC-1, tasks: [CF-1..] }
phase: "Wave 1 — -ts rebalance sweeps in flight (lifecycle Phase 3); Phases 1-2 closed"
stage: S2-execute
status: in-progress
blocked_on: null
last: { agent: claude-opus-5, at: 2026-08-30T03:40:00Z, ledger: L-5 }
next_action: "AUTONOMOUS until the sweep ends. T4/T5 running detached (runner_wave1.sh sweep Q6_K_XL Q6_K Q4_K_XL, pid 1498430); finish_wave1.sh (pid 1661639) waits on it and then runs summarize_wave1.py + verify-sweep.sh --stage 1a. D3/A8 is automatic inside the Q6_K sweep. Do NOT start a second runner (flock, exit 3) and do NOT run verify-sweep.sh by hand while the GPU work is live. T3b delete-1b is CANCELLED (DEC-9 — Q6_K_XL is kept as the 4th accuracy arm and the fidelity reference); Phase 1 closes on stage-1a + the A3 /srv/models waiver. AFTER Wave 1: T6 close-out, then WAVE 3 (accuracy, four arms, Stage A first) ahead of Wave 2 per DEC-10."
conductor: { run: qbench-t1, shape: solo-architect, waves: 4, manifest: docs/build-stream/qbench-t1-waves.json, state: HALTED-verdict-repair-exhausted-2026-08-30T01:57Z, execution: hand-driven per DEC-8 }
```
<!-- /STATUS BLOCK -->

## Plan overview (roadmap)

**Problem.** Multivac (2× RTX 5060 Ti 16 GB, sm120, 14 GiB RAM) hosts a quantization benchmark
study of Qwen3.8-27B. The 2026-08-29 execution pass (E0–E11) established the measured XL-tier
context ladder, the `-ts 58,42` rebalance finding (+33 % context, +93 % decode speed on Q6_K),
and eliminated vLLM/SGLang from Track A. The owner has now narrowed scope to **three quants —
UD-Q4_K_XL, UD-Q5_K_XL, UD-Q6_K** — and wants the definitive **coding-agent configuration**
per quant, with Unsloth/Qwen-consistent benchmarks, MTP/DFlash setting sweeps, full metric
continuity, and small-before-big gating on every GPU experiment.

**Outcomes (Track A deliverable + Track B data).**
1. One pinned, reproducible coding-agent config line per quant (accuracy → context → tok/s),
   with fallback ladder — the Track A answer.
2. Clean, image-provenanced data for the Track B technical report (no protocol mixing, CIs on
   every claim, reproducibility caveats stated).

**Top risks.**
- R1: wrong launch settings waste GPU hours (llama.cpp server silently defaults temp 0.8 /
  top_k 40 / top_p 0.95 / min_p 0.05; `-fit on` is default and silently shrinks context;
  thinking is ON by default and `/no_think` does not work on this template — only
  `chat_template_kwargs.enable_thinking:false` validated so far, `reasoning_effort:none`
  untested, G17). → Phase 2 harness-validation gate is mandatory before every stage.
- R2: marginal-rung VRAM nondeterminism (±100–200 MiB layer-split noise) produces false
  ceilings. → every ceiling bracketed with a re-test; VRAM failures re-tested (E11a lesson).
- R3: `-ts` ratio is not monotone-safe and is quant/KV/spec-dependent (G13) → full ratio sweep
  per config, keep fastest-that-loads, record imbalance.
- R4: disk pressure — `/srv/models` at 99 % (1.2 GB free). → Phase 1 sweep, delete list gated
  on preservation audit.
- R5: statistical power (G22): HumanEval+ n=164 → ±4.6 pts; SWE-bench n=50 → ±12 pts. Task
  benchmarks validate the final config; PPL/NLL on code is the only sensitive quant-ranking
  instrument. Every claim carries n + CI.

**Doc impact.** CLAUDE.md (multivac) gains: final config lines, ts-sweep results, sampling
A/B verdict, draft-KV findings. PAPER-REFERENCES.md gains the new measurement sections.
Documentation is never deleted — only appended.

### Scope fixed by owner (2026-08-30)
- Quants: **UD-Q4_K_XL (17.56 GB), UD-Q5_K_XL (20.88 GB), UD-Q6_K (21.98 GB)** only.
  IQ4_XS and Q6_K_XL GGUFs may be deleted once this file records their findings (they are).
  ⚠️ Open question for owner: "Q6_K" read as **plain UD-Q6_K** (the 21.98 GB file that holds the
  262,144 @ `-ts 58,42` record). Q6_K_XL (25.30 GB, best raw accuracy but 131K MTP ceiling)
  would then leave the active set — its results are already fully documented, so deletion is
  allowed under the preservation rule. Confirmation requested before Phase 1 runs.
- Benchmarks: same families as Qwen/Unsloth (coding + agentic), sweet-spot subset — §Benchmarks.
- MTP + DFlash2 stay in scope, with setting sweeps.
- Sampling research first: the coding-agent configuration IS the test configuration.
- vLLM/SGLang containers and NVFP4 models may be deleted (Track B E9 cross-backend comparison
  would then require a 22 GB re-download + image re-pull if it is ever run — flagged in delete
  list for an explicit owner call).
- Small tests before big tests: hard gate on every phase.

### Phase table

| Phase | Goal (one line) | Acceptance / verify | Status |
|-------|-----------------|---------------------|--------|
| 0 | Settings research consolidated into pinned config candidates + owner gates | owner approves DEC-1 set (this file) | **done** (DEC-1..DEC-6) |
| 1 | Disk sweep under preservation rule; delete list executed; manifests written | `bash /srv/bench/sweep/verify-sweep.sh` green + free ≥ 60 GB on /srv/models | **partial** — delete-1a executed 23:27:44Z (4 of 5 items, 65.4 GB); Q6_K_XL held for its bracket (D1); byte gate NOT yet met (38.9 GB free) and `verify-sweep.sh --stage 1a` deliberately deferred (L-5) |
| 2 | Harness-validation suite (validate-v2): launch contract, sampling contract, thinking control, provenance capture | `validate-v2.py` catches the 4 seeded fault configs (negative control) | **done** — gate green 2026-08-29T23:01Z (C1–C4 pass; F1→C1, F2→C3, F3→C2, F4→C4); a fifth contract (≥0.90 depth gate) added 2026-08-30 after PN-5 |
| 3 | Bring-up + `-ts` rebalance sweep per quant; bracket context ceilings | `tsweep-v2` full-ratio artifacts + bracketed ceilings re-tested | **in-progress** — Q5_K_XL complete+valid (262,144 @ `-ts 54,46`); Q6_K_XL/Q6_K/Q4_K_XL re-running under the repaired harness |
| 4 | Official-settings validation pilots (G17 equivalence, G8 losslessness at temp>0, pp-behavior probe) | pilot artifacts; spec-decode accuracy-arm rule locked | planned |
| 5 | MTP/DFlash setting sweep (depth, p-min, draft-KV dtype, DFlash n-max) | sweep JSONs at 32 K and full-depth; best-per-context recorded | planned |
| 6 | Accuracy instruments: PPL(P1) for UD-Q6_K, code-NLL ladder, HumanEval+ gap-fills, LCB v6 n=100 setup+run | artifacts under /srv/bench/, CIs attached | planned |
| 7 | Agentic: SWE-bench Verified 25-smoke → 50 stratified; agentic steps; thinking arm | smoke green before 50-run; per-instance manifest + Wilson CIs | planned |
| 8 | Context axis: Code-NIAH 6 depths × 2 needle classes × 3 seeds; E2 KV fidelity (f16 vs q4_0) | code-niah.json + kv-fidelity.json; decision rule applied | planned |
| 9 | Speed + energy at chosen config (speed curve, J/tok, filled depths) | chosen-config-speed.json | planned |
| 10 | Track A decision procedure + Track B data assembly; CLAUDE.md/PAPER-REFERENCES updates | config lines published with evidence trail | planned |

## Benchmarks — sweet-spot proposal (owner approval required before deployment)

"Same SWE and benchmarks as Unsloth and Qwen" but each has hundreds of tasks. Sized to
discriminate, with the statistical reality stated (G22):

| Benchmark | Official anchor | Sweet spot | n | Statistical reality | Cost |
|---|---|---|---|---|---|
| Perplexity (WikiText-2, Protocol 1) | Unsloth PPL tables | full corpus, 3 quants | 602 windows | most sensitive quant discriminator we have (G22); ±0.041 SE | ~30 min/quant; UD-Q6_K missing |
| Code-NLL ladder (NEW protocol-4) | — (target-workload analogue) | final 256 tok of django prefixes at {32K,64K,128K,CTX_MAX} | 4 depths × 3 quants × 2 KV | code-corpus fidelity at depth; feeds E2 decision rule | ~2–3 h |
| HumanEval+ (non-thinking) | Qwen: not published; Unsloth: uses PPL/KLD | full 164 | 164 | ±4.6 pts — cannot rank Q4/Q5/Q6 (differ 1–3 pts); validates sanity only | ~1 h/quant; UD-Q6_K missing |
| LiveCodeBench v6 | **Qwen official 90.3** | recent-problems subset | 100 | ±9–10 pts; validates vs official anchor, cannot rank quants | setup ~2 h + ~3 h GPU |
| SWE-bench Verified | Qwen: SWE-bench Pro 61.7 (⚠️ different benchmark) | stratified 25-smoke → 50 stratified (repo-balanced: django/astropy/sympy/etc.) | 25 / 50 | n=50 → ±12 pts; n=25 → ±18. Config validator, not a ranker | 25: ~4 h; 50: ~10–14 h (needs eval images re-pulled) |
| Agentic steps (T3-style) | — | 3 instances × 3 quants | 3 | loop-vs-converge signal only (Q3 disqualification precedent) | ~2 h |
| Code-NIAH at depth | — (G4) | 6 depths × 2 needle classes × 3 seeds | 36/quant | per-depth Wilson CIs; class-(ii) ≥90 % @ 90 % depth gate | ~6–8 h |
| MTP/DFlash sweeps | community norms (MTP ns 2–4, DFlash ns 4/7) | depths {2,4,8} × p-min {0,0.1} × draft-KV {f16,q4_0}; DFlash n-max {4,7,8} | 3-run medians | acceptance + tok/s are speed metrics, CIs via bootstrap | ~6–10 h |
| Speed + energy | Unsloth tok/s reporting | filled {0,40K,98K,CTX_MAX} × 3 repeats | medians | J/tok from 1 Hz power-log (§13.73 method) | ~2 h |

Smoke-before-deploy: each sweet-spot set first runs on a 5-task/1-depth pilot and must pass
`validate-v2.py` (Phase 2) before the full run. Suggested deployment order: PPL+HE+ gaps
(cheapest) → ts sweeps → MTP/DFlash → NIAH → SWE 25 → LCB → SWE 50.

## Metric continuity (carried through, no drops)

PPL (Protocol 1 + Protocol 2 + protocol-4 code-NLL, never mixed), KL divergence (cited
Unsloth + archived evidence), HumanEval/HE+ pass@1 + empty %, SWE-bench Verified
(resolved/submitted/completed/empty-patches, per-instance manifest), agentic step counts,
decode tok/s (depth-0 AND at-depth, always labelled), prefill tok/s, TTFT/TPOT, J/tok + avg W,
peak per-GPU VRAM (after deep prefill), MTP/DFlash acceptance (+ mean accepted length),
functional context ceiling (bracketed), quant provenance (GGUF sha256/size), image provenance
(env-manifest id), engine version, seed, sampling settings per run. Every artifact JSON:
`source` + `run_ids` + image id fields (swebench_agg.py convention).

## Configuration research — evidence and candidates (Phase 0 output)

### Evidence gathered 2026-08-30 (sources fetched and archived)
1. **Qwen model card** (via CLAUDE.md §OFFICIAL REFERENCES + unsloth page agreement):
   thinking = temp 1.0 / top_p 0.95 / top_k 20 / min_p 0 / presence 0.0;
   non-thinking = temp 0.7 / top_p 0.80 / top_k 20 / min_p 0 / **presence_penalty 1.5**;
   `--chat-template-kwargs '{"reasoning_effort":"…"}'` (xhigh default | medium | low | none);
   native ctx 262,144.
2. **Unsloth Qwen3.8 llama.cpp guide** (fetched 2026-08-30): recommended default quant =
   **UD-Q4_K_XL** (their llama-cli example runs exactly that quant; 4-bit = "16–19 GB VRAM");
   GGUFs ship "MTP enabled for fast inference" + "Developer Role Support for agentic tools
   like Codex"; `--temp 1.0 --top-p 0.95 --top-k 20 --min-p 0.0` in their examples;
   `--reasoning-effort medium` shown; KLD table (code 0.02600, top-1 96.68 %) re-confirmed.
   ⚠️ Their quant default is a general recommendation, not a 2×16 GB full-native-context
   recommendation (their own doc's 4-bit row: 16–19 GB RAM+VRAM total).
3. **Official llama.cpp server docs (master, fetched 2026-08-30)**:
   - `-sm layer` is the DEFAULT split (layers + KV per GPU, pipelined); `-sm tensor` is
     **EXPERIMENTAL** upstream → independently validates E6's CUDA-IMA on sm120; `-sm row`
     unsupported on 5060 Ti (no split buffers). Citable.
   - `-fit on` is DEFAULT ("adjust unset arguments to fit in device memory") — the silent
     context-shrink hazard; `-fit off` mandatory for measurement. `-fitt` (per-device margin,
     default 1024 MiB) and `-fitc` documented.
   - `-fa on|off|auto` (default auto); quantized V-cache (q4_0) requires flash attention.
   - `-ctk/-ctv` allowed: f32/f16/bf16/q8_0/q4_0/q4_1/iq4_nl/q5_0/q5_1 (default f16).
   - **`-ctkd/-ctvd` (draft KV dtype, default f16)** — DOCUMENTED, never swept here. The MTP
     draft context is a separate context against the target (measured cost: −114,688 tokens on
     Q6_K_XL). Quantizing draft KV is a candidate to reclaim window. NEW EXPERIMENT AXIS.
   - `--spec-draft-n-max` default **3** (we pinned 2); `-ctkd/-ctvd`, `--spec-draft-p-split`
     (default 0.10), `--spec-draft-p-min` (default 0.00), `--spec-draft-backend-sampling`
     (default on), `-ngld`, `--spec-draft-device` — all documented and sweepable.
   - `-ctxcp, --ctx-checkpoints` (default 32) = context checkpoints per slot (PR #15293) —
     NOT cache-reuse; recipes used 4. Record per run; smoke-test equality before changing.
   - `--cache-reuse N` (default 0) = min chunk size for KV-shift cache reuse — candidate for
     agentic conversation growth; smoke first.
   - `-b 2048 / -ub 512` defaults; compute buffers grow with ubatch → at 262 K windows VRAM is
     binding; ubatch sweep {512, 1024} trades prefill speed vs KV headroom. Small sweep.
   - `-np` default **auto** (wrong for single-agent full-window work — auto splits the KV pool
     across slots). `-np 1` explicit. `-kvu` unified KV default when slots auto.
   - **Sampling launch defaults: temp 0.80 / top_k 40 / top_p 0.95 / min_p 0.05 /
     presence_penalty 0** — matches NEITHER Qwen official NOR greedy. Any server launched
     without explicit sampling runs a third, undocumented configuration. (Root cause of the
     "wrong settings" run-wasting class.)

### Owner decision on sampling (DEC-2, supersedes the candidate below)
Task benchmarks run at **Qwen/Unsloth official settings** — non-thinking: temp 0.7,
top_p 0.80, top_k 20, min_p 0.0, presence_penalty 1.5, repetition_penalty 1.0; thinking:
temp 1.0, top_p 0.95, top_k 20, min_p 0.0, presence_penalty 0.0. Greedy (temp 0) is used
ONLY for logprob-based instruments (PPL/NLL/divergence), where sampling is undefined
anyway. Implication for spec decode: losslessness at temp>0 is unproven (G8) — the Wave 2
pilot decides whether spec-decode arms at official sampling can carry accuracy claims or
must run no-spec. The former Phase-4 candidate A/B is replaced by the official-settings
validation pilots (G17 equivalence + G8 losslessness + pp-behavior probe).

### Candidate configuration — coding agent (llama.cpp, 2×5060 Ti, per quant)

```bash
# Base bring-up line (Phase 3 smoke first at CTX=32768, then bracket ceilings)
docker run -d --name llamasrv --gpus all --network host \
  -v /srv/models:/models:ro -v /srv/bench/models:/models2:ro \
  llamacpp-mtp:latest \
  -m /models2/Qwen3.8-27B-UD-Q6_K.gguf \
  -ngl 99 -sm layer -ts <swept-per-quant> \
  -c <bracketed-ceiling> -fit off \
  -fa on -ctk q4_0 -ctv q4_0 \
  -b 2048 -ub 512 -np 1 -ctxcp 32 \
  --jinja --reasoning-budget -1 \
  --chat-template-kwargs '{"reasoning_effort":"none"}' \
  --seed 20260830 --host 0.0.0.0 --port 8080 \
  --spec-type draft-mtp --spec-draft-n-max 2 \
  -ctkd q4_0 -ctvd q4_0        # NEW axis: sweep {f16, q4_0}; Phase 2 smoke verifies legality
# DFlash2 arms: llama-dflash2:latest with --entrypoint /app/llama-server (lesson 5),
#   drafter Qwen3.8-27B-DFlash2-Q4_K_M.gguf, --spec-draft-n-max ∈ {4,7,8}
```

Sampling (request body; locked after Phase 4 A/B):
- **Quant-comparison arm**: greedy `temperature 0` (unchanged — keeps every historical number
  comparable; no sampling variance).
- **Coding-agent arm (candidate)**: temp 0.2 / top_p 0.80 / top_k 20 / min_p 0.0 /
  **presence_penalty 0.0** / repetition_penalty 1.0. Rationale: presence 1.5 (Qwen chat
  default) penalizes code-natural repetition (whitespace, identifiers, structure); llama.cpp
  defaults match nothing official; low-temp is the agentic-coding norm. A/B-verified on
  HumanEval-40 + a repetition-stress set before adoption (owner's hypothesis, made testable).
- **Thinking arm**: `reasoning_effort` knob tested (G17): `none` vs validated
  `enable_thinking:false` equivalence check; thinking benchmark runs use official
  temp 1.0 / top_p 0.95 / top_k 20.

## Disk sweep — preservation-audited delete list (NOTHING deleted yet)

Preservation rule: an item is deletable only when every finding it produced is already in
CLAUDE.md / PAPER-REFERENCES.md. Documentation and test data are never deleted.

| Item | Size | Findings already documented? | Verdict |
|---|---|---|---|
| `/srv/models/Qwen3.8-27B-UD-IQ4_XS.gguf` | 14.25 GB | Yes: PPL 6.6839, HE+ 87.8/86.0 (m+dflash), speed 57.5/46.9/27.2, J/tok 3.70–7.46, ceilings 262,144/245,760(f16), agentic 23 steps, KLD ≈0.019 | DELETE (owner-confirmed out of scope) |
| `/srv/models/Qwen3.8-27B-UD-Q6_K_XL.gguf` | 25.30 GB | Yes: PPL 6.6511, HE+ 93.9/91.5, thinking 90.9/88.4, SWE 3/3 + verified50 75.5 %, speed matrix, ceilings 131,072(MTP)/245,760, KLD 0.0016, E11c tsweep artifact | DELETE (pending owner Q6_K-vs-Q6_K_XL confirmation) |
| `/srv/models/.hf-cache/models--unsloth--Qwen3.8-27B-NVFP4` | 22 GB | Yes: PPL 8.5848/6.7073, HE 85.4/84.1, SWE 2/3, speed table, E9a pool 52,337; sha256 pins recorded | DELETE (duplicate of /srv/engines/nvfp4; G23) |
| `/srv/engines/nvfp4` (22 GB) | 22 GB | same as above | DELETE **only if owner accepts Track B E9 re-download later** (vLLM cross-backend-at-equal-context) — recommendation: keep until E9 go/no-go |
| `vllm/vllm-openai:v0.27.1` image | 30.8 GB | Yes: HE 85.4/84.1, SWE NVFP4 2/3, config recipes documented | DELETE (E9 would re-pull) |
| `vllm/vllm-openai:nightly` image | 28.8 GB | Yes: spec speed table, DFlash2-OOM finding, E9a pool measurements | DELETE (E9 would re-pull) |
| SGLang image | 0 (not on disk) | Attempted-failed documented (0.5.18 OOM) | nothing to delete |
| `python:3.12-slim` | 179 MB | tooling base | KEEP |
| telemetry stack images+containers | ~3 GB | infrastructure for J/tok + power logging | KEEP (running) |
| `llamacpp-mtp:latest`, `llama-dflash2:latest` | 12.3 GB | the surviving engines — all future work | KEEP |
| DFlash2 drafter `/srv/models/dflash2/*.gguf` | 1.14 GB | DFlash2 testing in scope | KEEP |
| `Q4_K_XL`, `Q5_K_XL`, `Q6_K` GGUFs | 60.4 GB | active set | KEEP |
| All `/srv/bench/**` results, logs, ledger, champion tree, e11 tree | — | test data — never deleted | KEEP |
| Docker build cache (check `docker system df`) | TBD | — | prune ONLY dangling build cache, never `-a` |

Expected recovery: ≥ 60 GB on `/srv/models` (99 % → ~45 %) and ~ 60 GB on `/` (90 % → ~60 %)
if vLLM images + NVFP4 all go. Pre-deletion: sha256 + size manifest of every GGUF appended to
`/srv/bench/env-manifest.json` (E0 convention) so any deleted quant remains re-downloadable to
the exact bytes.

## Conductor operation (manager contract — main agent is the conductor manager)
- Monitor cadence ~every 3 min (under the 5-min prompt-cache window): `conductor.py status --brief` + conductor.log tail; full `status` JSON + actor stdout.log when anything looks off; `scorecard.py` at stage completions.
- Escalate to the owner immediately on: `AWAITING-OWNER-APPROVAL` (present architect plan), `blocked=N` tasks, `RATE-LIMIT-BLOCKED=<role>` (wait out reset, then `task status <ref> open` buys one dispatch), `WEDGED` verdict, repeated review-fail rounds, or any owner-gated decision in the wave instructions.
- Worker timeouts: default 2 h wall / 30 min idle per worker; pi idle-kill disabled in defaults (idle_timeout_by_harness.pi=0).
- The conductor maintains the ledger for S2–S4; the main agent owns S0/S1/S5, reports verdicts, and runs the ship checklist at convergence.


<!-- consensus-winning-plan:qbench-t1-8f05db1f10552b03a1beda52c51944302348a299695c65f02ac5aaaf34a64849 -->
## Winning consensus plan — qbench-t1

# Plan A — Wave 1: harness validation, disk sweep, bring-up + `-ts` rebalance sweeps

**Task** `qbench-t1-PLAN-A` · **Role** `qbench-t1-architect-a` · **Slot** a · **Phase** draft (solo run — this plan stands on its own and goes to the owner)
**Scope** Lifecycle Phases 1–3 of `docs/build-stream/2026-08-30-quant-bench-trackA.md`, per `docs/build-stream/instructions-wave1.md`
**Authored** 2026-08-29 · claude-opus-5 @ effort=max · grounded in live probes of `multivac` (§1), not on documentation alone

---

## 0. Summary for the owner

Wave 1 is buildable as specified. Live reconnaissance of the host surfaced **five facts that change
the plan** and **two documented "facts" that are wrong**. All are handled below; three need an
owner call (Q-A1…Q-A3), and **none of them block starting**.

| # | Finding | Consequence |
|---|---|---|
| **F-A** | The legacy orchestrator (`watchdog.sh` pid 2810112 up 1d23h, `worker.sh` pid 3818720 up 23h) **is still running** and its `job_agentic_steps` launches `docker run --name llamasrv --port 8080` and calls `kill_server llamasrv ""` — **an empty label, which removes the container without saving its docker logs**. | Direct collision + a hard-rule-2 violation waiting to happen. **T1 quiesces it first.** |
| **F-B** | `UD-Q6_K.gguf` (21.98 GB, the current champion quant) lives in `/srv/bench/models/` → on `/`, **not** on `/srv/models`; and it is **absent from `env-manifest.json`** — the champion quant has no sha256 pin. | The delete list frees `/srv/models` only; the `/` target rests entirely on the two vLLM images. E0 provenance hole must be closed in T3a. |
| **F-C** | Measured deletion arithmetic lands `/srv/models` at **64.22 GB / 59.81 GiB free**. The `≥60 GB` gate **passes in decimal GB (margin 4.2 GB) and fails by 204 MB in GiB** — and `df -h` rounds 59.81 GiB up to `60G`, so a casual check looks like a pass either way. | Gate must be defined in explicit bytes. **Q-A2** pre-authorizes the escalation. |
| **F-D** | The lifecycle file's R1 states llama.cpp defaults are `temp 0.80 / top_k 40 / top_p 0.95 / min_p 0.05`. **Measured on `llamacpp-mtp:latest`: `temp 1.0 / top_k 20 / top_p 0.95 / min_p 0.05 / presence 0.0`** — a *fourth* configuration, ≈Qwen's *thinking* preset with the wrong `min_p`. | The hazard is real but its shape is different; the F3 negative control asserts the measured values. Doc correction owed. |
| **F-E** | `{"reasoning_effort":"none"}` **failed** on this template (no `choices` in the response) while `{"enable_thinking":false}` works. | Early G17 signal. Wave 1 records it; Wave 2 still owns the verdict. |

Two deliberate deviations from the wave-1 text, both preserving every approved decision:
**D1** — run the Q6_K_XL `-ts` bracket *before* deleting it (closes G21 for ~75 min; deleting first makes a
probably-wrong published ceiling permanently uncorrectable). **D2** — "keep the fastest that loads"
gets a noise floor before it is allowed to pick a winner.

**Estimated cost: 8–11 h GPU + ~3 h non-GPU.** This exceeds the conductor's 2 h worker wall-clock,
so §7 mandates a detached `nohup` runner (there is no `tmux` on the host).

---

## 1. Ground truth (measured on multivac, 2026-08-29, not quoted from docs)

### 1.1 Host

2× RTX 5060 Ti 16 GB (sm120), 15,650 MiB usable/GPU (env-manifest), 16,311 MiB card total, both idle at 2 MiB.
14 GiB RAM + 35 GiB swap (3 GiB used). Python 3.14.4. venvs `/srv/bench/.venv-evalplus`, `.venv-swebench`.
**No `tmux`, no `jq`** — `nohup` + pid-file is the only detachment convention available.

### 1.2 Disks — exact bytes (`df -B1`, `du -sb`)

| mount | dev | size | used | **available** |
|---|---|---|---|---|
| `/srv/models` | /dev/sda | 117,549,133,824 | 110,304,100,352 | **1,226,551,296 B = 1.14 GiB (99 %)** |
| `/` (holds `/srv/bench` 33 G, `/srv/engines` 22 G, `/var/lib/docker`) | /dev/sdb2 | 234,039,422,976 | 198,522,765,312 | **23,553,507,328 B = 21.94 GiB (90 %)** |

`/dev/sda` reserves 1,465,260 × 4096 B = 6.0 GB for root (already excluded from "available").
`docker info` → Docker Root Dir `/var/lib/docker`, storage driver `overlayfs`, **on `/`**.

### 1.3 Delete-list ledger (measured sizes, mount-attributed)

| item | mount | bytes |
|---|---|---|
| `/srv/models/Qwen3.8-27B-UD-IQ4_XS.gguf` | /srv/models | 14,252,845,984 |
| `/srv/models/Qwen3.8-27B-UD-Q6_K_XL.gguf` | /srv/models | 25,299,061,664 |
| `/srv/models/.hf-cache/models--unsloth--Qwen3.8-27B-NVFP4` | /srv/models | 23,444,506,232 |
| `vllm/vllm-openai:nightly` | / | 28.82 GB **unique** (shared 6.9 kB) |
| `vllm/vllm-openai:v0.27.1` | / | 30.84 GB **unique** (shared 6.9 kB) |

→ `/srv/models` after: 1,226,551,296 + 62,996,413,880 = **64,222,965,176 B = 64.22 GB = 59.81 GiB**
→ `/` after: 23.55 + 59.66 = **≈ 83.2 GB = 77.5 GiB** (target ≥55 GB: passes under either reading)

**`docker system df` reports build cache 41/41 active, `0 B` reclaimable** → `docker builder prune`
(dangling-only) will yield ≈ 0. Do not budget for it. **Never `-a`.**

**Not on the delete list ⇒ KEEP** (stated explicitly so nobody "helps"):
`.hf-cache/hub` (3,875,861,645 B), `.hf-cache/models--z-lab--Qwen3.8-27B-DFlash2` (3,849,114,297 B),
`/srv/engines/nvfp4` (22 GB, DEC-4 explicit KEEP), all three active GGUFs, the DFlash2 drafter,
`llamacpp-mtp:latest` + `llama-dflash2:latest`, the six telemetry containers/images, **all of
`/srv/bench/**`** including `champion-20260821` (2.2 GB) and **`orchestrator/state/*.done`** (see F-A).

### 1.4 Existing harness — extend, do not rewrite (`/srv/bench/e11/`)

`lib_probe.py` (launch/health/`/props`/tokenize/kill_server), `ctx_ceiling.py` (**behavioural**
ceiling probe: healthy + `/props n_ctx == requested` + real 95 % prefill + generate; VRAM recorded,
never gated — the fix for E1's noise-band threshold bug), `pad.py` (token-exact django pads,
disk-cached; identical pads across configs are what make cross-config comparison valid),
`tsweep.py` (**carries the G13 defect**), `validate2.py`, `speed_curve.py`, `depth_bench.py`.
Cached pads already exist for 186,265 / 232,960 / 248,524 / 65,536 / 8,192 tokens.

### 1.5 Engine flags — verified present on `llamacpp-mtp:latest` (`--help`, live)

`-fa {on,off,auto}` (default `auto`), `-fit`, `-fitt`, `-fitc`, `-ts`, `-sm {none,layer,row,tensor}`,
`-ctxcp`, `-kvu`, `-np` (default −1 auto), `--cache-reuse`, `--chat-template-kwargs`,
**`--jinja` default *enabled***, `--spec-draft-n-max` (default 3), `--spec-draft-p-min` (0.00),
`--spec-draft-p-split`, and **`-ctkd`/`-ctvd` = `--spec-draft-type-k/-v` exist** → Wave 2's new
draft-KV axis is legal on this image. Engine `0.3.0-dev (build 1, commit d222767)`,
image id `sha256:feb0231976b6…`.

### 1.6 Server API surface — verified by a live 32K bring-up (architect recon)

A Q4_K_XL server was launched at `-c 32768` under the full candidate contract, probed, and torn
down **log-first** per hard rule 2 (`/srv/bench/server-timings/arch-recon-props-20260829.serverlog`,
4,160 B; container removed; `gpu.lock` released; GPUs back to 2 MiB). Load time **≈180 s at 32 K**.

1. **`/completion` echoes the effective per-request sampling** in `generation_settings` — sending
   the DEC-2 non-thinking block read back exactly `temperature 0.7, top_k 20, top_p 0.80,
   min_p 0.0, presence_penalty 1.5, repeat_penalty 1.0, seed 20260830`.
   **⇒ the sampling contract is directly assertable. This is the check that kills the whole
   "wrong settings" run-wasting class, and it costs one request.**
2. **`/props.default_generation_settings.params` = `temp 1.0, top_k 20, top_p 0.95, min_p 0.05,
   presence_penalty 0.0, repeat_penalty 1.0`** → **F-D**: not the documented default set.
3. **`/props` reports `"speculative.types": "none"` even though MTP was active** — the same
   request returned `timings.draft_n = 16, draft_n_accepted = 14`.
   **⇒ ground truth for "is spec decode live" is `timings.draft_n`, never `/props`.**
4. Thinking control, `/v1/chat/completions`, `max_tokens: 2`:
   - no control → `content=''`, `reasoning_content` len 8, `finish_reason=length` → **thinking ON by default, and the 2-token probe is a ~1 s discriminator**;
   - `{"enable_thinking": false}` → `content='OK'`, `reasoning_content` len 0, `finish=stop` ✓;
   - `{"reasoning_effort": "none"}` → **request failed, response had no `choices`** (**F-E**; error body not captured — capturing it is a Wave-1 recording duty, and the verdict stays Wave 2's).
5. `/props.model_path` and the response's top-level `model` both name the served GGUF
   → the F4 provenance cross-check has **two independent sources**.
6. Response also exposes `truncated`, `tokens_evaluated`, `tokens_cached` → cheap extra
   launch-contract assertions (a silently truncated prompt invalidates any depth measurement).

### 1.7 Baseline the sweep must improve on

| quant | file / mount | ceiling on the **surviving** image (q4_0 KV, MTP n2, `-sm layer`) | best `-ts` | decode @ depth | peak VRAM per GPU | **imbalance** |
|---|---|---|---|---|---|---|
| Q4_K_XL | `/srv/models` 17.56 GB | 196,608 (262K/229K = init-hang) | **never swept** | 30.16 | 10,996 / 14,344 | **3,348 MiB** |
| Q5_K_XL | `/srv/models` 20.88 GB | 163,840 default; **262,144 @ 54,46** | 54,46 (**first tried**) | 8.22 | 14,658 / 15,402 | 744 MiB |
| Q6_K | `/srv/bench/models` 21.98 GB | **262,144 @ 58,42** | 58,42 (54,46 crashed) | 13.85 | 15,320 / 15,080 | 240 MiB |
| Q6_K_XL | `/srv/models` 25.30 GB | 131,072 MTP / 245,760 no-spec | **only 54,46 @196,608 tried → failed** | — | — | G21 open |

Two things fall out. **Q4_K_XL's 3,348 MiB imbalance is by far the largest in the set and has never
been rebalanced — it is the highest-expected-value cell in the entire sweep** (rebalancing plausibly
buys 229,376–262,144). And G13 is now quantified: Q5 (744 MiB imbalance → 8.22 tok/s) vs Q6_K
(240 MiB → 13.85 tok/s) — **the Q5-vs-Q6 speed comparison is ratio-confounded and must not be quoted
as a model property until both are fully swept.**

Three *distinct* failure modes are visible in the artifacts and must be **classified, not lumped**:
`init-hang` (health timeout, no error), `compute-buffer OOM` (`failed to allocate compute pp buffers`
/ `failed to create MTP context` — Q6_K_XL @196,608), `crash` (backtrace through
`llama_context_can_seq_rm` — Q6_K @262,144 `54,46`).

---

## 2. Design decisions

### D1 — delete Q6_K_XL **after** its `-ts` bracket, not before  *(owner gate Q-A1; safe default = yes)*

DEC-4 approves deleting the Q6_K_XL GGUF, and the preservation rule licenses it: every finding it
*produced* is documented. But **G21 records that one of those findings is probably wrong**: only
`54,46 @196,608` was ever tried, and `58,42` is precisely the ratio that unlocked Q6_K's full
262,144 window. Its published ceiling (131,072 MTP) is therefore a likely *under-measurement* of the
highest-accuracy quant measured on this host (PPL 6.6511, HE+ 93.9/91.5, SWE-V 75.5 %). Deleting the
bytes makes that number permanently uncorrectable while it stays in PAPER-REFERENCES as fact.
The preservation rule is silent on findings *known to be wrong*; this plan reads that silence
conservatively.

**Deviation:** split Phase 1 into **1a** (IQ4_XS + NVFP4 cache + both vLLM images — frees 37.70 GB on
`/srv/models` and 59.66 GB on `/`, which unblocks everything) and **1b** (Q6_K_XL GGUF, executed at
the *end* of Wave 1 after the bracket). The `≥60 GB /srv/models` gate is therefore evaluated at
**Wave-1 exit**, not Phase-1 exit. *No approved decision is reversed — only the ordering moves.*
Cost: 3–5 probe cells ≈ 60–90 min GPU, zero new disk. If the owner declines, 1b simply runs inside
1a and nothing else in this plan changes.

### D2 — "keep the fastest that loads" needs a noise floor  *(no gate; do it)*

The existing probe derives `decode_tok_s` from a **single 64-token generation** (≈4.6 s at 13.85 tok/s)
and MTP acceptance from ~45 draft tokens. Picking "the fastest ratio" off one 64-token sample can be
noise-driven, and R2 already documents ±100–200 MiB VRAM nondeterminism. Fix, cheaply:
`n_predict = 192` on every ranking cell, and **if the top two ratios' decode medians are within 10 %,
re-run both 3× and decide on median-of-3** (tie → smaller |imbalance| → then the ratio nearer default).
Adds ~10 min per *contested comparison*, not per cell.

### D3 — pin `-ctxcp 4` for the sweep, then A/B `4` vs `32` once  *(no gate; do it)*

e11 ran `-ctxcp 4`; the candidate config line and the upstream default are `32`. Context checkpoints
are per-slot allocations, so this plausibly moves VRAM and therefore the ceilings. Sweeping at `32`
while comparing against e11's `4`-derived ceilings would mix two variables into every
"ceiling correction" claim. **Sweep at `-ctxcp 4` (baseline-comparable); then run one A/B pair at
Q6_K's winning ratio.** Δ = 0 → adopt `32` for Waves 2–4; Δ ≠ 0 → the candidate config line is wrong
and that is itself a finding. Cost: 2 cells ≈ 30 min.

### D4 — collision-proofing rather than trusting the legacy worker to stay idle *(no gate; do it)*

`worker.sh` currently logs `ALL QUEUED JOBS COMPLETE` every 300 s because every job has a `.done`
marker. That is one deleted marker away from `job_agentic_steps` seizing `llamasrv`/:8080, or
`job_score_verified50` pulling ~50 SWE-bench eval images at ~4 GB each — its own guard defers only
while `/` free < 40 GB, and **after our sweep `/` will have ~83 GB free, so the guard stops
deferring**. Defence in depth, all three: **quiesce** (watchdog *then* worker — reverse order just
gets it restarted within 120 s), **distinct container name** `llamasrv-e12`, and **take
`/srv/bench/orchestrator/gpu.lock`** so a restarted legacy worker sees `gpu_busy()` and yields.

### D5 — paths of record, reconciling two documents *(no gate; note to owner)*

The standing sync rule (owner, 2026-08-30) makes `tools/sync-multivac.sh` the contract, and it
deploys `experiments/` → `multivac:/srv/bench/e12/experiments/` and pulls into `data/bench/`.
Wave-1 text says `multivac:/srv/bench/e12/validate_v2.py` and `data/raw/e12/`. **The sync script
wins** (it is the newer directive and it is executable truth). To leave *both* documents literally
true and prevent a divergent second copy, T2 creates
`/srv/bench/e12/validate_v2.py → experiments/validate_v2.py` as a symlink. Artifacts land in
`data/bench/e12/`; `data/raw/e12/` is not created. Worth a one-line doc correction at ship.

---

## 3. Deliverables

All authored in the worktree under `experiments/`, deployed by `tools/sync-multivac.sh push`.

### 3.1 `experiments/lib_e12.py` — hardened successor to `lib_probe.py`

Same API shape so e11 callers port trivially. Changes, each tied to a defect above:

| # | change | why |
|---|---|---|
| 1 | `CONT = "llamasrv-e12"` | F-A / D4 collision |
| 2 | `launch()` emits the **full contract** — `-ngl 99 -sm layer [-ts R] -c CTX -fit off -fa on -ctk/-ctv -b 2048 -ub 512 -np 1 -ctxcp 4 --seed --host --port` + spec args — and **returns the exact command string, stored verbatim in every record** | irreproducible rows are the #1 provenance defect in this corpus (G7) |
| 3 | `preflight()` — refuse to launch unless: no `llamasrv*` container exists, nothing listening on :8080, **both** GPUs < 500 MiB used, `gpu.lock` is ours | fail loud rather than emit a confounded number |
| 4 | `vram_sampler` — 1 Hz background thread spanning prefill **and** decode, recording per-GPU **true peak** | e11 reads `nvidia-smi` *once, after* prefill returns and calls it the peak |
| 5 | `save_and_kill(label)` — `docker logs > /srv/bench/server-timings/<label>.serverlog` **before** `docker rm -f`; **asserts the serverlog exists and is non-empty**; returns byte count + `tg =` sample count | hard rule 2, enforced in code, not in prose (F-A shows prose is not enough) |
| 6 | `classify_failure(serverlog)` → `init-hang` \| `compute-buffer-oom` \| `crash` \| `props-shrink` \| `prefill-fail` \| `generate-fail` | §1.7: three distinct modes are currently lumped into "failed" |
| 7 | `record_env()` — image id + engine version string, GGUF path + sha256 + bytes (from env-manifest; **computed and appended if missing** — see F-B), seed, full sampling block, KV dtypes, spec settings, ctx requested/reported, `-ts`, `-ctxcp`, free bytes on both mounts, UTC ts | every artifact carries `source` + `run_ids` + `image_id` (swebench_agg convention) |
| 8 | `spec_live(resp)` → `timings.draft_n > 0` | §1.6.3 — `/props` lies about spec |

### 3.2 `experiments/validate_v2.py` — the Phase-2 gate

Positive run at `-c 32768` on Q4_K_XL (cheapest active to load, ≈180 s). Four contract families:

- **C1 launch contract** — `/props.n_ctx == requested` (proves `-fit off`); `total_slots == 1`;
  `-ts`/`-sm layer`/`-ctxcp` echoed in the serverlog; **flash-attn asserted ON from the serverlog**
  (`-fa auto` could resolve either way and quantized V-cache requires it); response `truncated ==
  false`; image id matches env-manifest.
- **C2 sampling contract** — send the DEC-2 non-thinking block, read back
  `generation_settings` (§1.6.1) and assert all six fields **and** assert they are *not* the
  measured server defaults `temp 1.0 / top_k 20 / top_p 0.95 / min_p 0.05 / presence 0.0` (F-D).
  Same for the thinking block.
- **C3 thinking control** — the 2-token probe (§1.6.4). Gate: `enable_thinking:false` ⇒ non-empty
  `content` **and** empty `reasoning_content`; no-control ⇒ empty `content` (proves the gate can
  actually fire). **Records, without gating, the `reasoning_effort:"none"` response body verbatim**
  including the error (F-E) — Wave 2 owns the G17 verdict.
- **C4 provenance capture** — the artifact's env block is complete and non-null, and the served
  model resolved from `/props.model_path` **and** the response `model` agrees with the requested
  GGUF and its env-manifest sha256.

**`--selftest` — the negative control (this is the acceptance criterion).** Four seeded faults;
each must be **caught**, i.e. `validate_v2` exits non-zero **and names the specific failing check**:

| fault | injection | must be caught by | expected signal |
|---|---|---|---|
| F1 ctx-shrink | launch `-fit on` with `-c 262144` on Q4_K_XL (above its 196,608 ceiling) | C1 | `/props.n_ctx` < requested |
| F2 thinking leak | omit `chat_template_kwargs` entirely | C3 | `content == ''`, `finish_reason == length` at `max_tokens 2` |
| F3 sampling-defaults leak | send the request with **no** sampling fields | C2 | read-back = `1.0 / 20 / 0.95 / 0.05 / 0.0` (the **measured** defaults, F-D) |
| F4 unprovenanced model | request whose `model` field is absent, then one that names a different GGUF | C4 | run rejected as unprovenanced |

> **F4 needs saying out loud or it will be faked.** llama.cpp ignores the request's `model` and
> serves the single loaded model, so "missing model field" **cannot** fail at the HTTP layer. The
> honest negative control is: *validate_v2 must refuse to emit an artifact whose provenance block
> cannot name the served model.* It resolves the model from `/props.model_path` + the response
> `model`, cross-checks against the env-manifest sha256, and rejects on absence or mismatch.
> A passing F4 that merely got HTTP 200 is a **failed** implementation of F4.

Cost: 5 launches × ≈180 s + probes ≈ **35–45 min**.

### 3.3 `experiments/tsweep_v2.py` (+ thin `tsweep_v2.sh` driver) — the G13 fix

- Sweeps the **full** ratio set `{default, 54,46, 56,44, 58,42, 60,40, 62,38}` at a fixed ctx.
  **Never returns early. Keeps every cell.**
- Selection: among `ok == true`, **max `decode_tok_s`**, with D2's tie-break; `imbalance_mib =
  max(peak) − min(peak)` recorded for every cell, winner or not.
- Ceiling bracketing: start one LADDER rung **above** the known ceiling; if a ratio succeeds there,
  climb until failure; if none succeed, descend until one does, then **re-test the rung above with
  the winning ratio** (R2's mandatory re-test — a rung is only "failed" after two attempts).
- Per cell: exact launch command, image id, ctx requested/reported, ok + failure `stage` +
  **classified** error, per-GPU true-peak VRAM after ≥90 % prefill, prefill tok/s, decode tok/s at
  depth (n_predict 192), MTP acceptance + mean accepted length, imbalance, serverlog path.
- **Writes incrementally after every cell and is resumable** — skips cells already present in the
  output JSON unless `--redo`. A 3 h sweep that loses everything on cell 11 is not acceptable.

### 3.4 `experiments/sweep_v2.sh` + `experiments/verify-sweep.sh` — Phase 1

Deletion order enforced **in code**: **docs → manifest → delete.**
1. `manifest`: sha256 + bytes for every delete-list item (≈61.5 GB ⇒ 10–20 min, under `nohup`),
   appended to `/srv/bench/env-manifest.json` as a `deleted_items[]` array carrying deletion
   timestamp, the findings-citation per item, and the re-download coordinates.
   **Two provenance repairs in the same pass:** add the missing `UD-Q6_K.gguf` sha256 (F-B), and
   record `docker image inspect --format '{{index .RepoDigests 0}}'` for both vLLM images —
   **without the RepoDigest, "re-pull" is not byte-exact.**
2. `docs`: ledger entry + PAPER-NOTES entries + lifecycle Status/roadmap update are **committed
   before any `rm` / `docker rmi`**.
3. `delete`: the 1a set now; 1b at wave exit (D1).
4. `verify-sweep.sh` asserts, non-zero on any failure: free **bytes** on both mounts vs the gate
   (§Q-A2); every KEEP item still present (full sha256 on the three active GGUFs ≈ 7 min, size+mtime
   on the rest); `deleted_items[]` covers every deleted item; the six telemetry containers still Up;
   `orchestrator/state/*.done` intact.

### 3.5 `experiments/quiesce_legacy.sh` (+ `restore_legacy.sh`)

Stop `watchdog.sh` **then** `worker.sh`; record both pids and the exact restart command into the
artifact and the ledger; leave `state/*.done` untouched. **Default: stays quiesced through Waves 2–4**
(they need the GPU exclusively too); restore is a ship-checklist step.

---

## 4. Task breakdown

| id | task | GPU | est | depends on |
|---|---|---|---|---|
| **T1** | Quiesce legacy orchestrator (D4); preflight snapshot (disk bytes, GPU, images, container/port); create `/srv/bench/e12/`; `sync-multivac.sh push` | no | 30 min | — |
| **T2** | `lib_e12.py` + `validate_v2.py`; positive run; **`--selftest` catches F1–F4**; symlink (D5) | light | 3 h | T1 |
| **T3a** | Phase 1a sweep: docs → manifest (incl. F-B repairs + RepoDigests) → delete IQ4_XS, NVFP4 cache, both vLLM images; `verify-sweep.sh` | no | 2 h | T1, T2 gate green |
| **T4** | `tsweep_v2` for the three actives (§5) + D3 `-ctxcp` A/B | **yes** | 6–9 h | T2, T3a |
| **T5** | G21 bracket for Q6_K_XL (D1, gate Q-A1) | **yes** | 1–1.5 h | T4 |
| **T3b** | Delete Q6_K_XL; final `verify-sweep.sh`; the `≥60 GB` gate is evaluated **here** | no | 30 min | T5 |
| **T6** | `sync-multivac.sh both`; ledger `L-3`; PAPER-NOTES `PN-1…`; lifecycle Status + roadmap; findings register | no | 1 h | all |

**Ordering note.** T2 before T3a is deliberate — "small tests before big tests" means the cheapest
thing that can detect a broken environment runs first, and validate_v2 is that thing. T3a's sha256
pass *could* overlap T2, but both are I/O-heavy against the same spindles and T2's model loads would
be slowed and its load-time numbers polluted; **default is strict serialization**, and any implementer
choosing otherwise must record the choice.

---

## 5. The `-ts` sweep matrix (T4)

| quant | ctx | ratios | goal | note |
|---|---|---|---|---|
| **Q4_K_XL** | **212,992** (one rung above 196,608), then climb 229,376 → 245,760 → 262,144 while a ratio succeeds | all 6 | ceiling **and** speed | **highest expected value in the wave** — 3,348 MiB imbalance, never rebalanced |
| **Q5_K_XL** | 262,144 (already the native max — nothing above it) | all 6 | **speed only** — de-confound G13 | 54,46 was the *first* ratio tried; 744 MiB residual imbalance |
| **Q6_K** | 262,144 | all 6 | **speed only** — confirm 58,42 is the best, not merely the first success | + D3 `-ctxcp` 4-vs-32 A/B at the winner |
| ~~**Q6_K_XL** (T5)~~ | ~~196,608, then bracket down 180,224 → 163,840 → 147,456~~ | ~~58,42 · 62,38 · 60,40 first~~ | close **G21** | **SUPERSEDED 2026-08-30 by DEC-7 — the ratio list pointed the wrong way; see the corrected row below** |
| **Q6_K_XL** (T5, corrected) | 196,608, then bracket **up** 212,992 → 229,376 → … while a ratio succeeds | `default` · 52,48 · 54,46 · 56,44 · 58,42 | close **G21** | 58,42 already **overshoots** on this quant (GPU0 heavy 2,760 MiB); the balance point lies between `default` and 58,42, so the list must bracket **both** sides — DEC-7 |

All cells: `-sm layer`, `-ctk/-ctv q4_0`, `--spec-type draft-mtp --spec-draft-n-max 2`, `-fit off`,
`-fa on`, `-np 1`, `-ctxcp 4` (D3), `--seed 20260830`, prefill ≥ 90 % of window, `n_predict 192` (D2).

> **The ≥ 90 % prefill rule is now enforced in code, not merely documented** (2026-08-30). It was
> a comment until PN-5: a cell below `prefill_frac 0.90` now FAILS as `pad-too-short`, the value is
> printed per cell and recorded in the artifact's `policy` block. Every cell measured before that
> change is quarantined, not trusted — see L-5.

**Cost model from measured e11 timings** — load 181–306 s at depth (≈180 s at 32 K); prefill 248,522
tok @ ≈502 tok/s = **8.3 min**; decode 192 tok @ 8–14 tok/s = 15–25 s ⇒ **successful deep cell
14–16 min**, failed cell 5–10 min (600 s health limit). 6 ratios × 3 quants + climb/bracket +
D2 re-runs + D3 A/B ≈ **26–34 cells ≈ 6–9 h**; T5 ≈ 5 cells ≈ 1–1.5 h.

---

## 6. Acceptance criteria

Wave 1 is done when **all** of these hold. Each is a command, not a judgement.

**A1 — harness gate.** `validate_v2.py --selftest` exits non-zero on each of F1–F4 **and names the
specific failing check**; the positive run exits 0 with all of C1–C4 green;
`data/bench/e12/validate-v2-selftest.json` shows `caught: true` for all four, with the F4 rejection
reason being *unprovenanced model*, not an HTTP status.

**A2 — no log was ever lost.** For every container this wave created, a non-empty
`/srv/bench/server-timings/<label>.serverlog` exists whose mtime **precedes** the container's
removal; `save_and_kill` recorded the byte count in the artifact. Count of labels ≥ count of cells.

**A3 — disk gate** (evaluated at T3b): `/srv/models` available **≥ 60 × 10⁹ B** and `/` available
**≥ 55 × 10⁹ B**, recorded as exact byte counts (plus the GiB figure) in `sweep-v2.json`.
`verify-sweep.sh` exits 0: every KEEP item present with matching sha256/size, `deleted_items[]`
complete with sha256 + bytes + RepoDigests, telemetry Up, `state/*.done` intact.

**A4 — provenance repaired.** `env-manifest.json` contains a sha256 + bytes entry for
`/srv/bench/models/Qwen3.8-27B-UD-Q6_K.gguf` (F-B) and a RepoDigest for each deleted vLLM image.

**A5 — G13 closed.** For each of the three actives, `tsweep-v2-<quant>.json` contains **all six**
ratio cells (no early return), a `best` chosen by max decode with the D2 rule applied, and an
`imbalance_mib` on every cell. Explicit statement of whether the historical Q5-vs-Q6 speed gap
survives ratio-matching.

**A6 — ceilings bracketed and re-tested.** Every reported ceiling has a *failed* rung above it that
was attempted **twice** (R2), each failure carrying a classified mode, not a bare "failed".

**A7 — G21 closed or explicitly declined.** Either `tsweep-v2-Q6_K_XL.json` with a bracketed
rebalanced ceiling, or a ledger line recording the owner's decline under Q-A1 — **and in the decline
case a PAPER-NOTES caveat that the published 131,072 MTP ceiling is an un-rebalanced lower bound**.

**A8 — D3 answered.** A `-ctxcp` 4-vs-32 A/B pair at Q6_K's winning ratio, with the candidate config
line either confirmed or corrected.

**A9 — narrative + sync.** `sync-multivac.sh both` run at stage end with its result in the ledger's
Verified field; ledger `L-3` appended (marker verbatim); ≥1 PAPER-NOTES entry per §11; lifecycle
Status block + roadmap Status column updated; findings register rows for anything raised.

---

## 7. Exact verification

```bash
# --- T1 ---
ssh multivac 'pgrep -af "watchdog.sh|worker.sh"'                 # expect EMPTY after quiesce
ssh multivac 'ls /srv/bench/orchestrator/state/*.done | wc -l'   # unchanged (6)
ssh multivac 'df -B1 /srv/models / ; nvidia-smi --query-gpu=index,memory.used --format=csv,noheader'

# --- T2 (gate) ---
ssh multivac 'cd /srv/bench/e12 && python3 experiments/validate_v2.py            --out /srv/bench/e12/validate-v2.json'          ; echo "positive rc=$?"   # 0
ssh multivac 'cd /srv/bench/e12 && python3 experiments/validate_v2.py --selftest --out /srv/bench/e12/validate-v2-selftest.json'; echo "selftest rc=$?"   # 0 iff all 4 caught
ssh multivac 'python3 -c "import json;d=json.load(open(\"/srv/bench/e12/validate-v2-selftest.json\"));print([(f[\"id\"],f[\"caught\"],f[\"caught_by\"]) for f in d[\"faults\"]])"'
#   expect [("F1",True,"C1"),("F2",True,"C3"),("F3",True,"C2"),("F4",True,"C4")]

# --- T3a / T3b ---
ssh multivac 'bash /srv/bench/e12/experiments/verify-sweep.sh'; echo "sweep rc=$?"   # 0
ssh multivac 'df -B1 /srv/models / | cat'                        # >=60e9 and >=55e9 available
ssh multivac 'docker images | grep -c vllm'                      # 0
ssh multivac 'ls /srv/engines/nvfp4 >/dev/null && echo KEEP-OK'  # KEEP-OK  (DEC-4)
ssh multivac 'python3 -c "import json;d=json.load(open(\"/srv/bench/env-manifest.json\"));print(len(d.get(\"deleted_items\",[])), any(\"UD-Q6_K.gguf\" in g[\"file\"] for g in d[\"gguf_models\"]))"'  # 5 True

# --- T4 / T5 ---
ssh multivac 'for q in Q4_K_XL Q5_K_XL Q6_K Q6_K_XL; do python3 - <<PY
import json,glob
for f in glob.glob("/srv/bench/e12/tsweep-v2-$q*.json"):
    d=json.load(open(f)); t=d["trials"]
    print("$q", "cells=",len(t), "ok=",sum(1 for x in t if x["ok"]),
          "best=",(d.get("best") or {}).get("ts"), (d.get("best") or {}).get("ctx"),
          "modes=",sorted({x.get("failure_mode") for x in t if not x["ok"]}))
PY
done'                                                            # cells>=6 per quant; modes classified
ssh multivac 'ls -la /srv/bench/server-timings/ | wc -l'         # grew by >= number of cells
ssh multivac 'find /srv/bench/server-timings -name "e12-*.serverlog" -size -1c | wc -l'   # 0 empty logs

# --- T6 ---
bash tools/sync-multivac.sh both
ls data/bench/e12/ && git -C . status --short
```

---

## 8. Owner gates

| id | question | recommendation | blocks? |
|---|---|---|---|
| **Q-A1** | Run the Q6_K_XL `-ts` bracket (3–5 cells, 60–90 min) before deleting it, closing G21? | **Yes.** It is cheap and it protects a published number for the highest-accuracy quant from becoming permanently uncorrectable. | **No** — Wave 1 starts either way; only the position of step 1b moves. |
| **Q-A2** | If `/srv/models` lands at 59.8 GiB (F-C — passes in GB, misses 60 GiB by 204 MB), accept the decimal-GB reading, or authorize one more deletion? | **Accept the byte-explicit decimal gate (≥60×10⁹ B, measured 64.2×10⁹).** The only untapped levers are `.hf-cache/hub` (3.88 GB) and `models--z-lab--DFlash2` (3.85 GB) — neither is approved, and DFlash2 is in scope for Wave 2. | **No** — answer needed only at T3b. |
| **Q-A3** | Leave the legacy orchestrator quiesced through Waves 2–4 (restore at ship), or restore after Wave 1? | **Leave quiesced.** Waves 2–3 need the GPU exclusively; all its queued jobs are `.done`. | **No** — default is quiesced. |

---

## 9. Risks

| id | risk | likelihood | mitigation | residual |
|---|---|---|---|---|
| **RA-1** | Legacy worker seizes `llamasrv`/:8080 mid-sweep, or its `kill_server llamasrv ""` destroys a container's logs unsaved (F-A) | med → low after T1 | D4 triple defence: quiesce, `llamasrv-e12`, `gpu.lock`; `preflight()` refuses to launch into a dirty host | a manual `docker run` by another operator; `preflight()` catches it at the next cell |
| **RA-2** | Marginal-rung VRAM nondeterminism produces a false ceiling (R2) | **high** — Q6_K peaked at 15,320/15,650 MiB, **330 MiB of headroom, inside the noise band** | bracket + mandatory re-test of the rung above; true-peak 1 Hz sampler; failure-mode classification | ceilings are honest *for this image*; a re-test-passing rung is reported with both attempts |
| **RA-3** | Speed ranking driven by measurement noise rather than by `-ts` | med | D2: n_predict 192, 10 % → median-of-3, imbalance tie-break | ratios genuinely within noise are reported as **tied**, not ranked |
| **RA-4** | Wave exceeds the conductor's 2 h wall / 30 min idle worker timeout | **high** — 8–11 h of GPU work | **mandatory**: `nohup setsid bash runner.sh &` + pid file + per-cell state files (host has no `tmux`); the agent polls and re-attaches; every script is resumable (§3.3) | a host reboot loses in-flight cells only |
| **RA-5** | Deletion is irreversible and something needed later is gone | low | manifest-before-delete with sha256 + bytes + **RepoDigests**; 1a/1b split; KEEP list restated in §1.3; `verify-sweep.sh` re-checks every KEEP item | Track B E9 still needs a 22 GB re-download + image re-pull — already accepted in DEC-4 |
| **RA-6** | `/` refills silently after the sweep (`job_score_verified50`'s 40 GB guard stops deferring at ~83 GB free) | med if worker restarts | T1 quiesce + `state/*.done` on the KEEP list + `verify-sweep.sh` free-space re-check at T6 | — |
| **RA-7** | `-ctxcp` 4 → 32 shifts VRAM and silently invalidates ceiling comparisons | med | D3: sweep at 4, A/B once, adopt deliberately | if Δ ≠ 0, Waves 2–4 must re-derive their ceilings — flagged in the handoff |
| **RA-8** | `-fa auto` resolves differently from e11 and moves VRAM | low (`-ctv q4_0` requires FA, so e11 must already have had it on) | C1 asserts FA state from the serverlog; any change is recorded as a confounder | — |
| **RA-9** | Q4_K_XL's 262K/229K "init-hang" is a fixed engine limit, not a VRAM one → rebalancing buys nothing | med | the classifier distinguishes `init-hang` from `compute-buffer-oom`; a null result is still a publishable systems finding | outcome recorded either way |
| **RA-10** | 14 GiB RAM + 3 GiB swap already used; concurrent sha256 of 61 GB and a 25 GB mmap thrash page cache | low-med | strict serialization (§4); sha256 under `nohup`, one file at a time | slower, not wrong |

---

## 10. Rollback

**Code/docs** — everything is a new file under `experiments/` plus append-only edits to the lifecycle
file and PAPER-NOTES. `git revert` of the wave commit restores the repo exactly; nothing on the host
is overwritten (e11 is untouched — v2 files are new names in a new directory).

**Host state** — `restore_legacy.sh` restarts the watchdog (which restarts the worker within 120 s),
using the pids/command recorded in T1. `gpu.lock` is removed on every exit path, including failure.

**Deletions** — genuinely irreversible; that is why the order is *docs → manifest → delete* and why
1b is deferred. Recovery path, recorded in `deleted_items[]`:

| item | recovery | cost |
|---|---|---|
| IQ4_XS GGUF | `hf download unsloth/Qwen3.8-27B-GGUF <file>` → verify sha256 `40fac405…` | 14.25 GB |
| Q6_K_XL GGUF | same → verify `701d8fa9…` | 25.30 GB |
| NVFP4 hf-cache | duplicate of `/srv/engines/nvfp4`, which is **KEPT** — recovery is a local copy | 0 |
| vllm images | `docker pull vllm/vllm-openai@<RepoDigest>` (byte-exact only because T3a records the digest) | 59.7 GB |

**Point of no return:** the first `rm` in T3a. Everything before it is reversible; A3's byte-exact
manifest is the safety net after it.

---

## 11. Expected PAPER-NOTES entries (§ per protocol)

- **§Systems findings** — `-ts` rebalance deltas per quant, with imbalance MiB; the G13 de-confound
  verdict on Q5-vs-Q6; the three distinct failure modes as an engineering finding; **F-D**: the
  measured sampling defaults on `llamacpp-mtp:latest` differ from the upstream-documented set
  (a silent-misconfiguration hazard, and a correction owed to the lifecycle file's R1).
- **§Context axis** — corrected/confirmed ceilings per quant with the bracket + re-test evidence;
  the G21 result for Q6_K_XL (or the explicit lower-bound caveat).
- **§Speculative decoding** — MTP acceptance at depth per ratio; **`/props` misreports
  `speculative.types: none` while spec is live — use `timings.draft_n`** (a reproducibility trap).
- **§Reproducibility & provenance** — the champion quant `UD-Q6_K` was unpinned in `env-manifest`
  until this wave; RepoDigest-vs-image-id as the requirement for byte-exact image recovery.
- **§Sampling & protocol** — the 2-token thinking probe as a ~1 s discriminator;
  `reasoning_effort:"none"` failing on this template while `enable_thinking:false` works (G17
  signal, Wave 2 owns the verdict).

Every entry carries n, conditions (quant, ctx, KV, spec, ratio, `-ctxcp`), the artifact path under
`data/bench/e12/`, and the image id — `feb0231976b6…` is **not** the image that produced the
historical 262K/tensor-split corpus (G7), and that caveat must travel with every comparison.

---

## 12. Out of scope → new tasks, not edits in this wave

`-ctkd`/`-ctvd` draft-KV sweep (Wave 2 — legality confirmed §1.5) · G17 equivalence verdict (Wave 2) ·
G8 losslessness at temp > 0 (Wave 2) · `--cache-reuse` and ubatch sweeps (Wave 2, smoke first) ·
speed-vs-filled-context curve G14 (Wave 4) · moving `UD-Q6_K.gguf` from `/` to `/srv/models` to
rebalance the two volumes (a real headroom win of ~22 GB on the tighter disk, but it changes the
container mount path recorded in existing provenance — **file it, do not do it here**) ·
the G18 untested quants · any deletion not on the DEC-4 list.

---

## 13. Handoff to the Wave-1 implementer

1. Read §1 before writing code — it is measured, and it contradicts the lifecycle file in two places
   (F-B, F-D).
2. `experiments/` is new; `/srv/bench/e11/` is the reference implementation. **Port, don't reinvent** —
   `ctx_ceiling.probe()`'s behavioural gate is correct and hard-won; keep it and add §3.1's items.
3. The only things that gate the wave are A1–A9. Everything else is engineering judgement.
4. Nothing gets deleted until the ledger entry, the PAPER-NOTES entries, and the manifest are
   **committed**. That order is not advisory.
5. Run detached (`nohup`, no `tmux` on the host) or the conductor will kill the sweep at 2 h.
6. `bash tools/sync-multivac.sh both` at stage end; put its result in the ledger's `Verified:` line.

<!-- /consensus-winning-plan:qbench-t1-8f05db1f10552b03a1beda52c51944302348a299695c65f02ac5aaaf34a64849 -->

## Accuracy program — four-quant amendment (2026-08-30, DEC-9 + DEC-10)

This section amends the §Benchmarks table for the four-arm active set. It does not redesign the
suite: the instruments, the sweet spot and the order were approved under DEC-4 and are kept. What
changes is the arm count, the comparison depth, and where accuracy sits in the wave order.

### The rule that makes a four-quant comparison legitimate

**COMMON-DEPTH RULE.** Q6_K_XL tops out at 212,992 while Q5_K_XL and Q6_K reach 262,144. Comparing
each quant "at its own ceiling" confounds the quant with the depth it was measured at — and decode
and fidelity are both strongly depth-dependent on this host. Therefore:

> Every cross-quant accuracy cell runs at ONE common depth: `D_common = min(ceiling of the four
> actives)`, provisionally **212,992** pending Q4_K_XL's ceiling from the running sweep. Each
> quant's own ceiling is reported separately as a **context-axis** result, never mixed into an
> accuracy table. A quant is never credited with accuracy at a depth another arm cannot reach.

Each arm runs at its own winning `-ts` ratio (the ratio is a loading property, not a treatment):
Q5_K_XL `54,46` · Q6_K_XL `56,44` · Q6_K and Q4_K_XL per the running sweep. All arms keep the
Wave-1 configuration otherwise — `-sm layer`, q4_0 KV, MTP n=2, `-fit off`, `-ctxcp 4`, `-np 1`,
DEC-2 official sampling for task benchmarks, greedy for logprob instruments.

### Stage A — instruments that can actually rank the four quants (run FIRST)

Cheap, sensitive, and the only things that answer "which quant is most accurate".

| # | Instrument | Arms | Why it goes first | Est. |
|---|---|---|---|---|
| A1 | **E2 KV fidelity** — code-NLL f16 vs q4_0 at `D_common` and 32K | 4 | **Gates everything.** Every number this project has produced depends on q4_0 KV and nothing has ever validated it. If q4_0 costs fidelity, every config line changes. Decision rule already fixed: ΔNLL ≤ 3 % + divergence ≤ 6/256 | ~3-4 h |
| A2 | **PPL Protocol 1**, full WikiText-2, 602 windows | 4 | most sensitive discriminator available (±0.041 SE, G22); Q6_K cell missing, Q6_K_XL cell new; comparable to Unsloth's published tables | ~30 min/arm |
| A3 | **Code-NLL ladder (protocol-4)** at {32K, 64K, 128K, `D_common`} | 4 | the target-workload analogue — a coding agent's accuracy at depth, which is the actual Track A question | ~3-4 h |
| A4 | **KL divergence vs Q6_K_XL** as reference arm | 3 vs ref | direct quant-degradation measure, the instrument Unsloth publishes; DEC-9(c) makes Q6_K_XL the natural reference | ~1-2 h |

**Stage A output: a defensible accuracy ranking of the four quants, with CIs, in ~8-12 h.**
This is the deliverable that has been missing.

### Stage B — validators, not rankers (run after Stage A)

These answer "is this configuration sane, and does it reproduce published numbers" — they do NOT
rank the arms, and the plan must say so wherever they appear.

| # | Instrument | Arms | n | What it can and cannot say | Est. |
|---|---|---|---|---|---|
| B1 | HumanEval+ non-thinking, full set | 4 | 164 | ±4.6 pts — sanity + empty-rate only | ~1 h/arm |
| B2 | LiveCodeBench v6 subset (5-problem pilot first) | 4 | 100 | ±9-10 pts — validates against Qwen's official 90.3 | ~2 h setup + ~4 h |
| B3 | SWE-bench Verified, 25-smoke → 50 stratified | 4 | 25/50 | ±12 pts at n=50 — config validator; eval images land on `/` | ~14-18 h |
| B4 | Code-NIAH at depth + agentic steps | 4 | 36/arm | per-depth Wilson CIs; loop-vs-converge signal | ~8-10 h |

Smoke-before-deploy stays a hard gate on every one of these, and `validate_v2.py` must pass at the
launched configuration before any full run.

### Why this order, in one line

The four quants differ by 1-3 accuracy points. Stage B's instruments carry ±4.6 to ±12 points of
uncertainty; Stage A's carry ±0.041. **Running Stage B first would spend 25-35 h of GPU to produce
four overlapping intervals and no answer.**

### What this costs and what it does not

- Four arms instead of three: **+33 % on every accuracy cell**.
- Nothing in Wave 1 is invalidated — the `-ts` ceilings and speed rows stand as measured.
- No re-download, no new corpus: `wikitext2-test.txt` and the django corpus are both on disk, and
  the `.venv-evalplus` / `.venv-swebench` environments already exist.
- Wave 2 (MTP/DFlash) is not cancelled, only re-ordered after Wave 3.

## Small-Sample Accuracy protocol (SSA) — supersedes the Stage A/B program (2026-08-30, DEC-11)

Owner directive: the four-arm program above is days of GPU. Replace it with something an academic
or ML-engineering reader would accept as a sound sample, in **hours**. This section is that
protocol, with its methodology grounded in what the relevant labs and tools actually do.

> **Sources of record for everything in this section: `docs/paper/METHOD-REFERENCES.md`** (R1-R7),
> which states what each source contributes and which SSA element it constrains.

### The single fact the design turns on

**Divergence instruments draw their statistical power from TOKEN count; task benchmarks draw theirs
from PROBLEM count.** A coding benchmark has 164 problems and cannot be made bigger cheaply. A
divergence measurement over the same wall-clock has tens of thousands of per-token observations, so
its CLT standard error is smaller by orders of magnitude. That is why 30 minutes of KL divergence
can rank four quants that 20 hours of task benchmarking cannot — and it is the accepted practice,
not a shortcut:

- **llama.cpp** ships this exact instrument: `llama-perplexity --kl-divergence-base <file>` records
  reference logits, `--kl-divergence` scores a quant against them. One pass emits mean KLD with
  uncertainty, PPL ratio, mean Δp for correct tokens, Δp percentiles, RMS Δp, and the frequency of
  identical top-token assignments. Wikitext-2 is the stated convention.
- **Unsloth** ranks its Dynamic GGUFs on **mean KL divergence** — 150+ benchmarks — and explicitly
  warns that calibrating and evaluating on the same Wikipedia-like data overfits the metric.
- **Fireworks** evaluates production quantization on KLD + token rejection rate, splits prefill from
  generation, forces the quantized model to follow reference completions, and publishes a usable
  threshold: **KLD < 0.007 for high-quality deployments**. They also state the reason to prefer KLD
  over perplexity: PPL has an **averaging bias** — tokens made worse are cancelled by tokens made
  better, so real degradation hides inside an unchanged mean.
- **LocalBench's** GGUF quality benchmark uses **~250,000 tokens across 6 task domains**, reports
  **KLD on prompt tokens only** plus **top-1 agreement %**, and observes KLD ≈ 0.01–0.03 for Q4_K_M.
- **Miller (Anthropic), "Adding Error Bars to Evals"** supplies the statistics: CLT standard errors,
  **paired per-question differences between models** rather than independent means, and power
  analysis to size a comparison.

### The protocol

**Reference arm: UD-Q6_K_XL.** No FP16 exists on the host and a 27B F16 GGUF (~54 GB) exceeds free
space on `/srv/models`. Every divergence figure is therefore **relative to the least-quantized
available arm**, and must be labelled that way in every table — it measures ladder degradation, not
absolute distance from the unquantized model. DEC-9(c) already assigned Q6_K_XL this role.

**Sample: 65,536 tokens per domain per arm** (32 chunks × 2,048-token context, matching the ~2,048
convention). Against LocalBench's 250k across 6 domains, this is 131k across the 2 domains that
matter here. At n = 65,536 per-token observations the standard error on mean KLD is σ/256.

| Step | What | Arms | Est. |
|---|---|---|---|
| **S0** | Smoke: 4-chunk run end-to-end, assert the KLD fields are populated and `validate_v2` passes at the launched config (hard gate, small-before-big) | 1 | ~10 min |
| **S1** | Record reference logits from Q6_K_XL on both domains | ref | ~15 min |
| **S2** | **D1 wikitext-2** — KLD + top-1 agreement + PPL, the published convention, gives comparability with Unsloth/llama.cpp tables | 3 | ~20 min |
| **S3** | **D2 django code corpus** — same instrument on the target workload. This is the contribution: quant degradation measured on *code*, where the published tables measure prose | 3 | ~20 min |
| **S4** | **E2 KV fidelity** — same instrument, `-ctk/-ctv f16` vs `q4_0`, on the reference arm. Non-negotiable: every number this project has produced rests on q4_0 KV and nothing has validated it | 1 | ~20 min |
| **S5** | **HumanEval+ prompt-KLD** — the divergence instrument over the 164 task prompts with forced reference completions (the Fireworks method). Pure prefill, no generation | 3 | ~15 min |
| **S6** | **Generative HumanEval+ on the two extremes only** (Q4_K_XL vs Q6_K_XL), scored as **paired per-problem differences**, seed-matched, official DEC-2 non-thinking sampling | 2 | ~2 h |
| | | **total** | **~3.5 h** |

### Why S6 is two arms and not four

At n=164 the independent-comparison CI is ±4.6 points and the arms differ by 1–3 — four arms would
buy four overlapping intervals. Two arms at the ladder's extremes, analysed **paired**, answers the
only question a task benchmark can answer here: *is there a detectable task-level difference at all
between the cheapest and the most faithful quant?* A null result is a publishable finding, not a
failure — it is the empirical justification for ranking on divergence, and it is reported as such
with its power stated.

### What this yields for the paper

Per arm, on two domains: mean KLD ± uncertainty, top-1 agreement %, Δp percentiles, RMS Δp, PPL and
PPL ratio — plus a KV-dtype fidelity verdict and a paired task-level anchor. Pre-registered
interpretation bands from the sources: **KLD < 0.007 high-quality (Fireworks)**; **0.01–0.03 the
observed Q4_K_M range (LocalBench)**. Bands are cited as external reference points, not adopted as
this project's pass/fail rule.

### Honest limits, to be stated in the paper

1. Divergence is measured against Q6_K_XL, not FP16 — a ladder-relative measure.
2. Prompt-token divergence is not generation quality; S6 is the only generative evidence and it is
   deliberately small and reported with its power.
3. Both corpora are single-domain (English prose, Python/django). No multilingual or tool-calling
   coverage, unlike LocalBench's 6 categories.
4. Unsloth's calibration-contamination warning applies: these GGUFs' imatrix calibration data is not
   published in detail, so a wikitext-favourable bias cannot be excluded — which is exactly why D2
   (code) carries the weight for the Track A conclusion.
5. Logits files are ~11 GB per domain; they land on `/` (82.9 GB free) and are deleted after use.

### What SSA replaces and what it does not

Replaces: Stage A's PPL/code-NLL/KLD program and Stage B's LCB v6, SWE-bench, NIAH and agentic runs
**for the purpose of ranking quant accuracy**. Those remain in the plan as Phase 6-8 work if the
owner ever wants published-anchor comparability; they are no longer on the critical path.
Does not replace: Wave 1's context ceilings and speed rows (a different axis), or E2 (kept, as S4).

DEC-11 | 2026-08-30 | S2-execute | owner | scope cut on the accuracy program
Context: DEC-10's Stage A + Stage B program is 35-47 h of GPU across four arms. Owner: "we need a
much, much smaller version... something that academia and AI Engineers and Researchers would accept
as a good sample, but that won't take 3 or 4 entire days... hours, not days, and not many hours."
Decision: adopt the **Small-Sample Accuracy protocol (SSA)** above — ~3.5 h, four arms, divergence-
first, with a two-arm paired task anchor. Stage B's LCB v6 / SWE-bench / NIAH / agentic batteries
come OFF the critical path; they stay in the plan as optional Phase 6-8 work.
Why: the ranking question is answerable by KL divergence at a fraction of the cost, and doing so is
established practice rather than a compromise — llama.cpp ships the instrument, Unsloth ranks its
released quants on it, and Fireworks uses it for production quantization decisions with a published
quality threshold. The task batteries were never able to rank arms separated by 1-3 points; keeping
them on the critical path spent days to produce overlapping confidence intervals.
Cost of the cut, stated: no comparability against Qwen's official LiveCodeBench 90.3 anchor, no
agentic/SWE evidence, and no absolute-vs-FP16 distance (reference is Q6_K_XL). All four are
recorded as paper limitations rather than silently dropped.

## Decision log

<!-- consensus-winner-decision:qbench-t1-8f05db1f10552b03a1beda52c51944302348a299695c65f02ac5aaaf34a64849 -->
DEC-consensus-winner | 2026-08-29 | S1-plan | conductor
Context: sole architect plan accepted (no voting round)
Decision: slot a selected from qbench-t1-PLAN-A
Why: votes={}; tiebreak_used=False; plan_file=docs/build-stream/plans/qbench-t1-plan-a.md



DEC-1 | 2026-08-30 | S0 | owner
Context: Owner narrowed scope to 3 quants (Q4_K_XL, Q5_K_XL, Q6_K), coding-agent-config-first
testing, MTP/DFlash sweeps with settings variation, disk sweep allowed under preservation
rule, benchmark sweet spot to be proposed and approved before deployment.
Decision: PENDING — owner must approve (a) conductor shape + roles, (b) delete list
(incl. NVFP4/vLLM images and the Q6_K vs Q6_K_XL reading), (c) benchmark sweet spot + order.
Why: these three gates are exactly the owner's stated checkpoints before anything runs.

DEC-2 | 2026-08-30 | S1 | owner
Context: Phase 4 proposed a coding-agent sampling candidate (temp 0.2, presence 0.0) to
A/B against Qwen official settings. Owner ruled: use Qwen/Unsloth official model settings
for the tests.
Decision: Task benchmarks run at the official settings — non-thinking: temp 0.7, top_p 0.80,
top_k 20, min_p 0.0, presence_penalty 1.5, repetition_penalty 1.0; thinking: temp 1.0,
top_p 0.95, top_k 20, min_p 0.0, presence_penalty 0.0. Greedy (temp 0) remains the
instrument for logprob-based work only (PPL/NLL/divergence). Phase 4 becomes an
official-settings validation set (G17 equivalence, G8 losslessness at temp>0, pp-behavior
probe) instead of a candidate A/B. MTP-losslessness implication: accuracy arms that use
spec decode at temp>0 must re-prove equivalence or run no-spec (pilot decides).
Why: owner's explicit instruction; makes absolute scores comparable to published numbers
(resolves the G16 comparability concern for the new runs).

DEC-3 | 2026-08-30 | S1 | owner
Context: Conductor shape + roles chosen from Option A (solo architect) and the standing
registry.
Decision: SOLO architect mode. architect = claude / claude-opus-5 @ max; implementer =
pi / zai/glm-5.3-flash @ max; code-reviewer = pi / zai/glm-5.3-flash @ max; fixer = claude /
claude-opus-4-6 @ max. No fallbacks (registry unchanged). Main agent acts as conductor
manager (monitoring, incident surfacing, owner gates).
Why: owner directive 2026-08-30. Solo plan is appropriate because the lifecycle file already
holds the detailed plan; the architect reviews/freezes it.

DEC-4 | 2026-08-30 | S1 | owner
Context: Delete list + preservation audit + sweet-spot + Q6_K reading presented.
Decision: APPROVED as presented: quants = UD-Q4_K_XL / UD-Q5_K_XL / plain UD-Q6_K; delete
IQ4_XS + Q6_K_XL GGUFs, NVFP4 hf-cache duplicate, vLLM stable+nightly images; KEEP
/srv/engines/nvfp4 (E9 option preserved); sweet-spot suite + order approved; official
sampling per DEC-2; small-tests-first is a hard gate; all logs saved + docs appended
BEFORE any deletion or teardown.
Why: owner directive 2026-08-30.

DEC-5 | 2026-08-30 | S1 | owner
Context: The standing sync rule was first written as "everything from multivac". Owner
clarified: synchronization scope is DOCUMENTATION ONLY — CLAUDE.md, PAPER-REFERENCES.md, the
multivac paper-data folder, and this repo's docs. Models, containers, images, and bulk
artifact trees are NOT synced; artifacts are pulled selectively when needed as evidence.
Decision: tools/sync-multivac.sh pull = docs of record only (CLAUDE.md + multivac paper-data
folder); push = repo docs + experiments/; new `artifact <remote> <local>` subcommand for
selective evidence pulls. The watcher's periodic pull runs the docs-only sync.
Why: owner message 2026-08-30; keeps the paper folder lean and the repo git-friendly.

DEC-6 | 2026-08-30 | S1 | owner
Context: Owner approved Plan A (qbench-t1-plan-a.md) with the architect's recommended
defaults for all three owner gates — Q-A1 YES (bracket Q6_K_XL -ts ratios before deleting
it; closes G21), Q-A2 accept the explicit byte gate (>=60x10^9 B on /srv/models; measured
64.2x10^9), Q-A3 leave the legacy orchestrator quiesced through Waves 2-4 (restore at ship).
Owner also changed one role: code-reviewer is now claude claude-opus-5 @ max (was
pi zai/glm-5.3-flash @ max). Updated in the routing registry and in the run cast.
Decision: APPROVE Plan A; reviewer role = opus-5 max; conductor released to implement Wave 1.
Why: owner directives 2026-08-30.

DEC-7 | 2026-08-30 | S2-execute | agent (recorded, owner-visible) | supersedes §5 Q6_K_XL row
Context: The approved §5 matrix gave Q6_K_XL the ratio list `58,42 · 62,38 · 60,40`, all of which
shift MORE model onto GPU0, on the reasoning that 54,46 was "already known-failed". Live
measurement at 196,608 shows 58,42 already OVERSHOOTS on this quant: GPU0 15,036 / GPU1 12,276 MiB,
2,760 MiB GPU0-heavy, while the default split is 1,482 MiB GPU1-heavy. The balance point lies
BETWEEN default and 58,42 and the approved list contained no ratio there.
Decision: Q6_K_XL's ratio list becomes `[default, 52,48, 54,46, 56,44, 58,42]` and the ladder
brackets UP from 196,608, not down.
Why: with the approved list every cell would have failed, the sweep would have descended rung by
rung, and G21 would have concluded "rebalance does not lift the Q6_K_XL ceiling" — a FALSE NEGATIVE
on the highest-fidelity quant, which is Track A priority (1). Physically, Q6_K_XL's layers are the
largest on the ladder (25.30 GB), so a smaller layer-fraction shift moves the same MiB than on
Q6_K (21.98 GB), whose optimum is 58,42. Confirmed by measurement: 52,48 cuts the imbalance from
1,806 to 448 MiB, and 56,44 LOADS at 196,608 (17.26 tok/s at 0.9474 depth) against a published
Q6_K_XL MTP ceiling of 131,072.
Note: this is an agent correction to an owner-approved plan, made because the plan as written
could not answer its own question. It widens no scope and spends no extra owner budget — the same
cell count, pointed the right way. Flagged here for the owner rather than applied silently.

DEC-8 | 2026-08-30 | S2-execute | agent (recorded, owner decision pending) | execution route
Context: The Compass Forge conductor halted 2026-08-30T01:57Z with `VERDICT-REPAIR-EXHAUSTED`
(`qbench-t1-code-reviewer`, task `REREV-NV2-REREV-NV1-REREV-qbench-t1-REVIEW-r1`, repair_count 2,
verdict `fail` from zai/glm-5.3-xhigh; `conductor.pid` empty — the process is gone). Wave-1 work
continued regardless, hand-driven on multivac via `runner_wave1.sh` plus a direct review pass.
Decision: Wave 1 finishes HAND-DRIVEN. The conductor stays halted and is NOT restarted mid-sweep;
this lifecycle file, its ledger, and PAPER-NOTES are the record of authority for the remainder of
Wave 1. The stale reviewer task is left as-is for an owner call at the wave boundary.
Why: the running measurement is the scarce resource — restarting the pipeline mid-sweep risks a
second runner, `gpu.lock` contention and junk cells (exactly the D6 failure already observed).
The conductor's own halt contract requires owner action anyway, so nothing is lost by deferring it.
Consequence: `data/watch/state.json` health=VERDICT-REPAIR-EXHAUSTED describes a pipeline that no
longer reflects the work; read this file, not the watcher, for Wave-1 status. The watcher itself
(pid 88692) is left running — its only remaining function is the 10-minute docs pull, which is
harmless and keeps the mirror fresh.

OPEN-1 | 2026-08-30T03:44Z | RESOLVED 2026-08-30 by owner -> DEC-9 (KEEP Q6_K_XL). Original text kept below.
Context: DEC-4 approved deleting the Q6_K_XL GGUF (25,299,061,664 B). At the time, Q6_K_XL was
recorded as "best raw accuracy but 131,072 MTP ceiling" — the low ceiling was part of why it could
go. That premise is now measured false. Under the DEC-7 ratio correction, Q6_K_XL loads at
**212,992** at `-ts 56,44` (12.98 tok/s at 0.9469 depth; 196,608 gives 17.26 tok/s at 0.9474),
with 229,376 bracketing above. That is +81,920 tokens (+62.5 %) over the published ceiling, on the
highest-fidelity quant on the ladder.
Question: does DEC-4's deletion still stand? The trade has changed shape — Q6_K_XL is now
"best accuracy, 212,992 context" rather than "best accuracy, 131,072 context", and it sits against
plain Q6_K's 262,144. It remains the only quant on the ladder whose accuracy has never been
measured against the others (Phase 6 has no NLL/PPL data for it).
Consequences either way: deleting it frees the 25.3 GB that carries `/srv/models` past the
>=60x10^9 B A3 gate (38.9 + 25.3 = 64.2 GB) and the file is re-downloadable but not cheaply;
keeping it means the A3 gate needs a different 25 GB or an owner waiver, and Phase 1 does not
close. Nothing is deleted until this is answered — the sweep is not blocked by it.

DEC-9 | 2026-08-30 | S2-execute | owner | resolves OPEN-1; supersedes DEC-4's delete of Q6_K_XL
Context: DEC-4 approved deleting the Q6_K_XL GGUF while its ceiling was believed to be 131,072.
Wave 1 measured 212,992 at `-ts 56,44` (G21 closed). Owner: "Do not delete Q6_K_XL, it became
interesting with this new test, but we do need to test its accuracy in the official benchmarks
against the others."
Decision: (a) Q6_K_XL is NOT deleted; T3b delete-1b is cancelled. (b) The active set becomes FOUR
quants — UD-Q4_K_XL, UD-Q5_K_XL, UD-Q6_K, UD-Q6_K_XL — for the accuracy program. (c) Q6_K_XL
additionally serves as the fidelity REFERENCE arm for divergence-based instruments (it is the
least-quantized model on the ladder).
Why: the premise behind its deletion was measured false, and it is the only quant on the ladder
whose accuracy has never been measured against the others — deleting it would have made that
permanently unanswerable without a 25 GB re-download.
Consequences, stated plainly:
- **A3's `/srv/models` limb cannot be met** and is hereby WAIVED. Free space stays 38,924,001,280 B
  against a >=60x10^9 B gate. The waiver is safe because that gate existed to leave room for model
  downloads, and no further downloads are planned; the four actives are all resident. **A3's `/`
  limb (>=55x10^9 B) is NOT waived** — it currently passes at 83,012,120,576 B and it is the limb
  that matters, because SWE-bench eval images land on `/`. `verify-sweep.sh --stage 1b` and the
  Phase-1 byte gate are re-scoped to the `/` limb only.
- **Every accuracy cell costs +33 %** (4 arms instead of 3).
- Phase 1 closes on the stage-1a verification plus this waiver, not on delete-1b.

DEC-10 | 2026-08-30 | S2-execute | agent recommendation, owner may veto | wave order + accuracy design
Context: Owner asked where the accuracy requirement went. It was never dropped: accuracy is Wave 3
(Phases 6-8) in `qbench-t1-waves.json`, with the sweet-spot suite approved under DEC-4. Wave 1
(running) measures context and speed only, by design — an accuracy benchmark at depth cannot be
configured until the `-ts` sweep says what loads at what context. But Wave 2 (MTP/DFlash setting
sweeps, ~6-10 h GPU) sits in front of Wave 3 without gating it.
Decision: (a) **Run Wave 3 BEFORE Wave 2.** Accuracy is Track A priority (1); MTP/DFlash tuning is
a speed optimisation that changes no accuracy verdict, and Wave 3's own gate (E2) must be answered
before any config line is published anyway. Wave 2 keeps its content and moves after.
(b) Within Wave 3, run the SENSITIVE instruments before the validators — see the accuracy program
section below. (c) Adopt the common-depth rule below for all cross-quant accuracy comparison.
Why: G22 is already in this plan and it is decisive — HumanEval+ at n=164 carries +/-4.6 pts,
LCB v6 at n=100 carries +/-9-10, SWE-bench at n=50 carries +/-12, while the quants differ by 1-3
points. **The task benchmarks cannot rank these four quants and were never able to.** PPL, code-NLL
and KL divergence can. Running the expensive validators first would spend ~10-16 h of GPU to
produce four overlapping confidence intervals and no ranking.

## Ledger

### L-3 | 2026-08-29T21:14:13Z | S1-plan | claude-opus-5 | architect | Phase 0 -> Wave 1 draft <!-- bsc-ledger:qbench-t1-PLAN-A -->
Did: Consensus-architect DRAFT (solo run) for Wave 1 (lifecycle Phases 1-3). Wrote
docs/build-stream/plans/qbench-t1-plan-a.md (512 lines): design, 7-task breakdown (T1..T6 +
T3a/T3b split), acceptance A1-A9, exact verification commands, 10 risks, rollback, expected
PN entries. Grounded in live reconnaissance of multivac (ssh probes + one 32K Q4_K_XL
bring-up, torn down log-first per hard rule 2 ->
/srv/bench/server-timings/arch-recon-props-20260829.serverlog, 4160 B). No lifecycle-plan
body, Status Block or roadmap edits: the architect role instruction forbids editing the
lifecycle plan, so only this append-only ledger entry was added.
Result: Plan A ready for owner review; qbench-t1-PLAN-A. Five plan-changing findings raised
(F-A..F-E) + two design deviations (D1, D2) + three no-gate decisions (D3, D4, D5):
F-A legacy orchestrator watchdog.sh(pid 2810112)+worker.sh(pid 3818720) STILL RUNNING; its
  job_agentic_steps takes container llamasrv + port 8080 and calls kill_server llamasrv ""
  with an EMPTY label -> removes a container without saving docker logs (hard-rule-2 breach).
F-B UD-Q6_K.gguf (21.98 GB champion quant) is on / via /srv/bench/models, NOT /srv/models,
  and has NO sha256 entry in env-manifest.json (E0 provenance hole).
F-C measured sweep lands /srv/models at 64,222,965,176 B = 64.22 GB = 59.81 GiB: the ">=60 GB"
  gate PASSES in decimal GB (+4.2 GB) and MISSES by 204 MB in GiB, and df -h rounds it to
  "60G" either way -> gate must be byte-explicit.
F-D lifecycle R1 says llama.cpp defaults are temp 0.80/top_k 40/top_p 0.95/min_p 0.05;
  MEASURED on llamacpp-mtp:latest: temp 1.0/top_k 20/top_p 0.95/min_p 0.05/presence 0.0.
F-E chat_template_kwargs {"reasoning_effort":"none"} FAILED (no choices in response) while
  {"enable_thinking":false} works -> early G17 signal, Wave 2 keeps the verdict.
D1 run the Q6_K_XL -ts bracket BEFORE deleting it (closes G21, ~75 min) -> Phase 1 splits into
  1a/1b and the disk gate is evaluated at wave exit; no approved decision reversed (gate Q-A1).
D2 "fastest that loads" gets a noise floor (n_predict 192; within 10 % -> median-of-3).
Also verified for the implementer: /completion echoes effective per-request sampling in
generation_settings (so the DEC-2 sampling contract is directly assertable); /props reports
speculative.types "none" while MTP is live (use timings.draft_n); 2-token probe cleanly
discriminates thinking ON/OFF; -ctkd/-ctvd exist on the image (Wave 2 axis is legal).
Verified: ssh multivac state audit (df -B1, du -sb, nvidia-smi, docker images/system df -v,
docker info); llama-server --help flag audit on llamacpp-mtp:latest; live 32K bring-up with
the full candidate launch contract -> /props + /completion + 3 chat probes, then log-saved
teardown, gpu.lock released, GPUs back to 2 MiB; read /srv/bench/e11/{lib_probe,ctx_ceiling,
tsweep,pad,validate2}.py and the tsweep/ceiling artifacts; arithmetic re-checked in python3.
No repo tests exist (docs/data repo); no build or gate to run.
Next: owner review of Plan A (gates Q-A1 disk/G21 ordering, Q-A2 byte-explicit disk gate,
Q-A3 keep legacy orchestrator quiesced) -> Wave 1 implementer executes T1..T6.

### L-2 | 2026-08-30 | S1-plan | main-agent | planner | Phase 0
Did: Locked owner decisions into the plan (DEC-2 official sampling, DEC-3 conductor roles,
DEC-4 delete list/sweet-spot/Q6_K); wrote paper-notes protocol + PAPER-NOTES.md;
wrote wave instruction files 1-4 + qbench-t1-waves manifest; updated routing registry
(architect=claude-opus-5 max, implementer+reviewer=pi zai/glm-5.3-flash max, fixer=claude-opus-4-6 max, no fallbacks).
Result: Plan ready for conductor bootstrap: make_pipeline --with-planning --architects 1.
Verified: routing.py set outputs (4 writes confirmed); zai/glm-5.3-flash present in
`pi --list-models`; claude CLI 2.1.250 present.
Next: conductor preflight (real probes) -> make_cast -> spawn -> monitor.

### L-1 | 2026-08-30 | S0-frame/S1-plan | main-agent | framer | Phase 0
Did: Read CLAUDE.md (997 lines) + PAPER-REFERENCES.md (974 lines) on multivac; audited live
state (disk, models, images, containers, orchestrator idle, GPUs idle, e11 artifacts); fetched
Unsloth Qwen3.8 guide + official llama.cpp server docs; initialized plan repo
(/Users/user/Documents/multivac-paper, git + CF native pin 559af310…); wrote this lifecycle
file; created CF-SPEC-1 with clarify/plan/tasks.
Result: Plan created; three owner gates (conductor, delete list, sweet spot) block execution.
Verified: `ssh multivac` state audit; `compass-forge` init + spec spine output in CF state;
pin digest match OK.
Next: owner gates → conductor preflight → make_pipeline --with-planning → make_cast → spawn.

### L-4 | 2026-08-29T23:40:00Z | S2-execute | zai/glm-5.3-flash | executor | Wave-1 T1+T2+T3a-manifest <!-- bsc-ledger:qbench-t1-IMPL -->
Did: Wave-1 implementation, phases T1/T2/T3a-manifest (implementer, this task qbench-t1-IMPL).
  Authored experiments/ harness (commit fa9400c + fixes): lib_e12.py (hardened lib_probe
  successor: CONT llamasrv-e12, full launch contract returned verbatim, preflight() fail-loud,
  1 Hz VRAM sampler, save_and_kill log-first, classify_failure, record_env, spec_live,
  gpu.lock takeover), pad_e12.py, validate_v2.py (C1-C4 + selftest F1-F4), tsweep_v2.py
  (G13 fix: full ratio set, never early-return, resumable, D2 noise floor, A6 two-attempt
  bracketing, D3 ctxcp A/B), sweep_v2.sh (docs->manifest->delete enforced in code),
  verify-sweep.sh, quiesce_legacy.sh/restore_legacy.sh, runner_wave1.sh (nohup phases).
  T1: legacy orchestrator QUIESCED (watchdog 2810112 then worker 3818720; pids + restore
  command in /srv/bench/e12/quiesce-state.json; 6 state/*.done intact); preflight snapshot;
  e12 dir created; pads/corpus seeded from e11; D5 symlink validate_v2.py; sync push.
  T2 GATE GREEN: positive run C1-C4 all pass; selftest catches F1->C1, F2->C3, F3->C2,
  F4->C4 (artifacts /srv/bench/e12/validate-v2*.json, mirrored data/bench/e12/).
  T3a manifest COMPLETE (nothing deleted): deleted_items[] = iq4_xs-gguf 14,252,845,984 B
  sha 40fac405...; q6kxl-gguf 25,299,061,664 B sha 701d8fa9...; nvfp4-hf-cache 19 files
  23,444,505,588 B tree 5c15917b... (root-owned blobs read via sudo -n cat);
  vllm-nightly-image + vllm-v0.27.1-image with RepoDigests (byte-exact re-pull now possible);
  F-B REPAIRED: UD-Q6_K.gguf sha256 pinned in env-manifest. All deleted_utc still NULL.
  PN-1..PN-4 appended to docs/paper/PAPER-NOTES.md (F-D defaults, 2-token probe, F-E
  reasoning_effort:none Jinja exception, F1 fit-did-not-shrink).
Result: qbench-t1-IMPL T1/T2/T3a-manifest done. This commit IS the docs-before-delete gate:
  delete-1a runs only after it. 3 self-corrections during the stage (runner $phase var,
  lib_e12 launch log-first cleanup, validate C1 /props-after-teardown + f32 tolerance);
  all fixed and re-run green. New systems finding: -fit on at 262,144 on engine d222767
  loads full n_ctx (E1 shrink class did not reproduce) — PN-4.
Verified: ssh multivac 'pgrep -af watchdog.sh|worker.sh' -> empty (quiesced); state/*.done = 6;
  validate-v2.json ok=true checks C1..C4 all true; validate-v2-selftest.json ok=true faults
  [(F2,T,C3),(F3,T,C2),(F4,T,C4),(F1,T,C1)]; env-manifest deleted_items = 5 with hashes +
  RepoDigests, UD-Q6_K pinned True; sync-multivac.sh push rc=0.
Next: T3a delete-1a + verify-sweep --stage 1a -> detached T4 tsweeps (Q4/Q5/Q6) -> T5 G21
  bracket (Q6_K_XL) -> T3b delete-1b + byte gate -> T6 sync/ledger/PN close-out.


### L-5 | 2026-08-30T03:40:00Z | S2-execute | claude-opus-5 | conductor-manager | Wave-1 reconciliation (T3a-delete-1a, T4, T5 in flight) <!-- bsc-ledger:qbench-t1-RECONCILE -->
Did: Reconciled the record after ~4 h of unrecorded Wave-1 work (23:27Z–03:40Z) executed on
  multivac OUTSIDE the conductor. No GPU work was started, stopped or touched by this entry —
  the T4/T5 sweep is live and was left alone (see Next).
  (a) DOC-OF-RECORD REPAIR: this repo's `docs/` had fallen behind the multivac mirror by two
  commits' worth of content (23.5 KB vs 69 KB — it was missing the winning consensus plan, L-3,
  L-4 and PN-1..PN-4). A `sync-multivac.sh push` in that state would have CLOBBERED the multivac
  copy with a stale ancestor. `docs/` fast-forwarded from `data/multivac-src/build-stream-docs/`,
  verified byte-identical, AppleDouble `._*` junk (which matches the sync's `*.md` filter) deleted.
  (b) T3a delete-1a IS DONE — executed 2026-08-29T23:27:44Z, never recorded: iq4_xs-gguf
  14,252,845,984 B, nvfp4-hf-cache 23,444,505,588 B, vllm-nightly-image 8,642,650,217 B,
  vllm-v0.27.1-image 9,110,698,465 B, all with `deleted_utc` stamped. q6kxl-gguf `deleted_utc`
  correctly still NULL — held for its bracket under D1. `/srv/models` 1.2 GB -> 38,924,001,280 B
  free; `/` 83,012,120,576 B free.
  (c) REVIEW-AND-REPAIR PASS (02:30–03:10Z, Claude Code session on multivac) pulled in as evidence:
  8 defects found and fixed. Three are material and are now recorded as PN-5..PN-7 —
  the pad builder silently returning short pads (Q4_K_XL measured at 0.797 of window, not 0.948:
  both its speed row and its ceiling verdict were optimistic AND it was not comparable to
  Q5_K_XL); the >=0.90 depth gate documented but never enforced in code, which is why the first
  defect was invisible; and the §5 Q6_K_XL ratio list pointing the wrong way (DEC-7). Three more
  are process defects with no data consequence but real wedging risk: a never-started container
  wedging every subsequent cell, a zero-successful-cell sweep exiting 0 and writing a `.done`
  marker, and no single-instance guard — two runners raced and produced 32 junk cells across
  three quants (now `quarantine/*.race-025630`). An aggregator (`summarize_wave1.py`) was written;
  none existed, so nothing turned the tsweep JSONs into the wave's answer.
  (d) ARTIFACTS PULLED to `data/raw/e12/` (11 JSON/MD + 8 logs + quarantine evidence + the 13-file
  repaired harness under `harness-src/`), which also repairs the dangling `data/bench/e12/...`
  evidence paths in PN-1..PN-4 — that tree stopped syncing under DEC-5 and never existed in this
  repo; a remap note now heads PAPER-NOTES.md (old entries superseded, never rewritten). The
  harness copy is deliberately NOT at `$REPO/experiments/`: `sync-multivac.sh push` copies that
  path onto `/srv/bench/e12`, so creating it would let a later push overwrite the harness the
  sweep is running against.
  (e) §5 matrix corrected, phase table statuses updated (0 done, 1 partial, 2 done, 3 in-progress),
  status block re-pointed, DEC-7 (ratio direction) and DEC-8 (hand-driven execution) recorded.
Result: The record now matches the machine. One owner-visible item: DEC-7 is an AGENT correction to
  an owner-approved plan — the approved Q6_K_XL ratio list could not have answered G21, and would
  have returned a confident false negative on the highest-fidelity quant. Same cell count, opposite
  direction. Nothing was deleted, restarted or re-run by this entry.
  Results standing as of this entry:
  - **Q5_K_XL COMPLETE AND VALID** — reaches the full native 262,144 window when rebalanced and
    FAILS at the default split (compute-buffer-oom, imbalance 1,530 MiB). Best `-ts 54,46`,
    decode 10.82 tok/s at 0.948 depth (median-of-3 12.70), imbalance 742 MiB, MTP acceptance 0.516.
    9 of 10 cells ok, every one at depth 0.948. Supersedes E11a's 196,608 and E1's 163,840.
    This is a clean causal demonstration that the REBALANCE, not the quant, sets the ceiling:
    one identical configuration, five ratios that load, one that does not. Note the ratio with the
    smallest imbalance (58,42, 28 MiB) is the SLOWEST (8.50 tok/s) — balance and speed are
    different objectives, and G13's "keep the fastest that loads" is the right rule.
  - **Q6_K_XL** — `56,44` LOADS at 196,608: 17.26 tok/s at 0.9474 depth, MTP acceptance 0.8971,
    VRAM 15,416/15,840 MiB, imbalance 424 MiB. default/52,48/54,46/58,42 all compute-buffer-oom.
    Against a published ceiling of 131,072 that is +65,536 tokens, and G21 is closing POSITIVELY —
    the opposite of what the approved matrix would have concluded.
  - **Q4_K_XL, Q6_K** — no valid data yet; first-pass cells quarantined (shallow prefill / runner
    race), re-running under the repaired harness.
Verified: `ssh multivac` 03:36:37Z — runner pid 1498430 + tsweep pid 1498435 alive, container
  llamasrv-e12 up, currently on the G21 bracket above (212,992 @ 56,44, 2 attempts per A6);
  env-manifest `deleted_utc` read back for all 5 items; `df -B1` byte counts as quoted;
  multivac's docs of record untouched since 23:23–23:26Z (no concurrent writer — this session is
  the sole writer of the lifecycle file); `docs/` vs mirror diff clean after fast-forward;
  `data/raw/e12/` 20 files pulled, sizes logged. NOT verified and deliberately not run:
  `verify-sweep.sh --stage 1a` (it sha256s ~60 GB — the disk I/O would perturb the live
  measurement; it is the first thing to run when the sweep ends).
Next: let the sweep finish (Q6_K_XL bracket -> Q6_K -> Q4_K_XL; ~2-5 h at 14-16 min/deep cell).
  Then, in order: `summarize_wave1.py` -> `verify-sweep.sh --stage 1a` -> T3b delete-1b (Q6_K_XL,
  25,299,061,664 B, which is what carries `/srv/models` past the >=60x10^9 B A3 gate; 38.9 + 25.3
  = 64.2 GB, matching F-C's arithmetic) -> D3 `-ctxcp` 4-vs-32 A/B at Q6_K's winner (A8) -> T6
  close-out. Owner calls waiting at the wave boundary: DEC-7 acknowledgement, and what to do with
  the halted conductor's stale reviewer task (DEC-8).

Addendum 2026-08-30T03:41Z: `runner_wave1.sh` stops after its tsweeps — nothing chained to the
  closing steps, so the wave would have idled until a human noticed. Added
  `/srv/bench/e12/finish_wave1.sh` (pid 1661639, flock-guarded per D6): it waits for runner pid
  1498430 to exit, sleeps 45 s for the last container teardown and serverlog flush, then runs
  `summarize_wave1.py --md` and `verify-sweep.sh --stage 1a` — the two REVERSIBLE closing steps,
  in the only order that is safe (the sha256 pass cannot overlap a live measurement). It stops
  deliberately before T3b delete-1b: that deletion is irreversible, is gated on the Q6_K_XL
  bracket results reaching this ledger, and stays an owner action. A8 needs no step here — the
  D3 `-ctxcp` 4-vs-32 A/B runs inside the Q6_K sweep automatically (`tsweep_v2.run_d3`).

Addendum 2026-08-30T04:19Z (autonomous chain built out): the box now runs the remainder of the
  plan unattended in three stages, each waiting on the one before —
  `runner_wave1.sh` (T4/T5 sweeps) -> `finish_wave1.sh` (summarize + verify-sweep --stage 1a)
  -> `ssa_runner.sh` (SSA S0 gate, then S1-S4). Harness `experiments/ssa_kld.py` written and
  deployed; mirrored to `data/raw/e12/harness-src/`.
  Two safety properties were built in deliberately and both are verified:
  (i) `ssa_kld.py` REFUSES to start while any GPU experiment is live (`pgrep` on the sweep and
  on `llamasrv-e12`) — confirmed by running it during the sweep, which exited 4 without touching
  the GPU; and it exits 2 rather than 0 when no cell succeeded (Wave-1 defect D5).
  (ii) `ssa_runner.sh` waits on a CONDITION, not a pid. The first version waited on a pid from
  `pgrep`, which returned the setsid PARENT (1661575) rather than the working child (1661639) —
  the same parent/child split behind Wave-1 defect D6. Had the parent exited first, SSA would
  have started during the finisher's ~60 GB sha256 pass. Rewritten to require that no
  `finish_wave1.sh` process of any kind remains AND that the log carries the completion marker
  the finisher writes only on a clean exit; if the marker is missing it aborts (exit 6) for a
  human rather than proceeding. Caught before it could fire.
  S0 is a real gate: a 4-chunk end-to-end run must exit 0 with populated KLD fields before the
  full budget is spent; on failure the chain stops and does NOT fall through.
  Still requiring a harness that does not exist: S5 (HumanEval+ prompt-KLD) and S6 (generative
  HumanEval+, 2 arms, paired). Also noted from `llama-perplexity --help`: `--hellaswag`,
  `--winogrande` and `--multiple-choice` are built into the same binary and are logprob-scored
  (no generation), so a standard task anchor is available at near-zero GPU cost — proposed as an
  optional S7, not adopted without an owner call.


### L-6 | 2026-08-30T04:15:00Z | S2-execute | claude-opus-5 | conductor-manager | Wave-1 continuation, accuracy-scope decisions, host telemetry <!-- bsc-ledger:qbench-t1-SSA -->
Did: (a) OWNER DECISIONS recorded: DEC-9 (Q6_K_XL is NOT deleted — its measured 212,992 ceiling
  falsified the premise behind DEC-4's delete; it becomes the 4th arm AND the fidelity reference;
  T3b delete-1b cancelled; A3's `/srv/models` limb waived with reasons, `/` limb kept),
  DEC-10 (Wave 3 moves ahead of Wave 2 — accuracy is priority (1) and MTP/DFlash tuning gates
  nothing), DEC-11 (owner cut the 35-47 h four-arm accuracy program to the ~3.5 h **Small-Sample
  Accuracy protocol**). OPEN-1 marked resolved.
  (b) SSA DESIGNED AND GROUNDED, not invented: researched llama.cpp's own perplexity/KLD tool,
  the llama.cpp contributors' PPL-vs-KLD argument, Unsloth's Dynamic-GGUF KLD methodology (the
  provenance of the quants under test), Fireworks' production quantization evaluation, LocalBench's
  GGUF quality benchmark, Miller/Anthropic's *Adding Error Bars to Evals*, and the recent unified
  llama.cpp quantization paper. Written up as `docs/paper/METHOD-REFERENCES.md` (R1-R7) with a table
  mapping each SSA element to the source that constrains it. Design rests on one fact: divergence
  instruments draw power from TOKEN count (n = 65,536/domain/arm, SE = sigma/256) while task
  benchmarks draw it from PROBLEM count (n = 164, CI +/-4.6 pts against arms separated by 1-3 pts).
  Verified `llama-perplexity` is present in `llamacpp-mtp:latest` and both corpora are on disk.
  (c) HOST TELEMETRY extracted from the 1 Hz power log and written up as PN-11 (power envelope) and
  PN-12 (thermal asymmetry). This partially closes the "energy extraction from power-log.csv" item
  PAPER-REFERENCES.md itself lists as open.
  (d) SECOND STALE-COPY TRAP found and fixed: the repo-root `PAPER-REFERENCES.md` is a 51,904 B
  snapshot from 2026-08-28 while multivac's doc of record is 76,779 B. Unlike `docs/`, this file is
  NOT carried by `sync-multivac.sh push` (push sends `docs/` and `experiments/` only), so
  PAPER-REFERENCES.md is multivac-owned and must be appended THERE; the repo copies are read-only
  mirrors. Root copy refreshed from the mirror and the ownership rule recorded here so the next
  agent does not append to a copy that never syncs.
Result: The accuracy question the owner raised is answered and costed at ~3.5 h against 35-47 h,
  with academic and industry precedent cited rather than asserted. Q6_K_XL is preserved. Wave 1 is
  untouched by any of it and still running. What the cut costs is recorded, not hidden: no
  comparability against Qwen's official LiveCodeBench 90.3, no SWE-bench or agentic evidence, and
  divergence measured against Q6_K_XL rather than FP16 (no FP16 on the host; a 27B F16 GGUF at
  ~54 GB exceeds free space on `/srv/models`).
Verified: `nvidia-smi` and `sensors` read live at 04:11:04Z; power log 43,182 consecutive 1 Hz
  samples over exactly 12.00 h differenced on its cumulative-Wh columns; `/app/llama-perplexity`
  listed inside the engine image; `wikitext2-test.txt` (1,256,449 B) and `corpus.txt` (9,097,163 B)
  present; `/` free 82,936,868,864 B against a ~11 GB per-domain logits file; sweep alive at
  04:13:38Z with Q6_K 3 cells / 1 ok, Q4_K_XL queued.
Next: let Wave 1 finish (Q6_K incl. the automatic D3/A8 A/B, then Q4_K_XL), then finish_wave1.sh
  closes it (summarize + verify-sweep --stage 1a). Then build and run SSA S0-S6 against a free GPU.
  T6 close-out and the PAPER-REFERENCES graduation follow.


### L-7 | 2026-08-30T04:35:00Z | S2-execute | claude-opus-5 | conductor-manager | Private git sync + unattended autonomy <!-- bsc-ledger:qbench-t1-AUTONOMY -->
Did: Owner is away for some hours and asked that the work continue without an agent present.
  (a) PRIVATE GIT SYNC between the laptop and multivac. Bare hub at
  `multivac:~/repos/multivac-paper.git` (mode 700), working clone at `~/repos/multivac-paper`,
  laptop remote `multivac`. **No origin, no GitHub, never public** — `git remote -v` shows the one
  ssh remote and nothing else. Round-trip verified in both directions (laptop -> hub -> multivac,
  and multivac -> hub -> laptop).
  Exclusion-first `.gitignore`: GGUFs, `*.kld` logits (~11 GB each), container/image material,
  bulk corpora, generated pads, serverlogs, venvs. Provenance for every excluded item lives in
  `env-manifest.json`, which IS tracked — sha256 + bytes + RepoDigest, so anything omitted is
  re-obtainable. Result: 87 files, largest 152 KB, 13 MB working tree.
  (b) AGENT ORIENTATION: `AGENTS.md` (points at CLAUDE.md, plus the five things that have actually
  gone wrong here) and a repo-root `CLAUDE.md` covering what the project is, the document-ownership
  table, the sync topology, the eight hard rules, the configuration facts that are counter-intuitive
  on this stack, current state, and a TODO through total completion. It is a project guide and does
  NOT duplicate multivac's `~/CLAUDE.md`, which remains the machine doc of record.
  (c) UNATTENDED EXECUTION: `supervisor.sh` replaces the fail-fast chain. Contract: **a failing step
  is logged, marked `.failed` and SKIPPED — the chain continues** so the plan gets as far as it can
  without a human. Every step writes its own log under `logs/` and an outcome row in
  `state/progress.json`; results are committed and pushed to the hub after every step, so nothing
  depends on the process surviving. Steps are idempotent (`.done` markers), so a restart resumes.
  The one deliberate exception to continue-on-failure is the SSA S0 smoke gate: if the 4-chunk
  smoke fails, S1-S4 are skipped (small-tests-first is a hard rule) but the supervisor still runs
  its reporting and sync steps rather than dying.
  (d) `keepalive.sh` restarts the supervisor if it dies before `finished_utc` appears. There is no
  cron on this host and systemd user lingering is OFF — enabling it is a system setting and was NOT
  changed while the owner is away, so a plain detached flock-guarded sleep loop is used instead.
  A `supervisor-watchdog.sh` is deployed for the cron case should cron ever be installed.
Result: The remainder of Wave 1 and all of SSA S0-S4 now run without a human and without this
  agent. The supervisor cleanly superseded the earlier `finish_wave1.sh` / `ssa_runner.sh` chain
  (which was fail-fast) and is waiting on the live sweep. Verified working, not assumed:
  git push/pull in both directions, `progress.json` being written, the multivac-side commit+push
  path, and the supervisor's takeover of the old chain.
Verified: `git remote -v` = one ssh remote, no origin; hub at 19 commits; laptop pulled multivac's
  commit; `ls -ld ~/repos/multivac-paper.git` = drwx------; supervisor pid 1846476 and keepalive
  pid 1846870 both alive at 04:31:41Z with the sweep (pid 1498430, Q6_K) untouched;
  `progress.json` initialised.
Next: unattended — sweep finishes -> summarize -> verify-sweep --stage 1a -> SSA S0 gate ->
  S1-S4 -> final report, with per-step logs and git pushes throughout. On return read
  `state/progress.json` first: it names every step, its rc, and its log. Still needing a human:
  S5/S6 harnesses (not written), the S7 owner call, T6 close-out, and Waves 2 and 4.


### L-8 | 2026-08-30T12:00:00Z | S2-execute | claude-opus-5 | conductor-manager | Wave 1 COMPLETE + SSA accuracy ranking obtained <!-- bsc-ledger:qbench-t1-SSA-RESULTS -->
Did: Reviewed the unattended run (04:31Z-10:27Z, no human, no agent). The supervisor completed
  6 of 7 steps green, skipped the one failure exactly as designed, and pushed to the git hub after
  every step (35 commits). keepalive exited having made 0 restarts — the supervisor never died.
  (a) WAVE 1 COMPLETE, all four arms. Every quant reaches the full native 262,144 window once
  rebalanced except Q6_K_XL at 212,992; all four gained over their default-split ceilings
  (+65,536 x3, +81,920 for Q6_K_XL). Fastest at 262,144 is Q4_K_XL @ `-ts 56,44`, 13.33 tok/s.
  A8/D3 CLOSED: `-ctxcp 32` gains 6.8 % decode and 7.6 % prefill at identical VRAM -> adopt (PN-18).
  (b) SSA S0-S4 COMPLETE — the accuracy ranking this project has never had. Non-overlapping CIs,
  monotone in both domains, 3.7-11.8 sigma between adjacent arms (PN-13). Headline: **code
  degrades ~2x more than prose and the gap widens with more aggressive quantization** (1.75x /
  2.30x / 2.62x) — prose-corpus quant tables understate the cost for coding work (PN-14).
  E2 CLOSED: q4_0 KV costs 0.002955 KLD, 51 % of a whole quant level, top-1 99.401 % — defensible
  but not free, and PPL moved only +0.15 % on the identical pair, a clean demonstration of the
  averaging bias that disqualifies PPL as the ranker (PN-15).
  (c) HARNESS DEFECT found, diagnosed and fixed WITHOUT re-running anything. All ten KLD cells
  exited 0, were marked ok, and parsed EMPTY: the patterns expected ASCII "+/-" and llama.cpp
  emits Unicode "±"/"Δ". Recovered every cell from the serverlogs via `ssa_reparse.py` — which
  was possible only because hard rule 2 had persisted full stdout before each teardown. Fixed at
  source in `ssa_kld.py`: patterns accept either form, and a kld cell without `mean_kld` is no
  longer reported ok. Written up as method, PN-17.
Result: Track A now has all three axes for the first time — accuracy (SSA), context and speed
  (Wave 1). The ~3.5 h estimate for SSA was accurate: S0-S4 ran 08:22-10:27Z. DEC-11's bet paid
  off — divergence separated the arms decisively in the time a single HumanEval+ arm would have
  taken, and would still have been unable to rank them.
  TWO ITEMS NEED A HUMAN, neither urgent, both deliberately left alone: (1) `verify_1a` failed on
  "7 empty e12 serverlogs" — all seven are timestamped 02:55:04-02:55:52Z, exactly the D6
  double-runner race window, and four are named `e12-stale-recover-*`. This is residue of a defect
  already found, fixed and documented, NOT a new fault; it wants an acknowledge-and-clean plus a
  verify-sweep amendment that distinguishes race residue from live evidence loss, not a re-run.
  (2) `/srv/bench/e12/ssa` holds 50 GB of `*.kld` logits (3 x 16.26 GB + 2 x 2.03 GB smoke) with
  `/` at 87 % (28 GB free). Results are fully extracted, so they are safe to delete and doing so
  returns `/` to ~78 GB — but they are root-owned and deletion is irreversible, so it stays an
  owner call.
Verified: progress.json summary ok=6 failed=[verify_1a] skipped=[]; finished_utc 10:27:39Z;
  keepalive log "0 restart(s)"; all 10 SSA cells recovered by ssa_reparse.py; patched ssa_kld.py
  compiles and both fixes present at lines 98 and 110; git hub at 35 commits with per-step
  autonomous pushes; the 7 empty serverlogs enumerated with timestamps confirming the race window.
Next: T6 close-out for Wave 1 + SSA. Then the two human items above, the S5/S6 harnesses, and the
  S7 owner call (`--hellaswag`/`--winogrande`, free in the same binary). Waves 2 and 4 remain.
