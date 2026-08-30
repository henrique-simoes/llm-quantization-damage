#!/usr/bin/env python3
"""validate_v2.py — Wave-1 harness-validation gate (plan qbench-t1-plan-a §3.2).

Positive run:  python3 validate_v2.py            --out /srv/bench/e12/validate-v2.json
Selftest:      python3 validate_v2.py --selftest --out /srv/bench/e12/validate-v2-selftest.json

Contract families:
  C1 launch contract   /props.n_ctx == requested (proves -fit off); total_slots == 1;
                       n_slots/n_ctx_slot echoed in serverlog; full flag set proven from the
                       container argv; flash-attn ON proven from the serverlog param dump
                       (launch carries -lv 5) OR behaviourally (-ctv q4_0 requires FA);
                       response truncated == false; image id matches env-manifest.
  C2 sampling contract DEC-2 non-thinking and thinking blocks read back via
                       generation_settings, all six fields exact, AND proven != the measured
                       server defaults (F-D: temp 1.0/top_k 20/top_p 0.95/min_p 0.05/pres 0.0).
  C3 thinking control  2-token probe: enable_thinking:false => non-empty content + empty
                       reasoning_content; no-control => empty content (gate can fire);
                       reasoning_effort:"none" response recorded verbatim, NOT gated (F-E —
                       Wave 2 owns the G17 verdict).
  C4 provenance        env block complete/non-null; served model resolved from BOTH
                       /props.model_path and the response model, cross-checked against the
                       requested GGUF and its env-manifest sha256.

--selftest injects four seeded faults; each must be CAUGHT (validator names the failing
check): F1 ctx-shrink (-fit on above ceiling -> C1), F2 thinking leak (no control -> C3),
F3 sampling-defaults leak (no sampling fields -> C2), F4 unprovenanced model (C4 refuses to
emit an artifact whose provenance cannot name the served model — llama.cpp IGNORES the
request's model field, so the protection is at the provenance layer, not HTTP).

Exit codes: positive 0 iff C1-C4 all green. Selftest 0 iff all four faults caught by their
expected check. Serverlog is saved for every launch (hard rule 2).
"""
import argparse
import json
import os
import re
import sys
import time

sys.path.insert(0, "/srv/bench/e12/experiments")
import lib_e12 as L

MODEL = "/srv/models/Qwen3.8-27B-UD-Q4_K_XL.gguf"   # cheapest active to load (~180 s at 32K)
CTX = 32768
KV = "q4_0"
SPEC = "mtp2"


def write_json_atomic(path, value):
    """Persist an artifact atomically so a killed runner cannot leave partial JSON."""
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(value, f, indent=1)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def saved_launch(ctx, label, fit="off", extra="", health=600, verbose_env="-lv 5"):
    """Preflight + full-contract launch + health; returns (cmd, argv, health_ok, secs)."""
    pre = L.preflight()
    cmd, rc, err = L.launch(MODEL, ctx, kv=KV, spec=SPEC, fit=fit, extra=extra + " " + verbose_env)
    if rc != 0:
        raise RuntimeError(f"docker run failed: {err}")
    argv = L.container_argv()
    ok, secs = L.wait_health(health)
    return cmd, argv, ok, secs, pre


def tear_down(label):
    nbytes, tg = L.save_and_kill(label)
    return {"serverlog": f"{L.TIMINGS_DIR}/{label}.serverlog", "serverlog_bytes": nbytes,
            "tg_samples": tg, "removed_utc": L.utcnow()}


