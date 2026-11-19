import os
import json
import pandas as pd
import numpy as np

# Read cleaned data
input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
df = pd.read_csv(input_path)

# Ensure correct dtypes
df['resolution_minutes'] = pd.to_numeric(df['resolution_minutes'], errors='coerce')
df['satisfaction_score'] = pd.to_numeric(df['satisfaction_score'], errors='coerce')
df['reopened'] = pd.to_numeric(df['reopened'], errors='coerce')
df['labor_cost'] = pd.to_numeric(df['labor_cost'], errors='coerce')
df['hourly_cost'] = pd.to_numeric(df['hourly_cost'], errors='coerce')

# Q1: Overall metrics
ticket_count = float(len(df))
mean_resolution_minutes = float(df['resolution_minutes'].mean())
total_labor_cost = float(df['labor_cost'].sum())

# Q2: Team labor costs
labor_cost_alpha = float(df.loc[df['team'] == 'Alpha', 'labor_cost'].sum())
labor_cost_beta = float(df.loc[df['team'] == 'Beta', 'labor_cost'].sum())
labor_cost_gamma = float(df.loc[df['team'] == 'Gamma', 'labor_cost'].sum())

# Q3: Channel mean resolution minutes
resolution_email = float(df.loc[df['channel'] == 'email', 'resolution_minutes'].mean())
resolution_chat = float(df.loc[df['channel'] == 'chat', 'resolution_minutes'].mean())
resolution_phone = float(df.loc[df['channel'] == 'phone', 'resolution_minutes'].mean())

# Q4: Reopening rates by channel
email_tickets = df[df['channel'] == 'email']
chat_tickets = df[df['channel'] == 'chat']

reopen_rate_email_pct = float(email_tickets['reopened'].mean() * 100)
reopen_rate_chat_pct = float(chat_tickets['reopened'].mean() * 100)

# (email rate - chat rate) / chat rate * 100
email_vs_chat_reopen_change_pct = float((reopen_rate_email_pct - reopen_rate_chat_pct) / reopen_rate_chat_pct * 100)

# Q5: High-cost low-satisfaction segment
high_cost_low_sat = df[(df['labor_cost'] >= 100) & (df['satisfaction_score'].notna()) & (df['satisfaction_score'] <= 2)]
high_cost_low_sat_count = float(len(high_cost_low_sat))
if high_cost_low_sat_count > 0:
    high_cost_low_sat_reopen_pct = float(high_cost_low_sat['reopened'].mean() * 100)
else:
    high_cost_low_sat_reopen_pct = 0.0

# Q6: Distribution metrics
resolution_median = float(df['resolution_minutes'].median())
resolution_std = float(df['resolution_minutes'].std(ddof=1))
satisfaction_mean = float(df['satisfaction_score'].mean())
satisfaction_missing_count = float(df['satisfaction_score'].isna().sum())

# Q7: Agent concentration
unique_agent_count = float(df['agent_id'].nunique())
agent_ticket_counts = df['agent_id'].value_counts()
top_agent_ticket_count = float(agent_ticket_counts.iloc[0])
top_agent_ticket_share_pct = float(top_agent_ticket_count / ticket_count * 100)

# Assemble findings
findings = {
    "ticket_count": ticket_count,
    "mean_resolution_minutes": mean_resolution_minutes,
    "total_labor_cost": total_labor_cost,
    "labor_cost_alpha": labor_cost_alpha,
    "labor_cost_beta": labor_cost_beta,
    "labor_cost_gamma": labor_cost_gamma,
    "resolution_email": resolution_email,
    "resolution_chat": resolution_chat,
    "resolution_phone": resolution_phone,
    "reopen_rate_email_pct": reopen_rate_email_pct,
    "reopen_rate_chat_pct": reopen_rate_chat_pct,
    "email_vs_chat_reopen_change_pct": email_vs_chat_reopen_change_pct,
    "high_cost_low_sat_count": high_cost_low_sat_count,
    "high_cost_low_sat_reopen_pct": high_cost_low_sat_reopen_pct,
    "resolution_median": resolution_median,
    "resolution_std": resolution_std,
    "satisfaction_mean": satisfaction_mean,
    "satisfaction_missing_count": satisfaction_missing_count,
    "unique_agent_count": unique_agent_count,
    "top_agent_ticket_count": top_agent_ticket_count,
    "top_agent_ticket_share_pct": top_agent_ticket_share_pct
}

# Validate all values are finite numbers
for k, v in findings.items():
    if not isinstance(v, (int, float)) or not np.isfinite(v):
        raise ValueError(f"Non-finite or non-numeric value for key '{k}': {v}")

# Write output
output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
with open(output_path, 'w') as f:
    json.dump(findings, f)

print("findings.json written successfully.")
print(json.dumps(findings, indent=2))
