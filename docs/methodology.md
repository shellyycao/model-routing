# Routing & XAI Methodology (DRAFT, M5)

Owner: XAI Researcher. Status: draft. Implemented offline and tested only on **SYNTHETIC_FIXTURE** records
(`tests/fixtures/xai/`). No real Experiment A/B results existed when this was written, so this document has
**no results**.

Code: `src/routing/`, `src/explainability/`, `configs/routing.yaml`, `experiments/evaluate_routing.py`,
`experiments/validate_counterfactuals.py`.

## 1. Evaluation unit and leave-one-project-out (LOPO)

For each project *h*, the router decides for *h* using only the other projects.

1. **Physical exclusion.** `build_training_view(store, h)` builds a new frozen `TrainingView` with only the
   Experiment A (`StageBenchmarkRecord`) and Experiment B (`WorkflowRunRecord`) records of projects ≠ *h*.
   - The view keeps no reference to the full store, and its constructor rejects any record from *h*.
   - Estimators accept only a `TrainingView` and raise `TypeError` for anything else.
2. **Type-level check.** Every prediction carries typed `EvidenceRef`s, and `DecisionTrace` rejects
   evidence from outside `training_projects` (a second line of defence).
3. **Phase separation.** Phase 1 (`evaluate_routing.py`) makes decisions and writes counterfactual
   predictions to a hash-chained log. Phase 2 (`validate_counterfactuals.py`) reads the held-out outcomes
   for validation and for the S4 oracle. Only Phase 2 calls `RecordStore.retrospective_outcomes(h)`.

**Loader input:**
- JSONL, one object per line. Each object is a `WorkflowRunRecord` (has `path_id` + `stages`) or a
  `StageBenchmarkRecord` (has `stage` + `record`).
- `contract_version` must equal the current contract version.
- A directory is scanned recursively for `*.jsonl`, and duplicate `run_id`s are rejected.
- Outputs derived from SYNTHETIC_FIXTURE records are refused under `results/`.

## 2. Stage estimates (Experiment A, training projects only)

For each (stage, model, training project), repeats are averaged into one *cell*.

**Excluded records:**
- `INFRA_ERROR` records are void.
- `BLOCKED_BY_INVALID_ARTIFACT` and `NOT_RUN_UPSTREAM_FAILURE` records (contracts v1.2) are attributed
  upstream. They are never counted against this stage's model.

**Cell quantities:**

| Quantity | Definition |
|---|---|
| `feasible` | #PASSED / #remaining records |
| `<stage>.<metric>` | mean ground-truth quality over PASSED records (conditional on success) |
| `stage_time_ms` | mean of generation + execution + validation + handoff ms over PASSED, non-cache-hit records |
| `tokens` | mean input + output tokens over PASSED, non-cache-hit records |
| `cost_usd` | mean only if every PASSED record has `cost_status="estimated"`; otherwise **None** |

**Pooling:**
- Pooled estimate = unweighted mean over training projects. Projects are the unit of generalisation.
- **Uncertainty = [min, max] of the per-project cell values** (the "project range").
- With 2–4 training projects this is a descriptive range. It is **not** a confidence interval, and no
  coverage guarantee is claimed.
- Pooled cost is None if any training project lacks a verified price. Prices are currently unverified for
  all three models, so cost is None everywhere.

## 3. Path predictions

**Quantity keys** follow the contract: `feasible`, `<stage>.<metric>`, `end_to_end_ms`, `total_tokens`,
`cost_usd`, `n_switches`.

**S1 – single-model baselines.** These are the fixed policies A-A-A, B-B-B and C-C-C.
- Each gets its own trace with one candidate, predicted stage-additively.
- The trace reports whether the policy is predicted to meet the objective.
- The executed path is always the policy path (`explanation_components.policy_path_id`).
- No oracle knowledge is used.

**S2 – task-only (greedy) routing.** Predictions use Experiment A only, and interactions are ignored:
- feasible = ∏ₛ feasible(s, mₛ), with interval [∏ lo, ∏ hi]
- `<stage>.<metric>` = the stage estimate of the model used at that stage
- end_to_end_ms = Σ stage_time_ms; total_tokens = Σ tokens
- cost = Σ cost, or None if any stage cost is None

