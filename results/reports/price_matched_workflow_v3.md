# Price-Matched Workflow v3 Replication

## Key findings

- Integrity audit: **PASS**. The analysis resolves 161 raw Part B records to 156 effective cells, replacing all 5 approved Docker voids while retaining their originals. Source: `results/processed/price_matched_workflow_v3_summary.json`, `integrity_audit`.
- In the 108-cell main grid, v3 marked **41/108** feasible and post-hoc v3.1 marked **53/108**. Under primary v3, single-model paths were **3/12** feasible and cross-model paths **38/96**. The observed direction differs from the original group's near-equality; it is descriptive, with unequal denominators, and is not a causal benefit claim. Source: the same JSON, `part_b`.
- Router explanations were computationally faithful: **451/451** claims and **20/20** replayed selections matched. Source: `results/routing/price_matched_workflow_v3_primary/computational_faithfulness.jsonl`.
- Feasibility direction matched **31/64** (48.4%), beside **22/50** (44.0%) for the original model group. This descriptively supports “faithful but not empirically valid” in the second group; it is not a causal or provider-wide claim. Source: `results/routing/price_matched_workflow_v3_primary/counterfactual_validations.jsonl` and `results/processed/v3_primary_analysis/counterfactual_validity.json`.
- Effective Part B spend was **$23.2235** across 156 runs; cost per feasible completion was $0.3807 under v3 and $0.3016 under v3.1. Source: the summary JSON, `costs.all_effective`.
- The post-hoc cost-aware variant changed **7/8** selectable traces (7/20 overall). Token-based cost direction matched **64/64**, compared with **56/64** for naive unit-price ordering. This descriptive post-hoc gap plausibly reflects token volume because Kimi K3 and Sonnet 4.6 share unit prices but used different token volumes; it is not a prospective or causal result. Source: `results/processed/price_matched_workflow_v3_cost_posthoc.json`.

## Scope and disclosures

This report concerns **these three specific models under this account**: Sonnet 4.6, Kimi K3, and GLM 5. It does not rank vendors. The replication used `maxTokens=16384`, whereas the original model group used 4096; Kimi omitted the unsupported temperature field while the other two models used temperature 0. Retail sales was pilot-exposed. Five Docker/sandbox voids were rerun once under standing authorization, outcome-blind and append-only. v3 is primary; v3.1 and the cost-aware Router are post-hoc secondary/exploratory views.

## Integrity audit

The audit linked 470 main invocations to records, and all 479 paid attempts reconciled to the ledger: 1,096,569 input tokens, 1,607,032 output tokens, $25.8875, zero failed attempts, and no pending reservations. Frozen protocol hashes, the immutable 156-line prefix, model IDs, `maxTokens=16384`, Kimi's omitted temperature, other-model temperature 0, prompt hashes, canonical data hashes, and pinned image `sha256:88988a15503bdb96538c3dd62244a79879d5c7848397db18b1267ccfd0a9727a` all passed. Source: the summary JSON, `integrity_audit`; raw evidence remains under `results/raw/price_matched_workflow/`, `results/raw/stage_benchmark/`, and `results/raw/workflow_runs/`.

### Docker rerun resolution

All five originals remain in the raw JSONL. Their five `rerun_of` records replace them only in the effective analysis: energy `C-C-A/B/C` reruns were infeasible; retail `A-A-A/A-A-B` reruns were feasible. There are 156 effective cells and no unresolved rerun void. Source: summary JSON, `integrity_audit.rerun_resolution`.

## Part A: single-stage benchmark

| Stage | Model | v3 passed | v3.1 reporting passed |
|---|---|---:|---:|
| cleaning | Sonnet 4.6 | 3/4 | n/a |
| cleaning | Kimi K3 | 4/4 | n/a |
| cleaning | GLM 5 | 4/4 | n/a |
| analysis | Sonnet 4.6 | 4/4 | n/a |
| analysis | Kimi K3 | 4/4 | n/a |
| analysis | GLM 5 | 0/4 | n/a |
| reporting | Sonnet 4.6 | 2/4 | 3/4 |
| reporting | Kimi K3 | 1/4 | 1/4 |
| reporting | GLM 5 | 4/4 | 4/4 |

v3.1 changes only the reporting validator and is never substituted for v3. Source: `results/raw/stage_benchmark/expA_price_matched_workflow_v3.jsonl` and `results/processed/v3_1_rescore/expA_price_matched_workflow_v3_reporting.json`.

## Part B: workflow outcomes

| View | n | v3 feasible | v3.1 feasible |
|---|---:|---:|---:|
| Main grid | 108 | 41 (38.0%) | 53 (49.1%) |
| Single-model main-grid paths | 12 | 3 (25.0%) | 4 (33.3%) |
| Cross-model main-grid paths | 96 | 38 (39.6%) | 49 (51.0%) |
| All saved effective runs | 156 | 61 | 77 |

First-failure counts in the 108-cell main grid were: `{'analysis': 21, 'cleaning': 11, 'none_feasible': 41, 'reporting': 35}`. Source: summary JSON, `part_b.first_failure_stage_main_grid`; full per-path schema-compatible tables are in `results/processed/price_matched_workflow_v3_analysis/path_summary.json`.

### Error propagation

Propagation is reported as conditional-reference quality minus ground-truth quality. It is descriptive and combines upstream error, formatting, and stochasticity; it is not a causal switching cost.