def check_c1(ctx, cmd, argv, health_ok, health_secs, teardown, prefill_resp=None,
             live_props=None):
    """Launch contract. `live_props` must be captured while the server is UP.
    Returns (ok, detail dict)."""
    d = {"requested_ctx": ctx, "health_ok": health_ok, "health_seconds": health_secs}
    ok = health_ok
    d["health"] = "server healthy" if health_ok else "health FAILED"
    n_ctx = (live_props or {}).get("default_generation_settings", {}).get("n_ctx", 0)
    d["n_ctx_reported"] = n_ctx
    c_nctx = (n_ctx == ctx)
    d["fit_off_n_ctx_matches"] = c_nctx
    ok &= c_nctx
    slots = (live_props or {}).get("total_slots")
    d["total_slots"] = slots
    log = ""
    if teardown.get("serverlog"):
        try:
            with open(teardown["serverlog"], errors="replace") as f:
                log = f.read()
        except Exception:
            log = ""
    m = re.search(r"n_slots = (\d+), n_ctx_slot = (\d+)", log)
    d["serverlog_slots_echo"] = m.groups() if m else None
    c_echo = bool(m) and int(m.group(1)) == 1 and int(m.group(2)) == ctx
    d["serverlog_echo_ok"] = c_echo
    ok &= c_echo
    # if /props does not expose total_slots on this build, the serverlog echo is the slot proof
    c_slots = (slots == 1) if slots is not None else (bool(m) and int(m.group(1)) == 1)
    d["single_slot"] = c_slots
    d["single_slot_source"] = "props" if slots is not None else "serverlog-echo"
    ok &= c_slots
    argv_s = " ".join(argv) if argv else ""
    want = [["-fa", "on"], ["-sm", "layer"], ["-fit", "off"], ["-c", str(ctx)],
            ["-ctk", KV], ["-ctv", KV], ["-ctxcp", "4"], ["-np", "1"]]
    missing = [w for w in want if " ".join(w) not in argv_s]
    d["argv_missing_flags"] = missing
    d["argv_ok"] = (not missing) and bool(argv)
    ok &= d["argv_ok"]
    fa_dump = bool(re.search(r"flash[_ ]?attn\s*=\s*(on|true|1)", log, re.I))
    d["fa_evidence"] = ("serverlog-param-dump" if fa_dump else
                        "behavioural: -ctv q4_0 loaded (FA is REQUIRED for quantized V cache)"
                        if health_ok else "none")
    d["fa_on"] = bool(fa_dump or health_ok)
    ok &= d["fa_on"]
    img = L.image_provenance()
    d["image_id"] = img["image_id"]
    d["image_matches_manifest"] = img["matches_manifest"]
    ok &= img["matches_manifest"]
    trunc = None
    if prefill_resp is not None:
        trunc = prefill_resp.get("truncated")
    d["response_truncated"] = trunc
    # A missing field is not proof of a complete response. The launch gate must
    # fail closed because the depth probe is valid only when the server explicitly
    # reports that it did not truncate the response.
    ok &= (trunc is False)
    d["_cmd"] = cmd
    return ok, d


def readback_generation_settings(sampling, seed=None, n_predict=1, suffix=""):
    body = {"prompt": "Count: one two three." + suffix, "n_predict": n_predict,
            "cache_prompt": False, "seed": seed if seed is not None else L.SEED}
    body.update(sampling)
    r = L.post("/completion", body, timeout=900)
    gs = r.get("generation_settings", {}) or {}
    return r, gs


def cmp_block(gs, want, tol=1e-3):
    """Exact compare for ints; f32-tolerant for floats (the server stores f32:
    0.7 reads back as 0.699999988079071)."""
    fields = {}
    okall = True
    for k, v in want.items():
        got = gs.get(k)
        if isinstance(v, float) or isinstance(got, float):
            okk = isinstance(got, (int, float)) and abs(float(got) - v) <= tol
        else:
            okk = got == v
        fields[k] = {"want": v, "got": got, "ok": okk}
        okall &= okk
    return okall, fields


def _feq(a, b, tol=1e-3):
    return a is not None and abs(float(a) - b) <= tol


def is_server_defaults(gs):
    return (_feq(gs.get("temperature"), L.SERVER_DEFAULTS_MEASURED["temperature"])
            and gs.get("top_k") == L.SERVER_DEFAULTS_MEASURED["top_k"]
            and _feq(gs.get("top_p"), L.SERVER_DEFAULTS_MEASURED["top_p"])
            and _feq(gs.get("min_p"), L.SERVER_DEFAULTS_MEASURED["min_p"])
            and _feq(gs.get("presence_penalty"), L.SERVER_DEFAULTS_MEASURED["presence_penalty"]))


