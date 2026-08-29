# Wave 1 — Harness validation, disk sweep, bring-up + `-ts` rebalance sweeps

You are the implementer for Wave 1 of the multivac Track A quant-benchmark plan.
The durable plan is `docs/build-stream/2026-08-30-quant-bench-trackA.md` (read Phase 1–3
sections first). The paper-notes duty is `docs/paper/PAPER-NOTES-PROTOCOL.md`.

## Hard rules (owner-mandated, non-negotiable)
1. **Small tests before big tests.** Every new script first runs a 5-task / 32K-context /
   ~64-token pilot and must pass `experiments/validate_v2.py` before any full run. A full
   run without a passing pilot in the ledger is a process violation.
2. **Save all logs BEFORE any teardown or deletion.** Every llama.cpp container goes down
   only via the orchestrator `kill_server` convention (docker logs →
   `/srv/bench/server-timings/<label>.serverlog` first). Before any file/model/image
   deletion: sha256+size manifest appended to `/srv/bench/env-manifest.json`, ledger entry
   written, paper notes appended. Deletion order is: docs updated → manifest → delete.
3. **Launch contract on every server**: `-fit off` asserted via `/props` `n_ctx` == requested;
   explicit sampling (never rely on server defaults); thinking control verified (2-token
   probe); image id + seed + sampling settings recorded in the artifact.
4. **Bracket + re-test every marginal VRAM rung** (±100–200 MiB layer-split noise).
5. Official sampling settings (owner decision 2026-08-30, DEC-2):
   - Non-thinking: temp 0.7, top_p 0.80, top_k 20, min_p 0.0, presence_penalty 1.5, repetition_penalty 1.0
   - Thinking: temp 1.0, top_p 0.95, top_k 20, min_p 0.0, presence_penalty 0.0
   - Greedy (temperature 0) remains the instrument for PPL/NLL/divergence work only.

## Tasks (detailed acceptance criteria in the lifecycle file, Phases 1–3)
1. **validate_v2.py** under `experiments/`: launch contract + sampling contract + thinking
   control + provenance capture, with a `--selftest` negative-control mode that MUST catch
   4 seeded fault configs (ctx-shrink via -fit on; thinking-ON leak; sampling-defaults leak;
   missing model field in request). Deploy to `multivac:/srv/bench/e12/validate_v2.py`.
2. **Disk sweep** per the lifecycle delete list (IQ4_XS GGUF, Q6_K_XL GGUF, NVFP4 hf-cache
   duplicate, vLLM stable+nightly images; KEEP /srv/engines/nvfp4, all 3 active quants,
   DFlash2 drafter, llama.cpp images, telemetry, all results). Rule 2 applies strictly.
   Target: ≥60 GB free on /srv/models, ≥55 GB on /.
3. **Bring-up + ts sweeps** (`experiments/tsweep_v2.sh`): for each of UD-Q4_K_XL,
   UD-Q5_K_XL, UD-Q6_K with MTP n=2 + q4_0 KV + `-sm layer`: full ratio sweep
   {default, 54,46, 56,44, 58,42, 60,40, 62,38} at the rung above the known ceiling, then
   bracket the true ceiling (descend until success, re-test the rung above). Record per
   cell: image id, ctx requested/reported, ok/err, per-GPU VRAM after ≥90 % prefill,
   prefill/decode tok/s, acceptance, imbalance. Artifacts: `/srv/bench/e12/tsweep-v2-*.json`,
   pulled back to `data/raw/e12/`.

## Finish contract additions
- Ledger entry per the conductor protocol (`docs/build-stream/...` file, L-<n> format).
- Append at least one PN-<n> entry to `docs/paper/PAPER-NOTES.md` if any measurement or
  systems finding emerged (e.g. ts-rebalance deltas, ceiling corrections vs G21).
- Update the roadmap Status column in the lifecycle file.

## Standing rule — synchronization (owner directive 2026-08-30)
Everything produced on multivac MUST exist in this repo's `data/` tree, always. At the end
of every stage: `bash tools/sync-multivac.sh both` (pushes `experiments/` to
multivac:/srv/bench/e12/, pulls docs + artifacts + server logs into `data/`). Include the
sync result in your ledger entry's Verified field. The detached watcher also pulls every
10 minutes, but the worker-side sync at stage end is the contract — never rely on it.
