# STYLE-GUIDE — how this report is written

**Scope.** This file governs the prose of the arXiv technical report drafted against
[`OUTLINE.md`](OUTLINE.md). It decides voice, density, section craft, sentence-level convention,
table and figure form, and how corrections and nulls are presented. It does **not** decide what the
report claims — [`../docs/paper/PAPER-NOTES.md`](../docs/paper/PAPER-NOTES.md) does that, and
`OUTLINE.md` decides where each claim goes.

**Status.** Written 2026-09-03, before drafting. Sources in §9. Where this guide and a reviewer
document disagree, the disagreement is named in place and a decision is given; do not silently
average them.

---

## 0. The five rules that override everything

If you internalise nothing else, internalise these. Every later section is an elaboration of one of
them.

1. **Every claim sentence carries its own bound.** The number, its `n`, and its interval — or the
   explicit reason it has none — live inside the sentence making the claim, not in a following
   sentence, not in a footnote, not in the caption. This is what lets the report be dense and honest
   at the same time: the hedging is *inside* the claim, so there is no second, weakening sentence.
   **This rule is not a preference; it is the one intervention with experimental support.** Budescu
   et al. found that readers systematically regress verbal uncertainty terms toward 50 % *even when
   a calibrated scale is supplied to them*, and that the only reliable correction is restating the
   numeric range alongside the word **at each point of use** [S46, S47]. A hedge ladder defined once
   in §4 and then used as bare vocabulary in §5 does not survive contact with a scanning reader.
   Write "±4.6 points at n = 164" beside every "indistinguishable", every time.

2. **The subject of a results sentence is the instrument, the measurement or the number — never a
   person, never a vague plural.** "Divergence separates every adjacent pair on code at 8.7–18.1 σ."
   Not "we find that…", not "it was found that…". This one rule resolves voice, density and
   register simultaneously (§1.3).

3. **Every section and subsection opens with its result, in one standalone sentence a reader can
   quote.** A reader arriving from a table of contents, a search engine or a link must get the
   finding in the first line and be able to leave. This is the load-bearing device that makes a
   30-page dense report navigable non-linearly (§2.5).

4. **Hedge strength tracks evidence strength, and both directions are errors.** Under-hedging an
   `n = 12` result and over-hedging a 12-sigma separation are the same failure. §4.6 is a ladder
   from "shows" to "is withdrawn"; use it mechanically.

5. **A caveat that changes the claim is not a caveat — it is part of the claim.** Write it into the
   main clause. Reserve riders and notes for provenance that does not change what the reader would
   conclude (§2.6).

---

## 1. Positioning and voice

### 1.1 The situation, stated plainly

One author. One machine. Twelve days. No lab, no cluster, no co-author, no institutional review, no
funding. The author is a professional master's candidate in Data Science and Analytics at the
Universidade de São Paulo, and the work was done independently of that programme.

Two failure modes are available, and both are fatal in this readership:

- **Apologising.** A report that opens by explaining what it is not, hedges every number, and calls
  itself "preliminary" trains the reader to discount measurements that are, in fact, better
  provenanced than most published ones. Excessive hedging does not read as modesty; it reads as
  the author's own low confidence, and a reader will not hold a claim more firmly than its author.
- **Borrowed institutional register.** "We hypothesise that our contributions…" on a single-author,
  single-host study collapses the moment a reviewer looks at the author block and the `n` column.
  It is the same category of error the report spends nine corrections repairing in its data: a
  register that overstates the evidence behind it.

**The resolution is not a tone. It is a structural commitment: the report claims exactly the
authority its artifacts support, sentence by sentence, and says so in the sentence.** A study that
attaches `n`, an interval and a protocol label to every number does not need to establish
credibility by voice, because it establishes it by construction. Once that discipline is in place,
being visibly a one-person study costs nothing — and *becomes an asset*, because a single operator
on a single pinned image can offer complete provenance that a multi-site study cannot.

This is empirically supported, not merely a hope. Altenmüller, Nuding & Gollwitzer (2021) found
across two experiments (N = 337, N = 365) that researchers who expressed self-criticism and reform
intentions were rated **higher** on epistemic trustworthiness and credibility than those who did
not, and that *denying* self-doubt produced measurable reputational harm [S12]. Clarke et al. (2024)
make the complementary craft point: what damages a paper is a limitations section that is vague,
boilerplate, or omits a constraint the reviewer would find anyway — not the existence of real
limitations [S13].

**And the comparator is favourable, which the drafter should know before writing a single hedge.**
The closest published analogue to this study — a single-author, unified evaluation of llama.cpp
quantizations, arXiv:2601.14277 [S26] — carries **no affiliation at all**, no limitations section,
no confidence intervals, and no discussion of seeds or variance. It is indexed, cited and
uncontroversial. This report has protocol labels, Wilson and bootstrap intervals, a quarantine
register, a determinism control, eighteen threats to validity and a claim index. **It is not the
weak entry in its genre; it is the strong one.** Write it accordingly. The register that fits is
neither deference nor assertion — it is the register of someone reporting numbers they are certain
of, at exactly the scope they hold.

### 1.2 The author block

Use this, verbatim, adapting only the contact line.

```
Divergence Ranks What Benchmarks Bound
Quantization, context and speculative decoding for a 27B coding model
on two 16 GB GPUs

Luiz Henrique Simões
Independent researcher
MSc candidate (professional master's), Data Science and Analytics,
Universidade de São Paulo
<contact>
```

Rules for the block:

- **"Independent researcher" is the affiliation line; USP is the second line and is a
  qualification, not a sponsor.** Never render it as `Luiz Henrique Simões, Universidade de São
  Paulo` — that asserts institutional backing the work does not have, and it is the single most
  damaging small dishonesty available here.
- Do **not** put "Independent Researcher" in parentheses or in a smaller font than the university
  line. It is the primary affiliation.
- No `*` / `†` markers, no "corresponding author" (there is only one author), no ORCID unless one
  exists — an empty scholarly footprint drawn attention to is worse than one not mentioned.
- The compact one-line form, for the arXiv metadata author field and for `CITATION.cff`:
  `Luiz Henrique Simões (Independent researcher; MSc candidate, Universidade de São Paulo)`.

**Page-1 footnote**, unnumbered, immediately under the author block:

> Technical report. Not peer reviewed. Artifacts: `<Zenodo DOI>` · code state: `<SWHID>` · engine
> image `sha256:feb0231976b6…`. Correspondence: `<contact>`.

That footnote does three jobs at once — status, artifact availability (arXiv requires a link that
resolves publicly [S1]), and the pin that makes every number in the paper attributable. It is eight
seconds of the reader's attention and it buys the rest of the document.

#### The arXiv metadata that carries the same signal

There is **no arXiv document type for "technical report"** — it is a register, signalled through
metadata [S25]. Four mechanisms are in use in this genre, and this report should use the first:

1. **The Comments field** — the conventional, cheap signal, and it also declares publication intent.
   Precedents: `Technical Report`; `Technical report. First Edition. April 18th, 2018. 66 pages`
   (the Volta microbenchmarking report, arXiv:1804.06826 [S27]); `Technical report: not intended for
   publication`. **Use:**
   `Technical report. NN pages, 6 figures, 5 tables. Artifacts: <DOI URL>`
2. Title prefix (`Technical Report: …`) — a stronger commitment, suited to documentation work.
3. Title suffix (`…, A Technical Report`).
4. Nothing at all — which is what the most influential single-author systems report in this corpus
   does (FlashAttention-2, arXiv:2307.08691 [S28]). Not recommended here, because the owner's
   honesty requirement is explicit.

Two metadata mechanics that will otherwise cost a resubmission [S5]:

- **Affiliations in the author metadata go in parentheses** and take city and country only —
  `Luiz Henrique Simões (Independent Researcher, São Paulo, Brazil)`. No honorifics, no degree
  suffixes, no street address.
- **The `Report-no` field cannot be used.** arXiv restricts it to "your institution's locally
  assigned publication number"; a self-issued report number does not qualify.

### 1.3 Pronoun: **first-person singular, used sparingly; the editorial "we" is banned**

**Decision. The report uses "I" for acts of judgement and decision; the default subject of a
measurement sentence is the instrument, the metric or the configuration; the harness takes an
agentless past for procedural acts. "We", "our" and "us" do not appear.**

#### Why

Machine-learning convention is overwhelmingly "we", including in single-author papers, and a
drafter's instinct will be to follow it. Follow it here and the report writes "we measure a 27B
coding model" under an author block with one name, about a host with one operator, in a document
that discloses in §3 that the campaign was agent-executed under one person's direction. Every
reader who notices takes a small, cheap credibility hit off the paper — and this readership
notices, because noticing is what it does for a living.

The style authorities agree and the corpus evidence agrees:

- APA Style is explicit that a solo author uses "I", that there is no rule against first-person
  pronouns, and that the editorial "we" meaning "people in general" is separately discouraged as
  vague (*Publication Manual*, 7th ed., §4.16; and the style team's own blog post exists precisely
  because the opposite belief is a persistent myth) [S14, S15].
- Corpus work on first-person pronouns in research articles finds "we" is disciplinary convention
  rather than a semantic necessity, and that its use is a rhetorical positioning choice authors
  make, not a grammatical requirement [S16].

But the decisive argument is internal. **This report's thesis is that an instrument must be scoped
to what it can support.** A plural voice for a singular study is the same error in the register that
PN-40 is a correction of in the statistics: a form that implies more backing than exists. A paper
that makes that argument in §5 and commits the analogous error in every sentence of §5 is not
credible, and a reviewer who spots it will say so in one line.

#### The three-way sorting rule

Decide the subject of every sentence by what the sentence reports.

| the sentence reports | subject | example |
|---|---|---|
| a measurement, a number, a behaviour of the system | **the instrument, the metric, the configuration** | "Mean KL divergence separates every adjacent pair on code at 8.7–18.1 σ." |
| a choice, a judgement, a scope decision, a withdrawal, a refusal | **I** | "I use UD-Q6_K_XL as the reference arm because no FP16 checkpoint fits the host." |
| a procedural act performed by the harness under supervision | **agentless past** | "Each cell was launched with `-fit off`, and its reported `n_ctx` was asserted against the request." |

The third row is not evasion. The measurement campaign *was* executed by an agent-driven harness
(§1.6); writing "I ran 65,536 tokens through `llama-perplexity`" would be less accurate than the
passive, not more. Reserve "I" for the things a human actually did, and it stays informative.

Expected frequency: **"I" should appear roughly once or twice per page** — often enough that the
report is unmistakably one person's work, rare enough that it never reads as memoir. If a page has
five, the sentences are about the author when they should be about the measurement. If a page has
none across §4, §7 or §9, judgements are being hidden behind the passive.

#### Worked conversions

| ✗ | ✓ |
|---|---|
| We measure a 27B coding model across four GGUF quantizations. | I measure a 27B coding model across four GGUF quantizations. *(abstract; a decision to study something is a judgement)* |
| We find that divergence separates the arms. | Divergence separates the arms at 8.7–18.1 σ on code. |
| Our results show the ceiling is set by the split. | For two of the four arms the tensor split, not the quantization, sets the reachable window. |
| We were unable to measure KL divergence at depth. | KL divergence at depth is not measurable on this host: the tool holds a chunk's logits resident and 14 GiB caps it at `n_ctx` 8,192. |
| We believe this is because the corpus is highly predictable. | The code corpus has a reference perplexity of 1.18 against WikiText-2's 5.79, so the argmax token is usually obvious and survives quantization while the distribution around it moves. |
| We withdraw this claim. | An earlier revision reported 16.8 tok/s at `n-max 4`; that measurement timed 17 generated tokens rather than 192, and it is withdrawn. |
| As we can see in Table 3… | Table 3 … *(cross-reference, no verb of seeing)* |
| We note that Q4_K_XL loads at the default split. | UD-Q4_K_XL loads at the default split, so the claim holds for two of the four arms measured. |

#### The one hard case

Sentences that would naturally take a reader-inclusive "we" — "we now see that PPL averages away
the signal". Rewrite with the object as subject: "PPL averages the signal away." The
reader-inclusive "we" is the weakest construction in scientific prose in any case; losing it is a
gain.

### 1.4 The §1 status statement

**Placement: the final paragraph of §1, after the contributions list and immediately before §2.**
Not the first paragraph — a report that opens with what it is not has spent its strongest position
on a disclaimer. Not §7 either — a reader who discovers on page 16 that this was one person on one
machine feels managed, and retro-discounts everything above it. At the end of §1 it arrives after
the reader already knows what was measured, so it reads as scope, which is what it is.

**Form: state the constraint, then state what the constraint bought.** Every honest limitation in
this study has a compensating design decision behind it, and that pairing is what converts a
limitation from an apology into a method statement. Use this text as the base:

> This is a technical report and it has not been peer reviewed. It was designed, run and written by
> one person on one machine — a dedicated two-GPU consumer host — across twelve days of measurement
> between 2026-08-29 and 2026-09-02, independently of any institution. The constraints that follow
> are load-bearing rather than incidental: 14 GiB of system RAM is why no FP16 reference exists and
> why every divergence here is a distance along a ladder rather than from an unquantized model
> (§7.1); a single operator is why sample sizes are what they are; and the cost of GPU time on one
> host is why the report measures cost per answered question at all, which turned out to be one of
> its results. What a single host buys in exchange is provenance: every number traces to a named
> artifact produced by one pinned engine image on identical hardware, nothing is averaged across
> machines whose differences were not measured, and the full measurement record — including nine
> corrected findings and three withdrawn claims — is released rather than summarised.

**Then, in the same position, a compact "what this report does not show" block** — eight lines,
bulleted, promoted from `README.md`. This is progressive disclosure applied to limitations: the
reader meets the honest scope on page 3 in eight lines, and §7 gives the full eighteen on page 16.
A reader who has met the short version does not feel ambushed by the long one; a reader who has met
only the long one, late, feels sold to.

Note what that paragraph does with the resource constraint: it makes it **causal and specific** —
14 GiB is *why* there is no FP16 reference — rather than general and apologetic. That move has
formal backing. Resource constraints are one of six recognised legitimate sample-size
justifications, and in equivalence testing "the maximum sample size you are willing to collect
implicitly determines your SESOI" [S64, S11]. **"GPU hours were the binding constraint" is a
methodological position with a citation, not a confession.** Write it once, here, cite it, and never
apologise for it again in the document.

**What the status statement must not do:**

- Ask for allowance. No "given these constraints, we hope the reader will…".
- Compare itself to better-resourced work. No "unlike large industrial labs, we…". The comparison
  invites the reader to make it too.
- Use "only", "just", "merely", or "small-scale" about its own measurements. `n = 65,536` tokens per
  cell is not small; `n = 12` at the deepest RULER rung is, and that gets said where it is true.
- Claim novelty for the constraint. Running on consumer hardware is the *setting*, not a
  contribution. It becomes a contribution only where it produced a finding — the per-card VRAM
  limit, the tensor-split result — and there it is stated as a finding.

### 1.5 The AI-conduct disclosure

arXiv requires disclosure of significant use of generative tools, holds the author fully
responsible regardless of how text was produced, and forbids listing such tools as authors [S1].
Every entry in `PAPER-NOTES.md` is signed by a model and the ledger records agent-driven execution,
so this is not optional and cannot be discovered-in-the-artifacts rather than stated.

Write it once, in §3, as a provenance statement rather than a confession:

> The measurement campaign was executed by an agent-driven harness under my direction. I designed
> the protocol, approved each experiment before it ran, and am responsible for all content
> including every error. The decision log, ledger and per-finding notes recording that process are
> released with the artifacts, so the chain from an instruction to a number is inspectable at every
> step.

Same rhetorical move as §1.4: constraint, then what it bought. Almost no paper can offer a complete
instruction-to-number chain; this one can, and the disclosure is where it says so.

### 1.6 Register rules

- **Assert, then bound. Never bound, then assert.** "Divergence separates every adjacent pair on
  code at 8.7–18.1 σ; the weakest prose adjacency, 3.71 σ, does not survive Bonferroni under a
  design effect of 1.5 and is not used for ranking." Not: "Although our analysis has limitations,
  we tentatively suggest that divergence may separate…".
- **No throat-clearing.** Delete "It is important to note that", "It should be emphasised that",
  "In this section we will", "As mentioned previously". Each is a sentence that says a sentence is
  coming.
- **No epistemic inflation.** "Novel", "state-of-the-art", "significant" (as a synonym for "large"),
  "dramatically", "crucially", "importantly". If a result is important, its number says so.
- **No community-flattering plural.** "The community has long known", "practitioners widely
  believe". Name who, with a citation, or delete.
- **Cite for the specific claim, not for the topic.** A citation attached to a sentence must support
  that sentence. This matters here because §2 is a moderation-risk section (§3.2).
- **Contractions: none.** Not a formality point — the report is read by non-native speakers and
  parsed by search; contractions cost nothing to remove.
- **British or US spelling: pick one and state it in a comment at the top of the LaTeX source.** The
  corpus is currently mixed ("summarise" alongside "analyzed"). US is the arXiv-cs default; either
  is fine; inconsistency is not.
- **Never anthropomorphise the model in a claim sentence.** "The model prefers", "the model
  understands" — replace with what was measured. Acceptable in a mechanism paragraph if flagged:
  "the reasoning block competes with the answer for the 128-token budget" is fine because closure
  was measured.

### 1.7 Phrases to avoid, with the honest alternative

| avoid | why | write instead |
|---|---|---|
| "we hypothesise that our contributions…" | borrowed register; the reader checks `n` | "This report's four contributions are:" |
| "extensive experiments demonstrate" | "extensive" is unfalsifiable; "demonstrate" overclaims | "Across 19 inferential tests over 12 days of measurement, …" |
| "no significant difference was found" | absence of evidence stated as evidence of absence [S9] | "bounded at −0.61 points, 95 % CI […]; the exact test could not have reached p < 0.25 at 3 discordant pairs" |
| "results are preliminary" | discounts the work without informing | name the specific limit: "measured at one seed, one context length, one engine image" |
| "future work will address" | promises nothing checkable | "A re-run at a generous `n_predict` with thinking disabled would settle this; it costs about 40 minutes and was not done." |
| "to the best of our knowledge, the first" | invites a five-minute refutation | "I found no published measurement of X on this hardware class; the nearest is [cite]." |
| "our approach is superior" | not a claim this study makes | "Divergence separated the arms where three task instruments bounded them." |
| "small-scale study" | self-discounting and imprecise | state the actual `n` for the instrument under discussion |
| "obviously", "clearly", "of course" | if it were obvious the sentence would be unnecessary | delete |
| "arguably", "it could be argued" | argues with nobody | state the claim, or the counter-claim, and its evidence |
| "significantly" (non-statistical) | collides with the statistical sense in a statistics-heavy paper | "by 6.74 %", "by 3 points" |
| "proves", "conclusively" | nothing here proves anything | "separates", "bounds", "is consistent with" |
| "cannot" (of an instrument) | PN-60 is this report's own counter-example — the instrument *did* see something, on another construct | "does not resolve", "bounds rather than resolves", "did not separate the arms on this construct" |
| "state-of-the-art hardware" / "modest hardware" | value-laden | "2× RTX 5060 Ti 16 GB, no NVLink, 180 W cap" |
| "the model was confused" | anthropomorphism in a claim | "the reference arm did not close its reasoning block on 23 of 100 items" |
| "as expected" | either the expectation was pre-registered, or this is hindsight | "consistent with the pre-registered band (DEC-11)" or delete |
| "unfortunately" | editorialises a measurement | delete |
| "note that", "we note that" | throat-clearing | delete; keep the content |

---

## 2. Density without exhaustion

The owner's instruction is that the write-up must not compress the corpus: twelve days of GPU time
produced 64 evidence notes, and summarising them away wastes the measurement. That instruction is
compatible with clarity, but only if the report stops trying to be read once, front to back, by one
kind of reader. **The technique is not compression. It is layering.**

### 2.1 Three readers, one document

Design every section for all three at once. This is the whole method.

