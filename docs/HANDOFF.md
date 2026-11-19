# HANDOFF: model-routing-xai

- **Handover date:** 2026-11-18.
- **Frozen benchmark commit:** `411fcd7` on `main`, tagged `benchmark-v2-frozen`. Run `git log -1` for the latest handover/pilot-planning documentation commit.
- **Companion documents:**
  - `docs/EXPERIMENT_PROTOCOL.md`: the frozen experimental protocol.
  - `docs/architecture.md`: scope, contracts change log, file ownership, critical rules.
  - `docs/AGENT_STATUS.md`: per-agent history.
  - `docs/reviews/`: every review and its disposition.
  - `docs/reviews/2026-11-18_post_freeze_v3_audit.md`: Docker root cause, reporting taxonomy,
    additive v3 design and offline saved-output rescore.

**Labels used here:**
- **[TESTED]** means automated tests exercise the feature and pass at the handover commit.
- **[PLANNED]** means not implemented.
- **[UNTESTED]** means code exists but has not been run in that mode.

---

## 0. CURRENT STATE: overnight update, 2026-11-18. This section SUPERSEDES the status in §2, §6, §7 and §9 where they differ.

**Research structure:**

| Part | Topic | Report |
|---|---|---|
| A | Independent task-specific model evaluation | `results/reports/phase1_model_specialization.md` (data-workflow stages) + `results/reports/independent_task_benchmark.md` (A1 debugging, A2 extraction, A3 literature; tag `independent-v1-frozen`; 90 runs, 0 void) |
| B | End-to-end multi-model workflows | `results/reports/phase2_3_workflow_and_xai.md` |
| C | Explainable routing and counterfactual validation | same file |

**Primary experiment and versions:**
- **Prospective v3:** tag `benchmark-v3-frozen`, commit `22a56e6`. Switch with `--protocol v3`; experiment IDs `expA_stage_v3` and `expB_paths_v3`.
- **v2:** kept as a pilot only.
- **Post-hoc reporting validator v3.1:** a secondary rescore, never substituted for v3 (`docs/reviews/2026-11-18_reporting_v3_1_posthoc.md`).

**Completed and tested:**

| Item | Result |
|---|---|
| Experiment A v3 | 36/36 runs |
| Experiment B v3 | 108/108 main runs + 48 pre-registered repeats; 0 void_infra, so nothing needed a retry |
| Reconciliation (`results/processed/reconciliation.json`) | 356/356 invocations referenced; 339 API attempts = 339 ledger calls; 240/240 executions in verified image `88988a15`; 0 cache hits |
| v3.1 rescore | Experiment A 7→9 of 12 reports; Experiment B 32→43 of 82 reports. All flips are the single customer_churn q7 comparative-clause pattern. |
| M5 (`results/routing/v3_primary/`) | Leave-one-project-out S1–S4, 20 traces, 50 hash-chained counterfactual predictions, all validated |
| M6 (`results/processed/v3_primary_analysis/`, config `configs/analysis_v3.yaml`) | Every table complete |
| Tests | Full suite 324 passed, 8 skipped (paid live tests) |

**Headline findings** (exploratory, n = 4 projects; details in the reports):
- **Part A:**
  - Claude is the most accurate at cleaning (also 28/36 in Experiment B).
  - Claude and gpt-oss tie on analysis.
  - Nova Pro is fastest, but its cleaning and analysis code failed.
  - gpt-oss's cleaning failures are output truncation at 4096 tokens.
- **Part B:**
  - Single-model vs cross-model strict feasibility is about equal on average: 2/12 vs 15/96.
  - In 2 of 4 projects no single model completed the workflow but some mixtures did.
  - Cleaning is the bottleneck: first failure in 64 of 108 runs.
  - Upstream errors propagate: analysis ground-truth accuracy median 0.10 vs conditional accuracy 1.0 on bad-but-usable cleaned data.
  - 6 of 24 repeated cells flip outcome.
- **Part C:**
  - S3 (workflow-aware) picked an executed-feasible path in 3 of 4 held-out projects, from single runs; S2 in 0 of 4.
  - Explanations are computationally faithful: 429/429 claims consistent, 20/20 replays match.
  - Feasibility counterfactuals are directionally right only 22/50 times. **Faithful ≠ empirically valid.**

