# PAPER-NOTES — candidate lines for the Track B technical report

Protocol: `docs/paper/PAPER-NOTES-PROTOCOL.md`. Append-only. Global monotonic PN-<n>.
Every entry: Finding / Evidence (artifact path) / Use-as (paper section) / Caveat.

## §Sampling & protocol
- PN-1 | 2026-08-29T23:30:00Z | S2-execute/Wave1-T2 | zai/glm-5.3-flash | L-4
  Finding: The llama.cpp server default sampling configuration on the surviving engine image (llamacpp-mtp:latest, engine 0.3.0-dev commit d222767, image sha256:feb0231976b6…) was measured at temperature 1.0, top_k 20, top_p 0.95, min_p 0.05, presence_penalty 0.0 — this matches NEITHER the upstream llama.cpp-documented launch defaults (temp 0.80 / top_k 40 / top_p 0.95 / min_p 0.05) NOR the Qwen3.8-27B official thinking or non-thinking presets, so any server launched without an explicit per-request sampling block runs an undocumented fourth configuration; the hazard is directly assertable because /completion echoes the effective per-request sampling back in generation_settings.
  Evidence: data/bench/e12/validate-v2-selftest.json fault F3 (request without sampling fields reads back exactly the measured defaults); data/bench/e12/validate-v2.json C2 (DEC-2 official non-thinking and thinking blocks read back field-exact modulo f32 storage rounding, e.g. 0.7 → 0.699999988079071); n=1 launch per run, image id in artifact env block.
  Use as: §Sampling & protocol (silent-misconfiguration hazard) + correction to the multivac lifecycle file R1 (which documents the upstream 0.80/40/0.95/0.05 set as if it were the measured server default).
  Caveat: single-image measurement (llamacpp-mtp:latest feb0231976b6…); the historical corpus image (llamacpp-dflash2-pr27342, 1deefcc) is gone — defaults may differ across engine versions; f32 readback needs 1e-3 tolerance in any re-implementation.
- PN-2 | 2026-08-29T23:30:00Z | S2-execute/Wave1-T2 | zai/glm-5.3-flash | L-4
  Finding: A 2-token /v1/chat/completions probe is a reliable ~1 s discriminator of the thinking-mode state on Qwen3.8-27B GGUFs served by this engine: with no thinking control the model thinks by default (content empty, reasoning_content non-empty, finish_reason "length" at max_tokens 2), while chat_template_kwargs {"enable_thinking": false} yields non-empty content and empty reasoning_content — measured on UD-Q4_K_XL at 32,768 context.
  Evidence: data/bench/e12/validate-v2.json check C3 (both directions green); data/bench/e12/validate-v2-selftest.json fault F2 caught by C3 (omitting the control reproduces the leak exactly: content "", reasoning_len 8, finish_reason length).
  Use as: §Sampling & protocol (thinking-control validation method for every future run).
  Caveat: template- and engine-specific (llamacpp-mtp:latest feb0231976b6…); Track B must re-verify on its serving stack before relying on it.
- PN-3 | 2026-08-29T23:30:00Z | S2-execute/Wave1-T2 | zai/glm-5.3-flash | L-4
  Finding: The chat template on the surviving engine rejects chat_template_kwargs {"reasoning_effort": "none"} with a Jinja exception ("Unexpected reasoning effort none. Supported types are xhigh (default), medium, and low."), while {"enable_thinking": false} works — the G17 equivalence question (whether reasoning_effort:none is a valid no-think mechanism on this stack) is answered NEGATIVELY for the 'none' value at the template level, though the equivalence verdict itself remains Wave 2's.
  Evidence: data/bench/e12/validate-v2.json C3.reasoning_effort_none_F_E (response body recorded verbatim); earlier corroborating capture /srv/bench/server-timings/arch-recon-props-20260829.serverlog (500 Jinja Exception, same message).
  Use as: §Sampling & protocol (G17 signal feeding the Wave-2 pilot design).
  Caveat: n=1 template version on image feb0231976b6…; error body recorded verbatim so the Wave-2 verdict can cite the exact failure mode; not a measurement of no-think equivalence itself.

## §Context axis
*(empty)*

## §Speculative decoding
*(empty)*

## §Quant ladder
*(empty)*

## §Systems findings
- PN-4 | 2026-08-29T23:30:00Z | S2-execute/Wave1-T2 | zai/glm-5.3-flash | L-4
  Finding: On the surviving engine (0.3.0-dev d222767, image feb0231976b6…), launching UD-Q4_K_XL with -fit on at a requested context of 262,144 loaded successfully and /props reported the FULL requested 262,144 within the 600 s health window — the "-fit silently shrinks context" failure class documented in E1 did NOT reproduce at this rung on this engine (the E1 observation was made on the now-deleted historical image), so the silent-shrink negative control had to be injected via an un-fittable request (999,999,999 tokens) instead, which the context contract check catches via the reported-vs-requested comparison.
  Evidence: data/bench/e12/validate-v2-selftest.json fault F1 stage "fit-on-262144" (n_ctx_reported 262,144, caught=false) and stage "fit-on-999999999" (caught=true, named by C1); n=1 per stage.
  Use as: §Systems findings (-fit behavior change between engine images) and as a hazard note for Wave 2+: -fit on is NOT trustworthy to bound allocation even when it does not shrink n_ctx — always launch measurement runs with -fit off and assert reported == requested.
  Caveat: fit-on load success does NOT prove the context is usable at depth (deep prefill may still fail); the Wave-1 sweep's fit-off behavioral brackets are the ceiling evidence of record.

## §Efficiency
*(empty)*

## §Agentic behavior
*(empty)*

## §Reproducibility & provenance
*(empty)*
