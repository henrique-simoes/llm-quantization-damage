# Method references — quantization-accuracy evaluation

External sources of record for the **Small-Sample Accuracy protocol (SSA)** adopted under DEC-11.
Fetched and read 2026-08-30. Each entry states what we take from it and how it constrains our
design, so the technical report can cite a methodological precedent rather than assert one.

Companion files: `PAPER-NOTES.md` (our findings), `PAPER-NOTES-PROTOCOL.md` (how to write them),
`../build-stream/2026-08-30-quant-bench-trackA.md` §Small-Sample Accuracy protocol (the design).

---

## R1 — llama.cpp perplexity/KLD tool (the instrument we run)
<https://github.com/ggml-org/llama.cpp/blob/master/tools/perplexity/README.md>

The tool that ships with the engine we are already using. `--kl-divergence-base <file>` records
reference logits; `--kl-divergence` scores a quant against them. One pass emits **mean KL divergence
with uncertainty, PPL ratio, mean Δp for correct tokens, Δp percentiles, RMS Δp, and the frequency
of identical top-token assignments**. Uncertainty on mean KLD is computed by treating per-token KLD
as Gaussian. WikiText-2 is the stated convention for the field.

*Constraint it imposes:* the logits file is large — the docs give **11 GiB for LLaMA-2 and 37 GiB
for LLaMA-3 on the full WikiText-2 test set**. Scaled to Qwen3.8-27B's vocabulary this is ~11 GB per
domain at our 65,536-token sample, which is why SSA fixes a token budget rather than using the full
corpus, and why the files land on `/` (82.9 GB free) and are deleted after use.

*Binary confirmed present* in `llamacpp-mtp:latest` as `/app/llama-perplexity`.

## R2 — llama.cpp discussion #4110: PPL is a poor quantization-loss metric
<https://github.com/ggml-org/llama.cpp/discussions/4110>

The community argument, from the engine's own contributors, that perplexity is an inadequate
quantization-loss benchmark and KL divergence is the better data point. Establishes that
divergence-first is the *norm* in this tooling ecosystem, not a shortcut we invented.

## R3 — Unsloth Dynamic GGUF methodology (the quants under test)
<https://unsloth.ai/docs/basics/unsloth-dynamic-2.0-ggufs> ·
<https://unsloth.ai/docs/basics/dynamic-3.0-ggufs>

The provenance of the models we are benchmarking. Unsloth ranks its Dynamic GGUFs on **mean KL
divergence** — over 150 KLD benchmarks, ~9 TB of GGUFs — and reports leading mean-KLD in 21 of 22
model sizes. Their per-layer quantization choice is made to minimize accuracy loss per layer.

*Constraint it imposes:* Unsloth explicitly warns that **evaluating on Wikipedia-like data while
calibrating on Wikipedia-like data overfits the metric**, and they deliberately do not use their own
calibration set when benchmarking KLD. We cannot inspect these GGUFs' imatrix calibration data, so a
wikitext-favourable bias cannot be excluded — recorded as SSA limitation 4, and the reason the
**code domain (D2) carries the weight** for the Track A conclusion rather than wikitext (D1).

## R4 — Fireworks: production quantization evaluation
<https://fireworks.ai/blog/fireworks-quantization>

Industry practice for exactly our decision. Metrics: **KLD + token rejection rate**, each split into
**prefill and generation** phases. Method: run a reference 16-bit model over varied prompts, record
top-N logprobs (**N=16 covers 0.99 of the distribution**), then **force the quantized model to follow
reference completions** so that divergent generations do not skew the comparison.

*What we take:* the forced-completion technique is what makes SSA step **S5** possible — divergence
measured over the 164 HumanEval+ task prompts with no generation at all, in minutes.

*Threshold:* they publish **KLD < 0.007 for high-quality deployments**, while noting a single
acceptable value is hard to define.

*Their argument against PPL, which we adopt:* perplexity **suffers from averaging bias** — lower
probabilities on some tokens are cancelled by higher probabilities on others, so real degradation
can hide inside an unchanged mean.

## R5 — LocalBench: GGUF quantization quality benchmark
<https://localbench.substack.com/p/gguf-benchmark-methodology>

