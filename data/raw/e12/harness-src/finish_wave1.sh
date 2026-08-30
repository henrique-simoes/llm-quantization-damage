#!/bin/bash
# finish_wave1.sh — post-sweep tail for Wave 1. Added 2026-08-30 (ledger L-5).
#
# runner_wave1.sh stops after its tsweeps; nothing chained to the closing steps, so the wave
# would sit idle waiting for a human. This waits for the live runner to exit, then runs the two
# REVERSIBLE closing steps:
#   1. summarize_wave1.py           — aggregate the tsweep JSONs into the wave's answer
#   2. verify-sweep.sh --stage 1a   — sha256s ~60 GB; MUST NOT run during a measurement
#
# It deliberately STOPS before T3b delete-1b. Deleting Q6_K_XL (25,299,061,664 B) is
# irreversible and the plan's docs-before-delete gate requires its bracket results in the
# ledger first. The D3 -ctxcp 4-vs-32 A/B (A8) needs nothing here — tsweep_v2 runs it inside
# the Q6_K sweep automatically.
set -uo pipefail
E12=/srv/bench/e12
PY=/srv/bench/.venv-evalplus/bin/python
WATCH_PID="${1:?usage: finish_wave1.sh <runner-pid>}"
cd "$E12" || exit 1
mkdir -p "$E12/state"

exec 9>"$E12/state/finish.lock"
flock -n 9 || { echo "REFUSING: another finisher already holds the lock"; exit 3; }

log(){ echo "[$(date -u +%FT%TZ)] $*"; }
log "finisher pid $$ watching runner pid $WATCH_PID"
while kill -0 "$WATCH_PID" 2>/dev/null; do sleep 60; done
log "runner $WATCH_PID exited"
sleep 45   # let the last container tear down and its serverlog flush to disk

log "state markers:"; ls -1 "$E12/state" | sed 's/^/    /'
log "tsweep artifacts:"; ls -la "$E12"/tsweep-v2-*.json 2>/dev/null | sed 's/^/    /'

log "=== 1/2 summarize_wave1.py ==="
$PY experiments/summarize_wave1.py --md; rc_sum=$?
log "summarize rc=$rc_sum"

log "=== 2/2 verify-sweep.sh --stage 1a (GPU work has stopped; sha256 is safe now) ==="
bash experiments/verify-sweep.sh --stage 1a; rc_ver=$?
log "verify-sweep rc=$rc_ver"

log "=== FINISHER DONE (summarize rc=$rc_sum, verify rc=$rc_ver) ==="
log "NOT run by design: T3b delete-1b (Q6_K_XL, 25,299,061,664 B -> carries /srv/models past"
log "  the >=60e9 B A3 gate) and the 1b byte gate. Irreversible; owner-gated on the bracket"
log "  results reaching the ledger. Everything else in Wave 1 is now closed."
exit 0
