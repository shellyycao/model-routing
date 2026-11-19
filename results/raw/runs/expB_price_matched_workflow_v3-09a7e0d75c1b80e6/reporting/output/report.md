# Support Operations Cost and Performance Analysis

This report analyzes 347 support tickets with a total labor cost of $27,422.90. While the average satisfaction score is strong at 4.15, significant inefficiencies exist. Email tickets take longer to resolve and have a substantially higher reopening rate compared to chat. Additionally, a segment of 12 high-cost, low-satisfaction tickets indicates specific quality concerns, and workload concentration is moderate with the top agent handling 7.5% of all tickets.

## Key findings
- [q1] The dataset contains 347 tickets with a mean resolution time of 75.19 minutes and a total labor cost of $27,422.90.
  - Reported values: ticket_count=347.0, mean_resolution_minutes=75.19, total_labor_cost=27422.9
- [q2] Team Beta incurred the highest labor cost at $10,247.36, followed by Gamma at $9,387.73 and Alpha at $7,787.81.
  - Reported values: labor_cost_alpha=7787.81, labor_cost_beta=10247.36, labor_cost_gamma=9387.73
  - Ranking: Beta, Gamma, Alpha
- [q3] Resolution times vary by channel: chat is slowest at 83.04 minutes, email averages 73.02 minutes, and phone is fastest at 69.25 minutes.
  - Reported values: resolution_email=73.02, resolution_chat=83.04, resolution_phone=69.25
  - Ranking: chat, email, phone
- [q4] The email reopen rate is 17.24%, which is 119.83% higher than the chat reopen rate of 7.84%.
  - Reported values: reopen_rate_email_pct=17.24, reopen_rate_chat_pct=7.84, email_vs_chat_reopen_change_pct=119.83
  - Direction: increase
- [q5] There are 12 tickets in the high-cost, low-satisfaction segment (cost ≥$100, satisfaction ≤2), with a reopen rate of 8.33%.
  - Reported values: high_cost_low_sat_count=12.0, high_cost_low_sat_reopen_pct=8.33
- [q6] Resolution times have a median of 65.0 minutes and a standard deviation of 51.93 minutes. The mean satisfaction score is 4.15, though 19 tickets are missing this score.
  - Reported values: resolution_median=65.0, resolution_std=51.93, satisfaction_mean=4.15, satisfaction_missing_count=19.0
- [q7] The support team consists of 18 unique agents. The busiest agent handled 26 tickets, representing 7.49% of the total workload.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=26.0, top_agent_ticket_share_pct=7.49

## Limitations
- Satisfaction scores are missing for 19 tickets, potentially biasing the mean satisfaction score.
- The analysis assumes the labor cost calculation provided in the cleaned dataset is accurate and consistent.
- Historical trends are not available; findings represent a static snapshot of the exported data.

## Conclusion
Support operations show a clear disparity in efficiency between channels, with email tickets being significantly more prone to reopening than chat. While overall satisfaction is high, the high-cost, low-satisfaction segment requires targeted intervention. Workload distribution appears balanced, but monitoring the root causes of email reopen rates could yield significant quality improvements.
