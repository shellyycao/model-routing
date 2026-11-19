# Retail Sales Performance Report: 2023–2024

Across 520 cleaned orders, the business generated $445,325 in total revenue over 2023–2024, with a healthy 10.1% year-over-year increase from 2023 to 2024. The East region led all geographies, 2024 showed strong mid-year momentum, and a small segment of high-discount Electronics orders represents a notable revenue concentration worth monitoring.

## Key findings
- [q1] Total revenue across all 520 orders was $445,325.09, yielding an average order value of $856.39.
  - Reported values: total_revenue=445325.09, order_count=520.0, average_order_value=856.39
- [q2] East led regional revenue at $130,516.69, followed by North ($124,845.75), West ($99,428.16), and South ($90,534.49). East outpaced South by approximately $40,000.
  - Reported values: revenue_east=130516.69, revenue_north=124845.75, revenue_west=99428.16, revenue_south=90534.49
  - Ranking: East, North, West, South
  - Derived difference(revenue_east, revenue_south): 39982.2
- [q3] 2024 quarterly revenue peaked in Q3 ($71,674.99), followed by Q4 ($68,948.71), Q2 ($56,616.79), and Q1 ($36,108.31), indicating strong second-half performance.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Ranking: Q3, Q4, Q2, Q1
- [q4] Revenue grew from $211,976.29 in 2023 to $233,348.80 in 2024, a year-over-year increase of 10.1%.
  - Reported values: revenue_2023=211976.29, revenue_2024=233348.8, revenue_yoy_change_pct=10.08
  - Direction: increase
- [q5] 22 Electronics orders carried a discount of 20% or more, generating $50,035.33 in combined revenue — roughly 11.2% of total revenue.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
  - Derived share(electronics_high_discount_revenue, total_revenue): 11.24
- [q6] Order revenue is highly right-skewed: the mean ($856.39) is nearly three times the median ($313.28), with a standard deviation of $1,295.74. Values range from $5.27 to $7,844.02, indicating a long tail of large orders.
  - Reported values: order_revenue_mean=856.39, order_revenue_median=313.28, order_revenue_std=1295.74, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] Across 222 distinct customers, the top customer alone contributed $27,793.13, representing 6.2% of total revenue — a meaningful concentration risk.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.24

## Limitations
- The dataset covers only two calendar years (2023–2024); longer historical context would improve trend reliability.
- Customer identifiers are anonymised, preventing deeper behavioural or demographic segmentation.
- Discount percentages are taken at face value from the export; any upstream data-entry errors would affect the high-discount Electronics filter.
- Revenue figures reflect order-level totals and do not account for returns, cancellations, or fulfilment costs.
- Regional labels are categorical with no sub-regional breakdown, limiting geographic granularity.

## Conclusion
The business delivered solid growth in 2023–2024, with total revenue of $445,325 and a 10.1% year-over-year uplift. The East region and the second half of 2024 were the primary performance drivers. However, the highly skewed order-value distribution and a single customer accounting for 6.2% of revenue highlight concentration risks. High-discount Electronics orders also warrant margin scrutiny. Addressing these areas should be a priority for the 2025 planning cycle.
