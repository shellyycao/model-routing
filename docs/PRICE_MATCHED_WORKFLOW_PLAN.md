# Price-matched workflow and routing replication plan

## Status and decision boundary

**Protocol status:** compatibility pilot and main run completed; the five-cell Docker-void rerun is
approved pending the exact amended freeze tag.
On 2026-11-19 the user
decided, in the exact words **“16384, $100 cap”**: all three models use common `maxTokens=16384` in
Parts A and B, and the pilot plus any later main run share a **$100 hard cap** enforced by the
reserve-then-settle ledger. After reviewing the pilot, the user explicitly approved the main run on
2026-11-19 with the exact words **“Approve the main run (504 calls, about $43 expected, $100
cap)”**.

The completed pilot remains tied to `price-matched-workflow-pilot-v1`. The Docker-void rerun now
requires tag `price-matched-workflow-main-v1.2` and the main manifest with `main_approved=true`;
authorization alone does not bypass this freeze gate. Tags `price-matched-workflow-main-v1` and
`price-matched-workflow-main-v1.1` remain as history and do not authorize the amended runner.

### Execution amendment — 2026-11-19

Before any main-run call, Docker Desktop intermittently failed to resolve the short reference
`model-routing-xai-sandbox:1.0`, even while the fully qualified name and immutable image ID remained
available. The failure reproduced from both the shell and Python and is attributable to short-name
resolution in Docker Desktop's containerd image store. **No main-run model call had been made.**

The runner now constructs its sandbox executor with the already verified immutable image ID
`sha256:88988a15503bdb96538c3dd62244a79879d5c7848397db18b1267ccfd0a9727a`. Availability checks,
the restricted lease container, and every `docker run` use that same ID. If it is absent, execution
fails before Bedrock construction and does not fall back to a tag. The shared executor's default
short-name constant is unchanged so other frozen experiments are unaffected. The sandbox contents,
data, prompts, models, parameters, order, validators, retry rules, and budget are unchanged; this is
an execution-only reproducibility amendment.

### Docker-void rerun amendment — 2026-11-19

The main run completed with Part A 36/36, Part B 156/156, no failed API attempts, no pending ledger
reservations, and $25.480151 total spend including the pilot. The main-grid checkpoint projected
$24.365199, below the $100 cap. During an approximately two-minute Docker daemon outage, five
repeat-0 cells became `void_infra` because `docker info` timed out and the sandbox gate refused
execution:

- `energy_consumption`: `C-C-A`, `C-C-B`, `C-C-C`;
- `retail_sales`: `A-A-A`, `A-A-B`.

The user gave standing authorization on 2026-11-19, in the exact words
(translated) **“No need for my approval; if it's a Docker problem, just re-run it”** (exact original wording in the manifest). The dedicated `--rerun-docker-voids` entry point selects only original
repeat-0 `void_infra` records whose failure detail contains both sandbox-gate refusal and Docker
daemon/`docker info` failure. The five targets are fixed before execution and each receives exactly
one logical rerun regardless of earlier rerun outcomes. Models, parameters, prompts, repeat index,
immutable sandbox image, shared ledger, and $100 cap remain unchanged.

Every rerun has a new `infra_attempt=1` run ID and `rerun_of` pointing to the original. The original
156 records are an immutable file prefix and are never deleted or overwritten; reruns append up to
five lines. A repeated command skips any original that already has a rerun record. The exact command
is:

```bash
.venv/bin/python -m experiments.run_price_matched_workflow --rerun-docker-voids
```

The plan-by-default entry point is:

```bash
.venv/bin/python -m experiments.run_price_matched_workflow
```

It prints the selected option, the preserved alternative-budget comparison, and the pending main
freeze requirement; it makes no network or model call by default.

## Research question and fixed protocol

The primary question is whether the original finding—computationally faithful explanations but
weak empirical prediction of feasibility—replicates with a second, account-callable model set. The
secondary aim is end-to-end workflow evidence for Kimi K3 and GLM 5.

