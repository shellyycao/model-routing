# Post-hoc workflow cost analysis rules

## Amendment — 2026-11-19: dual feasibility views

Before computation, the frozen v3 feasibility view remains the **primary** analysis and a post-hoc
v3.1 feasibility view is added as a **secondary** sensitivity analysis. The secondary view may use
only the existing reporting-stage labels saved in `results/processed/v3_1_rescore/`; no new validator,
rescore, or relabeling is permitted. Project/path tables show the v3 and v3.1 feasible counts,
non-void denominators, feasibility rates, and cost per feasible completion side by side. Project-level
and pooled Pareto frontiers are computed and reported separately for both views.

Executed spend is identical in the two views: stage calls, tokens, retries, missingness, prices, total
spend, and mean cost per run do not change. Only feasibility labels, feasible-completion denominators,
cost per feasible completion, and resulting Pareto membership may differ. This sensitivity is required
because frozen v3 has a documented `customer_churn` q7 false reject. The report must also disclose that
`retail_sales` is pilot-exposed, so the pooled view contains one pilot-exposed project.

## 1. Scope and status

These rules are locked before any workflow-cost result is computed. The analysis is offline,
post-hoc, and exploratory. It covers the saved Experiment B v3 workflow records and the saved Part C
v3 routing traces, predictions, and validations. It does not modify or replay the frozen Router, alter
any trace or prediction, rescore feasibility, or make model calls.

The executed-cost analysis and the Router token-conversion analysis are separate estimands and must
remain separate in every machine-readable and narrative output:

- **Executed cost:** recorded usage for API attempts that actually occurred, priced after the run.
- **Post-hoc conversion of token predictions:** frozen Router token estimates converted after the run
  with verified prices. This is not an executed cost and was not a dollar prediction by the Router.

## 2. Frozen inputs and price source

The primary Experiment B source is `results/raw/workflow_runs/expB_paths_v3.jsonl`. Stage records are
joined to API records in `results/raw/invocations.jsonl` through `invocation_ids`; run and stage
artifacts may be consulted only to verify correspondence or reconstruct a recorded reservation. The
Part C sources are the 20 saved records in `results/routing/v3_primary/traces.jsonl` and their frozen
counterfactual prediction and validation logs. Existing processed reports are context, not sources of
new observations.

The sole price source is the verified A/B/C `pricing` blocks in `configs/models.yaml`, retrieved
2026-11-18. The analysis records the file hash, model IDs, retrieval date, source strings, and these
USD-per-million-token prices:

| Alias | Input | Output |
|---|---:|---:|
| A — Claude Sonnet 4.6 | 3.30 | 16.50 |
| B — Amazon Nova Pro | 0.80 | 3.20 |
| C — OpenAI gpt-oss-120b | 0.15 | 0.60 |

No price may be inferred from current web pages, another experiment, blended-price shortcuts, or a
different regional/service-tier SKU. Provider-reported reasoning tokens are already part of billed
`output_tokens` and are not added again.

## 3. Analysis units and record eligibility

The executed-cost unit is one saved workflow run, identified by `(project_id, path_id,
repeat_index, run_id)`. A path is the ordered cleaning → analysis → reporting model triple in
`path_id`. The analysis validates that `models`, stage aliases, stage order, run ID, project, repeat,
and invocation contexts agree before using a run.

All saved Experiment B v3 runs remain in the cost ledger, including feasible, infeasible, and
`void_infra` runs, because an unsuccessful or void run can still spend money. Feasibility retains the
frozen `feasibility.outcome`; it is not reconstructed from cost data. The primary feasibility rate is

`number of feasible runs / number of non-void runs`.

Both numerator and denominator are reported. If there are no non-void runs, the rate is `not
estimable`. Void counts and their attributable spend are reported separately. No run is silently
dropped because its cost, usage, or outcome is inconvenient.

## 4. Executed-cost definition and reconciliation

For an API attempt with known usage under model `m`:

`attempt_cost_usd = (input_tokens × input_price_m + output_tokens × output_price_m) / 1,000,000`.

Run cost is the sum over every API attempt actually sent for that run. This includes successful
responses, responses that later fail parsing or validation, terminal API failures, and failed retry
attempts. The following counting rules prevent omissions and double counting:

1. A primary invocation record represents the API request and is charged once from its usage.
2. A `:parse` child is a local parse event, not another API request; it is linked to its parent and
   contributes no additional tokens or cost.
3. Every entry in a primary invocation's `attempts` list is an additional failed API attempt and must
   be included. When its provider usage is unavailable, use the exact conservative input/output
   reservation recorded by the experiment accounting system, or reconstruct that reservation with
   the frozen request and the same estimator/settings. Label it `conservative_unknown_usage`, never
   `actual_usage`.
4. A successful final attempt with a missing usage block is handled by its recorded conservative
   reservation and labeled `conservative_unknown_usage`.
5. A validation or execution failure after a model response still incurs the model-call cost.
6. A stage with `blocked_by_invalid_artifact` or `not_run_upstream_failure`, no invocation IDs, and
   `cost_status=not_incurred` made no API call and contributes an explicit $0 incremental cost. This
   is known non-incurrence, not imputation of missing usage.
