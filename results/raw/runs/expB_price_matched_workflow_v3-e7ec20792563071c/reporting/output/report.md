# Customer Churn Analysis Report

Analysis of 749 customers reveals an overall churn rate of 37.7%. Monthly-contract customers churn at more than double the rate of annual-contract customers. A high-risk segment of 100 customers with poor satisfaction and heavy support usage churns at 71%. Lifetime value scales sharply with plan tier, with Premium customers generating nearly 4× the value of Basic customers.

## Key findings
- [q1] The dataset contains 749 customers with an overall churn rate of 37.7% and a mean monthly fee of $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
- [q2] Churn rates differ modestly across plans: Basic is highest at 38.9%, followed by Standard at 36.7%, and Premium is lowest at 36.6%. The spread between Basic and Premium is approximately 2.3 percentage points.
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Ranking: Basic, Standard, Premium
  - Derived difference(churn_rate_basic_pct, churn_rate_premium_pct): 2.27
- [q3] Churn by signup cohort shows the 2024 cohort is highest at 39.8%, followed by 2021 at 38.0%, 2023 at 37.1%, and 2022 lowest at 36.7%. The pattern is non-linear, with the most recent cohort showing the greatest churn risk.
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Ranking: 2024, 2021, 2023, 2022
- [q4] Monthly-contract customers churn at 48.3% versus 21.9% for annual-contract customers — a relative increase of 121.1%, meaning monthly customers churn at more than twice the rate of annual customers.
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
- [q5] 100 customers meet the at-risk criteria (≥5 support tickets and satisfaction score ≤2). This segment churns at 71.0%, nearly double the overall rate, representing a critical retention priority.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
  - Derived share(at_risk_customer_count, customer_count): 13.35
- [q6] Customer tenure averages 20.8 months (median 19.0, SD 13.2 months), indicating a wide spread in customer longevity. Mean satisfaction among the 722 customers with non-missing scores is 3.42 out of 5; 27 customers have no satisfaction score recorded.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
  - Derived difference(customer_count, satisfaction_missing_count): 722.0
- [q7] Mean lifetime value rises sharply by plan tier: Basic $463, Standard $869, and Premium $1,817. Premium LTV is 292.0% higher than Basic, confirming that upselling to higher tiers has a substantial revenue impact.
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401546, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic

## Limitations
- The 2024 cohort may be underrepresented due to shorter observation windows, inflating its apparent churn rate relative to older cohorts.
- 27 customers (3.6%) are missing satisfaction scores, which may introduce bias into satisfaction-based metrics and the at-risk segment definition.
- The analysis is cross-sectional; causal relationships between plan type, contract length, and churn cannot be established without longitudinal or experimental data.
- Lifetime value is a derived field from the cleaned dataset; its calculation methodology and assumptions are not fully documented in the handoff.

## Conclusion
Churn is a significant business risk at 37.7% overall. The strongest lever identified is contract type: migrating monthly customers to annual contracts could reduce churn by more than half for that group. The 100-customer at-risk segment (71% churn rate) warrants immediate targeted intervention. Premium plan customers deliver nearly 4× the lifetime value of Basic customers, making upsell programs a high-priority growth strategy alongside retention efforts.
