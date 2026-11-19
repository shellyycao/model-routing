# Codex — Post-hoc scorer/environment diagnostics

## Scope

Implemented the requested offline diagnostic pipeline without touching frozen raw data, validators, scores, or conclusions. It inventories both model groups, resolves the price-matched Docker reruns, narrowly patches only NumPy-scalar JSON serialization, reuses the immutable image and frozen validators, computes reported-precision rounding and q7 sensitivities separately, audits truncation from invocation plus stage records, and decomposes the 64/64 cost-direction result against the naive price baseline.

## Findings

Non-execution results are internally consistent: 63 exact int64 failures (49 analysis, 14 cleaning), including GLM 5's 4 Part A and 31 Part B analysis records; 15 reporting recoveries under literal reported-precision rounding, separate from 30 known q7 v3.1 transitions; 5 truncation-caused original-group workflows versus 0 in the 16384-token group; and cost direction 64/64 versus naive 56/64, with a $0.0546 median absolute executed-cost gap.

The required pinned-image replay could not run in this Codex sandbox. Docker socket access fails with `operation not permitted` before container startup. The implementation deliberately does not fall back to host execution, so no serialization counterfactual pass count is asserted. Run `.venv/bin/python -m experiments.analyze_diagnostics_posthoc` from an environment with Docker socket access to generate the final JSON and replace the execution-status report.

## Verification

Added `tests/test_diagnostics_posthoc.py` covering the patch scope, exact 63-record inventory, literal-decimal rounding, separation from q7, truncation attribution, fail-fast image pinning, and 64/64 versus 56/64 cost sanity numbers. Full suite: **537 passed, 23 skipped in 51.11s**. The final replay command is model/network-free and pins `sha256:88988a15503bdb96538c3dd62244a79879d5c7848397db18b1267ccfd0a9727a`.
