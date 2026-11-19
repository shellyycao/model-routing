# Agent Status

Maintained by the lead under the `agent-status` protocol (`.claude/skills/agent-status/SKILL.md`).
An agent is marked IN_PROGRESS only while its run can be observed.

_Last sync: 2026-11-17 23:58 EST (prospective v3 adopted and frozen; paid v3 runs in progress; M6 agent running)._

> Agent runtime note: the project agent types in `.claude/agents/` only register when a session starts, so Wave 1 runs as general-purpose agents (engineers, each in its own git worktree) and the built-in Plan agent (reviewer, which has no edit or write tools), each told to follow its role file.

### Lead (Coordinator)
- Task / milestone: offline post-pilot repair, v3 reporting audit and handoff
- Status: COMPLETED OFFLINE; STOPPED BEFORE ANY NEW PAID CALL
- Branch / worktree: main (repo root)
- Last update: 2026-11-17 23:42 EST
- Files modified: additive validator/prompt v3, offline rescoring, Docker image lease, current verification record, tests and handoff/audit docs. Frozen v2 and all existing raw evidence were left unchanged.
- Tests/execution: full suite 303 passed, 8 paid-live skipped; executor 20/20 on rebuilt image; offline v3 rescore 10 reports (v2 0 pass, v3 secondary analysis 7 pass). No Bedrock calls.
- Current blocker: user must choose frozen-v2 completion versus a separately named prospective v3 design before paid work; prices remain unverified.
- Next action: obtain separate approval with calls/token caps, then execute only the selected design. Do not selectively retry failures.

### LLM Infrastructure Engineer
- Task / milestone: M1 completion
- Status: COMPLETED
- Branch / worktree: worktree-agent-a18433eab8d8b83af (.claude/worktrees/, from 54af241)
- Last update: 2026-11-17 19:41 EST merged into main (bdf5f3b)
- Files modified: src/bedrock/{client,usage,models,concurrency,provenance,discovery}.py, configs/models.yaml, scripts/discover_models.py, tests/test_bedrock_{client,concurrency,provenance,discovery,live}.py, results/raw/model_discovery_2026-11-18.json
- Tests executed: agent's worktree: 84 passed, 8 skipped (live). Lead on merged main: 99 passed, 8 skipped. Live tests not run (need approval: 7 planned calls, at most 10 attempts)
- Current blocker: none. Prices still unverified (null)
- Next action: none until Wave 2 needs it; the live test run awaits user approval

### Benchmark Engineer
- Task / milestone: M2: datasets, ground truth, validators, sandbox
- Status: COMPLETED
- Branch / worktree: worktree-agent-a6de0118e6abf459e (.claude/worktrees/, from 54af241)
- Last update: 2026-11-17 19:58 EST lead verified the sandbox in real Docker: 16/16 executor tests pass on image sha256:4bf3a80b…; the no_network assertion was corrected by the lead (see docs/reviews/2026-11-18_sandbox_verification.md)
- Files modified: datasets/ (3 projects: retail_sales, customer_churn, energy_consumption), src/evaluation/{cleaning,analysis,reporting}.py, src/workflow/executor.py, sandbox/Dockerfile, tests/test_eval_*.py, tests/test_executor.py, tests/fixtures/benchmark/
- Tests executed: agent's worktree: 106 passed, 11 skipped. Lead on merged main: 179 passed, 19 skipped; datasets.generate --check: all 3 projects byte-reproducible
- Current blocker: none
- Next action: T1 implementation is complete on main; independent re-review and freeze are next

### Research Reviewer (read-only)
- Task / milestone: Benchmark validity audit (difficulty, ambiguity, validator false accepts/rejects, ceiling effects, leakage)
- Status: COMPLETED
- Branch / worktree: n/a (read-only, main @ 54af241)
- Last update: 2026-11-17 21:11 EST final T1 re-review approved benchmark-v2 freeze
- Files modified: none; report stored by the lead in docs/reviews/2026-11-17_review_M1_contracts_v1.0.md
- Tests executed: none (read-only)
- Current blocker: none
- Next action: none until post-pilot audit

