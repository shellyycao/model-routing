# Customer Churn Analysis Report

The analysis of 749 customers reveals an overall churn of 37.7% and highlights higher churn among monthly contracts and the at‑risk segment. Churn varies modestly across plans, with the Basic plan slightly higher. Recent signup cohorts (2024) show the highest churn. Lifetime value is strongest for Premium customers, delivering nearly three times the value of Basic customers.

## Key findings
- [q1] The dataset contains 749 customers, with an overall churn rate of 37.65% and an average monthly fee of $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
- [q2] Churn rates differ by plan, highest for Basic (38.87%), followed by Standard (36.68%) and Premium (36.60%).
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Ranking: Basic, Standard, Premium
- [q3] Churn by signup cohort is highest in 2024 (39.83%), then 2021 (38.02%), 2023 (37.05%) and 2022 (36.74%).
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Ranking: 2024, 2021, 2023, 2022
- [q4] Monthly contracts churn at 48.32% versus 21.85% for Annual contracts, a 121.1% higher churn rate for monthly plans.
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
- [q5] The at‑risk segment (≥5 support tickets and satisfaction ≤2) includes 100 customers (13.35% of the base) and experiences a churn rate of 71%.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
  - Derived share(at_risk_customer_count, customer_count): 13.351135513351135
- [q6] Customers have an average tenure of 20.81 months (median 19, std dev 13.25) and an average satisfaction score of 3.42, with 27 missing satisfaction entries.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
- [q7] Average lifetime value is $463.46 for Basic, $868.83 for Standard, and $1,816.78 for Premium, with Premium delivering a 292.0% higher LTV than Basic.
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401545, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic

## Limitations
- The analysis relies on a single snapshot; churn may be influenced by factors not captured in the data.
- Missing satisfaction scores (27 customers) could bias the satisfaction summary.
- At‑risk segment definition is based on arbitrary thresholds and may not capture all vulnerable customers.

## Conclusion
Overall churn is moderate but spikes for monthly contracts and the identified at‑risk group, suggesting targeted retention efforts. Premium customers generate substantially higher lifetime value, reinforcing the business case for upselling. Monitoring cohort trends and improving satisfaction data completeness will enhance future analyses.
