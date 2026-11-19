# Retail Sales Performance Report (2023‑2024)

The cleaned retail order data shows solid growth in 2024, with total revenue rising 10.1% year‑over‑year to $445.3K across 520 orders. East region leads revenue, and Q3 2024 was the strongest quarter. High‑discount electronics orders, while few, contributed $50K. Revenue distribution is skewed, with a mean of $856 but a median of $313. Customer concentration is modest; the top customer accounts for just over 6% of revenue.

## Key findings
- [q1] In 2023‑2024 the cleaned dataset contains 520 orders generating $445,325.07 in total revenue, yielding an average order value of $856.39.
  - Reported values: total_revenue=445325.07, order_count=520.0, average_order_value=856.394365
- [q2] Revenue by region shows East leading, followed by North, West, and South.
  - Reported values: revenue_north=124845.75, revenue_south=90534.48, revenue_east=130516.68, revenue_west=99428.16
  - Ranking: East, North, West, South
- [q3] Quarterly revenue in 2024 increased from Q1 to a peak in Q3, then slightly declined in Q4.
  - Reported values: revenue_2024_q1=36108.32, revenue_2024_q2=56616.79, revenue_2024_q3=71674.98, revenue_2024_q4=68948.7
  - Ranking: Q3, Q4, Q2, Q1
- [q4] Revenue grew from $211,976.28 in 2023 to $233,348.79 in 2024, a year‑over‑year increase of 10.08%.
  - Reported values: revenue_2023=211976.28, revenue_2024=233348.79, revenue_yoy_change_pct=10.082501
  - Direction: increase
  - Derived difference(revenue_2024, revenue_2023): 21372.51
- [q5] There were 22 high‑discount (≥20%) electronics orders contributing $50,035.32 in revenue.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.32
- [q6] Order revenue distribution: mean $856.39, median $313.28, standard deviation $1,295.74, ranging from $5.27 to $7,844.02.
  - Reported values: order_revenue_mean=856.394365, order_revenue_median=313.275, order_revenue_std=1295.742355, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] The dataset includes 222 distinct customers; the top customer generated $27,793.12, representing 6.24% of total revenue.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.12, top_customer_revenue_share_pct=6.241086
  - Derived share(top_customer_revenue, total_revenue): 6.241086

## Limitations
- The analysis relies on a single exported dataset; any missing or mis‑recorded orders are not accounted for.
- Discount percentages are taken as reported; the impact of promotional bundles is not isolated.
- Revenue figures are not adjusted for inflation or currency fluctuations between 2023 and 2024.

## Conclusion
Overall, the retail business demonstrated healthy growth in 2024, driven by strong performance in the East region and a robust Q3. While high‑discount electronics orders contribute notable revenue, the order value distribution is highly skewed, indicating a mix of low‑ and high‑value transactions. Customer concentration remains low, with the top customer accounting for just over 6% of revenue, suggesting diversified revenue sources. Continued monitoring of regional trends and discount strategies will be key to sustaining growth.
