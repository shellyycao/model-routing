# Cost-aware Router — post-hoc / exploratory

## Key findings

- Frozen feasibility/quality constraints left 8/20 traces with a selected path that could possibly change; 12/20 no-feasible-path traces could not change.
- Activating direct cost changed 1/8 selectable traces (1/20 overall).
- Cost entered the Pareto filter in 8/20 traces and the cost preference was active in 8/20; 1 selection change arose at the preference step and 0 at the Pareto filter.
- Template faithfulness was 421/421 claims with 20/20 replay matches.
- Counterfactual cost direction matched 41/50 estimable pairs; the naive unit-price baseline matched 41/50 on that subset. Feasibility direction matched 23/50.

## Scope and method

This is a **post-hoc / exploratory** rerun of S1–S3 over saved prospective-v3 records. It changes only the availability of `cost_usd`: constraints, LOPO folds, Pareto rules, preference order, tolerance, non-cost estimators and trace machinery remain fixed. Primary cost uses every fresh PASSED or FAILED non-void Experiment A record; PASSED-only is a sensitivity. S3 cost is additive and has no cost interaction term.

## Coverage

Primary stage-cell coverage was 108/108. Candidate cost coverage was 228/228. The cost preference was active in 8/20 traces; 12/20 stopped before any preference step because no candidate satisfied the frozen constraints.

| Strategy | Traces | Candidate cost | Eligible cost | Cost Pareto active | Cost preference active | Selected |
|---|---:|---:|---:|---:|---:|---:|
| S1_single_model | 12 | 12/12 | 2/2 | 2/12 | 2/12 | 2/12 |
| S2_greedy_task_only | 4 | 108/108 | 6/6 | 2/4 | 2/4 | 2/4 |
| S3_workflow_aware | 4 | 108/108 | 8/8 | 4/4 | 4/4 | 4/4 |

The earlier CP4b 8/20 figure was selection estimability after frozen constraint gating plus a total-token conversion. This variant prices input/output tokens directly, but unchanged constraints still prevent no-feasible-path traces from reaching cost selection.

## Selection comparison

| Project | Strategy/policy | Frozen | Cost-aware | Changed | Cause |
|---|---|---|---|---:|---|
| customer_churn | S1_single_model / A-A-A | A-A-A | A-A-A | no | — |
| customer_churn | S1_single_model / B-B-B | no feasible path | no feasible path | no | — |
| customer_churn | S1_single_model / C-C-C | no feasible path | no feasible path | no | — |
| customer_churn | S2_greedy_task_only | A-C-A | C-C-A | yes | cost_preference |
| customer_churn | S3_workflow_aware | A-C-B | A-C-B | no | — |
| energy_consumption | S1_single_model / A-A-A | no feasible path | no feasible path | no | — |
| energy_consumption | S1_single_model / B-B-B | no feasible path | no feasible path | no | — |
| energy_consumption | S1_single_model / C-C-C | no feasible path | no feasible path | no | — |
| energy_consumption | S2_greedy_task_only | no feasible path | no feasible path | no | — |
| energy_consumption | S3_workflow_aware | A-C-B | A-C-B | no | — |
| retail_sales | S1_single_model / A-A-A | no feasible path | no feasible path | no | — |
| retail_sales | S1_single_model / B-B-B | no feasible path | no feasible path | no | — |
| retail_sales | S1_single_model / C-C-C | no feasible path | no feasible path | no | — |
| retail_sales | S2_greedy_task_only | no feasible path | no feasible path | no | — |
| retail_sales | S3_workflow_aware | C-C-B | C-C-B | no | — |
| support_operations | S1_single_model / A-A-A | A-A-A | A-A-A | no | — |
| support_operations | S1_single_model / B-B-B | no feasible path | no feasible path | no | — |
| support_operations | S1_single_model / C-C-C | no feasible path | no feasible path | no | — |
| support_operations | S2_greedy_task_only | A-C-A | A-C-A | no | — |
| support_operations | S3_workflow_aware | C-C-B | C-C-B | no | — |

## Pareto versus preference effects

Cost changed the Pareto set in 1/20 traces. Among the 1 selection changes, 0 first removed the frozen selection at the Pareto filter and 1 first removed it at the explicit cost preference. A `pareto_filter` cause means the cost dimension removed the old selection before lexicographic preferences; a `cost_preference` cause means it survived the Pareto set and was removed at the explicit cost step.

## Executed outcomes and cost per feasible completion

