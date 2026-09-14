# gpu-nvml-exporter

NVML exporter (plan §3.3) built on `nvidia-ml-py` (`pynvml`). It exports energy counters, GPM
activity ratios, PCIe throughput, XID events and per-process VRAM for the GeForce cards on this host.
It replaces nothing: `nvidia_gpu_exporter` stays for temperature, throttle and link gen/width.

## How values are obtained

| metric | type | labels | source |
|---|---|---|---|
| `nvml_gpu_energy_joules_total` | counter | gpu, uuid, name | `nvmlDeviceGetTotalEnergyConsumption` mJ / 1000, read at scrape time |
| `nvml_gpu_power_watts` | gauge | 〃 | `nvmlDeviceGetPowerUsage` mW / 1000 (display only) |
| `nvml_gpu_power_limit_watts` | gauge | 〃 | `nvmlDeviceGetEnforcedPowerLimit` |
| `nvml_gpu_memory_used_bytes`, `nvml_gpu_memory_total_bytes` | gauge | 〃 | `nvmlDeviceGetMemoryInfo` |
| `nvml_gpu_pcie_replay_total` | counter | 〃 | `nvmlDeviceGetPcieReplayCounter` |
| `nvml_gpu_gpm_ratio` | gauge | 〃 + `metric` | GPM, 0–1: `graphics_util`, `sm_util`, `sm_occupancy`, `mem_bandwidth_util` (`NVML_GPM_METRIC_DRAM_BW_UTIL`, id 10; no `MEM_UTIL` constant exists), `fp16_util`, `fp32_util`, `integer_util` |
| `nvml_gpu_pcie_tx_bytes_per_second`, `nvml_gpu_pcie_rx_bytes_per_second` | gauge | 〃 | GPM `PCIE_TX_PER_SEC` / `PCIE_RX_PER_SEC` |
| `nvml_gpu_xid_events_total` | counter | gpu, uuid, name, xid | NVML critical-XID events; kernel journal fallback |
| `nvml_gpu_process_memory_bytes` | gauge | 〃 + pid, container | `nvmlDeviceGetComputeRunningProcesses` |
| `nvml_exporter_gpm_supported` | gauge | gpu, uuid, name | 1 if the last GPM interval produced values |
| `nvml_exporter_xid_watch_up` | gauge | source | **addition**: 1 while the XID watcher is attached (`nvml`/`journal`/`none`) |

**GPM.** A background thread calls `nvmlGpmSampleGet` every `sample_interval_s`. It alternates two
sample buffers per GPU and computes `nvmlGpmMetricsGet` between consecutive samples, so each value
covers the preceding interval and trails instant power by up to one interval.

**Units, verified on this host** (RTX 5060 Ti): NVML's own
`nvmlGpmMetric_t.metricInfo.unit` returns `"%"` for all the utilisation metrics and `"MiB/s"` for
`PCIE_{TX,RX}_PER_SEC`. The exporter reads the unit string at runtime: `%` → ×0.01,
`MiB/s` → ×1,048,576 bytes/s. A metric in an unknown unit is logged and skipped rather than exported
mis-scaled.

**Processes.** NVML returns **host PIDs**. Verified: the PID it reported (3818177) equals
`docker inspect -f '{{.State.Pid}}' qwen38-serve`. The container is resolved from `/proc/<pid>/cgroup`
(`0::/system.slice/docker-<id>.scope`, cgroup v1 `/docker/<id>` also accepted), then
`docker inspect -f '{{.Name}}' <id>`, cached per container id. Host processes get `container=""`.

**XID.** `--xid-source auto` (default) registers `nvmlEventTypeXidCriticalError` on each GPU and waits
with `nvmlEventSetWait_v2`. This works unprivileged on the GeForce cards here: the supported-event mask
includes the XID bit and registration returns success. Only if registration fails does it fall back to
`journalctl -k -f -o cat`, parsing `NVRM: Xid (PCI:0000:01:00): 79, …` and mapping the PCI bus id to a
GPU index. Least privilege for that fallback: user `multivac` can read the kernel journal through group
**`adm`** (checked). `/dev/kmsg` is root-only (0644 root, read denied). So the unit runs as
`User=multivac` with `SupplementaryGroups=docker adm`, never as root.

## Config / run

```bash
/srv/bench/telemetry/.venv/bin/python gpu_nvml_exporter.py --config /srv/bench/telemetry/etc/targets.yml
# overrides: --listen 127.0.0.1:19836  --sample-interval 1  --xid-source auto|nvml|journal|none
```

Reads `nvml: {listen, sample_interval_s}` from `targets.yml`.

## Test

```bash
python -m unittest discover -s tests -v          # cgroup, XID line / PCI mapping, unit scaling, DRAM_BW constant
python tests/validate_energy.py --exporter http://127.0.0.1:19836/metrics --seconds 30
```

`validate_energy.py` compares Δ`nvml_gpu_energy_joules_total`/Δt per GPU with the mean of 1 Hz
`nvidia-smi --query-gpu=power.draw.instant` samples over the same window.

Results on 2026-09-14:

| window | GPU0 exporter / smi | GPU1 exporter / smi |
|---|---|---|
| 35 s idle | 11.19 / 11.22 W (−0.3 %) | 11.02 / 11.04 W (−0.2 %) |
| 30 s with one 128-token decode | 33.13 / 35.09 W (−5.6 %) | 30.33 / 32.70 W (−7.2 %) |

The larger gap under load is expected. 1 Hz instantaneous samples over- or under-weight short bursts,
while the counter integrates them, which is why the rules must use the counter.

GPM during that decode (UD-Q6_K, `-sm layer`, depth ≈ 160 tokens):
- `sm_util`: GPU0 0.44–0.49, GPU1 0.40–0.44
- `graphics_util`: GPU0 0.57–0.62, GPU1 0.43–0.45
- `mem_bandwidth_util`: 0.28–0.38
- `sm_occupancy`: 0.13–0.20
- All ratios are 0.00 at idle.

## Known limitations

- The XID event path is only proven to *register*. No XID occurred during testing, so event delivery
  itself is unverified on GeForce.
- Energy counts from driver load and resets on driver reload. Prometheus `rate()` handles the reset.
- One GPM consumer per GPU is assumed (plan R3). Do not run DCGM alongside.
- If docker is unreachable, `container` falls back to the 12-character container id.
