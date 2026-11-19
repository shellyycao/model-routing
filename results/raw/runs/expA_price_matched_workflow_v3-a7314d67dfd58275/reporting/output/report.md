# Support Operations Cost and Performance Analysis

Analysis of 347 support tickets reveals a total labor cost of $27,742.84 with an average resolution time of 75.2 minutes. Team Beta incurred the highest costs, while phone support was the fastest channel. A significant finding indicates email tickets are reopened 119.8% more often than chat tickets. Additionally, 12 tickets were identified as high-cost with low satisfaction, and ticket handling is well-distributed among 18 agents.

## Key findings
- [q1] The dataset comprises 347 tickets with a mean resolution time of 75.19 minutes and a total labor cost of $27,422.84.
  - Reported values: ticket_count=347.0, mean_resolution_minutes=75.193084, total_labor_cost=27422.84
- [q2] Team Beta had the highest labor cost at $10,247.32, followed by Gamma ($9,387.74) and Alpha ($7,787.78).
  - Reported values: labor_cost_alpha=7787.78, labor_cost_beta=10247.32, labor_cost_gamma=9387.74
  - Ranking: Beta, Gamma, Alpha
- [q3] Resolution times varied by channel: chat was slowest (83.04 minutes), followed by email (73.02 minutes) and phone (69.25 minutes).
  - Reported values: resolution_email=73.017241, resolution_chat=83.039216, resolution_phone=69.253521
  - Ranking: chat, email, phone
- [q4] The email reopening rate was 17.24%, representing a 119.83% increase over the chat reopening rate of 7.84%.
  - Reported values: reopen_rate_email_pct=17.241379, reopen_rate_chat_pct=7.843137, email_vs_chat_reopen_change_pct=119.827586
  - Direction: increase
- [q5] There were 12 tickets identified as high-cost and low-satisfaction, with an 8.33% reopening percentage.
  - Reported values: high_cost_low_sat_count=12.0, high_cost_low_sat_reopen_pct=8.333333
- [q6] Resolution times had a median of 65.0 minutes and a standard deviation of 51.93 minutes. The mean satisfaction score was 4.15, with 19 missing satisfaction entries.
  - Reported values: resolution_median=65.0, resolution_std=51.925749, satisfaction_mean=4.152439, satisfaction_missing_count=19.0
- [q7] Tickets were handled by 18 unique agents. The top agent handled 26 tickets, accounting for 7.49% of the total volume.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=26.0, top_agent_ticket_share_pct=7.492795

## Limitations
- Satisfaction scores were missing for 19 tickets, potentially biasing the satisfaction mean.
- Labor cost calculations rely on the provided agent roster rates and may not capture overhead costs.
- The analysis assumes the 'resolution_minutes' field accurately reflects active work time.

## Conclusion
While overall ticket distribution is healthy, the high reopening rate for email tickets suggests a need for process review in that channel. The high-cost, low-satisfaction segment, though small, warrants investigation to prevent resource drain and customer churn.