The closest published analogue to what we are building. **~250,000 tokens across 6 task categories**
(coding, general chat, tool calling, science, non-Latin scripts, long documents), contexts up to
~30,000 tokens. Reports **KLD computed on prompt tokens only** plus **top-1 agreement %** — defined
usefully as "top-1 agreement of 85% means that for 85 out of every 100 tokens, the quant would pick
the same token as the original under greedy decoding". Measures over **top-40 token log-probabilities**
per position. Notes most KLD benchmarks use ~2,048-token context, and reports observed
**KLD ≈ 0.01–0.03 for Q4_K_M**.

⚠️ **Correction, 2026-09-02:** this band must NOT be cited as a neutral reference range. LocalBench
**disclaims** it — the source attributes those values to short-context Wikipedia-style protocols
(*"If you've seen KL values of 0.01-0.03 for Q4_K_M elsewhere, that's why"*). Citing it as a
baseline, as R5 and PN-14 originally did, inverts the source's meaning and would be caught in
review. Correcting it **strengthens** our argument: LocalBench is then independent support for the
protocol-dependence thesis this paper argues, not a benchmark we are measured against.

*Calibration for our sample size:* SSA's 131,072 tokens across 2 domains is roughly half
LocalBench's token budget, concentrated on the two domains that bear on a coding agent. Their
6-category breadth is what we explicitly give up (SSA limitation 3).

## R6 — Miller (Anthropic), *Adding Error Bars to Evals* (arXiv 2411.00640)
<https://arxiv.org/abs/2411.00640>

The statistics. Treats eval questions as a sample from a super-population, and recommends: CLT-based
standard errors reported alongside mean scores; **clustered standard errors** where questions are
grouped; **analysis of paired differences between models** rather than independent means; **power
analysis** to size a comparison; and multiple answers per question to reduce scoring noise.

*What we take:* the paired-difference recommendation is the entire justification for SSA step **S6**
running on **two arms rather than four**. At n=164 the independent-comparison interval is ±4.6
points while the arms differ by 1–3, so independent means cannot separate them; a seed-matched
paired per-problem comparison of the ladder's two extremes is the powered version of that question,
and a null result there is a reportable finding with stated power.

## R7 — *Which Quantization Should I Use?* — unified llama.cpp quantization evaluation (arXiv 2601.14277)
<https://arxiv.org/html/2601.14277v1>

Recent academic treatment of llama.cpp quantization on Llama-3.1-8B-Instruct: GSM8K (5-shot),
HellaSwag, IFEval, MMLU, TruthfulQA (0-shot), plus WikiText-2 perplexity obtained via
`./scripts/get-wikitext-2.sh` with identical runtime settings across schemes.

*Read honestly, this paper is a caution rather than a template.* It does not report KL divergence at
all, does not state token/chunk counts for its perplexity computation, and reports standard errors
without a minimum-effect-size or power discussion. It is cited as evidence that the task-battery
approach is publishable, and as the gap SSA is designed to avoid: **stating the sample and the power
up front instead of reporting intervals that cannot separate the arms.**

## R8 — RULER: the long-context benchmark, and the instrument S12 uses
<https://arxiv.org/abs/2404.06654> · <https://github.com/NVIDIA/RULER>

NVIDIA's synthetic long-context benchmark: retrieval (NIAH variants — single-key, multi-key,
multi-value, multi-query), multi-hop tracing (variable tracking), aggregation (common- and
frequent-word extraction) and QA (SQuAD/HotpotQA with distractors), all generated at a controlled
sequence length. Scored by string match; the reference metric `string_match_all` awards, per
sample, the fraction of reference answers appearing case-insensitively in the prediction.

*What we take:* the task generators, the official templates and answer prefixes from its
`constants.py`, its prompt construction (`input + answer_prefix`), and its metric — reproduced
verbatim and unit-checked against the reference implementation.

*What we could not take, and why (stated in the paper):* RULER's `OpenAIClient` is hardcoded to
OpenAI/Azure endpoints (requires `OPENAI_API_KEY`, tiktoken `cl100k_base`, and a fixed
model→context-length table) and its `requirements.txt` pins `nemo-toolkit[all]`, `vllm==0.5.4` and
`transformers==4.44.2`. Generation and scoring are therefore RULER's; only transport is ours.

