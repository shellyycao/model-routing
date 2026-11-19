# 2023-2024 Retail Sales Performance Report

Analysis of 520 verified orders reveals total revenue of $445,325.07 for 2023-2024, with a strong 10.1% year-over-year increase in 2024. The East region leads regional performance, and 2024 quarterly revenue shows robust growth in the second half. High-discount electronics orders represent a notable portion of sales, and customer concentration remains moderate.

## Key findings
- [q1] The dataset contains 520 orders generating a total revenue of $445,325.07, resulting in an average order value of $856.39.
  - Reported values: total_revenue=445325.07, order_count=520.0, average_order_value=856.394365
- [q2] The East region generated the highest revenue at $130,516.68, followed by North at $124,845.75. The West region recorded $99,428.16, and the South region contributed $90,534.48.
  - Reported values: revenue_north=124845.75, revenue_south=90534.48, revenue_east=130516.68, revenue_west=99428.16
  - Ranking: East, North, West, South
- [q3] In 2024, quarterly revenue peaked in Q3 at $71,674.98. Revenue increased from $36,108.32 in Q1 to $56,616.79 in Q2, reaching a high in Q3 before slightly decreasing to $68,948.70 in Q4.
  - Reported values: revenue_2024_q1=36108.32, revenue_2024_q2=56616.79, revenue_2024_q3=71674.98, revenue_2024_q4=68948.7
  - Ranking: Q3, Q4, Q2, Q1
- [q4] Revenue increased by 10.08% year-over-year, rising from $211,976.28 in 2023 to $233,348.79 in 2024.
  - Reported values: revenue_2023=211976.28, revenue_2024=233348.79, revenue_yoy_change_pct=10.082501
  - Direction: increase
- [q5] There were 22 Electronics orders with discounts of 20% or higher, generating a combined revenue of $50,035.32.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.32
  - Derived share(electronics_high_discount_revenue, total_revenue): 11.2
- [q6] Order revenue showed significant variation with a mean of $856.39 and a median of $313.28. The standard deviation was $1,295.74, with values ranging from a minimum of $5.27 to a maximum of $7,844.02.
  - Reported values: order_revenue_mean=856.394365, order_revenue_median=313.275, order_revenue_std=1295.742355, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] The 520 orders originated from 222 unique customers. The top customer contributed $27,793.12 in revenue, accounting for 6.24% of the total.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.12, top_customer_revenue_share_pct=6.241086

## Limitations
- The analysis relies on a cleaned export of retail orders; any systematic errors in the raw data source may impact the accuracy of these findings.
- Customer concentration analysis is limited to revenue contribution and does not assess purchase frequency or retention rates.

## Conclusion
The business demonstrates healthy growth with a 10.1% revenue increase in 2024 compared to 2023. The East and North regions are the primary revenue drivers, and the strong performance in Q3 2024 suggests seasonality or successful initiatives in the second half. The high average order value relative to the median indicates a right-skewed distribution driven by high-value transactions, which merits further investigation into the characteristics of these large orders.
