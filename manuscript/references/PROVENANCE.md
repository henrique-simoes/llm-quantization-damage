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

**Gaps between the repo and the host — status after the 2026-09-02 review round.** Nearly all are
now closed:

| item | 2026-09-02 | now |
|---|---|---|
| `ruler/s12-ruler.json` stale (pre-MK-NIAH, pre-dedup) | **missing** | ✅ synced, and **superseded** by the mk100 cells |
| `ruler/s12-preds-*-mkniah-c131072.json` | missing | ✅ synced |
| `s8/s8-scores-reparsed.json` | missing | ✅ synced and verified |
| `progress.json` | missing | ✅ present — and it is the evidence behind PN-41's 2.15 h |
| `s11-pads-manifest.json` | missing | ❌ still host-only (minor) |

⚠ **One summary block is still stale inside a synced artifact**: `s12-ruler.json`'s
`accuracy_recovery` has **no `mk100` entry** and still shows the superseded n=12 value of 91.67,
while its `tasks` and `n_samples` fields describe the original design. See `METRIC-CORPUS.md`
⚑**F-27**. The `cells` array is correct and complete.

Pull anything else with
`./tools/sync-multivac.sh artifact /srv/bench/e12/<path> data/raw/e12/<dest-dir>/`
(the second argument is a destination **directory**).

### 7.1 Artifacts added by the review round and the mk100 run

| artifact | what it fixes |
|---|---|
| `corpus-manifest.json` | the code corpus (D2) was **gitignored and unmanifested** — every code-domain number in the study rested on a file with no digest. Now pinned: **9,097,163 B**, `sha256:049d12efad53048bbadf7b8f2c79afeedfbdfb7cbf316633f5673cd8a9f915af` |
| `harness-src/s12_mkniah_generate.sh` | the MK-NIAH **generation command existed nowhere** — the harness read a pre-generated file and the `--num_needle_k 4` invocation was ad-hoc, so the dataset was not reproducible from a public repo |
| `harness-src/mk100_analyse.py` | the paired analysis, **written and committed before the second arm finished**, so the test was fixed in advance of the data |
| `s8/s8-scores-reparsed.json` | the repaired S8 scoring with Wilson intervals; `s8-scores.json` is left unedited and superseded |
| `_WARNING_` fields in four artifacts | see below |

**`corpus-manifest.json` carries a stated limitation that is load-bearing for the headline** and
must travel with any citation of the code domain: reference-arm perplexity on this corpus is
**1.1809 (0.240 bits/token)** against **5.7898** on WikiText-2, and median per-token KLD is
**1.7e-05** against a mean of **0.021529** — *the mean is ~1,266× the median.* **The corpus is far
more predictable than general source code.** It is a path-sorted concatenation of a Python/django
tree, **not deduplicated**, and whole passes repeat when the requested length exceeds the tree. A
public reader cannot regenerate it byte-for-byte without the same checkout; the sha256 pins the
exact file used.

### 7.2 In-artifact warnings — the review round's most reusable practice

Four artifacts now carry a `_WARNING_` field written *into the JSON*, so a reader who never opens
the paper notes still cannot misread them:

| artifact | field | says |
|---|---|---|
| `ssa/ssa-results-parsed.json` | `_WARNING_label_collision` | two cells share `ssa-Q6_K_XL-code-base` and one serverlog; **for these two cells trust `metrics`, not `metrics_reparsed`** — the reverse of the rule everywhere else |
| `s8/s8-humaneval.json` | `_WARNING_equivalence_dflash4` | the dflash4 entry records 0/164 for a server that **never loaded**; excluded data (PN-25) |
| `s9/s9d-depthsweep.json` | `_WARNING_best_n_per_arm_per_depth` | **superseded** — it names a winning draft depth, which PN-32 shows is unanswerable at n=3 |
| `s9/s9e-n262k.json` | `_WARNING_best_n_per_arm_per_depth` | **superseded** — "best n=4" is a 3 % difference far inside the noise |

