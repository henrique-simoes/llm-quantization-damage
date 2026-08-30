# `data/` — mirrors and pulled evidence

Nothing in this directory is authored here. Two kinds of content, and the distinction matters:

| path | what | who owns it |
|---|---|---|
| `multivac-src/` | **read-only mirrors** of documents multivac owns — refreshed by `tools/sync-multivac.sh pull`, and any local edit is destroyed on the next pull | multivac |
| `raw/` | evidence pulled from `/srv/bench/` as it is cited — artifacts, serverlogs, quarantine registers, a read-only copy of the harness source | multivac (pulled selectively) |
| `watch/`, `orchestrator/`, `experiment-reports/`, loose `*.json` / `*.txt` | historical run data from earlier waves | multivac |

## Two naming rules, both load-bearing

1. **No file in this repository may be named `CLAUDE.md` except the one at the root.** Claude Code
   discovers `CLAUDE.md` by name and merges what it finds into an agent's instructions. multivac's
   machine documentation is a 79 KB engineering log, not instructions for this repo, so it is
   mirrored as `multivac-src/multivac-CLAUDE.md`. The root `CLAUDE.md` is the agent guide and the
   only one that governs.
2. **One copy of each mirrored document.** `PAPER-REFERENCES.md` previously existed three times —
   repo root, `data/`, and `data/multivac-src/` — and the root copy had silently gone stale by
   25 KB. Mirrors live at exactly one path: `multivac-src/`.

## Editing

Don't. Edit multivac's copy over ssh and `pull`, or edit `docs/` here and `push`. See the
ownership table in the root `CLAUDE.md` §1 — getting this backwards has nearly destroyed work twice.