### Workflow Engineer
- Task / milestone: M3–M4: prompts, stages, handoff, orchestrator, Experiment A and B runners, resume, sandbox gate, pilot estimate (offline, with fakes)
- Status: COMPLETED (offline; no paid calls made)
- Branch / worktree: worktree-agent-a6c73b80981a3bdf7 (merged into main)
- Last update: 2026-11-17 20:14 EST merged
- Files modified: src/workflow/{stages,orchestrator,handoff}.py, src/storage/*, src/evaluation/workflow_metrics.py, prompts/v1/*.txt, experiments/run_{workflow_grid,stage_benchmark}.py, tests/test_workflow.py, tests/fixtures/workflow/fakes.py
- Tests executed: agent: 220 passed, 8 skipped. Lead on merged main: 253 passed, 8 skipped (incl. the new real-sandbox end-to-end test)
- Current blocker: none. Known gaps: no --failure-policy flag (continue policy always used); execution is sequential; cleaning_summary.json is not validated; the fake injects bugs through a header that only FixtureExecutor honours
- Next action: none; the pilot needs user approval

### XAI Researcher
- Task / milestone: M5: leakage-safe training view, S1–S4, router and selection steps, decision traces, template explanations, hash-chained counterfactual log, validation, faithfulness checks, methodology draft (offline, synthetic fixtures)
- Status: COMPLETED (offline; synthetic fixtures only, no results)
- Branch / worktree: worktree-agent-a36ac69bb2a5798c9 (merged into main)
- Last update: 2026-11-17 20:11 EST merged
- Files modified: src/routing/*, src/explainability/*, configs/routing.yaml, experiments/{evaluate_routing,validate_counterfactuals}.py, docs/methodology.md, tests/test_routing.py, tests/test_xai.py, tests/fixtures/xai/SYNTHETIC_FIXTURE_*
- Tests executed: agent's worktree: 225 passed, 8 skipped. Lead on merged main: 225 passed, 8 skipped
- Current blocker: none. Minor contract gaps (feasibility agreement is stored in direction_correct; router settings in explanation_components), queued for contracts v1.3
- Next action: run evaluate_routing on real Experiment A and B records once they exist

### Frontend Engineer
- Task / milestone: M7
- Status: NOT_STARTED
- Branch / worktree: n/a
- Last update: n/a
- Files modified: none
- Tests executed: none
- Current blocker: no complete, methodologically selected real-result set; M5 real routing/XAI and M6 figures do not exist
- Next action: after the v2/v3 decision and approved experiments, generate M5/M6 processed artifacts, then build the optional demo in `web/`

## Pending integrations at handover
- None. All four agent branches are merged into main, and their worktrees have no uncommitted changes.
- Not started / awaiting decision:
  - predefined all-five retry of the three-stage `void_infra` paths (needs separate approval);
  - Experiment A and the remaining three-project Experiment B runs (needs separate approval);
  - real-data M5 routing/XAI evaluation;
  - M6 figures and tables;
  - M7 demo.

## Session resumed (2026-11-17 23:58 EST): Claude Code lead
- **Decision:** the user chose prospective v3 as primary; v2 is kept as a pilot.
  - Protocol switch committed: `--protocol v3`, experiment IDs ending `_v3`.
  - v3 frozen at `22a56e6`, tag `benchmark-v3-frozen`.
- **Sandbox:** the image was missing from Docker. It was rebuilt as `sha256:88988a15…` and re-verified 20/20. The previous record is kept in `results/verification/history/`.
- **Tests:** full suite 305 passed, 8 skipped (paid live).
- **Paid runs** (user-approved v3 run, spending monitoring relaxed by the user):
  - **Status:** IN_PROGRESS in the background. Experiment A `expA_stage_v3` runs first (36 calls), then Experiment B `expB_paths_v3` (4 projects × 27 paths, 324 calls).
  - **Log:** `results/logs/v3_run_main.log`.
  - **Earlier launch:** a first attempt failed at argument parsing, before any model call, because of shell quoting. Its log is kept.
- **M6 analysis pipeline:** IN_PROGRESS. XAI Researcher agent (offline) in its own worktree, branch assigned by the harness. It owns `src/analysis/`, `experiments/analyze_results.py`, `docs/analysis_schema.md` and `tests/test_analysis*`.
- 2026-11-18 00:05 EST: the M6 analysis pipeline was merged (branch worktree-agent-ae56890eb1e0bdd0c). Non-Docker suite: 297 passed. `docs/analysis_schema.md` committed by the lead, and matplotlib added to the dependencies. Docker tests were not run during the live experiment, to avoid container contention.

## Overnight plan (2026-11-18 01:16 EST): lead only, no new agents
- **Phase 1 (Part A) report:** committed.
- **Post-hoc reporting validator v3.1:** committed, together with the Experiment A rescore.
- **Experiment B v3 (`expB_paths_v3`):** IN_PROGRESS, 68/108 at 01:16. Not touched.
- **Overnight chain** (`scripts/overnight_v3_chain.sh`, log `results/logs/v3_overnight_chain.log`): QUEUED. It waits for the Experiment B process to exit, then:
  - retries `void_infra` runs once;
  - runs the pre-registered repeats: A-A-A B-B-B C-C-C A-C-A A-A-C A-C-C, repeat_index 1-2, all 4 projects (48 runs, 144 calls).
- **`docs/INDEPENDENT_BENCHMARK_PLAN.md` (A1-A3):** written. **AT THE APPROVAL GATE**; not implemented, not run.
- **Next, once the runs finish:** reconcile records against logs; v3.1 rescore of Experiment B; M5 routing/XAI; M6 analysis; tests; HANDOFF update; overnight report.

## Overnight results (2026-11-18 ~02:20): lead only, no agents
- **Paid runs:** COMPLETED. Experiment B v3 108/108, then the pre-registered repeats 48/48. The chain found no void runs to retry.
- **Reconciliation:** passed (`results/processed/reconciliation.json`).
- **Post-hoc v3.1 rescore of Experiment B:** COMPLETED. 11 reports flipped, all on the churn q7 pattern.
- **M5 on real v3:** COMPLETED. M6 on real v3: COMPLETED (all tables complete).
- **Reports:** `results/reports/phase2_3_workflow_and_xai.md` added; the Phase 1 report is unchanged apart from the v3.1 section.
- **Tests:** full suite 324 passed, 8 skipped (live).
- **Commits:** `a0ccbb6` (raw v3 results), `5085cfa` (analysis and reports).
- **A1–A3 independent benchmarks:** AT THE APPROVAL GATE. Plan only; nothing implemented or run.
- **Website:** not started (by instruction).

## A1–A3 extension (2026-11-18): lead only
- **Status:** COMPLETED. Implemented, frozen (`independent-v1-frozen`, `45a1d74`), then run with 90 calls, 0 void, 98.7K input and 73.7K output tokens. Results commit `f1f50d3`.
- **Tests:** 342 passed, 8 skipped (live).
- **Findings needing care:**
  - A1 shows a ceiling effect.
  - A2 gpt-oss: 7 failures from the missing schema wrapper; the content was perfect.
  - A3: the frozen grounding scorer's paraphrase artifact is corrected post hoc as v1.1; gpt-oss was truncated in 4 of 10.
- **Transient Docker issue:** a transient tag-resolution failure in Docker's image store was observed before the run. It is handled by the gate and void_infra; no runs were affected.
