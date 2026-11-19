# Retail Sales Performance Report (2023‑2024)

The analysis of cleaned retail order data shows total revenue of $445.3 K across 520 orders, with an average order value of $856.39. Revenue is highest in the East region and grew 10.1% year‑over‑year, driven by a $21.4 K absolute increase in 2024. Quarterly revenue in 2024 rose to a peak in Q3. High‑discount electronics orders, though few, contributed $50.0 K (≈11.2% of total). Revenue is spread across 222 customers, with the top customer accounting for 6.24% of total sales.

## Key findings
- [q1] In 2023‑2024 the company generated total revenue of $445.3 K across 520 orders, yielding an average order value of $856.39.
  - Reported values: total_revenue=445325.08999999997, order_count=520.0, average_order_value=856.3944038461538
- [q2] Regional revenue varies, with the East region leading at $130.5 K, followed by North ($124.8 K), West ($99.4 K), and South ($90.5 K).
  - Reported values: revenue_north=124845.75, revenue_south=90534.49, revenue_east=130516.69, revenue_west=99428.16
  - Ranking: East, North, West, South
- [q3] Quarterly revenue in 2024 shows a rising trend, peaking in Q3 at $71.7 K, then Q4 $68.9 K, Q2 $56.6 K, and Q1 $36.1 K.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Ranking: Q3, Q4, Q2, Q1
- [q4] Total revenue grew from $212.0 K in 2023 to $233.3 K in 2024, an increase of $21.4 K (10.1 % YoY).
  - Reported values: revenue_2023=211976.28999999998, revenue_2024=233348.80000000002, revenue_yoy_change_pct=10.082500264534321
  - Direction: increase
  - Derived difference(revenue_2024, revenue_2023): 21372.51
- [q5] There were 22 Electronics orders with discounts of 20 % or higher, contributing $50.0 K in revenue (≈11.2 % of total revenue).
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
  - Derived share(electronics_high_discount_revenue, total_revenue): 11.24
- [q6] Order revenue distribution: mean $856.39, median $313.28, standard deviation $1,295.74, ranging from $5.27 to $7,844.02.
  - Reported values: order_revenue_mean=856.3944038461538, order_revenue_median=313.275, order_revenue_std=1295.7423896952698, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] Revenue came from 222 distinct customers; the top customer contributed $27,793.13, representing 6.24 % of total revenue.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.241087830914715

## Limitations
- The cleaning stage failed, so residual data quality issues (e.g., missing or malformed region values) may remain.
- Revenue figures are based on the exported order data and do not include returns, refunds, or offline sales.
- Discount percentages are taken as recorded; any post‑order adjustments are not reflected.
- Customer concentration analysis uses total revenue per customer but does not account for profit margins.

## Conclusion
Overall, the business demonstrated solid growth in 2024, with regional strengths in the East and a clear quarterly upward trend. High‑discount electronics orders, while a small share of order count, represent a notable portion of revenue. Customer base is fairly diversified, though the top customer accounts for over 6% of sales. Addressing data cleaning gaps will improve confidence in future analyses.
