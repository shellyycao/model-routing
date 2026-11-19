# Architecture & Coordination

## Research direction (confirmed)

- **A. Experimental foundation:** find out when collaboration between different LLMs improves end-to-end workflow performance.
- **B. Primary XAI contribution:** test whether model-routing explanations and counterfactual predictions are (1) computationally faithful and (2) empirically valid.

**Scope (fixed; changes need the user's approval):**
- Three models, A / B / C.
- Three stages: cleaning → analysis → reporting.
- Three to five synthetic projects.
- All 27 paths per project.
- Independent stage-level evaluation (Experiment A).
- Task-only (S2) vs. workflow-aware (S3) routing, plus S1 single-model baselines and an S4 retrospective oracle.
- Execution-validated counterfactuals.
- An optional Next.js app.

## Models (verified 2026-11-17, us-east-1)

| Alias | Model | Bedrock ID |
|---|---|---|
| A | Claude Sonnet 4.6 (Anthropic) | `us.anthropic.claude-sonnet-4-6` |
| B | Amazon Nova Pro (Amazon) | `us.amazon.nova-pro-v1:0` |
| C | gpt-oss-120b (OpenAI, open-weight) | `openai.gpt-oss-120b-1:0` |

**Pricing:** unverified for all three models.
- The `pricing:GetProducts` API is not permitted for this IAM user, and the public page shows no us-east-1 rows for these models.
- Until a price is set by hand with source and date, cost is recorded as `unavailable`.
- Hard limits on **calls and tokens** apply. The dollar guard reports itself as inactive.

## Evaluation framework (no weighted composite score)

| Group | Contents | Role |
|---|---|---|
| **A. Feasibility** | Mandatory stages executed, required artifacts present, mandatory checks passed | Hard gate. If any mandatory stage fails, the workflow is infeasible, even when a downstream artifact looks valid, and the failure stays visible per stage. |
| **B. Stage quality** | Cleaning: correctness, integrity, schema compliance. Analysis: numerical accuracy, calculation coverage, reproducibility. Reporting: numerical consistency, finding coverage, unsupported-claim count | Each metric is reported separately |
| **C. Efficiency** | End-to-end time, API latency, execution time, tokens, verifiable cost, model switches | Preferences applied among feasible paths |

**Routing objective:**
- Predefined quality constraints, a minimum feasibility probability, and a lexicographic preference order (for example cost, then time) with a tie tolerance.
- When no candidate satisfies the constraints, the router returns **"No feasible path"**.
- Pareto-optimal sets are reported when no single path is best.

## Shared contracts

`src/contracts/` is **frozen at v1.2**. Only the lead edits it. Every change bumps `CONTRACT_VERSION` and is logged below.

| Module | Defines |
|---|---|
| `ids.py` | `StageId`, path IDs (`"A-B-C"`), Cartesian path enumeration, switch counting |
| `project.py` | `ProjectSpec` (`datasets/projects/<id>/project.json`) |
| `artifacts.py` | Model output schemas (`CleaningOutput`, `AnalysisOutput`, `ReportOutput`), `HandoffPackage` |
| `execution.py` | `Executor` protocol, `ExecutionResult` and status enum, `ValidationResult` |
| `records.py` | `StageRunRecord`, `WorkflowRunRecord` (feasible ⇒ every stage passed), `StageBenchmarkRecord`, quality metric names |
| `routing.py` | `RoutingObjective`, `PathPrediction`, `DecisionTrace` (rejects leakage), `CounterfactualPrediction` (hashed, tamper-evident), `CounterfactualValidation`, `FaithfulnessCheck` |

**Contract change log:**
- 1.0 (2026-11-17): initial freeze.
- 1.1 (2026-11-17): fixes from the Reviewer's findings in `docs/reviews/2026-11-17_review_M1_contracts_v1.0.md`. No records existed yet.
  - **Runs (B3, M11):** a `WorkflowRunRecord` must have exactly one stage record per path position, in order, with matching models. Statuses must be consistent, and stages after a failure must be marked not-run. `Feasibility.outcome` is `feasible`, `infeasible` or `void_infra`, and `.feasible` became a property.
  - **Stage records (M3, M9):**
    - `StageRunRecord` gains a prompt hash, cache-hit flag, shared-run list, input and output artifact hashes, cost status, and `conditional_validation`.
    - `ValidationResult.quality_basis` is either `ground_truth` or `conditional_reference`.
    - `WorkflowRunRecord` gains `failure_policy` and `conditional_quality`.
  - **Evidence (M6):** evidence is a typed `EvidenceRef(project_id, run_id, experiment_id)`, and every reference is checked against the training projects. Traces carry `training_data_hash`, and project IDs are normalised.
  - **Traces (M10):** `DecisionTrace` gains `target_project`, `selection_steps`, `inactive_criteria`, set-consistency validators and `trace_hash()`.
  - **Counterfactuals (M7, M8):**
    - `CounterfactualPrediction` is frozen and hashed with canonical JSON over an explicit field list. The hash is required, and records are built with `.create()`.
    - It gains strategy, version, config, objective, absolute predictions and delta intervals.
    - `CounterfactualValidation` gains repeat spread, interval coverage and `check_against()`.
  - **Faithfulness:** `FaithfulnessCheck` gains the trace and explanation hashes, a list of checks, and a replay result.
  - **Helpers:** `canonical_json`, `sha256_hex` and `chain_hash` for append-only logs.
- 1.2 (2026-11-18): a pre-experiment design change approved by the user, following the benchmark-validity review (`docs/reviews/2026-11-18_review_benchmark_validity.md`).
  - **Failure policy:** a new `continue_with_actual_artifact` policy.
    - A downstream stage runs on the ACTUAL upstream artifact whenever it is structurally consumable. The artifact is never replaced with canonical data.
    - Otherwise the stage is `BLOCKED_BY_INVALID_ARTIFACT`, which is attributed upstream.
    - The strict `outcome` is kept unchanged.
    - `PropagationSummary` records downstream executability, upstream error severity, end-to-end accuracy, propagation impact and blocked stages.
    - `StageRunRecord.structural_ok` is added.
  - **Reports:** `KeyFinding` gains `direction`, `ranking` and `derived_values` (a list of `DerivedValue`).
  - **Handoffs:** `HandoffPackage.validation_status` may only be `passed`, `failed`, `not_run` or `blocked_by_invalid_artifact`. Validator details never reach models.
  - **Projects:**
    - `ProjectSpec` gains `input_files` (`InputFile`), the explicit allow-list of model-readable files, and `model_view()`, the only project data that may be rendered to models. `notes` and canonical or ground-truth paths are hidden.
    - A validator rejects canonical or ground-truth files listed as inputs.
    - `AnalysisQuestion` gains `direction_key` and `ranking_labels`; these are validator-only.

## Benchmark freeze

- **benchmark-v2-frozen (2026-11-17 EST / 2026-11-18 UTC):** frozen before any pilot or full-model outcomes.
  - Dataset generator: 2.0; four synthetic projects; byte-reproducible committed artifacts.
  - Contracts: 1.2.
  - Validators: cleaning 1.0, analysis 1.0, reporting 2.0.
  - Prompts: v2 (v1 preserved); identical for every model/path.
  - Verification: 291 passed, 8 paid-live tests skipped; Docker isolation 16/16 and real-sandbox E2E 2/2.
  - Independent review: `docs/reviews/2026-11-18_review_benchmark_v2_t1.md`, freeze approved with no remaining finding.
  - Post-freeze benchmark or prompt changes must be documented as post-hoc and use a new version/tag.

## Post-freeze v3 candidate and Docker lease (2026-11-18)

- Frozen v2 remains unchanged and active. The additive reporting validator
  `3.0-post-freeze`, `prompts/v3/` and offline rescore are documented in
  `docs/reviews/2026-11-18_post_freeze_v3_audit.md`; v2 and v3 scores are stored separately.
- The current sandbox verification lives at `results/verification/sandbox_verification.json` so the
  prior raw verification record is not overwritten. Paid runners preflight before creating a model
  client and pin the verified image with a restricted holder container for the whole run.
- No paid calls were made for this repair. The five pilot `void_infra` records remain unchanged.

## File ownership (exclusive write)

| Owner | Files |
|---|---|
| Lead | `src/contracts/`, `configs/experiments.yaml`, `docs/architecture.md`, `docs/AGENT_STATUS.md`, `docs/reviews/`, `README.md`, `.claude/` |
| LLM Infra Engineer | `src/bedrock/`, `configs/models.yaml`, `scripts/discover_models.py`, `tests/test_bedrock*` |
| Benchmark Engineer | `datasets/`, `src/evaluation/{cleaning,analysis,reporting}.py`, `src/workflow/executor.py`, `sandbox/`, `tests/test_eval*`, `tests/test_executor*`, `tests/fixtures/benchmark/` |
| Workflow Engineer | `src/workflow/{stages,orchestrator,handoff}.py`, `src/storage/`, `src/evaluation/workflow_metrics.py`, `prompts/`, `experiments/run_stage_benchmark.py`, `experiments/run_workflow_grid.py`, `tests/test_workflow*`, `tests/fixtures/workflow/` |
| XAI Researcher | `src/routing/`, `src/explainability/`, `configs/routing.yaml`, `experiments/evaluate_routing.py`, `experiments/validate_counterfactuals.py`, `docs/methodology.md`, `tests/test_routing*`, `tests/test_xai*`, `tests/fixtures/xai/` |
| Research Reviewer | Read-only. The lead stores its reports in `docs/reviews/`. |
| Frontend Engineer | `web/` |

**How the agents work:**
- Each writing agent works in its own git worktree and branch.
- The lead reviews, runs the tests, and merges.
- Paid Bedrock calls are made only by the lead, and only after the user approves.

## Critical rules (from the master spec; non-negotiable)

1. Never fabricate model performance or experimental results.
2. Never replace failed model outputs with ground truth during full-workflow evaluation.
3. Never use test outcomes to retrospectively construct a supposedly prospective routing prediction.
4. Never claim that workflow interaction effects are caused only by handoff costs.
5. Never compare models under materially different task instructions without documenting the difference.
6. Never execute untrusted generated code without isolation.
7. Never expose AWS credentials.
8. Never treat lower API latency as lower end-to-end completion time.
9. Never describe oracle performance as deployable router performance.
10. Never claim that three tested models establish universal LLM rankings.
11. Never hide uncertainty or unsuccessful experimental runs.
12. Never put visual polish ahead of a correct research implementation.

**Additional rules from the user (2026-11-17):**
- Repeat runs must bypass the response cache and keep each individual record.
- Report variability without claiming statistical significance.
- A missing price is never treated as $0.

## Experiment protocol versions
- **v2** (`benchmark-v2-frozen`): pilot only.
- **v3** (`benchmark-v3-frozen`): prospective primary, adopted by the user on 2026-11-18 (see `docs/EXPERIMENT_PROTOCOL.md` §12).
- The experiment ID suffix `_v3` selects v3. The two versions are never pooled.
