# PROVENANCE — the reproducibility record

**Everything needed to say exactly what produced each number in this study.**
Compiled 2026-09-02 from `data/raw/e12/env-manifest.json`, the `env` block embedded in every
Wave-1 artifact, the `launch_cmd` recorded per cell, and the machine records at
`data/multivac-src/`. Cross-checked against the live host.

Companion: [`METRIC-CORPUS.md`](METRIC-CORPUS.md) (what was measured) ·
[`TIMELINE.md`](TIMELINE.md) (when and why) · [`references.bib`](references.bib) (external sources).

> **The one-sentence version.** Every E12 number came from a single container image,
> `sha256:feb0231976b65b548772845652833a370f78890d94f485a1392e25fdb5944b62`, except the DFlash2 arm
> which came from `sha256:22bb8b7fed8b3cfc8edb28ab5c4e1db0575670b35619da19693830a8d2952354`; every
> pre-2026-08-29 number came from an image that **no longer exists**.

---

## 1. Host

| component | specification |
|---|---|
| GPUs | **2 × NVIDIA RTX 5060 Ti 16 GB** (Blackwell, **sm120**), power limit **180 W each** |
| GPU interconnect | **none** — no NVLink. The cards are not a memory pool (see §6) |
| Usable VRAM | **15,650 MiB/GPU** practical ceiling; **16,311 MiB** card total |
| CPU | AMD Ryzen 5 8500G, 12 threads |
| **System RAM** | **14 GiB** — load-bearing: it is why KL divergence cannot be measured beyond n_ctx 8,192 (PN-31) |
| Driver / CUDA | NVIDIA 595.84, CUDA 13.2 |
| OS | Ubuntu, headless, x86_64. Hostname `multivac` |
| Power instrumentation | **no BMC/IPMI** → wall power is not measurable. GPU energy integrated from 1 Hz `nvidia-smi`; CPU from kernel RAPL powercap; the system total is **modelled**, not measured |
| Storage | `/` (`/dev/sdb2`) and a **separate 110 GB `/srv/models` disk (`/dev/sda`)**. New GGUFs go to `/srv/bench/models/`, mounted into containers as `/models2` |

Recorded in `data/raw/e12/env-manifest.json` → `gpu_hardware`.

---

## 2. Container images — the pins every number hangs on

| role | tag | image id | created | version string |
|---|---|---|---|---|
| **primary engine** — every E12 measurement except the DFlash2 arm | `llamacpp-mtp:latest` | `sha256:feb0231976b65b548772845652833a370f78890d94f485a1392e25fdb5944b62` | 2026-08-25T22:35:04Z | `version: 0.3.0-dev (build 1, commit d222767); built with GNU 13.3.0 for Linux x86_64` |
| **DFlash2 engine** — S9c only | `llama-dflash2:latest` | `sha256:22bb8b7fed8b3cfc8edb28ab5c4e1db0575670b35619da19693830a8d2952354` | 2026-08-25T11:12:54Z | `version: 0.1.2-dev (build 50, commit f7aadef); built with GNU 13.3.0 for Linux x86_64` |
| ⚠ **DELETED** — produced **every** tensor-split result and **every** 262,144-token result in the pre-E12 corpus | `llamacpp-dflash2-pr27342:1deefcc-sm120-cuda128-abi` | **gone from disk; no digest recorded before deletion** | — | — |
| deleted 2026-08-29 (DEC-4), re-pullable by digest | `vllm/vllm-openai:nightly` | `sha256:22d3b1217fda569653f32f1e00a2a4e64119c1601c67ff94cc72d7ca5ef352c8` | — | `0.26.1rc1.dev1219+g46638857f` |
| deleted 2026-08-29 (DEC-4), re-pullable by digest | `vllm/vllm-openai:v0.27.1` | `sha256:0a51ea5b4ae2dc5d81890e5173f54203d2a3ae0cfffe51b8fd2afd4391bfd967` | — | `0.27.1` |
| pre-E12 split-mode matrix only (2026-08-20) | `llamacpp-nccl231:latest` | not recorded | — | — |

**Every artifact carries its own image id** and asserts `matches_manifest: true` against the
manifest, so a cell's engine is checkable without trusting this table.

