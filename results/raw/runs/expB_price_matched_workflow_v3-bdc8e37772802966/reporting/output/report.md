# 2023-2024 Retail Sales Performance Report

This report analyzes verified retail sales data from 2023 and 2024. Total revenue reached $445,325.08 across 520 orders. The business experienced a 10.08% year-over-year revenue increase, with the East region leading regional performance. However, high-discount electronics orders and significant customer concentration present areas for strategic review.

## Key findings
- [q1] The dataset contains 520 orders generating a total revenue of $445,325.08, resulting in an average order value of $856.39.
  - Reported values: total_revenue=445325.09, order_count=520.0, average_order_value=856.39
- [q2] Revenue performance varied by region. The East region generated the highest revenue at $130,516.69, followed by North at $124,845.75. The West region recorded $99,428.16, and the South region generated the lowest revenue at $90,534.49.
  - Reported values: revenue_east=130516.69, revenue_north=124845.75, revenue_west=99428.16, revenue_south=90534.49
  - Ranking: East, North, West, South
- [q3] In 2024, quarterly revenue showed an upward trend through the first three quarters. Revenue grew from $36,108.31 in Q1 to a peak of $71,674.99 in Q3, before slightly retracting to $68,948.71 in Q4.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Ranking: Q3, Q4, Q2, Q1
- [q4] Comparing full-year results, revenue increased from $211,976.29 in 2023 to $233,348.80 in 2024. This represents a year-over-year growth of 10.08%.
  - Reported values: revenue_2023=211976.29, revenue_2024=233348.8, revenue_yoy_change_pct=10.08
  - Direction: increase
- [q5] There were 22 orders in the Electronics category with discounts of 20% or higher. These high-discount orders generated a total revenue of $50,035.33.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
- [q6] Order revenue distribution is highly skewed. While the mean order value is $856.39, the median is significantly lower at $313.28. Order values ranged from a minimum of $5.27 to a maximum of $7,844.02, with a sample standard deviation of $1,295.74.
  - Reported values: order_revenue_mean=856.39, order_revenue_median=313.28, order_revenue_std=1295.74, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] The customer base consists of 222 unique customers. The top customer generated $27,793.13 in revenue, accounting for 6.24% of the total revenue.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.24

## Limitations
- The analysis relies on a single export file; data completeness depends on the source system's export integrity.
- Customer concentration analysis identifies the top customer's revenue share but does not assess risk associated with potential churn.
- Regional analysis aggregates data by label without accounting for market size or operational costs specific to those regions.

## Conclusion
The business demonstrated solid growth in 2024 with a 10.08% revenue increase. The East region is the primary revenue driver, and Q3 2024 was the strongest quarter. However, the large gap between mean and median order values indicates that revenue is heavily reliant on a subset of high-value orders, a risk underscored by the top customer representing over 6% of total revenue. Strategic focus should be placed on stabilizing the South region's performance and diversifying the customer base to mitigate concentration risk.
