# Retail Sales Performance Report: 2023–2024

Across 520 cleaned orders, the business generated $445,325 in total revenue over 2023–2024, with a healthy 10.1% year-over-year increase from 2023 to 2024. The East region led all regions in revenue. Within 2024, revenue accelerated through Q3 before a modest Q4 dip. Customer concentration is moderate, with the top customer accounting for 6.2% of total revenue. High-discount Electronics orders represent a notable revenue pocket worth monitoring.

## Key findings
- [q1] Total revenue across all 520 orders was $445,325.09, yielding an average order value of $856.39.
  - Reported values: total_revenue=445325.09, order_count=520.0, average_order_value=856.39
- [q2] East led all regions with $130,516.69 in revenue, followed by North ($124,845.75), West ($99,428.16), and South ($90,534.49). East outpaced South by approximately $40,000.
  - Reported values: revenue_east=130516.69, revenue_north=124845.75, revenue_west=99428.16, revenue_south=90534.49
  - Ranking: East, North, West, South
  - Derived difference(revenue_east, revenue_south): 39982.2
- [q3] Within 2024, revenue grew strongly from Q1 ($36,108.31) through Q3 ($71,674.99) before declining slightly in Q4 ($68,948.71). Q2 recorded $56,616.79. Q3 was the peak quarter.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Ranking: Q3, Q4, Q2, Q1
- [q4] Revenue grew from $211,976.29 in 2023 to $233,348.80 in 2024, a year-over-year increase of 10.1%.
  - Reported values: revenue_2023=211976.29, revenue_2024=233348.8, revenue_yoy_change_pct=10.08
  - Direction: increase
- [q5] There were 22 Electronics orders with a discount of 20% or more, generating $50,035.33 in combined revenue — representing approximately 11.2% of total revenue.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
  - Derived share(electronics_high_discount_revenue, total_revenue): 11.24
- [q6] Order revenue is highly right-skewed: the mean is $856.39 but the median is only $313.28, with a standard deviation of $1,295.74. Values range from $5.27 to $7,844.02, indicating a long tail of high-value orders.
  - Reported values: order_revenue_mean=856.39, order_revenue_median=313.28, order_revenue_std=1295.74, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] The dataset contains 222 distinct customers. The highest-revenue customer contributed $27,793.13, equal to 6.2% of total revenue, suggesting moderate but noteworthy concentration at the top.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.24

## Limitations
- The dataset covers only 520 orders; findings may not be representative of the full customer or product population.
- No product-level margin data is available, so revenue figures cannot be translated into profitability.
- Customer identifiers are anonymised; churn, repeat-purchase behaviour, and lifetime value cannot be assessed.
- The cause of the Q4 2024 revenue dip relative to Q3 cannot be determined from order data alone — seasonal, promotional, or supply factors are unknown.
- High-discount Electronics analysis is based on discount_pct thresholds in the cleaned data; the original discount policy context is not available to assess whether these discounts were intentional promotions or data anomalies.

## Conclusion
The business delivered solid growth in 2023–2024, with total revenue of $445,325 and a 10.1% year-over-year increase. The East region and Q3 2024 were standout performers. The wide gap between mean and median order values signals a skewed revenue distribution driven by a minority of large orders. High-discount Electronics orders warrant pricing discipline review, and the top customer's 6.2% revenue share merits retention focus. Overall, the trajectory is positive, but diversifying revenue across customers and smoothing seasonal volatility should be priorities going forward.
