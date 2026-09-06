# Divergence Ranks What Benchmarks Bound

This repository contains the publication-facing artifacts for a study of quantization,
speculative decoding, context limits, and benchmark sensitivity in a 27B coding model.

The central result is methodological: distribution-level divergence consistently separates the
tested quantization arms, while several task benchmarks only place broad bounds on their
differences. Configuration choices can affect feasibility and throughput more than the selected
quantization level.

## Public contents

- [`manuscript/ABSTRACT.md`](manuscript/ABSTRACT.md) contains the submission abstract.
- [`manuscript/figures/data/`](manuscript/figures/data/) contains derived, publication-ready tables.
- [`manuscript/references/references.bib`](manuscript/references/references.bib) contains the bibliography.
- [`CITATION.cff`](CITATION.cff) contains citation metadata.

## Publication boundary

Only derived scientific material is published here. Raw execution artifacts, operational logs,
host-specific configuration, network details, credentials, access instructions, internal paths,
and machine-identifying metadata are intentionally excluded. The published tables are sufficient
to audit the numerical claims represented in the manuscript without exposing the environment in
which measurements were produced.

## License

The repository uses separate licenses for prose, code, and data. See [`LICENSE`](LICENSE),
[`LICENSE-CODE`](LICENSE-CODE), and [`LICENSE-DATA`](LICENSE-DATA).
