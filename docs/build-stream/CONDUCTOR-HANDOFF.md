# CONDUCTOR HANDOFF — qbench-t1 (multivac Track A quant benchmark)

> ## ⚠️ RETIRED — historical document, do not act on it
>
> The conductor this file hands off **halted on 2026-08-30T01:57Z** with
> `VERDICT-REPAIR-EXHAUSTED` and was deliberately not restarted (DEC-8). Its state directory
> `.compass-forge/` is gone, the watcher process is dead, and the remaining work finished
> hand-driven. **Do not restart it.** Kept as the record of how the run was orchestrated.
>
> Its tooling moved on 2026-08-31 and the paths below are stale:
> `tools/watch-qbench.sh` → `tools/retired/watch-qbench.sh` ·
> `tools/parse_tick.py` → `tools/retired/parse_tick.py` ·
> `recipes/` → `tools/retired/recipes/` ·
> `data/watch/` → `tools/retired/watch-state/`.
>
> For the actual state of the work read the STATUS block of
> [`2026-08-30-quant-bench-trackA.md`](2026-08-30-quant-bench-trackA.md), or `CLAUDE.md` §1.

You are taking over **conductor management** for an autonomous multi-model Build Stream run.
A previous agent set everything up and is stepping back. The pipeline is ALREADY RUNNING —
your job is to supervise it, report to the owner (the human you talk to), and handle the
owner gates. Read this whole file before doing anything. Nothing here requires you to touch
multivac's GPUs directly — the conductor and its workers do that.

---

## 0. The one-paragraph state of the world (as of 2026-08-29 22:50 UTC)

A conductor daemon has been running `qbench-t1` for ~2 h on the local Mac (not on the GPU
host). Wave 1 of 4 is mid-implementation: the implementer (Google GLM 5.3-flash via the `pi`
CLI, session 2, task `qbench-t1-IMPL`) has committed the full e12 experiment harness to the
worktree (3 commits), quiesced the legacy orchestrator on multivac (T1 ✅), and is iterating
on the `validate_v2` gate (T2): positive run ALL GREEN, selftest 3/4 — fault F1 (seeded
ctx-shrink) did NOT fire because the test scenario itself was mis-designed for the quant
(Q4_K_XL no-spec can genuinely report 262,144; MTP is what costs the window). State marker:
`multivac:/srv/bench/e12/state/validate.selftest.failed`. GPUs are idle; no sweep has
started — BY DESIGN (owner rule: no big battery until small tests pass). The implementer is
expected to fix the F1 injection and re-run; if it exhausts its 2 h wall clock, the
conductor retries (retries=2) and the per-cell state files make it resume.

## 1. Topology and paths (memorize these)

