#!/usr/bin/env python3
"""lib_e12.py — hardened successor to e11/lib_probe.py (Wave 1, plan qbench-t1-plan-a §3.1).

Every change below is tied to a measured defect (see plan §1 / §3.1 table):
  1. CONT = "llamasrv-e12"                      (F-A/D4: legacy worker owns "llamasrv"/:8080)
  2. launch() emits the FULL contract and returns the exact command string, which every
     record stores verbatim                                    (G7: irreproducible rows)
  3. preflight() refuses to launch into a dirty host            (fail loud, not confounded)
  4. vram_sampler: 1 Hz background thread spanning prefill AND decode, per-GPU true peak
                                                (e11 sampled nvidia-smi once, post-prefill)
  5. save_and_kill(): docker logs BEFORE docker rm -f, asserts non-empty log   (hard rule 2)
  6. classify_failure(): named failure modes instead of bare "failed"          (plan §1.7)
  7. record_env(): full provenance block per artifact                          (E0 convention)
  8. spec_live(): timings.draft_n > 0 — /props LIES about speculative status   (plan §1.6.3)

Sampling (DEC-2, owner 2026-08-30): task-facing requests carry the official Qwen/Unsloth
block. NOTE (F-D): the measured server defaults on llamacpp-mtp:latest are
temp 1.0 / top_k 20 / top_p 0.95 / min_p 0.05 / presence 0.0 — NOT the upstream-documented
set; never rely on them (hard rule 3).
"""
import hashlib
import json
import os
import re
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

PORT = 8080
BASE = f"http://localhost:{PORT}"
CONT = "llamasrv-e12"                       # change #1: collision-proof container name
IMAGE = "llamacpp-mtp:latest"
SEED = 20260830
TIMINGS_DIR = "/srv/bench/server-timings"
ORCH = "/srv/bench/orchestrator"
GPU_LOCK = f"{ORCH}/gpu.lock"
MANIFEST = "/srv/bench/env-manifest.json"
E12 = "/srv/bench/e12"

MODEL_DIRS = {"/srv/models": "/models", "/srv/bench/models": "/models2"}

# DEC-2 official sampling blocks (request-level; never rely on server defaults — F-D)
SAMPLING_NON_THINKING = {
    "temperature": 0.7, "top_p": 0.80, "top_k": 20, "min_p": 0.0,
    "presence_penalty": 1.5, "repeat_penalty": 1.0,
}
SAMPLING_THINKING = {
    "temperature": 1.0, "top_p": 0.95, "top_k": 20, "min_p": 0.0,
    "presence_penalty": 0.0, "repeat_penalty": 1.0,
}
# Measured server defaults on this image (F-D) — asserted AGAINST by validate_v2 C2.
SERVER_DEFAULTS_MEASURED = {
    "temperature": 1.0, "top_k": 20, "top_p": 0.95, "min_p": 0.05,
    "presence_penalty": 0.0, "repeat_penalty": 1.0,
}


def utcnow():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sh(cmd, timeout=180):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)


# ---------------------------------------------------------------- GPU lock (D4) ---
def gpu_lock_acquired():
    """Take /srv/bench/orchestrator/gpu.lock (pid-file convention of orchestrator/lib.sh):
    a restarted legacy worker's gpu_busy() sees a live pid and yields."""
    try:
        if os.path.exists(GPU_LOCK):
            other = open(GPU_LOCK).read().strip()
            if other and other != str(os.getpid()):
                os.kill(int(other), 0)          # raises if the holder is dead
                return False                    # someone else holds a live lock
        with open(GPU_LOCK, "w") as f:
            f.write(str(os.getpid()))
        return True
    except (ProcessLookupError, ValueError):
        pass  # stale lock from a dead pid — take it over
    except Exception:
        return False
    with open(GPU_LOCK, "w") as f:
        f.write(str(os.getpid()))
    return True


