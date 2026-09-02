#!/bin/bash
# s12_chain.sh — RULER long-context accuracy, cheapest length first.
set -uo pipefail
E12=/srv/bench/e12; PY=/srv/bench/.venv-evalplus/bin/python; REPO=$HOME/repos/multivac-paper
LOG=$E12/logs/s12_chain.log
mkdir -p "$E12/logs" "$E12/state" "$E12/ruler"
exec 3>"$E12/state/s12.lock"; flock -n 3 || { echo "REFUSING: another s12 chain"; exit 3; }
say(){ echo "[$(date -u +%FT%TZ)] $*" | tee -a "$LOG"; }
sync_git(){
  { mkdir -p "$REPO/data/raw/e12/ruler"
    for f in "$E12"/ruler/*.json; do [ -f "$f" ] && [ "$(stat -c%s "$f")" -lt 5000000 ] && cp -f "$f" "$REPO/data/raw/e12/ruler/" 2>/dev/null; done
    for f in "$E12"/logs/s12*.log; do [ -f "$f" ] && cp -f "$f" "$REPO/data/raw/e12/logs/" 2>/dev/null; done
    cp -f "$E12/experiments/s12_ruler.py" "$E12/s12_chain.sh" "$REPO/data/raw/e12/harness-src/" 2>/dev/null
    cd "$REPO" && git add -A >/dev/null 2>&1
    git diff --cached --quiet 2>/dev/null || {
      git commit -q -m "data(s12): autonomous sync — $1" >/dev/null 2>&1
      git pull -q --rebase origin main >/dev/null 2>&1 || true
      git push -q origin main >/dev/null 2>&1 && say "  git: pushed ($1)" || say "  git: push deferred ($1)"; }
  } || say "  git: sync errored ($1)"; return 0
}
say "s12_chain pid $$ — RULER; smoke already PASSED (score 100.0 @4K, metric verified == RULER's)"
for ph in c8192 c32768 c131072 summarize; do
  [ -f "$E12/state/s12_$ph.done" ] && { say "=== $ph already done — skipping ==="; continue; }
  say "=== PHASE $ph START ==="
  $PY "$E12/experiments/s12_ruler.py" --phase "$ph" > "$E12/logs/s12_$ph.log" 2>&1
  rc=$?
  if [ $rc -eq 0 ]; then date -u +%FT%TZ > "$E12/state/s12_$ph.done"; say "=== PHASE $ph OK ==="
  else date -u +%FT%TZ > "$E12/state/s12_$ph.failed"
       say "=== PHASE $ph FAILED rc=$rc ==="; tail -8 "$E12/logs/s12_$ph.log" | sed 's/^/      /' | tee -a "$LOG"; fi
  grep -E "score |ACCURACY RECOVERY" "$E12/logs/s12_$ph.log" 2>/dev/null | sed 's/^/      /' | tee -a "$LOG"
  sync_git "after s12 $ph"
done
say "=== S12 CHAIN COMPLETE ==="
