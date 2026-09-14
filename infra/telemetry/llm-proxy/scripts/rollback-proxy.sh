#!/usr/bin/env bash
# Rollback of the D5 cut-over: stop llm-proxy, then relaunch the server bound directly on the
# original client address. Logs are saved first (same rule as the cut-over).
#
# Usage: rollback-proxy.sh ADDRESS [PORT] [LABEL]
#        ORIG_HOST=100.x.y.z ORIG_PORT=8080 rollback-proxy.sh
source "$(dirname "$0")/_relaunch_common.sh"

HOST="${1:-${ORIG_HOST:-}}"
PORT="${2:-${ORIG_PORT:-8080}}"
LABEL="${3:-pre-rollback}"
if [ -z "$HOST" ]; then
  echo "usage: $0 ADDRESS [PORT] [LABEL]   (or ORIG_HOST=... ORIG_PORT=...)" >&2
  exit 2
fi

say "stopping llm-proxy.service"
sudo systemctl stop llm-proxy.service
for _ in $(seq 1 20); do
  ss -ltnH "sport = :$PORT" | grep -q "$HOST:$PORT" || break
  sleep 0.5
done
if ss -ltnH "sport = :$PORT" | grep -q "$HOST:$PORT"; then
  say "ERROR: $HOST:$PORT still in use after stopping the proxy"
  exit 1
fi

relaunch_server "${CONTAINER:-qwen38-serve}" "$HOST" "$PORT" "$LABEL"
say "rollback complete; the proxy unit is stopped (disable it with: sudo systemctl disable llm-proxy.service)"
