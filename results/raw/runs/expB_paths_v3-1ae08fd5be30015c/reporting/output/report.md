# Retail Sales Performance Report (2023‑2024)

The cleaned retail dataset shows total revenue of $445,325.07 across 520 orders, with an average order value of $856.39. Revenue is strongest in the East region and grew 10.08% year‑over‑year. Quarterly revenue in 2024 peaked in Q3. High‑discount electronics orders contributed $50,035.32. Revenue distribution is wide, and the top customer accounts for 6.24% of total sales.

## Key findings
- [q1] In 2023‑2024 the company generated total revenue of $445,325.07 across 520 orders, yielding an average order value of $856.39.
  - Reported values: total_revenue=445325.07, order_count=520.0, average_order_value=856.39
- [q2] Revenue by region shows East leading, followed by North, West, and South.
  - Reported values: revenue_north=124845.75, revenue_south=90534.48, revenue_east=130516.68, revenue_west=99428.16
  - Ranking: East, North, West, South
- [q3] Quarterly revenue in 2024 increased through the year, with Q3 highest, then Q4, Q2, and Q1.
  - Reported values: revenue_2024_q1=36108.32, revenue_2024_q2=56616.79, revenue_2024_q3=71674.98, revenue_2024_q4=68948.7
  - Ranking: Q3, Q4, Q2, Q1
- [q4] Revenue grew from $211,976.28 in 2023 to $233,348.79 in 2024, a year‑over‑year increase of 10.08%.
  - Reported values: revenue_2023=211976.28, revenue_2024=233348.79, revenue_yoy_change_pct=10.08
  - Direction: increase
- [q5] There were 22 high‑discount (≥20%) electronics orders contributing $50,035.32 in revenue.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.32
- [q6] Order revenue distribution: mean $856.39, median $313.28, standard deviation $1,295.74, ranging from $5.27 to $7,844.02.
  - Reported values: order_revenue_mean=856.39, order_revenue_median=313.28, order_revenue_std=1295.74, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] Revenue came from 222 distinct customers; the top customer generated $27,793.12, representing 6.24% of total revenue.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.12, top_customer_revenue_share_pct=6.24
  - Derived share(top_customer_revenue, total_revenue): 6.24

## Limitations
- The analysis relies on a single exported dataset; any missing or mis‑recorded transactions are not accounted for.
- Discount percentages are taken as reported; the impact of promotional bundles is not isolated.
- Customer revenue share is based on total revenue without adjusting for returns or refunds.

## Conclusion
Overall, the business demonstrated solid growth in 2024, especially in the East region and during the third quarter. High‑discount electronics orders represent a notable revenue stream, while revenue concentration remains modest, with the top customer contributing just over 6% of sales. Continued monitoring of regional performance and discount strategies will help sustain growth.
