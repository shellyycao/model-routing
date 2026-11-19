# Router relabel re-scoring

**POST-HOC / EXPLORATORY / RETROSPECTIVE.** Frozen predictions are re-scored against corrected executed outcomes. This is not prospective evidence; no router was retrained. Wilson 95% intervals and exact binomial p-values (vs 0.5) treat predictions as independent; they are clustered by project and strategy, so these intervals are optimistic. A 3-class sign match has no natural 0.5 chance level; compare with the baselines. Source: `results/processed/router_relabel_posthoc.json`.

## Plain statement of what the baselines show

- The trivial **always-tie** baseline (predict no feasibility change) is at least as accurate as the frozen router in 7 of the 8 group/validator/label cells, and beats it with corrected v3 labels: original 26/50 vs 21/50 and price-matched 36/64 vs 24/64. The detailed tables below give every baseline for every slice, including where **always-less** or the training-only **stage-rate** baseline equals or beats the router (for example price-matched frozen v3: always-less 32/64 and stage-rate 36/64 vs router 31/64).
- The router exceeds **always-more** by a wide margin; its margin over the other baselines is small or negative in the cells shown.
- Corrected labels depend on the 40 paid continuation calls and on the 11 cleaning recoveries, whose downstream stages saw a `failed` upstream label; they are a sensitivity, not a reconstruction.
- Nothing here shows the router repaired, validated or deployable. Corrected labels lowered its accuracy in every group and validator shown; this is a retrospective re-scoring only.

## Reproduction gate

- original_4096: 50/50 validations reproduced exactly; pooled 22/50 (expected 22/50).
- price_matched_16384: 64/64 validations reproduced exactly; pooled 31/64 (expected 31/64).

## Group original_4096 (alias meaning: `A` = Sonnet 4.6, `B` = Nova Pro, `C` = gpt-oss-120b)

### v3_primary

