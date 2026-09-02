#!/bin/bash
# s12_mkniah_generate.sh — REGENERATES the MK-NIAH dataset behind PN-33/PN-34.
#
# Recorded 2026-09-02 after two independent reviews found the dataset present but its generating
# command absent from the repository: s12_ruler.py's mk131072 phase READS a pre-generated file, and
# the dataset was originally produced by an ad-hoc shell invocation that existed nowhere. Without
# this file the multi-key result cannot be reproduced from the public repo.
#
# Multi-key NIAH = RULER's standard harder retrieval variant: 4 distractor keys instead of 1.
set -euo pipefail
GEN=/srv/bench/RULER/scripts/data/synthetic
PY=/srv/bench/.venv-evalplus/bin/python
TPL=$($PY -c "import sys; sys.path.insert(0,'$GEN'); import constants; print(constants.TASKS['niah']['template'])")
cd "$GEN"
$PY niah.py \
  --save_dir /srv/bench/e12/ruler/data --save_name mkniah_131072 \
  --tokenizer_path /srv/engines/nvfp4 --tokenizer_type hf \
  --max_seq_length 131072 --tokens_to_generate 128 --num_samples 12 \
  --type_haystack noise --type_needle_k words --type_needle_v numbers \
  --num_needle_k 4 --num_needle_v 1 --num_needle_q 1 \
  --random_seed 42 --template "$TPL"
