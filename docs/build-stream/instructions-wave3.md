# Wave 3 — Accuracy instruments, agentic runs, context axis

Implementer for Wave 3. Durable plan: `docs/build-stream/2026-08-30-quant-bench-trackA.md`
(Phases 6–8). Paper-notes duty: `docs/paper/PAPER-NOTES-PROTOCOL.md`. All prior hard rules
apply. Official sampling settings for ALL task benchmarks (DEC-2); greedy only for
logprob-based instruments.

## Tasks
1. **PPL Protocol 1 for UD-Q6_K** (missing cell): exact Protocol-1 windows from
   `/srv/bench/corpus/wikitext2-test.txt`, never mixed with other protocols in tables.
2. **Code-NLL ladder (protocol-4, labelled)**: final 256 tokens of django code prefixes at
   {32K, 64K, 128K, CTX_MAX} × {f16 where it fits, q4_0} × 3 quants — the E2 KV-fidelity
   decision rule (ΔNLL ≤3 % + divergence ≤6/256 at 98K) decides q4_0 adoption per quant.
3. **HumanEval+ gap-fill**: UD-Q6_K non-thinking (official settings). Full 164.
4. **LiveCodeBench v6, n=100 subset**: set up harness (pilot of 5 problems must pass
   validate-v2 first), run 3 quants, compare vs official 90.3 with CIs.
5. **SWE-bench Verified**: 25-instance stratified smoke FIRST (repo-balanced), Wilson CIs;
   only after smoke review → 50-instance stratified run. Per-instance report.json
   manifests via `swebench_agg.py` conventions; empty-patch counts recorded.
6. **Agentic steps** (T3-style, 3 instances × 3 quants).
7. **Code-NIAH** (E3): 6 depths {10,25,50,75,90,99} % × 2 needle classes × 3 seeds on the
   rebalanced configs; real django padding only; per-depth Wilson CIs; class-(ii) ≥90 % at
   90 % depth gate.

## Finish contract additions
Ledger + PN notes (§Quant ladder, §Agentic behavior, §Context axis, §Reproducibility).

## Standing rule — synchronization (owner directive 2026-08-30)
Everything produced on multivac MUST exist in this repo's `data/` tree, always. At the end
of every stage: `bash tools/sync-multivac.sh both` (pushes `experiments/` to
multivac:/srv/bench/e12/, pulls docs + artifacts + server logs into `data/`). Include the
sync result in your ledger entry's Verified field. The detached watcher also pulls every
10 minutes, but the worker-side sync at stage end is the contract — never rely on it.