| slice | method | frozen | corrected |
|---|---|---|---|
| pooled | router | 22/50 = 0.440 [0.312, 0.577] p=0.480 | 21/50 = 0.420 [0.294, 0.558] p=0.322 |
| pooled | a_always_less | 19/50 = 0.380 [0.259, 0.518] p=0.119 | 18/50 = 0.360 [0.241, 0.499] p=0.065 |
| pooled | b_always_more | 4/50 = 0.080 [0.032, 0.188] p=0.000 | 6/50 = 0.120 [0.056, 0.238] p=0.000 |
| pooled | c_stage_rate_frozen | 20/50 = 0.400 [0.276, 0.538] p=0.203 | 18/50 = 0.360 [0.241, 0.499] p=0.065 |
| pooled | c_stage_rate_corrected | 16/50 = 0.320 [0.208, 0.458] p=0.015 | 14/50 = 0.280 [0.175, 0.417] p=0.003 |
| pooled | d_always_tie | 27/50 = 0.540 [0.404, 0.670] p=0.672 | 26/50 = 0.520 [0.385, 0.652] p=0.888 |
| S2_greedy_task_only | router | 2/16 = 0.125 [0.035, 0.360] p=0.004 | 2/16 = 0.125 [0.035, 0.360] p=0.004 |
| S2_greedy_task_only | a_always_less | 0/16 = 0.000 [0.000, 0.194] p=0.000 | 0/16 = 0.000 [0.000, 0.194] p=0.000 |
| S2_greedy_task_only | b_always_more | 3/16 = 0.188 [0.066, 0.430] p=0.021 | 3/16 = 0.188 [0.066, 0.430] p=0.021 |
| S2_greedy_task_only | c_stage_rate_frozen | 2/16 = 0.125 [0.035, 0.360] p=0.004 | 2/16 = 0.125 [0.035, 0.360] p=0.004 |
| S2_greedy_task_only | c_stage_rate_corrected | 2/16 = 0.125 [0.035, 0.360] p=0.004 | 2/16 = 0.125 [0.035, 0.360] p=0.004 |
| S2_greedy_task_only | d_always_tie | 13/16 = 0.812 [0.570, 0.934] p=0.021 | 13/16 = 0.812 [0.570, 0.934] p=0.021 |
| S3_workflow_aware | router | 20/34 = 0.588 [0.422, 0.736] p=0.392 | 19/34 = 0.559 [0.395, 0.711] p=0.608 |
| S3_workflow_aware | a_always_less | 19/34 = 0.559 [0.395, 0.711] p=0.608 | 18/34 = 0.529 [0.367, 0.685] p=0.864 |
| S3_workflow_aware | b_always_more | 1/34 = 0.029 [0.005, 0.149] p=0.000 | 3/34 = 0.088 [0.030, 0.230] p=0.000 |
| S3_workflow_aware | c_stage_rate_frozen | 18/34 = 0.529 [0.367, 0.685] p=0.864 | 16/34 = 0.471 [0.315, 0.633] p=0.864 |
| S3_workflow_aware | c_stage_rate_corrected | 14/34 = 0.412 [0.264, 0.578] p=0.392 | 12/34 = 0.353 [0.215, 0.521] p=0.121 |
| S3_workflow_aware | d_always_tie | 14/34 = 0.412 [0.264, 0.578] p=0.392 | 13/34 = 0.382 [0.239, 0.550] p=0.229 |
| project:customer_churn | router | 9/17 = 0.529 [0.310, 0.738] p=1.000 | 8/17 = 0.471 [0.262, 0.690] p=1.000 |
| project:customer_churn | a_always_less | 7/17 = 0.412 [0.216, 0.640] p=0.629 | 6/17 = 0.353 [0.173, 0.587] p=0.332 |
| project:customer_churn | b_always_more | 2/17 = 0.118 [0.033, 0.343] p=0.002 | 2/17 = 0.118 [0.033, 0.343] p=0.002 |
| project:customer_churn | c_stage_rate_frozen | 7/17 = 0.412 [0.216, 0.640] p=0.629 | 6/17 = 0.353 [0.173, 0.587] p=0.332 |
| project:customer_churn | c_stage_rate_corrected | 7/17 = 0.412 [0.216, 0.640] p=0.629 | 6/17 = 0.353 [0.173, 0.587] p=0.332 |
| project:customer_churn | d_always_tie | 8/17 = 0.471 [0.262, 0.690] p=1.000 | 9/17 = 0.529 [0.310, 0.738] p=1.000 |
| project:energy_consumption | router | 8/9 = 0.889 [0.565, 0.980] p=0.039 | 8/9 = 0.889 [0.565, 0.980] p=0.039 |
| project:energy_consumption | a_always_less | 8/9 = 0.889 [0.565, 0.980] p=0.039 | 8/9 = 0.889 [0.565, 0.980] p=0.039 |
| project:energy_consumption | b_always_more | 0/9 = 0.000 [0.000, 0.299] p=0.004 | 0/9 = 0.000 [0.000, 0.299] p=0.004 |
| project:energy_consumption | c_stage_rate_frozen | 5/9 = 0.556 [0.267, 0.811] p=1.000 | 5/9 = 0.556 [0.267, 0.811] p=1.000 |
| project:energy_consumption | c_stage_rate_corrected | 4/9 = 0.444 [0.189, 0.733] p=1.000 | 4/9 = 0.444 [0.189, 0.733] p=1.000 |
| project:energy_consumption | d_always_tie | 1/9 = 0.111 [0.020, 0.435] p=0.039 | 1/9 = 0.111 [0.020, 0.435] p=0.039 |
| project:retail_sales | router | 5/8 = 0.625 [0.306, 0.863] p=0.727 | 5/8 = 0.625 [0.306, 0.863] p=0.727 |
| project:retail_sales | a_always_less | 4/8 = 0.500 [0.215, 0.785] p=1.000 | 4/8 = 0.500 [0.215, 0.785] p=1.000 |
| project:retail_sales | b_always_more | 0/8 = 0.000 [0.000, 0.324] p=0.008 | 0/8 = 0.000 [0.000, 0.324] p=0.008 |
| project:retail_sales | c_stage_rate_frozen | 5/8 = 0.625 [0.306, 0.863] p=0.727 | 5/8 = 0.625 [0.306, 0.863] p=0.727 |
| project:retail_sales | c_stage_rate_corrected | 3/8 = 0.375 [0.137, 0.694] p=0.727 | 3/8 = 0.375 [0.137, 0.694] p=0.727 |
| project:retail_sales | d_always_tie | 4/8 = 0.500 [0.215, 0.785] p=1.000 | 4/8 = 0.500 [0.215, 0.785] p=1.000 |
| project:support_operations | router | 0/16 = 0.000 [0.000, 0.194] p=0.000 | 0/16 = 0.000 [0.000, 0.194] p=0.000 |
| project:support_operations | a_always_less | 0/16 = 0.000 [0.000, 0.194] p=0.000 | 0/16 = 0.000 [0.000, 0.194] p=0.000 |
| project:support_operations | b_always_more | 2/16 = 0.125 [0.035, 0.360] p=0.004 | 4/16 = 0.250 [0.102, 0.495] p=0.077 |
| project:support_operations | c_stage_rate_frozen | 3/16 = 0.188 [0.066, 0.430] p=0.021 | 2/16 = 0.125 [0.035, 0.360] p=0.004 |
| project:support_operations | c_stage_rate_corrected | 2/16 = 0.125 [0.035, 0.360] p=0.004 | 1/16 = 0.062 [0.011, 0.283] p=0.001 |
| project:support_operations | d_always_tie | 14/16 = 0.875 [0.640, 0.965] p=0.004 | 12/16 = 0.750 [0.505, 0.898] p=0.077 |

