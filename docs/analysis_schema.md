# Processed analysis schema (`analysis-1.0`)

This is the contract between the M6 analysis pipeline and the M7 web demo. The demo reads only these files. It never reads `results/raw/` and never recomputes numbers.

**Producer:** `experiments/analyze_results.py` → `src/analysis/`, configured by `configs/analysis.yaml`. It runs offline: no AWS calls, no execution of model code.

**Inputs:**
- Experiment B `WorkflowRunRecord` JSONL.
- Optional:
  - Experiment A `StageBenchmarkRecord` JSONL;
  - `evaluate_routing` / `validate_counterfactuals` output directories;
  - validator-version rescore files.

**Reused aggregation:** `workflow_metrics.summarize_runs`, `routing.outcomes.aggregate_runs`, `routing.scoring.pareto_front`, and `routing.data` for parsing, the contract-version check, duplicate detection and synthetic detection.

## Versioning
- **Version bumps:**
  - Adding a column or table is a minor bump (`analysis-1.1`).
  - Renaming or removing something, or changing its meaning or units, is a major bump (`2.0`).
- **One output directory per analysis run.** v2 (pilot) and v3 (primary) get separate directories.
- **Version columns:** every row carries `experiment_id`, `benchmark_version`, `prompt_version` and `validator_version`.
- **Mixed `experiment_id`s are refused** unless they are listed in `experiment_group`. Even then, results are summarised per experiment and never pooled.

## Layout
```
<out_dir>/manifest.json        schema_version, generated_at, code_version, source_files{path: sha256},
                               experiment_ids, synthetic_fixture, tables{name:{status, evidence_status, n_rows}}, files{name: sha256}
<out_dir>/<table>.json         {"metadata": {...}, "columns": [...], "rows": [...]}   (authoritative)
<out_dir>/<table>.csv          "# key: value" metadata lines, then header + rows
<out_dir>/fig_<name>.png + fig_<name>_data.{json,csv}
```
**Value conventions:**
- Missing values are `null` in JSON and empty in CSV.
- A missing price is never 0: `cost_usd` is null, with `cost_status` set to `unavailable` or `partial`.

## Metadata (every table)
| Key | Meaning |
|---|---|
| `schema_version` | `analysis-1.0` |
| `table` | Table name |
| `status` | Display status: `complete`, `partial`, `insufficient_evidence` or `pilot_only` |
| `evidence_status` | Computed status before any override |
| `generated_at` | Defaults to the latest source-record time, so output is byte-identical on rerun. `generated_at_basis` says which time was used. |
| `code_version` | git HEAD, with `-dirty` if `src/`, `experiments/` or `configs/` have uncommitted changes |
| `source_files` | `{path: sha256}` |
| `experiment_ids` | The experiments analysed |
| `synthetic_fixture` | `true` if any input is synthetic; such output is refused under `results/` |
| `notes` | Interpretation notes; the demo must show them |
| `n_rows` | Number of rows |

**Status values:**
- `insufficient_evidence`: a single row whose `status_detail` starts with `insufficient_evidence:`. Numbers are never invented.
- `partial`: a `void_infra` run, an incomplete path grid, or a missing Experiment A counterpart.
- `pilot_only`: a display override; `evidence_status` keeps the computed value.

**Common row prefix:** `experiment_id`, `benchmark_version`, `prompt_version`, `validator_version`, `project_id`, `n_runs` (void runs included), `n_void_infra` (counted, but excluded from rates, quality and efficiency) and `status_detail`.

## Tables
1. **`path_summary`**: one row per experiment × project × path.
   - `path_id`, `n_stages`, `same_model`, `n_switches`.
   - `n_feasible`, `n_infeasible`, `n_valid`.
   - `feasibility_rate`: STRICT, feasible ÷ non-void runs.
   - `outcome_label`, `first_failure_stage`, `failure_type`.
   - Quality, side by side and never combined:
     - `gt.<stage>.<metric>`: ground truth;
     - `cond.<stage>.<metric>`: conditional reference;
     - `n_gt.<stage>`: runs behind the `gt` means.
   - Efficiency:
     - `end_to_end_ms_mean`, kept distinct from `api_latency_ms_mean`;
     - `execution_ms_mean`, token means, `n_calls_mean`, `n_cache_hits`;
     - `cost_usd_mean` and `cost_status`.
   - Quality metrics lie in [0, 1], except `reporting.unsupported_claim_count`, a count where lower is better.
   - There is no composite score.
