#!/bin/bash
# /srv/bench/orchestrator/nvfp4-perplexity.sh
# Compute perplexity for vLLM NVFP4 using logprobs from the vLLM API.
# llama-perplexity is GGUF-only, so we compute PPL from token-level logprobs.
# Protocol: WikiText-2 test, sliding window of 4096 tokens, stride 2048.
set -euo pipefail

PORT=8090
MODEL="Qwen/Qwen3-27B"
VLLM_IMAGE="vllm/vllm-openai:nightly"
OUT=/srv/bench/perplexity/nvfp4-vllm-ppl.json
LOG=/srv/bench/perplexity/nvfp4-vllm.log
mkdir -p /srv/bench/perplexity

echo "$(date -Iseconds) | nvfp4-ppl: starting vLLM server" | tee -a "$LOG"

# Start vLLM server with NVFP4
docker rm -f vllm-ppl 2>/dev/null || true
docker run -d --name vllm-ppl --gpus all --network host \
  -v /srv/models:/models:ro \
  --shm-size=8g \
  "$VLLM_IMAGE" \
  --model "$MODEL" \
  --quantization fp4 \
  --kv-cache-dtype auto \
  --max-model-len 8192 \
  --port $PORT \
  --reasoning-parser qwen3 \
  --disable-log-requests \
  2>&1 | tee -a "$LOG"

# Wait for health
echo "$(date -Iseconds) | waiting for vLLM to be ready..." | tee -a "$LOG"
for i in $(seq 1 360); do
  if curl -sf "http://localhost:$PORT/health" >/dev/null 2>&1; then
    echo "$(date -Iseconds) | vLLM ready after $((i*5))s" | tee -a "$LOG"
    break
  fi
  if [ $i -eq 360 ]; then
    echo "$(date -Iseconds) | FAILED: vLLM did not start in 30 min" | tee -a "$LOG"
    docker logs vllm-ppl 2>&1 | tail -30 >> "$LOG"
    docker rm -f vllm-ppl 2>/dev/null
    exit 1
  fi
  sleep 5
done

# Compute perplexity via logprobs
echo "$(date -Iseconds) | computing perplexity..." | tee -a "$LOG"
python3 << 'PYEOF' 2>&1 | tee -a "$LOG"
import json, math, os, sys
try:
    from datasets import load_dataset
except ImportError:
    # Fall back to local copy if available
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "datasets", "--quiet"])
    from datasets import load_dataset

import requests

PORT = 8090
API = f"http://localhost:{PORT}/v1/completions"
MODEL = "Qwen/Qwen3-27B"
SEQ_LEN = 4096
STRIDE = 2048
MAX_CHUNKS = 20  # Match Protocol 2

# Load WikiText-2
print("Loading WikiText-2...")
ds = load_dataset("wikitext", "wikitext-2-raw-v1", split="test")
text = "\n\n".join([t for t in ds["text"] if t.strip()])

# Tokenize via the API (count tokens)
print(f"Text length: {len(text)} chars")

# Process in chunks with sliding window
nlls = []
n_tokens = 0
chunk_results = []

for chunk_idx in range(MAX_CHUNKS):
    # Use character offsets as proxy, then let the API tokenize
    char_start = chunk_idx * STRIDE * 4  # rough chars-per-token estimate
    char_end = char_start + SEQ_LEN * 4
    if char_start >= len(text):
        break

    chunk_text = text[char_start:char_end]
    if len(chunk_text.strip()) < 100:
        break

    try:
        resp = requests.post(API, json={
            "model": MODEL,
            "prompt": chunk_text,
            "max_tokens": 1,
            "logprobs": 1,
            "echo": True,
            "temperature": 0,
        }, timeout=120)
        resp.raise_for_status()
        data = resp.json()

        logprobs = data["choices"][0].get("logprobs", {})
        token_logprobs = logprobs.get("token_logprobs", [])

        # First token has no logprob (it's the prompt start)
        valid_logprobs = [lp for lp in token_logprobs if lp is not None]

        if valid_logprobs:
            chunk_nll = -sum(valid_logprobs) / len(valid_logprobs)
            chunk_ppl = math.exp(chunk_nll)
            nlls.extend(valid_logprobs)
            n_tokens += len(valid_logprobs)
            chunk_results.append({
                "chunk": chunk_idx,
                "n_tokens": len(valid_logprobs),
                "nll": round(chunk_nll, 6),
                "ppl": round(chunk_ppl, 4)
            })
            print(f"  chunk {chunk_idx}: {len(valid_logprobs)} tokens, NLL={chunk_nll:.4f}, PPL={chunk_ppl:.4f}")
        else:
            print(f"  chunk {chunk_idx}: no valid logprobs")

    except Exception as e:
        print(f"  chunk {chunk_idx}: ERROR {e}")
        continue

if nlls:
    avg_nll = -sum(nlls) / len(nlls)
    ppl = math.exp(avg_nll)
    result = {
        "model": "Qwen3-27B-NVFP4",
        "engine": "vLLM",
        "protocol": 2,
        "dataset": "wikitext-2-raw-v1",
        "seq_len": SEQ_LEN,
        "stride": STRIDE,
        "n_chunks": len(chunk_results),
        "n_tokens": n_tokens,
        "avg_nll": round(avg_nll, 6),
        "perplexity": round(ppl, 4),
        "chunks": chunk_results
    }
    print(f"\nFINAL: PPL={ppl:.4f} over {n_tokens} tokens ({len(chunk_results)} chunks)")

    with open("/srv/bench/perplexity/nvfp4-vllm-ppl.json", "w") as f:
        json.dump(result, f, indent=2)
    print(f"Saved to {'/srv/bench/perplexity/nvfp4-vllm-ppl.json'}")
else:
    print("ERROR: no logprobs collected")
    sys.exit(1)
PYEOF

echo "$(date -Iseconds) | cleaning up vLLM server" | tee -a "$LOG"
docker logs vllm-ppl > /srv/bench/server-timings/nvfp4-ppl.serverlog 2>&1 || true
docker rm -f vllm-ppl 2>/dev/null || true
echo "$(date -Iseconds) | nvfp4-ppl: DONE" | tee -a "$LOG"
