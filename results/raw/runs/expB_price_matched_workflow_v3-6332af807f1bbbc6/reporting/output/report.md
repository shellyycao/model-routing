# Support Operations Analysis Report

This report details verified findings on 347 support tickets, revealing a total labor cost of $27,742.90 and an average resolution time of 75.2 minutes. Key insights include a significant disparity in reopen rates between email and chat channels (email is 119.8% higher), and the identification of 12 high-cost, low-satisfaction tickets. The workload is distributed among 18 agents, with the top agent handling 7.5% of all tickets.

## Key findings
- [q1] The dataset contains 347 tickets. The average resolution time is 75.2 minutes, and the total labor cost amounts to $27,422.90.
  - Reported values: ticket_count=347.0, mean_resolution_minutes=75.19308357348703, total_labor_cost=27422.9
- [q2] Team Beta incurred the highest labor cost at $10,247.36, followed by Gamma at $9,387.73 and Alpha at $7,787.81.
  - Reported values: labor_cost_alpha=7787.81, labor_cost_beta=10247.36, labor_cost_gamma=9387.73
  - Ranking: Beta, Gamma, Alpha
- [q3] Chat channels have the longest average resolution time at 83.0 minutes, while phone is fastest at 69.3 minutes. Email averages 73.0 minutes.
  - Reported values: resolution_email=73.01724137931035, resolution_chat=83.03921568627452, resolution_phone=69.25352112676056
  - Ranking: chat, email, phone
- [q4] Email tickets have a reopen rate of 17.2%, compared to 7.8% for chat. This represents a 119.8% increase in the reopen rate for email relative to chat.
  - Reported values: reopen_rate_email_pct=17.24137931034483, reopen_rate_chat_pct=7.8431372549019605, email_vs_chat_reopen_change_pct=119.82758620689657
  - Direction: increase
- [q5] There are 12 tickets in the high-cost, low-satisfaction segment (labor cost >= $100 and satisfaction <= 2). This segment has a reopen rate of 8.3%.
  - Reported values: high_cost_low_sat_count=12.0, high_cost_low_sat_reopen_pct=8.333333333333332
- [q6] The median resolution time is 65.0 minutes with a standard deviation of 51.9 minutes. Average satisfaction is 4.15, with 19 tickets missing a satisfaction score.
  - Reported values: resolution_median=65.0, resolution_std=51.92574910613114, satisfaction_mean=4.152439024390244, satisfaction_missing_count=19.0
- [q7] Tickets are handled by 18 unique agents. The most active agent handled 26 tickets, accounting for 7.5% of the total workload.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=26.0, top_agent_ticket_share_pct=7.492795389048991

## Limitations
- Satisfaction scores were missing for 19 tickets, potentially biasing the average satisfaction metric.
- The analysis assumes the 'cleaned.csv' export accurately represents the full support ticket history.
- Reopen rate comparison was limited to email and chat channels as specified in the analysis scope.

## Conclusion
The analysis highlights significant inefficiencies in email support, which shows a markedly higher reopen rate than chat. While phone support is the fastest channel, chat resolution times lag, suggesting potential process bottlenecks. The concentration of tickets among agents appears balanced, though attention should be paid to the specific high-cost, low-satisfaction tickets to prevent churn.
