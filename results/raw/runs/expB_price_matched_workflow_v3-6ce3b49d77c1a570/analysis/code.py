import os
import json
import pandas as pd
import numpy as np

# Read cleaned data
input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
df = pd.read_csv(input_path)

# Ensure correct dtypes
df['resolution_minutes'] = pd.to_numeric(df['resolution_minutes'], errors='coerce')
df['labor_cost'] = pd.to_numeric(df['labor_cost'], errors='coerce')
df['satisfaction_score'] = pd.to_numeric(df['satisfaction_score'], errors='coerce')
df['reopened'] = pd.to_numeric(df['reopened'], errors='coerce')
df['hourly_cost'] = pd.to_numeric(df['hourly_cost'], errors='coerce')

findings = {}

# q1: Overall metrics
findings['ticket_count'] = float(len(df))
findings['mean_resolution_minutes'] = float(df['resolution_minutes'].mean())
findings['total_labor_cost'] = float(df['labor_cost'].sum())

# q2: Team comparison - total labor_cost per team
team_costs = df.groupby('team')['labor_cost'].sum()
findings['labor_cost_alpha'] = float(team_costs.get('Alpha', 0.0))
findings['labor_cost_beta'] = float(team_costs.get('Beta', 0.0))
findings['labor_cost_gamma'] = float(team_costs.get('Gamma', 0.0))

# q3: Channel comparison - mean resolution_minutes by channel
channel_res = df.groupby('channel')['resolution_minutes'].mean()
findings['resolution_email'] = float(channel_res.get('email', np.nan))
findings['resolution_chat'] = float(channel_res.get('chat', np.nan))
findings['resolution_phone'] = float(channel_res.get('phone', np.nan))

# q4: Reopening rates by channel
email_df = df[df['channel'] == 'email']
chat_df = df[df['channel'] == 'chat']

reopen_rate_email = float(email_df['reopened'].mean() * 100) if len(email_df) > 0 else 0.0
reopen_rate_chat = float(chat_df['reopened'].mean() * 100) if len(chat_df) > 0 else 0.0

findings['reopen_rate_email_pct'] = reopen_rate_email
findings['reopen_rate_chat_pct'] = reopen_rate_chat
findings['email_vs_chat_reopen_change_pct'] = float((reopen_rate_email - reopen_rate_chat) / reopen_rate_chat * 100) if reopen_rate_chat != 0 else 0.0

# q5: High-cost low-satisfaction segment
high_cost_low_sat = df[(df['labor_cost'] >= 100) & (df['satisfaction_score'].notna()) & (df['satisfaction_score'] <= 2)]
findings['high_cost_low_sat_count'] = float(len(high_cost_low_sat))
findings['high_cost_low_sat_reopen_pct'] = float(high_cost_low_sat['reopened'].mean() * 100) if len(high_cost_low_sat) > 0 else 0.0

# q6: Distribution metrics
findings['resolution_median'] = float(df['resolution_minutes'].median())
findings['resolution_std'] = float(df['resolution_minutes'].std(ddof=1))
findings['satisfaction_mean'] = float(df['satisfaction_score'].mean())
findings['satisfaction_missing_count'] = float(df['satisfaction_score'].isna().sum())

# q7: Agent concentration
findings['unique_agent_count'] = float(df['agent_id'].nunique())
agent_ticket_counts = df['agent_id'].value_counts()
top_agent_ticket_count = float(agent_ticket_counts.iloc[0]) if len(agent_ticket_counts) > 0 else 0.0
findings['top_agent_ticket_count'] = top_agent_ticket_count
findings['top_agent_ticket_share_pct'] = float(top_agent_ticket_count / findings['ticket_count'] * 100) if findings['ticket_count'] > 0 else 0.0

# Validate all values are finite numbers
for key, val in findings.items():
    if not isinstance(val, (int, float)) or not np.isfinite(val):
        raise ValueError(f"Non-finite or invalid value for metric '{key}': {val}")

# Write findings.json
output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
with open(output_path, 'w') as f:
    json.dump(findings, f)

print("findings.json written successfully.")
print(json.dumps(findings, indent=2))
