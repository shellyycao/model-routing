# Customer Churn Analysis Report

Analysis of 749 customers reveals an overall churn rate of 37.7%. Monthly-contract customers churn at more than double the rate of annual-contract customers. A high-risk segment of 100 customers (high support tickets, low satisfaction) churns at 71.0%. Premium-plan customers generate nearly 4× the lifetime value of Basic customers, underscoring the revenue importance of retention at the top tier.

## Key findings
- [q1] The dataset contains 749 customers with an overall churn rate of 37.7% and an average monthly fee of $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
- [q2] Churn rates differ modestly across plans: Basic is highest at 38.9%, followed by Standard at 36.7%, and Premium at 36.6%. The spread is narrow (~2.3 percentage points), suggesting plan tier alone is not a strong churn driver.
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Ranking: Basic, Standard, Premium
  - Derived difference(churn_rate_basic_pct, churn_rate_premium_pct): 2.27
- [q3] Churn by signup cohort shows the 2024 cohort is highest at 39.8%, followed by 2021 at 38.0%, 2023 at 37.1%, and 2022 at 36.7%. The 2024 cohort's elevated rate may reflect insufficient onboarding time or product-fit issues for recent signups.
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Ranking: 2024, 2021, 2023, 2022
- [q4] Contract type is a major churn driver. Monthly-contract customers churn at 48.3% versus 21.9% for annual-contract customers — monthly churn is 121.1% higher than annual, meaning monthly customers churn at more than twice the rate.
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
- [q5] 100 customers with 5 or more support tickets and a satisfaction score ≤ 2 form a critical at-risk segment, churning at 71.0% — nearly double the overall rate of 37.7%.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
  - Derived difference(at_risk_churn_rate_pct, churn_rate_pct): 33.35
- [q6] Customer tenure averages 20.8 months (median 19.0, std 13.2), indicating a wide spread of tenures. Mean satisfaction is 3.42 out of 5, with 27 customers missing a satisfaction score.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
- [q7] Lifetime value rises sharply with plan tier: Basic averages $463, Standard $869, and Premium $1,817. Premium LTV is 292.0% higher than Basic, making Premium customer retention the highest-value retention priority.
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401546, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic

## Limitations
- The cleaning stage validation failed, meaning the cleaned dataset may contain residual data quality issues (e.g., duplicates, incorrect type coercions, or improperly handled outliers) that could affect all downstream metrics.
- 27 customers are missing satisfaction scores, which may introduce bias into satisfaction-related metrics and the at-risk segment definition.
- The 2024 cohort has had less time to churn, so its elevated churn rate may partly reflect a shorter observation window rather than a genuine behavioural difference.
- Lifetime value is derived from available fields; if revenue data is incomplete or estimated, LTV comparisons across plans should be treated as indicative rather than definitive.
- No statistical significance testing was performed on group differences (e.g., plan or cohort churn rates), so small differences may not be meaningful.

## Conclusion
The most actionable findings are the contract-type gap (monthly customers churn 121% more than annual) and the at-risk segment (71% churn rate). Prioritising annual-contract conversion and targeted intervention for high-ticket, low-satisfaction customers could materially reduce churn. Given Premium customers deliver 292% more lifetime value than Basic, retention efforts should be weighted toward that tier. The cleaning-stage failure warrants a data quality review before acting on precise figures.
