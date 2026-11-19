# Support Operations Ticket Analysis Report

The analysis of 235 support tickets reveals overall performance metrics, cost distribution across teams, channel‑specific resolution times, and agent workload concentration. Team Gamma bears the highest labor cost, chat tickets resolve slower than email or phone, and the email channel shows a markedly higher reopen rate compared to chat. A small subset of high‑cost tickets also suffers low satisfaction. The data set includes 18 agents, with the top agent handling 8.5% of all tickets.

## Key findings
- [q1] The dataset contains 235 tickets with an average resolution time of 75.30 minutes, incurring a total labor cost of $18,704.10.
  - Reported values: ticket_count=235.0, mean_resolution_minutes=75.3, total_labor_cost=18704.1
- [q2] Team Gamma incurred the highest labor cost, followed by Beta and Alpha.
  - Reported values: labor_cost_alpha=5254.6, labor_cost_beta=6466.66, labor_cost_gamma=6982.84
  - Ranking: Gamma, Beta, Alpha
- [q3] Chat tickets have the longest average resolution time, then email, then phone.
  - Reported values: resolution_email=73.48, resolution_chat=83.54, resolution_phone=67.89
  - Ranking: chat, email, phone
- [q4] The email channel’s reopen rate is 92.68% higher than chat, indicating an increase.
  - Reported values: reopen_rate_email_pct=19.83, reopen_rate_chat_pct=10.29, email_vs_chat_reopen_change_pct=92.68
  - Direction: increase
- [q5] Eight tickets cost $100 or more and received low satisfaction (≤2); 12.5% of these were reopened.
  - Reported values: high_cost_low_sat_count=8.0, high_cost_low_sat_reopen_pct=12.5
- [q6] The median resolution time is 66 minutes with a standard deviation of 53.34 minutes. Average satisfaction score is 4.13, with 10 tickets missing a score.
  - Reported values: resolution_median=66.0, resolution_std=53.34, satisfaction_mean=4.13, satisfaction_missing_count=10.0
- [q7] There are 18 distinct agents; the most active agent handled 20 tickets, representing 8.51% of all tickets.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=20.0, top_agent_ticket_share_pct=8.51

## Limitations
- The cleaning stage failed, so any remaining data quality issues (e.g., duplicate rows, inconsistent timestamps) may affect the metrics.
- Satisfaction scores are missing for 10 tickets, which could bias the average satisfaction calculation.
- Cost and time figures are based on reported labor cost and resolution minutes; they do not account for indirect overhead or multi‑agent collaboration.

## Conclusion
Overall ticket volume is modest, with average resolution times under 1.5 hours but notable variation across channels. Team Gamma’s higher labor cost suggests either higher ticket complexity or pricing differences. Chat handling is slower, and the email channel shows a substantially higher reopen rate, highlighting an area for process improvement. Agent workload is relatively balanced, though the top agent’s share (8.5%) warrants monitoring to avoid burnout. Addressing data cleaning gaps and missing satisfaction scores will improve future analyses.
