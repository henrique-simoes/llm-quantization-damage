#!/bin/bash
# keepalive.sh — keeps supervisor.sh alive until the plan finishes.
#
# There is no cron on this host and systemd user lingering is off (enabling it is a
# system setting, not ours to change unattended), so this is a plain detached loop:
# check every 5 minutes, restart the supervisor if it is gone and the plan is not done.
# The supervisor is flock-guarded and step-idempotent, so a restart RESUMES.
#
# Deliberately trivial — a sleep loop is the most robust thing available here.
E12=/srv/bench/e12
LOG=$E12/keepalive.log
say(){ echo "[$(date -u +%FT%TZ)] $*" >> "$LOG"; }

exec 9>"$E12/state/keepalive.lock"
flock -n 9 || { say "another keepalive holds the lock; exiting"; exit 3; }

say "keepalive pid $$ started"
restarts=0
while true; do
  if [ -f "$E12/state/progress.json" ] && grep -q '"finished_utc"' "$E12/state/progress.json" 2>/dev/null; then
    say "plan finished (finished_utc present) — keepalive exiting after $restarts restart(s)"
    exit 0
  fi
  if ! pgrep -f "bash $E12/supervisor\.sh" >/dev/null 2>&1; then
    restarts=$((restarts+1))
    say "supervisor not running and plan not finished — restart #$restarts"
    nohup setsid bash "$E12/supervisor.sh" >> "$E12/supervisor-restart.log" 2>&1 < /dev/null &
    sleep 20
  fi
  sleep 300
done
