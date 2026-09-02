# multivac-paper — working guide

**What the study is and what it found: [`README.md`](README.md). This file is how to work in the
repository** — what owns what, the rules, the facts that are easy to get wrong, and what is left.
The two do not repeat each other; keep it that way.

**The objective is a technical report for arXiv.** Measurement is complete. Everything remaining is
assembly, and the deliverable lives in [`manuscript/`](manuscript/).

Two products, never conflated:

- **Track A** — the practical answer: one pinned, reproducible coding-agent configuration for this
  host, with a fallback ladder. Priority order **accuracy → context → tok/s**. **DECIDED** —
  [`docs/paper/TRACK-A-DECISION.md`](docs/paper/TRACK-A-DECISION.md).
- **Track B** — the report. Every claim carries n, interval, protocol label and provenance, and
  reports the strongest configuration *per objective*. **Track B must not inherit Track A's
  priority ordering.**

Model: **Qwen3.8-27B**, Unsloth GGUFs. Arms: **UD-Q4_K_XL, UD-Q5_K_XL, UD-Q6_K, UD-Q6_K_XL**
(the last is the divergence reference). Host: 2× RTX 5060 Ti 16 GB (sm120, no NVLink), 14 GiB RAM.

---

## 1. Where the work stands

*As of 2026-08-31. The live answer is the STATUS block and final ledger entry of
[`docs/build-stream/2026-08-30-quant-bench-trackA.md`](docs/build-stream/2026-08-30-quant-bench-trackA.md).*

**No GPU work is queued or running, and none is required.** The last run finished
2026-08-30T16:16Z. Nothing is in flight; both cards are idle.

| programme | state |
|---|---|
| Wave 1 — context ceilings and `-ts` rebalance, 4 arms | **closed** (L-8, L-9) |
| SSA — the accuracy protocol, S0–S5 + S7 | **closed** (L-8, L-11, L-12) |
| S8 — speculative decoding: equivalence, draft depth, at-depth | **closed** (L-13); at-depth half withdrawn (PN-30) |
| S9 — determinism · SSA S6 · DFlash2 | **closed** (L-15) — PN-26, PN-28, PN-29 |
| S9d/S9e — draft depth at matched depth | **closed** (L-17) — underpowered; PN-32 |
| S10 — KL divergence at depth | **INFEASIBLE** (DEC-15, PN-31) — 14 GiB caps the tool at n_ctx 8,192 |
| S11 — greedy divergence at depth | **REJECTED on its own data** — trajectories fork; metric saturated |
| S12 — RULER long-context accuracy | **closed** (L-18) — PN-33, **PN-34** |
| Track A decision | **decided** (L-10), amended twice (S8, then withdrawn by PN-30) |
| Wave 2 breadth · Wave 4 energy curve | **CANCELLED** (DEC-12) |
| The report | **not drafted** — this is the remaining work |

**MEASUREMENT IS CLOSED (L-18, 2026-09-02).** No GPU work is queued and none is required.

Ceilings, MTP n=2 + q4_0 KV + `-sm layer`, each at its own winning ratio:
**Q4_K_XL 262,144 @ `-ts 56,44` · Q5_K_XL 262,144 @ `54,46` · Q6_K 262,144 @ `58,42` ·
Q6_K_XL 212,992 @ `56,44`.** All four fail or fall short at the engine's default split.

The Compass Forge conductor is **halted** (`VERDICT-REPAIR-EXHAUSTED`, 2026-08-30T01:57Z) and is
**not to be restarted** (DEC-8). Its state directory is gone and its tooling is parked in
[`tools/retired/`](tools/retired/).

## 2. Which document owns what — read before editing anything

This has bitten three times. Two files with the same name in different places are **not** copies of
equal standing; one is the record and the others are mirrors that silently go stale.

