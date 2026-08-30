#!/bin/bash
# fetch_s7.sh — fetch the two external eval datafiles SSA step S7 needs, with provenance.
#
# `llama-perplexity` ships --hellaswag and --winogrande, but NOT their data; both must be
# supplied with -f. These are the canonical files llama.cpp's own get-hellaswag.sh /
# get-winogrande.sh scripts fetch. Owner-approved 2026-08-30.
#
# Everything that enters the paper needs provenance, downloaded data included: URL, HTTP
# status, byte count, sha256 and fetch time all land in s7-data-provenance.json next to the
# files, so a reader can verify they got the same corpus we scored against.
set -uo pipefail
DEST=/srv/bench/corpus
PROV=$DEST/s7-data-provenance.json
LOG=/srv/bench/e12/logs/s7_fetch.log
mkdir -p "$DEST" /srv/bench/e12/logs
say(){ echo "[$(date -u +%FT%TZ)] $*" | tee -a "$LOG"; }

declare -A URLS=(
  [hellaswag_val_full.txt]="https://raw.githubusercontent.com/klosax/hellaswag_text_data/main/hellaswag_val_full.txt"
  [winogrande-debiased-eval.csv]="https://huggingface.co/datasets/ikawrakow/winogrande-eval-for-llama.cpp/resolve/main/winogrande-debiased-eval.csv"
)
entries=""
rc=0
for f in "${!URLS[@]}"; do
  u="${URLS[$f]}"
  say "fetching $f from $u"
  code=$(curl -sL --max-time 300 -w '%{http_code}' -o "$DEST/$f.part" "$u" 2>>"$LOG")
  if [ "$code" != "200" ]; then say "  FAILED http=$code"; rm -f "$DEST/$f.part"; rc=1; continue; fi
  mv "$DEST/$f.part" "$DEST/$f"
  b=$(stat -c%s "$DEST/$f"); h=$(sha256sum "$DEST/$f" | cut -d' ' -f1); l=$(wc -l < "$DEST/$f")
  say "  ok http=200 bytes=$b lines=$l sha256=$h"
  entries="$entries{\"file\":\"$f\",\"url\":\"$u\",\"http\":200,\"bytes\":$b,\"lines\":$l,\"sha256\":\"$h\",\"fetched_utc\":\"$(date -u +%FT%TZ)\"},"
done
cat > "$PROV" <<JSON
{
 "record": "s7-external-eval-data",
 "purpose": "datafiles for llama-perplexity --hellaswag / --winogrande (SSA step S7)",
 "note": "llama-perplexity ships the FLAGS but not the DATA; these are the files llama.cpp's own get-hellaswag.sh / get-winogrande.sh fetch. Downloaded with owner approval 2026-08-30.",
 "caution": "third-party corpora, not produced by this project: cite by URL + sha256, and treat any score against them as comparable only to other runs on the SAME sha256.",
 "created_utc": "$(date -u +%FT%TZ)",
 "files": [ ${entries%,} ]
}
JSON
say "provenance -> $PROV"
cat "$PROV"
exit $rc
