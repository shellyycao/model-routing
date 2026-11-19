# retail_sales Three-Stage Pilot Result

- **Executed:** 2026-11-17 (America/New_York; raw records use UTC on 2026-11-18)
- **Scope:** Experiment B, `retail_sales`, 27 fresh three-stage paths, repeat 0
- **Frozen baseline:** `benchmark-v2-frozen` (`411fcd7`)
- **Hard limits:** 120 API attempts, 950,000 input tokens, 340,000 output tokens
- **Execution result:** 27 workflow records written: 22 infeasible and 5 `void_infra`
- **Completion status:** incomplete as an empirical 27-path grid; the 5 infrastructure-void paths have not been retried
- **Next-phase status:** stopped after this phase; Experiment A was not run

## High-level outcomes

No path was feasible in the initial three-stage execution. Among the 22 paths with model outcomes, nine first failed at reporting validation, one at analysis execution, six at cleaning execution, three at cleaning parsing, two at cleaning truncation and one at cleaning validation. Five further paths are excluded from model-quality conclusions because the Docker sandbox image disappeared during the run.

| First failure | Paths |
|---|---:|
| Reporting validation | 9 |
| Analysis execution | 1 |
| Cleaning execution | 6 |
| Cleaning parse | 3 |
| Cleaning truncation | 2 |
| Cleaning validation | 1 |
| Infrastructure void | 5 |

Stage status counts across all 27 records were:

- Cleaning: 10 passed, 12 failed, 5 infrastructure errors.
- Analysis: 9 passed, 2 failed, 11 blocked by an unusable artifact, 5 not run because of infrastructure failure.
- Reporting: 10 failed, 12 blocked by an unusable artifact, 5 not run because of infrastructure failure.

## Model and propagation observations

- Model A cleaning passed all 9 fresh A-prefixed paths.
- Model B cleaning failed all 9 B-prefixed paths: 6 generated Python runtime errors and 3 responses contained invalid JSON escapes.
- Of the four C-prefixed cleaning paths that reached a model outcome, one passed, one failed validation and two hit the shared `maxTokens=4096` limit. The other five C-prefixed paths are infrastructure voids.
- A-B-A passed cleaning but its B analysis code raised an execution error; reporting was correctly blocked.
- C-B-A produced a structurally consumable but incorrect cleaned artifact. Analysis and reporting continued on the actual artifact and failed against ground truth, preserving the intended propagation evidence.

Reporting ran on 10 paths and failed mandatory validation on all 10. Every one failed `rankings_correct`; two also failed `derived_values_correct`, and the propagated C-B-A report additionally failed reported-value consistency, substantive-statement and prose-consistency checks. Nine of the ten reports nevertheless had finding coverage 1.0 and numerical consistency 1.0. This recurring ranking failure needs review before any full experiment, but the frozen prompt, schema and validator must not be changed silently after observing outcomes.

## Infrastructure incident

The sandbox image was rebuilt immediately before the run and passed all 16 isolation tests as image:

`sha256:7f95c0dedbe5dedde14b03130fce5c5e889062d63d7bde9dd10c3f7891bbb738`

Twenty-eight actual sandbox executions recorded exactly that verified image ID. During C-B-B cleaning, the C model call completed after 324.56 seconds, but the image was no longer present when the generated code was to execute. C-B-B therefore became `void_infra`. The next four paths were refused before model invocation by `SandboxGate`, also as `void_infra`. A post-run `docker image inspect` confirmed the image was absent. Docker retained no image-delete event for the interval, consistent with an external daemon reset or cleanup rather than application code deleting it.

The safety behavior was correct: infrastructure failures were not counted as model failures, no code ran on the host, and downstream stages were marked not run.

## Accounting and provenance checks

| Check | Result |
|---|---|
| Three-stage records validate against contracts v1.2 | 27/27 passed |
| Unique run IDs | 27/27 |
| Paid logical calls / API attempts | 44 / 44 |
| Failed attempts or retries | 0 |
| Input tokens | 103,895 |
| Output tokens | 105,047 |
| Cache hits | 0 invocation and 0 stage cache hits |
| Ledger reconciliation | calls and both token totals match invocation log exactly |
| Pending ledger reservations | 0 |
| Cost handling | all 44 calls `unavailable`; no verified dollar amount |
| Invocation records | 49: 44 paid calls plus 5 zero-usage parse-error events |
| Real sandbox executions | 28/28 used the verified image ID |

The run stayed below every approved hard limit. The five infrastructure-void records are completed and skipped by ordinary resume. They can only be re-attempted with the explicit `--retry-void-infra` mode, which creates new run IDs and preserves the original void records.

## Retry plan, not approved or executed

The plan-only retry contains 5 paths and at most 15 model calls, 170,010 input tokens and 61,440 output tokens. If approved, it should reuse the original ledger so aggregate usage remains under the already declared 120 / 950,000 / 340,000 caps:

```bash
.venv/bin/python -m experiments.run_workflow_grid \
  --projects retail_sales --stages 3 --repeats 1 \
  --retry-void-infra --execute \
  --ledger results/raw/ledgers/expB_paths_20261118T030936Z.json \
  --max-calls 120 \
  --max-input-tokens 950000 \
  --max-output-tokens 340000
```

C-B-B already incurred one paid cleaning call before its sandbox failure. Retrying it will make a fresh call, so retry requires a separate explicit decision. The Docker image must first be rebuilt, pass 16/16 isolation tests again, and be protected from disappearing during a long model response.

## Stored evidence

- Workflow records: `results/raw/workflow_runs/expB_paths.jsonl`
- Invocation log: `results/raw/invocations.jsonl`
- Usage ledger: `results/raw/ledgers/expB_paths_20261118T030936Z.json`
- Per-run prompts, responses, reasoning, code, executions and validations: `results/raw/runs/expB_paths-*`
- Sandbox verification record: `results/raw/sandbox_verification.json`

## Decision gate

Do not treat the initial grid as 27 completed model outcomes, do not count the five voids as model failures, and do not run routing evaluation yet. First decide whether to retry the five void paths. Independently, review the systematic structured-ranking failures before authorizing full experiments; any post-freeze prompt, schema or validator change must be explicitly documented as such.
