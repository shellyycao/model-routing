import os
import json
import pandas as pd
import numpy as np

# Define paths
input_dir = os.environ["INPUT_DIR"]
output_dir = os.environ["OUTPUT_DIR"]
input_file = os.path.join(input_dir, "cleaned.csv")
output_file = os.path.join(output_dir, "findings.json")

# Read cleaned data
df = pd.read_csv(input_file)

# Initialize results dictionary
results = {}

# Q1: Overall metrics
results["ticket_count"] = len(df)
results["mean_resolution_minutes"] = df["resolution_minutes"].mean()
results["total_labor_cost"] = df["labor_cost"].sum()

# Q2: Team comparison (labor cost by team)
labor_by_team = df.groupby("team")["labor_cost"].sum()
results["labor_cost_alpha"] = labor_by_team.get("Alpha", 0.0)
results["labor_cost_beta"] = labor_by_team.get("Beta", 0.0)
results["labor_cost_gamma"] = labor_by_team.get("Gamma", 0.0)

# Q3: Channel comparison (mean resolution minutes by channel)
resolution_by_channel = df.groupby("channel")["resolution_minutes"].mean()
results["resolution_email"] = resolution_by_channel.get("email", np.nan)
results["resolution_chat"] = resolution_by_channel.get("chat", np.nan)
results["resolution_phone"] = resolution_by_channel.get("phone", np.nan)

# Q4: Reopening change (email vs chat)
def calc_reopen_rate(channel_df):
    if len(channel_df) == 0:
        return np.nan
    return (channel_df["reopened"].sum() / len(channel_df)) * 100

email_df = df[df["channel"] == "email"]
chat_df = df[df["channel"] == "chat"]

reopen_rate_email = calc_reopen_rate(email_df)
reopen_rate_chat = calc_reopen_rate(chat_df)

results["reopen_rate_email_pct"] = reopen_rate_email
results["reopen_rate_chat_pct"] = reopen_rate_chat

if pd.isna(reopen_rate_chat) or reopen_rate_chat == 0:
    results["email_vs_chat_reopen_change_pct"] = np.nan
else:
    results["email_vs_chat_reopen_change_pct"] = ((reopen_rate_email - reopen_rate_chat) / reopen_rate_chat) * 100

# Q5: High-cost low-satisfaction segment
high_cost_low_sat_mask = (df["labor_cost"] >= 100) & (df["satisfaction_score"].notna()) & (df["satisfaction_score"] <= 2)
high_cost_low_sat_df = df[high_cost_low_sat_mask]
results["high_cost_low_sat_count"] = len(high_cost_low_sat_df)
if len(high_cost_low_sat_df) > 0:
    results["high_cost_low_sat_reopen_pct"] = (high_cost_low_sat_df["reopened"].sum() / len(high_cost_low_sat_df)) * 100
else:
    results["high_cost_low_sat_reopen_pct"] = np.nan

# Q6: Distribution metrics
results["resolution_median"] = df["resolution_minutes"].median()
results["resolution_std"] = df["resolution_minutes"].std(ddof=1)  # sample std
results["satisfaction_mean"] = df["satisfaction_score"].mean()
results["satisfaction_missing_count"] = df["satisfaction_score"].isna().sum()

# Q7: Agent concentration
results["unique_agent_count"] = df["agent_id"].nunique()
agent_ticket_counts = df["agent_id"].value_counts()
results["top_agent_ticket_count"] = agent_ticket_counts.iloc[0] if len(agent_ticket_counts) > 0 else 0
results["top_agent_ticket_share_pct"] = (results["top_agent_ticket_count"] / results["ticket_count"]) * 100

# Handle NaN/Infinity for JSON serialization
for key, value in results.items():
    if pd.isna(value) or (isinstance(value, float) and (np.isinf(value) or np.isnan(value))):
        results[key] = None

# Write results to JSON
with open(output_file, "w") as f:
    json.dump(results, f)
