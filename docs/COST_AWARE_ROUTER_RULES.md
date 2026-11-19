# Post-hoc cost-aware router rules

**Rules version:** `cost-aware-router-posthoc-1.0`  
**Date fixed:** 2026-11-19  
**Evidence level:** **post-hoc / exploratory**  
**Status:** CP6a rules only; no cost-aware route has been computed

## 1. Status and scope

This variant asks how the existing S1–S3 leave-one-project-out Router would behave if verified dollar cost were active. It is retrospective: all Experiment A/B outcomes existed before these rules. It cannot establish prospective routing quality and must be labelled **post-hoc / exploratory** in every manifest, trace set, analysis, and report.

The frozen Router is the comparator and is immutable. These rules do not modify `configs/routing.yaml`, `results/routing/v3_primary/`, its traces or explanations, its hash-chained predictions or validations, or any raw record. Repricing creates derived in-memory or processed copies only. The new configuration is `configs/routing_cost_posthoc.yaml`; later outputs must go only to `results/routing/v3_cost_posthoc/` and the post-hoc report paths defined below.

Except for making `cost_usd` estimable, the variant retains the frozen Router's:

- leave-one-project-out splits and physical held-out-project exclusion;
- feasibility threshold (`0.5`) and quality constraints;
- Pareto dimensions and lexicographic order (`cost_usd`, then `end_to_end_ms`, then `total_tokens`);
- 5% relative tie tolerance and final tie-break;
- project-equal pooling, project-range uncertainty, and S3 interaction shrinkage `k = 2.0` for the quantities to which interactions apply;
- S1, S2, and S3 meanings, trace contract, explanation templates, counterfactual construction, and replay checks.

S4 remains a retrospective oracle/reference only and is not rerun as a deployable strategy.

## 2. Evidence inputs and eligibility

Only the committed prospective-v3 evidence is eligible:

- Experiment A stage records: `results/raw/stage_benchmark/expA_stage_v3.jsonl`;
- Experiment B workflow records: `results/raw/workflow_runs/expB_paths_v3.jsonl`;
- verified A/B/C standard on-demand prices: `configs/models.yaml`.

Every output manifest must record SHA-256 hashes of those files, the new config, these rules, the implementation, and the frozen comparator traces. Prices are accepted only when both input and output prices are non-null, non-negative, and carry source and retrieval metadata. Missing or invalid pricing makes the corresponding cost estimate unavailable; it is never zero.

The existing `TrainingView` remains the only input to S1–S3 estimation. A held-out project's Experiment A and B records must be physically absent before repricing or estimation, and every evidence reference in the new trace must belong to a training project.

## 3. Stage cost per record

For an executed stage record `r` using model alias `m`, derive:

```text
record_cost_usd(r) =
    input_tokens(r)  × input_price_per_mtok(m)  / 1,000,000
  + output_tokens(r) × output_price_per_mtok(m) / 1,000,000
```

Input and output tokens are priced separately; a blended rate is not used. The calculation uses the token fields stored on the `StageRunRecord`, not `WorkflowEfficiency.cost_usd`, and never writes the result back into the record.

An observed numeric zero is valid if it was actually recorded. A null token field is missing usage, not zero. If either token field or either verified price is missing, that record's cost is unavailable. Cache-hit records are excluded because their displayed tokens refer to an earlier generation and the current record incurred no new model call.

### Primary record rule: all non-void executed records

The primary cost estimate uses every fresh Experiment A stage record from the training projects whose status is `PASSED` or `FAILED`. This includes parse, truncation, execution, and validation failures because their calls consumed tokens and money. It excludes:

- `INFRA_ERROR` records, which are void under the frozen protocol;
- `BLOCKED_BY_INVALID_ARTIFACT` and `NOT_RUN_UPSTREAM_FAILURE`, which made no model call;
- cache hits.

For each `(stage, model, training project)` cell:

1. derive each eligible record cost;
2. require complete usage for every eligible record in the cell;
3. take the arithmetic mean across the cell's records.

