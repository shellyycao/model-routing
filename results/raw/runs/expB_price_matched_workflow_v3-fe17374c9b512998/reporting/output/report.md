# Retail Sales Performance Report: 2023–2024

Across 520 cleaned orders, the business generated $445,325 in total revenue over 2023–2024, with a 10.1% year-over-year increase from 2023 to 2024. The East region led all regions in revenue. Within 2024, revenue accelerated through Q3 before a modest Q4 dip. Order values are highly right-skewed, and a single top customer accounts for 6.2% of total revenue.

## Key findings
- [q1] The cleaned dataset contains 520 orders generating total revenue of $445,325.09, with an average order value of $856.39.
  - Reported values: total_revenue=445325.09, order_count=520.0, average_order_value=856.39
- [q2] East led all regions with $130,516.69 in revenue, followed by North ($124,845.75), West ($99,428.16), and South ($90,534.49). East outpaced South by approximately $40,000.
  - Reported values: revenue_east=130516.69, revenue_north=124845.75, revenue_west=99428.16, revenue_south=90534.49
  - Ranking: East, North, West, South
  - Derived difference(revenue_east, revenue_south): 39982.2
- [q3] 2024 quarterly revenue grew from $36,108.31 in Q1 to a peak of $71,674.99 in Q3, before declining slightly to $68,948.71 in Q4. Q2 came in at $56,616.79, ranking third.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Ranking: Q3, Q4, Q2, Q1
- [q4] Total revenue grew from $211,976.29 in 2023 to $233,348.80 in 2024, a year-over-year increase of 10.1%.
  - Reported values: revenue_2023=211976.29, revenue_2024=233348.8, revenue_yoy_change_pct=10.08
  - Direction: increase
  - Derived pct_change(revenue_2024, revenue_2023): 10.08
- [q5] 22 Electronics orders carried a discount of 20% or more, generating $50,035.33 in combined revenue — representing approximately 11.2% of total revenue.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
  - Derived share(electronics_high_discount_revenue, total_revenue): 11.24
- [q6] Order revenue is highly right-skewed: the mean is $856.39 but the median is only $313.28, with a standard deviation of $1,295.74. Values range from $5.27 to $7,844.02, indicating a long upper tail driven by a small number of large orders.
  - Reported values: order_revenue_mean=856.39, order_revenue_median=313.28, order_revenue_std=1295.74, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] The 520 orders span 222 unique customers. The single highest-revenue customer contributed $27,793.13, representing 6.2% of total revenue — a notable concentration for one account.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.24
  - Derived share(top_customer_revenue, total_revenue): 6.24

## Limitations
- The dataset covers only two calendar years (2023–2024); longer historical context would be needed to assess whether the 10.1% YoY growth is above or below trend.
- No product-level margin data is available, so revenue figures cannot be translated into profitability; high-discount Electronics orders may be loss-making despite their revenue contribution.
- Customer identifiers are anonymised, preventing segmentation by customer type, size, or geography beyond the regional order-level data.
- The order revenue distribution is heavily right-skewed (mean nearly 3× median), suggesting a small number of outlier orders materially influence aggregate metrics; outlier treatment choices in the cleaning stage could affect results.
- Regional assignments are at the order level and may not reflect the customer's true location, limiting the reliability of regional comparisons.

## Conclusion
The retail business delivered solid growth in 2023–2024, with total revenue of $445,325 and a 10.1% year-over-year uplift. The East region is the strongest market, and 2024 showed a clear positive intra-year trend peaking in Q3. Key risks include heavy revenue skew toward large orders, a single customer accounting for 6.2% of revenue, and 22 high-discount Electronics orders whose margin impact warrants further review.
