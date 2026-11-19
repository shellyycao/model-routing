# Support Operations Analysis Report

Analysis of 235 support tickets reveals a total labor cost of $18,704 and a mean resolution time of ~75 minutes. Team Gamma carries the highest labor cost, phone channel resolves fastest, and email tickets reopen at nearly twice the rate of chat. A small high-cost, low-satisfaction segment warrants targeted intervention, and one agent handles 8.5% of all tickets, indicating moderate concentration risk.

## Key findings
- [q1] The dataset contains 235 tickets with a mean resolution time of 75.3 minutes and a total labor cost of $18,704.10.
  - Reported values: ticket_count=235.0, mean_resolution_minutes=75.29787234042553, total_labor_cost=18704.1
- [q2] Team Gamma incurred the highest labor cost at $6,982.84, followed by Beta at $6,466.66 and Alpha at $5,254.60. Gamma's cost exceeds Alpha's by $1,728.24.
  - Reported values: labor_cost_alpha=5254.599999999999, labor_cost_beta=6466.66, labor_cost_gamma=6982.839999999998
  - Ranking: Gamma, Beta, Alpha
  - Derived difference(labor_cost_gamma, labor_cost_alpha): 1728.24
- [q3] Phone is the fastest channel at 67.9 minutes mean resolution, followed by email at 73.5 minutes and chat at 83.5 minutes.
  - Reported values: resolution_email=73.47933884297521, resolution_chat=83.54411764705883, resolution_phone=67.8913043478261
  - Ranking: chat, email, phone
- [q4] Email tickets reopen at 19.8% versus 10.3% for chat, representing a 92.7% relative increase in reopen rate for email over chat.
  - Reported values: reopen_rate_email_pct=19.834710743801654, reopen_rate_chat_pct=10.294117647058822, email_vs_chat_reopen_change_pct=92.68004722550181
  - Direction: increase
- [q5] 8 tickets meet the high-cost (labor ≥ $100) and low-satisfaction (score ≤ 2) criteria, and 12.5% of these were reopened, flagging a critical at-risk segment.
  - Reported values: high_cost_low_sat_count=8.0, high_cost_low_sat_reopen_pct=12.5
- [q6] Resolution time has a median of 66.0 minutes and a standard deviation of 53.3 minutes, indicating high variability. Mean satisfaction (where recorded) is 4.1 out of 5, with 10 tickets missing a satisfaction score.
  - Reported values: resolution_median=66.0, resolution_std=53.34267341837612, satisfaction_mean=4.128888888888889, satisfaction_missing_count=10.0
- [q7] 18 distinct agents handled tickets. The busiest single agent resolved 20 tickets, representing 8.5% of all tickets, suggesting moderate but notable workload concentration.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=20.0, top_agent_ticket_share_pct=8.51063829787234

## Limitations
- Both the cleaning and analysis pipeline stages reported validation failures; results should be treated as provisional until the underlying data quality issues are investigated and resolved.
- 10 tickets have missing satisfaction scores, which may bias the satisfaction mean if missingness is non-random.
- Labor cost calculations depend on the accuracy of the agent roster join; any unmatched tickets could distort team-level cost figures.
- The high-cost low-satisfaction segment contains only 8 tickets, making the 12.5% reopen rate statistically fragile.
- Channel and team assignments are taken as-is from the export; any miscategorisation in the source system would propagate into all channel and team comparisons.

## Conclusion
Support operations show acceptable average satisfaction (4.1/5) but meaningful inefficiencies: email tickets reopen at nearly twice the chat rate, chat resolution is the slowest channel, and Team Gamma drives the largest share of labor cost. The high-cost, low-satisfaction segment and the top-agent concentration (8.5% of tickets) are priority areas for operational review. Given pipeline validation failures, findings should be confirmed once data quality issues are remediated.
