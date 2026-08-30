#!/bin/bash
# ssa_runner.sh -- stage 2 of the autonomous chain. Waits for finish_wave1.sh (which is
# itself waiting on the Wave-1 sweep), then runs SSA with its smoke gate enforced.
#
# Chain: runner_wave1.sh  ->  finish_wave1.sh  ->  ssa_runner.sh
#          (T4/T5 sweeps)     (summarize + verify-1a)   (S0 gate -> S1..S4)
#
# Small-before-big is a HARD GATE (plan §6): S0 runs 4 chunks end-to-end and must exit 0
# with populated KLD fields before the real budget is spent. If S0 fails this stops and
# leaves the box idle for a human -- it does NOT fall through to the full run.
set -uo pipefail
E12=/srv/bench/e12
PY=/srv/bench/.venv-evalplus/bin/python
cd "$E12" || exit 1
mkdir -p "$E12/state" "$E12/ssa"

exec 9>"$E12/state/ssa-runner.lock"
flock -n 9 || { echo "REFUSING: another ssa_runner holds the lock"; exit 3; }

log(){ echo "[$(date -u +%FT%TZ)] $*"; }

# Wait on the CONDITION, not on a pid. `nohup setsid bash ...` leaves a parent AND a
# child (Wave-1 defect D6): waiting on whichever pid pgrep happened to return first
# could fall through while the real work was still going -- e.g. during the finisher's
# ~60 GB sha256 pass. Instead: no finish_wave1.sh process of ANY kind may remain, and
# its log must carry the completion marker it only writes on a clean exit.
FIN_LOG="$E12/finish-wave1.log"
log "ssa_runner pid $$ waiting for finish_wave1.sh to complete (condition-based)"
while true; do
  procs=$(pgrep -fc "finish_wave1\.sh" 2>/dev/null || echo 0)
  if [ "$procs" -eq 0 ]; then
    if grep -q "FINISHER DONE" "$FIN_LOG" 2>/dev/null; then
      log "finisher completed cleanly (marker found, no processes left)"; break
    fi
    log "ABORT: finish_wave1.sh is gone but its log has no completion marker."
    log "  It died or was killed. Not starting SSA -- a human should look at $FIN_LOG."
    exit 6
  fi
  sleep 60
done
sleep 30

if pgrep -f "tsweep_v2.py|runner_wave1.sh sweep" >/dev/null 2>&1; then
  log "ABORT: a sweep is somehow still running. Not starting SSA."; exit 5
fi

log "=== S0 smoke gate (4 chunks, reference arm, both domains) ==="
$PY experiments/ssa_kld.py --step S0 --out "$E12/ssa/ssa-smoke.json"; rc0=$?
log "S0 rc=$rc0"
if [ "$rc0" -ne 0 ]; then
  log "S0 GATE FAILED (rc=$rc0). Stopping by design -- the full run is NOT started."
  log "Inspect $E12/ssa/ssa-smoke.json and /srv/bench/server-timings/ssa-*.serverlog"
  exit "$rc0"
fi
log "S0 GATE GREEN"

for step in S1 S2 S3 S4; do
  log "=== $step ==="
  $PY experiments/ssa_kld.py --step "$step" --out "$E12/ssa/ssa-results.json"; rc=$?
  log "$step rc=$rc"
  if [ "$rc" -ne 0 ]; then log "$step FAILED -- stopping chain"; exit "$rc"; fi
done

log "=== SSA S0-S4 COMPLETE -> $E12/ssa/ssa-results.json ==="
log "Remaining, NOT run here: S5 (HumanEval+ prompt-KLD, needs the prompt file built) and"
log "  S6 (generative HumanEval+, 2 arms paired). Both need a harness that does not exist yet."
log "Logits files under $E12/ssa/*.kld are ~11 GB each -- delete once results are pulled."
exit 0