def check_c2():
    d = {}
    ok = True
    r1, gs1 = readback_generation_settings(L.SAMPLING_NON_THINKING, seed=L.SEED)
    ok1, f1 = cmp_block(gs1, L.SAMPLING_NON_THINKING)
    d["non_thinking"] = {"ok": ok1, "fields": f1, "echo": gs1}
    d["non_thinking"]["not_server_defaults"] = not is_server_defaults(gs1)
    ok &= ok1 and d["non_thinking"]["not_server_defaults"]
    r2, gs2 = readback_generation_settings(L.SAMPLING_THINKING, seed=L.SEED + 1)
    ok2, f2 = cmp_block(gs2, L.SAMPLING_THINKING)
    d["thinking"] = {"ok": ok2, "fields": f2, "echo": gs2}
    d["thinking"]["not_server_defaults"] = not is_server_defaults(gs2)
    ok &= ok2 and d["thinking"]["not_server_defaults"]
    return ok, d, r1


def chat(body_extra=None, max_tokens=2, timeout=600):
    body = {"messages": [{"role": "user", "content": "Reply with exactly: OK"}],
            "max_tokens": max_tokens, "seed": L.SEED}
    body.update(L.SAMPLING_NON_THINKING)
    if body_extra:
        body.update(body_extra)
    try:
        r = L.post("/v1/chat/completions", body, timeout=timeout)
        msg = r["choices"][0]["message"]
        return {"status": "ok", "content": msg.get("content") or "",
                "reasoning_content": msg.get("reasoning_content") or "",
                "finish_reason": r["choices"][0].get("finish_reason"),
                "raw": r}
    except Exception as e:
        return {"status": "error", "error": str(e)[:400], "raw": None}


def check_c3():
    d = {}
    ok = True
    off = chat({"chat_template_kwargs": {"enable_thinking": False}})
    c_off = (off["status"] == "ok" and bool((off["content"] or "").strip())
             and len((off["reasoning_content"] or "").strip()) == 0)
    d["enable_thinking_false"] = {"ok": c_off, "content_head": (off["content"] or "")[:80],
                                  "reasoning_len": len(off.get("reasoning_content") or ""),
                                  "finish_reason": off.get("finish_reason")}
    ok &= c_off
    none = chat(None)
    c_none = (none["status"] == "ok" and (none["content"] or "").strip() == "")
    d["no_control"] = {"ok": c_none, "content_head": (none["content"] or "")[:80],
                       "reasoning_len": len(none.get("reasoning_content") or ""),
                       "finish_reason": none.get("finish_reason")}
    ok &= c_none
    try:
        body = {"messages": [{"role": "user", "content": "Reply with exactly: OK"}],
                "max_tokens": 2, "seed": L.SEED,
                "chat_template_kwargs": {"reasoning_effort": "none"}}
        body.update(L.SAMPLING_NON_THINKING)
        r = L.post("/v1/chat/completions", body, timeout=300)
        d["reasoning_effort_none_F_E"] = {"recorded": True, "status": r.get("status", "ok"),
                                          "body": json.dumps(r)[:1200]}
    except Exception as e:
        d["reasoning_effort_none_F_E"] = {"recorded": True, "status": "error",
                                          "body": str(e)[:1200]}
    return ok, d


def resolve_served_model(model_resp_field=None):
    """Served model from TWO independent sources, mapped back to host path."""
    inner = L.props_model_path()
    host = None
    for h, c in L.MODEL_DIRS.items():
        if inner == c or inner.startswith(c + "/"):
            host = inner.replace(c, h, 1)
    return {"props_model_path_inner": inner, "props_model_path_host": host,
            "response_model": model_resp_field}


