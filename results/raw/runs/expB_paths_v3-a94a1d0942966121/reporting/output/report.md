# Retail Sales Performance Report: 2023–2024

Across 520 orders, the business generated $445,325 in total revenue over 2023–2024, with a healthy 10.1% year-over-year increase from 2023 to 2024. The East region led all regions in revenue. Within 2024, revenue accelerated through Q3 before a modest Q4 dip. High-discount electronics represent a notable revenue concentration risk, and order revenue is highly skewed, with the median far below the mean. Customer concentration is moderate, with the top customer accounting for 6.2% of total revenue.

## Key findings
- [q1] The business recorded 520 orders totalling $445,325 in revenue, yielding an average order value of $856.39.
  - Reported values: total_revenue=445325.09, order_count=520.0, average_order_value=856.39
- [q2] East led all regions with $130,517 in revenue, followed by North ($124,846), West ($99,428), and South ($90,534).
  - Reported values: revenue_east=130516.69, revenue_north=124845.75, revenue_west=99428.16, revenue_south=90534.49
  - Ranking: East, North, West, South
- [q3] 2024 quarterly revenue grew strongly from Q1 ($36,108) through Q3 ($71,675), the peak quarter, before declining slightly in Q4 ($68,949). Q2 contributed $56,617.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Ranking: Q3, Q4, Q2, Q1
- [q4] Revenue grew from $211,976 in 2023 to $233,349 in 2024, a year-over-year increase of 10.1%.
  - Reported values: revenue_2023=211976.29, revenue_2024=233348.8, revenue_yoy_change_pct=10.08
  - Direction: increase
- [q5] 22 Electronics orders carried a discount of 20% or more, generating $50,035 in revenue — representing 11.2% of total revenue.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
  - Derived share(electronics_high_discount_revenue, total_revenue): 11.2
- [q6] Order revenue is highly right-skewed: the mean is $856.39 but the median is only $313.28, with a standard deviation of $1,295.74. Values range from $5.27 to $7,844.02, indicating a small number of very large orders drive the average.
  - Reported values: order_revenue_mean=856.39, order_revenue_median=313.28, order_revenue_std=1295.74, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] The 520 orders came from 222 unique customers. The single highest-revenue customer contributed $27,793, equal to 6.2% of total revenue, indicating moderate but notable concentration.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.24
  - Derived share(top_customer_revenue, total_revenue): 6.24

## Limitations
- The dataset covers only two calendar years (2023–2024); longer historical context would be needed to assess whether the 10.1% YoY growth is above or below trend.
- Product category granularity is limited; high-discount analysis is restricted to Electronics and does not cover discount patterns in other categories.
- Customer identifiers are anonymised, preventing any qualitative assessment of the top customer's strategic importance or churn risk.
- The highly skewed order revenue distribution (median $313 vs. mean $856) suggests potential data quality issues or a mix of very different order types that may warrant further segmentation.
- Regional definitions are not documented; it is unclear whether regions reflect geography, sales territories, or another dimension, limiting actionability of regional comparisons.

## Conclusion
The business delivered solid growth in 2023–2024, with total revenue of $445,325 and a 10.1% year-over-year increase. The East region and Q3 2024 were standout performers. However, the highly skewed order distribution, meaningful high-discount electronics exposure (11.2% of revenue), and moderate top-customer concentration (6.2%) are areas warranting closer monitoring to protect margin and revenue stability.
