Poster charts. All PNG, 10 x 5.5 in, 300 dpi (3000x1650 px), white background.
Regenerate: python3 poster/charts/make_charts.py (reads the source files below directly; no model calls).
Group 1 = Sonnet 4.6 / Nova Pro / gpt-oss-120b (maxTokens 4096). Group 2 = Sonnet 4.6 / Kimi K3 / GLM 5 (maxTokens 16384).
The poster shows final (post-hoc corrected) values; the frozen values stay in docs/FINAL_REPORT.md beside them.

1. q1_stage_success.png  (Q1: who is good at what)
 Source: results/reports/corrected_view.md, Part A tables. Successes out of 4 projects for cleaning / analysis / reporting:
 Sonnet 4.6 3,4,3 | Nova Pro 0,0,2 | gpt-oss-120b 2,4,2 | Kimi K3 4,4,1 | GLM 5 4,4,4.
 GLM 5 analysis is drawn at its corrected value 4/4 (frozen 0/4; all four failures were int64 serialization only).

2. q2_single_vs_mixed_final_only.png  (Q2: does mixing beat one model)
 Source: results/processed/corrected_q2.json, model_groups.<group>.{single_model_main_grid,cross_model_main_grid}.corrected_v3.
 Group 1: single 2/12 (17%), mixed 23/96 (24%). Group 2: single 6/12 (50%), mixed 46/96 (48%).
 Frozen values (not plotted): Group 1 2/12 and 15/96; Group 2 3/12 and 38/96.

3. q3_router_vs_baselines.png  (Q3: can the router be trusted)
 Source: results/processed/router_relabel_posthoc.json, model_groups.<group>.validators.v3_primary.corrected.slices.pooled.methods.
 Group 1 (n=50): router 21 (42%), always "no change" 26 (52%), always "worse" 18 (36%), always "better" 6 (12%).
 Group 2 (n=64): router 24 (38%), always "no change" 36 (56%), always "worse" 25 (39%), always "better" 3 (5%).

4. cost_vs_success_two_groups.png  (Cost: which workflow is worth its cost)
 Source: results/processed/corrected_q2.json, model_groups.<group>.project_path_outcomes_main_grid
 (corrected_cost_usd averaged over the 4 projects; success = corrected_v3 "feasible", out of 4 projects, one run each).
 Group 1: gpt-oss -> gpt-oss -> Nova $0.010, 3/4 | Sonnet -> gpt-oss -> Nova $0.068, 3/4 | Sonnet only $0.145, 2/4.
 Group 2: GLM only $0.022, 4/4 | GLM -> Sonnet -> GLM $0.056, 4/4 | Sonnet only $0.144, 1/4.
 Selected rows: the cheapest and the next workflow with the group's best success, plus Sonnet only for reference.
 Single-run evidence per project; GLM only is 1/4 under the frozen labels.
