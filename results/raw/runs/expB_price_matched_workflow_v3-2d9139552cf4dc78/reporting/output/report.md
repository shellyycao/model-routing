# Support Operations Analysis Report

This report analyzes 347 support tickets to evaluate cost, speed, reopening rates, satisfaction, and agent concentration. The total labor cost was $27,422.90. Key findings indicate that the Beta team incurred the highest costs, chat resolution times were the slowest, and email tickets had a significantly higher reopening rate than chat tickets. A small segment of high-cost, low-satisfaction tickets was identified, and agent workload concentration appears moderate.

## Key findings
- [q1] The dataset contains 347 tickets with a mean resolution time of 75.2 minutes and a total labor cost of $27,422.90.
  - Reported values: ticket_count=347.0, mean_resolution_minutes=75.19308357348703, total_labor_cost=27422.9
- [q2] Team labor costs ranked as follows: Beta ($10,247.36), Gamma ($9,387.73), Alpha ($7,787.81).
  - Reported values: labor_cost_alpha=7787.81, labor_cost_beta=10247.36, labor_cost_gamma=9387.730000000001
  - Ranking: Beta, Gamma, Alpha
- [q3] Mean resolution times by channel ranked as follows: chat (83.0 minutes), email (73.0 minutes), phone (69.3 minutes).
  - Reported values: resolution_email=73.01724137931035, resolution_chat=83.03921568627452, resolution_phone=69.25352112676056
  - Ranking: chat, email, phone
- [q4] The email reopening rate (17.2%) was 119.8% higher than the chat reopening rate (7.8%), indicating a significant increase in reopenings for email compared to chat.
  - Reported values: reopen_rate_email_pct=17.24137931034483, reopen_rate_chat_pct=7.8431372549019605, email_vs_chat_reopen_change_pct=119.82758620689657
  - Direction: increase
- [q5] There were 12 tickets identified as high-cost and low-satisfaction, representing a critical segment with an 8.3% reopening rate.
  - Reported values: high_cost_low_sat_count=12.0, high_cost_low_sat_reopen_pct=8.333333333333332
- [q6] Resolution times had a median of 65.0 minutes and a standard deviation of 51.9 minutes. The average satisfaction score was 4.15, with 19 tickets missing satisfaction data.
  - Reported values: resolution_median=65.0, resolution_std=51.92574910613114, satisfaction_mean=4.152439024390244, satisfaction_missing_count=19.0
- [q7] The support team consists of 18 unique agents. The top agent handled 26 tickets, accounting for 7.5% of the total workload.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=26.0, top_agent_ticket_share_pct=7.492795389048991

## Limitations
- Satisfaction scores were missing for 19 tickets, which may bias the satisfaction mean.
- The analysis assumes the 'cleaned.csv' data is accurate and representative of current operations.
- The 'high-cost low-satisfaction' segment is small (12 tickets), so conclusions there should be drawn cautiously.

## Conclusion
The analysis highlights significant variations in cost and performance across teams and channels. The high reopening rate for email tickets compared to chat suggests a potential area for process improvement. While agent workload is not heavily concentrated, monitoring the high-cost, low-satisfaction segment could prevent value leakage.