McNemar exact p, router vs baseline (pooled; discordant router-only/baseline-only), corrected labels:

- a_always_less: 3/0, p=0.25
- b_always_more: 21/6, p=0.005924612283706665
- c_stage_rate_frozen: 9/6, p=0.60723876953125
- c_stage_rate_corrected: 10/3, p=0.09228515625
- d_always_tie: 18/23, p=0.5327092552361137

Predicted sign (rows -1,0,1) by actual sign (cols -1,0,1), frozen / corrected:

- frozen: -1|-1:19; -1|0:23; -1|1:3; 0|-1:0; 0|0:3; 0|1:1; 1|-1:0; 1|0:1; 1|1:0
- corrected: -1|-1:18; -1|0:22; -1|1:5; 0|-1:0; 0|0:3; 0|1:1; 1|-1:0; 1|0:1; 1|1:0

Predictions whose correctness or actual sign changed: 3 (listed in the JSON `changed_predictions`).

### v31_secondary

| slice | method | frozen | corrected |
|---|---|---|---|
| pooled | router | 22/50 = 0.440 [0.312, 0.577] p=0.480 | 20/50 = 0.400 [0.276, 0.538] p=0.203 |
| pooled | a_always_less | 22/50 = 0.440 [0.312, 0.577] p=0.480 | 20/50 = 0.400 [0.276, 0.538] p=0.203 |
| pooled | b_always_more | 5/50 = 0.100 [0.043, 0.214] p=0.000 | 8/50 = 0.160 [0.083, 0.285] p=0.000 |
| pooled | c_stage_rate_frozen | 22/50 = 0.440 [0.312, 0.577] p=0.480 | 19/50 = 0.380 [0.259, 0.518] p=0.119 |
| pooled | c_stage_rate_corrected | 18/50 = 0.360 [0.241, 0.499] p=0.065 | 15/50 = 0.300 [0.191, 0.438] p=0.007 |
| pooled | d_always_tie | 23/50 = 0.460 [0.330, 0.596] p=0.672 | 22/50 = 0.440 [0.312, 0.577] p=0.480 |
| S2_greedy_task_only | router | 4/16 = 0.250 [0.102, 0.495] p=0.077 | 3/16 = 0.188 [0.066, 0.430] p=0.021 |
| S2_greedy_task_only | a_always_less | 5/16 = 0.312 [0.142, 0.556] p=0.210 | 4/16 = 0.250 [0.102, 0.495] p=0.077 |
| S2_greedy_task_only | b_always_more | 4/16 = 0.250 [0.102, 0.495] p=0.077 | 5/16 = 0.312 [0.142, 0.556] p=0.210 |
| S2_greedy_task_only | c_stage_rate_frozen | 4/16 = 0.250 [0.102, 0.495] p=0.077 | 3/16 = 0.188 [0.066, 0.430] p=0.021 |
| S2_greedy_task_only | c_stage_rate_corrected | 4/16 = 0.250 [0.102, 0.495] p=0.077 | 3/16 = 0.188 [0.066, 0.430] p=0.021 |
| S2_greedy_task_only | d_always_tie | 7/16 = 0.438 [0.231, 0.668] p=0.804 | 7/16 = 0.438 [0.231, 0.668] p=0.804 |
| S3_workflow_aware | router | 18/34 = 0.529 [0.367, 0.685] p=0.864 | 17/34 = 0.500 [0.341, 0.659] p=1.000 |
| S3_workflow_aware | a_always_less | 17/34 = 0.500 [0.341, 0.659] p=1.000 | 16/34 = 0.471 [0.315, 0.633] p=0.864 |
| S3_workflow_aware | b_always_more | 1/34 = 0.029 [0.005, 0.149] p=0.000 | 3/34 = 0.088 [0.030, 0.230] p=0.000 |
| S3_workflow_aware | c_stage_rate_frozen | 18/34 = 0.529 [0.367, 0.685] p=0.864 | 16/34 = 0.471 [0.315, 0.633] p=0.864 |
| S3_workflow_aware | c_stage_rate_corrected | 14/34 = 0.412 [0.264, 0.578] p=0.392 | 12/34 = 0.353 [0.215, 0.521] p=0.121 |
| S3_workflow_aware | d_always_tie | 16/34 = 0.471 [0.315, 0.633] p=0.864 | 15/34 = 0.441 [0.289, 0.605] p=0.608 |
| project:customer_churn | router | 9/17 = 0.529 [0.310, 0.738] p=1.000 | 7/17 = 0.412 [0.216, 0.640] p=0.629 |
| project:customer_churn | a_always_less | 10/17 = 0.588 [0.360, 0.784] p=0.629 | 8/17 = 0.471 [0.262, 0.690] p=1.000 |
| project:customer_churn | b_always_more | 3/17 = 0.176 [0.062, 0.410] p=0.013 | 4/17 = 0.235 [0.096, 0.473] p=0.049 |
| project:customer_churn | c_stage_rate_frozen | 9/17 = 0.529 [0.310, 0.738] p=1.000 | 7/17 = 0.412 [0.216, 0.640] p=0.629 |
| project:customer_churn | c_stage_rate_corrected | 9/17 = 0.529 [0.310, 0.738] p=1.000 | 7/17 = 0.412 [0.216, 0.640] p=0.629 |
| project:customer_churn | d_always_tie | 4/17 = 0.235 [0.096, 0.473] p=0.049 | 5/17 = 0.294 [0.133, 0.531] p=0.143 |
| project:energy_consumption | router | 8/9 = 0.889 [0.565, 0.980] p=0.039 | 8/9 = 0.889 [0.565, 0.980] p=0.039 |
| project:energy_consumption | a_always_less | 8/9 = 0.889 [0.565, 0.980] p=0.039 | 8/9 = 0.889 [0.565, 0.980] p=0.039 |
| project:energy_consumption | b_always_more | 0/9 = 0.000 [0.000, 0.299] p=0.004 | 0/9 = 0.000 [0.000, 0.299] p=0.004 |
| project:energy_consumption | c_stage_rate_frozen | 5/9 = 0.556 [0.267, 0.811] p=1.000 | 5/9 = 0.556 [0.267, 0.811] p=1.000 |
| project:energy_consumption | c_stage_rate_corrected | 4/9 = 0.444 [0.189, 0.733] p=1.000 | 4/9 = 0.444 [0.189, 0.733] p=1.000 |
| project:energy_consumption | d_always_tie | 1/9 = 0.111 [0.020, 0.435] p=0.039 | 1/9 = 0.111 [0.020, 0.435] p=0.039 |
| project:retail_sales | router | 5/8 = 0.625 [0.306, 0.863] p=0.727 | 5/8 = 0.625 [0.306, 0.863] p=0.727 |
| project:retail_sales | a_always_less | 4/8 = 0.500 [0.215, 0.785] p=1.000 | 4/8 = 0.500 [0.215, 0.785] p=1.000 |
| project:retail_sales | b_always_more | 0/8 = 0.000 [0.000, 0.324] p=0.008 | 0/8 = 0.000 [0.000, 0.324] p=0.008 |
| project:retail_sales | c_stage_rate_frozen | 5/8 = 0.625 [0.306, 0.863] p=0.727 | 5/8 = 0.625 [0.306, 0.863] p=0.727 |
| project:retail_sales | c_stage_rate_corrected | 3/8 = 0.375 [0.137, 0.694] p=0.727 | 3/8 = 0.375 [0.137, 0.694] p=0.727 |
| project:retail_sales | d_always_tie | 4/8 = 0.500 [0.215, 0.785] p=1.000 | 4/8 = 0.500 [0.215, 0.785] p=1.000 |
| project:support_operations | router | 0/16 = 0.000 [0.000, 0.194] p=0.000 | 0/16 = 0.000 [0.000, 0.194] p=0.000 |
| project:support_operations | a_always_less | 0/16 = 0.000 [0.000, 0.194] p=0.000 | 0/16 = 0.000 [0.000, 0.194] p=0.000 |
| project:support_operations | b_always_more | 2/16 = 0.125 [0.035, 0.360] p=0.004 | 4/16 = 0.250 [0.102, 0.495] p=0.077 |
| project:support_operations | c_stage_rate_frozen | 3/16 = 0.188 [0.066, 0.430] p=0.021 | 2/16 = 0.125 [0.035, 0.360] p=0.004 |
| project:support_operations | c_stage_rate_corrected | 2/16 = 0.125 [0.035, 0.360] p=0.004 | 1/16 = 0.062 [0.011, 0.283] p=0.001 |
| project:support_operations | d_always_tie | 14/16 = 0.875 [0.640, 0.965] p=0.004 | 12/16 = 0.750 [0.505, 0.898] p=0.077 |

