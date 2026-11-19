# Support Operations Analysis Report

This report details verified findings on 220 support tickets, revealing a total labor cost of $17,445.07 and an average resolution time of 75.7 minutes. Analysis indicates that the Beta team incurs the highest labor costs, while email tickets show a significantly higher reopening rate compared to chat. A small segment of high-cost, low-satisfaction tickets was identified, and agent workload is relatively distributed with no single agent dominating the volume.

## Key findings
- [q1] The dataset contains 220 tickets with a total labor cost of $17,445.07 and a mean resolution time of 75.66 minutes.
  - Reported values: ticket_count=220.0, total_labor_cost=17445.07, mean_resolution_minutes=75.6590909090909
- [q2] Team Beta has the highest total labor cost at $6,928.72, followed by Gamma ($5,911.44) and Alpha ($4,604.91).
  - Reported values: labor_cost_alpha=4604.91, labor_cost_beta=6928.72, labor_cost_gamma=5911.44
  - Ranking: Beta, Gamma, Alpha
- [q3] Chat channels have the longest mean resolution time at 82.23 minutes, followed by phone (74.07 minutes) and email (71.72 minutes).
  - Reported values: resolution_chat=82.23287671232876, resolution_phone=74.07142857142857, resolution_email=71.72380952380952
  - Ranking: chat, phone, email
- [q4] The email reopening rate is 15.24%, which is 122.48% higher than the chat reopening rate of 6.85%.
  - Reported values: reopen_rate_email_pct=15.238095238095239, reopen_rate_chat_pct=6.8493150684931505, email_vs_chat_reopen_change_pct=122.47619047619051
  - Direction: increase
- [q5] There are 9 tickets classified as high-cost and low-satisfaction, representing a segment with an 11.11% reopening rate.
  - Reported values: high_cost_low_sat_count=9.0, high_cost_low_sat_reopen_pct=11.11111111111111
- [q6] Resolution times have a median of 65.0 minutes and a standard deviation of 51.3 minutes. The mean satisfaction score is 4.14, with 14 missing satisfaction records.
  - Reported values: resolution_median=65.0, resolution_std=51.302729053162466, satisfaction_mean=4.140776699029126, satisfaction_missing_count=14.0
- [q7] Tickets are handled by 18 unique agents. The most active agent handled 16 tickets, accounting for 7.27% of the total volume.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=16.0, top_agent_ticket_share_pct=7.2727272727272725

## Limitations
- The cleaning and analysis stages reported validation failures, suggesting potential data quality issues in the source exports.
- Satisfaction scores were missing for 14 tickets, which may bias the calculated mean satisfaction score.
- The analysis assumes labor cost is directly aggregable and does not account for hourly rate variations per agent.

## Conclusion
The support operations data highlights significant efficiency variances, particularly the high reopening rate for email tickets compared to chat. While agent workload appears balanced, the identified high-cost, low-satisfaction segment warrants further investigation to reduce operational risk. Addressing the specific drivers of email reopenings could yield substantial quality improvements.
