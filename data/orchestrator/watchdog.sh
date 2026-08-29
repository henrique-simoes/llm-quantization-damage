#!/bin/bash
# /srv/bench/orchestrator/watchdog.sh
# Keeps the worker alive across crashes and host reboots.
# Deliberately dumb: check, restart if absent, sleep. No state of its own.
ORCH=/srv/bench/orchestrator
while true; do
  if ! pgrep -f "$ORCH/worker.sh" >/dev/null 2>&1; then
    echo "$(date -Iseconds) | worker absent -- restarting" >> "$ORCH/watchdog.log"
    setsid nohup bash "$ORCH/worker.sh" >/dev/null 2>&1 < /dev/null &
  fi
  sleep 120
done
