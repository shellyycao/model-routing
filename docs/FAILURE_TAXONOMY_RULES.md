# Failure-Cause Taxonomy Rules

## Status and scope

**Status: pre-computation rules, written before any category was counted. Post-hoc, exploratory.**
The taxonomy describes why frozen stage records failed or never ran. It reads saved records only,
changes no label, and does not replace any frozen, corrected-view or v3.1 result. It never edits a
raw record, manifest, validator, diagnostic, or existing script.

Model-name policy: processed JSON uses aliases `A/B/C` only; the alias meaning differs by group
(original `A/B/C` = Sonnet 4.6 / Nova Pro / gpt-oss-120b; price-matched `A/B/C` = Sonnet 4.6 /
Kimi K3 / GLM 5). Names appear only in the rendered report. Groups are never pooled.

## 1. Unit of analysis

One **stage record** that is not `passed`, from the frozen v3 inputs of both groups:

| Group | Part A (`StageBenchmarkRecord.record`) | Part B (`WorkflowRunRecord.stages[*]`) |
|---|---|---|
| original 4096 | `results/raw/stage_benchmark/expA_stage_v3.jsonl` | `results/raw/workflow_runs/expB_paths_v3.jsonl` |
| price-matched 16384 | `results/raw/stage_benchmark/expA_price_matched_workflow_v3.jsonl` | `results/raw/workflow_runs/expB_price_matched_workflow_v3.jsonl`, **after** `resolve_workflow_reruns` |

- Included statuses: `failed`, `infra_error`, `blocked_by_invalid_artifact`, `not_run_upstream_failure`.
  Passed stages are not units. Pilot files and the earlier non-v3 files (`expB_paths.jsonl`) are
  excluded.
- **Docker reruns:** the price-matched Part B records are resolved with the frozen rule (a
  successful rerun replaces its void original). Failed stages of the **replaced void originals** are
  not units; they are listed in a separate audit table (run id, replaced-by id, stages) so the 5
  reruns are visible and the unit total reconciles to raw. A rerun that is itself void remains an
  effective record and its stages are units.
- The 40 continuation reporting records and the 11 cleaning/analysis replays are **not** records and
  are not units. They are attached to units as non-exclusive annotations (`later_recovered_by`:
  `none | continuation_reporting_exists | cleaning_replay_pass | analysis_replay_pass`), never changing the category.
- A unit is keyed by `(group, part, run_id, stage)`; `run_id` is unique within a part and group.
- The denominator for context is the number of stage opportunities in each
  `(group, part, stage, alias)` cell (all statuses), printed beside every failure count.

## 2. Mutually exclusive categories and precedence

Each unit gets **exactly one** category, from the first rule below that matches. Rules use only
saved fields: `status`, `failure_type`, `failure_detail`, `parse_ok`, `structural_ok`, `execution`
(`status`, `exit_code`, `stderr`), `validation` (`hard_pass`, `checks[].name/passed/mandatory`),
`invocation_ids`, and for stop reasons the `stop_reason` field of the matching invocation row.
String matching is exact, case-sensitive substring, on the raw saved text. No fuzzy matching, no
model-generated text interpreted.

Invocation join: invocation rows are read from the group's invocation file
(`results/raw/invocations.jsonl` for original; `results/raw/price_matched_workflow/invocations.jsonl`
for price-matched), restricted to the group's experiment ids, keyed by `invocation_id`. A unit with
an `invocation_id` that is missing from the file is reported (`n_invocation_join_missing`) and the
missing id contributes nothing to rule 2; it is never guessed.

