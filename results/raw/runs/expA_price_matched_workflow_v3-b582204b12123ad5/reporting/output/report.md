# Support Operations Analysis: Cost, Speed, Reopening, Satisfaction and Agent Concentration

Across 347 support tickets, total labor cost was $27,422.84 and mean resolution time was 75.2 minutes. Team Beta is the largest cost center at $10,247.32, phone is the fastest channel (69.3 minutes) and chat the slowest (83.0). Email's reopen rate of 17.24% is 119.8% higher than chat's 7.84%. Only 12 tickets are both high-cost and low-satisfaction, and workload is well spread across 18 agents, with the busiest agent handling just 7.49% of all tickets.

## Key findings
- [q1] The cleaned dataset contains 347 tickets, with a mean resolution time of 75.2 minutes and a total labor cost of $27,422.84.
  - Reported values: ticket_count=347.0, mean_resolution_minutes=75.193084, total_labor_cost=27422.84
  - Direction: not_applicable
- [q2] Total labor cost is highest for Team Beta ($10,247.32), followed by Gamma ($9,387.74) and Alpha ($7,787.78). Beta exceeds Alpha by $2,459.54 and accounts for about 37.4% of total labor cost.
  - Reported values: labor_cost_alpha=7787.78, labor_cost_beta=10247.32, labor_cost_gamma=9387.74
  - Direction: not_applicable
  - Ranking: Beta, Gamma, Alpha
  - Derived difference(labor_cost_beta, labor_cost_alpha): 2459.54
  - Derived share(labor_cost_beta, total_labor_cost): 37.4
- [q3] Phone is the fastest channel with a mean resolution time of 69.3 minutes, ahead of email (73.0) and chat (83.0); chat takes about 13.8 minutes longer than phone on average.
  - Reported values: resolution_email=73.017241, resolution_chat=83.039216, resolution_phone=69.253521
  - Direction: not_applicable
  - Ranking: chat, email, phone
  - Derived difference(resolution_chat, resolution_phone): 13.8
- [q4] Email's reopen rate (17.24%) is 119.8% higher than chat's (7.84%), a gap of roughly 9.4 percentage points — a clear increase in reopening for email relative to chat.
  - Reported values: reopen_rate_email_pct=17.241379, reopen_rate_chat_pct=7.843137, email_vs_chat_reopen_change_pct=119.827586
  - Direction: increase
  - Derived difference(reopen_rate_email_pct, reopen_rate_chat_pct): 9.4
- [q5] Only 12 tickets — 3.5% of all tickets — combine labor cost of $100 or more with a satisfaction score of 2 or lower, and their reopen rate is 8.33%, well below the email-channel rate.
  - Reported values: high_cost_low_sat_count=12.0, high_cost_low_sat_reopen_pct=8.333333
  - Direction: not_applicable
  - Derived share(high_cost_low_sat_count, ticket_count): 3.5
- [q6] Resolution time is right-skewed: the median (65 minutes) sits below the mean (75.2), with a sample standard deviation of 51.9 minutes. Mean satisfaction is 4.15, with 19 tickets missing a satisfaction score.
  - Reported values: resolution_median=65.0, resolution_std=51.925749, satisfaction_mean=4.152439, satisfaction_missing_count=19.0
  - Direction: not_applicable
- [q7] 18 distinct agents handled the workload; the busiest single agent closed 26 tickets, or 7.49% of total volume, against an average of 19.3 tickets per agent — indicating no heavy concentration on any one agent.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=26.0, top_agent_ticket_share_pct=7.492795
  - Direction: not_applicable
  - Derived ratio(ticket_count, unique_agent_count): 19.3

## Limitations
- Satisfaction scores are missing for 19 tickets; the satisfaction mean (4.15) and the q5 segment exclude them, so results could be biased if missingness is not random.
- The high-cost, low-satisfaction segment contains only 12 tickets, so its 8.33% reopen rate rests on a very small sample and should not be over-interpreted.
- The data is a single export with no time dimension, so trends, seasonality, and the impact of any process changes cannot be assessed.
- Team labor-cost totals are not normalized for ticket volume or ticket mix, so the team ranking reflects total spend rather than per-ticket efficiency.

## Conclusion
Support operations look broadly healthy: costs are moderate, resolution times cluster near 65–75 minutes, satisfaction averages 4.15, and no single agent dominates the workload. Priorities are to investigate why email tickets reopen at 17.24% (119.8% above chat), review chat workflows behind the slowest mean resolution time (83.0 minutes), and keep monitoring the small high-cost, low-satisfaction segment before it grows.
