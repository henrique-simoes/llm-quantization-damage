#!/bin/bash
# watch-qbench.sh — DETACHED watcher for the qbench-t1 conductor run. Never run in foreground.
#   start: nohup python3 -c "import os; os.setsid(); os.execvp('bash',['bash','tools/watch-qbench.sh'])" >/dev/null 2>&1 & disown
#          (os.setsid detaches the session — plain nohup is killed with the terminal's group)
#   stop : kill $(cat data/watch/watcher.pid)
# Jobs (never blocks a conversation):
#   1. tails conductor.log ticks -> transitions -> data/watch/events.log + macOS notification
#   2. every SYNC_EVERY seconds: tools/sync-multivac.sh pull  (docs-only sync, DEC-5)
REPO="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$REPO/.compass-forge/conductor/conductor.log"
OUT="$REPO/data/watch"
EVENTS="$OUT/events.log"; STATE="$OUT/state.json"; PIDF="$OUT/watcher.pid"; SYNCLOG="$OUT/sync.log"
PARSER="$REPO/tools/parse_tick.py"
INTERVAL=45; SYNC_EVERY=600
mkdir -p "$OUT"; echo $$ > "$PIDF"
echo "$(date -u +%FT%TZ) | watcher started pid $$" >> "$EVENTS"

last_await=""; last_blocked=-1; last_health=""; last_conv=""; last_tasks=-1; last_active=""; last_rate=""
sync_ts=0

notify() { # notify <msg> <important:0|1>
  echo "$(date -u +%FT%TZ) | $1" >> "$EVENTS"
  if [ "$2" = "1" ]; then osascript -e "display notification \"$1\" with title \"qbench-t1 conductor\" sound name \"Glass\"" >/dev/null 2>&1; fi
}

while true; do
  tick_line=$(grep '"tick"' "$LOG" 2>/dev/null | tail -1)
  if [ -n "$tick_line" ]; then
    kv=$(printf '%s' "$tick_line" | python3 "$PARSER" 2>/dev/null)
    if [ -n "$kv" ]; then
      for kvpair in $(printf '%s' "$kv" | tr ';' ' '); do export "${kvpair?}"; done
      if [ "$await" = "1" ] && [ "$last_await" = "0" ]; then
        notify "PLAN READY — owner approval required (conductor paused at the gate)" 1
      fi
      if [ "$last_blocked" != "-1" ] && [ "$blocked" -gt "$last_blocked" ] 2>/dev/null; then
        notify "PROBLEM: $blocked task(s) BLOCKED [$blocked_roles] — needs human" 1
      fi
      if [ -n "$last_health" ] && [ "$health" != "$last_health" ] && [ "$health" != "ok" ]; then
        notify "PROBLEM: conductor health=$health (possible WEDGED worker)" 1
      fi
      if [ "$last_rate" = "0" ] && [ "$rate_blocked" = "1" ]; then
        notify "PROBLEM: rate-limited role blocked — reset wait required" 1
      fi
      if [ "$last_conv" != "" ] && [ "$conv" = "1" ] && [ "$last_conv" = "0" ]; then
        notify "WAVE CONVERGED — reviews passed; next wave importing" 1
      fi
      if [ "$last_active" != "" ] && [ "$active" != "$last_active" ]; then
        notify "stage transition: $last_active -> $active" 0
      fi
      last_await=$await; last_blocked=$blocked; last_health=$health; last_conv=$conv; last_active=$active; last_rate=$rate_blocked
      printf '{"at":"%s","await_owner":%s,"blocked":%s,"blocked_roles":"%s","health":"%s","converged":%s,"tasks":%s,"active":"%s","verdicts":"%s","rate_limited":%s}\n' \
        "$(date -u +%FT%TZ)" "$await" "$blocked" "$blocked_roles" "$health" "$conv" "$tasks" "$active" "$verdicts" "$rate_blocked" > "$STATE"
    fi
  fi
  now=$(date +%s)
  if [ $((now - sync_ts)) -ge "$SYNC_EVERY" ]; then
    sync_ts=$now
    bash "$REPO/tools/sync-multivac.sh" pull >> "$SYNCLOG" 2>&1 || notify "docs sync pull FAILED (see data/watch/sync.log)" 0
    echo "$(date -u +%FT%TZ) | periodic docs sync done" >> "$SYNCLOG"
  fi
  sleep "$INTERVAL"
done
