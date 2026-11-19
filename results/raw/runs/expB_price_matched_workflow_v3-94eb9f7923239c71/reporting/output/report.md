# 2023-2024 Retail Sales Performance Report

This report details verified sales performance for 2023-2024. Total revenue reached $445,325.09 across 520 orders. Year-over-year revenue grew by 10.08%. The East region led regional sales, while 2024 Q3 was the strongest quarter. High-discount electronics orders contributed $50,035.33 in revenue.

## Key findings
- [q1] Overall performance totaled $445,325.09 in revenue from 520 orders, resulting in an average order value of $856.39.
  - Reported values: total_revenue=445325.09, order_count=520.0, average_order_value=856.39
- [q2] Regional revenue was led by the East region ($130,516.69), followed by North ($124,845.75), West ($99,428.16), and South ($90,534.49).
  - Reported values: revenue_east=130516.69, revenue_north=124845.75, revenue_west=99428.16, revenue_south=90534.49
  - Ranking: East, North, West, South
- [q3] In 2024, quarterly revenue increased from $36,108.31 in Q1 to a peak of $71,674.99 in Q3, before settling at $68,948.71 in Q4.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Ranking: Q3, Q4, Q2, Q1
- [q4] Revenue increased 10.08% year-over-year, rising from $211,976.29 in 2023 to $233,348.80 in 2024.
  - Reported values: revenue_2023=211976.29, revenue_2024=233348.8, revenue_yoy_change_pct=10.08
  - Direction: increase
- [q5] There were 22 high-discount Electronics orders (discount ≥ 20%), generating $50,035.33 in revenue.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
- [q6] Order revenue distribution was right-skewed: the mean was $856.39 while the median was $313.28, with a standard deviation of $1,295.74. Values ranged from $5.27 to $7,844.02.
  - Reported values: order_revenue_mean=856.39, order_revenue_median=313.28, order_revenue_std=1295.74, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] The customer base of 222 unique customers shows moderate concentration; the top customer contributed $27,793.13, representing 6.24% of total revenue.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.24

## Limitations
- The analysis assumes the 'cleaning' stage successfully handled all data quality issues (e.g., missing values, duplicates) in the raw export.
- The dataset represents a snapshot of order exports; it may not capture returns, cancellations, or pending orders not yet in the system.
- Customer concentration analysis relies on a single customer ID field; shared accounts or guest checkouts could affect the accuracy of the unique customer count.

## Conclusion
The business shows healthy growth with a 10.08% revenue increase in 2024. While the East and North regions are the primary revenue drivers, the strong performance in Q3 and Q4 suggests positive momentum. The high variance in order values and the specific contribution of high-discount electronics warrant continued monitoring of pricing strategies and regional performance.