def gpu_lock_release():
    try:
        if os.path.exists(GPU_LOCK):
            if open(GPU_LOCK).read().strip() == str(os.getpid()):
                os.unlink(GPU_LOCK)
    except Exception:
        pass


# ---------------------------------------------------------------- preflight (#3) ---
def preflight(auto_recover_own=True):
    """Refuse to launch unless the host is clean. Returns list of check results;
    raises RuntimeError on any failure (fail loud rather than emit a confounded number)."""
    checks = []
    r = sh('pgrep -af "watchdog.sh|worker.sh" | grep -v pgrep || true')
    legacy = [ln for ln in r.stdout.strip().splitlines() if "pgrep" not in ln]
    checks.append({"check": "legacy_orchestrator_quiesced", "ok": not legacy,
                   "detail": legacy or "watchdog.sh/worker.sh not running"})
    all_ids = sh("docker ps -a --filter name=llamasrv -q").stdout.strip().splitlines()
    own_ids = set(sh(f"docker ps -a --filter name={CONT} -q").stdout.strip().splitlines())
    foreign = [container_id for container_id in all_ids if container_id not in own_ids]
    own_exists = bool(own_ids)
    if foreign:
        checks.append({"check": "no_llamasrv_container", "ok": False,
                       "detail": "foreign llamasrv* container exists; refusing"})
    elif own_exists:
        if auto_recover_own:
            lbl = f"e12-stale-recover-{int(time.time())}"
            n = save_and_kill(lbl)
            checks.append({"check": "no_llamasrv_container", "ok": True,
                           "detail": f"recovered stale own container, log saved {lbl} ({n} B)"})
        else:
            checks.append({"check": "no_llamasrv_container", "ok": False,
                           "detail": "stale own container exists and auto_recover disabled"})
    else:
        checks.append({"check": "no_llamasrv_container", "ok": True, "detail": "clean"})
    s = socket.socket()
    s.settimeout(2)
    port_busy = (s.connect_ex(("127.0.0.1", PORT)) == 0)
    s.close()
    checks.append({"check": "port_8080_free", "ok": not port_busy,
                   "detail": "in use" if port_busy else "free"})
    v = vram()
    ok_v = len(v) == 2 and all(x < 500 for x in v)
    checks.append({"check": "gpus_idle_lt_500mib", "ok": ok_v,
                   "detail": f"memory.used MiB: {v}"})
    lock_ok = gpu_lock_acquired()
    checks.append({"check": "gpu_lock_ours", "ok": lock_ok,
                   "detail": f"pid {os.getpid()} -> {GPU_LOCK}" if lock_ok
                             else f"{GPU_LOCK} held by a live process"})
    bad = [c for c in checks if not c["ok"]]
    if bad:
        gpu_lock_release()
        raise RuntimeError("preflight FAILED: " + json.dumps(bad))
    return checks


# ---------------------------------------------------------------- VRAM sampler (#4) ---
class VramSampler:
    """1 Hz per-GPU sampling thread spanning prefill AND decode -> true peak."""

    def __init__(self, interval=1.0):
        self.interval = interval
        self.samples = []
        self._stop = threading.Event()
        self._t = threading.Thread(target=self._loop, daemon=True)
        self._started = False

    def _loop(self):
        while not self._stop.is_set():
            v = vram()
            if v:
                self.samples.append((time.time(), v))
            self._stop.wait(self.interval)

    def start(self):
        if self._started:
            return
        self._started = True
        self._t.start()

    def stop(self):
        self._stop.set()
        if self._started:
            self._t.join(timeout=5)
        return self.summary()

    def last(self):
        return self.samples[-1][1] if self.samples else []

    def summary(self):
        if not self.samples:
            return {"vram_peak_mib": [], "imbalance_mib": None,
                    "imbalance_timealigned_mib": None, "samples": 0}
        peaks = [max(s[1][g] for s in self.samples) for g in range(len(self.samples[0][1]))]
        imb = (max(peaks) - min(peaks)) if len(peaks) == 2 else None
        imb_ta = None
        if len(peaks) == 2:
            imb_ta = max(abs(s[1][0] - s[1][1]) for s in self.samples)
        return {"vram_peak_mib": peaks, "imbalance_mib": imb,
                "imbalance_timealigned_mib": imb_ta, "samples": len(self.samples)}


