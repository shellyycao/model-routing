# Support Ticket Operations – Key Metrics Report

The analysis of 220 support tickets reveals overall resolution performance, cost distribution across teams, channel speed differences, and areas of concern such as high‑cost low‑satisfaction tickets. Team Beta bears the greatest labor cost, chat tickets resolve slower than other channels, and email tickets exhibit a markedly higher reopening rate compared with chat. Agent workload is spread across 18 staff, with the top agent handling 7.3% of tickets.

## Key findings
- [q1] The dataset contains 220 tickets, with an average resolution time of 75.66 minutes and total labor cost of $17,445.07.
  - Reported values: ticket_count=220.0, mean_resolution_minutes=75.6590909090909, total_labor_cost=17445.07
- [q2] Team labor costs differ, with Beta incurring the highest cost, followed by Gamma, then Alpha.
  - Reported values: labor_cost_alpha=4604.91, labor_cost_beta=6928.720000000001, labor_cost_gamma=5911.439999999999
  - Ranking: Beta, Gamma, Alpha
- [q3] Resolution speed varies by channel; chat tickets take the longest on average, phone is faster, and email is fastest.
  - Reported values: resolution_email=71.72380952380952, resolution_chat=82.23287671232876, resolution_phone=74.07142857142857
  - Ranking: chat, phone, email
- [q4] Email tickets have a reopening rate 122.48% higher than chat tickets, indicating a substantial increase.
  - Reported values: reopen_rate_email_pct=15.238095238095239, reopen_rate_chat_pct=6.8493150684931505, email_vs_chat_reopen_change_pct=122.47619047619051
  - Direction: increase
- [q5] There are 9 tickets meeting the high‑cost (≥$100) and low‑satisfaction (≤2) criteria, and 11.11% of them were reopened.
  - Reported values: high_cost_low_sat_count=9.0, high_cost_low_sat_reopen_pct=11.11111111111111
- [q6] The median resolution time is 65 minutes, with a standard deviation of 51.30 minutes; average satisfaction score is 4.14, and 14 tickets lack a satisfaction rating.
  - Reported values: resolution_median=65.0, resolution_std=51.302729053162466, satisfaction_mean=4.140776699029126, satisfaction_missing_count=14.0
- [q7] Tickets were handled by 18 distinct agents; the most active agent resolved 16 tickets, representing 7.27% of all tickets.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=16.0, top_agent_ticket_share_pct=7.2727272727272725

## Limitations
- The cleaning stage failed, so residual data quality issues (e.g., duplicate rows, inconsistent formats) may remain.
- Analysis stage also flagged as failed, indicating potential runtime warnings that were not captured.
- 14 tickets have missing satisfaction scores, limiting the completeness of satisfaction insights.
- The sample size (220 tickets) may not represent longer‑term trends.

## Conclusion
Overall ticket volume and cost are moderate, but notable inefficiencies exist: chat channels resolve slower, and email tickets experience a high reopening rate. Team Beta’s labor cost dominance suggests a focus area for cost‑optimization. Addressing the high‑cost, low‑satisfaction segment and improving data cleaning processes will enhance future reporting accuracy.
