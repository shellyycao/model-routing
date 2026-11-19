# Retail Sales Performance Report: 2023–2024

Across 520 cleaned orders, the business generated $445,325 in total revenue over 2023–2024. Revenue grew 10.1% year-over-year, driven by a strong second half of 2024. The East region led all regions. Customer concentration is moderate, and order revenue is highly right-skewed, with a median far below the mean.

## Key findings
- [q1] The cleaned dataset contains 520 orders with total revenue of $445,325.09 and an average order value of $856.39.
  - Reported values: total_revenue=445325.09, order_count=520.0, average_order_value=856.39
- [q2] East led all regions with $130,516.69 in revenue, followed by North ($124,845.75), West ($99,428.16), and South ($90,534.49). East outpaced South by $39,982.20.
  - Reported values: revenue_east=130516.69, revenue_north=124845.75, revenue_west=99428.16, revenue_south=90534.49
  - Ranking: East, North, West, South
  - Derived difference(revenue_east, revenue_south): 39982.2
- [q3] 2024 quarterly revenue accelerated through Q3 then eased slightly: Q3 was the peak at $71,674.99, followed by Q4 ($68,948.71), Q2 ($56,616.79), and Q1 ($36,108.31). Q3 revenue was nearly double Q1.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Ranking: Q3, Q4, Q2, Q1
  - Derived ratio(revenue_2024_q3, revenue_2024_q1): 1.98
- [q4] Revenue increased from $211,976.29 in 2023 to $233,348.80 in 2024, a year-over-year growth of 10.1%.
  - Reported values: revenue_2023=211976.29, revenue_2024=233348.8, revenue_yoy_change_pct=10.08
  - Direction: increase
- [q5] 22 Electronics orders carried a discount of 20% or more, generating $50,035.33 in combined revenue — averaging $2,274.33 per order, well above the overall average.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
  - Derived ratio(electronics_high_discount_revenue, electronics_high_discount_orders): 2274.33
- [q6] Order revenue is highly right-skewed: the median is $313.28 versus a mean of $856.39, with a standard deviation of $1,295.74. Values range from $5.27 to $7,844.02, indicating a long tail of high-value orders.
  - Reported values: order_revenue_mean=856.39, order_revenue_median=313.28, order_revenue_std=1295.74, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] There are 222 unique customers. The top customer alone contributed $27,793.13, representing 6.2% of total revenue — a moderate but notable concentration.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.24
  - Derived share(top_customer_revenue, total_revenue): 6.24

## Limitations
- The dataset covers only two years (2023–2024); longer historical data would improve trend reliability.
- No product-level cost data is available, so profitability and margin impact of high discounts cannot be assessed.
- Customer identifiers are anonymised; repeat-purchase behaviour and churn cannot be evaluated.
- Regional definitions are not documented — it is unclear whether they reflect geography, sales territory, or another segmentation.
- The analysis uses order revenue as reported after discounts; pre-discount revenue comparisons are not possible with the available data.

## Conclusion
The business delivered solid 10.1% revenue growth in 2024, with the East region and the second half of the year as key drivers. The highly skewed order distribution and the top customer's 6.2% revenue share warrant attention to both upsell opportunities and concentration risk. High-discount Electronics orders generate above-average revenue per order, suggesting selective deep discounting may be effective, though margin impact should be monitored.
