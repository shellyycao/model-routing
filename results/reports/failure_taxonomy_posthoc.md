# Failure-cause taxonomy

**POST-HOC / EXPLORATORY.** Mutually exclusive categories by the precedence in `docs/FAILURE_TAXONOMY_RULES.md`. Source: `results/processed/failure_taxonomy_posthoc.json`. Categories describe saved evidence, not proven root causes. Blocked/not-run units are their own category and inflate the all-units denominator; the failed-only residual share is the co-headline.

**Caveats (read before the tables).**

1. `genuine_validator_mismatch` is a broad catch-all keyed on `failure_type == validation_failed` with a failed mandatory check. It does **not** assign fault to the model or to the validator; the 'model-behaviour-like' grouping below is by failure type only, not a finding that the model was wrong.
2. The 0 unexplained residual follows from the precedence rules and the `failure_type` mapping: every failed record carries a `failure_type` that maps to rules 7-9. It is **not** evidence that every failure is understood, and the review sample is empty for that reason.
3. The artifact-like share includes `blocked_or_not_run_upstream` records, whose upstream roots differ by group (see each group's root list: mostly non-artifact roots in the original group, mostly int64 in the price-matched group). The share without that category is shown beside it.

## Unexplained residual share

| scope | all units | failed units only |
|---|---|---|
| original_4096 | 0/322 = 0.000 [0.000, 0.012] | 0/193 = 0.000 [0.000, 0.020] |
| original_4096 / Sonnet 4.6 (`A`) | 0/80 = 0.000 [0.000, 0.046] | 0/44 = 0.000 [0.000, 0.080] |
| original_4096 / Nova Pro (`B`) | 0/126 = 0.000 [0.000, 0.030] | 0/77 = 0.000 [0.000, 0.048] |
| original_4096 / gpt-oss-120b (`C`) | 0/116 = 0.000 [0.000, 0.032] | 0/72 = 0.000 [0.000, 0.051] |
| price_matched_16384 | 0/168 = 0.000 [0.000, 0.022] | 0/133 = 0.000 [0.000, 0.028] |
| price_matched_16384 / Sonnet 4.6 (`A`) | 0/60 = 0.000 [0.000, 0.060] | 0/50 = 0.000 [0.000, 0.071] |
| price_matched_16384 / Kimi K3 (`B`) | 0/38 = 0.000 [0.000, 0.092] | 0/30 = 0.000 [0.000, 0.114] |
| price_matched_16384 / GLM 5 (`C`) | 0/70 = 0.000 [0.000, 0.052] | 0/53 = 0.000 [0.000, 0.068] |
| both groups (descriptive sum) | 0/490 = 0.000 [0.000, 0.008] | 0/326 = 0.000 [0.000, 0.012] |

## original_4096

Category totals: int64_serialization=26; truncation=7; infrastructure_void=0; blocked_or_not_run_upstream=129; reporting_rounding_only=4; known_q7_false_reject=13; other_execution_error=49; parse_or_schema_failure=13; genuine_validator_mismatch=81; unexplained_residual=0

Artifact-like share (includes blocked/not-run) 172/322 = 0.534 [0.480, 0.588]; artifact-like share **excluding** blocked/not-run 43/322 = 0.134 [0.101, 0.175]; blocked/not-run share 129/322 = 0.401 [0.349, 0.455]; model-behaviour-like by failure type only, not fault 150/322 = 0.466 [0.412, 0.520].

| part | stage | model | opportunities | non-passed | int64_serialization | truncation | infrastructure_void | blocked_or_not_run_upstream | reporting_rounding_only | known_q7_false_reject | other_execution_error | parse_or_schema_failure | genuine_validator_mismatch | unexplained_residual |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| part_a | analysis | Nova Pro (`B`) | 4 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 1 | 0 |
| part_a | cleaning | Sonnet 4.6 (`A`) | 4 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| part_a | cleaning | Nova Pro (`B`) | 4 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 1 | 0 | 0 |
| part_a | cleaning | gpt-oss-120b (`C`) | 4 | 2 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| part_a | reporting | Sonnet 4.6 (`A`) | 4 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| part_a | reporting | Nova Pro (`B`) | 4 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| part_a | reporting | gpt-oss-120b (`C`) | 4 | 2 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 0 |
| part_b | analysis | Sonnet 4.6 (`A`) | 52 | 22 | 0 | 0 | 0 | 14 | 0 | 0 | 0 | 0 | 8 | 0 |
| part_b | analysis | Nova Pro (`B`) | 44 | 39 | 12 | 0 | 0 | 22 | 0 | 0 | 4 | 0 | 1 | 0 |
| part_b | analysis | gpt-oss-120b (`C`) | 60 | 33 | 2 | 0 | 0 | 19 | 0 | 0 | 1 | 0 | 11 | 0 |
| part_b | cleaning | Sonnet 4.6 (`A`) | 68 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 16 | 0 |
| part_b | cleaning | Nova Pro (`B`) | 44 | 43 | 0 | 0 | 0 | 0 | 0 | 0 | 30 | 12 | 1 | 0 |
| part_b | cleaning | gpt-oss-120b (`C`) | 44 | 29 | 12 | 5 | 0 | 0 | 0 | 0 | 8 | 0 | 4 | 0 |
| part_b | reporting | Sonnet 4.6 (`A`) | 52 | 40 | 0 | 0 | 0 | 22 | 4 | 6 | 0 | 0 | 8 | 0 |
| part_b | reporting | Nova Pro (`B`) | 44 | 34 | 0 | 0 | 0 | 27 | 0 | 0 | 0 | 0 | 7 | 0 |
| part_b | reporting | gpt-oss-120b (`C`) | 60 | 50 | 0 | 0 | 0 | 25 | 0 | 5 | 0 | 0 | 20 | 0 |

Sub-classes:

- blocked_or_not_run_upstream: blocked_by_invalid_artifact=129
- genuine_validator_mismatch: derived_values_correct+finding_statements_substantive=1; derived_values_correct+finding_statements_substantive+prose_claims_consistent+rankings_correct+reported_values_consistent=1; derived_values_correct+finding_statements_substantive+rankings_correct+reported_values_consistent=7; derived_values_correct+finding_statements_substantive+reported_values_consistent=2; derived_values_correct+numeric_attribution_correct+reported_values_consistent=2; finding_statements_substantive=8; finding_statements_substantive+rankings_correct=1; finding_statements_substantive+rankings_correct+reported_values_consistent=8; numeric_attribution_correct+prose_claims_consistent=2; rankings_correct=5; required_metric_keys_present=1; row_set_matches_reference=19; row_set_matches_reference+values_match_reference=2; schema_constraints+values_match_reference=1; values_within_tolerance=21
- other_execution_error: AttributeError=5; IndentationError=3; NameError=2; SyntaxError=7; TypeError=26; ValueError=5; pandas.errors.IndexingError=1
- parse_or_schema_failure: parse_error=13

- blocked/not-run upstream root: {'genuine_validator_mismatch': 6, 'int64_serialization': 11, 'other_execution_error': 78, 'parse_or_schema_failure': 24, 'truncation': 10}
- later_recovered_by annotation: {'none': 291, 'analysis_replay_pass': 11, 'continuation_reporting_exists': 11, 'cleaning_replay_pass': 9}
- multi-rule matches before precedence: {'1+6+7': 1, '1+7': 11, '1+7+8': 14, '2+8': 7, '5+9': 4, '6+9': 13, '7+8': 49}; rule5/rule6 overlap 0
- invocation-join misses: 0; int64 stderr-only: 0
- Docker rerun audit: 0 replaced void originals (excluded from units): []
- reconciliation: {'units': 322, 'raw_nonpassed': 322, 'replaced_original_nonpassed': 0, 'retained_rerun_void_nonpassed_not_effective': 0}

## price_matched_16384

Category totals: int64_serialization=37; truncation=0; infrastructure_void=0; blocked_or_not_run_upstream=35; reporting_rounding_only=11; known_q7_false_reject=17; other_execution_error=2; parse_or_schema_failure=0; genuine_validator_mismatch=66; unexplained_residual=0

Artifact-like share (includes blocked/not-run) 100/168 = 0.595 [0.520, 0.667]; artifact-like share **excluding** blocked/not-run 65/168 = 0.387 [0.317, 0.462]; blocked/not-run share 35/168 = 0.208 [0.154, 0.276]; model-behaviour-like by failure type only, not fault 68/168 = 0.405 [0.333, 0.480].

| part | stage | model | opportunities | non-passed | int64_serialization | truncation | infrastructure_void | blocked_or_not_run_upstream | reporting_rounding_only | known_q7_false_reject | other_execution_error | parse_or_schema_failure | genuine_validator_mismatch | unexplained_residual |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| part_a | analysis | GLM 5 (`C`) | 4 | 4 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| part_a | cleaning | Sonnet 4.6 (`A`) | 4 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| part_a | reporting | Sonnet 4.6 (`A`) | 4 | 2 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 |
| part_a | reporting | Kimi K3 (`B`) | 4 | 3 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 2 | 0 |
| part_b | analysis | Sonnet 4.6 (`A`) | 52 | 8 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 7 | 0 |
| part_b | analysis | Kimi K3 (`B`) | 44 | 4 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 3 | 0 |
| part_b | analysis | GLM 5 (`C`) | 60 | 33 | 31 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| part_b | cleaning | Sonnet 4.6 (`A`) | 68 | 12 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 12 | 0 |
| part_b | cleaning | Kimi K3 (`B`) | 44 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| part_b | cleaning | GLM 5 (`C`) | 44 | 5 | 2 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 2 | 0 |
| part_b | reporting | Sonnet 4.6 (`A`) | 52 | 37 | 0 | 0 | 0 | 9 | 8 | 10 | 0 | 0 | 10 | 0 |
| part_b | reporting | Kimi K3 (`B`) | 44 | 30 | 0 | 0 | 0 | 7 | 1 | 1 | 0 | 0 | 21 | 0 |
| part_b | reporting | GLM 5 (`C`) | 60 | 28 | 0 | 0 | 0 | 17 | 0 | 5 | 0 | 0 | 6 | 0 |

Sub-classes:

- blocked_or_not_run_upstream: blocked_by_invalid_artifact=35
- genuine_validator_mismatch: derived_values_correct+finding_statements_substantive+rankings_correct+reported_values_consistent=9; derived_values_correct+numeric_attribution_correct=8; derived_values_correct+numeric_attribution_correct+prose_claims_consistent=1; derived_values_correct+numeric_attribution_correct+reported_values_consistent+required_metric_keys_present=1; finding_statements_substantive+rankings_correct+reported_values_consistent=3; numeric_attribution_correct=7; numeric_attribution_correct+prose_claims_consistent=4; numeric_attribution_correct+prose_claims_consistent+reported_values_consistent+required_metric_keys_present=1; numeric_attribution_correct+reported_values_consistent+required_metric_keys_present=2; prose_claims_consistent=1; reported_values_consistent+required_metric_keys_present=2; row_set_matches_reference=15; values_within_tolerance=12
- other_execution_error: KeyError=1; TypeError=1

- blocked/not-run upstream root: {'genuine_validator_mismatch': 2, 'int64_serialization': 29, 'other_execution_error': 4}
- later_recovered_by annotation: {'analysis_replay_pass': 33, 'none': 104, 'continuation_reporting_exists': 29, 'cleaning_replay_pass': 2}
- multi-rule matches before precedence: {'1+7': 2, '1+7+8': 35, '5+9': 11, '6+9': 17, '7+8': 2}; rule5/rule6 overlap 0
- invocation-join misses: 0; int64 stderr-only: 0
- Docker rerun audit: 5 replaced void originals (excluded from units): [{'original_run_id': 'expB_price_matched_workflow_v3-10db877a3ba2a603', 'replaced_by': 'expB_price_matched_workflow_v3-fe17374c9b512998', 'original_nonpassed_stages': [['cleaning', 'A', 'infra_error'], ['analysis', 'A', 'not_run_upstream_failure'], ['reporting', 'A', 'not_run_upstream_failure']]}, {'original_run_id': 'expB_price_matched_workflow_v3-2cc5c33d604f5c14', 'replaced_by': 'expB_price_matched_workflow_v3-d7ecc4310ea69dea', 'original_nonpassed_stages': [['analysis', 'A', 'infra_error'], ['reporting', 'B', 'not_run_upstream_failure']]}, {'original_run_id': 'expB_price_matched_workflow_v3-60743b466c67af29', 'replaced_by': 'expB_price_matched_workflow_v3-be954fe589395228', 'original_nonpassed_stages': [['cleaning', 'C', 'infra_error'], ['analysis', 'C', 'not_run_upstream_failure'], ['reporting', 'B', 'not_run_upstream_failure']]}, {'original_run_id': 'expB_price_matched_workflow_v3-b13b2e1a92f0b484', 'replaced_by': 'expB_price_matched_workflow_v3-c74b8e30d7cc56c5', 'original_nonpassed_stages': [['cleaning', 'C', 'infra_error'], ['analysis', 'C', 'not_run_upstream_failure'], ['reporting', 'C', 'not_run_upstream_failure']]}, {'original_run_id': 'expB_price_matched_workflow_v3-d348486e2b0e6141', 'replaced_by': 'expB_price_matched_workflow_v3-c9cc09e47b04cc1c', 'original_nonpassed_stages': [['cleaning', 'C', 'infra_error'], ['analysis', 'C', 'not_run_upstream_failure'], ['reporting', 'A', 'not_run_upstream_failure']]}]
- reconciliation: {'units': 168, 'raw_nonpassed': 182, 'replaced_original_nonpassed': 14, 'retained_rerun_void_nonpassed_not_effective': 0}