def check_c4(requested=MODEL, model_resp_field=None, env=None):
    d = {}
    ok = True
    prov = L.gguf_provenance(requested)
    d["requested_model"] = prov
    ok &= bool(prov.get("sha256"))
    served = resolve_served_model(model_resp_field)
    d["served_resolution"] = served
    agree = served["props_model_path_host"] == requested
    d["props_model_matches_requested"] = agree
    ok &= agree
    if model_resp_field is not None:
        resp_host = None
        for h, c in L.MODEL_DIRS.items():
            if str(model_resp_field) == c or str(model_resp_field).startswith(c + "/"):
                resp_host = str(model_resp_field).replace(c, h, 1)
        same = (resp_host == requested) or (str(model_resp_field) == requested)
        d["response_model_matches_requested"] = same
        ok &= same
    else:
        d["response_model_matches_requested"] = False
        ok = False
    need = ["image", "model", "seed", "sampling_non_thinking", "kv_dtype", "spec",
            "ctx_requested", "ctxcp", "free_bytes", "recorded_utc"]
    miss = [k for k in need if not env or env.get(k) in (None, {}, [])]
    d["env_block_missing"] = miss
    ok &= not miss
    return ok, d


# ------------------------------------------------------------------ runs ---
def run_positive(out):
    art = {"experiment": "e12-validate-v2-positive", "when_utc": L.utcnow()}
    t0 = time.time()
    cmd, argv, hok, secs, _pre = saved_launch(CTX, "e12-validate-positive")
    if not hok:
        err = L.container_err(1500)
        td = tear_down("e12-validate-positive")
        art.update({"ok": False, "failed_at": "health", "error": err, "teardown": td,
                    "command": cmd})
        write_json_atomic(out, art)
        print(f"POSITIVE RUN FAILED at health: {err[:300]}", flush=True)
        return 2
    prefill_resp = None
    live_props = {}
    try:
        prefill_resp, gs = readback_generation_settings(L.SAMPLING_NON_THINKING, seed=L.SEED)
        live_props = L.props()          # captured while the server is UP
    except Exception:
        pass  # C1/C2 below handle failures; keep going so teardown still saves the log
    c2ok, c2, r1 = (False, {"error": "request failed"}, None)
    try:
        c2ok, c2, r1 = check_c2()
    except Exception as e:
        c2["error"] = str(e)[:400]
    c3ok, c3 = (False, {})
    try:
        c3ok, c3 = check_c3()
    except Exception as e:
        c3["error"] = str(e)[:400]
    env = L.record_env(MODEL, CTX)
    model_field = (r1 or {}).get("model")
    c4ok, c4 = (False, {})
    try:
        c4ok, c4 = check_c4(MODEL, model_field, env)
    except Exception as e:
        c4["error"] = str(e)[:400]
    td = tear_down("e12-validate-positive")
    c1ok, c1 = check_c1(CTX, cmd, argv, hok, secs, td, prefill_resp, live_props=live_props)
    checks = {"C1": c1ok, "C2": c2ok, "C3": c3ok, "C4": c4ok}
    art.update({"ok": all(checks.values()), "checks": checks,
                "C1": {k: v for k, v in c1.items() if k != "_cmd"},
                "C2": c2, "C3": c3, "C4": c4, "env": env,
                "command": cmd, "teardown": td,
                "elapsed_s": int(time.time() - t0)})
    write_json_atomic(out, art)
    for k in ("C1", "C2", "C3", "C4"):
        print(f"[{'PASS' if checks[k] else 'FAIL'}] {k}", flush=True)
    print(f"POSITIVE RUN: {'ok' if art['ok'] else 'FAILED'} -> {out}", flush=True)
    return 0 if art["ok"] else 1


