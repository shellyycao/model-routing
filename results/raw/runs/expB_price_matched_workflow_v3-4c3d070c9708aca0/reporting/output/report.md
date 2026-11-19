# Support Operations Analysis Report

Analysis of 220 support tickets reveals a total labor cost of $17,445.07 and a mean resolution time of 75.7 minutes. Team Beta carries the highest labor cost share. Chat is the slowest channel by resolution time. Email tickets reopen at a rate more than twice that of chat tickets, representing a significant quality concern. A small high-cost, low-satisfaction segment of 9 tickets warrants targeted intervention. Agent workload is moderately concentrated, with the busiest agent handling 7.3% of all tickets.

## Key findings
- [q1] The dataset contains 220 tickets with a mean resolution time of 75.7 minutes and a total labor cost of $17,445.07.
  - Reported values: ticket_count=220.0, mean_resolution_minutes=75.6590909090909, total_labor_cost=17445.07
- [q2] Team Beta incurred the highest labor cost at $6,928.72, followed by Gamma at $5,911.44 and Alpha at $4,604.91. Beta accounts for the largest share of total labor spend.
  - Reported values: labor_cost_alpha=4604.91, labor_cost_beta=6928.720000000001, labor_cost_gamma=5911.439999999999
  - Ranking: Beta, Gamma, Alpha
- [q3] Chat had the longest mean resolution time at 82.2 minutes, followed by phone at 74.1 minutes and email at 71.7 minutes.
  - Reported values: resolution_email=71.72380952380952, resolution_chat=82.23287671232876, resolution_phone=74.07142857142857
  - Ranking: chat, phone, email
- [q4] Email tickets reopen at 15.2%, compared to 6.8% for chat — an increase of 122.5% relative to the chat reopen rate, indicating email is a materially higher-risk channel for ticket quality.
  - Reported values: reopen_rate_email_pct=15.238095238095239, reopen_rate_chat_pct=6.8493150684931505, email_vs_chat_reopen_change_pct=122.47619047619051
  - Direction: increase
  - Derived pct_change(reopen_rate_email_pct, reopen_rate_chat_pct): 122.5
- [q5] Nine tickets met the high-cost (labor ≥ $100) and low-satisfaction (score ≤ 2) criteria, of which 11.1% were reopened — a segment meriting priority review.
  - Reported values: high_cost_low_sat_count=9.0, high_cost_low_sat_reopen_pct=11.11111111111111
- [q6] Resolution time has a median of 65.0 minutes and a standard deviation of 51.3 minutes, indicating notable spread. Mean satisfaction (on available scores) is 4.14 out of 5, with 14 tickets missing a satisfaction score.
  - Reported values: resolution_median=65.0, resolution_std=51.302729053162466, satisfaction_mean=4.140776699029126, satisfaction_missing_count=14.0
- [q7] Across 18 distinct agents, the busiest single agent handled 16 tickets, representing 7.3% of total volume — a moderate but not extreme concentration.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=16.0, top_agent_ticket_share_pct=7.2727272727272725
  - Derived share(top_agent_ticket_count, ticket_count): 7.3

## Limitations
- Both the cleaning and analysis pipeline stages reported validation failures; results should be treated as provisional until the underlying data quality issues are investigated and resolved.
- Fourteen tickets are missing satisfaction scores, which may introduce bias into the satisfaction mean if missingness is non-random.
- The high-cost, low-satisfaction segment contains only 9 tickets, making the 11.1% reopen rate statistically fragile.
- Labor cost calculations depend on the accuracy of the agent roster join; any unmatched records dropped during cleaning could distort team-level cost comparisons.
- Resolution time spread (std = 51.3 min vs. median = 65.0 min) suggests potential outliers that could skew mean-based metrics.

## Conclusion
Support operations show acceptable overall satisfaction (mean 4.14) but elevated email reopen rates (+122% vs. chat) and a costly low-satisfaction segment demand immediate attention. Team Beta's disproportionate labor cost and chat's slower resolution times are further areas for operational review. Given pipeline validation failures, findings should be confirmed once data quality issues are remediated.
