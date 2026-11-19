# Retail Sales Performance Report: 2023–2024

Across 520 orders, the business generated $445,325 in total revenue over 2023–2024, with a healthy 10.1% year-over-year increase from 2023 to 2024. The East region led all regions in revenue. Within 2024, revenue accelerated through Q3 before a modest Q4 dip. High-discount electronics represent a notable revenue segment, and order revenue is highly right-skewed, with a small number of customers driving disproportionate value.

## Key findings
- [q1] Total revenue across all 520 orders was $445,325.09, yielding an average order value of $856.39.
  - Reported values: total_revenue=445325.09, order_count=520.0, average_order_value=856.39
- [q2] East led all regions with $130,516.69 in revenue, followed by North ($124,845.75), West ($99,428.16), and South ($90,534.49). East outpaced South by $39,982.20.
  - Reported values: revenue_east=130516.69, revenue_north=124845.75, revenue_west=99428.16, revenue_south=90534.49
  - Ranking: East, North, West, South
  - Derived difference(revenue_east, revenue_south): 39982.2
- [q3] 2024 quarterly revenue grew strongly from Q1 ($36,108.31) through Q3 ($71,674.99), then eased slightly in Q4 ($68,948.71). Q2 recorded $56,616.79. Q3 was the peak quarter.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Ranking: Q3, Q4, Q2, Q1
- [q4] Revenue grew year-over-year by 10.1%, rising from $211,976.29 in 2023 to $233,348.80 in 2024, an increase of $21,372.51.
  - Reported values: revenue_2023=211976.29, revenue_2024=233348.8, revenue_yoy_change_pct=10.08
  - Direction: increase
  - Derived difference(revenue_2024, revenue_2023): 21372.51
- [q5] Among Electronics orders with a discount of 20% or more, there were 22 orders totalling $50,035.33 in revenue, averaging $2,274.33 per order.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
  - Derived ratio(electronics_high_discount_revenue, electronics_high_discount_orders): 2274.33
- [q6] Order revenue is highly right-skewed: the mean is $856.39 but the median is only $313.28, with a standard deviation of $1,295.74. Values range from $5.27 to $7,844.02, indicating a long upper tail of high-value orders.
  - Reported values: order_revenue_mean=856.39, order_revenue_median=313.28, order_revenue_std=1295.74, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] There are 222 unique customers. The single highest-revenue customer contributed $27,793.13, representing 6.24% of total revenue, indicating moderate concentration risk.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.24
  - Derived share(top_customer_revenue, total_revenue): 6.24

## Limitations
- The dataset covers only two years (2023–2024); longer historical data would improve trend reliability and seasonality assessment.
- Customer identity is based solely on customer_id; duplicate or merged accounts could distort concentration metrics.
- Discount percentages are taken at face value from the export; any data-entry errors in discount_pct would affect the high-discount electronics filter.
- Regional assignments are fixed per order and may not reflect actual delivery geography or sales territory boundaries.
- The analysis uses cleaned data only; records removed during cleaning are not characterised, so survivorship bias cannot be ruled out.

## Conclusion
The business delivered solid growth in 2023–2024, with total revenue of $445,325 and a 10.1% year-over-year increase. The East region is the top revenue contributor, and 2024 showed a strong upward quarterly trend peaking in Q3. The highly skewed order distribution and a single customer accounting for 6.2% of revenue warrant attention to customer diversification and upsell opportunities among mid-tier buyers. High-discount electronics orders, while limited in volume, generate meaningful revenue and merit margin scrutiny.
