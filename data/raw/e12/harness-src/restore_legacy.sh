#!/bin/bash
# restore_legacy.sh — ship-checklist step (plan §10). Restart the legacy orchestrator using
# the command recorded by quiesce_legacy.sh. The watchdog restarts worker.sh within 120 s.
set -uo pipefail
STATE=/srv/bench/e12/quiesce-state.json
[ -f "$STATE" ] || { echo "no quiesce-state.json — nothing to restore"; exit 1; }
# release our gpu.lock only if it holds a dead/foreign-to-legacy pid recorded by us
if [ -f /srv/bench/orchestrator/gpu.lock ]; then
  pid=$(cat /srv/bench/orchestrator/gpu.lock 2>/dev/null || echo "")
  if ! kill -0 "$pid" 2>/dev/null; then
    rm -f /srv/bench/orchestrator/gpu.lock
    echo "stale gpu.lock (pid $pid) removed"
  else
    echo "gpu.lock held by live pid $pid — leaving it"
  fi
fi
setsid nohup bash /srv/bench/orchestrator/watchdog.sh >/dev/null 2>&1 < /dev/null &
sleep 3
if pgrep -f "orchestrator/watchdog.sh" >/dev/null 2>&1; then
  echo "watchdog restored (worker.sh follows within 120 s)"
else
  echo "ERROR: watchdog did not start"; exit 1
fi
