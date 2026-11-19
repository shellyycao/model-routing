# Customer Churn Analysis Report

The analysis of 749 customers reveals an overall churn rate of 37.7% with notable variations across plans, contract types, and signup cohorts. Monthly contracts churn more than twice as fast as annual contracts. A high‑risk segment (customers with many support tickets and low satisfaction) shows a 71% churn rate. Lifetime value differs dramatically by plan, with Premium customers delivering roughly three times the LTV of Basic customers.

## Key findings
- [q1] The dataset contains 749 customers, with an overall churn rate of 37.7% and an average monthly fee of $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
- [q2] Churn rates differ by plan: Basic 38.9%, Standard 36.7%, Premium 36.6%.
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Ranking: Basic, Standard, Premium
- [q3] Cohort churn rates (2021‑2024) range from 36.7% to 39.8%, with the 2024 cohort highest at 39.8%.
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Ranking: 2024, 2021, 2023, 2022
- [q4] Monthly contracts churn at 48.3% versus 21.9% for annual contracts, a 121.1% higher churn rate.
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
- [q5] The at‑risk segment comprises 100 customers and experiences a churn rate of 71%.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
- [q6] Average tenure is 20.8 months (median 19, standard deviation 13.25). Average satisfaction score is 3.42, with 27 customers missing a score.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
- [q7] Mean lifetime value is $463.46 for Basic, $868.83 for Standard, and $1,816.78 for Premium, representing a 292% higher LTV for Premium versus Basic.
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401545, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic

## Limitations
- The analysis is based on a single snapshot of customers; churn may evolve over time.
- 27 customers have missing satisfaction scores, which could bias the satisfaction summary.
- Churn is defined as a binary flag without distinguishing voluntary vs involuntary churn.
- Support ticket counts and satisfaction scores are self‑reported and may not capture all at‑risk behavior.

## Conclusion
Overall churn is high at 37.7%, especially among monthly contract holders and the recent 2024 signup cohort. Plan type influences churn modestly, while lifetime value varies dramatically, with Premium customers delivering substantially higher revenue. Targeted interventions for the identified at‑risk segment and a focus on converting customers to annual contracts could reduce churn and improve profitability.
