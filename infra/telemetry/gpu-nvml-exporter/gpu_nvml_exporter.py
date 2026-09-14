#!/usr/bin/env python3
"""gpu-nvml-exporter — NVML energy, power, GPM, PCIe, XID and per-process VRAM (plan §3.3).

Instant values (energy counter, power, memory, replay counter, processes) are read at scrape
time. GPM ratios need two samples: a background thread takes one nvmlGpmSample every
sample_interval_s and computes the metrics between consecutive samples.

Units verified on this host (RTX 5060 Ti) from NVML's own
nvmlGpmMetric_t.metricInfo.unit: utilisation metrics report "%", PCIE_{TX,RX}_PER_SEC report
"MiB/s". The exporter reads that unit string at runtime and converts: % -> ratio 0-1,
MiB/s -> bytes/s (x 1,048,576).
"""
from __future__ import annotations

import argparse
import re
import signal
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pynvml as N

MIB = 1024 * 1024
# contract label -> candidate NVML_GPM_METRIC_* suffixes (first that exists wins)
GPM_RATIOS: list[tuple[str, tuple[str, ...]]] = [
    ("graphics_util", ("GRAPHICS_UTIL",)),
    ("sm_util", ("SM_UTIL",)),
    ("sm_occupancy", ("SM_OCCUPANCY",)),
    ("mem_bandwidth_util", ("DRAM_BW_UTIL", "MEM_UTIL", "MEMORY_BANDWIDTH_UTIL")),
    ("fp16_util", ("FP16_UTIL",)),
    ("fp32_util", ("FP32_UTIL",)),
    ("integer_util", ("INTEGER_UTIL",)),
]
GPM_PCIE: list[tuple[str, tuple[str, ...]]] = [("tx", ("PCIE_TX_PER_SEC",)), ("rx", ("PCIE_RX_PER_SEC",))]
UNIT_SCALE = {"%": 0.01, "MiB/s": MIB, "KiB/s": 1024.0, "B/s": 1.0, "bytes/s": 1.0}

STOP = threading.Event()


def log(msg: str) -> None:
    print(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), msg, file=sys.stderr, flush=True)


def escape(v) -> str:
    return str(v).replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def labels(d: dict) -> str:
    return "{" + ",".join(f'{k}="{escape(v)}"' for k, v in d.items()) + "}"


def _s(v) -> str:
    return v.decode() if isinstance(v, bytes) else str(v)


# ---------------- pure helpers (unit-tested) ----------------
RE_CGROUP_DOCKER = re.compile(r"docker-([0-9a-f]{64})\.scope|/docker/([0-9a-f]{64})")
RE_XID = re.compile(r"NVRM: Xid \(PCI:([0-9a-fA-F:.]+)\): (\d+)")


def container_id_from_cgroup(text: str) -> str | None:
    m = RE_CGROUP_DOCKER.search(text)
    return (m.group(1) or m.group(2)) if m else None


def parse_xid_line(line: str) -> tuple[str, int] | None:
    m = RE_XID.search(line)
    return (m.group(1), int(m.group(2))) if m else None


def pci_key(bus_id: str) -> tuple[int, int, int] | None:
    """'00000000:01:00.0' (NVML) and '0000:01:00' (kernel) -> (domain, bus, device)."""
    m = re.search(r"(?:([0-9a-fA-F]+):)?([0-9a-fA-F]{2}):([0-9a-fA-F]{2})(?:\.[0-9a-fA-F])?$", bus_id.strip())
    if not m:
        return None
    return int(m.group(1) or "0", 16), int(m.group(2), 16), int(m.group(3), 16)


def scale_gpm(value: float, unit: str) -> float | None:
    k = UNIT_SCALE.get(unit)
    return None if k is None else value * k


# ---------------- NVML state ----------------
class Gpu:
    def __init__(self, index: int):
        self.index = index
        self.h = N.nvmlDeviceGetHandleByIndex(index)
        self.uuid = _s(N.nvmlDeviceGetUUID(self.h))
        self.name = _s(N.nvmlDeviceGetName(self.h))
        self.pci = pci_key(_s(N.nvmlDeviceGetPciInfo(self.h).busId))
        self.lab = {"gpu": str(index), "uuid": self.uuid, "name": self.name}