**Known issue:** the frozen v3 reporting validator falsely rejects comparative clauses ("X is N% higher than Y"). It affects customer_churn heavily, including making Nova look like the best churn reporter. v3.1 is the secondary view.

**Standing instruction (2026-11-18):** the user said not to wait for approvals. Proceed autonomously, but keep hard limits, document every change and never fabricate.

**A1–A3:** DONE.
- Runner: `experiments/run_independent_benchmark.py`.
- Analysis: `experiments/analyze_independent.py`.
- Post-hoc views: `experiments/rescore_independent_posthoc.py`, for A3 grounding v1.1 (frozen-scorer paraphrase artifact) and the A2 unwrapped-content diagnostic (gpt-oss missing wrapper).

**Next tasks:**
1. M7 website, when the user asks: over `results/processed/*`, with Parts A, B and C kept separate.
2. Optional:
   - extra repeats for paths that S3 selected from single runs;
   - a harder A1 (ceiling effect).

## 1. Project overview

This is a research system for **explainable multi-model routing** over a three-stage knowledge workflow: data cleaning → data analysis → reporting. In each stage an LLM writes Python, which runs in a sandbox, or writes a report.

- **Main question:** can execution-validated counterfactual explanations show when multi-model routing improves end-to-end workflow performance compared with single-model execution?
- **RQ1:** how do the LLMs perform per stage (correctness, reliability, latency, cost)?
- **RQ2:** does picking the best model per stage give the best end-to-end workflow? Do interaction effects, handoffs or error propagation change the answer?
- **RQ3:** are routing explanations (a) **computationally faithful** to the router, and (b) **empirically valid**, meaning their counterfactual predictions match executed outcomes? These two are evaluated separately.
- **Research direction:**
  - A, the experimental foundation: when does LLM collaboration help?
  - B, the primary XAI contribution: faithfulness and empirical validity of routing explanations.

**Models** (us-east-1, AWS profile `xai-bedrock`, Converse API):

| Alias | Model | Bedrock ID |
|---|---|---|
| A | Claude Sonnet 4.6 | `us.anthropic.claude-sonnet-4-6` |
| B | Amazon Nova Pro | `us.amazon.nova-pro-v1:0` |
| C | OpenAI gpt-oss-120b (open-weight) | `openai.gpt-oss-120b-1:0` |

## 2. Implementation status

| Milestone | Status | Evidence |
|---|---|---|
| M1 Bedrock client | **Done [TESTED]** | `tests/test_bedrock_*.py`. Live runs: smoke test 6/6 and live tests 8/8 (13 paid calls; logs in `results/raw/`). |
| Contracts v1.2 | **Frozen [TESTED]** | `tests/test_contracts.py` |
| M2 Benchmark v2 | **Frozen [TESTED]:** 4 projects, ground truth, validators, prompts v2 | `tests/test_eval_*.py`; `python -m datasets.generate --check`; tag `benchmark-v2-frozen` |
| Sandbox | **Repaired [TESTED]:** rebuilt unchanged image, 20/20 controls; paid runners now preflight before client construction and hold an exact-image lease | `tests/test_executor.py`, `results/verification/sandbox_verification.json` |
| M3 Workflow | **Done offline [TESTED]:** one 3-stage path through the real sandbox with a fake LLM | `tests/test_workflow.py`, `tests/test_integration_e2e.py` |
| M4 Path grid, resume, metrics | **Done [TESTED]** offline and in real-model two- and three-stage retail pilots. Five three-stage paths remain `void_infra`. | `tests/test_workflow.py`, `docs/reviews/2026-11-17_retail_sales_pilot_2stage.md`, `docs/reviews/2026-11-17_retail_sales_pilot_3stage.md` |
| M5 Routing and XAI | **Done offline [TESTED]** on synthetic fixtures only. **No results exist.** | `tests/test_routing.py`, `tests/test_xai.py` |
| Benchmark revision v2 (T1) | **Done [TESTED, INDEPENDENTLY REVIEWED]** | `docs/reviews/2026-11-18_review_benchmark_v2_t1.md` |
| Benchmark freeze | **Done** | tag `benchmark-v2-frozen` |
| Pilot plan | **Done [PLAN ONLY]**, no AWS calls | `docs/PILOT_PLAN.md` |
| Two-stage retail_sales pilot | **Done [REAL MODELS, INSPECTED]**: 3/9 feasible, 13 calls | `docs/reviews/2026-11-17_retail_sales_pilot_2stage.md` |
| Three-stage retail_sales pilot | **Executed, incomplete:** 22 infeasible + 5 `void_infra`; retry unapproved | `docs/reviews/2026-11-17_retail_sales_pilot_3stage.md` |
| Post-freeze reporting v3 | **Done offline [TESTED]:** additive validator/prompt; saved outputs rescore v2 0/10, v3 secondary analysis 7/10; active workflow remains v2 | `docs/reviews/2026-11-18_post_freeze_v3_audit.md` |
| Experiment A and full experiments | **[PLANNED]**, need separate user approval | |
| M6 Research analysis and figures | **[PLANNED]** | |
| M7 Next.js / Vercel demo | **[PLANNED]**, optional | |

