# Retail Sales Performance Report (2023-2024)

This report analyzes verified retail sales data from 2023-2024. The business generated a total revenue of $445,325.09 across 520 orders. Year-over-year analysis reveals a healthy 10.1% revenue growth. The East region leads regional performance, while 2024 quarterly trends show revenue peaking in Q3. High-discount electronics orders represent a modest portion of total sales, and customer concentration risk appears low with the top customer contributing roughly 6.2% of total revenue.

## Key findings
- [q1] The overall performance for the period resulted in a total revenue of $445,325.09 from 520 orders, yielding an average order value of $856.39.
  - Reported values: total_revenue=445325.08999999997, order_count=520.0, average_order_value=856.3944038461538
- [q2] Regional revenue comparison indicates that the East region is the top performer with $130,516.69, followed by the North region at $124,845.75. The West and South regions generated $99,428.16 and $90,534.49 respectively.
  - Reported values: revenue_north=124845.75, revenue_south=90534.49, revenue_east=130516.69, revenue_west=99428.16
  - Ranking: East, North, West, South
- [q3] In 2024, quarterly revenue showed an upward trend through the first three quarters, peaking in Q3 at $71,674.99 before slightly decreasing to $68,948.71 in Q4. Q1 was the lowest performing quarter at $36,108.31.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Ranking: Q3, Q4, Q2, Q1
- [q4] Comparing year-over-year performance, revenue increased from $211,976.29 in 2023 to $233,348.80 in 2024, representing a growth of 10.1%.
  - Reported values: revenue_2023=211976.28999999998, revenue_2024=233348.80000000002, revenue_yoy_change_pct=10.082500264534321
  - Direction: increase
- [q5] There were 22 orders in the Electronics category with a discount of 20% or higher, generating a total revenue of $50,035.33.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
- [q6] The distribution of order revenue shows a mean of $856.39 and a median of $313.28, indicating a right-skewed distribution with a high standard deviation of $1,295.74. Order values ranged from a minimum of $5.27 to a maximum of $7,844.02.
  - Reported values: order_revenue_mean=856.3944038461538, order_revenue_median=313.275, order_revenue_std=1295.7423896952698, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] The customer base consists of 222 unique customers. The top customer contributed $27,793.13 in revenue, accounting for approximately 6.2% of the total revenue.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.241087830914715

## Limitations
- The analysis relies on a static export of order data; real-time fluctuations are not captured.
- Customer concentration analysis is limited to revenue contribution and does not assess purchase frequency or retention rates.

## Conclusion
The retail business demonstrates solid growth momentum with a 10.1% year-over-year revenue increase. The East region and Q3 2024 period represent the strongest performance areas. While the high average order value suggests effective upselling, the significant gap between mean and median order revenue indicates that a subset of high-value transactions drives a large portion of revenue. Customer concentration risk is currently low, providing a stable foundation for future operations.
