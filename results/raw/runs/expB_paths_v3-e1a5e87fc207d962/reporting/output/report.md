# Retail Sales Performance Report (2023‑2024)

The analysis of cleaned retail order data shows solid growth in 2024, with total revenue reaching $445,325.09 across 520 orders (average $856.39 per order). The East region generated the most revenue, and quarterly revenue peaked in Q3. Year‑over‑year revenue increased by 10.08%, driven in part by high‑discount electronics sales. Revenue is concentrated among 222 customers, with the top customer accounting for 6.24% of total sales.

## Key findings
- [q1] In 2023‑2024 the company generated total revenue of $445,325.09 across 520 orders, yielding an average order value of $856.39.
  - Reported values: total_revenue=445325.09, order_count=520.0, average_order_value=856.39
- [q2] Regional revenue shows the East region leading, followed by North, West, and South.
  - Reported values: revenue_north=124845.75, revenue_south=90534.49, revenue_east=130516.69, revenue_west=99428.16
  - Ranking: East, North, West, South
- [q3] Quarterly revenue in 2024 increased through the year, with Q3 highest, then Q4, Q2, and Q1.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Ranking: Q3, Q4, Q2, Q1
- [q4] Year‑over‑year revenue rose from $211,976.29 in 2023 to $233,348.80 in 2024, a 10.08% increase.
  - Reported values: revenue_2023=211976.29, revenue_2024=233348.8, revenue_yoy_change_pct=10.0825
  - Direction: increase
  - Derived difference(revenue_2024, revenue_2023): 21372.51
- [q5] There were 22 high‑discount (≥20%) electronics orders contributing $50,035.33 in revenue.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
- [q6] Order revenue distribution: mean $856.39, median $313.28, standard deviation $1,295.74, ranging from $5.27 to $7,844.02.
  - Reported values: order_revenue_mean=856.39, order_revenue_median=313.28, order_revenue_std=1295.74, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] Revenue came from 222 distinct customers; the top customer generated $27,793.13, representing 6.24% of total revenue.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.2411

## Limitations
- The analysis relies on a single exported dataset; any missing or mis‑recorded orders are not accounted for.
- Discount percentages are taken as reported; the impact of promotional bundles or returns is not captured.
- Customer revenue share is based on total revenue without adjusting for multi‑order customers over time.

## Conclusion
Overall, the retail business demonstrated healthy growth in 2024, with revenue increasing year‑over‑year and strong performance in the East region and Q3. High‑discount electronics orders contributed notable revenue, while a modest concentration of sales among top customers suggests opportunities to broaden the customer base. Addressing data completeness and deeper profitability analysis will further inform strategic decisions.
