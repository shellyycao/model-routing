# Support Operations Cost and Performance Analysis Report

This report analyzes 347 support tickets to evaluate cost, speed, reopening rates, and agent concentration. The total labor cost was $27,422.90. Key findings indicate that email tickets have a significantly higher reopening rate than chat (119.8% higher), and the Beta team incurred the highest labor costs. A segment of 12 high-cost, low-satisfaction tickets was identified for review.

## Key findings
- [q1] The dataset contains 347 tickets with a mean resolution time of 75.2 minutes and a total labor cost of $27,422.90.
  - Reported values: ticket_count=347.0, mean_resolution_minutes=75.19308357348703, total_labor_cost=27422.9
- [q2] Team Beta had the highest total labor cost at $10,247.36, followed by Gamma ($9,387.73) and Alpha ($7,787.81).
  - Reported values: labor_cost_alpha=7787.81, labor_cost_beta=10247.36, labor_cost_gamma=9387.73
  - Ranking: Beta, Gamma, Alpha
- [q3] Resolution times varied by channel: chat was slowest at 83.0 minutes, email averaged 73.0 minutes, and phone was fastest at 69.3 minutes.
  - Reported values: resolution_email=73.01724137931035, resolution_chat=83.03921568627452, resolution_phone=69.25352112676056
  - Ranking: chat, email, phone
- [q4] The email reopening rate was 17.2% compared to 7.8% for chat, representing a 119.8% increase relative to the chat baseline.
  - Reported values: reopen_rate_email_pct=17.24137931034483, reopen_rate_chat_pct=7.8431372549019605, email_vs_chat_reopen_change_pct=119.82758620689657
  - Direction: increase
  - Derived pct_change(reopen_rate_email_pct, reopen_rate_chat_pct): 119.82758620689657
- [q5] There were 12 tickets identified as high-cost and low-satisfaction, with a reopening rate of 8.3%.
  - Reported values: high_cost_low_sat_count=12.0, high_cost_low_sat_reopen_pct=8.333333333333332
- [q6] Resolution times had a median of 65.0 minutes and a standard deviation of 51.9 minutes. The average satisfaction score was 4.15, with 19 tickets missing a score.
  - Reported values: resolution_median=65.0, resolution_std=51.92574910613114, satisfaction_mean=4.152439024390244, satisfaction_missing_count=19.0
- [q7] The team consists of 18 unique agents. The most active agent handled 26 tickets, accounting for 7.5% of the total volume.
  - Reported values: unique_agent_ticket_count=18.0, top_agent_ticket_count=26.0, top_agent_ticket_share_pct=7.492795389048991

## Limitations
- Satisfaction scores were missing for 19 tickets (5.5% of the dataset), which may bias the satisfaction mean.
- The analysis assumes the 'cleaned.csv' input accurately represents the operational period; data collection errors in the source system are not accounted for.
- Labor cost calculations depend on the accuracy of the cost attribution logic applied during the cleaning stage.

## Conclusion
The analysis highlights a significant disparity in reopening rates between email and chat channels, suggesting process improvements are needed for email ticket handling. While agent concentration is relatively low, the identification of 12 high-cost, low-satisfaction tickets provides a specific target for quality review to improve efficiency and customer experience.
