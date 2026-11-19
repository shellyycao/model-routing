# Retail Sales Performance Report: 2023–2024

Across 520 cleaned orders, the business generated $445,325 in total revenue over 2023–2024, with a healthy 10.1% year-over-year increase from 2023 to 2024. The East region led all regions in revenue. Within 2024, revenue accelerated through Q3 before a modest Q4 dip. High-discount Electronics orders represent a notable revenue concentration risk, and order revenue is highly right-skewed, with a small number of large orders driving the mean well above the median.

## Key findings
- [q1] The cleaned dataset contains 520 orders generating total revenue of $445,325.07, with an average order value of $856.39.
  - Reported values: total_revenue=445325.07, order_count=520.0, average_order_value=856.394365
- [q2] East led all regions with $130,517 in revenue, followed by North ($124,846), West ($99,428), and South ($90,534). East outpaced the lowest region, South, by approximately $40,000.
  - Reported values: revenue_east=130516.68, revenue_north=124845.75, revenue_west=99428.16, revenue_south=90534.48
  - Ranking: East, North, West, South
  - Derived difference(revenue_east, revenue_south): 39982.2
- [q3] Within 2024, quarterly revenue rose steadily from $36,108 in Q1 to a peak of $71,675 in Q3, before declining slightly to $68,949 in Q4. Q2 recorded $56,617.
  - Reported values: revenue_2024_q1=36108.32, revenue_2024_q2=56616.79, revenue_2024_q3=71674.98, revenue_2024_q4=68948.7
  - Ranking: Q3, Q4, Q2, Q1
- [q4] Total revenue grew from $211,976 in 2023 to $233,349 in 2024, a year-over-year increase of 10.1%.
  - Reported values: revenue_2023=211976.28, revenue_2024=233348.79, revenue_yoy_change_pct=10.082501
  - Direction: increase
- [q5] There are 22 Electronics orders with a discount of 20% or more, collectively generating $50,035 in revenue — representing approximately 11.2% of total revenue.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.32
  - Derived share(electronics_high_discount_revenue, total_revenue): 11.24
- [q6] Order revenue is highly right-skewed: the mean is $856.39 but the median is only $313.28, with a standard deviation of $1,295.74. Values range from $5.27 to $7,844.02, indicating a small number of very large orders inflate the average.
  - Reported values: order_revenue_mean=856.394365, order_revenue_median=313.275, order_revenue_std=1295.742355, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] There are 222 unique customers. The single highest-revenue customer contributed $27,793, representing 6.2% of total revenue — a meaningful concentration for one customer out of 222.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.12, top_customer_revenue_share_pct=6.241086

## Limitations
- The dataset covers only two calendar years (2023–2024); longer historical context would be needed to assess whether the 10.1% YoY growth is above or below trend.
- Revenue is computed from the cleaned export only; any orders removed during cleaning are excluded and may bias totals.
- Regional assignments are taken as given in the data; no geographic validation was performed to confirm correct region labelling.
- High-discount Electronics analysis uses a fixed 20% threshold; sensitivity to alternative thresholds has not been assessed.
- Customer concentration analysis identifies the top customer by revenue share but does not account for multi-account customers or corporate hierarchies.

## Conclusion
The business delivered solid growth in 2023–2024, with total revenue of $445,325 across 520 orders and a 10.1% year-over-year uplift. The East region is the strongest performer, and 2024 showed a clear ramp through Q3. Key risks to monitor include the skewed order-value distribution (a few large orders drive the mean), the 6.2% revenue share held by a single customer, and the $50,035 tied to heavily discounted Electronics orders. Addressing customer diversification and discount discipline in Electronics should be priorities for 2025 planning.