| # | Category | Exact detection rule (all conditions) |
|---|---|---|
| 1 | `int64_serialization` | `status == "failed"` AND the unit has at least one invocation id (it actually ran) AND the literal string `Object of type int64 is not JSON serializable` occurs in `failure_detail`. Same literal and field as the frozen diagnostic. Records where it occurs only in `execution.stderr` and not in `failure_detail` are **not** matched here; they are counted in `n_int64_stderr_only` and fall through. Blocked or not-run records that quote it in their upstream detail are excluded by the status and invocation guards. |
| 2 | `truncation` | `status == "failed"` AND (`failure_type == "truncated"` OR any invocation of the unit has `stop_reason == "max_tokens"`). |
| 3 | `infrastructure_void` | `status == "infra_error"` OR `failure_type in {"infra", "api_error"}` OR `execution.status == "sandbox_unavailable"`. Sub-class = the `failure_type` value, plus `docker` when `failure_detail` contains `docker` or `Docker`, plus `rerun_audit` when the unit's run is a retained void rerun. (Decision flag D1: `api_error` is placed here because it is not a model-output failure; the manager may move it.) |
| 4 | `blocked_or_not_run_upstream` | `status in {"blocked_by_invalid_artifact", "not_run_upstream_failure"}`. Sub-class = the status. Annotated (non-exclusive) with `upstream_root_category`: the category (rules 1-3, 5-10) of the first non-passed earlier stage of the same run, to show how many blocked stages trace to an int64, truncation, etc. root cause; these annotated units are **not** double counted as failures of the root category. |
| 5 | `reporting_rounding_only` | `stage == "reporting"` AND `status == "failed"` AND `validation` present AND the set of failed mandatory checks equals `{"derived_values_correct"}` AND the unit's `(group, part, run_id)` is a `recoverable == true` row of `derived_values_only_candidates` in `results/processed/diagnostics_posthoc.json` (the frozen stated-precision half-up rule). Failed mandatory checks equal to `{"derived_values_correct"}` but `recoverable == false` do **not** match here; they fall to rule 9 (genuine mismatch) with sub-class `derived_values_not_rounding`. |
| 6 | `known_q7_false_reject` | `(group, part, run_id)` is a row of `known_q7_v31_false_rejects` in the same diagnostics JSON (v3 hard fail, v3.1 pass, reporting stage). Must be disjoint from rule 5; if a unit matches both, rule 5 wins and the overlap count is reported (`overlap_rule5_rule6`). |
| 7 | `other_execution_error` | `status == "failed"` AND (`failure_type in {"execution_error", "timeout", "security_violation"}` OR (`execution` present AND `execution.status in {"runtime_error", "test_failure", "timeout", "security_violation"}`)). Sub-class from the exception, in order: (i) `timeout` if `failure_type == "timeout"`; (ii) `security_violation` if that failure type; (iii) the exception class name taken as the first regex match of `^([A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception|Exit))\b` over the **last non-empty line** of `execution.stderr` that contains a colon, else over `failure_detail`, e.g. `KeyError`, `FileNotFoundError`, `SyntaxError`; (iv) `no_exception_class` when none is found. The final table lists every sub-class with its count; no sub-class is merged away. |
| 8 | `parse_or_schema_failure` | `status == "failed"` AND (`failure_type in {"parse_error", "invalid_output"}` OR `parse_ok is False` OR `structural_ok is False`). Sub-class = `failure_type` (or `parse_ok_false` / `structural_ok_false` when `failure_type` is neither). |
| 9 | `genuine_validator_mismatch` | `status == "failed"` AND `failure_type == "validation_failed"` AND `validation` present with `hard_pass == False` AND at least one failed mandatory check. Sub-class = sorted failed mandatory check names joined with `+`. This is the category for a numeric value outside tolerance, a wrong ranking, etc. as reported by the frozen validator; it makes no claim that the model, rather than the validator, was at fault. |
| 10 | `unexplained_residual` | Everything else. In particular: `failed` units not matched by 1-9, such as `validation_failed` without a validation object or without a failed mandatory check, an `execution_error` whose execution info is absent, `failure_type` and detail that contradict each other, or any status not listed. |

Notes on precedence:

- Rules 1-3 precede rule 4's statuses only in textual order; they are guarded by status so they
  cannot capture blocked/not-run records. A unit with `status == "failed"` can match more than one
  of rules 1, 2, 5-9 by content; the earliest rule wins.
- Rule 2 precedes rules 7-9 because truncation commonly *produces* parse errors or execution errors
  downstream of a cut-off response; attributing to the earlier, upstream cause is deliberate.
- Rule 3 precedes rule 4. Rules 5 and 6 precede 7-9 so that known validator artifacts are not
  presented as model errors.
- **Overlap audit:** before applying precedence, the analyzer computes, for every unit, the full
  set of rules whose conditions match, and reports the matrix of multi-match combinations with
  counts. The assignment itself uses only first-match.
- Corrected/recovered status is **not** used to reassign categories. A unit remains in its frozen
  category and carries the `later_recovered_by` annotation.

## 3. Reporting

All tables are labelled `post-hoc / exploratory`. For each group, in the rendered report and the
processed JSON:

