"""Pure parsing helpers: docker Args -> launch labels, RFC3339Nano timestamps, /slots gauge math."""
from __future__ import annotations

import calendar
import re

# label -> every spelling llama-server accepts for it
LAUNCH_FLAGS: dict[str, tuple[str, ...]] = {
    "ctx": ("-c", "--ctx-size"),
    "ctk": ("-ctk", "--cache-type-k"),
    "ctv": ("-ctv", "--cache-type-v"),
    "ts": ("-ts", "--tensor-split"),
    "sm": ("-sm", "--split-mode"),
    "spec_type": ("--spec-type",),
    "draft_n_max": ("--spec-draft-n-max",),
    "ctxcp": ("-ctxcp", "--ctx-checkpoints"),
    "batch": ("-b", "--batch-size"),
    "ubatch": ("-ub", "--ubatch-size"),
    "np": ("-np", "--parallel"),
    "fa": ("-fa", "--flash-attn"),
}
LAUNCH_LABELS = tuple(LAUNCH_FLAGS) + ("image",)
_SPELLING = {s: label for label, spellings in LAUNCH_FLAGS.items() for s in spellings}
_NUMBER = re.compile(r"^-?\d+(\.\d+)?$")


def parse_launch_args(args: list[str], image: str = "") -> dict[str, str]:
    """Map a llama-server argv (docker inspect .Args) to launch_info labels.

    Handles `-flag value`, `--flag=value`, and bare boolean flags (value "on", e.g. legacy `-fa`).
    The last occurrence wins, as in llama.cpp's own parser. Unset flags map to "".
    """
    out = {label: "" for label in LAUNCH_LABELS}
    i = 0
    while i < len(args):
        tok = args[i]
        name, eq, inline = tok.partition("=")
        label = _SPELLING.get(name)
        if label is None:
            i += 1
            continue
        if eq:
            out[label] = inline
            i += 1
            continue
        nxt = args[i + 1] if i + 1 < len(args) else None
        if nxt is None or (nxt.startswith("-") and not _NUMBER.match(nxt)):
            out[label] = "on"
            i += 1
        else:
            out[label] = nxt
            i += 2
    out["image"] = image
    return out


_TS = re.compile(r"^(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?(Z|[+-]\d{2}:\d{2})$")


def parse_rfc3339(ts: str) -> float | None:
    """RFC3339 / RFC3339Nano (docker's format, 9 fractional digits) -> epoch seconds."""
    m = _TS.match(ts.strip())
    if not m:
        return None
    date, hh, mm, ss, frac, tz = m.groups()
    y, mo, d = (int(x) for x in date.split("-"))
    if y < 1971:  # docker's zero time "0001-01-01T00:00:00Z" = never started
        return None
    epoch = calendar.timegm((y, mo, d, int(hh), int(mm), int(ss), 0, 0, 0))
    if frac:
        epoch += int(frac) / 10 ** len(frac)
    if tz != "Z":
        sign = 1 if tz[0] == "+" else -1
        epoch -= sign * (int(tz[1:3]) * 3600 + int(tz[4:6]) * 60)
    return epoch


def format_rfc3339(epoch: float) -> str:
    import time

    whole = int(epoch)
    nanos = int(round((epoch - whole) * 1e9))
    if nanos >= 1_000_000_000:
        whole, nanos = whole + 1, nanos - 1_000_000_000
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(whole)) + f".{nanos:09d}Z"


def split_docker_timestamp(line: str) -> tuple[float | None, str]:
    """`docker logs --timestamps` prefixes '<RFC3339Nano> '. Returns (epoch|None, rest)."""
    head, sep, rest = line.partition(" ")
    if sep and head[:4].isdigit() and "T" in head:
        ts = parse_rfc3339(head)
        if ts is not None:
            return ts, rest
    return None, line


def slot_gauges(slot: dict) -> dict[str, float]:
    """/slots entry -> contract gauge values.

    kv_tokens = n_prompt_tokens + next_token[0].n_decoded (tokens held in the slot).
    """
    nt = slot.get("next_token") or [{}]
    if isinstance(nt, dict):  # older builds returned an object, not a list
        nt = [nt]
    decoded = int((nt[0] or {}).get("n_decoded", 0) or 0)
    n_prompt = int(slot.get("n_prompt_tokens", 0) or 0)
    return {
        "processing": 1.0 if slot.get("is_processing") else 0.0,
        "kv_tokens": float(n_prompt + decoded),
        "n_ctx": float(slot.get("n_ctx", 0) or 0),
        "prompt_processed_tokens": float(slot.get("n_prompt_tokens_processed", 0) or 0),
        "prompt_cache_tokens": float(slot.get("n_prompt_tokens_cache", 0) or 0),
        "decoded_tokens": float(decoded),
    }


def health_state(status: int | None, body: str = "") -> str:
    """HTTP result of GET /health -> ok|loading|error|down. status None = no connection."""
    if status is None:
        return "down"
    if status == 200:
        return "ok"
    if status == 503:  # llama-server answers 503 {"message":"Loading model"} while loading
        return "loading"
    return "error"
