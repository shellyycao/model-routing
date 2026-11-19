# Support Ticket Operations: Cost, Speed, Reopening and Agent Workload Report

Analysis of 347 verified support tickets shows a total labor cost of 27,422.90 and a mean resolution time of 75.19 minutes. Team Beta carries the highest labor cost (10,247.36). Chat tickets take the longest to resolve (83.04 minutes) while phone is fastest (69.25 minutes). Email is the clearest quality concern: its reopen rate of 17.24% is 119.83% higher than chat's 7.84%. Only 12 tickets fall in the high-cost, low-satisfaction segment, reopening at 8.33%. Workload is spread across 18 agents, with the busiest handling 26 tickets (a 7.49% share), indicating no problematic concentration.

## Key findings
- [q1] The cleaned dataset contains 347 tickets with a mean resolution time of 75.19 minutes and a total labor cost of 27,422.90, equivalent to roughly 79.03 in labor cost per ticket.
  - Reported values: ticket_count=347.0, mean_resolution_minutes=75.19308357348703, total_labor_cost=27422.9
  - Direction: not_applicable
  - Derived ratio(total_labor_cost, ticket_count): 79.03
- [q2] Team Beta accounts for the most labor cost at 10,247.36, followed by Gamma at 9,387.73 and Alpha at 7,787.81; Beta's total exceeds Alpha's by 2,459.55.
  - Reported values: labor_cost_alpha=7787.81, labor_cost_beta=10247.36, labor_cost_gamma=9387.73
  - Direction: not_applicable
  - Ranking: Beta, Gamma, Alpha
  - Derived difference(labor_cost_beta, labor_cost_alpha): 2459.55
- [q3] Average resolution time is highest for chat at 83.04 minutes, then email at 73.02 minutes and phone at 69.25 minutes; chat tickets take 13.79 minutes longer than phone tickets on average.
  - Reported values: resolution_email=73.01724137931035, resolution_chat=83.03921568627452, resolution_phone=69.25352112676056
  - Direction: not_applicable
  - Ranking: chat, email, phone
  - Derived difference(resolution_chat, resolution_phone): 13.79
- [q4] Email tickets reopen at 17.24% versus 7.84% for chat, an increase of 119.83% (about 9.4 percentage points more), making email the reopening hotspot among the channels compared.
  - Reported values: reopen_rate_email_pct=17.24137931034483, reopen_rate_chat_pct=7.8431372549019605, email_vs_chat_reopen_change_pct=119.82758620689657
  - Direction: increase
  - Derived difference(reopen_rate_email_pct, reopen_rate_chat_pct): 9.4
- [q5] Only 12 tickets, 3.46% of all 347 tickets, combine a labor cost of at least 100 with a satisfaction score of 2 or lower, and 8.33% of this segment was reopened.
  - Reported values: high_cost_low_sat_count=12.0, high_cost_low_sat_reopen_pct=8.333333333333332
  - Direction: not_applicable
  - Derived share(high_cost_low_sat_count, ticket_count): 3.46
- [q6] Resolution times vary widely, with a median of 65.0 minutes and a sample standard deviation of 51.93 minutes. Mean satisfaction is 4.15, and 19 tickets (5.48% of 347) are missing a satisfaction score.
  - Reported values: resolution_median=65.0, resolution_std=51.92574910613114, satisfaction_mean=4.152439024390244, satisfaction_missing_count=19.0
  - Direction: not_applicable
  - Derived share(satisfaction_missing_count, ticket_count): 5.48
- [q7] The 347 tickets were handled by 18 distinct agents, and the busiest single agent closed 26 tickets, a 7.49% share, against an even-distribution average of 19.28 tickets per agent.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=26.0, top_agent_ticket_share_pct=7.492795389048991
  - Direction: not_applicable
  - Derived ratio(ticket_count, unique_agent_count): 19.28

## Limitations
- Satisfaction scores are missing for 19 tickets, so satisfaction-based metrics (mean and the low-satisfaction segment) cover only a subset of tickets.
- The high-cost low-satisfaction segment contains just 12 tickets, so its 8.33% reopen rate is based on a very small sample and may be unstable.
- Cost figures reflect labor cost only; other cost drivers such as tooling or overhead are not captured in the export.
- The reopening comparison covers email and chat only; phone reopen rates were not part of the verified analysis.
- The analysis is a single cross-sectional snapshot with no time dimension, so trends and seasonality cannot be assessed.

## Conclusion
Support operations appear broadly efficient, with a moderate 75.19-minute mean resolution time and a well-balanced 18-agent workload. The clearest action item is email quality: a reopen rate of 17.24%, 119.83% above chat, warrants root-cause review of email handling. The small high-cost, low-satisfaction segment (12 tickets) should be monitored, and Beta's leading labor cost of 10,247.36 may merit a staffing or ticket-mix review.
