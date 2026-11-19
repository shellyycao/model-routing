# Retail Sales 2023-2024: Verified Performance Report

Across the cleaned 2023-2024 order data the business recorded total revenue of $445,325.09 on 520 orders (average order value $856.39). Revenue rose 10.08% year over year, from $211,976.29 in 2023 to $233,348.80 in 2024. The East region generated the most revenue, and within 2024 revenue peaked in Q3. Order revenue is strongly right-skewed, and the single largest customer accounts for only 6.24% of revenue, indicating low single-customer dependence.

## Key findings
- [q1] Overall performance for 2023-2024: total revenue of $445,325.09 across 520 orders, giving an average order value of $856.39.
  - Reported values: total_revenue=445325.08999999997, order_count=520.0, average_order_value=856.3944038461538
- [q2] Regional revenue, highest to lowest: East $130,516.69, North $124,845.75, West $99,428.16, South $90,534.49; the leading East region exceeded the lowest region (South) by $39,982.20.
  - Reported values: revenue_north=124845.75, revenue_south=90534.49, revenue_east=130516.69, revenue_west=99428.16
  - Ranking: East, North, West, South
  - Derived difference(revenue_east, revenue_south): 39982.2
- [q3] Within 2024, quarterly revenue climbed from $36,108.31 in Q1 to $56,616.79 in Q2 and peaked at $71,674.99 in Q3, before easing to $68,948.71 in Q4; ranked highest to lowest: Q3, Q4, Q2, Q1.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Ranking: Q3, Q4, Q2, Q1
- [q4] Revenue increased year over year: $211,976.29 in 2023 versus $233,348.80 in 2024, a rise of 10.08%.
  - Reported values: revenue_2023=211976.28999999998, revenue_2024=233348.80000000002, revenue_yoy_change_pct=10.082500264534321
  - Direction: increase
- [q5] High-discount Electronics orders (discount_pct >= 20) numbered 22 and produced $50,035.33 in revenue, roughly 11.24% of total revenue.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
  - Derived share(electronics_high_discount_revenue, total_revenue): 11.24
- [q6] Order revenue is highly right-skewed: the mean ($856.39) sits well above the median ($313.28), with a large sample standard deviation ($1,295.74) and values spanning $5.27 to $7,844.02.
  - Reported values: order_revenue_mean=856.3944038461538, order_revenue_median=313.275, order_revenue_std=1295.7423896952698, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] The data contains 222 distinct customers; the highest-revenue customer contributed $27,793.13, equal to 6.24% of total revenue, indicating limited single-customer concentration.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.241087830914715

## Limitations
- Only two years (2023-2024) are covered, so the 10.08% YoY increase cannot be benchmarked against a longer multi-year trend or seasonality beyond 2024 quarters.
- Figures are gross order revenue; no cost or margin data were provided, so the high-discount Electronics revenue of $50,035.33 may overstate its profit contribution.
- Regional comparison uses revenue totals only, with no order counts, customer counts, or market-size normalization per region, so differences may reflect market size rather than performance.
- Order revenue is strongly skewed (median $313.28 vs mean $856.39, max $7,844.02), so the mean and standard deviation are sensitive to a small number of large orders.
- Customer concentration is assessed only via the single top customer; repeat-purchase, cohort retention, and churn were not analysed.

## Conclusion
2024 delivered a clear 10.08% revenue increase over 2023, with momentum building through Q3 before a Q4 cooldown. East and North are the revenue anchors, while South lags. The skewed order distribution and modest 6.24% top-customer share suggest growth is broad-based rather than dependent on a few accounts; priority actions are to sustain Q2-Q3 momentum into Q4 and to lift the South region.