7. A cache hit contributes $0 incremental executed cost to the consuming run because it made no new
   API call. The producing run bears the fresh call. Cache-hit and shared-output counts must be shown
   because this allocation is execution-order dependent; no shared call is redistributed across paths.

For each run, retain known-usage cost, conservative-unknown-usage cost, API-attempt count, failed
attempt count, missing-usage count, and completeness status. Stage-token sums, invocation-token sums,
and applicable ledger deltas must reconcile. A mismatch is an audit failure, not a reason to choose
one source silently.

Missing usage is never converted to zero. If an actually sent attempt cannot be priced from known
usage or its recorded/reconstructable reservation, that run's total is incomplete. The primary run
cost is then `not estimable`; any known partial sum is shown only as `known partial spend`, with the
missing-attempt count.

## 5. Feasible completion and cost per feasible completion

For each grouping, report total attributable spend, mean cost per run, feasibility rate, feasible
count, non-void count, void count, and:

`cost per feasible completion = total attributable spend across all saved runs / feasible runs`.

The spend numerator includes feasible, infeasible, and void attempts: all were paid in pursuing the
group's feasible completions. The denominator includes only runs whose frozen outcome is `feasible`.
If any run cost needed for the numerator is incomplete, the primary total, mean, and cost per feasible
completion are `not estimable`; a coverage-only partial statistic may be reported but must be labeled.
If the feasible count is zero, cost per feasible completion is the literal string `not estimable` in
reports and `null` plus `not_estimable_reason="zero_feasible_runs"` in JSON. It is never $0, blank, or
infinite.

Mean cost per run uses all saved runs in the grouping, including voids, when every run cost is
complete. Its denominator and cost-complete coverage are always shown.

## 6. Single-run evidence label

Every reported path row carries `n_runs`, `n_nonvoid`, `n_feasible`, and `n_cost_complete`. Any row
with `n_runs = 1` is explicitly tagged **single-run evidence** in JSON, tables, plots, and prose. A
single observation may describe that execution but cannot establish a stable path ranking.

The report states that most path cells are single-run and that repeated cells have shown outcome
instability. It makes no “cheapest model combination” claim without the corresponding feasibility
denominator and evidence count. It does not add confidence intervals unsupported by the small and
uneven repeat structure.

## 7. Project-level and pooled summaries

Primary summaries are computed for each `(project_id, path_id)` cell. Within a cell, sums are over
runs and rates use the denominators in §§3–5; repeats are observations, not independent projects.

The pooled view groups by `path_id` across projects and is labeled **pooled post-hoc view**. Pooled
feasibility is `sum(feasible) / sum(non-void)`, pooled mean cost is `sum(spend) / sum(saved runs)`, and
pooled cost per feasible completion is `sum(spend) / sum(feasible)`. Project cells are not averaged
with equal weight, and pooled evidence is not presented as a replacement for project-level results.

An overall audit may sum spend and attempts across all runs solely for reconciliation. It is not a
path-performance statistic.

## 8. Pareto frontiers

Construct one frontier per project from the project/path cells and one separately labeled pooled
frontier from pooled path rows. The two dimensions are:

- x-axis: mean executed cost per saved run, lower is better;
- y-axis: frozen feasibility rate among non-void runs, higher is better.

Path `x` dominates path `y` iff `x` is no more expensive and no less feasible, with at least one
strict inequality. Exact ties are all retained. Only rows with complete mean cost and an estimable
feasibility rate are frontier-eligible. Excluded rows are listed with reasons; missing values are not
assigned $0 or worst-case ranks. Each frontier point shows its denominators and the `single-run
evidence` tag where applicable. Cost per feasible completion is displayed alongside points but is not
a third dominance dimension.

## 9. Router cost-first sensitivity view

Add a `cost_first_posthoc_token_conversion` view alongside, without replacing, the existing
`router_sensitivity_posthoc` views. It uses each of the 20 frozen traces independently. The candidate
set, feasibility probabilities, quality estimates, constraints, strategy, target/training split,
path IDs, tie tolerance, and all non-cost candidate fields remain frozen.

Because the frozen candidates contain `cost_usd=None`, the new quantity is constructed only from the
candidate's frozen token estimate and trace-embedded evidence:

1. Recreate the frozen stage-additive input/output token composition using only the evidence record
   references embedded in that candidate and the original estimator's project-first pooling rules.
2. Price that composition with `configs/models.yaml`. For a workflow-aware candidate whose frozen
   `total_tokens` contains an interaction adjustment but no input/output split, multiply the frozen
   total-token point estimate by the additive estimate's verified effective blended rate
   (`additive_cost / additive_total_tokens`). This preserves the frozen total-token prediction and
   does not invent a new interaction model.
3. If the frozen `total_tokens`, required evidence usage, or effective rate is missing, the converted
   candidate cost is missing—not zero.

