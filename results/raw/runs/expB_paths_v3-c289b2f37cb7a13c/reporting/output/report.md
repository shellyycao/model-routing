# Customer Churn Analysis Report

The analysis of 661 customers reveals an overall churn rate of 36.8% and highlights significant differences across plans, contract types, and signup cohorts. Monthly contracts experience markedly higher churn than annual contracts. A high‑risk segment with many support tickets and low satisfaction churns at 73.2%. Lifetime value varies widely by plan, with premium customers delivering over four times the value of basic customers.

## Key findings
- [q1] The dataset contains 661 customers, with an overall churn rate of 36.8% and an average monthly fee of $42.02.
  - Reported values: customer_count=661.0, churn_rate_pct=36.7624810892587, avg_monthly_fee=42.01723146747352
- [q2] Churn rates differ by plan: Basic 38.4%, Standard 35.7%, Premium 35.1%.
  - Reported values: churn_rate_basic_pct=38.38383838383838, churn_rate_standard_pct=35.65217391304348, churn_rate_premium_pct=35.07462686567165
  - Ranking: Basic, Standard, Premium
- [q3] Churn by signup cohort shows the highest rates in 2022 (37.2%) and 2023 (37.1%), followed by 2021 (36.9%) and lowest in 2024 (35.0%).
  - Reported values: churn_rate_cohort_2021_pct=36.93181818181818, churn_rate_cohort_2022_pct=37.17277486910995, churn_rate_cohort_2023_pct=37.11340206185567, churn_rate_cohort_2024_pct=35.0
  - Ranking: 2022, 2023, 2021, 2024
- [q4] Customers on monthly contracts churn at 47.6%, versus 20.9% for annual contracts, a difference of 26.7 percentage points, representing a 127.7% higher churn rate for monthly contracts.
  - Reported values: churn_rate_monthly_pct=47.58269720101781, churn_rate_annual_pct=20.8955223880597, churn_monthly_vs_annual_change_pct=127.7171937477281
  - Direction: increase
  - Derived difference(churn_rate_monthly_pct, churn_rate_annual_pct): 26.68717481295811
- [q5] The at‑risk segment (≥5 support tickets and satisfaction ≤2) comprises 71 customers, of whom 73.2% have churned.
  - Reported values: at_risk_customer_count=71.0, at_risk_churn_rate_pct=73.23943661971832
- [q6] Average tenure is 21.2 months (median 19, std dev 13.3). Average satisfaction among respondents is 3.43, with 116 customers missing a score.
  - Reported values: tenure_mean=21.193645990922843, tenure_median=19.0, tenure_std=13.292354450514928, satisfaction_mean=3.4275229357798165, satisfaction_missing_count=116.0
- [q7] Average lifetime value is $465 for Basic, $888 for Standard, and $1,888 for Premium plans. Premium LTV is about 4.06 times the Basic LTV, a 305.8% increase.
  - Reported values: ltv_basic=465.21272727272725, ltv_standard=888.2470434782609, ltv_premium=1887.7605223880596, premium_vs_basic_ltv_change_pct=305.78436739143103
  - Direction: increase
  - Ranking: Premium, Standard, Basic
  - Derived ratio(ltv_premium, ltv_basic): 4.06

## Limitations
- The cleaning stage failed, so the underlying data may contain inconsistencies or errors that were not corrected.
- Analysis relied on simple aggregations without adjusting for potential confounders (e.g., customer age, region).
- Missing satisfaction scores (116 customers) could bias the satisfaction summary.

## Conclusion
Churn is substantial overall and especially high for monthly contracts. Plan tiering shows modest churn differences, while premium customers deliver far higher lifetime value. Targeting the identified at‑risk segment and encouraging annual contracts could reduce churn and improve revenue.
