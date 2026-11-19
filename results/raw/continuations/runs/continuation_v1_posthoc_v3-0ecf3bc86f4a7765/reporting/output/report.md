# Support Operations Analysis Report

Analysis of 347 support tickets reveals a total labor cost of $27,422.90 and a mean resolution time of 75.2 minutes. Team Beta carries the highest labor cost share. Phone is the fastest resolution channel. Email tickets reopen at more than twice the rate of chat tickets, and a small high-cost, low-satisfaction segment warrants targeted intervention. Agent workload is moderately concentrated, with the busiest agent handling 7.5% of all tickets.

## Key findings
- [q1] The dataset contains 347 tickets with a mean resolution time of 75.2 minutes and a total labor cost of $27,422.90.
  - Reported values: ticket_count=347.0, mean_resolution_minutes=75.19308357348703, total_labor_cost=27422.9
- [q2] Team Beta incurred the highest labor cost at $10,247.36, followed by Gamma at $9,387.73 and Alpha at $7,787.81.
  - Reported values: labor_cost_alpha=7787.81, labor_cost_beta=10247.36, labor_cost_gamma=9387.73
  - Ranking: Beta, Gamma, Alpha
- [q3] Phone is the fastest channel at a mean of 69.3 minutes, followed by email at 73.0 minutes; chat is the slowest at 83.0 minutes.
  - Reported values: resolution_email=73.01724137931035, resolution_chat=83.03921568627452, resolution_phone=69.25352112676056
  - Ranking: chat, email, phone
- [q4] Email tickets reopen at 17.2% versus 7.8% for chat, representing a 119.8% relative increase in reopen rate for email over chat.
  - Reported values: reopen_rate_email_pct=17.24137931034483, reopen_rate_chat_pct=7.8431372549019605, email_vs_chat_reopen_change_pct=119.82758620689657
  - Direction: increase
  - Derived pct_change(reopen_rate_email_pct, reopen_rate_chat_pct): 119.82758620689657
- [q5] 12 tickets meet the high-cost (≥$100), low-satisfaction (≤2) criteria, of which 8.3% were reopened, flagging a small but at-risk segment.
  - Reported values: high_cost_low_sat_count=12.0, high_cost_low_sat_reopen_pct=8.333333333333332
- [q6] Resolution time has a median of 65.0 minutes and a standard deviation of 51.9 minutes, indicating a right-skewed distribution. Mean satisfaction is 4.15 out of 5, though 19 tickets have missing satisfaction scores.
  - Reported values: resolution_median=65.0, resolution_std=51.92574910613114, satisfaction_mean=4.152439024390244, satisfaction_missing_count=19.0
- [q7] 18 distinct agents handled tickets. The busiest single agent handled 26 tickets, representing 7.5% of all tickets, indicating moderate but not extreme concentration.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=26.0, top_agent_ticket_share_pct=7.492795389048991
  - Derived share(top_agent_ticket_count, ticket_count): 7.492795389048991

## Limitations
- 19 tickets have missing satisfaction scores, which may introduce bias into the satisfaction mean if missingness is non-random.
- Labor cost figures reflect the cleaned export only; any tickets excluded during cleaning are not represented in totals.
- Channel and team groupings are based on the agent roster join; unmatched agents could distort team-level cost comparisons.
- Reopening rates are computed from the available snapshot and do not account for tickets that may reopen after the export date.
- The analysis covers a single export period; trends over time cannot be inferred from this cross-sectional dataset.

## Conclusion
Support operations are broadly healthy, with a mean satisfaction of 4.15 and a median resolution time of 65 minutes. However, Team Beta's disproportionate labor cost, email's elevated reopen rate (120% higher than chat), and the 12 high-cost low-satisfaction tickets each represent actionable improvement areas. Addressing email-channel quality and reviewing Beta's workload distribution should be prioritized in the next operational cycle.
