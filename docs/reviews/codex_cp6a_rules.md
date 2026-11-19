# Codex CP6a — cost-aware router rules

## Scope completed

CP6a defines the post-hoc cost-aware Router before any new selection is computed. The rules are in `docs/COST_AWARE_ROUTER_RULES.md`; the isolated configuration is `configs/routing_cost_posthoc.yaml`. The frozen `configs/routing.yaml`, frozen routing outputs, traces, predictions, validations, and raw records remain untouched. No model or network call was made.

## Decisions fixed

- Primary stage cost uses all fresh, non-void Experiment A records that actually ran (`PASSED` and `FAILED`), pricing recorded input and output tokens separately with verified `configs/models.yaml` prices. Missing usage propagates as unavailable and is never zero. PASSED-only cost is a named sensitivity.
- Pooling remains project-equal with project-range uncertainty. S1 and S2 costs are additive. S3 retains its existing interactions for other quantities but keeps cost additive, because the frozen workflow efficiency aggregator is success-conditional and an all-run cost residual could reward early blocking.
- The existing constraints, Pareto behavior, 5% tolerance, preference order, and missing-value semantics remain fixed. Missing cost does not cause a candidate to be silently dropped.
- Coverage will be reported separately for stage cells, candidates, eligible candidates, active cost steps, and selected traces. The earlier 8/20 is documented as selection estimability after constraint gating plus a frozen-token conversion—not simple price availability. Direct repricing removes the `total_tokens` conversion dependency but does not make an ineligible trace selectable.

## Guardrails and next checkpoint

CP6b must use a new output directory and new prediction/validation hash chains, log predictions before held-out validation, compare v3 primary with v3.1 secondary, report actual cost and cost per feasible completion with denominators, and include the naive unit-price baseline on the same cost-direction subset. Every output is labelled post-hoc/exploratory; no claim that the variant is better, optimal, deployable, or prospectively validated is permitted. This turn produced no per-trace result.
