# Customer Churn Analysis Report

Across 749 customers, overall churn is 37.7% with an average monthly fee of $42.1. Churn varies modestly by plan, is highest for recent 2024 sign‑ups, and is dramatically higher for monthly contracts (48.3%) versus annual contracts (21.9%). A high‑risk segment (100 customers) churns at 71%. Tenure averages 20.8 months (median 19) with a satisfaction mean of 3.42 and 27 missing scores. Lifetime value rises sharply from Basic ($463) to Premium ($1,817), a 292% increase.

## Key findings
- [q1] The dataset contains 749 customers; 37.7% have churned, and the average monthly fee is $42.1.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
- [q2] Churn rates by plan are: Basic 38.9%, Standard 36.7%, Premium 36.6%.
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Ranking: Basic, Standard, Premium
- [q3] Churn by signup cohort shows the highest rate in 2024 (39.8%) and the lowest in 2022 (36.7%).
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Ranking: 2024, 2021, 2023, 2022
- [q4] Monthly contracts churn at 48.3% versus 21.9% for annual contracts, a 121% higher churn rate for monthly plans.
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
- [q5] The at‑risk segment comprises 100 customers and experiences a churn rate of 71%.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
- [q6] Customers have an average tenure of 20.8 months (median 19, std 13.25). The mean satisfaction score is 3.42, with 27 customers missing a score.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
- [q7] Average lifetime value is $463 for Basic, $869 for Standard, and $1,817 for Premium, meaning Premium LTV is 292% higher than Basic.
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401545, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic

## Limitations
- The analysis is based on a single snapshot of 749 customers; results may not generalize to the full population.
- Missing satisfaction scores (27 records) could bias the satisfaction summary.
- Churn is treated as a binary flag without timing information, limiting causal inference.
- Lifetime value is calculated from available data and may not capture future revenue or cost variations.

## Conclusion
Churn remains substantial overall, with modest plan‑level differences but a stark contrast between contract types. Recent sign‑ups (2024) show slightly higher churn, and a notable high‑risk segment churns at a very high rate. Lifetime value escalates sharply with plan tier, highlighting the revenue upside of premium offerings. Targeted retention actions—especially for monthly contracts and at‑risk customers—are recommended to reduce churn and protect high‑value revenue.
