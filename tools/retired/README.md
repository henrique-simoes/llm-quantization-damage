# `tools/retired/` — the Compass Forge conductor subsystem

A multi-agent orchestration pipeline ("conductor") drove the planning waves of this study. It
**halted on 2026-08-30T01:57Z** with `VERDICT-REPAIR-EXHAUSTED` and was deliberately not restarted
(DEC-8): the remaining work finished hand-driven, and restarting mid-sweep risked a second runner
and GPU-lock contention. Its state directory `.compass-forge/` is gone and the watcher process is
dead.

Everything it needed is grouped here so the rest of the tree reflects only live tooling. Nothing is
deleted — the run is part of the project's history and `docs/build-stream/CONDUCTOR-HANDOFF.md`
documents how it worked.

| file | role |
|---|---|
| `watch-qbench.sh` | detached watcher: tailed `conductor.log`, wrote transitions, ran the 10-minute docs pull |
| `parse_tick.py` | one conductor tick line → shell-safe `KEY=VALUE` |
| `recipes/generic/recipe.toml` | conductor role definitions (implementer, reviewer, fixer, architects) |
| `watch-state/` | the watcher's own output: `events.log`, `state.json`, `sync.log`, `watcher.pid` |

**Path remap** (moved 2026-08-31; older ledger entries and `CONDUCTOR-HANDOFF.md` use the originals):

    tools/watch-qbench.sh  ->  tools/retired/watch-qbench.sh
    tools/parse_tick.py    ->  tools/retired/parse_tick.py
    recipes/               ->  tools/retired/recipes/
    data/watch/            ->  tools/retired/watch-state/

⚠️ `watch-state/state.json` reads `health: VERDICT-REPAIR-EXHAUSTED`. That describes a pipeline
that no longer reflects the work. It is a frozen artifact, not a status —
`docs/build-stream/2026-08-30-quant-bench-trackA.md` is the status of record.

One standing item survives the retirement: the conductor's stale reviewer task
(`REREV-NV2-…-REVIEW-r1`) was never resolved or formally retired.