**Latest offline repair result:** `.venv/bin/python -m pytest -q` gives **303 passed, 8 skipped**.
The 8 skipped tests are paid live Bedrock tests and were not authorized. The focused repair suite is
87/87, the real executor suite is 20/20, and all four generated projects are byte-reproducible.

## 3. Repository structure
```
configs/models.yaml        models, inference settings, pricing rules (all null), concurrency
configs/routing.yaml       routing objective, shrinkage k, tie tolerance
src/contracts/             FROZEN shared schemas v1.2 (ids, project, artifacts, execution, records, routing)
src/bedrock/               client.py (Converse, retries, cache, limits), usage.py (records + cross-process
                           ledger), models.py (registry, pricing rules), concurrency.py, provenance.py, discovery.py
src/evaluation/            frozen validators plus additive reporting_v3.py; workflow_metrics.py summaries
src/workflow/              executor.py (Docker sandbox + image lease), stages.py (prompts, SandboxGate, stage runners),
                           handoff.py, orchestrator.py (run_path, failure policies, propagation summary)
src/storage/run_store.py   append-only run store, resume, mode pinning
src/routing/               data.py (LOPO TrainingView), estimation.py, scoring.py, router.py, strategies.py,
                           counterfactual.py (hash-chained log), outcomes.py, config.py
src/explainability/        explanations.py (templates from traces), validation.py (faithfulness + empirical)
datasets/                  generate.py + per-project generators; projects/<id>/{raw.csv, project.json,
                           canonical/, ground_truth.json}
prompts/v1/, prompts/v2/   frozen prompt versions; v2 active and identical for all models
prompts/v3/                explicit post-freeze reporting contract; candidate only, not active
sandbox/Dockerfile         execution image (python 3.12.8-slim, numpy 2.2.6, pandas 2.2.3, uid 10001)
experiments/               m1_smoke.py, run_stage_benchmark.py (Exp A), run_workflow_grid.py (Exp B),
                           evaluate_routing.py, validate_counterfactuals.py
scripts/discover_models.py control-plane model discovery (free)
tests/                     unit + integration tests; fixtures under tests/fixtures/* labelled SYNTHETIC_FIXTURE
results/raw/               append-only historical evidence; unchanged by the offline repair
results/processed/         additive offline v3 side-by-side rescore
results/verification/      current verified Docker image record (historical raw record preserved)
docs/                      HANDOFF.md, EXPERIMENT_PROTOCOL.md, architecture.md, methodology.md (draft),
                           AGENT_STATUS.md, reviews/
.claude/agents, .claude/skills   role definitions and status protocol (Claude Code specific)
```

## 4. Key architecture and data contracts (`src/contracts/`, v1.2)
- **IDs and paths:**
  - `StageId` is cleaning, analysis or reporting.
  - Path IDs look like `"A-B-C"`; position i is the model for stage i.
  - `enumerate_paths()` uses a Cartesian product.
- **`ProjectSpec`:**
  - `model_view()` is the ONLY project data rendered to models. `notes`, canonical paths and the ground-truth path are hidden.
  - `model_input_files()` is the ONLY set of files mounted for the cleaning stage.
