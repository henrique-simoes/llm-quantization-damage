# `power-log.csv.gz` — datasheet

A continuous 1 Hz power and thermal trace of the measurement host across the whole E12 campaign.
Published because it exists, is complete, and is expensive to reproduce — **not** because a claim
in the report rests on it. Read the *Known defect* section before it carries one.

## Provenance

| | |
|---|---|
| Host | `multivac` — see *The setup* in the repository README |
| Sampler | 1 Hz poll of `nvidia-smi` and the Linux `powercap` RAPL sysfs counters |
| First sample | `2026-08-27T16:21:53Z` |
| Last sample | `2026-09-05T16:45:32Z` |
| Wall span | 9.02 days (778,979 s) |
| Rows | 778,726 data rows + 1 header |
| Coverage | 100.0 % of nominal 1 Hz |
| Gaps > 5 s | 72; largest 65 s |

## Columns

| column | unit | source |
|---|---|---|
| `ts_unix` | s | sampler clock, UTC |
| `iso_utc` | ISO 8601 | same instant, formatted |
| `gpu0_w`, `gpu1_w`, `gpu_total_w` | W | `nvidia-smi` instantaneous power draw |
| `cpu_pkg_w`, `cpu_core_w` | W | RAPL package / core zones, differenced per second |
| `est_system_w` | W | **derived estimate** — see *Known defect* |
| `gpu0_mib`, `gpu1_mib` | MiB | per-GPU framebuffer in use |
| `gpu0_util`, `gpu1_util` | % | per-GPU utilization |
| `gpu0_c`, `gpu1_c` | °C | per-GPU core temperature |
| `cum_gpu_wh`, `cum_cpu_wh`, `cum_sys_wh` | Wh | running integrals from sampler start |

## Campaign totals at the final sample

```
cum_gpu_wh   14,209.3 Wh
cum_cpu_wh    2,791.0 Wh
cum_sys_wh   26,738.0 Wh      (26.7 kWh)
```

Peak observed `gpu_total_w` is **353.1 W** across both cards, consistent with two 180 W-capped
RTX 5060 Ti under load.

## Known defect — `est_system_w` is not trustworthy as-is

`est_system_w` reaches **9,371.4 W**, which is physically impossible for this machine. The cause is
a counter-wrap artifact: RAPL exposes a monotonic microjoule counter that rolls over at
`max_energy_range_uj`, and the sampler differences consecutive readings without detecting the
rollover, so each wrap produces one enormous spurious delta.

Consequences, in order of severity:

1. **`est_system_w` requires wrap correction or outlier rejection before use.** Filter, or
   recompute from the raw counters with rollover handling.
2. **`cpu_pkg_w` and `cpu_core_w` inherit the same mechanism** and should be checked the same way,
   though their observed range is plausible throughout.
3. **`cum_sys_wh` integrates the uncorrected series**, so the 26.7 kWh total is an upper bound, not
   a measurement. The GPU integral `cum_gpu_wh` does not depend on RAPL and is unaffected.

The GPU columns come from `nvidia-smi`, not RAPL, and show no comparable artifact.

## Truncation

The host lost AC power at `2026-09-05T16:45:32Z` while the sampler was writing. The final row is
complete; the filesystem left 338 trailing NUL bytes in the last allocated block. Those bytes were
removed on 2026-09-09 with no row lost, and the file now terminates on a newline after the
`16:45:32Z` row. The unmodified pre-trim file is retained on the host.

## Status in the report

Wave 4 — the energy curve — was **cancelled** under `DEC-12`, before this series was complete. The
sampler was never stopped, so the trace continued to the power cut. No finding in `PAPER-NOTES.md`
depends on it. It is released as an unclaimed artifact: usable for anyone studying inference energy
on consumer hardware, and honest about why it is not load-bearing here.

## Reuse

```python
import pandas as pd
df = pd.read_csv("power-log.csv.gz", parse_dates=["iso_utc"])

# GPU columns are safe as-is
df["gpu_total_w"].describe()

# est_system_w is not: reject the wrap spikes before using it
clean = df[df["est_system_w"] < 1000]
```
