# Support Operations Cost and Performance Analysis Report

This report analyzes 347 support tickets to evaluate cost, speed, reopening rates, satisfaction, and agent concentration. The total labor cost is $27,422.90. Email tickets show a significantly higher reopen rate than chat (17.2% vs 7.8%), representing a 119.8% increase. A small segment of 12 high-cost, low-satisfaction tickets was identified. Workload is distributed among 18 agents, with the top agent handling 7.5% of all tickets.

## Key findings
- [q1] The dataset contains 347 tickets with a mean resolution time of 75.2 minutes and a total labor cost of $27,422.90.
  - Reported values: ticket_count=347.0, mean_resolution_minutes=75.19308357348703, total_labor_cost=27422.9
- [q2] Team Beta incurred the highest labor cost at $10,247.36, followed by Gamma ($9,387.73) and Alpha ($7,787.81).
  - Reported values: labor_cost_alpha=7787.81, labor_cost_beta=10247.36, labor_cost_gamma=9387.730000000001
  - Ranking: Beta, Gamma, Alpha
- [q3] Resolution times vary by channel: chat is slowest (83.0 minutes), followed by email (73.0 minutes) and phone (69.3 minutes).
  - Reported values: resolution_chat=83.03921568627452, resolution_email=73.01724137931035, resolution_phone=69.25352112676056
  - Ranking: chat, email, phone
- [q4] The email reopen rate is 17.2%, which is 119.8% higher than the chat reopen rate of 7.8%.
  - Reported values: reopen_rate_email_pct=17.24137931034483, reopen_rate_chat_pct=7.8431372549019605, email_vs_chat_reopen_change_pct=119.82758620689657
  - Direction: increase
  - Derived pct_change(reopen_rate_email_pct, reopen_rate_chat_pct): 119.82758620689657
- [q5] There are 12 tickets classified as high-cost and low-satisfaction, with a reopen rate of 8.3%.
  - Reported values: high_cost_low_sat_count=12.0, high_cost_low_sat_reopen_pct=8.333333333333332
- [q6] Resolution times have a median of 65.0 minutes and a standard deviation of 51.9 minutes. The mean satisfaction score is 4.15, with 19 tickets missing a satisfaction rating.
  - Reported values: resolution_median=65.0, resolution_std=51.92574910613114, satisfaction_mean=4.152439024390244, satisfaction_missing_count=19.0
- [q7] The support team consists of 18 unique agents. The top agent handled 26 tickets, accounting for 7.5% of the total workload.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=26.0, top_agent_ticket_share_pct=7.492795389048991

## Limitations
- Satisfaction scores were missing for 19 tickets, potentially biasing the satisfaction mean and the high-cost low-satisfaction segment analysis.
- The analysis assumes the provided labor cost and resolution time data are accurate and consistently recorded across all channels and teams.
- Historical trends are not available in this dataset; findings represent a static snapshot of the current ticket export.

## Conclusion
The analysis reveals significant efficiency differences between channels, with chat having the longest resolution times and email having the highest reopen rate. Team Beta bears the highest labor cost. While agent workload distribution appears relatively balanced with no single agent dominating the volume, the high reopen rate for email tickets suggests a need for process review in that channel. Addressing the 12 high-cost, low-satisfaction tickets could improve overall customer experience and reduce waste.
