#!/usr/bin/env python3
"""Compare exporter Δenergy/Δt per GPU with the mean of 1 Hz nvidia-smi power.draw.instant samples
over the same window. Usage: validate_energy.py [--exporter URL] [--seconds 30]"""
import argparse
import re
import subprocess
import time
import urllib.request

RE = re.compile(r'^nvml_gpu_energy_joules_total\{gpu="(\d+)"[^}]*\} (\S+)$', re.M)


def energy(url):
    text = urllib.request.urlopen(url, timeout=5).read().decode()
    return time.time(), {int(g): float(v) for g, v in RE.findall(text)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exporter", default="http://127.0.0.1:19836/metrics")
    ap.add_argument("--seconds", type=int, default=30)
    a = ap.parse_args()
    samples: dict[int, list[float]] = {}
    t0, e0 = energy(a.exporter)
    deadline = t0 + a.seconds
    while time.time() < deadline:
        tick = time.time()
        out = subprocess.run(["nvidia-smi", "--query-gpu=index,power.draw.instant", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True).stdout
        for row in out.strip().splitlines():
            i, w = (x.strip() for x in row.split(","))
            samples.setdefault(int(i), []).append(float(w))
        time.sleep(max(0.0, 1.0 - (time.time() - tick)))
    t1, e1 = energy(a.exporter)
    dt = t1 - t0
    print(f"window {dt:.2f} s")
    for g in sorted(e0):
        w_exp = (e1[g] - e0[g]) / dt
        s = samples.get(g, [])
        w_smi = sum(s) / len(s) if s else float("nan")
        print(f"gpu {g}: exporter dE/dt = {w_exp:.2f} W ({e1[g] - e0[g]:.1f} J) | nvidia-smi mean = {w_smi:.2f} W "
              f"(n={len(s)}) | diff = {100 * (w_exp - w_smi) / w_smi:+.1f} %")


if __name__ == "__main__":
    main()
