# Manager Checkpoints (Codex executes, Claude reviews)

**Roles:**
- **Codex** does the work.
- **Claude** acts as a lightweight manager. It reviews only at the checkpoints below, does not do the
  work, and does not re-derive every number.
- **The user** approves anything that costs money or changes scope.

**Why:** a Claude model and an OpenAI model are both under evaluation. Neither agent is neutral, so
each one's work gets checked by the other.

## Protocol

1. Claude sends instructions to Codex directly, by resuming the Codex thread through the Codex CLI.
   The user does not relay messages.
2. When Codex reaches a checkpoint, it **stops** (ends its turn) and writes
   `docs/reviews/codex_cp<N>_<short-name>.md`, half a page at most, covering:
   - what was done, with commit hashes;
   - any deviation from the plan or rules;
   - open questions.
3. Claude writes `docs/reviews/<date>_cp<N>_review.md` with a verdict, then sends Codex the next
   instruction:
   - **PASS:** continue.
   - **PASS WITH NOTES:** continue, and fix the notes in the next step.
   - **HOLD:** stop and fix before continuing.
4. Claude escalates to the user only for decisions that are the user's: spending money, changing
   scope, or the user decisions listed at CP3. Codex never passes a stop checkpoint without a PASS,
   and paid calls also need the user's explicit approval.

## Checkpoints

| CP | When | What Claude checks (and only this) |
|---|---|---|
| CP1 | Post-hoc rules committed | Rules are model-agnostic and committed before results exist. **Done:** `2026-11-18_posthoc_rules_checkpoint1_review.md`, PASS WITH NOTES (R-1 A3 attribute-vocabulary disclosure, R-2 Wilcoxon amendment). |
| CP2 | Post-hoc draft report ready | R-1 and R-2 handled. Frozen and post-hoc views side by side. 3–5 headline numbers spot-checked against the JSON. No overclaiming wording, with Claude-favourable wording checked first. Tests pass. |
| CP3 | Tier-matched protocol ready to freeze (**stop**) | Models chosen by the rule from official prices, with no hand-picks. Bands fixed before prices were read. Scorer v2.2 frozen first. Worst-case budget computed. Decision recorded on the A3 attribute vocabulary. User decisions listed. |
| CP4 | After the paid run | Integrity audit passed. Call count, cost and ledger match the plan. No selective retries. No post-run changes to the frozen protocol. |
| CP4b | Workflow cost analysis (`docs/POSTHOC_WORKFLOW_COST_BRIEF.md`), after CP4 | Rules committed before computation. Failed attempts are counted in cost. Feasibility denominators are shown. Post-hoc label. Frozen Router unchanged. |
| CP6a/b | Cost-aware Router variant (`docs/COST_AWARE_ROUTER_BRIEF.md`), user-approved 2026-11-19 | Rules committed before computation. Frozen Router untouched. Separate output directory and new counterfactual log. Faithfulness intact. Post-hoc label everywhere. Comparison against the naive baseline. No "better router" claim. |
| CP5 | Final research write-up | Pre-registered, post-hoc and limitation sections separated. Model-selection fairness disclosed. Claims match the evidence level. Nothing framed as a vendor ranking. |
