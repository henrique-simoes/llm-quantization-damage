#!/bin/bash
# sync-multivac.sh — DOCUMENTATION synchronization between multivac and this paper repo.
#   ./tools/sync-multivac.sh pull              # docs of record multivac -> repo data/
#   ./tools/sync-multivac.sh push              # repo docs + experiment scripts -> multivac
#   ./tools/sync-multivac.sh artifact /srv/bench/e12/foo.json data/raw/e12/   # selective, per-need
# SCOPE (owner directive 2026-08-30): ONLY documentation — CLAUDE.md, PAPER-REFERENCES.md,
# the multivac paper-data folder, and this repo's docs. NOT models, containers, images, or
# bulk artifact trees; those stay on multivac and are pulled selectively when a specific
# artifact is needed as paper evidence (artifact command below).
# Transport: tar-over-ssh (multivac has no rsync). Pull NEVER deletes local files.
set -uo pipefail
MODE="${1:-pull}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
D="$REPO/data"
H=multivac
SSHOPT="ssh -o BatchMode=yes -o ConnectTimeout=15"
rc=0

pull() {
  mkdir -p "$D"/multivac-src "$D"/watch
  # 1. CLAUDE.md — the machine's project documentation of record
  $SSHOPT $H 'cat ~/CLAUDE.md' > "$D/CLAUDE.md" 2>/dev/null || { echo "WARN: CLAUDE.md pull failed"; rc=1; }
  # 2. The multivac paper-data folder (PAPER-REFERENCES.md + mirrors)
  $SSHOPT $H "cd 'Documents/multivac-paper/data' && find . \\( -name '*.md' -o -name '*.json' -o -name '*.txt' -o -name '*.sh' -o -name '*.py' \\) -type f -print0 2>/dev/null | tar czf - --null -T -" | tar xzf - -C "$D/multivac-src" 2>/dev/null || rc=1
  echo "documentation pull complete (rc=$rc)"
}

push() {
  # Repo docs (lifecycle, instructions, paper notes) -> multivac mirror folder
  tar czf - -C "$REPO" docs | $SSHOPT $H 'mkdir -p ~/Documents/multivac-paper/data/build-stream-docs && tar xzf - -C ~/Documents/multivac-paper/data/build-stream-docs' || rc=1
  # Experiment scripts authored in the repo -> multivac execution area
  if [ -d "$REPO/experiments" ]; then
    tar czf - -C "$REPO" experiments | $SSHOPT $H 'mkdir -p /srv/bench/e12 && tar xzf - -C /srv/bench/e12' || rc=1
  fi
  echo "push complete (rc=$rc)"
}

artifact() { # artifact <remote-path> <local-dest-dir> — selective evidence pull
  local rpath="$1" dest="$2"; mkdir -p "$dest"
  $SSHOPT $H "tar czf - -C \"\$(dirname '$rpath')\" \"\$(basename '$rpath')\"" | tar xzf - -C "$dest" && echo "artifact $rpath -> $dest" || { echo "artifact pull FAILED: $rpath"; rc=1; }
}

case "$MODE" in
  pull) pull ;;
  push) push ;;
  artifact) shift; artifact "$@" ;;
  both) pull; push ;;
  *) echo "usage: $0 pull|push|both|artifact <remote-path> <local-dir>"; exit 2 ;;
esac
exit $rc