| Stage | Metric | n | Mean conditional − ground truth | Min | Max |
|---|---|---:|---:|---:|---:|
| analysis | calculation_coverage | 143 | 0.0000 | 0.0000 | 0.0000 |
| analysis | numerical_accuracy | 143 | 0.0443 | 0.0000 | 0.9048 |
| analysis | reproducibility | 116 | 0.0000 | 0.0000 | 0.0000 |
| reporting | finding_coverage | 123 | 0.0000 | 0.0000 | 0.0000 |
| reporting | numerical_consistency | 123 | 0.0890 | 0.0000 | 0.9524 |
| reporting | unsupported_claim_count | 123 | -2.4553 | -47.0000 | 4.0000 |

Source: summary JSON, `part_b.propagation_conditional_minus_ground_truth`; the schema-compatible decomposition is `results/processed/price_matched_workflow_v3_analysis/propagation.json`.

## Repeat variability

Across 24 project/path cells with three repeats, v3 outcomes were identical in 20/24 cells and v3.1 outcomes in 20/24. No significance claim is made. Source: summary JSON, `part_b.repeat_variability`; metric spreads are in `results/processed/price_matched_workflow_v3_analysis/variability.json`.

## Part C: routing replication

LOPO training used only the new records: every fold contains 27 Part A records and 117 effective Part B runs from the other three projects. Held-out evidence references: 0. The prediction and validation hash chains both verify. There were 20 S1–S3 traces and 64 prospective counterfactual predictions. Source: `results/routing/price_matched_workflow_v3_primary/predict_manifest.json`, `traces.jsonl`, and the summary JSON, `primary_routing`.

Computational faithfulness was 451/451 with 20/20 replay matches. Feasibility direction was 31/64 versus the original group's 22/50. Both rates are below 50%, while trace faithfulness is complete. Thus the qualitative statement **“faithful but not empirically valid” holds descriptively for this second model group**, with different denominators and no causal inference.

## Cost analysis

Across 156 effective Part B runs, spend was $23.2235 and mean attempted-run cost was $0.1489. Feasible completions were 61 under v3 and 77 under v3.1; the corresponding costs per feasible completion were $0.3807 and $0.3016. Failed non-void stages are included; blocked stages incur zero. Source: summary JSON, `costs`.

Per-run costs and every per-project/path feasibility denominator are in `costs.run_costs` and `costs.project_path_summaries`. The Pareto axes are mean executed cost per run (lower) and feasibility rate (higher); single-run cells are explicitly labelled.

| Project | v3 Pareto paths | v3.1 Pareto paths |
|---|---|---|
| customer_churn | C-A-C, C-C-B | C-A-C, C-C-B |
| energy_consumption | C-A-C, C-C-B, C-C-C | C-A-C, C-C-B, C-C-C |
| retail_sales | C-C-C | C-C-C |
| support_operations | C-A-C, C-B-A | C-A-C, C-B-A |

Source: summary JSON, `costs.pareto_frontiers`; each row there carries cost, feasibility, n, and the evidence label.

## Post-hoc cost-aware Router variant

This is **post-hoc / exploratory**. It reused the CP6 constraints and cost rules with verified prices for these three models. All 228/228 candidate costs were estimable; cost was active in 8/20 traces, while 12/20 had no feasible path. Cost changed 7/8 selectable traces. No Pareto set changed (0/20); all 7 changes occurred at the explicit cost-preference step.

Faithfulness was 444/444 with 20/20 replay matches. Cost direction matched 64/64; the naive unit-price ordering matched 56/64 on the same subset, and feasibility direction matched 41/64. The result depends on the all-non-void cost-scope rule: PASSED-only changed 7/20 selections relative to the primary cost-aware view. Source: `results/processed/price_matched_workflow_v3_cost_posthoc.json`, fields `coverage`, `selection_comparison`, `faithfulness`, `counterfactual_validity`, and `passed_only_sensitivity`; trace artifacts are in `results/routing/price_matched_workflow_v3_cost_posthoc/`.

## Limitations

- Four synthetic projects and many single-run project/path cells limit generalization.
- The model set was constrained by this account's access, and settings differ from the original group.
- v3.1, all dollar comparisons, and the cost-aware Router are post-hoc/exploratory.
- A faithful trace establishes computational consistency, not empirical correctness.
- Docker reruns removed infrastructure voids from effective cells but are disclosed and preserved raw.

## Reproduction and source paths

```bash
.venv/bin/python -m experiments.rescore_reporting_v3_1 --records results/raw/workflow_runs/expB_price_matched_workflow_v3.jsonl
.venv/bin/python -m experiments.run_price_matched_workflow --run-offline-routing
.venv/bin/python -m experiments.analyze_results --config configs/analysis_price_matched_workflow_v3.yaml
tmpdir="$(mktemp -d)"
.venv/bin/python -m experiments.analyze_price_matched_workflow_v3 --out "$tmpdir/summary.json" --report "$tmpdir/report.md" --cost-routing "$tmpdir/cost-routing" --cost-processed "$tmpdir/cost.json"
```

The first three commands reproduce the v3.1 labels, prospective routing, and schema-compatible v3 tables; those frozen-output commands require their documented fresh-output conditions. The last command uses a fresh temporary directory to reproduce the integrity, cost, and separate post-hoc cost-aware Router results without overwriting committed artifacts.
