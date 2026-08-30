#!/bin/bash
# supervisor.sh — autonomous driver for the remainder of the Wave-1 + SSA plan.
#
# CONTRACT (owner directive 2026-08-30, "keep going even if the agent is gone"):
#   * every step runs even if the previous one FAILED — a failure is logged, marked and
#     SKIPPED, never fatal, so the chain gets as far as it possibly can unattended
#   * every step's full stdout+stderr goes to its own log under logs/
#   * every step's outcome lands in state/progress.json for a returning agent to read
#   * results are committed and pushed to the private git hub as they land, so nothing
#     depends on this process surviving
#   * idempotent and resumable: a step with a .done marker is skipped on restart
#
# The ONE exception to "continue past failure" is the SSA S0 smoke gate: if the 4-chunk
# smoke fails, S1-S4 are skipped by design (small-tests-first is a hard rule) — but the
# supervisor still continues to the sync and report steps rather than dying.
set -uo pipefail

E12=/srv/bench/e12
STATE=$E12/state
LOGS=$E12/logs
REPO=$HOME/repos/multivac-paper
PY=/srv/bench/.venv-evalplus/bin/python
PROGRESS=$STATE/progress.json
SUPLOG=$E12/supervisor.log

mkdir -p "$STATE" "$LOGS" "$E12/ssa"

exec 9>"$STATE/supervisor.lock"
if ! flock -n 9; then echo "REFUSING: another supervisor holds the lock"; exit 3; fi

log(){ echo "[$(date -u +%FT%TZ)] $*" | tee -a "$SUPLOG"; }

