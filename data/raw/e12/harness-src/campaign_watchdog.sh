#!/bin/bash
# campaign_watchdog.sh — emits ONE LINE PER NEW PROBLEM on stdout. Run under Monitor so each
# line becomes a chat notification. Silent while things are healthy; that silence is only
# meaningful because the checks below cover FAILURE, not just progress.
#
# What it watches, and why each one exists:
#   STALL   — a phase log has not been written to AND both GPUs are idle. Either alone is
#             normal (llama-perplexity is quiet for long stretches; a deep prefill pins the
#             GPU without logging), so the alarm requires BOTH.
#   ERROR   — a new CUDA / OOM / Traceback / allocation-failure signature in any phase log or
#             in a serverlog written since the watchdog started.
#   DEAD    — a chain process vanished without writing "CHAIN COMPLETE". This is the failure
#             mode a phase-transition monitor cannot see: nothing is logged when a script is
#             killed, so silence would otherwise look identical to "still running".
#   DISK    — `/` below 20 GB. S10 needs ~11 GB per logits file and the SSA runs once took `/`
#             to 87 %.
#   ORPHAN  — a llamasrv container up for >90 min with no chain alive to own it.
#   DONE    — every chain finished; the campaign is over.
set -uo pipefail
E12=/srv/bench/e12
STALL_MIN=${STALL_MIN:-18}
POLL=${POLL:-60}
STATE=/tmp/campaign_watchdog.seen
: > "$STATE"

emit(){ echo "$(date -u +%H:%MZ) $*"; }
seen(){ grep -qxF "$1" "$STATE" 2>/dev/null; }
mark(){ echo "$1" >> "$STATE"; }
once(){ seen "$1" || { mark "$1"; emit "$2"; }; }

chains_alive(){ pgrep -f "[s]9_chain.sh|[s]9d_chain.sh|[s]9e_chain.sh|[s]10_chain.sh" | wc -l; }
# NOTE: `bc` is NOT installed on this host. An earlier version piped through it, which made
# this function silently return "0" and therefore report the GPUs idle ALWAYS — every quiet
# stretch would have fired a false STALL. Summed with awk instead.
# Sampled over a window, not instantaneously. nvidia-smi returns a point reading, and a
# decode loop dips to 0 % between tokens, so a single sample says nothing. S10 matters most
# here: llama-perplexity can be COMPUTE-BUSY and LOG-SILENT for 30-60 min at n_ctx 65,536,
# and that combination must not read as a hang. Five samples over 12 s; idle only if every
# one is low.
gpu_idle(){ local i u
  for i in 1 2 3 4 5; do
    u=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits 2>/dev/null \
        | awk '{s+=$1} END{printf "%d", s+0}')
    [ "${u:-100}" -ge 5 ] && return 1
    sleep 3
  done
  return 0; }

emit "watchdog armed — $(chains_alive) chains alive, stall threshold ${STALL_MIN} min"

while true; do
  now=$(date +%s)
  alive=$(chains_alive)

  # ---- ERROR signatures in phase logs (only lines added since we started)
  for f in "$E12"/logs/s9_*.log "$E12"/logs/s9d_*.log "$E12"/logs/s9e_*.log "$E12"/logs/s10_*.log; do
    [ -f "$f" ] || continue
    hit=$(grep -aoiE "CUDA error[^\"]{0,80}|illegal memory access|out of memory|failed to allocate[^\"]{0,60}|Traceback \(most recent call last\)|MemoryError|No space left on device|CUDA_ERROR[A-Z_]*" "$f" 2>/dev/null | tail -1)
    if [ -n "$hit" ]; then
      key="err:$(basename "$f"):$hit"
      once "$key" "ERROR in $(basename "$f"): $hit"
    fi
  done

  # ---- STALL: log quiet AND GPUs idle AND a chain still alive
  if [ "$alive" -gt 0 ] && gpu_idle; then
    newest=$(ls -t "$E12"/logs/*.log 2>/dev/null | head -1)
    if [ -n "$newest" ]; then
      age=$(( (now - $(stat -c %Y "$newest")) / 60 ))
      if [ "$age" -ge "$STALL_MIN" ]; then
        once "stall:$(basename "$newest"):$((age/STALL_MIN))" \
             "STALL: no log write for ${age} min and both GPUs idle (newest: $(basename "$newest")) — a phase may be hung"
      fi
    fi
  fi

  # ---- DEAD: a chain that started but neither completed nor is running
  for c in s9 s9d s9e s10; do
    log="$E12/logs/${c}_chain.log"
    [ -f "$log" ] || continue
    grep -q "CHAIN COMPLETE\|CHAIN STOPS\|PILOT FAILED" "$log" 2>/dev/null && continue
    pgrep -f "[${c:0:1}]${c:1}_chain.sh" >/dev/null 2>&1 && continue
    once "dead:$c" "DEAD: ${c}_chain.sh is gone but never wrote CHAIN COMPLETE — check $log"
  done

  # ---- DISK
  freeg=$(df -BG --output=avail / | tail -1 | tr -dc '0-9')
  [ "${freeg:-99}" -lt 20 ] && once "disk:$((freeg/5))" "DISK: only ${freeg} GB free on / — S10 needs ~11 GB per logits file"

  # ---- ORPHAN container
  if [ "$alive" -eq 0 ]; then
    orph=$(docker ps --filter "name=llamasrv" --format '{{.Names}} {{.Status}}' 2>/dev/null)
    [ -n "$orph" ] && once "orphan" "ORPHAN: no chain alive but a server container is up: $orph"
  fi

  # ---- DONE
  if [ "$alive" -eq 0 ] && grep -q "CAMPAIGN DONE\|S10 CHAIN COMPLETE" "$E12/logs/s10_chain.log" 2>/dev/null; then
    emit "CAMPAIGN DONE — all chains finished, no chain processes remain"
    exit 0
  fi
  if [ "$alive" -eq 0 ]; then
    once "allgone" "ALL CHAINS GONE — campaign ended (check whether S10 completed or died)"
  fi
  sleep "$POLL"
done
