# `manuscript/` — the arXiv technical report

**This is the project's deliverable.** Everything else in the repository is either evidence for it,
a record of how the evidence was produced, or tooling that produced it.

**Status: not yet drafted.** Measurement is complete (see the root `CLAUDE.md` §"Where the work
stands"). The findings exist as 25 evidence-cited paper notes in `../docs/paper/PAPER-NOTES.md`;
`OUTLINE.md` here maps them onto a paper structure. Writing is the remaining work.

## Contents

| file | what |
|---|---|
| `OUTLINE.md` | section-by-section plan, each claim mapped to its paper note and artifact, with what is missing |

Add as drafting proceeds: `sections/`, `figures/`, `refs.bib`, `main.tex` (or Markdown → Pandoc).

## The rules that govern what may enter the paper

These are not stylistic. Each one exists because violating it has already produced a wrong number
in this project.

1. **Every claim carries n, its interval, and its protocol label.** A claim enters only if the
   intervals separate or the effect exceeds the interval width; otherwise it is reported as
   "indistinguishable at n = …", which is itself a finding here.
2. **Never mix protocols in a table.** Perplexity protocols 1, 2 and 4 are different instruments.
   Depth-0 and at-depth decode differ 3–5×. Greedy and official-sampling rows are not comparable.
3. **Label irreproducible rows.** Every measurement predating 2026-08-29 came from an engine image
   that no longer exists, and it is the only image on which `-sm tensor` ever worked.
4. **Divergence is ladder-relative.** It is measured against UD-Q6_K_XL because no FP16 reference
   fits on the host. These are distances *along the ladder*, never from the unquantized model, and
   the reference arm's own degradation is unmeasured and zero by construction.
5. **Divergence is measured on prompt tokens.** It is not a measurement of generated-code quality.
6. **State the limitations that are unflattering.** The largest — long-context task accuracy — was
   never measured for any arm. It is a stated limitation, not an omission.