2. **`propagation`**: long format, one row per path × stage × quantity × metric.
   - Columns: `mean`, `min`, `max`, `n`.
   - Quantities:
     - `downstream_executable`;
     - `blocked`;
     - `upstream_error_severity` (1 − the upstream ground-truth metric);
     - `propagation_impact` (conditional − ground truth);
     - `end_to_end_accuracy`.
   - `interpretation` is `descriptive_decomposition_not_causal_switching_cost`.
3. **`matched_baseline`**: the analysis stage on canonical input (Experiment A) vs actual upstream (Experiment B).
   - One row per model × upstream cleaning model × metric.
   - Columns: `canonical_mean` / `canonical_n`, `actual_upstream_mean` / `actual_upstream_n`, and `difference_actual_minus_canonical`. The difference is descriptive, not a switching cost.
   - Pairing is set in `matched_pairs`, or is automatic when exactly one Experiment A experiment is loaded.
   - Experiment A prompts differ in one documented phrase ("Canonical reference …").
4. **`pareto`**: per project × `n_stages`.
   - `row_type`:
     - `candidate`: a path with at least one feasible non-void run;
     - `no_feasible_path`.
   - Columns: `pareto_optimal`, `dominated_by`, `objectives` (`key:max|min`), `quality_feasible_mean`, `end_to_end_ms`, `total_tokens`, and `cost_usd`.
   - `cost_usd` counts as an objective only when it is verified for every candidate.
5. **`strategies`**: S1/S2/S3 decisions vs the S4 oracle, per held-out project, from `oracle_comparison.json`.
   - Columns: `strategy`, `selected_path_id`, `no_feasible_path`, `executed_outcome_label`, `executed_values`, `oracle_selected_path_id`, `oracle_role`, `matches_oracle_selection`, `in_oracle_feasible_set` and `in_oracle_pareto_set`.
   - `oracle_role` is always `S4_retrospective_reference_not_deployable`.
   - **S4 is never a strategy row.**
6. Two tables, **never merged**:
   - **`counterfactual_validity`** (EMPIRICAL VALIDITY): one row per prediction × quantity.
     - Both hash chains are verified, and each validation is checked against its prediction hash.
     - Columns: `predicted_delta`, `predicted_delta_interval`, `actual_delta`, `actual_delta_spread`, `abs_error`, `direction_correct`, `interval_covers_actual`, and the actual outcomes.
     - A delta is alternative − selected.
   - **`faithfulness`** (COMPUTATIONAL FAITHFULNESS): one row per trace.
     - Columns: `claims_checked`, `claims_consistent`, `replay_matches_selection`, `n_inconsistencies`, `trace_hash`, `explanation_hash`.
7. **`reporting_scores`**: validator versions side by side, never pooled.
   - `row_type`:
     - `run`: one row per run × basis × version;
     - `version_summary`: `n_reports` and `n_hard_pass` within one version, basis and origin.
   - `origin` is `raw_record` or `post_hoc_rescore`, and each row carries a `comparability_note`.
   - A rescore entry that conflicts with the raw record for the same version is refused.
8. **`variability`**: repeats, i.e. runs with `repeat_index > 0`.
   - Columns: `n`, `min`, `max`, `spread`, `repeat_indices`.
   - Quantities: feasible, time, tokens, and `gt.*` quality.
   - No significance tests.

## Figures (PNG plus the exact data drawn; deterministic)
- **Data label in each title:**
  - `SYNTHETIC FIXTURE - not results`
  - `PILOT ONLY - engineering smoke, not findings`
  - `PARTIAL DATA`
  - `INSUFFICIENT EVIDENCE`
- **Figures:**
  - `fig_feasibility_by_path`: strict feasibility.
  - `fig_quality_heatmap`: ground truth, [0, 1] metrics only.
  - `fig_propagation_impact`: descriptive.
  - `fig_pareto_scatter`.
  - `fig_counterfactual_deltas`: only when validations exist.

## Rules the demo must keep
- **Labelling:**
  - Show `status`, `evidence_status` and `notes`.
  - Label pilot and synthetic data on every view.
- **Never show:**
  - S4 presented as a deployable router;
  - a composite score;
  - significance claims.
- Show a missing cost as "unavailable".
- **Show as separate quantities:**
  - `gt` vs `cond` quality;
  - faithfulness vs validity;
  - v2 vs v3 reporting scores.
