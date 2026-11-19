# Support Operations Ticket Analysis Report

The analysis of 347 support tickets reveals overall cost and performance metrics, notable differences across teams and channels, and areas of concern such as high‑cost tickets with low satisfaction. Team Beta incurs the highest labor cost, chat tickets take the longest to resolve, and email tickets have a substantially higher reopen rate than chat. A small segment of expensive tickets shows low satisfaction, and agent workload is relatively dispersed with the top agent handling only 7.5% of tickets.

## Key findings
- [q1] The dataset contains 347 tickets, with an average resolution time of 75.2 minutes and total labor cost of $27,422.9.
  - Reported values: ticket_count=347.0, mean_resolution_minutes=75.19308357348703, total_labor_cost=27422.9
- [q2] Team labor costs differ markedly: Beta $10,247.36, Gamma $9,387.73, Alpha $7,787.81.
  - Reported values: labor_cost_alpha=7787.81, labor_cost_beta=10247.36, labor_cost_gamma=9387.73
  - Ranking: Beta, Gamma, Alpha
- [q3] Average resolution time varies by channel: chat 83.04 minutes, email 73.02 minutes, phone 69.25 minutes.
  - Reported values: resolution_email=73.01724137931035, resolution_chat=83.03921568627452, resolution_phone=69.25352112676056
  - Ranking: chat, email, phone
- [q4] Reopen rate for email tickets is 17.24%, for chat 7.84%, representing a 119.83% higher reopen rate for email versus chat.
  - Reported values: reopen_rate_email_pct=17.24137931034483, reopen_rate_chat_pct=7.8431372549019605, email_vs_chat_reopen_change_pct=119.82758620689657
  - Direction: increase
- [q5] There are 12 high‑cost, low‑satisfaction tickets, and 8.33% of them were reopened.
  - Reported values: high_cost_low_sat_count=12.0, high_cost_low_sat_reopen_pct=8.333333333333332
- [q6] Resolution time median is 65 minutes with a standard deviation of 51.93 minutes. Average satisfaction score is 4.15, with 19 tickets missing a score.
  - Reported values: resolution_median=65.0, resolution_std=51.92574910613114, satisfaction_mean=4.152439024390244, satisfaction_missing_count=19.0
- [q7] Tickets were handled by 18 distinct agents; the most active agent handled 26 tickets, representing 7.49% of all tickets.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=26.0, top_agent_ticket_share_pct=7.492795389048991

## Limitations
- The cleaning stage failed, so residual data quality issues (e.g., inconsistent casing, missing values) may remain.
- Satisfaction scores are missing for 19 tickets, limiting the completeness of satisfaction analysis.
- All monetary values are in the original currency without inflation adjustment.
- The analysis is based on a single export snapshot and may not reflect longer‑term trends.

## Conclusion
Overall ticket volume is modest, with average resolution times under 1.5 hours and total labor cost of $27.4k. Team Beta drives the bulk of labor expense, while chat channels are the slowest to resolve. Email tickets exhibit a markedly higher propensity to be reopened, suggesting potential quality issues. A small high‑cost, low‑satisfaction segment warrants targeted improvement. Agent workload is fairly balanced, with the top agent handling less than 8% of tickets. Addressing data cleaning gaps and missing satisfaction data will improve future analyses.
