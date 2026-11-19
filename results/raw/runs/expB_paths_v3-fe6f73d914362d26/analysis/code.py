import os
import pandas as pd
import numpy as np

# Read the cleaned data
input_dir = os.environ['INPUT_DIR']
output_dir = os.environ['OUTPUT_DIR']
df = pd.read_csv(os.path.join(input_dir, 'cleaned.csv'))

# Analysis
ticket_count = len(df)
mean_resolution_minutes = df['resolution_minutes'].mean()
total_labor_cost = df['labor_cost'].sum()

labor_cost_alpha = df[df['team'] == 'Alpha']['labor_cost'].sum()
labor_cost_beta = df[df['team'] == 'Beta']['labor_cost'].sum()
labor_cost_gamma = df[df['team'] == 'Gamma']['labor_cost'].sum()

resolution_email = df[df['channel'] == 'email']['resolution_minutes'].mean()
resolution_chat = df[df['channel'] == 'chat']['resolution_minutes'].mean()
resolution_phone = df[df['channel'] == 'phone']['resolution_minutes'].mean()

reopen_rate_email = df[df['channel'] == 'email']['reopened'].mean() * 100
reopen_rate_chat = df[df['channel'] == 'chat']['reopened'].mean() * 100
email_vs_chat_reopen_change_pct = (reopen_rate_email - reopen_rate_chat) / reopen_rate_chat * 100 if reopen_rate_chat!= 0 else 0

high_cost_low_sat = df[(df['labor_cost'] >= 100) & (df['satisfaction_score'].notna()) & (df['satisfaction_score'] <= 2)]
high_cost_low_sat_count = len(high_cost_low_sat)
high_cost_low_sat_reopen_pct = high_cost_low_sat['reopened'].mean() * 100

resolution_median = df['resolution_minutes'].median()
resolution_std = df['resolution_minutes'].std()
satisfaction_mean = df['satisfaction_score'].mean()
satisfaction_missing_count = df['satisfaction_score'].isna().sum()

unique_agent_count = df['agent_id'].nunique()
top_agent_ticket_count = df['agent_id'].value_counts().max()
top_agent_ticket_share_pct = (top_agent_ticket_count / ticket_count) * 100

# Prepare findings
findings = {
    'ticket_count': ticket_count,
    'mean_resolution_minutes': mean_resolution_minutes,
    'total_labor_cost': total_labor_cost,
    'labor_cost_alpha': labor_cost_alpha,
    'labor_cost_beta': labor_cost_beta,
    'labor_cost_gamma': labor_cost_gamma,
   'resolution_email': resolution_email,
    'resolution_chat': resolution_chat,
   'resolution_phone': resolution_phone,
   'reopen_rate_email_pct': reopen_rate_email,
   'reopen_rate_chat_pct': reopen_rate_chat,
    'email_vs_chat_reopen_change_pct': email_vs_chat_reopen_change_pct,
    'high_cost_low_sat_count': high_cost_low_sat_count,
    'high_cost_low_sat_reopen_pct': high_cost_low_sat_reopen_pct,
   'resolution_median': resolution_median,
   'resolution_std': resolution_std,
   'satisfaction_mean': satisfaction_mean,
    'satisfaction_missing_count': satisfaction_missing_count,
    'unique_agent_count': unique_agent_count,
    'top_agent_ticket_count': top_agent_ticket_count,
    'top_agent_ticket_share_pct': top_agent_ticket_share_pct
}

# Write findings to JSON
with open(os.path.join(output_dir, 'findings.json'), 'w') as f:
    import json
    json.dump(findings, f)

expected_artifacts = ['findings.json']
methods_description = 'This script performs analysis on the cleaned support ticket data to compute various metrics such as ticket count, mean resolution time, total labor cost, team-wise labor cost, channel-wise resolution time, reopening rates, high-cost low-satisfaction segment, and agent concentration metrics.'
