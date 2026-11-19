# Retail Sales Performance Report: 2023–2024

Across 520 orders, the business generated $445,325 in total revenue over the 2023–2024 period, with a year-over-year revenue increase of approximately 10.1%. The East region led all regions in revenue. A data issue caused all 2024 quarterly revenue figures to return zero, preventing quarterly trend analysis. High-discount electronics represent a notable revenue segment, and customer concentration is moderate with the top customer accounting for 6.2% of total revenue.

## Key findings
- [q1] The dataset contains 520 orders generating total revenue of $445,325.09, with an average order value of $856.39.
  - Reported values: total_revenue=445325.09, order_count=520.0, average_order_value=856.3944038461538
- [q2] The East region led with $130,516.69 in revenue, followed by North ($124,845.75), West ($99,428.16), and South ($90,534.49). East outpaced South by $39,982.20.
  - Reported values: revenue_east=130516.69, revenue_north=124845.75, revenue_west=99428.16, revenue_south=90534.49
  - Ranking: East, North, West, South
  - Derived difference(revenue_east, revenue_south): 39982.2
- [q3] All four 2024 quarterly revenue figures (Q1–Q4) returned $0.00 due to a data processing failure. No valid quarterly trend can be reported; this requires investigation into the date parsing or data coverage for 2024.
  - Reported values: revenue_2024_q1=0.0, revenue_2024_q2=0.0, revenue_2024_q3=0.0, revenue_2024_q4=0.0
  - Ranking: Q1, Q2, Q3, Q4
- [q4] Revenue grew from $211,976.29 in 2023 to $233,348.80 in 2024, a year-over-year increase of approximately 10.1%.
  - Reported values: revenue_2023=211976.29, revenue_2024=233348.8, revenue_yoy_change_pct=10.082500264534293
  - Direction: increase
  - Derived pct_change(revenue_2024, revenue_2023): 10.08
- [q5] There are 22 Electronics orders with a discount of 20% or more, generating $50,035.33 in combined revenue.
  - Reported values: electronics_high_discount_orders=22.0, electronics_high_discount_revenue=50035.33
- [q6] Order revenue is highly right-skewed: the mean is $856.39 but the median is only $313.28, with a standard deviation of $1,295.74. Values range from $5.27 to $7,844.02, indicating a small number of very large orders pulling the average upward.
  - Reported values: order_revenue_mean=856.3944038461538, order_revenue_median=313.275, order_revenue_std=1295.7423896952698, order_revenue_min=5.27, order_revenue_max=7844.02
- [q7] There are 222 unique customers. The highest-revenue customer contributed $27,793.13, representing 6.2% of total revenue, indicating moderate but notable concentration at the top.
  - Reported values: unique_customer_count=222.0, top_customer_revenue=27793.13, top_customer_revenue_share_pct=6.241087830914715
  - Derived share(top_customer_revenue, total_revenue): 6.24

## Limitations
- Both the cleaning and analysis pipeline stages reported validation failures; all findings should be treated as provisional until the pipeline is re-run on validated data.
- All 2024 quarterly revenue values are zero, indicating a likely date-parsing or data-coverage error in the analysis stage; the quarterly trend analysis is therefore unreliable.
- The contradiction between non-zero revenue_2024 ($233,348.80) and zero quarterly 2024 revenues suggests a date format inconsistency that was not resolved during cleaning.
- The cleaning stage failure may mean that duplicate records, outliers, or missing values were not fully addressed, potentially affecting all aggregated metrics.
- No product-level or margin data is available, so revenue figures cannot be translated into profitability insights.

## Conclusion
Despite pipeline validation failures, the data indicates positive overall momentum: 520 orders, $445,325 in total revenue, and approximately 10.1% year-over-year growth from 2023 to 2024. The East region leads in revenue, and order values are highly skewed, suggesting a long tail of small orders alongside a few high-value transactions. The 2024 quarterly trend is unresolvable due to a data error and must be re-investigated. Stakeholders should treat these figures as directional until a clean, validated pipeline run is completed.
