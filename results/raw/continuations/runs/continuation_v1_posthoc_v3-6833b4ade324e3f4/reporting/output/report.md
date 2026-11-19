# Customer Churn Analysis Report

This report analyzes a snapshot of 749 customers to identify churn drivers. The overall churn rate is 37.7%. Key findings indicate that Monthly contracts and an identifiable at-risk segment are the primary drivers of customer loss. Lifetime value is significantly higher for Premium subscribers, and recent signup cohorts show slightly elevated churn rates compared to previous years.

## Key findings
- [q1] The dataset contains 749 customers with an overall churn rate of 37.7% and an average monthly fee of $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
- [q2] Churn rates vary slightly by plan. The Basic plan has the highest churn rate at 38.9%, followed by Standard at 36.7% and Premium at 36.6%.
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Ranking: Basic, Standard, Premium
- [q3] Analyzing signup cohorts, the 2024 cohort has the highest churn rate at 39.8%, while the 2022 cohort has the lowest at 36.7%.
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Ranking: 2024, 2021, 2023, 2022
- [q4] Contract type is a major churn driver. Monthly contracts exhibit a 48.3% churn rate, which is a 121.1% increase compared to the 21.9% churn rate for Annual contracts.
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
- [q5] A specific at-risk segment was identified: 100 customers with high support tickets (>=5) and low satisfaction (<=2). This group has a critical churn rate of 71.0%.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
- [q6] Customer tenure averages 20.8 months (median 19.0) with a standard deviation of 13.2 months. The average satisfaction score is 3.42, though 27 customers have missing satisfaction data.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
- [q7] Lifetime value (LTV) correlates strongly with plan tier. Premium LTV is $1,816.78, which is 292.0% higher than the Basic LTV of $463.46.
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401545, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic

## Limitations
- The dataset is a single snapshot and does not reflect real-time churn dynamics.
- Satisfaction scores are missing for 27 customers (3.6% of the total), which may bias the satisfaction analysis.
- The analysis assumes the 'lifetime_value' field accurately represents customer value; the calculation method for this metric was not verified in this stage.

## Conclusion
To reduce churn, the business should prioritize converting Monthly customers to Annual contracts and focus retention efforts on the identified at-risk segment with high support tickets and low satisfaction. The significantly higher LTV of Premium customers justifies investment in upselling strategies.