The following are fixed from `benchmark-v3`:

- the four projects and their current dataset hashes: `customer_churn`, `energy_consumption`,
  `retail_sales`, and `support_operations`;
- `prompts/v3`, primary validators v3, and additive post-hoc v3.1 reporting rescore;
- fresh calls, the `continue_with_actual_artifact` handoff/failure policy, the pinned sandbox image,
  resource limits, and no canonical-data substitution;
- the 27-path, three-stage grid and the same six repeated paths;
- leave-one-project-out folds, `configs/routing.yaml`, decision traces, template explanations,
  prospective counterfactual logging, retrospective validation, and S4 only as an oracle reference;
- `configs/routing_cost_posthoc.yaml` for a separately labelled post-hoc/exploratory cost-aware view.

The new Router must train **only** from
`expA_price_matched_workflow_v3` and `expB_price_matched_workflow_v3`. Original A/B/C workflow
records may be used only as a clearly labelled historical comparison or as assumptions for the
pre-run budget; they must never enter a new LOPO training fold.

## Model mapping and parameters

Paths retain the A/B/C notation required by the existing orchestrator and Router, but the registry
is rebuilt offline from `price_matched_model_verification.json`:

| Alias | Model | Callable model ID | Temperature |
|---|---|---|---|
| A | Sonnet 4.6 | `us.anthropic.claude-sonnet-4-6` | field sent as `0` |
| B | Kimi K3 | `us.moonshotai.kimi-k3` | field omitted |
| C | GLM 5 | `zai.glm-5` | field sent as `0` |

Kimi's omission is the already verified model-specific deviation. No runner may remove, add, or
alter a parameter after an error. Reasoning remains the vendor default. The selected common output
budget is **16,384 tokens**.

This differs from the original Parts A/B setting of 4,096. It gives Kimi's returned reasoning more
room and reduces the risk that the experiment primarily measures truncation, but the replication is
therefore not identical on output budget; every comparison with the original model set must
disclose this setting difference.

## Compatibility pilot

The pilot had exactly **9 logical calls**: canonical cleaning, analysis, and reporting for
each of A/B/C on `retail_sales`, in stage-major then A/B/C order. Retail sales is used because it was
already pilot-exposed; the other three projects receive no new exposure before the main run.

Pilot acceptance checks are structural only:

- the request is accepted with the exact effective parameters;
- the response parses into the existing stage schema;
- generated artifacts reach the existing sandbox and structural gates;
- raw input/output usage, returned reasoning characters, stop reason, latency, and incurred cost are
  recorded; and
- Docker/sandbox availability is distinguished from model behavior.

Pilot quality must not be inspected, aggregated, or used for routing, and the pilot experiment ID
is excluded from all main analysis. If a model rejects a parameter, the remaining pilot slots for
that model are skipped and the reason is recorded; no unapproved parameter-removal retry is
allowed. The user approved this pilot under the selected 16,384-token setting and shared $100 cap.
It uses the same capped ledger as any later approved main run.

The pilot completed 9/9 API calls successfully: all 9 responses parsed, all returned
`stopReason=end_turn`, and no parameter failure occurred. The shared ledger recorded 9 attempts,
20,741 input tokens, 27,868 output tokens, and **$0.449949**. Structural checks were recorded but
answer quality was not inspected; the pilot remains excluded from main training and analysis.

## Main experiment

Execution uses fresh calls and new experiment IDs:

| Component | Design | Potential logical model calls |
|---|---|---:|
| Part A | 4 projects × 3 stages × 3 models | 36 |
| Part B main | 4 projects × all 27 paths × up to 3 stages | 324 |
| Part B repeats | repeats 1–2 of 6 paths × 4 projects × up to 3 stages | 144 |
| Main total | Parts A + B | 504 |