class GpmSampler(threading.Thread):
    def __init__(self, gpus: list[Gpu], interval: float):
        super().__init__(name="gpm", daemon=True)
        self.gpus, self.interval = gpus, interval
        self.lock = threading.Lock()
        self.values: dict[int, dict[str, float]] = {}
        self.supported: dict[int, bool] = {g.index: False for g in gpus}
        self.ids: list[tuple[str, str, int]] = []  # (kind, label, metric id); kind = ratio|pcie
        for kind, table in (("ratio", GPM_RATIOS), ("pcie", GPM_PCIE)):
            for label, names in table:
                mid = next((getattr(N, "NVML_GPM_METRIC_" + n) for n in names if hasattr(N, "NVML_GPM_METRIC_" + n)), None)
                if mid is None:
                    log(f"GPM metric {label}: none of {names} exists in this nvidia-ml-py")
                else:
                    self.ids.append((kind, label, mid))
        self.unit_warned: set[str] = set()

    def _compute(self, s1, s2) -> dict[str, float]:
        md = N.c_nvmlGpmMetricsGet_t()
        md.version = N.NVML_GPM_METRICS_GET_VERSION
        md.numMetrics = len(self.ids)
        md.sample1, md.sample2 = s1, s2
        for k, (_, _, mid) in enumerate(self.ids):
            md.metrics[k].metricId = mid
        N.nvmlGpmMetricsGet(md)
        out = {}
        for k, (kind, label, _) in enumerate(self.ids):
            m = md.metrics[k]
            if m.nvmlReturn != 0:
                continue
            unit = _s(m.metricInfo.unit)
            v = scale_gpm(float(m.value), unit)
            if v is None:
                if label not in self.unit_warned:
                    self.unit_warned.add(label)
                    log(f"GPM {label}: unexpected unit {unit!r}; series skipped")
                continue
            out[f"{kind}:{label}"] = v
        return out

    def run(self) -> None:
        bufs, prev = {}, {}
        for g in self.gpus:
            try:
                if not N.nvmlGpmQueryDeviceSupport(g.h).isSupportedDevice:
                    log(f"GPU {g.index}: GPM not supported")
                    continue
                bufs[g.index] = [N.nvmlGpmSampleAlloc(), N.nvmlGpmSampleAlloc()]
            except N.NVMLError as e:
                log(f"GPU {g.index}: GPM unavailable: {e}")
        turn = 0
        while not STOP.is_set():
            t0 = time.monotonic()
            for g in self.gpus:
                if g.index not in bufs:
                    continue
                cur = bufs[g.index][turn]
                try:
                    N.nvmlGpmSampleGet(g.h, cur)
                    if g.index in prev:
                        vals = self._compute(prev[g.index], cur)
                        with self.lock:
                            self.values[g.index] = vals
                            self.supported[g.index] = bool(vals)
                    prev[g.index] = cur
                except N.NVMLError as e:
                    prev.pop(g.index, None)
                    with self.lock:
                        self.values.pop(g.index, None)
                        self.supported[g.index] = False
                    log(f"GPU {g.index}: GPM sample failed: {e}")
            turn ^= 1  # alternate buffers so the previous sample stays intact
            STOP.wait(max(0.05, self.interval - (time.monotonic() - t0)))


class ContainerResolver:
    """host PID -> docker container name, via /proc/<pid>/cgroup and a cached docker inspect."""

    def __init__(self):
        self.names: dict[str, tuple[str, float]] = {}

    def __call__(self, pid: int) -> str:
        try:
            with open(f"/proc/{pid}/cgroup") as f:
                cid = container_id_from_cgroup(f.read())
        except OSError:
            return ""
        if not cid:
            return ""
        hit = self.names.get(cid)
        if hit and (hit[0] or time.monotonic() - hit[1] < 60):
            return hit[0]
        name = ""
        try:
            r = subprocess.run(["docker", "inspect", "-f", "{{.Name}}", cid], capture_output=True, text=True, timeout=10)
            if r.returncode == 0:
                name = r.stdout.strip().lstrip("/")
        except (OSError, subprocess.TimeoutExpired):
            pass
        if not name:
            name = cid[:12]  # still a container; name unresolved (docker unreachable)
            self.names[cid] = ("", time.monotonic())
            return name
        self.names[cid] = (name, time.monotonic())
        return name