*Constraint it imposes:* every sample needs a full prefill of its own haystack and prefix caching
cannot help, because each sample's haystack differs. At this host's measured ~600 tok/s that is
3.6 min per sample at 131,072 — the reason S12 runs n=12 there rather than the n=500 the benchmark
contemplates.

## R9 — Published precedents for exactly our experiment
<https://developers.redhat.com/articles/2024/02/03/how-well-do-quantized-models-handle-long-context-tasks> ·
<https://arxiv.org/abs/2505.20276>

**Red Hat** ran RULER on Llama-3.1 8B/70B at 4K–128K across FP W8A8, INT W8A8 and INT W4A16,
reporting **accuracy recovery** (quantized ÷ unquantized) per sequence length — >99.5 % at most
lengths, falling to **85–88 % for INT W4A16 at 128K**, on ~200,000 evaluations.
**arXiv 2505.20276**, *"Does quantization affect models' performance on long-context tasks?"* —
9.7K examples, 5 models × 5 schemes: 8-bit ≈ 0.8 % drop, 4-bit up to **59 %** on long inputs.

*What we take:* the accuracy-recovery framing, and a published band to place our MK-NIAH 91.67 %
beside. *What separates us:* they had clusters and ~200,000 evaluations; we have 150. Our numbers
are comparable in kind, not in power, and PN-33 says so.

## R10 — LongPPL: why a perplexity ladder would not have answered this
<https://arxiv.org/abs/2410.23771> (ICLR 2025) · <https://github.com/PKU-ML/LongPPL>

Establishes that perplexity is unreliable for long-context evaluation because it averages over all
tokens and thereby drowns the few **key tokens** that long-context ability actually turns on;
proposes LongPPL, which weights them, and reports a Pearson correlation of −0.96 with long-context
benchmark performance where plain PPL correlates poorly.

*Why it matters here:* S10 proposed a divergence/perplexity ladder at depth and was abandoned when
the instrument proved infeasible on this host's 14 GiB (PN-31). R10 says that even had it run, an
averaged token-level metric would have been the wrong instrument for the question — which is the
independent reason S12 uses a task benchmark instead. Cite it so the switch reads as a
methodological choice rather than a workaround for a memory limit.

## R11 — PaperBanana: the figure-generation tool this project is REQUIRED to use
<https://arxiv.org/abs/2601.23265> · <https://github.com/llmsresearch/paperbanana>

**Project prerequisite (owner, 2026-09-02).** Figures for this report are to be produced with
PaperBanana — the method for automating academic illustration, and an open-source implementation
of it.
⚠️ **Attribution corrected 2026-09-02 after review:** this note first called PaperBanana "Google
Research's method". The paper has a **mixed-affiliation author list**, not a Google Research one,
and the open implementation states it is **not affiliated with the original authors**. Cite the
paper and the implementation as separate artifacts with correct authorship; do not attribute
either to Google Research. Multi-agent pipeline: a retriever selects reference exemplars, a planner
writes a detailed figure description, a stylist refines it, a visualizer renders, and a critic
iterates (≈3 rounds, or until satisfied under auto-refine). Produces methodology diagrams,
statistical plots from CSV/JSON, and multi-panel composite figures; batch generation supported.

*What it produces:* **figures only** — not LaTeX, not prose, not full papers.

⚠️ *Constraint that affects planning:* it is **cloud-dependent and cannot run offline**. It needs
API keys for OpenAI (GPT-5.2 + GPT-Image-1.5), Google Gemini (free tier available:
gemini-2.5-flash + gemini-3-pro-image-preview), Atlas Cloud, or Azure OpenAI/Foundry. This host has
no such keys configured. Figure specifications must therefore be authored here as precise
descriptions plus the CSV/JSON the plots draw from, and rendered wherever the keys live. Every
figure spec in the manuscript should be written to be directly consumable by PaperBanana's planner.

## R12 — DFlash, and a published losslessness claim our measurements contradict
<https://arxiv.org/abs/2602.06036> (Chen, Liang & Liu, 2026, *DFlash: Block Diffusion for Flash
Speculative Decoding*) — **accepted at ICML 2026, cite the venue not the preprint**.
Authors' code: <https://github.com/z-lab/dflash> · third-party MLX port:
<https://github.com/Aryagm/dflash-mlx>

