# Customer Churn Analysis Report

This report presents the findings from the analysis of customer churn data. Key metrics include overall churn rate, churn rates by plan, signup cohort, and contract type, identification of at-risk customers, and lifetime value by plan. The analysis reveals significant insights into customer behavior and potential areas for improvement.

## Key findings
- [q1] The overall customer count is 749, with a churn rate of 37.65% and an average monthly fee of $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
- [q2] Churn rates vary by plan: Basic at 38.87%, Standard at 36.68%, and Premium at 36.60%.
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Ranking: Basic, Standard, Premium
- [q3] Churn rates by signup cohort are as follows: 2021 at 38.02%, 2022 at 36.74%, 2023 at 37.05%, and 2024 at 39.83%.
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Ranking: 2024, 2021, 2023, 2022
- [q4] Monthly contracts have a significantly higher churn rate (48.32%) compared to annual contracts (21.85%), with a 121.11% increase.
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
- [q5] There are 100 at-risk customers with a high churn rate of 71.0%.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
- [q6] The mean tenure is 20.81 months, the median is 19.0 months, and the standard deviation is 13.25 months. The mean satisfaction score is 3.42, with 27 missing values.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
- [q7] Lifetime value (LTV) by plan is as follows: Basic at $463.46, Standard at $868.83, and Premium at $1816.78. The Premium plan shows a 292.01% increase in LTV compared to the Basic plan.
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401546, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic

## Limitations
- The analysis is based on a snapshot of customer data and may not capture all dynamic changes over time.
- The satisfaction score has missing values, which may affect the accuracy of related metrics.
- The at-risk segment is defined by specific criteria and may not encompass all potential at-risk customers.

## Conclusion
The analysis provides valuable insights into customer churn, highlighting areas for potential improvement such as contract types and customer satisfaction. Addressing the identified at-risk segment and enhancing customer satisfaction could help reduce churn rates and improve overall customer retention.