def run_selftest(out):
    """Four seeded faults; each must be caught by its expected check.
    Uses TWO launches: a contract-compliant control (F2/F3/F4 are request/artifact-level
    faults on the control server) and the F1 launch (-fit on above the ceiling)."""
    faults = []
    art = {"experiment": "e12-validate-v2-selftest", "when_utc": L.utcnow(),
           "faults": faults}

    # ---- control launch (contract-compliant) ----
    cmd, argv, hok, secs, _pre = saved_launch(CTX, "e12-selftest-control")
    if not hok:
        err = L.container_err(1500)
        tear_down("e12-selftest-control")
        art["ok"] = False
        art["error"] = f"control launch unhealthy: {err[:300]}"
        write_json_atomic(out, art)
        print("SELFTEST ABORTED: control launch unhealthy", flush=True)
        return 2
    env = L.record_env(MODEL, CTX)

    # ---- F2 thinking leak: omit chat_template_kwargs -> C3 ----
    none = chat(None)
    caught2 = (none["status"] == "ok" and (none["content"] or "").strip() == ""
               and none.get("finish_reason") == "length"
               and len((none.get("reasoning_content") or "").strip()) > 0)
    faults.append({"id": "F2", "injected": "no chat_template_kwargs (thinking ON by default)",
                   "caught": caught2, "caught_by": "C3" if caught2 else None,
                   "detail": {"content_head": (none.get("content") or "")[:60],
                              "reasoning_len": len(none.get("reasoning_content") or ""),
                              "finish_reason": none.get("finish_reason")}})

    # ---- F3 sampling-defaults leak: request WITHOUT sampling fields -> C2 ----
    try:
        r = L.post("/completion", {"prompt": "Count: one two three.", "n_predict": 1,
                                   "cache_prompt": False, "seed": L.SEED}, timeout=900)
        gs = r.get("generation_settings", {}) or {}
        leaked = is_server_defaults(gs)
        caught3 = leaked
        faults.append({"id": "F3", "injected": "request carries no sampling fields",
                       "caught": caught3, "caught_by": "C2" if caught3 else None,
                       "detail": {"readback": gs,
                                  "expected_defaults_F_D": L.SERVER_DEFAULTS_MEASURED}})
    except Exception as e:
        faults.append({"id": "F3", "injected": "request carries no sampling fields",
                       "caught": False, "caught_by": None, "detail": {"error": str(e)[:300]}})

    # ---- F4 unprovenanced model -> C4 refuses ----
    # (a) requested != served: llama.cpp ignores the client's model field, so the honest
    #     control is provenance-level: the validator must refuse when the requested GGUF
    #     does not match the served one (/props.model_path + response model).
    resp_field = None
    try:
        r1, _gs = readback_generation_settings(L.SAMPLING_NON_THINKING, seed=L.SEED + 2)
        resp_field = r1.get("model")
        http_no_model = L.post("/completion", {"prompt": "x", "n_predict": 1,
                                               "cache_prompt": False}, timeout=300)
        f4_http = {"http_200_without_model_field": True,
                   "note": "llama.cpp ignores the client model field (HTTP 200) — "
                           "protection lives in C4 provenance, by design (plan F4 note)"}
    except Exception as e:
        resp_field, f4_http = None, {"error": str(e)[:200]}
    c4_mismatch_ok, c4_mismatch = check_c4(requested="/srv/models/Qwen3.8-27B-UD-Q5_K_XL.gguf",
                                           model_resp_field=resp_field, env=env)
    caught4a = (not c4_mismatch_ok) and (
        c4_mismatch.get("props_model_matches_requested") is False)
    # (b) manifest absence: use a deliberately nonexistent self-test path. The
    # real Q6_K champion is pinned by T3a before validation is re-run, so using
    # it here would make this seeded fault disappear on a correct manifest.
    absent_path = "/srv/bench/models/Qwen3.8-27B-UD-UNPINNED-SELFTEST.gguf"
    absent = L.gguf_provenance(absent_path, compute_if_missing=False)
    caught4b = absent.get("sha256") is None
    caught4 = caught4a and caught4b
    faults.append({"id": "F4", "injected": "requested-model mismatch (Q5_K_XL requested vs "
                                            "Q4_K_XL served) + manifest-absent GGUF lookup",
                   "caught": caught4, "caught_by": "C4" if caught4 else None,
                   "detail": {"mismatch_rejected": caught4a, "absence_rejected": caught4b,
                              "absent_probe": absent, "http": f4_http}})

    td = tear_down("e12-selftest-control")

    # ---- F1 ctx-shrink: -fit on above the ceiling -> C1 ----
    # Stage 1 (plan-literal): -fit on with -c 262144 on Q4_K_XL. On THIS engine the load
    # succeeded with the full 262,144 reported (contrary to e11's init-hang at fit-off) —
    # if so, the fault does not materialize and is recorded as a finding; stage 2 then
    # injects an un-fittable request that must clamp (silent shrink -> C1 catches).
    try:
        pre = L.preflight()
        f1_stages = []
        caught1 = False
        cmd1, rc1, err1 = L.launch(MODEL, 262144, kv=KV, spec=SPEC, fit="on")
        f1_cmd = cmd1
        if rc1 != 0:
            caught1 = True
            f1_stages.append({"stage": "docker-run", "caught": True, "error": err1[:300]})
        else:
            okh, secs1 = L.wait_health(600)
            if not okh:
                caught1 = True
                f1_stages.append({"stage": "health", "caught": True,
                                  "error": L.container_err(600)[:300]})
            else:
                n_ctx = L.props_nctx()
                shrunk = (n_ctx != 262144)
                f1_stages.append({"stage": "fit-on-262144", "caught": shrunk,
                                  "n_ctx_reported": n_ctx,
                                  "note": ("silent shrink caught" if shrunk else
                                           "FAULT DID NOT MATERIALIZE: this engine loaded and "
                                           "reported 262,144 with -fit on (e11 saw init-hang at "
                                           "fit-off) — recorded as a Wave-1 finding")})
                caught1 |= shrunk
            tear_down("e12-selftest-f1")
        if not caught1:
            L.preflight()
            cmd1, rc1, err1 = L.launch(MODEL, 999999999, kv=KV, spec=SPEC, fit="on")
            f1_cmd = cmd1
            if rc1 != 0:
                caught1 = True
                f1_stages.append({"stage": "docker-run-999999999", "caught": True,
                                  "error": err1[:300]})
            else:
                okh, secs1 = L.wait_health(600)
                if not okh:
                    caught1 = True
                    f1_stages.append({"stage": "health-999999999", "caught": True,
                                      "error": L.container_err(600)[:300]})
                else:
                    n_ctx = L.props_nctx()
                    shrunk = (n_ctx != 999999999)
                    f1_stages.append({"stage": "fit-on-999999999", "caught": shrunk,
                                      "n_ctx_reported": n_ctx,
                                      "note": "un-fittable request must clamp -> props "
                                              "n_ctx < requested is the C1 signal"})
                    caught1 |= shrunk
                tear_down("e12-selftest-f1b")
        faults.append({"id": "F1", "injected": "-fit on above the ceiling (262,144, then "
                                               "999,999,999 if unshrunk)",
                       "caught": caught1, "caught_by": "C1" if caught1 else None,
                       "detail": {"stages": f1_stages}})
    except Exception as e:
        faults.append({"id": "F1", "injected": "-fit on above the ceiling", "caught": False,
                       "caught_by": None, "detail": {"error": str(e)[:300]}})

    art["faults"] = faults
    art["ok"] = all(f["caught"] and f["caught_by"] for f in faults)
    art["control_command"] = cmd
    art["teardown"] = td
    art["env"] = env
    write_json_atomic(out, art)
    for f in faults:
        print(f"[{'CAUGHT' if f['caught'] else 'MISSED'}] {f['id']} by {f['caught_by']}: "
              f"{json.dumps(f['detail'])[:200]}", flush=True)
    print(f"SELFTEST: {'all faults caught' if art['ok'] else 'FAILURES PRESENT'} -> {out}",
          flush=True)
    return 0 if art["ok"] else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out", default="/srv/bench/e12/validate-v2.json")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(run_selftest(a.out))
    sys.exit(run_positive(a.out))


if __name__ == "__main__":
    main()
