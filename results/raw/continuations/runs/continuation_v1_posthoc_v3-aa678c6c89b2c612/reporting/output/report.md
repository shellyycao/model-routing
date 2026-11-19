# Customer Churn Analysis — Verified Findings Report

Across 749 customers, overall churn is 37.65% and the average monthly fee is $42.11. Churn varies little by plan (36.60%–38.87%) or signup cohort (36.74%–39.83%), but contract type is decisive: monthly-contract customers churn at 48.32% versus 21.85% for annual contracts, a 121.11% relative increase. A defined at-risk segment of 100 customers churns at 71.0%. Premium customers deliver a mean lifetime value of $1,816.78, 292.01% above Basic.

## Key findings
- [q1] The cleaned dataset contains 749 customers. Overall churn is 37.65%, and the mean monthly fee is $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
- [q2] Churn is nearly flat across plans: Basic 38.87%, Standard 36.68% and Premium 36.60% — a spread of only 2.27 percentage points between the highest (Basic) and lowest (Premium) plan.
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Ranking: Basic, Standard, Premium
  - Derived difference(churn_rate_basic_pct, churn_rate_premium_pct): 2.27
- [q3] Churn by signup cohort is stable with no clear trend: 2021 38.02%, 2022 36.74%, 2023 37.05% and 2024 39.83%. The newest (2024) cohort is highest, 3.09 percentage points above the lowest (2022).
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Ranking: 2024, 2021, 2023, 2022
  - Derived difference(churn_rate_cohort_2024_pct, churn_rate_cohort_2022_pct): 3.09
- [q4] Contract type is the strongest churn differentiator: monthly contracts churn at 48.32% versus 21.85% for annual contracts, a 121.11% relative increase — about 26.47 percentage points higher.
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
  - Derived difference(churn_rate_monthly_pct, churn_rate_annual_pct): 26.47
- [q5] The at-risk segment (5+ support tickets and satisfaction score of 2 or less) comprises 100 customers — 13.35% of the customer base — and churns at 71.0%, which is 33.35 percentage points above the overall churn rate of 37.65%.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
  - Derived share(at_risk_customer_count, customer_count): 13.35
  - Derived difference(at_risk_churn_rate_pct, churn_rate_pct): 33.35
- [q6] Mean tenure is 20.81 months (median 19.0; sample standard deviation 13.25), with the mean above the median indicating a spread of longer-tenured customers. Mean satisfaction is 3.42 among scored customers, and 27 customers have a missing satisfaction score.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
- [q7] Mean lifetime value rises steeply with plan tier: Basic $463.46, Standard $868.83 and Premium $1,816.78. Premium LTV is 292.01% higher than Basic, roughly 3.92x the Basic value.
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401545, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic
  - Derived ratio(ltv_premium, ltv_basic): 3.92

## Limitations
- The analysis is a single point-in-time snapshot; all differences are associational, not causal. For example, annual-contract customers may self-select as more committed rather than being retained by the contract itself.
- Satisfaction scores are missing for 27 customers, and the at-risk definition excludes them, so the at-risk segment may be understated.
- Lifetime value is computed from current data without adjusting for tenure or cohort mix, so plan-level LTV gaps partly reflect how long customers on each plan have been subscribed.
- No statistical significance testing was performed; small differences (such as the 2.27-point spread between plans) may not be meaningful.
- The at-risk thresholds (5+ support tickets, satisfaction <= 2) are arbitrary cut-offs, and segment results are sensitive to these choices.

## Conclusion
Churn risk is dominated by contract structure and service experience, not by plan tier or signup cohort. Converting monthly customers to annual contracts and running targeted retention on the 100-customer at-risk segment, which churns at 71.0%, are the highest-leverage actions to reduce the 37.65% overall churn rate.
