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
results["ticket_count"] = len(df)
results["mean_resolution_minutes"] = df["resolution_minutes"].mean()
results["total_labor_cost"] = df["labor_cost"].sum()

# q2: Team comparison (labor cost)
team_costs = df.groupby("team")["labor_cost"].sum()
results["labor_cost_alpha"] = team_costs.get("Alpha", 0.0)
results["labor_cost_beta"] = team_costs.get("Beta", 0.0)
results["labor_cost_gamma"] = team_costs.get("Gamma", 0.0)

# q3: Channel comparison (mean resolution minutes)
channel_resolution = df.groupby("channel")["resolution_minutes"].mean()
results["resolution_email"] = channel_resolution.get("email", 0.0)
results["resolution_chat"] = channel_resolution.get("chat", 0.0)
results["resolution_phone"] = channel_resolution.get("phone", 0.0)

# q4: Reopening change
email_tickets = df[df["channel"] == "email"]
chat_tickets = df[df["channel"] == "chat"]

reopen_rate_email = email_tickets["reopened"].mean() * 100
reopen_rate_chat = chat_tickets["reopened"].mean() * 100

results["reopen_rate_email_pct"] = reopen_rate_email
results["reopen_rate_chat_pct"] = reopen_rate_chat

if reopen_rate_chat != 0:
    email_vs_chat_change = ((reopen_rate_email - reopen_rate_chat) / reopen_rate_chat) * 100
else:
    email_vs_chat_change = 0.0
results["email_vs_chat_reopen_change_pct"] = email_vs_chat_change

# q5: High-cost low-satisfaction segment
# Criteria: labor_cost >= 100 AND satisfaction_score <= 2 (non-missing)
high_cost_low_sat_df = df[(df["labor_cost"] >= 100) & (df["satisfaction_score"] <= 2) & (df["satisfaction_score"].notna())]
results["high_cost_low_sat_count"] = len(high_cost_low_sat_df)
if len(high_cost_low_sat_df) > 0:
    results["high_cost_low_sat_reopen_pct"] = high_cost_low_sat_df["reopened"].mean() * 100
else:
    results["high_cost_low_sat_reopen_pct"] = 0.0

# q6: Distribution
results["resolution_median"] = df["resolution_minutes"].median()
results["resolution_std"] = df["resolution_minutes"].std(ddof=1) # Sample standard deviation
results["satisfaction_mean"] = df["satisfaction_score"].mean() # pandas ignores NaN by default
results["satisfaction_missing_count"] = df["satisfaction_score"].isna().sum()

# q7: Agent concentration
results["unique_agent_count"] = df["agent_id"].nunique()
agent_ticket_counts = df["agent_id"].value_counts()
results["top_agent_ticket_count"] = agent_ticket_counts.iloc[0] if len(agent_ticket_counts) > 0 else 0
results["top_agent_ticket_share_pct"] = (results["top_agent_ticket_count"] / results["ticket_count"]) * 100

# Write results to JSON
with open(output_path, 'w') as f:
    json.dump(results, f)
