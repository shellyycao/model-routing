# Customer Churn: Verified Findings Report for Business Stakeholders

Of 749 customers, 37.65% have churned, at an average monthly fee of 42.11. Contract type is the dominant churn factor: monthly plans churn at 48.32% versus 21.85% for annual plans, a 121.11% relative increase. Plan tier barely differentiates churn (36.60%–38.87%), while the newest cohort (2024) churns most at 39.83%. A well-defined at-risk segment of 100 customers — five or more support tickets and satisfaction of two or less — churns at 71.0%. Premium customers carry the highest lifetime value at 1,816.78 on average, 292.01% above Basic. Recommended focus: move monthly customers to annual contracts and intervene early with high-ticket, low-satisfaction customers.

## Key findings
- [q1] The cleaned customer base contains 749 customers. The overall churn rate is 37.65%, and the average monthly fee is 42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
  - Direction: not_applicable
- [q2] Churn is nearly flat across plans: Basic 38.87%, Standard 36.68% and Premium 36.60%. The gap between the highest- and lowest-churn plans is just 2.27 percentage points, so plan tier alone is a weak churn driver.
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Direction: not_applicable
  - Ranking: Basic, Standard, Premium
  - Derived difference(churn_rate_basic_pct, churn_rate_premium_pct): 2.27
- [q3] Cohort churn is fairly stable, but the newest customers churn most: the 2024 cohort at 39.83%, followed by 2021 (38.02%), 2023 (37.05%) and 2022 (36.74%) — a spread of 3.09 percentage points between the highest and lowest cohorts.
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Direction: not_applicable
  - Ranking: 2024, 2021, 2023, 2022
  - Derived difference(churn_rate_cohort_2024_pct, churn_rate_cohort_2022_pct): 3.09
- [q4] Contract type is the strongest churn factor: monthly contracts churn at 48.32% versus 21.85% for annual contracts — a 121.11% relative increase, meaning monthly customers churn at roughly 2.21 times the annual rate.
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
  - Derived ratio(churn_rate_monthly_pct, churn_rate_annual_pct): 2.21
- [q5] The at-risk segment (five or more support tickets and a satisfaction score of 2 or below) contains 100 customers — 13.35% of the 749-customer base — and churns at 71.0%, about 1.89 times the overall churn rate of 37.65%.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0, customer_count=749.0, churn_rate_pct=37.6502002670227
  - Direction: not_applicable
  - Derived share(at_risk_customer_count, customer_count): 13.35
  - Derived ratio(at_risk_churn_rate_pct, churn_rate_pct): 1.89
- [q6] Tenure averages 20.81 months (median 19.0, standard deviation 13.25), a right-skewed base of relatively young customers. Mean satisfaction is 3.42, and 27 customers (3.6% of the base) have no satisfaction score.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0, customer_count=749.0
  - Direction: not_applicable
  - Derived share(satisfaction_missing_count, customer_count): 3.6
- [q7] Lifetime value climbs steeply by plan: Basic 463.46, Standard 868.83 and Premium 1,816.78 on average. Premium customers are worth 292.01% more than Basic customers — about 3.92 times the Basic value.
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401546, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic
  - Derived ratio(ltv_premium, ltv_basic): 3.92

## Limitations
- Findings come from a single snapshot; relationships (e.g., annual contracts and lower churn) are correlational — lower-risk customers may simply choose annual plans — so no causal effect is proven.
- Plan and cohort differences are small and were not tested for statistical significance, so they may reflect random variation rather than real effects.
- Satisfaction scores are missing for 27 customers, and the at-risk filter only includes customers with non-missing scores, so the true at-risk population may be larger than reported.
- Signup cohorts have unequal exposure windows: 2024 customers have had the least time to churn yet already show the highest rate, so cohort figures will shift as these accounts mature.
- Lifetime value is revenue-based with no cost or margin data, so the LTV ranking may not reflect profitability; per-plan group sizes were not reported, limiting confidence assessment.

## Conclusion
Churn is concentrated among monthly-contract customers and a clearly identifiable high-ticket, low-satisfaction segment. Because Premium accounts carry by far the highest lifetime value, retention spending should prioritise at-risk Premium customers, incentivise migration to annual billing, and trigger service recovery before customers accumulate five or more support tickets.
