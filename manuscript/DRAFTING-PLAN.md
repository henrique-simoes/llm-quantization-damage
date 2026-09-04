# Drafting plan — the arXiv technical report

**Status:** drafting opened 2026-09-03. Measurement is closed (L-18); re-analysis closed at L-26.
Evidence base: **PN-1…PN-64**. This document is the process of record for turning that base into a
submitted paper. It does not restate findings — those live in `docs/paper/PAPER-NOTES.md` — it
decides *how the paper gets written, illustrated, formatted and submitted*, and in what order.

Companion documents, each owning one thing:
| document | owns |
|---|---|
| [`OUTLINE-V2.md`](OUTLINE-V2.md) | **the live structure** — §1–§8 plus lettered appendices A–D, the 13,500-word budget, and the PN→section evidence map for all 66 notes |
| [`OUTLINE.md`](OUTLINE.md) | the superseded v1 structure (§1–§9), retained unedited as the record of the pre-rebalance plan |
| [`STYLE-GUIDE.md`](STYLE-GUIDE.md) | voice, positioning, density technique, sentence conventions |
| [`figures/FIGURE-PROGRAMME.md`](figures/) | every figure and table, its claim, spec and data |
| [`references/`](references/) | the metric corpus, provenance, timeline, `references.bib` |
| [`review/`](review/) | four blind reviews — historical record, never edited |
| `tex/` | the LaTeX source that is actually submitted |

---

## 0. The three things that decide everything else

**a. The North Star, already decided (L-25).** Title and abstract are fixed and are not reopened
during drafting:

> **Divergence Ranks What Benchmarks Bound: quantization, context and speculative decoding for a
> 27B coding model on two 16 GB GPUs**

Abstract: reviewer D's A2 as adopted, live in `CITATION.cff`. The thesis in one line — *the
instrument decides whether there is anything to see*. Every section either supports that or is
labelled as supporting material.

**b. Authorship and scope — an honesty requirement, not a disclaimer.**
Solo-authored by **Luiz Henrique Simões**, independent researcher; **professional master's
candidate in Data Science and Analytics, Universidade de São Paulo (USP)**. The paper must state
plainly, in the author block and again in §1, that it is **a technical report by an independent
practitioner — not a peer-reviewed paper from a university group or an AI lab**. No institutional
"we" that implies a team. No implied peer review. The evidence carries the authority; the framing
must claim exactly that much and no more. See `STYLE-GUIDE.md` §1 for the exact wording.

**c. Density over compression — the owner's binding instruction.**
Twelve-plus days of GPU time produced this corpus. A write-up that summarises it away wastes the
measurement. **Prefer a full table carrying n, estimator, interval and protocol over a summarising
sentence. Give each substantive finding its own figure or table.** The paper is meant to be large
and dense *and* readable; `STYLE-GUIDE.md` §2 carries the techniques that make those compatible.

---

## 1. ⚠️ START ENDORSEMENT NOW — it gates submission and it is slow

**This is the single most likely thing to stall the paper for weeks, and it is independent of
drafting. Begin it in parallel, today.**

Since **2026-01-21** arXiv no longer accepts an institutional email as the sole qualifier for a new
author in any category; auto-endorsement needs an institutional address **and** prior claimed
authorship in the domain. A first-time solo author with a personal address has neither, so
**personal endorsement is the only route**, and arXiv staff cannot waive or supply it.

Sequence:
1. Start a submission, pick the category — arXiv emails a six-character endorsement code.
2. Find candidates via *"Which authors of this paper are endorsers?"* on the abstract page of a
   recent paper this report cites; the submitter's email is under Submission history.
3. Contact them **individually** with the code, a scholarly profile link, and ideally the draft.
   arXiv states it is *"inappropriate to email large numbers of potential endorsers at once."*
4. `cs` is a **single endorsement domain** — any active `cs.*` author qualifies for `cs.LG` or
   `cs.PF`, which widens the pool considerably.
5. Net endorsement must stay positive; negatives are recorded.

A USP affiliation may help in the approach even though it does not auto-qualify. Source: reviewer B,
`review/reviewer-b-structure.md` §arXiv submission mechanics, with arXiv help URLs.

---

## 2. arXiv compliance — settled, do not re-derive

Researched and recorded in `review/reviewer-b-structure.md`; binding for this submission.