- **Model outputs:** `CleaningOutput`, `AnalysisOutput`, `ReportOutput`. `KeyFinding` has `reported_values`, `direction`, `ranking` and `derived_values`.
- **`HandoffPackage`:** one policy for same-model and cross-model steps. Its `validation_status` may only be passed, failed, not_run or blocked_by_invalid_artifact.
- **`StageRunRecord` / `WorkflowRunRecord`:**
  - `feasibility.outcome` is feasible, infeasible or void_infra. A run is feasible only if every stage passed.
  - `quality` is measured against ground truth; `conditional_quality` against the reference recomputed from the actual upstream artifact.
  - `efficiency` keeps end-to-end time separate from API latency. Cost is `None` while prices are unverified.
  - `propagation`, a `PropagationSummary`, is required under `continue_with_actual_artifact`.
- **`StageBenchmarkRecord`:** an Experiment A result on canonical inputs.
- **Routing:**
  - `DecisionTrace` rejects evidence from the held-out project and checks `training_data_hash`.
  - `CounterfactualPrediction` is frozen and hashed, and must be built with `.create()`.
  - `CounterfactualValidation.check_against()` verifies the prediction hash.
  - `FaithfulnessCheck` is kept separate from empirical validation.

## 5. Commands

**Install.** This environment was built with these exact commands:
```bash
python3 -m venv .venv
.venv/bin/pip install "boto3>=1.42" "pydantic>=2.7" "pyyaml>=6" "pandas>=2.2" "numpy>=1.26" "pytest>=8"
```
The tested versions are boto3 1.44.5, pydantic 2.14.3, pandas 3.1.1, numpy 2.5.5 and pytest 9.2.0, on Python 3.12. `pip install -e ".[dev]"` should also work from `pyproject.toml` **[UNTESTED]**.

**AWS:** credentials come from the `xai-bedrock` profile in `~/.aws`. Never put keys in the repo. No AWS CLI is needed.

**Tests:**
```bash
.venv/bin/python -m pytest -q                                  # full offline suite: 303 passed, 8 paid-live skipped
.venv/bin/python -m pytest -q tests/test_executor.py           # sandbox + image lease: 20 passed
.venv/bin/python -m pytest -q tests/test_integration_e2e.py    # real-sandbox 3-stage workflow (Docker): 2 passed
.venv/bin/python -m datasets.generate --check                  # datasets byte-reproducible
.venv/bin/python -m experiments.rescore_reporting_v3           # offline only; no model client imported
```

**Sandbox:**
```bash
docker build -t model-routing-xai-sandbox:1.0 sandbox/         # only if the image is missing
docker image inspect --format '{{.Id}}' model-routing-xai-sandbox:1.0   # must equal results/verification/sandbox_verification.json
```
A rebuild, or a build on another machine, gives a different image ID. The `SandboxGate` then refuses to run model code. To re-verify:
1. Run `tests/test_executor.py`.
2. If 20/20 pass, write a new current record under `results/verification/`; never overwrite the
   historical raw verification record.

Never set `all_controls_verified: true` without a passing run.

**Executing a workflow.** `--plan` is the default and makes no AWS calls. PAID execution needs user approval:
```bash
.venv/bin/python -m experiments.run_workflow_grid --projects retail_sales --stages 3 --plan    # 81 calls planned
.venv/bin/python -m experiments.run_stage_benchmark --projects retail_sales --plan             # Experiment A
# PAID, only after explicit user approval; limits are mandatory:
.venv/bin/python -m experiments.run_workflow_grid --projects retail_sales --stages 3 --execute \
    --max-calls <N> --max-input-tokens <N> --max-output-tokens <N>
```
- Outputs go to:
  - `results/raw/workflow_runs/<experiment_id>.jsonl`
  - `results/raw/stage_benchmark/<experiment_id>.jsonl`
  - `results/raw/runs/<run_id>/<stage>/`, which holds the prompt, response, code, outputs and validation.
- Completed runs are skipped on resume.

**Routing evaluation** (offline). It has been run on synthetic fixtures only; on real records it is **[UNTESTED]**:
```bash
.venv/bin/python -m experiments.evaluate_routing --records results/raw --out results/routing/<run> --phase all
```

## 6. Current blockers and known bugs or limitations

**Blockers**
1. **Methodology decision: frozen v2 or prospective v3.** The audit is complete, but only the user
   can choose whether to finish v2 as the primary experiment or authorize a separately named v3
   experiment. Saved-output v3 rescoring is post-hoc and is not a substitute for prospective v3 data.
2. **Five retained `void_infra` paths need paid calls if frozen v2 is completed.** The Docker repair
   is tested, but the all-five retry is unapproved. C-B-B would duplicate one previously paid call.
