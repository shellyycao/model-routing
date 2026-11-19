# Customer Churn Analysis Report

Analysis of 749 customers reveals an overall churn rate of 37.7%. Monthly-contract customers churn at more than double the rate of annual-contract customers. A high-risk segment of 100 customers with poor satisfaction and frequent support contacts churns at 71%. Premium-plan customers generate nearly 4× the lifetime value of Basic customers, underscoring the revenue importance of retention at the top tier.

## Key findings
- [q1] The cleaned dataset contains 749 customers. Overall, 37.7% have churned, and the average monthly fee across all customers is $42.11.
  - Reported values: customer_count=749.0, churn_rate_pct=37.6502002670227, avg_monthly_fee=42.106154873164215
- [q2] Churn rates differ modestly across plans: Basic is highest at 38.9%, followed by Standard at 36.7%, and Premium at 36.6%. The spread is narrow (~2.3 percentage points), suggesting plan tier alone is not a strong churn driver.
  - Reported values: churn_rate_basic_pct=38.87240356083086, churn_rate_standard_pct=36.67953667953668, churn_rate_premium_pct=36.60130718954248
  - Ranking: Basic, Standard, Premium
  - Derived difference(churn_rate_basic_pct, churn_rate_premium_pct): 2.27
- [q3] Churn rates by signup cohort show no strong linear trend but the 2024 cohort is highest at 39.8%, followed by 2021 at 38.0%, 2023 at 37.1%, and 2022 at 36.7%. The 2024 cohort's elevated rate may reflect shorter tenure and less product familiarity.
  - Reported values: churn_rate_cohort_2021_pct=38.02083333333333, churn_rate_cohort_2022_pct=36.74418604651163, churn_rate_cohort_2023_pct=37.05357142857143, churn_rate_cohort_2024_pct=39.83050847457627
  - Ranking: 2024, 2021, 2023, 2022
- [q4] Contract type is a strong churn predictor. Monthly-contract customers churn at 48.3% versus 21.9% for annual-contract customers — a relative increase of 121.1%, meaning monthly customers churn at more than twice the rate of annual customers.
  - Reported values: churn_rate_monthly_pct=48.322147651006716, churn_rate_annual_pct=21.85430463576159, churn_monthly_vs_annual_change_pct=121.11043319097013
  - Direction: increase
- [q5] 100 customers meet the at-risk criteria (≥5 support tickets and satisfaction score ≤2). This segment churns at 71.0%, nearly double the overall rate, making it the highest-priority retention target.
  - Reported values: at_risk_customer_count=100.0, at_risk_churn_rate_pct=71.0
  - Derived difference(at_risk_churn_rate_pct, churn_rate_pct): 33.35
- [q6] Average customer tenure is 20.8 months (median 19.0 months, std 13.2 months), indicating a wide spread in customer longevity. Mean satisfaction score is 3.42 out of 5 among the 722 customers with a recorded score; 27 customers have a missing satisfaction score.
  - Reported values: tenure_mean=20.81041388518024, tenure_median=19.0, tenure_std=13.24739298193327, satisfaction_mean=3.4168975069252077, satisfaction_missing_count=27.0
  - Derived difference(customer_count, satisfaction_missing_count): 722.0
- [q7] Mean lifetime value rises sharply with plan tier: Basic $463, Standard $869, Premium $1,817. Premium LTV is 292.0% higher than Basic, representing a nearly 4× revenue multiplier and making Premium customer retention especially valuable.
  - Reported values: ltv_basic=463.4573590504451, ltv_standard=868.8301544401545, ltv_premium=1816.7777124183006, premium_vs_basic_ltv_change_pct=292.00536509779596
  - Direction: increase
  - Ranking: Premium, Standard, Basic

## Limitations
- 27 customers have missing satisfaction scores, which may introduce slight bias into satisfaction-based metrics and the at-risk segment definition.
- Cohort churn rates for the 2024 cohort may be understated or overstated because those customers have had less time to churn; a survival-analysis approach would give more comparable cohort estimates.
- Lifetime value is a derived column from the cleaned data; its calculation methodology (e.g., whether it accounts for discounting or projected future revenue) is not documented, limiting interpretability.
- The at-risk segment uses fixed thresholds (tickets ≥5, satisfaction ≤2) that were not validated against a holdout set; predictive accuracy of this rule is unknown.
- The dataset is a single snapshot with no timestamp for churn events, preventing time-series or survival modelling of churn dynamics.

## Conclusion
With more than one-third of customers churning, the business faces a significant retention challenge. The most actionable levers are: (1) converting monthly-contract customers to annual contracts, which is associated with a 121% relative reduction in churn risk; (2) immediately intervening with the 100 at-risk customers churning at 71%; and (3) prioritising Premium-plan retention given their $1,817 average LTV — nearly 4× that of Basic customers. Cohort and plan-tier differences are comparatively small, suggesting contract type and service experience are the primary drivers to address.
