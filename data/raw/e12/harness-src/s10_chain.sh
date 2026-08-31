#!/bin/bash
# s10_chain.sh — divergence vs CONTEXT DEPTH, queued behind s9e.
# Pilot is a HARD GATE and is also real work: it records rung B's reference logits and scores
# one arm, so on success it costs nothing extra and rungB reuses its base file. If the pilot
# fails, the chain STOPS — nothing downstream would mean anything.
set -uo pipefail
E12=/srv/bench/e12; PY=/srv/bench/.venv-evalplus/bin/python; REPO=$HOME/repos/multivac-paper
LOG=$E12/logs/s10_chain.log
mkdir -p "$E12/logs" "$E12/state" "$E12/s10"
say(){ echo "[$(date -u +%FT%TZ)] $*" | tee -a "$LOG"; }
exec 5>"$E12/state/s10.lock"; flock -n 5 || { echo "REFUSING: another s10 chain"; exit 3; }

sync_git() {
  { mkdir -p "$REPO/data/raw/e12/s10"
    for f in "$E12"/s10/*.json; do [ -f "$f" ] && cp -f "$f" "$REPO/data/raw/e12/s10/" 2>/dev/null; done
    for f in "$E12"/logs/s10*.log; do [ -f "$f" ] && cp -f "$f" "$REPO/data/raw/e12/logs/" 2>/dev/null; done
    cp -f "$E12/experiments/s10_ctxdepth.py" "$REPO/data/raw/e12/harness-src/" 2>/dev/null
    cp -f "$E12/s10_chain.sh"                "$REPO/data/raw/e12/harness-src/" 2>/dev/null
    cd "$REPO" && git add -A >/dev/null 2>&1
    git diff --cached --quiet 2>/dev/null || {
      git commit -q -m "data(s10): autonomous sync — $1" >/dev/null 2>&1
      git pull -q --rebase origin main >/dev/null 2>&1 || true
      git push -q origin main >/dev/null 2>&1 && say "  git: pushed ($1)" || say "  git: push deferred ($1)"; }
  } || say "  git: sync errored ($1) — ignored"; return 0
}

say "s10_chain pid $$ queued — waiting on s9e.lock"
t0=$(date +%s); exec 4>"$E12/state/s9e.lock"; flock 4
say "s9e.lock acquired after $(( $(date +%s) - t0 ))s — starting S10"; sleep 20

say "=== S10 PILOT START (hard gate: does --kl-divergence run at -c 65536?) ==="
$PY "$E12/experiments/s10_ctxdepth.py" --phase pilot > "$E12/logs/s10_pilot.log" 2>&1
if [ $? -ne 0 ]; then
  date -u +%FT%TZ > "$E12/state/s10_pilot.failed"
  say "=== S10 PILOT FAILED — CHAIN STOPS, battery not run ==="
  tail -20 "$E12/logs/s10_pilot.log" | sed 's/^/      /' | tee -a "$LOG"
  sync_git "s10 pilot FAILED"; exit 4
fi
date -u +%FT%TZ > "$E12/state/s10_pilot.done"; say "=== S10 PILOT OK ==="; sync_git "after s10 pilot"

for phase in rungA rungB kv summarize; do
  [ -f "$E12/state/s10_$phase.done" ] && { say "=== $phase already done — skipping ==="; continue; }
  say "=== PHASE $phase START ==="
  $PY "$E12/experiments/s10_ctxdepth.py" --phase "$phase" > "$E12/logs/s10_$phase.log" 2>&1
  rc=$?
  if [ $rc -eq 0 ]; then date -u +%FT%TZ > "$E12/state/s10_$phase.done"; say "=== PHASE $phase OK ==="
  else date -u +%FT%TZ > "$E12/state/s10_$phase.failed"
       say "=== PHASE $phase FAILED rc=$rc — logged and SKIPPED, chain continues ==="
       tail -10 "$E12/logs/s10_$phase.log" | sed 's/^/      /' | tee -a "$LOG"; fi
  grep -E "VERDICT:|TREND:|KV AT DEPTH:" "$E12/logs/s10_$phase.log" 2>/dev/null | sed 's/^/      /' | tee -a "$LOG"
  sync_git "after s10 $phase"
done
say "=== S10 CHAIN COMPLETE — CAMPAIGN DONE ==="
exit 0
