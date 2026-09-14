#!/bin/bash
# power-logger.sh -- long-term, low-footprint power/energy logger for multivac.
# Uses ONLY pre-installed tooling: nvidia-smi (GPU) + kernel RAPL powercap (CPU).
# No packages installed. Append-only CSV, 1 Hz, resumable, wrap-safe.
#
# Columns:
#   ts_unix, iso_utc,
#   gpu0_w, gpu1_w, gpu_total_w,           <- instantaneous GPU power
#   cpu_pkg_w, cpu_core_w,                 <- derived from RAPL cumulative deltas (exact)
#   est_system_w,                          <- GPU + CPU pkg + fixed platform overhead estimate
#   gpu0_mib, gpu1_mib, gpu0_util, gpu1_util, gpu0_c, gpu1_c,
#   cum_gpu_wh, cum_cpu_wh, cum_sys_wh     <- running energy totals (Wh)
#
# Platform overhead (mobo/RAM/NVMe/fans/PSU loss) is NOT measurable without a BMC or
# smart plug on this consumer board; PLATFORM_W is a documented constant, not a measurement.
#
# v2 (2026-09-14): fixes the est_system_w spikes recorded in POWER-LOG.md. A failed RAPL
# read used to return 0, so the next successful read produced a delta equal to the whole
# counter. A failed read now repeats the previous reading (a zero delta for that sample),
# and any CPU delta implying more than RAPL_MAX_W is discarded in favour of the last
# plausible value. Column schema is unchanged. Runs as root under systemd, so RAPL is read
# directly; sudo is used only as a fallback.

OUT=${OUT:-/srv/bench/power-log.csv}
INTERVAL=${INTERVAL:-1}
PLATFORM_W=${PLATFORM_W:-45}     # documented estimate; see note above
RAPL_MAX_W=${RAPL_MAX_W:-250}    # physical ceiling for a 65 W TDP package, with margin
STATE=/srv/bench/.power-logger.state

RAPL_PKG=/sys/class/powercap/intel-rapl:0/energy_uj
RAPL_CORE=/sys/class/powercap/intel-rapl:0:0/energy_uj

read_sysfs() { cat "$1" 2>/dev/null || sudo -n cat "$1" 2>/dev/null; }

RAPL_MAX=$(read_sysfs /sys/class/powercap/intel-rapl:0/max_energy_range_uj)
RAPL_MAX=${RAPL_MAX:-65532610987}

# header only if new file
if [ ! -f "$OUT" ]; then
  echo "ts_unix,iso_utc,gpu0_w,gpu1_w,gpu_total_w,cpu_pkg_w,cpu_core_w,est_system_w,gpu0_mib,gpu1_mib,gpu0_util,gpu1_util,gpu0_c,gpu1_c,cum_gpu_wh,cum_cpu_wh,cum_sys_wh" > "$OUT"
fi

# resume cumulative energy across restarts
if [ -f "$STATE" ]; then . "$STATE"; fi
CUM_GPU_J=${CUM_GPU_J:-0}; CUM_CPU_J=${CUM_CPU_J:-0}; CUM_SYS_J=${CUM_SYS_J:-0}

# read a RAPL counter; on failure repeat the previous value so the delta is zero, not huge
read_rapl() { local v; v=$(read_sysfs "$1"); if [[ "$v" =~ ^[0-9]+$ ]]; then echo "$v"; else echo "$2"; fi; }

prev_pkg=$(read_rapl $RAPL_PKG 0); prev_core=$(read_rapl $RAPL_CORE 0); prev_t=$(date +%s.%N)
last_pkgw=0; last_corew=0

# nvidia-smi in DAEMON mode: one long-lived process streaming samples (low overhead)
nvidia-smi --query-gpu=power.draw,memory.used,utilization.gpu,temperature.gpu \
           --format=csv,noheader,nounits -l $INTERVAL 2>/dev/null | \
while true; do
  # each GPU emits one line per interval; read both
  read -r l0 || break
  read -r l1 || break
  now_t=$(date +%s.%N); ts=$(date +%s); iso=$(date -u +%Y-%m-%dT%H:%M:%SZ)

  g0w=$(echo "$l0" | cut -d, -f1 | tr -d ' '); g0m=$(echo "$l0" | cut -d, -f2 | tr -d ' ')
  g0u=$(echo "$l0" | cut -d, -f3 | tr -d ' '); g0c=$(echo "$l0" | cut -d, -f4 | tr -d ' ')
  g1w=$(echo "$l1" | cut -d, -f1 | tr -d ' '); g1m=$(echo "$l1" | cut -d, -f2 | tr -d ' ')
  g1u=$(echo "$l1" | cut -d, -f3 | tr -d ' '); g1c=$(echo "$l1" | cut -d, -f4 | tr -d ' ')

  cur_pkg=$(read_rapl $RAPL_PKG "$prev_pkg"); cur_core=$(read_rapl $RAPL_CORE "$prev_core")

  read gput cpupkgw cpucorew sysw cgj ccj csj <<<$(awk -v g0="$g0w" -v g1="$g1w" \
      -v pp="$prev_pkg" -v cp="$cur_pkg" -v pc="$prev_core" -v cc="$cur_core" \
      -v pt="$prev_t" -v nt="$now_t" -v mx="$RAPL_MAX" -v plat="$PLATFORM_W" \
      -v lim="$RAPL_MAX_W" -v lpk="$last_pkgw" -v lco="$last_corew" \
      -v cgj="$CUM_GPU_J" -v ccj="$CUM_CPU_J" -v csj="$CUM_SYS_J" 'BEGIN{
    dt = nt - pt; if (dt <= 0) dt = 1;
    gt = g0 + g1;
    dpkg = cp - pp; if (dpkg < 0) dpkg += mx;      # wrap-safe
    dcore = cc - pc; if (dcore < 0) dcore += mx;
    pkgw = (dpkg/1e6)/dt; corew = (dcore/1e6)/dt;
    if (pkgw > lim) pkgw = lpk;                    # implausible delta: keep last good value
    if (corew > lim) corew = lco;
    sysw = gt + pkgw + plat;
    cgj += gt*dt; ccj += pkgw*dt; csj += sysw*dt;
    printf "%.2f %.2f %.2f %.2f %.3f %.3f %.3f", gt, pkgw, corew, sysw, cgj, ccj, csj;
  }')

  printf "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%.4f,%.4f,%.4f\n" \
    "$ts" "$iso" "$g0w" "$g1w" "$gput" "$cpupkgw" "$cpucorew" "$sysw" \
    "$g0m" "$g1m" "$g0u" "$g1u" "$g0c" "$g1c" \
    "$(awk -v j=$cgj 'BEGIN{print j/3600}')" \
    "$(awk -v j=$ccj 'BEGIN{print j/3600}')" \
    "$(awk -v j=$csj 'BEGIN{print j/3600}')" >> "$OUT"

  CUM_GPU_J=$cgj; CUM_CPU_J=$ccj; CUM_SYS_J=$csj
  prev_pkg=$cur_pkg; prev_core=$cur_core; prev_t=$now_t
  last_pkgw=$cpupkgw; last_corew=$cpucorew

  # persist cumulative state every ~60 samples for crash/restart resume
  if [ $((ts % 60)) -eq 0 ]; then
    printf 'CUM_GPU_J=%s\nCUM_CPU_J=%s\nCUM_SYS_J=%s\n' "$cgj" "$ccj" "$csj" > "$STATE"
  fi
done
