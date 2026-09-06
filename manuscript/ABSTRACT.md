# Abstract

KL divergence over 65,536 tokens per domain separates the three quantized arms of a GGUF ladder
from one another on code at 8.7-18.1 sigma in 2.3 accelerator-hours; three task-benchmark
instrument classes costing 14.3 hours separate the same arms nowhere. This report measures a 27B
coding model on two consumer GPUs across eight quantizations, three inference backends, and five
benchmark families. Each benchmark fails differently, which is the point: WikiText-2 perplexity
spans 0.033 across four arms against +/-0.041 of standard error per point; HellaSwag at n=400 rates
the most heavily quantized arm nominally highest, two arms answering all 400 items identically;
paired HumanEval+ at n=164 bounds the ladder's extremes at 0.61 points, 95 per cent interval
[-3.28, +2.06], a test no outcome could have made significant at the observed discordance; and a
50-instance SWE-bench Verified campaign inverts the ordering at 77.6, 76.0, and 75.5 per cent
inside +/-12 points. Divergence is roughly twice as large on code as on prose and 3.1-4.4x prose
on the benchmark's own prompts, so against a published <0.007 quality threshold two of three arms
pass on prose, one on generic code, and none on the task distribution. What moves the numbers is
configuration, not quantization: for two of four arms tensor placement sets the reachable context
window; decode throughput spans 6.7 per cent between arms against 40.7 per cent within one
configuration at three repetitions; speculative decoding is deterministically non-equivalent to
unspeculated decoding, reproducing it on 131 of 164 problems while reproducing itself
byte-exactly; and one 1.19 GiB draft-worker allocation blocks a separate drafter on two of three
engines, one of which never served a request. These are measurements of one model under fixed
software images on one two-accelerator host. Derived tables and the bibliography are released.
