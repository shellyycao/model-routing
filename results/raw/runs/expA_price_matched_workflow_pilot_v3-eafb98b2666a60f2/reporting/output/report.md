# Retail Sales Performance Report: 2023–2024

Across 520 cleaned orders, the business generated $445,325 in total revenue over 2023–2024, with a healthy 10.1% year-over-year increase from 2023 to 2024. The East region led all regions in revenue. Within 2024, revenue accelerated through Q3 before a modest Q4 dip. High-discount electronics represent a notable revenue pocket, and order revenue is highly right-skewed, with the top customer accounting for 6.2% of total revenue.

## Key findings
- [q1] The cleaned dataset contains 520 orders generating total revenue of $445,325.07, with an average order value of $856.39.
  - Reported values: total_revenue=445325.07, order_count=520.0, average_order_value=856.394365
- [q2] East led all regions with $130,517 in revenue, followed by North ($124,846), West ($99,428), and South ($90,534). East outpaced the lowest region (South) by approximately $40,000.
  - Reported values: revenue_east=130516.68, revenue_north=124845.75, revenue_west=99428.16, revenue_south=90534.48
  - Ranking: East, North, West, South
  - Derived difference(revenue_east, revenue_south): 39982.2
- [q3] Within 2024, revenue grew strongly from Q1 ($36,108) through Q3 ($71,675), the peak quarter, before declining slightly in Q4 ($68,949). Q2 contributed $56,617.
  - Reported values: revenue_2024_q1=36108.32, revenue_2024_q2=56616.79, revenue_2024_q3=71674.98, revenue_2024_q4=68948.7
  - Ranking: Q3, Q4, Q2, Q1
- [q4] Total revenue grew from $211,976 in 2023 to $233,349 in 2024, a year-over-year increase of 10.1%.
  - Reported values: revenue_2023=211976.28, revenue_2024=233348.79, revenue_yoy_change_pct=10.082501
  - Direction: increase
  - Derived difference(revenue_2024, revenue_2023): 21372.51
- [q5] There are 22 Electronics orders with a discount of 20% or more, generating $50,035 in combined revenue — a meaningful segment warranting margin scrutiny.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.32
- [q6] Order revenue is highly right-skewed: the mean is $856.39 but the median is only $313.28, with a standard deviation of $1,295.74. Values range from $5.27 to $7,844.02, indicating a long tail of high-value orders.
  - Reported values: order_revenue_mean=856.394365, order_revenue_median=313.275, order_revenue_std=1295.742355, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] The 520 orders span 222 unique customers. The single highest-revenue customer contributed $27,793, representing 6.2% of total revenue — a moderate concentration risk.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.12, top_customer_revenue_share_pct=6.241086
  - Derived share(top_customer_revenue, total_revenue): 6.24

## Limitations
- The dataset covers only 520 orders; findings may not be representative if the export is a sample rather than the full order population.
- No product-level cost data is available, so revenue figures cannot be translated into gross margin or profitability.
- The high-discount Electronics analysis uses a fixed 20% threshold; the business impact of discounts just below this threshold is not captured.
- Customer concentration is assessed on revenue only; order frequency and lifetime value dimensions are not analysed.
- The Q4 2024 data may be incomplete if the export was generated before year-end, which could understate Q4 and full-year 2024 revenue.

## Conclusion
The business delivered solid growth in 2023–2024, with total revenue of $445,325 and a 10.1% year-over-year uplift. The East region and Q3 2024 were standout performers. The highly skewed order-value distribution and a single customer holding 6.2% of revenue suggest opportunities to broaden the customer base and manage large-order dependency. High-discount Electronics orders merit a margin review to ensure promotional activity is value-accretive.
