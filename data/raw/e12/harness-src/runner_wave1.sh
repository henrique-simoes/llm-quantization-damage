#!/bin/bash
# runner_wave1.sh — detached Wave-1 GPU runner (RA-4: no tmux on the host; the conductor
# kills workers at 2 h, so everything long runs under nohup + pid file + per-phase state
# files; every python phase is resumable). Run from /srv/bench/e12.
#   nohup setsid bash experiments/runner_wave1.sh validate > runner-validate.log 2>&1 &
#   nohup setsid bash experiments/runner_wave1.sh manifest > runner-manifest.log 2>&1 &
#   nohup setsid bash experiments/runner_wave1.sh sweep    > runner-sweep.log 2>&1 &
set -uo pipefail
E12=/srv/bench/e12
STATE=$E12/state
PY=/srv/bench/.venv-evalplus/bin/python
mkdir -p "$STATE"
PHASE="${1:-help}"

mark() {
  local marker="$1"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$STATE/$marker"
  case "$marker" in
    *.done) rm -f "$STATE/${marker%.done}.failed" ;;
    *.ok) rm -f "$STATE/${marker%.ok}.failed" ;;
  esac
}
have() { [ -f "$STATE/$1" ]; }

echo "[$(date -u +%FT%TZ)] runner phase=$PHASE pid=$$"

# SINGLE INSTANCE (2026-08-30). `nohup setsid bash runner...` leaves a setsid parent AND a
# child; killing one PID left the sibling alive, it advanced to the next quant, and a second
# runner started in parallel — two tsweeps then fought over gpu.lock and the container name
# and produced 32 junk cells across three quants. flock on fd 9 makes a second runner refuse.
exec 9>"$STATE/runner.$PHASE.lock"
if ! flock -n 9; then
  echo "REFUSING: another runner already holds $STATE/runner.$PHASE.lock"; exit 3
fi

# Propagate shutdown to the child so stopping the runner stops the GPU work deterministically.
CHILD=""
on_signal() {
  echo "[$(date -u +%FT%TZ)] runner: signal received; stopping child ${CHILD:-none}"
  [ -n "$CHILD" ] && kill -TERM "$CHILD" 2>/dev/null
  wait "$CHILD" 2>/dev/null
  exit 143
}
trap on_signal TERM INT
# NOTE: the gpu.lock belongs to the PYTHON experiments (lib_e12.preflight), not to this
# runner — a lock held by a dead-between-phases runner pid would wedge the next phase.

case "$PHASE" in
  validate)
    if have validate.done; then echo "validate already done"; exit 0; fi
    if have validate.positive.ok; then
      echo "positive run already green — skipping to selftest"
    else
      $PY experiments/validate_v2.py --out /srv/bench/e12/validate-v2.json \
        && mark validate.positive.ok || { mark validate.positive.failed; exit 1; }
    fi
    $PY experiments/validate_v2.py --selftest --out /srv/bench/e12/validate-v2-selftest.json \
      && mark validate.done || { mark validate.selftest.failed; exit 1; }
    exit 0 ;;
  manifest)
    if have manifest.done; then echo "manifest already done"; exit 0; fi
    bash experiments/sweep_v2.sh manifest && mark manifest.done || { mark manifest.failed; exit 1; }
    exit 0 ;;
  sweep)
    # Order is a parameter (2026-08-30): Wave 1 feeds a Track A decision whose priority is
    # accuracy -> context -> tok/s, so the highest-fidelity / least-known quants run FIRST.
    # Default keeps the original order; callers pass an explicit list to reprioritise.
    shift || true
    QUANTS_TO_RUN="${*:-Q4_K_XL Q5_K_XL Q6_K Q6_K_XL}"
    for q in $QUANTS_TO_RUN; do
      if have "sweep-$q.done"; then echo "sweep $q already done"; continue; fi
      echo "[$(date -u +%FT%TZ)] starting tsweep $q"
      $PY experiments/tsweep_v2.py --quant "$q" --out "/srv/bench/e12/tsweep-v2-$q.json" &
      CHILD=$!
      if wait "$CHILD"; then mark "sweep-$q.done"
      else mark "sweep-$q.failed"; echo "sweep $q FAILED — continuing with next quant"; fi
      CHILD=""
    done
    if ls "$STATE"/sweep-*.failed >/dev/null 2>&1; then exit 1; fi
    mark sweep.done
    exit 0 ;;
  *)
    echo "usage: runner_wave1.sh validate|manifest|sweep"; exit 2 ;;
esac
