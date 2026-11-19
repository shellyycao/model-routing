# Support Operations Analysis Report

Analysis of 347 support tickets reveals a total labor cost of $27,422.90 and a mean resolution time of ~75.2 minutes. Team Beta carries the highest labor cost, phone channel resolves tickets fastest, and email tickets reopen at roughly twice the rate of chat tickets. A small high-cost, low-satisfaction segment warrants targeted intervention, and moderate agent concentration suggests manageable workload distribution.

## Key findings
- [q1] The dataset contains 347 tickets with a mean resolution time of 75.2 minutes and a total labor cost of $27,422.90.
  - Reported values: ticket_count=347.0, mean_resolution_minutes=75.19308357348703, total_labor_cost=27422.9
- [q2] Team Beta incurred the highest labor cost at $10,247.36, followed by Gamma at $9,387.73 and Alpha at $7,787.81. Beta's cost exceeds Alpha's by $2,459.55.
  - Reported values: labor_cost_alpha=7787.81, labor_cost_beta=10247.36, labor_cost_gamma=9387.73
  - Ranking: Beta, Gamma, Alpha
  - Derived difference(labor_cost_beta, labor_cost_alpha): 2459.55
- [q3] Phone channel resolves tickets fastest at 69.3 minutes on average, followed by email at 73.0 minutes and chat at 83.0 minutes. Chat is the slowest channel.
  - Reported values: resolution_email=73.01724137931035, resolution_chat=83.03921568627452, resolution_phone=69.25352112676056
  - Ranking: chat, email, phone
- [q4] Email tickets reopen at 17.2% versus 7.8% for chat, representing an increase of ~119.8% relative to the chat reopen rate — email tickets are more than twice as likely to be reopened.
  - Reported values: reopen_rate_email_pct=17.24137931034483, reopen_rate_chat_pct=7.8431372549019605, email_vs_chat_reopen_change_pct=119.82758620689657
  - Direction: increase
  - Derived pct_change(reopen_rate_email_pct, reopen_rate_chat_pct): 119.83
- [q5] 12 tickets meet the high-cost (≥$100) and low-satisfaction (score ≤2) criteria. Of these, 8.3% were reopened, indicating a small but notable at-risk segment requiring focused follow-up.
  - Reported values: high_cost_low_sat_count=12.0, high_cost_low_sat_reopen_pct=8.333333333333332
- [q6] Resolution time has a median of 65.0 minutes and a standard deviation of 51.9 minutes, indicating a right-skewed distribution. Mean satisfaction among scored tickets is 4.15 out of 5, with 19 tickets missing a satisfaction score.
  - Reported values: resolution_median=65.0, resolution_std=51.92574910613114, satisfaction_mean=4.152439024390244, satisfaction_missing_count=19.0
- [q7] 18 distinct agents handled the 347 tickets. The busiest single agent handled 26 tickets, representing 7.5% of total volume — a moderate concentration with no single agent dominating workload.
  - Reported values: unique_agent_count=18.0, top_agent_ticket_count=26.0, top_agent_ticket_share_pct=7.492795389048991
  - Derived share(top_agent_ticket_count, ticket_count): 7.49

## Limitations
- 19 tickets are missing satisfaction scores, which may introduce bias into the satisfaction mean if missingness is non-random (e.g., correlated with poor outcomes).
- The high-cost low-satisfaction segment contains only 12 tickets; conclusions drawn from this group have limited statistical power.
- Labor cost is derived from a joined roster; any agents absent from the roster or with incorrect rates would distort team-level cost comparisons.
- The dataset represents a single export snapshot with no time dimension, so trends over time cannot be assessed.
- Reopen rates are based on a binary flag and do not capture multiple reopenings, potentially understating chronic resolution failures.

## Conclusion
Support operations are broadly healthy — satisfaction averages 4.15 and the top agent handles only 7.5% of tickets — but two areas merit action: the email channel's reopen rate is ~120% higher than chat's, and Team Beta's labor cost leads all teams at $10,247. Investigating email resolution quality and Beta's cost drivers should be prioritized, alongside outreach to the 12 high-cost, low-satisfaction customers.
