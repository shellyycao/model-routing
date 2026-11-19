# Support Operations Cost and Performance Analysis

This report analyzes 220 support tickets with a total labor cost of $17,445.07. While the average satisfaction score is high at 4.14, significant inefficiencies exist. Email tickets show a 122% higher reopening rate than chat, and a segment of 9 high-cost tickets with low satisfaction indicates a quality control issue. Agent workload is relatively distributed, with the top agent handling 7.3% of all tickets.

## Key findings
- [q1] The dataset contains 220 tickets with a mean resolution time of 75.66 minutes and a total labor cost of $17,445.07.
  - Reported values: ticket_count=220.0, mean_resolution_minutes=75.6590909090909, total_labor_cost=17445.07
- [q2] Team Beta incurred the highest labor cost at $6,928.72, followed by Gamma ($5,911.44) and Alpha ($4,604.91).
  - Reported values: labor_cost_alpha=4604.91, labor_cost_beta=6928.72, labor_cost_gamma=5911.44
  - Ranking: Beta, Gamma, Alpha
- [q3] Chat channels have the longest mean resolution time at 82.23 minutes, followed by phone (74.07 minutes) and email (71.72 minutes).
  - Reported values: resolution_email=71.72380952380952, resolution_chat=82.23287671232876, resolution_phone=74.07142857142857
  - Ranking: chat, phone, email
- [q4] The reopening rate for email tickets is 15.24%, which is 122.48% higher than the chat reopening rate of 6.85%.
  - Reported values: reopen_rate_email_pct=15.238095238095239, reopen_rate_chat_pct=6.8493150684931505, email_vs_chat_reopen_change_pct=122.47619047619051
  - Direction: increase
- [q5] There are 9 tickets in the high-cost low-satisfaction segment, with a reopening rate of 11.11%.
  - Reported values: high_cost_low_sat_count=9.0, high_cost_low_sat_reopen_pct=11.11111111111111
- [q6] The median resolution time is 65.0 minutes with a standard deviation of 51.30 minutes. The mean satisfaction score is 4.14, though 14 records are missing this value.
  - Reported values: resolution_median=65.0, resolution_std=51.302729053162466, satisfaction_mean=4.140776699029126, satisfaction_missing_count=14.0
- [q7] 18 unique agents handled the tickets. The top agent handled 16 tickets, representing 7.27% of the total volume.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=16.0, top_agent_ticket_share_pct=7.2727272727272725

## Limitations
- The cleaning and analysis stages reported validation failures, suggesting potential data quality issues in the source pipeline.
- 14 tickets are missing satisfaction scores, which may bias the satisfaction analysis.
- The analysis assumes labor cost is the primary cost driver and does not account for overhead or technology costs.

## Conclusion
Operational efficiency varies significantly by channel and team. The high reopening rate for email tickets (15.24%) suggests a process failure that warrants immediate investigation. Additionally, the presence of high-cost, low-satisfaction tickets indicates a need for targeted quality intervention. Addressing these specific areas could reduce costs and improve overall customer satisfaction.