The six repeated paths are `A-A-A`, `A-A-C`, `A-C-A`, `A-C-C`, `B-B-B`, and `C-C-C`. A stage
blocked by an unusable upstream artifact makes no call, so 504 is the all-stages-execute ceiling,
not a promise of actual billed calls.

The runner executes Part A first and then stops for a mandatory cost/integrity checkpoint. Only the
explicit `--continue-after-part-a` resume flag can begin Part B after approval remains valid.
Completed run IDs are skipped and never selectively rerun except for the five outcome-blind Docker
voids authorized by the dated amendment above. Other void-infrastructure reruns require a separate
protocol amendment and user decision. The durable checkpoint is
`results/raw/price_matched_workflow/part_a_cost_checkpoint.json`; pilot and final summaries live in
the same directory.

After the 27-path main grid, the runner stops a second time before repeats 1–2. It writes
`results/raw/price_matched_workflow/main_grid_cost_checkpoint.json`, projects repeat spend from the
observed main-grid spend using the pre-frozen realistic repeat/main-grid cost ratio, and records
whether projected total spend is at most $100. Repeats require a new invocation with both
`--continue-after-part-a` and `--continue-after-main-grid`; resume refuses if the checkpoint is
missing, changed, or projects above the cap.

The exact paid sequence, each rechecking the main manifest and tag, is:

```bash
# Part A; stops at the Part A checkpoint
.venv/bin/python -m experiments.run_price_matched_workflow --execute-approved-main

# 27-path main grid; stops before repeats
.venv/bin/python -m experiments.run_price_matched_workflow --execute-approved-main --continue-after-part-a

# Resume after the reviewed main-grid checkpoint and run repeats 1–2
.venv/bin/python -m experiments.run_price_matched_workflow --execute-approved-main --continue-after-part-a --continue-after-main-grid
```

Progress and resume bookkeeping read only the two task-record files—never the adjacent invocation
log or a `*.jsonl` directory glob:

| Task file | Complete line count | Progress grouping fields |
|---|---:|---|
| `results/raw/stage_benchmark/expA_price_matched_workflow_v3.jsonl` | 36 | `project_id`, `stage`, `model_alias` |
| `results/raw/workflow_runs/expB_price_matched_workflow_v3.jsonl` | 156 originals; up to 161 after reruns | `project_id`, `path_id`, `repeat_index`, `rerun_of` |

For Part B, `repeat_index=0` identifies the 108 main-grid records; indices 1 and 2 identify the 48
repeat records. `results/raw/price_matched_workflow/invocations.jsonl` remains the append-only call
log and may be grouped by `context.experiment_id`, but it is not a completion source.

## Routing and analysis

After all 36 Part A records and 156 original Part B workflow records exist, offline routing runs in two
separated phases: predictions/traces/explanations first, then held-out validation. The prepared
analysis config is `configs/analysis_price_matched_workflow_v3.yaml`; primary routing outputs go to
`results/routing/price_matched_workflow_v3_primary/`.

```bash
.venv/bin/python -m experiments.run_price_matched_workflow --run-offline-routing
```

This offline phase requires 36 Part A records and resolves the Part B append-only file to exactly
156 effective cells. For a matching `(project_id, path_id, repeat_index)`, a rerun whose outcome is
not `void_infra` replaces the original Docker void for analysis; if the rerun is also void, the
original void remains the effective cell. In both cases, the raw original and rerun are retained and
the resolution audit reports their run IDs. The same rule is set in
`configs/analysis_price_matched_workflow_v3.yaml`. Original-model files are never loaded.

The prospective analysis must report S1–S3 selections, S4 oracle reference, explanation
faithfulness and replay, counterfactual feasibility direction, project/path outcomes, propagation,
and variability. V3 remains primary; v3.1 is displayed beside it as secondary. The cost-aware
variant is computed later from the same new records only and remains **post-hoc / exploratory** in a
separate output directory and hash chain. It must not rewrite the prospective traces.

