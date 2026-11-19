# Retail Sales Performance Report (2023‑2024)

The cleaned retail order data shows solid growth in 2024, with total revenue increasing 10.1% year‑over‑year to $233.3 K. East region leads revenue, and quarterly performance peaked in Q3. High‑discount electronics orders, while few, generate substantial revenue. Revenue distribution is skewed, and the top customer accounts for just over 6% of total sales.

## Key findings
- [q1] In 2023‑2024 the dataset contains 520 orders generating $445,325.09 in total revenue, yielding an average order value of $856.39.
  - Reported values: total_revenue=445325.08999999997, order_count=520.0, average_order_value=856.3944038461538
- [q2] Revenue by region ranks East highest, followed by North, West, and South.
  - Reported values: revenue_north=124845.75, revenue_south=90534.49, revenue_east=130516.69, revenue_west=99428.16
  - Ranking: East, North, West, South
- [q3] Quarterly revenue in 2024 increased through Q3, peaking at $71,674.99, then slightly declined in Q4.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Ranking: Q3, Q4, Q2, Q1
- [q4] Total revenue grew from $211,976.29 in 2023 to $233,348.80 in 2024, a year‑over‑year increase of 10.08% (an absolute rise of $21,372.51).
  - Reported values: revenue_2023=211976.28999999998, revenue_2024=233348.80000000002, revenue_yoy_change_pct=10.082500264534321
  - Direction: increase
  - Derived difference(revenue_2024, revenue_2023): 21372.51
- [q5] There were 22 high‑discount (≥20%) electronics orders contributing $50,035.33 in revenue, averaging $2,274.33 per order.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
  - Derived ratio(electronics_high_discount_revenue, electronics_high_discount_orders): 2274.33
- [q6] Order revenue distribution: mean $856.39, median $313.28, standard deviation $1,295.74, ranging from $5.27 to $7,844.02.
  - Reported values: order_revenue_mean=856.3944038461538, order_revenue_median=313.275, order_revenue_std=1295.7423896952698, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] The dataset includes 222 distinct customers; the top customer contributed $27,793.13, representing 6.24% of total revenue.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.241087830914715

## Limitations
- The analysis relies on a single exported CSV; any orders missing from the source file are not represented.
- Regional revenue totals assume the 'region' field is complete; missing or mis‑coded entries were treated as zero.
- Discount analysis uses a fixed 20% threshold and does not consider promotional bundles or coupon stacking.
- Revenue figures are not adjusted for inflation or currency fluctuations between 2023 and 2024.

## Conclusion
Overall, the retail business demonstrated healthy growth in 2024, driven by strong performance in the East region and a robust Q3. High‑discount electronics orders, though few, contribute disproportionately to revenue. Revenue distribution is heavily right‑skewed, indicating a mix of small and large orders, while customer concentration remains low, with the top customer accounting for just over 6% of sales. Continued monitoring of regional trends and discount strategies will support sustained growth.
