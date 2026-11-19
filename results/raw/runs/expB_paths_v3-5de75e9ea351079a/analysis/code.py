import os
import json
import pandas as pd
import numpy as np

# Read cleaned data
input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
df = pd.read_csv(input_path, dtype={
    'ticket_id': str,
    'agent_id': str,
    'team': str,
    'region': str,
    'channel': str,
    'resolution_minutes': int,
    'reopened': int,
    'hourly_cost': float,
    'labor_cost': float
})

# satisfaction_score is nullable int
df['satisfaction_score'] = pd.to_numeric(df['satisfaction_score'], errors='coerce')

# Q1: Overall metrics
ticket_count = len(df)
mean_resolution_minutes = df['resolution_minutes'].mean()
total_labor_cost = df['labor_cost'].sum()

# Q2: Team labor costs
labor_cost_alpha = df.loc[df['team'] == 'Alpha', 'labor_cost'].sum()
labor_cost_beta = df.loc[df['team'] == 'Beta', 'labor_cost'].sum()
labor_cost_gamma = df.loc[df['team'] == 'Gamma', 'labor_cost'].sum()

# Q3: Channel mean resolution minutes
resolution_email = df.loc[df['channel'] == 'email', 'resolution_minutes'].mean()
resolution_chat = df.loc[df['channel'] == 'chat', 'resolution_minutes'].mean()
resolution_phone = df.loc[df['channel'] == 'phone', 'resolution_minutes'].mean()

# Q4: Reopening rates by channel
email_df = df[df['channel'] == 'email']
chat_df = df[df['channel'] == 'chat']

reopen_rate_email_pct = email_df['reopened'].mean() * 100
reopen_rate_chat_pct = chat_df['reopened'].mean() * 100
email_vs_chat_reopen_change_pct = (reopen_rate_email_pct - reopen_rate_chat_pct) / reopen_rate_chat_pct * 100

# Q5: High-cost low-satisfaction segment
high_cost_low_sat = df[(df['labor_cost'] >= 100) & (df['satisfaction_score'].notna()) & (df['satisfaction_score'] <= 2)]
high_cost_low_sat_count = len(high_cost_low_sat)
if high_cost_low_sat_count > 0:
    high_cost_low_sat_reopen_pct = high_cost_low_sat['reopened'].mean() * 100
else:
    high_cost_low_sat_reopen_pct = 0.0

# Q6: Distribution metrics
resolution_median = df['resolution_minutes'].median()
resolution_std = df['resolution_minutes'].std(ddof=1)  # sample std
satisfaction_mean = df['satisfaction_score'].mean()  # mean of non-missing
satisfaction_missing_count = df['satisfaction_score'].isna().sum()

# Q7: Agent concentration
unique_agent_count = df['agent_id'].nunique()
agent_ticket_counts = df['agent_id'].value_counts()
top_agent_ticket_count = int(agent_ticket_counts.iloc[0])
top_agent_ticket_share_pct = top_agent_ticket_count / ticket_count * 100

# Build findings dict
findings = {
    "ticket_count": float(ticket_count),
    "mean_resolution_minutes": float(mean_resolution_minutes),
    "total_labor_cost": float(total_labor_cost),
    "labor_cost_alpha": float(labor_cost_alpha),
    "labor_cost_beta": float(labor_cost_beta),
    "labor_cost_gamma": float(labor_cost_gamma),
    "resolution_email": float(resolution_email),
    "resolution_chat": float(resolution_chat),
    "resolution_phone": float(resolution_phone),
    "reopen_rate_email_pct": float(reopen_rate_email_pct),
    "reopen_rate_chat_pct": float(reopen_rate_chat_pct),
    "email_vs_chat_reopen_change_pct": float(email_vs_chat_reopen_change_pct),
    "high_cost_low_sat_count": float(high_cost_low_sat_count),
    "high_cost_low_sat_reopen_pct": float(high_cost_low_sat_reopen_pct),
    "resolution_median": float(resolution_median),
    "resolution_std": float(resolution_std),
    "satisfaction_mean": float(satisfaction_mean),
    "satisfaction_missing_count": float(satisfaction_missing_count),
    "unique_agent_count": float(unique_agent_count),
    "top_agent_ticket_count": float(top_agent_ticket_count),
    "top_agent_ticket_share_pct": float(top_agent_ticket_share_pct)
}

# Validate all values are finite numbers
for k, v in findings.items():
    if not isinstance(v, (int, float)) or not np.isfinite(v):
        raise ValueError(f"Non-finite value for metric '{k}': {v}")

# Write findings.json
output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
with open(output_path, 'w') as f:
    json.dump(findings, f)

print("findings.json written successfully.")
print(json.dumps(findings, indent=2))
