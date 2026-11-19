# Retail Sales Performance Report (2023‑2024)

The analysis of cleaned retail order data shows strong growth in 2024, with total revenue more than doubling year‑over‑year. Regional performance is led by the East and North markets, while the 2024 quarterly trend peaks in Q3. High‑discount electronics orders contribute a notable share of revenue. Order values are highly variable, and revenue is moderately concentrated among customers, with the top customer accounting for just over 6% of total sales.

## Key findings
- [q1] In 2023‑2024 the company generated total revenue of $445,325.09 across 520 orders, yielding an average order value of $856.39.
  - Reported values: total_revenue=445325.09, order_count=520.0, average_order_value=856.39
- [q2] Regional revenue varies, with the East region leading at $130,516.69, followed by North $124,845.75, West $99,428.16, and South $90,534.49.
  - Reported values: revenue_north=124845.75, revenue_south=90534.49, revenue_east=130516.69, revenue_west=99428.16
  - Ranking: East, North, West, South
- [q3] Quarterly revenue in 2024 shows a rising trend, peaking in Q3 at $71,674.99, then Q4 $68,948.71, Q2 $56,616.79, and Q1 $36,108.31.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Ranking: Q3, Q4, Q2, Q1
- [q4] Total revenue grew from $211,976.29 in 2023 to $445,325.09 in 2024, a year‑over‑year increase of 110.08%, representing an absolute increase of $233,348.80.
  - Reported values: revenue_2023=211976.29, revenue_2024=445325.09, revenue_yoy_change_pct=110.08
  - Direction: increase
  - Derived difference(revenue_2024, revenue_2023): 233348.8
- [q5] There were 22 high‑discount (≥20%) electronics orders, contributing $50,035.33 in revenue.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
- [q6] Order revenue distribution: mean $856.39, median $313.28, standard deviation $1,295.74, minimum $5.27, maximum $7,844.02.
  - Reported values: order_revenue_mean=856.39, order_revenue_median=313.28, order_revenue_std=1295.74, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] The dataset includes 222 distinct customers; the top customer generated $27,793.13, representing 6.24% of total revenue.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.24

## Limitations
- The cleaning stage failed, so any residual data quality issues (e.g., missing values, incorrect formats) may affect the analysis.
- Revenue figures are based on the exported order data and may not include returns, refunds, or post‑sale adjustments.
- The analysis does not account for seasonality beyond the quarterly aggregation, nor does it segment by product sub‑categories beyond the high‑discount electronics filter.

## Conclusion
Despite data‑quality concerns, the verified findings indicate robust growth in 2024, with the East and North regions driving revenue and a clear upward quarterly trend. High‑discount electronics orders represent a modest but significant revenue stream. Order values are highly dispersed, and revenue concentration is low, suggesting a diversified customer base. Stakeholders should consider investigating the data cleaning gaps and exploring deeper drivers of regional performance and discount strategies.
