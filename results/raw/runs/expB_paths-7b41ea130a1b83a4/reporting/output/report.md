# Retail Sales Performance Report (2023‑2024)

The analysis of cleaned retail order data reveals $445k total revenue across 520 orders, with an average order value of $856. Revenue is strongest in the East region and grew 10% year‑over‑year from 2023 to 2024. Quarterly revenue in 2024 shows a clear upward trajectory through Q3 before a slight dip in Q4. High‑discount Electronics orders, though few, generate high average revenue. Order values are highly variable, and the top customer contributes 6.2% of total sales.

## Key findings
- [q1] In 2023‑2024 the cleaned dataset contains 520 orders generating $445,325 in total revenue, with an average order value of $856.39.
  - Reported values: total_revenue=445325.09, order_count=520.0, average_order_value=856.39
  - Direction: not_applicable
- [q2] Regional revenue shows the East region leading ($130,517), followed by North ($124,846), West ($99,428) and South ($90,534).
  - Reported values: revenue_north=124845.75, revenue_south=90534.49, revenue_east=130516.69, revenue_west=99428.16
  - Direction: not_applicable
  - Ranking: East, North, West, South
- [q3] Quarterly revenue in 2024 grew from $36,108 in Q1 to $71,675 in Q3, indicating a strong upward trend, before a modest dip to $68,949 in Q4.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Direction: increase
- [q4] Revenue rose from $211,976 in 2023 to $233,349 in 2024, a year‑over‑year increase of $21,373 (10.08%).
  - Reported values: revenue_2023=211976.29, revenue_2024=233348.8, revenue_yoy_change_pct=10.08
  - Direction: increase
  - Derived difference(revenue_2024, revenue_2023): 21372.51
- [q5] There were 22 high‑discount (≥20%) Electronics orders, contributing $50,035 in revenue, averaging $2,274 per order.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
  - Direction: not_applicable
  - Derived ratio(electronics_high_discount_revenue, electronics_high_discount_orders): 2274.33
- [q6] Order values have a mean of $856, median $313, standard deviation $1,296, ranging from $5.27 to $7,844.
  - Reported values: order_revenue_mean=856.39, order_revenue_median=313.28, order_revenue_std=1295.74, order_revenue_min=5.27, order_revenue_max=7844.02
  - Direction: not_applicable
- [q7] The business served 222 distinct customers; the top customer accounted for $27,793 in sales, representing 6.24% of total revenue (average revenue per customer $2,007).
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.24
  - Direction: not_applicable
  - Derived share(top_customer_revenue, total_revenue): 6.24
  - Derived ratio(total_revenue, unique_customer_count): 2006.53

## Limitations
- The analysis relies on a single exported dataset; any missing or mis‑recorded orders are not accounted for.
- Discount percentages are taken as reported; the impact of promotional bundles or returns is not captured.
- Revenue figures are gross and do not reflect costs, taxes, or refunds.

## Conclusion
Retail sales have grown modestly year‑over‑year, driven by strong performance in the East region and a clear upward quarterly trend in 2024. High‑discount Electronics orders, while few, generate high average revenue. Customer concentration is low, with the top customer contributing just over 6% of total sales, indicating a diversified customer base. Ongoing monitoring of regional performance and discount strategies will help sustain growth.