# ---------------------------------------------------------------- HTTP ---
def post(path, payload, timeout=7200):
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def get(path, timeout=30):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
        return json.loads(r.read())


def vram():
    r = sh("nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits")
    try:
        return [int(x.strip()) for x in r.stdout.strip().splitlines()]
    except Exception:
        return []


def free_bytes(mount):
    st = os.statvfs(mount)
    return st.f_bavail * st.f_frsize


def df_b1():
    r = sh("df -B1 /srv/models / | tail -2")
    out = {}
    for ln in r.stdout.strip().splitlines():
        p = ln.split()
        if len(p) >= 6:
            out[p[5]] = {"available": int(p[3])}
    return out


# ---------------------------------------------------------------- launch (#2) ---
def launch(model_path, ctx, kv="q4_0", spec="mtp2", sm="layer", ts=None, ctxcp=4,
           fit="off", fa="on", extra="", image=IMAGE, health_env=""):
    """model_path is a HOST path; mapped to the container mount automatically.
    Returns (cmd, rc, stderr_head). The FULL contract is explicit here — callers must
    store the returned command verbatim in every record (G7)."""
    inner = None
    for host, cont in MODEL_DIRS.items():
        if model_path.startswith(host):
            inner = model_path.replace(host, cont, 1)
    assert inner, f"model {model_path} not under a known mount"
    # defensive cleanup — STILL log-first (hard rule 2: never rm without persisted logs;
    # F-A showed an empty-label kill destroys evidence)
    if sh(f"docker ps -a --filter name={CONT} -q", timeout=30).stdout.strip():
        save_and_kill(f"e12-prelaunch-{int(time.time())}")
    mounts = " ".join(f"-v {h}:{c}:ro" for h, c in MODEL_DIRS.items() if os.path.isdir(h))
    spec_args = "--spec-type draft-mtp --spec-draft-n-max 2" if spec == "mtp2" else ""
    ts_arg = f"-ts {ts}" if ts else ""
    # BUGFIX 2026-08-30: "{ts_arg}-c" glued the tensor-split value to "-c" whenever a -ts
    # ratio was set (argv became "-ts 54,46-c 212992" -> the server swallowed "-c" into the
    # -ts value and died on the stray positional: error: invalid argument: 212992).
    # Every -ts cell of the first sweep run failed this way; only ts=default cells ran.
    cmd = (f"docker run -d --name {CONT} --gpus all --network host {mounts} {image} "
           f"-m {inner} -ngl 99 -sm {sm} {ts_arg} -c {ctx} -fit {fit} "
           f"-fa {fa} -ctk {kv} -ctv {kv} -b 2048 -ub 512 -np 1 -ctxcp {ctxcp} "
           f"{spec_args} --seed {SEED} {health_env} {extra} --host 0.0.0.0 --port {PORT}")
    cmd = re.sub(r"\s+", " ", cmd).strip()
    r = sh(cmd, timeout=180)
    return cmd, r.returncode, (r.stderr or "")[:400]


def container_argv():
    """Exact argv of the running container (docker inspect) — argv-level launch proof."""
    r = sh(f"docker inspect --format '{{{{json .Args}}}}' {CONT}", timeout=30)
    try:
        return json.loads(r.stdout.strip())
    except Exception:
        return []


