# Retail Sales Performance Report: 2023–2024

Cleaned 2023–2024 order data (520 orders) shows total revenue of $445,325.09, with revenue growing 10.08% year over year, from $211,976.29 in 2023 to $233,348.80 in 2024. The East region leads regional revenue at $130,516.69, while the South trails at $90,534.49. Within 2024, revenue strengthened through the year, peaking in Q3 ($71,674.99). Order revenue is highly right-skewed (median $313.28 vs. mean $856.39), and customer concentration is moderate: the top of 222 customers contributes 6.24% of revenue. High-discount (>=20%) Electronics orders are a meaningful slice of the business at $50,035.33 (11.24% of total revenue).

## Key findings
- [q1] Overall performance: total revenue of $445,325.09 across 520 cleaned orders, giving an average order value of $856.39.
  - Reported values: total_revenue=445325.08999999997, order_count=520.0, average_order_value=856.3944038461538
  - Direction: not_applicable
- [q2] Regional comparison: East leads with $130,516.69, followed by North ($124,845.75), West ($99,428.16) and South ($90,534.49); the gap between the strongest (East) and weakest (South) region is $39,982.20.
  - Reported values: revenue_north=124845.75, revenue_south=90534.49, revenue_east=130516.69, revenue_west=99428.16
  - Direction: not_applicable
  - Ranking: East, North, West, South
  - Derived difference(revenue_east, revenue_south): 39982.2
- [q3] 2024 quarterly trend: revenue climbed from Q1 ($36,108.31) to Q2 ($56,616.79), peaking in Q3 ($71,674.99) before easing slightly in Q4 ($68,948.71); Q3 exceeded Q1 by $35,566.68.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Direction: not_applicable
  - Ranking: Q3, Q4, Q2, Q1
  - Derived difference(revenue_2024_q3, revenue_2024_q1): 35566.68
- [q4] Year-over-year change: revenue increased from $211,976.29 in 2023 to $233,348.80 in 2024, a rise of 10.08% (an absolute gain of $21,372.51).
  - Reported values: revenue_2023=211976.28999999998, revenue_2024=233348.80000000002, revenue_yoy_change_pct=10.082500264534321
  - Direction: increase
  - Derived difference(revenue_2024, revenue_2023): 21372.51
- [q5] High-discount electronics: 22 Electronics orders carried a discount of 20% or more, generating $50,035.33 in revenue, equivalent to 11.24% of total revenue.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
  - Direction: not_applicable
  - Derived share(electronics_high_discount_revenue, total_revenue): 11.24
- [q6] Order revenue distribution is strongly right-skewed: the mean ($856.39) is 2.73x the median ($313.28), with a standard deviation of $1,295.74 and values spanning $5.27 to $7,844.02, indicating a minority of large orders pull the average up.
  - Reported values: order_revenue_mean=856.3944038461538, order_revenue_median=313.275, order_revenue_std=1295.7423896952698, order_revenue_min=5.27, order_revenue_max=7844.02
  - Direction: not_applicable
  - Derived ratio(order_revenue_mean, order_revenue_median): 2.73
- [q7] Customer concentration is moderate: 222 unique customers placed orders, and the single highest-revenue customer contributed $27,793.13, or 6.24% of total revenue, so no single account dominates sales.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.241087830914715
  - Direction: not_applicable

## Limitations
- Only two years of data are available, so the year-over-year growth rate rests on a single year-pair and cannot establish a longer-term trend.
- The analysis measures revenue only; no cost or margin data was provided, so profitability of regions, quarters or discounted orders cannot be assessed.
- The 20% threshold defining 'high-discount' electronics orders is an arbitrary cut-off, and results would change with a different threshold.
- It is not stated whether the revenue figures are net of discounts, which affects interpretation of the high-discount segment.
- The Q4 2024 dip versus Q3 cannot be attributed to a cause (seasonality, promotions, data coverage) from this dataset alone.
- The mean order value is heavily influenced by large outlier orders, as evidenced by the mean being 2.73x the median.

## Conclusion
The business grew healthily in 2024, with revenue up 10.08% to $233,348.80 and momentum building through the year, peaking in Q3. East and North are the revenue engines, while the South region underperforms and may warrant targeted investment. Revenue is diversified across 222 customers with no single-account dependency, but sales are driven by a minority of high-value orders, and 11.24% of revenue comes from deeply discounted electronics — a segment whose margin impact should be reviewed before expanding discount-led promotions.
