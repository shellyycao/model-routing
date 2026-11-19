---
name: agent-status
description: Update docs/AGENT_STATUS.md for model-routing-xai whenever a project agent starts, finishes, becomes blocked, or hands off work, and produce the integration-cycle summary for the user.
---

# Agent status protocol

`docs/AGENT_STATUS.md` is the persistent record of every project agent. The lead updates it at these checkpoints:
- an agent is launched
- an agent's hand-off report arrives
- a blocker is found
- work is merged
- a review completes

## Rules
- **Allowed statuses:** `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `IN_REVIEW`, `COMPLETED`, `FAILED`.
- Mark an agent `IN_PROGRESS` only when its run is observably running, meaning it was launched and no completion notice has arrived. Never infer progress.
- Mark it `COMPLETED` only after the lead has run the tests on the merged result. An agent's own report is not proof.
- Record the exact test command and the pass/fail counts.
- Use absolute dates and times (UTC or local with zone).

## Per-agent block (keep all fields)
```
### <Agent name>
- Task / milestone:
- Status:
- Branch / worktree:
- Last update:
- Files modified:
- Tests executed:
- Current blocker:
- Next action:
```

## Integration-cycle summary for the user
After each integration cycle, report:
- completed tasks
- active tasks
- blockers
- tests and evidence
- estimated experiment usage and cost: calls and tokens from `results/raw/cost_ledger.json`, with dollars only where prices are verified
- decisions that need the user's approval
