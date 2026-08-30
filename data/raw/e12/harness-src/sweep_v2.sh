#!/bin/bash
# sweep_v2.sh — Wave-1 Phase 1 disk sweep. DELETION ORDER ENFORCED IN CODE (hard rule 2):
#   1. manifest  — sha256+bytes for every delete-list item appended to env-manifest.json
#                  as deleted_items[] (+ F-B repair: UD-Q6_K.gguf sha256; RepoDigests for
#                  both vLLM images — without them "re-pull" is not byte-exact). NO deletion.
#   2. docs      — committed in the paper repo BEFORE delete (caller passes --docs-commit);
#                  delete-1a/delete-1b REFUSE to run without it.
#   3. delete    — 1a set (IQ4_XS GGUF, NVFP4 hf-cache duplicate, both vLLM images);
#                  1b (Q6_K_XL GGUF) only after the G21 bracket (D1 / gate Q-A1).
# Usage:
#   sweep_v2.sh manifest
#   sweep_v2.sh delete-1a --docs-commit <git-sha>
#   sweep_v2.sh delete-1b --docs-commit <git-sha>
set -uo pipefail
MANIFEST=/srv/bench/env-manifest.json
E12=/srv/bench/e12
EVIDENCE=$E12/sweep-v2.json
PY=/srv/bench/.venv-evalplus/bin/python

jget() { $PY -c "import json,sys;d=json.load(open('$MANIFEST'));print(json.dumps(d$1))"; }

record_df() {
  df -B1 /srv/models / | tail -2 | awk '{print $1, $4, $6}' >> "$EVIDENCE.dflog"
}

manifest_one_gguf() { # <path> <id> <findings-citation> <recovery>
  local p="$1" id="$2" cite="$3" rec="$4"
  $PY - "$p" "$id" "$cite" "$rec" <<'PYEOF'
import hashlib, json, os, subprocess, sys
path, item_id, cite, recovery = sys.argv[1:5]
MAN = "/srv/bench/env-manifest.json"
d = json.load(open(MAN))
d.setdefault("deleted_items", [])
existing = next((x for x in d["deleted_items"] if x.get("id") == item_id), None)
if existing and existing.get("sha256") and existing.get("bytes"):
    print(f"manifest: {item_id} already present — skip"); sys.exit(0)
if not os.path.exists(path):
    print(f"manifest: MISSING {path} — abort before any deletion"); sys.exit(3)
h = hashlib.sha256()
with open(path, "rb") as f:
    for b in iter(lambda: f.read(1 << 24), b""):
        h.update(b)
ent = {"id": item_id, "path": path, "bytes": os.path.getsize(path), "sha256": h.hexdigest(),
       "kind": "gguf", "findings_citation": cite, "recovery": recovery,
       "manifested_utc": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                        capture_output=True, text=True).stdout.strip(),
       "deleted_utc": None}
if existing:
    ent["deleted_utc"] = existing.get("deleted_utc")
    existing.update(ent)
else:
    d["deleted_items"].append(ent)
json.dump(d, open(MAN + ".tmp", "w"), indent=1)
os.replace(MAN + ".tmp", MAN)
print(f"manifest: {item_id} {ent['bytes']} B sha256={ent['sha256'][:16]}…")
PYEOF
  rc=$?
  case $rc in
    0) ;;
    3) echo "ABORT: manifest target missing"; exit 3 ;;
    *) echo "manifest FAILED rc=$rc"; exit $rc ;;
  esac
}