| reader | what they do | what they need | where they stop |
|---|---|---|---|
| **The scanner** (most readers) | reads title, abstract, section openers, table captions, the limitations box | one sentence per section that is true and quotable | never opens a table |
| **The practitioner** | arrives from a search for "Q6_K 262144 tensor split" | the number, its conditions, and the command | §5.3, Appendix A |
| **The checker** (reviewer, replicator, sceptic) | wants to break a specific claim | `n`, estimator, interval, protocol, artifact path | Appendix C, D and the artifact |

A section that serves only the checker is unreadable. A section that serves only the scanner is
the compression the owner has forbidden. Progressive disclosure serves all three from the same
material [S17, S18].

### 2.2 The four-layer rule

Every result subsection is written in four layers, in this order, and a reader may stop after any
of them with a correct (if less complete) understanding.

1. **The claim sentence** — one sentence, standalone, containing the headline number, its `n`, and
   its bound. Quotable out of context; true out of context.
2. **The evidence paragraph** — 80–150 words. The comparison, the interval, the scope. Where the
   caveats that change the claim live, in-clause.
3. **The table or figure** — the full numbers, with a note line naming protocol, `n`, estimator and
   interval type. The scanner skips it; the practitioner reads only it.
4. **The appendix or artifact pointer** — one sentence, e.g. "Full sweep in Appendix C, Table 11;
   per-cell JSON at `data/raw/e12/tsweep-v2-Q5_K_XL.json`."

The mechanism paragraph, where one exists, sits between 2 and 3. Mechanism is what earns a
measurement paper its citations, and it is the part most often cut for space; cut layer 4 first,
then table rows, and never the mechanism.

### 2.3 What belongs where

| content | prose | table | figure | appendix | artifact only |
|---|---|---|---|---|---|
| ≤ 3 numbers carrying one argument | ✔ | | | | |
| ≥ 4 numbers, or any 2-D structure (arm × domain) | | ✔ | | | |
| the *shape* is the claim (monotonicity, a crossover, a distribution) | | | ✔ | | |
| a full parameter sweep (10 ratios × 4 arms) | | | | ✔ | |
| per-repetition raw readings | | | | | ✔ |
| an interval, an `n`, an estimator name | ✔ always, in the sentence | ✔ always, in the note | ✔ in the caption | | |
| a protocol label | ✔ | ✔ | ✔ | ✔ | ✔ |
| a defect that changed a published number | ✔ where the number is | | | ✔ full register | |
| a defect that changed nothing | | | | ✔ | |
| a command line the reader may run | | | | ✔ verbatim | |

**Two rules that keep this from bloating:**

- **A number appears in exactly one table.** If it must appear again, the second occurrence is a
  cross-reference (`Table 3`), not a repetition. Repeated numbers drift; three intervals for the
  same paired difference are already circulating in this project's own planning documents (§6.4).
- **A table that is only read by the checker belongs in an appendix.** The body carries the table
  that supports the argument; the appendix carries the one that survives an audit.

### 2.4 The paragraph contract

Every body paragraph obeys one of three shapes. Mixing them inside a paragraph is what makes dense
prose exhausting.

- **Claim paragraph.** Sentence 1 is the claim with its number and bound. Sentences 2–4 are the
  comparison, the scope and the contrast. No new claims after sentence 1.
- **Mechanism paragraph.** Sentence 1 names the mechanism. The rest gives the quantity that makes it
  a mechanism rather than a story. Ends with what the mechanism predicts, so it is falsifiable.
- **Procedure paragraph.** Agentless past, chronological, no claims. Belongs in §3 and §4 and
  nowhere else.

**Three to seven lines is the right paragraph length** [S48], which at this line width is roughly
60–130 words. If a paragraph exceeds that it is doing two jobs; split it at the seam. The
first clause of every paragraph is privileged — readers scan the top-left of each block before
anything else [S49, S50] — so the number goes there, not in the middle of sentence three.

This is Mensh & Kording's context–content–conclusion scheme applied recursively [S21]: it holds at
the scale of the report, the section, the paragraph and the sentence, and applying it at all four
scales is what makes dense material feel orderly rather than relentless.

### 2.5 Navigability: writing for the reader who arrives in the middle

Long dense documents are read non-linearly, and information that is only available in reading order
is lost [S18].

- **Section openers.** §5.3 opens with "For two of the four arms measured, the tensor split rather
  than the quantization set the reachable context window." Not "In this section we examine context
  ceilings." The opener is the section's abstract.
- **A finding is never introduced by its evidence.** Result first, method second, always. The reader
  who leaves after one sentence must leave with the finding, not with the protocol.
- **Every subsection number in §5 maps to exactly one claim in the abstract or the contributions
  list.** If §5.6 supports no contribution, either it is a contribution or it belongs in an
  appendix. This mapping is also what a moderator uses to decide the report is research and not a
  survey (§3.2).
- **Repeat the protocol label, not the caveat.** A reader landing in §5.6 needs to know they are
  reading Protocol 1 numbers; they do not need the full averaging-bias argument again. Tag, then
  cross-reference: "[Protocol 1; §4.2]".
- **Forward references are allowed; backward assumptions are not.** "…and §7.4 gives the clustering
  correction" is a service. "…as established above" is a trap for a reader who arrived here from a
  search engine.
- **The claim index (Appendix D) is a navigation device, not bookkeeping.** One row per headline
  number: number → §, PN, artifact path, serverlog. A checker starts there. Say so in §1 so they
  find it.

#### Devices that are verified conventions — and one that is not

I had these checked against the HTML of ten long ML papers rather than assumed. **Boxed "Takeaway"
callouts are not a convention in ML survey or empirical papers** — none of four major
LLM-efficiency surveys uses them. Do not adopt one on the belief that it is standard. What *is*
used, and works:

1. **A §1.1 "Summary" of findings as bolded run-in headings.** Kaplan et al.'s scaling-laws paper
   states eight findings this way — each a complete claim as a bold lead-in, followed by two or
   three sentences [S51]. A reader gets the entire result set in two minutes. **This is the single
   best structural device available to this report** and it should carry the four contributions plus
   the five instrument bounds.
2. **The same results restated as reference tables at a second depth.** Kaplan repeats the findings
   in a "Summary of Scaling Laws" subsection *and* in an appendix table. Appendix C and Appendix D
   are this report's equivalent, and the duplication is the point: it is what serves the non-linear
   reader.
3. **A named "Caveats" appendix.** Kaplan's Appendix C is titled exactly that and is a bulleted list
   of things the authors are not confident about. This is precedent for keeping G13–G23-class open
   gaps visible rather than dissolving them into §7 prose.
4. **A roadmap that separates what could be measured from what was measured.** HELM's §2.4 does this
   explicitly, distinguishing "what is fundamentally possible vs. what we, as a specific collective
   of benchmark designers, chose to prioritize and emphasize" [S52]. **One sentence in that shape
   converts the cancelled Wave 2 and Wave 4 from absences into stated scope decisions** — which is
   exactly what they are.
5. **Labelled inline callouts, sparingly.** The vLLM anatomy writeup uses four labels — *Note*,
   *Assumption*, *Additional notes*, *Advanced notes* — and states its method as an "inverse-pyramid
   approach: starts broad and then layers in detail" [S53]. The two labels this report needs are
   **Assumption** and **Protocol**; more than two becomes furniture.
6. **A table of contents at both ends of a long document** [S53]. In LaTeX, `\tableofcontents` after
   the abstract; the claim index (Appendix D) serves as the closing one.
7. **A separate "Recommendations" section from the "Limitations" section.** Dettmers & Zettlemoyer
   split §7 Recommendations & Future Work from §8 Discussion & Limitations, and add an Appendix B
   *Further negative results* [S54]. That split maps exactly onto this project's Track A / Track B
   separation and onto S10/S11.

### 2.6 How a caveat attaches to a claim

The rule from §0: **a caveat that changes the claim goes in the main clause.** Everything else uses
one of three lighter attachments, and the choice is determined by what the caveat does.

| the caveat… | attachment | example |
|---|---|---|
| changes who or what the claim covers | **in-clause scope**, grammatically inseparable | "**For two of the four arms measured**, the tensor split set the reachable window." |
| bounds the number itself | **em-dash rider** immediately after the number | "82.75 / 82.25 / 82.75 / 83.25 % — a 1.0-point spread inside ±7.4-point intervals" |
| names the protocol or instrument condition | **bracketed tag** | "6.6511 ± 0.04111 [Protocol 1, n = 602 windows]" |
| records provenance without changing the claim | **terminal sentence** or **table note** | "Measured on the pre-2026-08-29 image; labelled *irreproducible-on-current-images* throughout." |
| is a reproducibility warning of interest only to a replicator | **appendix / claim index** | — |

**Never a footnote for a caveat that changes the claim.** Footnotes are for provenance, DOIs and
version pins. A scope condition in a footnote is a scope condition the reader will not apply.

**Caveat budget: at most one in-clause scope per sentence.** Two produces the cascade that makes
careful writing unreadable. If a claim genuinely needs two scopes, it is two claims — split it, and
the second one is usually the more interesting.

### 2.7 Worked before/after, from this report's own material

**A — the hedge cascade (§5.2, HellaSwag).**

> ✗ We attempted to measure the effect of quantization using a multiple-choice benchmark. It should
> be noted that our sample size was limited. HellaSwag was run at n = 400 on all four arms. The
> results were 82.75 %, 82.25 %, 82.75 % and 83.25 %. Unfortunately these differences were not
> statistically significant. It is possible that with a larger sample a difference might have been
> detected. We therefore cannot draw strong conclusions from this experiment. *(78 words, 5 hedges,
> 0 mechanisms, ends weaker than it started)*

> ✓ HellaSwag at n = 400 scores the four arms 82.75 / 82.25 / 82.75 / 83.25 % — a 1.0-point spread,
> with the most-quantized arm nominally highest. The paired analysis on the identical task set is
> the informative one: UD-Q6_K_XL and UD-Q5_K_XL answer all 400 items identically, and no pair
> disagrees on more than four items. More items would narrow the intervals and change nothing.
> Multiple-choice scoring resolves an argmax over four candidates, so it is insensitive by
> construction to a perturbation that leaves the argmax intact — and divergence measures exactly
> that perturbation, at 3.7× between these same two arms on code prompts. *(102 words, 0 hedges, 1
> mechanism, ends on a quantity)*

The rewrite is *longer* and *denser* and reads faster, because every clause carries a number and
nothing carries an apology. This is the whole density technique in one example.

**B — caveat cascade (§5.3, ceilings).**

> ✗ UD-Q5_K_XL reaches 262,144 tokens at five tensor-split ratios and fails at the default split.
> This shows that the ceiling is a property of the split rather than of the quantization. However,
> it should be noted that UD-Q4_K_XL loads at the default split. It should also be noted that each
> default-split failure was only attempted once, whereas this project's protocol calls for two
> attempts. *(59 words; the claim is asserted, then twice retracted)*

> ✓ For two of the four arms measured, the tensor split rather than the quantization set the
> reachable window: UD-Q5_K_XL and UD-Q6_K each fail to load at 262,144 tokens under the engine's
> default layer split and load at a swept ratio, while UD-Q4_K_XL loads at the default and
> UD-Q6_K_XL was never attempted there. Each of those load failures is a single attempt against a
> bracketing rule of two — cheap to replicate, and not replicated. *(72 words; the claim is stated
> once, at its true scope, and never retracted)*

**C — the null that is actually a bound (§5.2, generative anchor).**

> ✗ The generative coding benchmark found no significant difference between the ladder's extremes
> (McNemar p = 1.0).

> ✓ Across the full width of the ladder the two extreme arms agree on 161 of 164 HumanEval+
> problems. The paired difference is −0.61 points, 95 % CI [−3.28, +2.06] (Wald interval on the
> paired proportion difference; 5 discordant pairs). The exact McNemar test could not have returned
> p < 0.0625 at that discordance under any outcome, so no p-value is reported: the informative
> statement is that a 3.69× increase in code-prompt divergence moves HumanEval+ pass@1 by at most
> about three points.

**D — the field-claim opener that reads as a position paper (§1).**

> ✗ The machine-learning community relies heavily on task benchmarks to certify quantized models.
> This reliance is problematic, because…

> ✓ Two hours and nine minutes of divergence measurement separated four quantizations of the same
> 27B coding model at 8.7–18.1 σ on code. Four hours and forty-eight minutes of task benchmarking
> separated them nowhere.

The second version says the same thing and is a *measurement*, which matters beyond style: arXiv's
cs moderation now refuses review and position papers without prior peer review [S3, S4], and the
first sentence of the abstract and of §1 are where a moderator decides which kind of document this
is.

