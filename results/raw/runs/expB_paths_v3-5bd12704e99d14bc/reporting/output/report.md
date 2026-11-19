# Customer Churn Analysis Report

Analysis of 749 customers reveals an overall churn rate of 37.7%, well above healthy benchmarks. Monthly-contract customers churn at more than double the rate of annual-contract customers, and a high-risk segment of 100 customers with poor satisfaction and frequent support contacts churns at 71%. Premium-plan customers generate nearly 4× the lifetime value of Basic customers, making retention investment in that tier especially valuable.

## Key findings
- [q1] The dataset contains 749 customers with an overall churn rate of 37.7% and an average monthly fee of $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
- [q2] Churn rates differ modestly across plans: Basic is highest at 38.9%, followed by Standard at 36.7%, and Premium at 36.6%. The spread is narrow (~2.3 percentage points), suggesting plan tier alone is not a strong churn driver.
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Ranking: Basic, Standard, Premium
  - Derived difference(churn_rate_basic_pct, churn_rate_premium_pct): 2.27
- [q3] Churn by signup cohort shows the 2024 cohort is highest at 39.8%, followed by 2021 at 38.0%, 2023 at 37.1%, and 2022 at 36.7%. The most recent cohort's elevated churn may reflect insufficient onboarding time.
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Ranking: 2024, 2021, 2023, 2022
- [q4] Contract type is a strong churn predictor. Monthly-contract customers churn at 48.3% versus 21.9% for annual-contract customers — monthly churn is 121.1% higher than annual, meaning monthly customers churn at more than twice the rate.
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
- [q5] 100 customers meet the at-risk criteria (≥5 support tickets and satisfaction score ≤2). This segment churns at 71.0%, nearly double the overall rate, and warrants immediate intervention.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
  - Derived difference(at_risk_churn_rate_pct, churn_rate_pct): 33.35
- [q6] Customer tenure averages 20.8 months (median 19.0, SD 13.2), indicating a wide spread in customer longevity. Mean satisfaction among scored customers is 3.4 out of 5; 27 customers are missing satisfaction scores, limiting coverage.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
- [q7] Lifetime value rises sharply with plan tier: Basic averages $463, Standard $869, and Premium $1,817. Premium LTV is 292.0% higher than Basic, underscoring the outsized revenue impact of retaining Premium customers.
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401546, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic

## Limitations
- 27 customers (3.6%) are missing satisfaction scores, which may introduce slight bias in satisfaction-based metrics and the at-risk segment definition.
- The 2024 cohort has had less time to churn than earlier cohorts; its elevated churn rate may partly reflect a shorter observation window rather than a genuine behavioural difference.
- Lifetime value is computed as a mean per plan without controlling for tenure or contract type, so plan-level LTV differences may be confounded by those variables.
- The at-risk segment threshold (≥5 tickets, satisfaction ≤2) is rule-based and not derived from a predictive model; different thresholds could materially change segment size and churn rate.
- The snapshot represents a single point in time; longitudinal tracking would be needed to confirm whether churn trends are worsening or improving.

## Conclusion
With more than one-in-three customers churning, retention is a critical priority. The most actionable levers are: (1) converting monthly-contract customers to annual plans, which is associated with a 26-percentage-point lower churn rate; (2) immediately engaging the 100 at-risk customers churning at 71%; and (3) protecting Premium customers, whose LTV of $1,817 is nearly 4× that of Basic customers. Cohort data suggest recent sign-ups need stronger early-lifecycle support to reduce their above-average churn.