manifest_tree() { # <dir> <id> <findings-citation> <recovery>   (deterministic tree digest)
  local p="$1" id="$2" cite="$3" rec="$4"
  $PY - "$p" "$id" "$cite" "$rec" <<'PYEOF'
import hashlib, json, os, subprocess, sys
path, item_id, cite, recovery = sys.argv[1:5]
MAN = "/srv/bench/env-manifest.json"
d = json.load(open(MAN))
d.setdefault("deleted_items", [])
existing = next((x for x in d["deleted_items"] if x.get("id") == item_id), None)
if existing and existing.get("sha256_tree") and existing.get("bytes"):
    print(f"manifest: {item_id} already present — skip"); sys.exit(0)
if not os.path.isdir(path):
    print(f"manifest: MISSING {path} — abort before any deletion"); sys.exit(3)
files = []
for root, dirs, fs in os.walk(path):
    for fn in sorted(fs):
        fp = os.path.join(root, fn)
        if os.path.isfile(fp) and not os.path.islink(fp):
            files.append(fp)
files.sort()
tb = 0
th = hashlib.sha256()
nfile = 0
nroot_owned = 0


def hash_file(fp):
    """sha256 with a sudo fallback: hf-cache blobs may be root-owned (0600)."""
    h = hashlib.sha256()
    try:
        with open(fp, "rb") as f:
            for b in iter(lambda: f.read(1 << 24), b""):
                h.update(b)
    except PermissionError:
        # Stream through the privileged subprocess; capture_output would hold a
        # multi-gigabyte cache blob in RAM and can kill the manifest phase.
        proc = subprocess.Popen(["sudo", "-n", "cat", fp], stdout=subprocess.PIPE)
        try:
            for b in iter(lambda: proc.stdout.read(1 << 24), b""):
                h.update(b)
        finally:
            proc.stdout.close()
        if proc.wait() != 0:
            raise RuntimeError(f"sudo hash failed for {fp}")
    return h.hexdigest()


for fp in files:
    try:
        open(fp, "rb").close()
    except PermissionError:
        nroot_owned += 1
    hh = hash_file(fp)
    sb = os.path.getsize(fp)
    tb += sb
    th.update(hh.encode()); th.update(f"{sb}\n".encode())
    nfile += 1
ent = {"id": item_id, "path": path, "bytes": tb, "files": nfile,
       "sha256_tree": th.hexdigest(), "kind": "dir", "root_owned_files_read_via_sudo": nroot_owned,
       "findings_citation": cite, "recovery": recovery,
       "manifested_utc": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                        capture_output=True, text=True).stdout.strip(),
       "deleted_utc": None}
if existing:
    ent["deleted_utc"] = existing.get("deleted_utc")
    existing.update(ent)
else:
    d["deleted_items"].append(ent)
json.dump(d, open(MAN + ".tmp", "w"), indent=1)
os.replace(MAN + ".tmp", MAN)
print(f"manifest: {item_id} {nfile} files {tb} B tree={ent['sha256_tree'][:16]}…")
PYEOF
  rc=$?
  case $rc in
    0) ;;
    3) echo "ABORT: manifest target missing"; exit 3 ;;
    *) echo "manifest FAILED rc=$rc"; exit $rc ;;
  esac
}

manifest_image() { # <image> <id> <recovery>
  local img="$1" id="$2" rec="$3"
  $PY - "$img" "$id" "$rec" <<'PYEOF'
import json, os, subprocess, sys
img, item_id, recovery = sys.argv[1:4]
MAN = "/srv/bench/env-manifest.json"
d = json.load(open(MAN))
d.setdefault("deleted_items", [])
existing = next((x for x in d["deleted_items"] if x.get("id") == item_id), None)
if existing and existing.get("repodigest"):
    print(f"manifest: {item_id} already present — skip"); sys.exit(0)
def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()
iid = run(f"docker image inspect --format '{{{{.Id}}}}' {img}")
size = run(f"docker image inspect --format '{{{{.Size}}}}' {img}")
digest = run(f"docker image inspect --format '{{{{index .RepoDigests 0}}}}' {img}")
os.makedirs("/srv/bench", exist_ok=True)
if not iid:
    print(f"manifest: image {img} missing — abort before any deletion"); sys.exit(3)
ent = {"id": item_id, "path": img, "kind": "docker-image", "image_id": iid,
       "repodigest": digest or None, "bytes": int(size) if size.isdigit() else None,
       "findings_citation": "DEC-4: vLLM/SGLang eliminated from Track A; E9 cross-backend "
                            "re-run would re-pull by digest",
       "recovery": recovery,
       "manifested_utc": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                        capture_output=True, text=True).stdout.strip(),
       "deleted_utc": None}
if not digest:
    print(f"manifest: image {img} has no RepoDigest — abort before any deletion"); sys.exit(3)
if existing:
    existing.update(ent)
else:
    d["deleted_items"].append(ent)
json.dump(d, open(MAN + ".tmp", "w"), indent=1)
os.replace(MAN + ".tmp", MAN)
print(f"manifest: {item_id} image_id={iid[:20]}… repodigest={digest or 'NONE (recorded!)'}")
PYEOF
  rc=$?
  case $rc in
    0) ;;
    3) echo "ABORT: manifest target missing"; exit 3 ;;
    *) echo "manifest FAILED rc=$rc"; exit $rc ;;
  esac
}