⚠️ **Corrected 2026-09-02 after review, three ways.** (a) It is an ICML 2026 paper, not a preprint.
(b) The authors' own repository is `z-lab/dflash` — **the same lab as this project's
`llama-dflash2:latest` engine fork**, which is a provenance link the paper should state rather than
leave implicit. (c) **The "bit-for-bit identical" wording belongs to the third-party MLX port, not
to the paper**; whether the paper itself makes that claim is UNVERIFIED. Attribute the quote to the
port, and do not put words in the paper's mouth.

The origin of the DFlash/DFlash2 drafter this study benchmarks (PN-29): a small block-diffusion
model proposes several tokens at once, which the target verifies in a single pass. The MLX **port** states the method is **"bit-for-bit identical to plain target decoding"** and
describes the verification rule as accepting the longest matching prefix plus one bonus correction
token. That sentence is the port's; the paper's own claim is unverified.

*Why this matters to our argument:* it is a clean, citable instance of the assumption our
measurements refute. PN-23 found MTP reproducing the no-spec baseline on only **131 of 164**
problems at temperature 0 with a fixed seed, and PN-26 established that both configurations
reproduce *themselves* byte-identically — so the divergence is **deterministic and systematic**,
not noise. We are not contradicting DFlash's own implementation, which we could not measure
losslessly (PN-25/PN-29 — different engine, different verification path); we are showing that
**"speculative decoding is lossless" is an implementation property that must be verified per
stack, not inherited from the algorithm's specification.** Cite R12 as MOTIVATION — the assumption is live and in print — and never as something this study
refutes: we measured llama.cpp's MTP head, not DFlash, and our own DFlash2 arm is engine-confounded
(PN-29). Setting it up as a refutation is the single easiest way to lose a reviewer.

## R13 — Dutta et al., *Accuracy is Not All You Need* — the prior work our broad framing belongs to
<https://arxiv.org/abs/2407.09141> — Abhinav Dutta, Sanjeev Krishnan, Nipun Kwatra,
Ramachandran Ramjee. **NeurIPS 2024.**

Establishes that benchmark accuracy is insufficient for evaluating compressed LLMs: baseline and
compressed models can score alike while behaving substantially differently. Introduces **"flips"**
— answers changing correct↔incorrect between baseline and compressed at notable rates despite
matched accuracy — and proposes **KL divergence** and flips as the metrics to use instead, showing
the two correlate. Qualitative MT-Bench evaluation shows compressed models markedly worse on
free-form generation. Studies multiple compression techniques, models and datasets.

⚠️ **This must be cited in our introduction, not in related work as an afterthought.** It owns the
claim "divergence sees what accuracy hides", and this study's PN-13/PN-22/PN-28 are an
**independent confirmation** of it — on a different model family (Qwen3.8-27B), a different
compression family (llama.cpp GGUF k-quants rather than the schemes they study), consumer
dual-GPU hardware, and three instrument classes including a generative coding benchmark. A
confirmation across that much variation is worth reporting and is not a novelty claim.

*What remains ours after crediting it:* **PN-35's tail structure.** Dutta et al. show accuracy
hides damage; they do not, as far as we can establish, decompose the divergence by quantile or
report that damage on code inverts between the median and the tail. That decomposition supplies a
mechanism with a numerical prediction — damage confined to ~1-5 % of positions changes an outcome
only when a tail token lands somewhere decisive, which predicts the 3/164 and 5/164 discordances
actually observed. Their "flips" metric is the outcome-level counterpart of exactly that prediction
and should be cited as such.

---

## How the sources combine into SSA

| SSA element | Source |
|---|---|
| KLD + top-1 agreement as the ranking instrument | R1, R2, R3, R5 |
| Divergence on **prompt tokens**, no generation | R4, R5 |
| Forced reference completions over task prompts (S5) | R4 |
| ~2,048-token context, token-budgeted sample | R1, R5 |
| Reference arm instead of FP16, labelled ladder-relative | R1 (logits-file cost), local constraint |
| Interpretation bands (<0.007; 0.01–0.03) | R4, R5 |
| Two-arm **paired** task anchor (S6), power stated | R6 |
| Rejecting PPL-alone as the ranker | R2, R4, R10 |
| Code domain weighted over wikitext | R3 (calibration contamination) |

