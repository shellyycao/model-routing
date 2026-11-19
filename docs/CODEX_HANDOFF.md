# Codex Handoff — Independent Benchmark Audit and v2 Candidate

**Branch:** `codex/independent-benchmark-audit-v2`

**Date:** 2026-11-18

**Paid calls made:** 270

**Frozen artifacts modified after `independent-v2-frozen-v1.1`:** none

## Completed

- Audited all 90 frozen independent-v1 records against saved prompts, cases, responses, and scorers.
- Confirmed zero hash, artifact, or rescore discrepancies.
- Documented A1 ceiling/status/test-suite issues, A2 content/schema separation, A3 v1/v1.1 grounding sensitivity, and benchmark-author bias.
- Generated an 18-item blinded human-review packet, a separate identity/automatic-score key, and a deterministic manifest.
- Validated and incorporated the user's completed 18-item review after judgments were locked; produced a joined machine-readable analysis and human-results report.
- Froze `independent-v2-1.0`: 30 cases per task, balanced 10/10/10 by difficulty. The locked first-pass human review identified an overly broad A3 surface form; the corrected targeted rereview accepted 3/3 query rules and 18/18 labels with no remaining disagreement.
- Added the v1.1 pricing-and-budget amendment using official AWS Price List data, conservative retry accounting, and a user-approved $100 hard ceiling.
- Executed all 270 planned Independent-v2 model-case cells from the exact v1.1 tag. All completed without infrastructure failure or retry; actual ledger cost was $1.1181174.
- Audited every run ID, invocation ID, model ID, prompt hash, case hash, saved artifact, and ledger total; the post-run integrity audit passed.
- Added a deterministic v2 analysis and report. The frozen A3 scorer can assign nDCG/grade-2 recall above 1 to invalid duplicate rankings; raw scores remain unchanged and the report discloses strict-invalid-as-zero and valid-ranking-only sensitivity views.
- Added additive v2 response contracts and deterministic decomposed scorers.
- Added v2 prompts, a dedicated plan-by-default v2 runner, immutable protocol hashes, and offline safety tests.
- Produced independent-score and Router post-hoc sensitivity reports.
- Preserved the frozen Router, traces, predictions, validations, datasets, and raw results.

## Deliverables

- `docs/BENCHMARK_AUDIT.md`
- `docs/HUMAN_REVIEW_PROTOCOL.md`
- `results/review/human_review_worksheet.csv`
- `results/review/human_review_key.csv`
- `results/review/human_review_manifest.json`
- `results/review/human_review_completed.csv`
- `results/reports/human_review_results.md`
- `results/processed/independent/human_review_results.json`
- `docs/INDEPENDENT_V2_PLAN.md`
- `datasets/independent_v2/`
- `src/independent/v2.py`
- `experiments/run_independent_v2_benchmark.py`
- `results/processed/independent/independent_v2_freeze_manifest.json`
- `results/raw/independent_v2/`
- `results/raw/ledgers/independent_v2_20261118T185508Z.json`
- `results/processed/independent_v2/analysis.json`
- `results/reports/independent_v2_benchmark.md`
- `tests/test_independent_v2.py`
- `results/reports/benchmark_scoring_sensitivity.md`
- `results/reports/router_sensitivity_posthoc.md`
- `results/processed/independent/audit_v1.json`
- `results/processed/independent/scoring_sensitivity.json`
- `results/processed/router_sensitivity_posthoc.json`

## Reproduction

```bash
.venv/bin/python -m experiments.audit_independent_v1
.venv/bin/python -m experiments.prepare_human_review
.venv/bin/python -m experiments.analyze_human_review --completed <completed_worksheet.csv>
.venv/bin/python -m experiments.prepare_a3_v2_label_review
.venv/bin/python -m experiments.analyze_a3_v2_label_review --query-completed <completed_query.csv> --label-completed <completed_label.csv>
.venv/bin/python -m experiments.prepare_a3_v2_label_rereview
.venv/bin/python -m experiments.analyze_a3_v2_label_rereview --query-completed <completed_query.csv> --label-completed <completed_label.csv>
.venv/bin/python -m datasets.independent_v2.generate --check
.venv/bin/python -m experiments.run_independent_v2_benchmark --plan
.venv/bin/python -m experiments.analyze_independent_sensitivity
.venv/bin/python -m experiments.analyze_router_sensitivity_posthoc
.venv/bin/python -m pytest -q tests/test_independent.py tests/test_independent_v2.py tests/test_routing.py tests/test_xai.py
```

## Current gates

1. No additional model calls are authorized; the prospective 270-cell run is complete.
2. Preserve the frozen raw records and scorer. Any scorer correction or repeat experiment must be a separately named post-hoc sensitivity analysis or a newly frozen prospective protocol.

## Approval plan summary

- Models: `us.anthropic.claude-sonnet-4-6`, `us.amazon.nova-pro-v1:0`, `openai.gpt-oss-120b-1:0`.
- Logical calls: 270 before any separately approved repeats.
- Estimated input tokens: 311,568; hard guard 500,000.
- Worst-case output tokens: 1,474,560.
- Maximum API attempts under the five-attempt retry policy: 1,350.
- Expected full-cap cost: $10.42 at estimated input; conservative five-attempt exposure $52.10.
- Hard dollar guard: $100.00, including full worst-case reservations for retries.
- Actual execution: 270 attempts, 232,581 input tokens, 224,100 output tokens, $1.1181174, zero failed attempts.
- A1/A2 max output: 4,096; A3: 8,192.

## Important interpretation

- Frozen v1 remains the primary historical benchmark.
- A2 recovered-wrapper and A3 v1.1 views are post-hoc diagnostics.
- Human review confirms the A2 decomposition and identifies additional A1-localization and A3 prose/citation scorer limitations.
- Router sensitivity is post-hoc and does not create new prospective traces.
- Part A scores were not inserted into the Data Science Workflow Router.
- The existing `benchmark-v2-frozen` tag belongs to the workflow benchmark and must not be reused for Independent v2.
