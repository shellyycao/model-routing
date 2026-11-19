# Customer Churn Analysis — Verified Findings Report

Across 749 customers, 37.65% churned, paying an average monthly fee of $42.11. Churn is strikingly insensitive to plan tier (36.60%–38.87%) but highly sensitive to contract type: Monthly customers churn at 48.32% versus 21.85% for Annual, a 121.11% relative increase. The newest signup cohort (2024) churns most at 39.83%. A high-risk segment of 100 customers with 5+ support tickets and satisfaction ≤ 2 churns at 71%. Lifetime value, unlike churn, scales sharply with plan: Premium customers are worth 292.01% more than Basic.

## Key findings
- [q1] The cleaned dataset contains 749 customers, of whom 37.65% churned; the average monthly fee is $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
- [q2] Churn varies little across plans — Basic 38.87%, Standard 36.68%, Premium 36.60% — only a 2.27 percentage-point spread between the highest (Basic) and lowest (Premium) tier.
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Ranking: Basic, Standard, Premium
  - Derived difference(churn_rate_basic_pct, churn_rate_premium_pct): 2.27
- [q3] Cohort churn is broadly stable with an uptick among the newest signups: 2021 38.02%, 2022 36.74%, 2023 37.05%, 2024 39.83%; 2024 sits 3.09 percentage points above the lowest cohort (2022).
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Ranking: 2024, 2021, 2023, 2022
  - Derived difference(churn_rate_cohort_2024_pct, churn_rate_cohort_2022_pct): 3.09
- [q4] Contract type is the dominant churn factor: Monthly 48.32% versus Annual 21.85%, a 26.47 percentage-point gap — Monthly churn is 121.11% higher, about 2.21x the Annual rate.
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
  - Derived difference(churn_rate_monthly_pct, churn_rate_annual_pct): 26.47
  - Derived ratio(churn_rate_monthly_pct, churn_rate_annual_pct): 2.21
- [q5] The at-risk segment — 100 customers (13.4% of the base) with support_tickets ≥ 5 and satisfaction ≤ 2 — churns at 71%, roughly 1.89x the overall rate and the clearest intervention target.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
  - Derived share(at_risk_customer_count, customer_count): 13.4
  - Derived ratio(at_risk_churn_rate_pct, churn_rate_pct): 1.89
- [q6] Mean tenure is 20.81 months (median 19, SD 13.25); mean satisfaction is 3.42, with 27 customers (3.6%) missing a satisfaction score.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
  - Derived share(satisfaction_missing_count, customer_count): 3.6
- [q7] Lifetime value rises steeply by tier: Basic $463.46, Standard $868.83 (1.87x Basic), Premium $1,816.78 (3.92x Basic, a 292.01% increase).
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401546, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic
  - Derived ratio(ltv_standard, ltv_basic): 1.87
  - Derived ratio(ltv_premium, ltv_basic): 3.92

## Limitations
- Churn is measured at a single snapshot; newer cohorts have had less time to churn, so cohort comparisons mix tenure effects with cohort effects.
- Satisfaction scores are missing for 27 customers; satisfaction-based metrics and the at-risk filter exclude them.
- Results are associational, not causal — annual contracts may attract inherently loyal customers rather than directly reduce churn.
- Group churn differences (plan, cohort) were not tested for statistical significance, and the at-risk thresholds (5 tickets, satisfaction ≤ 2) are analyst-chosen cutoffs.

## Conclusion
Overall churn of 37.65% is high. The strongest levers are contract mix and the at-risk segment: shifting Monthly customers toward Annual contracts and proactively engaging the 100 high-ticket, low-satisfaction customers (71% churn) offer the largest retention gains. Plan tier barely moves churn but multiplies lifetime value, so upselling remains a revenue, not retention, strategy.