> **The irreproducibility that shaped the whole study.** The deleted
> `llamacpp-dflash2-pr27342` image is the *only* image on which `-sm tensor` ever worked on this
> host, and it produced every 262,144-token and every tensor-split figure in the historical corpus.
> Its digest was **not** recorded before deletion, so it cannot be re-pulled. This is why
> `env-manifest.json` now records **sha256 + bytes + RepoDigest** for every deletable item, and why
> `data/archive/README.md` carries a standing `IRREPRODUCIBLE-ON-CURRENT-IMAGES` warning.

**Reproducible split modes (E6, both surviving images):** `-sm layer` ✓ · `-sm tensor` ✗ (CUDA
illegal memory access) · `-sm row` ✗ (device does not support split buffers).
**`-sm layer` is the only reproducible split mode on this host.**

`llama-dflash2:latest` requires **`--entrypoint /app/llama-server`** — its default entrypoint is a
wrapper that rejects `--host` and dies in ~19 s.

---

## 3. Model files — sha256 and exact byte counts

All from `unsloth/Qwen3.8-27B-GGUF` on Hugging Face (verified to exist 2026-09-02: repo created
2026-08-13T08:28:40Z). Digests and sizes from `data/raw/e12/env-manifest.json` → `gguf_models`,
re-asserted in every Wave-1 artifact's `env.model` block.

| arm | path on host | bytes | sha256 |
|---|---|---|---|
| **UD-Q4_K_XL** | `/srv/models/Qwen3.8-27B-UD-Q4_K_XL.gguf` | **17,559,178,144** | `3f227079003add2511437e5b1e94812e363385225bf6a9b47b0054a72bc8b01e` |
| **UD-Q5_K_XL** | `/srv/models/Qwen3.8-27B-UD-Q5_K_XL.gguf` | **20,876,938,144** | `8601193d3d5760c37fb8ce1b43afebc69df5fb24e1fbc5a547c32e2200305276` |
| **UD-Q6_K** | `/srv/bench/models/Qwen3.8-27B-UD-Q6_K.gguf` | **21,983,677,344** | `c9c206812fbe4ac7b76a729e25928b63f2ae89d37f69da7a71c20aec763cd436` |
| **UD-Q6_K_XL** *(reference arm)* | `/srv/models/Qwen3.8-27B-UD-Q6_K_XL.gguf` | **25,299,061,664** | `701d8fa9ed214ab21bfc130cd2a7df19ca89bbef7713e2dfb19f3c63696aa917` |
| DFlash2 drafter | `/srv/models/dflash2/Qwen3.8-27B-DFlash2-Q4_K_M.gguf` | **1,143,006,752** | `18a380efc9b7ed8d88677fc895f5c11ae170653434ee378f7348f715c14d0594` |
| UD-IQ4_XS *(deleted 2026-08-29)* | `/srv/models/Qwen3.8-27B-UD-IQ4_XS.gguf` | 14,252,845,984 | `40fac4050e940397dbf13087afd50f4734a11805bf9d65ef8ddd7483470e6199` |

Note `UD-Q6_K` lives on `/srv/bench/models` (mounted `/models2`), the others on `/srv/models`
(mounted `/models`) — visible in every `launch_cmd`.

**All four active GGUFs carry the MTP head** — verifiable with
`head -c 60000000 <gguf> | strings -n 6 | grep nextn`, which finds
`qwen35.nextn_predict_layers` and `blk.64.nextn.{eh_proj,enorm,hnorm,shared_head_norm}.weight`.
There was never a separate "embedded-MTP" build.

**GGUFs gone and not re-obtainable cheaply:** `Q3_K_XL` and `Q4_K_M` (16,464,440,224 B, size
recovered from `/srv/models/download.log`). Rows using them are irreproducible without re-download.

### The model itself

`Qwen/Qwen3.8-27B` — verified live 2026-09-02: created 2026-08-05, Apache-2.0, architecture
`qwen3_5`, **pipeline tag `image-text-to-text`**, 18 safetensors shards, native context **262,144**
(≈1 M via YaRN, untested here).

> ⚠ **The model is a vision-language model. Every measurement in this study is text-only.** The
> paper must state this; a reader will otherwise assume the vision path was exercised.

