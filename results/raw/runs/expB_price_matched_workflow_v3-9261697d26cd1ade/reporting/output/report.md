# 2023-2024 Retail Sales Performance Report

This report analyzes retail sales performance from 2023 to 2024 based on 520 verified orders. Total revenue reached $445,325.09, with a 10.1% year-over-year increase. The East region led regional sales, while Q3 2024 was the strongest quarter. High-discount electronics orders contributed $50,035.33, and the customer base showed healthy diversity with no single customer dominating revenue.

## Key findings
- [q1] The dataset contains 520 orders generating a total revenue of $445,325.09, resulting in an average order value of $856.39.
  - Reported values: total_revenue=445325.08999999997, order_count=520.0, average_order_value=856.3944038461538
- [q2] Revenue varied by region, with the East region generating the highest revenue at $130,516.69, followed by North at $124,845.75, West at $99,428.16, and South at $90,534.49.
  - Reported values: revenue_north=124845.75, revenue_south=90534.49, revenue_east=130516.69, revenue_west=99428.16
  - Ranking: East, North, West, South
- [q3] In 2024, quarterly revenue showed an upward trend through the first three quarters, peaking in Q3 at $71,674.99 before slightly decreasing to $68,948.71 in Q4. Q1 recorded the lowest revenue at $36,108.31.
  - Reported values: revenue_2024_q1=36108.31, revenue_2024_q2=56616.79, revenue_2024_q3=71674.99, revenue_2024_q4=68948.71
  - Ranking: Q3, Q4, Q2, Q1
- [q4] Comparing 2023 and 2024, revenue increased from $211,976.29 to $233,348.80, representing a year-over-year growth of 10.08%.
  - Reported values: revenue_2023=211976.28999999998, revenue_2024=233348.80000000002, revenue_yoy_change_pct=10.082500264534321
  - Direction: increase
- [q5] There were 22 orders in the Electronics category with a discount of 20% or higher, generating a total revenue of $50,035.33.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
- [q6] Order revenue distribution had a mean of $856.39 and a median of $313.28, indicating a right-skewed distribution. Values ranged from a minimum of $5.27 to a maximum of $7,844.02, with a standard deviation of $1,295.74.
  - Reported values: order_revenue_mean=856.3944038461538, order_revenue_median=313.275, order_revenue_std=1295.7423896952698, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] The customer base consists of 222 unique customers. The top customer contributed $27,793.13 in revenue, accounting for 6.24% of the total revenue.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.241087830914715

## Limitations
- The analysis relies on a single cleaned export file and may not reflect real-time operational data.
- Customer concentration analysis is limited to revenue contribution and does not assess purchase frequency or retention.
- Regional analysis assumes the 'region' field in the raw data is accurately populated.

## Conclusion
The business experienced solid growth of 10.08% from 2023 to 2024, with the East region and Q3 2024 performing best. The low customer concentration risk and diverse order values suggest a stable revenue base, though the high standard deviation relative to the mean warrants further investigation into high-value outliers.
