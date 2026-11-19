# Retail Sales Performance Report: 2023–2024

Across 520 cleaned orders, the business generated $445,325 in total revenue over 2023–2024, with a healthy 10.1% year-over-year increase from 2023 to 2024. The East region led all regions in revenue. Within 2024, revenue accelerated through Q3 before a modest Q4 dip. High-discount electronics represent a notable revenue pocket, and customer concentration is moderate with the top customer accounting for 6.2% of total revenue.

## Key findings
- [q1] The cleaned dataset contains 520 orders generating total revenue of $445,325.09, yielding an average order value of $856.39.
  - Reported values: total_revenue=445325.09, order_count=520.0, average_order_value=856.3944038461538
- [q2] East led all regions with $130,516.69 in revenue, followed by North ($124,845.75), West ($99,428.16), and South ($90,534.49). East outpaced South by $39,982.20.
  - Reported values: revenue_east=130516.69, revenue_north=124845.75, revenue_west=99428.16, revenue_south=90534.49
  - Ranking: East, North, West, South
  - Derived difference(revenue_east, revenue_south): 39982.2
- [q3] 2024 quarterly revenue rose sharply from Q1 ($36,108.31) through Q3 ($71,674.99), then eased slightly in Q4 ($68,948.71). Q2 came in at $56,616.79, ranking third.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Ranking: Q3, Q4, Q2, Q1
- [q4] Total revenue increased from $211,976.29 in 2023 to $233,348.80 in 2024, a year-over-year growth of 10.1%.
  - Reported values: revenue_2023=211976.29, revenue_2024=233348.8, revenue_yoy_change_pct=10.082500264534321
  - Direction: increase
- [q5] There are 22 Electronics orders with a discount of 20% or more, collectively generating $50,035.33 in revenue.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
- [q6] Order revenue is highly right-skewed: the mean is $856.39 but the median is only $313.28, with a standard deviation of $1,295.74. Values range from $5.27 to $7,844.02, indicating a long tail of high-value orders.
  - Reported values: order_revenue_mean=856.3944038461538, order_revenue_median=313.275, order_revenue_std=1295.7423896952698, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] The dataset spans 222 unique customers. The highest-revenue customer contributed $27,793.13, representing 6.2% of total revenue, indicating moderate but noteworthy concentration.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.241087830914715
  - Derived share(top_customer_revenue, total_revenue): 6.24

## Limitations
- The analysis covers only two calendar years (2023–2024); longer historical data would be needed to assess whether the 10.1% YoY growth is above or below trend.
- The revenue distribution is heavily right-skewed (mean nearly 3× the median), suggesting a small number of large orders drive aggregate figures; segment-level analysis would provide more actionable insight.
- High-discount Electronics analysis uses a fixed 20% threshold; sensitivity to alternative thresholds has not been tested.
- Customer concentration is assessed solely by revenue; order frequency and profitability per customer are not captured in this dataset.
- Regional boundaries and their composition are not defined in the data, limiting interpretation of regional differences.

## Conclusion
The business delivered solid growth in 2023–2024, with total revenue of $445,325 and a 10.1% year-over-year increase. The East region and the Q3 2024 quarter were standout performers. The wide spread in order values and moderate top-customer concentration warrant ongoing monitoring. Targeted review of high-discount Electronics orders and continued investment in the East and North regions are recommended priorities.
