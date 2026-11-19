# Retail Sales Performance Report: 2023–2024

Across 520 orders, the business generated $445,325 in total revenue over 2023–2024. Revenue grew ~10.1% year-over-year, driven by a strong second half of 2024. The East region led all regions, while the South lagged. High-discount Electronics orders represent a notable revenue concentration risk, and a single top customer accounts for 6.2% of total revenue.

## Key findings
- [q1] Total revenue across all 520 orders was $445,325.09, yielding an average order value of $856.39.
  - Reported values: total_revenue=445325.09, order_count=520.0, average_order_value=856.39
- [q2] The East region generated the highest revenue at $130,516.69, followed by North ($124,845.75), West ($99,428.16), and South ($90,534.49). East outpaced South by approximately $40,000.
  - Reported values: revenue_east=130516.69, revenue_north=124845.75, revenue_west=99428.16, revenue_south=90534.49
  - Ranking: East, North, West, South
  - Derived difference(revenue_east, revenue_south): 39982.2
- [q3] Within 2024, quarterly revenue rose sharply through Q3 before a modest dip in Q4. Q3 was the strongest quarter at $71,674.99, followed by Q4 ($68,948.71), Q2 ($56,616.79), and Q1 ($36,108.31).
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Ranking: Q3, Q4, Q2, Q1
- [q4] Revenue increased from $211,976.29 in 2023 to $233,348.80 in 2024, a year-over-year growth of approximately 10.1%.
  - Reported values: revenue_2023=211976.29, revenue_2024=233348.8, revenue_yoy_change_pct=10.08
  - Direction: increase
- [q5] There were 22 Electronics orders with a discount of 20% or more, generating $50,035.33 in combined revenue. These heavily discounted orders warrant margin scrutiny.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
- [q6] Order revenue is highly right-skewed: the mean is $856.39 but the median is only $313.28, with a standard deviation of $1,295.74. Values range from $5.27 to $7,844.02, indicating a small number of very large orders pull the average up significantly.
  - Reported values: order_revenue_mean=856.39, order_revenue_median=313.28, order_revenue_std=1295.74, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] The dataset contains 222 distinct customers. The single highest-revenue customer contributed $27,793.13, representing 6.2% of total revenue—a meaningful concentration for one account.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.24
  - Derived share(top_customer_revenue, total_revenue): 6.24

## Limitations
- The dataset covers only two calendar years (2023–2024); longer historical context would improve trend reliability.
- Product-level cost data is absent, so revenue figures cannot be converted to margin or profitability metrics.
- Customer identifiers are anonymised; it is not possible to assess churn, repeat-purchase behaviour, or segment customers beyond revenue totals.
- Regional assignments are taken as given in the export; any mis-categorisation in the source system would propagate into the regional comparison.
- High-discount Electronics orders are identified by discount_pct threshold alone; the business rationale (promotions, clearance, negotiated contracts) is unknown and could affect interpretation.

## Conclusion
The business delivered solid 10.1% revenue growth in 2024, with momentum building through Q3. The East and North regions are the primary revenue engines. However, the wide gap between mean and median order values signals a skewed order mix, and a single customer accounting for 6.2% of revenue represents a concentration risk. High-discount Electronics orders merit a margin review to ensure promotional activity is profitable.
