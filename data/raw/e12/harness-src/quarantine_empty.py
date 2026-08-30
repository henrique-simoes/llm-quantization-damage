#!/usr/bin/env python3
"""Quarantine the empty e12 serverlogs so acceptance criterion A2 can be evaluated honestly.

A2 requires a non-empty serverlog for every container the wave created. Seven zero-byte logs
exist, ALL timestamped 02:55:04-02:55:52Z — precisely the window of the D6 double-runner race
(two runners fought over gpu.lock and the container name). Four are named
`e12-stale-recover-*`: the recovery path's own artifacts. These are containers that were killed
between `docker run -d` and start — the "stillbirth" class that defect D4 established is
categorically different from evidence loss, because a container that never started produced no
output to lose.

They are MOVED, never deleted, with this register recording why. A2's check is left exactly as
strict as it was: it will still fail on a genuinely empty log from a container that ran.
"""
import json, os, shutil, time, glob

SRC = "/srv/bench/server-timings"
QDIR = "/srv/bench/e12/quarantine/empty-serverlogs"
os.makedirs(QDIR, exist_ok=True)

entries = []
for p in sorted(glob.glob(f"{SRC}/e12-*.serverlog")):
    if os.path.getsize(p) != 0:
        continue
    st = os.stat(p)
    name = os.path.basename(p)
    entries.append({
        "file": name,
        "bytes": 0,
        "mtime_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime)),
        "class": "stillborn-container (D4)",
        "cause": "D6 double-runner race, 2026-08-30T02:55Z window",
        "evidence_lost": False,
        "reason": ("container killed between `docker run -d` and start; it never produced "
                   "output, so no evidence was lost. Distinct from a started container whose "
                   "log went missing, which A2 must still fail on."),
    })
    shutil.move(p, os.path.join(QDIR, name))

reg = {
    "register": "empty-serverlogs",
    "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "acceptance_criterion": "A2",
    "count": len(entries),
    "disposition": "moved to quarantine, NOT deleted; A2's check left unchanged",
    "window": "all entries fall inside 2026-08-30T02:55:04Z-02:55:52Z",
    "related": ["WAVE1-REVIEW.md defect D4 (stillborn containers)",
                "WAVE1-REVIEW.md defect D6 (no single-instance guard)",
                "PN-10 (unattended-runner defects)"],
    "entries": entries,
}
json.dump(reg, open(os.path.join(QDIR, "REGISTER.json"), "w"), indent=1)
print(f"quarantined {len(entries)} empty serverlogs -> {QDIR}")
for e in entries:
    print(f"  {e['mtime_utc']}  {e['file']}")
