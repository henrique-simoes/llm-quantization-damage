#!/bin/bash
# s12_mk100_chain.sh — MK-NIAH at n=100, the one outstanding measurement.
# Decides whether a long-context claim can stay in the paper's title: at n=12 the arms scored
# 100.0 vs 91.67 with overlapping Wilson intervals (one discordant sample, p=1.0). At n=100, if
# the ~8% rate holds, McNemar sees ~0 vs ~8 discordant -> p ~ 0.008.
# Verified before launch: RULER's own MK-NIAH config (num_keys=4, 1 queried, 3 hard distractors),
# data generated and checked (100 samples, all needles unique, 130,439-131,072 tokens), and the
# full code path exercised by --phase mkmock at 8,192 in 4 minutes.
set -uo pipefail
E12=/srv/bench/e12; PY=/srv/bench/.venv-evalplus/bin/python; REPO=$HOME/repos/multivac-paper
LOG=$E12/logs/s12_mk100_chain.log
mkdir -p "$E12/logs" "$E12/state"
exec 3>"$E12/state/s12mk100.lock"; flock -n 3 || { echo "REFUSING: already running"; exit 3; }
say(){ echo "[$(date -u +%FT%TZ)] $*" | tee -a "$LOG"; }
sync_git(){
  { cp -f "$E12"/ruler/*.json "$REPO/data/raw/e12/ruler/" 2>/dev/null
    cp -f "$E12"/logs/s12_*.log "$REPO/data/raw/e12/logs/" 2>/dev/null
    cp -f "$E12/experiments/s12_ruler.py" "$E12/s12_mk100_chain.sh" "$REPO/data/raw/e12/harness-src/" 2>/dev/null
    cd "$REPO" && git add -A >/dev/null 2>&1
    git diff --cached --quiet 2>/dev/null || {
      git commit -q -m "data(s12-mk100): autonomous sync — $1" >/dev/null 2>&1
      git pull -q --rebase origin main >/dev/null 2>&1 || true
      git push -q origin main >/dev/null 2>&1 && say "  git: pushed ($1)" || say "  git: push deferred ($1)"; }
  } || say "  git: sync errored"; return 0
}
say "mk100 START — 2 arms x 100 samples @131,072, ~9.4 h (measured 170 s/sample, not estimated)"
$PY "$E12/experiments/s12_ruler.py" --phase mk100 > "$E12/logs/s12_mk100.log" 2>&1
rc=$?
if [ $rc -eq 0 ]; then date -u +%FT%TZ > "$E12/state/s12_mk100.done"; say "=== mk100 OK ==="
else date -u +%FT%TZ > "$E12/state/s12_mk100.failed"; say "=== mk100 FAILED rc=$rc ==="
     tail -10 "$E12/logs/s12_mk100.log" | sed 's/^/      /' | tee -a "$LOG"; fi
grep -E "score |cells ok" "$E12/logs/s12_mk100.log" 2>/dev/null | sed 's/^/      /' | tee -a "$LOG"
sync_git "after mk100"
say "=== CHAIN COMPLETE ==="
