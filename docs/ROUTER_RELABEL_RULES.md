# Router Relabel Rules (re-scoring with corrected executed outcomes)

## Status and scope

**Status: pre-computation rules, written before any re-scored number exists. Post-hoc, exploratory,
retrospective.** The router, its traces, explanations, logged counterfactual predictions and the
original validations stay frozen and authoritative for their original claims:

- original group: `results/routing/v3_primary/`
- price-matched group: `results/routing/price_matched_workflow_v3_primary/`

This analysis **re-scores, it does not retrain, re-route, or re-predict.** It is not prospective
evidence: the corrected labels were defined after the frozen outcomes were seen, the baselines were
designed after the frozen accuracies (22/50 and 31/64) were known, and the router was never given
the corrected outcomes. Every table is labelled `post-hoc / exploratory / retrospective`. Nothing
here replaces or edits a frozen figure; frozen and corrected values are always printed side by side.

Model-name policy: processed JSON uses aliases `A/B/C` only. **The alias meaning differs by group**
(original `A/B/C` = Sonnet 4.6 / Nova Pro / gpt-oss-120b; price-matched `A/B/C` = Sonnet 4.6 /
Kimi K3 / GLM 5), so aliases are never compared or pooled across groups. Names appear only in the
rendered report, mapped per group. The two groups are never pooled into one accuracy.

## 1. What is re-scored

The unit is one logged `CounterfactualPrediction` (S2 and S3 strategies; S1 has none; S4 is an oracle
and has none and is never scored here). Predictions are read from each group's
`counterfactual_predictions.jsonl` after `PredictionLog.verify()` succeeds (hash chain intact, every
`content_hash` recomputed). A broken chain stops the run. Predicted values are used exactly as
saved; no prediction field is recomputed.

For each prediction, the frozen validator (`validate_prediction`, `src/explainability/validation.py`)
defines the primary quantity and this analysis reproduces it unchanged except for the label source:

- **Primary metric: feasibility direction** = `direction_correct["feasible"]` =
  `_sign(predicted_delta["feasible"]) == _sign(actual_delta["feasible"])`, where
  `actual_delta = actual_alternative_feasible - actual_selected_feasible`, and
  `_sign(x) = 0 if |x| <= 1e-12 else sign(x)`.
- **Secondary metrics (same labels):** `feasibility_agreement:selected` and
  `feasibility_agreement:alternative`, each `(predicted_feasible >= 0.5) == (actual_feasible >= 0.5)`.

A prediction is **in scope** for a (label view, metric) only when its actual value is not `None`
(both paths have at least one non-void executed run). A `None` is excluded from `n` and counted in
an explicit `n_excluded_no_outcome` field, never counted as wrong. `n` is printed with every
accuracy. The 3-way sign comparison means a predicted tie (`0`) counts as correct only against an
actual tie, and vice versa; ties are never rounded away or reassigned. Counts of
(predicted sign x actual sign) cells are reported as a 3x3 table for each group, view and strategy.

## 2. Corrected executed outcome per (project, path)

### 2.1 The frozen aggregation being reproduced (`src/routing/outcomes.py::aggregate_runs`)

For the held-out project, take **every** effective Experiment B run of the path (all repeat indices;
the saved manifest shows the LOPO training view used all non-held-out effective runs, 117 in the
first fold, and validation likewise used every run of the project). Then:

1. Runs whose outcome is `void_infra` are excluded from the denominator and counted (`n_void`).
2. `feasible` = (number of non-void runs with outcome `feasible`) / (number of non-void runs). It is
   therefore a **fraction over repeats, not a majority vote**; it may be 0, 1, or in between. If
   there are no non-void runs it is `None` (excluded, see section 1).
3. Delta = alternative minus selected; direction uses `_sign` with tolerance `1e-12`; agreement uses
   the `>= 0.5` threshold (a fraction of exactly 0.5 counts as feasible).
4. Quality, latency, token and cost quantities are not re-scored here (they are conditional on
   feasibility and depend on which runs pass; re-scoring them requires a separate protocol).

### 2.2 Label views

Four label views are produced for every prediction, all aggregated by the identical function above
and differing only in each run's `outcome` string:

| View | Run outcome source |
|---|---|
| `frozen_v3` | `run.feasibility.outcome` of the effective frozen record. Must reproduce the saved validations (see 2.4). |
| `corrected_v3` | `corrected_v3` of the corrected Q2 row for that run (`experiments/analyze_corrected_q2.py` logic): frozen stage statuses with the 40 continuation reporting results substituted for the 40 stalled analysis cells, and the 11 cleaning recoveries substituted with `passed` (downstream stages exactly as observed). |
| `frozen_v31` | the Q2 row's `frozen_v31`: frozen statuses with the saved v3.1 reporting rescore passing the reporting stage when cleaning and analysis passed. |
| `corrected_v31` | the Q2 row's `corrected_v31`: corrected statuses with v3.1 applied to reporting, including the v3.1 rescore of each continuation report. |

**v3 is the primary validator; v3.1 is secondary** (post-hoc, designed after outputs were seen), as
in `docs/CORRECTED_VIEW_RULES.md`. Headline numbers are v3; v3.1 rows are always labelled secondary.
Rounding recovery is **not** applied to Part B labels (consistent with `corrected_q2.json`
`rounding_recovery_applied_to_q2 = false`).

### 2.3 Runs, repeats, ties, voids

- The corrected outcome needs a status for **every effective run (156 per group)**, not only the
  108 main-grid (`repeat_index == 0`) rows saved in `results/processed/corrected_q2.json`. The
  analyzer must rebuild the per-run rows from the same inputs and the same status-substitution
  logic as `analyze_corrected_q2.py` (copying or importing helper functions; the existing script is
  not edited) and assert that its repeat-0 rows equal the saved `corrected_q2.json`
  `project_path_outcomes_main_grid` for all four views. Any difference stops the run.
- Effective runs: the price-matched group first applies `resolve_workflow_reruns` (successful Docker
  rerun replaces its void original, 5 cases). A run whose outcome is `void_infra` in a view (for
  example a continuation that ended `infra_error`) is excluded by rule 1 and counted.
- Repeats are aggregated as the fraction in 2.1.2. No majority vote, no first-repeat shortcut.
- A path never executed for the project gives `None` and is excluded (reported).

### 2.4 Reproduction gate (must pass before any corrected number is printed)

1. Using `frozen_v3` labels, recompute `validate_prediction` for every logged prediction and assert
   that `direction_correct` (all keys) and `actual_selected/alternative["feasible"]` equal the saved
   `counterfactual_validations.jsonl` records, record by record.
2. Assert that the pooled primary counts equal the frozen published counts **22/50 (original) and
   31/64 (price-matched)**. The manager has quoted these as the frozen "feasibility-direction
   accuracy"; the gate is also the test that this is the metric (`direction_correct["feasible"]`,
   S2 and S3 pooled). If it does not reproduce, **stop and report**; do not choose a different
   definition after the fact.
3. Assert every prediction's `content_hash` equals the saved hash and no logged prediction is
   modified. Emit the SHA-256 of every input file.

## 3. Reporting: both groups, both validators

For each group (original, price-matched) and each validator (v3 primary, v3.1 secondary) print
**frozen next to corrected** with `n`, correct count, accuracy, Wilson interval and p-value:

- pooled (S2 + S3), S2 alone, S3 alone;
- per held-out project (4 projects), because predictions are clustered by project and by strategy;
- the 3x3 predicted-sign by actual-sign table;
- the list of predictions whose direction correctness **changed** between frozen and corrected
  (prediction id, strategy, predicted sign, frozen actual sign, corrected actual sign), identifiers
  only plus signs; this is an audit table, not a headline.

The pooled S2+S3 count is the headline only because it matches the frozen 22/50 and 31/64. S2 and S3
predictions for the same project share outcomes (and may share candidate paths), so
the **effective sample size is smaller than `n`**. Intervals and p-values below treat predictions as
independent and are therefore optimistic; this caveat is printed under every table. No cross-group
pooling.

Interpretation is limited to: "did the frozen router's feasibility-direction predictions agree with
the corrected executed outcomes, and how does that compare with trivial baselines." Corrected labels
may move accuracy in either direction. If a corrected accuracy is higher or lower, the report does
not describe the router as repaired, validated, or deployable; it states a retrospective
re-scoring, and that corrected labels depend on 40 paid continuation calls and on 11 cleaning
recoveries whose downstream stages saw a `failed` upstream label.

## 4. Baselines (all use the identical prediction set and identical label view)