| document | owner | how it moves | never |
|---|---|---|---|
| `README.md`, `CLAUDE.md`, `AGENTS.md`, `docs/**`, `manuscript/**` | **this repo** | git · `tools/sync-multivac.sh push` | — |
| `~/CLAUDE.md` on multivac (the machine's own log: hardware, engines, historical results) | **multivac** | pulled → `data/multivac-src/multivac-CLAUDE.md` | edit the mirror — push does not carry it. Edit **on multivac** |
| `PAPER-REFERENCES.md` (the report's historical reference log) | **multivac**, at `~/Documents/multivac-paper/data/` | pulled → `data/multivac-src/` | append to the mirror. Append **on multivac** |
| `/srv/bench/**` artifacts | **multivac** | pulled selectively → `data/raw/` | bulk-sync — DEC-5 makes the routine sync docs-only |

**One `CLAUDE.md`.** This file, at the repo root, is the only file in the repository allowed to
carry that name. Claude Code discovers the name anywhere in the tree and merges what it finds into
an agent's instructions, so multivac's 79 KB machine log is mirrored as
`data/multivac-src/multivac-CLAUDE.md` — an engineering record, not instructions. Likewise every
mirrored document has exactly **one** copy, under `data/multivac-src/`.

> **Resolved 2026-08-31: the mirror loop.** `data/multivac-src/build-stream-docs/` was this repo's
> own `docs/`, pushed to multivac and pulled back — 12 files that had silently diverged by up to
> 12 KB. It is removed, and `sync-multivac.sh pull` now prunes that path so it cannot return. If
> you ever see it again, the exclusion has been lost.

## 3. Syncing

Two independent mechanisms; they cover different things.

**Git** — a bare repo on the host is the hub. No GitHub, no public remote, by design.

```bash
git push origin main
```

**tar-over-ssh** — `tools/sync-multivac.sh`: `pull` = documents of record from multivac;
`push` = this repo's `docs/`; `artifact <remote> <local>` = selective evidence pull.

> `push` also copies `$REPO/experiments` onto `/srv/bench/e12`. **There is deliberately no
> `experiments/` directory here** — the live harness lives on multivac and a stale push would
> overwrite it. It is mirrored read-only at `data/raw/e12/harness-src/`. To change it, edit on
> multivac and pull back.

**Before any `push`, confirm `docs/` is not behind the target.** It was once 23.5 KB against the
mirror's 69 KB, and a push would have destroyed four hours of work. `sync-multivac.sh both` runs
pull-then-push, so the mirror lags the push by one step — re-run `pull` if you are comparing.

## 4. Hard rules — not style preferences

1. **Logs before teardown.** A container that started is never removed until its `docker logs` are
   on disk at `/srv/bench/server-timings/<label>.serverlog`. A failed run is recoverable; lost
   evidence is not. This rule is the only reason three separate failure modes were diagnosable.
2. **Docs before deletion.** Nothing is deleted until the ledger entry, the paper note and the
   manifest naming it are committed. `env-manifest.json` records sha256 + bytes + RepoDigest for
   every deleted item so it can be re-obtained.
3. **Small tests before big tests.** Every battery runs a pilot that must pass first.
4. **Bracket and re-test every ceiling.** A ceiling needs a *failed* rung above it, attempted
   twice — layer-split VRAM carries ±100–200 MiB of noise and single failures lie.
5. **Never mix protocols in a table.** PPL protocols 1/2/4 are different instruments. Depth-0 and
   at-depth decode differ 3–5×. Greedy and official-sampling rows are not comparable.
6. **Append, never rewrite.** Ledger entries and paper notes are superseded by new ones, never
   edited. Quarantine bad data under `quarantine/`; do not delete it. When a path changes, record a
   remap note rather than rewriting history — there are three such notes in the tree already.
7. **A run that measured nothing must not exit 0**, and must not get a `.done` marker.
8. **One runner at a time.** Every long-running script takes an `flock`. `nohup setsid bash …`
   leaves a *parent and a child* — never wait on a PID from `pgrep`, wait on a condition.
9. **A finding that is not written down did not happen.** A stage that produced measurements and
   appended no paper note is an incomplete stage. S8 sat undocumented for a day and its headline
   contradicted a premise three documents were still asserting.

## 5. Configuration facts you will otherwise get wrong

- **Speculative decoding is NOT lossless here.** MTP reproduces the no-spec baseline on only
  131/164 problems at greedy with a fixed seed (PN-23). Any document still saying "spec decode is
  greedy-lossless → method affects speed only" is stale — that claim was refuted 2026-08-30.
- Sampling defaults on this engine image are **not** the documented llama.cpp defaults. Measured:
  temp 1.0 / top_k 20 / top_p 0.95 / min_p 0.05. Always send an explicit sampling block.
- **Thinking is ON by default.** `/no_think` does not work on this template.
  `chat_template_kwargs {"enable_thinking": false}` works; `{"reasoning_effort":"none"}` raises a
  Jinja exception (PN-3).
- **Official settings (DEC-2)** for task benchmarks — non-thinking: temp 0.7, top_p 0.80, top_k 20,
  min_p 0.0, presence_penalty 1.5. Greedy is for logprob instruments only.
- `-fit on` is the default and cannot be trusted to bound allocation. Launch measurements with
  `-fit off` and assert reported `n_ctx` == requested.
- **`-ts` is not portable.** The optimum is quant-specific and not monotone-safe. Re-sweep on any
  change of quant, KV dtype or spec setting. Q6_K's optimum is `58,42`; on Q6_K_XL that overshoots
  and only `56,44` loads.
- **`-ctxcp 32`** over the default 4: +6.8 % decode, +7.6 % prefill, identical VRAM (PN-18).
- **q4_0 KV is validated, not free** — 0.002955 ± 0.000127 KLD, 51 % of a quant level (PN-15).
- **A drafter is bound to its engine build.** DFlash2 needs `llama-dflash2:latest` (plus
  `--entrypoint /app/llama-server`); on `llamacpp-mtp:latest` it fails to load and the harness
  records a clean `0.000` that looks like a result (PN-25).
- `/srv/models` is a **separate disk** from `/`. New GGUFs go to `/srv/bench/models/`.

## 6. Where the evidence is

Every headline number traces: **paper note → artifact → serverlog**. Start at
[`docs/paper/PAPER-NOTES.md`](docs/paper/PAPER-NOTES.md) (PN-1…PN-25) and follow its Evidence line.

| you want | go to |
|---|---|
| what a finding claims, with its interval and caveat | `docs/paper/PAPER-NOTES.md` |
| how to write one | `docs/paper/PAPER-NOTES-PROTOCOL.md` |
| the external sources behind the method | `docs/paper/METHOD-REFERENCES.md` (R1–R7) |
| the configuration recommendation and its conditions | `docs/paper/TRACK-A-DECISION.md` |
| why a decision was made | the plan's **Decision log** (DEC-1…DEC-11) |
| what was done, when, and what it verified | the plan's **Ledger** (L-1…L-13) |
| the numbers themselves | `data/raw/e12/` — `tsweep-v2-*.json`, `ssa/`, `s8/` |
| the code that produced them | `data/raw/e12/harness-src/` (read-only mirror) |
| data excluded, and why | `data/raw/e12/quarantine/` |
| historical results (pre-E12) | `data/archive/` and `data/multivac-src/PAPER-REFERENCES.md` |
| raw tool output | `/srv/bench/server-timings/` on the host — gitignored, never committed |

## 7. TODO to completion

### The report — the remaining project scope
- [ ] Draft the report against [`manuscript/OUTLINE.md`](manuscript/OUTLINE.md); every claim traced
      to a PN entry
- [ ] Write threats-to-validity **before** polishing results, not after
- [ ] Every table names its protocol, n and estimator *in the table*
- [ ] Label or exclude pre-2026-08-29 rows (*irreproducible-on-current-images*)
- [ ] Owner call on releasing artifacts with the paper — the repo is private and has no public remote

### S9 — the closing experiments (DEC-12 retained set, in flight)
Design in the plan's §S9. Driven by `/srv/bench/e12/s9_chain.sh`, detached, one `flock`, a failed
phase is logged and skipped — except the pilot, where failure stops the chain.

- [~] **S9a determinism control** — re-runs S8's `nospec` and `mtp2` byte-identically and compares
      each to its own S8 output. Whichever way it lands, PN-23's mechanism stops being "not
      established" and gets an answer.
- [~] **S9b SSA S6** — generative HumanEval+, ladder extremes, paired per problem, official
      sampling, **no-spec on both arms** (PN-23 would otherwise confound it). The generative anchor.
- [~] **S9c DFlash2 on `llama-dflash2:latest`** — the arm S8 voided (PN-25), plus a descending
      at-depth ladder for the 1.19 GiB draft-worker wall.
- [~] **S8 score-parser repair** — `s8-scores.json`'s `parsed` field captured the `1` from `pass@1`
      as the score. Re-parsed with Wilson intervals into `s8-scores-reparsed.json`; original left
      unedited.
- [~] **S9d MTP draft-depth sweep** (DEC-13, reinstated) — 4 arms × 2 matched depths
      {131,072 · 196,608} × n_draft {2,4,8} = 24 cells. Repairs PN-9's quant/depth/ratio confound
      and tests whether PN-24's n=4 ordering generalises. Queued behind S9 on a **blocking**
      `flock` — the running chain is never edited.

Monitor: `tail -f /srv/bench/e12/logs/s9_chain.log` and `s9d_chain.log` · state markers in
`/srv/bench/e12/state/`. Re-run a phase with `rm /srv/bench/e12/state/s9_<phase>.done`
(or `s9d_sweep.done`).

### Cancelled — will not be run (DEC-12)
Recorded so nobody re-derives them as open work. Each becomes a **stated limitation** in the report.
- **Wave 2 breadth**, minus the depth sweep (reinstated as S9d, DEC-13) — G17
  `reasoning_effort` equivalence · G8 losslessness at temp > 0 · presence-penalty probe ·
  draft-KV dtype. The consequence that matters: **PN-23's result stays greedy-only**, and the
  presence-penalty question — arguably the paper's thesis in a second dimension — stays open.
- **Wave 4 energy curve** — no per-config J/tok figure will exist. PN-11 remains the host baseline;
  the historical J/tok table is depth-0 and from the deleted image, so it cannot substitute.

### Graduation and housekeeping
- [ ] Graduate Wave 1 + SSA + S8 into multivac's `PAPER-REFERENCES.md` (append **on multivac**)
- [ ] Restore the legacy orchestrator at ship (`/srv/bench/e12/restore_legacy.sh`; state in
      `data/raw/e12/quiesce-state.json`) — quiesced by design until then
- [ ] Retire the halted conductor's stale reviewer task
- [ ] `verify_1a` carries a `.failed` marker from 2026-08-30T08:18Z, skipped by the supervisor and
      never revisited; the later hand-run passed. Reconcile or record why it stands.

## 8. Owner context

Solo researcher; multivac is a personal machine. **GPU hours are the scarce resource** — think
before spending them and prefer the instrument that answers the question at the lowest cost; that
preference is itself one of the study's findings. Say plainly what a measurement can and cannot
support: an underpowered result reported as a ranking is worse than no result. The deliverable is a
published report, so provenance and honest limitations matter more than favourable numbers.

Communication is often in Portuguese; technical content stays in English.
