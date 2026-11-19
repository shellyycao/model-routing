# Customer Churn Analysis Report

This report analyzes churn patterns across 749 customers. The overall churn rate stands at 37.7%. Critical risk factors include monthly contracts, which show a 121% higher churn rate than annual contracts, and a specific at-risk segment with high support ticket volume and low satisfaction, exhibiting a 71% churn rate. Lifetime value scales significantly with plan tier, offering potential for revenue growth through retention efforts.

## Key findings
- [q1] The dataset comprises 749 customers with an overall churn rate of 37.7% and an average monthly fee of $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
- [q2] Churn rates are relatively consistent across plans, ranging from 36.6% (Premium) to 38.9% (Basic). The Basic plan has the highest churn rate.
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Ranking: Basic, Standard, Premium
- [q3] Churn rates by signup cohort show minor variation, with the 2024 cohort having the highest churn rate at 39.8% and the 2022 cohort the lowest at 36.7%.
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Ranking: 2024, 2021, 2023, 2022
- [q4] Monthly contract holders churn at a rate of 48.3%, compared to 21.9% for annual contract holders. This represents a 121.1% increase in churn rate for monthly contracts relative to annual ones.
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
- [q5] An at-risk segment of 100 customers with high support tickets and low satisfaction exhibits a churn rate of 71.0%, nearly double the overall average.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
  - Derived ratio(at_risk_churn_rate_pct, churn_rate_pct): 1.9
- [q6] Customer tenure averages 20.8 months (median 19.0, std dev 13.2). The average satisfaction score is 3.4, with 27 customers missing a satisfaction score.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
- [q7] Lifetime value (LTV) increases significantly by plan tier, with Premium LTV at $1,817 compared to Basic at $463. Premium LTV is 292.0% higher than Basic LTV.
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401545, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic

## Limitations
- The analysis is based on a single snapshot and does not capture time-series dynamics beyond signup cohorts.
- Satisfaction scores were missing for 27 customers, which may bias the satisfaction mean.
- Causality cannot be inferred; observed associations (e.g., contract type and churn) may be influenced by unobserved factors.

## Conclusion
To reduce churn, prioritize converting monthly customers to annual contracts and intervene with the high-support, low-satisfaction segment. The substantial LTV difference between Basic and Premium plans suggests that retention efforts focused on Premium customers could yield significant revenue protection.
