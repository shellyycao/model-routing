# Customer Churn Analysis — Verified Findings Report

Across 749 customers, overall churn stands at 37.65%, with an average monthly fee of $42.11. Churn varies little by plan or signup cohort, but contract type is the standout driver: Monthly contracts churn at 48.32% versus 21.85% for Annual, a 121.11% relative increase. An at-risk segment of 100 customers with heavy support contact and low satisfaction churns at 71.0%. Plan tier strongly affects value rather than churn: Premium customers deliver 292.01% more lifetime value than Basic customers.

## Key findings
- [q1] The cleaned dataset contains 749 customers. Overall churn stands at 37.65%, and the average monthly fee is $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
  - Direction: not_applicable
- [q2] Churn differs little across plans: Basic 38.87%, Standard 36.68%, and Premium 36.60%, with Basic only 2.27 points above Premium. Plan choice alone does not appear to drive churn.
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Direction: not_applicable
  - Ranking: Basic, Standard, Premium
  - Derived difference(churn_rate_basic_pct, churn_rate_premium_pct): 2.27
- [q3] Churn is stable across signup cohorts — 2021: 38.02%, 2022: 36.74%, 2023: 37.05%, 2024: 39.83%. The 2024 cohort is highest, 3.09 points above the lowest cohort (2022).
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Direction: not_applicable
  - Ranking: 2024, 2021, 2023, 2022
  - Derived difference(churn_rate_cohort_2024_pct, churn_rate_cohort_2022_pct): 3.09
- [q4] Contract type is the clearest churn differentiator: Monthly contracts churn at 48.32% versus 21.85% for Annual, a 121.11% relative increase — roughly 2.21x the rate and 26.47 points higher.
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
  - Derived ratio(churn_rate_monthly_pct, churn_rate_annual_pct): 2.21
  - Derived difference(churn_rate_monthly_pct, churn_rate_annual_pct): 26.47
- [q5] The at-risk segment (five or more support tickets and a satisfaction score of 2 or lower) comprises 100 customers, 13.35% of the base, and churns at 71.0% — 33.35 points above the overall churn rate.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
  - Direction: not_applicable
  - Derived share(at_risk_customer_count, customer_count): 13.35
  - Derived difference(at_risk_churn_rate_pct, churn_rate_pct): 33.35
- [q6] Customer tenure averages 20.81 months (median 19.0, standard deviation 13.25), indicating a wide spread of customer lifespans. Average satisfaction is 3.42; 27 customers, or 3.6% of the base, have no satisfaction score.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
  - Direction: not_applicable
  - Derived share(satisfaction_missing_count, customer_count): 3.6
- [q7] Average lifetime value climbs steeply by plan: Basic $463.46, Standard $868.83, and Premium $1,816.78. Premium customers are worth 292.01% more than Basic — about 3.92x the value.
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401545, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic
  - Derived ratio(ltv_premium, ltv_basic): 3.92

## Limitations
- The analysis is descriptive and correlational; no causal claims can be made. For example, Annual-contract customers may simply be lower-risk buyers rather than being retained by the contract itself.
- Satisfaction scores are missing for a subset of customers, and the at-risk definition excludes anyone without a score, so the true size of that segment may be understated.
- No statistical significance tests or confidence intervals were computed, so the small churn differences between plans and cohorts may reflect random variation rather than real effects.
- Findings come from a single customer snapshot; tenure, seasonality, and time-to-churn dynamics are not captured.

## Conclusion
Retention efforts should prioritize shifting Monthly customers toward Annual contracts, which show far lower churn, and proactively engaging the 100 at-risk customers, who churn at 71.0%. Plan tier has little effect on churn, but Premium accounts carry 292.01% higher lifetime value than Basic, so retaining high-tier customers delivers outsized returns.
