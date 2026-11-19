# Support Operations Report: Cost, Speed, Reopening, Satisfaction and Agent Concentration

Across 347 verified support tickets, mean resolution time was 75.2 minutes and total labor cost was $27,422.90. Team Beta carries the largest labor cost ($10,247.36). Chat is the slowest channel (83.0 minutes mean) yet reopens least (7.8%), while email reopens at 17.2% — a verified 119.8% higher rate than chat. Satisfaction averages 4.15 with 19 missing scores, and work is spread across 18 agents, the busiest handling 7.5% of tickets. Priorities: investigate email reopening and chat resolution speed, and review Beta's cost drivers.

## Key findings
- [q1] The cleaned dataset contains 347 tickets, with a mean resolution time of 75.2 minutes and total labor cost of $27,422.90.
  - Reported values: ticket_count=347.0, mean_resolution_minutes=75.19308357348703, total_labor_cost=27422.9
- [q2] Team Beta records the highest total labor cost at $10,247.36, followed by Gamma at $9,387.73 and Alpha at $7,787.81; Beta exceeds Alpha by $2,459.55.
  - Reported values: labor_cost_alpha=7787.81, labor_cost_beta=10247.36, labor_cost_gamma=9387.73
  - Ranking: Beta, Gamma, Alpha
  - Derived difference(labor_cost_beta, labor_cost_alpha): 2459.55
- [q3] Chat is the slowest channel with a mean resolution of 83.0 minutes, ahead of email at 73.0 minutes and phone at 69.3 minutes; chat takes about 13.8 minutes longer than phone on average.
  - Reported values: resolution_email=73.01724137931035, resolution_chat=83.03921568627452, resolution_phone=69.25352112676056
  - Ranking: chat, email, phone
  - Derived difference(resolution_chat, resolution_phone): 13.8
- [q4] Email tickets reopen at 17.2% versus 7.8% for chat — a verified relative increase of 119.8%, roughly 9.4 percentage points higher for email.
  - Reported values: reopen_rate_email_pct=17.24137931034483, reopen_rate_chat_pct=7.8431372549019605, email_vs_chat_reopen_change_pct=119.82758620689657
  - Direction: increase
  - Derived difference(reopen_rate_email_pct, reopen_rate_chat_pct): 9.4
- [q5] 12 tickets combine labor cost of at least $100 with a satisfaction score of 2 or below — about 3.5% of all tickets — and 8.3% of this segment was reopened.
  - Reported values: high_cost_low_sat_count=12.0, high_cost_low_sat_reopen_pct=8.333333333333332
  - Derived share(high_cost_low_sat_count, ticket_count): 3.5
- [q6] Resolution time is right-skewed: the median is 65.0 minutes versus a mean of 75.2 (a 10.2-minute gap), with a sample standard deviation of 51.9 minutes. Mean satisfaction is 4.15, and 19 tickets lack a satisfaction score.
  - Reported values: resolution_median=65.0, resolution_std=51.92574910613114, satisfaction_mean=4.152439024390244, satisfaction_missing_count=19.0
  - Derived difference(mean_resolution_minutes, resolution_median): 10.2
- [q7] 18 distinct agents handled the workload; the busiest single agent resolved 26 tickets, equal to 7.5% of all tickets, against an average of about 19.3 tickets per agent — indicating no extreme concentration.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=26.0, top_agent_ticket_share_pct=7.492795389048991
  - Derived ratio(ticket_count, unique_agent_count): 19.3

## Limitations
- 19 of 347 tickets have missing satisfaction scores; satisfaction-based metrics exclude them and could be biased if missingness is not random.
- Results are descriptive aggregates from a single export: no time frame, significance testing, or confounders (e.g., ticket complexity, channel mix per team) were analysed.
- The high-cost low-satisfaction segment holds only 12 tickets, so its 8.3% reopen rate is statistically fragile.
- The relative reopen change is sensitive to the small chat baseline (7.8%), so the 119.8% figure should be read alongside the absolute percentage-point gap.

## Conclusion
Operations look broadly healthy — satisfaction averages 4.15 and no single agent dominates volume — but email's elevated reopen rate and chat's slower resolution are the clearest improvement targets. Reviewing Team Beta's higher labor cost against its outcomes is recommended before the next reporting cycle.
