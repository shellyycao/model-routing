# Customer Churn Analysis Report

This report analyzes a snapshot of 749 customers, revealing an overall churn rate of 37.7%. The most critical risk factors identified are monthly contracts, which show a 121% higher churn rate than annual contracts, and a specific at-risk segment with high support ticket volume and low satisfaction, exhibiting a 71% churn rate. Lifetime value scales significantly with plan tier, with Premium customers generating nearly four times the value of Basic customers.

## Key findings
- [q1] The dataset contains 749 customers with an overall churn rate of 37.7% and an average monthly fee of $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
- [q2] Churn rates across plans are relatively consistent, ranging from 36.6% (Premium) to 38.9% (Basic). The Basic plan experiences the highest churn.
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Ranking: Basic, Standard, Premium
- [q3] Churn rates by signup cohort show slight variation, with the 2024 cohort having the highest churn rate at 39.8% and the 2022 cohort the lowest at 36.7%.
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Ranking: 2024, 2021, 2023, 2022
- [q4] Monthly contracts exhibit a churn rate of 48.3%, which is 121.1% higher than the 21.9% rate for Annual contracts.
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
- [q5] An at-risk segment of 100 customers (defined as having 5+ support tickets and satisfaction score ≤ 2) shows a critical churn rate of 71.0%.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
- [q6] Customer tenure averages 20.8 months (median 19.0, std dev 13.2). The average satisfaction score is 3.42, with 27 records missing a score.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
- [q7] Lifetime value increases significantly with plan tier: Basic averages $463, Standard $869, and Premium $1,817. Premium LTV is 292.0% higher than Basic.
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401545, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic

## Limitations
- The analysis is based on a single snapshot and does not capture temporal trends or causality.
- Satisfaction scores were missing for 27 customers, potentially biasing the average satisfaction metric.
- Lifetime value calculations depend on the accuracy of the derived 'lifetime_value' column provided in the cleaned dataset.

## Conclusion
To reduce churn, immediate focus should be placed on converting monthly contract customers to annual plans and addressing the high-churn at-risk segment through targeted retention strategies. While Basic plans have slightly higher churn rates, the significantly higher LTV of Premium customers underscores the importance of retention efforts across all tiers.