This is worth stating in the paper as method: **when a summary field in a machine-readable artifact
contradicts the note that cites it, correct the artifact in place with a warning rather than
deleting the field** — deletion loses the record that the mistake was made.

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
`s12_ruler.py`, **`s12_mkniah_generate.sh`** (the MK-NIAH dataset generator, added by the review
round), **`mk100_analyse.py`** (the pre-registered paired analysis) · `pad_e12.py`,
`prebuild_pads.py`.

### 9.1 Reproducing the study's two headline results

| result | command path |
|---|---|
| **PN-35** — the tail quantiles | read `median_kld`, `kld_90p`, `kld_95p`, `kld_99p`, `max_kld` from `metrics_reparsed` in `ssa/ssa-results-parsed.json` and take code ÷ wikitext2 per arm. **Six of the seven rows need no GPU and no serverlog**; only the p99.9 row requires the host-only serverlogs |
| **PN-44** — MK-NIAH at n=100 | regenerate with `s12_mkniah_generate.sh` (RULER's own generator, `num_needle_k=4`), serve at `-c 131072 -ts 56,44 -ctk/-ctv q4_0 -ctxcp 32`, greedy, no-spec, then `mk100_analyse.py`. Or score the shipped `ruler/s12-preds-*-mk100-c131072.json` directly with RULER's `string_match_all` — **every figure in PN-44 reproduces from those two files alone**, verified 2026-09-03 |

---

## 10. Public-repository readiness — what publication requires that this repo does not yet have

Researched 2026-09-02 against the primary standards, with the URL for every claim. Recorded here
because the repository is to be made public alongside an arXiv submission, and three of these are
blocking.

### 10.1 A GitHub link is not an archived artifact

ACM's *Artifact Review and Badging* **v1.1 (2020-08-24)** defines **Artifacts Available** as
*"Author-created artifacts relevant to this paper have been placed on a publically accessible
**archival** repository. A DOI or link to this repository along with a unique identifier for the
object is provided"* — and states *"Personal web pages are not acceptable for this purpose."*
ACM CCS 2025 makes the exclusion explicit: *"making the artifacts available solely through personal
web pages, **GitHub, GitLab, or a similar software-development site is not adequate** for receiving
this badge."* Acceptable: Zenodo, FigShare, Dryad, Software Heritage.
· <https://www.acm.org/publications/policies/artifact-review-and-badging-current>
· <https://www.sigsac.org/ccs/CCS2025/call-for-artifacts/>

Corroborated by *Good Enough Practices in Scientific Computing* rule 1g — *"Submit data to a
reputable DOI-issuing repository so that others can access and cite it"*
(<https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1005510>) — and by
NeurIPS's dataset guidance (*"The dataset should have a persistent identifier such as a Digital
Object Identifier"*).

> ⚠ **This repository currently has no public remote at all** — by design, a bare hub on the host.
> So the GitHub→Zenodo automation does not apply, and the route is **manual Zenodo upload**.

### 10.2 The DOI, and the ordering problem

Zenodo mints **two DOIs on first publication**: a **version DOI** for the specific deposit and a
**concept DOI** representing all versions
(<https://support.zenodo.org/help/en-gb/1-upload-deposit/97-what-is-doi-versioning>).

* **Cite the version DOI in the paper's bibliography** — it is the only identifier that resolves to
  the exact artifact that produced the tables.
* **Use the concept DOI in the README badge and in `CITATION.cff`**, where "always latest" is what
  a reader wants.

**The ordering trap, and why the manual route is the right one here.** Zenodo's GitHub integration
fires on a **Release** object (not a tag, not a push) and *"It is not possible to pre-reserve DOIs
before using GitHub integration with Zenodo"*
(<https://support.zenodo.org/help/en-gb/24-github-integration/73-can-i-pre-reserved-a-doi-before-a-github-release>).
A **manual upload does support DOI pre-reservation** — *"You can include this DOI in files prior to
uploading them"* (<https://help.zenodo.org/docs/deposit/describe-records/reserve-doi>), with the
caveat that deleting the draft loses the reserved DOI. Since this repo has no public forge, the
manual route is both the only available one **and** the one that lets the DOI be printed inside the
archived artifact and in the paper before submission.

⚠ **`.zenodo.json` silently disables `CITATION.cff`**: *"If both files are present in your
repository, **only** the `.zenodo.json` metadata will be used… The `CITATION.cff` metadata will be
ignored by Zenodo"* (<https://help.zenodo.org/docs/github/describe-software/>). Keep
`CITATION.cff` anyway — GitHub uses it for its "Cite this repository" panel.

**Size:** 50 GB and 100 files per record by default, with a self-service allowance to 200 GB, and
unlimited records under 50 GB (<https://help.zenodo.org/docs/deposit/manage-quota/>). ⚠ Zenodo's
own policies page still states a flat 50 GB cap, so the two disagree — re-check before relying on
it. This repo's tracked tree is ~13 MB, so the limit is not close to binding; it would only matter
if GGUFs or serverlogs were ever archived. Note also *"The **older API** supports 100MB per file"* —
the classic scripted-upload trap (<https://developers.zenodo.org/>).

**Retention, quotable in a data-availability statement:** *"Items will be retained for the lifetime
of the repository. This is currently the lifetime of the host laboratory CERN, which currently has
an experimental programme defined for the next 20 years at least"* — with Zenodo's own caveat that
it *"makes no promises of usability and understandability of deposited objects over time"*
(<https://about.zenodo.org/policies/>).

### 10.3 Software Heritage — complementary, and intrinsic

Deposit via Save Code Now (<https://archive.softwareheritage.org/save/>), no account required,
supporting `git, hg, svn, cvs, bzr, tarball`. SWH's advice is to *"trigger archival on branch, tag,
or release creation, rather than on every push"*
(<https://www.softwareheritage.org/how-to-archive-reference-code/>).

The identifier is an **SWHID**, standardised as **ISO/IEC 18670:2025** on 2025-04-23
(<https://www.swhid.org/>), with grammar
`swh:1:<snp|rel|rev|dir|cnt>:<40 hex digits>` plus optional `origin=`, `visit=`, `anchor=`,
`path=`, `lines=` qualifiers
(<https://docs.softwareheritage.org/devel/swh-model/persistent-identifiers.html>).

The distinction that makes it worth doing **in addition to** a DOI, in SWH's own words:
*"**Extrinsic**: use a register to keep the correspondence between the identifier and the object.
**Intrinsic**: intimately bound to the designated object, they do not need a register, only
agreement on a standard."* A DOI is a registry's promise; a SWHID **is** the hash, recomputable
offline. Since late 2024 Zenodo forwards publicly-accessible single-archive deposits to SWH
automatically (<https://blog.zenodo.org/2024/10/21/2024-10-21-swh>) — but **do a Save Code Now
anyway**, because it archives the full git history, which a Zenodo tarball does not.

⚠ Save Code Now needs a **publicly clonable URL**, which this repo does not currently have.
⚠ A restricted or embargoed Zenodo record is **not** forwarded to SWH.

### 10.4 What the public README must contain

The operative standard is the **ML Code Completeness Checklist**
(<https://github.com/paperswithcode/releasing-research-code>), adopted as official NeurIPS
guidance: *specification of dependencies · training code · evaluation code · pre-trained models ·
a README with a table of results accompanied by precise commands to reproduce them.*
(⚠ Papers-with-Code itself is sunset — `paperswithcode.com` now redirects to Hugging Face — but
the checklist repository is live and still cited by NeurIPS.)

Two of its five items do not apply to an inference-benchmark paper and need substituting: **training
code → the launch/measurement harness** (`data/raw/e12/harness-src/`), and **pre-trained models →
the exact quantized weights with sha256 and provenance** (§3 above).

Four sections distinguish a systems-benchmark repo from a generic ML one, and none of them come
from the general project-layout literature — **all four are already written and only need
surfacing into a public README**:

| section | source | where it already exists here |
|---|---|---|
| hardware and environment specification | ML Reproducibility Checklist v2.0, *"a description of the computing infrastructure used"*; NeurIPS checklist item 8 | §1, §2, §9 of this file |
| expected runtime / compute / energy per result | MLRC, *"the average runtime for each result, or estimated energy cost"* | per-cell `seconds` in every artifact; §7 of `METRIC-CORPUS.md` |
| statistical protocol — n, estimator, seeds, interval type | MLRC; NeurIPS item 7 | §8.4 of `METRIC-CORPUS.md`; §4 of this file |
| known limitations / what this repo does **not** contain | NeurIPS item 2 (*"Reviewers will be specifically instructed to not penalize honesty concerning limitations"*) and item 5 | §7 of this file; §9.10 of `METRIC-CORPUS.md` |

<https://www.cs.mcgill.ca/~jpineau/ReproducibilityChecklist.pdf> ·
<https://neurips.cc/public/guides/PaperChecklist>

### 10.5 Three practices this project already follows, which the standards name

Worth stating in the public README as compliance rather than leaving them as internal habit:

1. **`irreproducible-on-current-images` labelling** is exactly NeurIPS checklist item 5: *"If a
   subset of experiments are reproducible, you should state which ones are."* It reads as an
   admission and is in fact best practice.
2. **`quarantine/`** — excluded but retained, with a register — maps to the ML Reproducibility
   Checklist's *"an explanation of any data that were excluded."*
3. **`env-manifest.json`** (sha256 + bytes + RepoDigest for every artifact, including deleted ones)
   maps to ACM's *"Documented: at minimum, an **inventory of artifacts** is included"* and to
   MLPerf's `systems/<system_desc_id>.json` machine-readable hardware/software manifest
   (<https://github.com/mlcommons/policies/blob/master/submission_rules.adoc>).

### 10.6 Missing files, and licensing

**Not present and required for publication:** `LICENSE` (Zenodo makes the licence field
**mandatory**, on the SPDX list, and the GitHub→Zenodo path requires one),
`LICENSE-DATA`, `CITATION.cff`, and a public-facing `README.md` section covering §10.4.

`CITATION.cff` is at **version 1.2.0**, requires exactly four keys — `authors`, `cff-version`,
`message`, `title` — and must sit at the **root of the default branch**
(<https://citation-file-format.github.io/>,
<https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files>).
GitHub renders APA and BibTeX from it.
⚠ The two CFF→BibTeX converters **disagree on entry type** — `cffconvert` emits `@misc`,
`ruby-cff` emits `@software` — and GitHub does not document which it uses. Compile whatever is
pasted and read the `.blg`.

**Licensing, code vs data.** Creative Commons *"recommend[s] against using Creative Commons
licenses for software"* while confirming *"CC licenses can be used on databases"*
(<https://creativecommons.org/faq/>); the Turing Way recommends CC0/CC-BY/PDDL/ODC-BY/ODbL for data
(<https://book.the-turing-way.org/reproducible-research/licensing/licensing-data>). Dual licensing
— permissive for the harness, CC-BY-style for the measurement data — follows from combining the
two, though **neither states it as a requirement**. The only hard rule is NeurIPS's: *the license
and any data-access restrictions must be described in the paper.*

### 10.7 One terminology trap worth avoiding in the manuscript

ACM v1.1 **swapped the senses of two words**: *"ACM agreed with NISO's recommendation to **swap the
terms 'reproducibility' and 'replication'**… ACM took action to update all prior badging to ensure
consistency."* Current senses: **Repeatability** = same team, same setup · **Reproducibility** =
*different* team, same setup · **Replicability** = different team, different setup. Many live
conference pages still show the pre-2020 opposite sense. **Define the term in the paper and cite
the version.**

---

## 11. The rules that made this record possible

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
