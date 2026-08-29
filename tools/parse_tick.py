#!/usr/bin/env python3
"""parse_tick.py — one conductor.log tick line on stdin -> shell-safe KEY=VALUE assignments."""
import json, sys

try:
    t = json.loads(sys.stdin.read())["tick"]
except Exception:
    sys.exit(1)

ad = t.get("active_detail") or []
roles = ",".join(sorted({a["role"] for a in ad})) if ad else "-"
bv = t.get("role_verdicts") or {}
vs = ",".join(f"{k}={v}" for k, v in sorted(bv.items()))
blocked = t.get("blocked") or []

out = {
    "await": int(bool(t.get("awaiting_owner_approval"))),
    "blocked": len(blocked),
    "blocked_roles": ",".join(str(b) for b in blocked)[:120],
    "health": t.get("health"),
    "conv": int(bool(t.get("converged"))),
    "tasks": t.get("tasks_total"),
    "active": roles[:120],
    "verdicts": vs[:160],
    "rate_blocked": int(bool(t.get("rate_limited_blocked"))),
}
print(";".join(f"{k}={v}" for k, v in out.items()))
