# Support Operations Report: Cost, Resolution Speed, Reopening, Satisfaction and Agent Concentration

Analysis of 347 cleaned support tickets joined to the agent roster shows a mean resolution time of 75.19 minutes and total labor cost of $27,422.90. Team Beta carries the highest labor cost ($10,247.36). Chat is the slowest channel on average (83.04 minutes), while email reopens far more often than chat (17.24% vs 7.84%). Only 12 tickets combine high cost (>= $100) with low satisfaction (<= 2). Satisfaction averages 4.15, and workload is well distributed across 18 agents, with the busiest agent handling just 7.49% of tickets.

## Key findings
- [q1] The cleaned dataset contains 347 tickets, with a mean resolution time of 75.19 minutes and a total labor cost of $27,422.90.
  - Reported values: ticket_count=347.0, mean_resolution_minutes=75.19308357348703, total_labor_cost=27422.9
  - Direction: not_applicable
- [q2] Beta has the highest team labor cost at $10,247.36, followed by Gamma ($9,387.73) and Alpha ($7,787.81); Beta exceeds Alpha by $2,459.55.
  - Reported values: labor_cost_alpha=7787.81, labor_cost_beta=10247.36, labor_cost_gamma=9387.73
  - Direction: not_applicable
  - Ranking: Beta, Gamma, Alpha
  - Derived difference(labor_cost_beta, labor_cost_alpha): 2459.55
- [q3] Chat is the slowest channel with a mean resolution of 83.04 minutes, ahead of email (73.02 minutes) and phone (69.25 minutes); chat takes 13.79 minutes longer than phone on average.
  - Reported values: resolution_email=73.01724137931035, resolution_chat=83.03921568627452, resolution_phone=69.25352112676056
  - Direction: not_applicable
  - Ranking: chat, email, phone
  - Derived difference(resolution_chat, resolution_phone): 13.79
- [q4] Email tickets reopen at 17.24% versus 7.84% for chat, a relative increase of 119.83% for email over chat.
  - Reported values: reopen_rate_email_pct=17.24137931034483, reopen_rate_chat_pct=7.8431372549019605, email_vs_chat_reopen_change_pct=119.82758620689657
  - Direction: increase
- [q5] 12 tickets combine labor cost of at least $100 with a satisfaction score of 2 or lower, representing 3.46% of all tickets; 8.33% of these tickets were reopened.
  - Reported values: high_cost_low_sat_count=12.0, high_cost_low_sat_reopen_pct=8.333333333333332
  - Direction: not_applicable
  - Derived share(high_cost_low_sat_count, ticket_count): 3.46
- [q6] Median resolution time is 65 minutes with a sample standard deviation of 51.93 minutes; the mean of 75.19 minutes sits 10.19 minutes above the median, indicating right-skewed resolution times. Mean satisfaction is 4.15, with 19 tickets missing a satisfaction score.
  - Reported values: resolution_median=65.0, resolution_std=51.92574910613114, satisfaction_mean=4.152439024390244, satisfaction_missing_count=19.0
  - Direction: not_applicable
  - Derived difference(mean_resolution_minutes, resolution_median): 10.19
- [q7] 18 distinct agents handled the 347 tickets; the busiest single agent handled 26 tickets, or 7.49% of total volume, indicating a broadly distributed workload with no dominant agent.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=26.0, top_agent_ticket_share_pct=7.492795389048991
  - Direction: not_applicable

## Limitations
- 19 tickets lack a satisfaction_score; the reported satisfaction mean of 4.15 reflects only non-missing responses and could be biased if dissatisfied customers respond less often.
- All findings are descriptive; no statistical significance testing was performed, so differences such as the email-vs-chat reopen gap may partly reflect random variation.
- The high-cost low-satisfaction segment contains only 12 tickets, so its 8.33% reopen rate is based on a small sample and is unstable.
- Resolution times are highly variable (standard deviation 51.93 minutes against a mean of 75.19), so averages conceal substantial ticket-level differences.
- No time period, ticket severity, or channel volume mix is provided in the verified findings, limiting trend, seasonality, and root-cause interpretation.

## Conclusion
Support operations are generally healthy: satisfaction is high (4.15 mean) and workload is evenly spread across 18 agents. The clearest action areas are chat resolution speed (83.04 minutes mean, the slowest channel) and email quality, given email's 17.24% reopen rate. Team Beta's leading labor cost ($10,247.36) warrants a workload or staffing review.
