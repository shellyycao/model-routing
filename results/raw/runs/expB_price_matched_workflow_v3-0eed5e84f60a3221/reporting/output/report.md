# 2023-2024 Retail Sales Performance Report

Analysis of 520 cleaned retail orders reveals total revenue of $445,325.09 for 2023-2024, with a strong 10.1% year-over-year growth. The East region leads regional performance, while 2024 quarterly trends show revenue peaking in Q3. High-discount electronics orders represent a modest portion of sales, and customer concentration risk appears low with the top customer contributing 6.2% of total revenue.

## Key findings
- [q1] The dataset contains 520 orders generating a total revenue of $445,325.09, resulting in an average order value of $856.39.
  - Reported values: total_revenue=445325.08999999997, order_count=520.0, average_order_value=856.3944038461538
- [q2] Regional revenue performance is led by the East region at $130,516.69, followed by North at $124,845.75, West at $99,428.16, and South at $90,534.49.
  - Reported values: revenue_north=124845.75, revenue_south=90534.49, revenue_east=130516.69, revenue_west=99428.16
  - Ranking: East, North, West, South
- [q3] In 2024, quarterly revenue increased from $36,108.31 in Q1 to a peak of $71,674.99 in Q3, before settling at $68,948.71 in Q4.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Ranking: Q3, Q4, Q2, Q1
- [q4] Revenue increased from $211,976.29 in 2023 to $233,348.80 in 2024, representing a 10.1% year-over-year growth.
  - Reported values: revenue_2023=211976.28999999998, revenue_2024=233348.80000000002, revenue_yoy_change_pct=10.082500264534321
  - Direction: increase
- [q5] There were 22 high-discount Electronics orders (discount ≥ 20%), contributing a combined revenue of $50,035.33.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
- [q6] Order revenue distribution shows a mean of $856.39 and median of $313.28, with a standard deviation of $1,295.74. Values range from a minimum of $5.27 to a maximum of $7,844.02.
  - Reported values: order_revenue_mean=856.3944038461538, order_revenue_median=313.275, order_revenue_std=1295.7423896952698, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] The business serves 222 unique customers. The top customer generated $27,793.13 in revenue, accounting for 6.2% of total revenue.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.241087830914715

## Limitations
- The analysis covers only 2023-2024 data; long-term trends cannot be established.
- Profitability analysis was not in scope; high-discount revenue figures do not reflect margin impact.
- Data quality is dependent on the preceding cleaning stage validation.

## Conclusion
The business demonstrates healthy growth with a 10.1% revenue increase in 2024. The East region is the strongest performer, and Q3 2024 showed the highest quarterly revenue. With 222 unique customers and no single customer exceeding 6.3% of revenue, the revenue base appears well-diversified.
