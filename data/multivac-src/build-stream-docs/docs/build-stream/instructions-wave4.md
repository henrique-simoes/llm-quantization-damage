# Wave 4 — Speed/energy at chosen config, Track A decision procedure, docs

Implementer for Wave 4. Durable plan: `docs/build-stream/2026-08-30-quant-bench-trackA.md`
(Phases 9–10). Paper-notes duty: `docs/paper/PAPER-NOTES-PROTOCOL.md`.

## Tasks
1. **Speed + energy at the chosen config per quant** (`experiments/speed_curve_v2.py`):
   filled-context ladder {4K, 40K, 98K, CTX_MAX}, 3-run medians, decode AND prefill at each
   depth (always labelled depth-0 vs at-depth), J/tok from 1 Hz power-log integration
   (method §13.73). Run the queued-but-never-executed speed-curve design (G14).
2. **Track A decision procedure** (lifecycle §TRACK A): one config line per quant
   (accuracy → context → tok/s) + fallback ladder, applying the E2/E3/E5-style gates and CI
   separation rules; "indistinguishable at n=" statements where CIs overlap.
3. **Track B data assembly**: verify every artifact has source/run_ids/image-id/seed/
   sampling fields; PPL protocols segregated; irreproducible rows labelled.
4. **Docs graduation**: update CLAUDE.md (multivac) + PAPER-REFERENCES.md with final
   config lines, sweep results, closed gaps (G13/G14/G15/G16-partial/G17/G21/G8);
   PAPER-NOTES.md reviewed for completeness (every headline number has a PN entry).

## Finish contract additions
Ledger + PN notes (§Efficiency, §Systems findings, §Reproducibility) + the final config
lines as PN entries marked "Use as: Track A headline".

## Standing rule — synchronization (owner directive 2026-08-30, narrowed same day)
`tools/sync-multivac.sh` synchronizes DOCUMENTATION ONLY: CLAUDE.md, PAPER-REFERENCES.md,
the multivac paper-data folder, and this repo's docs. It does NOT sync artifact trees,
models, or containers (owner clarification 2026-08-30). Run `bash tools/sync-multivac.sh
both` at every stage end (result goes in the ledger Verified field). Individual artifacts
needed as paper evidence are pulled selectively:
`bash tools/sync-multivac.sh artifact /srv/bench/e12/<file>.json data/raw/<phase>/`.
Always run it BEFORE any deletion or container teardown (docs first, then manifest, then delete).
