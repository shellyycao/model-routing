# Support Operations Analysis Report

Analysis of 220 support tickets reveals a total labor cost of $17,445.07 and a mean resolution time of 75.7 minutes. Team Beta carries the highest labor cost share. Chat resolves fastest while email tickets reopen at a rate more than twice that of chat. A small high-cost, low-satisfaction segment warrants targeted intervention. Agent workload is moderately concentrated across 18 agents.

## Key findings
- [q1] The dataset contains 220 tickets with a mean resolution time of 75.7 minutes and a total labor cost of $17,445.07.
  - Reported values: ticket_count=220.0, mean_resolution_minutes=75.6590909090909, total_labor_cost=17445.07
- [q2] Team Beta incurred the highest labor cost at $6,928.72, followed by Gamma at $5,911.44 and Alpha at $4,604.91.
  - Reported values: labor_cost_alpha=4604.91, labor_cost_beta=6928.720000000001, labor_cost_gamma=5911.439999999999
  - Ranking: Beta, Gamma, Alpha
- [q3] Chat had the longest mean resolution time at 82.2 minutes, followed by phone at 74.1 minutes and email at 71.7 minutes.
  - Reported values: resolution_email=71.72380952380952, resolution_chat=82.23287671232876, resolution_phone=74.07142857142857
  - Ranking: chat, phone, email
- [q4] Email tickets reopen at 15.2% versus 6.8% for chat, representing a 122.5% relative increase in reopen rate for email over chat — indicating email is a materially higher-risk channel for reopening.
  - Reported values: reopen_rate_email_pct=15.238095238095239, reopen_rate_chat_pct=6.8493150684931505, email_vs_chat_reopen_change_pct=122.47619047619051
  - Direction: increase
  - Derived pct_change(reopen_rate_email_pct, reopen_rate_chat_pct): 122.47619047619051
- [q5] Nine tickets meet the high-cost (labor_cost ≥ $100) and low-satisfaction (score ≤ 2) criteria, with 11.1% of them having been reopened — a segment requiring priority review.
  - Reported values: high_cost_low_sat_count=9.0, high_cost_low_sat_reopen_pct=11.11111111111111
- [q6] Resolution time has a median of 65.0 minutes and a standard deviation of 51.3 minutes, indicating notable spread. Mean satisfaction (where recorded) is 4.14 out of 5, with 14 tickets missing a satisfaction score.
  - Reported values: resolution_median=65.0, resolution_std=51.302729053162466, satisfaction_mean=4.140776699029126, satisfaction_missing_count=14.0
- [q7] Tickets are handled by 18 distinct agents. The busiest single agent handled 16 tickets, representing 7.3% of total volume — suggesting workload is reasonably distributed with no extreme concentration.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=16.0, top_agent_ticket_share_pct=7.2727272727272725
  - Derived share(top_agent_ticket_count, ticket_count): 7.2727272727272725

## Limitations
- Both the cleaning and analysis pipeline stages reported validation failures; results should be treated as provisional until the underlying data quality issues are investigated and resolved.
- Fourteen tickets are missing satisfaction scores, which may introduce bias into the satisfaction mean if missingness is non-random (e.g., correlated with poor outcomes).
- The high-cost low-satisfaction segment contains only 9 tickets, making the 11.1% reopen rate statistically fragile and unsuitable for firm conclusions without additional data.
- Agent concentration metrics identify only the top agent's share; the full distribution of workload across all 18 agents is not captured in the verified findings.
- No time-series or trend data is available, so it is not possible to determine whether any of these metrics are improving or deteriorating over time.

## Conclusion
Support operations show acceptable overall satisfaction (mean 4.14) and moderate resolution times, but email's reopen rate is 122% higher than chat's, signalling a process gap. Team Beta accounts for the largest labor cost share. The high-cost, low-satisfaction segment is small but warrants targeted follow-up. Data pipeline failures in both prior stages mean all figures should be validated before driving operational decisions.
