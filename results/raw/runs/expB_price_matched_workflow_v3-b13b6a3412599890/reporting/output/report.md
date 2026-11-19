# Customer Churn Analysis Report

Analysis of 749 customers reveals an overall churn rate of 37.7%. Monthly contract holders and an identified at-risk segment show significantly elevated churn. While churn rates are stable across signup cohorts and plans, Lifetime Value (LTV) scales dramatically with plan tier, offering a clear incentive for upgrades.

## Key findings
- [q1] The dataset contains 749 customers with an overall churn rate of 37.7% and an average monthly fee of $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
- [q2] Churn rates are similar across plans, ranging from 36.6% to 38.9%. The Basic plan has the highest churn rate, followed by Standard and Premium.
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Ranking: Basic, Standard, Premium
- [q3] Churn rates have remained relatively stable across signup cohorts, fluctuating between 36.7% and 39.8%. The 2024 cohort shows the highest churn rate at 39.8%, while the 2022 cohort was lowest at 36.7%.
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Ranking: 2024, 2021, 2023, 2022
- [q4] Contract type is a strong predictor of churn. Monthly contract holders churn at 48.3%, which is 121.1% higher than the 21.9% rate for Annual contract holders.
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
- [q5] An at-risk segment of 100 customers with high support tickets (≥5) and low satisfaction (≤2) exhibits a critical churn rate of 71.0%.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
- [q6] Customer tenure averages 20.8 months (median 19.0) with a standard deviation of 13.2 months. Average satisfaction is 3.42, though 27 records are missing satisfaction scores.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
- [q7] Lifetime Value (LTV) increases significantly by plan. Premium LTV is $1,816.78, which is 292.0% higher than Basic LTV ($463.46). Standard LTV is $868.83.
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401545, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic

## Limitations
- Satisfaction scores are missing for 27 customers, potentially biasing the satisfaction mean.
- The analysis is based on a snapshot and does not track churn over time.
- Causal factors for churn were not modeled; reported associations do not imply causation.

## Conclusion
To reduce churn, prioritize converting monthly customers to annual contracts and intervene with the high-support, low-satisfaction segment. Upselling to Premium plans offers substantial LTV gains.
