# Retail Sales Performance Report 2023–2024

In 2023–2024 the business generated $445,325.07 in revenue across 520 orders, averaging $856.39 per order. Revenue grew 10.08% year over year in 2024, with momentum building through Q3 before a modest Q4 dip. The East and North regions lead sales, the customer base is well diversified (top customer just 6.24% of revenue), and order values are highly skewed, with most orders small and a few very large.

## Key findings
- [q1] Total revenue for 2023–2024 was $445,325.07 across 520 orders, giving an average order value of $856.39.
  - Reported values: total_revenue=445325.07, order_count=520.0, average_order_value=856.394365
- [q2] East generated the most revenue ($130,516.68), followed by North ($124,845.75), West ($99,428.16) and South ($90,534.48); East outpaced the weakest region, South, by $39,982.20.
  - Reported values: revenue_north=124845.75, revenue_south=90534.48, revenue_east=130516.68, revenue_west=99428.16
  - Ranking: East, North, West, South
  - Derived difference(revenue_east, revenue_south): 39982.2
- [q3] 2024 revenue built steadily through the year: Q1 $36,108.32, Q2 $56,616.79, Q3 $71,674.98 (the strongest quarter, $35,566.66 above Q1), before easing to $68,948.70 in Q4.
  - Reported values: revenue_2024_q1=36108.32, revenue_2024_q2=56616.79, revenue_2024_q3=71674.98, revenue_2024_q4=68948.7
  - Ranking: Q3, Q4, Q2, Q1
  - Derived difference(revenue_2024_q3, revenue_2024_q1): 35566.66
- [q4] Revenue increased 10.08% year over year, from $211,976.28 in 2023 to $233,348.79 in 2024 — an absolute gain of $21,372.51.
  - Reported values: revenue_2023=211976.28, revenue_2024=233348.79, revenue_yoy_change_pct=10.082501
  - Direction: increase
  - Derived difference(revenue_2024, revenue_2023): 21372.51
- [q5] High-discount electronics orders (discount of 20% or more) numbered 22 and produced $50,035.32 in revenue, about 11.24% of total company revenue.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.32
  - Derived share(electronics_high_discount_revenue, total_revenue): 11.24
- [q6] Order revenue is strongly right-skewed: the mean ($856.39) is about 2.73× the median ($313.28), the standard deviation is $1,295.74, and values range from $5.27 to $7,844.02.
  - Reported values: order_revenue_mean=856.394365, order_revenue_median=313.275, order_revenue_std=1295.742355, order_revenue_min=5.27, order_revenue_max=7844.02
  - Derived ratio(order_revenue_mean, order_revenue_median): 2.73
- [q7] The customer base is diversified: 222 unique customers placed orders, and the largest single customer contributed $27,793.12, just 6.24% of total revenue, indicating low customer-concentration risk.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.12, top_customer_revenue_share_pct=6.241086

## Limitations
- The data covers only 2023–2024, so longer-term seasonality and trends cannot be assessed from a single year-over-year comparison.
- Figures reflect revenue only; returns, cancellations, product costs and discount impact on margin are not captured, so revenue growth may not equal profit growth.
- The 20% cut-off defining high-discount electronics is arbitrary, and the reported counts and revenue are sensitive to that threshold.
- Order revenue is highly skewed, so averages are heavily influenced by a small number of very large orders.
- Regional and quarterly differences are descriptive; no statistical significance testing was performed to rule out random variation.

## Conclusion
2024 was a growth year: revenue rose 10.08% to $233,348.79, with quarterly momentum peaking in Q3. East and North are the strongest regions, the 222-customer base shows low concentration risk (top customer 6.24% of revenue), and high-discount electronics contribute a modest 11.24% of revenue. The wide gap between the median ($313.28) and mean ($856.39) order suggests distinct small- and large-order segments worth serving differently. Priorities: carry Q3 momentum into Q4 and investigate the South region, the weakest at $90,534.48.
