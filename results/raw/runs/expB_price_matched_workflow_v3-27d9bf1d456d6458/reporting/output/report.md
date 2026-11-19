# Customer Churn Analysis Report

Analysis of 749 customers reveals an overall churn rate of 37.7%. Monthly-contract customers churn at more than double the rate of annual-contract customers. A high-risk segment of 100 customers (high support tickets, low satisfaction) churns at 71.0%. Premium-plan customers generate nearly 4× the lifetime value of Basic-plan customers, underscoring the revenue importance of retention at the top tier.

## Key findings
- [q1] The dataset contains 749 customers with an overall churn rate of 37.7% and an average monthly fee of $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
- [q2] Churn rates differ modestly across plans: Basic is highest at 38.9%, followed by Standard at 36.7%, and Premium is lowest at 36.6%. The spread is narrow (~2.3 percentage points), suggesting plan tier alone is not a strong churn differentiator.
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Ranking: Basic, Standard, Premium
  - Derived difference(churn_rate_basic_pct, churn_rate_premium_pct): 2.27
- [q3] Churn by signup cohort shows the 2024 cohort is highest at 39.8%, followed by 2021 at 38.0%, 2023 at 37.1%, and 2022 lowest at 36.7%. The most recent cohort's elevated churn may reflect insufficient onboarding time.
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Ranking: 2024, 2021, 2023, 2022
- [q4] Monthly-contract customers churn at 48.3% versus 21.9% for annual-contract customers — a 121.1% relative increase. This is the single strongest churn predictor identified, making contract-type conversion a high-priority retention lever.
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
- [q5] 100 customers with 5 or more support tickets and a satisfaction score ≤ 2 form a critical at-risk segment, churning at 71.0% — nearly double the overall rate.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
  - Derived difference(at_risk_churn_rate_pct, churn_rate_pct): 33.35
- [q6] Customer tenure averages 20.8 months (median 19.0, SD 13.2), indicating a wide spread. Mean satisfaction among the 722 customers with a score is 3.4 out of 5; 27 customers have a missing satisfaction score.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
  - Derived difference(customer_count, satisfaction_missing_count): 722.0
- [q7] Lifetime value rises sharply with plan tier: Basic averages $463, Standard $869, and Premium $1,817. Premium LTV is 292.0% higher than Basic, making Premium-customer retention disproportionately valuable to revenue.
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401545, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic

## Limitations
- The 2024 cohort has had less time to churn than earlier cohorts, so its elevated churn rate may partly reflect truncated observation windows rather than a genuine behavioural difference.
- 27 customers (3.6%) have missing satisfaction scores, which could introduce slight bias into satisfaction-based metrics and the at-risk segment definition.
- Lifetime value is a derived field whose calculation methodology is not documented in the handoff; results should be interpreted with that caveat.
- The dataset is a single snapshot; no longitudinal tracking is available to confirm causal relationships between plan, contract type, and churn.
- The at-risk segment threshold (tickets ≥ 5, satisfaction ≤ 2) is rule-based and has not been validated against a predictive model.

## Conclusion
Contract type is the dominant churn driver: converting monthly subscribers to annual contracts could cut their churn rate by more than half. The 100-customer at-risk segment (71.0% churn) warrants immediate intervention. Given Premium customers deliver 292% more lifetime value than Basic customers, targeted retention programmes for high-value subscribers should be prioritised alongside broader efforts to improve support resolution and onboarding for the 2024 cohort.
