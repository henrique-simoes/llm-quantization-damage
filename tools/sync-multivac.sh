#!/bin/bash
# sync-multivac.sh — keep the multivac research state synchronized in this repo. ALWAYS.
#   ./tools/sync-multivac.sh pull   # multivac -> data/  (docs, artifacts, logs — run after every stage)
#   ./tools/sync-multivac.sh push   # repo -> multivac   (experiment scripts -> /srv/bench/e12/)
# Rules: pull NEVER deletes local files (--update, no --delete). Documentation is never
# removed. Binary GGUFs/Docker images are never transferred (sha256 manifests instead).
set -uo pipefail
MODE="${1:-pull}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
D="$REPO/data"
MV=multivac
MK="ssh -o BatchMode=yes -o ConnectTimeout=15 $MV"
R="rsync -a --update --max-size=50m -e \"$MK\""
rc=0

pull() {
  mkdir -p "$D"/bench "$D"/watch
  # 1. Documentation of record (canonical lives on multivac)
  $MK 'cat ~/CLAUDE.md' > "$D/CLAUDE.md" 2>/dev/null || { echo "WARN: CLAUDE.md pull failed"; rc=1; }
  rsync -a --update -e "$MK" "$MV:Documents/multivac-paper/data/" "$D/multivac-src/" || rc=1
  # 2. Bench artifacts (JSON/TXT/CSV at /srv/bench root)
  rsync -a --update --max-size=50m --include='*.json' --include='*.txt' --include='*.csv' --exclude='*' -e "$MK" "$MV:/srv/bench/" "$D/bench/" || rc=1
  # 3. Experiment trees + server logs (the "save all logs" evidence trail)
  for t in e11 e12 server-timings perplexity swebench-results evalplus_results splitmode-repro.json env-manifest.json; do
    rsync -a --update --max-size=50m -e "$MK" "$MV:/srv/bench/$t" "$D/bench/" 2>/dev/null || true
  done
  # 4. Champion summaries only (raw/ is 184K files — stay out; timings JSON covers it)
  rsync -a --update --max-size=10m --include='*.json' --exclude='*' -e "$MK" "$MV:/srv/bench/champion-20260821/" "$D/bench/champion-20260821/" 2>/dev/null || true
  echo "pull complete -> $D (rc=$rc)"
}

push() {
  # Experiment scripts authored in the repo -> multivac execution area
  [ -d "$REPO/experiments" ] && rsync -a --update -e "$MK" "$REPO/experiments/" "$MV:/srv/bench/e12/experiments/" || true
  # Paper repo docs -> multivac mirror folder (lifecycle, instructions, paper notes)
  rsync -a --update -e "$MK" "$REPO/docs/" "$MV:Documents/multivac-paper/data/build-stream-docs/" || true
  echo "push complete (rc=$rc)"
}

case "$MODE" in
  pull) pull ;;
  push) push ;;
  both) pull; push ;;
  *) echo "usage: $0 pull|push|both"; exit 2 ;;
esac
exit $rc
