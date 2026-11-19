import os
import json
import pandas as pd
import numpy as np

# Define input and output paths
input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

# Read cleaned data
df = pd.read_csv(input_path)

# Initialize results dictionary
results = {}

# q1: Overall metrics
results['ticket_count'] = len(df)
results['mean_resolution_minutes'] = df['resolution_minutes'].mean()
results['total_labor_cost'] = df['labor_cost'].sum()

# q2: Team comparison labor cost
team_costs = df.groupby('team')['labor_cost'].sum()
results['labor_cost_alpha'] = team_costs.get('Alpha', 0.0)
results['labor_cost_beta'] = team_costs.get('Beta', 0.0)
results['labor_cost_gamma'] = team_costs.get('Gamma', 0.0)

# q3: Channel comparison mean resolution minutes
channel_resolution = df.groupby('channel')['resolution_minutes'].mean()
results['resolution_email'] = channel_resolution.get('email', np.nan)
results['resolution_chat'] = channel_resolution.get('chat', np.nan)
results['resolution_phone'] = channel_resolution.get('phone', np.nan)

# q4: Reopening rates for email and chat
email_tickets = df[df['channel'] == 'email']
chat_tickets = df[df['channel'] == 'chat']

email_reopen_rate = email_tickets['reopened'].mean() * 100 if len(email_tickets) > 0 else np.nan
chat_reopen_rate = chat_tickets['reopened'].mean() * 100 if len(chat_tickets) > 0 else np.nan

results['reopen_rate_email_pct'] = email_reopen_rate
results['reopen_rate_chat_pct'] = chat_reopen_rate

if chat_reopen_rate is not np.nan and chat_reopen_rate != 0 and email_reopen_rate is not np.nan:
    results['email_vs_chat_reopen_change_pct'] = (email_reopen_rate - chat_reopen_rate) / chat_reopen_rate * 100
else:
    results['email_vs_chat_reopen_change_pct'] = np.nan

# q5: High-cost low-satisfaction segment
high_cost_low_sat = df[(df['labor_cost'] >= 100) & (df['satisfaction_score'].notna()) & (df['satisfaction_score'] <= 2)]
results['high_cost_low_sat_count'] = len(high_cost_low_sat)
results['high_cost_low_sat_reopen_pct'] = high_cost_low_sat['reopened'].mean() * 100 if len(high_cost_low_sat) > 0 else np.nan

# q6: Distribution metrics
results['resolution_median'] = df['resolution_minutes'].median()
results['resolution_std'] = df['resolution_minutes'].std(ddof=1)
results['satisfaction_mean'] = df['satisfaction_score'].mean() # .mean() skips NA automatically
results['satisfaction_missing_count'] = df['satisfaction_score'].isna().sum()

# q7: Agent concentration
results['unique_agent_count'] = df['agent_id'].nunique()
agent_counts = df['agent_id'].value_counts()
results['top_agent_ticket_count'] = agent_counts.iloc[0] if len(agent_counts) > 0 else 0
if results['ticket_count'] > 0:
    results['top_agent_ticket_share_pct'] = results['top_agent_ticket_count'] / results['ticket_count'] * 100
else:
    results['top_agent_ticket_share_pct'] = np.nan

# Handle NaN/Inf values to ensure valid JSON output
for key, value in results.items():
    if isinstance(value, float):
        if np.isnan(value) or np.isinf(value):
            results[key] = None

# Write results to JSON
with open(output_path, 'w') as f:
    json.dump(results, f)
