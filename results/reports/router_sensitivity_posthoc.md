# Router Sensitivity — Post-hoc Evaluation-Criteria Analysis

**Status:** isolated offline sensitivity analysis

**Frozen Router changed:** no

**Frozen traces, predictions, validations changed:** no

This analysis asks how saved routing candidates would be selected under alternative, explicitly documented criteria. It does not retrain the Router, read Part A independent-task scores into the workflow Router, or create a new prospective validation.

Reproduce with:

```bash
.venv/bin/python -m experiments.analyze_router_sensitivity_posthoc
```

Machine-readable output is `results/processed/router_sensitivity_posthoc.json`.

## Alternative criteria

| View | Feasibility | Quality constraints | Preference |
|---|---|---|---|
| Frozen v3 | ≥0.50 | analysis accuracy ≥0.90; unsupported claims ≤1 | latency, then tokens (cost unavailable) |
| Feasibility only | ≥0.50 | none | latency, then tokens |
| Strict quality | ≥2/3 | analysis accuracy =1; unsupported claims =0 | latency, then tokens |
| Token first | frozen v3 constraints | same as frozen | tokens, then latency |
| Maximum reliability | no minimum | none | highest predicted feasibility, then latency/tokens |

These alternative selectors operate only on candidate estimates already embedded in the 20 frozen traces.

## Selection changes

| View | Selected traces | No feasible selection | Changes vs frozen |
|---|---:|---:|---:|
| Frozen v3 | 8 | 12 | 0 |
| Feasibility only | 8 | 12 | 0 |
| Strict quality | 1 | 19 | 7 |
| Token first | 8 | 12 | 0 |
| Maximum reliability | 20 | 0 | 13 |

Dropping the two frozen quality constraints or swapping latency/tokens does not change a selection on these saved candidates. Tightening quality collapses feasible selection from eight traces to one. Choosing the most reliable available path regardless of a minimum changes 13/20 traces and forces a choice where frozen v3 appropriately reports no feasible path.

Therefore, Decision Trace content is robust to the tested efficiency preference order but highly sensitive to feasibility/quality policy. Any alternative trace would need new selection-step text, feasible-set counts, and “what would change” claims; the frozen explanation cannot simply be relabelled.

## Computational faithfulness

All 20 frozen explanation checks remain computationally faithful to their own frozen traces:

- every checked claim is consistent with its bound trace value;
- every replay matches the stored frozen selection.

This result is invariant because the analysis did not mutate or regenerate those traces. It does not imply that one evaluation policy is normatively correct.

## Validator v3 versus post-hoc v3.1

Saved-output reporting rescoring changes:

| Experiment | Reports rescored | v3 ground-truth pass | v3.1 ground-truth pass | False→true |
|---|---:|---:|---:|---:|
| A | 12 | 7 | 9 | 2 |
| B | 82 | 32 | 43 | 11 |

v3.1 removes identified comparative-clause false rejects, but it was created after outputs were observed. These label changes demonstrate that strict end-to-end feasibility and any routing model trained from it can be validator-sensitive. Frozen v3 traces remain the prospective primary result; a v3.1 route is not retrospectively substituted.

## Counterfactual robustness

The frozen counterfactual log contains 50 predictions with executed-outcome validation.

| Strategy | Quantity | n | Direction/agreement | Mean absolute error |
|---|---|---:|---:|---:|
| S2 | selected feasibility agreement | 16 | 0.000 | — |
| S2 | alternative feasibility agreement | 16 | 0.750 | — |
| S2 | feasibility delta direction | 16 | 0.125 | 0.514 |
| S2 | switch count | 16 | 1.000 | 0.000 |
| S3 | selected feasibility agreement | 34 | 0.765 | — |
| S3 | alternative feasibility agreement | 34 | 0.647 | — |
| S3 | feasibility delta direction | 34 | 0.588 | 0.458 |
| S3 | switch count | 34 | 1.000 | 0.000 |

The structural counterfactual conclusion about number of model switches is robust because it is deterministic from path IDs. Feasibility counterfactuals are not uniformly robust: S2 selected-path agreement is 0/16 and feasibility-delta direction is only 2/16; S3 is better but incomplete. Quality and efficiency validation is often undefined when executed paths are infeasible.

Changing the decision criterion also changes which alternatives are decision-relevant. The frozen counterfactual conclusions must therefore be interpreted as conditional on the frozen v3 objective, not as objective-independent properties of the model paths.

## Conclusion

Computational faithfulness is strong: explanations reproduce the computation that was actually stored. Empirical validity is mixed, especially for feasibility. Selection is stable to the tested latency/token preference swap but not to stricter quality thresholds or a forced maximum-reliability policy. This is post-hoc sensitivity evidence, not a new prospective Router validation.
