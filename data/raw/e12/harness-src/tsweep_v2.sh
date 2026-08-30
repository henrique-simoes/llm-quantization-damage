#!/bin/bash
# tsweep_v2.sh — thin driver: run the -ts rebalance sweep for one quant (or all four).
#   bash tsweep_v2.sh Q4_K_XL          # single quant
#   bash tsweep_v2.sh all              # Q4_K_XL, Q5_K_XL, Q6_K, then the G21 Q6_K_XL bracket
# Resumable; cells land in /srv/bench/e12/tsweep-v2-<quant>.json incrementally.
set -uo pipefail
E12=/srv/bench/e12
PY=/srv/bench/.venv-evalplus/bin/python
Q="${1:-all}"
run() { $PY "$E12/experiments/tsweep_v2.py" --quant "$1" --out "$E12/tsweep-v2-$1.json"; }
case "$Q" in
  all) rc=0; for q in Q4_K_XL Q5_K_XL Q6_K Q6_K_XL; do run "$q" || rc=1; done; exit $rc ;;
  *) run "$Q"; exit $? ;;
esac