class XidWatcher(threading.Thread):
    def __init__(self, gpus: list[Gpu], mode: str):
        super().__init__(name="xid", daemon=True)
        self.gpus, self.mode = gpus, mode
        self.lock = threading.Lock()
        self.counts: dict[tuple, int] = {}  # (gpu, uuid, name, xid) -> n
        self.source = "none"
        self.up = 0
        self.proc: subprocess.Popen | None = None

    def _inc(self, gpu: Gpu | None, xid: int) -> None:
        key = (str(gpu.index), gpu.uuid, gpu.name, str(xid)) if gpu else ("", "", "", str(xid))
        with self.lock:
            self.counts[key] = self.counts.get(key, 0) + 1
        log(f"XID {xid} on GPU {key[0] or '?'}")

    def _nvml(self) -> bool:
        try:
            es = N.nvmlEventSetCreate()
        except N.NVMLError as e:
            log(f"XID: NVML event set unavailable: {e}")
            return False
        registered = 0
        for g in self.gpus:
            try:
                if N.nvmlDeviceGetSupportedEventTypes(g.h) & N.nvmlEventTypeXidCriticalError:
                    N.nvmlDeviceRegisterEvents(g.h, N.nvmlEventTypeXidCriticalError, es)
                    registered += 1
            except N.NVMLError as e:
                log(f"XID: GPU {g.index} registration failed: {e}")
        if registered == 0:
            N.nvmlEventSetFree(es)
            return False
        self.source, self.up = "nvml", 1
        log(f"XID: NVML critical-XID events registered on {registered} GPU(s)")
        by_uuid = {g.uuid: g for g in self.gpus}
        while not STOP.is_set():
            try:
                data = N.nvmlEventSetWait_v2(es, 5000)
            except N.NVMLError_Timeout:
                continue
            except N.NVMLError as e:
                log(f"XID: event wait failed: {e}")
                STOP.wait(5)
                continue
            if data.eventType & N.nvmlEventTypeXidCriticalError:
                try:
                    gpu = by_uuid.get(_s(N.nvmlDeviceGetUUID(data.device)))
                except N.NVMLError:
                    gpu = None
                self._inc(gpu, int(data.eventData))
        return True

    def _journal(self) -> bool:
        probe = subprocess.run(["journalctl", "-k", "-n", "1", "-q", "--no-pager"], capture_output=True, text=True)
        if probe.returncode != 0 or not probe.stdout.strip():
            log("XID: cannot read the kernel journal (user needs group adm or systemd-journal)")
            return False
        self.source = "journal"
        by_pci = {g.pci: g for g in self.gpus}
        backoff = 1.0
        while not STOP.is_set():
            self.proc = subprocess.Popen(["journalctl", "-k", "-f", "-n", "0", "-o", "cat", "--no-pager"],
                                         stdout=subprocess.PIPE, text=True, errors="replace")
            self.up = 1
            for line in self.proc.stdout:
                hit = parse_xid_line(line)
                if hit:
                    self._inc(by_pci.get(pci_key(hit[0])), hit[1])
            self.proc.wait()
            self.up = 0
            STOP.wait(backoff)
            backoff = min(backoff * 2, 30)
        return True

    def run(self) -> None:
        if self.mode in ("auto", "nvml") and self._nvml():
            return
        if self.mode in ("auto", "journal"):
            self._journal()


