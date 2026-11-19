# Customer Churn Analysis Report

Analysis of 749 customers reveals an overall churn rate of 37.7%. Monthly-contract customers churn at more than double the rate of annual-contract customers, and a high-risk segment of 100 customers with poor satisfaction and frequent support tickets churns at 71%. Premium-plan customers generate nearly 4× the lifetime value of Basic customers, making retention of that segment especially critical.

## Key findings
- [q1] The dataset contains 749 customers with an overall churn rate of 37.7% and an average monthly fee of $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
- [q2] Churn rates differ modestly across plans: Basic is highest at 38.9%, followed by Standard at 36.7%, and Premium at 36.6%. The spread between Basic and Premium is approximately 2.3 percentage points.
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Ranking: Basic, Standard, Premium
  - Derived difference(churn_rate_basic_pct, churn_rate_premium_pct): 2.27
- [q3] Churn rates by signup cohort show the 2024 cohort is highest at 39.8%, followed by 2021 at 38.0%, 2023 at 37.1%, and 2022 at 36.7%. The variation across cohorts is narrow (roughly 3 percentage points), suggesting no strong secular trend.
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Ranking: 2024, 2021, 2023, 2022
  - Derived difference(churn_rate_cohort_2024_pct, churn_rate_cohort_2022_pct): 3.09
- [q4] Contract type is a strong churn driver. Monthly-contract customers churn at 48.3% versus 21.9% for annual-contract customers — monthly churn is 121% higher than annual, a clear increase in risk for month-to-month subscribers.
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
- [q5] 100 customers with 5 or more support tickets and a satisfaction score of 2 or below form a high-risk segment with a churn rate of 71.0% — nearly double the overall rate.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
  - Derived difference(at_risk_churn_rate_pct, churn_rate_pct): 33.35
- [q6] Customer tenure averages 20.8 months (median 19.0, std 13.2), indicating a wide spread in customer longevity. Mean satisfaction is 3.4 out of 5; 27 customers have a missing satisfaction score, which may slightly bias this average.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
- [q7] Mean lifetime value rises sharply by plan: Basic $463, Standard $869, Premium $1,817. Premium LTV is 292% higher than Basic, making Premium customer retention the highest-value retention priority.
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401545, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic

## Limitations
- The 2024 cohort likely contains fewer customers with shorter observable tenure, which may inflate its churn rate relative to older cohorts.
- 27 customers (3.6%) have missing satisfaction scores; the reported satisfaction mean excludes these records and may not reflect the full customer base.
- Lifetime value is computed as a mean per plan and does not account for tenure heterogeneity within plans, potentially overstating or understating LTV for specific sub-groups.
- The at-risk segment definition (tickets ≥ 5 AND satisfaction ≤ 2) is a threshold-based heuristic; customers just below these thresholds may also be at elevated risk.
- The dataset is a single snapshot; causal relationships (e.g., whether low satisfaction drives churn or vice versa) cannot be established from this cross-sectional analysis.

## Conclusion
Churn is broad-based at 37.7% but is strongly amplified by two factors: monthly contracts (48.3% churn vs. 21.9% for annual) and poor service experience (71% churn in the high-ticket, low-satisfaction segment). Immediate priorities should be converting monthly subscribers to annual plans and intervening with the 100 identified at-risk customers. Given that Premium customers deliver 292% more lifetime value than Basic customers, targeted retention programmes for Premium subscribers will yield the greatest financial return.
