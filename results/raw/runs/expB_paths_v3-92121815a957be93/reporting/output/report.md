# Customer Churn Analysis Report – Key Findings

The analysis of 731 customers reveals an overall churn rate of 37.2% with modest variation across subscription plans and signup cohorts. Monthly contract holders churn at more than double the rate of annual contract holders, highlighting contract length as a key driver. An at‑risk segment of 100 customers shows a high churn of 71%. Tenure averages 21 months and satisfaction averages 3.42 on a 5‑point scale, though 27 scores are missing. Lifetime value (LTV) differs sharply by plan, with Premium customers delivering roughly $1,839 versus $466 for Basic, a 295% increase. These insights point to opportunities for targeted retention, contract restructuring, and plan‑specific value enhancement.

## Key findings
- [q1] The dataset contains 731 customers, with an overall churn rate of 37.2% and an average monthly fee of $42.14.
  - Reported values: customer_count=731.0, churn_rate_pct=37.2093023255814, avg_monthly_fee=42.137742818057454
- [q2] Churn rates differ by subscription plan, with Basic customers experiencing the highest churn (38.6%), followed by Standard (36.5%) and Premium (35.3%).
  - Reported values: churn_rate_basic_pct=38.60182370820669, churn_rate_standard_pct=36.507936507936506, churn_rate_premium_pct=35.333333333333336
  - Ranking: Basic, Standard, Premium
- [q3] Churn by signup cohort shows a slight variation across years, highest for the 2024 cohort (38.1%) and lowest for the 2023 cohort (36.4%).
  - Reported values: churn_rate_cohort_2021_pct=37.696335078534034, churn_rate_cohort_2022_pct=37.08920187793427, churn_rate_cohort_2023_pct=36.44859813084112, churn_rate_cohort_2024_pct=38.05309734513274
  - Ranking: 2024, 2021, 2022, 2023
- [q4] Customers on Monthly contracts churn at a rate 119% higher than those on Annual contracts, indicating a substantial increase.
  - Reported values: churn_rate_monthly_pct=47.80600461893764, churn_rate_annual_pct=21.812080536912752, churn_monthly_vs_annual_change_pct=119.17214425297564
  - Direction: increase
  - Derived ratio(churn_rate_monthly_pct, churn_rate_annual_pct): 2.19
- [q5] The identified at‑risk segment comprises 100 customers, of whom 71% have churned.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
- [q6] Across all customers, average tenure is 21 months (median 19, std dev 13.3). The mean satisfaction score is 3.42, with 27 customers missing a score.
  - Reported values: tenure_mean=20.99452804377565, tenure_median=19.0, tenure_std=13.28610243682788, satisfaction_mean=3.421875, satisfaction_missing_count=27.0
- [q7] Lifetime value varies strongly by plan: Premium customers generate $1,839, Standard $878, and Basic $466. Premium LTV is 295% higher than Basic.
  - Reported values: ltv_basic=465.84024316109424, ltv_standard=878.3645238095238, ltv_premium=1839.1815333333332, premium_vs_basic_ltv_change_pct=294.80949968019786
  - Direction: increase
  - Ranking: Premium, Standard, Basic
  - Derived difference(ltv_premium, ltv_basic): 1373.34

## Limitations
- The cleaning stage failed, so residual data quality issues (e.g., duplicate rows, inconsistent formats) may remain.
- Missing values for satisfaction_score (27 customers) were excluded from mean calculations, potentially biasing the satisfaction estimate.
- The analysis relies on simple aggregations; causal relationships (e.g., why contract type affects churn) are not established.
- At‑risk segment definition uses arbitrary thresholds (≥5 support tickets, ≤2 satisfaction) and may miss other at‑risk customers.

## Conclusion
Churn is substantial overall and especially high among monthly contract holders, suggesting that encouraging longer‑term contracts could improve retention. Plan‑specific strategies are warranted: Basic plans show the highest churn, while Premium plans deliver the greatest revenue per customer. Targeted outreach to the identified at‑risk segment could mitigate its 71% churn rate. Improving data cleaning processes will enhance future analyses.
