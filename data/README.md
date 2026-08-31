# `data/` — evidence and mirrors

Nothing in this directory is authored here. Three kinds of content, and the distinction matters:

| path | what | owner |
|---|---|---|
| `raw/e12/` | **current evidence** — artifacts, logs, quarantine registers, and a read-only copy of the harness source, pulled from `/srv/bench/` as it is cited | multivac (pulled selectively) |
| `archive/` | **historical evidence** predating the E12 harness. Superseded on every axis E12 touches, never deleted — see `archive/README.md` for the two warnings that travel with it | multivac |
| `multivac-src/` | **read-only mirrors** of documents multivac owns, refreshed by `tools/sync-multivac.sh pull`; any local edit is destroyed on the next pull | multivac |

## Naming rules, both load-bearing

1. **No file here may be named `CLAUDE.md`.** Claude Code discovers that name anywhere in the tree
   and merges what it finds into an agent's instructions. multivac's machine documentation is a
   79 KB engineering log, not instructions for this repo, so it is mirrored as
   `multivac-src/multivac-CLAUDE.md`. The root `CLAUDE.md` is the only one that governs.
2. **One copy of each mirrored document.** `PAPER-REFERENCES.md` once existed three times and the
   root copy had silently gone stale by 25 KB. Mirrors live at exactly one path: `multivac-src/`.

## The mirror loop, closed 2026-08-31

`multivac-src/build-stream-docs/` held this repo's own `docs/`, pushed to multivac and pulled back
— 12 files diverging by up to 12 KB from the originals two directories away. Removed, and
`sync-multivac.sh pull` now prunes that path. **If it reappears, the exclusion has been lost.**

## Path remap

Loose files were consolidated into `archive/` on 2026-08-31. Ledger entries and paper notes written
before then use the old paths; `archive/README.md` maps every one. Earlier still, PN-1…PN-4 cite
`data/bench/e12/…`, which never existed in this repo — read it as `data/raw/e12/…`.

## Editing

Don't. Edit multivac's copy over ssh and `pull`, or edit `docs/` here and `push`. See the ownership
table in the root `CLAUDE.md` §2 — getting this backwards has nearly destroyed work twice.
