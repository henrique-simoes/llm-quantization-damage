#!/bin/bash
# s7_chain.sh — run S7 once S5 has released the GPU.
# Condition-based wait (never on a pid — Wave-1 defect D6), flock-guarded, logs everything.
set -uo pipefail
E12=/srv/bench/e12
PY=/srv/bench/.venv-evalplus/bin/python
LOG=$E12/logs/ssa_S7.log
mkdir -p "$E12/logs" "$E12/state"
exec 9>"$E12/state/s7.lock"
flock -n 9 || { echo "REFUSING: another s7 chain holds the lock"; exit 3; }
say(){ echo "[$(date -u +%FT%TZ)] $*" | tee -a "$LOG"; }

say "s7_chain pid $$ waiting for S5 / any GPU work to finish"
waited=0
while pgrep -f "ssa_s5\.py|llama-perplexity|tsweep_v2\.py" >/dev/null 2>&1; do
  sleep 30; waited=$((waited+30))
  [ $((waited % 600)) -eq 0 ] && say "  still waiting (${waited}s)"
  [ $waited -gt 7200 ] && { say "GIVING UP after 2 h"; exit 5; }
done
say "GPU free after ${waited}s; starting S7"
sleep 20
$PY "$E12/experiments/ssa_s7.py" 2>&1 | tee -a "$LOG"
rc=${PIPESTATUS[0]}
say "S7 exited rc=$rc"
exit $rc