If the cell has no eligible records, or any eligible record has missing usage or price, its cost is unavailable. The pooled stage/model point estimate is the unweighted mean of the training-project cell means; its uncertainty is `[min, max]` across those project means. Every training project represented for that stage/model must have an estimable cell. This strict propagation prevents complete cases from silently hiding paid records with missing usage.

This rule is chosen over PASSED-only because the routing decision concerns the expected spend of attempting a stage, not only the spend conditional on success. Feasibility and quality estimates are unchanged and continue to follow the frozen estimator.

### PASSED-only sensitivity

A secondary sensitivity repeats only the cost calculation with fresh `PASSED` Experiment A records. It otherwise uses the same formula, strict missingness, project-equal pooling, prices, constraints, and Router. It must be labelled `passed_only_cost_sensitivity`; it is not substituted for the all-non-void primary view.

The output must report primary and sensitivity coverage before comparing selections.

## 4. Path cost and strategy behavior

### S1 and S2

S1's fixed single-model path and every S2 candidate use the additive stage estimate:

```text
path_cost_usd(A-B-C) =
    cost(cleaning, A) + cost(analysis, B) + cost(reporting, C)
```

The point estimate sums the three pooled stage/model means. Its project-range interval sums the corresponding lower endpoints and upper endpoints, matching the frozen additive efficiency estimator. If any component is unavailable, the path cost and its cost interval are unavailable.

### S3: cost remains additive

S3 retains the frozen shrunk interaction terms for feasibility, quality, time, and total tokens, but **does not learn a `cost_usd` interaction term**. Its cost is the same additive estimate defined above.

This is deliberate for two reasons:

1. The current frozen S3 outcome aggregator exposes efficiency quantities only for feasible workflow runs. Learning a cost residual from it would make cost conditional on success, conflicting with the primary all-non-void rule.
2. Replacing that aggregator only for cost would make early blocking look like a favorable negative “interaction”: a workflow can be cheap because an upstream failure prevents later calls. The frozen feasibility and quality gates already represent reliability; the cost preference should not receive an additional reward for failure.

Keeping cost additive makes the new dimension transparent and confines the change to repricing saved stage evidence. The trace's explanation components must explicitly state `cost_predictor: stage_additive_all_nonvoid` (or `stage_additive_passed_only` in sensitivity), and `interaction_terms` must not contain `cost_usd`.

### Routing with missing cost

The existing Router missingness behavior is retained. Cost enters the Pareto filter only if every candidate remaining after feasibility and quality constraints has an estimate. At the lexicographic cost step, if any remaining candidate has `cost_usd = null`, the entire cost criterion is recorded as inactive for that trace; missing-cost candidates are not dropped merely to force a comparison. Cost is never treated as zero. The Router then proceeds to time and tokens exactly as before.

## 5. Coverage and the earlier 8/20 conversion

Coverage must be reported at three distinct levels, separately for each strategy and LOPO fold:

1. **Stage-cell coverage:** estimable `(stage, model, training project)` cells / required cells.
2. **Candidate coverage:** candidates with all three additive cost components / all candidates, and the same fraction among candidates surviving feasibility and quality constraints.
3. **Trace coverage:** traces where the cost lexicographic step is active / all traces, plus traces with any final selection / all traces.

The CP4b `8/20` figure was **trace-level cost-first selection estimability**, not simply “eight traces had prices.” That conversion operated on frozen candidates. It first required a candidate to survive the frozen feasibility and quality constraints; a trace with no eligible candidate could not yield a cost-first selection. For each eligible candidate it also required a non-null frozen `total_tokens` prediction and complete PASSED, non-cache-hit Experiment A input/output evidence for every stage/model component, from which it constructed an effective dollars-per-token rate. Failure of any prerequisite left the conversion unavailable.

The new variant does not convert frozen total-token predictions. It prices input and output tokens directly and uses failed as well as passed non-void Experiment A records in the primary view. It therefore removes dependence on `candidate.total_tokens` and may change candidate cost coverage. It does **not** change the frozen feasibility/quality rules, so a trace with no candidate surviving those constraints still has no selected path. CP6b must report the three coverage levels above rather than assume that the earlier 8/20 necessarily rises.

