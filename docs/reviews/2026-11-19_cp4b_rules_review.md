# CP4b Rules Review: `POSTHOC_WORKFLOW_COST_RULES.md`

**Verdict: PASS WITH ONE REQUIRED ADDITION**, made before any computation.

## Checked
The rules were written before any aggregation. All of the following are correct:
- Cost includes failed attempts and retries.
- Missing usage is never $0.
- Zero-feasible groups are `not estimable`.
- Rows with n = 1 are tagged `single-run evidence`.
- Void runs count in spend but not in the feasibility denominator.
- The pooled view is labelled separately and is not equal-weighted.
- Pareto ties are retained.
- The Router dollar figure is labelled a post-hoc conversion of token predictions, separate from executed
  cost.

## Required addition (amend the rules before computing)
**Report feasibility under both the frozen v3 validator (primary) and the post-hoc reporting validator
v3.1 (secondary).** Use the existing saved rescore in `results/processed/v3_1_rescore/`, side by side,
including both Pareto frontiers.

**Why:** v3 has a documented false reject (customer_churn q7). It makes Nova-as-reporter paths look
uniquely feasible on that project (Parts B/C report, §B1). A cost-efficiency ranking built only on v3
would inherit that artifact.

**Constraints:**
- Do not create any new validator.
- Use only the existing v3.1 labels.
- Spend is identical under both views; only the denominators change.

## Note for the report
State that retail_sales is pilot-exposed, so pooled views include one pilot-exposed project.