> ⚠ **There is no arXiv paper for Qwen3.8.** The official citation is a blog post
> (`@misc{qwen38}`). arXiv 2505.09388 is the *Qwen3* technical report — an earlier generation —
> and does not describe this model.

**Available but unused:** the same GGUF repo ships a **BF16** (2 shards) and a separate
`MTP/mtp-Qwen3.8-27B-Q4_0.gguf` drafter. So G20's "no BF16 reference exists" is a statement about
*this host's* 14 GiB RAM and 2×16 GB VRAM, not about availability. Divergence is ladder-relative
because BF16 **will not fit**, not because it could not be obtained.

---

## 4. Seeds, sampling and the launch contract

### Seeds

| seed | used for |
|---|---|
| **20260830** | every E12 run — server `--seed`, `llama-perplexity -s`, HellaSwag task selection (which is what makes S7 **paired**), generation seeds |
| 20260831 | recorded in some Wave-1 cell bodies as the per-cell generation seed |
| 20260829 | pre-E12 (E11) runs |
| 20260825 | pre-E12 bootstrap CIs (B = 10,000) |

### Sampling — three regimes, never mixed

| regime | settings | used by |
|---|---|---|
| **DEC-2 official non-thinking** | temp **0.7** · top_p **0.80** · top_k **20** · min_p **0.0** · presence_penalty **1.5** · repeat_penalty **1.0** | Wave 1 (all ceilings and speed), SSA S6, S9d, S9e |
| **greedy** | temperature **0** · top_p **1** (S12: top_k 1) | S8, S9a, S9c, S11, S12; and every logprob instrument (KLD/PPL) where sampling does not apply |
| DEC-2 official thinking *(never used in a measurement)* | temp 1.0 · top_p 0.95 · top_k 20 · min_p 0.0 · presence 0.0 · repeat 1.0 | — |

> ⚠ **The engine's own defaults are a fourth, undocumented configuration** (PN-1): measured
> temp **1.0** / top_k **20** / top_p **0.95** / min_p **0.05** / presence **0.0**. This matches
> neither the upstream llama.cpp documented launch defaults (0.80 / 40 / 0.95 / 0.05) nor either
> official preset. **Always send an explicit per-request sampling block**, and assert the readback:
> `/completion` echoes the effective sampling in `generation_settings`. Note f32 storage rounding —
> 0.7 reads back as 0.699999988079071, so any check needs a 1e-3 tolerance.

> ⚠ **Thinking is ON by default.** `/no_think` does not work on this template.
> `chat_template_kwargs {"enable_thinking": false}` works.
> `chat_template_kwargs {"reasoning_effort": "none"}` raises a Jinja exception:
> *"Unexpected reasoning effort none. Supported types are xhigh (default), medium, and low."*

### The launch pattern (Wave 1 / S9d / S9e / S12), verbatim from `launch_cmd`

```bash
docker run -d --name llamasrv-e12 --gpus all --network host \
  -v /srv/models:/models:ro -v /srv/bench/models:/models2:ro \
  llamacpp-mtp:latest \
  -m /models/Qwen3.8-27B-UD-<QUANT>.gguf \
  -ngl 99 -sm layer -ts <RATIO> -c <CTX> \
  -fit off -fa on \
  -ctk q4_0 -ctv q4_0 \
  -b 2048 -ub 512 -np 1 -ctxcp <4|32> \
  --seed 20260830 \
  --spec-type draft-mtp --spec-draft-n-max <N> \
  --host 0.0.0.0 --port 8080
```

The DFlash2 arm (S9c) differs in four places:

```bash
docker run -d --name llamasrv-e12 --gpus all --network host \
  -v /srv/models:/models:ro -v /srv/bench/models:/models2:ro \
  --entrypoint /app/llama-server \
  llama-dflash2:latest \
  -m /models2/Qwen3.8-27B-UD-Q6_K.gguf ... \
  --spec-type draft-dflash --spec-draft-n-max 4 \
  -md /models/dflash2/Qwen3.8-27B-DFlash2-Q4_K_M.gguf
```

The divergence instrument (SSA) runs a different entrypoint in the same image:

