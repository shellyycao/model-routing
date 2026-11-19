# Price-Matched Workflow + Routing Replication — Brief

**Status:** user-approved to prepare in the background on 2026-11-19. No paid call is authorized by this
brief. The compatibility pilot and the main run each need explicit user approval of the budget.

## Goal
Replicate Parts A, B and C (stage benchmark, 27-path workflow grid, LOPO routing with traces,
explanations and counterfactuals) with the price-matched trio:
- Sonnet 4.6, `us.anthropic.claude-sonnet-4-6`
- Kimi K3, `us.moonshotai.kimi-k3`, with no temperature field
- GLM 5, `zai.glm-5`

**Main research question:** does "computationally faithful but empirically weak on feasibility" hold
for a second, independent model set?

**Secondary aim:** give Kimi and GLM end-to-end workflow evidence, for Evidence Matching in the product.

## Fixed from the original protocol (benchmark-v3)
- The same 4 projects and datasets.
- `prompts/v3`.
- Validators: v3 primary, v3.1 secondary.
- The same handoff policy, sandbox image and LOPO folds.
- The same router config (`configs/routing.yaml`) and the same cost-aware post-hoc variant config.
- The same repeat design: 27 paths × 4 projects main, plus repeats 1–2 of the same 6 paths.
- **The router must be retrained from the new records only.** It must not mix in old-model records.

## Decisions to present to the user, not to make

1. **Output budget.** The original Parts A/B used maxTokens 4096. Kimi's A3 outputs had a median of
   about 7.7k billed tokens, most of it reasoning, so 4096 would likely truncate Kimi.
   - Option 1: 4096. Comparable with the original Parts A/B, but likely Kimi truncation, which would
     measure the budget rather than the model.
   - Option 2: 16384. Fair to reasoning models, but no longer the same setting as the original runs.

   Present both, with worst-case and realistic budgets and the comparability consequences.
2. **Total budget cap**, given Kimi's token volume.

## Deliverables (CP7a, stop before any paid call)
- A protocol document: `docs/PRICE_MATCHED_WORKFLOW_PLAN.md`.
- A plan-by-default runner, reusing the existing orchestrator and runners where possible.
- A compatibility pilot plan: workflow stages × 3 models on one project, a few calls, structural checks
  only.
- A worst-case and a realistic budget for each maxTokens option.
- Offline tests.
- A status file: `docs/reviews/codex_cp7a_workflow_plan.md`.

**Docker note:** Docker Desktop intermittently fails image lookups. The runner must classify those
failures as sandbox-unavailable or void_infra, never as a model failure.
