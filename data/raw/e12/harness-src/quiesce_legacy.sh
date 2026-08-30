#!/bin/bash
# quiesce_legacy.sh — Wave-1 T1 (plan D4 / F-A / owner gate Q-A3 = quiesced through Waves 2-4).
# Stops the legacy orchestrator: watchdog.sh FIRST (reverse order just gets worker restarted
# within 120 s), then worker.sh. Records pids + the exact restore command into
# /srv/bench/e12/quiesce-state.json. Leaves orchestrator/state/*.done untouched (KEEP list).
set -uo pipefail
E12=/srv/bench/e12
STATE=$E12/quiesce-state.json
mkdir -p "$E12"

wd_pid=$(pgrep -f "bash /srv/bench/orchestrator/watchdog.sh" | head -1 || true)
wk_pid=$(pgrep -f "bash /srv/bench/orchestrator/worker.sh" | head -1 || true)
wd_cmd=$(tr '\0' ' ' < /proc/"$wd_pid"/cmdline 2>/dev/null || echo "bash /srv/bench/orchestrator/watchdog.sh")
wk_cmd=$(tr '\0' ' ' < /proc/"$wk_pid"/cmdline 2>/dev/null || echo "bash /srv/bench/orchestrator/worker.sh")
echo "watchdog pid=$wd_pid worker pid=$wk_pid"

[ -n "$wd_pid" ] && kill -TERM "$wd_pid" 2>/dev/null || true
sleep 2
[ -n "$wk_pid" ] && kill -TERM "$wk_pid" 2>/dev/null || true
for i in $(seq 1 15); do
  pgrep -f "orchestrator/(watchdog|worker).sh" >/dev/null 2>&1 || break
  sleep 2
done
for pid in $(pgrep -f "orchestrator/(watchdog|worker).sh" 2>/dev/null); do
  echo "escalating to SIGKILL: $pid"; kill -KILL "$pid" 2>/dev/null || true
done
sleep 1
if pgrep -f "orchestrator/(watchdog|worker).sh" >/dev/null 2>&1; then
  echo "ERROR: legacy orchestrator still running"; exit 1
fi

done_count=$(ls /srv/bench/orchestrator/state/*.done 2>/dev/null | wc -l)
cat > "$STATE" <<EOF
{
 "quiesced_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
 "watchdog": {"pid": ${wd_pid:-0}, "cmdline": "$wd_cmd"},
 "worker": {"pid": ${wk_pid:-0}, "cmdline": "$wk_cmd"},
 "state_done_markers_intact": $done_count,
 "restore_command": "setsid nohup bash /srv/bench/orchestrator/watchdog.sh >/dev/null 2>&1 < /dev/null &",
 "restore_script": "/srv/bench/e12/experiments/restore_legacy.sh",
 "note": "watchdog stopped FIRST, then worker. state/*.done untouched (KEEP). gpu.lock held by the e12 runner while experiments run (legacy gpu_busy() yields on a live pid)."
}
EOF
echo "quiesced. state/*.done count=$done_count (expect 6)"
echo "quiesce-state -> $STATE"
