# Customer Churn Analysis Report

This report presents the findings from the analysis of customer churn rates, segmented by plan, signup cohort, contract type, and an at-risk segment. Key metrics include overall churn rate, churn rates by plan and cohort, contract effect on churn, at-risk segment identification, and lifetime value by plan.

## Key findings
- [q1] The overall churn rate is 37.65%, with an average monthly fee of $42.11 across 749 customers.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502, avg_monthly_fee=42.106155
- [q2] Churn rates vary by plan, with Basic at 38.87%, Standard at 36.68%, and Premium at 36.60%.
  - Reported values: churn_rate_basic_pct=38.872404, churn_rate_standard_pct=36.679537, churn_rate_premium_pct=36.601307
  - Ranking: Basic, Standard, Premium
- [q3] Churn rates by signup cohort show fluctuations, with 2024 at 39.83%, 2021 at 38.02%, 2023 at 37.05%, and 2022 at 36.74%.
  - Reported values: churn_rate_cohort_2021_pct=38.020833, churn_rate_cohort_2022_pct=36.744186, churn_rate_cohort_2023_pct=37.053571, churn_rate_cohort_2024_pct=39.830508
  - Ranking: 2024, 2021, 2023, 2022
- [q4] Monthly contracts have a significantly higher churn rate (48.32%) compared to Annual contracts (21.85%), representing a 121.11% increase.
  - Reported values: churn_rate_monthly_pct=48.322148, churn_rate_annual_pct=21.854305, churn_monthly_vs_annual_change_pct=121.110433
  - Direction: increase
  - Derived pct_change(churn_rate_monthly_pct, churn_rate_annual_pct): 121.110433
- [q5] Customers with 5 or more support tickets and a satisfaction score of 2 or lower have a high churn rate of 71.0%, indicating they are at risk.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
- [q6] The average tenure is 20.81 months with a median of 19.0 months and a standard deviation of 13.25 months. The average satisfaction score is 3.42, with 27 missing values.
  - Reported values: tenure_mean=20.810414, tenure_median=19.0, tenure_std=13.247393, satisfaction_mean=3.416898, satisfaction_missing_count=27.0
- [q7] Lifetime value (LTV) increases significantly from Basic ($463.46) to Standard ($868.83) and Premium ($1,816.78), with a 292.01% increase from Basic to Premium.
  - Reported values: ltv_basic=463.457359, ltv_standard=868.830154, ltv_premium=1816.777712, premium_vs_basic_ltv_change_pct=292.005365
  - Direction: increase
  - Ranking: Premium, Standard, Basic
  - Derived pct_change(ltv_premium, ltv_basic): 292.005365

## Limitations
- The analysis is based on a snapshot of customer data, which may not capture recent changes.
- The satisfaction score has missing values, which could affect the accuracy of related metrics.
- The at-risk segment is defined by specific thresholds, which may not capture all at-risk customers.

## Conclusion
The analysis highlights significant variations in churn rates across different plans, cohorts, and contract types. Identifying at-risk segments and understanding lifetime value by plan can inform targeted retention strategies.
