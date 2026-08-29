#!/bin/bash
# /srv/bench/orchestrator/worker.sh
# Durable benchmark worker for multivac. Survives client/session death.
# Idempotent: every job checks its own completion first, so restarting is always safe.
# Priority order is deliberate -- cheapest recoverable data first, GPU work last.
source /srv/bench/orchestrator/lib.sh
exec >> "$ORCH/worker.stdout" 2>&1
echo "===== WORKER START $(ts) pid=$$ ====="
echo $$ > "$ORCH/worker.pid"

SWEBENCH=/srv/bench/.venv-swebench/bin
SWE=/srv/bench/swebench-results

# ------------------------------------------------------------------
# JOB 1 -- score the SWE-bench thinking runs (CPU only, images local)
# These have patches but were never evaluated; "Submitted" != "resolved".
# ------------------------------------------------------------------
job_score_thinking() {
  local J=score-thinking
  job_done $J && return 0
  mark_start $J
  for cfg in mtp-IQ4_XS mtp-Q4_K_XL mtp-Q5_K_XL mtp-Q6_K_XL dflash-IQ4_XS dflash-Q4_K_XL; do
    local D="$SWE/thinking/$cfg"
    [ -f "$D/preds.json" ] || { jlog $J "skip $cfg (no preds)"; continue; }
    grep -q "Instances resolved" "$D/eval.log" 2>/dev/null && { jlog $J "skip $cfg (scored)"; continue; }
    jlog $J "scoring $cfg"
    timeout 3600 $SWEBENCH/swebench eval verified -p "$D/preds.json" --run-id "sc-$cfg" \
      > "$D/eval.log" 2>&1
    jlog $J "$cfg -> $(grep -E 'Instances (completed|resolved)' "$D/eval.log" 2>/dev/null | tr '\n' ' ')"
  done
  mark_done $J
}

# ------------------------------------------------------------------
# JOB 2 -- score verified50 (a FULL 50-instance run, 49 patches, never scored)
# Needs ~50 eval images at ~4 GB each, so pull/score/prune in batches to
# respect the disk. Aborts safely if free space drops too low.
# ------------------------------------------------------------------
job_score_verified50() {
  local J=score-verified50
  job_done $J && return 0
  local D="$SWE/verified50"
  [ -f "$D/preds.json" ] || { jlog $J "no preds.json"; return 0; }
  local free; free=$(df --output=avail -BG / | tail -1 | tr -dc '0-9')
  if [ "${free:-0}" -lt 30 ]; then
    jlog $J "DEFER: only ${free}G free, need >=30G for batched eval"
    return 0
  fi
  mark_start $J
  jlog $J "starting batch scoring (49 instances in batches of 8)"
  timeout 43200 bash "$ORCH/batch-score-verified50.sh" >> "$LOGS/$J.log" 2>&1
  jlog $J "-> $(grep -E 'Instances (completed|resolved|unresolved|with errors)' "$D/eval.log" 2>/dev/null | tr '\n' ' ')"
  mark_done $J
}

