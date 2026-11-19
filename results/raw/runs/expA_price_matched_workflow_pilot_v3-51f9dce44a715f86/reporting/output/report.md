# Retail Sales Performance 2023-2024: Verified Findings Report

Cleaned order data shows $445,325.07 in total revenue across 520 orders in 2023-2024, with revenue growing 10.08% year over year to $233,348.79 in 2024. The East region leads regional sales, 2024 revenue built steadily to a Q3 peak, and customer concentration is low (top customer: 6.24% of revenue). Order revenue is highly right-skewed, with a small number of large orders pulling the mean well above the median.

## Key findings
- [q1] Overall 2023-2024 performance: total revenue of $445,325.07 across 520 orders, giving an average order value of $856.39.
  - Reported values: total_revenue=445325.07, order_count=520.0, average_order_value=856.394365
  - Direction: not_applicable
- [q2] Regional revenue ranking (highest to lowest): East $130,516.68, North $124,845.75, West $99,428.16, South $90,534.48. The leading East region exceeded the trailing South region by $39,982.20.
  - Reported values: revenue_north=124845.75, revenue_south=90534.48, revenue_east=130516.68, revenue_west=99428.16
  - Direction: not_applicable
  - Ranking: East, North, West, South
  - Derived difference(revenue_east, revenue_south): 39982.2
- [q3] 2024 quarterly revenue rose through the year before a slight Q4 easing: Q1 $36,108.32, Q2 $56,616.79, Q3 $71,674.98 (peak), Q4 $68,948.70. Q3 exceeded Q1 by $35,566.66, showing strong momentum across the year despite the Q4 dip.
  - Reported values: revenue_2024_q1=36108.32, revenue_2024_q2=56616.79, revenue_2024_q3=71674.98, revenue_2024_q4=68948.7
  - Direction: not_applicable
  - Ranking: Q3, Q4, Q2, Q1
  - Derived difference(revenue_2024_q3, revenue_2024_q1): 35566.66
- [q4] Year-over-year revenue increased 10.08%, rising from $211,976.28 in 2023 to $233,348.79 in 2024, an absolute gain of $21,372.51.
  - Reported values: revenue_2023=211976.28, revenue_2024=233348.79, revenue_yoy_change_pct=10.082501
  - Direction: increase
  - Derived difference(revenue_2024, revenue_2023): 21372.51
- [q5] 22 Electronics orders carried discounts of 20% or more, generating $50,035.32 in revenue, equivalent to an 11.24% share of total revenue.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.32
  - Direction: not_applicable
  - Derived share(electronics_high_discount_revenue, total_revenue): 11.24
- [q6] Order revenue is strongly right-skewed: mean $856.39 versus median $313.28 (the mean is about 2.73x the median), with a standard deviation of $1,295.74 and values spanning $5.27 to $7,844.02. A minority of large orders drives much of the revenue.
  - Reported values: order_revenue_mean=856.394365, order_revenue_median=313.275, order_revenue_std=1295.742355, order_revenue_min=5.27, order_revenue_max=7844.02
  - Direction: not_applicable
  - Derived ratio(order_revenue_mean, order_revenue_median): 2.73
- [q7] Customer concentration is low: 222 unique customers placed orders, and the highest-revenue customer contributed $27,793.12, just 6.24% of total revenue, indicating a well-diversified customer base.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.12, top_customer_revenue_share_pct=6.241086
  - Direction: not_applicable

## Limitations
- The analysis covers revenue only; no cost, margin or profit data was available, so the impact of high discounts (e.g., the 22 Electronics orders at >=20% off) on profitability cannot be assessed.
- Only two years of data were analysed, limiting the ability to separate genuine growth from seasonality or one-off effects; the Q4 2024 dip versus Q3 cannot be explained from the available fields.
- Order revenue is highly skewed (mean $856.39 vs median $313.28), so averages can be misleading and a small number of large orders disproportionately influence totals.
- Findings depend on the cleaning stage's decisions; any orders excluded during cleaning are not reflected in these figures.

## Conclusion
The business delivered solid, broad-based performance in 2023-2024: revenue grew 10.08% to $233,348.79 in 2024, quarterly momentum strengthened through Q3, the East and North regions lead sales, and revenue rests on a diversified base of 222 customers rather than a few large accounts. Priorities for stakeholders: investigate the Q4 slowdown, monitor high-discount Electronics orders for margin risk, and track the skew toward large orders when setting targets.
