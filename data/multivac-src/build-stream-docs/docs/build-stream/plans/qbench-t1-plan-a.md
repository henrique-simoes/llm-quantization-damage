# Plan A — Wave 1: harness validation, disk sweep, bring-up + `-ts` rebalance sweeps

**Task** `qbench-t1-PLAN-A` · **Role** `qbench-t1-architect-a` · **Slot** a · **Phase** draft (solo run — this plan stands on its own and goes to the owner)
**Scope** Lifecycle Phases 1–3 of `docs/build-stream/2026-08-30-quant-bench-trackA.md`, per `docs/build-stream/instructions-wave1.md`
**Authored** 2026-08-29 · claude-opus-5 @ effort=max · grounded in live probes of `multivac` (§1), not on documentation alone

---

## 0. Summary for the owner

Wave 1 is buildable as specified. Live reconnaissance of the host surfaced **five facts that change
the plan** and **two documented "facts" that are wrong**. All are handled below; three need an
owner call (Q-A1…Q-A3), and **none of them block starting**.

| # | Finding | Consequence |
|---|---|---|
| **F-A** | The legacy orchestrator (`watchdog.sh` pid 2810112 up 1d23h, `worker.sh` pid 3818720 up 23h) **is still running** and its `job_agentic_steps` launches `docker run --name llamasrv --port 8080` and calls `kill_server llamasrv ""` — **an empty label, which removes the container without saving its docker logs**. | Direct collision + a hard-rule-2 violation waiting to happen. **T1 quiesces it first.** |
| **F-B** | `UD-Q6_K.gguf` (21.98 GB, the current champion quant) lives in `/srv/bench/models/` → on `/`, **not** on `/srv/models`; and it is **absent from `env-manifest.json`** — the champion quant has no sha256 pin. | The delete list frees `/srv/models` only; the `/` target rests entirely on the two vLLM images. E0 provenance hole must be closed in T3a. |
| **F-C** | Measured deletion arithmetic lands `/srv/models` at **64.22 GB / 59.81 GiB free**. The `≥60 GB` gate **passes in decimal GB (margin 4.2 GB) and fails by 204 MB in GiB** — and `df -h` rounds 59.81 GiB up to `60G`, so a casual check looks like a pass either way. | Gate must be defined in explicit bytes. **Q-A2** pre-authorizes the escalation. |
| **F-D** | The lifecycle file's R1 states llama.cpp defaults are `temp 0.80 / top_k 40 / top_p 0.95 / min_p 0.05`. **Measured on `llamacpp-mtp:latest`: `temp 1.0 / top_k 20 / top_p 0.95 / min_p 0.05 / presence 0.0`** — a *fourth* configuration, ≈Qwen's *thinking* preset with the wrong `min_p`. | The hazard is real but its shape is different; the F3 negative control asserts the measured values. Doc correction owed. |
| **F-E** | `{"reasoning_effort":"none"}` **failed** on this template (no `choices` in the response) while `{"enable_thinking":false}` works. | Early G17 signal. Wave 1 records it; Wave 2 still owns the verdict. |

Two deliberate deviations from the wave-1 text, both preserving every approved decision:
**D1** — run the Q6_K_XL `-ts` bracket *before* deleting it (closes G21 for ~75 min; deleting first makes a
probably-wrong published ceiling permanently uncorrectable). **D2** — "keep the fastest that loads"
gets a noise floor before it is allowed to pick a winner.

**Estimated cost: 8–11 h GPU + ~3 h non-GPU.** This exceeds the conductor's 2 h worker wall-clock,
so §7 mandates a detached `nohup` runner (there is no `tmux` on the host).

---

## 1. Ground truth (measured on multivac, 2026-08-29, not quoted from docs)

### 1.1 Host

2× RTX 5060 Ti 16 GB (sm120), 15,650 MiB usable/GPU (env-manifest), 16,311 MiB card total, both idle at 2 MiB.
14 GiB RAM + 35 GiB swap (3 GiB used). Python 3.14.4. venvs `/srv/bench/.venv-evalplus`, `.venv-swebench`.
**No `tmux`, no `jq`** — `nohup` + pid-file is the only detachment convention available.

### 1.2 Disks — exact bytes (`df -B1`, `du -sb`)

| mount | dev | size | used | **available** |
|---|---|---|---|---|
| `/srv/models` | /dev/sda | 117,549,133,824 | 110,304,100,352 | **1,226,551,296 B = 1.14 GiB (99 %)** |
| `/` (holds `/srv/bench` 33 G, `/srv/engines` 22 G, `/var/lib/docker`) | /dev/sdb2 | 234,039,422,976 | 198,522,765,312 | **23,553,507,328 B = 21.94 GiB (90 %)** |

`/dev/sda` reserves 1,465,260 × 4096 B = 6.0 GB for root (already excluded from "available").
`docker info` → Docker Root Dir `/var/lib/docker`, storage driver `overlayfs`, **on `/`**.

### 1.3 Delete-list ledger (measured sizes, mount-attributed)

| item | mount | bytes |
|---|---|---|
| `/srv/models/Qwen3.8-27B-UD-IQ4_XS.gguf` | /srv/models | 14,252,845,984 |
| `/srv/models/Qwen3.8-27B-UD-Q6_K_XL.gguf` | /srv/models | 25,299,061,664 |
| `/srv/models/.hf-cache/models--unsloth--Qwen3.8-27B-NVFP4` | /srv/models | 23,444,506,232 |
| `vllm/vllm-openai:nightly` | / | 28.82 GB **unique** (shared 6.9 kB) |
| `vllm/vllm-openai:v0.27.1` | / | 30.84 GB **unique** (shared 6.9 kB) |

