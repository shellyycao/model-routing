# Support Operations Analysis Report

Analysis of 347 support tickets reveals a total labor cost of $27,422.90 and a mean resolution time of 75.2 minutes. Team Beta carries the highest labor cost share. Phone is the fastest channel while chat is the slowest. Email tickets reopen at more than double the rate of chat tickets, and a small high-cost, low-satisfaction segment warrants targeted intervention. Agent workload is moderately concentrated, with the busiest agent handling 7.5% of all tickets.

## Key findings
- [q1] The dataset contains 347 tickets with a mean resolution time of 75.2 minutes and a total labor cost of $27,422.90.
  - Reported values: ticket_count=347.0, mean_resolution_minutes=75.19308357348703, total_labor_cost=27422.9
- [q2] Team Beta incurred the highest labor cost at $10,247.36, followed by Gamma at $9,387.73 and Alpha at $7,787.81. Beta's cost exceeds Alpha's by $2,459.55.
  - Reported values: labor_cost_alpha=7787.81, labor_cost_beta=10247.36, labor_cost_gamma=9387.73
  - Ranking: Beta, Gamma, Alpha
  - Derived difference(labor_cost_beta, labor_cost_alpha): 2459.55
- [q3] Phone is the fastest channel at 69.3 minutes mean resolution, followed by email at 73.0 minutes; chat is the slowest at 83.0 minutes.
  - Reported values: resolution_email=73.01724137931035, resolution_chat=83.03921568627452, resolution_phone=69.25352112676056
  - Ranking: chat, email, phone
- [q4] Email tickets have a reopen rate of 17.2%, compared to 7.8% for chat — an increase of approximately 119.8% relative to chat's rate, indicating email tickets are far more likely to require reopening.
  - Reported values: reopen_rate_email_pct=17.24137931034483, reopen_rate_chat_pct=7.8431372549019605, email_vs_chat_reopen_change_pct=119.82758620689657
  - Direction: increase
  - Derived pct_change(reopen_rate_email_pct, reopen_rate_chat_pct): 119.82758620689657
- [q5] 12 tickets meet the high-cost (labor cost ≥ $100) and low-satisfaction (score ≤ 2) criteria, with a reopen rate of 8.3%. This segment represents a priority area for quality improvement.
  - Reported values: high_cost_low_sat_count=12.0, high_cost_low_sat_reopen_pct=8.333333333333332
- [q6] Resolution time has a median of 65.0 minutes and a standard deviation of 51.9 minutes, indicating notable spread. Mean satisfaction (from 328 scored tickets) is 4.15 out of 5, with 19 tickets missing a satisfaction score.
  - Reported values: resolution_median=65.0, resolution_std=51.92574910613114, satisfaction_mean=4.152439024390244, satisfaction_missing_count=19.0
- [q7] 18 distinct agents handled the 347 tickets. The busiest single agent resolved 26 tickets, representing 7.5% of total volume — a moderate but notable concentration.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=26.0, top_agent_ticket_share_pct=7.492795389048991
  - Derived share(top_agent_ticket_count, ticket_count): 7.492795389048991

## Limitations
- 19 tickets are missing satisfaction scores, which may introduce bias into the mean satisfaction calculation if missingness is non-random.
- Labor cost thresholds (e.g., ≥$100 for the high-cost segment) are fixed cut-offs; results may differ under alternative definitions.
- The analysis covers a single export snapshot; trends over time cannot be assessed.
- Agent identity is represented only by agent_id; roster attributes such as tenure or specialisation are not incorporated into the analysis.
- Reopen rates are computed per channel but not adjusted for ticket complexity or type, which may confound channel comparisons.

## Conclusion
Support operations show acceptable overall satisfaction (4.15/5) but meaningful inefficiencies: email tickets reopen at nearly 120% the rate of chat tickets, chat resolution is the slowest channel, and Team Beta accounts for the largest share of labor cost. The 12 high-cost, low-satisfaction tickets and the high resolution-time variability (std 51.9 min) suggest targeted process reviews for email handling and complex ticket types would yield the greatest operational gains.
