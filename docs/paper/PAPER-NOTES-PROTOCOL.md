# PAPER-NOTES protocol — reusable findings for the Track B technical report

Every conductor worker (implementer, fixer, architect) that touches experiments or data
MUST, as part of its finish contract, append candidate paper material to this file.
Reviewers check for it; a stage that produced measurements but appended no paper notes is
an incomplete stage (reviewer should raise a finding).

## Why
The lifecycle ledger records what was done; this file extracts what the *paper* can say.
The agents who will write the technical report later should find ready-to-reuse,
evidence-cited lines here instead of re-mining raw artifacts.

## Where and what to append

Append under the matching section below (create the section if missing), in this exact
entry format:

```
- PN-<n> | <ISO datetime> | <stage/phase> | <model-id> | <ledger ref L-n>
  Finding: <one self-contained sentence, paper-grade prose, no jargon shorthand>
  Evidence: <exact artifact path + the number(s), with CI/n when applicable>
  Use as: <which paper section this serves — e.g. "§Results/tok-s", "§Context axis", "§Systems findings">
  Caveat: <any reproducibility/provenance warning that must travel with the claim — image id, protocol label, KV-UNKNOWN, etc.>
```

Numbering: PN IDs are global and monotonic (read the last entry before appending; never
renumber, never edit an old entry — supersede with a new one).

## Rules for a good paper note
1. **Self-contained**: a reader who sees only this line must understand the claim.
2. **Quantified**: every claim carries its number, n, CI, and conditions (context depth,
   quant, spec method, sampling settings).
3. **Protocol-honest**: never mix PPL protocols, depth-0 vs at-depth speed, or
   irreproducible-on-current-images rows without the caveat field.
4. **Cite the artifact**, not the chat: Evidence must be a path under /srv/bench/ or the
   local data/ mirror.
5. **Both tracks aware**: mark whether the note serves Track A (machine config) or Track B
   (neutral report) or both — Track B notes must NOT inherit Track A's priority ordering.
6. **Contradictions are gold**: if a new measurement contradicts CLAUDE.md/PAPER-REFERENCES,
   write the note AND flag the doc section that needs the correction in your ledger entry.

## Sections
- §Sampling & protocol — official Qwen/Unsloth settings effects, greedy vs official deltas,
  thinking-mode findings (empty-rate, reasoning_effort equivalence).
- §Context axis — ceilings, depth degradation, NIAH retrieval, KV-dtype effects.
- §Speculative decoding — MTP/DFlash sweeps, acceptance-vs-depth, losslessness caveats (G8).
- §Quant ladder — accuracy/PPL/NLL ordering, KL, HumanEval/SWE/LCB numbers per quant.
- §Systems findings — dual-card behavior, -ts rebalance, -fit, split modes, VRAM model.
- §Efficiency — tok/s, prefill, J/tok, power.
- §Agentic behavior — step counts, convergence, SWE-bench results.
- §Reproducibility & provenance — image/engine versions, seeds, CI conventions, exclusions.
