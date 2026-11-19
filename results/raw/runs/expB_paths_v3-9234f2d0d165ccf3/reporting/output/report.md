# Customer Churn Analysis Report

The analysis of 749 customers reveals an overall churn rate of 37.7% and highlights notable differences across subscription plans, signup cohorts, and contract types. Monthly contracts churn more than twice as fast as annual contracts, and a high‑risk segment with many support tickets shows a 71% churn rate. Lifetime value varies dramatically by plan, with Premium customers delivering nearly three times the value of Basic customers.

## Key findings
- [q1] The dataset contains 749 customers, with an overall churn rate of 37.7% and an average monthly fee of $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
- [q2] Churn rates differ by plan: Basic 38.9%, Standard 36.7%, Premium 36.6%.
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Ranking: Basic, Standard, Premium
- [q3] Churn by signup cohort shows the highest rate for 2024 (39.8%) and the lowest for 2022 (36.7%).
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Ranking: 2024, 2021, 2023, 2022
- [q4] Customers on Monthly contracts churn at 48.3%, versus 21.9% for Annual contracts, representing a 121.1% increase.
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
  - Derived ratio(churn_rate_monthly_pct, churn_rate_annual_pct): 2.21
- [q5] The identified at‑risk segment comprises 100 customers, with a churn rate of 71%.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
- [q6] Average tenure is 20.8 months (median 19, standard deviation 13.25). Average satisfaction score is 3.42, with 27 customers missing a score.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
- [q7] Average lifetime value is $463.46 for Basic, $868.83 for Standard, and $1,816.78 for Premium, meaning Premium LTV is 292% higher than Basic.
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401546, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic
  - Derived difference(ltv_premium, ltv_basic): 1353.32
  - Derived ratio(ltv_premium, ltv_basic): 3.92

## Limitations
- The churn metric is binary and does not capture timing of churn within the observation window.
- Satisfaction scores are missing for 27 customers, which may bias the average satisfaction estimate.
- Support ticket counts are only a proxy for customer distress and may not reflect all at‑risk behaviors.
- Lifetime value is calculated from available revenue data and assumes no future changes in pricing or usage.

## Conclusion
Churn remains high overall, especially among monthly contract holders and the identified at‑risk segment. Premium customers deliver substantially higher lifetime value, suggesting opportunities to upsell or retain higher‑value segments. Targeted interventions for high‑ticket, low‑satisfaction customers and incentives for annual contracts could reduce churn and improve revenue stability.
