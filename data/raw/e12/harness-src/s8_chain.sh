#!/bin/bash
# s8_chain.sh — run the merged spec-decode test after S7 releases the GPU.
# Same contract as supervisor.sh: a failing phase is LOGGED and SKIPPED, the chain continues,
# every phase writes its own log, and results are pushed to the git hub as they land.
set -uo pipefail
E12=/srv/bench/e12
PY=/srv/bench/.venv-evalplus/bin/python
REPO=$HOME/repos/multivac-paper
LOG=$E12/logs/s8_chain.log
mkdir -p "$E12/logs" "$E12/state" "$E12/s8"
exec 9>"$E12/state/s8.lock"
flock -n 9 || { echo "REFUSING: another s8 chain holds the lock"; exit 3; }
say(){ echo "[$(date -u +%FT%TZ)] $*" | tee -a "$LOG"; }

sync_git() {
  { mkdir -p "$REPO/data/raw/e12/s8"
    for f in "$E12"/s8/*.json "$E12"/s8/*.txt; do
      [ -f "$f" ] && [ "$(stat -c%s "$f")" -lt 5000000 ] && cp -f "$f" "$REPO/data/raw/e12/s8/" 2>/dev/null
    done
    for f in "$E12"/logs/s8*.log; do
      [ -f "$f" ] && cp -f "$f" "$REPO/data/raw/e12/logs/" 2>/dev/null
    done
    cd "$REPO" && git add -A >/dev/null 2>&1
    git diff --cached --quiet 2>/dev/null || {
      git commit -q -m "data(s8): autonomous sync — $1" >/dev/null 2>&1
      git pull -q --rebase origin main >/dev/null 2>&1 || true
      git push -q origin main >/dev/null 2>&1 && say "  git: pushed ($1)" || say "  git: push deferred ($1)"
    }
  } || say "  git: sync errored ($1) — ignored"
  return 0
}

say "s8_chain pid $$ waiting for S7 / any GPU work to finish"
w=0
while pgrep -f "ssa_s7\.py|llama-perplexity|ssa_kld\.py|tsweep_v2\.py" >/dev/null 2>&1; do
  sleep 60; w=$((w+60))
  [ $((w % 900)) -eq 0 ] && say "  still waiting (${w}s)"
  [ $w -gt 14400 ] && { say "GIVING UP after 4 h"; exit 5; }
done
say "GPU free after ${w}s"
sleep 30

for phase in humaneval score atdepth; do
  say "=== PHASE $phase START ==="
  $PY "$E12/experiments/s8_spec.py" --phase "$phase" > "$E12/logs/s8_$phase.log" 2>&1
  rc=$?
  if [ $rc -eq 0 ]; then
    date -u +%FT%TZ > "$E12/state/s8_$phase.done"
    say "=== PHASE $phase OK ==="
  else
    date -u +%FT%TZ > "$E12/state/s8_$phase.failed"
    say "=== PHASE $phase FAILED rc=$rc — logged and SKIPPED, chain continues ==="
    tail -5 "$E12/logs/s8_$phase.log" 2>/dev/null | sed 's/^/      /' | tee -a "$LOG"
  fi
  sync_git "after s8 $phase"
done

say "=== S8 CHAIN COMPLETE ==="
say "phases: $(ls "$E12/state" | grep -c '^s8_.*\.done') done, $(ls "$E12/state" 2>/dev/null | grep -c '^s8_.*\.failed') failed"
exit 0
