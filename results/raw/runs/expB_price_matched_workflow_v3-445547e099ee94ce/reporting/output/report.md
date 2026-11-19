# Customer Churn Analysis: Verified Findings for Business Stakeholders

Across 749 customers, overall churn is 37.65%. Churn varies little by plan (Basic 38.87%, Standard 36.68%, Premium 36.60%) or signup cohort (2024 highest at 39.83%), but contract type is decisive: monthly contracts churn at 48.32% versus 21.85% for annual contracts, a 121.11% higher rate. An at-risk segment of 100 customers with heavy support tickets and low satisfaction churns at 71.0%. Premium customers deliver the highest average lifetime value at $1,816.78, 292.01% above Basic's $463.46.

## Key findings
- [q1] The cleaned dataset contains 749 customers. The overall churn rate is 37.65%, and the average monthly fee is $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
- [q2] Churn is broadly similar across plans: Basic 38.87%, Standard 36.68% and Premium 36.60%. Basic ranks highest, only about 2.27 percentage points above Premium.
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Ranking: Basic, Standard, Premium
  - Derived difference(churn_rate_basic_pct, churn_rate_premium_pct): 2.27
- [q3] Churn by signup cohort is fairly stable: 2022 is lowest at 36.74%, 2023 is 37.05%, 2021 is 38.02%, and the newest 2024 cohort is highest at 39.83%.
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Ranking: 2024, 2021, 2023, 2022
- [q4] Contract type is the strongest differentiator: monthly-contract customers churn at 48.32% versus 21.85% for annual contracts, a relative increase of 121.11%.
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
- [q5] The at-risk segment — customers with five or more support tickets and a satisfaction score of 2 or lower — contains 100 customers and churns at 71.0%, versus 37.65% overall.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0, churn_rate_pct=37.6502002670227
- [q6] Customers average 20.81 months of tenure (median 19.0, standard deviation 13.25). Mean satisfaction is 3.42, and 27 customers are missing a satisfaction score.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
- [q7] Average lifetime value climbs steeply by plan: $463.46 for Basic, $868.83 for Standard and $1,816.78 for Premium. Premium LTV is 292.01% higher than Basic.
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401546, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic

## Limitations
- This is a single cross-sectional snapshot; observed differences (e.g., by contract type) are associational and may reflect customer self-selection rather than causal effects.
- Satisfaction scores are missing for 27 customers; the at-risk segment excludes them, so its size and churn rate may be understated.
- No statistical significance or confidence testing was performed; the small differences between plans and between cohorts may be due to chance.
- Cohort churn mixes tenure effects: newer cohorts have had less time to churn, which complicates trend interpretation.
- Lifetime value is taken as a precomputed field; its calculation method and any revenue or cost assumptions are not documented in this workflow.

## Conclusion
Retention efforts should prioritise monthly-contract customers and the 100-customer at-risk segment, where churn reaches 71.0%. Encouraging migration to annual contracts and proactive support for dissatisfied, high-ticket customers offers the largest leverage. Plan and cohort effects are comparatively minor, and Premium customers justify the greatest retention investment given their $1,816.78 average lifetime value.
