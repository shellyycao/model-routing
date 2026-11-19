# Support Ticket Operations: Cost, Speed, Reopening, Satisfaction, and Agent Concentration

This report summarizes verified findings from 347 cleaned support tickets. Total labor cost reached $27,422.90, with Team Beta spending the most ($10,247.36). Mean resolution time is 75.19 minutes; chat is the slowest channel (83.04 minutes) and phone the fastest (69.25). Email's reopen rate of 17.24% is a 119.83% relative increase over chat's 7.84%. Satisfaction averages 4.15, and the 12-ticket high-cost, low-satisfaction segment is small. Workload is spread evenly across 18 agents; the busiest handles 7.49% of tickets.

## Key findings
- [q1] The final cleaned dataset contains 347 tickets. Mean resolution time is 75.19 minutes, and total labor cost across all tickets is $27,422.90 — the overall workload and spend baseline for this analysis.
  - Reported values: ticket_count=347.0, mean_resolution_minutes=75.19308357348703, total_labor_cost=27422.9
- [q2] Labor cost ranks Beta ($10,247.36) > Gamma ($9,387.73) > Alpha ($7,787.81). Beta, the highest-spending team, spends $2,459.55 more than Alpha, the lowest.
  - Reported values: labor_cost_alpha=7787.81, labor_cost_beta=10247.36, labor_cost_gamma=9387.73
  - Ranking: Beta, Gamma, Alpha
  - Derived difference(labor_cost_beta, labor_cost_alpha): 2459.55
- [q3] Average resolution time ranks chat (83.04 minutes) > email (73.02) > phone (69.25). Chat, the slowest channel, takes 13.79 minutes longer than phone, the fastest.
  - Reported values: resolution_email=73.01724137931035, resolution_chat=83.03921568627452, resolution_phone=69.25352112676056
  - Ranking: chat, email, phone
  - Derived difference(resolution_chat, resolution_phone): 13.79
- [q4] Email reopens 17.24% of tickets versus 7.84% for chat — a 119.83% relative increase (9.40 percentage points higher). The email-to-chat reopen change is an increase, flagging email handling quality as a concern.
  - Reported values: reopen_rate_email_pct=17.24137931034483, reopen_rate_chat_pct=7.8431372549019605, email_vs_chat_reopen_change_pct=119.82758620689657
  - Direction: increase
  - Derived difference(reopen_rate_email_pct, reopen_rate_chat_pct): 9.4
- [q5] Only 12 tickets combine labor cost ≥ $100 with satisfaction ≤ 2 (3.46% of all tickets); 8.33% of this segment reopened. The high-cost, dissatisfied segment is small and not a major reopen driver.
  - Reported values: high_cost_low_sat_count=12.0, high_cost_low_sat_reopen_pct=8.333333333333332
  - Derived share(high_cost_low_sat_count, ticket_count): 3.46
- [q6] Resolution time is right-skewed: median 65 minutes, sample standard deviation 51.93 minutes, with the mean (75.19) above the median. Mean satisfaction is 4.15, though 19 tickets have no satisfaction score.
  - Reported values: resolution_median=65.0, resolution_std=51.92574910613114, satisfaction_mean=4.152439024390244, satisfaction_missing_count=19.0
- [q7] 18 distinct agents handled the workload. The busiest agent closed 26 tickets, just 7.49% of the total, so workload is broadly distributed with no single-agent concentration risk.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=26.0, top_agent_ticket_share_pct=7.492795389048991

## Limitations
- 19 tickets lack a satisfaction score, so the 4.15 mean reflects only responded tickets and may carry non-response bias.
- Findings are descriptive only; no statistical significance tests were run, so differences (e.g., channel reopen rates) may reflect sampling noise.
- The high-cost low-satisfaction segment uses fixed thresholds ($100, score ≤ 2) that are arbitrary and yield a very small sample of 12 tickets.
- The export provides no time period, region, or ticket-complexity fields, so results cannot be trended or adjusted for case mix.

## Conclusion
Operations are broadly healthy: satisfaction is high (4.15) and workload is well spread across 18 agents. Priorities are (1) investigating email's 17.24% reopen rate, which more than doubles chat's, and (2) reviewing why chat resolution (83.04 minutes) lags phone by 13.79 minutes. Team Beta's leading labor spend ($10,247.36) warrants a cost-driver review.