# ------------------------------------------------------------------
# JOB 3 -- agentic step-count profile (T3 style) for IQ4_XS and Q5_K_XL.
# THE decisive missing datum: Q3 loops to the 250-step limit while Q6
# converges in ~45 steps. We have no equivalent for IQ4_XS or Q5_K_XL,
# and the model recommendation depends on it. GPU job.
# ------------------------------------------------------------------
job_agentic_steps() {
  local J=agentic-steps
  job_done $J && return 0
  gpu_busy && { jlog $J "waiting: GPU busy"; return 0; }
  mark_start $J; gpu_acquire
  local INSTANCES="astropy__astropy-12907|django__django-10880|django__django-10973"
  for q in IQ4_XS Q5_K_XL; do
    local label="agentic-$q" out="$SWE/agentic-steps/$q"
    [ -f "$out/preds.json" ] && { jlog $J "skip $q (exists)"; continue; }
    mkdir -p "$out"
    kill_server llamasrv ""
    docker run -d --name llamasrv --gpus all --network host -v /srv/models:/models:ro \
      llamacpp-mtp:latest -m "/models/Qwen3.8-27B-UD-${q}.gguf" \
      -ngl 99 --split-mode layer --ctx-size 131072 --cache-type-k q4_0 --cache-type-v q4_0 \
      -np 1 --seed 20260825 --reasoning-format deepseek --reasoning on \
      --spec-type draft-mtp --spec-draft-n-max 2 --port 8080 --host 0.0.0.0 >/dev/null 2>&1
    if ! wait_health 8080 900; then
      jlog $J "$q FAILED to start"; kill_server llamasrv "$label"; continue
    fi
    jlog $J "$q server up, running agentic instances"
    cat > "$out/config.yaml" <<YAML
model:
  cost_tracking: ignore_errors
  model_name: hosted_vllm/Qwen3.8-27B-UD-${q}
  model_kwargs:
    drop_params: true
    parallel_tool_calls: true
    api_base: http://localhost:8080/v1
    api_key: dummy-key-12345
YAML
    ( cd /srv/bench && OPENAI_API_KEY=dummy-key-12345 timeout 14400 \
      $SWEBENCH/python -m minisweagent.run.benchmarks.swebench \
      -c swebench.yaml -c "$out/config.yaml" --subset verified --split test \
      --filter "$INSTANCES" --output "$out" --redo-existing ) > "$out/run.log" 2>&1
    # step counts are the whole point of this job
    python3 - "$out" <<'PY' >> "$out/steps.txt" 2>/dev/null
import json,glob,sys,os
d=sys.argv[1]
for f in glob.glob(os.path.join(d,"*","*.traj.json")):
    try:
        t=json.load(open(f)); m=t.get("messages",t)
        steps=sum(1 for x in m if isinstance(x,dict) and x.get("role")=="assistant")
        print(f"{os.path.basename(os.path.dirname(f))}: {steps} assistant steps")
    except Exception as e: print(f"{f}: ERR {e}")
PY
    jlog $J "$q steps -> $(tr '\n' ' ' < "$out/steps.txt" 2>/dev/null)"
    kill_server llamasrv "$label"
  done
  gpu_release
  mark_done $J
}

# ------------------------------------------------------------------
# JOB 4 -- bootstrap confidence intervals (CPU only, pure analysis).
# Required before ANY ordering claim in the report.
# ------------------------------------------------------------------
job_bootstrap() {
  local J=bootstrap-ci
  job_done $J && return 0
  mark_start $J
  python3 /srv/bench/bootstrap-ci.py > /srv/bench/bootstrap-ci.json 2>> "$LOGS/$J.log"
  jlog $J "wrote bootstrap-ci.json"
  mark_done $J
}


# ------------------------------------------------------------------
# JOB 5 -- NVFP4 perplexity via vLLM logprobs (GPU job).
# llama-perplexity is GGUF-only; this uses vLLM's echo+logprobs API
# to compute PPL on WikiText-2 (Protocol 2, 20 chunks @4096).
# ------------------------------------------------------------------
job_nvfp4_ppl() {
  local J=nvfp4-ppl
  job_done $J && return 0
  gpu_busy && { jlog $J "waiting: GPU busy"; return 0; }
  mark_start $J; gpu_acquire
  jlog $J "starting NVFP4 perplexity"
  timeout 7200 bash "$ORCH/nvfp4-perplexity.sh" >> "$LOGS/$J.log" 2>&1
  local rc=$?
  gpu_release
  if [ $rc -eq 0 ] && [ -f /srv/bench/perplexity/nvfp4-vllm-ppl.json ]; then
    jlog $J "DONE: $(python3 -c 'import json; d=json.load(open("/srv/bench/perplexity/nvfp4-vllm-ppl.json")); print("PPL=%.4f n=%d" % (d["perplexity"], d["n_tokens"]))' 2>/dev/null)"
    mark_done $J
  else
    jlog $J "FAILED (exit $rc)"
  fi
}

# ------------------------------------------------------------------
# main loop -- re-evaluates the queue every 5 minutes, forever.
# ------------------------------------------------------------------
while true; do
  job_score_thinking
  job_bootstrap
  job_agentic_steps
  job_score_verified50
  job_nvfp4_ppl
  snapshot_metrics

  if job_done score-thinking && job_done bootstrap-ci && job_done agentic-steps; then
    if (job_done score-verified50 || [ -f "$STATE/score-verified50.deferred" ]) && job_done nvfp4-ppl; then
      echo "$(ts) | ALL QUEUED JOBS COMPLETE" >> "$ORCH/worker.log"
    fi
  fi
  sleep 300
done
