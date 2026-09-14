#!/usr/bin/env python3
"""Check llm.rules.yml against a live Prometheus.

For every recording rule: query the recorded name (after deployment) or, with --expr, the rule's
expression itself (before deployment). For every alert: evaluate its expression. Prints a table of
ok / empty / error and exits non-zero when

  * any query errors, or
  * any recording rule is empty while sum(rate(llm_requests_total[15m])) > 0 (there was traffic),
    unless the rule is listed with --allow-empty.

An empty alert expression is the normal, non-firing state and never fails the check.
stdlib only; PyYAML is used if importable, otherwise a line parser for this file's layout.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_RULES = Path(__file__).resolve().parent / "rules" / "llm.rules.yml"
TRAFFIC_EXPR = "sum(rate(llm_requests_total[15m]))"


def load_rules(path: Path) -> list[dict]:
    """Return [{kind, name, expr, labels}] for every rule in the file."""
    text = path.read_text()
    try:
        import yaml  # type: ignore

        doc = yaml.safe_load(text)
        out = []
        for group in doc.get("groups", []):
            for r in group.get("rules", []):
                kind = "record" if "record" in r else "alert"
                out.append({"kind": kind, "name": r[kind], "expr": " ".join(str(r["expr"]).split()),
                            "labels": r.get("labels") or {}})
        return out
    except ImportError:
        return _parse_rules_fallback(text)


def _parse_rules_fallback(text: str) -> list[dict]:
    # Handles `- record:|- alert:` items with `expr:` either inline or as a `>`/`|` block, and
    # `labels: { k: v }` flow maps — the layout used by llm.rules.yml.
    out: list[dict] = []
    cur: dict | None = None
    in_expr = False
    expr_indent = 0
    for line in text.splitlines():
        m = re.match(r"^(\s*)- (record|alert):\s*(\S+)\s*$", line)
        if m:
            cur = {"kind": m.group(2), "name": m.group(3), "expr": "", "labels": {}}
            out.append(cur)
            in_expr = False
            continue
        if cur is None:
            continue
        if in_expr:
            if line.strip() == "" or (len(line) - len(line.lstrip())) >= expr_indent:
                cur["expr"] += " " + line.strip()
                continue
            in_expr = False
        m = re.match(r"^(\s*)expr:\s*(.*)$", line)
        if m:
            rest = m.group(2).strip()
            if rest in (">", "|", ">-", "|-"):
                in_expr, expr_indent = True, len(m.group(1)) + 2
            else:
                cur["expr"] = rest
            continue
        m = re.match(r"^\s*labels:\s*\{(.*)\}\s*$", line)
        if m:
            for kv in m.group(1).split(","):
                if ":" in kv:
                    k, v = kv.split(":", 1)
                    cur["labels"][k.strip()] = v.strip().strip('"')
    for r in out:
        r["expr"] = " ".join(r["expr"].split())
    return out


def query(base: str, expr: str, timeout: float = 30.0) -> tuple[str, int, str]:
    """Instant query. Returns (status, n_series, detail) with status in ok|empty|error."""
    data = urllib.parse.urlencode({"query": expr}).encode()
    req = urllib.request.Request(f"{base}/api/v1/query", data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read())
        except Exception:
            return "error", 0, f"HTTP {e.code}"
    except Exception as e:  # connection refused, timeout
        return "error", 0, str(e)
    if body.get("status") != "success":
        return "error", 0, body.get("error", "unknown error")
    result = body["data"]["result"]
    n = len(result) if isinstance(result, list) else 1
    return ("ok" if n else "empty"), n, ""


def selector_for(rule: dict) -> str:
    # Recording rules sharing a name differ by static labels (window, scope, position).
    if not rule["labels"]:
        return rule["name"]
    sel = ",".join(f'{k}="{v}"' for k, v in sorted(rule["labels"].items()))
    return f"{rule['name']}{{{sel}}}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prometheus", default="http://localhost:9091")
    ap.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    ap.add_argument("--expr", action="store_true",
                    help="evaluate recording-rule expressions instead of recorded names (pre-deploy)")
    ap.add_argument("--allow-empty", action="append", default=[], metavar="RULE",
                    help="recording rule allowed to be empty under traffic (repeatable), "
                         "e.g. llm:spec_conditional_acceptance on a no-spec server")
    args = ap.parse_args()
    base = args.prometheus.rstrip("/")

    rules = load_rules(args.rules)
    status, _, detail = query(base, TRAFFIC_EXPR)
    if status == "error":
        print(f"cannot evaluate traffic gate: {detail}", file=sys.stderr)
        return 2
    traffic = 0.0
    if status == "ok":
        body = urllib.request.urlopen(f"{base}/api/v1/query?" + urllib.parse.urlencode({"query": TRAFFIC_EXPR}),
                                      timeout=30).read()
        traffic = float(json.loads(body)["data"]["result"][0]["value"][1])

    rows = []
    failures = 0
    for r in rules:
        if r["kind"] == "record":
            q = r["expr"] if args.expr else selector_for(r)
        else:
            q = r["expr"]
        st, n, det = query(base, q)
        flag = ""
        if st == "error":
            failures += 1
            flag = "FAIL"
        elif st == "empty" and r["kind"] == "record" and traffic > 0 and r["name"] not in args.allow_empty:
            failures += 1
            flag = "FAIL"
        label = selector_for(r) if r["kind"] == "record" else r["name"]
        rows.append((r["kind"], label, st, n, flag, det))

    w = max(len(x[1]) for x in rows)
    print(f"traffic gate {TRAFFIC_EXPR} = {traffic:.4g} req/s  "
          f"(mode: {'rule expressions' if args.expr else 'recorded names'})")
    print(f"{'kind':<7}{'rule':<{w + 2}}{'status':<8}{'series':>7}  flag")
    for kind, label, st, n, flag, det in rows:
        line = f"{kind:<7}{label:<{w + 2}}{st:<8}{n:>7}  {flag}"
        if det:
            line += f"  {det}"
        print(line)
    counts = {s: sum(1 for x in rows if x[2] == s) for s in ("ok", "empty", "error")}
    print(f"\n{len(rows)} rules: {counts['ok']} ok, {counts['empty']} empty, {counts['error']} error; "
          f"{failures} failing")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
