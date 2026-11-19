# Retail Sales Performance Report: 2023–2024

Across 520 cleaned orders, the business generated $445,325 in total revenue over 2023–2024, with a healthy 10.1% year-over-year increase. The East region led all regions in revenue. Within 2024, revenue accelerated through Q3 before a modest Q4 dip. High-discount Electronics orders represent a notable revenue concentration risk, and a single top customer accounts for 6.2% of total revenue.

## Key findings
- [q1] The business recorded 520 orders totalling $445,325 in revenue, yielding an average order value of $856.39.
  - Reported values: total_revenue=445325.09, order_count=520.0, average_order_value=856.39
- [q2] The East region generated the highest revenue at $130,517, followed by North ($124,846), West ($99,428), and South ($90,534). East outpaced South by approximately $40,000.
  - Reported values: revenue_east=130516.69, revenue_north=124845.75, revenue_west=99428.16, revenue_south=90534.49
  - Ranking: East, North, West, South
  - Derived difference(revenue_east, revenue_south): 39982.2
- [q3] Within 2024, revenue grew strongly from Q1 ($36,108) through Q3 ($71,675) before declining slightly in Q4 ($68,949). Q2 contributed $56,617. Q3 was the peak quarter, nearly double Q1.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Ranking: Q3, Q4, Q2, Q1
  - Derived difference(revenue_2024_q3, revenue_2024_q1): 35566.68
- [q4] Total revenue grew from $211,976 in 2023 to $233,349 in 2024, a year-over-year increase of 10.1%, indicating solid business momentum.
  - Reported values: revenue_2023=211976.29, revenue_2024=233348.8, revenue_yoy_change_pct=10.08
  - Direction: increase
- [q5] There were 22 Electronics orders with a discount of 20% or more, generating $50,035 in combined revenue. These high-discount orders warrant margin scrutiny given their scale.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
- [q6] Order revenue is highly right-skewed: the mean is $856.39 but the median is only $313.28, with a standard deviation of $1,295.74. Orders range from $5.27 to $7,844.02, indicating a long tail of high-value transactions.
  - Reported values: order_revenue_mean=856.39, order_revenue_median=313.28, order_revenue_std=1295.74, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] The dataset contains 222 distinct customers. The single highest-revenue customer contributed $27,793, representing 6.2% of total revenue—a meaningful concentration for one account.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.24
  - Derived share(top_customer_revenue, total_revenue): 6.24

## Limitations
- The analysis covers only the cleaned subset of the raw export; any orders removed during cleaning are excluded and may affect representativeness.
- Discount percentage thresholds for the high-discount Electronics filter are applied as-is; the profitability or margin impact of those discounts is not assessed.
- Customer concentration is measured by revenue share only; order frequency and product mix per customer are not analysed.
- The 2024 quarterly trend covers only orders present in the dataset and may be incomplete if the export was pulled before year-end.
- Regional assignments are taken from the cleaned data without validation against geographic master data, so misclassified orders could distort regional comparisons.

## Conclusion
The business delivered $445,325 in revenue across 520 orders in 2023–2024, with a 10.1% year-over-year uplift. The East region leads geographically, and 2024 showed strong mid-year momentum peaking in Q3. The wide spread between mean and median order values highlights a skewed revenue distribution driven by a small number of large orders. Management should monitor high-discount Electronics activity for margin erosion and assess dependency on the top customer, who alone accounts for 6.2% of total revenue.
