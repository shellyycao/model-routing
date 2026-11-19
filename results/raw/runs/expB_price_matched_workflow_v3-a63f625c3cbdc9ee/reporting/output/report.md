# Support Operations Report: Cost, Speed, Reopening and Satisfaction

Analysis of 347 cleaned support tickets joined to the agent roster shows total labor cost of $27,422.90 and a mean resolution time of 75.2 minutes. Team Beta carries the highest labor cost, chat is the slowest channel, and email tickets reopen at 17.24% — a 119.83% relative increase over chat's 7.84%. Only 12 tickets combine high cost with low satisfaction, and workload is spread across 18 agents with the busiest handling just 7.49% of volume.

## Key findings
- [q1] The export contains 347 tickets with a mean resolution time of 75.2 minutes and a total labor cost of $27,422.90, equivalent to roughly $79.03 per ticket.
  - Reported values: ticket_count=347.0, mean_resolution_minutes=75.19308357348703, total_labor_cost=27422.9
  - Direction: not_applicable
  - Derived ratio(total_labor_cost, ticket_count): 79.03
- [q2] Team Beta generated the highest total labor cost at $10,247.36, followed by Gamma at $9,387.73 and Alpha at $7,787.81; Beta's total exceeds Alpha's by $2,459.55.
  - Reported values: labor_cost_alpha=7787.81, labor_cost_beta=10247.36, labor_cost_gamma=9387.73
  - Direction: not_applicable
  - Ranking: Beta, Gamma, Alpha
  - Derived difference(labor_cost_beta, labor_cost_alpha): 2459.55
- [q3] Chat is the slowest channel with a mean resolution time of 83.0 minutes, ahead of email (73.0 minutes) and phone (69.3 minutes); chat takes about 13.79 minutes longer than phone on average.
  - Reported values: resolution_email=73.01724137931035, resolution_chat=83.03921568627452, resolution_phone=69.25352112676056
  - Direction: not_applicable
  - Ranking: chat, email, phone
  - Derived difference(resolution_chat, resolution_phone): 13.79
- [q4] Email tickets reopen at 17.24% versus 7.84% for chat — 9.4 percentage points higher, a relative increase of 119.83% for email over chat.
  - Reported values: reopen_rate_email_pct=17.24137931034483, reopen_rate_chat_pct=7.8431372549019605, email_vs_chat_reopen_change_pct=119.82758620689657
  - Direction: increase
  - Derived difference(reopen_rate_email_pct, reopen_rate_chat_pct): 9.4
- [q5] 12 tickets (3.46% of all tickets) combine high labor cost (>= $100) with a low satisfaction score (<= 2); this segment's reopen rate is 8.33%.
  - Reported values: high_cost_low_sat_count=12.0, high_cost_low_sat_reopen_pct=8.333333333333332
  - Direction: not_applicable
  - Derived share(high_cost_low_sat_count, ticket_count): 3.46
- [q6] Resolution time is right-skewed: the median is 65 minutes, below the 75.2-minute mean, with a standard deviation of 51.9 minutes. Mean satisfaction is 4.15, and 19 tickets (5.48%) are missing a satisfaction score.
  - Reported values: resolution_median=65.0, resolution_std=51.92574910613114, satisfaction_mean=4.152439024390244, satisfaction_missing_count=19.0
  - Direction: not_applicable
  - Derived share(satisfaction_missing_count, ticket_count): 5.48
- [q7] 18 unique agents handled the tickets. The busiest agent handled 26 tickets, a 7.49% share of total volume, compared with an average of about 19.28 tickets per agent, indicating no extreme concentration.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=26.0, top_agent_ticket_share_pct=7.492795389048991
  - Direction: not_applicable
  - Derived ratio(ticket_count, unique_agent_count): 19.28

## Limitations
- 19 tickets (about 5.5%) lack satisfaction scores; if missingness is not random, satisfaction-based findings may be biased.
- All comparisons are descriptive, not causal: ticket complexity, priority, customer type and agent tenure were not controlled for.
- The export covers a single period with no time dimension, so trends over time cannot be assessed.
- The high-cost/low-satisfaction thresholds ($100, <=2) are arbitrary cutoffs, and the resulting segment of 12 tickets is too small for strong statistical inference.
- Agent concentration is summarized only by the top agent's share; a full workload distribution (e.g., Gini coefficient) was not computed.

## Conclusion
Support operations are broadly healthy: satisfaction averages 4.15 and workload is evenly spread across 18 agents. Priorities are (1) investigating why email tickets reopen at 17.24% — more than double chat's rate — and (2) reviewing chat handling, the slowest channel at 83.0 minutes on average. The 12 high-cost, low-satisfaction tickets warrant individual follow-up, and satisfaction capture should be improved to close the 5.5% data gap.
