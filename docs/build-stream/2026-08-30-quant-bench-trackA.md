# Build Stream — Multivac Quant Bench Track A: Q4_K_XL / Q5_K_XL / Q6_K coding-agent configuration

<!-- STATUS BLOCK -->
```yaml
item: quant-bench-trackA
branch: main
cf: { spec: CF-SPEC-1, tasks: [CF-1..] }
phase: "Closing experiment campaign in flight (S9 + S9d). Wave 1, SSA S0-S5+S7, and S8 closed. Track A decided and amended."
stage: S3-report
status: campaign-running
blocked_on: null
last: { agent: claude-opus-5, at: 2026-08-31T21:45:00Z, ledger: L-13 }
next_action: "TWO DETACHED CHAINS ARE RUNNING — do not start a third GPU runner and do not edit either script while it runs. (1) s9_chain.sh pid 1822394, launched 21:23Z: pilot 3/3 DONE, then determinism -> s6 -> dflash -> score, ~3.5 h. (2) s9d_chain.sh pid 1887775, queued 21:42Z on a BLOCKING flock against s9.lock: the 24-cell MTP draft-depth sweep at matched depth, ~4 h, starts automatically when S9 releases the lock. Both commit and push to the hub after every phase. Check: cat /srv/bench/e12/logs/s9_chain.log and s9d_chain.log; markers in /srv/bench/e12/state/. WHEN BOTH COMPLETE: write the ledger entry (L-14) and the paper notes (PN-26 onward) for each phase, then the project moves to drafting the arXiv report against manuscript/OUTLINE.md. The owner has said the drafting pass will be MULTI-AGENT (writers, reviewers, re-writers) and will request it explicitly — do not launch agents or a workflow unprompted."
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
| 1 | Disk sweep under preservation rule; delete list executed; manifests written | `bash /srv/bench/sweep/verify-sweep.sh` green + free ≥ 60 GB on /srv/models | **closed** (L-9) — delete-1a executed (4 of 5 items, 65.4 GB); delete-1b **cancelled** by DEC-9 (Q6_K_XL kept as the 4th arm and the divergence reference); the `/srv/models` byte gate was **waived** by the owner, the `/` limb passes; `verify-sweep.sh --stage 1a` rc=0 after 7 race-residue empty logs were quarantined with a register |
| 2 | Harness-validation suite (validate-v2): launch contract, sampling contract, thinking control, provenance capture | `validate-v2.py` catches the 4 seeded fault configs (negative control) | **done** — gate green 2026-08-29T23:01Z (C1–C4 pass; F1→C1, F2→C3, F3→C2, F4→C4); a fifth contract (≥0.90 depth gate) added 2026-08-30 after PN-5 |
| 3 | Bring-up + `-ts` rebalance sweep per quant; bracket context ceilings | `tsweep-v2` full-ratio artifacts + bracketed ceilings re-tested | **done** (L-8/L-9) — all four arms: Q4_K_XL 262,144 @ `-ts 56,44` · Q5_K_XL 262,144 @ `54,46` · Q6_K 262,144 @ `58,42` · Q6_K_XL 212,992 @ `56,44` (G21 closed). `-ctxcp 32` adopted (A8). Headline: the ceiling is a property of the SPLIT, not the quant (PN-6) |
| 4 | Official-settings validation pilots (G17 equivalence, G8 losslessness at temp>0, pp-behavior probe) | pilot artifacts; spec-decode accuracy-arm rule locked | **partial** (L-13) — **G8 answered at greedy and NEGATIVELY**: MTP is not output-identical to no-spec, 131/164 exact match (PN-23). G17 answered negatively at the template level only (PN-3); `reasoning_effort` equivalence and the temp>0 arm remain unrun and are now optional |
| 5 | MTP/DFlash setting sweep (depth, p-min, draft-KV dtype, DFlash n-max) | sweep JSONs at 32 K and full-depth; best-per-context recorded | **partial** (L-13) — draft depth swept {none, n=2, n=4} at 32 K **and** at the full 262,144 window: n=4 wins at both and the margin grows with depth (PN-24). DFlash2 **void** — wrong engine image, 5 cells excluded (PN-25). p-min and draft-KV dtype unrun, both optional |
| 6 | Accuracy instruments: PPL(P1) for UD-Q6_K, code-NLL ladder, HumanEval+ gap-fills, LCB v6 n=100 setup+run | artifacts under /srv/bench/, CIs attached | **superseded by DEC-11** — replaced by the Small-Sample Accuracy protocol (SSA). Delivered: KLD on prose (S2), code (S3), task prompts (S5), q4_0-KV cost (S4 = E2 closed), HellaSwag control (S7), HumanEval+ generative at n=164 (S8). LiveCodeBench v6 never set up (G19, out of scope) |
| 7 | Agentic: SWE-bench Verified 25-smoke → 50 stratified; agentic steps; thinking arm | smoke green before 50-run; per-instance manifest + Wilson CIs | **not run in this wave** — the historical SWE-bench corpus (verified50, 75.5 %) stands as prior work in PAPER-REFERENCES.md. G22 makes it structurally unable to rank these arms (±12 pts at n=50); S7 demonstrated the same limitation empirically |
| 8 | Context axis: Code-NIAH 6 depths × 2 needle classes × 3 seeds; E2 KV fidelity (f16 vs q4_0) | code-niah.json + kv-fidelity.json; decision rule applied | **partial** — **E2 CLOSED** by SSA S4: q4_0 KV costs 0.002955 ± 0.000127 KLD vs f16, 51 % of a quant level (PN-15). Code-NIAH **not run**; long-context task accuracy (G1) remains the largest open hole and is stated as a limitation in the report |
| 9 | Speed + energy at chosen config (speed curve, J/tok, filled depths) | chosen-config-speed.json | **partial** — host power envelope characterised (PN-11) and the thermal asymmetry of `-ts` recorded (PN-12); the per-config J/tok curve at the chosen configuration was never run. Optional: the decision does not depend on it (PN-19 shows speed does not discriminate the arms) |
| 10 | Track A decision procedure + Track B data assembly; CLAUDE.md/PAPER-REFERENCES updates | config lines published with evidence trail | **in progress** — Track A **DECIDED** (docs/paper/TRACK-A-DECISION.md, L-10, amended by S8). Track B assembly is the remaining project scope: the arXiv technical report, drawn from PN-1..PN-25 |

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

## S9 — the closing experiment set (DEC-12 retained), designed 2026-08-31

Three experiments, ~4 h GPU. Wave 2 breadth and the Wave 4 energy curve are cancelled (DEC-12);
what remains is the set that either closes a stated open question or repairs a void result.
Harness: `/srv/bench/e12/experiments/s9_final.py` + `s9_score.py`, driven by `s9_chain.sh`.
All runs: `llamacpp-mtp:latest` unless stated, `-sm layer`, q4_0 KV, `-ctxcp 32`, seed 20260830,
each arm at its own Wave-1 winning `-ts` ratio.

### Hard gate — pilot (3 checks × 5 problems, ~10 min)
Three launches that exercise every distinct configuration the batteries need: the MTP image, the
DFlash2 image with its `--entrypoint /app/llama-server`, and official-sampling generation on
Q4_K_XL. **If the pilot fails the chain STOPS** rather than skipping — this is the one place where
continuing is wrong, because every downstream phase would be measuring the same broken thing. It
exists because S8 spent four hours discovering a drafter that could not load (PN-25); this catches
that class in ten minutes.

### S9a — determinism control (closes PN-23's open mechanism)
Re-run S8's `nospec` and `mtp2` configurations **byte-identically** — same model, ctx, `-ts`,
`-ctxcp`, KV dtype, seed, sampling, prompt order, image — and compare each against its own S8
output. Nothing varies, so any difference is engine nondeterminism.

| outcome | reading |
|---|---|
| `nospec==nospec` **and** `mtp2==mtp2` | engine is deterministic → PN-23's divergence is **caused by speculation**, and the partial n=2/n=4 set overlap (Jaccard 0.610) makes it draft-depth-dependent, not random |
| `nospec==nospec` **but** `mtp2!=mtp2` | speculation itself is nondeterministic run-to-run → rules out a fixed verification-rule error, supports the batch-shape / float-associativity account |
| `nospec!=nospec` | the engine is not deterministic → **PN-23 must be restated relative to that floor**; only the EXCESS over self-divergence is attributable to speculation |

Any of the three is a publishable answer. The current state — "mechanism not established" — is the
only outcome that is not.

### S9b — SSA S6, the generative anchor
UD-Q4_K_XL vs UD-Q6_K_XL (the ladder's extremes) on all 164 HumanEval+ problems, **paired per
problem**, DEC-2 official non-thinking sampling, seed-matched, scored with Wilson intervals and an
exact McNemar test. Two arms rather than four for the reason R6 gives: at n=164 the
independent-comparison interval is ±4.6 points while these arms differ by 1–3, so independent means
cannot separate them and only the paired test is powered.
**Run NO-SPEC on both arms** — a direct consequence of PN-23. With MTP on, ~20 % of completions
would change for reasons unrelated to the quantization, confounding the only comparison this
experiment exists to make. This is S8's finding immediately changing an experimental design.
A null result is the expected outcome and is reportable: it is the task-level counterpart of S7,
and together they are the empirical case for ranking on divergence.

### S9c — DFlash2 on its correct image (repairs PN-25)
`llama-dflash2:latest` with `--entrypoint /app/llama-server`. Equivalence + speed + acceptance at
ctx 32,768 against the S8 no-spec baseline, then a descending at-depth ladder
(262,144 → 212,992 → 163,840 → 131,072 → 65,536) to find whether the 1.1 GB draft GGUF fits
anywhere near the Track A deployment context — the "1.19 GiB draft-worker wall".
⚠️ **Stated confound**: the baseline was produced on `llamacpp-mtp:latest` and this arm runs on a
different fork, so an engine-version difference is confounded with the speculation effect. The
equivalence number must carry that caveat; it is not comparable to S8's MTP equivalence figures.

### Also repaired here — S8's score parser
S8's scorer used `re.findall(r"(base|base \+ extra|humaneval\+?)[^\d]*([\d.]+)", …)`, which
matches `humaneval … pass@1` and captures **the 1 from `pass@1`**, not the score. Every arm in
`s8-scores.json` reads `parsed=[["humaneval","1"],["humaneval+","1"]]`. The real numbers were never
lost — they are in the preserved `raw_tail` and `*-eval.txt` — but anything reading the
machine-readable field would conclude every arm scored 1.0. Same defect class as PN-17. Re-parsed
into `s8-scores-reparsed.json` with Wilson intervals; the original is left unedited on disk.

### S9d — MTP draft-depth sweep at MATCHED depth (reinstated, DEC-13)

The one item pulled back from DEC-12's cancelled set, because it is the only one that **repairs a
claim the report makes** rather than adding one the report lacks.

**What it fixes.** PN-9 reports that MTP acceptance differs sharply by quantization (0.897 / 0.564 /
0.516) and then retracts most of its own force in the caveat: the three cells sat at different
context depths *and* different `-ts` ratios, so quant, depth and ratio are confounded, and the note
says outright it is "a signal … NOT a measured quant ranking." PN-24 has the parallel problem in
the other direction — n=4 > n=2 with the margin growing with depth, measured on UD-Q6_K alone, with
an explicit warning not to carry the ordering across the ladder without measuring.

**Design.** 4 arms × 2 matched depths × 3 draft depths = **24 cells**.

| axis | values | why |
|---|---|---|
| arm | Q4_K_XL · Q5_K_XL · Q6_K · Q6_K_XL | the full active ladder, each at its **own** Wave-1 winning `-ts` |
| depth | **131,072 · 196,608** | the only two rungs with *verified* pads (0.9435 / 0.9474) that **all four** arms reach — Q6_K_XL's ceiling is 212,992 |
| n_draft | **2 · 4 · 8** | turns the question from "which of two" into "where is the optimum"; n=8 may not fit at depth on the larger arms, which is itself an answer |

Per cell: one deep prefill, then **three 512-token generations**. Three because this host's
within-arm decode noise reaches 32.9 % (PN-19) and one reading cannot support a speed claim; reps 2
and 3 are nearly free because the server's prefix cache means the pad is not re-processed — and
`prompt_n`/`cache_n` are recorded per rep so that is checkable rather than asserted. 512 tokens
rather than S8's 192 because acceptance is a ratio over draft events and S8's at-depth acceptance
read exactly 1.000 for both arms, which is not a stable estimate at that sample size.

**The PN-5 gate is asserted in code, not documented in a docstring**: a cell is `valid` only if
`prefill_frac >= 0.90`, and invalid cells are excluded from every aggregate. That is the whole
lesson of PN-5 — a contract that is not checked is not a contract.

**Stated confound, not hidden.** `-ts` necessarily varies *between* arms, because the optimum is
not portable (PN-7). It is held fixed *within* an arm across all six of its cells, so the
draft-depth and context-depth comparisons are clean; only the between-arm comparison carries the
ratio with it, and the artifact records that in a `confound_statement` field.

**Sequencing.** `s9d_chain.sh` takes a **blocking** `flock` on the same lock `s9_chain.sh` holds,
so it waits for that chain to finish and then holds it. The running chain is never edited — bash
reads a script lazily by byte offset, so appending a phase to a running script can make it resume
mid-token. Queued 2026-08-31T21:42Z, ~3.5–4 h once it starts.

### S9e — draft depth at the Track A window (262,144), added 2026-08-31

S9d matches depth across all four arms, which forced it to 131,072 and 196,608 (Q6_K_XL's ceiling
is 212,992). That leaves the Track A configuration itself unmeasured: its published throughput
rests on **one** 192-token reading at n=4, taken on a `-ts` ratio selected under **n=2**
(`tsweep-v2-Q6_K.json` records `spec: mtp2`), with **n=8 never tested anywhere in E12**.

Three cells close it: Q6_K × 262,144 × n ∈ {2,4,8}, three 512-token generations each on the
verified 248,522-token pad. Every outcome is useful — n=4 wins and the number gains a median-of-3;
n=8 wins and the config line changes again *and* the ratio needs re-sweeping at the new draft
depth; n=8 fails to load and the draft context does not fit at the full window, which is the same
1.19 GiB draft-worker wall DFlash2 is being tested against.

### S10 — does quantization damage grow with CONTEXT DEPTH? (added 2026-08-31)

**The hole.** Every accuracy number in this study was measured at **n_ctx 2048** — the KLD ladder
(PN-13), the domain hierarchy (PN-14, PN-21), the q4_0-KV verdict (PN-15). The deployment
configuration runs at **262,144**. That is a 128× extrapolation, and PN-15 states the limitation
itself: *"measured … at n_ctx 2048 — NOT at the 212K–262K depths where the KV cache actually
dominates memory and where the effect could differ materially."*

**Why it is affordable.** KLD cost scales with the **token budget**, not with context length.
65,536 tokens at `-c 2048` is 32 chunks; the same 65,536 tokens at `-c 65536` is one. Identical
per-token observation count, identical ~11 GB logits file — each token merely conditioned on 32×
more context. Only the attention work grows.

| rung | n_ctx | chunks | tokens | |
|---|---|---|---|---|
| (S3) | 2,048 | 32 | 65,536 | already measured — the anchor |
| A | 16,384 | 4 | 65,536 | 8× deeper |
| B | 65,536 | 1 | 65,536 | 32× deeper |

Code domain only (the target workload; wikitext skipped to halve cost — a scope choice, stated).
q4_0 KV on **both** base and arms exactly as in S2/S3, so the KV error is present on both sides and
largely cancels and the residual divergence is quant-attributable. Plus **the KV axis at rung B**:
f16 base vs q4_0 scoring on the reference arm — S4's design moved to depth, where the cache holds
32× more quantized keys. That closes the open half of PN-15.

**Split.** S2/S3 used the engine default because VRAM pressure at n_ctx 2048 was negligible. At
65,536 it is not — the default split is what OOMed Q5_K_XL at 262,144 in Wave 1. A **single fixed
`-ts 56,44`** is used at the deep rungs, identical for every arm, so it stays controlled without
relying on the default placement being survivable.

**Reading it.** Flat across rungs → quantization damage is depth-independent and published
2K-context tables transfer. Rising → those tables (Unsloth's, Fireworks', LocalBench's, all near
2K) understate the cost for long-context work, which is structurally the same finding this study
already makes about prose-vs-code, in a second dimension.

⚠️ **Caveat that must travel with rung B.** Budget-matching drives chunks down as n_ctx rises: 32
at 2,048, **one** at 65,536. The deep rung's 65,536 observations therefore come from a single
contiguous passage rather than 32 scattered ones — more correlated, less corpus-representative,
same token count. The tool's Gaussian interval does not know this. Any rung-to-rung difference
smaller than S3's arm-to-arm separation is suggestive, not established.

**Pilot is a hard gate and also real work**: it records rung B's reference logits and scores one
arm, so it costs nothing extra on success and rung B reuses its base file. It answers in ~30 min
whether `--kl-divergence` runs at all at `-c 65536` on this stack and whether the reference fits.

### S11 — Greedy Divergence at Depth (replaces S10's instrument, 2026-09-01)

**Question unchanged; instrument replaced.** Does quantization damage grow with context depth?
S10 was to answer it with KL divergence and cannot: the tool holds a chunk's logits resident and
this host tops out at n_ctx 8,192 (PN-31). S11 measures the same question with an instrument whose
memory cost is that of an ordinary serving run.

**Why it reaches depth.** No logits buffering — each cell is one `/completion` returning text. The
ceiling becomes VRAM, which is already mapped, instead of host RAM, which was not.

**Why the comparison is clean — it rests on PN-26.** No-spec greedy generation on this engine is
byte-reproducible (md5-identical across runs a day apart). So with speculation off and temperature
0, any text difference between two arms on the same prompt at the same depth is attributable to the
quantization. ⚠️ Speculation must stay OFF: PN-23/PN-26 show MTP alters ~20 % of completions for
reasons unrelated to the quant, which would swamp the effect.

**Metric — first-divergence position, not exact-match.** Greedy decoding is a trajectory: after the
first differing token the sequences are on different paths and per-position comparison stops
meaning anything, so exact-match would be a coarse binary. The graded metric is *where* they
separate — the index of the first differing character against the reference arm on the identical
prompt. **A falling index as depth rises means damage grows with context.**

| axis | value |
|---|---|
| depths | 8,192 · 65,536 · 196,608 — cheapest first, each slice usable alone |
| arms | Q6_K_XL (reference) · Q6_K · Q5_K_XL · Q4_K_XL |
| split | one fixed `-ts 56,44` for every arm — a per-arm ratio would be an uncontrolled variable in an accuracy comparison |
| sampling | greedy, no-spec, `/completion` + the proven continuation cue |
| n | 3 distinct corpus excerpts per (arm, depth) |
| gates | `prefill_frac ≥ 0.90` **and** `generated_tokens ≥ 128`, both asserted in code |

**Controls, because this harness family has failed three times.**
1. **Self-consistency**: the reference arm generates the same pad twice at the deepest rung with
   `cache_prompt: false`, re-prefilling both times. Not identical → the experiment is void and
   stops, rather than reporting noise.
2. **Pilot runs the HARDEST cell first** — the reference arm at 196,608, where the VRAM arithmetic
   says RISK (16,426 MiB/GPU predicted vs a 15,650 practical ceiling) while E11a measured that arm
   at 245,760 no-spec. The estimate and the history disagree, so it is measured before any battery.
3. Both gates above, which are the two that were missing in PN-5 and PN-30.

**Resource math, done before the harness was written** (the discipline whose absence caused PN-30
and PN-31): RAM not a constraint (no logits buffer); VRAM comfortable for three arms and flagged
RISK for the fourth at the deepest rung; ~3.1 h total.

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

DEC-12 | 2026-08-31 | S3-report | owner | scope cut on the remaining experiments
Context: After S8 closed, five optional experiment groups remained. The owner reviewed them
against the objective (the arXiv report) and cut the two that add breadth without correcting
anything.
Decision: **CANCELLED — will not be run.**
  (a) **Wave 2 breadth**, in full:
      - **G17 `reasoning_effort` equivalence** — half-answered already by PN-3 (the documented
        `{"reasoning_effort":"none"}` raises a Jinja exception on this template while
        `{"enable_thinking":false}` works). Cancelled rather than completed.
      - **G8 losslessness at temp > 0** — a weak instrument by construction: speculation consumes
        the sampler's RNG differently, so outputs diverge whether or not the verification rule is
        exact, and only a distributional comparison would mean anything.
      - **Presence-penalty probe** — whether the official preset's `presence_penalty 1.5` harms
        code generation. Genuinely open and genuinely interesting; cut on cost.
      - **MTP depth sweep on the other arms** — would disentangle the quant/depth/ratio confound
        that PN-9 explicitly flags. Cut on cost; PN-9's caveat stands unresolved and must be
        stated as such in the report.
      - **draft-KV dtype** (`-ctkd`/`-ctvd`, confirmed present in the image) — never tested.
  (b) **Wave 4 speed + energy curve** at the chosen configuration (J/tok at filled depths).
      PN-11 remains the host baseline; there will be no per-config energy figure. The historical
      J/tok table is depth-0 and from the deleted image, so it cannot substitute — the report
      states that energy at the deployment configuration is unmeasured.
Still to run (owner-confirmed): the no-spec-vs-no-spec **determinism control** (attributes PN-23),
  **SSA S6** (the generative anchor), and **DFlash2 on its correct image** (the arm S8 voided).
Why: neither cancelled group corrects an existing claim, and neither can change the Track A
decision — PN-19 already establishes that decode speed does not discriminate these arms, so an
energy curve would rank configurations on an axis the decision does not use. The three retained
experiments each either close a stated open question or repair a void result. Cost was the binding
constraint: GPU hours are the scarce resource and the objective is now the report.
Consequence for the paper: three limitations become permanent rather than pending, and must be
written as such — PN-9's confound, the absence of a temp>0 equivalence check, and the absence of a
per-config energy measurement.

DEC-13 | 2026-08-31 | S3-report | owner | reinstates one item from DEC-12
Context: Asked which cancelled item would most help the technical report, the assessment was that
almost every cancelled item ADDS a result the paper lacks, while exactly one REPAIRS a claim the
paper already makes — the MTP depth sweep, which is what PN-9's caveat explicitly asks for
("a signal that the Phase-5 sweep must resolve at matched depth, NOT a measured quant ranking")
and what PN-24's warning depends on ("do not carry this ordering … without measuring").
Owner: "Yes I want it."
Decision: **REINSTATED** as S9d, queued behind the S9 chain. 24 cells, ~3.5-4 h. Design above.
The rest of DEC-12 stands cancelled: G17, G8-at-temp>0, the presence-penalty probe, draft-KV dtype,
and the Wave 4 energy curve.
Why the others stay cancelled, recorded so they are not re-litigated:
  - **presence-penalty probe** was the runner-up and on thematic grounds the most attractive — the
    official preset's `presence_penalty 1.5` penalises every token already emitted, and code
    repeats `self`, `return` and indentation constantly, so a measurable harm would be the paper's
    own thesis appearing in a second dimension (a published default tuned on a general distribution
    misfiring on code). Cut because it is a hypothesis that may return null and it strengthens a
    section that is already adequately supported.
  - **G8 at temp>0** sounds important because PN-23 is a headline, but doing it properly needs many
    samples per problem to compare distributions — precisely the underpowered design the report
    spends a section warning against. "Greedy-only, and a powered temp>0 test was not affordable"
    is a better limitation than a weak result.
  - **energy curve** ranks last despite leaving a section thin: PN-19 already shows the arms are
    indistinguishable on decode throughput at the same power cap, so J/tok across quants would most
    likely be another null. The interesting energy question is across *speculation* settings, not
    quants — a different experiment from the one cancelled.

DEC-14 | 2026-08-31 | S3-report | owner | two additions, and the campaign is sequenced
Context: (a) Pressed on whether the 16.81 tok/s headline was really the best config at full
context, the provenance check found it rests on n=1 at a ratio tuned for a different draft depth,
with n=8 untested. (b) Owner: "accuracy here is my biggest doubt under heavy context, but all
types of context really, compared to the other quants and configurations" — which is G1/PN-15, the
study's largest hole.
Decision: add **S9e** (3 cells, Q6_K × 262,144 × n{2,4,8}) and **S10** (divergence vs context
depth, ~3.5 h). Designs above. Owner approved the full ~11 h campaign.
Sequencing: four detached chains, each taking a BLOCKING flock on the previous one's lock —
S9 → S9d → S9e → S10. No polling for "is the GPU free"; the wait is on the lock, which is the
condition itself. No running script is ever edited: bash reads scripts lazily by byte offset.
Supervision: `campaign_watchdog.sh` emits one line per NEW problem (error signature, stall, dead
chain, disk, orphan container) and is watched so failures surface immediately; plus a 20-minute
independent check for the classes a watchdog cannot see — cells that return ok with empty metrics
(the PN-17 class), prefill_frac below the 0.90 gate, acceptance reading exactly 1.000, and whether
the autonomous git pushes are landing.
Why: S9e repairs the deliverable's own headline number, which currently could not be printed
without a footnote. S10 converts the accuracy program's biggest stated limitation into a measured
result, and it is cheap for the reason above — the instrument's cost is set by tokens, not context.

DEC-15 | 2026-09-01 | S3-report | owner | S10 replaced by S11; instrument findings are a footnote
Context: S10's pilot failed with `std::bad_alloc`. Empirical measurement then established a hard
ceiling of n_ctx 8,192 for KL divergence on this host (PN-31). Owner: "S10 is actually important...
If it's not possible to perform the test reliably, say so" — and, on the OOM findings, that they
are footnote material rather than a paper feature, because the report is about serving models,
quantization and configuration, with the host specification and honest limitations stated in Setup.
Decision: (a) KL divergence at depth is **declared not reliably measurable on this host** and the
4× ladder is NOT run — it cannot support a claim about a 128× deployment context. (b) The question
is retained and answered by **S11**, design above. (c) PN-31 is marked FOOTNOTE MATERIAL; the only
clause with bearing on the paper's argument is that the standard divergence tooling's footprint
scales with context length, which is itself why published quantization tables are all measured
near 2K.
Why: the owner has raised repeatedly that hours are being lost to runs launched without resource
arithmetic or a pilot. S11 was therefore specified with the memory/VRAM math stated before the
harness existed, the hardest cell piloted first, and both output gates asserted in code.

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


### L-9 | 2026-08-30T12:30:00Z | S2-execute | claude-opus-5 | conductor-manager | T6 CLOSE-OUT — Wave 1 + SSA closed, all acceptance criteria met <!-- bsc-ledger:qbench-t1-T6 -->
Did: (a) EVIDENCE SECURED BEFORE ANY DELETION, in that order. Pulled all 9 SSA serverlogs to
  `data/raw/e12/serverlogs/` — the raw source every published number was recovered from (PN-17) —
  and verified locally that all 7 kld cells carry `mean_kld` and all 3 base cells carry `ppl`
  before touching anything.
  (b) 50 GB RECLAIMED. Deleted the five `*.kld` reference-logit files after four checks: no GPU or
  eval process running, 7/7 kld cells' metrics extracted, 9 serverlogs intact on the host, and no
  remaining consumer — every arm is measured, and S5 needs a base over the HumanEval+ prompt
  corpus, which these files are not. `/` went 87 % -> 63 % used, 28 GB -> 77 GB free.
  (c) A2 / verify_1a RESOLVED HONESTLY, not silenced. All 7 empty serverlogs fall inside
  02:55:04-02:55:52Z — the D6 double-runner race window — and 4 are the recovery path's own
  `e12-stale-recover-*` artifacts. These are the D4 "stillborn container" class: killed between
  `docker run -d` and start, so they never produced output and no evidence was lost, which is
  categorically different from a started container whose log went missing. They were MOVED to
  `quarantine/empty-serverlogs/` with a `REGISTER.json` recording each file, its timestamp, its
  class, cause, and an explicit `evidence_lost: false`. **A2's check itself was left exactly as
  strict as it was** — it will still fail on a genuinely empty log from a container that ran.
  `verify-sweep.sh --stage 1a` re-run: **rc=0**.
  (d) ACCEPTANCE CRITERIA, checked rather than asserted: A1 harness gate green (C1-C4 + F1-F4);
  A2 green (above); A3 `/` limb 77 GB >= 55e9 B, `/srv/models` limb waived under DEC-9 with reasons
  recorded; A4 provenance repaired (UD-Q6_K sha256 pinned, RepoDigests present); A5 G13 closed —
  all six ratio cells present for Q4_K_XL, Q5_K_XL and Q6_K, and the DEC-7-corrected five for
  Q6_K_XL, with `imbalance_mib` on every cell in all four artifacts; A6 ceilings bracketed with a
  failed rung above attempted twice; A7 G21 closed positively at 212,992; A8 answered — adopt
  `-ctxcp 32`; A9 this entry plus PN-13..PN-18 and the sync below.
  (e) MINOR DEFECT RECORDED, not repaired: `ssa_kld.py`'s serverlog label omits the KV dtype, so
  the f16 base run overwrote the q4_0 base run's log for the same arm+domain (both are
  `ssa-Q6_K_XL-code-base`). Only 9 of 10 logs survive as distinct files. No number is affected —
  both PPL values are in the JSON — but the label should include `kv` before any re-run.
Result: **Wave 1 and SSA are CLOSED.** Track A has all three axes for the first time: accuracy
  (SSA divergence ranking, both domains, E2 closed), context (four bracketed ceilings) and speed.
  Nothing is running on the GPU. No data was lost anywhere in the deletion or the quarantine.
Verified: `verify-sweep.sh --stage 1a` rc=0 with "no empty e12 serverlogs"; `df -h /` 77 G avail;
  `ls /srv/bench/e12/ssa/` = 3 JSON files, no `.kld`; quarantine REGISTER.json holds 7 entries;
  9 serverlogs present locally with the raw `Mean KLD` line confirmed in a spot-check; A5 cell and
  ratio counts enumerated per quant; git hub and tar sync both updated.
Next: no autonomous work remains — every queued step has run. Outstanding items ALL need a human
  decision or unwritten code: S5 (HumanEval+ prompt-KLD harness), S6 (generative HumanEval+, 2 arms
  paired), S7 (owner call on the free `--hellaswag`/`--winogrande` anchors), Wave 2 (MTP/DFlash
  sweeps), Wave 4 (speed/energy curve, Track A decision procedure, docs graduation into CLAUDE.md
  and PAPER-REFERENCES.md). The halted conductor's stale reviewer task also remains open.


### L-10 | 2026-08-30T12:50:00Z | S2-execute | claude-opus-5 | conductor-manager | TRACK A DECIDED + repo reorganisation <!-- bsc-ledger:qbench-t1-TRACKA -->
Did: (a) REPO ORGANISATION, owner-raised: two files named `CLAUDE.md` existed — the root agent
  guide and `data/CLAUDE.md`, which md5 confirms was a byte-identical mirror of multivac's 79 KB
  MACHINE log. Claude Code discovers `CLAUDE.md` **by name** anywhere in a tree and merges what it
  finds into an agent's instructions, so an agent working under `data/` could have loaded an
  engineering log as governing instructions. Moved to `data/multivac-src/multivac-CLAUDE.md`;
  the root file is now the only `CLAUDE.md` in the repository, by rule. The same audit found
  `PAPER-REFERENCES.md` existing THREE times (root, `data/`, `data/multivac-src/`) with the root
  copy silently 25 KB stale — consolidated to the single `multivac-src/` mirror. `sync-multivac.sh`
  rewritten to the new paths and re-verified end-to-end; `data/README.md` added stating both naming
  rules and why they are load-bearing.
  (b) TRACK A DECIDED — `docs/paper/TRACK-A-DECISION.md`. Produced with **zero additional GPU
  time** from Wave-1 and SSA data. Primary: **UD-Q6_K** at `-ts 58,42 -ctxcp 32`, full 262,144
  window. Fallback A (max fidelity): UD-Q6_K_XL at 212,992. Fallback B (min VRAM): UD-Q4_K_XL.
  **UD-Q5_K_XL is DOMINATED and recommended against** — same ceiling as Q6_K, 1.76x the code
  divergence, speed inside noise, only 1.1 GB smaller.
  (c) THE FINDING THAT DROVE IT, and it required correcting our own summary. `wave1-summary.md`'s
  decode column mixed THREE estimators: Q4_K_XL's figure was its last repetition (13.33, not its
  median-of-six 12.61), Q5_K_XL's was its FIRST repetition (10.82, not its median 12.70), Q6_K's
  was correctly a median-of-three. Recomputed on one statistic for all arms, the medians are 12.70
  / 12.61 / 11.90 — a **6.7 % span against within-arm repetition noise reaching 32.9 %**. The arms
  are INDISTINGUISHABLE on decode throughput; accuracy separates them at 3.7-11.8 sigma. So the
  decision rule's first criterion is the only one that resolves anything, and the usual "smaller
  quant buys speed" trade does not hold on this host — the cheaper arm is not faster, only less
  accurate. Recorded as PN-19 (the finding) and PN-20 (the reporting defect). The summary file is
  left on disk unedited and superseded by the note, per the append-never-rewrite rule.
Result: The project's primary deliverable exists. Track A has a defended answer with its evidence
  trail, its conditions, and its honest limits. Catching the mixed-estimator defect mattered: taken
  at face value the summary reversed the apparent speed ranking of two arms and would have argued
  for a different configuration.
Verified: one `CLAUDE.md` in the repo (`find` confirms); one `PAPER-REFERENCES.md` mirror;
  `sync-multivac.sh pull` green against the new paths with both mirrors landing correctly; decode
  repetitions enumerated per arm from the tsweep artifacts and medians recomputed independently of
  the summary; TRACK-A-DECISION.md cites only artifact-backed numbers.
Next: S5 in flight. S7 blocked on an owner call — it needs two external datafile downloads
  (HellaSwag and Winogrande), which I wrongly described as "free/built-in" when recommending it;
  the flags are built in, the data is not. S6 needs an unwritten generative harness. Wave 2 and
  Wave 4's speed/energy curve are both optional — the Track A decision does not depend on either.


### L-11 | 2026-08-30T13:00:00Z | S2-execute | claude-opus-5 | conductor-manager | S5 complete; S7 pilot gate fired; S7 cost corrected twice <!-- bsc-ledger:qbench-t1-S5-S7 -->
Did: (a) S5 COMPLETE — divergence over the 164 HumanEval+ task prompts (18,432 tokens/cell),
  same instrument, reference and seed as S2/S3. Result establishes a THREE-TIER DOMAIN HIERARCHY
  (PN-21): mean KLD rises monotonically prose -> generic code -> actual task prompts, and the
  prose-to-task amplification GROWS with quantization aggressiveness (3.13x / 3.87x / 4.40x for
  Q6_K / Q5_K_XL / Q4_K_XL). Against Fireworks' <0.007 threshold, two of three arms pass on prose,
  one on generic code, **none on the task distribution**. Q4_K_XL's top-1 agreement falls to
  95.894 % — about one token in 24 differs from the reference under greedy decoding.
  TRACK-A-DECISION.md updated: the primary recommendation (UD-Q6_K) is unchanged, but Fallback A
  (Q6_K_XL) is strengthened and Fallback B (Q4_K_XL) is weakened, both with the reasoning stated.
  (b) S7 PILOT GATE FIRED, and it earned its place. The 25-task HellaSwag pilot returned rc=0 with
  an unparsed score, so the gate stopped the run (exit 2) BEFORE the full budget was spent. Cause
  was the same class as PN-17: the real output is a running tab-separated table whose accuracy
  carries a `%` suffix and is followed by a CI column, and the first parser matched neither.
  Fixed and verified by re-parsing the existing pilot log — 25 rows, final acc_norm 72.00 %,
  CI95 [52.42 %, 85.72 %]. The `ok` criterion now also requires a parsed accuracy, so this class
  cannot report green again here either.
  (c) S7 COST CORRECTED — twice now, both times by me, both recorded rather than quietly adjusted.
  I first recommended S7 as "free, already built into llama-perplexity": the FLAGS are built in,
  the DATA is not (two external downloads, since fetched with sha256 provenance). The pilot then
  measured the true compute: **250 s fixed model load per cell plus 3.08 s per task**, which makes
  the design as specified (HellaSwag 400 + Winogrande 1267, four arms) **~375 min**, not "free".
  Stopped and put the scope to the owner rather than spending it.
Result: S5 delivered the study's sharpest finding. S7 is parser-fixed, provenance-logged and ready,
  but paused on an owner scope decision. Nothing is running on the GPU.
  Standing caution for the record: S7 cannot rank the arms at any affordable n — at 400 tasks the
  interval is roughly +/-4-5 points against inter-arm gaps of 1-3. Its only value is face validity
  and comparability with published tables. The Track A decision does not depend on it.
Verified: ssa-s5-results.json all 4 cells ok with populated metrics; the three-domain table
  recomputed independently from the two results files; pilot log re-parsed with the fixed patterns
  (25 rows, load 249.756 s); cost arithmetic derived from measured load and rate, not estimated;
  harness, provenance and serverlogs mirrored to data/raw/e12/ and pushed.
Next: owner scope call on S7. Then the remaining optional work: S6 (generative HumanEval+, harness
  unwritten), Wave 2 (MTP/DFlash), Wave 4 speed/energy curve. All optional — Track A is decided.


### L-12 | 2026-08-30T13:45:00Z | S2-execute | claude-opus-5 | conductor-manager | S7 complete — the control that validates the method <!-- bsc-ledger:qbench-t1-S7 -->
Did: S7 ran to completion at the owner-scoped size (HellaSwag, 400 tasks, all four arms) in
  ~32 min, well under the 99 min the pilot-derived cost model predicted — the model reloads faster
  in the steady state than the cold pilot implied, and the cost note in the artifact records both
  figures rather than quietly replacing one with the other.
  Scores: Q6_K_XL 82.75, Q6_K 82.25, Q5_K_XL 82.75, Q4_K_XL 83.25 % — a 1.0-point spread inside
  ~7.4-point independent intervals, with the MOST heavily quantized arm scoring nominally HIGHEST.
  Then extracted considerably more from the same data at zero extra GPU cost: because every arm ran
  at seed 20260830 the tool selects the SAME 400 tasks each time, so these are PAIRED observations
  and the tool's independent intervals waste that structure. Recovered per-task outcome vectors by
  differencing the cumulative accuracy table (`experiments/s7_paired.py`) and ran McNemar —
  Miller/Anthropic's paired-difference recommendation (METHOD-REFERENCES R6) applied to data
  already on disk. Result: **UD-Q6_K_XL and UD-Q5_K_XL answer all 400 items IDENTICALLY** (b=0,
  c=0); every other pair disagrees on 2-4 items; no pair distinguishable (all p >= 0.13).
Result: S7 is the CONTROL that validates DEC-11's whole design, and it is a stronger result than a
  bare null. The same four arms are separated at 3.7-11.8 sigma by divergence, and UD-Q4_K_XL
  alters about one token in 24 under greedy decoding — yet a multiple-choice battery cannot see any
  of it, and ranks the arms backwards. The cause is structural rather than statistical: such
  scoring depends only on an argmax over a few candidate continuations, so it is robust to exactly
  the distribution shift that changes free-form generated code. More tasks would narrow the
  intervals and fix nothing. **Had Track A been decided the conventional way — on a task battery —
  it would have concluded "no meaningful difference" and selected the cheapest arm.**
  Recorded as PN-22 and added to TRACK-A-DECISION.md as the check that changed nothing.
Verified: 4/4 cells scored with parsed accuracies and tool-emitted CIs; per-task vectors recovered
  for all four arms with correct counts (333/331/329/331 of 400) reconciling exactly to the printed
  accuracies; McNemar b/c counts and p-values computed from the paired vectors; artifacts, paired
  analysis, harness and all four serverlogs pulled to data/raw/e12/ and pushed to the hub.
Next: S8 (merged spec-decode test) running — phase 1 humaneval in progress, then score, then the
  descending at-depth ladder. Remaining after that: Wave 2's wider MTP/DFlash setting sweeps and
  Wave 4's speed/energy curve, both optional; Track A is decided.

### L-13 | 2026-08-31T00:00:00Z | S2-execute | claude-opus-5 | conductor-manager | S8 complete — speculative decoding is NOT lossless; n=4 wins at depth <!-- bsc-ledger:qbench-t1-S8 -->
Did: S8 ran to completion unattended on 2026-08-30 (13:37Z–16:16Z, three phases, all green) and
  was then left undocumented for a day — the data was committed by the autonomous sync but no
  ledger entry, paper note or decision amendment was written. This entry closes that gap and
  records the finding that contradicts a premise the study had carried since E11.
  Phase 1 (humaneval): 164 HumanEval+ problems on UD-Q6_K at ctx 32,768, greedy temp 0 / top_p 1 /
  seed 20260830 — a DELIBERATE departure from DEC-2 official sampling, because exact-match
  equivalence is only meaningful at greedy — across four spec configurations. Phase 2 scored them
  through the standard evalplus sanitize/evaluate pipeline. Phase 3 (atdepth) re-measured each
  configuration at the Track A deployment point: UD-Q6_K, `-ts 58,42`, `-ctxcp 32`, q4_0 KV,
  262,144-token window filled to 93.9 % (prompt_n 246,176).
Result: three findings, one of them a correction to the documentation of record.
  1. **MTP is not output-identical to no-spec.** Both `--spec-draft-n-max 2` and `4` reproduce the
     no-spec baseline byte-exactly on 131 of 164 problems (79.88 %), diverging on 33, first
     difference at a median of 715/730 characters in. The standing claim in multivac's ~/CLAUDE.md
     — headline finding 8 and LONG-CONTEXT structural fact 1, "spec decode is greedy-lossless ->
     method affects speed only; accuracy is a quant property" — is **refuted as written** and is
     corrected in that file by this entry. The mechanism is NOT established: the two arms'
     divergence sets overlap only partially (25 shared, 8 unique each, Jaccard 0.610), which points
     at numerical nondeterminism from the changed decode batch shape rather than a broken
     verification rule, but no no-spec-vs-no-spec repeat control was run and that control is what
     would settle it. pass@1 moves 94.5/91.5 -> 93.9/90.2 -> 93.9/90.9, entirely inside the
     ±4.6-point interval at n=164, so it ranks nothing. Recorded as PN-23.
  2. **Draft depth n=4 beats n=2 at every depth, and the gap widens with depth**: +25.6 % at
     32,768 (47.03 vs 37.44 tok/s) and +46.4 % at the full window (16.81 vs 11.48), i.e. 4.90x vs
     3.35x over no-spec's 3.43 tok/s. Since the two depths are equally non-lossless and reach the
     same 262,144 ceiling, the accuracy and context criteria are tied and the tok/s tiebreaker
     decides — which amends the Track A config line from n=2 to n=4. Recorded as PN-24 and as
     Amendment 1 in TRACK-A-DECISION.md.
  3. **All five DFlash2 cells are void** — launched against `llamacpp-mtp:latest`, which cannot
     parse the DFlash2 drafter (`expected 81, got 58`); the fork `llama-dflash2:latest` is
     required. They reported 0.000 pass@1 and `generate-failed`, which in a table is
     indistinguishable from a model that ran and failed. Excluded data, not a DFlash2 result.
     Recorded as PN-25.
Verified: equivalence recomputed independently from the preserved per-problem completions in
  s8-{nospec,mtp2,mtp4}.jsonl, reproducing 33/33 divergences per arm and yielding the set-overlap
  statistic the artifact does not carry; all five dflash4 failures confirmed against their
  serverlogs (identical loader error, server exited during load, hence the connection-refused
  entries in s8-atdepth.json); drafter file confirmed intact on disk; at-depth generation length
  read from the harness (max_tokens 192) and recorded as the caveat on the acceptance figures,
  which read exactly 1.000 for both arms and are not stable estimates at that sample size.
  Evidence pulled to data/raw/e12/s8/ (11 artifacts + 8 completion jsonl) and
  data/raw/e12/harness-src/{s8_spec.py,s8_chain.sh}.
Next: no GPU work is queued and none is required — Track A stands, with its config line amended.
  The one cheap experiment worth running is the no-spec-vs-no-spec determinism control that would
  attribute PN-23's divergence (~40 min). Everything else outstanding is report assembly: this
  repository is being reorganised around the arXiv technical report as its deliverable, with
  CLAUDE.md rewritten as the source of truth and a README added.

### L-14 | 2026-08-31T23:35:00Z | S3-report | claude-opus-5 | conductor-manager | S9a answers PN-23; the campaign self-destructed and was repaired <!-- bsc-ledger:qbench-t1-S9A -->
Did: launched the DEC-12/DEC-13/DEC-14 campaign as four detached chains sequenced by blocking
  flock (S9 → S9d → S9e → S10, ~11 h), supervised by a sentinel emitting one line per new problem
  plus an independent 20-minute check. S9's determinism phase completed. Then the campaign
  cascaded to failure in 8 minutes and was diagnosed, repaired and relaunched.
Result — the science (PN-26): **the S8 divergence is deterministic and systematic, not stochastic.**
  Re-running S8's two configurations unchanged a day later, no-spec reproduced its own 164
  completions byte-identically (md5 `37616d8911fb4792fb76cadf0806511c` on both runs; 18.463 vs
  18.485 tok/s) and MTP n=2 reproduced itself byte-identically as well — while both still differ
  from each other on exactly 33 of 164 problems. Speculation is therefore a **reproducibly
  different decode path**, not an approximation that drifts.
  ⚠️ **This refutes the mechanism PN-23's caveat proposed.** That note argued the partial n=2/n=4
  set overlap (Jaccard 0.610) pointed at float nondeterminism from the changed decode batch shape.
  It cannot: both arms are individually deterministic. The overlap is explained by n=2 and n=4
  being different algorithms — different draft lengths put verification boundaries at different
  token positions, so each diverges deterministically but at a different set of problems. PN-23's
  numbers stand; its mechanistic speculation is withdrawn, and PN-26 supersedes it. Where in the
  verification the difference arises needs engine-level instrumentation, not output comparison.
Result — the incident (PN-27): `preflight()` refuses to launch while the legacy orchestrator runs,
  implemented as `pgrep -af "watchdog.sh|worker.sh"` — unanchored, matching ANY such process. The
  sentinel armed to supervise the campaign was named `campaign_watchdog.sh`. Every phase launched
  after 22:32Z failed preflight; s6, dflash, the 24-cell sweep, the 262 K addendum and the S10
  pilot all died between 22:55:51Z and 23:02:32Z. **The supervision killed the campaign it was
  built to protect.** No data corrupted and no GPU consumed — the check worked correctly on a
  false positive it could not distinguish from a true one.
Verified: fixed two independent ways and both tested under the live failing condition — pattern
  path-anchored to `orchestrator/watchdog[.]sh|orchestrator/worker[.]sh`, and the script renamed to
  `campaign_sentinel.sh`. `preflight()` re-run with the sentinel armed: all five checks pass. A
  second instance of the same family was found while fixing the first — the sentinel's own
  `chains_alive()` used `[s]9_chain.sh`, whose unescaped `.` is a wildcard one character from
  matching the monitor's `tail -f .../s9_chain.log`; escaped and path-anchored. Failed markers and
  error logs archived under `state/*.preflight-selfmatch-20260831` and
  `logs/preflight-selfmatch-20260831/` rather than deleted. All four chains relaunched 23:27:22Z;
  the idempotence guards did their job — determinism and score were skipped as already done.
Next: campaign re-running from S9's pilot; ~11 h. The determinism result is banked and does not
  need re-running. On completion: ledger entries and paper notes per phase, then the report.

### L-15 | 2026-09-01T02:00:00Z | S3-report | claude-opus-5 | conductor-manager | S9 COMPLETE — the generative anchor is null, DFlash2 measured at last <!-- bsc-ledger:qbench-t1-S9-DONE -->
Did: S9 ran to completion after the PN-27 repair (01:53:59Z). Pilot 3/3 with the sentinel armed;
  `determinism` and `score` correctly skipped as already done on the relaunch; `s6`, `dflash` and
  `score` executed. Four artifacts, five scored arms, no empty generations anywhere.
Result 1 — **SSA S6 is a null, and that is the finding** (PN-28). The ladder's two extremes on all
  164 HumanEval+ problems, official sampling, seed-matched, no-spec on both arms:
  UD-Q4_K_XL 93.90 % [89.14, 96.65] vs UD-Q6_K_XL 94.51 % [89.90, 97.09] base; 89.63 % vs 90.24 %
  plus. Paired: the arms agree on **161 of 164** problems (base, discordant 3) and **159 of 164**
  (plus, discordant 5), exact McNemar **p = 1.0** on both, direction inconsistent (1-vs-2, 2-vs-3).
  These are the same arms that differ **3.69×** in code KLD. **This is the generative counterpart
  of S7**: PN-22 showed a multiple-choice battery cannot see quantization damage; PN-28 shows a
  generative coding benchmark cannot either, at the sample size the benchmark has. Together they
  are the empirical case for DEC-11's divergence-first design. The informative quantity is the
  discordance (3 and 5 of 164), not the p-value.
Result 2 — **DFlash2 measured properly for the first time** (PN-29), repairing PN-25. At ctx 32,768
  it is the FASTEST method on the host: 51.78 tok/s, acceptance 0.9172, 2.80× no-spec, ahead of
  MTP n=4 (47.03) and n=2 (37.44); pass@1 93.29/90.24, indistinguishable from every other arm —
  against the 0.000 S8 recorded for it. At depth it is **strictly dominated**: compute-buffer OOM
  at 262,144 AND 212,992, highest reachable rung **163,840** (37.5 % less window than MTP), where
  decode falls to 8.34 tok/s and acceptance **halves to 0.4583**. The 1.19 GiB draft-worker wall is
  now quantified: ~330 MiB of headroom at the Track A config against a ~1,090 MiB drafter. The
  historical acceptance collapse (0.41-0.55 at ~184 K) is reproduced on a surviving image.
Result 3 — S8's score parser repaired (`s8-scores-reparsed.json`), now with Wilson intervals:
  nospec 0.945/0.915, mtp2 0.939/0.902, mtp4 0.939/0.909, dflash4 0.0/0.0 (the void cells). The
  original `s8-scores.json` is left unedited and is superseded.
Verified: independent confirmation of PN-26 through a different pipeline — `nospec-r2` scores
  0.945/0.915 and `mtp2-r2` scores 0.939/0.902, exactly matching their S8 originals, so the
  byte-identity result reproduces at the level of scored outcomes and not only text comparison.
  All five arms carry parsed scores and Wilson intervals; no cell returned ok with empty metrics.
Next: S9d's 24-cell matched-depth sweep started 01:54:19Z, then S9e (262,144 draft depth) and S10
  (divergence vs context depth). One claim is deliberately NOT written yet: S6's decode medians
  (Q4_K_XL 22.15 vs Q6_K_XL 16.06 tok/s at 32,768, a 38 % gap) suggest the inter-quant speed gap
  SHRINKS with depth against PN-19's 6.7 % span at 262,144 — but those two measurements differ in
  spec setting, sampling and ratio, so the comparison is confounded. S9d measures it cleanly at
  matched depth with identical settings; the note waits for that.

### L-16 | 2026-09-01T05:35:00Z | S3-report | claude-opus-5 | conductor-manager | S9d invalid — degenerate generation; PN-24 and Amendment 1 withdrawn <!-- bsc-ledger:qbench-t1-S9D-DEFECT -->
Did: S9d's 24-cell sweep completed at 05:13:28Z reporting 23/24 valid. Every cell reported
  **acceptance exactly 1.000** — the red flag the standing 20-minute check lists — so the artifact
  was inspected before any note was written. It is invalid, and so is more than the sweep.
Result — the defect (PN-30): the cell probe posted the 123,666-token pad to
  `/v1/chat/completions` as a user message with `max_tokens: 512`. Given a corpus and no
  instruction the model answers briefly and stops: **all 69 reps generated exactly 17 tokens**
  (min = median = max). Decode was therefore timed over 17 tokens — yielding 52.27 tok/s at
  131,072, faster than most configurations reach at depth 0 — and acceptance was computed over
  36-48 draft events on a trivially predictable continuation. The `valid` gate asserted
  `prefill_frac >= 0.90` (which passed at 0.9435) and asserted nothing about generation. **PN-5's
  lesson recurring inside the harness written to honour it**: prefill contract in code, generation
  contract in the docstring.
Reach: the same construction is used by `s8_spec.py --phase atdepth`, and the engine's own log
  confirms it — `eval time = 951.92 ms / 17 tokens` and `draft acceptance = 1.00000 (16 accepted /
  16 generated)`. **PN-24's at-depth half is withdrawn**; its ctx-32,768 half (medians over 164 real
  HumanEval+ generations at max_tokens 1024) stands. **Track A Amendment 1 is withdrawn** by
  Amendment 2 and the config line reverts to `--spec-draft-n-max 2`, the only draft depth with a
  valid measurement at 262,144 (11.90 tok/s, median of 3, Wave 1).
  ✅ **Wave 1 is UNAFFECTED and was checked, not assumed**: every tsweep cell records
  `n_predict = 192` with acceptance spread 0.495-0.911, because tsweep uses `/completion` with
  `prompt = pad + "\n\n# Summary:\n"`. PN-6, PN-7, PN-8, PN-18, PN-19 and the quantization decision
  are sound. The recommendation changed a flag, not the model.
Verified: harness repaired to tsweep's proven construction (`/completion` + continuation cue,
  official sampling so acceptance stays comparable with PN-9) plus a generation gate. **Piloted on
  one cell before re-running 24**: predicted_n 512/258/512 against the previous 17, acceptance
  0.7747 over 1003 draft events, decode median 17.78 with 33.9 % spread (matching PN-19's
  documented noise), prefix cache confirmed (`prompt_n` 4, `cache_n` 123,666 on reps 2-3). The
  pilot also corrected the gate itself: an initial "every rep >= 90 % of n_predict" rule failed a
  good cell whose middle rep stopped naturally at 258 tokens on EOS, so the gate is now an absolute
  128-token floor, which rejects the degenerate case decisively and accepts natural EOS variation.
  Invalid artifact quarantined with a register (`quarantine/README-s9d-degenerate.md`), never
  deleted. The stale `s9d_sweep.done` — written because the run exited 0 under the WRONG gate — was
  archived as `.INVALID-degenerate-17tok-20260901`; under the corrected gate a degenerate run
  yields zero valid cells, exits 2, and cannot leave a marker at all.
Cost: ~3.3 h of GPU on the invalid sweep, plus the re-run. Chains relaunched 05:29:41Z in lock
  order s9d → s9e → s10.
Next: S9d (~4 h), S9e (~40 min), S10 (~3.5 h). The 20-minute check earned its place here — the
  sweep would otherwise have been written up as a result.

### L-17 | 2026-09-01T20:00:00Z | S3-report | claude-opus-5 | conductor-manager | S9d re-run + S9e closed; both underpowered <!-- bsc-ledger:qbench-t1-S9D-DONE -->
Did: S9d re-ran under the repaired harness (09:17:24Z, 21/24 valid) and S9e completed (09:53:27Z,
  2/3 valid). Both were analysed before anything was written up — prompted by the standing
  20-minute check, whose red-flag list includes "acceptance reading exactly 1.000".
Result (PN-32): the repaired harness worked — depth matching exact (identical prompt_n 123,670 and
  186,270 at the two rungs), generations real, and the generation gate caught two cells at 55 and
  124 tokens. **Acceptance falls monotonically with draft depth in 12 of 13 adjacent pairs
  (sign test p = 0.0017)**, ~0.67-0.92 at n=2 down to ~0.25-0.57 at n=8. S9e: Q6_K at 262,144
  gives n=2 12.47 tok/s / n=4 12.88 tok/s — a 3 % difference — and **n=8 fails to load**, the
  draft context not fitting at the full window.
  ⚠️ **The ranking question is unanswerable at n=3.** Decode rep-spread reached 166 % (median 34 %,
  75 % for n=8 cells) and per-rep acceptance ranged up to 0.629 within a single cell. The pooled
  Wilson intervals (±0.02 over 1,000-4,000 draft events) are MISLEADING — draft events inside one
  generation are correlated, so the effective n is 3 generations, not 4,000 events. That is R6's
  clustered-standard-error trap, and it is the most useful thing this sweep produced.
Consequence: **PN-9's quant/depth/ratio confound stays unresolved and PN-24's generality question
  stays unanswered** — DEC-13 reinstated this sweep specifically to close them, and it did not.
  Resolving either needs ~30 reps per cell rather than 3. No per-arm "best draft depth" is
  reported. Track A's revert to `--spec-draft-n-max 2` (Amendment 2) stands, now on the firmer
  ground that n=2 and n=4 are indistinguishable at 262,144 rather than on a withdrawn measurement.
Verified: sign test computed over all 13 adjacent pairs; per-rep acceptance recomputed from the raw
  reps to expose the clustering the pooled figure hides; both invalid cells carry their
  `invalid_reason`; S9e's n=8 failure classified from its serverlog.
Next: nothing running. S10 is cancelled as infeasible (DEC-15/PN-31), S11's instrument was
  measured and rejected (see below), and the depth question now awaits an owner decision on a
  RULER-based design.

### L-18 | 2026-09-02T13:00:00Z | S3-report | claude-opus-5 | conductor-manager | S12 RULER complete — MEASUREMENT PHASE CLOSED <!-- bsc-ledger:qbench-t1-S12 -->
Did: built and ran S12 after S10 was declared infeasible (PN-31) and S11 was rejected on its own
  data. Researched what the field actually does rather than improvising: RULER (R8) is the
  standard, and two published studies run our exact experiment with it (R9). Used RULER's own
  generators, templates, prompt construction and metric — the metric unit-checked against the
  reference implementation on five cases before any GPU time.
Result 1 (PN-33): **S-NIAH saturated at 100.0 for BOTH arms at 8,192 / 32,768 / 131,072**;
  accuracy recovery 100 % at every length, zero empties, prompt_n medians on target. **MK-NIAH at
  131,072 gives 100.0 vs 91.67** — recovery 91.67 %, beside Red Hat's published 85-88 % for 4-bit
  at 128K. ⚠️ That is ONE failed sample of twelve; Wilson intervals [75.7, 100.0] and [64.6, 98.5]
  overlap almost entirely. Reported as "consistent with published results, not established here".
  Separating an 8-point drop needs n≈100 ≈ 11 h at this depth.
Result 2 (PN-34) — **the finding that emerged, and the paper's methodological through-line**:
  sixteen-fold more context bought NO discrimination on S-NIAH, because the task is saturated.
  Holding depth fixed and raising DIFFICULTY is what produced a difference. So a benchmark's
  sensitivity to quantization damage is gated by **task headroom, not by modality and not by
  context length**. That closes a three-instrument arc: PN-22 (multiple-choice, blind),
  PN-28 (generative coding, blind), PN-33/34 (retrieval, blind while easy — sighted when hard).
  Every one has a ceiling; divergence does not, which is why 20 min of KLD separates these arms at
  3.7-11.8 σ where ~20 h of task benchmarking across three modalities separates them nowhere.
Verified: metric identical to RULER's on 5 cases incl. partial-match and case-folding; end-to-end
  smoke 100.0 @4K before the battery; every generated set within ~1 % of its target length; two
  duplicate c8192 cells (failed resume) deduped with a note; `variable_tracking` excluded after two
  measured attempts (30 and 120 token budgets) for an output-format artifact — data retained under
  `variable_tracking_excluded_cells`, never deleted.
Cost control applied mid-run: the flat n=25 design was 8.0 h with ~75 % in the deepest rung, so
  sample counts went per-length (25/25/12); dropping `variable_tracking` halved the remainder.
  MK-NIAH data was pre-generated on CPU while the GPU ran, so the hedge cost nothing until needed.
Next: **measurement is closed.** No GPU work is queued and none is required. Remaining scope is the
  arXiv report: draft against manuscript/OUTLINE.md, every claim traced to a PN entry.

### L-19 | 2026-09-02T20:00:00Z | S3-report | claude-opus-5 | conductor-manager | Three-way review round: two blind reviews + an archivist <!-- bsc-ledger:qbench-t1-REVIEW -->
Did: at the owner's direction, spawned three researchers at max effort — two performing INDEPENDENT
  BLIND reviews (neither saw the other's work, nor my own non-blind pass), and one archivist
  building the reference corpus. Each read PN-1..PN-35, the 2,086-line build stream, all 173
  `data/raw/e12/` artifacts and both machine records, and each **recomputed values from the
  artifacts rather than trusting the notes**. I contributed a fourth, explicitly non-blind pass
  (`manuscript/review/insider-notes.md`) covering what only an author knows: which results are
  fragile for reasons not written down.
  Deliverables now on disk: `manuscript/review/{reviewer-a-rigor.md (1,655 lines),
  reviewer-b-structure.md (1,551 lines), insider-notes.md}` and
  `manuscript/references/{METRIC-CORPUS.md (1,659), references.bib (47 verified entries),
  PROVENANCE.md, TIMELINE.md}`.
Result — **the reviews converged independently on the same defects, which is the strongest
  corroboration this process can produce.** Both found the missing MK-NIAH artifact; both found the
  PN-19 depth confound; both flagged scope creep on the losslessness claim.
  1. **PN-19's statistics are wrong** (found by both). Its "n=6 repetitions at 262,144" is six
     readings across FOUR depths, so its 32.9 % "repetition noise" is largely a depth effect.
     Recomputed over true repetition groups: max within-configuration spread is **46.7 %**, the
     matched-depth between-arm span is **8.6 %**, and UD-Q4_K_XL has **no repetition group at all**
     at 262,144 (n=1). **The conclusion is unchanged and better supported.** Superseded by PN-36.
  2. **PN-33/PN-34's centerpiece had no artifact in the repo** — the MK-NIAH data existed only on
     the host, so the paper's declared headline broke its own note→artifact→serverlog rule. Synced.
     Worse, the *generation command* existed nowhere: the harness READS a pre-generated file and the
     `--num_needle_k 4` invocation was ad-hoc. Recorded as `s12_mkniah_generate.sh` so the dataset is
     reproducible from a public repo.
  3. **Two errors in PN-35, written hours earlier by me.** Its evidence line claimed the quantiles
     exist only in serverlogs — false; six of seven are in the committed artifact's
     `metrics_reparsed`. And it cited this ledger entry before it existed. Both corrected in place
     with dated markers.
  4. **A citation that inverts its source.** R5/PN-14 cite LocalBench's "KLD 0.01-0.03 for Q4_K_M"
     as a reference band; LocalBench **disclaims** it as an artifact of short-context Wikipedia
     protocols. Corrected — and it now supports this paper's protocol-dependence thesis instead of
     standing against it.
  5. **R11/R12 attribution corrected three ways**: PaperBanana is not "Google Research's method"
     (mixed affiliations; the implementation disclaims affiliation); DFlash is an **ICML 2026**
     paper whose authors' code is `z-lab/dflash` — **the same lab as our `llama-dflash2` engine
     fork**; and "bit-for-bit identical" is the third-party MLX port's wording, not the paper's.
     R12 is reframed as MOTIVATION only, never as something this study refutes.
  6. **The thesis needs restating.** Saturation is factually wrong for two of three instruments
     (HellaSwag has ~17 points of headroom, HumanEval+ ~5); only S-NIAH is saturated. And
     Dutta et al., *Accuracy is Not All You Need* (NeurIPS 2024, arXiv 2407.09141), may already own
     "divergence sees what accuracy hides" — which is precisely why PN-35's tail structure matters
     as the novel contribution.
  7. **PN-35 was found by review, not by us** — the median and decile KLD fields sat in our own
     artifacts for twelve days unexamined.
Verified: I independently re-derived the PN-19 depth confound from the cells' `key` fields before
  accepting it, and re-derived PN-35's quantile table from raw serverlogs before writing it. Every
  correction above was checked against the artifact rather than taken on a reviewer's word.
Next: 33 numbered repairs are listed in reviewer-a-rigor.md; most cost no GPU. The one that does —
  MK-NIAH at n≈100, ~11 h — decides whether a long-context claim can stay in the title. Outstanding
  documentation debt: S11 ran, produced 12 cells and still has no paper note.

### L-20 | 2026-09-03T03:00:00Z | S3-report | claude-opus-5 | conductor-manager | MK-NIAH n=100 — the long-context question is answered <!-- bsc-ledger:qbench-t1-MK100 -->
Did: ran MK-NIAH at n=100 on both ladder extremes at 131,072 (9.4 h, 200 full prefills, 0 empty
  responses). Pre-flight followed the discipline the earlier failures forced: RULER's semantics read
  from its own source (`num_needle_k=4` → four keys, one queried, three hard distractors) and
  confirmed against the paper; the dataset generated and checked (100 samples, all needles unique,
  130,439-131,072 tokens); the full code path exercised by a 4-minute mock at 8,192; the time
  estimate taken from the measured n=12 cells (170 s/sample) rather than guessed; and the paired
  analysis **written and committed before the second arm finished**, so the test was fixed in
  advance of the data.
Result (PN-44): **UD-Q6_K_XL 89.0, UD-Q4_K_XL 79.0, recovery 88.76 %, exact McNemar p = 0.0020**,
  paired difference −10.00 pts [−15.88, −4.12]. Ten discordant items, **zero in the other
  direction** — the cheaper arm's failures are a strict superset of the reference's, and the test
  returned the minimum p its design permits. The figure sits inside Red Hat's published 85-88 %
  band for 4-bit at 128K (R9), reached independently on a different model, compression family and
  hardware class.
  ⚠️ **This supersedes PN-33's MK-NIAH half.** Its n=12 reference of 100.0 was a lucky draw
  (P(12/12 | p=0.89) ≈ 0.25) and implied a ceiling that does not exist — the n=12 estimate was not
  merely imprecise, it pointed the wrong way. The 11 GPU-hours bought the difference between
  "consistent with published results, not established here" and a separated result.
Consequence for the paper: **§5.2 now has a third instrument that separates**, and the three order
  themselves by how close each task sits to the model's limit — multiple-choice and generative
  coding bound the effect to a few points, single-needle retrieval to zero, multi-key retrieval
  separates it. That ordering is what PN-35's tail mechanism predicts, and it is a stronger
  argument than three bounds of differing width. OUTLINE §5.2 updated; the "do not write until this
  lands" marker is removed.
Next: measurement is closed for real this time. Remaining scope is drafting, plus two owner
  decisions blocking publication — no LICENSE file, and commit authorship carrying an internal LAN
  IP across the history.

### L-21 | 2026-09-03T05:10:00Z | S3-report | claude-opus-5 | conductor-manager | PN-45 — a correction to a correction <!-- bsc-ledger:qbench-t1-PN45 -->
Did: audited PN-36, which this session had itself written to supersede PN-19's within-arm speed
  variance figure, after an archivist pass flagged the arithmetic. Two independent defects, both
  mine, both in the same note.
Result (PN-45): **the estimator was switched silently.** PN-19 computed within-arm spread as
  `(max − min) / median`; PN-36 reported 46.7 %, which is `(max − min) / min`. Under PN-19's own
  rule the maximum is **40.7 %**, not 32.9 % and not 46.7 % — so PN-36 was right that PN-19
  understated the spread, and wrong about by how much, because it changed the denominator without
  saying so. Second defect: the Q6_K `-ts 58,42` group **mixed `-ctxcp 4` and `-ctxcp 32` readings**
  — the fourth reading, 11.48, is tagged `:ctxcp32` and is PN-18's A/B partner, not a repeat. Its
  inclusion pulled the group median from 11.90 to 11.69 and manufactured a "8.6 % between-arm span"
  that does not exist; **the corrected span is 6.74 %.**
Consequence: §5.5's claim that speed does not discriminate **survives** — a 40.7 % within-arm spread
  against a 6.74 % between-arm span argues it more strongly than the numbers it replaces. But the
  defect class is the one this project has now hit three times: a comparison group assembled without
  checking that every member shares the varied-variable's control settings (PN-43's label collision,
  PN-9's depth/ratio confound, and now this). Also fixed F-27 in passing: `s12-ruler.json`'s
  `accuracy_recovery` carried the stale n=12 value of 91.67 and no `mk100` entry; it now carries
  88.76 and the stale figure is removed.
Next: the historical corpus has no paper notes at all — see L-22.

### L-22 | 2026-09-03T14:50:00Z | S13-historical-integration | claude-opus-5 | conductor-manager | The first nine days enter the record <!-- bsc-ledger:qbench-t1-HIST -->
Did: audited the whole corpus against the paper notes rather than against the last wave, after the
  owner observed that the review round and the outline were both built almost entirely from E12.
  The audit is unambiguous: **every one of PN-1…PN-45 is dated 2026-08-29 or later, and the study
  began around 2026-08-20** — so roughly nine days of measurement, including the study's only
  full-size task-benchmark runs, had no paper note of any kind. Occurrence counts inside
  `PAPER-NOTES.md` before this entry: `SWE-bench` 0, `vLLM` 0, `NVFP4` 0, `"Protocol 1"` 0,
  `agentic` 1, `energy` 1.
Result: **PN-46…PN-59 written**, every number verified against an artifact rather than against
  prose, because two of the historical summaries turned out to be stale in ways that would have
  propagated. The four that change what the paper can say:
  - **PN-49 — the perplexity protocol reconciliation.** The same checkpoint reads +29 % worse or
    +0.8 % worse than its comparison ladder depending only on corpus file, window coverage and
    scoring rule: **a 36-fold swing in the reported effect from measurement convention alone**, with
    the intuitive explanation (tokenizer mismatch) tested and disproven. This is the paper's
    methodological thesis, already measured, and it belongs near the front.
  - **PN-51 — Q3_K_XL.** Fastest configuration in the study (116.9 tok/s), acceptable HumanEval+
    (84.1/81.7), **1.000 draft acceptance at 258,779 attended tokens**, and 6 of 6 instances at the
    agent step limit against the reference's 0 of 6. Every cheap instrument rates it well; only the
    expensive one rates it correctly. It also kills "acceptance is an accuracy signal" outright.
  - **PN-50 — SWE-bench Verified.** Three arms at n≈50 resolve 77.6 / 76.0 / 75.5 %, **inverting**
    the HumanEval+ and perplexity ordering, on a ±12-point bootstrap interval. The inversion is
    noise, and saying so is the point: the study's most expensive instrument cannot rank its own
    ladder.
  - **PN-59 — the losslessness premise.** "No separate runs needed" was written into the reference
    log on 2026-08-21 and refuted on 2026-08-30 (PN-23). The suppressed runs were never performed,
    so the corpus has no divergence measurement of any speculative configuration. The cost of an
    unmeasured premise, documented.
  Also entered: PN-46/47/48 (the two HumanEval+ ladders and the PPL ladder, all monotonic, none
  separating), PN-52 (agentic step counts, non-monotonic across the full ladder), PN-53/54 (the
  1.19 GiB draft-worker wall across three engines, and SGLang producing no results at all),
  PN-55 (cross-backend speed and energy), PN-56 (the 5.1× context gap), PN-57 (the deleted image),
  PN-58 (the ten-defect instrumentation audit).
⚠️ Two source documents are **stale and must not be quoted**: `PAPER-REFERENCES.md`'s SWE-bench
  table carries the pre-ARM64-fix figures (36/47, 35/48) superseded twice over, and its
  thinking-mode HumanEval+ table still shows four of seven arms as "running"/"queued". The machine
  log has the corrected values in both cases. Recorded here rather than edited, per hard rule 6 —
  both documents are owned by multivac and any repair is appended there.
Next: two peer reviewers are auditing the full corpus in parallel — one on completeness and
  historical integration, one adversarial on statistics and positioning — each also proposing a
  title and abstract. Reconcile PN-46…PN-59 against their registers when they land; expect
  additions, and expect some of these to be judged too thin to promote. The outline must then be
  rewritten against a 59-note evidence base rather than a 45-note one, with §Agentic behavior
  populated for the first time.

### L-23 | 2026-09-03T15:40:00Z | S13-adversarial-review | claude-opus-5 | conductor-manager | Two reviewers, and the long-context headline does not survive <!-- bsc-ledger:qbench-t1-REV2 -->
Did: ran two independent peer reviews over the full corpus — one on completeness and historical
  integration, one adversarial on statistics and positioning — after the owner observed that the
  first review round and the outline were both built almost entirely from the last four days.
  Outputs: `manuscript/review/reviewer-c-corpus.md` (1,168 lines) and `reviewer-d-adversarial.md`
  (1,214 lines). **Every consequential claim below was recomputed here from committed artifacts
  before being accepted; none is taken on a reviewer's word.**
Result — two corrections, both confirmed, both free:
  **PN-60 supersedes PN-44 and PN-37's mechanism clause.** The MK-NIAH n=100 battery ran through
  `/completion` with `n_predict=128` and thinking on, so every generation is a `<think>` block
  competing with the answer for 128 tokens. Recomputed from the committed predictions:
  **closed-and-wrong = 0 in both arms** — every failure is a truncation — and on the **55 of 100
  items where neither arm's budget bound, both score 55/55 with zero discordance.** The real,
  still-separated effect is budget closure: 77 vs 60, discordance 22/5, exact McNemar
  **p = 0.001514**. The 89.0/79.0/88.76 %/p = 0.0020 headline is a reasoning-verbosity result, not a
  retrieval result, and the Red Hat 85-88 % recovery comparison (R9) is **void**. This is the same
  defect that got `variable_tracking` excluded from this very battery; the budget check that
  justified keeping the needle tasks ran at 8,192 on the single-needle variant and was never re-run
  at 131,072 on the multi-key one.
  **PN-61 corrects PN-51, written four hours earlier in this same session.** The historical
  acceptance figures of exactly 1.000 at 99K-259K are **degenerate-generation artifacts**: 50-55
  generated tokens over 34-36 draft events, the PN-30 signature. The rows that actually generated
  1,024 tokens record 0.9221 (MTP n2 @168,011) and 0.553 (DFlash2 n4 @184,011). PN-51's agentic
  finding (6/6 at the step limit vs the reference's 0/6) **stands**; its acceptance clause is
  struck, and with it the tidy "perfect acceptance beside total agentic failure" line. The
  Q3-embedded speed-versus-depth curve inherits the same defect, so "graceful degradation, no
  cliff" is not supported by it; the MTP-vs-DFlash2 reversal survives because both its arms
  generated 1,024 tokens.
Also raised, verified, not yet acted on:
  - **PN-35's tail quantiles are in no committed file.** `ssa-results.json` carries only `ppl` and
    `ppl_err`; the KLD distribution tables exist solely in 14 host serverlogs under
    `/srv/bench/server-timings/`, which `.gitignore` excludes. The paper's novel contribution is
    currently not reproducible from the public repository at all. Extraction is free and is next.
  - **Multiple comparisons:** Holm and BH over all 19 tests leave all 11 positive results standing,
    but the weakest (prose Q6_K-Q5, 3.71 sigma) dies at design effect 1.5 under Bonferroni — so the
    signature phrase "3.7-11.8 sigma" quotes a range whose lower endpoint does not survive.
  - **PN-22's six McNemar tests could not have reached p < 0.05 at any outcome** (max discordant 4,
    minimum attainable p = 0.125). PN-40 was written to fix exactly this error and fixed PN-28 only.
  - **The "unexplained" decode noise is the acceptance lottery.** Both reviewers found it
    independently: `draft_n`/`draft_n_accepted` are byte-identical across `-ts` ratios within a rep,
    and decode regresses on acceptance at r-squared 0.83-0.99. Conditioning collapses within-config
    spread from 17-41 % to 3-11 %. Three passes (PN-19 -> 36 -> 45) missed it.
  - **PN-32 tests a tautology** — acceptance = accepted/drafted is strictly decreasing in draft
    depth for any per-token probability below 1 — and its pair count is 11, not 13 (two are n2->n8
    skips), giving p = 0.0059 rather than 0.0017.
  - **PN-29's DFlash2 at-depth cell reportedly uses the same unrepaired probe** as PN-30's withdrawn
    claims and was never withdrawn. **Unverified here.** It is cited in OUTLINE §5.4.
  - **PN-41's cost contrast is stale by 9.4 h** (mk100 landed after it): approximately 2.2 h vs
    14.3 h, about 6x, not 2.2x.
  - Artifact-badging: honest tier is **Artifacts Available only**, after a DOI. `acmtxt.md` is a
    76 KB scraped web page with cookie-banner text at the repo root and should go; `CITATION.cff`
    declares a repository URL that does not exist yet.
Consequence for the paper: **§5.2 loses its third instrument.** The ordering "multiple-choice and
  generative coding bound the effect, single-needle bounds it to zero, multi-key separates it" —
  L-20's strongest structural claim — no longer holds, because multi-key separates on closure and
  not on retrieval. What replaces it is arguably better evidenced and comes from the first nine
  days: SWE-bench Verified **inverting** the ladder at n≈50 on a ±12-point interval (PN-50), and
  Protocol-1 perplexity spanning 0.033 against its own ±0.041 standard error (PN-48). Both reviewers
  independently proposed retitling away from the tail finding as the load-bearing claim.
Next: extract the KLD tables from the 14 serverlogs and commit them; verify the PN-29 exposure;
  re-analyse the speed data conditioned on acceptance; then rewrite the outline against a 61-note
  base. Title and abstract remain the owner's call — both reviewers' proposals are in their files.

### L-24 | 2026-09-03T16:25:00Z | S13-integrity-audit | claude-opus-5 | conductor-manager | S12 integrity audit — the S-NIAH cells are clean, and PN-60 gets its control <!-- bsc-ledger:qbench-t1-S12AUDIT -->
Did: ran a requested integrity pass over the S12 RULER battery. **Premise correction first: nothing
  is running and nothing is hung.** S12 completed 2026-09-02T06:22Z and the mk100 arm 2026-09-03T02:55Z;
  all five phase markers carry `.done`, no `.failed`, both GPUs idle at 2 MiB, no llama-server or
  chain process alive, only the six telemetry containers up. Disk on `/` is 71 GB free (well above
  the 20 GB floor). There is no active phase to verify and no new length slice to write up.
Result: the per-cell screen passes on every criterion except one, and that one is a **false alarm
  worth recording**. All 12 cells have non-null scores, `n` matching N_SAMPLES for their length,
  `n_empty` = 0 everywhere, and `prompt_n_median` at 98.2-99.9 % of target (8,041 / 32,616 /
  130,936-130,941) — no haystack truncation anywhere. The screen's degenerate-match rule
  ("no cell at exactly 0.0 or exactly 100.0 across both arms") flags **five slices**: single-needle
  at 8,192, 32,768 and 131,072, plus the mock. **PN-63 clears them on independent evidence** — those
  cells close their reasoning block on 100 % of samples in both arms with zero truncations, so the
  100.0 is a real ceiling, not a broken prompt. A score alone cannot make that distinction; closure
  can.
  The audit also hands PN-60 the control it was missing. At the **same** 131,072 length, same arms,
  same 128-token budget, single-needle closes 12/12 in both arms while multi-key closes 77/100 and
  60/100 — so the truncation that voids PN-44 is caused by **task difficulty lengthening the
  reasoning, not by depth**. That narrows the correction from "confounded" to a specific,
  defensible mechanism. Across all fourteen cells `closed-and-wrong` is **exactly zero**: not one
  instance in the whole battery of the model finishing its reasoning and answering wrongly.
  Two further confirmations: `variable_tracking` is 0/25 in both arms with zero closures and a
  127-character median output — the existing exclusion was right, and this is the same defect at its
  extreme; and `mkmock` scores 3/3 in both arms with **zero** closures, a direct demonstration that
  the scoring rule passes truncated generations.
⚠️ The requested comparison of accuracy-recovery against Red Hat's published points (>99.5 % short,
  85-88 % for 4-bit at 128K) was **not performed, deliberately**: PN-60 established that the mk100
  numbers measure budget closure rather than retrieval, so checking them against a retrieval-recovery
  band would re-commit the error PN-60 corrects. `s12-ruler.json`'s `accuracy_recovery` field should
  be read as void for the mk100 entry until a re-run with thinking disabled exists.
Next: unchanged from L-23 — verify the PN-29 exposure, re-analyse speed conditioned on acceptance,
  rewrite the outline against what is now a 63-note base.

### L-25 | 2026-09-03T17:10:00Z | S3-report | claude-opus-5 | conductor-manager | Title and abstract chosen <!-- bsc-ledger:qbench-t1-TITLE -->
Did: selected the paper's title and abstract from the six title sets and six abstracts proposed by
  the second review round, and retired the incumbent working title in `CITATION.cff` and
  `manuscript/OUTLINE.md`.
Result — **title: reviewer D's T2**, *"Divergence Ranks What Benchmarks Bound: quantization, context
  and speculative decoding for a 27B coding model on two 16 GB GPUs"*. D ranked T2 **second**, behind
  a deliberately safe descriptive title, but made the ordering explicitly conditional: *"If the
  MK-NIAH re-analysis is done and comes back as I predict, T2 becomes clearly correct and I would
  prefer it."* It was done and it came back as predicted (**PN-60**), so this takes D's stated
  preference rather than its hedge. PN-60 does not merely permit T2, it strengthens it: while PN-44
  stood, a task benchmark *did* resolve the ladder, which contradicted "what benchmarks bound"; with
  MK-NIAH re-analysed, no task instrument separates the arms on its intended construct and the
  contrast is cleanly true across all twelve days.
  Reviewer C's T9 (*"What the Benchmarks Cannot See, and What the Protocol Decides"*) was rejected on
  **C's own caution against putting "cannot" in the title**. C's stated reason has since evaporated
  — it was that PN-44 resolved the ladder — but the word still overclaims, because PN-60 found
  budget closure *did* separate the arms at p = 0.001514. Something was seen, on a different
  construct. D's "bound" is precise where "cannot see" is not. T2 additionally names the paper's
  actual three-part structure, and **PN-62 does not touch it**: scoping the tail leaves PN-13's
  separations intact, and those are the only claim "ranks" rests on.
  **Abstract: reviewer D's A2** (249 words as proposed, 251 as adopted). It is the only one of the
  six that **already contains PN-62's control** — "a shape we show is set by the corpus rather than
  by the compression, since changing only the KV-cache dtype reproduces it" — written before that
  correction existed as a note and independently confirmed here hours later. It also drops the
  3.7-sigma lower endpoint that does not survive Bonferroni at design effect 1.5 (using 8.7-18.1
  instead), and carries **no MK-NIAH sentence**, which is what makes D's A3 unusable after PN-60.
  Reviewer C's A1 was the runner-up and led with PN-49's 36-fold protocol swing — the
  best-provenanced number in the corpus — but opens on a checkpoint that is not one of the paper's
  four arms and leads with a claim the chosen title does not name.
  **Three edits applied to A2 as adopted**: the KV-only control now cites **PN-62** rather than
  PN-15; **PN-49's 36-fold swing was added**, since A2 omitted the study's best-evidenced single
  result and C's A1 was right to lead with it; and the median ratio is stated as **181-206x** rather
  than "100-200x", per D-8 — PN-35's printed median row is wrong by 2x for two of three arms and
  must not be quoted until that note is superseded.
⚠️ Outstanding: **PN-35's median row is still misprinted in the note itself** (D-8), and the abstract
  now states the corrected figure while the note it derives from does not. That inconsistency must be
  closed by a superseding note before submission — the abstract is currently more correct than its
  own evidence line.
Next: rewrite OUTLINE §5 against the 63-note base — §5.2 loses its third instrument (PN-60), §5.1
  gains PN-62's shape/magnitude separation, and §Agentic behavior needs a section that does not yet
  exist. Then verify the PN-29 exposure and re-analyse speed conditioned on acceptance.

### L-26 | 2026-09-03T19:10:00Z | S13-verification | claude-opus-5 | conductor-manager | PN-35's median row verified, corrected, and found unrankable <!-- bsc-ledger:qbench-t1-PN35MED -->
Did: verified reviewer D's D-8 — the last unverified claim from either review — by recomputing all
  twenty cells of PN-35's quantile table from `ssa-kld-tables.json`.
Result (PN-64): **D-8 is confirmed, and the table is otherwise sound.** Eighteen of twenty cells
  reproduce exactly — every p90, p95, p99 and p99.9 across all three arms — and the crossover claim
  holds (p90 below unity at 0.449/0.541/0.613, p95 above it at 1.527/1.888/2.184). **Two of three
  median cells are wrong**: Q6_K prints `0.01x` for a measured **0.0050x** (2.0x overstated) and
  Q5_K_XL prints `0.01x` for **0.0055x** (1.8x); Q4_K_XL's `0.005x` is correct. The prose sentence
  "100-200x less at the median" is wrong at both ends — measured ratios are **199 / 181 / 206** —
  and the mechanism is visible: **100 is the reciprocal of the rounded 0.01x cell**, so the sentence
  was written from the rounded table rather than from the data.
  **Beyond D-8, and new here: the median row cannot rank the arms at all.** `llama-perplexity`
  prints six decimal places, so the code medians (0.000007 / 0.000010 / 0.000017) carry one to two
  significant figures. Half-ULP propagation gives 199 [185.6, 214.2], 181 [172.4, 190.5] and
  206 [200.5, 212.7] — **±7.2 %, ±5.0 %, ±2.9 % from print precision alone** — and Q6_K's interval
  overlaps both others. Only the Q5/Q4 pair separates, in the *non-monotone* direction. So even the
  corrected "181-206x" over-states resolution, and any per-arm ordering read off that row is a
  rounding artifact. The paper should say **"about 200x"** and not tabulate the median per arm.
  This is the study's own standing rule (G22) applied to its own headline table.
  `CITATION.cff`'s abstract carried "181-206x" from D-8; corrected to "about 200x" in the same
  commit. The tail finding is unaffected — median far below prose, crossover between p90 and p95,
  5.0-8.1x prose at p99, all verified. Withdrawn is a spuriously precise range and an ordering the
  instrument cannot resolve. Independent of **PN-62**, which scopes the tail's *interpretation*;
  both corrections apply.
Consequence: **no unverified reviewer claim remains.** The abstract, `CITATION.cff` and PN-35's
  evidence line now agree, closing the inconsistency L-25 flagged as outstanding.
Next: PN-29's DFlash2 at-depth cell is still unchecked for the PN-30 probe defect (it is cited in
  OUTLINE §5.4); re-analyse speed conditioned on draft acceptance; then draft the report.

### L-27 | 2026-09-03T20:15:00Z | S14-drafting | claude-opus-5 | conductor-manager | Drafting opens; authorship and scope recorded <!-- bsc-ledger:qbench-t1-DRAFT0 -->
Did: opened the drafting stage. Wrote `manuscript/DRAFTING-PLAN.md` as the process of record, and
  recorded two facts stated by the owner today that nothing in the repository carried.
New facts, now binding on the whole document:
  - **Authorship and scope.** The report is **solo-authored by Luiz Henrique Simões**, independent
    researcher, **professional master's candidate in Data Science and Analytics, Universidade de São
    Paulo (USP)**. It must state plainly — in the author block and again in §1 — that it is a
    technical report by an independent practitioner, **not a peer-reviewed paper from a university
    group or an AI lab**. The owner framed this as an honesty requirement, not a disclaimer to bury.
    No institutional "we"; no implied peer review.
  - **Density over compression.** Twelve-plus days of GPU time must be exercised technically. Prefer
    a full table with n, estimator, interval and protocol over a summarising sentence; give each
    substantive finding its own figure or table. Large and dense *and* readable.
  Both are also written to project memory so they survive session boundaries.
⚠️ **The gating item is endorsement, not writing.** Since 2026-01-21 arXiv no longer accepts an
  institutional email as sole qualifier for a new author in any category; auto-endorsement needs an
  institutional address **and** prior claimed authorship in the domain. A first-time solo author
  with a personal address has neither, so **personal endorsement is the only route** and arXiv staff
  cannot waive it. This is independent of drafting, takes weeks, and should start now. `cs` is a
  single endorsement domain, so any active `cs.*` author qualifies for `cs.LG`/`cs.PF`.
Resolved today: arXiv requires that code/data links resolve to a **publicly available** repository.
  Reviewer B flagged the private repository as a submission blocker; publication of
  `github.com/henrique-simoes/llm-quantization-damage` (L-25/L-26 work) clears it. Still outstanding
  for compliance: a **Zenodo DOI** and a **Software Heritage SWHID**, printed in a page-1 footnote
  and an *Artifact availability* section.
Compliance settled and not to be re-derived (source: reviewer B's submission research): primary
  `cs.LG`, one cross-list `cs.PF` (**not `cs.AI`** — arXiv defines it as excluding ML), ACM class
  `D.4.8; I.2.6`, **LaTeX source not PDF**, `.bib` direct since 2025-11-05, vector PDF for line
  plots, ≤ 50 MB and ≤ 34 megapixels per image, CC BY 4.0 (irrevocable per version), JSON artifacts
  as ancillary files under `anc/`.
Drafting order fixed as D0-D9, dependencies first: style guide and figures, then the LaTeX skeleton,
  then §3/§4 (the measurement contract), **then §7 threats before §5 results** — writing results
  first is how a section acquires claims the threats section must later retract — then §6/§8/§9,
  §2, and §1 last because it promises what §5 delivers.
Two agents dispatched in parallel: a visualisation architect designing the full figure and table
  programme as PaperBanana-consumable specs plus an `extract.py` that regenerates every data file
  from artifacts (PaperBanana is cloud-dependent and has no keys here, so the deliverable is
  render-ready inputs, not images); and a technical-writing consultant producing `STYLE-GUIDE.md`,
  whose hardest brief is how a solo practitioner report claims exactly the authority its evidence
  supports without either apologising or overclaiming.
Carried into the plan as open items drafting must not paper over: **PN-29's DFlash2 at-depth cell is
  still unverified** for the PN-30 defect and is cited in OUTLINE §5.4; the speed data still wants
  re-analysis conditioned on draft acceptance (free, and both reviewers found it independently); no
  multiple-comparisons correction exists across ~19 tests; and the honest artifact tier is
  **Artifacts Available only**, because every evidence chain ends in a gitignored serverlog.
Next: D1 once the style guide and figure programme land — LaTeX skeleton, then §3/§4.

### L-28 | 2026-09-03T21:30:00Z | S14-drafting | claude-opus-5 | conductor-manager | Style guide lands; four verified defects fixed in the outline <!-- bsc-ledger:qbench-t1-STYLE -->
Did: received `manuscript/STYLE-GUIDE.md` (2,004 lines, 97 sourced references) and **verified every
  structural and statistical claim it made about the outline before acting on any of them.** All
  confirmed; all fixed.
Result — four defects, one of which would have put a wrong number in the paper:
  1. ⚠️ **The outline's thesis paragraph still said "100–200×" at the median**, which **PN-64
     withdrew** hours earlier. Replaced with "roughly two orders of magnitude", plus an explicit
     prohibition on tabulating that row per arm — PN-64 showed two of three cells were overstated
     ~2×, the measured ratios are 199/181/206, and print precision (±3–7 %) leaves the intervals
     overlapping so the row cannot rank the arms. §5.1 also did not cite PN-64; it does now.
  2. ⚠️ **§5.2 quoted the HumanEval *base* row under a HumanEval+ label.** In evalplus `base` is
     HumanEval and `base+extra` is HumanEval+. The outline carried −0.61 pts [−2.68, +1.46] with
     3 discordant — that is the **base** row. The true HumanEval+ row is −0.61 pts **[−3.28, +2.06]**
     with **5** discordant. Both rows are now tabulated and labelled explicitly. Three different
     intervals for "the paired HumanEval+ difference" were circulating in the corpus; this is why.
  3. **The paper had no conclusion.** §7 ran straight into two appendices numbered as body sections.
     Added **§8 Conclusion**, and renumbered the appendices to **A** and **B** so they stop reading
     as results.
  4. **§5.2's heading said "Three instruments"** over text listing five. Retitled *"Every instrument
     bounds, none resolves"*, which is also the claim that survives PN-60.
⚠️ **New moderation risk, not in L-27's compliance table.** Since **2025-10-31** arXiv's `cs`
  categories refuse review and position papers without prior peer review. An assertive-thesis title
  over a long multi-thread background is the shape a moderator declines, so §2 now carries a **hard
  900-word cap** and a rule that every paragraph ends on what *this report measures differently*.
Positioning decisions adopted from the guide: **first-person singular "I", used sparingly and only
  for acts of judgement**; the default subject of a measurement sentence is the instrument or the
  number; the harness takes an agentless past; **"we/our/us" banned outright** — a plural voice for a
  one-person, one-host study is the same overclaim in the register that PN-40 corrects in the
  statistics. USP appears as a **qualification, never an affiliation**; the author block reads
  *Independent researcher*.
  The most useful finding for framing: the closest published comparator — arXiv:2601.14277, a solo
  llama.cpp quantization evaluation — has **no affiliation, no limitations section and no confidence
  intervals**, verified by PDF extraction. **This report is the strong entry in its genre, not the
  weak one**, and the drafting should stop hedging defensively.
Recorded but **NOT verified**, and must be checked before citing: three related-work items the guide
  says are missing — arXiv:2411.02355 (Kurtic et al., ACL 2025), arXiv:2607.08734 (Rababah et al.,
  2026), arXiv:2601.09527 (same GPU). Flagged inline in §2.
Next: the figure programme agent is still running. D1 (LaTeX skeleton) once it lands.

### L-29 | 2026-09-03T22:20:00Z | S14-drafting | claude-opus-5 | conductor-manager | Figure programme lands; a provenance gap and a multiplicity failure <!-- bsc-ledger:qbench-t1-FIGS -->
Did: received the figure and table programme — **28 figures, 23 tables, 38 data files (812 rows)**,
  all generated by an offline stdlib-only `extract.py` that is idempotent and exits 2 with named
  paths when an artifact is missing. Plus `TABLES.md` in publication form with n, estimator, interval
  and protocol **inside** each table, a `paperbanana/` directory with a ready-to-run 30-item
  `plots.yaml` and a venue style pack, and `RENDERING.md`. The specs were written against **verified**
  PaperBanana CLI facts read from its own README; the one asymmetry that could not be resolved
  (whether `plot` accepts `--venue`) is flagged rather than assumed, and nothing was installed or run.
  Essential five: **F1** divergence ladder × domain · **F2** the tail decomposition with its KV-only
  control · **F3** the instrument forest with minimum-attainable-p · **F4** ceiling × tensor-split ·
  **F5** speculation's speed-versus-identity trade.
Result — two findings verified here before acceptance, both consequential:
  **PN-65 — seven families of numbers existed in the repository only as prose.** Including the
  SWE-bench totals PN-50 reports and the README features as a headline. The committed
  `data/archive/ledger-data.json` carries `iq4_xs-verified50` at **36/47**, the superseded
  pre-ARM64-fix figure; the corrected **38/49** appeared nowhere except a sentence in the mirrored
  machine log. **A reader could not have verified the study's most expensive task-benchmark result
  from any committed file.** Identical to the defect PN-62 fixed for PN-35's quantiles — third
  instance of one failure mode, which makes it a finding. All seven now committed under
  `data/raw/historical/`: the live ledger as a dated snapshot (carrying `resolved: 38`,
  `source: "per-instance report.json"` and an explicit `eval_log_disagrees` block), the verified50
  per-instance manifest, both NVFP4 perplexity protocols, all seven thinking-mode HumanEval+ arms
  (**n=164 verified in each**), the T3 agentic step counts, the n8 throughput logs, and the energy,
  KL and bootstrap artifacts. The stale archive copy is **left unedited** per append-never-rewrite
  and must not be cited for SWE-bench.
  **PN-66 — PN-32 does not survive multiplicity once its pair count is repaired.** Two of its
  "13 adjacent pairs" skip a rung, so the test is **10 of 11**, exact one-sided *p* = **0.00586**
  (recomputed; the as-written 12/13 gives 0.00171, matching PN-32's printed figure and confirming it
  reports a one-sided p). Holm thresholds at m=19 are 0.00500 / 0.00556 / 0.00625 at ranks 10/11/12
  — **it fails at ranks 10 and 11 and passes only at rank 12**. Two-sided it is 0.01172 and fails
  everywhere. Compounds reviewer D's separate objection that the statistic is near-tautological.
  **All nine divergence separations (PN-13) pass both Holm and BH** and are untouched.
Recorded, **not yet verified**, from the extraction pass: the cost contrast has moved again — 2.32 h
  divergence against **14.31 h** task benchmarking (**6.2×**), because PN-41 predates the 9.4-hour
  MK-NIAH cell; **PN-38's pairwise edit distances do not reproduce** under any of four normalisations
  (its note states none), though its conclusion does; PN-29's DFlash2 first-divergence median is 730
  in the artifact against 722.5 recomputed. Each needs checking before it reaches the paper.
  Also: **PN-43's label collision bit the extractor itself** — indexing `ssa-results-parsed.json` by
  label silently returned the f16 cell. Fixed by keying on (label, kv), with the corrupted field
  emitted alongside and marked DO NOT USE. The defect register is now self-demonstrating.
Where the data cannot support a figure the outline wants: no divergence at deployment depth (S10
  infeasible, S11's metric failed structurally); **no retrieval result at 131,072** — PN-60 leaves it
  *unanswered*, not negative; no accuracy-vs-context for any arm; nothing at temperature > 0; no
  per-arm best draft depth; UD-Q4_K_XL has no repetition group at 262,144.
Next: verify the three unverified items above, then D1 — the LaTeX skeleton.