→ `/srv/models` after: 1,226,551,296 + 62,996,413,880 = **64,222,965,176 B = 64.22 GB = 59.81 GiB**
→ `/` after: 23.55 + 59.66 = **≈ 83.2 GB = 77.5 GiB** (target ≥55 GB: passes under either reading)

**`docker system df` reports build cache 41/41 active, `0 B` reclaimable** → `docker builder prune`
(dangling-only) will yield ≈ 0. Do not budget for it. **Never `-a`.**

**Not on the delete list ⇒ KEEP** (stated explicitly so nobody "helps"):
`.hf-cache/hub` (3,875,861,645 B), `.hf-cache/models--z-lab--Qwen3.8-27B-DFlash2` (3,849,114,297 B),
`/srv/engines/nvfp4` (22 GB, DEC-4 explicit KEEP), all three active GGUFs, the DFlash2 drafter,
`llamacpp-mtp:latest` + `llama-dflash2:latest`, the six telemetry containers/images, **all of
`/srv/bench/**`** including `champion-20260821` (2.2 GB) and **`orchestrator/state/*.done`** (see F-A).

### 1.4 Existing harness — extend, do not rewrite (`/srv/bench/e11/`)

`lib_probe.py` (launch/health/`/props`/tokenize/kill_server), `ctx_ceiling.py` (**behavioural**
ceiling probe: healthy + `/props n_ctx == requested` + real 95 % prefill + generate; VRAM recorded,
never gated — the fix for E1's noise-band threshold bug), `pad.py` (token-exact django pads,
disk-cached; identical pads across configs are what make cross-config comparison valid),
`tsweep.py` (**carries the G13 defect**), `validate2.py`, `speed_curve.py`, `depth_bench.py`.
Cached pads already exist for 186,265 / 232,960 / 248,524 / 65,536 / 8,192 tokens.

### 1.5 Engine flags — verified present on `llamacpp-mtp:latest` (`--help`, live)

`-fa {on,off,auto}` (default `auto`), `-fit`, `-fitt`, `-fitc`, `-ts`, `-sm {none,layer,row,tensor}`,
`-ctxcp`, `-kvu`, `-np` (default −1 auto), `--cache-reuse`, `--chat-template-kwargs`,
**`--jinja` default *enabled***, `--spec-draft-n-max` (default 3), `--spec-draft-p-min` (0.00),
`--spec-draft-p-split`, and **`-ctkd`/`-ctvd` = `--spec-draft-type-k/-v` exist** → Wave 2's new
draft-KV axis is legal on this image. Engine `0.3.0-dev (build 1, commit d222767)`,
image id `sha256:feb0231976b6…`.

### 1.6 Server API surface — verified by a live 32K bring-up (architect recon)

A Q4_K_XL server was launched at `-c 32768` under the full candidate contract, probed, and torn
down **log-first** per hard rule 2 (`/srv/bench/server-timings/arch-recon-props-20260829.serverlog`,
4,160 B; container removed; `gpu.lock` released; GPUs back to 2 MiB). Load time **≈180 s at 32 K**.

1. **`/completion` echoes the effective per-request sampling** in `generation_settings` — sending
   the DEC-2 non-thinking block read back exactly `temperature 0.7, top_k 20, top_p 0.80,
   min_p 0.0, presence_penalty 1.5, repeat_penalty 1.0, seed 20260830`.
   **⇒ the sampling contract is directly assertable. This is the check that kills the whole
   "wrong settings" run-wasting class, and it costs one request.**
2. **`/props.default_generation_settings.params` = `temp 1.0, top_k 20, top_p 0.95, min_p 0.05,
   presence_penalty 0.0, repeat_penalty 1.0`** → **F-D**: not the documented default set.
3. **`/props` reports `"speculative.types": "none"` even though MTP was active** — the same
   request returned `timings.draft_n = 16, draft_n_accepted = 14`.
   **⇒ ground truth for "is spec decode live" is `timings.draft_n`, never `/props`.**
