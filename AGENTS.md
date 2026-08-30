# AGENTS.md

**Read [`CLAUDE.md`](CLAUDE.md) before doing anything in this repository.** It is the orientation
document: what this project is, which file owns which document, the hard rules, the current state
of the work, and the TODO list through to completion.

Then read the STATUS block and the final ledger entry of
[`docs/build-stream/2026-08-30-quant-bench-trackA.md`](docs/build-stream/2026-08-30-quant-bench-trackA.md).
Together those tell you exactly where the last agent stopped and what comes next.

## The short version

- This repo is the **paper and planning** side. The **machine** is `ssh multivac`.
- Long GPU work runs **detached** on multivac and is **already running** — check before you start
  anything: `ssh multivac 'cat /srv/bench/e12/state/progress.json'`.
- **Never start a second runner.** Everything long takes an `flock`; a second instance exits 3.
- **Never `sync-multivac.sh push` without first checking `docs/` is not behind the mirror.**
  It has nearly destroyed hours of work once. `CLAUDE.md` §1 has the command.
- **Never delete anything** until the ledger entry, paper notes and manifest are committed.
- **Append, never rewrite.** Ledger entries and paper notes are superseded, not edited.
- Git syncs to a private bare repo on multivac. **No GitHub, no origin, never public.**

## Finishing a piece of work

1. Append a ledger entry to the plan (Did / Result / Verified / Next — copy the format above it).
2. Append any paper-worthy finding to `docs/paper/PAPER-NOTES.md` per its protocol file.
3. Update the STATUS block and the TODO in `CLAUDE.md`.
4. Commit, then `git push multivac main`, then `tools/sync-multivac.sh push`.

A stage that produced measurements but appended no paper note is an incomplete stage.