McNemar exact p, router vs baseline (pooled; discordant router-only/baseline-only), corrected labels:

- a_always_less: 1/1, p=1.0
- b_always_more: 20/8, p=0.03569813817739487
- c_stage_rate_frozen: 7/6, p=1.0
- c_stage_rate_corrected: 8/3, p=0.2265625
- d_always_tie: 19/21, p=0.8746293123804207

Predicted sign (rows -1,0,1) by actual sign (cols -1,0,1), frozen / corrected:

- frozen: -1|-1:21; -1|0:21; -1|1:3; 0|-1:1; 0|0:1; 0|1:2; 1|-1:0; 1|0:1; 1|1:0
- corrected: -1|-1:19; -1|0:20; -1|1:6; 0|-1:1; 0|0:1; 0|1:2; 1|-1:0; 1|0:1; 1|1:0

Predictions whose correctness or actual sign changed: 4 (listed in the JSON `changed_predictions`).

## Group price_matched_16384 (alias meaning: `A` = Sonnet 4.6, `B` = Kimi K3, `C` = GLM 5)

### v3_primary

| slice | method | frozen | corrected |
|---|---|---|---|
| pooled | router | 31/64 = 0.484 [0.366, 0.604] p=0.901 | 24/64 = 0.375 [0.267, 0.497] p=0.060 |
| pooled | a_always_less | 32/64 = 0.500 [0.381, 0.619] p=1.000 | 25/64 = 0.391 [0.281, 0.513] p=0.103 |
| pooled | b_always_more | 2/64 = 0.031 [0.009, 0.107] p=0.000 | 3/64 = 0.047 [0.016, 0.129] p=0.000 |
| pooled | c_stage_rate_frozen | 36/64 = 0.562 [0.441, 0.677] p=0.382 | 29/64 = 0.453 [0.337, 0.574] p=0.532 |
| pooled | c_stage_rate_corrected | 22/64 = 0.344 [0.239, 0.466] p=0.017 | 28/64 = 0.438 [0.323, 0.559] p=0.382 |
| pooled | d_always_tie | 30/64 = 0.469 [0.352, 0.589] p=0.708 | 36/64 = 0.562 [0.441, 0.677] p=0.382 |
| S2_greedy_task_only | router | 18/32 = 0.562 [0.393, 0.718] p=0.597 | 14/32 = 0.438 [0.282, 0.607] p=0.597 |
| S2_greedy_task_only | a_always_less | 20/32 = 0.625 [0.453, 0.771] p=0.215 | 16/32 = 0.500 [0.336, 0.664] p=1.000 |
| S2_greedy_task_only | b_always_more | 1/32 = 0.031 [0.006, 0.157] p=0.000 | 1/32 = 0.031 [0.006, 0.157] p=0.000 |
| S2_greedy_task_only | c_stage_rate_frozen | 18/32 = 0.562 [0.393, 0.718] p=0.597 | 14/32 = 0.438 [0.282, 0.607] p=0.597 |
| S2_greedy_task_only | c_stage_rate_corrected | 10/32 = 0.312 [0.180, 0.486] p=0.050 | 13/32 = 0.406 [0.255, 0.577] p=0.377 |
| S2_greedy_task_only | d_always_tie | 11/32 = 0.344 [0.204, 0.517] p=0.110 | 15/32 = 0.469 [0.309, 0.636] p=0.860 |
| S3_workflow_aware | router | 13/32 = 0.406 [0.255, 0.577] p=0.377 | 10/32 = 0.312 [0.180, 0.486] p=0.050 |
| S3_workflow_aware | a_always_less | 12/32 = 0.375 [0.229, 0.547] p=0.215 | 9/32 = 0.281 [0.156, 0.454] p=0.020 |
| S3_workflow_aware | b_always_more | 1/32 = 0.031 [0.006, 0.157] p=0.000 | 2/32 = 0.062 [0.017, 0.201] p=0.000 |
| S3_workflow_aware | c_stage_rate_frozen | 18/32 = 0.562 [0.393, 0.718] p=0.597 | 15/32 = 0.469 [0.309, 0.636] p=0.860 |
| S3_workflow_aware | c_stage_rate_corrected | 12/32 = 0.375 [0.229, 0.547] p=0.215 | 15/32 = 0.469 [0.309, 0.636] p=0.860 |
| S3_workflow_aware | d_always_tie | 19/32 = 0.594 [0.423, 0.745] p=0.377 | 21/32 = 0.656 [0.483, 0.796] p=0.110 |
| project:customer_churn | router | 12/16 = 0.750 [0.505, 0.898] p=0.077 | 10/16 = 0.625 [0.386, 0.815] p=0.454 |
| project:customer_churn | a_always_less | 14/16 = 0.875 [0.640, 0.965] p=0.004 | 12/16 = 0.750 [0.505, 0.898] p=0.077 |
| project:customer_churn | b_always_more | 2/16 = 0.125 [0.035, 0.360] p=0.004 | 2/16 = 0.125 [0.035, 0.360] p=0.004 |
| project:customer_churn | c_stage_rate_frozen | 12/16 = 0.750 [0.505, 0.898] p=0.077 | 10/16 = 0.625 [0.386, 0.815] p=0.454 |
| project:customer_churn | c_stage_rate_corrected | 4/16 = 0.250 [0.102, 0.495] p=0.077 | 6/16 = 0.375 [0.185, 0.614] p=0.454 |
| project:customer_churn | d_always_tie | 0/16 = 0.000 [0.000, 0.194] p=0.000 | 2/16 = 0.125 [0.035, 0.360] p=0.004 |
| project:energy_consumption | router | 12/16 = 0.750 [0.505, 0.898] p=0.077 | 8/16 = 0.500 [0.280, 0.720] p=1.000 |
| project:energy_consumption | a_always_less | 10/16 = 0.625 [0.386, 0.815] p=0.454 | 6/16 = 0.375 [0.185, 0.614] p=0.454 |
| project:energy_consumption | b_always_more | 0/16 = 0.000 [0.000, 0.194] p=0.000 | 0/16 = 0.000 [0.000, 0.194] p=0.000 |
| project:energy_consumption | c_stage_rate_frozen | 12/16 = 0.750 [0.505, 0.898] p=0.077 | 8/16 = 0.500 [0.280, 0.720] p=1.000 |
| project:energy_consumption | c_stage_rate_corrected | 6/16 = 0.375 [0.185, 0.614] p=0.454 | 8/16 = 0.500 [0.280, 0.720] p=1.000 |
| project:energy_consumption | d_always_tie | 6/16 = 0.375 [0.185, 0.614] p=0.454 | 10/16 = 0.625 [0.386, 0.815] p=0.454 |
| project:retail_sales | router | 2/16 = 0.125 [0.035, 0.360] p=0.004 | 2/16 = 0.125 [0.035, 0.360] p=0.004 |
| project:retail_sales | a_always_less | 0/16 = 0.000 [0.000, 0.194] p=0.000 | 0/16 = 0.000 [0.000, 0.194] p=0.000 |
| project:retail_sales | b_always_more | 0/16 = 0.000 [0.000, 0.194] p=0.000 | 0/16 = 0.000 [0.000, 0.194] p=0.000 |
| project:retail_sales | c_stage_rate_frozen | 2/16 = 0.125 [0.035, 0.360] p=0.004 | 2/16 = 0.125 [0.035, 0.360] p=0.004 |
| project:retail_sales | c_stage_rate_corrected | 6/16 = 0.375 [0.185, 0.614] p=0.454 | 6/16 = 0.375 [0.185, 0.614] p=0.454 |
| project:retail_sales | d_always_tie | 16/16 = 1.000 [0.806, 1.000] p=0.000 | 16/16 = 1.000 [0.806, 1.000] p=0.000 |
| project:support_operations | router | 5/16 = 0.312 [0.142, 0.556] p=0.210 | 4/16 = 0.250 [0.102, 0.495] p=0.077 |
| project:support_operations | a_always_less | 8/16 = 0.500 [0.280, 0.720] p=1.000 | 7/16 = 0.438 [0.231, 0.668] p=0.804 |
| project:support_operations | b_always_more | 0/16 = 0.000 [0.000, 0.194] p=0.000 | 1/16 = 0.062 [0.011, 0.283] p=0.001 |
| project:support_operations | c_stage_rate_frozen | 10/16 = 0.625 [0.386, 0.815] p=0.454 | 9/16 = 0.562 [0.332, 0.769] p=0.804 |
| project:support_operations | c_stage_rate_corrected | 6/16 = 0.375 [0.185, 0.614] p=0.454 | 8/16 = 0.500 [0.280, 0.720] p=1.000 |
| project:support_operations | d_always_tie | 8/16 = 0.500 [0.280, 0.720] p=1.000 | 8/16 = 0.500 [0.280, 0.720] p=1.000 |

