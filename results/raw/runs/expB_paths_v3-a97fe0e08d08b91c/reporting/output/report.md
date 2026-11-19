# Customer Churn Analysis Report

Analysis of 749 customers reveals an overall churn rate of 37.7%. Monthly-contract customers churn at more than double the rate of annual-contract customers, and a high-risk segment of 100 customers with poor satisfaction and frequent support contacts churns at 71%. Premium-plan customers generate nearly 4× the lifetime value of Basic customers, making retention of that segment especially valuable.

## Key findings
- [q1] The cleaned dataset contains 749 customers. Overall, 37.7% have churned, and the average monthly fee is $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
- [q2] Churn rates differ modestly across plans: Basic is highest at 38.9%, followed by Standard at 36.7%, and Premium at 36.6%. The spread between Basic and Premium is approximately 2.3 percentage points.
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Ranking: Basic, Standard, Premium
  - Derived difference(churn_rate_basic_pct, churn_rate_premium_pct): 2.27
- [q3] Churn rates by signup cohort are broadly similar across years. The 2024 cohort is highest at 39.8%, followed by 2021 at 38.0%, 2023 at 37.1%, and 2022 at 36.7%. No strong monotonic trend is evident.
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Ranking: 2024, 2021, 2023, 2022
- [q4] Contract type is a strong churn driver. Monthly-contract customers churn at 48.3% versus 21.9% for annual-contract customers — monthly churn is 121% higher than annual, representing an increase in relative risk.
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
- [q5] 100 customers meet the at-risk criteria (≥5 support tickets and satisfaction score ≤2). This segment churns at 71.0%, nearly double the overall rate, and warrants immediate intervention.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
  - Derived difference(at_risk_churn_rate_pct, churn_rate_pct): 33.35
- [q6] Customer tenure averages 20.8 months (median 19.0 months, SD 13.2 months), indicating a wide spread. Mean satisfaction score is 3.42 out of 5 across the 722 customers with a non-missing score; 27 customers have no satisfaction record.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
  - Derived difference(customer_count, satisfaction_missing_count): 722.0
- [q7] Lifetime value rises sharply with plan tier: Basic averages $463, Standard $869, and Premium $1,817. Premium LTV is 292% higher than Basic, making Premium customer retention the highest-value retention opportunity.
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401545, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic

## Limitations
- Satisfaction scores are missing for 27 customers (3.6%), which may introduce slight bias in satisfaction-based analyses and at-risk segment sizing.
- Cohort churn rates for 2024 may be understated if some 2024 sign-ups have had insufficient time to churn, making year-over-year cohort comparisons potentially misleading.
- The analysis is based on a single snapshot; without longitudinal tracking, causal relationships (e.g., whether low satisfaction drives churn or vice versa) cannot be established.
- Lifetime value is computed as a mean per plan without controlling for tenure or contract type, so plan-level LTV differences may partly reflect those confounders.

## Conclusion
The most actionable findings are the contract-type gap (monthly customers churn 121% more than annual) and the at-risk segment (71% churn rate among 100 high-ticket, low-satisfaction customers). Prioritising annual-contract conversion and targeted outreach to the at-risk segment could meaningfully reduce churn. Given Premium customers deliver 292% more lifetime value than Basic, protecting Premium retention should be a top strategic priority.
