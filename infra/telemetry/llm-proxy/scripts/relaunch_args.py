#!/usr/bin/env python3
"""Rebuild the `docker run` command of an existing container from `docker inspect`, changing
only llama-server's --host/--port. Reads the inspect JSON (a list) on stdin and prints a
NUL-separated argv on stdout so the shell can exec it without re-quoting.

Usage: docker inspect NAME | relaunch_args.py --host H --port P [--image-env-json FILE]
Carried over: name, image (by immutable image ID), entrypoint, args, binds, network mode,
GPU requests, restart policy, env vars not inherited from the image. Anything else that is
not a Docker default is reported on stderr and makes the tool exit 3 (refuse to guess).
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def replace_flag(args: list[str], names: tuple[str, ...], value: str) -> list[str]:
    out, i, found = [], 0, False
    while i < len(args):
        a = args[i]
        if a in names:
            out += [a, value]
            i += 2
            found = True
            continue
        if any(a.startswith(n + "=") for n in names):
            out.append(a.split("=", 1)[0] + "=" + value)
            found = True
        else:
            out.append(a)
        i += 1
    if not found:
        out += [names[0], value]
    return out


def flag_value(args: list[str], names: tuple[str, ...]) -> str | None:
    for i, a in enumerate(args):
        if a in names and i + 1 < len(args):
            return args[i + 1]
        for n in names:
            if a.startswith(n + "="):
                return a.split("=", 1)[1]
    return None


def build(inspect: dict[str, Any], host: str, port: str, image_env: list[str]) -> tuple[list[str], list[str]]:
    cfg, hc = inspect["Config"], inspect["HostConfig"]
    problems: list[str] = []
    args = replace_flag(list(inspect["Args"]), ("--host",), host)
    args = replace_flag(args, ("--port",), port)
    if "--metrics" not in args:
        args.append("--metrics")
    cmd = ["docker", "run", "-d", "--name", inspect["Name"].lstrip("/")]
    rp = hc.get("RestartPolicy") or {}
    if rp.get("Name") and rp["Name"] != "no":
        cmd += ["--restart", rp["Name"] + (f":{rp['MaximumRetryCount']}"
                                           if rp["Name"] == "on-failure" and rp.get("MaximumRetryCount") else "")]
    if hc.get("NetworkMode") and hc["NetworkMode"] != "default":
        cmd += ["--network", hc["NetworkMode"]]
    for dr in hc.get("DeviceRequests") or []:
        caps = [c for group in dr.get("Capabilities") or [] for c in group]
        if "gpu" not in caps:
            problems.append(f"unhandled device request {dr}")
        elif dr.get("DeviceIDs"):
            cmd += ["--gpus", '"device=' + ",".join(dr["DeviceIDs"]) + '"']
        else:
            cmd += ["--gpus", "all" if dr.get("Count", -1) == -1 else str(dr["Count"])]
    for b in hc.get("Binds") or []:
        cmd += ["-v", b]
    for e in cfg.get("Env") or []:
        if e not in image_env:
            cmd += ["-e", e]
    ep = cfg.get("Entrypoint") or []
    if ep:
        if len(ep) != 1:
            problems.append(f"multi-element entrypoint {ep}")
        cmd += ["--entrypoint", ep[0]]
    if (inspect.get("Path") or (ep[0] if ep else None)) != (ep[0] if ep else inspect.get("Path")):
        problems.append("Path differs from entrypoint")
    # Settings this tool does not reproduce: refuse rather than silently drop them.
    checks = {"Privileged": False, "IpcMode": ("", "private", "shareable"), "PidMode": "",
              "CapAdd": None, "Devices": None, "Ulimits": None, "PortBindings": None,
              "ShmSize": (0, 67108864), "Runtime": ("runc", "", None)}
    for key, ok in checks.items():
        v = hc.get(key)
        if isinstance(ok, tuple):
            good = v in ok
        elif ok is None:
            good = not v
        else:
            good = v == ok
        if not good:
            problems.append(f"HostConfig.{key}={v!r} is not reproduced")
    for mnt in inspect.get("Mounts") or []:
        if mnt.get("Type") != "bind":
            problems.append(f"non-bind mount {mnt.get('Name') or mnt.get('Destination')} not reproduced")
    cmd.append(inspect["Image"])  # immutable sha256 image ID, not the movable tag
    return cmd + args, problems


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    ap.add_argument("--port", required=True)
    ap.add_argument("--image-env-json", help="docker image inspect output, to skip inherited env")
    ap.add_argument("--print-ctx", action="store_true", help="print the -c/--ctx-size value and exit")
    a = ap.parse_args()
    inspect = json.load(sys.stdin)[0]
    if a.print_ctx:
        print(flag_value(inspect["Args"], ("-c", "--ctx-size")) or "")
        return
    image_env: list[str] = []
    if a.image_env_json:
        with open(a.image_env_json) as f:
            image_env = (json.load(f)[0].get("Config") or {}).get("Env") or []
    cmd, problems = build(inspect, a.host, a.port, image_env)
    for p in problems:
        print("relaunch_args: " + p, file=sys.stderr)
    if problems:
        sys.exit(3)
    sys.stdout.write("\0".join(cmd))


if __name__ == "__main__":
    main()
