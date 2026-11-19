# Post-hoc Workflow Cost Analysis — Brief (queued; starts after CP4)

**Status:** queued. User-approved idea, 2026-11-18. Codex executes it; Claude reviews.
**Scope:** offline only, over the saved Part B (Experiment B, v3) and Part C records. No model calls.
The frozen Router, traces, predictions and validations are not modified.

## Question
Each workflow path is a model combination for cleaning → analysis → reporting. What does each path
*actually* cost, and which paths are on the quality–cost Pareto frontier?

At the time of the run, cost was inactive in the Router because prices were unverified. They are now
verified in `configs/models.yaml` (retrieved 2026-11-18).

## Rules (commit as `docs/POSTHOC_WORKFLOW_COST_RULES.md` before computing anything)
1. **Cost per run:** the recorded input and output tokens of every stage call that was actually made,
   including failed and blocked attempts and retries, × the verified prices. Missing usage is never
   treated as zero; report it.
2. **Per path, report:**
   - mean cost per run;
   - feasibility rate;
   - **cost per feasible completion** = total spend on that path ÷ number of feasible runs. Mark it
     undefined when there are no feasible runs.
3. **Pareto frontier per project:** cost (lower is better) against feasibility (higher is better).
   Also report a pooled view, labelled as such.
4. **Router sensitivity:** add a "cost first" preference view, alongside the existing
   `router_sensitivity_posthoc` views, using only the candidate estimates in the 20 frozen traces.
5. **Cost counterfactual validity:** where traces imply token or cost differences between the selected
   path and an alternative, convert them with the verified prices. Check whether the direction matches
   the executed outcome.
   **The frozen Router never predicted dollars.** Label this check as a *post-hoc conversion of the
   Router's token predictions* (token-based cost estimate). Report it separately from executed cost,
   meaning recorded tokens × price. It must never be presented as a prospective cost prediction by the
   original Router.
6. **Uncertainty:** most paths have one run, and 6 of 24 repeated cells flipped. Report n per path. Make
   no "cheapest model combination" claim without the feasibility denominator.
   - Tag every path with n = 1 as `single-run evidence`.
   - For paths with zero feasible runs, cost per feasible completion is `not estimable`, never $0 and
     never blank-as-zero.

## Deliverables
- The rules file, committed first.
- `experiments/analyze_workflow_cost_posthoc.py`.
- `results/processed/workflow_cost_posthoc.json`.
- `results/reports/workflow_cost_posthoc.md`, labelled post-hoc / exploratory.
- Tests.

## Checkpoints
- Claude reviews the rules before computation.
- Claude reviews the draft report.
- The results feed into CP5, the final write-up.