def collect(gpus: list[Gpu], gpm: GpmSampler, xid: XidWatcher, resolve: ContainerResolver) -> str:
    fams: dict[str, tuple[str, str, list[str]]] = {}

    def add(name: str, kind: str, help_: str, lab: dict, value: float) -> None:
        fams.setdefault(name, (kind, help_, []))[2].append(f"{name}{labels(lab)} {float(value)!r}")

    def safe(fn, *a):
        try:
            return fn(*a)
        except N.NVMLError:
            return None

    with gpm.lock:
        gpm_values = {k: dict(v) for k, v in gpm.values.items()}
        gpm_sup = dict(gpm.supported)

    for g in gpus:
        L = g.lab
        if (e := safe(N.nvmlDeviceGetTotalEnergyConsumption, g.h)) is not None:
            add("nvml_gpu_energy_joules_total", "counter", "GPU energy since driver load (nvmlDeviceGetTotalEnergyConsumption mJ / 1000).", L, e / 1000.0)
        if (p := safe(N.nvmlDeviceGetPowerUsage, g.h)) is not None:
            add("nvml_gpu_power_watts", "gauge", "Instant power draw (display only; use the energy counter for J).", L, p / 1000.0)
        if (p := safe(N.nvmlDeviceGetEnforcedPowerLimit, g.h)) is not None:
            add("nvml_gpu_power_limit_watts", "gauge", "Enforced power limit.", L, p / 1000.0)
        if (mem := safe(N.nvmlDeviceGetMemoryInfo, g.h)) is not None:
            add("nvml_gpu_memory_used_bytes", "gauge", "Framebuffer memory used.", L, mem.used)
            add("nvml_gpu_memory_total_bytes", "gauge", "Framebuffer memory total.", L, mem.total)
        if (r := safe(N.nvmlDeviceGetPcieReplayCounter, g.h)) is not None:
            add("nvml_gpu_pcie_replay_total", "counter", "PCIe replay counter.", L, r)
        for proc in safe(N.nvmlDeviceGetComputeRunningProcesses, g.h) or []:
            used = getattr(proc, "usedGpuMemory", None)
            if used is None:
                continue
            add("nvml_gpu_process_memory_bytes", "gauge", "GPU memory per compute process (host PID; container via cgroup).",
                {**L, "pid": str(proc.pid), "container": resolve(proc.pid)}, used)
        vals = gpm_values.get(g.index, {})
        for key, v in sorted(vals.items()):
            kind, label = key.split(":", 1)
            if kind == "ratio":
                add("nvml_gpu_gpm_ratio", "gauge", "NVML GPM ratio over the last sample interval (0-1).", {**L, "metric": label}, v)
            else:
                add(f"nvml_gpu_pcie_{label}_bytes_per_second", "gauge", f"GPM PCIe {label.upper()} bytes/s (NVML MiB/s x 1048576).", L, v)
        add("nvml_exporter_gpm_supported", "gauge", "1 if GPM sampling produced values on the last interval.", L, 1.0 if gpm_sup.get(g.index) else 0.0)

    with xid.lock:
        counts = dict(xid.counts)
    for (gi, uuid, name, code), n in sorted(counts.items()):
        add("nvml_gpu_xid_events_total", "counter", "XID events (NVML critical-XID events, or kernel log fallback).",
            {"gpu": gi, "uuid": uuid, "name": name, "xid": code}, n)
    fams.setdefault("nvml_gpu_xid_events_total", ("counter", "XID events (NVML critical-XID events, or kernel log fallback).", []))
    add("nvml_exporter_xid_watch_up", "gauge", "1 while the XID watcher is attached, by source (nvml|journal|none).", {"source": xid.source}, xid.up)

    out = []
    for name, (kind, help_, lines) in fams.items():
        out += [f"# HELP {name} {help_}", f"# TYPE {name} {kind}", *lines]
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="NVML GPU exporter")
    ap.add_argument("--config", help="targets.yml (reads the nvml: section)")
    ap.add_argument("--listen", help="host:port (overrides nvml.listen)")
    ap.add_argument("--sample-interval", type=float, help="GPM sample interval seconds (overrides nvml.sample_interval_s)")
    ap.add_argument("--xid-source", choices=("auto", "nvml", "journal", "none"), default="auto")
    a = ap.parse_args(argv)

    cfg = {}
    if a.config:
        import yaml

        with open(a.config) as f:
            cfg = (yaml.safe_load(f) or {}).get("nvml") or {}
    listen = a.listen or cfg.get("listen", "127.0.0.1:9836")
    interval = a.sample_interval or float(cfg.get("sample_interval_s", 1))
    host, _, port = listen.rpartition(":")

    N.nvmlInit()
    gpus = [Gpu(i) for i in range(N.nvmlDeviceGetCount())]
    log(f"NVML driver {_s(N.nvmlSystemGetDriverVersion())}; GPUs: " + ", ".join(f"{g.index}={g.name}" for g in gpus))
    gpm = GpmSampler(gpus, interval)
    gpm.start()
    xid = XidWatcher(gpus, a.xid_source)
    if a.xid_source != "none":
        xid.start()
    resolve = ContainerResolver()
    scrape_lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = self.path.split("?")[0]
            if path == "/metrics":
                with scrape_lock:
                    body, code = collect(gpus, gpm, xid, resolve).encode(), 200
                ctype = "text/plain; version=0.0.4; charset=utf-8"
            elif path in ("/", "/healthz"):
                body, code, ctype = b"ok\n", 200, "text/plain"
            else:
                body, code, ctype = b"not found\n", 404, "text/plain"
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    httpd = ThreadingHTTPServer((host or "127.0.0.1", int(port)), Handler)
    httpd.daemon_threads = True

    def stop(*_):
        STOP.set()
        if xid.proc and xid.proc.poll() is None:
            xid.proc.terminate()
        threading.Thread(target=httpd.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    log(f"listening on http://{host}:{port}/metrics (GPM interval {interval} s, xid source {a.xid_source})")
    httpd.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
