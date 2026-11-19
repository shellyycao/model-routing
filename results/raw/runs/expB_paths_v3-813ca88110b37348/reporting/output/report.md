# Customer Churn Analysis Report

The customer base consists of 749 accounts with an overall churn rate of 37.7% and an average monthly fee of $42.11. Churn varies modestly across plans, rises for newer signup cohorts, and is markedly higher for month‑to‑month contracts. A high‑risk segment (5+ support tickets and low satisfaction) shows a 71% churn rate. Lifetime value is strongest for Premium customers, nearly three times that of Basic.

## Key findings
- [q1] The dataset contains 749 customers. Overall churn rate is 37.7%, and the average monthly fee is $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
- [q2] Churn rates differ by plan: Basic 38.9%, Standard 36.7%, Premium 36.6%.
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Ranking: Basic, Standard, Premium
- [q3] Churn by signup cohort is highest for 2024 (39.8%) and lowest for 2022 (36.7%).
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Ranking: 2024, 2021, 2023, 2022
- [q4] Monthly contracts churn at 48.3% versus 21.9% for annual contracts, a 121% increase and a 26.5‑point absolute gap.
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
  - Derived difference(churn_rate_monthly_pct, churn_rate_annual_pct): 26.467843015245126
- [q5] The at‑risk segment (≥5 support tickets and satisfaction ≤2) includes 100 customers, with a churn rate of 71%.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
- [q6] Average tenure is 20.8 months (median 19, std 13.25). Average satisfaction among respondents is 3.42, with 27 customers missing a score.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
- [q7] Lifetime value averages are $463.46 for Basic, $868.83 for Standard, and $1,816.78 for Premium. Premium LTV is 292% higher than Basic, representing a $1,353.32 difference.
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401546, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic
  - Derived difference(ltv_premium, ltv_basic): 1353.3203533678554

## Limitations
- The cleaning stage failed, so residual data quality issues (e.g., duplicate rows, inconsistent formats) may remain.
- Satisfaction scores are missing for 27 customers, potentially biasing the satisfaction summary.
- Churn is measured at a single snapshot; it does not capture future behavior or reasons behind churn.

## Conclusion
Churn is moderate overall but spikes for month‑to‑month contracts and the most recent signup cohort. The Premium plan delivers substantially higher lifetime value, while the identified at‑risk segment warrants targeted retention efforts. Improving data cleaning and enriching satisfaction data will sharpen future analyses.
