# Retail Sales Performance Report 2023-2024

Across 2023-2024 the retail business generated $445,325.09 in revenue from 520 orders, an average order value of $856.39. Revenue grew 10.08% year over year, from $211,976.29 in 2023 to $233,348.80 in 2024. The East region led all regions with $130,516.69, and 2024 revenue peaked in Q3 at $71,674.99. Order values are strongly right-skewed toward a minority of large orders, while customer concentration is low: the top customer accounts for only 6.24% of total revenue.

## Key findings
- [q1] Overall performance: total revenue of $445,325.09 was generated across 520 orders, giving an average order value of $856.39.
  - Reported values: total_revenue=445325.08999999997, order_count=520.0, average_order_value=856.3944038461538
  - Direction: not_applicable
- [q2] Regional comparison: the East led with $130,516.69, followed by the North ($124,845.75), the West ($99,428.16) and the South ($90,534.49); the East out-earned the lowest-performing South by $39,982.20.
  - Reported values: revenue_north=124845.75, revenue_south=90534.49, revenue_east=130516.69, revenue_west=99428.16
  - Direction: not_applicable
  - Ranking: East, North, West, South
  - Derived difference(revenue_east, revenue_south): 39982.2
- [q3] 2024 quarterly trend: revenue climbed from $36,108.31 in Q1 to $56,616.79 in Q2 and a peak of $71,674.99 in Q3, before easing to $68,948.71 in Q4; peak-quarter Q3 exceeded Q1 by $35,566.68.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Ranking: Q3, Q4, Q2, Q1
  - Derived difference(revenue_2024_q3, revenue_2024_q1): 35566.68
- [q4] Year-over-year change: revenue increased from $211,976.29 in 2023 to $233,348.80 in 2024, a 10.08% rise worth $21,372.51 in additional revenue.
  - Reported values: revenue_2023=211976.28999999998, revenue_2024=233348.80000000002, revenue_yoy_change_pct=10.082500264534321
  - Direction: increase
  - Derived difference(revenue_2024, revenue_2023): 21372.51
- [q5] High-discount Electronics: 22 orders had discounts of 20% or more, generating $50,035.33 in revenue - about 11.24% of total company revenue, averaging roughly $2,274.33 per order.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
  - Direction: not_applicable
  - Derived share(electronics_high_discount_revenue, total_revenue): 11.24
  - Derived ratio(electronics_high_discount_revenue, electronics_high_discount_orders): 2274.33
- [q6] Order revenue distribution: revenue per order is highly right-skewed - the mean of $856.39 is about 2.73x the median of $313.28, with a large standard deviation of $1,295.74 and values spanning $5.27 to $7,844.02.
  - Reported values: order_revenue_mean=856.3944038461538, order_revenue_median=313.275, order_revenue_std=1295.7423896952698, order_revenue_min=5.27, order_revenue_max=7844.02
  - Direction: not_applicable
  - Derived ratio(order_revenue_mean, order_revenue_median): 2.73
- [q7] Customer concentration: 222 distinct customers purchased in the period; the highest-revenue customer contributed $27,793.13, just 6.24% of total revenue, indicating a well-diversified customer base.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.241087830914715
  - Direction: not_applicable

## Limitations
- Only two years of data are available, so the 2024 quarterly pattern cannot be confirmed as a repeatable seasonal trend.
- The analysis is revenue-based only; product costs and margins are not included, so the profitability of high-discount Electronics orders is unknown.
- Order revenue is extremely skewed (standard deviation $1,295.74 versus a mean of $856.39), so averages are heavily influenced by a small number of very large orders.
- Regional totals are not normalized for store count, market size or customer base, so regional gaps may reflect scale rather than performance quality.

## Conclusion
The business grew a healthy 10.08% in 2024, with momentum building from Q1 to a Q3 peak before a mild Q4 easing. Recommended priorities: understand and replicate the Q2-Q3 drivers, investigate the South region's lower revenue ($90,534.49), review the margin impact of deep-discount Electronics sales, and protect the diversified customer base that keeps revenue resilient.