3. **Prices remain unverified.** Dollar cost cannot be responsibly estimated; only call and token
   limits are available. Missing cost is never treated as zero.

**Known limitations** (no known failing tests):
- **Workflow pipeline:**
  - `run_workflow_grid` has no `--failure-policy` flag. It always uses `continue_with_actual_artifact`, the approved primary policy.
  - Execution is sequential; the concurrency helper exists in `src/bedrock/concurrency.py` but is not wired into the runners.
  - `cleaning_summary.json` is requested from models but not validated.
- **Prompts and test fakes:**
  - Experiment A handoffs describe canonical inputs as "Canonical reference …", so Experiment A prompts differ slightly in wording from Experiment B. Under rule 5 this has to be documented in the methodology.
  - The test fake (`tests/fixtures/workflow/fakes.py`) injects bugs through a header that only `FixtureExecutor` honours. `tests/test_integration_e2e.py` works around this for the real sandbox.
- **Routing and XAI:**
  - The "what would change the decision" search varies single thresholds only.
  - The counterfactual log's last-line-plus-anchor removal is undetectable without an external anchor; committing the log to git provides one.
  - Contract gaps, intended for v1.3: feasibility agreement is stored in `CounterfactualValidation.direction_correct` under `feasibility_agreement:*`, and the router replay settings in `DecisionTrace.explanation_components.router_settings`.
- **Pricing and accounting:**
  - Prices are unverified for all three models, so the dollar guard is inactive and only call and token limits apply.
  - About 30 tiny probe calls made during model selection, before the ledger existed, are not in the ledger.

## 7. Remaining Work Report

| Module | Current state | Remaining work | Blocker / approval |
|---|---|---|---|
| M1 Bedrock/infrastructure | Client complete; Docker repair and exact-image lease tested | Verify image immediately before any paid run; no code work required | Paid runs require explicit approval; dollar prices unavailable |
| M2 benchmark | Frozen v2 preserved; additive v3 candidate and audit complete | User chooses v2 primary vs separately named prospective v3 | Methodological decision |
| M3 workflow | Complete offline; 303-test suite passes | Optional failure-policy flag/concurrency are not required for the study | None for sequential execution |
| M4 Experiment B | Retail 2-stage complete; retail 3-stage has 22 model outcomes + 5 retained voids | Under v2: retry all 5 once, then run 27 paths on each of 3 untouched projects | Paid approval; no selective retries |
| Experiment A | Runner tested; no real records | 3 models × 3 stages × 4 projects = 36 calls | Paid approval |
| M5 routing/XAI | Implementation complete on synthetic fixtures | Run LOPO routing, counterfactual logging/validation and faithfulness on complete real A/B records | Complete comparable real records |
| M6 analysis | Not started on real results | Produce tables/figures, uncertainty and limitation reporting | M5 plus complete A/B records |
| M7 final demo | Not started; `web/` absent | Build optional Next.js/Tailwind viewer over frozen processed outputs | Stable M6 artifact schema and complete real results |

### Remaining paid calls under the frozen-v2 completion path

Plan-only calculations made no AWS client and no model call:

| Work | Logical calls | Worst-case input tokens | Worst-case output tokens |
|---|---:|---:|---:|
| Retry all five retail `void_infra` paths once | 15 | 170,010 | 61,440 |
| Remaining Experiment B (includes those retries + 3 untouched projects) | 258 | 2,877,219 | 1,056,768 |
| Experiment A, all 4 projects | 36 | 402,807 | 147,456 |
| **Core remaining total before repeats** | **294** | **3,280,026** | **1,204,224** |

The 294-call total assumes frozen v2 remains primary. It excludes live tests, the not-yet-defined
repeat subset and any prospective v3 experiment. A full prospective v3 design would require a new
plan and separate approval; do not mix its calls or scores with v2. Structurally, a fresh four-project
v3 core would contain 324 Experiment B calls plus 36 Experiment A calls = **360 logical calls before
repeats**, but its prompt-specific token caps have not been calculated and it is not approval-ready.
API-attempt caps must also allow the predefined transport retry policy, but orchestration never
selectively re-prompts a failed model output.

### Recommended next sequence

1. User chooses frozen-v2 completion or a separately named prospective v3 design.
2. Present that design's exact command, logical calls, token caps and cost status for separate
   approval. Do not run Bedrock before approval.