```bash
docker run --rm --name ssa-perplexity --gpus all --network host \
  -v /srv/models:/models:ro -v /srv/bench/models:/models2:ro \
  -v /srv/bench/corpus:/corpus:ro -v /srv/bench/e12:/e12:ro -v /srv/bench/e12/ssa:/ssa \
  --entrypoint /app/llama-perplexity llamacpp-mtp:latest \
  -m /models/Qwen3.8-27B-UD-<QUANT>.gguf -f /corpus/<CORPUS> \
  -c 2048 --chunks <32|9> -ngl 99 -fa on -ctk q4_0 -ctv q4_0 -s 20260830 \
  --kl-divergence --kl-divergence-base /ssa/base-<domain>.kld
```

### Flags that must not be varied silently

| flag | why |
|---|---|
| **`-fit off`** | the default `-fit on` cannot be trusted to bound allocation. Launch every measurement with it off **and assert `/props n_ctx` == requested** (PN-4) |
| **`-fa on`** | required for a quantized V cache; `-ctv q4_0` loading at all is the behavioural evidence |
| **`-np 1`** | single slot, so `/props` `total_slots` is 1 and timings are not shared |
| **`-ts <ratio>`** | **part of the configuration, not a tuning detail.** Not portable, not monotone-safe. Re-sweep on any change of quant, KV dtype or spec setting |
| **`-ctxcp 32`** | +6.8 % decode, +7.6 % prefill at identical VRAM (PN-18, directional) |
| `-ctk/-ctv q4_0` | the only viable quantized KV dtype. **`q8_0` is broken on this stack** (three independent failures) |

### The per-configuration `-ts` optima

| arm | winning ratio | at |
|---|---|---|
| UD-Q4_K_XL | `56,44` (default also loads at 262,144) | 262,144 |
| UD-Q5_K_XL | `54,46` | 262,144 |
| UD-Q6_K | `58,42` | 262,144 |
| UD-Q6_K_XL | `56,44` | 212,992 |

S12 (RULER) deliberately used **one fixed `-ts 56,44` for both arms**, because a per-arm ratio
would be an uncontrolled variable in an accuracy comparison. S11 did the same.

---

## 5. Corpora and external data

| file | bytes | sha256 / note |
|---|---|---|
| `/srv/bench/e12/corpus.txt` (django code, D2 + all pads) | 9,097,163 | host only |
| `/srv/bench/corpus/wikitext2-test.txt` (D1) | 1,256,449 | host only |
| `/srv/bench/corpus/humanevalplus-prompts.txt` (D3, S5) | 74,220 chars, 164 prompts | built from the local EvalPlus set, prompts only, stable task-id order |
| `hellaswag_val_full.txt` | 7,770,677 | `d572539320eb2050e858ca34b495bbe2103e3b3f1391a9c3bcdf215b0bb93bd1` — from `raw.githubusercontent.com/klosax/hellaswag_text_data`, fetched 2026-08-30T12:40:21Z, HTTP 200, 60,252 lines |
| `winogrande-debiased-eval.csv` | 155,325 | `6726173ef65ffdc4abb0d28b755375d288ffb3eb41633bd833288c411c8ebf7c` — fetched 2026-08-30T12:40:22Z, **never run** |
| RULER task data | generated on-host by RULER's own `scripts/data/synthetic/niah.py` | `/srv/bench/e12/ruler/data/` |

Recorded in `data/raw/e12/s7-data-provenance.json`, which states the rule plainly: *"third-party
corpora, not produced by this project: cite by URL + sha256, and treat any score against them as
comparable only to other runs on the SAME sha256."*

**Pads** (the depth instrument) are tokenized with `Qwen3.8-27B-UD-Q4_K_XL.gguf` on the pinned
image; rule `target = int(ctx*0.95) − 512`, valid iff `|actual − target| ≤ max(64, 0.005·target)`
**and** `actual/ctx ≥ 0.90`. Nine pads, all within tolerance at ~0.945 — `pads-manifest.json`,
`all_ok: true`.

---

## 6. Two facts about this hardware that shape every result

**The two GPUs are not a memory pool.** With `-sm layer` each layer's weights **and its slice of
the KV cache** live on one card, and there is no NVLink on the 5060 Ti. The binding limit is
therefore **per-card 16,311 MiB**, never the 32,622 MiB aggregate: a run OOMs when the *heavier*
card fills while the other still holds room that is physically unreachable. This is why `-ts` moves
the ceiling at all, and why the ceiling is a property of the split (PN-6).