*Deviation from "best model per stage", documented.* S2 runs the same path-level router (§4) over all 27
stage-additive predictions. It does not pick each stage independently. This keeps S2 and S3 identical
except for the predictor, which is the comparison of interest.
- With stage-local quality constraints and additive efficiency, this usually matches per-stage greedy
  choice.
- It can differ in two ways: the feasibility product couples the stages, and tie tolerance applies to path
  sums.

**S3 – workflow-aware routing.** For each training project *j* with Experiment B runs of path *p*:

```
r_j(p,q) = observed_j(p,q) − additive_j(p,q)        (additive_j uses project j's own cells)
n        = #training projects with a residual for (p,q)
s        = n / (n + k)                               (k = interaction_shrinkage_k, default 2)
I(p,q)   = s · mean_j r_j(p,q)                        ("interaction term")
pred     = pooled_additive(p,q) + I(p,q)
interval = [additive_lo + s·min_j r_j, additive_hi + s·max_j r_j]     (feasible clipped to [0,1])
```

- `observed_j` follows the same aggregation rules as validation (`src/routing/outcomes.py`):
  - `void_infra` runs are excluded.
  - feasible = fraction of runs with strict outcome `feasible`.
  - Quality is averaged over feasible runs.
  - Efficiency is averaged over feasible runs with no cache hits.
- **Shrinkage rule:** with one training project, half the raw residual is applied; with two, two-thirds.
  With no Experiment B evidence, I = 0 and S3 = S2 for that quantity.
- These are **interaction terms**, never "handoff cost". Each one mixes several things:
  - error propagation between stages
  - handoff and format effects
  - orchestration overhead not covered by stage timings
  - differences between canonical and actual inputs
  - project idiosyncrasies and noise

  They are **not causally identified**.
- Contracts v1.2 `PropagationSummary` fields are loaded with the records but not yet used. They could
  later decompose these terms descriptively.

**S4 – retrospective oracle.**
- Built in Phase 2 from the held-out project's **observed** outcomes. Candidates are the executed paths;
  "uncertainty" is the range over repeats.
- It goes through the same router, which gives a retrospective best path and Pareto set.
- Its trace is labelled `retrospective_oracle: true, deployable: false`.
- It is never used for predictions. The contract and `generate_counterfactuals` both refuse S4.

## 4. Selection (no weighted composite score)

Every step is recorded as a `SelectionStep`, in this order:

1. `feasibility_threshold`: keep paths with predicted feasibility ≥ `min_feasibility_prob`. A missing
   prediction (no evidence) removes the path.
2. `quality_constraint`: one step per configured `"<stage>.<metric>" op threshold`, applied to the point
   prediction. A missing prediction removes the path.
   - If nothing remains, a `no_feasible_path` step is added and the router returns **"No feasible path"**.
3. `pareto_filter`: keeps the non-dominated set over these dimensions:
   - feasibility (max)
   - the configured quality keys (max; `reporting.unsupported_claim_count` is min)
   - each preference key (min)

   A dimension that is None for any remaining path is dropped and named in the step detail. Removed paths
   cite their first dominator.
4. `lexicographic_preference`: one step per key in `preference_order`. Paths with
   value ≤ best + tie_tolerance·|best| are kept.
   - If any remaining path has None for the key, the step is **inactive**: the reason is recorded, the key
     goes into `inactive_criteria`, and the step is skipped.
   - **None is never treated as 0.** Today `cost_usd` is always inactive.
5. `tie_break`: highest predicted feasibility, then alphabetical path_id.

**Feasible set and Pareto set:**
- `feasible_path_ids` = the paths left after steps 1–2.
- `pareto_path_ids` = the paths left after step 3. This set is reported whether or not a single path is
  selected.

**What would change.** For `min_feasibility_prob` and each constraint threshold, the router is **re-run**
at every breakpoint. A breakpoint is a candidate's predicted value, or the next float beyond it.
- The smallest absolute change that alters the selection is stored in
  `explanation_components.what_would_change`. A change to "no feasible path" counts.
- Tie tolerance and preference order are not searched (a limitation).

## 5. Decision traces and explanations

- `DecisionTrace` records everything the selection used:
  - the candidates with their evidence
  - the objective, the steps and the sets
  - inactive criteria
  - router settings (for replay) and the what-would-change results
  - `training_data_hash` and `config_hash`
