# 2023-2024 Retail Sales Performance Report

This report details the verified sales performance for 2023-2024 based on 520 cleaned orders. Total revenue reached $445,325.09, with a 10.08% year-over-year increase. The East region led regional performance, while 2024 Q3 was the strongest quarter. High-discount electronics orders contributed $50,035.33 in revenue.

## Key findings
- [q1] The business generated a total revenue of $445,325.09 from 520 orders, resulting in an average order value of $856.39.
  - Reported values: total_revenue=445325.08999999997, order_count=520.0, average_order_value=856.3944038461538
- [q2] Revenue varied by region, with the East region generating the highest revenue at $130,516.69, followed by North ($124,845.75), West ($99,428.16), and South ($90,534.49).
  - Reported values: revenue_east=130516.69, revenue_north=124845.75, revenue_west=99428.16, revenue_south=90534.49
  - Ranking: East, North, West, South
- [q3] In 2024, revenue trended upward through the first three quarters, peaking in Q3 at $71,674.99 before decreasing to $68,948.71 in Q4. Q1 was the lowest performing quarter at $36,108.31.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Ranking: Q3, Q4, Q2, Q1
- [q4] Revenue increased from $211,976.29 in 2023 to $233,348.80 in 2024, representing a year-over-year growth of 10.08%.
  - Reported values: revenue_2023=211976.28999999998, revenue_2024=233348.80000000002, revenue_yoy_change_pct=10.082500264534321
  - Direction: increase
- [q5] There were 22 high-discount electronics orders (discount ≥ 20%), which collectively generated $50,035.33 in revenue.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
- [q6] Order revenue showed significant variation, with a mean of $856.39 and a median of $313.28. The standard deviation was $1,295.74, with values ranging from a minimum of $5.27 to a maximum of $7,844.02.
  - Reported values: order_revenue_mean=856.3944038461538, order_revenue_median=313.275, order_revenue_std=1295.7423896952698, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] The dataset contains 222 unique customers. The top customer contributed $27,793.13 in revenue, accounting for 6.24% of the total revenue.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.241087830914715

## Limitations
- The analysis relies on the 'discount_pct' field as provided in the cleaned dataset without verifying its calculation method against raw prices.
- Customer concentration analysis is limited to the top customer and does not provide a full view of revenue distribution across the customer base.

## Conclusion
The business demonstrated solid growth in 2024 with a 10.08% revenue increase compared to 2023. While the East and North regions are the primary revenue drivers, the strong performance in Q3 2024 suggests positive momentum. However, the large gap between mean and median order values indicates that revenue is heavily skewed by high-value transactions, and the reliance on the top customer for 6.24% of revenue warrants attention regarding customer concentration risk.
