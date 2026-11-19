# Support Operations: Cost, Speed, Reopening and Satisfaction Report

This report covers 347 cleaned support tickets handled by 18 agents. Total labor cost was $27,422.90, with team Beta the largest cost center. Chat tickets are the slowest to resolve, while email tickets reopen at more than double the relative rate of chat tickets. Overall satisfaction is strong at 4.15 out of 5, and workload is well distributed: the busiest agent accounts for only 7.5% of tickets. A small segment of 12 high-cost, low-satisfaction tickets warrants targeted review.

## Key findings
- [q1] The dataset contains 347 tickets, with a mean resolution time of 75.2 minutes and a total labor cost of $27,422.90.
  - Reported values: ticket_count=347.0, mean_resolution_minutes=75.19308357348703, total_labor_cost=27422.9
  - Direction: not_applicable
- [q2] Team Beta carries the highest total labor cost at $10,247.36, followed by Gamma at $9,387.73 and Alpha at $7,787.81; Beta exceeds Alpha by $2,459.55.
  - Reported values: labor_cost_alpha=7787.81, labor_cost_beta=10247.36, labor_cost_gamma=9387.73
  - Direction: not_applicable
  - Ranking: Beta, Gamma, Alpha
  - Derived difference(labor_cost_beta, labor_cost_alpha): 2459.55
- [q3] Chat is the slowest channel at 83.0 minutes on average, then email at 73.0 minutes, then phone at 69.3 minutes; chat runs about 13.8 minutes longer than phone per ticket.
  - Reported values: resolution_email=73.01724137931035, resolution_chat=83.03921568627452, resolution_phone=69.25352112676056
  - Direction: not_applicable
  - Ranking: chat, email, phone
  - Derived difference(resolution_chat, resolution_phone): 13.8
- [q4] Email tickets reopen at 17.2% versus 7.8% for chat tickets, a 119.8% relative increase for email over chat.
  - Reported values: reopen_rate_email_pct=17.24137931034483, reopen_rate_chat_pct=7.8431372549019605, email_vs_chat_reopen_change_pct=119.82758620689657
  - Direction: increase
- [q5] Only 12 tickets combine high labor cost (at least $100) with low satisfaction (score of 2 or less), and 8.3% of that segment was reopened.
  - Reported values: high_cost_low_sat_count=12.0, high_cost_low_sat_reopen_pct=8.333333333333332
  - Direction: not_applicable
- [q6] Resolution time has a median of 65 minutes with a sample standard deviation of 51.9 minutes; the mean of 75.2 minutes sitting above the median indicates a right-skewed distribution. Mean satisfaction is 4.15 out of 5 across non-missing scores, with 19 tickets missing a satisfaction score.
  - Reported values: resolution_median=65.0, resolution_std=51.92574910613114, satisfaction_mean=4.152439024390244, satisfaction_missing_count=19.0
  - Direction: not_applicable
- [q7] Tickets are spread across 18 distinct agents, and the single busiest agent handled 26 tickets, representing just 7.5% of the total workload.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=26.0, top_agent_ticket_share_pct=7.492795389048991
  - Direction: not_applicable

## Limitations
- Satisfaction scores are missing for 19 tickets; the reported mean of 4.15 excludes them and may be biased if dissatisfied customers respond less often.
- The high-cost, low-satisfaction segment contains only 12 tickets, so its 8.3% reopen rate is based on a very small sample and is unstable.
- The 119.8% email-versus-chat reopen change is a relative figure computed on a low chat base rate (7.8%), so small absolute shifts produce large percentage changes.
- Results are descriptive only; no statistical significance testing was performed, so differences between teams and channels may reflect chance or case mix.
- Team cost and agent workload comparisons do not adjust for ticket complexity or channel mix, which may partly explain Beta's higher cost and chat's longer resolution times.
- The data is a single export snapshot; no trends over time can be assessed.

## Conclusion
Support operations show healthy satisfaction and well-balanced agent workloads, but chat resolution speed and the elevated email reopen rate are the clearest improvement targets. Team Beta's leading labor cost and the small high-cost, low-satisfaction segment merit focused review before scaling decisions are made.
