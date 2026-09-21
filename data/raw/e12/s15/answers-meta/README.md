# Second-battery answer metadata (AA-LCR, GPQA Diamond)

One line per answered item, mirrored from the host's `answers.jsonl` files with all benchmark and model
TEXT removed: no questions, official answers, document text, candidate answers, reasoning traces, GPQA
answer letters or option permutations (AA-LCR and GPQA licensing; GPQA asks that items not be republished).
Kept: item identifier, configuration, sampling seed, token counts, server timings, speculative counters,
per-request GPU energy, peak VRAM, host-memory counters, timestamps, and for GPQA the two correctness
booleans and the reasoning-closure flag. `*_chars` fields give the length of the removed text.
AA-LCR correctness is in the `JUDGE-OUTPUT-*.jsonl` files one directory up, keyed by item and arm.

Total 756 answers, 68.9 h summed per-answer wall time. `MANIFEST.json` carries the SHA-256 of
each source file.
