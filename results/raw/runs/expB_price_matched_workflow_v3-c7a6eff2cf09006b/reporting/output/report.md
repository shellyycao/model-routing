# Customer Churn Analysis — Verified Findings Report

Of 749 cleaned customers, 37.65% have churned, paying an average monthly fee of $42.11. Plan tier barely differentiates churn (36.60–38.87% across Premium, Standard and Basic) and cohort churn is nearly flat (36.74–39.83%, with the 2024 cohort highest). Contract type is decisive: Monthly customers churn at 48.32% versus 21.85% for Annual — a 121.11% relative increase. A defined 100-customer at-risk segment (5+ support tickets, satisfaction <= 2) churns at 71.0%. Premium plans generate $1,816.78 mean lifetime value, 292.01% above Basic. Retention efforts should prioritise Monthly-to-Annual migration and early intervention with the at-risk segment.

## Key findings
- [q1] The cleaned dataset comprises 749 customers; 37.65% of them have churned and the average monthly fee is $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
- [q2] Churn varies little by plan: Basic is highest at 38.87%, followed by Standard at 36.68% and Premium at 36.60% — only 2.27 percentage points separate the highest (Basic) and lowest (Premium) tiers.
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Ranking: Basic, Standard, Premium
  - Derived difference(churn_rate_basic_pct, churn_rate_premium_pct): 2.27
- [q3] Churn by signup cohort is essentially flat: the 2024 cohort is highest at 39.83%, then 2021 at 38.02%, 2023 at 37.05% and 2022 lowest at 36.74% — a spread of just 3.09 percentage points between the highest and lowest cohorts, with the newest cohort churning most.
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Ranking: 2024, 2021, 2023, 2022
  - Derived difference(churn_rate_cohort_2024_pct, churn_rate_cohort_2022_pct): 3.09
- [q4] Contract type is the strongest churn differentiator: Monthly contracts churn at 48.32% versus 21.85% for Annual contracts — 26.47 percentage points higher, equivalent to a 121.11% relative increase (2.21× the Annual rate).
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
  - Derived difference(churn_rate_monthly_pct, churn_rate_annual_pct): 26.47
  - Derived ratio(churn_rate_monthly_pct, churn_rate_annual_pct): 2.21
- [q5] The at-risk segment (support_tickets >= 5 and satisfaction_score <= 2) contains 100 customers — 13.35% of the customer base — and churns at 71.0%, which is 33.35 percentage points above the overall churn rate of 37.65%.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
  - Derived share(at_risk_customer_count, customer_count): 13.35
  - Derived difference(at_risk_churn_rate_pct, churn_rate_pct): 33.35
- [q6] Customer tenure averages 20.81 months, with a median of 19.0 months and a sample standard deviation of 13.25 months — a wide spread relative to the mean. Average satisfaction is 3.42 among customers with a recorded score, and 27 customers are missing a satisfaction score.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
- [q7] Lifetime value rises steeply with plan tier: Premium averages $1,816.78, Standard $868.83 and Basic $463.46. Premium LTV is 292.01% above Basic — roughly 3.92× as high.
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401545, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic
  - Derived ratio(ltv_premium, ltv_basic): 3.92

## Limitations
- Satisfaction scores are missing for 27 customers; satisfaction-dependent results (mean satisfaction and the at-risk segment) exclude them and could be biased if missingness is not random.
- This is a single snapshot analysed with descriptive statistics only; no significance testing was performed, so small differences between plans or cohorts (roughly 2–3 percentage points) may not be statistically meaningful, and observed associations (e.g., contract type vs churn) are not proof of causation.
- lifetime_value is taken as given from the cleaned data — its derivation and currency unit are not documented in this handoff; monetary figures are presented in dollars by assumption.

## Conclusion
Churn is driven less by plan tier or signup cohort than by contract type and service friction. The highest-impact retention levers are migrating Monthly customers (48.32% churn) toward Annual contracts (21.85% churn) and proactively intervening with the 100-customer at-risk segment, which churns at 71.0%. Meanwhile, Premium customers — worth $1,816.78 on average, about 3.92× Basic — represent the most valuable segment to protect.
