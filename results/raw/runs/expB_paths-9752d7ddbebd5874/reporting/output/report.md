# Retail Sales Performance Report: 2023–2024

Across 508 orders, the business generated $441,146 in total revenue over the 2023–2024 period, with a healthy 9.9% year-over-year increase from 2023 to 2024. The East region led all regions in revenue. A data issue prevented quarterly 2024 breakdowns from being computed. High-discount Electronics orders represent a notable revenue concentration, and the overall order revenue distribution is highly skewed, signalling a wide mix of order sizes.

## Key findings
- [q1] The dataset contains 508 orders generating total revenue of $441,146. The average order value is $868.40, though this figure is heavily influenced by large outlier orders (see q6).
  - Reported values: total_revenue=441146.01, order_count=508.0, average_order_value=868.3976574803149
  - Direction: not_applicable
- [q2] The East region produced the highest revenue at $128,297, followed closely by North at $124,324, then West at $98,835, and South at $89,690. The East–South gap is approximately $38,607.
  - Reported values: revenue_north=124324.32, revenue_south=89689.71, revenue_east=128297.14, revenue_west=98834.84
  - Direction: not_applicable
  - Ranking: East, North, West, South
  - Derived difference(revenue_east, revenue_south): 38607.43
- [q3] Quarterly revenue figures for all four quarters of 2024 (Q1–Q4) returned $0.00, indicating that the analysis pipeline could not assign 2024 orders to calendar quarters. This is likely a consequence of date-parsing failures in the cleaning stage and should be treated as unreliable.
  - Reported values: revenue_2024_q1=0.0, revenue_2024_q2=0.0, revenue_2024_q3=0.0, revenue_2024_q4=0.0
  - Direction: no_change
- [q4] Revenue grew from $210,206 in 2023 to $230,940 in 2024, a year-over-year increase of approximately 9.9%. This represents an absolute gain of roughly $20,733.
  - Reported values: revenue_2023=210206.34, revenue_2024=230939.67, revenue_yoy_change_pct=9.86332286647492
  - Direction: increase
  - Derived difference(revenue_2024, revenue_2023): 20733.33
- [q5] 22 Electronics orders carried a discount of 20% or more, generating $50,035 in combined revenue. These high-discount orders account for approximately 11.3% of total revenue, suggesting meaningful margin exposure in this category.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
  - Direction: not_applicable
  - Derived share(electronics_high_discount_revenue, total_revenue): 11.34
- [q6] Order revenue ranges from $5.27 to $7,844.02. The mean order value is $868.40 but the median is only $315.76, confirming a right-skewed distribution driven by a small number of very large orders. The standard deviation of $1,307.86 further reflects this high variability.
  - Reported values: order_revenue_mean=868.3976574803149, order_revenue_median=315.76, order_revenue_std=1307.8582871421413, order_revenue_min=5.27, order_revenue_max=7844.02
  - Direction: not_applicable
- [q7] There are 222 unique customers. The single highest-revenue customer contributed $14,279, representing 3.2% of total revenue. This low concentration suggests the business is not overly dependent on any one customer.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=14278.81, top_customer_revenue_share_pct=3.236753745092243
  - Direction: not_applicable

## Limitations
- Both the cleaning and analysis pipeline stages reported validation failures; all findings should be interpreted with caution until root causes are resolved.
- The 2024 quarterly revenue figures (Q1–Q4) are all $0.00, almost certainly due to date-parsing errors in the cleaning stage. No quarterly trend analysis is possible from this run.
- The year-over-year and quarterly figures depend on correct date assignment; if dates were partially mis-parsed, the 2023/2024 split may also be inaccurate.
- The dataset covers only 508 orders, which may not be a complete export of all transactions for the period, limiting the representativeness of the findings.
- No product-level or margin data is available, so revenue figures cannot be translated into profitability conclusions.

## Conclusion
Despite pipeline validation failures, the available data indicates solid overall performance: $441,146 in revenue across 508 orders and a ~9.9% year-over-year revenue increase. The East and North regions are the strongest contributors. High-discount Electronics orders warrant margin scrutiny, and the highly skewed order distribution suggests a long tail of small transactions alongside a few very large ones. Customer concentration is low. The critical priority before the next reporting cycle is resolving the date-parsing failures so that quarterly trends can be accurately computed and all findings fully validated.
