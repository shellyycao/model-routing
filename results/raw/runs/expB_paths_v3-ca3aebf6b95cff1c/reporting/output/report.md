# Retail Sales Performance Report: 2023–2024

Across 520 orders, the business generated $445,325 in total revenue over 2023–2024. Revenue grew 10.1% year-over-year, driven by a strong second half of 2024. The East region led all regions, while high-discount electronics represent a notable margin-risk segment. Customer concentration is moderate, with the top customer accounting for 6.2% of total revenue.

## Key findings
- [q1] The business recorded 520 orders totalling $445,325 in revenue, yielding an average order value of $856.39.
  - Reported values: total_revenue=445325.09, order_count=520.0, average_order_value=856.39
- [q2] East led all regions with $130,517 in revenue, followed by North ($124,846), West ($99,428), and South ($90,534).
  - Reported values: revenue_east=130516.69, revenue_north=124845.75, revenue_west=99428.16, revenue_south=90534.49
  - Ranking: East, North, West, South
- [q3] Within 2024, Q3 was the strongest quarter at $71,675, followed by Q4 ($68,949), Q2 ($56,617), and Q1 ($36,108), indicating accelerating momentum through mid-year that plateaued slightly in Q4.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71675.0, revenue_2024_q4=68948.71
  - Ranking: Q3, Q4, Q2, Q1
- [q4] Revenue increased from $211,976 in 2023 to $233,349 in 2024, a year-over-year growth of 10.1%.
  - Reported values: revenue_2023=211976.29, revenue_2024=233348.8, revenue_yoy_change_pct=10.08
  - Direction: increase
  - Derived difference(revenue_2024, revenue_2023): 21372.51
- [q5] 22 Electronics orders carried a discount of 20% or more, generating $50,035 in combined revenue. These orders warrant margin scrutiny given the depth of discounting applied.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
- [q6] Order revenue is highly right-skewed: the mean is $856.39 but the median is only $313.28, with a standard deviation of $1,295.74. Values range from $5.27 to $7,844.02, indicating a long tail of high-value orders pulling the average upward.
  - Reported values: order_revenue_mean=856.39, order_revenue_median=313.28, order_revenue_std=1295.74, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] There are 222 distinct customers. The single highest-revenue customer contributed $27,793, representing 6.2% of total revenue, suggesting moderate but noteworthy concentration at the top.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.24
  - Derived share(top_customer_revenue, total_revenue): 6.24

## Limitations
- The dataset covers only two calendar years (2023–2024); longer historical context would improve trend reliability.
- Profitability and cost data are absent, so revenue growth cannot be assessed against margin impact, particularly for high-discount orders.
- Customer identifiers are anonymised; it is not possible to assess churn, repeat-purchase behaviour, or lifetime value.
- Regional definitions are not documented; it is unclear whether regions reflect geography, sales territories, or another segmentation.
- The high standard deviation and wide min-max range suggest potential outliers that were not explicitly removed during cleaning, which may distort mean-based metrics.

## Conclusion
The business delivered solid 10.1% revenue growth in 2024, with the East region and the second half of the year as key drivers. The highly skewed order distribution and the high-discount electronics segment are areas requiring closer attention to protect margins. Customer concentration is moderate, but the top customer's 6.2% revenue share merits relationship monitoring.