| What | Where |
|---|---|
| Plan repo (git, main branch) | `/Users/user/Documents/multivac-paper` |
| **Live worktree (workers work HERE; branch `conductor/qbench-t1`)** | `/Users/user/Documents/multivac-paper-wt-qbench-t1` |
| Lifecycle file (THE durable plan + ledger; worktree copy is authoritative until ship) | `docs/build-stream/2026-08-30-quant-bench-trackA.md` (in both) |
| Frozen Wave-1 plan (the architect's measured ground truth — read it) | worktree: `docs/build-stream/plans/qbench-t1-plan-a.md` (512 lines) |
| Wave instruction files | `docs/build-stream/instructions-wave{1,2,3,4}.md` |
| Paper-notes protocol + ledger | `docs/paper/PAPER-NOTES-PROTOCOL.md`, `docs/paper/PAPER-NOTES.md` |
| Conductor state (cast, consensus, logs) | `.compass-forge/conductor/` in the repo (cast.json, consensus.json, conductor.log, plan-approved) |
| Conductor daemon | PID recorded in `.compass-forge/conductor/conductor.pid`; log: same dir `conductor.log` |
| Audit DB | `~/conductor-logs/multivac-paper-8119f26952/conductor-audit.sqlite3` |
| Watcher daemon (yours now) | `tools/watch-qbench.sh` + `tools/parse_tick.py`; outputs `data/watch/{state.json,events.log,sync.log,watcher.pid}` |
| Sync bridge (docs-only, DEC-5) | `tools/sync-multivac.sh` (pull/push/both/artifact) |
| GPU host | `ssh multivac` (alias configured; BatchMode works). Experiments land in `/srv/bench/e12/`; artifacts mirror selectively into `data/raw/` or `data/bench/` |
| Conductor skill (scripts, protocol) | `/Users/user/Documents/Skills/build-stream-conductor/` (symlinked skills library) |

## 2. Non-negotiable bootstrap before ANY conductor.py call

Every `conductor.py` invocation needs the pinned Compass Forge binary in the environment
(it refuses otherwise: "COMPASS_FORGE_BIN and COMPASS_FORGE_SHA256 are required"):

```bash
eval "$(find -L /Users/user/.pi/agent/skills /Users/user/Documents/Skills \
  -path '*/build-stream-conductor/scripts/resolve-pin.sh' 2>/dev/null | head -1)"
SK=/Users/user/Documents/Skills/build-stream-conductor/scripts
python3 $SK/conductor.py status --project-root /Users/user/Documents/multivac-paper --brief
```

(If `/tmp/cf-env.sh` still exists you can `source /tmp/cf-env.sh` instead. The pin digest
must verify — never fall back to a PATH binary.)

## 3. Your monitoring runbook

**Cadence: check every ~3 minutes while a worker is active; at least every 15 min when idle.**

Quick check (10 s):
```bash
cat data/watch/state.json                       # fresh? (<2 min old, else restart watcher §5)
tail -5 data/watch/events.log                   # transitions/alerts
python3 $SK/conductor.py status --project-root /Users/user/Documents/multivac-paper --brief
grep '"tick"' .compass-forge/conductor/conductor.log | tail -1 | python3 tools/parse_tick.py
```
Reading `--brief`: `open=N` (open tasks) · `ready=N` (dispatchable now) · `active=[session@age]`
· `qbench-t1-code-reviewer=pass|fail|—` (review verdict) · `converged=` · `daemon=up` ·
`AWAITING-OWNER-APPROVAL` / `blocked=N` / `RATE-LIMITED-BLOCKED=...` appear here when present.

Deep dive (any anomaly): full `status` (no --brief) JSON; actor logs at
`.compass-forge/actor-runs/<session>/{stdout,stderr}.log`; worker process tree
(`ps -ax -o pid,ppid,etime,time,command` — find the `pi`/`claude` child of
`worker.example.sh`; **CPU time growing = healthy, network-bound wait is normal**);
worktree `git log --oneline` / `status --short`; `scorecard.py --project-root ...` at stage
completions; tail `conductor.log` (one JSON tick per line).

**Buffered-stdout caveat:** `pi -p` and `claude -p` write stdout only at the end of a turn.
0-byte stdout.log with growing CPU time is NORMAL. Do not kill a worker for a silent log;
kill-worthy is the conductor's own `WEDGED` verdict or a dead process tree.

## 4. Roles and routing (owner-fixed, do NOT change without the owner)

- **architect (solo)**: `claude` CLI, `claude-opus-5`, effort `max`
- **implementer**: `pi` CLI, `zai/glm-5.3-flash`, effort `max`
- **code-reviewer**: `claude` CLI, `claude-opus-5`, effort `max` (owner changed this 2026-08-30)
- **fixer**: `claude` CLI, `claude-opus-4-6`, effort `max`
- No fallback chains (registry `fallbacks: []` — a role that keeps failing parks as
  `blocked` and comes to you/ the owner).
- Registry: `~/.config/build-stream-conductor/defaults.json` (global). Run cast:
  `.compass-forge/conductor/cast.json` (this run). Both already agree — verify before any
  new wave.

## 5. The watcher daemon (you own it now)

Started detached (macOS has **no `setsid`/`timeout` binaries** — detach via python):
```bash
cd /Users/user/Documents/multivac-paper
nohup python3 -c "import os; os.setsid(); os.execvp('bash',['bash','tools/watch-qbench.sh'])" >/dev/null 2>&1 & disown
# stop: kill $(cat data/watch/watcher.pid)
```
It polls the conductor log every 45 s (parse_tick.py), appends transitions to
`data/watch/events.log`, fires macOS notifications (sound "Glass") on: plan-ready,
blocked tasks, rate-limits, health!=ok (WEDGED), convergence; and every 10 min runs the
docs-only sync. If `data/watch/state.json` is stale >2–3 min → restart it with the command
above (check `data/watch/watcher.pid` for a stale pid first).

## 6. The wave flow (generic solo mode — the shape that works)

This run does NOT use a strict wave manifest. **Structural rule learned the hard way:
solo-architect planning cannot carry a wave manifest** (make_cast refuses:
"strict-wave planning intent is three-architect only..."). Each wave is its own conductor
run with a complete implement→review→fix→converge cycle:

1. **Plan**: architect drafts Wave-N plan into `docs/build-stream/plans/` (worktree), plan
   task `qbench-t1-PLAN-A` completes, conductor halts at `AWAITING-OWNER-APPROVAL`.
2. **You present the plan to the owner; on "approve"**:
   `python3 $SK/conductor.py approve --project-root /Users/user/Documents/multivac-paper`
3. The tick dispatches the implementer → review (opus-5) → fix (opus-4.6) loop until the
   reviewer's latest verdict is `pass` → wave converged → ship checklist.
4. **Next wave**: `make_pipeline.py --root <repo> --prefix qbench-t1 --title "Wave N: ..." --instructions @<file> --scope "experiments/,docs/,data/" --with-planning --architects 1`
   then `make_cast.py --root <repo> --worktree <wt> --lifecycle docs/build-stream/2026-08-30-quant-bench-trackA.md --prefix qbench-t1 --with-planning --architects 1`
   (NO --wave-manifest!), then approve. **make_cast CLEARS the stale approval — always
   re-approve after regenerating a cast.**

Wave sequence (owner-approved order): Wave 1 (validation+disk sweep+ts sweeps, IN FLIGHT)
→ Wave 2 (official-settings pilots G17/G8 + MTP/DFlash sweeps) → Wave 3 (PPL/NLL, HE+,
LCB v6 n=100, SWE-bench 25→50, agentic steps, Code-NIAH) → Wave 4 (speed/J-tok, Track A
decision, docs graduation). Details in the instruction files.

## 7. Owner decisions already locked (DEC log in the lifecycle file — cite, don't relitigate)

- **DEC-2**: benchmarks run at OFFICIAL Qwen/Unsloth sampling (non-thinking: temp 0.7,
  top_p 0.80, top_k 20, min_p 0.0, presence 1.5, rep 1.0; thinking: temp 1.0, top_p 0.95,
  top_k 20, min_p 0.0, presence 0.0). Greedy (temp 0) ONLY for logprob instruments
  (PPL/NLL/divergence). G8 implication: spec-decode arms at temp>0 must re-prove
  losslessness (Wave 2 pilot) or run no-spec for accuracy claims.
- **DEC-3/DEC-6**: roles as in §4; solo architect shape.
- **DEC-4**: quants = UD-Q4_K_XL / UD-Q5_K_XL / plain UD-Q6_K; delete list approved
  (IQ4_XS, Q6_K_XL, NVFP4 hf-cache dup, both vLLM images); KEEP `/srv/engines/nvfp4`,
  the 3 active GGUFs, DFlash2 drafter, both llama.cpp images, telemetry, ALL results;
  Q-A1 YES (bracket Q6_K_XL `-ts` before deleting it), Q-A2 byte gate ≥60×10⁹ B on
  /srv/models, Q-A3 legacy orchestrator stays quiesced through Wave 4.
- **DEC-5**: sync scope = DOCUMENTATION ONLY (CLAUDE.md, PAPER-REFERENCES.md, multivac
  paper-data folder, repo docs). Artifacts pulled selectively via
  `tools/sync-multivac.sh artifact <remote-path> <local-dir>`. NOT models/containers/bulk trees.
- **Standing owner rules**: small tests before big tests (a failing selftest STOPS the
  wave — that is success of the gate, not a failure of the run); save ALL logs BEFORE any
  container teardown or deletion (docs → manifest → delete, never the reverse); never
  blind-prune docker; never delete test data or documentation; bracket + re-test every
  marginal VRAM rung; every metric carried through (PPL, KL, HE+, SWE, agentic steps,
  tok/s, prefill, J/tok, VRAM, acceptance, context ceiling, provenance).

## 8. Escalation contract — what you surface to the owner vs handle silently

**Surface immediately**: `AWAITING-OWNER-APPROVAL` (present plan summary + the plan's own
owner-gate questions) · `blocked=N` in --brief (retries exhausted; with no fallbacks this
is terminal until human action) · `RATE-LIMITED-BLOCKED=<role>` (wait out the printed
reset, then `compass-forge task status <ref> open --target <repo>` buys exactly one
re-dispatch; still limited ⇒ re-blocks, bounded) · conductor `WEDGED` verdict · any
owner-gated moment in the wave instructions (e.g., nothing gets deleted until the sweep
artifacts + docs are confirmed committed) · review verdicts on wave completion.

**Handle silently (the conductor self-heals; you just verify)**: reviewer-fail → auto
fix-task → delta re-review; no-verdict recovery; retry counters; worker timeout kill +
re-dispatch (2 h wall per worker; pi/claude idle-kill disabled for pi; retries=2).

**Never do**: hand-write evidence rows; kill the conductor daemon except via
`python3 $SK/conductor.py stop --project-root <repo>`; edit `cast.json` role routes without
mirroring the registry; run GPU jobs by hand outside the conductor's workers (that's how
confounded data happens); `docker image prune -a` on multivac; delete anything on multivac
outside the DEC-4 list.