def wait_health(limit=600):
    t0 = time.time()
    while time.time() - t0 < limit:
        try:
            urllib.request.urlopen(BASE + "/health", timeout=5).read()
            return True, int(time.time() - t0)
        except urllib.error.HTTPError:
            pass  # 503 while loading — keep waiting
        except Exception:
            pass
        if not sh(f"docker ps --filter name={CONT} --filter status=running -q",
                  timeout=30).stdout.strip():
            return False, int(time.time() - t0)   # container died -> fail fast
        time.sleep(5)
    return False, int(time.time() - t0)


def props():
    try:
        return get("/props")
    except Exception:
        return {}


def props_nctx():
    d = props()
    return d.get("default_generation_settings", {}).get("n_ctx", 0)


def props_model_path():
    d = props()
    mp = d.get("model_path") or d.get("default_generation_settings", {}).get("model_path") or ""
    return mp


def spec_live(resp):
    """timings.draft_n > 0 — /props misreports speculative.types 'none' while MTP is live."""
    tm = resp.get("timings", {}) or {}
    return (tm.get("draft_n") or 0) > 0


def tokenize(text):
    return post("/tokenize", {"content": text}, timeout=2400)["tokens"]


def container_err(n=4000):
    return sh(f"docker logs --tail 120 {CONT} 2>&1", timeout=60).stdout[-n:]


# ---------------------------------------------------------------- teardown (#5) ---
def never_started():
    """True iff the container exists but has NEVER been started (docker state 'created').
    Such a container has no log by construction, so an empty serverlog is not evidence
    loss — it is the absence of any run. Anything that HAS started must still obey the
    empty-log guard below."""
    r = sh(f"docker inspect --format '{{{{.State.Status}}}}|{{{{.State.StartedAt}}}}' {CONT}",
           timeout=30)
    out = r.stdout.strip()
    if r.returncode != 0 or not out:
        return False
    status, _, started = out.partition("|")
    return status == "created" or started.startswith("0001-01-01")


def save_and_kill(label):
    """docker logs BEFORE docker rm -f (hard rule 2, enforced in code).
    Returns (serverlog_bytes, tg_sample_count)."""
    path = None
    nbytes = 0
    if sh(f"docker ps -a --filter name={CONT} -q", timeout=30).stdout.strip():
        os.makedirs(TIMINGS_DIR, exist_ok=True)
        path = f"{TIMINGS_DIR}/{label}.serverlog"
        r = sh(f"docker logs {CONT} > {path} 2>&1", timeout=300)
        nbytes = os.path.getsize(path) if os.path.exists(path) else 0
        stillborn = never_started()
        if r.returncode != 0 and not stillborn:
            raise RuntimeError(f"docker logs failed for {CONT}: {(r.stderr or '')[:300]}")
        if nbytes == 0:
            # 2026-08-30: a container killed between `docker run -d` and start sits in state
            # 'created' with no log. The old code raised here, preflight() then re-raised on
            # the same corpse, and EVERY later cell failed — an unattended sweep wedged on a
            # teardown race. Record the stillbirth and allow removal; a container that DID
            # start still cannot be removed without a persisted log.
            if stillborn:
                with open(path, "w") as f:
                    f.write(f"[e12] container {CONT} was created but never started "
                            f"(no engine output exists); label={label}; {utcnow()}\n")
                nbytes = os.path.getsize(path)
            else:
                raise RuntimeError(f"serverlog {path} is EMPTY — refusing to remove {CONT}")
        removed = sh(f"docker rm -f {CONT}", timeout=120)
        if removed.returncode != 0:
            raise RuntimeError(f"docker rm failed for {CONT}: {(removed.stderr or '')[:300]}")
    time.sleep(2)
    if path and os.path.exists(path):
        with open(path, errors="replace") as f:
            txt = f.read()
        tg = len(re.findall(r"tg\s*=|eval time", txt))
    else:
        tg = 0
    return nbytes, tg


# ---------------------------------------------------------------- classification (#6) ---
OOM_PATTERNS = ["failed to allocate compute", "compute buffer", "failed to create MTP context",
                "out of memory", "cudaMalloc failed", "ggml_backend_alloc"]
