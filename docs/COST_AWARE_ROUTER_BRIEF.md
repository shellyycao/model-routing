# Cost-Aware Router (post-hoc variant) — Brief

**Status:** approved by the user on 2026-11-19. The user asked for this explicitly after the architecture
walkthrough. Codex executes it; Claude reviews.

**Scope:**
- Offline only, over saved Experiment A/B records and verified prices. No model calls.
- **The frozen Router and its outputs are not modified:** `results/routing/v3_primary/`, the traces, the
  counterfactual log, the validations and `configs/routing.yaml`.

**Evidence level: post-hoc.** All outcomes were seen before this variant was built, so its validation is
retrospective. It shows *how decisions change when cost is active*. It is not prospective evidence of
routing quality. Say this in every output.

## Goal
Re-run the existing S1–S3 leave-one-project-out routing with `cost_usd` **active**, using the verified
prices in `configs/models.yaml`. Then compare against the frozen Router:
- selections;
- explanations and faithfulness;
- counterfactual validity, for feasibility and for cost direction.

## Design principle: change one thing
Keep everything identical to the frozen Router except what is needed to activate cost:
- the same objective constraints (`min_feasibility_prob` 0.5, the same quality constraints);
- the same preference order (`cost_usd`, `end_to_end_ms`, `total_tokens`);
- the same tie tolerance, Pareto rules, estimators and LOPO splits.

Write the variant config as a new file, e.g. `configs/routing_cost_posthoc.yaml`, with
`router_version` marked as post-hoc. Never edit `configs/routing.yaml`.

## Rules to fix BEFORE computing (`docs/COST_AWARE_ROUTER_RULES.md`, commit first)
1. **Stage cost per record:** recorded input tokens × input price + output tokens × output price. Use a
   derived, repriced copy, never an edit of raw records. Missing usage stays missing, never 0.
2. **Which records feed the cost estimate.** Choose one rule and justify it:
   - all non-void records, since failed calls also cost money; or
   - the frozen estimator's PASSED-only convention.

   Report coverage, meaning how many path predictions have an estimable cost, for whichever rule is used.
   Recommended: all non-void records for cost, with the PASSED-only figure as a sensitivity.
3. **Path cost:** S2 uses the additive sum. For S3, state whether an interaction term is learned for
   cost or cost stays additive, and why.
4. **Outputs, in a separate directory** (`results/routing/v3_cost_posthoc/`):
   - new DecisionTraces;
   - template explanations;
   - a **new** hash-chained counterfactual log, including cost-delta predictions;
   - faithfulness checks with replay;
   - retrospective validation against the executed Experiment B outcomes.
5. **Comparison report** (`results/reports/cost_aware_router_posthoc.md`), labelled post-hoc. It covers:
   - selections, frozen vs cost-aware, per held-out project and strategy;
   - the executed outcome of each selected path: feasibility, using v3 primary and v3.1 secondary, and
     actual cost;
   - faithfulness, which should remain perfect;
   - counterfactual direction accuracy for feasibility and for cost, next to the naive price-ordering
     baseline from CP4b;
   - cost per feasible completion of the selected paths.
6. **What not to claim:** that the cost-aware router is "better". At most, describe the trade-off it
   makes and whether that trade-off held on executed outcomes, with denominators and the
   `single-run evidence` label.

## Checkpoints
- **CP6a:** the rules are committed and Claude reviews them before computation.
- **CP6b:** results and report, then Claude reviews and summarizes for the user.
- **Then:** add a short section to `docs/FINAL_REPORT.md`, labelled post-hoc.
