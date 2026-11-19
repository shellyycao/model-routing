# Support Operations Ticket Analysis Report

The analysis of 347 support tickets reveals overall moderate resolution times (average 75.2 minutes) and a total labor cost of $27,422.84. Team labor costs differ, with Team Beta incurring the highest cost. Resolution speed varies by channel, being slowest on chat. Email tickets experience a markedly higher reopen rate than chat. A small subset of high‑cost, low‑satisfaction tickets (12) represents about 3.5% of all tickets. Ticket handling is spread across 18 agents, with the top agent accounting for 7.5% of the workload.

## Key findings
- [q1] The dataset contains 347 tickets with an average resolution time of 75.2 minutes and a total labor cost of $27,422.84.
  - Reported values: ticket_count=347.0, mean_resolution_minutes=75.193084, total_labor_cost=27422.84
- [q2] Team labor costs vary, with Beta highest ($10,247.32), Gamma middle ($9,387.74), and Alpha lowest ($7,787.78). Beta's cost exceeds Alpha by $2,459.54.
  - Reported values: labor_cost_alpha=7787.78, labor_cost_beta=10247.32, labor_cost_gamma=9387.74
  - Ranking: Beta, Gamma, Alpha
  - Derived difference(labor_cost_beta, labor_cost_alpha): 2459.54
- [q3] Average resolution time is fastest on phone (69.3 min), slower on email (73.0 min), and slowest on chat (83.0 min). Chat is about 10.0 minutes slower than email.
  - Reported values: resolution_email=73.017241, resolution_chat=83.039216, resolution_phone=69.253521
  - Ranking: chat, email, phone
  - Derived difference(resolution_chat, resolution_email): 10.02
- [q4] Email tickets have a 17.2% reopen rate, which is 119.8% higher than the 7.8% rate for chat, indicating a substantial increase.
  - Reported values: reopen_rate_email_pct=17.241379, reopen_rate_chat_pct=7.843137, email_vs_chat_reopen_change_pct=119.827586
  - Direction: increase
- [q5] There are 12 high‑cost, low‑satisfaction tickets, representing 3.5% of all tickets, with an 8.3% reopen rate.
  - Reported values: high_cost_low_sat_count=12.0, high_cost_low_sat_reopen_pct=8.333333
  - Derived share(high_cost_low_sat_count, ticket_count): 3.46
- [q6] The median resolution time is 65 minutes with a standard deviation of 51.9 minutes. Average satisfaction score is 4.15, and 19 tickets lack a satisfaction rating.
  - Reported values: resolution_median=65.0, resolution_std=51.925749, satisfaction_mean=4.152439, satisfaction_missing_count=19.0
- [q7] Tickets were handled by 18 distinct agents; the busiest agent resolved 26 tickets, accounting for 7.5% of all tickets.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=26.0, top_agent_ticket_share_pct=7.492795

## Limitations
- The analysis relies on a single export snapshot; trends over time cannot be assessed.
- Satisfaction scores are missing for 19 tickets, which may bias the average satisfaction metric.
- Cost figures are limited to labor cost; other expenses (e.g., software, overhead) are not captured.

## Conclusion
Overall ticket volume and cost are moderate, but notable differences exist across teams and channels. Chat handling is slower and incurs higher reopen rates for email, suggesting process improvements. The small high‑cost, low‑satisfaction segment warrants targeted attention. Monitoring agent workload distribution can help balance capacity and maintain service quality.