1. Counts per `(group, part, stage, alias, category)`, with the `(group, part, stage, alias)`
   stage-opportunity denominator and the total failed-or-blocked count, as integers.
2. Counts per `(group, alias, category)` summed over stages and parts, and per `(group, category)`.
3. Category sub-class tables for `other_execution_error` (exception class), `genuine_validator_mismatch`
   (failed-check combination), `infrastructure_void` and `parse_or_schema_failure`.
4. **Unexplained residual share** = `unexplained_residual` count / all units, per group, per
   `(group, alias)`, and overall, as `k/n` with a Wilson 95% interval. It is reported next to the
   share of units explained by artifact categories (rules 1, 3-6) versus model-behaviour categories
   (rules 2, 7-9), with the grouping defined here in advance: **artifact-like** = 1, 3, 4, 5, 6;
   **model-behaviour-like** = 2, 7, 8, 9. Rule 4 units are also shown split by `upstream_root_category`.
   This grouping is descriptive; it is not a quality score or ranking and no composite is computed.
5. The `later_recovered_by` annotation counts, the duplicate/overlap audit, the 5-Docker-rerun audit
   table, the invocation-join misses, and the stderr-only int64 count.
6. Reconciliation: units per group equal (all non-passed effective stage records) and, for the
   original group Part B, equal the sum implied by the frozen `first_failure_stage` plus blocked and
   not-run downstream stages; any mismatch stops the run.

Fields in processed JSON carry only aliases, categories, sub-class strings and integer counts. The
rendered report alone adds model names. Failure-detail text is never copied into processed JSON or
the review list except as the sub-class strings defined above.

## 4. Review sample of the unexplained residual

For later human review. Defined now, drawn mechanically, and answer-free:

- **Population:** all `unexplained_residual` units.
- **Strata:** `(group, alias)` -- six strata. Model names are not used; each stratum is one model in
  one group.
- **Size:** `min(stratum size, 6)` per stratum, so at most 36 units. If a stratum has fewer than 6,
  all of it is taken; no redistribution. If the total residual is below 36, all are listed.
- **Seed:** the fixed string `failure-taxonomy-residual-review-v1`.
- **Selection:** within a stratum, order units by `sha256(seed + "|" + group + "|" + part + "|" +
  run_id + "|" + stage)` hexadecimal ascending and take the first `min(size, 6)`. The result is
  independent of file order, platform and Python hash randomisation. The analyzer asserts
  determinism by drawing twice.
- **Output:** `results/review/failure_taxonomy_residual_sample_ids.json` containing, per sampled unit,
  only `group`, `part`, `run_id`, `stage`, `alias`, `stratum`, and the sampling key hash, plus the
  seed, size rule, stratum sizes and an integrity hash of the file. **No category beyond the fact
  that it is a residual, no failure detail, no exception text, and no model name** is included, so a
  reviewer sees record identifiers only and reads the saved artifacts directly. Any reviewer answers
  go to a new file and are never merged into this list or into the taxonomy counts.

## 5. Procedure and non-mutation

1. Write the analyzer `experiments/analyze_failure_taxonomy.py` (new file) implementing exactly the
   rules above; unit tests under `tests/` use a labelled `SYNTHETIC_FIXTURE` that covers each rule,
   precedence collisions, the stderr-only int64 case, blocked-record quoting an int64 string, the
   rerun audit and sample determinism.
2. Record SHA-256 of every input file in the output. Read inputs only.
3. Outputs: `results/processed/failure_taxonomy_posthoc.json`,
   `results/reports/failure_taxonomy_posthoc.md`,
   `results/review/failure_taxonomy_residual_sample_ids.json`.
4. The rules are not changed after counts are seen. If a rule is wrong, discard the outputs, commit
   a dated amendment, and recompute; a large residual share is a finding to report, not a reason to
   add categories after the fact.

## 6. Known limits stated in advance

- Categories describe the saved string evidence; they are not a root-cause proof. A validator false
  reject is only recognised if it is in the saved q7 list or the stated-precision rule.
- The int64 rule relies on `failure_detail`; if a model's int64 failure was recorded only in stderr,
  it is not matched by rule 1 and is counted separately, so the int64 count is a lower bound.
- Truncation by `stop_reason` depends on the invocation join; cached stage outputs may reuse
  invocation ids from a different run.
- Recovered or corrected status is deliberately not used to reclassify, so the taxonomy reflects
  the frozen failure set.
