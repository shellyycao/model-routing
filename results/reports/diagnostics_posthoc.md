# Post-hoc workflow diagnostics

**POST-HOC / EXPLORATORY.** Frozen raw data, validators, scores, and conclusions remain unchanged.

## Key findings

- The serialization-only replay recovered **33/35** GLM 5 analysis failures and **44/49** analysis failures overall under the frozen validator. These are counterfactual diagnostics, not revised benchmark scores.
- **15** reporting-stage failures that failed only `derived_values_correct` become passes under the stated-precision rounding sensitivity. Known q7 false rejects are listed separately (**30** records).
- Truncation caused failures in **5** distinct Part B workflows across both groups; invocation-level counts are broken down by model and stage below.
- Token-based cost direction was **64/64**, versus **56/64** for naive unit-price ordering. The median absolute executed-cost gap was **$0.0546**.

## 1. NumPy scalar serialization replay

Saved code was replayed in the immutable protocol image with one patch: `json.dump` converts NumPy scalar values through `.item()`. Model logic, inputs, resource limits, and the frozen validators were unchanged. All original failures and partial outputs remain untouched.

| Group / part / stage / model | Would pass | Candidates |
|---|---:|---:|
| original_4096 / B / analysis / Amazon Nova Pro | 9 | 12 |
| original_4096 / B / analysis / OpenAI gpt-oss-120b | 2 | 2 |
| original_4096 / B / cleaning / OpenAI gpt-oss-120b | 9 | 12 |
| price_matched_16384 / A / analysis / GLM 5 | 4 | 4 |
| price_matched_16384 / B / analysis / GLM 5 | 29 | 31 |
| price_matched_16384 / B / cleaning / GLM 5 | 2 | 2 |

Each candidate and validator check is in `results/processed/diagnostics_posthoc.json` under `serialization_replay.records`; replay outputs are in `results/processed/diagnostics_posthoc_replay/`.

## 2. Reporting precision sensitivity

A record qualifies only when the frozen validator's sole mandatory failure is `derived_values_correct` and every otherwise-rejected derived value equals the recomputation rounded half-up to the decimal precision literally reported by the model. This does not replace v3.

| Group | Model | Frozen v3 passes / scored | Rounding-only recovered | Sensitivity passes / scored |
|---|---|---:|---:|---:|
| original_4096 | Amazon Nova Pro | 12/21 | 0 | 12/21 |
| original_4096 | OpenAI gpt-oss-120b | 12/39 | 0 | 12/39 |
| original_4096 | Sonnet 4.6 | 15/34 | 4 | 19/34 |
| price_matched_16384 | GLM 5 | 36/47 | 0 | 36/47 |
| price_matched_16384 | Kimi K3 | 15/41 | 2 | 17/41 |
| price_matched_16384 | Sonnet 4.6 | 17/47 | 9 | 26/47 |

Known q7 false rejects already covered by v3.1: **30**. They are not counted as rounding recoveries; identifiers are in the JSON.

## 3. Truncation

| Group | Model / stage | Invocations | max_tokens stop | truncated flag |
|---|---|---:|---:|---:|
| original_4096 | Amazon Nova Pro / analysis | 26 | 0 | 0 |
| original_4096 | Amazon Nova Pro / cleaning | 61 | 0 | 0 |
| original_4096 | Amazon Nova Pro / reporting | 21 | 0 | 0 |
| original_4096 | OpenAI gpt-oss-120b / analysis | 45 | 0 | 0 |
| original_4096 | OpenAI gpt-oss-120b / cleaning | 55 | 14 | 14 |
| original_4096 | OpenAI gpt-oss-120b / reporting | 39 | 0 | 0 |
| original_4096 | Sonnet 4.6 / analysis | 42 | 0 | 0 |
| original_4096 | Sonnet 4.6 / cleaning | 72 | 0 | 0 |
| original_4096 | Sonnet 4.6 / reporting | 34 | 0 | 0 |
| price_matched_16384 | GLM 5 / analysis | 64 | 0 | 0 |
| price_matched_16384 | GLM 5 / cleaning | 48 | 0 | 0 |
| price_matched_16384 | GLM 5 / reporting | 47 | 0 | 0 |
| price_matched_16384 | Kimi K3 / analysis | 47 | 0 | 0 |
| price_matched_16384 | Kimi K3 / cleaning | 48 | 0 | 0 |
| price_matched_16384 | Kimi K3 / reporting | 41 | 0 | 0 |
| price_matched_16384 | Sonnet 4.6 / analysis | 55 | 0 | 0 |
| price_matched_16384 | Sonnet 4.6 / cleaning | 73 | 0 | 0 |
| price_matched_16384 | Sonnet 4.6 / reporting | 47 | 0 | 0 |

Workflow failure attribution uses the frozen stage `failure_type=truncated`; a max-token stop that still parsed is shown at invocation level but is not called a caused workflow failure.

## 4. Why cost direction was 64/64

The cost-aware rule explicitly chooses the minimum estimated-cost member of the feasible Pareto set, so predicted alternatives are structurally expected to be no cheaper. Perfect observed agreement is not tautological: executed token volumes determine actual cost. The naive unit-price baseline isolates this distinction.

The 64 comparisons had executed absolute gaps: min $0.0114, p25 $0.0358, median $0.0546, p75 $0.1065, max $0.3218. Relative to selected-path cost, the median absolute gap was 96.1%. Actual directions were {'alternative more expensive': 56, 'alternative cheaper': 8}. The naive baseline missed 8/64 because unit-price ordering ignores realized input/output token volumes; this is evidence that 64/64 is not guaranteed merely by path structure.

## Scope and reproduction

This report is a post-hoc artifact check. It does not modify frozen data, scorers, protocol claims, or the main report. Reproduce offline with:

```bash
.venv/bin/python -m experiments.analyze_diagnostics_posthoc
```

Sources: both Part A/B record stores, their invocation ledgers, saved stage artifacts, frozen project ground truth, v3.1 rescores, `configs/models.yaml`, and `results/routing/price_matched_workflow_v3_cost_posthoc/`.
