#!/bin/bash
# s9_chain.sh — the DEC-12 retained experiment set, run unattended.
#
# Contract, same as supervisor.sh and s8_chain.sh: one runner at a time (flock), a failing
# phase is LOGGED and SKIPPED rather than stopping the chain, every phase writes its own log,
# and results are committed and pushed to the git hub as they land.
#
# HARD GATE: the pilot must pass before any battery runs. It costs ~6 min and catches the S8
# failure class (a drafter that cannot load on the image it was given) instead of discovering
# it four hours in. If the pilot fails, the chain STOPS — that is the one case where
# continuing is wrong, because every downstream phase would be measuring the same broken thing.
set -uo pipefail
E12=/srv/bench/e12
PY=/srv/bench/.venv-evalplus/bin/python
REPO=$HOME/repos/multivac-paper
LOG=$E12/logs/s9_chain.log
mkdir -p "$E12/logs" "$E12/state" "$E12/s9"
exec 9>"$E12/state/s9.lock"
flock -n 9 || { echo "REFUSING: another s9 chain holds the lock"; exit 3; }
say(){ echo "[$(date -u +%FT%TZ)] $*" | tee -a "$LOG"; }

sync_git() {
  { mkdir -p "$REPO/data/raw/e12/s9"
    for f in "$E12"/s9/*.json "$E12"/s9/*.jsonl; do
      [ -f "$f" ] && [ "$(stat -c%s "$f")" -lt 5000000 ] && cp -f "$f" "$REPO/data/raw/e12/s9/" 2>/dev/null
    done
    for f in "$E12"/logs/s9*.log; do
      [ -f "$f" ] && cp -f "$f" "$REPO/data/raw/e12/logs/" 2>/dev/null
    done
    cp -f "$E12/experiments/s9_final.py" "$REPO/data/raw/e12/harness-src/" 2>/dev/null
    cp -f "$E12/s9_chain.sh"             "$REPO/data/raw/e12/harness-src/" 2>/dev/null
    cp -f "$E12/experiments/lib_e12.py"  "$REPO/data/raw/e12/harness-src/" 2>/dev/null
    cd "$REPO" && git add -A >/dev/null 2>&1
    git diff --cached --quiet 2>/dev/null || {
      git commit -q -m "data(s9): autonomous sync — $1" >/dev/null 2>&1
      git pull -q --rebase origin main >/dev/null 2>&1 || true
      git push -q origin main >/dev/null 2>&1 && say "  git: pushed ($1)" || say "  git: push deferred ($1)"
    }
  } || say "  git: sync errored ($1) — ignored"
  return 0
}

say "s9_chain pid $$ starting (DEC-12 retained set: determinism, s6, dflash)"

# wait for any GPU work to clear — never contend
w=0
while pgrep -f "s8_spec\.py|ssa_s7\.py|llama-perplexity|ssa_kld\.py|tsweep_v2\.py" >/dev/null 2>&1; do
  sleep 60; w=$((w+60))
  [ $((w % 900)) -eq 0 ] && say "  still waiting for GPU (${w}s)"
  [ $w -gt 14400 ] && { say "GIVING UP after 4 h of waiting"; exit 5; }
done
[ $w -gt 0 ] && say "GPU free after ${w}s"

# ---- hard gate ------------------------------------------------------------
say "=== PILOT START (hard gate) ==="
$PY "$E12/experiments/s9_final.py" --phase pilot > "$E12/logs/s9_pilot.log" 2>&1
rc=$?
if [ $rc -ne 0 ]; then
  date -u +%FT%TZ > "$E12/state/s9_pilot.failed"
  say "=== PILOT FAILED rc=$rc — CHAIN STOPS. Nothing downstream would be trustworthy. ==="
  tail -20 "$E12/logs/s9_pilot.log" 2>/dev/null | sed 's/^/      /' | tee -a "$LOG"
  sync_git "s9 pilot FAILED"
  exit 4
fi
date -u +%FT%TZ > "$E12/state/s9_pilot.done"
say "=== PILOT OK ==="
sync_git "after s9 pilot"

# ---- batteries ------------------------------------------------------------
# Order is deliberate: determinism first because it is the cheapest and it changes how PN-23
# is written; dflash last because it is the one most likely to fail on a load.
for phase in determinism s6 dflash; do
  if [ -f "$E12/state/s9_$phase.done" ]; then
    say "=== PHASE $phase already done — skipping (idempotent) ==="
    continue
  fi
  say "=== PHASE $phase START ==="
  $PY "$E12/experiments/s9_final.py" --phase "$phase" > "$E12/logs/s9_$phase.log" 2>&1
  rc=$?
  if [ $rc -eq 0 ]; then
    date -u +%FT%TZ > "$E12/state/s9_$phase.done"
    say "=== PHASE $phase OK ==="
  else
    date -u +%FT%TZ > "$E12/state/s9_$phase.failed"
    say "=== PHASE $phase FAILED rc=$rc — logged and SKIPPED, chain continues ==="
    tail -8 "$E12/logs/s9_$phase.log" 2>/dev/null | sed 's/^/      /' | tee -a "$LOG"
  fi
  sync_git "after s9 $phase"
done

# ---- scoring (CPU only, no GPU contention) --------------------------------
say "=== PHASE score START ==="
if bash "$E12/s9_score.sh" > "$E12/logs/s9_score.log" 2>&1; then
  date -u +%FT%TZ > "$E12/state/s9_score.done"; say "=== PHASE score OK ==="
else
  date -u +%FT%TZ > "$E12/state/s9_score.failed"; say "=== PHASE score FAILED — see log ==="
  tail -8 "$E12/logs/s9_score.log" 2>/dev/null | sed 's/^/      /' | tee -a "$LOG"
fi
sync_git "after s9 score"

say "=== S9 CHAIN COMPLETE ==="
say "phases: $(ls "$E12/state" 2>/dev/null | grep -c '^s9_.*\.done') done, $(ls "$E12/state" 2>/dev/null | grep -c '^s9_.*\.failed') failed"
exit 0