3. Run only the approved phase; inspect and reconcile records before the next paid phase.
4. After complete comparable A/B data, run M5 and M6 offline.
5. Freeze the processed schema and build M7. The final demo is blocked today by the methodology
   decision, incomplete real records, absent real M5/M6 outputs and the unbuilt frontend.

## 8. Expected outputs and acceptance criteria

### 8.1 T1, benchmark revision v2
- **Reporting validator** (`src/evaluation/reporting.py`):
  - **Critical factual contradictions are hard failures:** a wrong reported value; a required metric key missing from `reported_values`; a number under the wrong key or group; a wrong `direction`; a wrong `ranking`.
  - **Correct derived values are accepted:** `derived_values` that recompute correctly from verified findings (difference, ratio, pct_change, share) within tolerance, and counts from the cleaning log.
  - **Minor unsupported commentary** is the quality metric `unsupported_claim_count`, with a pre-set threshold. It is not an automatic failure.
  - Numbers are matched per finding, against that finding's own keys first.
  - "e.g." example values are removed from the question texts.
  - `direction_key` and `ranking_labels` are filled in for the relevant questions.
- **Datasets** (`datasets/`):
  - 1–2 derived-step questions per project.
  - Duplicates whose copies differ in value, so the dedup order matters.
  - Questions that use the currently unread columns (retail `customer_id`, energy `meter_id`/`tariff`, churn `lifetime_value`).
  - A **4th, structurally different project**, for example a two-file join, with `ProjectSpec.input_files` listing every model-readable file.
  - `notes` stays hidden.
- **Minor fixes:** strip a BOM from the cleaned CSV header; compare money in integer cents (or `abs_tol` 0.011).
- **Acceptance:**
  - Regression tests reproduce **every** false accept and false reject listed in the validity review and now pass.
  - Reference solutions pass, and deliberately broken solutions fail for the right reason.
  - `datasets.generate --check` passes.
  - The full suite passes, and `tests/test_integration_e2e.py` passes with Docker.
  - The changes are logged as pre-experiment design changes in `docs/EXPERIMENT_PROTOCOL.md`.

### 8.2 Pilot
Every run is recorded, including infeasible and void_infra runs.

| Acceptance check | Where |
|---|---|
| Records validate against contracts v1.2 | — |
| Fresh calls only (no cache hits) | `expB_paths` |
| Ledger counts match the invocation log | — |
| Executions ran in the verified image | `sandbox_image` equals `image_id` |
| Costs recorded as `unavailable`, not 0 | — |

## 9. Unresolved user approvals
1. **Methodology:** finish frozen v2, or run a separately named prospective v3 experiment.
2. **Any paid execution:** approve its exact calls, token caps and cost status after the methodology
   decision. The existing five-path retry is not approved.
3. **Rerunning live tests:** separate approval; archive or rename
   `results/raw/live_test_ledger.json` first.
4. **Pricing:** do not request IAM changes. Prices may be filled in by hand only from a supplied or
   independently verified official us-east-1 source and date.

## 10. Git state at handover
- **Branch:** `main`. Nothing was ever pushed, and no remote is configured.
- **Working tree:** expected clean at the offline-repair handoff commit. Frozen tag
  `benchmark-v2-frozen` remains on `411fcd7`; no remote is configured and nothing is pushed.
- **Agent branches:** `worktree-agent-a18433eab8d8b83af` (Infra), `worktree-agent-a6de0118e6abf459e` (Benchmark), `worktree-agent-a6c73b80981a3bdf7` (Workflow) and `worktree-agent-a36ac69bb2a5798c9` (XAI). All are **fully merged into main**, with no uncommitted changes.
- **Worktrees:** the agent worktrees under `.claude/worktrees/` are git-ignored. They can be removed with `git worktree remove <path>` once no longer needed; nothing in them is unmerged.
- **Credential scan:** no credentials, account IDs or key files in tracked files. `.env` and `results/cache/` are git-ignored.

---

## Instructions for the Next Coding Agent

You are continuing an existing, tested research codebase. **Do not restart or re-scaffold it.**

**The single most important next task:** read the post-freeze audit and get an explicit user choice
between frozen-v2 completion and a separately named prospective v3 design. Do not count voids as
model failures, rerun completed paths, pool v2/v3 scores or execute a paid call without a separate
approval containing calls, token caps and cost status.

