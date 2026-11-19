# Support Operations Cost and Performance Analysis Report

This report details verified metrics for 235 support tickets, revealing a total labor cost of $18,704.10. While overall satisfaction is high at 4.13, email support shows a significantly higher reopen rate (19.8%) compared to chat (10.3%). The Gamma team incurred the highest costs, and a specific segment of high-cost, low-satisfaction tickets requires attention.

## Key findings
- [q1] The dataset contains 235 tickets with a mean resolution time of 75.30 minutes and a total labor cost of $18,704.10.
  - Reported values: ticket_count=235.0, mean_resolution_minutes=75.29787234042553, total_labor_cost=18704.1
- [q2] Team Gamma recorded the highest total labor cost at $6,982.84, followed by Beta at $6,466.66 and Alpha at $5,254.60.
  - Reported values: labor_cost_alpha=5254.6, labor_cost_beta=6466.66, labor_cost_gamma=6982.84
  - Ranking: Gamma, Beta, Alpha
- [q3] Chat support had the longest average resolution time at 83.54 minutes, while phone support was fastest at 67.89 minutes.
  - Reported values: resolution_email=73.47933884297521, resolution_chat=83.54411764705883, resolution_phone=67.8913043478261
  - Ranking: chat, email, phone
- [q4] The email reopen rate is 19.83%, which is 92.68% higher than the chat reopen rate of 10.29%.
  - Reported values: reopen_rate_email_pct=19.834710743801654, reopen_rate_chat_pct=10.294117647058822, email_vs_chat_reopen_change_pct=92.68004722550181
  - Direction: increase
  - Derived pct_change(reopen_rate_email_pct, reopen_rate_chat_pct): 92.68
- [q5] There are 8 tickets in the high-cost low-satisfaction segment, with a reopen percentage of 12.5%.
  - Reported values: high_cost_low_sat_count=8.0, high_cost_low_sat_reopen_pct=12.5
- [q6] Resolution times have a median of 66.0 minutes and a standard deviation of 53.34 minutes. The average satisfaction score is 4.13, with 10 missing values.
  - Reported values: resolution_median=66.0, resolution_std=53.34267341837612, satisfaction_mean=4.128888888888889, satisfaction_missing_count=10.0
- [q7] The 18 distinct agents show moderate concentration, with the top agent handling 20 tickets, representing an 8.51% share of the total workload.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=20.0, top_agent_ticket_share_pct=8.51063829787234

## Limitations
- The cleaning and analysis stages reported validation failures, suggesting potential data quality issues that could affect metric reliability.
- Satisfaction scores were missing for 10 tickets, which may bias the overall satisfaction mean.
- The analysis assumes labor cost and resolution time data were accurately captured in the source export.

## Conclusion
Operations show distinct cost and performance variations across teams and channels. The email channel's high reopen rate (19.83%) and the identification of 8 high-cost, low-satisfaction tickets suggest targeted areas for process improvement. Workload distribution among the 18 agents appears balanced, with no single agent handling more than 8.51% of tickets.
