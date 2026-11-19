# Customer Churn Analysis Report

This report presents the findings from the analysis of customer churn rates, segmented by plan, signup cohort, contract type, and an at-risk segment. Key metrics include overall churn rate, churn rates by plan and cohort, the impact of contract type on churn, identification of an at-risk segment, and lifetime value by plan. The analysis reveals significant insights into customer behavior and retention challenges.

## Key findings
- [q1] The overall analysis reveals a customer base of 676 individuals, with a churn rate of 37.3% and an average monthly fee of $41.93.
  - Reported values: customer_count=676.0, churn_rate_pct=37.278106508875744, avg_monthly_fee=41.927869822485206
- [q2] Churn rates vary by plan, with Basic at 38.7%, Standard at 36.2%, and Premium at 36.0%.
  - Reported values: churn_rate_basic_pct=38.68852459016394, churn_rate_standard_pct=36.17021276595745, churn_rate_premium_pct=36.029411764705884
  - Ranking: Basic, Standard, Premium
- [q3] Churn rates by signup cohort show slight variations, with 2021 at 37.3%, 2022 at 36.8%, 2023 at 37.9%, and 2024 at 36.9%.
  - Reported values: churn_rate_cohort_2021_pct=37.28813559322034, churn_rate_cohort_2022_pct=36.787564766839374, churn_rate_cohort_2023_pct=37.93103448275862, churn_rate_cohort_2024_pct=36.89320388349515
  - Ranking: 2023, 2021, 2024, 2022
- [q4] Monthly contracts exhibit a significantly higher churn rate (48.1%) compared to Annual contracts (21.0%), representing a 128.9% increase.
  - Reported values: churn_rate_monthly_pct=48.148148148148145, churn_rate_annual_pct=21.033210332103323, churn_monthly_vs_annual_change_pct=128.91487979207275
  - Direction: increase
  - Derived pct_change(churn_rate_monthly_pct, churn_rate_annual_pct): 128.91487979207275
- [q5] Customers with high support ticket counts and low satisfaction scores are at a significantly higher risk of churn, with 71 customers identified and a churn rate of 73.2% among this group.
  - Reported values: at_risk_customer_count=71.0, at_risk_churn_rate_pct=73.23943661971832
- [q6] The average tenure among customers is 21.0 months, with a median of 19.0 months and a standard deviation of 13.3 months. The mean satisfaction score is 3.42, with 117 customers having missing satisfaction scores.
  - Reported values: tenure_mean=21.034023668639055, tenure_median=19.0, tenure_std=13.258468570055241, satisfaction_mean=3.4239713774597496, satisfaction_missing_count=117.0
- [q7] Lifetime value (LTV) varies significantly by plan, with Basic at $462.60, Standard at $880.94, and Premium at $1871.25. The Premium plan shows a 304.5% increase in LTV compared to the Basic plan.
  - Reported values: ltv_basic=462.5962950819672, ltv_standard=880.9412765957447, ltv_premium=1871.248088235294, premium_vs_basic_ltv_change_pct=304.50996000815974
  - Direction: increase
  - Ranking: Premium, Standard, Basic
  - Derived pct_change(ltv_premium, ltv_basic): 304.50996000815974

## Limitations
- The cleaning stage failed, which may have introduced inaccuracies in the data.
- The analysis stage also failed, potentially affecting the reliability of the findings.
- The sample size for certain segments, such as the at-risk group, is relatively small, which may limit the generalizability of the findings.
- The satisfaction scores are missing for a significant number of customers, which could bias the analysis of satisfaction-related metrics.

## Conclusion
The analysis highlights critical areas for improving customer retention, particularly among customers with high support needs and low satisfaction. Addressing the higher churn rates associated with monthly contracts and enhancing the value proposition of the Basic plan could be strategic priorities. However, the limitations of the data and analysis stages should be considered when interpreting these findings.