CRASH_PATTERNS = ["backtrace", "segfault", "signal SIGSEGV", "llama_context_can_seq_rm",
                  "core dumped", "terminate called"]


def classify_failure(serverlog_text, stage, err=""):
    blob = f"{serverlog_text}\n{err}".lower()
    if "invalid argument" in blob or "unknown argument" in blob or "invalid value" in blob:
        return "launch-args"        # deterministic argv error — not a VRAM rung result
    if any(p.lower() in blob for p in OOM_PATTERNS):
        return "compute-buffer-oom"
    if any(p.lower() in blob for p in CRASH_PATTERNS):
        return "crash"
    if stage == "props":
        return "props-shrink"
    if stage == "prefill":
        return "prefill-fail"
    if stage == "generate":
        return "generate-fail"
    if stage == "health":
        return "init-hang"          # health timeout with no engine error text
    return "unknown"


# ---------------------------------------------------------------- provenance (#7) ---
def sha256_file(path, bufsize=1 << 24):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(bufsize)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def manifest_read():
    with open(MANIFEST) as f:
        return json.load(f)


def manifest_write_atomic(d):
    tmp = MANIFEST + ".tmp"
    with open(tmp, "w") as f:
        json.dump(d, f, indent=1)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, MANIFEST)


def manifest_gguf_entry(path):
    d = manifest_read()
    for g in d.get("gguf_models", []):
        if g.get("file") == path:
            return g
    return None


def gguf_provenance(path, compute_if_missing=True):
    """GGUF path -> {bytes, sha256} from env-manifest; computed AND APPENDED if missing (F-B)."""
    g = manifest_gguf_entry(path)
    if g and g.get("sha256"):
        return {"file": path, "bytes": g["bytes"], "sha256": g["sha256"], "source": "env-manifest"}
    if not compute_if_missing:
        return {"file": path, "bytes": os.path.getsize(path) if os.path.exists(path) else None,
                "sha256": None, "source": "missing"}
    if not os.path.exists(path):
        return {"file": path, "bytes": None, "sha256": None, "source": "missing"}
    ent = {"file": path, "bytes": os.path.getsize(path), "sha256": sha256_file(path),
           "added_by": "e12-record_env", "added_utc": utcnow()}
    d = manifest_read()
    d.setdefault("gguf_models", []).append(ent)
    manifest_write_atomic(d)
    return {**ent, "source": "computed-and-appended (F-B repair)"}


def image_provenance(image=IMAGE):
    r = sh(f"docker image inspect --format '{{{{.Id}}}}' {image}", timeout=30)
    image_id = r.stdout.strip()
    m = manifest_read().get("docker_images", {}).get(image, {})
    return {"image": image, "image_id": image_id,
            "manifest_image_id": m.get("image_id"),
            "version_string": m.get("version_string"),
            "matches_manifest": bool(image_id) and image_id == m.get("image_id")}


def record_env(model_path, ctx, ts=None, kv="q4_0", spec="mtp2", ctxcp=4, extra=None):
    """Full provenance block for an artifact (duty #7)."""
    m = df_b1()
    env = {
        "source": "e12-wave1",
        "run_ids": [],
        "recorded_utc": utcnow(),
        "image": image_provenance(),
        "model": gguf_provenance(model_path),
        "seed": SEED,
        "sampling_non_thinking": SAMPLING_NON_THINKING,
        "sampling_thinking": SAMPLING_THINKING,
        "server_defaults_measured": SERVER_DEFAULTS_MEASURED,
        "kv_dtype": kv,
        "spec": spec,
        "split_mode": "layer",
        "ctx_requested": ctx,
        "ts": ts,
        "ctxcp": ctxcp,
        "free_bytes": {k: v["available"] for k, v in m.items()},
        "extra": extra or {},
    }
    return env