McNemar exact p, router vs baseline (pooled; discordant router-only/baseline-only), corrected labels:

- a_always_less: 6/7, p=1.0
- b_always_more: 22/1, p=5.7220458984375e-06
- c_stage_rate_frozen: 2/7, p=0.1796875
- c_stage_rate_corrected: 12/16, p=0.5715881884098053
- d_always_tie: 20/32, p=0.12634707581392135

Predicted sign (rows -1,0,1) by actual sign (cols -1,0,1), frozen / corrected:

- frozen: -1|-1:25; -1|0:19; -1|1:0; 0|-1:5; 0|0:4; 0|1:0; 1|-1:2; 1|0:7; 1|1:2
- corrected: -1|-1:18; -1|0:25; -1|1:1; 0|-1:5; 0|0:4; 0|1:0; 1|-1:2; 1|0:7; 1|1:2

Predictions whose correctness or actual sign changed: 8 (listed in the JSON `changed_predictions`).

### v31_secondary

| slice | method | frozen | corrected |
|---|---|---|---|
| pooled | router | 27/64 = 0.422 [0.309, 0.544] p=0.260 | 20/64 = 0.312 [0.212, 0.434] p=0.004 |
| pooled | a_always_less | 24/64 = 0.375 [0.267, 0.497] p=0.060 | 17/64 = 0.266 [0.173, 0.385] p=0.000 |
| pooled | b_always_more | 0/64 = 0.000 [0.000, 0.057] p=0.000 | 1/64 = 0.016 [0.003, 0.083] p=0.000 |
| pooled | c_stage_rate_frozen | 32/64 = 0.500 [0.381, 0.619] p=1.000 | 25/64 = 0.391 [0.281, 0.513] p=0.103 |
| pooled | c_stage_rate_corrected | 22/64 = 0.344 [0.239, 0.466] p=0.017 | 28/64 = 0.438 [0.323, 0.559] p=0.382 |
| pooled | d_always_tie | 40/64 = 0.625 [0.503, 0.733] p=0.060 | 46/64 = 0.719 [0.599, 0.814] p=0.001 |
| S2_greedy_task_only | router | 16/32 = 0.500 [0.336, 0.664] p=1.000 | 12/32 = 0.375 [0.229, 0.547] p=0.215 |
| S2_greedy_task_only | a_always_less | 16/32 = 0.500 [0.336, 0.664] p=1.000 | 12/32 = 0.375 [0.229, 0.547] p=0.215 |
| S2_greedy_task_only | b_always_more | 0/32 = 0.000 [0.000, 0.107] p=0.000 | 0/32 = 0.000 [0.000, 0.107] p=0.000 |
| S2_greedy_task_only | c_stage_rate_frozen | 16/32 = 0.500 [0.336, 0.664] p=1.000 | 12/32 = 0.375 [0.229, 0.547] p=0.215 |
| S2_greedy_task_only | c_stage_rate_corrected | 10/32 = 0.312 [0.180, 0.486] p=0.050 | 13/32 = 0.406 [0.255, 0.577] p=0.377 |
| S2_greedy_task_only | d_always_tie | 16/32 = 0.500 [0.336, 0.664] p=1.000 | 20/32 = 0.625 [0.453, 0.771] p=0.215 |
| S3_workflow_aware | router | 11/32 = 0.344 [0.204, 0.517] p=0.110 | 8/32 = 0.250 [0.133, 0.421] p=0.007 |
| S3_workflow_aware | a_always_less | 8/32 = 0.250 [0.133, 0.421] p=0.007 | 5/32 = 0.156 [0.069, 0.318] p=0.000 |
| S3_workflow_aware | b_always_more | 0/32 = 0.000 [0.000, 0.107] p=0.000 | 1/32 = 0.031 [0.006, 0.157] p=0.000 |
| S3_workflow_aware | c_stage_rate_frozen | 16/32 = 0.500 [0.336, 0.664] p=1.000 | 13/32 = 0.406 [0.255, 0.577] p=0.377 |
| S3_workflow_aware | c_stage_rate_corrected | 12/32 = 0.375 [0.229, 0.547] p=0.215 | 15/32 = 0.469 [0.309, 0.636] p=0.860 |
| S3_workflow_aware | d_always_tie | 24/32 = 0.750 [0.579, 0.867] p=0.007 | 26/32 = 0.812 [0.647, 0.911] p=0.001 |
| project:customer_churn | router | 8/16 = 0.500 [0.280, 0.720] p=1.000 | 6/16 = 0.375 [0.185, 0.614] p=0.454 |
| project:customer_churn | a_always_less | 6/16 = 0.375 [0.185, 0.614] p=0.454 | 4/16 = 0.250 [0.102, 0.495] p=0.077 |
| project:customer_churn | b_always_more | 0/16 = 0.000 [0.000, 0.194] p=0.000 | 0/16 = 0.000 [0.000, 0.194] p=0.000 |
| project:customer_churn | c_stage_rate_frozen | 8/16 = 0.500 [0.280, 0.720] p=1.000 | 6/16 = 0.375 [0.185, 0.614] p=0.454 |
| project:customer_churn | c_stage_rate_corrected | 4/16 = 0.250 [0.102, 0.495] p=0.077 | 6/16 = 0.375 [0.185, 0.614] p=0.454 |
| project:customer_churn | d_always_tie | 10/16 = 0.625 [0.386, 0.815] p=0.454 | 12/16 = 0.750 [0.505, 0.898] p=0.077 |
| project:energy_consumption | router | 12/16 = 0.750 [0.505, 0.898] p=0.077 | 8/16 = 0.500 [0.280, 0.720] p=1.000 |
| project:energy_consumption | a_always_less | 10/16 = 0.625 [0.386, 0.815] p=0.454 | 6/16 = 0.375 [0.185, 0.614] p=0.454 |
| project:energy_consumption | b_always_more | 0/16 = 0.000 [0.000, 0.194] p=0.000 | 0/16 = 0.000 [0.000, 0.194] p=0.000 |
| project:energy_consumption | c_stage_rate_frozen | 12/16 = 0.750 [0.505, 0.898] p=0.077 | 8/16 = 0.500 [0.280, 0.720] p=1.000 |
| project:energy_consumption | c_stage_rate_corrected | 6/16 = 0.375 [0.185, 0.614] p=0.454 | 8/16 = 0.500 [0.280, 0.720] p=1.000 |
| project:energy_consumption | d_always_tie | 6/16 = 0.375 [0.185, 0.614] p=0.454 | 10/16 = 0.625 [0.386, 0.815] p=0.454 |
| project:retail_sales | router | 2/16 = 0.125 [0.035, 0.360] p=0.004 | 2/16 = 0.125 [0.035, 0.360] p=0.004 |
| project:retail_sales | a_always_less | 0/16 = 0.000 [0.000, 0.194] p=0.000 | 0/16 = 0.000 [0.000, 0.194] p=0.000 |
| project:retail_sales | b_always_more | 0/16 = 0.000 [0.000, 0.194] p=0.000 | 0/16 = 0.000 [0.000, 0.194] p=0.000 |
| project:retail_sales | c_stage_rate_frozen | 2/16 = 0.125 [0.035, 0.360] p=0.004 | 2/16 = 0.125 [0.035, 0.360] p=0.004 |
| project:retail_sales | c_stage_rate_corrected | 6/16 = 0.375 [0.185, 0.614] p=0.454 | 6/16 = 0.375 [0.185, 0.614] p=0.454 |
| project:retail_sales | d_always_tie | 16/16 = 1.000 [0.806, 1.000] p=0.000 | 16/16 = 1.000 [0.806, 1.000] p=0.000 |
| project:support_operations | router | 5/16 = 0.312 [0.142, 0.556] p=0.210 | 4/16 = 0.250 [0.102, 0.495] p=0.077 |
| project:support_operations | a_always_less | 8/16 = 0.500 [0.280, 0.720] p=1.000 | 7/16 = 0.438 [0.231, 0.668] p=0.804 |
| project:support_operations | b_always_more | 0/16 = 0.000 [0.000, 0.194] p=0.000 | 1/16 = 0.062 [0.011, 0.283] p=0.001 |
| project:support_operations | c_stage_rate_frozen | 10/16 = 0.625 [0.386, 0.815] p=0.454 | 9/16 = 0.562 [0.332, 0.769] p=0.804 |
| project:support_operations | c_stage_rate_corrected | 6/16 = 0.375 [0.185, 0.614] p=0.454 | 8/16 = 0.500 [0.280, 0.720] p=1.000 |
| project:support_operations | d_always_tie | 8/16 = 0.500 [0.280, 0.720] p=1.000 | 8/16 = 0.500 [0.280, 0.720] p=1.000 |

McNemar exact p, router vs baseline (pooled; discordant router-only/baseline-only), corrected labels:

- a_always_less: 6/3, p=0.5078125
- b_always_more: 20/1, p=2.09808349609375e-05
- c_stage_rate_frozen: 2/7, p=0.1796875
- c_stage_rate_corrected: 10/18, p=0.1849333420395851
- d_always_tie: 14/40, p=0.0005354355028570623

Predicted sign (rows -1,0,1) by actual sign (cols -1,0,1), frozen / corrected:

- frozen: -1|-1:21; -1|0:23; -1|1:0; 0|-1:3; 0|0:6; 0|1:0; 1|-1:0; 1|0:11; 1|1:0
- corrected: -1|-1:14; -1|0:29; -1|1:1; 0|-1:3; 0|0:6; 0|1:0; 1|-1:0; 1|0:11; 1|1:0

Predictions whose correctness or actual sign changed: 8 (listed in the JSON `changed_predictions`).

