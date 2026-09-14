#!/usr/bin/env bash
# D5 cut-over, server half: relaunch qwen38-serve with EXACTLY its current `docker inspect`
# arguments except --host 127.0.0.1 --port 18080 (--metrics kept). Logs are saved first to
# /srv/bench/server-timings/qwen38-serve-<label>-<UTCstamp>.serverlog.
# Afterwards start the proxy: sudo systemctl start llm-proxy.service
#
# Usage: run-qwen38-loopback.sh [LABEL]        (default label: pre-loopback)
# Env:   CONTAINER (qwen38-serve) LOOPBACK_HOST (127.0.0.1) LOOPBACK_PORT (18080)
source "$(dirname "$0")/_relaunch_common.sh"

relaunch_server "${CONTAINER:-qwen38-serve}" "${LOOPBACK_HOST:-127.0.0.1}" \
  "${LOOPBACK_PORT:-18080}" "${1:-pre-loopback}"
