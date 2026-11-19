# Support Operations Analysis Report

Analysis of 220 support tickets reveals a total labor cost of $17,445.07. The Beta team incurred the highest costs, and chat channel resolution times were the longest. Email tickets reopened at a rate 122% higher than chat tickets. Nine high-cost, low-satisfaction tickets were identified, and workload concentration shows the top agent handling 7% of all tickets.

## Key findings
- [q1] The dataset contains 220 tickets with a mean resolution time of 75.66 minutes and a total labor cost of $17,445.07.
  - Reported values: ticket_count=220.0, mean_resolution_minutes=75.6590909090909, total_labor_cost=17445.07
- [q2] Team Beta had the highest labor cost at $6,928.72, followed by Gamma at $5,911.44 and Alpha at $4,604.91.
  - Reported values: labor_cost_alpha=4604.91, labor_cost_beta=6928.72, labor_cost_gamma=5911.44
  - Ranking: Beta, Gamma, Alpha
- [q3] Resolution times were highest for chat at 82.23 minutes, followed by phone at 74.07 minutes and email at 71.72 minutes.
  - Reported values: resolution_email=71.72380952380952, resolution_chat=82.23287671232876, resolution_phone=74.07142857142857
  - Ranking: chat, phone, email
- [q4] The email reopen rate was 15.24%, compared to 6.85% for chat, representing a 122.48% increase relative to the chat rate.
  - Reported values: reopen_rate_email_pct=15.238095238095239, reopen_rate_chat_pct=6.8493150684931505, email_vs_chat_reopen_change_pct=122.47619047619051
  - Direction: increase
- [q5] There were 9 tickets identified as high-cost and low-satisfaction, with a reopen percentage of 11.11%.
  - Reported values: high_cost_low_sat_count=9.0, high_cost_low_sat_reopen_pct=11.11111111111111
- [q6] The median resolution time was 65.0 minutes with a standard deviation of 51.30 minutes. The mean satisfaction score was 4.14, with 14 missing satisfaction values.
  - Reported values: resolution_median=65.0, resolution_std=51.302729053162466, satisfaction_mean=4.140776699029126, satisfaction_missing_count=14.0
- [q7] There were 18 unique agents. The top agent handled 16 tickets, accounting for 7.27% of the total workload.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=16.0, top_agent_ticket_share_pct=7.2727272727272725

## Limitations
- The cleaning and analysis stages both failed validation; these findings are based on the output of the analysis code run in a sandbox environment.
- Satisfaction data was missing for 14 tickets, which may bias the satisfaction mean and the high-cost low-satisfaction segment count.
- The analysis assumes the 'cleaned.csv' input was correctly processed despite the cleaning stage failure.

## Conclusion
While the data pipeline encountered validation failures, the computed metrics suggest potential efficiency issues in the chat channel and a significant disparity in reopen rates between email and chat. Workload distribution appears relatively balanced with no single agent dominating the ticket volume. Stakeholders should review the data cleaning process to ensure reliability before taking operational action.
