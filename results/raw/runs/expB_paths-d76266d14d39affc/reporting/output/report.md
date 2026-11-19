# Retail Sales Performance Report: 2023–2024

Across 520 orders, the business generated $445,325 in total revenue over 2023–2024, with a healthy 10.1% year-over-year increase from 2023 to 2024. The East region led all regions in revenue. Within 2024, revenue grew strongly through Q3 before a modest Q4 dip. High-discount electronics orders represent a notable revenue concentration risk, and a single top customer accounts for 6.2% of total revenue.

## Key findings
- [q1] The business recorded 520 orders totalling $445,325 in revenue over the 2023–2024 period, yielding an average order value of $856.39.
  - Reported values: total_revenue=445325.09, order_count=520.0, average_order_value=856.39
  - Direction: not_applicable
- [q2] The East region generated the highest revenue at $130,517, followed by North ($124,846), West ($99,428), and South ($90,534). East outpaced South by approximately $39,983.
  - Reported values: revenue_north=124845.75, revenue_south=90534.49, revenue_east=130516.69, revenue_west=99428.16
  - Direction: not_applicable
  - Ranking: East, North, West, South
  - Derived difference(revenue_east, revenue_south): 39982.2
- [q3] 2024 quarterly revenue showed a strong upward trend from Q1 ($36,108) through Q3 ($71,675), representing a near-doubling over two quarters, before a slight decline in Q4 ($68,949).
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Direction: increase
  - Derived pct_change(revenue_2024_q3, revenue_2024_q1): 98.5
- [q4] Revenue grew from $211,976 in 2023 to $233,349 in 2024, a year-over-year increase of 10.1% (+$21,373).
  - Reported values: revenue_2023=211976.29, revenue_2024=233348.8, revenue_yoy_change_pct=10.08
  - Direction: increase
  - Derived difference(revenue_2024, revenue_2023): 21372.51
- [q5] 22 Electronics orders carried a discount of 20% or more, generating $50,035 in combined revenue. These high-discount orders represent 11.2% of total revenue despite being only 4.2% of all orders.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
  - Direction: not_applicable
  - Derived share(electronics_high_discount_revenue, total_revenue): 11.2
  - Derived share(electronics_high_discount_orders, order_count): 4.2
- [q6] Order revenue is highly right-skewed: the mean is $856.39 but the median is only $313.28, with a standard deviation of $1,295.74. Values range from $5.27 to $7,844.02, indicating a long tail of high-value orders.
  - Reported values: order_revenue_mean=856.39, order_revenue_median=313.28, order_revenue_std=1295.74, order_revenue_min=5.27, order_revenue_max=7844.02
  - Direction: not_applicable
- [q7] There are 222 unique customers. The single highest-revenue customer contributed $27,793, representing 6.2% of total revenue — a meaningful concentration for one customer out of 222.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.24
  - Direction: not_applicable

## Limitations
- The dataset covers only 520 orders; findings may not be statistically representative of broader business trends.
- No product-level cost data is available, so revenue figures cannot be translated into margin or profitability.
- Customer identifiers are anonymised, preventing deeper behavioural segmentation or churn analysis.
- The analysis covers exactly two calendar years (2023–2024); longer historical context would strengthen trend conclusions.
- High-discount Electronics orders are identified by discount_pct alone; the business rationale (promotions, clearance) is unknown and may affect interpretation.

## Conclusion
The business delivered solid growth in 2023–2024, with total revenue of $445,325 and a 10.1% year-over-year increase. The East and North regions are the primary revenue drivers. The 2024 intra-year trend is encouraging, though the Q4 softening warrants monitoring. The highly skewed order-value distribution and the top customer's 6.2% revenue share highlight concentration risks that management should address through customer diversification and pricing discipline on high-discount Electronics.
