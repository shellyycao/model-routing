# 2023-2024 Retail Sales Performance Report

Total revenue across 520 orders amounted to $445,325.09, with an average order value of $856.39. The business achieved 10.08% year-over-year revenue growth from 2023 to 2024. The East region led regional performance, while 2024 quarterly revenue peaked in Q3. High-discount Electronics orders contributed $50,035.33, and the top customer accounted for 6.24% of total revenue.

## Key findings
- [q1] The dataset contains 520 orders generating a total revenue of $445,325.09, resulting in an average order value of $856.39.
  - Reported values: total_revenue=445325.09, order_count=520.0, average_order_value=856.39
- [q2] Revenue varied by region, with the East region generating the highest revenue at $130,516.69, followed by North at $124,845.75, West at $99,428.16, and South at $90,534.49.
  - Reported values: revenue_east=130516.69, revenue_north=124845.75, revenue_west=99428.16, revenue_south=90534.49
  - Ranking: East, North, West, South
- [q3] In 2024, quarterly revenue increased from $36,108.31 in Q1 to a peak of $71,674.99 in Q3, before slightly decreasing to $68,948.71 in Q4.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Ranking: Q3, Q4, Q2, Q1
- [q4] Year-over-year revenue increased by 10.08%, rising from $211,976.29 in 2023 to $233,348.80 in 2024.
  - Reported values: revenue_2023=211976.29, revenue_2024=233348.8, revenue_yoy_change_pct=10.08
  - Direction: increase
- [q5] There were 22 high-discount Electronics orders (discount_pct >= 20%), generating a combined revenue of $50,035.33.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
- [q6] Order revenue displayed a right-skewed distribution: while the mean was $856.39, the median was considerably lower at $313.28, with a standard deviation of $1,295.74. Values ranged from a minimum of $5.27 to a maximum of $7,844.02.
  - Reported values: order_revenue_mean=856.39, order_revenue_median=313.28, order_revenue_std=1295.74, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] The 222 unique customers show moderate concentration; the top customer generated $27,793.13 in revenue, representing 6.24% of the total.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.24

## Limitations
- The analysis relies on a single cleaned export file and may not reflect real-time operational data.
- Customer concentration analysis is limited to revenue share and does not assess purchase frequency or retention.
- Regional and quarterly aggregations do not control for seasonality or promotional events.

## Conclusion
The business demonstrated solid growth in 2024, with revenue increasing by over 10% year-over-year. The East and North regions are the primary revenue drivers, and the 2024 quarterly trend suggests strong performance in the second half. While customer concentration is not critical, the skewed order revenue distribution indicates that a minority of high-value orders significantly impacts totals, warranting focused attention on large transactions.
