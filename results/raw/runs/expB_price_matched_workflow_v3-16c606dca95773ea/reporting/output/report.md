# Retail Sales Performance Report: 2023-2024

Total revenue for 2023-2024 was $445,325.09 across 520 cleaned orders, an average order value of $856.39. Revenue grew 10.08% year over year in 2024, building from $36,108.31 in Q1 to a $71,674.99 peak in Q3. East is the strongest region at $130,516.69. Order revenue is highly skewed toward a few large orders, and the top single customer accounts for 6.24% of revenue.

## Key findings
- [q1] Overall performance: total revenue of $445,325.09 was generated from 520 orders, giving an average order value of $856.39.
  - Reported values: total_revenue=445325.09, order_count=520.0, average_order_value=856.39
  - Direction: not_applicable
- [q2] Regional comparison: East leads with $130,516.69, followed by North ($124,845.75), West ($99,428.16) and South ($90,534.49); East outperforms the weakest region, South, by $39,982.20.
  - Reported values: revenue_north=124845.75, revenue_south=90534.49, revenue_east=130516.69, revenue_west=99428.16
  - Direction: not_applicable
  - Ranking: East, North, West, South
  - Derived difference(revenue_east, revenue_south): 39982.2
- [q3] 2024 quarterly trend: revenue climbed steadily from $36,108.31 in Q1 to $56,616.79 in Q2 and a peak of $71,674.99 in Q3, before easing slightly to $68,948.71 in Q4; Q3 exceeded Q1 by $35,566.68.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Direction: not_applicable
  - Ranking: Q3, Q4, Q2, Q1
  - Derived difference(revenue_2024_q3, revenue_2024_q1): 35566.68
- [q4] Year-over-year change: revenue increased 10.08%, rising from $211,976.29 in 2023 to $233,348.80 in 2024, an absolute gain of $21,372.51.
  - Reported values: revenue_2023=211976.29, revenue_2024=233348.8, revenue_yoy_change_pct=10.08
  - Direction: increase
  - Derived difference(revenue_2024, revenue_2023): 21372.51
- [q5] High-discount electronics: 22 Electronics orders carried a discount of 20% or more, contributing $50,035.33 in revenue, equal to 11.24% of total revenue from just 4.23% of all orders.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
  - Direction: not_applicable
  - Derived share(electronics_high_discount_revenue, total_revenue): 11.24
  - Derived share(electronics_high_discount_orders, order_count): 4.23
- [q6] Order revenue distribution is strongly right-skewed: the mean of $856.39 sits well above the median of $313.28, with a large standard deviation of $1,295.74 and values spanning $5.27 to $7,844.02, indicating a minority of very large orders pulls the average up.
  - Reported values: order_revenue_mean=856.39, order_revenue_median=313.28, order_revenue_std=1295.74, order_revenue_min=5.27, order_revenue_max=7844.02
  - Direction: not_applicable
- [q7] Customer concentration is low: 222 unique customers purchased in the period, and the highest-revenue customer spent $27,793.13, representing 6.24% of total revenue.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.24
  - Direction: not_applicable

## Limitations
- The analysis covers revenue only; no cost, margin or returns data were available, so the profitability of the 22 heavily discounted Electronics orders cannot be judged.
- Only two years of history exist, and the quarterly trend covers 2024 alone, so seasonal patterns cannot be separated from one-off events.
- Order revenue is highly skewed (standard deviation $1,295.74 exceeds the mean of $856.39), so averages are heavily influenced by a small number of large orders.
- Customer concentration was measured using only the single top customer; broader concentration (for example the top 5 or 10 customers) was not computed.
- The currency of revenue figures is not specified in the source data.

## Conclusion
2024 was a growth year, with revenue up 10.08% to $233,348.80 and momentum peaking in Q3 at $71,674.99. Priorities for stakeholders: build on the strong East and North regions, address the lagging South, review the margin impact of deep Electronics discounts, and manage the revenue risk embedded in a small number of very large orders.
