# Customer Churn Analysis Report

This report analyzes a snapshot of 749 customers, revealing an overall churn rate of 37.7%. Key drivers of churn include contract type, with monthly subscribers exhibiting significantly higher attrition, and a distinct at-risk segment characterized by high support ticket volume and low satisfaction. Lifetime value scales substantially with plan tier.

## Key findings
- [q1] The dataset contains 749 customers with an overall churn rate of 37.7% and an average monthly fee of $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
- [q2] Churn rates are similar across plans, ranging from 36.6% (Premium) to 38.9% (Basic).
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Ranking: Basic, Standard, Premium
- [q3] Churn rates remain stable across signup cohorts, fluctuating between 36.7% (2022) and 39.8% (2024).
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Ranking: 2024, 2021, 2023, 2022
- [q4] Monthly contracts show a churn rate of 48.3%, which is 121.1% higher than the 21.9% rate for Annual contracts.
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
  - Derived pct_change(churn_rate_monthly_pct, churn_rate_annual_pct): 121.1
- [q5] An at-risk segment of 100 customers (high support tickets, low satisfaction) exhibits a critical churn rate of 71.0%.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
- [q6] Customer tenure averages 20.8 months (median 19.0, std dev 13.2). Average satisfaction is 3.42, with 27 missing scores.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
- [q7] Lifetime value is highest for Premium customers ($1,817), which is 292.0% higher than Basic ($463).
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401545, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic
  - Derived pct_change(ltv_premium, ltv_basic): 292.0

## Limitations
- The analysis is based on a single snapshot and does not track customer behavior over time.
- Satisfaction scores were missing for 27 customers, potentially biasing the at-risk segment analysis.
- Causal relationships (e.g., whether high support tickets cause churn) cannot be determined from this observational data.

## Conclusion
To reduce churn, strategies should focus on converting monthly subscribers to annual contracts and prioritizing retention efforts for the identified at-risk segment. The significant LTV of Premium customers justifies investment in their acquisition and retention.
