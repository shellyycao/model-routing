# Support Operations Ticket Analysis Report

The analysis of 347 support tickets reveals overall performance, cost distribution across teams, channel‑specific resolution times, and areas of concern such as high‑cost low‑satisfaction tickets. Key insights include the highest labor cost incurred by Team Beta, slower resolution for chat, a markedly higher reopening rate for email tickets, and a modest concentration of work among agents.

## Key findings
- [q1] The dataset contains 347 tickets, with an average resolution time of 75.19 minutes and a total labor cost of $27,422.90.
  - Reported values: ticket_count=347.0, mean_resolution_minutes=75.19, total_labor_cost=27422.9
- [q2] Team labor costs differ, with Beta incurring the highest cost, followed by Gamma, then Alpha.
  - Reported values: labor_cost_alpha=7787.81, labor_cost_beta=10247.36, labor_cost_gamma=9387.73
  - Ranking: Beta, Gamma, Alpha
- [q3] Resolution speed varies by channel: chat is the slowest (83.04 min), email is faster (73.02 min), and phone is the quickest (69.25 min).
  - Reported values: resolution_email=73.02, resolution_chat=83.04, resolution_phone=69.25
  - Ranking: chat, email, phone
- [q4] Email tickets are reopened at 17.24 % versus 7.84 % for chat, representing a 119.83 % higher reopening rate for email.
  - Reported values: reopen_rate_email_pct=17.24, reopen_rate_chat_pct=7.84, email_vs_chat_reopen_change_pct=119.83
  - Direction: increase
- [q5] There are 12 high‑cost, low‑satisfaction tickets, of which 8.33 % were reopened.
  - Reported values: high_cost_low_sat_count=12.0, high_cost_low_sat_reopen_pct=8.33
- [q6] The median resolution time is 65 minutes with a standard deviation of 51.93 minutes. Average satisfaction score is 4.15, and 19 tickets lack a satisfaction rating.
  - Reported values: resolution_median=65.0, resolution_std=51.93, satisfaction_mean=4.15, satisfaction_missing_count=19.0
- [q7] Tickets involve 18 distinct agents; the most active agent handled 26 tickets, representing 7.49 % of all tickets.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=26.0, top_agent_ticket_share_pct=7.49

## Limitations
- The cleaning stage failed, so residual data quality issues (e.g., duplicate rows, inconsistent timestamps) may remain.
- Satisfaction scores are missing for 19 tickets, which could bias the average satisfaction metric.
- Labor cost calculations rely on the provided cost field; any unrecorded overhead or indirect costs are not captured.

## Conclusion
Overall ticket volume and cost are moderate, with Team Beta driving the majority of labor expense. Chat channels resolve tickets more slowly, and email tickets experience a substantially higher reopening rate, indicating potential quality concerns. A small subset of high‑cost, low‑satisfaction tickets warrants targeted review. Agent workload is fairly distributed, though the top agent handles a noticeable share of tickets. Addressing data cleaning gaps and missing satisfaction data will improve future analyses.
