# Retail Sales Performance Report, 2023-2024

Total 2023-2024 revenue was $445,325.07 across 520 orders, an average of $856.39 per order. Revenue grew 10.08% year over year, from $211,976.28 in 2023 to $233,348.79 in 2024, with 2024 momentum peaking in Q3. The East region leads regional sales, order values are highly skewed toward a small number of large orders, and customer concentration is low: the single largest customer accounts for just 6.24% of revenue.

## Key findings
- [q1] Overall performance: the cleaned 2023-2024 data shows total revenue of $445,325.07 across 520 orders, giving an average order value of $856.39.
  - Reported values: total_revenue=445325.07, order_count=520.0, average_order_value=856.3943653846154
- [q2] Regional comparison: the East leads with $130,516.68 in revenue, followed by the North ($124,845.75), the West ($99,428.16) and the South ($90,534.48); the East outperforms the South by $39,982.20.
  - Reported values: revenue_north=124845.75, revenue_south=90534.48, revenue_east=130516.68000000001, revenue_west=99428.16
  - Ranking: East, North, West, South
  - Derived difference(revenue_east, revenue_south): 39982.2
- [q3] 2024 quarterly trend: revenue built through the year, from $36,108.32 in Q1 to $56,616.79 in Q2, peaking at $71,674.98 in Q3 before easing to $68,948.70 in Q4; Q3 exceeded Q1 by $35,566.66.
  - Reported values: revenue_2024_q1=36108.32, revenue_2024_q2=56616.79, revenue_2024_q3=71674.98, revenue_2024_q4=68948.7
  - Ranking: Q3, Q4, Q2, Q1
  - Derived difference(revenue_2024_q3, revenue_2024_q1): 35566.66
- [q4] Year-over-year change: revenue increased from $211,976.28 in 2023 to $233,348.79 in 2024, a rise of 10.08%, equivalent to $21,372.51 in additional revenue.
  - Reported values: revenue_2023=211976.28, revenue_2024=233348.78999999998, revenue_yoy_change_pct=10.082500740177146
  - Direction: increase
  - Derived difference(revenue_2024, revenue_2023): 21372.51
- [q5] High-discount electronics: 22 electronics orders carried a discount of 20% or more, generating $50,035.32 in revenue, about 11.24% of total revenue.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.32
  - Derived share(electronics_high_discount_revenue, total_revenue): 11.24
- [q6] Order revenue distribution: revenue per order is highly right-skewed, with a mean of $856.39 roughly 2.73 times the median of $313.28, a standard deviation of $1,295.74, and values spanning $5.27 to $7,844.02.
  - Reported values: order_revenue_mean=856.3943653846154, order_revenue_median=313.275, order_revenue_std=1295.7423548861245, order_revenue_min=5.27, order_revenue_max=7844.02
  - Derived ratio(order_revenue_mean, order_revenue_median): 2.73
- [q7] Customer concentration: the base is broad, with 222 unique customers, and reliance on any single account is limited; the top customer contributed $27,793.12, or 6.24% of total revenue.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.12, top_customer_revenue_share_pct=6.241085865657642

## Limitations
- The data covers only 2023-2024, so longer-term trends and seasonality cannot be assessed; in particular, the Q3-to-Q4 2024 dip cannot be attributed to a cause.
- Figures reflect order revenue only; returns, cancellations, costs and margins are not captured, so high-discount electronics revenue does not indicate profitability.
- The analysis is descriptive; no statistical significance tests were run on regional or year-over-year differences.
- Customer concentration is summarised by the top customer alone; a broader view (e.g., top-10 share) is not available in these findings.

## Conclusion
The business is growing, with revenue up 10.08% in 2024 and momentum concentrated in the second half of the year. The East and North regions drive the majority of sales, while the South lags. Revenue depends on a small number of large orders rather than any single customer, suggesting opportunity in growing mid-sized orders and in reviewing the margin impact of deep electronics discounts.
