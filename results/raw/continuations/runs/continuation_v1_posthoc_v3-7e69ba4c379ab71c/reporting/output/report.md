# Customer Churn Analysis Report

This report analyzes a snapshot of 749 customers to identify churn drivers. The overall churn rate is 37.7%. Key findings indicate that contract type is the strongest predictor of churn, with monthly contracts associated with significantly higher attrition. An at-risk segment of 100 customers with high support tickets and low satisfaction shows a critical churn rate of 71.0%. Lifetime value scales substantially with plan tier.

## Key findings
- [q1] The dataset contains 749 customers with an overall churn rate of 37.7% and an average monthly fee of $42.1.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
- [q2] Churn rates are relatively stable across plans, ranging from 36.6% (Premium) to 38.9% (Basic). The Basic plan has the highest churn rate.
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Ranking: Basic, Standard, Premium
- [q3] Churn rates by signup cohort show minor variation, with the 2024 cohort having the highest rate at 39.8%.
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Ranking: 2024, 2021, 2023, 2022
- [q4] Contract type has a major impact on retention. Monthly contracts have a 48.3% churn rate compared to 21.9% for annual contracts, representing a 121.1% increase.
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
- [q5] An at-risk segment of 100 customers with high support tickets and low satisfaction exhibits a churn rate of 71.0%.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
- [q6] Customer tenure averages 20.8 months with a standard deviation of 13.2 months. The average satisfaction score is 3.4, with 27 customers missing a score.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
- [q7] Lifetime value increases significantly with plan tier. Premium customers have an average LTV of $1,817, which is 292.0% higher than the Basic plan LTV of $463.
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401545, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic

## Limitations
- The analysis is based on a single snapshot and does not track individual customer behavior over time.
- Satisfaction scores are missing for 27 customers, potentially biasing the satisfaction mean.
- Causality cannot be inferred; observed associations (e.g., contract type and churn) may be influenced by unobserved factors.

## Conclusion
To reduce churn, the business should prioritize converting monthly customers to annual contracts and intervene with the high-risk segment showing low satisfaction. While plan tier has a minor effect on churn rates, it significantly impacts lifetime value, suggesting retention efforts across all plans remain valuable.
