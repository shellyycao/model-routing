# Support Ticket Operations – Key Metrics Report

The analysis of 347 support tickets reveals overall cost and performance patterns, notable differences across teams and channels, and areas for service improvement. Labor costs are highest for Team Beta, while chat channels resolve tickets most slowly. Email tickets experience a markedly higher reopen rate than chat, and a small segment of high‑cost, low‑satisfaction tickets shows modest reopen activity. Agent workload is broadly distributed, with the top agent handling only 7.5% of tickets.

## Key findings
- [q1] The dataset contains 347 tickets, with an average resolution time of 75.2 minutes and total labor cost of $27,422.90.
  - Reported values: ticket_count=347.0, mean_resolution_minutes=75.19308357348703, total_labor_cost=27422.9
- [q2] Team labor costs differ, with Beta incurring the highest cost, followed by Gamma, then Alpha.
  - Reported values: labor_cost_alpha=7787.81, labor_cost_beta=10247.36, labor_cost_gamma=9387.73
  - Ranking: Beta, Gamma, Alpha
  - Derived share(labor_cost_alpha, total_labor_cost): 28.4
  - Derived share(labor_cost_beta, total_labor_cost): 37.37
  - Derived share(labor_cost_gamma, total_labor_cost): 34.22
- [q3] Resolution speed varies by channel, fastest on phone (69.3 min), slower on email (73.0 min), and slowest on chat (83.0 min).
  - Reported values: resolution_email=73.01724137931035, resolution_chat=83.03921568627452, resolution_phone=69.25352112676056
  - Ranking: chat, email, phone
- [q4] Email tickets are reopened at a rate 119.8% higher than chat tickets, indicating a substantial increase.
  - Reported values: reopen_rate_email_pct=17.24137931034483, reopen_rate_chat_pct=7.8431372549019605, email_vs_chat_reopen_change_pct=119.82758620689657
  - Direction: increase
- [q5] There are 12 high‑cost, low‑satisfaction tickets, with 8.33% of that segment being reopened.
  - Reported values: high_cost_low_sat_count=12.0, high_cost_low_sat_reopen_pct=8.333333333333332
- [q6] Resolution times have a median of 65 min and a standard deviation of 51.9 min; average satisfaction score is 4.15, with 19 tickets missing a score.
  - Reported values: resolution_median=65.0, resolution_std=51.92574910613114, satisfaction_mean=4.152439024390244, satisfaction_missing_count=19.0
- [q7] Across the sample, 18 agents handled tickets; the most active agent resolved 26 tickets, accounting for 7.49% of all tickets.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=26.0, top_agent_ticket_share_pct=7.492795389048991

## Limitations
- The analysis relies on a single export snapshot; trends over time cannot be assessed.
- Satisfaction scores are missing for 19 tickets, which may bias the average satisfaction metric.
- Labor cost calculations assume the provided cost values are complete and accurate; any unrecorded overhead is not captured.
- Reopen rates are based on the available data and may not reflect all internal ticket handling nuances.

## Conclusion
The support operation incurs moderate overall cost with clear cost concentration in Team Beta. Chat channels are the slowest, and email tickets exhibit a significantly higher propensity to be reopened, suggesting potential quality issues. While most agents share the workload, a single agent handles a noticeable share of tickets. Targeted process improvements for email handling and deeper investigation of high‑cost, low‑satisfaction cases could enhance efficiency and customer experience.
