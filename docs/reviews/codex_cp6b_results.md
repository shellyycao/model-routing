# Codex CP6b — cost-aware Router results

## Scope completed

CP6b is complete. The offline driver in `experiments/analyze_cost_aware_router_posthoc.py`
computed the post-hoc/exploratory S1–S3 variant from saved records, wrote 20 new traces and
explanations under `results/routing/v3_cost_posthoc/`, and created independent 50-record
prediction and validation hash chains. The processed result is
`results/processed/cost_aware_router_posthoc.json`; the readable comparison is
`results/reports/cost_aware_router_posthoc.md`. Frozen routing outputs and raw records were not
modified, and no model or network call was made.

## Key results

The frozen constraints left **8/20** traces with a selection that could possibly change; the other
**12/20** had no feasible path. Direct input/output-token pricing was complete for **108/108**
stage/model/fold cells and **228/228** candidate paths. The variant changed **1/8** selectable
traces (**1/20** overall): customer-churn S2 changed from A-C-A to C-C-A. Although its Pareto set
expanded, the prior selection survived that filter, so the change is classified as caused by the
explicit **cost preference**, not the Pareto filter (cost-preference changes 1; Pareto-filter
changes 0). Cost changed a Pareto set in 1/20 traces.

Computational faithfulness was **421/421** claims and **20/20** replay matches. Retrospective
counterfactual direction matched **41/50** for executed cost, the naive unit-price baseline also
matched **41/50** on that same subset, and feasibility direction matched **23/50**. PASSED-only
cost had only **60/108** complete stage cells; strict completeness therefore left **0/228** complete
paths and 0/20 active cost steps, changing 1/8 primary selections back to the non-cost result.

## Verification

Both new hash chains verify (**50/50** predictions and **50/50** validations), all trace IDs are
unique, and the held-out evidence leakage count is zero. Source hashes cover the raw inputs, frozen
traces/config, v3.1 labels, rules, new config, model registry, driver, and cost module. The full
offline suite passes: **505 passed, 23 skipped**.
