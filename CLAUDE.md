# multivac-paper — Qwen3.8-27B quantization study, paper & control repo

**Read this file first. Then `docs/build-stream/2026-08-30-quant-bench-trackA.md` — its STATUS
block and the last ledger entry tell you exactly where the work stopped.**

This repository is the *paper and planning* side of a benchmark study. The *machine* side is a
host called `multivac`, reachable as `ssh multivac`. Two deliverables, never conflated:

- **Track A** — the practical answer: one pinned, reproducible coding-agent config line per
  quantization, with a fallback ladder. Priority order: **accuracy → context → tok/s**.
- **Track B** — a neutral technical report. Every claim carries n, CI, protocol label and
  provenance. Track B must not inherit Track A's priority ordering.

Model under test: **Qwen3.8-27B**, Unsloth GGUFs. Active arms: **UD-Q4_K_XL, UD-Q5_K_XL,
UD-Q6_K, UD-Q6_K_XL**. Host: 2× RTX 5060 Ti 16 GB (sm120), 14 GiB RAM.

---

## 1. Which document owns what — read before editing anything

This has bitten twice. Two files with the same name in different places are **not** copies of
equal standing; one is the record and the others are mirrors that silently go stale.

| Document | Owner | How it moves | Never do this |
|---|---|---|---|
| `docs/**` (lifecycle plan, PAPER-NOTES, METHOD-REFERENCES) | **this repo** | `tools/sync-multivac.sh push` → multivac | Edit multivac's copy under `data/build-stream-docs/` — the next push overwrites it |
| `~/CLAUDE.md` on multivac (machine doc: hardware, engines, results) | **multivac** | pulled → `data/multivac-src/multivac-CLAUDE.md` | Edit the mirror expecting it to sync — push does **not** carry it. Edit **on multivac** |
| `PAPER-REFERENCES.md` (the report's reference log) | **multivac**, at `~/Documents/multivac-paper/data/` | pulled → `data/multivac-src/` | Append to a mirror — push does **not** carry it. Append **on multivac** |
| This `CLAUDE.md`, `AGENTS.md` | **this repo** | git + push | — |
| `/srv/bench/**` artifacts | **multivac** | pulled selectively → `data/raw/` | Bulk-sync it; DEC-5 makes the routine sync docs-only |

**Naming rule — one `CLAUDE.md`.** This file, at the repo root, is the only file in the repository
allowed to be named `CLAUDE.md`. Claude Code discovers that name anywhere in the tree and merges
what it finds into an agent's instructions, so multivac's 79 KB machine log is mirrored as
`data/multivac-src/multivac-CLAUDE.md` — it is an engineering record, not instructions for this
repo. Likewise every mirrored document has exactly **one** copy, under `data/multivac-src/`;
`PAPER-REFERENCES.md` once existed three times and the root copy had silently gone stale by 25 KB.
See `data/README.md`.

**Before any `sync-multivac.sh push`: confirm `docs/` is not behind the mirror.** It was once
23.5 KB against the mirror's 69 KB, and a push would have destroyed four hours of work.

```bash
diff -q docs/build-stream/2026-08-30-quant-bench-trackA.md \
        data/multivac-src/build-stream-docs/docs/build-stream/2026-08-30-quant-bench-trackA.md
```

`sync-multivac.sh both` runs **pull then push**, so the mirror lags the push by one step — re-run
`pull` afterwards if you are comparing.

## 2. Syncing between this machine and multivac

Two independent mechanisms. Use both; they cover different things.

**Git (durable, full history)** — a bare repo on multivac is the hub. No GitHub, no origin, never
public.

```bash
git push multivac main          # from here
git pull multivac main
```

On multivac the working clone is `~/repos/multivac-paper` (`git pull` / `git push origin main`).
The bare hub is `~/repos/multivac-paper.git`.

**tar-over-ssh (`tools/sync-multivac.sh`)** — moves live documents in and out of the paths the
running experiments actually read. `pull` = docs of record from multivac; `push` = this repo's
`docs/` + `experiments/`; `artifact <remote> <local>` = selective evidence pull.

> `push` copies `$REPO/experiments` onto `/srv/bench/e12`. **There is deliberately no
> `experiments/` directory in this repo** — the live harness lives on multivac and a stale push
> would overwrite the code a running sweep depends on. The harness is mirrored read-only at
> `data/raw/e12/harness-src/`. To change it, edit on multivac and pull back.

## 3. What is where

```
docs/build-stream/2026-08-30-quant-bench-trackA.md  THE plan: status, phases, decisions, ledger
docs/build-stream/instructions-wave{1..4}.md        per-wave implementer briefs
docs/paper/PAPER-NOTES.md                           paper-candidate findings (PN-1..N, append-only)
docs/paper/PAPER-NOTES-PROTOCOL.md                  how to write one
docs/paper/METHOD-REFERENCES.md                     external sources R1-R7 behind the accuracy design
data/raw/e12/                                       pulled evidence + harness-src/ + quarantine/
data/multivac-src/                                  read-only mirrors: multivac-CLAUDE.md, PAPER-REFERENCES.md
tools/sync-multivac.sh                              the tar sync
data/README.md                                      what lives under data/ and the naming rules
```

On multivac: `/srv/bench/e12/` (current wave), `/srv/bench/` (all prior results, never deleted),
`/srv/models` + `/srv/bench/models` (GGUFs), `~/CLAUDE.md` (machine doc).

## 4. Hard rules — these are not style preferences

1. **Logs before teardown.** A container that started may never be removed until its
   `docker logs` are on disk in `/srv/bench/server-timings/<label>.serverlog`. Evidence loss is
   unrecoverable; a failed run is not.
2. **Docs before deletion.** Nothing is deleted until the ledger entry, the paper notes and the
   manifest naming it are committed. `env-manifest.json` records sha256 + bytes + RepoDigest for
   every deleted item so it can be re-obtained.
3. **Small tests before big tests.** Every battery runs a pilot that must pass before the full run.
4. **Bracket and re-test every ceiling.** A ceiling needs a *failed* rung above it, attempted
   twice — VRAM has ±100–200 MiB of layer-split noise and single failures lie.
5. **Never mix protocols in a table.** PPL protocols 1/2/4 are different instruments. Depth-0 and
   at-depth decode differ 3–5×. Greedy and official-sampling rows are not comparable.
6. **Append, never rewrite.** Ledger entries and paper notes are superseded by new ones, never
   edited. Quarantine bad data under `quarantine/`; do not delete it.
7. **A run that measured nothing must not exit 0**, and must not get a `.done` marker.
8. **One runner at a time.** Every long-running script takes an `flock`. `nohup setsid bash …`
   leaves a *parent and a child* — never wait on a PID from `pgrep`, wait on a condition.

## 5. Configuration facts you will otherwise get wrong

- Sampling defaults on this engine image are **not** the documented llama.cpp defaults. Measured:
  temp 1.0 / top_k 20 / top_p 0.95 / min_p 0.05. Always send an explicit sampling block.
- Thinking is **ON by default**. `/no_think` does not work on this template.
  `chat_template_kwargs {"enable_thinking": false}` works; `{"reasoning_effort":"none"}` raises a
  Jinja exception (PN-3).
- **Official settings (DEC-2)** for task benchmarks — non-thinking: temp 0.7, top_p 0.80,
  top_k 20, min_p 0.0, presence_penalty 1.5. Greedy only for logprob instruments.
- `-fit on` is default and cannot be trusted to bound allocation. Launch measurements with
  `-fit off` and assert reported n_ctx == requested.
- **`-ts` is not portable.** The optimum differs per quant and is not monotone-safe. Re-sweep on
  any change of quant, KV dtype or spec setting. Q6_K's optimum is `58,42`; on Q6_K_XL that
  overshoots and only `56,44` loads.
- Everything measured so far rests on **q4_0 KV**, which has never been validated. SSA step S4 is
  that check.

## 6. Where the work stands

Read the plan's STATUS block for the live answer. As of 2026-08-30T04:20Z:

- **Wave 1** (Phases 1–3) in flight. Q5_K_XL **done** — 262,144 at `-ts 54,46`, and it *fails at
  the default split*: the rebalance sets the ceiling, not the quant. Q6_K_XL **done** — 212,992 at
  `-ts 56,44`, against a published 131,072 (**G21 closed**). Q6_K sweeping, Q4_K_XL queued.
- **Phase 1** partial: delete-1a executed; delete-1b **cancelled** (DEC-9 keeps Q6_K_XL);
  A3's `/srv/models` limb waived, `/` limb kept.
- **Accuracy** has never run. It is Wave 3, redesigned under DEC-11 as the ~3.5 h **Small-Sample
  Accuracy protocol** (SSA) — see the plan's SSA section and `docs/paper/METHOD-REFERENCES.md`.
- The **CF conductor is halted** (`VERDICT-REPAIR-EXHAUSTED`, 01:57Z). Wave 1 finishes hand-driven
  per DEC-8. Do not restart it mid-sweep.

## 7. TODO to total completion

Live checklist — update it as things land. `[~]` = running unattended.

### Wave 1 — context & speed (Phases 1–3)
- [x] T1 quiesce legacy orchestrator · [x] T2 harness gate · [x] T3a manifest + delete-1a
- [x] T4 Q5_K_XL sweep · [x] T5 Q6_K_XL G21 bracket
- [x] T4 Q6_K sweep — 262,144 @ `-ts 58,42`; **A8 closed: adopt `-ctxcp 32`** (+6.8 % decode, same VRAM)
- [x] T4 Q4_K_XL sweep — **262,144 @ `-ts 56,44`, 13.33 tok/s — fastest arm at the full window**
- [x] `summarize_wave1.py` → all four arms in `wave1-summary.md`
- [x] `verify-sweep.sh --stage 1a` **rc=0 green** — 7 race-residue empty logs quarantined with a register; the check itself was left as strict as it was
- [x] ~~T3b delete-1b~~ cancelled (DEC-9); `/srv/models` A3 limb waived, `/` limb passes
- [x] T6 close-out — all acceptance criteria A1-A9 met (L-9)

### Wave 3 — accuracy (SSA, ~3.5 h) — *runs before Wave 2, DEC-10*
- [x] S0 smoke gate
- [x] S1 reference logits
- [x] S2 wikitext-2 KLD — 0.00332 / 0.00447 / 0.00821
- [x] S3 code KLD — 0.00583 / 0.01029 / 0.02153 — **~2x prose, gap widens with quantization**
- [x] S4 **E2 closed** — q4_0 KV costs 0.00296 KLD = 51 % of a quant level; defensible, not free
- [~] S5 HumanEval+ prompt-KLD — harness written (`ssa_s5.py`), running: 164 prompts, 18,432 tokens
- [ ] S6 generative HumanEval+, Q4_K_XL vs Q6_K_XL, paired per-problem — **harness not written**
- [!] S7 *(owner call)* `--hellaswag` / `--winogrande` — the FLAGS are built in but the DATAFILES
      are not on disk and are not in the image; needs two external downloads. I described this as
      "free" when recommending it, which was wrong about the data
- [x] Deleted the `*.kld` logits — 50 GB reclaimed, `/` 87 % -> 63 %; serverlogs pulled locally first

### Wave 2 — MTP/DFlash sweeps (Phases 4–5), *deferred behind Wave 3*
- [ ] G17 `reasoning_effort` equivalence · [ ] G8 MTP losslessness at temp>0 · [ ] presence-penalty probe
- [ ] MTP depth sweep · [ ] draft-KV dtype · [ ] DFlash2 n-max

### Wave 4 — decision & graduation (Phases 9–10)
- [x] **Track A DECIDED** → `docs/paper/TRACK-A-DECISION.md`. Primary **UD-Q6_K** `-ts 58,42 -ctxcp 32` @262,144; Q5_K_XL dominated; Q4_K_XL for VRAM not speed
- [ ] Speed + energy curve at the chosen config (J/tok; PN-11 is the host baseline) — *optional, decision does not depend on it*
- [ ] Track B assembly: provenance fields on every artifact, protocols segregated
- [ ] Graduate into multivac's `~/CLAUDE.md` and `PAPER-REFERENCES.md`
- [ ] Every headline number has a PN entry

### Standing
- [ ] Restore the legacy orchestrator at ship (`/srv/bench/e12/restore_legacy.sh`; state in
      `quiesce-state.json`) — it stays quiesced through Waves 2–4 by design
- [ ] Resolve or retire the halted conductor's stale reviewer task
- [ ] Owner call on S7
- [ ] Re-parse defect fixed in `ssa_kld.py`; `ssa_reparse.py` recovers metrics from serverlogs if it recurs

## 8. Autonomy

`/srv/bench/e12/supervisor.sh` drives the remaining steps on multivac without a human. It
continues past a failing step rather than stopping, records every step's outcome in
`/srv/bench/e12/state/progress.json`, and commits and pushes to the git hub as results land.

```bash
ssh multivac 'cat /srv/bench/e12/state/progress.json'      # what has run and what it returned
ssh multivac 'tail -50 /srv/bench/e12/supervisor.log'      # narrative log
ssh multivac 'ls /srv/bench/e12/state/'                    # step markers
```

A `.failed` marker means that step was **skipped, logged and left for a human** — the chain kept
going. Read its log before re-running it.

## 9. Owner context

Solo researcher; multivac is a personal machine. GPU hours are the scarce resource — think before
spending them, and prefer the instrument that answers the question at the lowest cost. Say plainly
what a measurement can and cannot support; an underpowered result reported as a ranking is worse
than no result. Deliverables are a config recommendation and a technical report, so provenance and
honest limitations matter more than favourable numbers.
