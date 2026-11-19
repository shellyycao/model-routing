# Codex CP4b — workflow cost results

## Status

**Complete; integrity audit PASS.** The dated rules amendment was written before computation. The
analysis is offline and post-hoc/exploratory; frozen Router traces, predictions, validations, and raw
records were not changed. All 156 workflow records map to 339 primary API calls plus 17 non-billable
parse children. Both execution ledgers reconcile exactly to 828,017 input and 843,303 output tokens,
with zero failed or missing-usage attempts. Repriced executed spend is **$7.6922558**.

## Main findings

Frozen v3 remains primary: **28/156 feasible (17.9%)**, giving **$0.2747 per feasible completion**.
The saved post-hoc v3.1 labels are secondary: **38/156 feasible (24.4%)**, giving **$0.2024 per
feasible completion**. Spend and mean run cost are identical; only feasibility labels, denominators,
and view-specific Pareto membership can change. Project/path and pooled tables expose n, cost
completeness, both feasibility views, `single-run evidence`, and both Pareto sets. The report discloses
that `retail_sales` is pilot-exposed.

The separate Router view is explicitly a **post-hoc conversion of token predictions**, not a frozen
Router dollar forecast. It was estimable for **8/20 traces** and changed **1/20** selections. The cost
counterfactual direction was estimable for **32/50 pairs** and matched in **29/32**; all denominators
and executed repeat counts are retained.

## Validation and handoff

The 20 traces validate against their contracts; both 50-record counterfactual hash chains and all 50
prediction-to-validation links pass. Eight new offline tests cover prices, ledger reconciliation,
v3/v3.1 separation, zero-success handling, single-run labels, Pareto ties/missingness, the frozen 5%
direction tolerance, Router labeling, and deterministic outputs. Full suite: **500 passed, 23 skipped**.
No model or network calls were made.