## 6. Separate outputs and ordering

The later CP6b implementation must write a fresh, separate directory:

```text
results/routing/v3_cost_posthoc/
  traces.jsonl
  explanations.jsonl
  computational_faithfulness.jsonl
  counterfactual_predictions.jsonl
  counterfactual_predictions.jsonl.head
  counterfactual_validations.jsonl
  counterfactual_validations.jsonl.head
  predict_manifest.json
  validation_manifest.json
  cost_coverage.json
```

It must refuse to append to or overwrite a non-empty output directory unless an explicit, documented resume rule proves that the existing prefix and hashes match. The cost-aware predictions must be written to their own append-only hash chain **before** any held-out execution outcomes are loaded for validation. Prediction and validation chain heads, line counts, source hashes, config hash, rules version, Router version, and creation timestamps must be recorded in the manifests.

New decision traces must contain the repriced candidate costs, selection steps, inactive criteria, and cost-estimator metadata. Template explanations are rendered only from those traces. Faithfulness is tested claim by claim and by replay; it must be reported as observed and must not be assumed perfect merely because the templates were previously faithful.

The new counterfactual records use the existing alternative-selection rule and include absolute selected/alternative `cost_usd`, `alternative - selected` cost delta, and cost interval. Validation remains retrospective and separate from prediction creation.

## 7. Retrospective validation and comparison report

The comparison report is `results/reports/cost_aware_router_posthoc.md`; its machine-readable companion must be `results/processed/cost_aware_router_posthoc.json`. Both begin with the label **post-hoc / exploratory**.

For every held-out project and S1–S3 strategy, report:

- frozen and cost-aware selected path, including `no feasible path`;
- whether the cost criterion was active and its candidate/trace coverage denominator;
- the selected path's executed feasibility under frozen v3 (primary) and existing post-hoc v3.1 (secondary);
- actual executed cost with the number of non-void, cost-complete runs;
- the `single-run evidence` label whenever only one executed run supports the cell.

Actual executed run cost is the sum of costs for stages that made calls, using their recorded tokens and verified prices. A genuinely blocked/not-run stage contributes no incurred cost; this is different from an executed stage with missing usage, which makes the run cost unavailable. Void-infrastructure runs are excluded and counted. Failed executed stages remain in spend.

Cost per feasible completion for a selected path is:

```text
sum(actual cost of all cost-complete, non-void selected-path runs)
----------------------------------------------------------------
number of those runs labelled feasible
```

It is reported separately under frozen v3 and post-hoc v3.1. Spend is identical; only feasibility denominators can differ. If there are zero feasible runs or incomplete cost coverage, the value is `not estimable`, never zero.

The report also includes:

- selection changes from frozen to cost-aware, with denominators;
- faithfulness claims checked/consistent and replay counts;
- counterfactual direction accuracy for feasibility and cost, with estimable denominators;
- the CP4b naive unit-price-ordering baseline beside cost-direction accuracy, on the same comparable subset;
- primary all-non-void versus PASSED-only sensitivity changes and coverage.

Cost-direction equality uses the frozen 5% relative tolerance around the selected path's actual or predicted cost: within tolerance is `tie`; otherwise the alternative is `cheaper` or `more expensive`. Feasibility validation retains the frozen direction rule. V3.1 affects only the secondary executed-feasibility label; it does not retrain or rewrite the primary cost-aware traces.

## 8. Interpretation limits

The report may describe which selections changed, the cost/reliability trade-off the rule made, and whether predicted directions agreed with saved executions. It must not claim that the post-hoc cost-aware Router is “better,” optimal, deployable, or prospectively validated.

All comparisons require explicit denominators. A cheaper selected path must be paired with its executed feasibility and cost-per-feasible-completion denominator. Single-run cells remain `single-run evidence`. Provider-wide rankings, causal claims about handoff costs, and claims that an additive cost estimate captures every workflow interaction are out of scope.
