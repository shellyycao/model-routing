# Retail Sales Performance Report: 2023–2024

Across 520 orders, the business generated $445,325 in total revenue over 2023–2024, with a healthy 10.1% year-over-year increase from 2023 to 2024. The East region led all regions in revenue. The 2024 quarterly trend showed strong acceleration through Q3 before a modest Q4 dip. Customer concentration is moderate, with the top customer accounting for 6.2% of total revenue. High-discount Electronics orders represent a notable revenue pocket requiring margin scrutiny.

## Key findings
- [q1] The business recorded 520 orders totalling $445,325 in revenue, yielding an average order value of $856.39.
  - Reported values: total_revenue=445325.09, order_count=520.0, average_order_value=856.39
  - Direction: not_applicable
- [q2] The East region generated the highest revenue at $130,517, followed by North ($124,846), West ($99,428), and South ($90,534). The East-to-South gap is approximately $39,983.
  - Reported values: revenue_north=124845.75, revenue_south=90534.49, revenue_east=130516.69, revenue_west=99428.16
  - Direction: not_applicable
  - Ranking: East, North, West, South
  - Derived difference(revenue_east, revenue_south): 39982.2
- [q3] 2024 quarterly revenue rose sharply from $36,108 in Q1 to a peak of $71,675 in Q3, before declining slightly to $68,949 in Q4. Q2 contributed $56,617, indicating consistent acceleration through mid-year.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Direction: increase
- [q4] Total revenue grew from $211,976 in 2023 to $233,349 in 2024, a year-over-year increase of 10.1%.
  - Reported values: revenue_2023=211976.29, revenue_2024=233348.8, revenue_yoy_change_pct=10.08
  - Direction: increase
  - Derived difference(revenue_2024, revenue_2023): 21372.51
- [q5] 22 Electronics orders carried a discount of 20% or more, generating $50,035 in combined revenue. These high-discount orders warrant margin review given their significant revenue contribution.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
  - Direction: not_applicable
  - Derived share(electronics_high_discount_revenue, total_revenue): 11.24
- [q6] Order revenue is highly right-skewed: the median order is $313.28, well below the mean of $856.39, with a standard deviation of $1,295.74. Orders range from $5.27 to $7,844.02, indicating a long tail of high-value transactions.
  - Reported values: order_revenue_mean=856.39, order_revenue_median=313.28, order_revenue_std=1295.74, order_revenue_min=5.27, order_revenue_max=7844.02
  - Direction: not_applicable
- [q7] There are 222 distinct customers. The single highest-revenue customer contributed $27,793, representing 6.2% of total revenue, suggesting moderate but notable concentration at the top.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.24
  - Direction: not_applicable
  - Derived share(top_customer_revenue, total_revenue): 6.24

## Limitations
- The dataset covers only two calendar years (2023–2024); longer historical context would be needed to assess whether the 10.1% YoY growth is above or below trend.
- Profitability and cost data are absent; high-discount Electronics revenue figures cannot be evaluated for margin impact without cost-of-goods information.
- Customer identifiers are anonymised, preventing segmentation by customer type, geography, or acquisition channel.
- The highly skewed order revenue distribution (std $1,296 vs. median $313) suggests potential outliers that were not explicitly removed; their influence on mean-based metrics should be interpreted cautiously.
- Regional labels (North, South, East, West) are not mapped to specific geographies, limiting actionability of regional findings.

## Conclusion
The retail business delivered solid growth in 2023–2024, with total revenue of $445,325 and a 10.1% year-over-year increase. The East region and the mid-year 2024 quarters were the primary growth drivers. The highly skewed order distribution and the concentration of 6.2% of revenue in a single customer highlight both opportunity and risk. High-discount Electronics orders ($50,035 across 22 orders) merit a targeted margin review. Priorities for the next period should include sustaining Q3-level momentum into Q4, diversifying the top-customer revenue base, and evaluating discount policies in Electronics.