| Project | Strategy/policy | Selected path | Cost-complete | v3 feasible | v3.1 feasible | Mean actual cost | Cost/feasible v3 | Cost/feasible v3.1 | Evidence |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| customer_churn | S1_single_model / A-A-A | A-A-A | 3/3 | 0/3 | 3/3 | $0.1540 | not estimable | $0.1540 | repeated evidence |
| customer_churn | S1_single_model / B-B-B | no feasible path | — | — | — | — | not estimable | not estimable | no selection |
| customer_churn | S1_single_model / C-C-C | no feasible path | — | — | — | — | not estimable | not estimable | no selection |
| customer_churn | S2_greedy_task_only | C-C-A | 1/1 | 0/1 | 0/1 | $0.0513 | not estimable | not estimable | single-run evidence |
| customer_churn | S3_workflow_aware | A-C-B | 1/1 | 1/1 | 1/1 | $0.0746 | $0.0746 | $0.0746 | single-run evidence |
| energy_consumption | S1_single_model / A-A-A | no feasible path | — | — | — | — | not estimable | not estimable | no selection |
| energy_consumption | S1_single_model / B-B-B | no feasible path | — | — | — | — | not estimable | not estimable | no selection |
| energy_consumption | S1_single_model / C-C-C | no feasible path | — | — | — | — | not estimable | not estimable | no selection |
| energy_consumption | S2_greedy_task_only | no feasible path | — | — | — | — | not estimable | not estimable | no selection |
| energy_consumption | S3_workflow_aware | A-C-B | 1/1 | 1/1 | 1/1 | $0.0667 | $0.0667 | $0.0667 | single-run evidence |
| retail_sales | S1_single_model / A-A-A | no feasible path | — | — | — | — | not estimable | not estimable | no selection |
| retail_sales | S1_single_model / B-B-B | no feasible path | — | — | — | — | not estimable | not estimable | no selection |
| retail_sales | S1_single_model / C-C-C | no feasible path | — | — | — | — | not estimable | not estimable | no selection |
| retail_sales | S2_greedy_task_only | no feasible path | — | — | — | — | not estimable | not estimable | no selection |
| retail_sales | S3_workflow_aware | C-C-B | 1/1 | 1/1 | 1/1 | $0.0123 | $0.0123 | $0.0123 | single-run evidence |
| support_operations | S1_single_model / A-A-A | A-A-A | 3/3 | 1/3 | 1/3 | $0.1421 | $0.4262 | $0.4262 | repeated evidence |
| support_operations | S1_single_model / B-B-B | no feasible path | — | — | — | — | not estimable | not estimable | no selection |
| support_operations | S1_single_model / C-C-C | no feasible path | — | — | — | — | not estimable | not estimable | no selection |
| support_operations | S2_greedy_task_only | A-C-A | 3/3 | 0/3 | 0/3 | $0.0881 | not estimable | not estimable | repeated evidence |
| support_operations | S3_workflow_aware | C-C-B | 1/1 | 0/1 | 0/1 | $0.0027 | not estimable | not estimable | single-run evidence |

Actual spend includes failed non-void stages and genuinely excludes blocked/not-run calls. A zero-success denominator is reported as `not estimable`.

## Computational faithfulness

Observed template checks: **421/421** claims consistent; replay reproduced **20/20** selections. These are measurements of the new traces, not an assumption inherited from the frozen run.

## Counterfactual validity

| Strategy | Predictions | Cost direction | Feasibility direction |
|---|---:|---:|---:|
| S2_greedy_task_only | 16 | 13/16 | 3/16 |
| S3_workflow_aware | 34 | 28/34 | 20/34 |

Overall cost direction was 41/50; the naive unit-price ordering baseline was 41/50 on the same executed-cost-comparable pairs. This baseline is essential because A/B/C unit prices differ greatly.

## PASSED-only sensitivity

Changing only the cost record scope from all non-void executed records to PASSED-only changed 1/8 primary selections with a selected path. Only 60/108 stage/model/fold cells had PASSED records with complete usage. Under the pre-specified strict completeness rule this left 0/228 complete candidate-path estimates and therefore 0/20 active cost steps; the sensitivity falls back to the frozen non-cost logic when a candidate cost is incomplete.

| Project | Strategy/policy | Primary | PASSED-only | Changed | First cause |
|---|---|---|---|---:|---|
| customer_churn | S2_greedy_task_only | C-C-A | A-C-A | yes | pareto_filter |

## Limitations

- All outcomes preceded this variant; the result is post-hoc and not prospective evidence.
- Most selected path/project cells have one executed run and are labelled `single-run evidence`.
- Additive cost intentionally does not model cross-stage token interactions and does not reward early blocking.
- Selection and counterfactual claims apply only to these three models, four synthetic projects, verified prices, and this account's saved records.
- A lower attempted-run cost must be read beside feasibility and cost per feasible completion.