4. Thinking control, `/v1/chat/completions`, `max_tokens: 2`:
   - no control → `content=''`, `reasoning_content` len 8, `finish_reason=length` → **thinking ON by default, and the 2-token probe is a ~1 s discriminator**;
   - `{"enable_thinking": false}` → `content='OK'`, `reasoning_content` len 0, `finish=stop` ✓;
   - `{"reasoning_effort": "none"}` → **request failed, response had no `choices`** (**F-E**; error body not captured — capturing it is a Wave-1 recording duty, and the verdict stays Wave 2's).
5. `/props.model_path` and the response's top-level `model` both name the served GGUF
   → the F4 provenance cross-check has **two independent sources**.
6. Response also exposes `truncated`, `tokens_evaluated`, `tokens_cached` → cheap extra
   launch-contract assertions (a silently truncated prompt invalidates any depth measurement).

### 1.7 Baseline the sweep must improve on

| quant | file / mount | ceiling on the **surviving** image (q4_0 KV, MTP n2, `-sm layer`) | best `-ts` | decode @ depth | peak VRAM per GPU | **imbalance** |
|---|---|---|---|---|---|---|
| Q4_K_XL | `/srv/models` 17.56 GB | 196,608 (262K/229K = init-hang) | **never swept** | 30.16 | 10,996 / 14,344 | **3,348 MiB** |
| Q5_K_XL | `/srv/models` 20.88 GB | 163,840 default; **262,144 @ 54,46** | 54,46 (**first tried**) | 8.22 | 14,658 / 15,402 | 744 MiB |
| Q6_K | `/srv/bench/models` 21.98 GB | **262,144 @ 58,42** | 58,42 (54,46 crashed) | 13.85 | 15,320 / 15,080 | 240 MiB |
| Q6_K_XL | `/srv/models` 25.30 GB | 131,072 MTP / 245,760 no-spec | **only 54,46 @196,608 tried → failed** | — | — | G21 open |

Two things fall out. **Q4_K_XL's 3,348 MiB imbalance is by far the largest in the set and has never
been rebalanced — it is the highest-expected-value cell in the entire sweep** (rebalancing plausibly
buys 229,376–262,144). And G13 is now quantified: Q5 (744 MiB imbalance → 8.22 tok/s) vs Q6_K
(240 MiB → 13.85 tok/s) — **the Q5-vs-Q6 speed comparison is ratio-confounded and must not be quoted
as a model property until both are fully swept.**

Three *distinct* failure modes are visible in the artifacts and must be **classified, not lumped**:
`init-hang` (health timeout, no error), `compute-buffer OOM` (`failed to allocate compute pp buffers`
/ `failed to create MTP context` — Q6_K_XL @196,608), `crash` (backtrace through
`llama_context_can_seq_rm` — Q6_K @262,144 `54,46`).

---

## 2. Design decisions

### D1 — delete Q6_K_XL **after** its `-ts` bracket, not before  *(owner gate Q-A1; safe default = yes)*

DEC-4 approves deleting the Q6_K_XL GGUF, and the preservation rule licenses it: every finding it
*produced* is documented. But **G21 records that one of those findings is probably wrong**: only
`54,46 @196,608` was ever tried, and `58,42` is precisely the ratio that unlocked Q6_K's full
262,144 window. Its published ceiling (131,072 MTP) is therefore a likely *under-measurement* of the
highest-accuracy quant measured on this host (PPL 6.6511, HE+ 93.9/91.5, SWE-V 75.5 %). Deleting the
bytes makes that number permanently uncorrectable while it stays in PAPER-REFERENCES as fact.
The preservation rule is silent on findings *known to be wrong*; this plan reads that silence
conservatively.

**Deviation:** split Phase 1 into **1a** (IQ4_XS + NVFP4 cache + both vLLM images — frees 37.70 GB on
`/srv/models` and 59.66 GB on `/`, which unblocks everything) and **1b** (Q6_K_XL GGUF, executed at
the *end* of Wave 1 after the bracket). The `≥60 GB /srv/models` gate is therefore evaluated at
**Wave-1 exit**, not Phase-1 exit. *No approved decision is reversed — only the ordering moves.*
Cost: 3–5 probe cells ≈ 60–90 min GPU, zero new disk. If the owner declines, 1b simply runs inside
1a and nothing else in this plan changes.

### D2 — "keep the fastest that loads" needs a noise floor  *(no gate; do it)*

The existing probe derives `decode_tok_s` from a **single 64-token generation** (≈4.6 s at 13.85 tok/s)
and MTP acceptance from ~45 draft tokens. Picking "the fastest ratio" off one 64-token sample can be
noise-driven, and R2 already documents ±100–200 MiB VRAM nondeterminism. Fix, cheaply:
`n_predict = 192` on every ranking cell, and **if the top two ratios' decode medians are within 10 %,
re-run both 3× and decide on median-of-3** (tie → smaller |imbalance| → then the ratio nearer default).
Adds ~10 min per *contested comparison*, not per cell.

### D3 — pin `-ctxcp 4` for the sweep, then A/B `4` vs `32` once  *(no gate; do it)*

e11 ran `-ctxcp 4`; the candidate config line and the upstream default are `32`. Context checkpoints
are per-slot allocations, so this plausibly moves VRAM and therefore the ceilings. Sweeping at `32`
while comparing against e11's `4`-derived ceilings would mix two variables into every
"ceiling correction" claim. **Sweep at `-ctxcp 4` (baseline-comparable); then run one A/B pair at
Q6_K's winning ratio.** Δ = 0 → adopt `32` for Waves 2–4; Δ ≠ 0 → the candidate config line is wrong
and that is itself a finding. Cost: 2 cells ≈ 30 min.

### D4 — collision-proofing rather than trusting the legacy worker to stay idle *(no gate; do it)*

`worker.sh` currently logs `ALL QUEUED JOBS COMPLETE` every 300 s because every job has a `.done`
marker. That is one deleted marker away from `job_agentic_steps` seizing `llamasrv`/:8080, or
`job_score_verified50` pulling ~50 SWE-bench eval images at ~4 GB each — its own guard defers only
while `/` free < 40 GB, and **after our sweep `/` will have ~83 GB free, so the guard stops
deferring**. Defence in depth, all three: **quiesce** (watchdog *then* worker — reverse order just
gets it restarted within 120 s), **distinct container name** `llamasrv-e12`, and **take
`/srv/bench/orchestrator/gpu.lock`** so a restarted legacy worker sees `gpu_busy()` and yields.

### D5 — paths of record, reconciling two documents *(no gate; note to owner)*

The standing sync rule (owner, 2026-08-30) makes `tools/sync-multivac.sh` the contract, and it
deploys `experiments/` → `multivac:/srv/bench/e12/experiments/` and pulls into `data/bench/`.
Wave-1 text says `multivac:/srv/bench/e12/validate_v2.py` and `data/raw/e12/`. **The sync script
wins** (it is the newer directive and it is executable truth). To leave *both* documents literally
true and prevent a divergent second copy, T2 creates
`/srv/bench/e12/validate_v2.py → experiments/validate_v2.py` as a symlink. Artifacts land in
`data/bench/e12/`; `data/raw/e12/` is not created. Worth a one-line doc correction at ship.

---

## 3. Deliverables

All authored in the worktree under `experiments/`, deployed by `tools/sync-multivac.sh push`.

### 3.1 `experiments/lib_e12.py` — hardened successor to `lib_probe.py`

Same API shape so e11 callers port trivially. Changes, each tied to a defect above:

| # | change | why |
|---|---|---|
| 1 | `CONT = "llamasrv-e12"` | F-A / D4 collision |
| 2 | `launch()` emits the **full contract** — `-ngl 99 -sm layer [-ts R] -c CTX -fit off -fa on -ctk/-ctv -b 2048 -ub 512 -np 1 -ctxcp 4 --seed --host --port` + spec args — and **returns the exact command string, stored verbatim in every record** | irreproducible rows are the #1 provenance defect in this corpus (G7) |
| 3 | `preflight()` — refuse to launch unless: no `llamasrv*` container exists, nothing listening on :8080, **both** GPUs < 500 MiB used, `gpu.lock` is ours | fail loud rather than emit a confounded number |
| 4 | `vram_sampler` — 1 Hz background thread spanning prefill **and** decode, recording per-GPU **true peak** | e11 reads `nvidia-smi` *once, after* prefill returns and calls it the peak |
| 5 | `save_and_kill(label)` — `docker logs > /srv/bench/server-timings/<label>.serverlog` **before** `docker rm -f`; **asserts the serverlog exists and is non-empty**; returns byte count + `tg =` sample count | hard rule 2, enforced in code, not in prose (F-A shows prose is not enough) |
| 6 | `classify_failure(serverlog)` → `init-hang` \| `compute-buffer-oom` \| `crash` \| `props-shrink` \| `prefill-fail` \| `generate-fail` | §1.7: three distinct modes are currently lumped into "failed" |
| 7 | `record_env()` — image id + engine version string, GGUF path + sha256 + bytes (from env-manifest; **computed and appended if missing** — see F-B), seed, full sampling block, KV dtypes, spec settings, ctx requested/reported, `-ts`, `-ctxcp`, free bytes on both mounts, UTC ts | every artifact carries `source` + `run_ids` + `image_id` (swebench_agg convention) |
| 8 | `spec_live(resp)` → `timings.draft_n > 0` | §1.6.3 — `/props` lies about spec |

### 3.2 `experiments/validate_v2.py` — the Phase-2 gate

Positive run at `-c 32768` on Q4_K_XL (cheapest active to load, ≈180 s). Four contract families:

- **C1 launch contract** — `/props.n_ctx == requested` (proves `-fit off`); `total_slots == 1`;
  `-ts`/`-sm layer`/`-ctxcp` echoed in the serverlog; **flash-attn asserted ON from the serverlog**
  (`-fa auto` could resolve either way and quantized V-cache requires it); response `truncated ==
  false`; image id matches env-manifest.
- **C2 sampling contract** — send the DEC-2 non-thinking block, read back
  `generation_settings` (§1.6.1) and assert all six fields **and** assert they are *not* the
  measured server defaults `temp 1.0 / top_k 20 / top_p 0.95 / min_p 0.05 / presence 0.0` (F-D).
  Same for the thinking block.
- **C3 thinking control** — the 2-token probe (§1.6.4). Gate: `enable_thinking:false` ⇒ non-empty
  `content` **and** empty `reasoning_content`; no-control ⇒ empty `content` (proves the gate can
  actually fire). **Records, without gating, the `reasoning_effort:"none"` response body verbatim**
  including the error (F-E) — Wave 2 owns the G17 verdict.
- **C4 provenance capture** — the artifact's env block is complete and non-null, and the served
  model resolved from `/props.model_path` **and** the response `model` agrees with the requested
  GGUF and its env-manifest sha256.

**`--selftest` — the negative control (this is the acceptance criterion).** Four seeded faults;
each must be **caught**, i.e. `validate_v2` exits non-zero **and names the specific failing check**:

| fault | injection | must be caught by | expected signal |
|---|---|---|---|
| F1 ctx-shrink | launch `-fit on` with `-c 262144` on Q4_K_XL (above its 196,608 ceiling) | C1 | `/props.n_ctx` < requested |
| F2 thinking leak | omit `chat_template_kwargs` entirely | C3 | `content == ''`, `finish_reason == length` at `max_tokens 2` |
| F3 sampling-defaults leak | send the request with **no** sampling fields | C2 | read-back = `1.0 / 20 / 0.95 / 0.05 / 0.0` (the **measured** defaults, F-D) |
| F4 unprovenanced model | request whose `model` field is absent, then one that names a different GGUF | C4 | run rejected as unprovenanced |

> **F4 needs saying out loud or it will be faked.** llama.cpp ignores the request's `model` and
> serves the single loaded model, so "missing model field" **cannot** fail at the HTTP layer. The
> honest negative control is: *validate_v2 must refuse to emit an artifact whose provenance block
> cannot name the served model.* It resolves the model from `/props.model_path` + the response
> `model`, cross-checks against the env-manifest sha256, and rejects on absence or mismatch.
> A passing F4 that merely got HTTP 200 is a **failed** implementation of F4.

Cost: 5 launches × ≈180 s + probes ≈ **35–45 min**.

### 3.3 `experiments/tsweep_v2.py` (+ thin `tsweep_v2.sh` driver) — the G13 fix

- Sweeps the **full** ratio set `{default, 54,46, 56,44, 58,42, 60,40, 62,38}` at a fixed ctx.
  **Never returns early. Keeps every cell.**
- Selection: among `ok == true`, **max `decode_tok_s`**, with D2's tie-break; `imbalance_mib =
  max(peak) − min(peak)` recorded for every cell, winner or not.
- Ceiling bracketing: start one LADDER rung **above** the known ceiling; if a ratio succeeds there,
  climb until failure; if none succeed, descend until one does, then **re-test the rung above with
  the winning ratio** (R2's mandatory re-test — a rung is only "failed" after two attempts).
- Per cell: exact launch command, image id, ctx requested/reported, ok + failure `stage` +
  **classified** error, per-GPU true-peak VRAM after ≥90 % prefill, prefill tok/s, decode tok/s at
  depth (n_predict 192), MTP acceptance + mean accepted length, imbalance, serverlog path.
- **Writes incrementally after every cell and is resumable** — skips cells already present in the
  output JSON unless `--redo`. A 3 h sweep that loses everything on cell 11 is not acceptable.

### 3.4 `experiments/sweep_v2.sh` + `experiments/verify-sweep.sh` — Phase 1

Deletion order enforced **in code**: **docs → manifest → delete.**
1. `manifest`: sha256 + bytes for every delete-list item (≈61.5 GB ⇒ 10–20 min, under `nohup`),
   appended to `/srv/bench/env-manifest.json` as a `deleted_items[]` array carrying deletion
   timestamp, the findings-citation per item, and the re-download coordinates.
   **Two provenance repairs in the same pass:** add the missing `UD-Q6_K.gguf` sha256 (F-B), and
   record `docker image inspect --format '{{index .RepoDigests 0}}'` for both vLLM images —
   **without the RepoDigest, "re-pull" is not byte-exact.**
2. `docs`: ledger entry + PAPER-NOTES entries + lifecycle Status/roadmap update are **committed
   before any `rm` / `docker rmi`**.
3. `delete`: the 1a set now; 1b at wave exit (D1).
4. `verify-sweep.sh` asserts, non-zero on any failure: free **bytes** on both mounts vs the gate
   (§Q-A2); every KEEP item still present (full sha256 on the three active GGUFs ≈ 7 min, size+mtime
   on the rest); `deleted_items[]` covers every deleted item; the six telemetry containers still Up;
   `orchestrator/state/*.done` intact.

### 3.5 `experiments/quiesce_legacy.sh` (+ `restore_legacy.sh`)

Stop `watchdog.sh` **then** `worker.sh`; record both pids and the exact restart command into the
artifact and the ledger; leave `state/*.done` untouched. **Default: stays quiesced through Waves 2–4**
(they need the GPU exclusively too); restore is a ship-checklist step.

---

## 4. Task breakdown

| id | task | GPU | est | depends on |
|---|---|---|---|---|
| **T1** | Quiesce legacy orchestrator (D4); preflight snapshot (disk bytes, GPU, images, container/port); create `/srv/bench/e12/`; `sync-multivac.sh push` | no | 30 min | — |
| **T2** | `lib_e12.py` + `validate_v2.py`; positive run; **`--selftest` catches F1–F4**; symlink (D5) | light | 3 h | T1 |
| **T3a** | Phase 1a sweep: docs → manifest (incl. F-B repairs + RepoDigests) → delete IQ4_XS, NVFP4 cache, both vLLM images; `verify-sweep.sh` | no | 2 h | T1, T2 gate green |
| **T4** | `tsweep_v2` for the three actives (§5) + D3 `-ctxcp` A/B | **yes** | 6–9 h | T2, T3a |
| **T5** | G21 bracket for Q6_K_XL (D1, gate Q-A1) | **yes** | 1–1.5 h | T4 |
| **T3b** | Delete Q6_K_XL; final `verify-sweep.sh`; the `≥60 GB` gate is evaluated **here** | no | 30 min | T5 |
| **T6** | `sync-multivac.sh both`; ledger `L-3`; PAPER-NOTES `PN-1…`; lifecycle Status + roadmap; findings register | no | 1 h | all |

**Ordering note.** T2 before T3a is deliberate — "small tests before big tests" means the cheapest
thing that can detect a broken environment runs first, and validate_v2 is that thing. T3a's sha256
pass *could* overlap T2, but both are I/O-heavy against the same spindles and T2's model loads would
be slowed and its load-time numbers polluted; **default is strict serialization**, and any implementer
choosing otherwise must record the choice.

---

## 5. The `-ts` sweep matrix (T4)

| quant | ctx | ratios | goal | note |
|---|---|---|---|---|
| **Q4_K_XL** | **212,992** (one rung above 196,608), then climb 229,376 → 245,760 → 262,144 while a ratio succeeds | all 6 | ceiling **and** speed | **highest expected value in the wave** — 3,348 MiB imbalance, never rebalanced |
| **Q5_K_XL** | 262,144 (already the native max — nothing above it) | all 6 | **speed only** — de-confound G13 | 54,46 was the *first* ratio tried; 744 MiB residual imbalance |
| **Q6_K** | 262,144 | all 6 | **speed only** — confirm 58,42 is the best, not merely the first success | + D3 `-ctxcp` 4-vs-32 A/B at the winner |
| **Q6_K_XL** (T5) | 196,608, then bracket down 180,224 → 163,840 → 147,456 | 58,42 · 62,38 · 60,40 first (54,46 is already known-failed) | close **G21** | skip `default` — 131,072 is the known default-split ceiling |

All cells: `-sm layer`, `-ctk/-ctv q4_0`, `--spec-type draft-mtp --spec-draft-n-max 2`, `-fit off`,
`-fa on`, `-np 1`, `-ctxcp 4` (D3), `--seed 20260830`, prefill ≥ 90 % of window, `n_predict 192` (D2).

**Cost model from measured e11 timings** — load 181–306 s at depth (≈180 s at 32 K); prefill 248,522
tok @ ≈502 tok/s = **8.3 min**; decode 192 tok @ 8–14 tok/s = 15–25 s ⇒ **successful deep cell
14–16 min**, failed cell 5–10 min (600 s health limit). 6 ratios × 3 quants + climb/bracket +
D2 re-runs + D3 A/B ≈ **26–34 cells ≈ 6–9 h**; T5 ≈ 5 cells ≈ 1–1.5 h.

---

## 6. Acceptance criteria

Wave 1 is done when **all** of these hold. Each is a command, not a judgement.

**A1 — harness gate.** `validate_v2.py --selftest` exits non-zero on each of F1–F4 **and names the
specific failing check**; the positive run exits 0 with all of C1–C4 green;
`data/bench/e12/validate-v2-selftest.json` shows `caught: true` for all four, with the F4 rejection
reason being *unprovenanced model*, not an HTTP status.

**A2 — no log was ever lost.** For every container this wave created, a non-empty
`/srv/bench/server-timings/<label>.serverlog` exists whose mtime **precedes** the container's
removal; `save_and_kill` recorded the byte count in the artifact. Count of labels ≥ count of cells.

**A3 — disk gate** (evaluated at T3b): `/srv/models` available **≥ 60 × 10⁹ B** and `/` available
**≥ 55 × 10⁹ B**, recorded as exact byte counts (plus the GiB figure) in `sweep-v2.json`.
`verify-sweep.sh` exits 0: every KEEP item present with matching sha256/size, `deleted_items[]`
complete with sha256 + bytes + RepoDigests, telemetry Up, `state/*.done` intact.

**A4 — provenance repaired.** `env-manifest.json` contains a sha256 + bytes entry for
`/srv/bench/models/Qwen3.8-27B-UD-Q6_K.gguf` (F-B) and a RepoDigest for each deleted vLLM image.

**A5 — G13 closed.** For each of the three actives, `tsweep-v2-<quant>.json` contains **all six**
ratio cells (no early return), a `best` chosen by max decode with the D2 rule applied, and an
`imbalance_mib` on every cell. Explicit statement of whether the historical Q5-vs-Q6 speed gap
survives ratio-matching.

**A6 — ceilings bracketed and re-tested.** Every reported ceiling has a *failed* rung above it that
was attempted **twice** (R2), each failure carrying a classified mode, not a bare "failed".

**A7 — G21 closed or explicitly declined.** Either `tsweep-v2-Q6_K_XL.json` with a bracketed
rebalanced ceiling, or a ledger line recording the owner's decline under Q-A1 — **and in the decline
case a PAPER-NOTES caveat that the published 131,072 MTP ceiling is an un-rebalanced lower bound**.

**A8 — D3 answered.** A `-ctxcp` 4-vs-32 A/B pair at Q6_K's winning ratio, with the candidate config
line either confirmed or corrected.

**A9 — narrative + sync.** `sync-multivac.sh both` run at stage end with its result in the ledger's
Verified field; ledger `L-3` appended (marker verbatim); ≥1 PAPER-NOTES entry per §11; lifecycle
Status block + roadmap Status column updated; findings register rows for anything raised.

---

## 7. Exact verification

```bash
# --- T1 ---
ssh multivac 'pgrep -af "watchdog.sh|worker.sh"'                 # expect EMPTY after quiesce
ssh multivac 'ls /srv/bench/orchestrator/state/*.done | wc -l'   # unchanged (6)
ssh multivac 'df -B1 /srv/models / ; nvidia-smi --query-gpu=index,memory.used --format=csv,noheader'

# --- T2 (gate) ---
ssh multivac 'cd /srv/bench/e12 && python3 experiments/validate_v2.py            --out /srv/bench/e12/validate-v2.json'          ; echo "positive rc=$?"   # 0
ssh multivac 'cd /srv/bench/e12 && python3 experiments/validate_v2.py --selftest --out /srv/bench/e12/validate-v2-selftest.json'; echo "selftest rc=$?"   # 0 iff all 4 caught
ssh multivac 'python3 -c "import json;d=json.load(open(\"/srv/bench/e12/validate-v2-selftest.json\"));print([(f[\"id\"],f[\"caught\"],f[\"caught_by\"]) for f in d[\"faults\"]])"'
#   expect [("F1",True,"C1"),("F2",True,"C3"),("F3",True,"C2"),("F4",True,"C4")]

# --- T3a / T3b ---
ssh multivac 'bash /srv/bench/e12/experiments/verify-sweep.sh'; echo "sweep rc=$?"   # 0
ssh multivac 'df -B1 /srv/models / | cat'                        # >=60e9 and >=55e9 available
ssh multivac 'docker images | grep -c vllm'                      # 0
ssh multivac 'ls /srv/engines/nvfp4 >/dev/null && echo KEEP-OK'  # KEEP-OK  (DEC-4)
ssh multivac 'python3 -c "import json;d=json.load(open(\"/srv/bench/env-manifest.json\"));print(len(d.get(\"deleted_items\",[])), any(\"UD-Q6_K.gguf\" in g[\"file\"] for g in d[\"gguf_models\"]))"'  # 5 True

# --- T4 / T5 ---
ssh multivac 'for q in Q4_K_XL Q5_K_XL Q6_K Q6_K_XL; do python3 - <<PY
import json,glob
for f in glob.glob("/srv/bench/e12/tsweep-v2-$q*.json"):
    d=json.load(open(f)); t=d["trials"]
    print("$q", "cells=",len(t), "ok=",sum(1 for x in t if x["ok"]),
          "best=",(d.get("best") or {}).get("ts"), (d.get("best") or {}).get("ctx"),
          "modes=",sorted({x.get("failure_mode") for x in t if not x["ok"]}))
PY
done'                                                            # cells>=6 per quant; modes classified
ssh multivac 'ls -la /srv/bench/server-timings/ | wc -l'         # grew by >= number of cells
ssh multivac 'find /srv/bench/server-timings -name "e12-*.serverlog" -size -1c | wc -l'   # 0 empty logs

# --- T6 ---
bash tools/sync-multivac.sh both
ls data/bench/e12/ && git -C . status --short
```

---

## 8. Owner gates

| id | question | recommendation | blocks? |
|---|---|---|---|
| **Q-A1** | Run the Q6_K_XL `-ts` bracket (3–5 cells, 60–90 min) before deleting it, closing G21? | **Yes.** It is cheap and it protects a published number for the highest-accuracy quant from becoming permanently uncorrectable. | **No** — Wave 1 starts either way; only the position of step 1b moves. |
| **Q-A2** | If `/srv/models` lands at 59.8 GiB (F-C — passes in GB, misses 60 GiB by 204 MB), accept the decimal-GB reading, or authorize one more deletion? | **Accept the byte-explicit decimal gate (≥60×10⁹ B, measured 64.2×10⁹).** The only untapped levers are `.hf-cache/hub` (3.88 GB) and `models--z-lab--DFlash2` (3.85 GB) — neither is approved, and DFlash2 is in scope for Wave 2. | **No** — answer needed only at T3b. |
| **Q-A3** | Leave the legacy orchestrator quiesced through Waves 2–4 (restore at ship), or restore after Wave 1? | **Leave quiesced.** Waves 2–3 need the GPU exclusively; all its queued jobs are `.done`. | **No** — default is quiesced. |

---

## 9. Risks

| id | risk | likelihood | mitigation | residual |
|---|---|---|---|---|
| **RA-1** | Legacy worker seizes `llamasrv`/:8080 mid-sweep, or its `kill_server llamasrv ""` destroys a container's logs unsaved (F-A) | med → low after T1 | D4 triple defence: quiesce, `llamasrv-e12`, `gpu.lock`; `preflight()` refuses to launch into a dirty host | a manual `docker run` by another operator; `preflight()` catches it at the next cell |
| **RA-2** | Marginal-rung VRAM nondeterminism produces a false ceiling (R2) | **high** — Q6_K peaked at 15,320/15,650 MiB, **330 MiB of headroom, inside the noise band** | bracket + mandatory re-test of the rung above; true-peak 1 Hz sampler; failure-mode classification | ceilings are honest *for this image*; a re-test-passing rung is reported with both attempts |
| **RA-3** | Speed ranking driven by measurement noise rather than by `-ts` | med | D2: n_predict 192, 10 % → median-of-3, imbalance tie-break | ratios genuinely within noise are reported as **tied**, not ranked |
| **RA-4** | Wave exceeds the conductor's 2 h wall / 30 min idle worker timeout | **high** — 8–11 h of GPU work | **mandatory**: `nohup setsid bash runner.sh &` + pid file + per-cell state files (host has no `tmux`); the agent polls and re-attaches; every script is resumable (§3.3) | a host reboot loses in-flight cells only |
| **RA-5** | Deletion is irreversible and something needed later is gone | low | manifest-before-delete with sha256 + bytes + **RepoDigests**; 1a/1b split; KEEP list restated in §1.3; `verify-sweep.sh` re-checks every KEEP item | Track B E9 still needs a 22 GB re-download + image re-pull — already accepted in DEC-4 |
| **RA-6** | `/` refills silently after the sweep (`job_score_verified50`'s 40 GB guard stops deferring at ~83 GB free) | med if worker restarts | T1 quiesce + `state/*.done` on the KEEP list + `verify-sweep.sh` free-space re-check at T6 | — |
| **RA-7** | `-ctxcp` 4 → 32 shifts VRAM and silently invalidates ceiling comparisons | med | D3: sweep at 4, A/B once, adopt deliberately | if Δ ≠ 0, Waves 2–4 must re-derive their ceilings — flagged in the handoff |
| **RA-8** | `-fa auto` resolves differently from e11 and moves VRAM | low (`-ctv q4_0` requires FA, so e11 must already have had it on) | C1 asserts FA state from the serverlog; any change is recorded as a confounder | — |
| **RA-9** | Q4_K_XL's 262K/229K "init-hang" is a fixed engine limit, not a VRAM one → rebalancing buys nothing | med | the classifier distinguishes `init-hang` from `compute-buffer-oom`; a null result is still a publishable systems finding | outcome recorded either way |
| **RA-10** | 14 GiB RAM + 3 GiB swap already used; concurrent sha256 of 61 GB and a 25 GB mmap thrash page cache | low-med | strict serialization (§4); sha256 under `nohup`, one file at a time | slower, not wrong |

---

## 10. Rollback

**Code/docs** — everything is a new file under `experiments/` plus append-only edits to the lifecycle
file and PAPER-NOTES. `git revert` of the wave commit restores the repo exactly; nothing on the host
is overwritten (e11 is untouched — v2 files are new names in a new directory).

**Host state** — `restore_legacy.sh` restarts the watchdog (which restarts the worker within 120 s),
using the pids/command recorded in T1. `gpu.lock` is removed on every exit path, including failure.

**Deletions** — genuinely irreversible; that is why the order is *docs → manifest → delete* and why
1b is deferred. Recovery path, recorded in `deleted_items[]`:

| item | recovery | cost |
|---|---|---|
| IQ4_XS GGUF | `hf download unsloth/Qwen3.8-27B-GGUF <file>` → verify sha256 `40fac405…` | 14.25 GB |
| Q6_K_XL GGUF | same → verify `701d8fa9…` | 25.30 GB |
| NVFP4 hf-cache | duplicate of `/srv/engines/nvfp4`, which is **KEPT** — recovery is a local copy | 0 |
| vllm images | `docker pull vllm/vllm-openai@<RepoDigest>` (byte-exact only because T3a records the digest) | 59.7 GB |

**Point of no return:** the first `rm` in T3a. Everything before it is reversible; A3's byte-exact
manifest is the safety net after it.

---

## 11. Expected PAPER-NOTES entries (§ per protocol)

- **§Systems findings** — `-ts` rebalance deltas per quant, with imbalance MiB; the G13 de-confound
  verdict on Q5-vs-Q6; the three distinct failure modes as an engineering finding; **F-D**: the
  measured sampling defaults on `llamacpp-mtp:latest` differ from the upstream-documented set
  (a silent-misconfiguration hazard, and a correction owed to the lifecycle file's R1).
- **§Context axis** — corrected/confirmed ceilings per quant with the bracket + re-test evidence;
  the G21 result for Q6_K_XL (or the explicit lower-bound caveat).
- **§Speculative decoding** — MTP acceptance at depth per ratio; **`/props` misreports
  `speculative.types: none` while spec is live — use `timings.draft_n`** (a reproducibility trap).
- **§Reproducibility & provenance** — the champion quant `UD-Q6_K` was unpinned in `env-manifest`
  until this wave; RepoDigest-vs-image-id as the requirement for byte-exact image recovery.
- **§Sampling & protocol** — the 2-token thinking probe as a ~1 s discriminator;
  `reasoning_effort:"none"` failing on this template while `enable_thinking:false` works (G17
  signal, Wave 2 owns the verdict).

Every entry carries n, conditions (quant, ctx, KV, spec, ratio, `-ctxcp`), the artifact path under
`data/bench/e12/`, and the image id — `feb0231976b6…` is **not** the image that produced the
historical 262K/tensor-split corpus (G7), and that caveat must travel with every comparison.

---

## 12. Out of scope → new tasks, not edits in this wave

`-ctkd`/`-ctvd` draft-KV sweep (Wave 2 — legality confirmed §1.5) · G17 equivalence verdict (Wave 2) ·
G8 losslessness at temp > 0 (Wave 2) · `--cache-reuse` and ubatch sweeps (Wave 2, smoke first) ·
speed-vs-filled-context curve G14 (Wave 4) · moving `UD-Q6_K.gguf` from `/` to `/srv/models` to
rebalance the two volumes (a real headroom win of ~22 GB on the tighter disk, but it changes the
container mount path recorded in existing provenance — **file it, do not do it here**) ·
the G18 untested quants · any deletion not on the DEC-4 list.

---

## 13. Handoff to the Wave-1 implementer

1. Read §1 before writing code — it is measured, and it contradicts the lifecycle file in two places
   (F-B, F-D).
2. `experiments/` is new; `/srv/bench/e11/` is the reference implementation. **Port, don't reinvent** —
   `ctx_ceiling.probe()`'s behavioural gate is correct and hard-won; keep it and add §3.1's items.
3. The only things that gate the wave are A1–A9. Everything else is engineering judgement.
4. Nothing gets deleted until the ledger entry, the PAPER-NOTES entries, and the manifest are
   **committed**. That order is not advisory.
5. Run detached (`nohup`, no `tmux` on the host) or the conductor will kill the sweep at 2 h.
6. `bash tools/sync-multivac.sh both` at stage end; put its result in the ledger's `Verified:` line.
