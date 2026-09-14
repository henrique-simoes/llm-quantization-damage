#!/usr/bin/env python3
"""Parse-check every PromQL expression in the generated dashboards against a live Prometheus.

    python3 validate_dashboards.py [--prometheus http://localhost:9091] [--grafana-import]

Template variables are replaced with a regex that matches anything; Grafana's built-in interval
variables with fixed durations. Each expression is sent to /api/v1/query. Empty results are fine
(the new exporters may not be deployed yet); only parse/execution errors fail the run.

--grafana-import additionally POSTs every dashboard into a temporary folder "zz-validation" on the
live Grafana (admin credentials from --grafana-auth), checks the import, then deletes the
dashboards and the folder.
stdlib only.
"""
from __future__ import annotations

import os
import argparse
import base64
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

JSON_DIR = Path(__file__).resolve().parent / "provisioning" / "dashboards" / "json"
BUILTINS = {"$__rate_interval": "1m", "$__interval": "1m", "$__range": "1h", "${__range}": "1h"}


def walk_exprs(node, path: str = ""):
    """Yield (path, expr) for every Prometheus query in panels, templating and annotations."""
    if isinstance(node, dict):
        if isinstance(node.get("expr"), str) and node["expr"].strip():
            yield path, node["expr"]
        q = node.get("query")
        if isinstance(q, dict) and isinstance(q.get("query"), str):
            yield path + ".query", q["query"]
        for k, v in node.items():
            title = node.get("title") or node.get("name") or ""
            yield from walk_exprs(v, f"{path}/{title}" if k in ("panels", "targets", "list") and title else path)
    elif isinstance(node, list):
        for v in node:
            yield from walk_exprs(v, path)


def substitute(expr: str) -> str:
    for k, v in BUILTINS.items():
        expr = expr.replace(k, v)
    # $var and ${var} appear inside =~"..." matchers: replace with a match-anything regex.
    return re.sub(r"\$\{?[A-Za-z_][A-Za-z0-9_]*\}?", ".*", expr)


def label_values_to_series(expr: str) -> str:
    # label_values(metric{sel}, label) is a Grafana function, not PromQL: check its selector.
    m = re.match(r"^\s*label_values\((.*),\s*[A-Za-z_][A-Za-z0-9_]*\s*\)\s*$", expr)
    return m.group(1) if m else expr


def prom_query(base: str, expr: str) -> tuple[bool, int, str]:
    data = urllib.parse.urlencode({"query": expr}).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(f"{base}/api/v1/query", data=data), timeout=30) as r:
            body = json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = json.loads(e.read() or b"{}")
    except Exception as e:
        return False, 0, str(e)
    if body.get("status") != "success":
        return False, 0, body.get("error", "unknown")
    res = body["data"]["result"]
    return True, (len(res) if isinstance(res, list) else 1), ""


def grafana(base: str, auth: str, method: str, path: str, payload=None) -> tuple[int, dict]:
    headers = {"Authorization": "Basic " + base64.b64encode(auth.encode()).decode(),
               "Content-Type": "application/json"}
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(base + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"message": raw.decode(errors="replace")}


def grafana_import_check(base: str, auth: str, files: list[Path]) -> int:
    failures = 0
    st, folder = grafana(base, auth, "POST", "/api/folders", {"title": "zz-validation", "uid": "zz-validation"})
    if st not in (200, 201):
        print(f"grafana: cannot create folder zz-validation: {st} {folder}")
        return 1
    imported: list[str] = []
    try:
        for f in files:
            dash = json.loads(f.read_text())
            dash["uid"] = "zzv-" + dash["uid"]
            dash.pop("id", None)
            st, body = grafana(base, auth, "POST", "/api/dashboards/db",
                               {"dashboard": dash, "folderUid": "zz-validation", "overwrite": True})
            if st == 200 and body.get("status") == "success":
                imported.append(dash["uid"])
                st2, got = grafana(base, auth, "GET", f"/api/dashboards/uid/{dash['uid']}")
                n_in = sum(1 for p in dash["panels"])
                n_out = len(got.get("dashboard", {}).get("panels", []))
                ok = st2 == 200 and n_in == n_out
                failures += 0 if ok else 1
                print(f"grafana import {f.name}: {'ok' if ok else 'MISMATCH'} (uid {dash['uid']}, "
                      f"panels sent {n_in}, stored {n_out}, "
                      f"schemaVersion stored {got.get('dashboard', {}).get('schemaVersion')})")
            else:
                failures += 1
                print(f"grafana import {f.name}: FAILED {st} {body}")
    finally:
        for uid in imported:
            st, _ = grafana(base, auth, "DELETE", f"/api/dashboards/uid/{uid}")
            print(f"grafana cleanup: delete dashboard {uid} -> {st}")
        st, _ = grafana(base, auth, "DELETE", "/api/folders/zz-validation?forceDeleteRules=false")
        print(f"grafana cleanup: delete folder zz-validation -> {st}")
        st, left = grafana(base, auth, "GET", "/api/search?query=zz")
        print(f"grafana cleanup: search 'zz' after cleanup -> {len(left) if isinstance(left, list) else left} item(s)")
    return failures


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prometheus", default="http://localhost:9091")
    ap.add_argument("--dir", type=Path, default=JSON_DIR)
    ap.add_argument("--grafana-import", action="store_true")
    ap.add_argument("--grafana", default="http://localhost:3000")
    ap.add_argument("--grafana-auth", default=os.environ.get("GRAFANA_AUTH", ""), help="user:password (default: $GRAFANA_AUTH)")
    ap.add_argument("-v", "--verbose", action="store_true", help="print every query")
    args = ap.parse_args()
    base = args.prometheus.rstrip("/")

    files = sorted(args.dir.glob("*.json"))
    if not files:
        print(f"no dashboards in {args.dir}; run build_dashboards.py first")
        return 2
    total = errors = with_data = 0
    for f in files:
        dash = json.loads(f.read_text())
        n_f = e_f = d_f = 0
        for where, expr in walk_exprs(dash):
            q = substitute(label_values_to_series(expr))
            ok, n, det = prom_query(base, q)
            n_f += 1
            if not ok:
                e_f += 1
                print(f"PARSE/EXEC ERROR {f.name} {where}\n  expr: {expr}\n  sent: {q}\n  error: {det}")
            elif n:
                d_f += 1
            if args.verbose and ok:
                print(f"  {'data ' if n else 'empty'} {where}: {q[:110]}")
        print(f"{f.name}: {n_f} queries, {e_f} errors, {d_f} returning data, {n_f - e_f - d_f} empty")
        total, errors, with_data = total + n_f, errors + e_f, with_data + d_f
    print(f"TOTAL: {total} queries, {errors} parse/exec errors, {with_data} with data, "
          f"{total - errors - with_data} empty (expected until the new exporters are deployed)")

    failures = errors
    if args.grafana_import:
        failures += grafana_import_check(args.grafana.rstrip("/"), args.grafana_auth, files)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
