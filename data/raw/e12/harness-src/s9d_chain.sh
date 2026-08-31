#!/bin/bash
# s9d_chain.sh — the MTP draft-depth sweep, queued BEHIND the running s9 chain.
#
# WHY A SEPARATE SCRIPT: s9_chain.sh is executing right now. bash reads a script lazily, by
# byte offset, so appending a phase to a running script can make it resume mid-token and do
# something arbitrary. The running chain is never touched; this queues behind it instead.
#
# SEQUENCING: two locks.
#   s9d.lock  non-blocking  -> only one depth sweep may exist
#   s9.lock   BLOCKING      -> the same lock s9_chain.sh holds for its whole run, so this
#                              waits for that chain to finish and then holds it, which also
#                              stops anything else from starting a GPU runner underneath us.
# There is no polling for "is the GPU free" and no sleep-and-hope: the wait is on the lock,
# which is the condition itself (hard rule 8).
set -uo pipefail
E12=/srv/bench/e12
PY=/srv/bench/.venv-evalplus/bin/python
REPO=$HOME/repos/multivac-paper
LOG=$E12/logs/s9d_chain.log
mkdir -p "$E12/logs" "$E12/state" "$E12/s9"
say(){ echo "[$(date -u +%FT%TZ)] $*" | tee -a "$LOG"; }

exec 8>"$E12/state/s9d.lock"
flock -n 8 || { echo "REFUSING: another s9d chain holds the lock"; exit 3; }

sync_git() {
  { mkdir -p "$REPO/data/raw/e12/s9"
    for f in "$E12"/s9/*.json "$E12"/s9/*.jsonl; do
      [ -f "$f" ] && [ "$(stat -c%s "$f")" -lt 5000000 ] && cp -f "$f" "$REPO/data/raw/e12/s9/" 2>/dev/null
    done
    for f in "$E12"/logs/s9*.log; do
      [ -f "$f" ] && cp -f "$f" "$REPO/data/raw/e12/logs/" 2>/dev/null
    done
    cp -f "$E12/experiments/s9d_depthsweep.py" "$REPO/data/raw/e12/harness-src/" 2>/dev/null
    cp -f "$E12/s9d_chain.sh"                  "$REPO/data/raw/e12/harness-src/" 2>/dev/null
    cd "$REPO" && git add -A >/dev/null 2>&1
    git diff --cached --quiet 2>/dev/null || {
      git commit -q -m "data(s9d): autonomous sync — $1" >/dev/null 2>&1
      git pull -q --rebase origin main >/dev/null 2>&1 || true
      git push -q origin main >/dev/null 2>&1 && say "  git: pushed ($1)" || say "  git: push deferred ($1)"
    }
  } || say "  git: sync errored ($1) — ignored"
  return 0
}

say "s9d_chain pid $$ queued — waiting on s9.lock (the s9 chain must finish first)"
t0=$(date +%s)
exec 9>"$E12/state/s9.lock"
flock 9                                  # BLOCKS until s9_chain.sh releases it
say "s9.lock acquired after $(( $(date +%s) - t0 ))s — s9 chain is done, starting the sweep"
sleep 20                                 # let the last container's teardown settle

if [ -f "$E12/state/s9d_sweep.done" ]; then
  say "=== sweep already done — nothing to do (idempotent) ==="
  exit 0
fi

say "=== PHASE s9d_sweep START (24 cells, ~3.5-4 h) ==="
$PY "$E12/experiments/s9d_depthsweep.py" > "$E12/logs/s9d_sweep.log" 2>&1
rc=$?
if [ $rc -eq 0 ]; then
  date -u +%FT%TZ > "$E12/state/s9d_sweep.done"
  say "=== PHASE s9d_sweep OK ==="
  grep -E "ACCEPTANCE:|BEST-N:|done:" "$E12/logs/s9d_sweep.log" | sed 's/^/      /' | tee -a "$LOG"
else
  date -u +%FT%TZ > "$E12/state/s9d_sweep.failed"
  say "=== PHASE s9d_sweep FAILED rc=$rc — logged, see s9d_sweep.log ==="
  tail -12 "$E12/logs/s9d_sweep.log" 2>/dev/null | sed 's/^/      /' | tee -a "$LOG"
fi
sync_git "after s9d sweep"

say "=== S9D CHAIN COMPLETE ==="
exit 0
