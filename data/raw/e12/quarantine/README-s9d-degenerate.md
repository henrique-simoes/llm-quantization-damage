# Quarantined: S9d/S9e cells with degenerate generation (2026-09-01)

`s9d-depthsweep.json.degenerate-17tok-20260901` — 23 of 24 cells reported `ok` and `valid`, and
every one of them is meaningless.

**Defect.** The cell prompt was the raw pad posted to `/v1/chat/completions` as a user message with
`max_tokens: 512`. Given 123,666 tokens of django source and no instruction, the model replies with
a short acknowledgement and emits EOS: **every one of the 69 reps generated exactly 17 tokens**
(min = median = max = 17). Consequently

* `decode_tok_s` is a 17-token measurement dominated by the first decode steps after a deep
  prefill — not throughput. It produced the absurd reading of 52.27 tok/s at 131,072 for n=8,
  faster than most configurations manage at depth 0.
* `acceptance` reads exactly **1.000 in all 23 cells** because it is computed over 36-48 draft
  events on a trivially predictable continuation.

**Root cause, and why the harness did not catch it.** The `valid` gate asserted `prefill_frac >=
0.90` — which passed at 0.9435 — but nothing asserted that the model actually GENERATED what was
asked. The prefill contract was in code; the generation contract was only in the docstring. That is
PN-5's lesson ("a documented contract that is not asserted in code is not a contract") recurring in
the same harness that was written to honour it.

**The working pattern, which was already on disk.** `tsweep_v2.py` uses `/completion` with
`prompt = pad + "\n\n# Summary:\n"` and `n_predict`, not a chat message — every Wave-1 cell
generated its full 192 tokens with realistic acceptance (0.495-0.911). The Wave-1 corpus and every
paper note resting on it are UNAFFECTED.

**Reach.** The same construction was used by `s8_spec.py --phase atdepth`, so **S8's at-depth cells
share the defect**: their serverlogs show `eval time = 951.92 ms / 17 tokens` and
`draft acceptance = 1.00000 (16 accepted / 16 generated)`. PN-24's at-depth half is withdrawn by
PN-30; its ctx-32,768 half (medians over 164 real generations) stands.
