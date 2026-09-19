# JUDGING PENDING — S15 AA-LCR answers are NOT scored yet

**Owner decision, 2026-09-15:** no judge runs during S15. Every AA-LCR answer is logged judge-ready, and **one agent
judges everything at once after ALL S15 tiers have finished.** The judge model is **left open** (the owner may or may not
use Opus 5 at max effort). Do not report any AA-LCR score before this file is closed.

Paper records: `~/repos/multivac-paper` — plan §S15 and DEC-16; METHOD-REFERENCES R24/R25.

## What the judge must do (replicates Artificial Analysis AA-LCR v1.1)

- Equality checker only: it sees the **question (for reference only), the official answer, and the candidate's final answer**.
  It never sees the documents and never sees the model's reasoning trace.
- Use the v1.1 **system prompt** and **user prompt** verbatim from the dataset card
  (`/srv/bench/e12/s15/data/aa-lcr/README.md`, section "Scoring Approach"). Artificial Analysis uses GPT-5.6 Luna (medium);
  whatever judge is chosen must be recorded and every table must carry that difference as a label.
- Verdict per item: `CORRECT` or `INCORRECT`. Record the judge's raw reply.
- Recommended quality controls (owner to confirm): fresh context per item; a second independent judge on every item;
  disagreements to a third; report Cohen's κ.
- Truncated answers (`finish_reason == "length"`, or no committed final answer) are scored `INCORRECT` **and** counted
  separately as truncated — never folded silently (PN-60).

## Added after the independent review (DEC-17)

- A different judge from Artificial Analysis's changes scores: run a **second independent judge on every item**, report
  Cohen's κ, send disagreements to a third, and **hand-audit a sample of the disagreements**. Record judge model id and
  effort in every output line and in the paper tables.
- Licensing: AA-LCR questions and answers are Apache-2.0, but the **document texts are third-party and unlicensed by
  Artificial Analysis** — never republish document text or long quoted spans in judge logs meant for publication.
- The judge must never see `reasoning_content` (GPQA-style provisional answers appear in reasoning traces too).

## Where the inputs will be

- `/srv/bench/e12/s15/results/aa-lcr/<quant>-<drafter>/answers.jsonl` — one line per question with: `question_id`,
  `document_set_id`, `question`, `official_answer`, `candidate_answer` (final content only), `reasoning_content`
  (kept for audit, **not** shown to the judge), `finish_reason`, token counts, timings, drafter stats, KV dtype,
  window, server config hash, image digest, sampling, seed, UTC timestamps.
- `/srv/bench/e12/s15/results/aa-lcr/JUDGE-INPUT.jsonl` — built after the last tier: one line per (quant, drafter,
  question) with only the three judge inputs plus an opaque `item_id`, and the two prompts pre-rendered.
- Output expected from the judge: `/srv/bench/e12/s15/results/aa-lcr/JUDGE-OUTPUT-<judge>.jsonl`
  (`item_id`, verdict, raw reply, judge model id, effort, UTC).

## Status

- [x] All S15 tiers finished (CHAIN S15 COMPLETE 2026-09-19T15:12:38Z, serving restored)
- [x] JUDGE-INPUT.jsonl built and checksummed (260 items, sha256 73e4f91f374642031a1cfb7754c7bae7b9c595470851d798e98584a88d4d48e2)
- [x] Judge models: primary muse-spark|xhigh, second gpt-5.6-luna|medium, third deepseek-ai/DeepSeek-V4.1-Flash|max (disagreements only)
- [x] Judging run (primary): JUDGE-OUTPUT-muse-spark-xhigh.jsonl 219/260, sha c78cff1b92b8015c4e092825e37024b6a8245069b01fde3a372ee4fc7826cd09
- [x] Second judge + kappa: JUDGE-OUTPUT-gpt-5.6-luna-medium.jsonl 222/260, sha fbf691c464748ba6d4b3f728024991d61b94c4a2e4960c4f6d4de5170c124275; Po 0.9577 Pe 0.7422 kappa 0.8359, 11 disagreements
- [x] Third judge + hand-audit: JUDGE-OUTPUT-deepseek-v4.1-flash-max.jsonl 11 lines, sha bcebc991e6aa9c81dcd1652c5c14e6538b0f98651d2a51670df8a97dc574b454; resolved JUDGE-OUTPUT-resolved-majority.jsonl 260 lines 217/260, sha 971245decb1988c22a92357ab0b91aad63a6f880f393792f3499a300d0fb4329; hand-audit 5/11, no pipeline defect
- [x] Scores written to paper notes (PN-86..PN-95) and this file closed 2026-09-19

CLOSED: resolved AA-LCR 217/260 (83.5%) is the paper-reportable row; report with judge IDs and efforts; Fleiss kappa on disagreements is degenerate and must not be reported; see PN-94/PN-95.