Apply the same frozen feasibility threshold and quality constraints. Among eligible candidates with
estimable converted cost, select lexicographically by converted token cost, then frozen
`end_to_end_ms`, then frozen `total_tokens`, then path ID. Use the frozen 5% relative tie tolerance at
each numeric preference step and retain the frozen final feasibility/path-ID tie break. Candidates
with missing converted cost are not silently preferred or assigned infinity: report their count and
exclude them from the cost-comparable subset. If no eligible candidate has estimable converted cost,
the view returns `not estimable`, not a fallback selection.

Report selected path, change versus the frozen selection, eligible count, cost-comparable count, and
missingness reason per trace. The heading and every summary call this a **post-hoc conversion of the
Router's token predictions**, not a prospective Router cost prediction.

## 10. Cost-counterfactual check

For every frozen selected/alternative prediction pair with the necessary token estimates and
executed run references:

1. Convert the frozen selected and alternative token predictions to dollars by the §9 method.
2. Define predicted delta as `converted alternative − converted selected`.
3. Recompute executed selected and alternative mean run costs from the referenced Part B run IDs by
   §§3–5. Define executed delta as `executed alternative − executed selected`; show repeat counts and
   cost completeness for both arms.
4. Classify each delta as `alternative cheaper`, `tie`, or `alternative more expensive` using the
   frozen objective's 5% relative tie tolerance around the selected value. Direction matches only
   when the two three-way labels are identical.

If either side is not estimable, direction is `not estimable`; missing cases remain in the denominator
table. Report counts and rates with explicit denominators, plus per-pair deltas. This section must be
titled **Cost counterfactual: post-hoc conversion of token predictions** and placed separately from
executed path cost. It must say that the frozen Router never predicted dollars and that this check
does not retroactively validate a prospective dollar forecast.

## 11. Missingness, failures, and blocked stages

Every output distinguishes:

| Situation | Cost treatment | Outcome treatment |
|---|---|---|
| Response received, later parse/validation/execution failure | Include recorded response usage and failed retries | Use frozen infeasible/void label |
| API attempt failed with unknown provider usage | Include recorded conservative reservation and label it | Use frozen label |
| Actually sent attempt has neither usage nor recoverable reservation | Run cost `not estimable`; report known partial spend | Use frozen label |
| Blocked/not-run stage with no invocation | Explicit $0 incremental cost (`not_incurred`) | Preserve upstream-attributed status |
| Cache hit | Explicit $0 incremental executed cost for consumer; disclose | Preserve frozen status |
| `void_infra` run | Include attributable spend; exclude from feasibility denominator | Report separately |

Parse-event child records are never counted as API attempts. A stage's null historical `cost_usd`
reflects prices being unavailable at execution and is recomputed from tokens; it is not itself proof
of missing usage. Conversely, populated run-level `efficiency.input_tokens/output_tokens` cannot hide
an invocation-level missing attempt: completeness is established from the invocation correspondence.

## 12. Required outputs and reporting language

The later computation produces `experiments/analyze_workflow_cost_posthoc.py`,
`results/processed/workflow_cost_posthoc.json`, `results/reports/workflow_cost_posthoc.md`, and tests.
The report is labeled **post-hoc / exploratory** and contains, at minimum:

- source hashes, price provenance, and a run/stage/invocation/ledger integrity audit;
- per-project/path and pooled path tables with all denominators and evidence labels;
- project-level and pooled Pareto memberships plus excluded/missing rows;
- a separate Router cost-first token-conversion sensitivity section;
- a separate cost-counterfactual token-conversion section;
- missing-usage, conservative-reservation, cache, blocked-stage, retry, and void coverage;
- limitations on single runs, uneven repeats, execution-order cache allocation, and post-hoc prices.

Use “this saved path execution” or “these specific A/B/C paths,” not vendor-wide superiority claims.
Do not say “cheapest path” without scope, feasibility, n, and cost completeness. Do not call converted
token estimates “actual,” and do not call executed post-hoc prices “Router predictions.”

## 13. Validation and invariants

Before releasing results, tests and runtime assertions must establish:

1. every included workflow record validates against the v1.2 contract and has a unique run ID;
2. every non-cache stage invocation resolves to the correct run, stage, project, path, repeat, and
   model; parse children resolve to exactly one parent and do not add an API attempt;
3. stage usage equals primary-invocation usage where both are recorded, and blocked/not-run stages
   have no invocation IDs;
4. retry counts and unknown-usage reservations reconcile to the applicable ledgers without treating
   unpriced historical dollars as zero;
5. recomputed prices use exactly the A/B/C prices and model IDs in `configs/models.yaml`;
6. group totals equal their run components; pooled totals equal project-cell totals; no incomplete
   run enters a complete-cost mean or frontier;
7. zero-success groups emit `not estimable`/`null` with the required reason;
8. Pareto dominance, ties, missing exclusion, single-run labels, cost-first missingness, 5% tie
   tolerance, and three-way counterfactual directions have dedicated offline tests;
9. the 20 frozen trace hashes and all frozen prediction hashes are unchanged; and
10. running the analyzer twice produces byte-identical JSON and Markdown.
