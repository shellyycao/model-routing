# Retail Sales Performance Report: 2023–2024

Across 520 orders, the business generated $445,325 in total revenue over 2023–2024, with a healthy 10.1% year-over-year increase from 2023 to 2024. The East region led all regions in revenue. Within 2024, revenue accelerated through Q3 before a modest Q4 dip. High-discount Electronics orders represent a notable revenue concentration risk, and a single top customer accounts for 6.2% of total revenue.

## Key findings
- [q1] The business recorded 520 orders totalling $445,325 in revenue, yielding an average order value of $856.39.
  - Reported values: total_revenue=445325.09, order_count=520.0, average_order_value=856.39
- [q2] East led all regions with $130,517 in revenue, followed by North ($124,846), West ($99,428), and South ($90,534). East outpaced South by approximately $40,000.
  - Reported values: revenue_east=130516.69, revenue_north=124845.75, revenue_west=99428.16, revenue_south=90534.49
  - Ranking: East, North, West, South
  - Derived difference(revenue_east, revenue_south): 39982.2
- [q3] 2024 quarterly revenue grew steadily from $36,108 in Q1 to a peak of $71,675 in Q3, before easing slightly to $68,949 in Q4. Q2 came in at $56,617.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Ranking: Q3, Q4, Q2, Q1
- [q4] Total revenue grew from $211,976 in 2023 to $233,349 in 2024, a year-over-year increase of 10.1%.
  - Reported values: revenue_2023=211976.29, revenue_2024=233348.8, revenue_yoy_change_pct=10.08
  - Direction: increase
- [q5] 22 Electronics orders carried a discount of 20% or more, generating $50,035 in combined revenue — representing approximately 11.2% of total revenue.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
  - Derived share(electronics_high_discount_revenue, total_revenue): 11.24
- [q6] Order revenue is highly right-skewed: the mean is $856.39 but the median is only $313.28, with a standard deviation of $1,295.74. Values range from $5.27 to $7,844.02, indicating a long tail of high-value orders.
  - Reported values: order_revenue_mean=856.39, order_revenue_median=313.28, order_revenue_std=1295.74, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] There are 222 distinct customers. The single highest-revenue customer contributed $27,793, equal to 6.2% of total revenue, indicating moderate customer concentration.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.24

## Limitations
- The cleaning stage validation failed, meaning the cleaned dataset may contain residual data quality issues (e.g., duplicates, incorrect dates, or imputed values) that could affect all downstream metrics.
- Regional labels are assumed to be complete and correctly assigned; any mis-labelled or missing region values would cause revenue to be understated for affected regions.
- The analysis covers only two calendar years (2023–2024); longer historical context is unavailable, limiting the interpretation of the YoY growth trend.
- Customer concentration is assessed solely on revenue; order frequency and profitability per customer are not captured in this dataset.
- Discount percentages are taken at face value from the raw export; any data entry errors in discount_pct would affect the high-discount Electronics findings.

## Conclusion
The retail business delivered solid growth in 2023–2024, with total revenue of $445,325 and a 10.1% YoY increase. The East and North regions are the primary revenue drivers, and 2024 showed a strong mid-year acceleration. However, the highly skewed order-value distribution and the top customer's 6.2% revenue share warrant attention to diversification. High-discount Electronics orders also merit a margin review. Resolving the cleaning-stage data quality issues should be prioritised before acting on these figures.
