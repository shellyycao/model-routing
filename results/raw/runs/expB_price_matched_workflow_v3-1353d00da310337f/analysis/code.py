import os
import json
import pandas as pd
import numpy as np

# Define paths
input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

# Read cleaned data
df = pd.read_csv(input_path)

# Initialize results dictionary
results = {}

# --- Q1: Overall Metrics ---
results["ticket_count"] = len(df)
results["mean_resolution_minutes"] = df["resolution_minutes"].mean()
results["total_labor_cost"] = df["labor_cost"].sum()

# --- Q2: Team Comparison ---
team_costs = df.groupby("team")["labor_cost"].sum()
results["labor_cost_alpha"] = team_costs.get("Alpha", 0.0)
results["labor_cost_beta"] = team_costs.get("Beta", 0.0)
results["labor_cost_gamma"] = team_costs.get("Gamma", 0.0)

# --- Q3: Channel Comparison ---
channel_resolution = df.groupby("channel")["resolution_minutes"].mean()
results["resolution_email"] = channel_resolution.get("email", 0.0)
results["resolution_chat"] = channel_resolution.get("chat", 0.0)
results["resolution_phone"] = channel_resolution.get("phone", 0.0)

# --- Q4: Reopening Change ---
channel_reopen = df.groupby("channel")["reopened"].mean() * 100
results["reopen_rate_email_pct"] = channel_reopen.get("email", 0.0)
results["reopen_rate_chat_pct"] = channel_reopen.get("chat", 0.0)

email_rate = results["reopen_rate_email_pct"]
chat_rate = results["reopen_rate_chat_pct"]

if chat_rate != 0:
    change_pct = (email_rate - chat_rate) / chat_rate * 100
else:
    change_pct = 0.0
results["email_vs_chat_reopen_change_pct"] = change_pct

# --- Q5: High-cost Low-satisfaction Segment ---
# Filter: labor_cost >= 100 AND satisfaction_score is not NA AND satisfaction_score <= 2
high_cost_low_sat_df = df[
    (df["labor_cost"] >= 100) & 
    (df["satisfaction_score"].notna()) & 
    (df["satisfaction_score"] <= 2)
]
results["high_cost_low_sat_count"] = len(high_cost_low_sat_df)
if len(high_cost_low_sat_df) > 0:
    results["high_cost_low_sat_reopen_pct"] = high_cost_low_sat_df["reopened"].mean() * 100
else:
    results["high_cost_low_sat_reopen_pct"] = 0.0

# --- Q6: Distribution ---
results["resolution_median"] = df["resolution_minutes"].median()
results["resolution_std"] = df["resolution_minutes"].std(ddof=1) # Sample standard deviation
results["satisfaction_mean"] = df["satisfaction_score"].mean() # .mean() skips NA by default
results["satisfaction_missing_count"] = df["satisfaction_score"].isna().sum()

# --- Q7: Agent Concentration ---
results["unique_agent_count"] = df["agent_id"].nunique()
agent_counts = df["agent_id"].value_counts()
results["top_agent_ticket_count"] = agent_counts.iloc[0] if len(agent_counts) > 0 else 0
results["top_agent_ticket_share_pct"] = (results["top_agent_ticket_count"] / results["ticket_count"]) * 100

# Handle potential NaN values from empty dataframes or zero divisions (replace NaN with None then check, though logic prevents most)
# Convert to native Python types for JSON serialization
for key, value in results.items():
    if isinstance(value, (np.integer, np.floating)):
        results[key] = value.item()
    # Check for NaN/Inf just in case (though logic should prevent it)
    if isinstance(value, float):
        if np.isnan(value) or np.isinf(value):
            # Fallback to 0 or raise error depending on strictness. 
            # Prompt says "finite number". Logic ensures denominators are checked.
            results[key] = 0.0

# Write output
with open(output_path, 'w') as f:
    json.dump(results, f, indent=2)
