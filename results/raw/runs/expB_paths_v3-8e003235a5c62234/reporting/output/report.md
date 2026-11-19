# Customer Churn Analysis Report

Analysis of 749 customers reveals an overall churn rate of 37.7%. Monthly-contract customers churn at more than double the rate of annual-contract customers. A high-risk segment of 100 customers (high support tickets, low satisfaction) churns at 71%. Premium-plan customers deliver nearly 4× the lifetime value of Basic customers, underscoring the revenue importance of retention at the top tier.

## Key findings
- [q1] The dataset contains 749 customers with an overall churn rate of 37.7% and an average monthly fee of $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
- [q2] Churn rates differ modestly across plans: Basic is highest at 38.9%, followed by Standard at 36.7%, and Premium at 36.6%. The spread between Basic and Premium is approximately 2.3 percentage points.
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Ranking: Basic, Standard, Premium
  - Derived difference(churn_rate_basic_pct, churn_rate_premium_pct): 2.27
- [q3] Cohort churn rates are broadly stable across signup years but the 2024 cohort is highest at 39.8%, followed by 2021 at 38.0%, 2023 at 37.1%, and 2022 at 36.7%. No sustained downward trend is evident.
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Ranking: 2024, 2021, 2023, 2022
- [q4] Contract type is a strong churn driver. Monthly-contract customers churn at 48.3% versus 21.9% for Annual customers — Monthly churn is 121% higher than Annual, indicating that longer commitments substantially reduce attrition.
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
- [q5] 100 customers meet the at-risk criteria (≥5 support tickets and satisfaction score ≤2). This segment churns at 71.0%, nearly double the overall rate, making it the highest-priority retention target.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
  - Derived difference(at_risk_churn_rate_pct, churn_rate_pct): 33.35
- [q6] Customer tenure averages 20.8 months (median 19.0, SD 13.2), indicating a wide spread. Mean satisfaction is 3.4 out of 5, with 27 customers missing a satisfaction score.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
- [q7] Mean lifetime value rises sharply by plan: Basic $463, Standard $869, Premium $1,817. Premium LTV is 292% higher than Basic, confirming that retaining Premium customers is disproportionately valuable.
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401545, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic

## Limitations
- The 2024 cohort may be incomplete (customers signed up later in the year have had less time to churn), which could inflate or deflate its observed churn rate.
- 27 customers (3.6%) are missing satisfaction scores; their exclusion from satisfaction-based analyses may introduce a small bias if missingness is non-random.
- Lifetime value is computed from available data fields and may not capture all revenue streams (e.g., add-ons, discounts), so absolute LTV figures should be treated as indicative.
- The at-risk segment filter uses fixed thresholds (tickets ≥5, satisfaction ≤2); alternative thresholds could change segment size and churn rate.
- The dataset is a single snapshot; causal relationships (e.g., whether low satisfaction causes churn) cannot be established from cross-sectional data alone.

## Conclusion
Churn is elevated across all segments at ~37.7%, but contract type and customer health signals are the clearest levers. Migrating monthly customers to annual contracts and intervening early with the 100 at-risk customers (71% churn rate) represent the highest-impact near-term actions. Given Premium customers generate 292% more lifetime value than Basic, targeted retention investment at the Premium tier offers the greatest financial return.
