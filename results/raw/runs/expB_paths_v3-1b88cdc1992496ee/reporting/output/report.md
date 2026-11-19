# Retail Sales Performance Report: 2023–2024

Across 520 cleaned orders, the business generated $445,325 in total revenue over 2023–2024, with a healthy 10.1% year-over-year increase from 2023 to 2024. The East region led all regions in revenue. Within 2024, revenue accelerated through Q3 before a modest Q4 dip. High-discount electronics represent a notable revenue pocket, and order revenue is highly right-skewed, with a small number of customers and orders driving disproportionate share.

## Key findings
- [q1] The cleaned dataset contains 520 orders generating total revenue of $445,325.09, yielding an average order value of $856.39.
  - Reported values: total_revenue=445325.09, order_count=520.0, average_order_value=856.39
- [q2] East led all regions with $130,516.69 in revenue, followed by North ($124,845.75), West ($99,428.16), and South ($90,534.49). East outpaced South by $39,982.20.
  - Reported values: revenue_east=130516.69, revenue_north=124845.75, revenue_west=99428.16, revenue_south=90534.49
  - Ranking: East, North, West, South
  - Derived difference(revenue_east, revenue_south): 39982.2
- [q3] 2024 quarterly revenue rose sharply from Q1 ($36,108.31) through Q3 ($71,674.99), then eased slightly in Q4 ($68,948.71). Q2 came in at $56,616.79. Q3 was the peak quarter, nearly double Q1.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Ranking: Q3, Q4, Q2, Q1
- [q4] Total revenue grew from $211,976.29 in 2023 to $233,348.80 in 2024, a year-over-year increase of 10.1%.
  - Reported values: revenue_2023=211976.29, revenue_2024=233348.8, revenue_yoy_change_pct=10.08
  - Direction: increase
  - Derived pct_change(revenue_2024, revenue_2023): 10.08
- [q5] Among Electronics orders with a discount of 20% or more, there are 22 orders totalling $50,035.33 in revenue, averaging approximately $2,274.33 per order.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
  - Derived ratio(electronics_high_discount_revenue, electronics_high_discount_orders): 2274.33
- [q6] Order revenue is highly right-skewed: the mean is $856.39 but the median is only $313.28, with a standard deviation of $1,295.74. Values range from $5.27 to $7,844.02, indicating a long upper tail of high-value orders.
  - Reported values: order_revenue_mean=856.39, order_revenue_median=313.28, order_revenue_std=1295.74, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] There are 222 unique customers. The single highest-revenue customer contributed $27,793.13, representing 6.2% of total revenue—a meaningful concentration risk given the broad customer base.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.24
  - Derived share(top_customer_revenue, total_revenue): 6.24

## Limitations
- The analysis covers only the cleaned subset of the raw export; any orders removed during cleaning are excluded and may affect representativeness.
- Regional assignments are taken as given in the data; no geographic validation was performed.
- The high-discount Electronics filter relies on the accuracy of the discount_pct and product_category fields after cleaning.
- Customer concentration is assessed on revenue only; order frequency or profitability per customer is not considered.
- The 2024 quarterly trend covers only the orders present in the dataset and may not reflect a full calendar year if data collection ended before 31 December 2024.

## Conclusion
The business delivered solid growth in 2023–2024, with total revenue of $445,325 and a 10.1% year-over-year uplift. The East region and Q3 2024 were standout performers. The highly skewed order distribution and a single customer accounting for 6.2% of revenue warrant attention for risk management. High-discount Electronics orders, while few in number, generate meaningful revenue and merit pricing-strategy review.