- Explanations (`render_explanation`) are deterministic templates rendered **only from the trace**:
  - Each sentence is a claim with a fixed template kind.
  - Each claim's parameters are bound to trace field paths.
  - A few parameters are derived (stay/switch, swap identity, quantity name) and are re-derived when
    checked.
- Explanations cover:
  - why each stage's model was chosen: the step at which every single-stage swap was removed, and why
  - stay or switch at each transition
  - the decisive step
  - inactive criteria
  - predicted values with ranges
  - S3 interaction terms
  - what would change the decision

## 6. Computational faithfulness vs. empirical validity (kept separate)

These two are separate functions with separate output files and report sections. They are never combined
into one number.

**Computational faithfulness** (`check_faithfulness` → `FaithfulnessCheck`, file
`computational_faithfulness.jsonl`) checks that the explanation states what the router computed. For each
claim:
- every bound parameter equals the trace field
- the text equals the fixed template rendered with those parameters
- the text appears in the explanation
- derived values follow from the trace
- what-would-change claims hold when the router is re-run

The explanation as a whole is checked too:
- any sentence not backed by a claim is flagged
- the router is replayed from the trace inputs: `replay_matches_selection`, plus checks that the steps and
  sets match

Faithfulness says nothing about whether the predictions were right.

**Empirical validity** (`validate_prediction` / `validate_log` → `CounterfactualValidation`, files
`counterfactual_validations.jsonl`, `empirical_validity.json`) compares each logged prediction with the
held-out project's executed outcomes:

| Measure | Definition |
|---|---|
| abs_error | \|predicted Δ − actual Δ\|, where Δ = alternative − selected |
| direction_correct | sign agreement; values within 1e-12 count as zero |
| interval_covers_actual | actual Δ inside the predicted Δ interval |
| feasibility agreement | (predicted p ≥ 0.5) == (observed feasible rate ≥ 0.5), for each of selected and alternative |
| repeat spread | min/max of per-repeat Δ, paired by `repeat_index`, when there are ≥ 2 pairs |

- *Contract gap:* there is no dedicated field for feasibility agreement, so it is stored in
  `direction_correct` under the key `feasibility_agreement:<role>`.
- The summary is descriptive. Failed predictions are listed, never dropped.

## 7. Counterfactual predictions and their integrity

**Alternatives.** For each prospective trace with a selection, alternatives are every single-stage swap
plus every single-model baseline (8 alternatives with 3 models and 3 stages).
- Predictions come from the trace's own candidates.
- The Δ interval = [alt_lo − sel_hi, alt_hi − sel_lo]. This is conservative because it ignores
  correlation.
- S1 traces have only one candidate, so they produce no counterfactuals. Their paths appear as
  alternatives in S2 and S3.

**Logging and validation:**
- Each prediction is built with `CounterfactualPrediction.create` (canonical content hash) and appended to
  an append-only JSONL log.
- Each log line stores `seq`, `prev_hash`, `content_hash` and `chain_hash = H(prev ‖ content)`. A `.head`
  sidecar anchors the last link.
- `verify_chain` detects edited records (including re-hashed forgeries), deleted lines, reordered lines and
  tail truncation.
- Validation refuses a broken chain, re-validates each prediction's content hash, and calls
  `check_against` on the stored prediction.
- The prediction log is written in Phase 1, before any validation exists.

## 8. Limitations (explicit)

- **3–5 projects ⇒ exploratory.**
  - LOPO folds have 2–4 training projects.
  - Uncertainty ranges are min/max over very few points.
  - No statistical significance is claimed, and none should be inferred from per-fold agreement rates.
- **Interaction effects are not causally identified.** Residuals mix propagation, handoff, overhead,
  project idiosyncrasies and noise. They must never be described as handoff costs.
- **Three models do not establish universal rankings.** Results apply to these model IDs, these prompts,
  these projects and this period.
- **Quality and efficiency estimates are conditional on success.** Feasibility is modelled separately.
- **Stage time is a sum of recorded components.** It is not end-to-end time, and lower API latency is not
  treated as lower completion time. The S3 terms absorb the difference.
- **Cost is currently unavailable** (prices unverified), so the cost criterion is inactive.
- **What-would-change searches single thresholds only.** It does not search joint changes, tie tolerance
  or preference order.
- **The S4 oracle** is a retrospective reference and is never a deployable router's performance.
- **Synthetic fixtures** exist only to exercise the code. Their numbers must never be reported.
