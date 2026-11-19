# Retail Sales Performance Report: 2023–2024

Across 520 orders, the business generated $445,325 in total revenue over 2023–2024. Revenue grew 10.1% year-over-year, driven by a strong second half of 2024. The East region led all regions. High-discount electronics represent a notable revenue concentration risk, and a single customer accounts for 6.2% of total revenue.

## Key findings
- [q1] The business recorded 520 orders totalling $445,325.09 in revenue, yielding an average order value of $856.39.
  - Reported values: total_revenue=445325.09, order_count=520.0, average_order_value=856.39
- [q2] East led all regions with $130,516.69 in revenue, followed by North ($124,845.75), West ($99,428.16), and South ($90,534.49). East outpaced South by $39,982.20.
  - Reported values: revenue_east=130516.69, revenue_north=124845.75, revenue_west=99428.16, revenue_south=90534.49
  - Ranking: East, North, West, South
  - Derived difference(revenue_east, revenue_south): 39982.2
- [q3] 2024 quarterly revenue accelerated through Q3 then eased slightly: Q3 was the peak at $71,674.99, followed by Q4 ($68,948.71), Q2 ($56,616.79), and Q1 ($36,108.31). Revenue nearly doubled from Q1 to Q3.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Ranking: Q3, Q4, Q2, Q1
  - Derived difference(revenue_2024_q3, revenue_2024_q1): 35566.68
- [q4] Revenue increased year-over-year: 2023 revenue was $211,976.29 and 2024 revenue was $233,348.80, a gain of $21,372.51 or approximately 10.1%.
  - Reported values: revenue_2023=211976.29, revenue_2024=233348.8, revenue_yoy_change_pct=10.08
  - Direction: increase
  - Derived difference(revenue_2024, revenue_2023): 21372.51
- [q5] 22 Electronics orders carried a discount of 20% or more, generating $50,035.33 in combined revenue — an average of approximately $2,274.33 per high-discount order.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
  - Derived ratio(electronics_high_discount_revenue, electronics_high_discount_orders): 2274.33
- [q6] Order revenue is highly right-skewed: the mean is $856.39 but the median is only $313.28, with a standard deviation of $1,295.74. Values range from $5.27 to $7,844.02, indicating a long tail of large orders pulling the mean upward.
  - Reported values: order_revenue_mean=856.39, order_revenue_median=313.28, order_revenue_std=1295.74, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] There are 222 unique customers. The single highest-revenue customer contributed $27,793.13, representing 6.2% of total revenue — a meaningful concentration for one account.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.24
  - Derived share(top_customer_revenue, total_revenue): 6.24

## Limitations
- The dataset covers only two calendar years (2023–2024); longer historical data would be needed to assess whether the 10.1% YoY growth is a sustained trend or an anomaly.
- Customer identifiers are anonymised, so it is not possible to assess churn, repeat-purchase behaviour, or the business risk posed by the top customer without additional CRM data.
- High-discount Electronics analysis uses a fixed 20% threshold; the business impact of discounts just below this threshold is not captured.
- Regional labels (North, South, East, West) are not mapped to specific geographies, limiting actionability of regional findings.
- The order revenue distribution analysis does not distinguish between product categories, which may have very different price and margin profiles.

## Conclusion
The retail business delivered solid growth in 2023–2024, with total revenue of $445,325 and a 10.1% year-over-year increase. The East region and the second half of 2024 were the primary growth drivers. However, the highly skewed order distribution, notable customer concentration (one customer at 6.2% of revenue), and significant high-discount Electronics activity warrant attention to protect margin and reduce dependency risk going forward.
