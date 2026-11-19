# retail_sales Pilot Plan

- **Prepared:** 2026-11-17 (America/New_York)
- **Benchmark baseline:** `benchmark-v2-frozen` (`411fcd7`)
- **Status:** two-stage complete; initial three-stage execution inspected with 5 infrastructure voids; Experiment A unexecuted
- **Planning safety:** all commands below were run without `--execute`; they did not create an AWS client or make model calls

## Recommended sequence

Run the phases separately and inspect the records after each phase. Do not proceed from one paid phase to the next automatically.

1. Experiment B, two-stage development grid: 9 paths, cleaning + analysis.
2. Experiment B, three-stage grid: 27 paths, cleaning + analysis + reporting.
3. Experiment A, canonical stage benchmark: 3 models x 3 stages.

The two-stage and initial three-stage phases were explicitly approved and executed. Five three-stage paths remain infrastructure voids and require a separately approved retry. Experiment A also requires separate approval.

## Two-stage execution result

The first phase completed with 13 API attempts, 28,976 input tokens and 31,058 output tokens. There were no retries and no cache hits. Three paths were feasible and six were infeasible. Full evidence and failure analysis are in `docs/reviews/2026-11-17_retail_sales_pilot_2stage.md`.

## Three-stage execution result

The initial three-stage execution used 44 API attempts, 103,895 input tokens and 105,047 output tokens, with no retries or cache hits. It produced 22 infeasible model outcomes and 5 `void_infra` records after the Docker image disappeared. Full evidence is in `docs/reviews/2026-11-17_retail_sales_pilot_3stage.md`.

The plan-only `--retry-void-infra` estimate is 5 paths, at most 15 model calls, 170,010 input tokens and 61,440 output tokens. It is not approved or executed. The policy, if approved, is to retry all five exactly once—never a favorable subset—while preserving their original records and using new run IDs.

An offline post-freeze audit is recorded in `docs/reviews/2026-11-18_post_freeze_v3_audit.md`.
Saved-output v3 rescoring changes 7/10 reports from v2 fail to v3 semantic pass, while three genuine
errors remain. This is a secondary analysis only. Before any paid call, choose either (a) finish the
frozen-v2 grid under the predefined five-path retry or (b) authorize a separately named prospective
v3 experiment. The two designs must not be pooled.

## Generated plans and proposed hard limits

| Phase | Runs | Planned model calls | Worst-case input tokens | Worst-case output tokens | Proposed `max_calls` | Proposed input limit | Proposed output limit |
|---|---:|---:|---:|---:|---:|---:|---:|
| Experiment B, 2 stages | 9 | 18 | 192,780 | 73,728 | 30 | 200,000 | 80,000 |
| Experiment B, 3 stages | 27 | 81 | 918,054 | 331,776 | 120 | 950,000 | 340,000 |
| Experiment A, canonical stages | 9 | 9 | 102,006 | 36,864 | 15 | 110,000 | 40,000 |

`max_calls` counts API attempts, including failed attempts and retries. The proposed call caps allow limited retries without permitting the runner's theoretical five-attempt worst case. If a cap is reached, the affected run is recorded as `void_infra`; increasing a limit or retrying requires a new decision.

Input and output caps are rounded slightly above the planner's conservative bounds. Prices remain unverified, so the dollar guard is inactive; call and token limits are the enforceable spending controls.

For the currently defined core four-project study, the remaining plan-only minimum is 294 logical
model calls before repeats: 258 Experiment B calls (the three untouched projects plus all five
retail infrastructure retries) and 36 Experiment A calls. Worst-case reserved tokens are 3,280,026
input and 1,204,224 output. This count assumes frozen v2 remains primary; a prospective v3 rerun is
a different experiment and is not included. The repeat subset is not yet fixed, so repeat calls are
also excluded.

## Plan-only commands already run

```bash
.venv/bin/python -m experiments.run_workflow_grid \
  --projects retail_sales --stages 2 --repeats 1 --plan

.venv/bin/python -m experiments.run_workflow_grid \
  --projects retail_sales --stages 3 --repeats 1 --plan

.venv/bin/python -m experiments.run_stage_benchmark \
  --projects retail_sales --plan
```

All plans reported zero completed runs to skip.

## Paid commands

The following explicitly approved two-stage command has been executed and must not be rerun:

```bash
.venv/bin/python -m experiments.run_workflow_grid \
  --projects retail_sales --stages 2 --repeats 1 --execute \
  --max-calls 30 \
  --max-input-tokens 200000 \
  --max-output-tokens 80000
```

The three-stage command was approved and executed once; do not rerun it without `--retry-void-infra`. Experiment A remains unapproved and unexecuted:

```bash
.venv/bin/python -m experiments.run_workflow_grid \
  --projects retail_sales --stages 3 --repeats 1 --execute \
  --max-calls 120 \
  --max-input-tokens 950000 \
  --max-output-tokens 340000

.venv/bin/python -m experiments.run_stage_benchmark \
  --projects retail_sales --execute \
  --max-calls 15 \
  --max-input-tokens 110000 \
  --max-output-tokens 40000
```

## Inspection gate after each paid phase

- Validate every JSONL record against contracts v1.2.
- Confirm `from_cache` is false for every Experiment B invocation.
- Reconcile the ledger's attempts and tokens with the invocation log.
- Confirm every sandbox execution used the verified image ID.
- Confirm monetary cost is `unavailable`, never recorded as zero.
- Review model-output parsing, gpt-oss reasoning separation, `max_tokens` truncation, validation failures, and sandbox runtimes.
- Stop before the next phase and report the results to the user.

