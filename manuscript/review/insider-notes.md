# Insider notes — the third opinion, explicitly NOT blind

Two reviewers are assessing this work blind. I am not one of them: I produced most of it, so my
judgement of its quality is worth less than theirs. What I can contribute instead is the thing a
blind reviewer cannot reconstruct from the documents — **which results are fragile for reasons that
are not written down**, and which failures shaped the evidence in ways only visible from the inside.

Read this alongside `reviewer-a-rigor.md` and `reviewer-b-structure.md`, not instead of them. Where
they disagree with me, prefer them: they have the distance.

---

## 1. Results whose harness was later found defective — and whether they were re-verified

Four instrumentation defects were found *after* results had been produced with the same harness
family. For each, the question a reader should ask is: were the earlier results re-checked, or
merely assumed unaffected?

| defect | found | earlier results at risk | re-verified? |
|---|---|---|---|
| PN-5 — depth gate documented but not asserted | Wave 1 review | Q4_K_XL sweep cells | **Yes** — cells quarantined, pads rebuilt, all 9 verified in `pads-manifest.json` |
| PN-17 — `±` vs `+/-` parser mismatch, 10 KLD cells scored `ok` with empty metrics | SSA | every SSA divergence number | **Yes** — recovered from preserved serverlogs by `ssa_reparse.py`; the numbers in PN-13/14/15/16/21 are the re-parsed ones |
| PN-30 — 17-token generations timed as throughput | S9d | S8's at-depth figures | **Yes, and they failed** — PN-24's at-depth half and Track A Amendment 1 withdrawn. **Wave 1 was checked explicitly and is clean** (`n_predict=192` on every cell, acceptance spread 0.495–0.911) |
| S11 pad sizing (never given a PN — see §5) | S12 prep | S11 only | S11 was abandoned; no other experiment used those pads |

**The one to state plainly in the paper:** PN-30's defect reached a published claim and a
configuration decision, both of which were withdrawn. That is the strongest evidence the process
works, and it should be *shown*, not hidden in an appendix footnote.

## 2. What is load-bearing but under-argued

**PN-26 (determinism) is doing more work than its placement suggests.** It is written as a
speculative-decoding result, but it is the *enabling* result for several others: it is why any
byte-level output comparison in this study is attributable to the variable under test rather than
to engine noise. S11 was designed on the strength of it. If a reviewer doubts PN-26, several other
comparisons weaken with it. It deserves a place in Methods, not only in §Speculative decoding.

**The reference arm is not FP16, and this propagates further than the caveat admits.** Every
divergence number is a distance *along the ladder* from UD-Q6_K_XL, whose own degradation is
unmeasured and zero by construction. The three-tier domain hierarchy (PN-21) and the code-vs-prose
ratio (PN-14) are both ratios of ladder-relative quantities. I believe they survive — a ratio of
distances from a common point is still informative about relative damage — but the paper must say
so explicitly rather than leaving the reader to work out whether the reference's own error cancels.

## 3. Where I would attack this paper if it were not mine

1. **PN-34's third leg is thin.** The saturation thesis rests on three instruments, but the RULER
   leg's discriminating result (MK-NIAH 100.0 vs 91.67) is **one failed sample out of twelve**,
   with overlapping Wilson intervals. The *saturation* half of that leg is solid (100.0/100.0 at
   three lengths, n=25/25/12). The honest construction is: three instruments show blindness; one of
   them shows a hint of sight when made harder. Written any stronger, it invites the rejection.
2. **Speed claims rest on n=3–6 against 32.9 % within-arm noise.** PN-19's "speed does not
   discriminate" is a *null under high variance*, which is exactly the inference PN-32 warns
   against elsewhere in the same paper. The paper must not use a null this way in §5.5 while
   criticising it in §5.4.
3. **Energy is modelled, not measured.** `est_system_w` is GPU telemetry + RAPL + a fixed platform
   allowance. There is no wall-socket sensor on this host. Any kWh figure must carry that.
4. **PN-9 is unresolved after two attempts** (S9d and its re-run). The paper reports acceptance as
   quant-specific with a confound it explicitly failed to remove. Either retreat to the sign-test
   result (12/13 pairs, p=0.0017) or state the confound in the claim itself.
5. **The historical corpus is irreproducible.** Everything before 2026-08-29 came from an engine
   image that no longer exists, and it is the only image on which `-sm tensor` ever worked. Any
   table mixing those rows with current ones needs the label, every time.

## 4. What is stronger than the notes make it sound

- **PN-13's cost asymmetry is the paper's most quotable fact** and is currently buried in a caveat:
  ~20 minutes of GPU per arm separates these quantizations at 3.7–11.8 σ, where roughly 20 hours of
  task benchmarking across three modalities separates them nowhere. That belongs in the abstract.
- **The KLD-vs-PPL contrast in PN-15** is a clean, self-contained demonstration of averaging bias
  on an *identical* pair: PPL moves +0.15 % while the distribution demonstrably moves. It is a
  better argument against perplexity than the citation to R2/R4, because it is ours and it is
  controlled.
- **PN-6 (the ceiling belongs to the split) is genuinely useful to practitioners** and is
  independent of the paper's main thesis. It may be the most-cited result even if it is not the
  most interesting one.

## 5. Gaps in the record itself

- **The S11 pad-sizing defect has no PN entry.** It is documented in
  `data/raw/e12/quarantine/README-s11-padoverflow.md` and in the harness docstring, but it never
  received a paper note, unlike the other six defects. Either write it up (it is a good instance —
  a constant used where a tokenizer was required, in a file that cites PN-5) or state that S11 is
  excluded entirely and the defect with it.
- **S12's `variable_tracking` exclusion is recorded only inside the artifact JSON.** It is a
  legitimate methodological decision — two measured budgets, both floor-scored, the reference arm
  scoring *below* the cheaper arm — and it should be visible in the paper's appendix, not only in
  `s12-ruler.json`.
- **No PN entry covers the S9e result** that MTP n=8 fails to load at 262,144. It sits in PN-32's
  evidence line. It is small but it is the only measurement of that ceiling.

## 6. Process facts worth reporting as method

Three claims were withdrawn during the work (PN-24's at-depth half, S8's at-depth figures, Track A
Amendment 1). Two experiments were designed, built and abandoned on their own evidence (S10 on a
measured memory ceiling, S11 on a measured metric failure). One battery was invalidated by its own
supervision tooling (PN-27). None of this was discovered by a reviewer; all of it was caught by
gates the project wrote for itself, and every instance is preserved in `quarantine/` rather than
deleted.

For a paper whose thesis is *"the instruments the field trusts cannot see what they claim to
measure"*, a demonstrated willingness to discard one's own instruments is not an embarrassment. It
is the argument.
