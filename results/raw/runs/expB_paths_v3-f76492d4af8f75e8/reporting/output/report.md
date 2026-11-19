# Support Operations Analysis Report

Analysis of 347 support tickets reveals a total labor cost of $27,422.90 and a mean resolution time of 75.2 minutes. Team Beta carries the highest labor spend, phone is the fastest channel, and email tickets reopen at roughly twice the rate of chat tickets. A small high-cost, low-satisfaction segment (12 tickets) warrants targeted intervention. Agent workload is moderately concentrated, with the busiest agent handling 7.5% of all tickets.

## Key findings
- [q1] The dataset contains 347 tickets with a mean resolution time of 75.2 minutes and a total labor cost of $27,422.90.
  - Reported values: ticket_count=347.0, mean_resolution_minutes=75.19308357348703, total_labor_cost=27422.9
- [q2] Team Beta incurred the highest labor cost at $10,247.36, followed by Gamma at $9,387.73 and Alpha at $7,787.81. Beta's spend exceeds Alpha's by $2,459.55.
  - Reported values: labor_cost_alpha=7787.81, labor_cost_beta=10247.36, labor_cost_gamma=9387.73
  - Ranking: Beta, Gamma, Alpha
  - Derived difference(labor_cost_beta, labor_cost_alpha): 2459.55
- [q3] Phone is the fastest channel at 69.3 minutes mean resolution, followed by email at 73.0 minutes and chat at 83.0 minutes.
  - Reported values: resolution_email=73.01724137931035, resolution_chat=83.03921568627452, resolution_phone=69.25352112676056
  - Ranking: chat, email, phone
- [q4] Email tickets reopen at 17.2% versus 7.8% for chat, representing an increase of approximately 119.8% relative to the chat reopen rate.
  - Reported values: reopen_rate_email_pct=17.24137931034483, reopen_rate_chat_pct=7.8431372549019605, email_vs_chat_reopen_change_pct=119.82758620689657
  - Direction: increase
  - Derived pct_change(reopen_rate_email_pct, reopen_rate_chat_pct): 119.83
- [q5] Twelve tickets meet the high-cost (labor_cost ≥ $100) and low-satisfaction (score ≤ 2) criteria, with a reopen rate of 8.3% — a segment that merits priority review.
  - Reported values: high_cost_low_sat_count=12.0, high_cost_low_sat_reopen_pct=8.333333333333332
- [q6] Resolution time has a median of 65.0 minutes and a standard deviation of 51.9 minutes, indicating a right-skewed distribution. Mean satisfaction (where recorded) is 4.15 out of 5, with 19 tickets missing a satisfaction score.
  - Reported values: resolution_median=65.0, resolution_std=51.92574910613114, satisfaction_mean=4.152439024390244, satisfaction_missing_count=19.0
- [q7] Eighteen distinct agents handled the 347 tickets. The busiest single agent resolved 26 tickets, representing 7.5% of total volume — a moderate but notable concentration.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=26.0, top_agent_ticket_share_pct=7.492795389048991
  - Derived share(top_agent_ticket_count, ticket_count): 7.49

## Limitations
- Nineteen tickets (5.5%) are missing satisfaction scores, which may introduce bias into the satisfaction mean and the high-cost low-satisfaction segment count.
- Labor cost is derived from the export and may not capture indirect costs such as escalation overhead or managerial review time.
- The dataset represents a single export snapshot; seasonal or trend effects cannot be assessed without time-series data.
- Agent identity is based on agent_id from the roster join; any mismatches or unmatched records during cleaning could affect agent concentration metrics.
- Reopen rates are based on a binary reopened flag and do not capture multiple reopenings or partial resolutions.

## Conclusion
Support operations are broadly healthy, with a mean satisfaction of 4.15 and a median resolution of 65 minutes. However, three areas warrant action: (1) Team Beta's labor cost is 31.6% above Alpha's and should be reviewed for efficiency; (2) email's reopen rate is ~120% higher than chat's, suggesting process or quality gaps in email handling; and (3) the 12 high-cost, low-satisfaction tickets represent a concentrated risk that should be audited individually.
