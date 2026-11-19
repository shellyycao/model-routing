# Support Operations Analysis Report

Analysis of 220 support tickets reveals a total labor cost of $17,445.07 and a mean resolution time of 75.7 minutes. Team Beta carries the highest labor cost share. Chat is the slowest channel by resolution time. Email tickets reopen at a rate more than twice that of chat tickets, and a small high-cost, low-satisfaction segment warrants targeted intervention. Agent workload is moderately concentrated, with the busiest agent handling 7.3% of all tickets.

## Key findings
- [q1] The dataset contains 220 tickets with a mean resolution time of 75.7 minutes and a total labor cost of $17,445.07.
  - Reported values: ticket_count=220.0, mean_resolution_minutes=75.6590909090909, total_labor_cost=17445.07
- [q2] Team Beta incurred the highest labor cost at $6,928.72, followed by Gamma at $5,911.44 and Alpha at $4,604.91. Beta accounts for the largest share of total spend.
  - Reported values: labor_cost_alpha=4604.91, labor_cost_beta=6928.72, labor_cost_gamma=5911.44
  - Ranking: Beta, Gamma, Alpha
- [q3] Chat had the longest mean resolution time at 82.2 minutes, followed by phone at 74.1 minutes and email at 71.7 minutes.
  - Reported values: resolution_email=71.72380952380952, resolution_chat=82.23287671232876, resolution_phone=74.07142857142857
  - Ranking: chat, phone, email
- [q4] Email tickets reopen at 15.2%, compared to 6.8% for chat — an increase of 122.5% relative to the chat rate, indicating email interactions are substantially more likely to require follow-up.
  - Reported values: reopen_rate_email_pct=15.238095238095239, reopen_rate_chat_pct=6.8493150684931505, email_vs_chat_reopen_change_pct=122.47619047619051
  - Direction: increase
  - Derived pct_change(reopen_rate_email_pct, reopen_rate_chat_pct): 122.5
- [q5] Nine tickets meet the high-cost (≥$100) and low-satisfaction (≤2) criteria, with 11.1% of them having been reopened — a segment meriting priority review.
  - Reported values: high_cost_low_sat_count=9.0, high_cost_low_sat_reopen_pct=11.11111111111111
- [q6] Resolution time has a median of 65.0 minutes and a standard deviation of 51.3 minutes, indicating notable spread. Mean satisfaction (where recorded) is 4.1 out of 5, with 14 tickets missing a satisfaction score.
  - Reported values: resolution_median=65.0, resolution_std=51.302729053162466, satisfaction_mean=4.140776699029126, satisfaction_missing_count=14.0
- [q7] Tickets were handled by 18 distinct agents. The busiest single agent handled 16 tickets, representing 7.3% of total volume — a moderate but watchable concentration.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=16.0, top_agent_ticket_share_pct=7.2727272727272725
  - Derived share(top_agent_ticket_count, ticket_count): 7.3

## Limitations
- Both the cleaning and analysis pipeline stages reported validation failures; results should be treated as provisional until the underlying data quality issues are investigated and resolved.
- Fourteen tickets are missing satisfaction scores, which may introduce bias into the satisfaction mean if missingness is non-random.
- The high-cost, low-satisfaction segment contains only 9 tickets, making percentage-based conclusions (e.g., reopen rate) statistically fragile.
- Agent identity is based on agent_id only; if agents share IDs or IDs changed over time, concentration metrics may be understated or overstated.
- No time-period metadata is reported, so trends over time cannot be assessed from this snapshot.

## Conclusion
Support operations show acceptable average satisfaction (4.1/5) but meaningful variation in resolution speed and a concerning email reopen rate 122% higher than chat. Team Beta drives the largest labor cost share. Priority actions should include investigating email resolution quality and reviewing the nine high-cost, low-satisfaction tickets. Data pipeline failures must be remediated before these findings are used for formal decision-making.