## How the sources combine into S12 (long context)

| S12 element | Source |
|---|---|
| The benchmark, its generators, templates and metric | R8 |
| Accuracy-recovery framing vs a baseline arm, per length | R9 |
| Why a task benchmark rather than a perplexity/divergence ladder at depth | R10 |
| Two arms at the ladder's extremes rather than four | R6 (paired-difference, power) |
| Reporting "not separated at n" rather than a ranking | R6 |

## R14 — ACM Artifact Review and Badging, version 1.1
`https://www.acm.org/publications/policies/artifact-review-and-badging-current` (retrieved
2026-09-02). Defines the *Artifacts Available* / *Artifacts Evaluated — Functional* / *Results
Reproduced* tiers. **Used to scope this study's honest claim: Artifacts Available only**, once a DOI
exists. *Functional* requires the artifact to be complete, and it is not — every paper note's
Evidence line terminates in a `.serverlog` that `.gitignore` excludes, so the chain cannot be walked
from the public repository alone (reviewer D, §D3).
⚠️ A verbatim scrape of this page was committed at the repository root as `acmtxt.md` (74 KB) and
`acm.html` (45 KB), together with a copy of the Citation File Format JSON schema as `cff.json`
(63 KB). All three were **removed before publication and purged from history**: they are third-party
copyrighted web content, carried cookie-consent boilerplate and `blob:http://localhost/` image URLs,
and are properly cited here rather than vendored.

## R15 — Citation File Format, version 1.2.0
`https://citation-file-format.github.io/1.2.0/schema.json` (retrieved 2026-09-02). Schema used to
validate this repository's `CITATION.cff`. Validation was performed and passed; the schema copy
itself is not vendored — see the note under R14.

---

# S15 method references (added 2026-09-15, DEC-16)

Gathered by three research agents and checked by three adversarial verifiers against primary sources on
2026-09-15. Verdicts in brackets: **verified** (fact seen in the primary source), **corrected** (the fact as
stated here is the corrected one). Each entry says what S15 takes from it.

## R16 — llama.cpp PR #27342, DFlash2 support (merged 2026-08-27)
<https://github.com/ggml-org/llama.cpp/pull/27342> [corrected]
Merged 2026-08-27T17:05Z. Title "spec : add DFlash2 support (local convolution + candidate selector)". The
reconversion note ("GGUF generated before Aug 27th 2026 must be reconverted") is about **vision**, not text
drafting. Its own benchmark is Qwen3.8-27B Q4_K_M on Apple M5 Pro (~1.77–1.85× decode). *S15 takes:* one upstream
build runs MTP and DFlash2, removing PN-29's engine confound.

## R17 — llama.cpp PR #22105, DFlash support (merged 2026-06-28) and PR #22673, MTP (merged 2026-05-16)
<https://github.com/ggml-org/llama.cpp/pull/22105> · <https://github.com/ggml-org/llama.cpp/pull/22673> [corrected / verified]
`--spec-type draft-dflash`; up to 8× on dense targets; hybrid-model fallback handled by speculative checkpointing
(the "extra target forward per rejection" clause was struck from the PR body). MTP loads from the target GGUF but
has **its own context and KV cache**; Qwen3.6 aggregate acceptance 0.8258 at n-max 2, 0.7218 at n-max 3.
*S15 takes:* draft-length ranges, and that MTP's draft KV is a separate VRAM line.

## R18 — llama.cpp `docs/speculative.md` (master, 2026-09-15)
<https://github.com/ggml-org/llama.cpp/blob/master/docs/speculative.md> [corrected]
Lists draft-mtp, draft-dflash, draft-dspark, draft-eagle3; default `--spec-draft-n-max 3`; draft KV dtype
`-ctkd/-ctvd`; draft placement `--spec-draft-device/-devd`. The clamp to the trained block size is stated **only**
for DFlash and DSpark. *S15 takes:* DFlash2 n ∈ {3,5,7}; `--device-draft` in the placement sweep.