**Decode at a full window is 3–5× slower than decode into an empty one.** Measured on the same
server with the same flags: **37.22 tok/s at depth 0 → 7.19 tok/s at depth 186,265** (−81 %). Every
E12 speed row is measured after a real prefill to ≥0.90 of the window. Published `ctx=32768` speed
tables are depth-0 and are **not** long-context throughput.

---

## 7. What ships in the public repository, and what does not

| evidence | in repo | note |
|---|---|---|
| paper notes, decision log, ledger, plans | ✅ | `docs/` |
| E12 result artifacts (JSON), harness source, quarantine, logs | ✅ | `data/raw/e12/` — 173 files |
| pre-E12 archive | ✅ | `data/archive/` |
| machine records (mirrors) | ✅ | `data/multivac-src/` |
| **raw `docker logs` (`/srv/bench/server-timings/*.serverlog`)** | ❌ | **gitignored by design.** The provenance chain is *paper note → artifact → serverlog*, and the last link does not ship |
| **`/srv/bench/power-log.csv`** | ❌ | **all energy and thermal numbers (PN-11, PN-12) rest on it** |
| `*.kld` reference-logit files (~16 GB each) | ❌ | deleted after extraction; 50 GB reclaimed 2026-08-30 |
| generated pads, corpora, GGUFs, container images | ❌ | excluded by `.gitignore`; provenance in `env-manifest.json` |

**Known gaps between the repo and the host, as of 2026-09-02** — each is a file the paper cites and
the public repo does not contain:

| missing from repo | consequence |
|---|---|
| `ruler/s12-ruler.json` is **stale** (pre-MK-NIAH, pre-dedup) | **the long-context headline (PN-33/PN-34) has no evidence in the released artifacts** |
| `ruler/s12-preds-{Q6_K_XL,Q4_K_XL}-mkniah-c131072.json` | the MK-NIAH predictions |
| `s8/s8-scores-reparsed.json` | the repo publishes only the **broken** scorer output |
| `s11-pads-manifest.json`, `state/progress.json`, `quarantine/s11-gen-c8192.json` | minor; the quarantine register is incomplete |

Fix before publication: `tools/sync-multivac.sh artifact /srv/bench/e12/<path> data/raw/e12/<path>`.
Details in `METRIC-CORPUS.md` ⚑F-1 and ⚑F-4.

---

## 8. Figure-generation tooling — a reproducibility caveat for readers

This report's figures are to be produced with **PaperBanana** (`zhu2026paperbanana`), via the
community open implementation (`paperbanana_impl`, MIT — which states it is **not affiliated** with
the original authors).

> ⚠ **PaperBanana cannot run on the benchmark host, and cannot run offline at all.** Verified
> 2026-09-02: it requires a cloud VLM *and* image-generation provider — `OPENAI_API_KEY`
> (`gpt-5.2` + `gpt-image-1.5`, the default), `GOOGLE_API_KEY` (`gemini-2.5-flash` +
> `gemini-3-pro-image-preview`), `ATLASCLOUD_API_KEY`, Azure OpenAI (`OPENAI_API_KEY` +
> `OPENAI_BASE_URL`), or OpenRouter. **No such credential exists on `multivac`.** Statistical plots
> are emitted as VLM-generated matplotlib and need no *image* provider, but still require a VLM
> API call, so even those cannot be produced here.

**What this means for a reader of the public repository:** the figures are **not reproducible from
this repository alone**, and their generation is not deterministic — it depends on third-party
hosted models whose versions change. The measurements are unaffected: every figure draws on the
CSV/JSON in `data/raw/e12/`, which does ship.

**Consequence for how the manuscript is written:** figure specifications are authored on this host
as precise textual descriptions **plus the CSV/JSON the plots draw from**, and rendered wherever
the credentials live. Ship the specification and the source data alongside each figure so a reader
can regenerate it with any tool.

---

## 9. Software stack

