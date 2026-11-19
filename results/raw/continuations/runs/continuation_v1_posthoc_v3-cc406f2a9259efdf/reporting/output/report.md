# Customer Churn Analysis Report

This report analyzes a snapshot of 749 customers to identify churn drivers. The overall churn rate is 37.7%. Key findings indicate that Monthly contracts and an identified at-risk segment drive significantly higher churn. While churn rates are stable across plans and cohorts, Lifetime Value (LTV) is nearly four times higher for Premium subscribers.

## Key findings
- [q1] The dataset contains 749 customers with an overall churn rate of 37.7% and an average monthly fee of $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
- [q2] Churn rates are similar across plans, with the Basic plan slightly higher at 38.9% compared to Standard at 36.7% and Premium at 36.6%.
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Ranking: Basic, Standard, Premium
- [q3] Churn rates have remained relatively stable across signup cohorts, ranging from 36.7% in 2022 to 39.8% in 2024.
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Ranking: 2024, 2021, 2023, 2022
- [q4] Monthly contracts exhibit a churn rate of 48.3%, which is a 121.1% increase compared to the 21.9% rate for Annual contracts.
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
- [q5] An at-risk segment of 100 customers (those with 5+ support tickets and satisfaction scores of 2 or less) shows a critical churn rate of 71.0%.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
- [q6] Customer tenure averages 20.8 months (median 19.0, std dev 13.2). The average satisfaction score is 3.42, with 27 customers missing this data.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
- [q7] Lifetime Value rises significantly with plan tier: Basic ($463), Standard ($869), and Premium ($1,817). Premium LTV is 292% higher than Basic.
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401545, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic

## Limitations
- The analysis relies on a single snapshot in time and does not track customer behavior longitudinally.
- Satisfaction scores were missing for 27 customers, potentially biasing the satisfaction mean.
- The dataset does not contain demographic details, limiting segmentation depth.

## Conclusion
To reduce churn, the business should prioritize converting Monthly customers to Annual contracts and intervene specifically with the high-support, low-satisfaction segment. Retaining Premium customers is critical given their substantially higher Lifetime Value.
