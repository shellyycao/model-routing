# Customer Churn Analysis: Verified Findings for Business Stakeholders

Across 749 customers, overall churn is 37.7%, with an average monthly fee of $42.11. Contract type is the strongest churn differentiator: monthly contracts churn at 48.3% versus 21.9% for annual contracts, a relative increase of 121.1%. An at-risk segment of 100 customers with 5+ support tickets and satisfaction at or below 2 churns at 71.0%. Churn differs little across plans (36.6% to 38.9%), but lifetime value scales sharply with plan tier: Premium averages $1,816.78, +292.0% versus Basic at $463.46.

## Key findings
- [q1] The cleaned dataset contains 749 customers. The overall churn rate is 37.7% and the average monthly fee is $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502, avg_monthly_fee=42.106155
  - Direction: not_applicable
- [q2] Churn varies only modestly by plan: Basic 38.9%, Standard 36.7%, Premium 36.6%. Basic ranks highest, but only 2.27 percentage points above Premium, so plan tier alone does not strongly differentiate churn.
  - Reported values: churn_rate_basic_pct=38.872404, churn_rate_standard_pct=36.679537, churn_rate_premium_pct=36.601307
  - Direction: not_applicable
  - Ranking: Basic, Standard, Premium
  - Derived difference(churn_rate_basic_pct, churn_rate_premium_pct): 2.27
- [q3] Churn by signup cohort is non-monotonic: the 2024 cohort churns highest at 39.8%, followed by 2021 (38.0%), 2023 (37.1%) and 2022 (36.7%). The newest cohort churns 3.09 percentage points above the lowest (2022), indicating no sustained improvement in retention over time.
  - Reported values: churn_rate_cohort_2021_pct=38.020833, churn_rate_cohort_2022_pct=36.744186, churn_rate_cohort_2023_pct=37.053571, churn_rate_cohort_2024_pct=39.830508
  - Direction: not_applicable
  - Ranking: 2024, 2021, 2023, 2022
  - Derived difference(churn_rate_cohort_2024_pct, churn_rate_cohort_2022_pct): 3.09
- [q4] Contract type is the dominant churn factor: monthly contracts churn at 48.3% versus 21.9% for annual contracts, an absolute gap of 26.47 percentage points and a relative increase of 121.1%.
  - Reported values: churn_rate_monthly_pct=48.322148, churn_rate_annual_pct=21.854305, churn_monthly_vs_annual_change_pct=121.110433
  - Direction: increase
  - Derived difference(churn_rate_monthly_pct, churn_rate_annual_pct): 26.47
- [q5] Customers with 5+ support tickets and a satisfaction score at or below 2 form an at-risk segment of 100 customers (13.35% of the customer base) that churns at 71.0%, roughly 1.89 times the overall churn rate of 37.7%.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
  - Direction: not_applicable
  - Derived share(at_risk_customer_count, customer_count): 13.35
  - Derived ratio(at_risk_churn_rate_pct, churn_rate_pct): 1.89
- [q6] Typical customer tenure is 19 months (median), with a mean of 20.8 months and a standard deviation of 13.2 months, indicating a right-skewed tenure distribution. Average satisfaction is 3.42 among scored customers; 27 customers (3.6% of the base) have no satisfaction score.
  - Reported values: tenure_mean=20.810414, tenure_median=19.0, tenure_std=13.247393, satisfaction_mean=3.416898, satisfaction_missing_count=27.0
  - Direction: not_applicable
  - Derived share(satisfaction_missing_count, customer_count): 3.6
- [q7] Lifetime value rises steeply with plan tier: Basic averages $463.46, Standard $868.83 and Premium $1,816.78. Premium LTV is +292.0% versus Basic, about 3.92 times higher, making Premium retention especially valuable.
  - Reported values: ltv_basic=463.457359, ltv_standard=868.830154, ltv_premium=1816.777712, premium_vs_basic_ltv_change_pct=292.005365
  - Direction: increase
  - Ranking: Premium, Standard, Basic
  - Derived ratio(ltv_premium, ltv_basic): 3.92

## Limitations
- Satisfaction scores are missing for 27 customers; the at-risk segment and the satisfaction mean exclude them, which may introduce bias if missingness is not random.
- The data is a single cross-sectional snapshot, so cohort and tenure effects are confounded and no causal claims can be made (for example, that annual contracts prevent churn).
- No statistical significance testing was performed; small differences, such as the roughly two-point churn spread between plans, may reflect sampling noise.
- The at-risk thresholds (5+ support tickets, satisfaction at or below 2) are analytical choices rather than validated business definitions, and segment results are sensitive to those cut-offs.

## Conclusion
Churn is high overall at 37.7% and is concentrated among monthly-contract customers (48.3% churn) and the 100-customer at-risk segment (71.0% churn). Priority actions: incentivise migration from monthly to annual contracts, and trigger proactive retention outreach for customers with 5+ support tickets and satisfaction at or below 2. Because Premium customers carry the highest lifetime value ($1,816.78, +292.0% versus Basic), protecting that tier should deliver the greatest revenue impact.
