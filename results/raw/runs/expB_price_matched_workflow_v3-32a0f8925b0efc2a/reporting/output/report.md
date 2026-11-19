# Customer Churn Analysis Report

Analysis of 749 customers reveals an overall churn rate of 37.7%. Monthly-contract customers churn at more than double the rate of annual-contract customers, and a high-risk segment of 100 customers with heavy support usage and low satisfaction churns at 71%. Premium-plan customers generate nearly 4× the lifetime value of Basic customers, making retention of that segment especially valuable.

## Key findings
- [q1] The dataset contains 749 customers with an overall churn rate of 37.7% and an average monthly fee of $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
- [q2] Churn rates differ modestly across plans: Basic is highest at 38.9%, followed by Standard at 36.7%, and Premium at 36.6%. The spread is narrow (~2.3 percentage points), suggesting plan tier alone is not a strong churn driver.
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Ranking: Basic, Standard, Premium
  - Derived difference(churn_rate_basic_pct, churn_rate_premium_pct): 2.27
- [q3] Churn by signup cohort shows the 2024 cohort is highest at 39.8%, followed by 2021 at 38.0%, 2023 at 37.1%, and 2022 at 36.7%. The range is narrow (~3.1 pp), with no clear monotonic trend across years.
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Ranking: 2024, 2021, 2023, 2022
  - Derived difference(churn_rate_cohort_2024_pct, churn_rate_cohort_2022_pct): 3.09
- [q4] Contract type is a strong churn predictor. Monthly-contract customers churn at 48.3% versus 21.9% for annual-contract customers — monthly churn is 121% higher than annual, representing the single largest structural risk factor identified.
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
- [q5] 100 customers meet the at-risk criteria (≥5 support tickets and satisfaction score ≤2). This segment churns at 71.0% — nearly double the overall rate — and warrants immediate intervention.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
  - Derived difference(at_risk_churn_rate_pct, churn_rate_pct): 33.35
- [q6] Average customer tenure is 20.8 months (median 19.0, SD 13.2), indicating a wide spread in customer longevity. Mean satisfaction among the 722 customers with a score is 3.4 out of 5; 27 customers have a missing satisfaction score.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
  - Derived difference(customer_count, satisfaction_missing_count): 722.0
- [q7] Mean lifetime value rises sharply with plan tier: Basic $463, Standard $869, Premium $1,817. Premium LTV is 292% higher than Basic, making Premium customer retention disproportionately valuable to revenue.
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401545, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic

## Limitations
- The 2024 cohort likely contains customers who signed up recently and have had less time to churn, which may inflate or deflate that cohort's observed churn rate relative to mature cohorts.
- 27 customers (3.6%) have missing satisfaction scores; these are excluded from satisfaction-based metrics and the at-risk segment filter, potentially understating the at-risk population.
- The analysis is cross-sectional (a single snapshot); causal relationships between plan, contract type, and churn cannot be established without longitudinal or experimental data.
- Lifetime value is a mean and may be skewed by outliers within each plan tier; median LTV was not computed and could provide a more robust comparison.

## Conclusion
The most actionable findings are the contract-type gap (monthly customers churn 121% more than annual) and the at-risk segment (71% churn rate among 100 high-ticket, low-satisfaction customers). Prioritising annual-contract conversion and targeted retention outreach for at-risk customers — especially those on Premium plans given their 292% higher LTV — offers the clearest near-term opportunity to reduce revenue loss.
