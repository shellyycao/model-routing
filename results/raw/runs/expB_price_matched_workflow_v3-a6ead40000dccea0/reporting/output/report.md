# Support Operations Report: Cost, Speed, Reopening, Satisfaction and Agent Concentration

Analysis of 347 cleaned support tickets shows a total labor cost of $27,422.90 and a mean resolution time of 75.2 minutes against a median of 65.0. Team Beta carries the highest labor cost ($10,247.36), chat is the slowest channel (83.0 minutes mean), and email reopens 119.8% more often than chat (17.24% vs 7.84%). Satisfaction averages 4.15 out of 5, with 19 scores missing. Workload is well distributed across 18 agents, with the busiest agent handling just 7.49% of tickets. Twelve high-cost, low-satisfaction tickets were flagged for targeted review.

## Key findings
- [q1] The cleaned dataset contains 347 tickets, with a mean resolution time of 75.2 minutes and a total labor cost of $27,422.90.
  - Reported values: ticket_count=347.0, mean_resolution_minutes=75.19308357348703, total_labor_cost=27422.9
- [q2] Team Beta accounts for the highest total labor cost at $10,247.36, followed by Gamma ($9,387.73) and Alpha ($7,787.81); Beta exceeds Alpha by $2,459.55.
  - Reported values: labor_cost_alpha=7787.81, labor_cost_beta=10247.36, labor_cost_gamma=9387.73
  - Ranking: Beta, Gamma, Alpha
  - Derived difference(labor_cost_beta, labor_cost_alpha): 2459.55
- [q3] Chat is the slowest channel with a mean resolution time of 83.0 minutes, ahead of email (73.0 minutes) and phone (69.3 minutes); chat runs about 13.8 minutes slower than phone.
  - Reported values: resolution_email=73.01724137931035, resolution_chat=83.03921568627452, resolution_phone=69.25352112676056
  - Ranking: chat, email, phone
  - Derived difference(resolution_chat, resolution_phone): 13.8
- [q4] Email tickets reopen at 17.24% versus 7.84% for chat, an increase of 119.8% in relative terms (about 9.4 percentage points higher), making email the reopening hotspot.
  - Reported values: reopen_rate_email_pct=17.24137931034483, reopen_rate_chat_pct=7.8431372549019605, email_vs_chat_reopen_change_pct=119.82758620689657
  - Direction: increase
  - Derived difference(reopen_rate_email_pct, reopen_rate_chat_pct): 9.4
- [q5] Twelve tickets combine a labor cost of at least $100 with a satisfaction score of 2 or lower (3.46% of all tickets); this segment's reopen rate is 8.33%, well below the email channel rate of 17.24%.
  - Reported values: high_cost_low_sat_count=12.0, high_cost_low_sat_reopen_pct=8.333333333333332
  - Derived share(high_cost_low_sat_count, ticket_count): 3.46
- [q6] Resolution time is right-skewed: the median of 65.0 minutes sits below the mean of 75.2, with a standard deviation of 51.9 minutes indicating wide spread. Satisfaction averages 4.15 out of 5, and 19 scores are missing (5.48% of tickets).
  - Reported values: resolution_median=65.0, resolution_std=51.92574910613114, satisfaction_mean=4.152439024390244, satisfaction_missing_count=19.0
  - Derived share(satisfaction_missing_count, ticket_count): 5.48
- [q7] Tickets are spread across 18 distinct agents, and the busiest agent handled 26 tickets, only 7.49% of total volume, indicating low concentration and low key-person risk.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=26.0, top_agent_ticket_share_pct=7.492795389048991

## Limitations
- Satisfaction scores are missing for 19 tickets, so satisfaction-related results reflect only respondents and may be subject to non-response bias.
- Findings are descriptive; no statistical significance testing was performed, so differences such as the email-vs-chat reopen gap may partly reflect chance.
- The data is a single export snapshot with no time dimension, so trends, seasonality and the effect of any interventions cannot be assessed.
- The high-cost, low-satisfaction segment contains only 12 tickets, so its reopen rate is based on a small sample and should be read cautiously.
- Costs are analyzed as totals and means only; drivers within teams or channels (e.g., ticket mix or complexity) were not broken out.

## Conclusion
Operations look broadly healthy: satisfaction is high at 4.15 out of 5 and workload is evenly spread across 18 agents. The priorities are to investigate email's elevated reopen rate (17.24%), reduce chat resolution times (83.0 minutes mean), and review the 12 high-cost, low-satisfaction tickets. Tackling email reopening offers the largest single measurable efficiency gain.
