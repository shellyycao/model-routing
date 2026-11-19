# 2023-2024 Retail Sales Performance Report

This report analyzes verified retail sales data from 2023-2024. Total revenue reached $445,325.09 across 520 orders. The business experienced a 10.1% year-over-year revenue increase in 2024, driven by strong performance in the East region and a recovery in the second half of 2024.

## Key findings
- [q1] The dataset contains 520 orders generating a total revenue of $445,325.09, resulting in an average order value of $856.39.
  - Reported values: total_revenue=445325.09, order_count=520.0, average_order_value=856.39
- [q2] Revenue varied by region, with the East region generating the most revenue at $130,516.69, followed by North ($124,845.75), West ($99,428.16), and South ($90,534.49).
  - Reported values: revenue_north=124845.75, revenue_south=90534.49, revenue_east=130516.69, revenue_west=99428.16
  - Ranking: East, North, West, South
- [q3] In 2024, quarterly revenue showed an upward trend, ranking from Q4 ($68,948.71) and Q3 ($71,674.99) as the strongest quarters, down to Q2 ($56,616.79) and Q1 ($36,108.31).
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Ranking: Q3, Q4, Q2, Q1
- [q4] Comparing 2024 to 2023, revenue increased from $211,976.29 to $233,348.80, representing a year-over-year growth of 10.1%.
  - Reported values: revenue_2023=211976.29, revenue_2024=233348.8, revenue_yoy_change_pct=10.08
  - Direction: increase
- [q5] There were 22 high-discount Electronics orders (discount >= 20%), which contributed $50,035.33 to the total revenue.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
  - Derived share(electronics_high_discount_revenue, total_revenue): 11.2
- [q6] Order revenue distribution is right-skewed: while the mean is $856.39, the median is $313.28. The standard deviation is $1,295.74, with a minimum of $5.27 and a maximum of $7,844.02.
  - Reported values: order_revenue_mean=856.39, order_revenue_median=313.28, order_revenue_std=1295.74, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] The customer base of 222 unique customers shows moderate concentration; the top customer generated $27,793.13 in revenue, accounting for 6.2% of total sales.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.24

## Limitations
- The analysis relies on a single export file and may not capture real-time changes or returns processed after the export date.
- Customer concentration analysis is limited to revenue share and does not account for order frequency or profitability.

## Conclusion
The business demonstrated solid growth in 2024, reversing or improving upon 2023 figures. The East region leads performance, and the second half of 2024 showed significant strength. High-discount Electronics orders form a notable portion of revenue, warranting review of margin impacts.
