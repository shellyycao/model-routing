# Support Operations Ticket Analysis Report

The analysis of 220 support tickets reveals overall average resolution time of 75.7 minutes and total labor cost of $17,445. Team Alpha, Beta, and Gamma incurred $4,605, $6,929, and $5,911 respectively, with Beta bearing the highest cost. Chat tickets take the longest to resolve (82.2 min) while email is fastest (71.7 min). Reopened tickets are more common in email (15.2%) than chat (6.8%), representing a 122.5% increase. A small high‑cost, low‑satisfaction segment (9 tickets) shows an 11.1% reopen rate. Resolution time median is 65 min with a standard deviation of 51.3 min; average satisfaction is 4.14, though 14 scores are missing. Eighteen agents handled tickets, with the top agent responsible for 16 tickets (7.27% of total).

## Key findings
- [q1] The dataset contains 220 tickets with an average resolution time of 75.66 minutes and a total labor cost of $17,445.07.
  - Reported values: ticket_count=220.0, mean_resolution_minutes=75.6590909090909, total_labor_cost=17445.07
- [q2] Team labor costs differ markedly, with Beta the highest, followed by Gamma and Alpha.
  - Reported values: labor_cost_alpha=4604.91, labor_cost_beta=6928.72, labor_cost_gamma=5911.44
  - Ranking: Beta, Gamma, Alpha
- [q3] Mean resolution times vary by channel, chat being the slowest, then phone, and email the fastest.
  - Reported values: resolution_email=71.72380952380952, resolution_chat=82.23287671232876, resolution_phone=74.07142857142857
  - Ranking: chat, phone, email
- [q4] Email tickets have a higher reopen rate (15.24%) than chat tickets (6.85%), representing a 122.48% increase.
  - Reported values: reopen_rate_email_pct=15.238095238095239, reopen_rate_chat_pct=6.8493150684931505, email_vs_chat_reopen_change_pct=122.47619047619051
  - Direction: increase
- [q5] There are 9 high‑cost (≥ $100) tickets with low satisfaction (≤ 2), and 11.11% of them were reopened.
  - Reported values: high_cost_low_sat_count=9.0, high_cost_low_sat_reopen_pct=11.11111111111111
- [q6] Resolution time median is 65 minutes with a sample standard deviation of 51.30 minutes; average satisfaction score is 4.14, with 14 missing scores.
  - Reported values: resolution_median=65.0, resolution_std=51.302729053162466, satisfaction_mean=4.140776699029126, satisfaction_missing_count=14.0
- [q7] Tickets were handled by 18 distinct agents; the most active agent resolved 16 tickets, accounting for 7.27% of all tickets.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=16.0, top_agent_ticket_share_pct=7.2727272727272725

## Limitations
- The cleaning stage failed, so residual data quality issues (e.g., duplicate rows, inconsistent timestamps) may remain.
- 14 satisfaction scores are missing, which could bias the average satisfaction metric.
- The high‑cost low‑satisfaction segment is based on a very small sample (9 tickets), limiting statistical confidence.
- All monetary values are in the original currency without inflation adjustment.

## Conclusion
Overall ticket handling performance shows moderate resolution times and acceptable labor costs, but email channels suffer higher reopen rates. Targeted improvements in email processes and deeper investigation of the high‑cost, low‑satisfaction tickets could enhance efficiency and customer satisfaction. Monitoring agent workload distribution is advisable to ensure balanced resource allocation.
