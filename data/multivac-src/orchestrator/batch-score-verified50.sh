#!/bin/bash
# /srv/bench/orchestrator/batch-score-verified50.sh
# Scores verified50 predictions in batches, pruning eval images between batches
# to stay within disk limits. Each batch: eval N instances, prune their images.
# Results accumulate in a single run directory.
set -euo pipefail

SWEBENCH=/srv/bench/.venv-swebench/bin
D=/srv/bench/swebench-results/verified50
BATCH_SIZE=8
RUN_ID="verified50-score"
LOG="$D/eval.log"

# Get all instance IDs with patches
INSTANCES=$(python3 -c "
import json
d=json.load(open('$D/preds.json'))
for iid, v in sorted(d.items()):
    if isinstance(v, dict) and v.get('model_patch','').strip():
        print(iid)
")

total=$(echo "$INSTANCES" | wc -l)
echo "$(date -Iseconds) | batch-score: $total instances to evaluate in batches of $BATCH_SIZE"

# Process in batches
batch_num=0
echo "$INSTANCES" | while mapfile -t -n $BATCH_SIZE batch && [ ${#batch[@]} -gt 0 ]; do
  batch_num=$((batch_num + 1))
  count=${#batch[@]}
  echo "$(date -Iseconds) | batch $batch_num: $count instances"

  # Build -i flags
  inst_flags=""
  for iid in "${batch[@]}"; do
    inst_flags="$inst_flags -i $iid"
  done

  # Run evaluation for this batch
  timeout 7200 $SWEBENCH/swebench eval verified \
    -p "$D/preds.json" \
    --run-id "$RUN_ID" \
    -j 1 \
    $inst_flags \
    >> "$LOG" 2>&1 || true

  echo "$(date -Iseconds) | batch $batch_num done, pruning eval images"

  # Prune eval images for this batch (keep only images used by running containers)
  for iid in "${batch[@]}"; do
    # Image name pattern: swebench/sweb.eval.x86_64.<repo>_<num>_<instance>:latest
    img=$(docker images --format "{{.Repository}}:{{.Tag}}" 2>/dev/null | grep "$iid" || true)
    if [ -n "$img" ]; then
      docker rmi "$img" 2>/dev/null || true
    fi
  done

  # Also prune any dangling images
  docker image prune -f >/dev/null 2>&1 || true

  free=$(df --output=avail -BG / | tail -1 | tr -dc '0-9')
  echo "$(date -Iseconds) | disk: ${free}G free after prune"
done

echo "$(date -Iseconds) | batch-score: COMPLETE"
grep -E "Instances (completed|resolved|unresolved|with errors)" "$LOG" 2>/dev/null | tail -4
