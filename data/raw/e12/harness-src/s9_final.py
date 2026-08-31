#!/usr/bin/env python3
"""s9_final.py — the three experiments that close the study (DEC-12 retained set).

Wave 2 breadth and the Wave 4 energy curve are CANCELLED (DEC-12). What remains is the set
that either closes a stated open question or repairs a void result:

  A. determinism  — no-spec vs no-spec, and MTP vs MTP, on the SAME 164 problems as S8.
                    Attributes PN-23's 33/164 divergence. This is the whole point: S8 showed
                    MTP is not output-identical but could not say WHY, because it never
                    measured whether this engine is deterministic against ITSELF.
                    Reading the result:
                      nospec==nospec AND mtp2==mtp2  -> the engine is deterministic; the
                          divergence is caused by speculation, and the partial set overlap
                          (Jaccard 0.610) between n=2 and n=4 means the two draft depths
                          diverge at different places, i.e. it is depth-dependent, not random.
                      nospec!=nospec                 -> the engine is NOT deterministic and
                          PN-23 must be restated relative to that floor: the MTP number is
                          only meaningful as an EXCESS over the self-divergence baseline.
                      nospec==nospec BUT mtp2!=mtp2  -> speculation itself is nondeterministic
                          run-to-run, which is the batch-shape/float-associativity story and
                          rules out a fixed verification-rule error.

  B. s6          — SSA S6, the generative anchor the report lacks: UD-Q4_K_XL vs UD-Q6_K_XL
                    (the ladder's extremes) on HumanEval+, PAIRED per problem, at DEC-2
                    official non-thinking sampling, seed-matched. Miller/Anthropic R6: at
                    n=164 the independent-comparison interval is +/-4.6 pts while these arms
                    differ by 1-3, so independent means cannot separate them and a paired
                    per-problem McNemar test is the powered version of the question.
                    RUN NO-SPEC ON BOTH ARMS. This is a direct consequence of PN-23: with MTP
                    on, ~20 % of completions would change for reasons unrelated to the quant,
                    confounding the only comparison this experiment exists to make.
                    A null result here is a reportable finding, not a failure.

  C. dflash      — the arm S8 voided (PN-25). Correct image llama-dflash2:latest with
                    --entrypoint /app/llama-server. Equivalence + speed at 32 K against the S8
                    no-spec baseline, then a descending at-depth ladder to find whether the
                    1.1 GB draft GGUF fits at all near the Track A deployment context.

Hard rules honoured: pilot before battery (--phase pilot), logs persisted before every
teardown (L.save_and_kill), one runner at a time (flock, in s9_chain.sh), and a phase that
measured nothing exits non-zero so the chain cannot mark it done.
"""
import argparse, json, os, subprocess, sys, time

sys.path.insert(0, "/srv/bench/e12/experiments")
import lib_e12 as L

E12  = "/srv/bench/e12"
OUTD = f"{E12}/s9"
S8D  = f"{E12}/s8"
Q6K    = "/srv/bench/models/Qwen3.8-27B-UD-Q6_K.gguf"
Q6KXL  = "/srv/models/Qwen3.8-27B-UD-Q6_K_XL.gguf"
Q4KXL  = "/srv/models/Qwen3.8-27B-UD-Q4_K_XL.gguf"
DRAFT  = "/models/dflash2/Qwen3.8-27B-DFlash2-Q4_K_M.gguf"   # container path
DFIMG  = "llama-dflash2:latest"
DFEP   = "/app/llama-server"     # its default entrypoint is /app/llama-cli, which rejects --host
HE_CTX = 32768

# DEC-2 official non-thinking preset. Used ONLY in phase B; the equivalence phases stay greedy
# because exact-match is only meaningful there (same exception S8 recorded).
OFFICIAL_NON_THINKING = {"temperature": 0.7, "top_p": 0.80, "top_k": 20,
                         "min_p": 0.0, "presence_penalty": 1.5}

# Per-arm winning -ts ratios from Wave 1. NOT portable: re-swept per quant (PN-7).
TS = {"Q6_K": "58,42", "Q6_K_XL": "56,44", "Q4_K_XL": "56,44"}