repair_fb() { # F-B: the champion quant has no sha256 pin in env-manifest
  $PY - <<'PYEOF'
import hashlib, json, os, sys
MAN = "/srv/bench/env-manifest.json"
p = "/srv/bench/models/Qwen3.8-27B-UD-Q6_K.gguf"
d = json.load(open(MAN))
existing = next((g for g in d.get("gguf_models", []) if g.get("file") == p), None)
if existing and existing.get("sha256") and existing.get("bytes"):
    print("F-B repair: UD-Q6_K already pinned — skip"); sys.exit(0)
if not os.path.exists(p):
    print("F-B repair: model file missing!"); sys.exit(3)
h = hashlib.sha256()
with open(p, "rb") as f:
    for b in iter(lambda: f.read(1 << 24), b""):
        h.update(b)
ent = {"file": p, "bytes": os.path.getsize(p), "sha256": h.hexdigest(),
       "added_by": "e12-wave1-T3a (F-B repair)", "role": "champion quant"}
if existing:
    existing.update(ent)
else:
    d.setdefault("gguf_models", []).append(ent)
json.dump(d, open(MAN + ".tmp", "w"), indent=1)
os.replace(MAN + ".tmp", MAN)
print("F-B repair: UD-Q6_K sha256 pinned")
PYEOF
}

docs_commit_ok() {
  local sha="$1"
  if [ -z "$sha" ] || [ "$sha" = "NONE" ]; then
    echo "REFUSING TO DELETE: --docs-commit required (docs -> manifest -> delete, hard rule 2)"
    return 1
  fi
  return 0
}

mark_deleted() { # <id>
  $PY - "$1" <<'PYEOF'
import json, os, subprocess, sys
MAN = "/srv/bench/env-manifest.json"
iid = sys.argv[1]
d = json.load(open(MAN))
found = False
for x in d.get("deleted_items", []):
    if x["id"] == iid:
        found = True
        if not x.get("deleted_utc"):
            x["deleted_utc"] = subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                               capture_output=True, text=True).stdout.strip()
if not found:
    print(f"manifest: cannot mark unknown deleted item {iid}", file=sys.stderr)
    sys.exit(4)
json.dump(d, open(MAN + ".tmp", "w"), indent=1)
os.replace(MAN + ".tmp", MAN)
PYEOF
}

delete_file_and_mark() { # <path> <manifest-id>
  local path="$1" id="$2"
  if [ -e "$path" ] || [ -L "$path" ]; then
    rm -f -- "$path" || { echo "delete failed: $path"; return 1; }
  else
    echo "already absent: $path"
  fi
  mark_deleted "$id"
}

delete_dir_and_mark() { # <path> <manifest-id>
  local path="$1" id="$2"
  if [ -e "$path" ] || [ -L "$path" ]; then
    sudo -n rm -rf -- "$path" || { echo "delete failed: $path"; return 1; }
  else
    echo "already absent: $path"
  fi
  mark_deleted "$id"
}

delete_image_and_mark() { # <image-ref> <manifest-id>
  local image="$1" id="$2"
  if docker image inspect "$image" >/dev/null 2>&1; then
    docker rmi "$image" || { echo "delete failed: $image"; return 1; }
  else
    echo "already absent: $image"
  fi
  mark_deleted "$id"
}

