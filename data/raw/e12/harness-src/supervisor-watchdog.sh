#!/bin/bash
# supervisor-watchdog.sh — restarts supervisor.sh if it dies before finishing.
# Runs from cron every 10 minutes. Cheap, idempotent, and silent when healthy.
#
# The supervisor is flock-guarded and step-idempotent (.done markers), so a restart
# resumes rather than repeats. This exists so that a crash, an OOM-kill or a dropped
# session cannot leave the plan stalled overnight.
E12=/srv/bench/e12
LOG=$E12/watchdog.log
say(){ echo "[$(date -u +%FT%TZ)] $*" >> "$LOG"; }

# Finished cleanly? nothing to do, ever again.
if [ -f "$E12/state/progress.json" ] && grep -q '"finished_utc"' "$E12/state/progress.json" 2>/dev/null; then
  exit 0
fi
# Already running?
if pgrep -f "bash $E12/supervisor.sh" >/dev/null 2>&1; then exit 0; fi

say "supervisor not running and not finished — restarting"
nohup setsid bash "$E12/supervisor.sh" >> "$E12/supervisor-restart.log" 2>&1 < /dev/null &
say "restart issued"
exit 0