Each baseline outputs a predicted sign in {-1, 0, +1} for `actual_delta["feasible"]` for every
prediction in the set, and is scored with the same `_sign(actual)` equality as the router. Baselines
are evaluated for all four label views.

- **(a) always_less_feasible:** always `-1` (the alternative is less feasible than the selected
  path).
- **(b) always_more_feasible:** always `+1`.
- **(c) pooled_stage_model_rate (leakage-safe):** for each prediction with held-out project `P`,
  compute from **training-project Part A stage records only (all projects except `P`)** the pooled
  stage pass rate `r(stage, alias)` = passed / total records of that alias at that stage, with the
  group's own Part A file. For a single-stage swap that replaces alias `x` by `y` at stage `s`,
  predict `sign(r(s, y) - r(s, x))` with the same `1e-12` tie tolerance (a tie predicts `0`). For
  a single-model-baseline alternative (`X-X-X`, possibly differing from the selected path at more
  than one stage), predict the sign of `prod_s r(s, alt_alias_s) - prod_s r(s, sel_alias_s)`,
  an independence-based path pass rate, with the same tolerance. No held-out record, no Part B
  run, and no corrected label of any kind enters (c); the same function is used for all four label
  views, so (c) does not change between views. This mirrors the router's LOPO: it receives
  exactly the Part A records the router's `TrainingView` would for `P`.
  - Primary (c) uses the **frozen** Part A statuses (what the router saw).
  - Sensitivity (c-corrected) uses corrected Part A stage statuses from the `combined` view of
    `docs/CORRECTED_VIEW_RULES.md` (int64, rounding, v3.1), again training projects only, and is
    labelled as a sensitivity variant. If the Part A per-record attribution cannot be rebuilt
    without altering existing code, (c-corrected) is dropped and the omission reported.
- **(d) always_tie:** always `0`. Reported to show how much of the metric is tie agreement.

Additional comparison on the same predictions: the exact McNemar test (two-sided, binomial on
discordant pairs) of the router against each baseline, with the discordant counts printed.

For **every accuracy** (router and each baseline, each view, each group, each slice) report
`k/n`, accuracy `k/n`, the **Wilson 95% score interval** (`z = 1.959964`), and the **exact two-sided
binomial p-value against 0.5** (`scipy.stats.binomtest(k, n, 0.5)` or an exact implementation; `n`
as printed). The reference value 0.5 is a requested convention, not a chance model: a 3-class sign
match has no natural 0.5 chance level, which is why the baselines (a)-(d) are the meaningful
comparison. No multiplicity correction is applied and none of these p-values is a confirmatory
claim. A baseline that equals or beats the router is stated plainly.

## 5. Leakage rules

1. The held-out project's outcomes (any Part A or Part B record, frozen or corrected) never enter
   any prediction or any baseline for that project. Baseline (c) is built per held-out project from a
   physically filtered training set (reuse `build_training_view`, which raises on any held-out record).
2. Predictions are read-only from the verified append-only logs; the analyzer never regenerates a
   prediction or reads outcome files before the prediction log is verified.
3. Corrected labels are used only to **score** after verification, never as inputs to any estimator.
4. The analysis is not run again with altered definitions after outputs are inspected. If a rule here
   is found wrong, the run is discarded and a dated amendment is committed before recomputing.

## 6. Output contract

Writes only new files: `experiments/analyze_router_relabel.py` (new), `results/processed/router_relabel_posthoc.json`
(aliases only, with the label `post-hoc / exploratory / retrospective`, all input hashes, the
reproduction-gate result, per-slice `k`, `n`, `n_excluded_no_outcome`, Wilson bounds, p-values,
3x3 tables, changed-prediction list), `results/reports/router_relabel_posthoc.md` (the only
place with model names), and a test module under `tests/` that checks Wilson/binomial arithmetic on
a labelled `SYNTHETIC_FIXTURE`, tie handling, and the leakage guard. No frozen file, manifest,
router output, raw record, validator, or existing script is edited.

## 7. Known limits stated in advance

- `n` is small (50 and 64 predictions, 4 held-out projects); intervals are wide and clustered data
  make them optimistic.
- Corrected labels contain substituted statuses and 11 downstream outcomes conditioned on a
  `failed` upstream label; they are a sensitivity, not a reconstruction.
- Predictions were made for the frozen labels, and a router trained on corrected labels would
  predict differently; this analysis cannot say how.
- Pareto, "no feasible path" and quality predictions are out of scope.
