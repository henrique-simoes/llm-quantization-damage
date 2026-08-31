#!/bin/bash
# s9e_chain.sh — Q6_K draft-depth addendum AT THE TRACK A WINDOW (262,144).
#
# WHY THIS EXISTS SEPARATELY FROM S9D: the matched-depth sweep runs at 131,072 and 196,608,
# because matching depth across all four arms required staying at or below Q6_K_XL's 212,992
# ceiling. That leaves the Track A configuration itself -- Q6_K at the full 262,144 window --
# with its throughput resting on ONE 192-token reading at n=4, taken on a `-ts` ratio that was
# selected under n=2, with n=8 never tested anywhere in E12.
#
# Three cells fix that: Q6_K x 262,144 x n in {2,4,8}, three 512-token generations each on the
# verified 248,522-token pad. Outcome either way is useful:
#   - n=4 wins        -> the published number gains a median-of-3 instead of a single sample
#   - n=8 wins        -> the Track A config line changes again, and the `-ts` ratio needs a
#                        re-sweep at the new draft depth (it is not monotone-safe, PN-7)
#   - n=8 fails to load -> the draft context does not fit at the full window, which is the
#                        same 1.19 GiB draft-worker wall DFlash2 is being tested against
#
# Queued behind s9d via a BLOCKING flock on s9d.lock. Neither running script is edited.
set -uo pipefail
E12=/srv/bench/e12
PY=/srv/bench/.venv-evalplus/bin/python
REPO=$HOME/repos/multivac-paper
LOG=$E12/logs/s9e_chain.log
mkdir -p "$E12/logs" "$E12/state" "$E12/s9"
say(){ echo "[$(date -u +%FT%TZ)] $*" | tee -a "$LOG"; }

exec 7>"$E12/state/s9e.lock"
flock -n 7 || { echo "REFUSING: another s9e chain holds the lock"; exit 3; }

sync_git() {
  { mkdir -p "$REPO/data/raw/e12/s9"
    for f in "$E12"/s9/*.json "$E12"/s9/*.jsonl; do
      [ -f "$f" ] && [ "$(stat -c%s "$f")" -lt 5000000 ] && cp -f "$f" "$REPO/data/raw/e12/s9/" 2>/dev/null
    done
    for f in "$E12"/logs/s9*.log; do
      [ -f "$f" ] && cp -f "$f" "$REPO/data/raw/e12/logs/" 2>/dev/null
    done
    cp -f "$E12/experiments/s9d_depthsweep.py" "$REPO/data/raw/e12/harness-src/" 2>/dev/null
    cp -f "$E12/s9e_chain.sh"                  "$REPO/data/raw/e12/harness-src/" 2>/dev/null
    cd "$REPO" && git add -A >/dev/null 2>&1
    git diff --cached --quiet 2>/dev/null || {
      git commit -q -m "data(s9e): autonomous sync — $1" >/dev/null 2>&1
      git pull -q --rebase origin main >/dev/null 2>&1 || true
      git push -q origin main >/dev/null 2>&1 && say "  git: pushed ($1)" || say "  git: push deferred ($1)"
    }
  } || say "  git: sync errored ($1) — ignored"
  return 0
}

say "s9e_chain pid $$ queued — waiting on s9d.lock (the depth sweep must finish first)"
t0=$(date +%s)
exec 6>"$E12/state/s9d.lock"
flock 6                                  # BLOCKS until s9d_chain.sh exits
say "s9d.lock acquired after $(( $(date +%s) - t0 ))s — starting the 262,144 addendum"
sleep 20

if [ -f "$E12/state/s9e_n262k.done" ]; then
  say "=== addendum already done — nothing to do (idempotent) ==="; exit 0
fi

say "=== PHASE s9e_n262k START (3 cells: Q6_K x 262144 x n{2,4,8}, ~40 min) ==="
$PY "$E12/experiments/s9d_depthsweep.py" \
    --arms Q6_K --depths 262144 --ndraft 2,4,8 \
    --out s9e-n262k.json --tag s9e-ndraft-at-262144 \
    > "$E12/logs/s9e_n262k.log" 2>&1
rc=$?
if [ $rc -eq 0 ]; then
  date -u +%FT%TZ > "$E12/state/s9e_n262k.done"
  say "=== PHASE s9e_n262k OK ==="
  grep -E "BEST-N:|ACCEPTANCE:|done:" "$E12/logs/s9e_n262k.log" | sed 's/^/      /' | tee -a "$LOG"
else
  date -u +%FT%TZ > "$E12/state/s9e_n262k.failed"
  say "=== PHASE s9e_n262k FAILED rc=$rc ==="
  tail -12 "$E12/logs/s9e_n262k.log" 2>/dev/null | sed 's/^/      /' | tee -a "$LOG"
fi
sync_git "after s9e 262k draft-depth addendum"

say "=== S9E CHAIN COMPLETE ==="
exit 0