**E — precision beyond the instrument (§5.1; this is PN-64's lesson).**

> ✗ At the median, code tokens are perturbed 100–200× less than prose tokens (0.01× / 0.01× /
> 0.005× by arm).

> ✓ At the median, code tokens are perturbed by roughly two orders of magnitude less than prose
> tokens. The per-arm ratios are not reported: `llama-perplexity` prints six decimal places, so the
> code medians carry one to two significant figures, and propagating half-ULP bounds gives per-arm
> intervals that overlap. The ordering visible in that row is an artifact of rounding.

### 2.8 Length budget

The corpus is 64 notes and the instruction is not to compress it. Reviewer B's 9,000–10,500-word
body is achievable only by dropping notes, so it is superseded here. Budget:

| part | words | pages (single column) |
|---|---|---|
| §1 Introduction | 1,100 | 2 |
| §2 Background and related work | **≤ 900** (hard cap — see §3.2) | 1.5 |
| §3 Setup, harness validation, conduct disclosure | 900 + Table 1 | 2 |
| §4 Method (SSA) | 1,000 + Table 2 | 2 |
| §5 Results (5.1–5.7) | 5,200 + 5 tables, 5 figures | 10 |
| §6 What the measurements cost | 500 | 1 |
| §7 Threats to validity | 1,400 | 2.5 |
| §8 Conclusion | 350 | 0.75 |
| **body total** | **≈ 11,350** | **≈ 22** |
| Appendix A Practitioner configuration | 700 | 1.5 |
| Appendix B Reproducibility register | 1,100 | 2 |
| Appendix C Full tables | 600 + tables | 3 |
| Appendix D Claim index | 400 + table | 2 |
| **total** | **≈ 14,150** | **≈ 30** |

Thirty pages is long for cs.LG and normal for a measurement report. The layering in §2.2 is what
makes it navigable; without it, do not attempt this length.

**Budget the reader's time honestly.** Silent non-fiction reading averages about 238 words per
minute across 190 studies [S79], so ≈14,150 words is roughly **an hour** of continuous reading — and
essentially nobody will spend it. That is the argument for §2.2's layering, not against the length:
the scanner spends four minutes on openers and captions, the practitioner ten on §5.3 and Appendix
A, the checker twenty on Appendix C and D, and each of them gets a correct understanding. A report
that can only be read in one hour-long pass has one reader; a layered one has three.

---

## 3. Section-by-section craft notes

Each entry gives: **what the section must accomplish · its opening move · its characteristic failure
mode · length.** Section numbers follow `OUTLINE.md`; see §3.9 for the numbering change this guide
recommends.

### 3.0 Title and abstract — the two things most readers will read all of

**Title.** The chosen title is:

> *Divergence Ranks What Benchmarks Bound: quantization, context and speculative decoding for a 27B
> coding model on two 16 GB GPUs*

It is 20 words. The empirical literature on titles is genuinely mixed and mostly discipline-driven
[S34, S35], so no rule here is strong — but two things are supported and one is a live risk:

- **The colon-subtitle pattern is well supported.** Non-alphanumeric characters in titles, colons
  and hyphens in particular, correlate positively with citation impact [S36]. Keep it.
- **A question title would be a mistake.** Question titles are downloaded more and cited less
  [S37]. The rejected T8 (*"Which GGUF for a Coding Agent on 2× 16 GB?"*) was right to lose.
- **20 words is long.** The empirical-SE primer recommends ≤ 15 including articles and prepositions
  [S32]. A compliant trim that loses nothing the abstract does not immediately supply:
  > *Divergence Ranks What Benchmarks Bound: quantization and context for a 27B coding model on two
  > 16 GB GPUs* — 17 words; drops "speculative decoding", which is contribution 5 rather than the
  > thesis.
  This is the owner's call; the current title is defensible and the risk is small. Do not add to it.

**Abstract.** Hard limit **1,920 characters**, ASCII only, no LaTeX macros, and carriage returns are
stripped unless followed by leading whitespace — so an abstract that looks structured in the PDF
will run together in the metadata field unless deliberately indented [S5]. Practical target:
250–280 words.

Craft rules, all supported by the genre convention and by the sources:

1. **Numbers, and a lot of them.** Every close analogue in this subfield puts hard counts in the
   abstract, and the empirical-SE primer states it as a rule: include concrete numbers and sample
   sizes so a reader can judge the extensiveness of the study immediately [S32].
2. **Unstructured single paragraph, in Context → Objective → Method → Result → Conclusion order.**
   No labelled headings; no ML-systems paper in the surveyed corpus uses them.
3. **Open on a measurement, not on a claim about the field** — the S3 moderation consideration
   (§3.2), and the first thing a moderator reads.
4. **Close on a scope sentence that tells the reader how far the result generalises.** The best
   model found in this genre, and directly adaptable to this study's engine-image and split-mode
   confounds [S38]:
   > "Results should be interpreted as platform-level deployment characterisations for a single
   > model and prompt type, reflecting hardware and software combined, rather than general claims
   > about hardware capability alone."

   Adapted: *"These are measurements of one quantization ladder under one engine image on one
   two-GPU host, and every ceiling reported is a property of that combination rather than of the
   quantization alone."* This sentence does more for the report's honesty than any disclaimer, and
   it costs 40 characters of the abstract budget.
5. **Double-bound any superlative or priority claim**, or drop it. The convention in this corpus is
   "to the best of our knowledge" *plus* a time qualifier, or a downgrade to "one of the first".
   This report should simply not make one.
6. **Convert the current draft to first-person singular** (§1.3). Reviewer D's A2 opens "We measure
   a 27B coding model…"; it becomes "I measure a 27B coding model…". `CITATION.cff` carries the
   same sentence and must change with it.

### 3.1 §1 Introduction — 1,100 words

**Must accomplish.** (a) Establish that this is a measurement report, in the first two sentences.
(b) State the practitioner question. (c) State the four contributions as falsifiable claims with
numbers. (d) Credit Dutta et al. [R13] in the second paragraph so priority is settled before a
reviewer raises it. (e) Scope the study, including the status statement and the short
"does not show" block.

**Opening move.** A measured contrast, in numbers, in the first sentence. See §7 for a full draft.

**Failure mode.** Opening with a claim about the field. It reads as a position paper — a document
class arXiv cs now refuses without prior peer review [S3, S4] — and it makes the contributions look
like arguments rather than measurements. Second failure mode: contributions written as capabilities
("we present a protocol for…") rather than as results ("divergence separates the arms at …; three
task instruments bound the same comparison at …").

**Contributions list: four, each one sentence, each with a number and a bound.** Never five with one
weak; a reviewer discounts the whole list to the weakest member.

### 3.2 §2 Background and related work — **≤ 900 words, hard cap**

**Must accomplish.** Position four things and nothing else: (i) KL divergence as the instrument and
the case against perplexity's averaging bias [R1, R2, R4, R10]; (ii) the nearest published
neighbours and where they disagree with each other [R5, R7, R9]; (iii) the prior this report
confirms independently [R13]; (iv) the published claims this report's measurements contradict —
speculative-decoding losslessness [R12] and the long-context recovery band [R9] — flagged as
*motivation and comparison*, never as refutation of the algorithms themselves.

**Opening move.** A sentence about what the field measures, immediately followed by what it does
not disclose. One sentence of context, then straight to the gap.

**Failure mode — and this one has teeth.** A long, even-handed §2 makes the report look like a
survey, and arXiv's cs category has, since 2025-10-31, required review and position papers to carry
documentation of prior peer review or be rejected [S3, S4]. The countermeasure is structural:
**every paragraph in §2 ends with a sentence naming what this report measures differently.** Related
work as positioning, not as coverage. Simon Peyton Jones's advice to put related work at the end
[S19] is the stronger form of the same instinct; §2 stays where the outline puts it, but it obeys
the spirit — it exists to make the contributions legible, not to survey a field.

**Do not** cite a work you have not read to the level of the claim you attach to it. §2 is the
easiest place in the report to lose the credibility §1 just earned.

### 3.3 §3 Setup — 900 words + Table 1

**Must accomplish.** Host, engine pinned by image digest, four arms with sha256 and sizes, the
provenance discipline (`env-manifest.json`). Then two subsections that are *results*, not
preamble: the harness-validation gate (PN-1…PN-4) and the AI-conduct disclosure (§1.5). Then the
artifact-availability statement (§3.10).

**Opening move.** The constraint that produced the study: two 16 GB cards without NVLink are not a
32 GB pool, and under `--split-mode layer` each layer's weights *and its KV slice* live on one card,
so the binding limit is per-card.

**Failure mode.** Writing PN-1…PN-4 as housekeeping. They are the reason every downstream number was
produced under an asserted contract — measured sampling defaults matching neither the documented
engine defaults nor either official preset is a finding, and it is the finding that licenses the
rest of the report. 200 words, framed as results.

PN-31 is a **two-sentence footnote** to the host spec, per owner direction, keeping one
generalisable clause: *the standard divergence tooling's resident footprint scales with context
length, which is itself why the published quantization tables it produces are all measured near 2K.*

### 3.4 §4 Method — the Small-Sample Accuracy protocol — 1,000 words + Table 2

**Must accomplish.** The design principle, once and clearly: **divergence instruments draw power
from token count; task benchmarks draw it from problem count.** Then the reference-arm choice and
its ladder-relative consequence, the 65,536-token budget, and the pre-registered interpretation
bands declared as external reference points rather than adopted rules.

**Opening move.** The design principle, stated as one sentence, before any protocol detail.

**Add the subsection the outline lacks: "What is reported, and what is refused."** 150 words, three
rules, and this is the report's methodological spine:
1. Every table names its protocol, its `n` and its estimator, in the table.
2. A comparison is reported as an interval or an equivalence bound; a p-value appears only where the
   test could have reached significance, and the minimum attainable p is stated when it could not.
3. A claim enters only if the interval separates or the effect exceeds the interval width;
   otherwise it is reported as bounded, with the bound.

Rule 2 is what makes §5.2 a result instead of a null, and it must be declared *before* §5 so that
the reader meets it as method rather than as a defensive move. All three rules have external
backing — test selection [S89], variance sources that must be randomised or declared [S7, S90],
few-run reporting via stratified bootstrap and interquartile mean rather than point estimates
[S91], and the general statistical-practice rules that variability must be assessed and assumptions
checked [S44].

**The pre-registered interpretation bands (DEC-11) are worth naming as such.** Preregistration in
ML has a venue and a stated rationale — that reliance on performance as a proxy for progress
incentivises omitting the negative results encountered along the way [S97] — and the distinction it
turns on is the one this report needs: predictions tested versus postdictions generated. Report the
confirmatory analyses as confirmatory and everything else as exploratory, with intervals and
without significance claims.

**Failure mode.** Reciting protocol steps that belong in an appendix. §4 explains why the design
gives power, not how the script runs.

PN-26 (byte-level determinism) belongs here as well as in §5.4: it is the *enabling* result for
every byte-level comparison in the report, and it is under-placed if it appears only as a
speculative-decoding finding.

### 3.5 §5 Results — 5,200 words

**Must accomplish.** Seven subsections, each an independently readable unit obeying §2.2's four
layers. This is the section that must survive non-linear reading.

**Opening move for §5 as a whole.** One short orienting paragraph — three sentences — naming the
five instrument classes and what each is for. Not a summary of results; a map. Then §5.1 begins
immediately.

**Per-subsection notes:**

- **§5.1 The ladder and the domain** (900 w · Fig 1, 2 · Table 3). Leads with the three-tier
  hierarchy and the monotone separations. Carries PN-16's metric-pair argument as *mechanism*: top-1
  agreement and mean KLD disagree about which domain is hurt, and a top-1-only table inverts the
  conclusion. **PN-64's precision correction applies here** — state the median contrast as "roughly
  two orders of magnitude" and do not tabulate it per arm (§2.7E). **PN-62's scoping applies here
  too**, and it is the section's best moment: the tail's *shape* is a corpus property, its
  *magnitude* is a quantization property, and the study has the control that separates them.
  *Failure mode:* presenting the quantile table as the headline without the control, which is the
  version an adversarial reader breaks in ten minutes.

- **§5.2 What the task instruments bound** (1,200 w · Fig 3 · Table 4). **The report's centre.** Do
  not use a count in the heading — the supporting evidence is five-wide (multiple choice,
  generative, retrieval, SWE-bench Verified, corpus perplexity), and a heading that says "three"
  and a section that lists five is exactly the class of error this report is about. Every instrument
  is presented as a *bound*, with the bound. *Failure mode:* letting any of the five read as a
  failure of the study rather than a measurement of the instrument. The framing test: could this
  paragraph be read as "we could not find an effect"? If yes, rewrite until it reads as "this
  instrument resolves no finer than X."

- **§5.3 What sets the reachable window** (700 w · Fig 4 · Table 5). Physical mechanism first (no
  NVLink; per-card binding limit), then the scoped claim, then the non-monotone `-ts` optimum. Cite
  Heiser's benchmarking crime on unfair-competitor configuration [S20] to justify per-arm winning
  ratios as the methodologically correct comparison. *Failure mode:* stating the unscoped version
  from `README.md`; PN-39 scoped it and the scoped version must be the one in the body.

- **§5.4 Speculative decoding is part of the accuracy configuration** (750 w · Fig 5). Non-identity
  at greedy (131/164), then the determinism control upgrading it to *deterministically*
  non-equivalent. *Failure mode:* reading as a refutation of DFlash or of speculative decoding in
  general. It is a per-stack verification claim: "losslessness is a property to verify per stack",
  never "the algorithm is not lossless".

- **§5.5 Speed does not discriminate** (500 w). **Explain the noise, do not merely report it.**
  Decode regresses on draft acceptance at r² = 0.83–0.99, and conditioning on acceptance collapses
  within-configuration spread from 17–41 % to 3–11 %. *Failure mode:* using a null under high
  variance as a finding in §5.5 while criticising exactly that inference in §5.2. Say the noise is
  an upper bound and that a greedy re-measurement would tighten it.

- **§5.6 KV-cache quantization is not free** (400 w). The PPL-vs-KLD contrast on the identical pair
  is the report's cleanest self-contained demonstration of averaging bias: PPL moves +0.15 % while
  the distribution demonstrably moves. *Failure mode:* the "51 % of a quantization level" phrasing
  read as additive currency; PN-43 qualifies it as a size comparison.

- **§5.7 Systems and energy** (300 w). Short. Energy is modelled, not measured — say so in the
  first sentence, not the last.

### 3.6 §6 What the measurements cost — 500 words

**Must accomplish.** The measured cost contrast from the artifacts: 2.15 h of divergence against
≈4.8 h of task benchmarking. **The power ratio carries the point, not the cost ratio** — 2.1 hours
separated the arms; 4.8 hours bounded them and separated nothing.

**Opening move.** The corrected numbers, immediately, with the withdrawal of the old contrast in the
same paragraph (§6.2's Pattern 1).

**Failure mode.** Reaching for the retired "20 minutes vs 20 hours". It is falsifiable from the
repository in five minutes and its withdrawal is more persuasive than the original ever was.

### 3.7 §7 Threats to validity — 1,400 words

**Must accomplish.** Eighteen items, ordered by what an informed reader attacks first, not by topic.
Every item names the artifact that bounds it and, where one exists, the cost of removing it.
Reviewer D's draft (`review/reviewer-d-adversarial.md` §6) is the base text; adopt its ordering.

**Separate limitations from threats, in two labelled groups** [S32]. The distinction is not
cosmetic and this report needs it, because it has an unusual number of the first kind:

- **Limitations** are *conscious scope decisions*. One model family. Two single-domain corpora. The
  cancelled breadth wave. The temperature > 0 equivalence test not run. Each of these is a choice
  with a stated reason, and it is reported as a choice: "the presence-penalty probe was cancelled
  under DEC-12; the consequence is that the equivalence result stays greedy-only."
- **Threats** are *issues that are hard to mitigate and that could move a number*. The
  ladder-relative reference. The memorised code corpus. The token-independence assumption behind
  the intervals. The single engine image. Each of these is reported with what bounds it and how
  much it would have to be wrong to change a conclusion.

Grouping them this way is itself a signal of calibration: a reader can see at a glance which
constraints were chosen and which were endured, and it stops the eighteen items reading as one
undifferentiated list of excuses.

**Opening move.** The strongest objection to the report's headline, stated in the reader's own
words, in the first sentence. Clarke et al.'s "steel-person principle": state the best argument
against your conclusion, not a weaker one you can answer [S13].

**Form for each item — four moves, in one short paragraph:**
1. The threat, in the strongest form a critic would state it.
2. What bounds it — a number, a control, an invariance argument.
3. What survives, precisely scoped.
4. What it would cost to remove it, when that is knowable. "A second held-out code corpus is the
   single most valuable missing measurement in this study and would cost approximately one
   GPU-hour" is worth more than three paragraphs of qualification, because it is checkable and it
   tells the next person what to run.

**Failure mode.** Boilerplate. An item that could appear in any paper ("results may not generalise
to other models") is worse than no item: it dilutes the seventeen that are specific [S13]. Second
failure mode: writing §7 last, after §5 has been polished — the outline and this guide both require
§7 written first, because a threat discovered while polishing gets softened.

**Do not** end §7 on the weakest item. End on item 18, the compounding question: whether damage
confined to a small fraction of token positions compounds over a long-horizon agentic trajectory is
unmeasured, including here, and it is the natural next experiment. Naming the paper's own principal
open problem, precisely, is the move most likely to get it cited.

### 3.8 §8 Conclusion — 350 words · **this section does not currently exist in the outline**

**Must accomplish.** Three sentences of result, one of consequence for practice, one of open
problem. Nothing new; no new numbers; no restating of the abstract.

**Opening move.** The result that survived everything: divergence ranked the ladder; five task
instruments bounded it; the instrument decides whether there is anything to see.

**Closing sentence.** Use this shape:

> Quantization damage here is real, tail-concentrated on code and domain-amplified. At the
> single-turn scale these benchmarks measure, its effect is bounded small. Whether it compounds over
> a long-horizon agentic trajectory — where a model makes thousands of decisions and each is a draw
> from a perturbed distribution — is the question that matters, and it is unmeasured, including
> here.

**Failure mode.** A summary. A conclusion that recapitulates is a second abstract and readers skip
it; a conclusion that names the open problem gets cited by whoever runs it.

### 3.9 §§9+ Appendices — and a numbering change

`OUTLINE.md` currently runs §7 Threats → §8 Practitioner appendix → §9 Reproducibility appendix,
which leaves the report with **no conclusion** and with appendices numbered as body sections.
Renumber:

| now | recommended |
|---|---|
| §8 Practitioner appendix | **§8 Conclusion** (new, §3.8) |
| §9 Reproducibility appendix | **Appendix A** Practitioner configuration |
| — | **Appendix B** Reproducibility register |
| — | **Appendix C** Full tables |
| — | **Appendix D** Claim index |

**Appendix A — Practitioner configuration (700 w).** `TRACK-A-DECISION.md`, compressed, framed as
*what this analysis implies for one concrete deployment* and explicitly not the report's
recommendation. Include Amendment 2 and the reverted draft-depth flag as one paragraph — a worked
example of a withdrawn claim, not three paragraphs of process.

**Appendix B — Reproducibility register (1,100 w).** Twelve entries, grouped under the three
families the outline already identifies, and unified by one thesis stated in the first sentence:
*silent success is the dominant failure mode of automated benchmarking.* Each entry is written as a
trap another group would fall into, in the general first and the instance second. *Failure mode:*
writing it as confession. The register is a contribution; frame it as one and it will be the most
re-used part of the report.

**Appendix C — Full tables (600 w + tables).** Every percentile, the full `-ts` sweep,
per-repetition decode figures, and the `variable_tracking` exclusion with its reasoning. An honest,
well-argued exclusion should be *visible*, not buried in a JSON field.

**Appendix D — Claim index (400 w + table).** Number → § → PN → artifact path → serverlog. This is
the report's best answer to "we cannot check this", and it is cheap: the mapping already exists.

### 3.10 The artifact-availability statement

Its own short subsection at the end of §3, and repeated in the page-1 footnote (§1.2).

Claim **ACM *Artifacts Available* only, and say why not *Functional*** [S24, R14]:

> Artifacts are deposited at `<DOI>` and the exact code state at `<SWHID>`; the engine image is
> pinned by digest. This meets ACM's *Artifacts Available* criteria, which require an archival
> repository with a DOI and explicitly do not require completeness. It does **not** meet *Artifacts
> Evaluated — Functional*, whose criteria include completeness: every finding's evidence chain
> terminates in a server log excluded from the release for size, so the chain cannot be walked
> end-to-end from the public artifact alone. 72 server logs are cited in this report and 0 are
> released. *Results Reproduced* is unattainable by construction — the engine image that produced
> the pre-2026-08-29 corpus no longer exists.

Four verified details make this paragraph defensible rather than merely modest [S24]:

- **The three badge families are independent.** ACM's own text: "These badges are considered
  independent and any one, two or all three can be applied to any given paper." Claiming one is not
  a partial claim on the others.
- **Available explicitly tolerates incompleteness.** Verbatim: "Artifacts do not need to have been
  formally evaluated… In addition, **they need not be complete in the sense described above.**"
  That single sentence is the authority for depositing a partial artifact set honestly, and it
  should be paraphrased in the report so a reader does not read the gap as a failure.
- **Personal web pages are not acceptable** for Available — an institutional repository, Zenodo,
  figshare or Dryad is required. The private git remote is not a release.
- **v1.1 inverted v1.0's terms.** ACM adopted NISO's recommendation and "swap[ped] the terms
  'reproducibility' and 'replication'". Cite v1.1 and name the version, or a reader working from an
  older paper will read the claim backwards.

Naming the tier you *do not* claim, with the specific criterion you fail and the count, is worth
more than a badge. It is also the single clearest demonstration in the report of the behaviour it
advocates.

**When re-running is impossible, preserved evidence of the original run is the accepted
substitute.** That is not a local rationalisation: artifact-evaluation guidance for tools that
cannot be redistributed or that need more than 24 hours of execution accepts a detailed record of
the original run in place of a runnable artifact [S55], and cTuning's reviewing guide states
plainly that "the variation of empirical and numerical results is tolerated. In fact it is often
unavoidable in computer systems research" [S56] — which covers this host's ±100–200 MiB layer-split
noise. The logs-before-teardown rule is exactly the practice those guidelines describe; say so.
The general condition — software becoming unrunnable because its environment moved — has a name,
*software collapse* [S57], and using it converts "the image is gone" from an embarrassment into an
instance of a documented phenomenon.

---

## 4. Sentence-level conventions

### 4.1 Numbers

- **Token counts and context lengths in full, with thousands separators**: `262,144`, `65,536`,
  `131,072`. Never `262K` in a claim sentence. `K` is permitted on a figure axis and in a table
  header where width binds, and must be defined once in the caption.
- **Never print more digits than the instrument prints, and never derive a quantity at higher
  precision than its inputs.** PN-64 is this report's own cautionary instance: a "100–200×" range
  was the reciprocal of a rounded `0.01×` table cell, and the per-arm ordering it implied was an
  artifact of six-decimal print precision. When in doubt, propagate half-ULP bounds and report the
  order of magnitude. This has a name in the systems literature — SIGPLAN's empirical-evaluation
  checklist lists **"Inappropriate level of precision"** as a distinct flaw: "reporting '49.9 %'
  when the experimental error is ±1 % overstates the level of precision" [S72]. Cite it beside
  PN-64's correction; it converts an internal embarrassment into a recognised category.
- **KLD**: 6 decimal places, matching the tool. **Ratios**: 2 significant figures unless the inputs
  support more. **Percentages**: 1 decimal. **Throughput**: 2 decimals (`11.90 tok/s`).
- **Percentage points vs percent.** A difference between two percentages is in *points*: "−0.61
  points", "a 1.0-point spread". A relative change is a percent: "+0.15 %". Getting this wrong in a
  statistics-heavy paper is expensive.
- **Ranges use an en-dash and repeat the unit only once**: `8.7–18.1 σ`, `3.13–4.40×`,
  `0.41–0.55`.
- **A ± is never bare.** Either `0.003321 ± 0.000126 (tool-reported standard error, n = 65,536
  tokens)` or a bracketed interval with its estimator named.

### 4.2 Units

- **Binary units for memory as the tools report them**: `MiB`, `GiB`. **Decimal for file sizes as
  the vendor publishes them**: `21.98 GB`. State this convention once, in §3, in one sentence — the
  mixture is correct and will otherwise read as an error.
- `tok/s` lowercase, always with a depth qualifier in a claim sentence: `11.90 tok/s at 95 % window
  depth`. Depth-0 and at-depth throughput differ 3–5× and must never share a table.
- `σ` with a thin space, defined once at first use: *the separation between two arms in units of the
  pooled standard error of their means, as reported by the instrument*, with the Gaussian assumption
  and the clustering caveat stated in the same sentence.
- Wall-clock in `h`/`min`, never decimal hours in prose (`2 h 9 min`, not `2.15 h`) — decimal hours
  are fine in a table.

### 4.3 `n`, always, and its unit

`n` is attached to every estimate, and **its unit is named**, because the unit differing by
instrument is one of the report's method points:

- `n = 65,536 tokens` (divergence)
- `n = 164 problems, paired` (generative)
- `n = 400 items` (multiple choice)
- `n = 12 samples` (RULER, deepest rung)
- `n = 3 repetitions` (throughput)

Never a bare `n = 400`. Never "a large sample" or "sufficient samples".

### 4.4 Intervals

- **Always name the estimator in the sentence or the table note.** "95 % CI [−3.28, +2.06] (Wald
  interval on the paired proportion difference)". "Wilson score interval". "Bootstrap percentile
  interval, B = 10,000, seed 20260825".
- **One estimator per quantity, across the whole report.** Three different intervals for the same
  paired HumanEval+ difference are currently circulating in this project's planning documents (§6.4);
  pick one, state it in §4, and never mix.
- **Report the interval, not the p-value, for every paired comparison.** A p-value appears only when
  the test could have reached significance; where it could not, state the minimum attainable p
  instead (§6.3).
- **Report the minimum detectable effect as a designed result**, not as an apology: "at 400 items
  and the observed discordance, the smallest detectable difference was larger than any difference
  the instrument could produce." MDE-as-reporting-convention has an origin worth citing [S62], and
  its guard-rail is equally important: **never report observed (post-hoc) power computed from your
  own result** — that is a known fallacy [S63]. A design-stage MDE is a result; a post-hoc power
  number attached to a non-significant p is not.
- **Justify the sample size, and "GPU hours were the binding constraint" is a legitimate
  justification with a name.** Lakens enumerates six defensible sample-size justifications, two of
  which describe this study exactly: *resource constraints*, and *explicitly acknowledging the
  absence of a justification* [S64]. And in equivalence testing, "without practical boundaries or
  theoretical boundaries that indicate which effect size is meaningful, the maximum sample size you
  are willing to collect implicitly determines your SESOI" [S11]. **This converts the report's most
  awkward sentence — one operator, finite GPU time — from an apology into a cited methodological
  position.** Write it that way in §4 and §7 and never apologise for it again.
- **If the abstract concludes that two arms are equivalent, the abstract must also carry the
  equivalence bounds** used to reach that conclusion [S11]. This report's abstract says the task
  instruments "bound the whole ladder's effect at about three points"; that is the bound, and it is
  correctly placed.

### 4.5 Protocol labels

Perplexity Protocols 1, 2 and 4 are different instruments and must never share a table; depth-0 and
at-depth decode differ 3–5×; greedy and official-sampling rows are not comparable; pre-2026-08-29
rows come from a deleted engine image.

- **Define the labels once**, in a short table in §4, and use the label thereafter.
- **Every number in a table, figure caption and comparison sentence carries its label**:
  `[Protocol 1]`, `[SSA]`, `[at-depth]`, `[greedy]`, `[irreproducible-on-current-images]`.
- The last of these is not optional and not a footnote. A pre-2026-08-29 row without it is a defect.

### 4.6 Hedging calibrated to evidence strength

Hedging is not weakness. In the corpus linguistics of scientific writing it is a purposeful
pragmatic resource by which a writer matches a claim to the warrant behind it, and hedges and
**boosters** ("clearly", "demonstrate", "in fact") form a single continuum on which both directions
can be miscalibrated [S81]. Two of Salager-Meyer's five hedge families are useful here — *shields*
(`may`, `suggest`, `indicate`) and *approximators* (`approximately`, `roughly`) — and one is banned
outright: **compound hedges** of the form "it would seem reasonable to assume that…" [S80].

The stakes are not stylistic. Randomised evidence shows that readers rate a treatment more
favourably when given a "spun" abstract than when given an accurately hedged rewrite of the same
result, and spin appears in 37.5 % of Results sections and 58.3 % of Conclusions reporting
non-significant primary outcomes [S82]. Miscalibration misleads; it does not merely read badly.

Use the licensed verb for the evidence you have. This is mechanical; do not improvise.

| evidence | licensed | example |
|---|---|---|
| non-overlapping intervals, stated `n`, protocol declared | **separates · is · shows** | "Divergence separates every adjacent pair on code." |
| a measured bound whose interval contains zero | **bounds … at · moves by at most · resolves no finer than** | "bounds the ladder-wide effect at about three points of pass@1" |
| significant, but on a construct other than the intended one | **measures X, not Y** (say both) | "separates the arms on budget closure, not on retrieval" |
| direction consistent, intervals overlapping | **orders … without separating · is consistent with** | "orders the ladder correctly by a margin smaller than its own uncertainty" |
| a mechanism with a numerical prediction, prediction met | **predicts · explains** | "damage confined to 1–5 % of positions predicts the 3-of-164 discordance observed" |
| a mechanism without a measurement | **would imply — and is unmeasured** | never *shows*, never *suggests* on its own |
| `n = 1`, a single attempt, no replication | **one attempt · not replicated** | never *shows*; state the attempt count in the clause |
| an inference from a deleted image or lost provenance | **recorded as · labelled KV-UNKNOWN** | never a bare assertion |
| a claim this report has withdrawn | **was reported as X; that measurement … and is withdrawn** | §6.2 |

**Banned in both directions:** *suggests, seems to indicate, may potentially, tends to* (too weak to
be checkable); *proves, demonstrates conclusively, establishes definitively, cannot* (stronger than
any evidence here).

**And the failure mode this report is most exposed to has a name.** Lipton & Steinhardt's four
troubling trends include *conflating explanation with speculation* and *failure to identify the true
source of an empirical gain* [S83]. Both are live here: PN-23's mechanism for speculative
non-equivalence is explicitly not established, and the throughput comparison was ratio-confounded
until PN-42 and PN-45. **Where a mechanism is a hypothesis, label it one in the sentence** — "the
partial overlap of the divergence sets is consistent with float non-determinism from a changed
decode batch shape; the mechanism is not established, and a no-spec repeat control would settle it"
— and the report gains from naming the failure mode it avoided. The companion rule from the ML
pitfalls literature is the general form: **do not generalise beyond the data** [S85], and a
non-significant result never means the null is true [S86].

### 4.7 Tense

| context | tense | example |
|---|---|---|
| what was done | past | "Each cell ran 65,536 tokens through `llama-perplexity`." |
| what the data shows | present | "Divergence separates every adjacent pair on code." |
| what the system does | present | "Speculation produces a reproducibly different decode path." |
| prior work's claims | present | "Dutta et al. report that accuracy metrics hide compression damage." |
| prior work's procedure | past | "Red Hat measured a 4-bit recovery band of 85–88 % at 128K." |
| a withdrawn claim | past + explicit withdrawal | "An earlier revision reported 16.8 tok/s; that measurement timed 17 generated tokens and is withdrawn." |
| what a future experiment would do | conditional + cost | "A re-run at a generous `n_predict` would settle it, at about 40 minutes of GPU." |

### 4.8 Naming things consistently

- **Arms**: `UD-Q6_K_XL`, `UD-Q6_K`, `UD-Q5_K_XL`, `UD-Q4_K_XL` — full Unsloth names, code font,
  everywhere. Not "the 4-bit arm" in one section and "Q4" in another. "the cheaper arm" /
  "the reference arm" is allowed *once the arm has been named in the same paragraph*.
- **Model**: `Qwen3.8-27B` at first use in each section; "the model" thereafter within the section.
- **Flags and paths in code font**, always: `-ts 58,42`, `-fit off`, `--split-mode layer`,
  `data/raw/e12/ssa/ssa-results-parsed.json`.
- **Instruments by their real names**: `llama-perplexity --kl-divergence`, HumanEval+ (EvalPlus),
  RULER S-NIAH / MK-NIAH, HellaSwag, SWE-bench **Verified** (never bare "SWE-bench" — Qwen publishes
  on Pro and the two are not comparable).
- **The host is `multivac`** and is named once, in §3; thereafter "the host".

### 4.9 The abbreviation budget

This project has a large internal vocabulary — `PN-*`, `L-*`, `DEC-*`, SSA, MTP, DFlash2, `-ts`,
`-ctxcp`, S-NIAH, MK-NIAH, KLD, `q4_0`, TOST — and every one of them is a token the reader must
hold. Acronym density in NeurIPS titles rose roughly tenfold between 1987 and 2024 while abstract
readability fell by half, and 89 % of coined acronyms are used fewer than ten times [S29]. That is
the failure mode to avoid.

- **Coin nothing new.** Every abbreviation in the report must already name a real thing — a flag, a
  file, a published benchmark, a standard statistic. No new capitalised method names.
- **An abbreviation used fewer than five times is expanded every time and never abbreviated.**
- **`PN-*` and `L-*` do not appear in the body at all.** They are internal identifiers; the reader
  meets a claim, and the claim index (Appendix D) carries the PN mapping. Putting `(PN-35)` in a
  results sentence tells the reader nothing and costs them a lookup they cannot perform.
- **"SSA" (Small-Sample Accuracy protocol) is expanded at every section boundary** — a reader
  arriving at §5.6 has not read §4.
- Flags stay in code font and are never abbreviated further: `--split-mode layer`, not "SM-layer".

---

## 5. Tables and figures

### 5.0 Six performance-reporting rules this report is bound by

Hoefler & Belli's twelve rules for scientific benchmarking [S30] are the closest thing this genre
has to a standard, and six of them bite here. Treat them as constraints, not advice.

| rule (verbatim) | where it binds |
|---|---|
| **1.** "one should never report ratios without absolute values" | every speedup, every `×`, every "51 % of a quantization level". The KV-cache claim must carry `0.002955 ± 0.000127` beside the 51 %; the tail ratios must carry the underlying medians and percentiles |
| **2.** "Specify the reason for only reporting subsets of standard benchmarks… report all results, not just the best" | two of RULER's thirteen tasks were run and one of those excluded; the `-ts` sweep stopped at the first ratio that loaded for one arm (PN-13's estimator problem). Both must be stated where the result is, and the `variable_tracking` exclusion must be visible (Appendix C) |
| **4.** "Avoid summarizing ratios; summarize the costs or rates that the ratios base on" | the code÷prose divergence ratios are the report's headline. Report the underlying per-domain KLDs in the same table, and never average a ratio across arms |
| **5.** "Report if the measurement values are deterministic. For nondeterministic data, report confidence intervals" | the greedy instruments *are* deterministic and this report has the byte-level control to prove it — say so explicitly, because it is unusual and it is what makes the paired comparisons attributable. The throughput measurements are not, and carry n = 3–6 against a 40.7 % spread |
| **8.** "Carefully investigate if measures of central tendency… are useful… Some problems may require other percentiles" | this is the report's own headline finding stated as a reporting rule by an external authority. Cite it in §5.1 |
| **9.** "Document all varying factors and their levels as well as the complete experimental setup… to facilitate reproducibility" | Table 1 and the per-table note line (§5.3). Engine image digest, split mode, `-ts` ratio, KV dtype, `-ctxcp`, sampling block — all of them are varying factors in this study and all have moved a number |
| **12.** "Only connect measurements by lines if they indicate trends and the interpolation is valid" | the decode-vs-depth curve has three points for one configuration (PN-14's gap). Plot the points; do not draw the curve |

Hoefler's companion list for deep-learning workloads [S31] contains one item worth naming in the
report: *"Show performance when enabling option set A and show accuracy when enabling option set
B!"* — which is precisely what the "never mix protocols in a table" rule guards against, and it is
worth one citation in §4 to show the rule is a recognised standard rather than a local preference.

**Four further external anchors, each of which turns a local rule into a cited one.** Use them; a
solo report gains disproportionately from showing that its fastidiousness is the field's standard
and not the author's temperament.

| this report's rule | external anchor |
|---|---|
| depth-0 and at-depth decode never share a table | Raasveldt et al. name **"Cold vs Hot Runs"** and **"Cold vs Warm Runs"** as two of eight standard database-benchmarking pitfalls [S73]. The 32,768-context speed table quoted as long-context throughput is that pitfall exactly. Their **"Overly-Specific Tuning"** pitfall is likewise the frame for the `-ts` caveat |
| bracket and re-test every ceiling; single failures lie | Mytkowicz et al. showed that measurement bias from apparently irrelevant environmental factors — link order, environment size — can exceed the effect being measured [S74]. This is the citation for the ±100–200 MiB allocator-layout noise |
| every table names its protocol; instruments are never mixed | MLPerf's results-messaging rules forbid comparing MLPerf results "against non-MLPerf results" and require any comparison to "clearly identify any difference in version, division, category, verified or unverified status, scenario or chip count" [S75]. An industry standards body formally prohibits exactly what this rule prohibits |
| a spread is not a difference | Reimers & Gurevych found that comparing single test scores of **two identical systems** produces type-I errors in up to **26 %** of cases at p < 0.05 [S76]; seed choice alone moves NER F₁ by about a point [S88]. The single strongest number available for refusing to rank on point estimates |

One more, which is an alternative rather than an anchor: Bouthillier et al. recommend deciding
superiority not on mean performance but on a **probability-of-outperforming criterion, P(A > B) ≥ γ
with γ = 0.75** [S7]. If §5.5 wants to say something stronger than "the arms do not separate on
throughput", that is the instrument to say it with, and it is computable from the existing
repetition data at no GPU cost.

### 5.1 Which to use

- **Table** when the reader needs the *values*: ceilings, KLD by arm × domain, the instrument
  inventory, per-arm intervals.
- **Figure** when the reader needs the *shape*: the quantile crossover between p90 and p95, the
  monotone three-tier hierarchy, decode-vs-depth, acceptance-vs-draft-depth. If a figure's message
  survives being read as four numbers, it should have been a table.
- **Prose** when three numbers carry an argument that a table would fragment.
- **Never both.** A figure that duplicates a table wastes a page and creates two numbers to keep in
  sync.

Six figures and five tables in the body is the budget; everything else goes to Appendix C.

Two operational rules from the technical-writing style guides, both directly applicable [S78, S48]:

- **"Analytic minds tend to love tables. Given a page containing multiple paragraphs and a single
  table, engineers' eyes zoom towards the table."** For this readership the table is not a
  formatting choice, it is where attention lands first — which is why §5.3's note line is mandatory
  and why the caption must carry the claim.
- **"If a table cell holds more than two sentences, ask yourself whether that information belongs in
  some other format."** A caveat that will not fit in a cell belongs in the note line or the prose,
  not squeezed into a column.
- A table is right for "three or more related pieces of information per item"; a list is right below
  that; and never use a table to present a list of similar items.

### 5.2 Captions state the claim

**A caption is a sentence with a verb, asserting what the reader should take away. It is not a
label.** Many readers read only captions; a caption that names axes has told them nothing.

> ✗ **Figure 1.** KL divergence quantiles by arm and domain.
> ✓ **Figure 1.** Code-to-prose divergence crosses unity between the 90th and 95th percentile on all
> three arms: below it, code tokens are perturbed far less than prose; above it, far more. Ratios of
> per-token KL divergence, `n = 65,536` tokens per cell, reference arm `UD-Q6_K_XL` [SSA]. The
> median row is not shown — print precision does not support it (§5.1).

> ✗ **Table 4.** Task benchmark results.
> ✓ **Table 4.** Every task instrument bounds the ladder-wide effect; none resolves it. Paired
> differences with 95 % intervals where a pairing exists, and the minimum attainable exact p where
> the discordance count made significance unreachable.

Captions go **above tables, below figures**, and each is self-contained — a reader arriving from a
search engine meets the figure with no context. The outline-from-figures method and the argument
that captions carry the paper are Whitesides' [S22]; the operational version is Irene Zhang's rule
for systems papers: **state each conclusion three times — as a hypothesis at the start of the
section, as a result at the end of it, and in the caption beside the graph** [S42]. In a document
being read non-linearly that is not redundancy, it is three independent entry points to the same
finding.

Zhang's companion rule governs §3 and §4: *"Clearly state the set up for every experiment. So many
papers miss this. How many times did you run the experiment? For how long? State every data object
size!"* — which is Hoefler's Rule 9 in a practitioner's voice.

### 5.3 The table note line is mandatory

Every table carries a note (use `threeparttable`) naming, in this order:

> instrument · protocol label · `n` and its unit · estimator · interval type · engine image digest ·
> artifact path

This is one of the repository's own hard rules and it is also what separates this report from the
vendor benchmarks it implicitly criticises. A table without its note line is not ready.

### 5.4 Table construction

- `booktabs` only; no vertical rules; no `\hline`.
- `siunitx` `S` columns to decimal-align estimates against interval bounds.
- **Column order: identity → condition → estimate → uncertainty → `n` → protocol.** Uncertainty is
  never further from the estimate than one column.
- Rows sorted by the ladder (`UD-Q6_K_XL` first, as reference), never by outcome — sorting by
  outcome invents a ranking.
- **A cell that is not measured says so** (`—`, with the note explaining), never `0`, never blank.
  `UD-Q6_K_XL` at the default split at 262,144 was never attempted; that cell must read *not
  attempted*, not *fail*.

### 5.5 Figures

Figures are produced with PaperBanana [R11] on a keyed machine, so each needs a written spec and a
source CSV under `manuscript/figures/data/`, both released with the artifacts.

- Vector PDF for every line plot.
- **Never encode the only distinction in colour** — pair colour with marker or dash so the figure
  survives greyscale printing and colour-vision differences.
- Axis units and `n` on the axis label, not only in the caption.
- **Annotate the claim on the figure itself** — a reference line at ratio 1.0 with the label
  "crossover, p90–p95" does more than a paragraph.
- Check each rendered figure against its source CSV before submission; a figure produced on another
  machine from a description is a place where a number can silently change.

---

## 6. Presenting corrections and nulls

This study corrected nine of its own notes and withdrew or scoped several headline claims — PN-30,
PN-60, PN-61, PN-62, PN-64 — on its own re-analysis, mostly at zero GPU cost, after the measurements
were complete. **That is the report's strongest single credibility asset and it must be shown, not
buried.** The evidence that this works is direct: self-criticism and expressed reform intentions
*raise* rated trustworthiness and credibility, and denying self-doubt lowers them [S12].

Three further pieces of evidence settle the question of whether this is safe, and the drafter should
know them before deciding how visible to make the corrections:

- **Reviewers are explicitly instructed not to punish it.** The NeurIPS paper checklist addresses
  the fear directly: "We understand that authors might fear that complete honesty about limitations
  might be used by reviewers as grounds for rejection. It is worth keeping in mind that a worse
  outcome might be if reviewers discover limitations that aren't acknowledged in the paper…
  **Reviewers will be specifically instructed to not penalize honesty concerning limitations.**"
  [S65]
- **Almost nobody does it, which is why it signals.** Across 316 surveyed researchers, roughly 12 %
  reported a qualifying loss of confidence in their own published work — and "the loss of confidence
  was a matter of public record in fewer than a fifth of the reported cases (17 %)" [S66].
- **In the venues that specialise in this, it is a reviewable merit.** The "I Can't Believe It's Not
  Better" workshop series lists among its review criteria "**Vulnerability and honesty in
  discussion, particularly if the submission is by the original author**" and "Quality of discussion
  of limitations" [S67].

But there is a real limit, and it is a craft problem: **if every third sentence self-corrects, the
report reads as unstable rather than careful.**

### 6.1 The disclosure budget

**At most one correction disclosed in the body per subsection**, chosen as the one that changes what
the reader would otherwise conclude. Everything else goes to Appendix B and the claim index. In
practice that means roughly six corrections in the body — §5.1 (PN-64 precision, PN-62 scoping),
§5.2 (PN-60 withdrawal), §5.3 (PN-39 scoping), §5.5 (PN-45 estimator), §6 (PN-41 cost), Appendix A
(Amendment 2) — and the rest in the register.

**A correction is placed where the corrected number is**, in the same paragraph, not only in an
appendix. A reader who meets a number in §5.1 and its correction on page 26 has been managed; a
reader who meets both together has been informed.

### 6.2 Six rhetorical patterns

**Pattern 1 — Correction in place** (a number moved; the finding stands). Four moves, three
sentences: original claim → defect → corrected number → what survives.

> ✓ PN-64, §5.1: An earlier revision of this analysis reported the median code-to-prose ratio as
> "100–200×" from a table rounded to two decimal places. Recomputed from the committed quantile
> extracts, the measured ratios are 199 / 181 / 206×, and the "100" was the reciprocal of a rounded
> `0.01×` cell rather than a measurement. The median contrast is therefore reported here as roughly
> two orders of magnitude and is not tabulated per arm: at six printed decimal places the code
> medians carry one to two significant figures, and half-ULP propagation gives per-arm intervals
> that overlap. Eighteen of the twenty cells in that table reproduce exactly, including the
> crossover, which is the finding.

Note the shape: the correction is *specific*, it names the mechanism of the error (rounding), it
states what still holds and how much (18 of 20 cells), and it ends on the finding rather than the
error.

**Pattern 2 — Withdrawal** (the claim is gone). Five moves: what was measured → what it was reported
as → why that reading fails → what separates instead → what is now **unanswered, not answered
negatively**.

> ✓ PN-60, §5.2: The multi-key retrieval battery at 131,072 tokens was reported as a 10-point
> retrieval gap between the reference and the four-bit arm, exact McNemar p = 0.002. It is not a
> retrieval result. The harness ran a 128-token output budget with reasoning enabled, so every
> generation is a reasoning block competing with the answer for the budget: across all fourteen
> cells of the battery, `closed-and-wrong` is exactly zero — every failure in both arms is a
> truncation. Restricted to the 55 of 100 items where neither arm's budget bound, both arms score
> 55/55 with zero discordance. What does separate is budget closure — 77 against 60, discordance
> 22/5, exact McNemar p = 0.001514 — which is a reasoning-verbosity effect measured at depth, not a
> retrieval effect. Retrieval at 131,072 tokens is therefore **unanswered here, not answered
> negatively**: nothing in these data forecloses either outcome, and a re-run at a generous
> `n_predict` with thinking disabled would settle it. The same defect is why `variable_tracking` was
> excluded from this battery, and the budget check that justified retaining the needle tasks was run
> at `n_ctx` 8,192 on the easier variant and never repeated at 131,072.

The last sentence is the one that converts the withdrawal into method. It says the study's own
exclusion criterion should have caught this, names why it did not, and hands the next reader the
generalisable lesson. **Withdrawals that end on "and here is the trap" are contributions;
withdrawals that end on "we were wrong" are apologies.**

**Pattern 3 — The bound, never the null.** Never "no significant difference". Always the interval,
and — where the test lacked the power to reach significance at any outcome — the minimum attainable
p, stated as a property of the design. §2.7C is the worked example. This is the report's own
instance of the error it attributes to the field, and saying so in the body is worth more than
hiding it in the register [S6, S9, S10].

Two refinements worth adopting. First, **distinguish "too noisy to say anything" from "actively
indicates the effect is undetectably small"** [S87] — that distinction is exactly what separates
PN-40's corrected reading from PN-28's original one, and it is the difference between a study that
failed and a study that bounded. Second, for any claim of equivalence, follow the clinical-trials
reporting template: **state the margin, justify it, and report the interval against it** [S95].

**Pattern 4 — Minimum detectable effect as a designed result.** "At 400 items and the observed
discordance of 0–4, the smallest difference this instrument could have detected was larger than any
difference between these arms." State it in the results, not the limitations [S8].

**Pattern 5 — The defect as a general trap, instance second.** Appendix B's form throughout:

> ✓ A contract documented in a docstring and never asserted in code is not a contract. The depth
> gate for the Wave-1 sweep was specified in the harness's own documentation and enforced nowhere;
> nine cells were quarantined and their pads rebuilt. The same harness then repeated the pattern one
> stage later, asserting the prefill contract in code and leaving the generation contract in the
> docstring — which is how a 24-cell sweep came to report 52.27 tok/s at a context of 131,072 while
> every repetition generated exactly 17 tokens.

**Pattern 6 — The instrument that failed, reported as a measurement of the instrument.** S10 (KL at
depth: infeasible — 14 GiB caps the tool at `n_ctx` 8,192) and S11 (greedy divergence at depth:
rejected on its own data — free-running trajectories fork within 2–126 characters and every pairwise
distance saturates). Both are results about instruments and both belong in the report. Frame:
*designed, built, run, and rejected on its own evidence* — the sequence is the point.

The systems-paper literature has said this for forty years and the report should cite it rather
than argue for it. Levin & Redell's evaluation criteria for SOSP submissions, published in 1983 and
still the canonical statement of what a systems paper owes its reader, include [S33]:

> "A seemingly good idea that didn't pan out is at least as interesting as one that did."

and, under *Choices*:

> "What were the alternatives considered at various points, and why were the choices made the way
> they were? … Did the choices turn out to be right, and, if so, was it for the reasons that
> motivated them in the first place? … How often have you found yourself saying 'this works, but for
> the wrong reason'?"

That second passage is a precise description of the `-ts` rebalance result — a flag that bought
+33 % context and +93 % decode, whose mechanism was inferred rather than logged, and whose optimum
turned out not to be monotone-safe — and it is the frame to write it in.

### 6.3 The p-value rule, stated once

Because it is the report's methodological signature, state it once in §4 and apply it without
exception:

> A p-value is reported only where the test could have reached the conventional threshold. Where the
> discordance count made that impossible, the minimum attainable p is reported instead, and the
> comparison is stated as an interval or an equivalence bound. This rule is applied to this report's
> own generative anchor, where an earlier revision reported p = 1.0 from a test whose smallest
> obtainable p was 0.0625.

### 6.4 A live inconsistency the drafter must resolve first

Three different 95 % intervals for the *same* paired HumanEval+ difference are currently in
circulation across this project's documents:

| source | interval | estimator | metric |
|---|---|---|---|
| PN-40 table, row 1 | [−2.68, +1.46] | Wald, paired proportion difference | HumanEval **base** (3 discordant) |
| PN-40 table, row 2 | [−3.28, +2.06] | Wald, paired proportion difference | HumanEval**+** (5 discordant) |
| `reviewer-b-structure.md` §5 | [−4.08, +2.76] | Newcombe score, paired | HumanEval**+** (5 discordant) |

`OUTLINE.md` §5.2 quotes `[−2.68, +1.46]` while labelling the row **HumanEval+**, which is PN-40's
*base* row. Before drafting §5.2: pick one estimator, name it in §4, use it for every paired
proportion in the report, and correct the outline.

**And the literature answers the question PN-40 left open.** PN-40's own caveat says its interval is
the Wald form and "approximate at these small discordant counts". Fagerland, Lydersen & Laake give
the recommended tests and intervals for paired binomial proportions in exactly this regime [S58] —
use their recommendation, name it, and PN-40's self-flagged weakness closes. Two further results
make the surrounding argument citable rather than merely asserted:

- **The exact conditional McNemar test is known to be conservative** — it "produces unnecessary
  large p-values and has poor power", with type-I error staying near 3 % even at 100 pairs, and the
  mid-p variant is recommended instead [S59]. This is *why* 3 discordant pairs could never reach
  0.05.
- **The minimum attainable p-value on a discrete test statistic is a formal object**, not an
  observation: a discrete test's achievable p-values form a finite grid whose smallest element may
  exceed α [S60]. PN-40's arithmetic has a citation.

Separately, the interval family already chosen is independently endorsed for this exact regime:
CLT-based error bars "dramatically underestimate uncertainty" below a few hundred datapoints, and
Wilson score intervals are the preferred frequentist choice, with Clopper–Pearson judged "overly
conservative (too wide)" [S61]. At `n = 164` and `n = 49`, this report is squarely inside that
paper's stated failure regime, and saying so converts an estimator choice into a defended one.

This is not a nitpick. It is PN-20's defect — *an aggregate whose estimator is never named* — alive
inside the manuscript planning itself, and a reviewer who finds it will use it.

### 6.5 Three conventions worth borrowing

**(a) The GPT-3 disclosure pattern — for a defect you cannot afford to fix.** This report has one:
the pre-2026-08-29 corpus came from an engine image that no longer exists. The best published model
is the GPT-3 paper's handling of its contamination bug [S68], which does four things in three
sentences: names the defect ("a bug in the filtering caused us to ignore some overlaps"); says why
it was not fixed ("due to the cost of training it was not feasible to retrain the model"); commits
to quantifying the consequence ("in Section 4 we characterize the impact of the remaining
overlaps"); and then **acts on it in the tables** — affected rows marked with an asterisk, and for
the worst-affected sets, "we do not report results on these datasets."

Applied here: the *irreproducible-on-current-images* label is the asterisk, and the rows excluded
outright are the equivalent of the suppressed datasets. Say that explicitly once, in §3, and the
label stops looking like a hedge and starts looking like a policy.

**(b) A typed outcome tag per finding.** ReScience C tags each result `Re` (replication) or `Rp`
(reproduction), negated as `¬Re` / `¬Rp` on failure, and uses those tags in article titles [S69].
NISO's badging recommendation makes the same point normatively: "**Partially replicable findings…
should be made visible in some way in the scholarly record**" [S70]. The claim index (Appendix D)
should carry a status column on exactly this pattern — **confirmed · scoped · corrected ·
withdrawn** — so that a reader can see the shape of the corpus at a glance rather than discovering
it note by note.

**(c) State what kind of error a withdrawal fell to.** COPE's guidance distinguishes a *correction*
("a small portion of an otherwise reliable publication proves to be misleading, especially because
of honest error") from a *retraction* ("the findings are unreliable"), and requires a notice to
"state the reason(s) … to distinguish misconduct from honest error" [S71]. Every withdrawal in this
report is instrumentation or arithmetic; saying which, each time, is one clause and it forecloses
the reader's worse guess.

---

## 7. Worked example: §1's opening

Every rule in this guide, applied at once. Annotations follow; they come out before submission.

---

> Two hours and nine minutes of divergence measurement separated four quantizations of the same 27B
> coding model at 8.7–18.1 σ on code, with non-overlapping intervals at every adjacent step. Four
> hours and forty-eight minutes of task benchmarking — multiple-choice at `n = 400` items,
> unit-tested code generation at `n = 164` problems paired, and long-context retrieval at three
> lengths — separated them nowhere. That contrast is what this report is organised around, and the
> uncomfortable half is the second one: run the conventional way, on the conventional instruments,
> this study would have concluded that the four arms are equivalent and recommended the cheapest.
>
> The setting is a practitioner's question with a budget attached. On two 16 GB consumer GPUs
> without NVLink, which quantization of Qwen3.8-27B should serve a coding agent, and by what
> measurement would you know? The published answers are a perplexity number on English prose, a
> task-battery score, and the model card. I measured all three on four Unsloth GGUF arms under one
> engine image pinned by digest, and they do not agree with each other. Perplexity orders the ladder
> correctly across a span of 0.033 while carrying ±0.041 of standard error at every point [Protocol
> 1, `n = 602` windows], so it reproduces the ranking without certifying a single step of it. The
> same checkpoint scored against the same corpus under two defensible perplexity protocols reports
> either 29 % or 0.8 % degradation — a 36-fold swing in the estimated effect, produced by corpus
> file, window coverage and scoring rule alone, with the intuitive explanation, tokenizer mismatch,
> tested and disproven. And a multiple-choice battery at `n = 400` ranks the most heavily quantized
> arm nominally highest. Dutta et al. established that accuracy metrics hide compression damage
> [R13]; this report measures the shape of that damage on a code distribution, its dependence on how
> close the evaluation corpus sits to the task, and a quantified bound on what it costs at the task
> level — on hardware a practitioner can buy.

---

### What each move demonstrates

| move | rule |
|---|---|
| First sentence is a measured contrast in numbers, not a claim about the field | §0.3, §3.1 failure mode, and the arXiv position-paper moderation risk [S3, S4] |
| `8.7–18.1 σ on code` rather than `3.7–11.8 σ` | §4.6 — the 3.71 σ prose endpoint does not survive Bonferroni under a design effect of 1.5, so it is not used to carry a ranking claim. The paper's own §7.4 explains why; §1 simply does not lean on it. |
| `2 h 9 min` and `4 h 48 min` in words | §4.2 — decimal hours in prose read as false precision; and the corrected PN-41 figures are used, not the retired "20 minutes vs 20 hours" |
| `n = 400 items`, `n = 164 problems paired`, `n = 602 windows` | §4.3 — `n` always, with its unit, and the unit differs by instrument, which is the report's method point arriving free |
| `[Protocol 1]` tag | §4.5 — three perplexity protocols exist; the label is not optional |
| "separated them nowhere" not "found no significant difference" | §4.6, §6.3 — this is a bound being previewed, not a null |
| "would have concluded … and recommended the cheapest" | the stake, stated as a consequence rather than as a criticism of the field — it makes the report a measurement study, not a position paper |
| **"I measured all three"** | §1.3 — the only first-person in two paragraphs, attached to a decision about what to study. One per page is the target. |
| "they do not agree with each other" | the agentless subject is the measurements; §1.3's sorting rule |
| "orders the ladder correctly … without certifying a single step of it" | §4.6 — the licensed phrasing for *direction consistent, intervals overlapping*; it is precise, and it is more interesting than either "perplexity works" or "perplexity fails" |
| "tested and disproven" (the tokenizer hypothesis) | a falsified sub-hypothesis reported in the introduction — cheap, and it establishes early that this report reports what it found rather than what it expected |
| Dutta et al. credited in paragraph 2, before contributions | §3.1(d) — priority settled before a reviewer can raise it |
| "on hardware a practitioner can buy" | the setting stated as scope, not as a virtue; no "modest", no "resource-constrained" |
| "a span of 0.033 while carrying ±0.041 of standard error at every point" | §0.1 — **the bound travels inside the claim.** The reader never meets "perplexity is unreliable" as a bare assertion; they meet the two numbers whose relation makes it true, in one clause. This is the rule Budescu's result [S47] demands: the range is restated at the point of use, not deferred to a methods table |
| Three separate caveats, three different attachments | §2.6 — an em-dash rider on the 36-fold swing, a bracketed protocol tag on the perplexity figure, and an in-clause scope on `n = 400`. No footnotes, no "however", no sentence spent retracting the previous one |
| No banned phrase anywhere: no *note that*, *significant*, *novel*, *extensive*, *we* | §1.7 |
| Two paragraphs, 108 and 197 words | §2.4 — the first is a claim paragraph (claim, then stake); the second is a claim paragraph running long because it carries three instruments. At 197 words it is at the upper limit and would be split at "And a multiple-choice battery…" if §1 runs over budget |

### The paragraph that must follow within the same page

The status statement of §1.4, verbatim, plus the eight-line "what this report does not show" block.
Placed after the contributions list, at the end of §1. Do not move it earlier; do not move it later.

---

## 8. Pre-submission checklist

Mechanical and checkable. Anything not checkable belongs in §1–§7, not here.

**Run these first — they are mechanical**

```bash
# 1. Pronoun check: must return nothing outside quoted material.
grep -nEiw 'we|our|ours|us' manuscript/*.tex

# 2. Weasel words (list from S84). Every hit is reviewed, not necessarily removed.
grep -nEw 'many|various|very|fairly|several|extremely|exceedingly|quite|remarkably|few|surprisingly|mostly|largely|huge|tiny|excellent|interestingly|significantly|substantially|clearly|vast|relatively|completely|a number of' manuscript/*.tex

# 3. Banned constructions from §1.7.
grep -nEi 'it should be noted|it is important to note|note that|arguably|seems to (suggest|indicate)|may potentially|to the best of our knowledge|state-of-the-art|extensive experiments|no significant difference|preliminary|future work will' manuscript/*.tex

# 4. Every interval must name an estimator: eyeball each hit for a following estimator name.
grep -nE '95 *\\% *(CI|interval)|\[[-+−][0-9]' manuscript/*.tex

# 5. Un-unitised n.
grep -nE 'n *= *[0-9,]+ *[^a-zA-Z]' manuscript/*.tex

# 6. Bare K-notation in prose.
grep -nE '[0-9]+ *K\b' manuscript/*.tex
```

**Voice and positioning**
- [ ] Zero occurrences of `we`, `our`, `us` in the body, abstract and captions
- [ ] `I` appears between 15 and 40 times, and every occurrence is attached to a judgement, a choice or a withdrawal
- [ ] Author block reads *Independent researcher* on its own line; USP appears as a qualification, never as the affiliation
- [ ] Page-1 footnote carries: technical-report status, artifact DOI, SWHID, engine digest
- [ ] §1 ends with the status statement and the eight-line "does not show" block
- [ ] AI-conduct disclosure present in §3, one paragraph, worded as provenance
- [ ] Every phrase in the §1.7 avoid-list returns zero hits

**Claims and statistics**
- [ ] Every headline number traces: sentence → PN → artifact path → serverlog (Appendix D is complete)
- [ ] Every estimate carries `n` **with its unit**
- [ ] Every interval names its estimator, in the sentence or the table note
- [ ] **One estimator per quantity across the whole report** — §6.4 resolved and the outline corrected
- [ ] No p-value appears where the test could not have reached α = 0.05; minimum attainable p stated instead
- [ ] The minimum detectable effect is stated for HumanEval+ (`n = 164`) and HellaSwag (`n = 400`) in §5, not §7
- [ ] No sentence states a null; every one states a bound
- [ ] No post-hoc/observed power is reported anywhere [S63]
- [ ] The sample-size justification is stated as *resource constraints* with a citation [S64], not as an apology
- [ ] Every verb in a claim sentence is licensed by §4.6's ladder
- [ ] Every hedge word has its numeric range restated beside it at that point of use [S47]
- [ ] The 3.71 σ prose adjacency is never used to carry a ranking claim
- [ ] `PN-64` applied: the median contrast is "roughly two orders of magnitude" and is not tabulated per arm
- [ ] `PN-62` applied: the tail's *shape* is attributed to the corpus, its *magnitude* to quantization
- [ ] `PN-39` applied: "two of the four arms measured", everywhere, including the abstract and README-derived text
- [ ] `PN-41` applied: 2 h 9 min vs 4 h 48 min; the "20 minutes vs 20 hours" contrast appears nowhere
- [ ] `PN-61` applied: no acceptance figure of 1.000 is quoted without its generation length

**Protocol integrity**
- [ ] No table mixes perplexity Protocols 1, 2 and 4
- [ ] No table mixes depth-0 and at-depth throughput
- [ ] No table mixes greedy and official-sampling rows
- [ ] Every pre-2026-08-29 row is labelled *irreproducible-on-current-images*, or excluded
- [ ] Every table has its note line: instrument · protocol · `n`+unit · estimator · interval type · image digest · artifact path
- [ ] Withdrawn claims appear only as worked examples (§6) and in Appendix B — never as live results

**Structure**
- [ ] §7 threats-to-validity was written before §5 was polished
- [ ] §7 has ≥ 15 items, each naming the artifact that bounds it, and ≥ 8 naming the cost of removing it
- [ ] §7's first item is the strongest objection to the headline, in a critic's words
- [ ] §7 ends on the compounding question
- [ ] §8 Conclusion exists and introduces no new numbers
- [ ] Every §5 subsection opens with its result in one standalone sentence
- [ ] Every §5 subsection maps to exactly one abstract claim or contribution
- [ ] §2 is ≤ 900 words and every paragraph ends on what this report measures differently
- [ ] No section heading contains a count the section contradicts
- [ ] Appendix D (claim index) is complete and referenced from §1

**Tables and figures**
- [ ] Every caption is a sentence with a verb asserting a claim
- [ ] Captions above tables, below figures
- [ ] No number appears in two tables
- [ ] Unmeasured cells read *not attempted*, never `0` or blank
- [ ] Every figure has a released source CSV under `manuscript/figures/data/`
- [ ] Every figure checked against its CSV after rendering
- [ ] All figures vector PDF; no distinction encoded in colour alone

**Citations**
- [ ] Every `.bib` entry was verified against the primary document, not a summary (§9.10), and records an access date
- [ ] The eight traps in §9.10 have each been checked against the manuscript
- [ ] arXiv:2411.02355 (Kurtic et al.) and arXiv:2607.08734 (Rababah et al.) are cited in §2 (§10.4)
- [ ] arXiv:2601.09527 (same GPU family) is cited in §2 or §3
- [ ] Every citation supports the specific sentence it is attached to, not the topic

**arXiv mechanics** *(from reviewer B §9; verified against arXiv's own pages [S1, S2, S3, S5, S25])*
- [ ] Endorsement secured for `cs.LG` — **start weeks early**; institutional email alone no longer qualifies [S2]
- [ ] Categories: `cs.LG` primary, `cs.PF` cross-list only; `ACM-class: D.4.8; I.2.6`
- [ ] Artifacts deposited publicly (Zenodo DOI + SWHID); the private-repository blocker resolved — arXiv requires links to resolve publicly
- [ ] LaTeX source submitted, not PDF; `.bib` included; flattened directory; JSON artifacts in `anc/`
- [ ] Abstract ≤ 1,920 characters, **ASCII only**, no LaTeX macros, no en-dashes or curly quotes
- [ ] Abstract opens on a measurement, carries sample sizes, and closes on a scope sentence (§3.0)
- [ ] Abstract converted to first person singular; `CITATION.cff`'s copy changed to match
- [ ] Comments field carries `Technical report.` (§1.2)
- [ ] `Report-no` left empty — it is reserved for institution-assigned numbers [S5]
- [ ] Affiliation in the author metadata is in parentheses, city and country only [S5]
- [ ] Title, authors and abstract in the web form match the PDF exactly
- [ ] Licence CC BY 4.0 selected (irrevocable per version)
- [ ] Comments field: `NN pages, 6 figures, 5 tables. Artifacts: <DOI URL>`
- [ ] The document does not read as a review or position paper — §2 ≤ 900 words, abstract opens on a measurement, contributions are results [S3, S4]
- [ ] Self-audit against Heiser's benchmarking crimes [S20], Hoefler & Belli's twelve rules [S30], the SIGPLAN empirical-evaluation checklist [S72] and the SIGSOFT Benchmarking standard [S43]
- [ ] Announcement timing considered — position in the daily listing has a measurable readership effect [S45]

---

## 9. Sources

Full bibliographic data for `manuscript/references/references.bib`. The `S`-numbering is local to
this guide; `R`-numbers refer to `../docs/paper/METHOD-REFERENCES.md`, which already carries the
technical and instrument references and is not duplicated here. **Verification column**: *fetched* =
I retrieved the page and read the claim; *search* = confirmed from search results but the primary
page returned 403 or was paywalled — check before it enters the `.bib`.

### 9.1 arXiv: category, moderation, submission and disclosure

| # | source | supports | ver. |
|---|---|---|---|
| **S1** | arXiv. *Content Moderation* (policy page). `https://info.arxiv.org/help/moderation/index.html` (retrieved 2026-09-03). Verbatim: significant tool use including "text-to-text generative AI" is "among those that should be reported consistent with subject standards for methodology"; authors "each individually take full responsibility for all its contents, irrespective of how the contents were generated"; "generative AI language tools should not be listed as an author"; "Submissions that do not contain original or substantive research … may be declined". | §1.5 (the AI-conduct disclosure is mandatory, not optional); §3.2 (the "not substantive research" clause is the realistic moderation risk for this manuscript, and is why §2 is capped and §1 opens on a measurement) | fetched |
| **S2** | arXiv. *Attention Authors: updated endorsement policy.* arXiv blog, 2026-01-21. `https://blog.arxiv.org/2026/01/21/attention-authors-updated-endorsement-policy/` | §8 checklist — an institutional email address is no longer sufficient for auto-endorsement in any category, so a personal endorsement is the only route for this author and must be started weeks before drafting finishes | search |
| **S3** | arXiv. *Attention Authors: Updated Practice for Review Articles and Position Papers in arXiv CS Category.* arXiv blog, 2025-10-31. `https://blog.arxiv.org/2025/10/31/attention-authors-updated-practice-for-review-articles-and-position-papers-in-arxiv-cs-category/` Review articles and position papers must "be accepted at a journal or a conference and complete successful peer review" and supply "the peer reviewed journal reference and DOI metadata"; reason given is a flood of submissions that generative AI has made "fast and easy to write". | **The single most consequential external constraint on this report's rhetoric.** §3.1, §3.2, §2.7D: the abstract and §1 must open on a measurement, §2 must position rather than survey, and the contributions must read as results. An assertive-thesis title over a survey-shaped §2 is the shape a moderator declines. | fetched |
| **S4** | Nature news. *Preprint site arXiv is banning computer-science reviews: here's why.* 2025-11. `https://www.nature.com/articles/d41586-025-03664-7` | Corroborates S3 and gives the community context; useful in a cover letter, not in the report | search |
| **S5** | arXiv. *Metadata for Required and Optional Fields.* `https://info.arxiv.org/help/prep.html` — abstracts over 1,920 characters are not accepted; the metadata field takes ASCII only. | §8 checklist — the abstract must be counted and de-Unicoded before submission; en-dashes and curly quotes pasted from a PDF are the usual failure | search |

### 9.2 Statistics: intervals, nulls, power and equivalence

| # | source | supports | ver. |
|---|---|---|---|
| **S6** | Miller, E. (2024). *Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations.* arXiv:2411.00640. `https://arxiv.org/abs/2411.00640` | §4.4, §6.3 — evaluations are experiments drawn from an unseen super-population; report intervals, use paired designs where available, design for informativeness rather than for a threshold. Already `R6` / `miller2024errorbars` in the corpus; cited here for the *reporting* rules rather than the method | fetched |
| **S7** | Bouthillier, X., Delaunay, P., Bronzi, M., Trofimov, A., Nichyporuk, B., Szeto, J., Mohammadi Sepahvand, N., Raff, E., Madan, K., Voleti, V., Ebrahimi Kahou, S., Michalski, V., Arbel, T., Pal, C., Varoquaux, G., & Vincent, P. (2021). *Accounting for Variance in Machine Learning Benchmarks.* Proceedings of Machine Learning and Systems 3 (MLSys 2021). `https://mlsys.org/paper_files/paper/2021/file/0184b0cd3cfb185989f858a1d9f5c1eb-Paper.pdf` | §3.5 (§5.5) and §7 — multiple variance sources must be accounted for before a difference is attributed to a treatment. Directly applicable to the report's throughput noise: a within-configuration spread of 17–41 % that collapses to 3–11 % once conditioned on draft acceptance is a textbook instance of an uncontrolled variance source | fetched |
| **S8** | Card, D., Henderson, P., Khandelwal, U., Jia, R., Mahowald, K., & Jurafsky, D. (2020). *With Little Power Comes Great Responsibility.* Proceedings of EMNLP 2020, 9263–9274. ACL. DOI 10.18653/v1/2020.emnlp-main.745. `https://aclanthology.org/2020.emnlp-main.745/` | §4.4, §6.4 — **the citation behind reporting the minimum detectable effect as a designed result rather than an apology.** Establishes that underpowered comparisons are the NLP norm and that power analysis belongs in the design, which is exactly this report's argument transposed to quantization | fetched |
| **S9** | Altman, D. G., & Bland, J. M. (1995). *Absence of evidence is not evidence of absence.* BMJ, 311(7003), 485. DOI 10.1136/bmj.311.7003.485 | §1.7, §6.3 — the canonical citation for refusing to state a non-significant result as a null. This report needs it because its central move is converting three vacuous nulls into bounds | search (bmj.com returned 403; DOI and pagination are standard and stable) |
| **S10** | Wasserstein, R. L., & Lazar, N. A. (2016). *The ASA Statement on p-Values: Context, Process, and Purpose.* The American Statistician, 70(2), 129–133. DOI 10.1080/00031305.2016.1154108 | §6.3 — the authority for the p-value rule stated in §4: a p-value does not measure effect size or importance, and reporting one where the design could not have reached the threshold is uninformative | search (tandfonline 403) |
| **S11** | Lakens, D. (2017). *Equivalence Tests: A Practical Primer for t Tests, Correlations, and Meta-Analyses.* Social Psychological and Personality Science, 8(4), 355–362. DOI 10.1177/1948550617697177 | §4.4, §6.2 Pattern 3 — TOST is the correct instrument when the claim is "no meaningful difference". Note that a paper in this report's immediate neighbourhood already uses TOST at ±3 pp for a speculative-decoding equivalence claim, so it is established practice here | search (sagepub 403) |

### 9.3 Positioning, voice and the honest limitations section

| # | source | supports | ver. |
|---|---|---|---|
| **S12** | Altenmüller, M. S., Nuding, S., & Gollwitzer, M. (2021). *No harm in being self-corrective: Self-criticism and reform intentions increase researchers' epistemic trustworthiness and credibility in the eyes of the public.* Public Understanding of Science, 30(8), 962–976. DOI 10.1177/09636625211022181 | **§1.1 and §6 — the empirical warrant for showing the nine corrections rather than burying them.** Two experiments (N = 337, N = 365): expressed self-criticism and reform intentions *raise* rated integrity, benevolence, trustworthiness and credibility; *denying* self-doubt lowers them; the extent of the reform did not matter, so modest, specific commitments suffice | fetched |
| **S13** | Clarke, B., Alley, L. J., Ghai, S., Flake, J. K., Rohrer, J. M., Simmons, J. P., Schiavone, S. R., & Vazire, S. (2024). *Looking our limitations in the eye: A call for more thorough and honest reporting of study limitations.* Social and Personality Psychology Compass, 18(6), e12979. DOI 10.1111/spc3.12979 | §3.7 — the **steel-person principle**: state the best argument against your conclusion, not a weaker one you can answer; organise limitations as threats to construct, internal, external and statistical-conclusion validity. Also the source of §3.7's failure mode — boilerplate limitations dilute the specific ones | search (Wiley page indexed; open-access copy at `https://ora.ox.ac.uk/objects/uuid:457a51fe-74ad-456b-9e5f-2c6bed2132ca`) |
| **S14** | American Psychological Association. *Publication Manual of the American Psychological Association*, 7th ed. (2020), §4.16 "First-person pronouns". APA Style page: `https://apastyle.apa.org/style-grammar-guidelines/grammar/first-person-pronouns` | §1.3 — a solo author uses "I"; there is no rule against first-person pronouns; the editorial "we" meaning "people in general" is separately discouraged as vague | search (style page indexed; §4.16 is the Manual's own section number) |
| **S15** | APA Style blog. *The "no first-person" myth.* `https://apastyle.apa.org/blog/first-person-myth` | §1.3 — cited to establish that the avoid-first-person instinct is a widespread misconception rather than a rule, which is the belief the drafter must overcome | search |
| **S16** | Wang, S.-p., Tseng, W.-T., & Johanson, R. (2021). *To We or Not to We: Corpus-Based Research on First-Person Pronoun Use in Abstracts and Conclusions.* SAGE Open, 11(2). DOI 10.1177/21582440211008893 | §1.3 — first-person plural use is a disciplinary and rhetorical positioning choice rather than a grammatical requirement, which is what licenses departing from the ML convention on principled grounds | search (sagepub 403 on full text; DOI and metadata confirmed) |
| **S17** | Nielsen, J. (2006). *Progressive Disclosure.* Nielsen Norman Group, 2006-12-03. `https://www.nngroup.com/articles/progressive-disclosure/` | §2.1, §2.2 — the canonical formulation: defer advanced or rarely used material to a secondary layer; improves learnability and efficiency simultaneously, and users build a *more* complete mental model, not a less complete one, when material is prioritised. This is the direct warrant for the four-layer rule | fetched |
| **S18** | Nielsen Norman Group. *How Users Read on the Web* (Nielsen, 1997) and the F-shaped-pattern follow-ups. `https://www.nngroup.com/articles/how-users-read-on-the-web/` | §2.5 — readers scan rather than read linearly; information available only in reading order is lost. The warrant for result-first section openers and self-contained captions | search |
| **S19** | Peyton Jones, S. *How to Write a Great Research Paper* (seven simple suggestions). Microsoft Research; slides and video. `https://www.microsoft.com/en-us/research/academic-program/write-great-research-paper/` · `https://simon.peytonjones.org/great-research-paper/` | §3.1, §3.2 — "identify your key idea", "tell a story", "nail your contributions", "put related work at the end", "put your readers first". The related-work advice is the stronger form of §3.2's positioning rule and independently reduces the S3 moderation risk | search (both URLs live and indexed) |
| **S20** | Heiser, G. *Systems Benchmarking Crimes.* `https://gernot-heiser.org/benchmarking-crimes.html`; and van der Kouwe, E., Andriesse, D., Bos, H., Giuffrida, C., & Heiser, G. (2018). *Benchmarking Crimes: An Emerging Threat in Systems Security.* arXiv:1801.02381 | §3.5 (§5.3) and §8 — the taxonomy of 22 benchmarking crimes; specifically the *unfair-competitor* crime, which is what justifies comparing each quantization at its own winning `-ts` ratio rather than at the engine default. A survey of 50 papers found a mean of five crimes per tier-1 paper, with one clean paper in the sample | search |
| **S21** | Mensh, B., & Kording, K. (2017). *Ten simple rules for structuring papers.* PLOS Computational Biology, 13(9), e1005619. DOI 10.1371/journal.pcbi.1005619 | §2.4, §3 — the context–content–conclusion scheme at every scale (paper, section, paragraph); "deliver the results as a sequence of statements … that connect logically to support the central contribution"; allocate effort to title, abstract, figures and outline. Rule 3 is the origin of §2.4's paragraph contract | fetched |
| **S22** | Whitesides, G. M. (2004). *Whitesides' Group: Writing a Paper.* Advanced Materials, 16(15), 1375–1377. DOI 10.1002/adma.200400767 | §5.1, §5.2 — the outline-from-figures method and the argument that figures and their captions carry the paper. Supports the caption-states-the-claim rule | search |
| **S23** | Pineau, J., Vincent-Lamarre, P., Sinha, K., Larivière, V., Beygelzimer, A., d'Alché-Buc, F., Fox, E., & Larochelle, H. (2021). *Improving Reproducibility in Machine Learning Research: A Report from the NeurIPS 2019 Reproducibility Program.* Journal of Machine Learning Research, 22(164). `https://jmlr.org/papers/v22/20-303.html` | §3.10, §8 — the ML reproducibility checklist as a submission-time instrument; the model for the report's own claim index (Appendix D) | fetched |
| **S24** | ACM. *Artifact Review and Badging — Current (Version 1.1).* `https://www.acm.org/publications/policies/artifact-review-and-badging-current` (retrieved 2026-09-02; see `../docs/paper/METHOD-REFERENCES.md` R14) | §3.10 — the tier definitions that let the report claim *Artifacts Available* and explicitly decline *Artifacts Evaluated — Functional*, naming the completeness criterion it fails and the count (72 server logs cited, 0 released) | via R14 (page returned 403 on re-fetch) |

### 9.4 Genre exemplars — the papers this report is written next to

These are not craft references; they are the published comparators. Four of them are also
**missing related work** and belong in §2 regardless of what this guide says about style.

| # | source | supports | ver. |
|---|---|---|---|
| **S25** | arXiv. *Content Types* and *Cross-listing*. `https://info.arxiv.org/help/policies/content-types.html` · `https://info.arxiv.org/help/cross.html` — "Research articles are the primary content type"; articles "should be complete final drafts"; "It is rarely appropriate to add more than one or two cross-lists"; "Bad cross-lists will be removed". Category text, verbatim: **cs.PF** "Covers performance measurement and evaluation, queueing, and simulation"; **cs.LG** "Papers on all aspects of machine learning research… including also robustness, explanation, fairness, and methodology". | §1.2, §8 — there is no arXiv document type for "technical report"; and the cs.PF description is a literal description of this study's method, which is relevant to the category decision (§8 note) | fetched |
| **S26** | Kurt, U. (2026). *Which Quantization Should I Use? A Unified Evaluation of llama.cpp Quantization on Llama-3.1-8B-Instruct.* arXiv:2601.14277 [cs.LG]. 17 pages, 6 tables, 1 figure. `https://arxiv.org/abs/2601.14277` | **§1.1 — the closest published comparator, and the single most useful positioning datapoint in this guide.** Single author; the first-page author block is literally `Uygar Kurt` followed by `ABSTRACT`, with no institution, no email and no "Independent Researcher" string; no limitations section, no confidence intervals, no seed or variance discussion. Also already `R7`/`kurt2026whichquant` in the corpus, cited there as the nearest neighbour on content | fetched + PDF text extraction |
| **S27** | Jia, Z., Maggioni, M., Staiger, B., & Scarpazza, D. P. (2018). *Dissecting the NVIDIA Volta GPU Architecture via Microbenchmarking.* arXiv:1804.06826 [cs.DC, cs.PF]. Comments field, verbatim: `Technical report. First Edition. April 18th, 2018. 66 pages`. | §1.2 — the genre exemplar for *form*: a long, table-dense, measurement-only self-labelled technical report with no venue, which became a standard citation. Its abstract also legitimises the enterprise: manufacturers' "reluctance… to disclose low-level details" means "independent researchers have resorted to microbenchmarks-based dissection and discovery" | fetched |
| **S28** | Dao, T. (2023). *FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning.* arXiv:2307.08691 [cs.LG]. | §1.2 — single-author systems report that uses the technical-report register with no label a reader would notice, and calibrated verbs in the abstract ("around 2× speedup", "reaching 50–73 % of the theoretical maximum FLOPs/s"). Evidence that rhetorical volume is not credibility | fetched |
| **S39** | Knoop, J., & Holtmann, H. (2026). *Private LLM Inference on Consumer Blackwell GPUs: A Practical Guide for Cost-Effective Local Deployment in SMEs.* arXiv:2601.09527 [cs.LG; cs.AI, cs.PF]. Comments: "15 pages, 18 tables, 7 figures. Includes link to GitHub repository and Docker image for reproducibility." Second author's affiliation, verbatim: `Independent Researcher, Hamburg, Germany`. | **Missing related work — same hardware family (RTX 5060 Ti), overlapping axes (NVFP4, quantization format, context length).** Also the closest stylistic model: its abstract quantifies scope as "79 configurations spanning quantization formats (BF16, W4A16, NVFP4, MXFP4), context lengths (8k–64k), and three workloads", and it names where its own recommendation fails | fetched + PDF extraction |
| **S40** | Avinash, M. S. R. (2025). *Profiling LoRA/QLoRA Fine-Tuning Efficiency on Consumer GPUs: An RTX 4060 Case Study.* arXiv:2509.12229 [cs.LG; cs.AI, cs.PF]. Affiliation block: `Independent Researcher` / `Machine Learning Engineer, Juspay` / `Bengaluru, India` / personal address. | §1.1, §3.0 — a fourth close analogue: single author, consumer GPU, profiling case study, colon-subtitle, method-and-scope framing in the title. Direct evidence that "case study" and "empirical study" framings are the *convention* in this subfield rather than a weakness | fetched |
| **S38** | Tummalapalli, P., Arayakandy, S., Pal, R., & Kundan, K. (2026). *LLM Inference at the Edge: Mobile, NPU, and GPU Performance Efficiency Trade-offs Under Sustained Load.* arXiv:2603.23640 [cs.DC]. | §3.0(4) — the model abstract-closing scope sentence, quoted in full there. Disclaims exactly this report's hardware-versus-software-stack confound | fetched |
| **S41** | Besiroglu, T., Erdil, E., Barnett, M., & You, J. (2024). *Chinchilla Scaling: A replication attempt.* arXiv:2404.10102 [cs.AI, cs.CL]. Affiliation: `Epoch AI`. **Four authors, not solo.** | §6 — the template for contradicting a well-resourced group's published result: hedge in the *title* ("A replication **attempt**"), name the target in sentence one, deliver the sharpest claim as arithmetic the reader can redo. Directly applicable to §5.4's refutation of the losslessness premise | fetched |

### 9.5 Performance-evaluation and empirical-reporting standards

| # | source | supports | ver. |
|---|---|---|---|
| **S29** | Rangarajan, A. M., & Krishnan, J. (2026). *Machine Learning Research Has Outpaced Its Communication Norms and NeurIPS Should Act.* arXiv:2605.08889 [cs.LG]. Flesch Reading Ease of NeurIPS abstracts fell from ≈24 (1987) to ≈13 (2024); acronym density in titles rose 0.33 → 3.21 per 100 words, with 89 % of acronyms appearing fewer than ten times; more readable papers receive more citations. | §4.9 — the abbreviation budget, and the general warrant for the whole of §2 | fetched |
| **S30** | Hoefler, T., & Belli, R. (2015). *Scientific Benchmarking of Parallel Computing Systems: Twelve ways to tell the masses when reporting performance results.* Proc. SC '15, ACM. DOI 10.1145/2807591.2807644. ISBN 978-1-4503-3723-6. `https://htor.inf.ethz.ch/publications/img/hoefler-scientific-benchmarking.pdf` | **§5.0 — the single most directly applicable craft reference for this report.** All twelve rules verified verbatim from the PDF; six bind here. Rule 8 ("some problems may require other percentiles") is this report's own headline finding stated as a reporting rule by an external authority — cite it in §5.1 | fetched (PDF extraction) |
| **S31** | Hoefler, T. (2018). *Twelve ways to fool the masses when reporting performance of deep learning workloads.* Blog post, 2018-11-08. `http://htor.inf.ethz.ch/blog/index.php/2018/11/08/twelve-ways-to-fool-the-masses-when-reporting-performance-of-deep-learning-workloads/` (journal form: Hoefler, T. (2022). *Benchmarking Data Science: 12 Ways to Lie With Statistics and Performance on Parallel Computers.* Computer. DOI 10.1109/MC.2022.3152681) | §4.5, §5.0 — item 8, "Show performance when enabling option set A and show accuracy when enabling option set B", is exactly the failure the never-mix-protocols rule guards against | fetched |
| **S32** | Verdecchia, R., & Bogner, J. (2025). *Notes On Writing Effective Empirical Software Engineering Papers: An Opinionated Primer.* arXiv:2506.11002; ACM SIGSOFT Software Engineering Notes, DOI 10.1145/3743095.3743100. | §3.0 (title ≤ 15 words; concrete numbers and sample sizes in the abstract; Context/Objective/Method/Result/Conclusion order), §3.7 (**the limitations-versus-threats distinction**), §3.2 (related-work placement rule) | fetched |
| **S33** | Levin, R., & Redell, D. D. (1983). *An Evaluation of the Ninth SOSP Submissions — or — How (and How Not) to Write a Good Systems Paper.* ACM SIGOPS Operating Systems Review, 17(3), 35–40. Reprint PDF: `https://www.cs.cmu.edu/~18742/papers/levin83.pdf`; USENIX author-resources pointer: `https://www.usenix.org/conferences/author-resources/how-and-how-not-write-good-systems-paper` | **§6 and §3** — the canonical systems-paper writing reference, still the page OSDI/SOSP point authors to. Criteria: Original ideas · Reality · Lessons · Choices · Context · Focus · Presentation · Writing style. Quoted in §6 for "a seemingly good idea that didn't pan out is at least as interesting as one that did" and for the *Choices* passage. Also: "Is the paper finished? Omitting sections with a promise to fill them in later is generally unacceptable" | fetched (PDF text extraction) |
| **S42** | Zhang, I. (2021). *Hints on how to write an SOSP paper.* `https://irenezhang.net/blog/2021/06/05/hints.html` | §2.5, §5.2 — "Clearly state each conclusion 3 times: at the beginning of the section as a hypothesis… at the end of the section… in the caption next to the graph"; and "Clearly state the set up for every experiment… How many times did you run the experiment? For how long? State every data object size!" | fetched |
| **S43** | Ralph, P., et al. (2020). *Empirical Standards for Software Engineering Research.* arXiv:2010.03525; living version `https://www2.sigsoft.org/EmpiricalStandards/`. The **Benchmarking** standard: `https://www2.sigsoft.org/EmpiricalStandards/docs/standards?standard=Benchmarking` | §8 self-audit — essential attributes include allowing "different configurations to compete fairly without artificial limitations" (the per-arm `-ts` justification), "assess stability/reliability using sufficient repetitions", and "transparently report execution problems" (Appendix B). Its list of *invalid* criticisms includes "No independent replication reported", which is useful for a solo study | fetched |
| **S44** | Kass, R. E., Caffo, B. S., Davidian, M., Meng, X.-L., Yu, B., & Reid, N. (2016). *Ten Simple Rules for Effective Statistical Practice.* PLOS Computational Biology, 12(6), e1004961. DOI 10.1371/journal.pcbi.1004961. | §4.4, §7 — rules 2 ("Signals Always Come with Noise"), 7 ("Provide Assessments of Variability"), 8 ("Check Your Assumptions") and 9 ("When Possible, Replicate!"). Rule 8 is the citation for §7's token-independence threat | fetched |

### 9.6 Title and abstract — the empirical literature (mixed; cite with care)

| # | source | supports | ver. |
|---|---|---|---|
| **S34** | Letchford, A., Moat, H. S., & Preis, T. (2015). *The advantage of short paper titles.* Royal Society Open Science, 2(8), 150266. DOI 10.1098/rsos.150266. | §3.0 — the short-title claim. ⚠️ **The analysis is at journal level, not paper level.** Do not cite as a paper-level causal claim | fetched |
| **S35** | Milojević, S. (2017). *The Length and Semantic Structure of Article Titles — Evolving Disciplinary Practices and Correlations with Impact.* Frontiers in Research Metrics and Analytics, 2, 2. DOI 10.3389/frma.2017.00002. | §3.0 — directly contradicts S34: discipline is "the strongest determinant", and longer titles correlate *positively* with citations in some fields. Cite alongside S34 or not at all | fetched |
| **S36** | Buter, R. K., & van Raan, A. F. J. (2011). *Non-alphanumeric characters in titles of scientific publications.* Journal of Informetrics, 5(4), 608–617. DOI 10.1016/j.joi.2011.05.008. | §3.0 — colons and hyphens correlate positively with citation impact; the best available support for keeping the colon-subtitle pattern | search (pages unverified) |
| **S37** | Jamali, H. R., & Nikzad, M. (2011). *Article title type and its relation with the number of downloads and citations.* Scientometrics, 88(3), 653–661. DOI 10.1007/s11192-011-0412-z. | §3.0 — question titles are downloaded more and cited less across 2,172 PLoS articles; the reason not to use a question title | search (pages unverified) |
| **S45** | Haque, A., & Ginsparg, P. (2009). *Positional Effects on Citation and Readership in arXiv.* JASIST, 60(11), 2203–2218. arXiv:0907.4740 [cs.DL]. | Not a style rule: position 1 in the daily announcement gets 50–83 % more citations. Submission timing matters more than title style. Worth knowing; not worth optimising for | fetched |

### 9.7 Density, scanning and hedging

| # | source | supports | ver. |
|---|---|---|---|
| **S46** | Budescu, D. V., Broomell, S., & Por, H.-H. (2009). *Improving Communication of Uncertainty in the Reports of the Intergovernmental Panel on Climate Change.* Psychological Science, 20(3), 299–308. DOI 10.1111/j.1467-9280.2009.02284.x | §0.1 — readers regress verbal uncertainty terms toward 50 % | search (paywalled) |
| **S47** | Budescu, D. V., Por, H.-H., Broomell, S. B., & Smithson, M. (2014). *The interpretation of IPCC probabilistic statements around the world.* Nature Climate Change, 4(6), 508–512. DOI 10.1038/nclimate2194 | **§0.1 — the decisive finding: readers regress verbal hedges toward 50 % *even when the calibrated scale is supplied to them*. The only reliable correction is restating the numeric range beside the word at each point of use.** This is the experimental warrant for Rule 1 | Crossref-verified |
| **S48** | Microsoft. *Writing Style Guide — Scannable content* (ms.date 2023-06-20) and *Tables* (2023-03-10). `https://learn.microsoft.com/en-us/style-guide/scannable-content/` | §2.4 — "Three to seven lines is about the right length for a paragraph"; "Don't use a table just to present a list of items that are similar" | fetched |
| **S49** | Nielsen, J. (2006). *F-Shaped Pattern For Reading Web Content (original eyetracking research).* NN/g, n = 232. `https://www.nngroup.com/articles/f-shaped-pattern-reading-web-content-discovered/` · Pernice, K. (2017). *F-Shaped Pattern of Reading: Misunderstood, But Still Relevant.* NN/g (n = 47 follow-up). | §2.4, §2.5 — readers privilege the top-left of every block; the argument for putting the number in the first clause and the first column | fetched |
| **S50** | Morkes, J., & Nielsen, J. (1997). *Concise, SCANNABLE, and Objective: How to Write for the Web.* NN/g. Peer-reviewed short form: Morkes & Nielsen (1998), *CHI 98 Conference Summary*, 321–322, DOI 10.1145/286498.286792 | §2.1, §2.4 — **cite this rather than the famous "79 % scan" article**, which gives no sample size. Three studies (n = 11, 19, 51); measured usability gains over a promotional control: scannable +47 %, concise +58 %, objective +27 %, **combined +124 %** | fetched |
| **S51** | Kaplan, J., McCandlish, S., Henighan, T., Brown, T. B., Chess, B., Child, R., Gray, S., Radford, A., Wu, J., & Amodei, D. (2020). *Scaling Laws for Neural Language Models.* arXiv:2001.08361. | **§2.5 — the best available structural model.** §1.1 "Summary" states eight findings as bolded run-in headings; results restated as reference tables at two depths; **Appendix C is titled "Caveats"** and is a plain bulleted list of what the authors are not confident about | fetched |
| **S52** | Liang, P., Bommasani, R., Lee, T., et al. (2023). *Holistic Evaluation of Language Models.* TMLR. arXiv:2211.09110. §2.4 "Roadmap". | §2.5 — the roadmap that distinguishes "what is fundamentally possible vs. what we… chose to prioritize and emphasize". One sentence in that shape converts the cancelled Wave 2 and Wave 4 into stated scope decisions | fetched |
| **S53** | Gordic, A. (2025). *Inside vLLM: Anatomy of a High-Throughput LLM Inference System.* vLLM blog, 2025-09-05. `https://vllm.ai/blog/2025-09-05-anatomy-of-vllm` | §2.5 — stated audience and stated omissions; labelled callouts (*Note*, *Assumption*, *Additional notes*, *Advanced notes*); a table of contents at both ends; and its method named as an "inverse-pyramid approach" | fetched |
| **S54** | Dettmers, T., & Zettlemoyer, L. (2023). *The case for 4-bit precision: k-bit Inference Scaling Laws.* ICML 2023. arXiv:2212.09720. | §2.5, §6 — §7 Recommendations separated from §8 Discussion & Limitations, plus **Appendix B "Further negative results"**. Maps directly onto Track A / Track B and onto S10/S11 | fetched |
| **S78** | Google. *Developer documentation style guide — Tables* (2025-03-21) and *Technical Writing One — Lists and tables* (2026-02-17). `https://developers.google.com/style/tables` | §2.3, §5.1 — "Analytic minds tend to love tables. Given a page containing multiple paragraphs and a single table, engineers' eyes zoom towards the table"; and the operational rule **"If a table cell holds more than two sentences, ask yourself whether that information belongs in some other format"** | fetched |
| **S79** | Brysbaert, M. (2019). *How many words do we read per minute? A review and meta-analysis of reading rate.* Journal of Memory and Language, 109, 104047. DOI 10.1016/j.jml.2019.104047. 190 studies, 18,573 participants. | §2.8 — silent non-fiction reading averages **238 wpm**, so this report's ≈14,150 words is about **an hour** of reading. Budget honestly. ⚠️ Do not pair with the folk claim that technical prose reads at 100–150 wpm; no peer-reviewed source for that figure exists | fetched |
| **S80** | Salager-Meyer, F. (1994). *Hedges and Textual Communicative Function in Medical English Written Discourse.* English for Specific Purposes, 13(2), 149–170. DOI 10.1016/0889-4906(94)90013-2 | §4.6 — five hedge families, usable as a "pick the one that matches your epistemic state" checklist: **Shields** (*may, suggest, indicate*) · **Approximators** (*approximately, roughly*) · **author's personal doubt** · **emotionally-charged intensifiers** · **compound hedges** (*it would seem reasonable to assume that…* — the family to ban outright) | search (paywalled; taxonomy triangulated) |
| **S81** | Hyland, K. (1996). *Writing Without Conviction? Hedging in Science Research Articles.* Applied Linguistics, 17(4), 433–454. DOI 10.1093/applin/17.4.433. Book: Hyland, K. (1998), *Hedging in Scientific Research Articles*, John Benjamins, DOI 10.1075/pbns.54. Also Hyland (1998), *Boosting, hedging and the negotiation of academic knowledge*, Text & Talk 18(3), 349–382, DOI 10.1515/text.1.1998.18.3.349 | §1.1, §4.6 — hedging is a purposeful pragmatic resource matched to the writer's warrant, not stylistic weakness; and hedges and **boosters** ("clearly", "demonstrate", "in fact") are one continuum, which is why §4.6 calibrates in both directions | fetched (Applied Linguistics page) |
| **S82** | Boutron, I., Dutton, S., Ravaud, P., & Altman, D. G. (2010). *Reporting and Interpretation of Randomized Controlled Trials With Statistically Nonsignificant Results for Primary Outcomes.* JAMA, 303(20), 2058–2064. DOI 10.1001/jama.2010.651. And Boutron et al. (2014), *Impact of Spin in the Abstracts…* J Clin Oncol, 32(36), 4120–4126, DOI 10.1200/JCO.2014.56.7503 | §1.7, §6.3 — "spin" appears in 37.5 % of Results sections and 58.3 % of Conclusions reporting nonsignificant primary outcomes; and the 2014 randomised trial shows readers rate a treatment more favourably from a spun abstract than from an accurately hedged rewrite of the same result. **The citation for calibration on grounds of reader harm rather than taste** | search (paywalled) |
| **S83** | Lipton, Z. C., & Steinhardt, J. (2019). *Troubling Trends in Machine Learning Scholarship.* ACM Queue, 17(1), 45–77. DOI 10.1145/3317287.3328534. arXiv:1807.03341. | **§4.6, §6 — the most on-topic craft citation in ML.** Four named failure modes: conflating explanation with speculation; **failure to identify the true source of an empirical gain**; "mathiness"; and misuse of suggestive or anthropomorphic language. The second is exactly the ratio-confound (G13) and PN-23's unestablished mechanism | fetched |
| **S84** | Might, M. *Shell scripts for passive voice, weasel words, duplicates.* `https://matt.might.net/articles/shell-scripts-for-passive-voice-weasel-words-duplicates/` | §8 — an `egrep` lint wireable into the manuscript Makefile. Verified word list: *many, various, very, fairly, several, extremely, exceedingly, quite, remarkably, few, surprisingly, mostly, largely, huge, tiny, excellent, interestingly, significantly, substantially, clearly, vast, relatively, completely*, plus "a number of" | fetched (no publication date available) |
| **S85** | Lones, M. A. (2024). *Avoiding common machine learning pitfalls.* Patterns, 5(10), 101046. DOI 10.1016/j.patter.2024.101046. arXiv:2108.02497. | §4.6, §7 — §5.1 "Don't assume a bigger number means a better model", §5.5 "Don't always believe results from community benchmarks", **§6.3 "Don't generalise beyond the data"**. The last is this project's own "an underpowered result reported as a ranking is worse than no result", with a peer-reviewed citation | fetched |

### 9.8 Statistics, nulls and equivalence — the extended set

| # | source | supports | ver. |
|---|---|---|---|
| **S58** | Fagerland, M. W., Lydersen, S., & Laake, P. (2014). *Recommended tests and confidence intervals for paired binomial proportions.* Statistics in Medicine, 33(16), 2850–2875. DOI 10.1002/sim.6148 | **§6.4 — resolves PN-40's self-flagged caveat.** Gives the recommended tests and intervals for paired binomial proportions at small discordant counts, which is the regime PN-40 is in | Crossref-verified |
| **S59** | Fagerland, M. W., Lydersen, S., & Laake, P. (2013). *The McNemar test for binary matched-pairs data: mid-p and asymptotic are better than exact conditional.* BMC Medical Research Methodology, 13, 91. DOI 10.1186/1471-2288-13-91 | §6.4 — "One disadvantage with the exact test is conservatism: it produces unnecessary large p-values and has poor power"; type-I error stays "barely above 3 %" even at 100 pairs. Why 3 discordant pairs could never reach 0.05 | Crossref-verified |
| **S60** | Tarone, R. E. (1990). *A Modified Bonferroni Method for Discrete Data.* Biometrics, 46(2), 515–522. DOI 10.2307/2531456 | §6.4 — formalises the **minimum attainable p-value** for a discrete test statistic. PN-40's arithmetic has a citation | Crossref-verified |
| **S61** | Bowyer, S., Aitchison, L., & Ivanova, D. R. (2025). *Position: Don't Use the CLT in LLM Evals With Fewer Than a Few Hundred Datapoints.* ICML 2025 (Spotlight Position Paper), PMLR 267, 81143–81184. arXiv:2503.01747 | **§4.4 — the most load-bearing new statistics citation for this report.** CLT error bars "dramatically underestimate uncertainty" below a few hundred datapoints; **Wilson score intervals are the preferred frequentist choice**, Clopper–Pearson "overly conservative (too wide)", and bootstrap/CLT "systematically under-cover" on non-linear metrics. At n = 164 and n = 49 this study is inside that failure regime, and the Wilson choice already made is independently endorsed | fetched |
| **S62** | Bloom, H. S. (1995). *Minimum Detectable Effects: A Simple Way to Report the Statistical Power of Experimental Designs.* Evaluation Review, 19(5), 547–556. DOI 10.1177/0193841X9501900504 | §6.4 — the origin of MDE as a reporting convention | Crossref-verified |
| **S63** | Hoenig, J. M., & Heisey, D. M. (2001). *The Abuse of Power: The Pervasive Fallacy of Power Calculations for Data Analysis.* The American Statistician, 55(1), 19–24. DOI 10.1198/000313001300339897 | §6.4 — observed/post-hoc power computed from your own result is a fallacy. Report a design-stage MDE instead | Crossref-verified |
| **S64** | Lakens, D. (2022). *Sample Size Justification.* Collabra: Psychology, 8(1), 33267. DOI 10.1525/collabra.33267 | **§1.4, §4, §7 — six legitimate sample-size justifications, two of which describe this study: resource constraints, and explicitly acknowledging the absence of a justification.** Converts "GPU hours are the scarce resource" into a cited methodological position | Crossref-verified |
| **S86** | Greenland, S., Senn, S. J., Rothman, K. J., Carlin, J. B., Poole, C., Goodman, S. N., & Altman, D. G. (2016). *Statistical tests, P values, confidence intervals, and power: a guide to misinterpretations.* European Journal of Epidemiology, 31(4), 337–350. DOI 10.1007/s10654-016-0149-3 | §6.3 — numbered misinterpretations #4 ("A nonsignificant test result means the test hypothesis is true or should be accepted. No!"), #6, #24 and #25. **The checklist to write the null-reporting rule against** | fetched (PMC) |
| **S87** | Simonsohn, U. (2015). *Small Telescopes: Detectability and the Evaluation of Replication Results.* Psychological Science, 26(5), 559–569. DOI 10.1177/0956797614567341 | §6.3 — distinguishes "too noisy to say anything" from "actively indicates the effect is undetectably different from zero". Exactly the distinction between PN-40's corrected reading and PN-28's original one | Crossref-verified |
| **S88** | Reimers, N., & Gurevych, I. (2017). *Reporting Score Distributions Makes a Difference.* EMNLP 2017, 338–348. DOI 10.18653/v1/D17-1035 | §5.0 — seed choice alone produces statistically significant differences between identical systems (≈1 F₁ on NER) | Crossref-verified |
| **S76** | Reimers, N., & Gurevych, I. (2018). *Why Comparing Single Performance Scores Does Not Allow to Draw Conclusions About Machine Learning Approaches.* arXiv:1803.09578 | §5.0 — **type-I errors in up to 26 % of cases at p < 0.05 on CoNLL-2003 when the two "approaches" are identical.** The strongest single number for banning single-score rankings | fetched |
| **S89** | Dror, R., Baumer, G., Shlomov, S., & Reichart, R. (2018). *The Hitchhiker's Guide to Testing Statistical Significance in Natural Language Processing.* ACL 2018, 1383–1392. DOI 10.18653/v1/P18-1128. Book form: Dror, Peled-Cohen, Shlomov & Reichart (2020), Springer, DOI 10.1007/978-3-031-02174-9 | §4 — the test-selection protocol; the field-level warrant for foregrounding a test choice. ⚠️ Cite the Springer DOI for the book, not the retired Morgan & Claypool one | Crossref-verified |
| **S90** | Henderson, P., Islam, R., Bachman, P., Pineau, J., Precup, D., & Meger, D. (2018). *Deep Reinforcement Learning That Matters.* AAAI 2018, 32(1). DOI 10.1609/aaai.v32i1.11694. arXiv:1709.06560 | §5.0, §7 — non-determinism and variance make baseline comparisons unreliable; the precedent for "the same config, run again, is not the same number" | Crossref-verified |
| **S91** | Agarwal, R., Schwarzer, M., Castro, P. S., Courville, A., & Bellemare, M. G. (2021). *Deep Reinforcement Learning at the Edge of the Statistical Precipice.* NeurIPS 34. arXiv:2108.13264 | §4.4 — the few-runs regime: stratified bootstrap CIs, performance profiles and the interquartile mean instead of point estimates. Directly applicable to n = 3 medians. ⚠️ The circulating page range 29304–29320 is from BibTeX, not the proceedings page | fetched |
| **S92** | Heineman, D., Hofmann, V., Magnusson, I., Gu, Y., Smith, N. A., Hajishirzi, H., Lo, K., & Dodge, J. (2025). *Signal and Noise: A Framework for Reducing Uncertainty in Language Model Evaluation.* arXiv:2508.13144 | §5.2 — formalises **signal** (a benchmark's ability to separate models) and **noise** (its sensitivity to random variation). **This is the framework that makes "this instrument cannot resolve these arms" a property of the instrument rather than an excuse** — and it is the closest thing to a name for this report's central claim | fetched |
| **S93** | Rababah, B., Qamar, S., Sparrenberg, L., Sifa, R., Kantarcioglu, M., Akcora, C. G., & Leung, C. K. (2026). *The Illusion of Equivalency: Statistical Characterization of Quantization Effects in LLMs.* arXiv:2607.08734 | **Missing related work, and concurrent confirmation.** Proposes a decision-level "Correctness Agreement" metric and finds behavioural shift "even when accuracy and perplexity are preserved" — this report's thesis reached independently, in the same domain, by a different route. Citing it strengthens the contribution rather than threatening it | fetched |
| **S94** | Keller, D., Kwegyir-Aggrey, K., Steed, R., Rao, A. K., Sharp, J. L., & Bergman, A. S. (2026). *Expanding the AI Evaluation Toolbox with Statistical Models.* NIST AI 800-3. DOI 10.6028/NIST.AI.800-3 | §4.4, §7 — a standards-body distinction between **benchmark accuracy** (performance on the fixed item set) and **generalized accuracy** (the superpopulation), with the note that generalized CIs are wider. The citation for saying an interval on 164 HumanEval+ problems bounds *this benchmark*, not the model | fetched |
| **S95** | Piaggio, G., Elbourne, D. R., Pocock, S. J., Evans, S. J. W., & Altman, D. G., for the CONSORT Group (2012). *Reporting of Noninferiority and Equivalence Randomized Trials: Extension of the CONSORT 2010 Statement.* JAMA, 308(24), 2594–2604. DOI 10.1001/jama.2012.87802 | §6.2 Pattern 3 — the cross-disciplinary reporting template for an equivalence claim: state the margin, justify it, report the interval against it | Crossref-verified |

### 9.9 Corrections, negative results and artifact conventions — the extended set

| # | source | supports | ver. |
|---|---|---|---|
| **S65** | NeurIPS. *Paper Checklist Guidelines.* `https://neurips.cc/public/guides/PaperChecklist` | **§6 — "Reviewers will be specifically instructed to not penalize honesty concerning limitations."** Also item 7: error bars must state the factors of variability they capture, the calculation method, and whether they are a standard deviation or a standard error; item 1 requires abstract and introduction claims to match what the results support | fetched |
| **S66** | Rohrer, J. M., Tierney, W., Uhlmann, E. L., et al. (2021). *Putting the Self in Self-Correction: Findings From the Loss-of-Confidence Project.* Perspectives on Psychological Science, 16(6), 1255–1269. DOI 10.1177/1745691620964106 | §6 — ~12 % of 316 researchers reported a qualifying loss of confidence in their own published work, but it "was a matter of public record in fewer than a fifth of the reported cases (17 %)". The base rate that makes visible self-correction a contribution | fetched (PMC) |
| **S67** | *I Can't Believe It's Not Better* workshop series. `https://icbinb.cc/` · CfP `https://i-cant-believe-its-not-better.github.io/neurips2020/cfp/`. PMLR volumes v137, v163, v187, v239, v296. Peer-reviewed position paper: Karl, F., Kemeter, L. M., Dax, G., & Sierak, P. (2024). *Position: Embracing Negative Results in Machine Learning.* ICML 2024, PMLR 235, 23256–23265. arXiv:2406.03980 | §6 — the review criteria include "**Vulnerability and honesty in discussion, particularly if the submission is by the original author**" and "Quality of discussion of limitations". Karl et al. is the top-venue, peer-reviewed form: "predictive performance alone is not a good indicator for the worth of a publication". ⚠️ No ICBINB position or retrospective paper by the organisers exists — cite the CfP or Karl et al. | fetched |
| **S68** | Brown, T. B., Mann, B., Ryder, N., et al. (2020). *Language Models are Few-Shot Learners.* NeurIPS 33. arXiv:2005.14165, §2.2 and §4. | **§6.5(a) — the best published model for disclosing a defect you cannot afford to fix**, quoted there. Names the bug, says why it was not fixed, commits to quantifying the consequence, and acts on it in the tables (asterisked rows; suppressed datasets) | fetched |
| **S69** | *ReScience C.* `http://rescience.github.io/`, ISSN 2430-3658. | §6.5(b) — accepts negative results explicitly ("a failure to replicate the original results") with a due-caution protocol, and uses a **typed outcome notation** in titles: `Re` / `Rp`, negated as `¬Re` / `¬Rp`. Prior art for tagging each finding confirmed / scoped / corrected / withdrawn. Related: the ML Reproducibility Challenge, `https://reproml.org/`, whose CfP solicits "positive confirmations of prior results, partial replications, and failures to reproduce", and states that "reproducibility is not a binary outcome" — the warrant for **per-claim rather than per-paper verdicts** | fetched |
| **S70** | NISO. *RP-31-2021, Reproducibility Badging and Definitions.* NISO, 2021. DOI 10.3789/niso-rp-31-2021. ISBN 978-1-950980-03-1 | §6.5(b) — "**Partially replicable findings… should be made visible in some way in the scholarly record.**" ⚠️ **Trap: NISO's Appendix A quotes ACM's pre-swap v1.0 definitions and contradicts NISO's own §2.** Cite §2, never Appendix A | fetched |
| **S71** | Wager, E., Barbour, V., Yentis, S., & Kleinert, S., on behalf of COPE Council (2009). *Retractions: Guidance from the Committee on Publication Ethics (COPE).* | §6.5(c) — the correction-versus-retraction threshold, and the requirement to "state the reason(s) … to distinguish misconduct from honest error" | search |
| **S72** | Berger, E. D., Blackburn, S. M., Hauswirth, M., & Hicks, M., for the ACM SIGPLAN Executive Committee (2018). *SIGPLAN Empirical Evaluation Checklist.* `https://www.sigplan.org/Resources/EmpiricalEvaluation/` | **§4.1 — "Inappropriate level of precision: reporting '49.9 %' when the experimental error is ±1 % overstates the level of precision" (this is PN-64 by name).** Also "Insufficient information to repeat" (all version numbers and full hardware details), "No data distribution reported", and "Insufficient number of trials" — "Failure to do so risks treating noise as signal" | fetched |
| **S73** | Raasveldt, M., Holanda, P., Gubner, T., & Mühleisen, H. (2018). *Fair Benchmarking Considered Difficult: Common Pitfalls In Database Performance Testing.* DBTest '18, ACM, 1–6. DOI 10.1145/3209950.3209955 | **§5.0 — "Cold vs Hot Runs" and "Cold vs Warm Runs" are named standard pitfalls; the depth-0-versus-at-depth finding is that pitfall exactly.** "Overly-Specific Tuning" is the frame for the `-ts` caveat. Also worth copying: its rhetorical restraint — "we refrained from [citing examples] since research is hardly advanced by pointing fingers" | fetched (PDF) |
| **S74** | Mytkowicz, T., Diwan, A., Hauswirth, M., & Sweeney, P. F. (2009). *Producing wrong data without doing anything obviously wrong!* ASPLOS '09, ACM, 265–276. DOI 10.1145/1508244.1508275 | §5.0, §7 — measurement bias from apparently irrelevant environmental factors can exceed the effect being measured. The citation for the ±100–200 MiB allocator noise and for "single failures lie" | Crossref-verified |
| **S75** | MLCommons. *MLPerf® Results Messaging Guidelines.* `https://github.com/mlcommons/policies/blob/master/MLPerf_Results_Messaging_Guidelines.adoc` (cite with commit or access date). Benchmark paper: Reddi, V. J., Cheng, C., Kanter, D., Mattson, P., Schmuelling, G., Wu, C.-J., et al. (2020). *MLPerf Inference Benchmark.* ISCA 2020, 446–459. DOI 10.1109/ISCA45697.2020.00045 | §4.5, §5.0 — an industry standards body formally forbids comparing results across differing versions, scenarios or verification status, and requires unverified results to be labelled "unverified". **The strongest institutional precedent for the protocol-labelling rule** | fetched |
| **S96** | Kurtic, E., Marques, A., Pandit, S., Kurtz, M., & Alistarh, D. (2025). *"Give Me BF16 or Give Me Death"? Accuracy-Performance Trade-Offs in LLM Quantization.* ACL 2025. arXiv:2411.02355. | **Missing related work, and the best structural model available.** Verified section order: 1 Introduction · 2 Background · 3 Benchmark Design and Setup · 4 Quantization Impact on Accuracy (**4.4 Text Similarity Investigation** — the same argument this report makes with KL divergence) · 5 Quantized Inference Performance · 6 Conclusion · **Limitations** · A.3 **GPU Pricing**. Its Limitations section names **KV-cache quantization** as an open question, which is a direct positioning hook for PN-15. Moves to copy: numbered findings in the abstract; greedy sampling declared as a reproducibility choice; a cost appendix | fetched |
| **S97** | Bertinetto, L., Henriques, J. F., Albanie, S., Paganini, M., & Varol, G. (2021). *Preface*, NeurIPS Pre-registration Workshop. PMLR 148:i. And Nosek, B. A., Ebersole, C. R., DeHaven, A. C., & Mellor, D. T. (2018). *The preregistration revolution.* PNAS, 115(11), 2600–2606. DOI 10.1073/pnas.1708274114 | §4 — the warrant for the pre-registered interpretation bands (DEC-11), and for reporting post-hoc findings honestly *as postdictions*. The preface is on-thesis: "heavy reliance upon performance as a proxy for scientific progress may have limitations… Since typically only positive results are rewarded, the negative results inevitably encountered during research are often omitted" | fetched |
| **S55** | Krishnamurthi, S. *Artifact Evaluation guidelines.* `https://artifact-eval.org/guidelines.html` | §3.10 — for artifacts that cannot be redistributed or that need >24 h of execution, "a detailed screen-cast of the tool along with the results" is accepted. **The nearest published guidance to this situation: when re-running is impossible, preserved evidence of the original run is the accepted substitute** | fetched |
| **S56** | cTuning Foundation. *Artifact Reviewing Guide (V20201122).* `https://ctuning.org/ae/reviewing-20201122.html` | §3.10 — "the variation of empirical and numerical results is tolerated. In fact it is often unavoidable in computer systems research" | fetched |
| **S57** | Hinsen, K. (2019). *Dealing With Software Collapse.* Computing in Science & Engineering, 21(3), 104–108. DOI 10.1109/MCSE.2019.2900945 | §3.10 — the standard framing for software becoming unrunnable because its environment moved, i.e. a deleted engine image. ⚠️ Metadata Crossref-verified; full text paywalled and not read — **do not quote from it** | Crossref only |

### 9.10 Citation hygiene — a rule this research earned the hard way

During the research for this guide, an automated page-summarisation tool returned a **confidently
fabricated** answer: asked to summarise Levin & Redell's 1983 SOSP paper, it reported the document
as Peyton Jones' *How to Write a Great Research Paper* in the *Journal of Functional Programming*
and supplied five invented quotations. It was caught only by extracting the PDF text directly. A
separate search summary misattributed arXiv:2508.08531 to Georgi Gerganov, who has no arXiv paper
for llama.cpp.

**Therefore, a rule for the drafting, and it is not optional in a report whose thesis is about
measurement honesty:**

> No source enters `references.bib`, and no quotation enters the manuscript, on the strength of a
> summary. Every cited claim is verified against the primary document — the PDF, the abstract page,
> or the policy page itself — and the `.bib` entry records the access date.

Entries above marked *search*, *Crossref only* or *paywalled* have **not** met that bar for their
*content* (their bibliographic data is verified) and must be checked before any of their language is
quoted: S9, S10, S11, S13, S14, S15, S16, S18, S19, S20, S22, S36, S37, S46, S57, S71, S80, S82.
Additionally, the following need volume, issue or page numbers confirmed: Fleming & Wallace (1986),
Bailey (1991), Jain (1991), and Whitesides' body text (only image-scanned copies located).

**Eight specific traps found during this research. Each one would have produced a wrong `.bib`
entry or a wrong quotation:**

1. **A page-summarisation tool fabricated a whole document.** Asked for Levin & Redell 1983, it
   returned Peyton Jones' paper in the *Journal of Functional Programming* with five invented
   quotations. Only direct PDF extraction caught it.
2. **"The Importance of Being Negative" does not exist.** No paper of that title is findable in any
   venue or on any ICBINB page. If it appears in a draft, it was hallucinated. The real citation is
   Karl et al., ICML 2024 [S67].
3. **Pineau et al. (JMLR) has no DOI.** The circulating `10.5555/3546258.3546422` is an ACM Digital
   Library internal identifier; Crossref returns "Resource not found". Cite the JMLR URL and the
   arXiv ID [S23].
4. **`ReproducibilityChecklist.pdf` silently serves v2.0** while the JMLR paper describes v1.2. The
   item lists differ — v2.0 adds a runtime/energy item and merges the error-bar item. Cite the
   versioned URL for whichever you quote.
5. **NISO RP-31-2021's Appendix A contradicts its own §2**, because the appendix still quotes ACM's
   pre-swap v1.0 definitions. Cite §2 [S70].
6. **ACM's badging v1.1 inverted v1.0's terms** for *reproducibility* and *replication*, and ACM
   retroactively updated prior badges. Name the version. `acm.org` returns 403 to every automated
   client; the verified text above comes from Wayback captures and should be re-checked in a browser
   before submission.
7. **Crossref's registered titles differ from common usage** in two cases: Amrhein, Greenland &
   McShane's *Nature* comment is registered as "Scientists rise up against statistical significance"
   (not "Retire statistical significance"), and Wasserstein & Lazar is "The ASA Statement" (not
   "The ASA's Statement"). A search misattributed arXiv:2508.08531 to Georgi Gerganov, who has no
   arXiv paper for llama.cpp.
8. **A LaTeX `\today` artifact.** Regenerated arXiv HTML prints "August 24, 2026" under the author
   block of arXiv:2404.10102 and arXiv:2204.06745. That is not a paper date.

One live gap in the project's own corpus, surfaced by this research: **the Unsloth quantization
documentation URLs that back the cited KL-divergence table now return 404.** Until the page is
re-located, that table is archived-evidence-only (`/srv/bench/kl-evidence/`) and must be labelled as
figure-read from an archived copy, with the retrieval date.

### 9.11 Sources this guide deliberately does not use

- **Style manuals of general English prose** (Strunk & White, Williams). Their advice is real but
  under-determined for this problem, and citing them invites a tone this readership reads as
  literary rather than technical. The specific rules that matter are in §1.7 and §4, stated
  operationally.
- **Generic "how to write a limitations section" web guidance.** Superseded by S13, which is a
  peer-reviewed treatment with a usable principle (steel-person) rather than a list.
- **viXra/arXiv comparative scienceography.** Tempting for the independent-author question, but the
  finding — that single-author unaffiliated papers cluster on the lower-quality archive — is a
  correlation this report should not invoke, in either direction.


---

## 10. Addendum — what this research suggests should change in `OUTLINE.md`

Style research turned up eleven concrete defects and gaps in the plan. They are recorded here
because they are cheap to fix now and expensive to fix in LaTeX. **None is a matter of taste.**

### 10.1 Stale text the outline still carries

1. **A dangling fragment of the previous title.** Immediately after the abstract blockquote, the
   line `coding model, and what task benchmarks can and cannot bound**` sits orphaned between the
   title note and the revision warning. Delete it.
2. **The thesis paragraph is stale on its own headline sentence.** It reads "at the median, code
   tokens are perturbed 100–200× *less* than prose tokens". **PN-64 withdrew that**: the "100" is
   the reciprocal of a rounded `0.01×` table cell, the measured ratios are 199 / 181 / 206×, and the
   per-arm ordering is an artifact of print precision. Restate as "roughly two orders of magnitude",
   and do not tabulate per arm. `CITATION.cff` is already correct on this; the outline is not.
3. **The title blockquote's own correction is stale.** "Median ratio corrected to 181-206x per D-8"
   is superseded by PN-64, which says the range over-states the available resolution.
4. **§5.1's PN list omits PN-64.** It cites PN-13, 14, 21, 16 and PN-62; PN-64 corrects the section's
   headline row and must be listed.

### 10.2 Structural gaps

5. **There is no conclusion.** The outline runs §7 Threats → §8 Practitioner appendix → §9
   Reproducibility appendix. A 25-page report that ends on an appendix has no closing argument, and
   the strongest closing sentence available in the whole review corpus — the compounding question —
   has nowhere to live. Add **§8 Conclusion** and renumber the appendices A–D (§3.9).
6. **§5.2's heading contains a count the section contradicts.** "Three instruments, three bounds"
   is followed by text that lists five: multiple-choice, generative coding, retrieval, SWE-bench
   Verified and corpus perplexity. In a report about instruments that overstate what they resolve,
   this is the worst available place for an arithmetic slip. Retitle without a count.
7. **No reader's guide.** At this length and density, add three or four lines at the end of §1
   mapping reader type to section (§2.1). It costs a paragraph and it is what makes non-linear
   reading work.

### 10.3 A live statistical inconsistency — fix before drafting §5.2

8. **Three different 95 % intervals for the same paired HumanEval+ difference are in circulation,
   and the outline quotes the wrong one under the wrong label.** §5.2 states
   "−0.61 pts, 95 % CI [−2.68, +1.46]" for **HumanEval+**; PN-40's table gives that interval for
   HumanEval **base** (3 discordant pairs) and gives **[−3.28, +2.06]** for HumanEval**+** (5
   discordant). Reviewer B independently computed a Newcombe score interval of **[−4.08, +2.76]**
   for the same quantity. See §6.4 of this guide: pick one estimator, name it in §4, apply it
   throughout, and correct the outline. This is PN-20's defect — an aggregate whose estimator is
   never named — alive inside the manuscript's own planning.

### 10.4 Missing related work found while surveying the genre

Seven published papers in this exact niche are absent from the outline's §2 and from
`references.bib`. **Three of them are close enough that a reviewer will assume they were missed
rather than judged, and two of those are not merely related work — one is the report's best
structural model and the other is independent confirmation of its thesis.**

**A. The two that must be cited.**

- **arXiv:2411.02355 — Kurtic, Marques, Pandit, Kurtz & Alistarh, *"Give Me BF16 or Give Me Death"?
  Accuracy-Performance Trade-Offs in LLM Quantization*, ACL 2025** [S96]. The closest published peer.
  Its **§4.4 "Text Similarity Investigation"** makes this report's argument — that accuracy alone is
  insensitive and a distributional comparison against the unquantized model is required — by a
  different instrument. **Its Limitations section names KV-cache quantization as an open question**,
  which is a direct positioning hook for PN-15: this report answers a question that paper flagged.
  Structurally it is also the best available model (numbered findings in the abstract; greedy
  sampling declared as a reproducibility choice; a GPU-pricing appendix).
- **arXiv:2607.08734 — Rababah et al., *The Illusion of Equivalency: Statistical Characterization of
  Quantization Effects in LLMs*, 2026** [S93]. **Concurrent, independent confirmation of this
  report's thesis in the same domain**, via a decision-level "Correctness Agreement" metric, finding
  behavioural shift "even when accuracy and perplexity are preserved". Citing it strengthens the
  contribution: two groups reached the same conclusion by different routes. Failing to cite it looks
  like not having looked.

**B. The five that are useful rather than mandatory.**

9. **arXiv:2601.09527 — Knoop & Holtmann, *Private LLM Inference on Consumer Blackwell GPUs*.**
   Same hardware family (**RTX 5060 Ti**), overlapping axes (NVFP4, quantization format, context
   length 8k–64k, 79 configurations). This is mandatory related work and is also the closest
   stylistic model available. [S39]
10. **arXiv:2509.12229 — Avinash, *Profiling LoRA/QLoRA Fine-Tuning Efficiency on Consumer GPUs: An
    RTX 4060 Case Study*.** Single-author consumer-GPU profiling study; establishes the genre
    convention. [S40]
11. **arXiv:1804.06826 — Jia et al., Volta microbenchmarking**, as the form precedent for a
    self-labelled measurement technical report [S27]; and **arXiv:2404.10102 — Besiroglu et al.,
    Chinchilla replication attempt** [S41], as the template for §5.4's contradiction of a published
    losslessness claim. Both are optional in §2 and useful in §1 or §6.
12. **arXiv:2508.13144 — Heineman et al., *Signal and Noise*** [S92]. Formalises a benchmark's
    **signal** (its ability to separate models) against its **noise**. This is the nearest thing in
    the literature to a name for this report's central claim, and citing it makes "the instrument
    bounds rather than resolves" a contribution to a named framework rather than a coinage.
13. **NIST AI 800-3** [S94], for the **benchmark accuracy versus generalized accuracy** distinction
    — the standards-body warrant for saying that an interval on 164 HumanEval+ problems bounds
    *this benchmark*, not the model.

### 10.5 Two decisions the research reopens

**Category.** Reviewer B recommends `cs.LG` primary + `cs.PF` cross-list, on readership grounds, and
that recommendation stands. But note what the category text actually says: **cs.PF is "performance
measurement and evaluation"**, which is a literal description of this study's method, whereas cs.LG
is "papers on all aspects of machine learning research" [S25]. The closest comparators are split —
arXiv:2601.14277 is cs.LG-primary; arXiv:1804.06826 and several inference-benchmark papers are
cs.PF-primary. **The one condition that would flip the decision is moderation risk**: if the
submission is declined under the "not original or substantive research" clause or under the
review/position-paper practice [S1, S3], resubmit `cs.PF` primary, where a measurement study is
unambiguously on-topic. Keep the total at two categories either way — arXiv states that bad
cross-lists are removed and that more than one or two is rarely appropriate [S25].

**Title length.** 20 words against a recommended ≤ 15 [S32]. A compliant trim is given in §3.0. The
current title is defensible; the point is not to grow it.

