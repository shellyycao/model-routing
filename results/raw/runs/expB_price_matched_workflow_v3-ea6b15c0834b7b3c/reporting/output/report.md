# Customer Churn Analysis: Verified Findings Report

Across 749 cleaned customer records, 37.65% have churned, with an average monthly fee of $42.11. Contract type is the strongest churn differentiator: Monthly contracts churn at 48.32% versus 21.85% for Annual, a 121.11% relative increase. Plan tier barely affects churn (Basic 38.87%, Standard 36.68%, Premium 36.60%), but it strongly affects value: Premium customers' mean lifetime value of $1,816.78 is 292.0% above Basic's $463.46. A clearly defined at-risk segment of 100 customers (13.35% of the base), those with 5+ support tickets and satisfaction at or below 2, churns at 71.0%. Churn by signup cohort is stable (36.74%-39.83%), with the 2024 cohort highest. Average tenure is 20.81 months and mean satisfaction is 3.42.

## Key findings
- [q1] The cleaned dataset contains 749 customers; the overall churn rate is 37.65% and the average monthly fee is $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
  - Direction: not_applicable
- [q2] Churn is broadly similar across plans: Basic 38.87%, Standard 36.68% and Premium 36.60% - a spread of only 2.27 percentage points between the highest (Basic) and lowest (Premium) tiers.
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Direction: not_applicable
  - Ranking: Basic, Standard, Premium
  - Derived difference(churn_rate_basic_pct, churn_rate_premium_pct): 2.27
- [q3] Churn by signup cohort is stable, ranging from 36.74% (2022) to 39.83% (2024); ranked highest to lowest: 2024 (39.83%), 2021 (38.02%), 2023 (37.05%), 2022 (36.74%), with no clear improving or worsening trend.
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Direction: not_applicable
  - Ranking: 2024, 2021, 2023, 2022
- [q4] Contract type is the strongest churn driver: Monthly contracts churn at 48.32% versus 21.85% for Annual contracts - a gap of 26.47 percentage points and a 121.11% relative increase for Monthly over Annual.
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
  - Derived difference(churn_rate_monthly_pct, churn_rate_annual_pct): 26.47
- [q5] The at-risk segment (5+ support tickets and satisfaction score of 2 or below) contains 100 customers - 13.35% of the customer base - and churns at 71.0%, far above the 37.65% overall rate, making it a priority retention target.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
  - Direction: not_applicable
  - Derived share(at_risk_customer_count, customer_count): 13.35
- [q6] Customers average 20.81 months of tenure (median 19.0, standard deviation 13.25); mean satisfaction is 3.42, and 27 customers have a missing satisfaction score.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
  - Direction: not_applicable
- [q7] Mean lifetime value rises sharply with plan tier: Basic $463.46, Standard $868.83 and Premium $1,816.78; Premium LTV is 292.0% higher than Basic, so plan mix matters greatly for revenue even though it barely affects churn.
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401545, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic

## Limitations
- The analysis is descriptive only; no statistical significance testing was performed, so small differences (e.g., the 2.27-point churn spread across plans) may reflect random variation.
- Satisfaction scores are missing for 27 customers; the at-risk segment excludes customers without a score, so the segment may be undercounted.
- Cohort churn rates are not adjusted for differing observation windows; more recent cohorts (e.g., 2024) have had less time to churn, which can distort comparisons.
- Lifetime value differences by plan may reflect customer self-selection into tiers rather than a causal effect of the plan itself.
- Results are a single snapshot; no causal claims about contract type or support tickets can be drawn without longitudinal or experimental data.

## Conclusion
Retention efforts should prioritise converting Monthly customers to Annual contracts (48.32% vs 21.85% churn) and intervening with the 100-customer at-risk segment, which churns at 71.0%. Because plan tier drives lifetime value (Premium +292.0% vs Basic) but not churn, growth strategy should focus on upselling retained customers to higher tiers.
