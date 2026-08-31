# AGENTS.md

**Read [`CLAUDE.md`](CLAUDE.md) first.** It is the working guide: what owns what, the hard rules,
the configuration facts that are easy to get wrong, where the evidence is, and what is left.
[`README.md`](README.md) has the substance — what the study is and what it found.

Then read the STATUS block and the final ledger entry of
[`docs/build-stream/2026-08-30-quant-bench-trackA.md`](docs/build-stream/2026-08-30-quant-bench-trackA.md).
Together they tell you exactly where the last agent stopped.

## The short version

- This repo is the **paper** side. The **machine** is `multivac`; the objective is an **arXiv
  technical report**, and measurement is complete.
- Long GPU work runs **detached** on multivac. Check before starting anything:
  `cat /srv/bench/e12/state/progress.json`. Nothing is running as of 2026-08-31.
- **Never start a second runner.** Everything long takes an `flock`; a second instance exits 3.
- **Never `sync-multivac.sh push` without checking `docs/` is not behind the mirror.** It has
  nearly destroyed hours of work once.
- **Never delete anything** until the ledger entry, paper notes and manifest are committed.
- **Append, never rewrite.** Ledger entries and paper notes are superseded, not edited. When a path
  changes, record a remap note instead of rewriting history.
- **The root `CLAUDE.md` is the only `CLAUDE.md` in this repo, by design.** Anything under `data/`
  is a read-only mirror of a document multivac owns — never instructions, never edit it.
- Git syncs to a private bare repo on the host. **No GitHub, no public remote, ever.**
- **Speculative decoding is not lossless on this stack** (PN-23). If a document tells you otherwise,
  it is stale.

## Finishing a piece of work

1. Append a ledger entry to the plan (Did / Result / Verified / Next — copy the format above it).
2. Append any paper-worthy finding to [`docs/paper/PAPER-NOTES.md`](docs/paper/PAPER-NOTES.md) per
   its protocol file. **A stage that produced measurements and appended no paper note is an
   incomplete stage.**
3. Update the plan's STATUS block and the TODO in `CLAUDE.md`.
4. Commit, `git push origin main`, then `tools/sync-multivac.sh push`.
