# Support Operations Analysis Report

Analysis of 347 support tickets reveals a total labor cost of $27,492. While the average satisfaction score is strong at 4.15, email tickets show a significantly higher reopen rate compared to chat. A specific segment of 12 high-cost, low-satisfaction tickets warrants attention. Ticket resolution times vary by channel, and the workload is distributed among 18 agents with moderate concentration.

## Key findings
- [q1] The dataset contains 347 tickets with a mean resolution time of 75.19 minutes and a total labor cost of $27,422.90.
  - Reported values: ticket_count=347.0, mean_resolution_minutes=75.19308357348703, total_labor_cost=27422.9
- [q2] Team Beta incurred the highest total labor cost at $10,247.36, followed by Team Gamma ($9,387.73) and Team Alpha ($7,787.81).
  - Reported values: labor_cost_alpha=7787.81, labor_cost_beta=10247.36, labor_cost_gamma=9387.73
  - Ranking: Beta, Gamma, Alpha
- [q3] Chat channels had the longest mean resolution time at 83.04 minutes, followed by email (73.02 minutes) and phone (69.25 minutes).
  - Reported values: resolution_chat=83.03921568627452, resolution_email=73.01724137931035, resolution_phone=69.25352112676056
  - Ranking: chat, email, phone
- [q4] The email reopen rate is 17.24%, which is 119.83% higher than the chat reopen rate of 7.84%.
  - Reported values: reopen_rate_email_pct=17.24137931034483, reopen_rate_chat_pct=7.8431372549019605, email_vs_chat_reopen_change_pct=119.82758620689657
  - Direction: increase
- [q5] There are 12 tickets in the high-cost, low-satisfaction segment, with a reopen rate of 8.33%.
  - Reported values: high_cost_low_sat_count=12.0, high_cost_low_sat_reopen_pct=8.333333333333332
- [q6] The median resolution time is 65.0 minutes with a standard deviation of 51.93 minutes. The mean satisfaction score is 4.15, though 19 tickets are missing satisfaction data.
  - Reported values: resolution_median=65.0, resolution_std=51.92574910613114, satisfaction_mean=4.152439024390244, satisfaction_missing_count=19.0
- [q7] Tickets are handled by 18 unique agents. The most active agent handled 26 tickets, representing 7.49% of the total volume.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=26.0, top_agent_ticket_share_pct=7.492795389048991

## Limitations
- Satisfaction scores were missing for 19 tickets, which may bias the satisfaction mean calculation.
- The analysis assumes the accuracy of the cleaned data; anomalies in the export (e.g., duplicate tickets) could affect cost and volume metrics.
- Labor cost calculations depend on the provided agent roster and may not reflect real-time salary fluctuations.

## Conclusion
The support operations data highlights a critical efficiency gap in email handling, where reopen rates significantly exceed those of chat. While agent workload distribution appears balanced, the presence of high-cost, low-satisfaction tickets suggests a need for targeted process improvements. Addressing the email reopen loop and investigating the 12 identified problematic tickets should be prioritized to reduce costs and improve customer experience.
