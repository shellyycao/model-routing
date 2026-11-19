# Retail Sales Performance Report 2023-2024

The cleaned 2023-2024 retail dataset shows total revenue of $445,325.09 across 520 orders, an average order value of $856.39. Revenue grew 10.08% year over year in 2024, building quarter by quarter through Q3 before a modest Q4 pullback. The East and North regions are the largest revenue contributors, order values are highly skewed toward a minority of large orders, deep-discount Electronics orders account for about 11.24% of revenue, and customer concentration is low, with the top customer representing just 6.24% of total revenue.

## Key findings
- [q1] Across the cleaned 2023-2024 data, the business generated total revenue of $445,325.09 from 520 orders, giving an average order value of $856.39.
  - Reported values: total_revenue=445325.08999999997, order_count=520.0, average_order_value=856.3944038461538
  - Direction: not_applicable
- [q2] The East region leads with $130,516.69 in revenue, followed by North ($124,845.75), West ($99,428.16) and South ($90,534.49); East out-earned the lowest region, South, by $39,982.20.
  - Reported values: revenue_north=124845.75, revenue_south=90534.49, revenue_east=130516.69, revenue_west=99428.16
  - Direction: not_applicable
  - Ranking: East, North, West, South
  - Derived difference(revenue_east, revenue_south): 39982.2
- [q3] 2024 revenue climbed steadily from Q1 ($36,108.31) through Q2 ($56,616.79) to a Q3 peak ($71,674.99), then eased to $68,948.71 in Q4 - a $2,726.28 dip from the Q3 high. Ranked highest to lowest: Q3, Q4, Q2, Q1.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Direction: not_applicable
  - Ranking: Q3, Q4, Q2, Q1
  - Derived difference(revenue_2024_q3, revenue_2024_q4): 2726.28
- [q4] Revenue increased 10.08% year over year, rising from $211,976.29 in 2023 to $233,348.80 in 2024 - an absolute gain of $21,372.51.
  - Reported values: revenue_2023=211976.28999999998, revenue_2024=233348.80000000002, revenue_yoy_change_pct=10.082500264534321
  - Direction: increase
  - Derived difference(revenue_2024, revenue_2023): 21372.51
- [q5] 22 Electronics orders carried discounts of 20% or more, generating $50,035.33 in revenue - about 11.24% of total company revenue.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
  - Direction: not_applicable
  - Derived share(electronics_high_discount_revenue, total_revenue): 11.24
- [q6] Order revenue is strongly right-skewed: the mean order is $856.39 versus a median of $313.28, with a sample standard deviation of $1,295.74 and order values spanning $5.27 to $7,844.02.
  - Reported values: order_revenue_mean=856.3944038461538, order_revenue_median=313.275, order_revenue_std=1295.7423896952698, order_revenue_min=5.27, order_revenue_max=7844.02
  - Direction: not_applicable
- [q7] The data covers 222 distinct customers; the highest-revenue customer accounts for $27,793.13, or 6.24% of total revenue, indicating moderate rather than concentrated customer dependence.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.241087830914715
  - Direction: not_applicable

## Limitations
- Only two years (2023-2024) are covered, so longer-term trends and seasonality cannot be assessed.
- Order revenue is extremely skewed (std $1,295.74 vs median $313.28); averages are pulled upward by a few large orders.
- Analysis is revenue-only - no cost or margin data - so the 22 high-discount Electronics orders may be far less profitable than their $50,035.33 revenue suggests.
- The Q4 2024 dip ($68,948.71 vs Q3's $71,674.99) has no causal explanation in this data and no 2023 quarterly baseline for comparison.
- Customer concentration is measured by revenue share only; purchase recency, frequency and returns are not captured.

## Conclusion
2024 delivered solid growth of about 10% with balanced regional performance and low single-customer dependence. Priorities: sustain the East and North momentum, investigate the Q4 slowdown, and review deep-discount Electronics pricing for margin impact, since those 22 transactions contribute roughly 11% of revenue.