def log(*a):
    print(f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}]", *a, flush=True)


def image_id(img):
    return subprocess.run(["docker", "inspect", "-f", "{{.Id}}", img],
                          capture_output=True, text=True).stdout.strip()


def load_tasks(n=None):
    from evalplus.data import get_human_eval_plus
    probs = get_human_eval_plus()
    tasks = sorted(probs.items(), key=lambda kv: int(kv[0].split("/")[1]))
    return tasks[:n] if n else tasks


def generate(label, model, tasks, spec_args="", sampling=None, ctx=HE_CTX,
             max_tokens=1024, ts=None, image=L.IMAGE, entrypoint="", ctxcp=32):
    """Launch one configuration and generate a completion for every task.
    Returns a record; rec['ok'] is False unless at least one completion came back."""
    log(f"=== {label}: launching (ctx={ctx}, image={image.split(':')[0]}) ===")
    samp = dict(sampling or {"temperature": 0, "top_p": 1})
    cmd, rc, err = L.launch(model, ctx, kv="q4_0", spec="none", sm="layer",
                            ts=ts, ctxcp=ctxcp, extra=spec_args,
                            image=image, entrypoint=entrypoint)
    rec = {"label": label, "model": model, "spec_args": spec_args, "ctx": ctx,
           "sampling": samp, "max_tokens": max_tokens, "ts": ts,
           "image": image, "image_id": image_id(image), "entrypoint": entrypoint,
           "launch_cmd": cmd, "launch_rc": rc, "argv": None,
           "items": [], "ok": False, "failure_mode": None}
    if rc != 0:
        rec["failure_mode"] = f"launch-rc-{rc}"
        rec["error"] = err[:400]
        L.save_and_kill(f"s9-{label}-launchfail")
        log(f"    LAUNCH FAILED rc={rc}: {err[:200]}")
        return rec
    ok, secs = L.wait_health(900)
    if not ok:
        rec["failure_mode"] = "health-timeout"
        rec["health_wait_s"] = secs
        L.save_and_kill(f"s9-{label}-health")
        log(f"    HEALTH FAILED after {secs}s")
        return rec
    rec["argv"] = L.container_argv()
    rec["n_ctx_reported"] = L.props_nctx()

    t0 = time.time()
    for i, (tid, prob) in enumerate(tasks):
        body = {"messages": [{"role": "user", "content": prob["prompt"]}],
                "max_tokens": max_tokens, "seed": L.SEED,
                # this model reasons by default and returns empty content on a small budget;
                # /no_think does not work on this template (PN-2)
                "chat_template_kwargs": {"enable_thinking": False}}
        body.update(samp)
        try:
            r = L.post("/v1/chat/completions", body, timeout=1800)
            tm = r.get("timings", {}) or {}
            rec["items"].append({
                "task_id": tid,
                "solution": r["choices"][0]["message"]["content"] or "",
                "decode_tok_s": tm.get("predicted_per_second"),
                "predicted_n": tm.get("predicted_n"), "prompt_n": tm.get("prompt_n"),
                "draft_n": tm.get("draft_n"), "draft_n_accepted": tm.get("draft_n_accepted")})
        except Exception as e:
            rec["items"].append({"task_id": tid, "solution": "", "error": str(e)[:200]})
        if (i + 1) % 40 == 0:
            log(f"    {label}: {i+1}/{len(tasks)} ({time.time()-t0:.0f}s)")
    rec["seconds"] = round(time.time() - t0, 1)
    rec["ok"] = sum(1 for it in rec["items"] if it.get("solution")) > 0
    rec["n_empty"] = sum(1 for it in rec["items"] if not it.get("solution"))
    ds = [it["decode_tok_s"] for it in rec["items"] if it.get("decode_tok_s")]
    dn = sum(it.get("draft_n") or 0 for it in rec["items"])
    da = sum(it.get("draft_n_accepted") or 0 for it in rec["items"])
    rec["decode_tok_s_median"] = round(sorted(ds)[len(ds)//2], 3) if ds else None
    rec["acceptance"] = round(da / dn, 4) if dn else None
    L.save_and_kill(f"s9-{label}")
    log(f"=== {label}: {rec['seconds']}s  decode_median={rec['decode_tok_s_median']} "
        f"acceptance={rec['acceptance']} empties={rec['n_empty']} ===")
    return rec


def write_jsonl(rec, path):
    with open(path, "w") as f:
        for it in rec["items"]:
            f.write(json.dumps({"task_id": it["task_id"],
                                "solution": it.get("solution", "")}) + "\n")


def read_jsonl(path):
    d = {}
    if not os.path.exists(path):
        return d
    for line in open(path):
        line = line.strip()
        if line:
            r = json.loads(line)
            d[r["task_id"]] = r.get("solution", "")
    return d


def compare(a_map, b_map, a_name, b_name):
    """Exact-output comparison between two {task_id: text} maps."""
    keys = sorted(set(a_map) & set(b_map), key=lambda k: int(k.split("/")[1]))
    same, diff, firsts, difftasks = 0, 0, [], []
    for k in keys:
        x, y = a_map[k], b_map[k]
        if x == y:
            same += 1
        else:
            diff += 1
            difftasks.append(k)
            firsts.append(next((i for i, (p, q) in enumerate(zip(x, y)) if p != q),
                               min(len(x), len(y))))
    n = same + diff
    return {"a": a_name, "b": b_name, "n": n, "exact_match": same, "differs": diff,
            "exact_match_pct": round(100.0 * same / n, 2) if n else None,
            "first_divergence_char_median": (sorted(firsts)[len(firsts)//2] if firsts else None),
            "identical": diff == 0, "divergent_task_ids": difftasks}


def jaccard(a, b):
    a, b = set(a), set(b)
    return round(len(a & b) / len(a | b), 4) if (a | b) else None


# ------------------------------------------------------------------ A. determinism
def phase_determinism(tasks):
    """Re-run the S8 no-spec and MTP n=2 configurations, byte-identically, and compare each
    to its own S8 output. Everything is held fixed: model, ctx, ts, ctxcp, KV dtype, seed,
    sampling, prompt order, engine image."""
    out = {"experiment": "s9-determinism", "source": "e12-s9", "run_ids": ["s9"],
           "closes": "PN-23 mechanism (was: not established)",
           "quant": "UD-Q6_K", "ts": TS["Q6_K"], "ctxcp": 32, "kv": "q4_0", "ctx": HE_CTX,
           "sampling": "greedy temp=0 top_p=1, seed 20260830 — identical to S8",
           "image_id": image_id(L.IMAGE),
           "design": ("re-run two S8 configurations unchanged and compare each against its own "
                      "S8 output; any difference is engine nondeterminism, since nothing else "
                      "varied. This is the control S8 lacked."),
           "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "runs": []}
    plan = [("nospec-r2", ""), ("mtp2-r2", "--spec-type draft-mtp --spec-draft-n-max 2")]
    for label, spec in plan:
        rec = generate(label, Q6K, tasks, spec_args=spec, ts=TS["Q6_K"])
        write_jsonl(rec, f"{OUTD}/s9-{label}.jsonl")
        out["runs"].append(rec)
        json.dump(out, open(f"{OUTD}/s9-determinism.json", "w"), indent=1)

    # compare each repeat with its S8 original
    base_nospec = read_jsonl(f"{S8D}/s8-nospec.jsonl")
    base_mtp2   = read_jsonl(f"{S8D}/s8-mtp2.jsonl")
    base_mtp4   = read_jsonl(f"{S8D}/s8-mtp4.jsonl")
    r2_nospec   = read_jsonl(f"{OUTD}/s9-nospec-r2.jsonl")
    r2_mtp2     = read_jsonl(f"{OUTD}/s9-mtp2-r2.jsonl")

    cmp_ns = compare(base_nospec, r2_nospec, "s8-nospec", "s9-nospec-r2")
    cmp_m2 = compare(base_mtp2,   r2_mtp2,   "s8-mtp2",   "s9-mtp2-r2")
    # and the S8 divergence this is meant to attribute
    s8_m2_vs_ns = compare(base_nospec, base_mtp2, "s8-nospec", "s8-mtp2")
    s8_m4_vs_ns = compare(base_nospec, base_mtp4, "s8-nospec", "s8-mtp4")
    out["comparisons"] = {"nospec_self": cmp_ns, "mtp2_self": cmp_m2,
                          "s8_mtp2_vs_nospec": s8_m2_vs_ns,
                          "s8_mtp4_vs_nospec": s8_m4_vs_ns}
    out["set_overlap"] = {
        "s8_mtp2_vs_s8_mtp4_jaccard": jaccard(s8_m2_vs_ns["divergent_task_ids"],
                                              s8_m4_vs_ns["divergent_task_ids"]),
        "mtp2_self_vs_s8_mtp2_divergence_jaccard": jaccard(cmp_m2["divergent_task_ids"],
                                                           s8_m2_vs_ns["divergent_task_ids"])}

    ns_det = cmp_ns["identical"]
    m2_det = cmp_m2["identical"]
    if ns_det and m2_det:
        verdict = ("ENGINE-DETERMINISTIC: both configurations reproduce themselves byte-exactly. "
                   "PN-23's divergence is therefore CAUSED BY SPECULATION, not by run-to-run "
                   "nondeterminism, and the partial n=2/n=4 set overlap means it is "
                   "draft-depth-dependent rather than random.")
    elif ns_det and not m2_det:
        verdict = ("SPECULATION IS NONDETERMINISTIC: no-spec reproduces itself exactly but MTP "
                   "does not. This rules out a fixed verification-rule error and supports the "
                   "batch-shape / float-associativity explanation: the draft path itself does "
                   "not produce identical logits run to run.")
    else:
        verdict = ("ENGINE IS NOT DETERMINISTIC: no-spec does not reproduce itself. PN-23 must be "
                   f"RESTATED relative to this floor — self-divergence {cmp_ns['differs']}/"
                   f"{cmp_ns['n']} against MTP's {s8_m2_vs_ns['differs']}/{s8_m2_vs_ns['n']}. "
                   "Only the EXCESS over the floor is attributable to speculation.")
    out["verdict"] = verdict
    out["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    json.dump(out, open(f"{OUTD}/s9-determinism.json", "w"), indent=1)
    log("VERDICT: " + verdict)
    log("nospec self: " + json.dumps({k: v for k, v in cmp_ns.items() if k != "divergent_task_ids"}))
    log("mtp2   self: " + json.dumps({k: v for k, v in cmp_m2.items() if k != "divergent_task_ids"}))
    return sum(1 for r in out["runs"] if r["ok"])


# ------------------------------------------------------------------ B. SSA S6
def phase_s6(tasks):
    """Generative HumanEval+, ladder extremes, paired per problem, official sampling, NO-SPEC."""
    out = {"experiment": "s9-s6", "source": "e12-s9", "run_ids": ["s9"],
           "closes": "SSA S6 — the generative anchor",
           "arms": ["UD-Q4_K_XL", "UD-Q6_K_XL"],
           "arm_rationale": ("the ladder's extremes: the cheapest arm against the reference arm. "
                             "R6 (Miller/Anthropic) — at n=164 the independent-comparison interval "
                             "is +/-4.6 pts while these arms differ by 1-3, so two arms analysed "
                             "PAIRED is the powered version of the question, not four arms."),
           "sampling": OFFICIAL_NON_THINKING,
           "sampling_note": "DEC-2 official non-thinking preset; seed-matched across arms",
           "spec": "NONE on both arms — deliberate",
           "spec_rationale": ("PN-23: MTP changes ~20 % of completions at greedy. Leaving it on "
                              "would confound the quant comparison this experiment exists to make."),
           "image_id": image_id(L.IMAGE),
           "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "runs": []}
    for label, model in [("s6-Q4_K_XL", Q4KXL), ("s6-Q6_K_XL", Q6KXL)]:
        arm = label.split("s6-")[1]
        rec = generate(label, model, tasks, spec_args="", sampling=OFFICIAL_NON_THINKING,
                       ts=TS[arm])
        write_jsonl(rec, f"{OUTD}/s9-{label}.jsonl")
        out["runs"].append(rec)
        json.dump(out, open(f"{OUTD}/s9-s6.json", "w"), indent=1)
    out["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    json.dump(out, open(f"{OUTD}/s9-s6.json", "w"), indent=1)
    return sum(1 for r in out["runs"] if r["ok"])


# ------------------------------------------------------------------ C. DFlash2
def phase_dflash(tasks, ladder):
    """The arm S8 voided. Correct image + entrypoint; equivalence at 32 K, then at-depth fit."""
    out = {"experiment": "s9-dflash", "source": "e12-s9", "run_ids": ["s9"],
           "repairs": "PN-25 — S8's five DFlash cells ran on llamacpp-mtp:latest and could not load the drafter",
           "quant": "UD-Q6_K", "ts": TS["Q6_K"], "ctxcp": 32, "kv": "q4_0",
           "image": DFIMG, "image_id": image_id(DFIMG), "entrypoint": DFEP,
           "drafter": DRAFT, "sampling": "greedy temp=0 top_p=1, seed 20260830",
           "baseline": "s8-nospec.jsonl (same model, ctx, ts, ctxcp, KV, seed, sampling)",
           "baseline_caveat": ("the baseline was produced on llamacpp-mtp:latest; this arm runs on "
                               "llama-dflash2:latest, so an engine-version difference is confounded "
                               "with the speculation effect and the equivalence number must say so"),
           "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "ladder": ladder, "runs": [], "atdepth": []}

    spec = f"--spec-type draft-dflash --spec-draft-n-max 4 -md {DRAFT}"
    rec = generate("dflash4-he", Q6K, tasks, spec_args=spec, ts=TS["Q6_K"],
                   image=DFIMG, entrypoint=DFEP)
    write_jsonl(rec, f"{OUTD}/s9-dflash4-he.jsonl")
    out["runs"].append(rec)
    json.dump(out, open(f"{OUTD}/s9-dflash.json", "w"), indent=1)

    if rec["ok"]:
        out["equivalence"] = compare(read_jsonl(f"{S8D}/s8-nospec.jsonl"),
                                     read_jsonl(f"{OUTD}/s9-dflash4-he.jsonl"),
                                     "s8-nospec", "s9-dflash4")
        log("DFLASH EQUIVALENCE: " + json.dumps(
            {k: v for k, v in out["equivalence"].items() if k != "divergent_task_ids"}))

    # at-depth: descending ladder, first success is this configuration's ceiling
    pad = open(f"{E12}/corpus.txt").read()
    for ctx in ladder:
        log(f"=== dflash atdepth @ {ctx} ===")
        cmd, rc, err = L.launch(Q6K, ctx, kv="q4_0", spec="none", sm="layer",
                                ts=TS["Q6_K"], ctxcp=32, extra=spec,
                                image=DFIMG, entrypoint=DFEP)
        cell = {"ctx": ctx, "launch_cmd": cmd, "ok": False, "failure_mode": None}
        healthy = rc == 0 and L.wait_health(900)[0]
        if not healthy:
            cell["failure_mode"] = "load-or-health-failed"
            cell["error"] = err[:300]
            L.save_and_kill(f"s9-dflash-atdepth-{ctx}")
            cell["failure_class"] = L.classify_failure(
                open(f"{L.TIMINGS_DIR}/s9-dflash-atdepth-{ctx}.serverlog").read()
                if os.path.exists(f"{L.TIMINGS_DIR}/s9-dflash-atdepth-{ctx}.serverlog") else "",
                "load", err)
            out["atdepth"].append(cell)
            log(f"    FAILED ({cell['failure_class']}) -> descending")
            json.dump(out, open(f"{OUTD}/s9-dflash.json", "w"), indent=1)
            continue
        try:
            n_pad = int(ctx * 0.945)
            r = L.post("/v1/chat/completions",
                       {"messages": [{"role": "user", "content": pad[:n_pad * 4]}],
                        "temperature": 0, "top_p": 1, "max_tokens": 192, "seed": L.SEED,
                        "chat_template_kwargs": {"enable_thinking": False}}, timeout=7200)
            tm = r.get("timings", {}) or {}
            dn, da = tm.get("draft_n") or 0, tm.get("draft_n_accepted") or 0
            cell.update({"ok": True, "decode_tok_s": tm.get("predicted_per_second"),
                         "prefill_tok_s": tm.get("prompt_per_second"),
                         "prompt_n": tm.get("prompt_n"),
                         "prefill_frac": round((tm.get("prompt_n") or 0) / ctx, 4),
                         "acceptance": round(da / dn, 4) if dn else None})
            log(f"    ok decode={cell['decode_tok_s']} acc={cell['acceptance']} "
                f"prefill_frac={cell['prefill_frac']}")
        except Exception as e:
            cell["failure_mode"] = "generate-failed"
            cell["error"] = str(e)[:300]
        L.save_and_kill(f"s9-dflash-atdepth-{ctx}")
        out["atdepth"].append(cell)
        json.dump(out, open(f"{OUTD}/s9-dflash.json", "w"), indent=1)
        if cell["ok"]:
            log(f"    highest reachable rung is {ctx} -- not testing lower")
            break

    out["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    json.dump(out, open(f"{OUTD}/s9-dflash.json", "w"), indent=1)
    # a phase that neither generated nor reached any rung measured nothing
    return (1 if rec["ok"] else 0) + sum(1 for c in out["atdepth"] if c["ok"])


# ------------------------------------------------------------------ pilot
def phase_pilot():
    """Hard gate: 5 problems on each engine image before any battery runs.
    Catches the S8 failure class (wrong image / drafter that will not load) in ~6 min
    instead of ~4 h."""
    tasks = load_tasks(5)
    out = {"experiment": "s9-pilot", "source": "e12-s9",
           "purpose": "small-before-big gate for all three s9 phases",
           "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "checks": []}
    cases = [
        ("pilot-mtp-image", Q6K, "", None, L.IMAGE, "", TS["Q6_K"]),
        ("pilot-dflash-image", Q6K,
         f"--spec-type draft-dflash --spec-draft-n-max 4 -md {DRAFT}", None, DFIMG, DFEP,
         TS["Q6_K"]),
        ("pilot-official-sampling", Q4KXL, "", OFFICIAL_NON_THINKING, L.IMAGE, "", TS["Q4_K_XL"]),
    ]
    for label, model, spec, samp, img, ep, ts in cases:
        rec = generate(label, model, tasks, spec_args=spec, sampling=samp, ts=ts,
                       image=img, entrypoint=ep, max_tokens=512)
        out["checks"].append({"label": label, "ok": rec["ok"], "n_empty": rec["n_empty"],
                              "failure_mode": rec["failure_mode"],
                              "decode_tok_s_median": rec["decode_tok_s_median"],
                              "acceptance": rec["acceptance"],
                              "n_ctx_reported": rec.get("n_ctx_reported"),
                              "image_id": rec["image_id"]})
        json.dump(out, open(f"{OUTD}/s9-pilot.json", "w"), indent=1)
    out["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    npass = sum(1 for c in out["checks"] if c["ok"])
    out["verdict"] = f"{npass}/{len(cases)} pilot checks passed"
    json.dump(out, open(f"{OUTD}/s9-pilot.json", "w"), indent=1)
    log("PILOT: " + json.dumps(out["checks"]))
    return npass == len(cases)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True,
                    choices=["pilot", "determinism", "s6", "dflash"])
    ap.add_argument("--ladder", default="262144,212992,163840,131072,65536")
    ap.add_argument("--limit", type=int, default=0, help="task limit (debug only)")
    a = ap.parse_args()
    os.makedirs(OUTD, exist_ok=True)
    L.preflight()

    if a.phase == "pilot":
        ok = phase_pilot()
        log(f"phase pilot: {'PASS' if ok else 'FAIL'}")
        sys.exit(0 if ok else 2)

    tasks = load_tasks(a.limit or None)
    log(f"{len(tasks)} HumanEval+ problems")
    if a.phase == "determinism":
        n = phase_determinism(tasks)
    elif a.phase == "s6":
        n = phase_s6(tasks)
    else:
        n = phase_dflash(tasks, [int(x) for x in a.ladder.split(",")])
    log(f"phase {a.phase} done: {n} successful unit(s)")
    sys.exit(0 if n else 2)      # measured nothing -> non-zero, no .done marker


if __name__ == "__main__":
    main()
