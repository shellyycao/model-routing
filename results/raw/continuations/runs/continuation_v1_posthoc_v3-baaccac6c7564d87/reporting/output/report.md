# Support Operations Analysis Report

Analysis of 347 support tickets reveals a total labor cost of $27,422.90 and a mean resolution time of 75.2 minutes. Team Beta incurs the highest labor cost, phone channel resolves tickets fastest, and email reopening rates are approximately 120% higher than chat. A small high-cost, low-satisfaction segment warrants targeted intervention, and agent workload is moderately concentrated with the busiest agent handling 7.5% of all tickets.

## Key findings
- [q1] The dataset contains 347 tickets with a mean resolution time of 75.2 minutes and a total labor cost of $27,422.90.
  - Reported values: ticket_count=347.0, mean_resolution_minutes=75.19308357348703, total_labor_cost=27422.9
- [q2] Team Beta incurred the highest labor cost at $10,247.36, followed by Gamma at $9,387.73 and Alpha at $7,787.81.
  - Reported values: labor_cost_alpha=7787.81, labor_cost_beta=10247.36, labor_cost_gamma=9387.730000000001
  - Ranking: Beta, Gamma, Alpha
- [q3] Chat had the longest mean resolution time at 83.0 minutes, followed by email at 73.0 minutes, and phone was fastest at 69.3 minutes.
  - Reported values: resolution_email=73.01724137931035, resolution_chat=83.03921568627452, resolution_phone=69.25352112676056
  - Ranking: chat, email, phone
- [q4] Email tickets were reopened at a rate of 17.2%, compared to 7.8% for chat — an increase of approximately 120% relative to chat's reopening rate.
  - Reported values: reopen_rate_email_pct=17.24137931034483, reopen_rate_chat_pct=7.8431372549019605, email_vs_chat_reopen_change_pct=119.82758620689657
  - Direction: increase
  - Derived pct_change(reopen_rate_email_pct, reopen_rate_chat_pct): 119.82758620689657
- [q5] 12 tickets met the high-cost (labor cost ≥ $100), low-satisfaction (score ≤ 2) criteria, with a reopening rate of 8.3% within this segment.
  - Reported values: high_cost_low_sat_count=12.0, high_cost_low_sat_reopen_pct=8.333333333333332
- [q6] Resolution time has a median of 65.0 minutes and a standard deviation of 51.9 minutes, indicating notable spread. Mean satisfaction (where recorded) is 4.15 out of 5, with 19 tickets missing a satisfaction score.
  - Reported values: resolution_median=65.0, resolution_std=51.92574910613114, satisfaction_mean=4.152439024390244, satisfaction_missing_count=19.0
- [q7] 18 distinct agents handled tickets. The busiest single agent handled 26 tickets, representing 7.5% of all tickets — a moderate but notable concentration.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=26.0, top_agent_ticket_share_pct=7.492795389048991
  - Derived share(top_agent_ticket_count, ticket_count): 7.492795389048991

## Limitations
- 19 tickets are missing satisfaction scores, which may introduce bias into the satisfaction mean if missingness is non-random.
- Labor cost calculations depend on agent roster data joined at cleaning; any roster inaccuracies (e.g., incorrect hourly rates) would propagate to all cost metrics.
- The analysis covers a single export snapshot; trends over time cannot be assessed without longitudinal data.
- Reopening rates are computed per channel but do not control for ticket complexity or agent experience, which may confound comparisons.
- Agent concentration metrics identify the top agent by ticket count only; workload quality and ticket difficulty are not factored in.

## Conclusion
Support operations are broadly functional, with a mean satisfaction score of 4.15 and a median resolution time of 65 minutes. However, Team Beta's disproportionate labor cost, email's elevated reopening rate (~120% above chat), and the 12 high-cost low-satisfaction tickets represent clear areas for operational improvement. Addressing email resolution quality and reviewing Beta team workflows could yield meaningful cost and satisfaction gains.