# ---------- progress.json ----------------------------------------------------
py_progress() {
  "$PY" - "$@" <<'PYEOF'
import json, os, sys, time
p = "/srv/bench/e12/state/progress.json"
d = {"updated_utc": "", "supervisor_pid": None, "steps": []}
if os.path.exists(p):
    try: d = json.load(open(p))
    except Exception: pass
op = sys.argv[1]
if op == "init":
    d["supervisor_pid"] = int(sys.argv[2]); d["started_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
elif op == "step":
    name, status, rc, logf, note = sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]
    d["steps"] = [s for s in d.get("steps", []) if s.get("name") != name]
    d["steps"].append({"name": name, "status": status, "rc": int(rc), "log": logf,
                       "note": note, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
elif op == "done":
    d["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    ok = sum(1 for s in d.get("steps", []) if s["status"] == "ok")
    fl = [s["name"] for s in d.get("steps", []) if s["status"] == "failed"]
    sk = [s["name"] for s in d.get("steps", []) if s["status"] == "skipped"]
    d["summary"] = {"ok": ok, "failed": fl, "skipped": sk}
d["updated_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
json.dump(d, open(p, "w"), indent=1)
PYEOF
}

# ---------- run one step, never fatal ----------------------------------------
# usage: step <name> <command...>
step() {
  local name="$1"; shift
  if [ -f "$STATE/$name.done" ]; then
    log "SKIP $name (already done)"; py_progress step "$name" ok 0 "-" "pre-existing .done marker"; return 0
  fi
  local logf="$LOGS/$name.log"
  log "=== STEP $name START ==="
  log "    cmd: $*"
  ( "$@" ) > "$logf" 2>&1
  local rc=$?
  if [ $rc -eq 0 ]; then
    date -u +%Y-%m-%dT%H:%M:%SZ > "$STATE/$name.done"; rm -f "$STATE/$name.failed"
    log "=== STEP $name OK (rc=0) -> $logf ==="
    py_progress step "$name" ok 0 "$logf" ""
  else
    date -u +%Y-%m-%dT%H:%M:%SZ > "$STATE/$name.failed"
    log "=== STEP $name FAILED rc=$rc — LOGGED AND SKIPPED, chain continues -> $logf ==="
    log "    last 5 lines:"; tail -5 "$logf" 2>/dev/null | sed 's/^/      /' | tee -a "$SUPLOG"
    py_progress step "$name" failed "$rc" "$logf" "skipped, continuing"
  fi
  sync_to_git "after $name"
  return 0            # NEVER propagate failure
}

mark_skipped() { log "=== STEP $1 SKIPPED: $2 ==="; py_progress step "$1" skipped 0 "-" "$2"; }

# ---------- git sync: best-effort, never fatal -------------------------------
sync_to_git() {
  local why="${1:-periodic}"
  {
    mkdir -p "$REPO/data/raw/e12/ssa" "$REPO/data/raw/e12/logs" "$REPO/data/raw/e12/quarantine"
    # small artifacts only — .gitignore is the backstop, this is the first filter
    for f in "$E12"/*.json "$E12"/*.md "$E12"/state/progress.json; do
      [ -f "$f" ] && [ "$(stat -c%s "$f")" -lt 5000000 ] && cp -f "$f" "$REPO/data/raw/e12/" 2>/dev/null
    done
    for f in "$E12"/ssa/*.json; do
      [ -f "$f" ] && [ "$(stat -c%s "$f")" -lt 5000000 ] && cp -f "$f" "$REPO/data/raw/e12/ssa/" 2>/dev/null
    done
    for f in "$E12"/*.log "$LOGS"/*.log; do
      [ -f "$f" ] && [ "$(stat -c%s "$f")" -lt 5000000 ] && cp -f "$f" "$REPO/data/raw/e12/logs/" 2>/dev/null
    done
    cp -f "$E12"/../env-manifest.json "$REPO/data/raw/e12/" 2>/dev/null
    cd "$REPO" || exit 0
    git add -A >/dev/null 2>&1
    if ! git diff --cached --quiet 2>/dev/null; then
      git commit -q -m "data(e12): autonomous sync — $why

Committed by supervisor.sh on multivac while unattended." >/dev/null 2>&1
      git pull -q --rebase origin main >/dev/null 2>&1 || true
      git push -q origin main >/dev/null 2>&1 && log "  git: pushed ($why)" || log "  git: push failed ($why) — commit kept locally, will retry"
    fi
  } || log "  git: sync errored ($why) — ignored, chain continues"
  return 0
}

# ---------- wait helpers -----------------------------------------------------
wait_for_gpu_free() {
  log "waiting for GPU work to finish (sweep / llamasrv-e12)"
  local waited=0
  while pgrep -f "tsweep_v2\.py|runner_wave1\.sh sweep" >/dev/null 2>&1; do
    sleep 60; waited=$((waited+60))
    if [ $((waited % 1800)) -eq 0 ]; then log "  still waiting (${waited}s)"; sync_to_git "heartbeat"; fi
    if [ $waited -gt 43200 ]; then log "  GIVING UP after 12 h — proceeding anyway"; break; fi
  done
  log "GPU work finished after ${waited}s"
  sleep 45     # container teardown + serverlog flush
}

# ============================ MAIN ===========================================
log "################ SUPERVISOR START pid $$ ################"
py_progress init "$$"
log "plan: wait for sweep -> summarize -> verify-1a -> SSA S0 gate -> S1..S4 -> report"
log "policy: a failing step is logged and SKIPPED; the chain continues regardless"

# Stand down any older single-purpose chain runners — this supervisor supersedes them.
for old in ssa_runner.sh finish_wave1.sh; do
  for pid in $(pgrep -f "$old" 2>/dev/null); do
    log "superseding $old (pid $pid)"; kill -TERM "$pid" 2>/dev/null
  done
done
sleep 3

wait_for_gpu_free

step summarize   "$PY" "$E12/experiments/summarize_wave1.py" --md
step verify_1a   bash  "$E12/experiments/verify-sweep.sh" --stage 1a

# SSA S0 is a real gate (small-tests-first). Its failure skips S1-S4 but not the rest.
step ssa_S0      "$PY" "$E12/experiments/ssa_kld.py" --step S0 --out "$E12/ssa/ssa-smoke.json"

if [ -f "$STATE/ssa_S0.done" ]; then
  log "S0 gate GREEN — running the SSA budget"
  step ssa_S1 "$PY" "$E12/experiments/ssa_kld.py" --step S1 --out "$E12/ssa/ssa-results.json"
  step ssa_S2 "$PY" "$E12/experiments/ssa_kld.py" --step S2 --out "$E12/ssa/ssa-results.json"
  step ssa_S3 "$PY" "$E12/experiments/ssa_kld.py" --step S3 --out "$E12/ssa/ssa-results.json"
  step ssa_S4 "$PY" "$E12/experiments/ssa_kld.py" --step S4 --out "$E12/ssa/ssa-results.json"
else
  for s in ssa_S1 ssa_S2 ssa_S3 ssa_S4; do
    mark_skipped "$s" "S0 smoke gate did not pass — small-tests-first is a hard rule"
  done
fi

log "=== disk check (SSA .kld logits are ~11 GB each) ==="
{ df -h / /srv/models; du -sh "$E12/ssa" 2>/dev/null; } | tee -a "$SUPLOG"

py_progress done
sync_to_git "final"

log "################ SUPERVISOR COMPLETE ################"
"$PY" -c "
import json;d=json.load(open('$PROGRESS'))
s=d.get('summary',{})
print('ok:',s.get('ok'),'| failed:',s.get('failed'),'| skipped:',s.get('skipped'))
for x in d['steps']: print(f\"  {x['status']:<8} {x['name']:<12} rc={x['rc']:<4} {x['note']}\")
" 2>&1 | tee -a "$SUPLOG"
log "A .failed marker means that step was skipped for a human. Read its log before re-running."
exit 0
