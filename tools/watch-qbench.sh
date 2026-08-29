#!/bin/bash
# watch-qbench.sh — DETACHED watcher for the qbench-t1 conductor run. Never run in foreground.
#   start: nohup setsid bash tools/watch-qbench.sh >/dev/null 2>&1 & disown
#   stop : kill $(cat data/watch/watcher.pid)
# Does two jobs without ever blocking a conversation:
#   1. tails conductor.log ticks -> transitions -> data/watch/events.log + macOS notification
#   2. every SYNC_EVERY seconds: tools/sync-multivac.sh pull (multivac -> repo data/, always)
REPO="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$REPO/.compass-forge/conductor/conductor.log"
OUT="$REPO/data/watch"
EVENTS="$OUT/events.log"; STATE="$OUT/state.json"; PIDF="$OUT/watcher.pid"; SYNCLOG="$OUT/sync.log"
INTERVAL=45; SYNC_EVERY=600
mkdir -p "$OUT"; echo $$ > "$PIDF"
echo "$(date -u +%FT%TZ) | watcher started pid $$" >> "$EVENTS"

last_await=""; last_blocked=-1; last_health=""; last_conv=""; last_tasks=-1; last_active=""; sync_ts=0
NOTIF=1
notify() { # notify <msg> <important:0|1>
  echo "$(date -u +%FT%TZ) | $1" >> "$EVENTS"
  [ "$2" = "1" ] && [ "$NOTIF" = "1" ] && osascript -e "display notification \"$1\" with title \"qbench-t1 conductor\" sound name \"Glass\"" >/dev/null 2>&1
}

while true; do
  tick_line=$(grep '"tick"' "$LOG" 2>/dev/null | tail -1)
  if [ -n "$tick_line" ]; then
    eval "$(printf '%s' "$tick_line" | python3 -c "
import json,sys
try: t=json.load(sys.stdin)['tick']
except Exception: print('exit 1'); raise SystemExit
ad=t.get('active_detail') or []
roles=','.join(sorted({a['role'] for a in ad})) if ad else '-'
bv=t.get('role_verdicts') or {}
vs=','.join(f'{k}={v}' for k,v in sorted(bv.items()))
print(f'await={int(bool(t.get(\"awaiting_owner_approval\")))};blocked={len(t.get(\"blocked\") or [])};health={t.get(\"health\")};conv={int(bool(t.get(\"converged\")))};tasks={t.get(\"tasks_total\")};active={roles};verdicts={vs}')")" )
    [ "$await" != "$last_await" ] && [ -n "$last_await" ] && { [ "$await" = "1" ] && notify "PLAN READY — owner approval required (conductor paused at the gate)" 1; }
    [ "$blocked" != "$last_blocked" ] && [ "$last_blocked" != -1 ] && [ "$blocked" -gt 0 ] && notify "PROBLEM: $blocked task(s) BLOCKED — needs human" 1
    [ "$health" != "$last_health" ] && [ -n "$last_health" ] && [ "$health" != "ok" ] && notify "PROBLEM: conductor health=$health (possible WEDGED worker)" 1
    [ "$conv" != "$last_conv" ] && [ "$last_conv" != "" ] && [ "$conv" = "1" ] && notify "WAVE CONVERGED — reviews passed; next wave importing" 1
    [ "$tasks" != "$last_tasks" ] && [ "$last_tasks" != -1 ] && notify "task graph changed: $last_tasks -> $tasks tasks (stage transition: $active)" 0
    [ "$active" != "$last_active" ] && [ -n "$last_active" ] && notify "stage now active: $active (verdicts: $verdicts)" 0
    last_await=$await; last_blocked=$blocked; last_health=$health; last_conv=$conv; last_tasks=$tasks; last_active=$active; last_verdicts=$verdicts
    printf '{"at":"%s","await_owner":%s,"blocked":%s,"health":"%s","converged":%s,"tasks":%s,"active":"%s","verdicts":"%s"}\n' \
      "$(date -u +%FT%TZ)" "$await" "$blocked" "$health" "$conv" "$tasks" "$active" "$verdicts" > "$STATE"
  fi
  now=$(date +%s)
  if [ $((now - sync_ts)) -ge "$SYNC_EVERY" ]; then
    sync_ts=$now
    bash "$REPO/tools/sync-multivac.sh" pull >> "$SYNCLOG" 2>&1 || notify "sync-multivac pull FAILED (see data/watch/sync.log)" 0
    echo "$(date -u +%FT%TZ) | periodic sync done" >> "$SYNCLOG"
  fi
  sleep "$INTERVAL"
done
