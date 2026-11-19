# Customer Churn Analysis — Verified Findings Report

Across 749 customers, 37.65% have churned and the average monthly fee is $42.11. Churn barely differs by plan or signup cohort, but contract type matters greatly: Monthly customers churn at 48.32% versus 21.85% for Annual (+121.11%). A well-defined at-risk segment of 100 customers with 5+ support tickets and satisfaction ≤2 churns at 71.00%. Lifetime value rises sharply with plan tier — Premium averages $1,816.78, about 3.92× Basic's $463.46. Priorities: move Monthly customers to Annual contracts and intervene early with the high-ticket, low-satisfaction segment.

## Key findings
- [q1] The cleaned dataset contains 749 customers. The overall churn rate is 37.65% and the average monthly fee is $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
  - Direction: not_applicable
- [q2] Churn differs little by plan: Basic 38.87%, Standard 36.68% and Premium 36.60% — a spread of only 2.27 percentage points between the highest (Basic) and lowest (Premium).
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Direction: not_applicable
  - Ranking: Basic, Standard, Premium
  - Derived difference(churn_rate_basic_pct, churn_rate_premium_pct): 2.27
- [q3] Churn is broadly flat across signup cohorts: 2022 is lowest at 36.74% and 2024 highest at 39.83% (a range of 3.09 percentage points), with 2021 at 38.02% and 2023 at 37.05%.
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Direction: not_applicable
  - Ranking: 2024, 2021, 2023, 2022
  - Derived difference(churn_rate_cohort_2024_pct, churn_rate_cohort_2022_pct): 3.09
- [q4] Contract type is the strongest churn differentiator: Monthly customers churn at 48.32% versus 21.85% for Annual — 26.47 percentage points more, a relative increase of 121.11%.
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
  - Derived difference(churn_rate_monthly_pct, churn_rate_annual_pct): 26.47
- [q5] 100 customers (13.35% of the base) have 5+ support tickets and a satisfaction score of 2 or less; 71.00% of them churned — about 1.89× the overall churn rate of 37.65%.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
  - Direction: not_applicable
  - Derived share(at_risk_customer_count, customer_count): 13.35
  - Derived ratio(at_risk_churn_rate_pct, churn_rate_pct): 1.89
- [q6] Typical tenure is around two years: mean 20.81 months, median 19.00 months, standard deviation 13.25 months. Average satisfaction is 3.42, and 27 customers have no satisfaction score recorded.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
  - Direction: not_applicable
- [q7] Lifetime value rises steeply with plan tier: Basic $463.46, Standard $868.83 and Premium $1,816.78 — Premium is 292.01% higher than Basic, roughly 3.92× the value.
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401545, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic
  - Derived ratio(ltv_premium, ltv_basic): 3.92

## Limitations
- Findings are descriptive only; no statistical significance tests were run, so the small plan and cohort differences (a few percentage points) may reflect random variation.
- Associations (e.g., contract type, support tickets, satisfaction) are correlational and do not prove causation.
- 27 customers lack a satisfaction score and are excluded from satisfaction-based metrics, which could bias the at-risk segment definition.
- Signup cohorts have unequal observation windows: 2024 customers have had less time to churn, yet already show the highest churn rate.
- Lifetime value reflects recorded revenue only; cost and margin data were not available, so profitability by plan is unknown.

## Conclusion
Retention efforts should prioritise converting Monthly customers to Annual contracts (48.32% vs 21.85% churn) and proactive outreach to the 100-customer at-risk segment, which churns at 71.00%. Plan tier and cohort effects on churn are minor, but because Premium customers deliver $1,816.78 in average lifetime value, protecting and growing that tier offers the largest revenue payoff.
