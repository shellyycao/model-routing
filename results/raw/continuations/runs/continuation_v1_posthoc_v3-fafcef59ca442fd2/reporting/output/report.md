# Customer Churn: Verified Findings Report

Of 749 customers, 37.65% have churned (average monthly fee $42.11). Contract type is the strongest churn lever: monthly contracts churn at 48.32% versus 21.85% for annual contracts (121.11% higher). Plan and cohort differences are modest: Basic 38.87% vs Premium 36.60%, and the 2024 cohort is highest at 39.83%. A defined at-risk segment (support_tickets >= 5 and satisfaction_score <= 2) of 100 customers churns at 71.0%. Lifetime value is strongly tiered: Premium $1,816.78 vs Standard $868.83 vs Basic $463.46, with Premium 292.01% above Basic.

## Key findings
- [q1] Across 749 customers, the overall churn rate is 37.65% and the average monthly fee is $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
- [q2] Churn is highest on Basic (38.87%), followed by Standard (36.68%) and Premium (36.60%); the spread across plans is narrow.
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Ranking: Basic, Standard, Premium
- [q3] By signup year, churn is highest for the 2024 cohort (39.83%), then 2021 (38.02%), then 2023 (37.05%), and lowest for 2022 (36.74%).
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Ranking: 2024, 2021, 2023, 2022
- [q4] Monthly contracts churn at 48.32% versus 21.85% for annual contracts, a 121.11% higher churn rate for monthly (an increase).
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
- [q5] The at-risk segment (support_tickets >= 5 and a non-missing satisfaction_score <= 2) contains 100 customers, about 13.4% of the 749-customer base, and churns at 71.0%.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
  - Derived share(at_risk_customer_count, customer_count): 13.4
- [q6] Mean tenure is 20.81 months (median 19.0; sample standard deviation 13.25). Mean satisfaction_score is 3.42 among customers with a score, and 27 customers are missing satisfaction_score.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
- [q7] Mean lifetime value rises sharply by plan: Basic $463.46, Standard $868.83, and Premium $1,816.78; Premium is 292.01% above Basic (an increase).
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401546, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic

## Limitations
- Single snapshot with a binary churned flag: no churn date or observation window, so results are associational and cannot establish causality or timing versus tenure, fees, or tickets.
- satisfaction_score is missing for 27 customers; satisfaction_mean and the at-risk filter (which requires a non-missing score) exclude them, which may bias the at-risk segment and the satisfaction average.
- No significance tests or confidence intervals were run; the small plan and cohort differences (e.g., Basic 38.87% vs Premium 36.60%) may not be statistically meaningful.
- Cohort group sizes are not reported and the 2024 cohort may reflect a partial year, limiting cohort comparability.
- The lifetime_value derivation is not specified; LTV comparisons assume it was computed consistently across plans.

## Conclusion
Lead retention with contract migration (monthly 48.32% vs annual 21.85%) and a targeted save motion for the 100-customer at-risk segment churning at 71.0%. Protect Premium accounts given their $1,816.78 mean LTV. Because plan and cohort gaps are small, concentrate spend on annual-contract conversion and service recovery rather than plan redesign.
