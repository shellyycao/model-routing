# Customer Churn Analysis — Verified Findings Report

Across 749 customers, overall churn is 37.65% with an average monthly fee of $42.11. Churn is nearly flat across plans (36.60%-38.87%) and signup cohorts (36.74%-39.83%). Contract type is the strongest differentiator: Monthly contracts churn at 48.32% versus 21.85% for Annual, a 121.11% relative increase. An at-risk segment of 100 customers with many support tickets and low satisfaction churns at 71.0%. Premium customers deliver by far the highest average lifetime value at $1,816.78, +292.01% versus Basic.

## Key findings
- [q1] The cleaned dataset contains 749 customers. Overall churn stands at 37.65%, and the average monthly fee is $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
- [q2] Churn differs only modestly by plan: Basic 38.87%, Standard 36.68% and Premium 36.60% — a spread of roughly 2.3 percentage points between highest and lowest, so plan tier is not a strong churn driver.
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Ranking: Basic, Standard, Premium
  - Derived difference(churn_rate_basic_pct, churn_rate_premium_pct): 2.3
- [q3] Churn is broadly stable across signup cohorts: 2021 at 38.02%, 2022 at 36.74%, 2023 at 37.05% and 2024 at 39.83%. The newest (2024) cohort churns most, the 2022 cohort least.
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Ranking: 2024, 2021, 2023, 2022
- [q4] Customers on Monthly contracts churn at 48.32% versus 21.85% on Annual contracts — a relative increase of 121.11%, i.e. about 26.5 percentage points higher. Contract type is the clearest churn differentiator in this analysis.
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
  - Derived difference(churn_rate_monthly_pct, churn_rate_annual_pct): 26.5
- [q5] The at-risk segment (support_tickets >= 5 and satisfaction_score <= 2) comprises 100 customers, roughly 13.4% of the customer base, and churns at 71.0% — far above the overall churn rate of 37.65%.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
  - Derived share(at_risk_customer_count, customer_count): 13.4
- [q6] Average customer tenure is 20.81 months (median 19.0, sample standard deviation 13.25), indicating a wide spread of customer ages. Mean satisfaction among scored customers is 3.42, and 27 customers have a missing satisfaction score.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
- [q7] Average lifetime value rises steeply with plan tier: Basic $463.46, Standard $868.83 and Premium $1,816.78. Premium LTV is 292.01% higher than Basic, making Premium retention especially valuable.
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401546, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic

## Limitations
- Findings are associational, not causal: lower churn on Annual contracts may reflect customer self-selection rather than a true contract effect.
- 27 customers have missing satisfaction scores; they are excluded from the satisfaction mean and cannot qualify for the at-risk segment, which may bias both metrics.
- The at-risk segment uses fixed thresholds (support_tickets >= 5, satisfaction_score <= 2); results are sensitive to this definition.
- No statistical-significance testing was performed, so small differences between plans and cohorts may be due to chance.
- lifetime_value is taken as given; its calculation method and time window are not documented in the handoff.
- The snapshot is cross-sectional, so cohort churn rates reflect cumulative churn to date and not survival dynamics over time.

## Conclusion
Retention efforts should prioritise moving Monthly-contract customers to Annual plans, given the 121.11% relative churn gap, and proactively engaging the 100 at-risk customers who churn at 71.0%. Plan tier and signup cohort show little churn variation, so service experience and contract structure matter more than plan mix; protecting high-value Premium customers (average LTV $1,816.78) offers the greatest revenue payoff.
