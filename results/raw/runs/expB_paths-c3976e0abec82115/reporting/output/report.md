# Retail Sales Performance Report (2023‑2024)

The cleaned retail dataset shows solid growth in 2024, with total revenue reaching $445,325.09 across 520 orders (average order value $856.39). The East region leads in sales, and quarterly revenue rose through the first three quarters before a slight dip in Q4. Year‑over‑year revenue grew 10.08 % (an increase of $21,372.51). High‑discount electronics orders, though few (22), contributed $50,035.33. Order values are highly variable (mean $856.39, median $313.28, SD $1,295.74, range $5.27‑$7,844.02). Customer concentration is modest: 222 unique customers, with the top customer accounting for 6.24 % of total revenue.

## Key findings
- [q1] In 2023‑2024 the company generated $445,325.09 in revenue across 520 orders, yielding an average order value of $856.39.
  - Reported values: total_revenue=445325.09, order_count=520.0, average_order_value=856.39
  - Direction: not_applicable
- [q2] Regional revenue ranking shows East leading with $130,516.69, followed by North ($124,845.75), West ($99,428.16) and South ($90,534.49).
  - Reported values: revenue_north=124845.75, revenue_south=90534.49, revenue_east=130516.69, revenue_west=99428.16
  - Direction: not_applicable
  - Ranking: East, North, West, South
- [q3] Quarterly revenue in 2024 grew from $36,108.31 in Q1 to $56,616.79 in Q2 and peaked at $71,674.99 in Q3 before a modest dip to $68,948.71 in Q4, indicating an overall upward trend.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Direction: increase
- [q4] Revenue increased from $211,976.29 in 2023 to $233,348.80 in 2024, a year‑over‑year growth of 10.08 % (an absolute increase of $21,372.51).
  - Reported values: revenue_2023=211976.29, revenue_2024=233348.8, revenue_yoy_change_pct=10.08
  - Direction: increase
  - Derived difference(revenue_2024, revenue_2023): 21372.51
- [q5] There were 22 high‑discount (≥20 %) electronics orders contributing $50,035.33 in revenue.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
  - Direction: not_applicable
- [q6] Order values have a mean of $856.39, median $313.28, standard deviation $1,295.74, ranging from a low of $5.27 to a high of $7,844.02.
  - Reported values: order_revenue_mean=856.39, order_revenue_median=313.28, order_revenue_std=1295.74, order_revenue_min=5.27, order_revenue_max=7844.02
  - Direction: not_applicable
- [q7] The dataset contains 222 distinct customers; the top customer generated $27,793.13, representing 6.24 % of total revenue.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.24
  - Direction: not_applicable
  - Derived share(top_customer_revenue, total_revenue): 6.24

## Limitations
- The analysis covers only two fiscal years (2023‑2024) and may not reflect longer‑term trends.
- Data is limited to recorded orders; any offline or untracked sales are excluded.
- High‑discount electronics analysis uses a fixed 20 % threshold, which may omit near‑threshold cases.
- Customer concentration metric does not account for future growth potential of top customers.

## Conclusion
Overall, the retail business demonstrated healthy growth in 2024, with strong regional performance in the East and a modest increase in quarterly revenues. While order values are highly variable, the average order remains robust. Customer concentration is low, indicating a diversified base, though the top customer still contributes a notable share of revenue. Continued monitoring of discount strategies and regional dynamics will support sustained performance.
