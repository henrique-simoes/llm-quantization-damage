# Build Stream — Multivac Quant Bench Track A: Q4_K_XL / Q5_K_XL / Q6_K coding-agent configuration

<!-- STATUS BLOCK -->
```yaml
item: quant-bench-trackA
branch: main
cf: { spec: CF-SPEC-1, tasks: [CF-1..] }
phase: "Phase 0 — settings research consolidation"
stage: S1-plan
status: blocked
blocked_on: "owner: conductor shape + routing roles + delete-list + benchmark sweet-spot approval (DEC-1)"
last: { agent: main-agent, at: 2026-08-30, ledger: L-1 }
next_action: "Owner picks conductor shape/roles, approves delete list + benchmark sweet spot; then run conductor preflight, make_pipeline --with-planning, make_cast, spawn."
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
| 0 | Settings research consolidated into pinned config candidates + owner gates | owner approves DEC-1 set (this file) | in-progress |
| 1 | Disk sweep under preservation rule; delete list executed; manifests written | `bash /srv/bench/sweep/verify-sweep.sh` green + free ≥ 60 GB on /srv/models | planned |
| 2 | Harness-validation suite (validate-v2): launch contract, sampling contract, thinking control, provenance capture | `validate-v2.py` catches the 4 seeded fault configs (negative control) | planned |
| 3 | Bring-up + `-ts` rebalance sweep per quant; bracket context ceilings | `tsweep-v2` full-ratio artifacts + bracketed ceilings re-tested | planned |
| 4 | Sampling-protocol A/B (greedy vs Qwen-official vs coding-agent candidate) | A/B artifact on HumanEval-40 + repetition-stress set; config locked | planned |
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

## Decision log

DEC-1 | 2026-08-30 | S0 | owner
Context: Owner narrowed scope to 3 quants (Q4_K_XL, Q5_K_XL, Q6_K), coding-agent-config-first
testing, MTP/DFlash sweeps with settings variation, disk sweep allowed under preservation
rule, benchmark sweet spot to be proposed and approved before deployment.
Decision: PENDING — owner must approve (a) conductor shape + roles, (b) delete list
(incl. NVFP4/vLLM images and the Q6_K vs Q6_K_XL reading), (c) benchmark sweet spot + order.
Why: these three gates are exactly the owner's stated checkpoints before anything runs.

## Ledger

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
