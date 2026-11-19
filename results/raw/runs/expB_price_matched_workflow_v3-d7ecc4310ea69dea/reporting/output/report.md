# Retail Sales Performance 2023–2024: Verified Findings Report

Cleaned 2023–2024 data show total revenue of $445,325.09 across 520 orders. Revenue grew 10.08% year over year to $233,348.80 in 2024, with quarterly revenue peaking in Q3 ($71,674.99) before a Q4 dip. East leads regional revenue; order values are highly skewed (median $313.28 vs mean $856.39), while the top customer represents just 6.24% of revenue, so customer concentration risk is low.

## Key findings
- [q1] Across the cleaned 2023–2024 data, total revenue was $445,325.09 on 520 orders, giving an average order value of $856.39.
  - Reported values: total_revenue=445325.08999999997, order_count=520.0, average_order_value=856.3944038461538
- [q2] East generated the most revenue ($130,516.69), ahead of North ($124,845.75), West ($99,428.16) and South ($90,534.49); East exceeded the lowest region, South, by $39,982.20.
  - Reported values: revenue_north=124845.75, revenue_south=90534.49, revenue_east=130516.69, revenue_west=99428.16
  - Ranking: East, North, West, South
  - Derived difference(revenue_east, revenue_south): 39982.2
- [q3] 2024 quarterly revenue rose from $36,108.31 in Q1 to $56,616.79 in Q2, peaked at $71,674.99 in Q3, then dipped to $68,948.71 in Q4; Q3 exceeded Q1 by $35,566.68.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Ranking: Q3, Q4, Q2, Q1
  - Derived difference(revenue_2024_q3, revenue_2024_q1): 35566.68
- [q4] Annual revenue increased from $211,976.29 in 2023 to $233,348.80 in 2024, a year-over-year rise of 10.08% ($21,372.51).
  - Reported values: revenue_2023=211976.28999999998, revenue_2024=233348.80000000002, revenue_yoy_change_pct=10.082500264534321
  - Direction: increase
  - Derived difference(revenue_2024, revenue_2023): 21372.51
- [q5] 22 Electronics orders carried discounts of at least 20%, totalling $50,035.33 — 11.24% of overall revenue from just 4.23% of all orders.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
  - Derived share(electronics_high_discount_revenue, total_revenue): 11.24
  - Derived share(electronics_high_discount_orders, order_count): 4.23
- [q6] Order revenue is strongly right-skewed: mean $856.39 versus median $313.28 (mean 2.73x the median), standard deviation $1,295.74, with orders spanning $5.27 to $7,844.02.
  - Reported values: order_revenue_mean=856.3944038461538, order_revenue_median=313.275, order_revenue_std=1295.7423896952698, order_revenue_min=5.27, order_revenue_max=7844.02
  - Derived ratio(order_revenue_mean, order_revenue_median): 2.73
- [q7] There are 222 distinct customers; the largest accounts for $27,793.13, or 6.24% of total revenue, indicating low customer concentration.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.241087830914715

## Limitations
- The dataset spans only 2023–2024, so longer-term trends and repeatable seasonality cannot be established.
- Only revenue is available; with no cost or margin fields, the profitability of the high-discount Electronics orders ($50,035.33) cannot be judged.
- The average order value ($856.39) is inflated by a small number of very large orders (max $7,844.02) and is not typical (median $313.28).
- Customer metrics assume customer_id values uniquely and consistently identify real customers.
- The cause of the Q4 2024 dip ($68,948.71 vs $71,674.99 in Q3) cannot be determined from these data alone.

## Conclusion
2024 closed with solid 10.08% growth and a strong Q3, but the Q4 slowdown, the lagging South region and heavy order-value skew warrant attention. Recommended next steps: investigate Q4 drivers, review deep-discount Electronics profitability, and track median—not just mean—order value.