| item | decision |
|---|---|
| Primary category | **`cs.LG`** |
| Cross-list | **`cs.PF`** (one only). **Not `cs.AI`** — arXiv defines it as excluding ML. Not `cs.CL` as a third; *"bad cross-lists will be removed."* |
| ACM class | `D.4.8; I.2.6` |
| Source format | **LaTeX source, never PDF-only.** *"A PDF file created from a TeX/LaTeX file will typically be rejected."* PDF-only also forfeits accessible HTML **and ancillary files**. |
| Bibliography | `.bib` processed directly since **2025-11-05**; `.bbl` no longer required. |
| Figures | `.pdf`/`.png`/`.jpg` for pdfLaTeX; **vector PDF for every line plot**. No on-the-fly conversion, no external deps, no embedded JavaScript. |
| Layout | Flat directory, compiled from the submission root. |
| Size | Budget **≤ 50 MB**; arXiv warns on images above **34 megapixels** (from 2026-02). |
| Format policy | Named authorship, complete references, single-spaced 10–14 pt, ≥ 1″ margins, no line numbers, no watermarks. |
| Licence | **CC BY 4.0** — irrevocable per version, chosen at submission. Matches the repository's `LICENSE-DATA`. |
| Ancillary | JSON artifacts under `tex/anc/` — arXiv lists "raw data for tables and plots" and "program code" as intended contents. |
| Abstract | ≤ 1,920 characters, ASCII-clean, pastes into the metadata field unmodified. |

**Resolved 2026-09-03:** arXiv requires that *"links to code or data sets must resolve to a publicly
available repository."* The repository is now public at
`github.com/henrique-simoes/llm-quantization-damage`, which clears reviewer B's stated blocker.
Still to do before submission: **Zenodo deposit for a DOI** and a **Software Heritage SWHID** for
the exact tree state, both printed in a page-1 footnote and an *Artifact availability* section. Do
not rely on arXiv's "Code, Data, Media" tab — it was powered by Papers with Code, which shut down in
July 2025.

**Moderation risk, stated honestly:** the realistic decline ground is arXiv's clause on submissions
that *"do not contain original or substantive research, including course projects, research
proposals."* Mitigation is structural, not cosmetic: lead with measurement that does not exist
elsewhere (the divergence ladder, the protocol swing, the speculative non-equivalence result), and
make the twelve-day measurement record and its corrections visible as method. Moderation is not peer
review, gives no feedback, is appealed only through the support portal, and *"decisions upon appeal
are final."*

---

## 3. Drafting order — dependencies first, prose last

Writing §5 before §7 is how a results section acquires claims the threats section then has to
retract. This order is deliberate.

**Updated 2026-09-04 for `OUTLINE-V2.md`.** v2 splits the results body in two — §5 by instrument
class, §6 by configuration axis — so D4 becomes **D4a** (§5) and **D4b** (§6), drafted in that
order. D5 is renumbered with it: as originally written it named "§6 Cost, §8 Practitioner appendix,
§9 Reproducibility appendix", section numbers v2 has reassigned. **§6 is now the configuration
axes**, instrument economics is **§5.8**, the conclusion is **§8**, and the appendices are
**lettered A–D**, not numbered. D6 and D7 now depend on D4b rather than on a single D4.

| # | stage | produces | depends on |
|---|---|---|---|
| **D0** | Style guide + figure programme | `STYLE-GUIDE.md`, `figures/**` | — *(in flight)* |
| **D1** | LaTeX skeleton + build | `tex/main.tex` compiling to an empty-sectioned PDF | D0 |
| **D2** | §3 Setup, §4 Method | the measurement contract: host, engines, arms, protocols, SSA | — |
| **D3** | §7 Threats to validity | the honest bound on every claim §5 may make | D2 |
| **D4a** | §5 Results — what the instruments can see, subsection by subsection | the evaluation body, each claim traced to a PN | D2, D3, figures |
| **D4b** | §6 Results — what the configuration axes do | the deployment body; drafted after D4a because §6.3 and §6.5 apply instruments established in §5.1 and §5.5a | D4a |
| **D5** | §5.8 instrument economics · Appendix A practitioner configuration · Appendix B reproducibility register | the practitioner payload | D4b |
| **D6** | §2 Background and related work | positioning, credit, novelty claim | D4b |
| **D7** | §1 Introduction | written last, because it promises what §5 and §6 deliver | D4a, D4b, D6 |
| **D8** | Abstract reconciliation | verify the fixed abstract against the drafted body | D7 |
| **D9** | Compliance + artifact pass | Zenodo DOI, SWHID, ancillary files, checklist | D8 |

