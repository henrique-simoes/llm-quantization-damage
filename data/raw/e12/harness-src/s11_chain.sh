#!/bin/bash
# s11_chain.sh — greedy divergence at depth. Cheapest depth first so each slice stands alone.
set -uo pipefail
E12=/srv/bench/e12; PY=/srv/bench/.venv-evalplus/bin/python; REPO=$HOME/repos/multivac-paper
LOG=$E12/logs/s11_chain.log
mkdir -p "$E12/logs" "$E12/state" "$E12/s11"
exec 3>"$E12/state/s11.lock"; flock -n 3 || { echo "REFUSING: another s11 chain"; exit 3; }
say(){ echo "[$(date -u +%FT%TZ)] $*" | tee -a "$LOG"; }
sync_git(){
  { mkdir -p "$REPO/data/raw/e12/s11"
    for f in "$E12"/s11/*.json; do [ -f "$f" ] && [ "$(stat -c%s "$f")" -lt 5000000 ] && cp -f "$f" "$REPO/data/raw/e12/s11/" 2>/dev/null; done
    for f in "$E12"/logs/s11*.log; do [ -f "$f" ] && cp -f "$f" "$REPO/data/raw/e12/logs/" 2>/dev/null; done
    cp -f "$E12/experiments/s11_divdepth.py" "$E12/s11_chain.sh" "$REPO/data/raw/e12/harness-src/" 2>/dev/null
    cd "$REPO" && git add -A >/dev/null 2>&1
    git diff --cached --quiet 2>/dev/null || {
      git commit -q -m "data(s11): autonomous sync — $1" >/dev/null 2>&1
      git pull -q --rebase origin main >/dev/null 2>&1 || true
      git push -q origin main >/dev/null 2>&1 && say "  git: pushed ($1)" || say "  git: push deferred ($1)"; }
  } || say "  git: sync errored ($1)"; return 0
}
say "s11_chain pid $$ — pilot already PASSED (serves 196,608, 512 tok, byte-identical self-check)"
for ph in d8192 d65536 d196608 summarize; do
  [ -f "$E12/state/s11_$ph.done" ] && { say "=== $ph already done — skipping ==="; continue; }
  say "=== PHASE $ph START ==="
  $PY "$E12/experiments/s11_divdepth.py" --phase "$ph" > "$E12/logs/s11_$ph.log" 2>&1
  rc=$?
  if [ $rc -eq 0 ]; then date -u +%FT%TZ > "$E12/state/s11_$ph.done"; say "=== PHASE $ph OK ==="
  else date -u +%FT%TZ > "$E12/state/s11_$ph.failed"
       say "=== PHASE $ph FAILED rc=$rc — logged and SKIPPED ==="
       tail -8 "$E12/logs/s11_$ph.log" | sed 's/^/      /' | tee -a "$LOG"; fi
  grep -E "DIVERGENCE|FIRST-DIVERGENCE|  Q[0-9]" "$E12/logs/s11_$ph.log" 2>/dev/null | sed 's/^/      /' | tee -a "$LOG"
  sync_git "after s11 $ph"
done
say "=== S11 CHAIN COMPLETE ==="
