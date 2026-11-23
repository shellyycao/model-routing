# Guide to `docs/`

This folder keeps the full research record, including working notes, so every decision can be audited.
Most readers only need the first section.

## Start here

| File | What it is |
|---|---|
| [FINAL_REPORT.md](FINAL_REPORT.md) | Full report: question, architecture, timeline, all results with sources, limitations, verification guide |
| [RESULTS_REPORT.md](RESULTS_REPORT.md) | Results write-up in Chinese (motivation, method, results, limits) |
| [research/COMPETITIVE_LANDSCAPE.md](research/COMPETITIVE_LANDSCAPE.md) | Related products and papers, and the gap this project addresses |
| [architecture.md](architecture.md) | System design and component ownership |
| [methodology.md](methodology.md) | Routing and XAI method: leave-one-project-out, decision traces, counterfactual validation (written before results) |

## Frozen protocols (written before results; never edited)

| File | Covers |
|---|---|
| [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md) | Main workflow experiment (Group 1) |
| [PRICE_MATCHED_WORKFLOW_PLAN.md](PRICE_MATCHED_WORKFLOW_PLAN.md) | Replication with Group 2 (price-matched models) |
| [CONTINUATION_PROTOCOL.md](CONTINUATION_PROTOCOL.md) | 40-cell continuation run |
| [INDEPENDENT_BENCHMARK_PLAN.md](INDEPENDENT_BENCHMARK_PLAN.md), [INDEPENDENT_V2_PLAN.md](INDEPENDENT_V2_PLAN.md), [PRICE_MATCHED_V2_PLAN.md](PRICE_MATCHED_V2_PLAN.md) | Independent task benchmark (debugging, extraction, literature ranking) |
| [HUMAN_REVIEW_PROTOCOL.md](HUMAN_REVIEW_PROTOCOL.md), [A3_V2_LABEL_REVIEW_PROTOCOL.md](A3_V2_LABEL_REVIEW_PROTOCOL.md), [A3_V2_LABEL_REREVIEW_PROTOCOL.md](A3_V2_LABEL_REREVIEW_PROTOCOL.md) | Label review procedures |
| [HASH_REPRODUCIBILITY_AMENDMENT.md](HASH_REPRODUCIBILITY_AMENDMENT.md) | Additive amendment so frozen dataset hashes verify on a fresh checkout |
| [analysis_schema.md](analysis_schema.md) | Schema of processed analysis files |

## Post-hoc analysis rules (committed before each analysis was run)

[CORRECTED_VIEW_RULES.md](CORRECTED_VIEW_RULES.md), [ROUTER_RELABEL_RULES.md](ROUTER_RELABEL_RULES.md),
[FAILURE_TAXONOMY_RULES.md](FAILURE_TAXONOMY_RULES.md), [POSTHOC_WORKFLOW_COST_RULES.md](POSTHOC_WORKFLOW_COST_RULES.md),
[COST_AWARE_ROUTER_RULES.md](COST_AWARE_ROUTER_RULES.md), [POSTHOC_V2_RULES.md](POSTHOC_V2_RULES.md).
Results from these are exploratory and are always shown next to the frozen results, never in place of them.

## Audits and reviews

- [BENCHMARK_AUDIT.md](BENCHMARK_AUDIT.md): audit of the first independent benchmark.
- [reviews/](reviews/): dated reviews from each checkpoint (validity, leakage, sandbox, scoring decisions).

## Process notes (AI-assisted development)

The project was built with AI coding agents under the author's direction. These files record how work was
assigned and checked: [MANAGER_CHECKPOINTS.md](MANAGER_CHECKPOINTS.md), [AGENT_STATUS.md](AGENT_STATUS.md),
[HANDOFF.md](HANDOFF.md), [CODEX_HANDOFF.md](CODEX_HANDOFF.md), and the `*_BRIEF.md` files.
[PILOT_PLAN.md](PILOT_PLAN.md) is the early pilot, [TIER_MATCHED_PLAN_DRAFT.md](TIER_MATCHED_PLAN_DRAFT.md) is a
superseded draft, and [M7_STATUS.md](M7_STATUS.md) / [M7_WEBSITE_HANDOFF.md](M7_WEBSITE_HANDOFF.md) cover the demo
website. `design/` holds a website design mock-up.
