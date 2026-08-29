#!/bin/bash
# /srv/bench/orchestrator/lib.sh -- shared helpers for the benchmark worker.
# Every rule here exists because something was lost or corrupted before it did.

ORCH=/srv/bench/orchestrator
STATE=$ORCH/state
LOGS=$ORCH/logs
TIMINGS=/srv/bench/server-timings
GPU_LOCK=$ORCH/gpu.lock
mkdir -p "$STATE" "$LOGS" "$TIMINGS"

ts() { date -Iseconds; }

jlog() {  # jlog <job> <message>
  echo "$(ts) | $1 | $2" >> "$ORCH/worker.log"
  echo "$(ts) | $2" >> "$LOGS/$1.log"
}

job_done()    { [ -f "$STATE/$1.done" ]; }
mark_done()   { date -Iseconds > "$STATE/$1.done"; jlog "$1" "DONE"; }
mark_failed() { date -Iseconds > "$STATE/$1.failed"; jlog "$1" "FAILED: ${2:-unspecified}"; }
mark_start()  { date -Iseconds > "$STATE/$1.started"; jlog "$1" "START"; }

# --- GPU coordination -------------------------------------------------
# Other pipelines (phase3 humaneval, phase4 speed matrix) may own the GPU.
gpu_busy() {
  pgrep -f "run-humaneval-thinking-v2.sh" >/dev/null 2>&1 && return 0
  pgrep -f "phase4-quant-speed.sh"        >/dev/null 2>&1 && return 0
  pgrep -f "phase34-waiter.sh"            >/dev/null 2>&1 && return 0
  [ -f "$GPU_LOCK" ] && kill -0 "$(cat "$GPU_LOCK" 2>/dev/null)" 2>/dev/null && return 0
  return 1
}
gpu_acquire() { echo $$ > "$GPU_LOCK"; }
gpu_release() { rm -f "$GPU_LOCK"; }

# --- THE RULE THAT COST US DATA --------------------------------------
# Never destroy a container without first persisting its logs.
kill_server() {  # kill_server <container> <label>
  local c="${1:-llamasrv}" label="$2"
  if docker ps -a --filter "name=$c" -q | grep -q .; then
    if [ -n "$label" ]; then
      docker logs "$c" > "$TIMINGS/${label}.serverlog" 2>&1 || true
      local n; n=$(grep -c "tg = " "$TIMINGS/${label}.serverlog" 2>/dev/null || echo 0)
      jlog "${label}" "server log saved ($n timing samples)"
    fi
    docker rm -f "$c" >/dev/null 2>&1 || true
  fi
}

wait_health() {  # wait_health <port> <seconds> <container>
  local port="$1" limit="${2:-900}" c="${3:-llamasrv}" i=0
  while [ $i -lt "$limit" ]; do
    curl -sf "http://localhost:$port/health" >/dev/null 2>&1 && return 0
    docker ps --filter "name=$c" --filter status=running -q | grep -q . || return 1
    sleep 5; i=$((i+5))
  done
  return 1
}

snapshot_metrics() {  # refresh the JSON the ledger is generated from
  python3 /srv/bench/collect-metrics.py > /srv/bench/ledger-data.json.tmp 2>/dev/null \
    && mv /srv/bench/ledger-data.json.tmp /srv/bench/ledger-data.json
  python3 /srv/bench/extract-champion.py > /srv/bench/champion-timings.json.tmp 2>/dev/null \
    && mv /srv/bench/champion-timings.json.tmp /srv/bench/champion-timings.json
}
