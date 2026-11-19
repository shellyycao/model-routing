# Customer Churn Analysis Report

This report analyzes a snapshot of 749 customers to understand churn dynamics. The overall churn rate is 37.7%. Key drivers include contract type, with monthly subscribers showing significantly higher churn, and a distinct at-risk segment characterized by high support ticket volume and low satisfaction. Lifetime value scales substantially with plan tier.

## Key findings
- [q1] The dataset contains 749 customers. The overall churn rate is 37.7%, and the average monthly fee is $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
- [q2] Churn rates are similar across plans, ranging from 36.6% (Premium) to 38.9% (Basic). Basic plan customers have the highest churn rate.
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Ranking: Basic, Standard, Premium
- [q3] Churn rates have remained relatively stable across signup cohorts from 2021 to 2023 (around 37%), with a slight increase to 39.8% in the 2024 cohort.
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Ranking: 2024, 2021, 2023, 2022
- [q4] Monthly contract customers churn at a rate of 48.3%, which is 121.1% higher than the 21.9% rate for Annual contract customers.
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
- [q5] An at-risk segment of 100 customers with high support tickets (>=5) and low satisfaction (<=2) exhibits a churn rate of 71.0%.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
- [q6] Customer tenure averages 20.8 months (median 19.0) with a standard deviation of 13.2 months. Average satisfaction is 3.42, with 27 missing scores.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
- [q7] Average Lifetime Value (LTV) is highest for Premium customers ($1,816.78), followed by Standard ($868.83) and Basic ($463.46). Premium LTV is 292.0% higher than Basic LTV.
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401545, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic

## Limitations
- The analysis is based on a single snapshot and does not reflect real-time changes.
- Satisfaction scores were missing for 27 customers, potentially biasing the average satisfaction metric.
- Causality cannot be inferred; observed associations (e.g., between contract type and churn) may be influenced by unobserved factors.

## Conclusion
To reduce churn, the business should prioritize converting monthly subscribers to annual contracts and address the high-churn at-risk segment through targeted retention strategies. The significant LTV gap between Basic and Premium plans suggests that upselling initiatives could drive substantial revenue growth.