## R19 — DFlash 2 drafter for Qwen3.8-27B (Inco AI; z-lab mirror), cards, config and GGUFs
<https://huggingface.co/incoai/Qwen3.8-27B-DFlash2> · <https://huggingface.co/z-lab/Qwen3.8-27B-DFlash2> ·
<https://huggingface.co/z-lab/Qwen3.8-27B-DFlash2-GGUF> · blog <https://inco.ai/blog/dflash2/> (2026-08-18) [verified; blog corrected]
1,924,404,480 BF16 parameters, 5 layers, all sliding-window 2,048, `block_size` 8, target layers [5,19,33,47,61].
Mean acceptance length at block 8: DFlash 2 4.80 vs MTP 4.28 vs DSpark 3.62 (blog Table 4). The H200/SGLang setting
and the 2.67–3.43× speedups are in the **model card**, not the blog. GGUF acceptance BF16 5.28 / Q8_0 5.13 /
Q4_K_M 5.39 rests on **8 GSM8K prompts** — noise, not a quantization effect. Rope-sections fix: z-lab 2026-08-24,
incoai 2026-08-29. No training length and no long-context evaluation published. *S15 takes:* the drafter, its
revision pin, and that at-depth acceptance is unpublished.

## R20 — Chen, Liang & Liu, DFlash, ICML 2026 (arXiv 2602.06036 v2) — long-context behaviour
<https://arxiv.org/abs/2602.06036> [verified] — extends R12.
Drafters trained on ~800K samples at max length 3,072 (4,096 for the Coder drafter). Table 4 (DFlash v1, Qwen3.5-27B):
gov_report acceptance 4.53 (1K) → 2.09 (32K), held near 4 by a 1.6K-sample LongAlign fine-tune. *S15 takes:*
DFlash2 acceptance at depth must be measured, not assumed; do not transfer v1 numbers to v2.

## R21 — Community long-context DFlash2 measurements
<https://github.com/lukaLLM/DFlash2_Qwen3.8_3.6_27B_LlamaCPP> · <https://github.com/noonghunna/club-3090/discussions/1076> [verified]
lukaLLM (RTX PRO 6000, llama.cpp): n_max 5 faster than 7 at 8,192 tokens (3–7 valid generations per cell); zero valid
decode numbers at 65,536 and 131,072; +2,720 MiB at 262K f16. club-3090 (2× RTX 3090, vLLM, W4A16 drafter, fp8 KV):
~72 tok/s at ~90K, 66 at ~200K. *S15 takes:* community evidence only — never the sole support for a decision.

## R22 — llama.cpp issue #25618, speculative greedy divergence on quantized targets (open)
<https://github.com/ggml-org/llama.cpp/issues/25618> [corrected]
Divergence reported for DSpark and MTP on quantized targets; bf16 parity shown for DSpark only; later comments extend
it to Q8_0 at n-max 1 and to non-bit-exact batched kernels. *S15 takes:* drafter accuracy is compared at task level (PN-76).

## R23 — Thinking Machines Lab, "Defeating Nondeterminism in LLM Inference" (2025-09) and vLLM speculative-decoding docs
<https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/> · <https://docs.vllm.ai/en/latest/features/speculative_decoding/>
Run-to-run deterministic but batch-variant kernels; speculation lossless only up to hardware numerics. *S15 takes:* PN-76.

## R24 — Artificial Analysis: Qwen3.8-27B records and methodology (fetched 2026-09-15)
<https://artificialanalysis.ai/models/qwen3-8-27b> (+ `-medium`, `-low`, `-non-reasoning`) ·
<https://artificialanalysis.ai/methodology/intelligence-benchmarking> · <https://artificialanalysis.ai/methodology/performance-benchmarking>
Archived with sha256 at `/srv/bench/external/artificial-analysis/2026-09-15/` (PN-75). First-party Alibaba API;
temperature 0.6 for reasoning models (unless the lab recommends otherwise); max output tokens; pass@1; speed
workloads ~1K/10K/100K input with ≥1K/1.5K/2K answer tokens, P50 over 72 h (14 days for 100K). *S15 takes:* the
external comparison row and the speed workloads, labelled as a different serving stack.

