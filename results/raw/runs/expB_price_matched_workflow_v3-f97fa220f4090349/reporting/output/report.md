# Support Operations Analysis Report

Analysis of 220 support tickets reveals a total labor cost of $17,445.07 and a mean resolution time of 75.7 minutes. Team Beta incurs the highest labor cost, chat is the slowest channel by resolution time, and email tickets reopen at a rate 122% higher than chat. A small high-cost, low-satisfaction segment warrants targeted intervention, and agent workload shows moderate concentration among 18 agents.

## Key findings
- [q1] The dataset contains 220 tickets with a mean resolution time of 75.7 minutes and a total labor cost of $17,445.07.
  - Reported values: ticket_count=220.0, mean_resolution_minutes=75.6590909090909, total_labor_cost=17445.07
- [q2] Team Beta has the highest labor cost at $6,928.72, followed by Gamma at $5,911.44 and Alpha at $4,604.91. Beta accounts for the largest share of total labor spend.
  - Reported values: labor_cost_alpha=4604.91, labor_cost_beta=6928.72, labor_cost_gamma=5911.44
  - Ranking: Beta, Gamma, Alpha
- [q3] Chat is the slowest channel with a mean resolution time of 82.2 minutes, followed by phone at 74.1 minutes and email at 71.7 minutes.
  - Reported values: resolution_email=71.72380952380952, resolution_chat=82.23287671232876, resolution_phone=74.07142857142857
  - Ranking: chat, phone, email
- [q4] Email tickets reopen at 15.2%, compared to 6.8% for chat. Email's reopen rate is 122.5% higher than chat's, representing a substantial increase in reopening risk for the email channel.
  - Reported values: reopen_rate_email_pct=15.238095238095239, reopen_rate_chat_pct=6.8493150684931505, email_vs_chat_reopen_change_pct=122.47619047619051
  - Direction: increase
  - Derived pct_change(reopen_rate_email_pct, reopen_rate_chat_pct): 122.5
- [q5] Nine tickets meet the high-cost (labor_cost ≥ $100) and low-satisfaction (score ≤ 2) criteria. Of these, 11.1% were reopened, flagging a small but operationally significant at-risk segment.
  - Reported values: high_cost_low_sat_count=9.0, high_cost_low_sat_reopen_pct=11.11111111111111
- [q6] Resolution time has a median of 65.0 minutes and a standard deviation of 51.3 minutes, indicating notable spread. Mean satisfaction (where recorded) is 4.14 out of 5, with 14 tickets missing a satisfaction score.
  - Reported values: resolution_median=65.0, resolution_std=51.302729053162466, satisfaction_mean=4.140776699029126, satisfaction_missing_count=14.0
- [q7] There are 18 distinct agents. The busiest single agent handled 16 tickets, representing 7.3% of all tickets, suggesting workload is reasonably distributed with no extreme concentration.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=16.0, top_agent_ticket_share_pct=7.2727272727272725
  - Derived share(top_agent_ticket_count, ticket_count): 7.3

## Limitations
- Both the cleaning and analysis pipeline stages reported validation failures; results should be treated as provisional until the underlying data quality issues are investigated and resolved.
- Fourteen tickets are missing satisfaction scores, which may introduce bias into the satisfaction mean if missingness is non-random.
- The high-cost, low-satisfaction segment contains only 9 tickets, making percentage-based conclusions (e.g., reopen rate) statistically fragile.
- The analysis covers a single export snapshot with no time dimension, so trends over time cannot be assessed.
- Agent identity relies on agent_id from a joined roster; any mismatches during the join could distort agent concentration metrics.

## Conclusion
Support operations are broadly functional, with a mean resolution time of 75.7 minutes and a healthy average satisfaction score of 4.14. However, email tickets reopen at more than twice the rate of chat tickets, Team Beta drives the largest share of labor cost, and a small high-cost, low-satisfaction cohort merits focused quality review. Given the pipeline validation failures, these findings should be confirmed once data quality issues are remediated.