No original-model record may appear in a new trace's evidence references. A pre-validation audit
must check that every training reference comes from one of the other three new projects and that the
counterfactual prediction chain was durable before validation began.

## Budget decision and preserved alternatives

The figures below are generated by `experiments.run_price_matched_workflow.build_plan()` using the
verified regional prices. They include the 9-call pilot and 504-call main plan.

| Common maxTokens | Pilot realistic / static worst | Main realistic / static worst | Combined realistic / static worst | Comparability consequence |
|---:|---:|---:|---:|---|
| 4,096 | $0.401 / $3.573 | $21.561 / $195.075 | **$21.962 / $198.648** | Matches original Parts A/B, but Kimi is likely to hit the ceiling; truncation may measure the budget rather than the model. |
| 16,384 | $0.827 / $10.246 | $41.991 / $562.191 | **$42.817 / $572.437** | Gives returned reasoning substantially more room, but changes a core setting relative to the original run. |

The static worst case assumes every stage executes, every logical call consumes five paid API
attempts, and every attempt reaches `maxTokens`. The realistic estimate is still conservative: all
stages execute, attempts average 1.02 per logical call (close to the completed independent run's
retry rate), inputs use observed Sonnet workflow means adjusted by observed tokenizer ratios, and
outputs use observed Sonnet workflow medians scaled by completed price-matched output ratios and
capped at the selected `maxTokens`. In particular, the Kimi scaling reflects that its completed
independent outputs mainly contained returned reasoning text; it is an estimate, not workflow data.

The user selected the 16,384 option and a $100 total cap. This cap is below the $572.437 static worst
case but above the $42.817 realistic estimate. The accepted consequence is that reserve-then-settle
enforcement can stop the experiment with `budget_refused` before the logical design is complete if
actual use departs substantially from the estimate. The runner never raises the cap itself. The
ledger is shared by pilot and main, and checkpoints report actual spend, remaining cap, calls,
retry attempts, input tokens, output tokens, and pending reservations.

## Execution, integrity, and stop rules

- Paid execution, including `--rerun-docker-voids`, requires the main manifest, exact
  `price-matched-workflow-main-v1.2` tag,
  maxTokens 16,384, the shared $100 cap, unchanged hashes, and `main_approved=true`.
- The pilot, Part A, and Part B use distinct experiment IDs but one append-only invocation log and
  one reserve-then-settle ledger. All raw records and artifacts are append-only.
- The order is fixed by the machine plan. Errors never trigger model substitution or automatic
  parameter changes.
- Docker preflight happens before Bedrock construction. An image lookup/build/lease failure is
  recorded as `sandbox_unavailable` / `void_infra`, with `model_failure=false` and zero model calls;
  it is never scored against a model.
- Each checkpoint reconciles run IDs, invocations, ledger entries, hashes, effective parameters,
  recorded usage and cost. Missing usage is unknown, never zero.
- Execution stops on a hash mismatch, cap refusal, parameter incompatibility, unexpected model ID,
  raw-record conflict, selective-retry risk, or non-empty output target with an unverified prefix.

## Freeze checklist

Before the paid main run, Claude must commit the main manifest and create the exact main tag. The
main freeze records:

1. selected common `maxTokens=16384`, the user's exact wording, and the difference from the
   original 4,096-token Parts A/B setting;
2. the shared $100 hard cap and intentional acceptance that it is below static worst case;
3. the completed 9/9 pilot evidence and the user's exact main approval wording;
4. SHA-256 hashes from `protocol_hashes()` for this plan, brief, runner, model verification,
   datasets, prompts, sandbox, routing configs, and analysis config;
5. the frozen experiment IDs, main order, repeat paths, ledger/output paths, retry
   policy, stop rules, and exact required tag; and
6. both dated execution amendments, the user's Docker-rerun authorization, the five original run
   IDs and immutable-prefix hash, retention of both old main tags, and the outcome-blind analysis
   replacement rule.
