# Customer Churn Analysis Report

Analysis of 749 customers reveals an overall churn rate of 37.7%. Monthly-contract customers churn at more than double the rate of annual-contract customers, and a high-risk segment of 100 customers with poor satisfaction and frequent support tickets churns at 71.0%. Premium-plan customers generate nearly 4× the lifetime value of Basic customers, making retention investment in that tier especially valuable.

## Key findings
- [q1] The cleaned dataset contains 749 customers with an overall churn rate of 37.7% and an average monthly fee of $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502, avg_monthly_fee=42.106155
- [q2] Churn rates differ modestly across plans: Basic is highest at 38.9%, followed by Standard at 36.7%, and Premium at 36.6%. The spread is narrow (~2.3 percentage points), suggesting plan tier alone is not a strong churn driver.
  - Reported values: churn_rate_basic_pct=38.872404, churn_rate_standard_pct=36.679537, churn_rate_premium_pct=36.601307
  - Ranking: Basic, Standard, Premium
  - Derived difference(churn_rate_basic_pct, churn_rate_premium_pct): 2.27
- [q3] Churn by signup cohort shows the 2024 cohort is highest at 39.8%, followed by 2021 at 38.0%, 2023 at 37.1%, and 2022 at 36.7%. The 2024 cohort's elevated rate may reflect insufficient onboarding time, but the overall range is narrow.
  - Reported values: churn_rate_cohort_2021_pct=38.020833, churn_rate_cohort_2022_pct=36.744186, churn_rate_cohort_2023_pct=37.053571, churn_rate_cohort_2024_pct=39.830508
  - Ranking: 2024, 2021, 2023, 2022
- [q4] Contract type is the strongest churn predictor: Monthly customers churn at 48.3% versus 21.9% for Annual customers — a 121.1% relative increase. Migrating customers to annual contracts is the single highest-leverage retention lever identified.
  - Reported values: churn_rate_monthly_pct=48.322148, churn_rate_annual_pct=21.854305, churn_monthly_vs_annual_change_pct=121.110433
  - Direction: increase
- [q5] 100 customers with 5 or more support tickets and a satisfaction score of 2 or below form a critical at-risk segment, churning at 71.0% — nearly double the overall rate. Immediate intervention for this group is strongly recommended.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
  - Derived share(at_risk_customer_count, customer_count): 13.35
- [q6] Average customer tenure is 20.8 months (median 19.0, SD 13.2), indicating a wide spread in customer longevity. Mean satisfaction is 3.4 out of 5. Twenty-seven customers have missing satisfaction scores, limiting satisfaction-based analyses slightly.
  - Reported values: tenure_mean=20.810414, tenure_median=19.0, tenure_std=13.247393, satisfaction_mean=3.416898, satisfaction_missing_count=27.0
- [q7] Mean lifetime value rises sharply by plan: Basic $463, Standard $869, Premium $1,817. Premium LTV is 292.0% higher than Basic, making Premium customer retention disproportionately valuable to revenue.
  - Reported values: ltv_basic=463.457359, ltv_standard=868.830154, ltv_premium=1816.777712, premium_vs_basic_ltv_change_pct=292.005365
  - Direction: increase
  - Ranking: Premium, Standard, Basic

## Limitations
- The dataset is a single snapshot; churn is a binary flag with no timestamp, so time-to-churn and survival analysis are not possible.
- Twenty-seven customers (3.6%) have missing satisfaction scores, which may introduce slight bias in satisfaction-related findings.
- The 2024 cohort has had less time to mature, so its elevated churn rate may partly reflect shorter observation windows rather than a genuine behavioural difference.
- Lifetime value is a derived metric whose calculation assumptions (e.g., discount rate, fee constancy) are not documented, limiting interpretability.
- No causal inference is possible from this observational cross-section; associations between contract type, support tickets, and churn may be confounded by unobserved variables.

## Conclusion
With an overall churn rate of 37.7%, the business faces a significant retention challenge. The most actionable findings are: (1) monthly-contract customers churn at 121% the rate of annual customers — incentivising annual upgrades should be the top priority; (2) the 100-customer at-risk segment (high tickets, low satisfaction) churns at 71% and warrants immediate outreach; and (3) Premium customers deliver 292% more lifetime value than Basic, making targeted retention programmes for that tier highly cost-effective.
