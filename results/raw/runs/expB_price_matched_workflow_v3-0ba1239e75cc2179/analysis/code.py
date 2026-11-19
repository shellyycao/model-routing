import os
import json
import pandas as pd
import numpy as np

# Define input and output paths
input_dir = os.environ["INPUT_DIR"]
output_dir = os.environ["OUTPUT_DIR"]
input_file = os.path.join(input_dir, "cleaned.csv")
output_file = os.path.join(output_dir, "findings.json")

# Read the cleaned data
df = pd.read_csv(input_file)

# Initialize results dictionary
results = {}

# q1: Overall metrics
results['ticket_count'] = len(df)
results['mean_resolution_minutes'] = df['resolution_minutes'].mean()
results['total_labor_cost'] = df['labor_cost'].sum()

# q2: Team comparison (labor cost by team)
team_costs = df.groupby('team')['labor_cost'].sum()
results['labor_cost_alpha'] = team_costs.get('Alpha', 0.0)
results['labor_cost_beta'] = team_costs.get('Beta', 0.0)
results['labor_cost_gamma'] = team_costs.get('Gamma', 0.0)

# q3: Channel comparison (mean resolution minutes by channel)
channel_resolution = df.groupby('channel')['resolution_minutes'].mean()
results['resolution_email'] = channel_resolution.get('email', np.nan)
results['resolution_chat'] = channel_resolution.get('chat', np.nan)
results['resolution_phone'] = channel_resolution.get('phone', np.nan)

# q4: Reopening change
email_df = df[df['channel'] == 'email']
chat_df = df[df['channel'] == 'chat']

email_reopen_rate = email_df['reopened'].mean() * 100 if len(email_df) > 0 else np.nan
chat_reopen_rate = chat_df['reopened'].mean() * 100 if len(chat_df) > 0 else np.nan

results['reopen_rate_email_pct'] = email_reopen_rate
results['reopen_rate_chat_pct'] = chat_reopen_rate

if pd.notna(chat_reopen_rate) and chat_reopen_rate != 0 and pd.notna(email_reopen_rate):
    results['email_vs_chat_reopen_change_pct'] = (email_reopen_rate - chat_reopen_rate) / chat_reopen_rate * 100
else:
    results['email_vs_chat_reopen_change_pct'] = np.nan

# q5: High-cost low-satisfaction segment
high_cost_low_sat_mask = (df['labor_cost'] >= 100) & (df['satisfaction_score'].notna()) & (df['satisfaction_score'] <= 2)
high_cost_low_sat_df = df[high_cost_low_sat_mask]

results['high_cost_low_sat_count'] = len(high_cost_low_sat_df)
if len(high_cost_low_sat_df) > 0:
    results['high_cost_low_sat_reopen_pct'] = high_cost_low_sat_df['reopened'].mean() * 100
else:
    results['high_cost_low_sat_reopen_pct'] = np.nan

# q6: Distribution
results['resolution_median'] = df['resolution_minutes'].median()
results['resolution_std'] = df['resolution_minutes'].std(ddof=1)  # sample standard deviation
results['satisfaction_mean'] = df['satisfaction_score'].mean()  # mean of non-missing values
results['satisfaction_missing_count'] = df['satisfaction_score'].isna().sum()

# q7: Agent concentration
results['unique_agent_count'] = df['agent_id'].nunique()
agent_ticket_counts = df['agent_id'].value_counts()
results['top_agent_ticket_count'] = agent_ticket_counts.iloc[0] if len(agent_ticket_counts) > 0 else 0
results['top_agent_ticket_share_pct'] = (results['top_agent_ticket_count'] / results['ticket_count'] * 100) if results['ticket_count'] > 0 else np.nan

# Handle NaN values for JSON serialization (replace with None, then to null, but instructions say finite numbers)
# The instructions say "finite number" and "No strings, lists, null, NaN or Infinity as values".
# However, if a metric cannot be computed (e.g. division by zero), NaN is the standard pandas result.
# Given the data provided, all metrics should be computable finite numbers.
# We ensure no NaN/Inf remains.
def check_finite(val):
    if isinstance(val, float):
        if np.isnan(val) or np.isinf(val):
            return None # Should not happen based on data, but good practice
    return val

final_results = {k: check_finite(v) for k, v in results.items()}

# Write to JSON
with open(output_file, 'w') as f:
    json.dump(final_results, f)
