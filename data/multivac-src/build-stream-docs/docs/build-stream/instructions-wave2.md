# Wave 2 — Official-settings validation + MTP/DFlash setting sweeps

Implementer for Wave 2. Durable plan: `docs/build-stream/2026-08-30-quant-bench-trackA.md`
(Phases 4–5). Paper-notes duty: `docs/paper/PAPER-NOTES-PROTOCOL.md`. All Wave 1 hard rules
apply (small-tests-first, logs-before-teardown, launch contract, bracket+re-test).

## Tasks
1. **Official-settings validation pilots (small, cheap, before any big battery):**
   a. `enable_thinking:false` vs `{"reasoning_effort":"none"}` equivalence probe (closes G17)
      — 5 HumanEval tasks, token counts + empties compared.
   b. MTP + temp>0 losslessness probe (closes G8): identical prompt, greedy vs official
      non-thinking sampling, draft-mtp n=2, first-divergence token + exact-match rate. If
      divergence appears at temp>0, accuracy benchmarks that use spec decode must either run
      no-spec or re-prove equivalence — record which.
   c. presence_penalty 1.5 behavior on code: 5-task probe, note any degeneration (this is
      informational — the owner has FIXED official settings as the benchmark arm).
2. **MTP sweep** per quant (Q4_K_XL, Q5_K_XL, Q6_K) at the rebalanced config from Wave 1:
   depth n ∈ {1,2,4,8} at ctx 32,768; n ∈ {2,4} at full-depth (≥90 % window filled);
   draft-KV `-ctkd/-ctvd` ∈ {f16, q4_0} (documented axis, default f16 — tests whether draft
   KV quantization reclaims window); p-min ∈ {0.0, 0.1} at n=2 only. 3-run medians,
   acceptance + mean-accepted-length recorded. Artifacts `/srv/bench/e12/mtp-sweep-*.json`.
3. **DFlash2 sweep** on `llama-dflash2:latest` (--entrypoint /app/llama-server): n-max ∈
   {4,7,8} at 32,768; n=4 at full-depth; acceptance collapse at depth re-measured on the
   surviving image. Artifacts `/srv/bench/e12/dflash-sweep-*.json`.
4. Do NOT stack ngram-cache with MTP (measured −23 %, historical).

## Finish contract additions
Ledger entry + PN notes (expected: draft-KV window reclaim, MTP-vs-DFlash per-context
ranking on the surviving image, losslessness-at-temp>0 verdict for §Speculative decoding).

## Standing rule — synchronization (owner directive 2026-08-30)
Everything produced on multivac MUST exist in this repo's `data/` tree, always. At the end
of every stage: `bash tools/sync-multivac.sh both` (pushes `experiments/` to
multivac:/srv/bench/e12/, pulls docs + artifacts + server logs into `data/`). Include the
sync result in your ledger entry's Verified field. The detached watcher also pulls every
10 minutes, but the worker-side sync at stage end is the contract — never rely on it.
