# Codex CP7b — compatibility-pilot freeze

## User decision

Recorded the user's exact decision, **“16384, $100 cap”**, dated 2026-11-19. All three models use
`maxTokens=16384` for Parts A/B, and the compatibility pilot plus any later separately approved
main run share one reserve-then-settle $100 ledger. The plan explicitly discloses that the original
Parts A/B used 4,096 tokens, so comparisons are not parameter-identical. The 9-call structural
pilot is approved; the main run remains unapproved.

## Freeze and runner changes

Generated `results/processed/price_matched_workflow_protocol_manifest.json` with status
`pilot_frozen_paid_execution_approved`, the fixed stage-major A/B/C order, effective parameter and
usage fields, protocol hashes, and required tag `price-matched-workflow-pilot-v1`. The gate accepts
the pilot only at that exact tagged commit and independently refuses main execution because
`main_approved=false`. Pilot parameter incompatibility stops that model's remaining slots without
parameter mutation; quality is not inspected. A second mandatory main-run checkpoint now stops
after the 27-path grid, projects repeat spend against $100, and requires an unchanged ledger plus
both resume flags before repeats.

## Verification and execution handoff

The full offline suite passed: **517 passed, 23 skipped**. No model or network calls were made and
no tag was created in this sandbox. After committing, Claude should create the tag:

```bash
git tag price-matched-workflow-pilot-v1
```

The exact approved pilot command is:

```bash
.venv/bin/python -m experiments.run_price_matched_workflow --execute-approved-pilot
```

There is deliberately no approved main command at this checkpoint; a new user approval, main
manifest status, and distinct `price-matched-workflow-main-v1` tag are required first.
