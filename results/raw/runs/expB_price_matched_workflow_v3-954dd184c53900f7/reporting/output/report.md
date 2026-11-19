# 2023-2024 Retail Sales Performance Report

This report analyzes 520 verified retail orders from 2023-2024. Total revenue reached $445,325, with a 10.1% year-over-year increase. The East region led regional performance, and 2024 Q3 was the strongest quarter. High-discount electronics orders contributed $50,035 in revenue.

## Key findings
- [q1] The dataset contains 520 orders generating a total revenue of $445,325.09, resulting in an average order value of $856.39.
  - Reported values: total_revenue=445325.08999999997, order_count=520.0, average_order_value=856.3944038461538
- [q2] Regional revenue performance was led by the East region ($130,516.69), followed by North ($124,845.75), West ($99,428.16), and South ($90,534.49).
  - Reported values: revenue_east=130516.69, revenue_north=124845.75, revenue_west=99428.16, revenue_south=90534.49
  - Ranking: East, North, West, South
- [q3] In 2024, revenue trended upward through Q3 before a slight dip in Q4. Q3 was the strongest quarter ($71,674.99), followed by Q4 ($68,948.71), Q2 ($56,616.79), and Q1 ($36,108.31).
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Ranking: Q3, Q4, Q2, Q1
- [q4] Revenue increased from $211,976.29 in 2023 to $233,348.80 in 2024, representing a year-over-year growth of 10.1%.
  - Reported values: revenue_2023=211976.28999999998, revenue_2024=233348.80000000002, revenue_yoy_change_pct=10.082500264534321
  - Direction: increase
- [q5] There were 22 orders in the Electronics category with a discount of 20% or higher, generating a combined revenue of $50,035.33.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
- [q6] Order revenue distribution is right-skewed. While the mean is $856.39, the median is $313.28. Order values ranged from a minimum of $5.27 to a maximum of $7,844.02, with a standard deviation of $1,295.74.
  - Reported values: order_revenue_mean=856.3944038461538, order_revenue_median=313.275, order_revenue_std=1295.7423896952698, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] The business serves 222 unique customers. The top customer accounts for $27,793.13 in revenue, representing 6.2% of total revenue.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.241087830914715

## Limitations
- The analysis includes 'UNKNOWN' customer IDs in the unique customer count, which may slightly overstate the actual number of distinct customers.
- The dataset represents a snapshot of cleaned orders and may not capture returns or cancellations occurring after the order date.

## Conclusion
The business shows healthy growth with a 10.1% revenue increase in 2024. The East region and Q3 performance are key drivers. However, the high average order value relative to the median suggests reliance on high-value orders, and the top customer concentration (6.2%) warrants monitoring.
