# Customer Churn Analysis Report

The analysis of 749 customers reveals an overall churn rate of 37.65% and highlights key differences across subscription plans, signup cohorts, and contract types. Monthly contracts experience markedly higher churn than annual contracts. An at‑risk segment (high support tickets, low satisfaction) shows a 71% churn rate. Lifetime value varies strongly by plan, with Premium customers delivering nearly three times the value of Basic customers. These insights inform retention strategies and product pricing decisions.

## Key findings
- [q1] The dataset contains 749 customers, with an overall churn rate of 37.65% and an average monthly fee of $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502, avg_monthly_fee=42.106155
- [q2] Churn rates differ by plan: Basic 38.87%, Standard 36.68%, Premium 36.60%.
  - Reported values: churn_rate_basic_pct=38.872404, churn_rate_standard_pct=36.679537, churn_rate_premium_pct=36.601307
  - Ranking: Basic, Standard, Premium
- [q3] Churn by signup cohort shows the highest churn for the 2024 cohort (39.83%) and the lowest for the 2022 cohort (36.74%).
  - Reported values: churn_rate_cohort_2021_pct=38.020833, churn_rate_cohort_2022_pct=36.744186, churn_rate_cohort_2023_pct=37.053571, churn_rate_cohort_2024_pct=39.830508
  - Ranking: 2024, 2021, 2023, 2022
- [q4] Customers on Monthly contracts churn at 48.32% versus 21.85% for Annual contracts, a 121.1% higher churn rate for Monthly contracts.
  - Reported values: churn_rate_monthly_pct=48.322148, churn_rate_annual_pct=21.854305, churn_monthly_vs_annual_change_pct=121.110433
  - Direction: increase
  - Derived difference(churn_rate_monthly_pct, churn_rate_annual_pct): 26.467843
- [q5] The at‑risk segment (≥5 support tickets and satisfaction ≤2) comprises 100 customers, with a churn rate of 71%.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
  - Derived share(at_risk_customer_count, customer_count): 13.3511355
- [q6] Tenure averages 20.81 months (median 19, std dev 13.25). Average satisfaction score is 3.42, with 27 customers missing a score.
  - Reported values: tenure_mean=20.810414, tenure_median=19.0, tenure_std=13.247393, satisfaction_mean=3.416898, satisfaction_missing_count=27.0
- [q7] Average lifetime value is $463.46 for Basic, $868.83 for Standard, and $1,816.78 for Premium plans; Premium LTV is 292.0% higher than Basic.
  - Reported values: ltv_basic=463.457359, ltv_standard=868.830154, ltv_premium=1816.777712, premium_vs_basic_ltv_change_pct=292.005365
  - Direction: increase
  - Ranking: Premium, Standard, Basic
  - Derived difference(ltv_premium, ltv_basic): 1353.320353

## Limitations
- The analysis is based on a snapshot of customers; churn may be influenced by factors not captured in the data (e.g., market conditions).
- Satisfaction scores are missing for 27 customers, which could bias the satisfaction summary.
- Support ticket counts and satisfaction scores are self‑reported and may not fully reflect customer sentiment.

## Conclusion
Churn remains substantial, especially among monthly contract holders and the identified at‑risk segment. Targeted retention initiatives—such as improving support for high‑ticket users and incentivizing annual contracts—could reduce churn. The strong LTV advantage of Premium plans suggests opportunities to upsell, while the modest differences in churn across plans indicate that pricing alone is not driving attrition.
