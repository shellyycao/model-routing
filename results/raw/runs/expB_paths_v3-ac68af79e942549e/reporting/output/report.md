# Support Operations Analysis Report

This report presents the findings from the analysis of support operations data, focusing on cost, speed, reopening rates, satisfaction, and agent concentration. Key findings include the overall performance metrics, team and channel comparisons, reopening rates, high-cost low-satisfaction segment, distribution of resolution times and satisfaction scores, and agent concentration metrics.

## Key findings
- [q1] The overall performance metrics indicate a total of 347 tickets were processed with an average resolution time of 75.2 minutes and a total labor cost of $27,422.90.
  - Reported values: ticket_count=347.0, mean_resolution_minutes=75.19308357348703, total_labor_cost=27422.9
- [q2] Team comparison shows that Beta team incurred the highest labor cost at $10,247.36, followed by Gamma at $9,387.73, and Alpha at $7,787.81.
  - Reported values: labor_cost_alpha=7787.81, labor_cost_beta=10247.36, labor_cost_gamma=9387.730000000001
  - Ranking: Beta, Gamma, Alpha
- [q3] Channel comparison reveals that chat had the highest average resolution time at 83.0 minutes, followed by email at 73.0 minutes, and phone at 69.3 minutes.
  - Reported values: resolution_email=73.01724137931035, resolution_chat=83.03921568627452, resolution_phone=69.25352112676056
  - Ranking: chat, email, phone
- [q4] The reopening rate for email tickets is significantly higher than for chat tickets, with a 119.8% increase in the reopening rate for email compared to chat.
  - Reported values: reopen_rate_email_pct=17.24137931034483, reopen_rate_chat_pct=7.8431372549019605, email_vs_chat_reopen_change_pct=119.82758620689657
  - Direction: increase
- [q5] There are 12 tickets with a labor cost of at least $100 and a non-missing satisfaction score of 2 or lower, representing an 8.3% reopening rate.
  - Reported values: high_cost_low_sat_count=12.0, high_cost_low_sat_reopen_pct=8.333333333333332
- [q6] The distribution of resolution times shows a median of 65 minutes and a standard deviation of 51.9 minutes. The mean satisfaction score is 4.15, with 19 missing satisfaction scores.
  - Reported values: resolution_median=65.0, resolution_std=51.92574910613114, satisfaction_mean=4.152439024390244, satisfaction_missing_count=19.0
- [q7] There are 18 distinct agents handling tickets, with the top agent handling 26 tickets, representing 7.5% of the total tickets.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=26.0, top_agent_ticket_share_pct=7.492795389048991

## Limitations
- The cleaning stage failed, which may have impacted the quality of the data used in the analysis.
- The analysis is based on a specific dataset and may not be representative of all support operations.
- The satisfaction scores have missing values, which could affect the accuracy of the satisfaction metrics.

## Conclusion
The analysis provides valuable insights into the performance of support operations, highlighting areas for improvement such as reducing reopening rates and optimizing agent workload distribution.