**Read first, in this order:**
1. `docs/EXPERIMENT_PROTOCOL.md`
2. `docs/reviews/2026-11-18_post_freeze_v3_audit.md`
3. `docs/reviews/2026-11-17_retail_sales_pilot_3stage.md`
4. `src/evaluation/reporting.py` and `src/evaluation/reporting_v3.py`
5. `src/workflow/executor.py` and `src/workflow/stages.py`
6. `docs/PILOT_PLAN.md`

**Reproduce the current state:**
```bash
cd ~/Desktop/model-routing-xai
git log -1 --oneline                                 # latest pilot-planning/handover documentation commit
.venv/bin/python -m pytest -q                        # expect 303 passed, 8 paid-live skipped
.venv/bin/python -m datasets.generate --check        # expect all projects byte-reproducible
.venv/bin/python -m experiments.rescore_reporting_v3 # expect v2 0/10, v3 secondary 7/10
```

**Tests that must keep passing:**
- The full suite, including `tests/test_contracts.py`, `tests/test_workflow.py`, `tests/test_routing.py`, `tests/test_xai.py`, `tests/test_executor.py` and `tests/test_integration_e2e.py`.
- T1 artifacts are already regenerated. Future benchmark changes must remain generator-first and be documented as post-freeze changes if they occur after the freeze.

**Do not modify:**
- `src/contracts/`. If a change is truly needed: bump `CONTRACT_VERSION`, log it in `docs/architecture.md`, and get user approval for anything methodological.
- `results/raw/*`: append-only historical records, logs, ledgers and the historical sandbox verification.
- `sandbox/Dockerfile` and `src/workflow/executor.py` isolation flags. Any change invalidates the sandbox verification.
- `prompts/v1/*` or `prompts/v2/*`. Any future prompt change gets another explicit version and a
  separate experiment identity; v3 is currently a candidate, not active.
- `docs/reviews/*`: historical records. Add new files instead.
- Generated files in `datasets/projects/*`. Change the generator, then regenerate.

**Research rules that must not change:**
1. Never fabricate model performance or results. Synthetic fixtures stay labelled `SYNTHETIC_FIXTURE` and never go into `results/`.
2. Never replace failed or imperfect upstream outputs with canonical or ground-truth data in Experiment B. Use `continue_with_actual_artifact`, and mark unusable artifacts `blocked_by_invalid_artifact`.
3. Never use held-out project outcomes in prospective routing (LOPO). Predictions are logged before validation and never revised.
4. Never call interaction effects pure handoff or model-switching cost.
5. Identical prompts, inference settings and retry policy for every model and path. Document any difference.
6. Model-generated code runs only in the verified sandbox, through `SandboxGate`.
7. Never expose AWS credentials, ground truth, `notes` or validator details to models or to the repo.
8. Lower API latency does not mean lower end-to-end time; keep the two separate.
9. The oracle (S4) is retrospective only, never deployable.
10. Three models do not establish universal rankings. With 3–5 projects the results are exploratory, so make no significance claims.
11. Keep every failed or void run. Report uncertainty.
12. No weighted composite quality score. Use feasibility as a gate, report quality metrics separately, and apply efficiency preferences only among feasible paths.
13. Missing prices are never $0.
14. No paid AWS call, pilot or full run without explicit user approval and hard call and token limits.
15. Do not change the benchmark after inspecting full outcomes without documenting it as a post-hoc change.

**Tasks Codex can take independently** (no file overlap):

| Task | Exclusive files | Notes |
|---|---|---|
| Read-only preflight | plans, verification and current records | Recompute exact approval envelope; no AWS client, no writes to raw evidence |
| M5/M6 offline evaluation | `results/processed/`, routing/XAI scripts and analysis docs | Only after comparable real A/B records exist |
| M7 web scaffold | `web/` | May be scaffolded early, but publish no placeholder performance as real data |
| Grid runner `--failure-policy` flag/concurrency | runner and workflow tests | Optional; keep `continue_with_actual_artifact` as the primary default |
| Contracts v1.3 | `src/contracts/`, routing and explainability | Optional and methodological; requires version bump and documentation |

**Needs the user, not Codex:** the v2/v3 methodology choice, approving every paid phase, and
supplying or authorizing a verifiable pricing source.