phase="${1:-}"; shift || true
case "$phase" in
  manifest)
    mkdir -p "$E12"; touch "$EVIDENCE.dflog"; record_df
    echo "== manifest phase (no deletion happens here) =="
    manifest_one_gguf /srv/models/Qwen3.8-27B-UD-IQ4_XS.gguf iq4_xs-gguf \
      "DEC-4: out of scope; PPL 6.6839, HE+ 87.8/86.0, ceilings 262,144/245,760(f16), KLD ~0.019 documented" \
      "hf download unsloth/Qwen3.8-27B-GGUF Qwen3.8-27B-UD-IQ4_XS.gguf -> verify sha256"
    manifest_tree /srv/models/.hf-cache/models--unsloth--Qwen3.8-27B-NVFP4 nvfp4-hf-cache \
      "DEC-4: duplicate of /srv/engines/nvfp4 (KEEP, E9 option preserved); PPL/HE/SWE findings documented" \
      "local copy from /srv/engines/nvfp4 (byte-identical duplicate) — 0-byte network cost"
    manifest_image vllm/vllm-openai:nightly vllm-nightly-image \
      "docker pull vllm/vllm-openai@<repodigest> (byte-exact only because the digest is recorded)"
    manifest_image vllm/vllm-openai:v0.27.1 vllm-v0.27.1-image \
      "docker pull vllm/vllm-openai@<repodigest> (byte-exact only because the digest is recorded)"
    manifest_one_gguf /srv/models/Qwen3.8-27B-UD-Q6_K_XL.gguf q6kxl-gguf \
      "DEC-4 + Q-A1: deleted only AFTER the G21 -ts bracket ran; PPL 6.6511, HE+ 93.9/91.5, SWE-V 75.5%, KLD 0.0016 documented" \
      "hf download unsloth/Qwen3.8-27B-GGUF Qwen3.8-27B-UD-Q6_K_XL.gguf -> verify sha256"
    repair_fb
    [ $? -eq 0 ] || exit $?
    record_df
    n=$($PY -c 'import json; print(len(json.load(open("/srv/bench/env-manifest.json"))["deleted_items"]))')
    echo "manifest phase complete: $n items manifested (deletion timestamps still NULL)"
    ;;
  delete-1a|delete-1b)
    commit=""; prev=""; next=0
    while [ $# -gt 0 ]; do
      case "$1" in
        --docs-commit) commit="$2"; shift 2 ;;
        *) echo "unknown arg $1"; exit 2 ;;
      esac
    done
    docs_commit_ok "$commit" || exit 2
    n=$(jget "['deleted_items']" | $PY -c 'import json,sys;print(len(json.load(sys.stdin)))')
    if [ "$n" -lt 5 ]; then echo "REFUSING: manifest phase incomplete ($n/5 items)"; exit 3; fi
    touch "$EVIDENCE.dflog"; record_df
    if [ "$phase" = delete-1a ]; then
      echo "== delete-1a: IQ4_XS + NVFP4 cache + both vLLM images =="
      delete_file_and_mark /srv/models/Qwen3.8-27B-UD-IQ4_XS.gguf iq4_xs-gguf || exit 1
      delete_dir_and_mark /srv/models/.hf-cache/models--unsloth--Qwen3.8-27B-NVFP4 nvfp4-hf-cache || exit 1   # root-owned blobs inside (read via sudo, recorded in manifest)
      delete_image_and_mark vllm/vllm-openai:nightly vllm-nightly-image || exit 1
      delete_image_and_mark vllm/vllm-openai:v0.27.1 vllm-v0.27.1-image || exit 1
    else
      echo "== delete-1b: Q6_K_XL GGUF (after G21 bracket, gate Q-A1) =="
      delete_file_and_mark /srv/models/Qwen3.8-27B-UD-Q6_K_XL.gguf q6kxl-gguf || exit 1
    fi
    $PY - "$commit" "$phase" <<'PYEOF'
import json, subprocess, sys
commit, phase = sys.argv[1:3]
p = "/srv/bench/e12/sweep-v2.json"
try:
    d = json.load(open(p))
except Exception:
    d = {"experiment": "e12-phase1-disk-sweep"}
d.setdefault("phases", []).append({
    "phase": phase, "docs_commit": commit,
    "df_after_utc": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                   capture_output=True, text=True).stdout.strip(),
    "df": subprocess.run(["df", "-B1", "/srv/models", "/"], capture_output=True,
                         text=True).stdout,
    "byte_gates": {
        mount: {
            "available_bytes": int(subprocess.run(
                ["df", "-B1", "--output=avail", mount], capture_output=True,
                text=True, check=True).stdout.splitlines()[-1].strip()),
            "decimal_gb": round(int(subprocess.run(
                ["df", "-B1", "--output=avail", mount], capture_output=True,
                text=True, check=True).stdout.splitlines()[-1].strip()) / 1e9, 3),
            "gib": round(int(subprocess.run(
                ["df", "-B1", "--output=avail", mount], capture_output=True,
                text=True, check=True).stdout.splitlines()[-1].strip()) / (2 ** 30), 3),
        } for mount in ("/srv/models", "/")
    }})
json.dump(d, open(p, "w"), indent=1)
PYEOF
    rc=$?
    [ "$rc" -eq 0 ] || exit "$rc"
    record_df
    echo "delete phase complete; df recorded in $EVIDENCE.dflog"
    ;;
  *)
    echo "usage: sweep_v2.sh manifest | delete-1a --docs-commit <sha> | delete-1b --docs-commit <sha>"
    exit 2 ;;
esac
