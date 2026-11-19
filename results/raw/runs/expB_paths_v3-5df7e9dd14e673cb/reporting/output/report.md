# Retail Sales Performance Report: 2023–2024

Across 520 orders in 2023–2024, the business generated $445,325 in total revenue at an average order value of $856. Revenue grew 10.1% year-over-year, with 2024 outperforming 2023 in every measured dimension. The East region led all regions, 2024 showed strong mid-year momentum, and a single customer accounted for 6.2% of total revenue—a concentration risk worth monitoring.

## Key findings
- [q1] The business recorded 520 orders totalling $445,325 in revenue, yielding an average order value of $856.39 across the full 2023–2024 period.
  - Reported values: total_revenue=445325.09, order_count=520.0, average_order_value=856.39
- [q2] The East region generated the highest revenue at $130,517, followed by North ($124,846), West ($99,428), and South ($90,534). East and North together accounted for the majority of total sales.
  - Reported values: revenue_east=130516.69, revenue_north=124845.75, revenue_west=99428.16, revenue_south=90534.49
  - Ranking: East, North, West, South
- [q3] In 2024, quarterly revenue rose sharply from Q1 ($36,108) through Q3 ($71,675) before a modest dip in Q4 ($68,949). Q2 ($56,617) marked a strong acceleration, and Q3 was the peak quarter. The ranking from highest to lowest is Q3, Q4, Q2, Q1.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Ranking: Q3, Q4, Q2, Q1
- [q4] Revenue increased from $211,976 in 2023 to $233,349 in 2024, a year-over-year growth of 10.1%. This represents an absolute gain of approximately $21,373.
  - Reported values: revenue_2023=211976.29, revenue_2024=233348.8, revenue_yoy_change_pct=10.08
  - Direction: increase
  - Derived difference(revenue_2024, revenue_2023): 21372.51
- [q5] 22 Electronics orders carried a discount of 20% or more, generating $50,035 in combined revenue. These high-discount orders represent a segment worth evaluating for margin impact.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
- [q6] Order revenue is highly right-skewed: the median order is $313.28, well below the mean of $856.39, with a standard deviation of $1,295.74. Orders range from $5.27 to $7,844.02, indicating a long tail of high-value transactions.
  - Reported values: order_revenue_mean=856.39, order_revenue_median=313.28, order_revenue_std=1295.74, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] There are 222 unique customers. The top customer alone contributed $27,793 in revenue, representing 6.2% of total revenue—a notable concentration for a base of this size.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.24
  - Derived share(top_customer_revenue, total_revenue): 6.24

## Limitations
- The dataset covers only two years (2023–2024); longer historical context would improve trend reliability.
- Profitability and cost data are absent, so revenue growth cannot be assessed against margin impact—particularly relevant for the high-discount Electronics segment.
- Customer identifiers are anonymised; no demographic or segment-level analysis is possible.
- The extreme spread in order values (std $1,296 vs. median $313) suggests potential outliers that were not explicitly investigated or removed beyond the cleaning stage.
- Regional definitions (North/South/East/West) are not mapped to specific geographies, limiting actionability of regional findings.

## Conclusion
The business delivered solid 10.1% revenue growth in 2024, with the East region leading and Q3 2024 as the strongest quarter. However, the wide dispersion of order values, a single customer representing 6.2% of revenue, and 22 high-discount Electronics orders warrant further investigation into pricing strategy and customer dependency risk.
