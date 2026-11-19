# Support Operations Report: Cost, Speed, Reopening, Satisfaction and Agent Concentration

Across 347 cleaned support tickets, mean resolution time was 75.19 minutes and total labor cost reached $27,422.90. Team Beta carries the highest labor cost at $10,247.36, while chat is the slowest channel at 83.04 mean minutes. Email tickets reopen at 17.24% versus 7.84% for chat, a 119.83% relative increase. A small segment of 12 high-cost, low-satisfaction tickets reopens at 8.33%. Median resolution is 65 minutes, satisfaction averages 4.15 (19 scores missing), and workload is spread across 18 agents, with the top agent handling 26 tickets (7.49% share).

## Key findings
- [q1] The cleaned dataset contains 347 tickets, with a mean resolution time of 75.19 minutes and a total labor cost of $27,422.90.
  - Reported values: ticket_count=347.0, mean_resolution_minutes=75.19, total_labor_cost=27422.9
- [q2] Total labor cost by team: Beta $10,247.36, Gamma $9,387.73, Alpha $7,787.81. Beta accounts for the most labor spend, Alpha the least.
  - Reported values: labor_cost_alpha=7787.81, labor_cost_beta=10247.36, labor_cost_gamma=9387.73
  - Ranking: Beta, Gamma, Alpha
- [q3] Mean resolution time by channel: chat 83.04 minutes, email 73.02 minutes, phone 69.25 minutes. Chat is the slowest channel and phone the fastest.
  - Reported values: resolution_email=73.02, resolution_chat=83.04, resolution_phone=69.25
  - Ranking: chat, email, phone
- [q4] Email tickets reopen at 17.24% versus 7.84% for chat, a relative increase of 119.83% for email compared with chat.
  - Reported values: reopen_rate_email_pct=17.24, reopen_rate_chat_pct=7.84, email_vs_chat_reopen_change_pct=119.83
  - Direction: increase
- [q5] 12 tickets combine labor cost of at least $100 with a satisfaction score of 2 or lower; this high-cost, low-satisfaction segment reopens at 8.33%.
  - Reported values: high_cost_low_sat_count=12.0, high_cost_low_sat_reopen_pct=8.33
- [q6] Resolution time has a median of 65 minutes and a sample standard deviation of 51.93 minutes, indicating wide spread. Mean satisfaction is 4.15, with 19 tickets missing a satisfaction score.
  - Reported values: resolution_median=65.0, resolution_std=51.93, satisfaction_mean=4.15, satisfaction_missing_count=19.0
- [q7] 18 unique agents handled the tickets; the busiest single agent handled 26 tickets, a 7.49% share of all tickets, indicating workload is broadly distributed rather than concentrated.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=26.0, top_agent_ticket_share_pct=7.49

## Limitations
- 19 tickets are missing satisfaction scores; the 4.15 mean excludes them and could be biased if missingness is not random.
- The high-cost, low-satisfaction segment contains only 12 tickets, so its 8.33% reopen rate is based on a small sample and is unstable.
- The reopen comparison covers email and chat only; no verified reopen rate was computed for phone.
- Team labor costs are totals and have not been normalized per ticket, so differences may reflect ticket volume rather than efficiency.
- The export is a single snapshot with no time dimension in the verified metrics, so trends and seasonality cannot be assessed.

## Conclusion
Support operations handled 347 tickets at $27,422.90 total labor cost, with Beta the costliest team and chat the slowest channel. The clearest action signal is email's 17.24% reopen rate, well above chat's 7.84%; reviewing email resolution quality should be prioritized. Satisfaction is healthy at 4.15 and agent workload shows no risky concentration, with the top agent at just 7.49% of tickets.
