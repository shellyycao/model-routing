# Codex CP7c — main-run freeze

## Pilot outcome and user approval

The compatibility pilot completed **9/9 API calls**, with 9/9 parsed responses, 9/9
`stopReason=end_turn`, no parameter failures, and no automatic parameter changes. Its shared ledger
contains 9 attempts and **$0.449949**. The pilot task records and summary are now included in the
protocol hashes. On 2026-11-19 the user approved the main run with the exact words: **“Approve the
main run (504 calls, about $43 expected, $100 cap)”**.

## Main freeze and resume safety

Generated `results/processed/price_matched_workflow_protocol_manifest.json` with status
`main_frozen_paid_execution_approved` and required tag `price-matched-workflow-main-v1`. It freezes
the 504-call ceiling, `maxTokens=16384`, the pilot-plus-main $100 reserve-then-settle cap, and Kimi's
temperature-field omission. The current realistic projection is $42.440640 including actual pilot
spend; the pre-pilot combined estimate remains $42.817214 and the static worst case $572.437048.

Resume bookkeeping reads only the exact Part A and Part B task files. A regression test places an
`invocations.jsonl` and a pilot JSONL beside them and confirms neither contributes a completed
run ID. The mandatory Part A and main-grid stops remain in force; repeats require an unchanged
within-cap main-grid checkpoint.

## Verification and execution handoff

The full offline suite passed: **518 passed, 23 skipped**. No model or network call was made. After
committing all frozen files, Claude should create `price-matched-workflow-main-v1`. The two pilot
task-store files `expA_price_matched_workflow_pilot_v3.jsonl` and `.meta.json` are currently
untracked even though the other pilot evidence is in commit `90abc9d`; they must be added to this
commit because the main manifest hashes them. Execution is:

```bash
# Part A, then stop
.venv/bin/python -m experiments.run_price_matched_workflow --execute-approved-main

# Main grid, then stop before repeats
.venv/bin/python -m experiments.run_price_matched_workflow --execute-approved-main --continue-after-part-a

# Resume repeats after checkpoint review
.venv/bin/python -m experiments.run_price_matched_workflow --execute-approved-main --continue-after-part-a --continue-after-main-grid
```

Progress sources are
`results/raw/stage_benchmark/expA_price_matched_workflow_v3.jsonl` (**36 lines**, group by
`project_id`/`stage`/`model_alias`) and
`results/raw/workflow_runs/expB_price_matched_workflow_v3.jsonl` (**156 lines**, group by
`project_id`/`path_id`/`repeat_index`). In Part B, repeat index 0 is the 108-record main grid and
indices 1–2 are the 48 repeat records. The invocation log is supporting evidence, not a completion
source.