**Rule for every stage:** a section is not done until every numeric claim in it names a PN entry,
and every table in it carries n, estimator, interval and protocol label *inside the table*.

---

## 4. Evidence discipline while drafting

The project's hard rules apply to prose exactly as they applied to measurement.

1. **Every number comes from an artifact, not from prose.** Nine notes in this corpus correct other
   notes; two documents that looked authoritative were stale. If drafting needs a number, read the
   artifact the PN names.
2. **Never mix protocols in a table.** Perplexity protocols 1/2/4 are different instruments.
   Depth-0 and at-depth decode differ 3–5×. Greedy and official-sampling rows are not comparable.
3. **Label every pre-2026-08-29 row** *irreproducible-on-current-images* (PN-57).
4. **A withdrawn claim is never silently dropped.** PN-30, PN-60, PN-61, PN-62 and PN-64 withdrew or
   scoped headline results on this study's own re-analysis. They appear in the paper as method.
5. **Underpowered results are reported as bounds, never as rankings.** The paper's own thesis; it
   must model the behaviour it advocates. Where a test could never have reached significance, say
   so and give the minimum attainable p.
6. **Append, never rewrite.** New findings during drafting become new PN entries and a ledger entry,
   not edits to old ones.

### Known open items that drafting must not paper over
- **PN-29's DFlash2 at-depth cell is unverified** for the PN-30 degenerate-generation defect and is
  cited in OUTLINE §5.4. Verify before §5.4 is drafted, or scope the claim.
- **Speed data wants re-analysis conditioned on draft acceptance** — both reviewers found decode
  regresses on acceptance at r² 0.83–0.99, collapsing the spread from 17–41 % to 3–11 %. §5.5 should
  explain the noise, not report it. Costs no GPU time.
- **No multiple-comparisons correction exists** across ~19 tests. All 11 positives survive Holm and
  BH, but the weakest separation does not survive Bonferroni under clustering. §7 must carry this.
- **Every evidence chain terminates in a serverlog `.gitignore` excludes.** Honest artifact claim is
  **Artifacts Available only** (R14), not *Functional*.

---

## 5. Figures — the PaperBanana route

Figures are required to be produced with **PaperBanana** (R11, arXiv 2601.23265). It generates
figures only and is **cloud-dependent**: OpenAI / Gemini / Atlas Cloud / Azure keys, **none
configured on this host**, and it is not installed here.

Therefore the pipeline is:
1. `figures/FIGURE-PROGRAMME.md` — every figure's claim, spec, encodings, caption and honesty
   constraints, precise enough to render without a follow-up question.
2. `figures/data/` — one CSV/JSON per figure, generated by `figures/extract.py` from committed
   artifacts, never hand-typed.
3. `figures/RENDERING.md` — how to render with PaperBanana once keys exist, plus verification.
4. Rendered vector PDFs land in `tex/figures/` and are referenced from `main.tex`.

**Design constraints:** a caption states the claim, not the axes. Overlapping intervals are drawn as
overlapping — PN-64's median row cannot rank the arms and must not be drawn as three separated
points. Protocol labels appear *in* the figure. Palette must survive greyscale and be colour-blind
safe.

---

## 6. What "done" means

- [ ] Every §5 claim traces to a PN entry; every table carries n, estimator, interval, protocol
- [ ] §7 written before §5 was polished, and still true of the drafted §5
- [ ] Withdrawn claims appear as method, not as absence
- [ ] Author block and §1 carry the independent-practitioner status explicitly
- [ ] Figures rendered from `extract.py` data, vector PDF, captions state claims
- [ ] LaTeX source compiles from a flat root; `anc/` carries the JSON artifacts
- [ ] Zenodo DOI and SWHID minted and printed in the paper
- [ ] Abstract ≤ 1,920 ASCII characters and true of the drafted body
- [ ] Endorsement secured
- [ ] `cs.LG` primary, `cs.PF` cross-list, ACM class `D.4.8; I.2.6`, CC BY 4.0
