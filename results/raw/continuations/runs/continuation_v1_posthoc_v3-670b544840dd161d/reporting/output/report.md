# Customer Churn Analysis Report

Analysis of 749 customers reveals an overall churn rate of 37.7%. Monthly-contract customers churn at more than double the rate of annual-contract customers. A high-risk segment of 100 customers with heavy support usage and low satisfaction churns at 71.0%. Premium-plan customers generate lifetime value nearly 4× that of Basic customers, underscoring the revenue impact of retaining higher-tier subscribers.

## Key findings
- [q1] The dataset contains 749 customers with an overall churn rate of 37.7% and a mean monthly fee of $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
- [q2] Churn rates differ modestly across plans: Basic is highest at 38.9%, followed by Standard at 36.7%, and Premium at 36.6%. The spread between Basic and Premium is approximately 2.3 percentage points.
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Ranking: Basic, Standard, Premium
  - Derived difference(churn_rate_basic_pct, churn_rate_premium_pct): 2.27
- [q3] Churn by signup cohort shows the 2024 cohort is highest at 39.8%, followed by 2021 at 38.0%, 2023 at 37.1%, and 2022 at 36.7%. The 2024 cohort's elevated rate may reflect insufficient tenure to build loyalty.
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Ranking: 2024, 2021, 2023, 2022
- [q4] Contract type is a strong churn driver. Monthly-contract customers churn at 48.3% versus 21.9% for annual-contract customers — monthly churn is 121.1% higher than annual, representing an increase in churn risk for month-to-month subscribers.
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
- [q5] 100 customers meet the at-risk criteria (≥5 support tickets and satisfaction score ≤2). This segment churns at 71.0%, nearly double the overall rate, making it the highest-priority intervention target.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
  - Derived difference(at_risk_churn_rate_pct, churn_rate_pct): 33.35
- [q6] Customer tenure averages 20.8 months (median 19.0, SD 13.2), indicating a wide spread in customer longevity. Mean satisfaction is 3.4 out of 5; 27 customers have a missing satisfaction score, limiting satisfaction-based analyses.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
- [q7] Mean lifetime value rises sharply by plan: Basic $463, Standard $869, Premium $1,817. Premium LTV is 292.0% higher than Basic, confirming that retaining Premium customers delivers outsized revenue value.
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401545, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic

## Limitations
- 27 customers have missing satisfaction scores, which may introduce bias into satisfaction-based segmentation and the at-risk filter.
- The 2024 cohort has shorter observable tenure than earlier cohorts, so its elevated churn rate may partly reflect truncated observation windows rather than a genuine behavioural difference.
- Lifetime value is computed as a mean per plan and does not account for discounts, promotions, or variable usage fees that could affect true revenue.
- The at-risk segment definition (tickets ≥5 and satisfaction ≤2) is a heuristic threshold; alternative cut-offs could materially change segment size and churn rate.
- The dataset is a single snapshot; longitudinal tracking would be needed to confirm causal relationships between contract type, satisfaction, and churn.

## Conclusion
Churn is elevated across all segments at ~37.7%, but contract type and support experience are the clearest differentiators. Converting monthly subscribers to annual contracts and proactively addressing the 100 at-risk customers (71.0% churn rate) represent the highest-impact near-term interventions. Given Premium customers' LTV of $1,817 — 292% above Basic — targeted retention investment for Premium subscribers is strongly justified.
