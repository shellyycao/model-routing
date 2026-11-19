# Support Operations Analysis Report

Analysis of 347 support tickets reveals a total labor cost of $27,422.84 and a mean resolution time of ~75 minutes. Team Beta incurs the highest labor cost, phone is the fastest channel, and email tickets reopen at more than twice the rate of chat tickets. A small high-cost, low-satisfaction segment warrants targeted intervention, and workload is reasonably distributed across 18 agents.

## Key findings
- [q1] The dataset contains 347 tickets with a mean resolution time of 75.2 minutes and a total labor cost of $27,422.84.
  - Reported values: ticket_count=347.0, mean_resolution_minutes=75.193084, total_labor_cost=27422.84
- [q2] Team Beta incurred the highest labor cost at $10,247.32, followed by Gamma at $9,387.74 and Alpha at $7,787.78.
  - Reported values: labor_cost_alpha=7787.78, labor_cost_beta=10247.32, labor_cost_gamma=9387.74
  - Ranking: Beta, Gamma, Alpha
- [q3] Chat had the longest mean resolution time at 83.0 minutes, followed by email at 73.0 minutes; phone was fastest at 69.3 minutes.
  - Reported values: resolution_email=73.017241, resolution_chat=83.039216, resolution_phone=69.253521
  - Ranking: chat, email, phone
- [q4] Email tickets have a reopening rate of 17.2% versus 7.8% for chat—an increase of ~119.8% relative to chat, indicating email resolutions are far less durable.
  - Reported values: reopen_rate_email_pct=17.241379, reopen_rate_chat_pct=7.843137, email_vs_chat_reopen_change_pct=119.827586
  - Direction: increase
  - Derived pct_change(reopen_rate_email_pct, reopen_rate_chat_pct): 119.827586
- [q5] 12 tickets meet the high-cost (≥$100), low-satisfaction (score ≤2) criteria; of these, 8.3% were reopened, suggesting this segment has moderate but notable rework risk.
  - Reported values: high_cost_low_sat_count=12.0, high_cost_low_sat_reopen_pct=8.333333
- [q6] Resolution time has a median of 65 minutes and a standard deviation of 51.9 minutes, indicating a right-skewed distribution. Mean satisfaction (where recorded) is 4.15 out of 5, with 19 tickets missing a satisfaction score.
  - Reported values: resolution_median=65.0, resolution_std=51.925749, satisfaction_mean=4.152439, satisfaction_missing_count=19.0
- [q7] 18 distinct agents handled the 347 tickets. The busiest single agent handled 26 tickets, representing a 7.5% share of total volume—suggesting workload is reasonably distributed with no severe concentration.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=26.0, top_agent_ticket_share_pct=7.492795
  - Derived share(top_agent_ticket_count, ticket_count): 7.492795

## Limitations
- 19 tickets are missing satisfaction scores, which may introduce bias into the satisfaction mean if missingness is non-random (e.g., correlated with poor outcomes).
- Labor cost is derived from logged resolution minutes and assumed hourly rates; inaccuracies in time-tracking or rate assumptions would propagate into all cost metrics.
- The dataset represents a single export snapshot; trends over time cannot be assessed without longitudinal data.
- Reopening rates are computed per channel but not controlled for ticket complexity or priority, so channel differences may partly reflect ticket-mix rather than channel quality.
- Agent concentration analysis uses ticket count only; tickets vary in complexity and duration, so count-based share may understate or overstate true workload concentration.

## Conclusion
Overall support performance is solid—satisfaction averages 4.15 and the top agent holds only 7.5% of volume—but two areas need attention: email's reopening rate is 120% higher than chat's, and Team Beta accounts for the largest labor spend at $10,247. Reducing email rework and investigating Beta's cost drivers should be the immediate operational priorities.