## 9. Known pitfalls (all learned 2026-08-30, do not rediscover)

1. Every `conductor.py` call needs the pin env (§2). Symptom if missing: RuntimeError.
2. macOS: no `setsid`, no `timeout`. Detach via the python `os.setsid()` wrapper (§5).
   A plain `nohup ... &` child is killed when the bash-tool call ends (process-group kill).
3. multivac has **no rsync** — `tools/sync-multivac.sh` is tar-over-ssh for that reason.
4. `--wave-manifest` is a RELATIVE-path trap: pass an absolute path to make_cast, or it
   fails with "cannot load manifest".
5. `make_cast` clears `plan-approved` + resets `consensus.json` — re-run
   `conductor.py approve` after ANY cast regeneration.
6. The CF task graph may contain `qbench-t1-PLAN-B/C` with status `canceled` — that is
   CORRECT (moot three-architect planning tasks from the original mismatch; solo mode
   ignores them). Do not resurrect them.
7. `pi`/`claude` workers buffer stdout; judge liveness by process-tree CPU time (§3).
8. If the implementer's session 2 hits its 2 h wall mid-iteration, the conductor re-tries a
   fresh worker automatically; `multivac:/srv/bench/e12/state/*` files make every runner
   resumable. Do not manually "help" by launching the runner — let the worker do it.
9. The worktree branch `conductor/qbench-t1` is the LIVE document set; `main` lags until
   ship merges. Read lifecycle/plan files in the worktree.
10. The F1 selftest gap (§0): the correct fix is a fault that MUST shrink (e.g., request
    ctx above the model's 262,144 native cap with `-fit on`). If a fresh implementer
    re-runs instead of fixing, that's acceptable — but the gate must end 4/4 before T3a/T4.

## 10. First actions (in order)

1. Read the lifecycle file Status Block + last ledger entries (worktree copy).
2. Run the §3 quick check; confirm daemon `up`, watcher fresh, `active` role alive (§3
   process-tree probe).
3. Read `docs/build-stream/plans/qbench-t1-plan-a.md` §0 and §6 (you cannot supervise what
   you haven't read — the acceptance criteria A1–A9 are the wave's contract).
4. Report to the owner: one paragraph of current state + when they'll hear from you next.
5. Then just run the cadence. The pipeline does the rest.

Current one-line status at handoff: **implementer session 2 active 1h10m (T2 selftest
3/4, F1 fix expected), GPUs idle, nothing blocked, no alerts, watcher alive.**
