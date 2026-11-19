# Customer Churn Analysis Report

This report details verified churn metrics for 749 customers. The overall churn rate is 37.7%. Key drivers include contract type, with monthly contracts showing significantly higher churn, and a specific at-risk segment characterized by high support ticket volume and low satisfaction. Lifetime value varies substantially by plan, with Premium customers generating the highest value.

## Key findings
- [q1] The dataset contains 749 customers with an overall churn rate of 37.7% and an average monthly fee of $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
- [q2] Churn rates by plan show Basic customers have the highest churn rate at 38.9%, followed by Standard at 36.7% and Premium at 36.6%.
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Ranking: Basic, Standard, Premium
- [q3] Analyzing churn by signup cohort, the 2024 cohort has the highest churn rate at 39.8%, followed by 2021 (38.0%), 2023 (37.1%), and 2022 (36.7%).
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Ranking: 2024, 2021, 2023, 2022
- [q4] Monthly contract customers experience a churn rate of 48.3%, which is 121.1% higher than the 21.9% rate for Annual contract customers.
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
- [q5] An at-risk segment of 100 customers with high support tickets (≥5) and low satisfaction (≤2) exhibits a churn rate of 71.0%.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
- [q6] Customer tenure averages 20.8 months with a median of 19.0 months and standard deviation of 13.2 months. Average satisfaction is 3.42, though 27 customers lack a satisfaction score.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
- [q7] Lifetime value is highest for Premium customers ($1,816.78), followed by Standard ($868.83) and Basic ($463.46). Premium LTV is 292.0% higher than Basic.
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401545, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic

## Limitations
- Satisfaction scores are missing for 27 customers, which may bias the satisfaction mean.
- The analysis assumes the data is a representative snapshot; temporal trends beyond signup cohorts are not assessed.
- Causality cannot be inferred from this observational data (e.g., the relationship between support tickets and churn).

## Conclusion
Churn is significantly driven by contract type, with monthly subscribers and an identified at-risk segment (high tickets, low satisfaction) showing elevated rates. While Premium customers churn at rates similar to other plans, they deliver nearly 4x the lifetime value of Basic customers. Retention strategies should prioritize converting monthly customers to annual contracts and proactively managing the at-risk segment.
