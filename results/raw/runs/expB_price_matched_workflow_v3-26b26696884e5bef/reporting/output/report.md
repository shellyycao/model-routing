# Retail Sales Performance Report (2023-2024)

The business generated $445,325.09 in total revenue across 520 orders in 2023-2024. Year-over-year revenue increased by 10.08%. The East region led regional performance, and 2024 quarterly revenue peaked in Q3. High-discount electronics orders contributed $50,035.33, while revenue distribution was skewed by a few high-value transactions.

## Key findings
- [q1] Total revenue for the period was $445,325.09 from 520 orders, resulting in an average order value of $856.39.
  - Reported values: total_revenue=445325.08999999997, order_count=520.0, average_order_value=856.3944038461538
- [q2] Revenue varied by region, with the East region generating $130,516.69 and the South region generating $90,534.49.
  - Reported values: revenue_north=124845.75, revenue_south=90534.49, revenue_east=130516.69, revenue_west=99428.16
  - Ranking: East, North, West, South
- [q3] In 2024, quarterly revenue increased from $36,108.31 in Q1 to a peak of $71,674.99 in Q3, before settling at $68,948.71 in Q4.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Ranking: Q3, Q4, Q2, Q1
- [q4] Revenue increased from $211,976.29 in 2023 to $233,348.80 in 2024, representing a year-over-year increase of 10.08%.
  - Reported values: revenue_2023=211976.28999999998, revenue_2024=233348.80000000002, revenue_yoy_change_pct=10.082500264534321
  - Direction: increase
- [q5] There were 22 high-discount electronics orders (discount >= 20%), contributing $50,035.33 to total revenue.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
  - Derived share(electronics_high_discount_revenue, total_revenue): 11.2
- [q6] Order revenue distribution was right-skewed: the mean was $856.39 while the median was $313.28, with a sample standard deviation of $1,295.74. Values ranged from $5.27 to $7,844.02.
  - Reported values: order_revenue_mean=856.3944038461538, order_revenue_median=313.275, order_revenue_std=1295.7423896952698, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] The business served 222 unique customers. The top customer contributed $27,793.13 in revenue, accounting for 6.24% of the total.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.241087830914715

## Limitations
- The analysis assumes the cleaned dataset is complete for the 2023-2024 period; unexported or deleted orders are not represented.
- Customer concentration analysis relies on customer_id and does not account for potential duplicate identities or corporate hierarchies.

## Conclusion
The business shows healthy growth with a 10% year-over-year revenue increase. Regional performance is strongest in the East. The significant gap between mean and median order revenue indicates reliance on a subset of high-value orders, a risk also reflected in the top customer share. Monitoring the high-discount electronics segment is recommended given its 11% revenue contribution.
