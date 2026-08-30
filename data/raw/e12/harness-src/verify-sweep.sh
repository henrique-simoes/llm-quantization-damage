#!/bin/bash
# verify-sweep.sh — Phase-1 assertions (plan §3.4.4). Non-zero on ANY failure.
#   verify-sweep.sh --stage 1a   (after delete-1a; byte gates NOT yet applied — they are
#                                 evaluated at T3b per D1/Q-A2)
#   verify-sweep.sh --stage 1b   (after delete-1b; final byte gates: /srv/models >= 60e9 B,
#                                 / >= 55e9 B — Q-A2 byte-explicit decimal gate)
set -uo pipefail
MANIFEST=/srv/bench/env-manifest.json
PY=/srv/bench/.venv-evalplus/bin/python
STAGE=1a
[ "${1:-}" = "--stage" ] && STAGE="$2"
rc=0
fail() { echo "VERIFY-FAIL: $*"; rc=1; }
ok()   { echo "verify-ok: $*"; }

# --- deleted items actually gone ---
for p in /srv/models/Qwen3.8-27B-UD-IQ4_XS.gguf \
         /srv/models/.hf-cache/models--unsloth--Qwen3.8-27B-NVFP4; do
  [ -e "$p" ] && fail "1a item still present: $p" || ok "gone: $p"
done
nv=$(docker images --format '{{.Repository}}:{{.Tag}}' | grep -c vllm || true)
[ "$nv" = "0" ] && ok "no vLLM images" || fail "$nv vLLM images still present"
if [ "$STAGE" = 1b ]; then
  [ -e /srv/models/Qwen3.8-27B-UD-Q6_K_XL.gguf ] && fail "1b item still present: Q6_K_XL" \
    || ok "gone: Q6_K_XL"
fi

# --- KEEP items: full sha256 on the active GGUFs, presence elsewhere ---
$PY - <<'PYEOF'
import hashlib, json, os, sys
MAN = "/srv/bench/env-manifest.json"
d = json.load(open(MAN))
pins = {g["file"]: g for g in d.get("gguf_models", [])}
bad = []
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()
actives = ["/srv/models/Qwen3.8-27B-UD-Q4_K_XL.gguf",
           "/srv/models/Qwen3.8-27B-UD-Q5_K_XL.gguf",
           "/srv/bench/models/Qwen3.8-27B-UD-Q6_K.gguf"]
for p in actives:
    if not os.path.exists(p):
        bad.append(f"ACTIVE GGUF MISSING: {p}"); continue
    if p in pins:
        if pins[p].get("sha256") and sha(p) != pins[p]["sha256"]:
            bad.append(f"SHA MISMATCH: {p}")
        else:
            print(f"verify-ok: sha256 {os.path.basename(p)}")
    else:
        bad.append(f"NO MANIFEST PIN: {p}")
keep = ["/srv/models/dflash2/Qwen3.8-27B-DFlash2-Q4_K_M.gguf",
        "/srv/engines/nvfp4",
        "/srv/models/.hf-cache/hub",
        "/srv/models/.hf-cache/models--z-lab--Qwen3.8-27B-DFlash2",
        "/srv/bench/champion-20260821",
        "/srv/bench/e11"]
for p in keep:
    if not os.path.exists(p):
        bad.append(f"KEEP MISSING: {p}")
    else:
        print(f"verify-ok: keep {p}")
sys.exit(1 if bad else 0)
PYEOF
[ $? -eq 0 ] || fail "KEEP-item check failed (see above)"

di=$(docker images --format '{{.Repository}}:{{.Tag}}' | grep -c "llamacpp-mtp\|llama-dflash2" || true)
[ "$di" = "2" ] && ok "llama.cpp engine images present" || fail "llama.cpp images: $di != 2"

# --- telemetry containers still Up ---
tel=$(docker ps --filter name=tel- --format '{{.Names}}' | wc -l)
[ "$tel" = "6" ] && ok "6 telemetry containers Up" || fail "telemetry containers: $tel != 6"

# --- orchestrator state/*.done intact (F-A: one deleted marker wakes the legacy jobs) ---
nd=$(ls /srv/bench/orchestrator/state/*.done 2>/dev/null | wc -l)
[ "$nd" = "6" ] && ok "6 state/*.done markers intact" || fail "state/*.done count $nd != 6"

# --- deleted_items[] completeness + deletion timestamps + F-B repair + RepoDigests ---
$PY - <<'PYEOF'
import json, sys
d = json.load(open("/srv/bench/env-manifest.json"))
di = d.get("deleted_items", [])
ids = {x["id"] for x in di}
need = {"iq4_xs-gguf", "nvfp4-hf-cache", "vllm-nightly-image", "vllm-v0.27.1-image", "q6kxl-gguf"}
bad = []
if not need <= ids:
    bad.append(f"deleted_items incomplete: missing {need - ids}")
for x in di:
    if x["id"] in {"iq4_xs-gguf", "nvfp4-hf-cache", "vllm-nightly-image", "vllm-v0.27.1-image"}:
        if not x.get("sha256_tree") and not x.get("sha256") and x.get("kind") != "docker-image":
            bad.append(f"{x['id']}: no hash recorded")
        if not x.get("deleted_utc"):
            bad.append(f"{x['id']}: not marked deleted")
        if not x.get("recovery"):
            bad.append(f"{x['id']}: no recovery coordinates")
    if x["id"] == "q6kxl-gguf" and not x.get("sha256"):
        bad.append("q6kxl-gguf: no sha256")
for x in di:
    if x["kind"] == "docker-image" and not x.get("repodigest"):
        bad.append(f"{x['id']}: NO RepoDigest — re-pull would not be byte-exact")
pinned = any("UD-Q6_K.gguf" in g.get("file", "") and g.get("sha256")
             for g in d.get("gguf_models", []))
if not pinned:
    bad.append("F-B repair missing: UD-Q6_K.gguf still unpinned")
for b in bad:
    print("VERIFY-FAIL(manifest):", b)
sys.exit(1 if bad else 0)
PYEOF
[ $? -eq 0 ] || fail "env-manifest check failed"

# --- no empty e12 serverlogs (A2) ---
empty=$(find /srv/bench/server-timings -name "e12-*.serverlog" -size -1c 2>/dev/null | wc -l)
[ "$empty" = "0" ] && ok "no empty e12 serverlogs" || fail "$empty empty e12 serverlogs"

# --- byte gates (final, stage 1b only — Q-A2 decimal byte-explicit) ---
if [ "$STAGE" = 1b ]; then
  av_models=$(df -B1 /srv/models | tail -1 | awk '{print $4}')
  av_root=$(df -B1 / | tail -1 | awk '{print $4}')
  [ "$av_models" -ge 60000000000 ] && ok "/srv/models avail $av_models B >= 60e9" \
    || fail "/srv/models avail $av_models B < 60e9"
  [ "$av_root" -ge 55000000000 ] && ok "/ avail $av_root B >= 55e9" \
    || fail "/ avail $av_root B < 55e9"
  $PY - "$av_models" "$av_root" <<'PYEOF'
import sys

models, root = map(int, sys.argv[1:3])
print(
    "gate (decimal bytes): "
    f"/srv/models = {models} B ({models / 1e9:.2f} GB / {models / 2**30:.2f} GiB), "
    f"/ = {root} B ({root / 1e9:.2f} GB / {root / 2**30:.2f} GiB)"
)
PYEOF
fi

echo "verify-sweep stage $STAGE: rc=$rc"
exit $rc