| component | version | used for |
|---|---|---|
| llama.cpp (server + `llama-perplexity`) | 0.3.0-dev, build 1, commit `d222767` | every E12 measurement |
| llama.cpp z-lab DFlash2 fork | 0.1.2-dev, build 50, commit `f7aadef` | S9c only |
| EvalPlus | patched venv `/srv/bench/.venv-evalplus` | HumanEval+ scoring (`evalplus.sanitize` → `evalplus.evaluate`) |
| RULER | reference generators + `constants.py` templates; metric reproduced verbatim and unit-checked on 5 cases | S12 |
| Python | 3.x on host (harness), inside image for the engine | `data/raw/e12/harness-src/` |
| Docker | host daemon | all runs |
| mini-swe-agent | 2.4.6, venv `/srv/bench/.venv-swebench` | pre-E12 SWE-bench only |
| vLLM | stable 0.27.1 · nightly `0.26.1rc1.dev1219+g46638857f` | pre-E12 NVFP4 arm only; both images deleted |

**The harness that produced the E12 corpus** is mirrored read-only at
`data/raw/e12/harness-src/` (41 files). It is deliberately **not** at `$REPO/experiments/`, because
`tools/sync-multivac.sh push` copies that path onto `/srv/bench/e12` and a stale push would
overwrite the live harness. To change it, edit on multivac and pull back.

Key entry points: `lib_e12.py` (launch contract, 1 Hz VRAM sampler, `save_and_kill` log-first,
`classify_failure`, `preflight`) · `validate_v2.py` (the C1–C4 gate + F1–F4 self-test) ·
`tsweep_v2.py` (Wave 1) · `ssa_kld.py`, `ssa_s5.py`, `ssa_s7.py`, `ssa_reparse.py` (SSA) ·
`s8_spec.py`, `s9_final.py`, `s9d_depthsweep.py` (speculative decoding) · `s11_divdepth.py` ·
`s12_ruler.py` · `pad_e12.py`, `prebuild_pads.py`.

---

## 10. The rules that made this record possible

Stated because they are the paper's method contribution, and because each was written after a
failure that would otherwise have been unrecoverable.

1. **Logs before teardown.** A container that started is never removed until its `docker logs` are
   on disk at `/srv/bench/server-timings/<label>.serverlog`. This rule alone is why ten KLD cells
   were recovered after a parser bug (PN-17), why three distinct failure modes
   (compute-buffer-OOM / CUDA-IMA / init-hang) were separable, and why the mis-bound DFlash2
   drafter was diagnosable (PN-25).
2. **Docs before deletion.** Nothing is deleted until the ledger entry, the paper note and the
   manifest naming it are committed. `env-manifest.json` records sha256 + bytes + RepoDigest for
   every deleted item, so anything omitted is re-obtainable.
3. **Small tests before big tests.** Every battery runs a pilot that must pass first. The S7 pilot
   caught a parser bug before the full budget was spent; the S9d pilot caught the degenerate-
   generation defect and also corrected the gate itself.
4. **Bracket and re-test every ceiling.** A ceiling needs a *failed* rung above it, attempted
   twice — layer-split VRAM carries ±100–200 MiB of noise and single failures lie.
5. **Never mix protocols in a table.** PPL Protocols 1/2 and SSA-KLD are different instruments.
   Depth-0 and at-depth decode differ 3–5×. Greedy and official-sampling rows are not comparable.
6. **Append, never rewrite.** Superseded entries are superseded, never edited. Bad data is
   quarantined under `quarantine/`, never deleted; path changes get a remap note.
7. **A run that measured nothing must not exit 0**, and must not get a `.done` marker.
8. **One runner at a time.** Every long-running script takes an `flock`. `nohup setsid bash …`
   leaves a *parent and a child* — never wait on a PID from `pgrep`, wait on a condition.
9. **A finding that is not written down did not happen.** A stage that produced measurements and
   appended no paper note is an incomplete stage. (S8 sat undocumented for a day; S11 still is —
   see `METRIC-CORPUS.md` ⚑F-5.)
10. **Assert what you measured, not that the process succeeded.** Assert `/props n_ctx` ==
    requested; assert `prefill_frac ≥ 0.90`; assert a **generation floor**; assert the metric field
    is populated; assert the image id matches the manifest. Each of these was added after a defect
    that produced plausible-looking wrong numbers rather than an obvious failure.
11. **Anchor process-matching predicates to a path**, and escape regex metacharacters in literal
    filenames. An unanchored `pgrep -af "watchdog.sh|worker.sh"` matched the monitor built to
    supervise the campaign and killed eleven hours of work in eight minutes (PN-27).
