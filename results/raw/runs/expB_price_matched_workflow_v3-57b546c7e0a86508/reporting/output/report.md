# Retail Sales Performance Report, 2023-2024

The cleaned order data covers 520 orders generating $445,325.09 in total revenue, an average order value of $856.39. Revenue grew 10.08% year over year, from $211,976.29 in 2023 to $233,348.80 in 2024. The East region led all regions with $130,516.69, while 2024 revenue climbed steadily from $36,108.31 in Q1 to a peak of $71,674.99 in Q3. Order revenue is strongly right-skewed (mean $856.39 vs. median $313.28), and the customer base is well diversified: 222 unique customers with the top customer accounting for only 6.24% of revenue.

## Key findings
- [q1] Overall, the business generated $445,325.09 in total revenue across 520 orders in 2023-2024, yielding an average order value of $856.39.
  - Reported values: total_revenue=445325.08999999997, order_count=520.0, average_order_value=856.3944038461538
- [q2] Regional revenue was led by the East at $130,516.69, followed by the North at $124,845.75, the West at $99,428.16, and the South at $90,534.49; the East outperformed the South by $39,982.20.
  - Reported values: revenue_north=124845.75, revenue_south=90534.49, revenue_east=130516.69, revenue_west=99428.16
  - Ranking: East, North, West, South
  - Derived difference(revenue_east, revenue_south): 39982.2
- [q3] Within 2024, revenue rose from $36,108.31 in Q1 to $56,616.79 in Q2 and peaked at $71,674.99 in Q3, before easing slightly to $68,948.71 in Q4; Q3 exceeded Q1 by $35,566.68, indicating strong momentum through the year.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Ranking: Q3, Q4, Q2, Q1
  - Derived difference(revenue_2024_q3, revenue_2024_q1): 35566.68
- [q4] Revenue increased 10.08% year over year, rising from $211,976.29 in 2023 to $233,348.80 in 2024, an absolute increase of $21,372.51.
  - Reported values: revenue_2023=211976.28999999998, revenue_2024=233348.80000000002, revenue_yoy_change_pct=10.082500264534321
  - Direction: increase
  - Derived difference(revenue_2024, revenue_2023): 21372.51
- [q5] High-discount Electronics orders (discount of 20% or more) numbered 22 and produced $50,035.33 in revenue, equivalent to about 11.24% of total company revenue.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
  - Derived share(electronics_high_discount_revenue, total_revenue): 11.24
- [q6] Order revenue is highly right-skewed: the mean of $856.39 is roughly 2.73 times the median of $313.28, with a large standard deviation of $1,295.74 and values spanning $5.27 to $7,844.02, so a small number of large orders drives much of the revenue.
  - Reported values: order_revenue_mean=856.3944038461538, order_revenue_median=313.275, order_revenue_std=1295.7423896952698, order_revenue_min=5.27, order_revenue_max=7844.02
  - Derived ratio(order_revenue_mean, order_revenue_median): 2.73
- [q7] Customer concentration is low: 222 unique customers placed orders, and the highest-revenue customer contributed $27,793.13, just 6.24% of total revenue.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.241087830914715

## Limitations
- The analysis covers only 2023-2024, so the quarterly trend rests on a single year and seasonality cannot be confirmed.
- Metrics reflect revenue only; no cost or margin data was available, so profitability of high-discount Electronics orders is unknown, and it is unclear whether revenue is recorded net of discounts.
- Order revenue is dominated by outliers (maximum $7,844.02 vs. median $313.28), so the average order value overstates the typical order.
- Concentration was assessed only via the single top customer; broader measures (e.g., top-10 customer share) were not computed.

## Conclusion
The retail business grew a healthy 10.08% in 2024, with momentum building through the year and peaking in Q3. East and North are the strongest regions, while South lags and may warrant targeted investment. Revenue depends on a minority of high-value orders, but customer concentration risk is low given a diversified base of 222 customers. Stakeholders should monitor the Q4 dip and review the profitability of deeply discounted Electronics sales.