## R25 — AA-LCR v1.1 dataset (Artificial Analysis), Apache-2.0
<https://huggingface.co/datasets/ArtificialAnalysis/AA-LCR> revision `9a77ef56` (2026-09-04)
100 questions, 30 document sets, ~100K cl100k tokens per set; human-verified; v1.1 adds a judge **system prompt** and
16 corrected answer keys, so v1.0 scores are not comparable. Official prompt template and judge prompts are in the
card; Artificial Analysis grades with GPT-5.6 Luna (medium). *S15 takes:* the long-context accuracy instrument (T4a).

## R26 — GPQA (Rein et al., 2023), Diamond subset
<https://github.com/idavidrein/gpqa> · arXiv 2311.12022 · CC-BY-4.0
198 Diamond questions, distributed as a password-protected zip with a canary string; the authors ask that examples not
be revealed online. *S15 takes:* the short-context reasoning accuracy instrument (T4b), regex-scored.

## R27 — Long-context evaluation standards
RULER (Hsieh et al., NVIDIA, arXiv 2404.06654 = R8) · HELMET (Yen et al., ICLR 2025, arXiv 2410.02694) [verified: NIAH
correlates weakly with downstream tasks; RAG predicts best] · NoLiMa (Modarressi et al., ICML 2025, arXiv 2502.05167)
[corrected: 11 of 13 models fall below 50 % of their short-context baseline at 32K] · MRCR v2 (google-deepmind/eval_hub)
[verified bins; Anthropic's system cards use OpenAI's MRCR v2 release, not eval_hub's] · LongCodeBench (arXiv 2505.07897)
[verified: LongCodeQA 443 items, bins 32K–1M]. *S15 takes:* the case for a reasoning-over-documents instrument
(AA-LCR) over literal-match needles, and the reporting of budget and closure per item (PN-60).

## R28 — Speculative-decoding evaluation
Leviathan et al. (arXiv 2211.17192) · Chen et al. (arXiv 2302.01318) · EAGLE-3 (arXiv 2503.01840) · SPEED-Bench (NVIDIA,
arXiv 2604.09557) · Spec-Bench (Xia et al., arXiv 2401.07851) · MagicDec (arXiv 2408.11049). *S15 takes:* τ (mean accepted
length per pass) and t_pass as primary speed quantities, long real generations (never tens of tokens), each drafter at its
own best draft length, and depth-dependent reversal as an analysis requirement.

## R29 — KV-cache quantization quality
localbench (oobabooga), "Gemma 4 and Qwen 3.6 with q8_0 and q4_0 KV cache: KL divergence results" (2026-04-24) [corrected:
Qwen3.6-27B q8_0 0.024; Qwen q4_0 0.087–0.117; long documents up to 0.581; BF16 reference; top-40 KLD] · KIVI (arXiv 2402.02750)
· KVQuant (arXiv 2401.18079) · llama.cpp issue #23210 [verified: q8_0 + MTP crash on 2× 5060 Ti, cause not attributed to q8_0].
*S15 takes:* the KV/context map with q8_0 re-tested on the current image, and PN-77's scoping of PN-15.

## R30 — Evaluation statistics and serving-metric definitions
Miller, "Adding Error Bars to Evals" (Anthropic, arXiv 2411.00640 = R6) · Bowyer, Aitchison & Ivanova, "Don't Use the CLT in
LLM Evals With Fewer Than a Few Hundred Datapoints" (ICML 2025, arXiv 2503.01747) [verified] · MLPerf Inference rules
(MLCommons) · NVIDIA GenAI-Perf README · `vllm bench serve` · llama-bench README (`-d` depth) · llama.cpp server README
(`timings`). *S15 takes:* paired designs and small-n intervals; TTFT/TPOT/output-speed definitions; decode from server
timings, not SSE chunk arrival.

## How the sources combine into S15

| S15 element | Source |
|---|---|
| One upstream image for both drafters | R16, R17, PN-73 |
| DFlash2 n ∈ {3,5,7}, MTP n ∈ {2,3,4} | R17, R18, R19, R21 |
| Drafter placement sweep (`--device-draft`) | R18, PN-73 |
| Accuracy compared at task level, not byte identity | R22, R23, PN-23, PN-76 |
| AA-LCR at 262,144 with the official template | R24, R25, R27 |
| GPQA Diamond regex-scored | R24, R26 |
| τ, t_pass, long generations, per-drafter optimum | R28, PN-30, PN-68, PN-72 |
| KV/context map with q8_0 re-tested | R29, PN-15, PN-74 |
| Paired designs, small-n intervals, metric definitions | R30, R6, PN-32 |
| External comparison row | R24, PN-75 |

## R31 — llama.cpp source at the pinned commit 4c9233c (b10975): speculation, checkpoints, sampling
<https://github.com/ggml-org/llama.cpp/tree/4c9233c034fc450dcf34c7c0988aebe6da5cdf1a> (read 2026-09-15; the first two re-verified by hand)
- `tools/server/server-schema.cpp` lines 197–227: per-request `speculative.*` fields inside `#if 0` (PN-79).
- `tools/server/server-context.cpp` line 3565: `checkpoint_offsets[] = {4 + n_ubatch, 4}` — prompt checkpoints near the
  prompt end, created only during prompt processing (with PR #20288). *S15 takes:* prefix reuse across AA-LCR questions of a
  document set works at `-ctxcp 4`, asserted via `cache_n`.
- `common/sampling.cpp` `common_sampler_sample_and_accept_n`: the target samples every emitted position — why drafter
  accuracy is an equivalence gate (DEC-17 item 3). `common/speculative.cpp`: DFlash clamp to block_size−1; draft devices.
- `src/models/dflash.cpp`, `src/llama-model.cpp`: DFlash's sliding-window cache; `--swa-full` default false (b10975 `--help`).
(Items not re-verified by hand are from the S15 reviewer's reading of the same commit.)

## R32 — Artificial Analysis GPQA prompt and multiple-choice extraction (methodology page, archived 2026-09-15)
`/srv/bench/external/artificial-analysis/2026-09-15/methodology-intelligence-benchmarking.html` (sha256 in `SHA256SUMS`).
Template: "Answer the following multiple choice question. The last line of your response should be in the following format:
'Answer: A/B/C/D' (e.g. 'Answer: A')." + question + "A) … D) …". Extraction: single-letter responses taken directly; primary
`(?i)[\*\_]{0,2}Answer[\*\_]{0,2}\s*:[\s\*\_]{0,2}\s*([A-Z])(?![a-zA-Z0-9])`; fallbacks in order `\boxed\{[^}]*([A-Z])[^}]*\}`,
`answer is ([a-zA-Z])`, `answer is \(([a-zA-Z])`, `([A-Z])\)\s*[^A-Z]*`, `([A-Z])\s+is\s+the\s+correct\s+answer`, `([A-Z])\s*$`,
`([A-Z])\s*\.`, `([A-Z])\s*[^\w]`; "We always take the last match found". GPQA listed under legacy evaluations. *S15 takes:*
the locked GPQA protocol (DEC-17 item 6).

## R33 — OpenAI simple-evals, multiple-choice template and answer pattern
<https://github.com/openai/simple-evals> (`common.py`: `QUERY_TEMPLATE_MULTICHOICE`, `ANSWER_PATTERN_MULTICHOICE`
`(?i)Answer[ \t]*:[ \t]*\$?([A-D])\$?`). *S15 takes:* a secondary GPQA extraction column only. Taken from the reviewer's reading;
not re-verified by hand.

## R34 — llama.cpp PR #20288, context checkpoints near the prompt end (merged 2026-03-10)
<https://github.com/ggml-org/llama.cpp/pull/20288>. With R31, the mechanism behind cheap prefix reuse on the hybrid model.
Merge date from the reviewer; the code effect re-verified in R31.

| S15 amendment (DEC-17) | Source |
|---|---|
| One launch per draft length | R31, PN-79 |
| Same target KV for both drafters in the accuracy contrast | R31 (draft SWA cache), PN-74, PN-77 |
| Accuracy as equivalence gate | R31 (sample-and-match), R22, R23, R28 |
| Soak and q8_0 stability before T4 | R29 (#23210), PN-70 |
| GPQA template and extraction | R32 (primary), R33 (secondary) |
| Prefix reuse assertion | R31, R34 |
