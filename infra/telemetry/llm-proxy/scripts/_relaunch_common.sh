# Shared by run-qwen38-loopback.sh and rollback-proxy.sh. Source, do not execute.
# relaunch_server CONTAINER HOST PORT LABEL
#   1. saves `docker inspect` and `docker logs` to /srv/bench/server-timings/ (logs FIRST —
#      hard rule: a container is never removed before its logs are on disk)
#   2. rebuilds the run command from inspect with only --host/--port changed
#   3. stops + removes the container and runs the rebuilt command
#   4. waits for /health 200 and asserts /props n_ctx == the -c value

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMINGS_DIR="${TIMINGS_DIR:-/srv/bench/server-timings}"
HEALTH_TIMEOUT_S="${HEALTH_TIMEOUT_S:-1800}"

say() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >&2; }

relaunch_server() {
  local name="$1" host="$2" port="$3" label="$4"
  local stamp; stamp="$(date -u +%Y%m%dT%H%MZ)"
  local base="$TIMINGS_DIR/${name}-${label}-${stamp}"
  local tmp; tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  docker inspect "$name" > "$tmp/inspect.json"
  local image; image="$(python3 -c 'import json,sys;print(json.load(sys.stdin)[0]["Image"])' < "$tmp/inspect.json")"
  docker image inspect "$image" > "$tmp/image.json"

  # Build and validate the new command BEFORE touching the container.
  python3 "$SCRIPT_DIR/relaunch_args.py" --host "$host" --port "$port" \
    --image-env-json "$tmp/image.json" < "$tmp/inspect.json" > "$tmp/argv0"
  local ctx; ctx="$(python3 "$SCRIPT_DIR/relaunch_args.py" --host x --port 0 --print-ctx < "$tmp/inspect.json")"
  mapfile -d '' -t argv < "$tmp/argv0"
  say "new command: ${argv[*]}"

  mkdir -p "$TIMINGS_DIR"
  cp "$tmp/inspect.json" "${base}.inspect.json"
  docker logs --timestamps "$name" > "${base}.serverlog" 2>&1
  if [ ! -s "${base}.serverlog" ]; then
    say "ERROR: saved serverlog is empty (${base}.serverlog); refusing to remove the container"
    return 1
  fi
  say "saved logs: ${base}.serverlog ($(wc -c < "${base}.serverlog") bytes)"

  docker stop -t 30 "$name" >/dev/null
  docker rm "$name" >/dev/null
  "${argv[@]}" >/dev/null
  say "started $name on $host:$port; waiting for /health (timeout ${HEALTH_TIMEOUT_S}s)"

  local deadline=$(( $(date +%s) + HEALTH_TIMEOUT_S ))
  until [ "$(curl -s -o /dev/null -w '%{http_code}' "http://$host:$port/health" || true)" = "200" ]; do
    if [ "$(docker inspect -f '{{.State.Running}}' "$name" 2>/dev/null || echo false)" != "true" ]; then
      docker logs --timestamps "$name" > "${base}.failed-start.serverlog" 2>&1 || true
      say "ERROR: container exited during load; logs: ${base}.failed-start.serverlog"
      return 1
    fi
    if [ "$(date +%s)" -ge "$deadline" ]; then
      say "ERROR: /health not 200 after ${HEALTH_TIMEOUT_S}s"
      return 1
    fi
    sleep 5
  done

  local n_ctx
  n_ctx="$(curl -s "http://$host:$port/props" | python3 -c 'import json,sys;print(json.load(sys.stdin)["default_generation_settings"]["n_ctx"])')"
  if [ -n "$ctx" ] && [ "$n_ctx" != "$ctx" ]; then
    say "ERROR: /props n_ctx=$n_ctx but launch -c $ctx"
    return 1
  fi
  say "OK: $name healthy on $host:$port, n_ctx=$n_ctx"
}
