# Support Ticket Operations – Key Metrics Report

The analysis of 220 support tickets reveals overall resolution time of about 76 minutes and total labor cost of $17,445. Team-level cost varies, with Team Beta the most expensive. Chat channels take the longest to resolve, while email tickets have a markedly higher reopening rate (15.2% vs 6.9% for chat), a 122.5% increase. A small high‑cost, low‑satisfaction segment (9 tickets) shows an 11.1% reopening rate. Resolution time distribution is centered at 65 min (SD ≈ 51 min). Eighteen agents handled tickets; the top agent resolved 16 tickets, accounting for 7.27% of the workload.

## Key findings
- [q1] The dataset contains 220 tickets, with an average resolution time of 75.66 minutes and total labor cost of $17,445.07.
  - Reported values: ticket_count=220.0, mean_resolution_minutes=75.66, total_labor_cost=17445.07
- [q2] Team labor costs differ, with Beta incurring the highest cost, followed by Gamma, then Alpha.
  - Reported values: labor_cost_alpha=4604.91, labor_cost_beta=6928.72, labor_cost_gamma=5911.44
  - Ranking: Beta, Gamma, Alpha
- [q3] Average resolution time is longest for chat, then phone, then email.
  - Reported values: resolution_email=71.72, resolution_chat=82.23, resolution_phone=74.07
  - Ranking: chat, phone, email
- [q4] Reopened tickets are 15.24% for email and 6.85% for chat, representing a 122.48% higher reopening rate for email versus chat.
  - Reported values: reopen_rate_email_pct=15.24, reopen_rate_chat_pct=6.85, email_vs_chat_reopen_change_pct=122.48
  - Direction: increase
- [q5] There are 9 tickets with labor cost ≥ $100 and satisfaction ≤ 2, and 11.11% of these were reopened.
  - Reported values: high_cost_low_sat_count=9.0, high_cost_low_sat_reopen_pct=11.11
- [q6] Resolution time median is 65 minutes with a standard deviation of 51.30 minutes; average satisfaction score is 4.14, with 14 tickets missing satisfaction data.
  - Reported values: resolution_median=65.0, resolution_std=51.3, satisfaction_mean=4.14, satisfaction_missing_count=14.0
- [q7] Tickets were handled by 18 distinct agents; the top agent resolved 16 tickets, representing 7.27% of all tickets.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=16.0, top_agent_ticket_share_pct=7.27

## Limitations
- The cleaning stage failed, so any residual data quality issues (e.g., duplicate rows, inconsistent timestamps) may affect the metrics.
- Satisfaction scores are missing for 14 tickets, which could bias the average satisfaction figure.
- Labor cost and resolution time are aggregated at ticket level; variations within tickets (e.g., multi‑agent handoffs) are not captured.

## Conclusion
Overall support operations show moderate efficiency with an average resolution time of 76 minutes, but notable disparities exist across teams and channels. Email tickets are prone to higher reopening rates, suggesting potential quality issues. Targeted interventions on high‑cost, low‑satisfaction tickets and on the agents handling the bulk of work could improve both cost efficiency and customer experience.
