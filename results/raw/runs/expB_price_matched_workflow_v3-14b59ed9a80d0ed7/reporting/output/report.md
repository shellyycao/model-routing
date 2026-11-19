# Retail Sales Performance Report 2023-2024

Across 2023-2024 the business generated $445,325.07 in verified revenue from 520 cleaned orders, an average order value of $856.39. Revenue grew 10.08% year over year, from $211,976.28 in 2023 to $233,348.79 in 2024, with 2024 momentum building to a Q3 peak before a slight Q4 dip. The East region leads regional revenue, order values are strongly right-skewed (median $313.28 vs mean $856.39), and customer concentration is moderate, with the top customer accounting for 6.24% of revenue.

## Key findings
- [q1] Total verified revenue for 2023-2024 was $445,325.07 across 520 orders, giving an average order value of $856.39.
  - Reported values: total_revenue=445325.07, order_count=520.0, average_order_value=856.3943653846154
  - Direction: not_applicable
- [q2] The East region generated the most revenue ($130,516.68), followed by North ($124,845.75), West ($99,428.16) and South ($90,534.48); East exceeded South by $39,982.20.
  - Reported values: revenue_north=124845.75, revenue_south=90534.48, revenue_east=130516.68000000001, revenue_west=99428.16
  - Direction: not_applicable
  - Ranking: East, North, West, South
  - Derived difference(revenue_east, revenue_south): 39982.2
- [q3] 2024 revenue climbed through the year: Q1 was lowest at $36,108.32, Q2 reached $56,616.79, Q3 peaked at $71,674.98, and Q4 eased slightly to $68,948.70. Q3 exceeded Q1 by $35,566.66.
  - Reported values: revenue_2024_q1=36108.32, revenue_2024_q2=56616.79, revenue_2024_q3=71674.98, revenue_2024_q4=68948.7
  - Direction: not_applicable
  - Ranking: Q3, Q4, Q2, Q1
  - Derived difference(revenue_2024_q3, revenue_2024_q1): 35566.66
- [q4] Revenue increased year over year, rising 10.08% from $211,976.28 in 2023 to $233,348.79 in 2024.
  - Reported values: revenue_2023=211976.28, revenue_2024=233348.78999999998, revenue_yoy_change_pct=10.082500740177146
  - Direction: increase
- [q5] 22 electronics orders carried discounts of 20% or more, contributing $50,035.32 in revenue, about 11.24% of total revenue.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.32
  - Direction: not_applicable
  - Derived share(electronics_high_discount_revenue, total_revenue): 11.24
- [q6] Order revenue is highly right-skewed: the mean ($856.39) is about 2.73 times the median ($313.28), the sample standard deviation is $1,295.74, and order values range from $5.27 to $7,844.02.
  - Reported values: order_revenue_mean=856.3943653846154, order_revenue_median=313.275, order_revenue_std=1295.7423548861245, order_revenue_min=5.27, order_revenue_max=7844.02
  - Direction: not_applicable
  - Derived ratio(order_revenue_mean, order_revenue_median): 2.73
- [q7] The analysis covers 222 distinct customers. The highest-revenue customer spent $27,793.12, equal to 6.24% of total revenue, indicating meaningful but not dominant single-customer dependence.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.12, top_customer_revenue_share_pct=6.241085865657642
  - Direction: not_applicable

## Limitations
- Findings cover only 2023-2024; no earlier baseline is available to judge whether 10.08% growth is typical.
- Metrics are revenue-only; no cost or margin data, so profitability of high-discount electronics orders cannot be assessed.
- The strong right skew (mean $856.39 vs median $313.28) means averages are pulled up by a small number of large orders.
- Quarterly and year-over-year figures may reflect seasonality or one-off large orders; no returns, cancellations or currency effects are captured in the cleaned data.
- Customer concentration beyond the top customer (e.g., top-5 or top-10 share) was not computed.

## Conclusion
The business grew healthily in 2024, with revenue up 10.08% to $233,348.79 and momentum peaking in Q3. East is the strongest region while South lags. Growth is supported by a broad base of 222 customers with moderate concentration risk, but the heavy skew in order values and reliance on discounted electronics sales warrant margin-aware monitoring as 2025 plans are set.
