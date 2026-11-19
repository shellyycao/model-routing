import os
import json
import pandas as pd
import numpy as np

# Define input and output paths
input_file = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
output_file = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

# Read the cleaned data
df = pd.read_csv(input_file)

# Initialize results dictionary
results = {}

# --- Q1: Overall metrics ---
results["ticket_count"] = len(df)
results["mean_resolution_minutes"] = df["resolution_minutes"].mean()
results["total_labor_cost"] = df["labor_cost"].sum()

# --- Q2: Team comparison ---
team_costs = df.groupby("team")["labor_cost"].sum()
results["labor_cost_alpha"] = team_costs.get("Alpha", 0.0)
results["labor_cost_beta"] = team_costs.get("Beta", 0.0)
results["labor_cost_gamma"] = team_costs.get("Gamma", 0.0)

# --- Q3: Channel comparison ---
channel_resolution = df.groupby("channel")["resolution_minutes"].mean()
results["resolution_email"] = channel_resolution.get("email", np.nan)
results["resolution_chat"] = channel_resolution.get("chat", np.nan)
results["resolution_phone"] = channel_resolution.get("phone", np.nan)

# --- Q4: Reopening change ---
# Reopened percentage for email
email_tickets = df[df["channel"] == "email"]
if len(email_tickets) > 0:
    reopen_rate_email = email_tickets["reopened"].mean() * 100
else:
    reopen_rate_email = np.nan
results["reopen_rate_email_pct"] = reopen_rate_email

# Reopened percentage for chat
chat_tickets = df[df["channel"] == "chat"]
if len(chat_tickets) > 0:
    reopen_rate_chat = chat_tickets["reopened"].mean() * 100
else:
    reopen_rate_chat = np.nan
results["reopen_rate_chat_pct"] = reopen_rate_chat

# Email vs Chat reopen change percentage
if pd.notna(reopen_rate_chat) and reopen_rate_chat != 0:
    email_vs_chat_change = ((reopen_rate_email - reopen_rate_chat) / reopen_rate_chat) * 100
else:
    email_vs_chat_change = np.nan
results["email_vs_chat_reopen_change_pct"] = email_vs_chat_change

# --- Q5: High-cost low-satisfaction segment ---
# Filter: labor_cost >= 100 AND satisfaction_score is not missing AND satisfaction_score <= 2
high_cost_segment = df[(df["labor_cost"] >= 100) & 
                       (df["satisfaction_score"].notna()) & 
                       (df["satisfaction_score"] <= 2)]
results["high_cost_low_sat_count"] = len(high_cost_segment)
if len(high_cost_segment) > 0:
    results["high_cost_low_sat_reopen_pct"] = high_cost_segment["reopened"].mean() * 100
else:
    results["high_cost_low_sat_reopen_pct"] = 0.0

# --- Q6: Distribution ---
results["resolution_median"] = df["resolution_minutes"].median()
results["resolution_std"] = df["resolution_minutes"].std(ddof=1) # Sample standard deviation
results["satisfaction_mean"] = df["satisfaction_score"].mean() # mean of non-missing by default
results["satisfaction_missing_count"] = df["satisfaction_score"].isna().sum()

# --- Q7: Agent concentration ---
results["unique_agent_count"] = df["agent_id"].nunique()
agent_counts = df["agent_id"].value_counts()
if len(agent_counts) > 0:
    top_agent_count = agent_counts.iloc[0]
else:
    top_agent_count = 0
results["top_agent_ticket_count"] = top_agent_count
if results["ticket_count"] > 0:
    results["top_agent_ticket_share_pct"] = (top_agent_count / results["ticket_count"]) * 100
else:
    results["top_agent_ticket_share_pct"] = 0.0

# Handle potential NaN/Infinity values for JSON serialization
# Convert NaN to None, then replace None with a placeholder or handle if necessary.
# The prompt implies finite numbers are expected. If a calculation results in NaN (e.g. empty dataframe), 
# we must ensure it doesn't break the JSON dump. However, based on the cleaning summary, we have 347 rows.
# We replace NaN/inf with 0 or appropriate value if logic dictates, but standard float('nan') is not valid JSON.
# We will replace NaN with None and then check, or use a custom encoder. 
# Given the constraints, we assume valid data produces finite numbers. 
# If a specific metric is NaN (e.g. mean of empty series), we will cast to None and then to 0 or handle.
# For this specific task, we'll replace NaN with None to allow json.dump to handle it or fail if it can't.
# But the prompt says "No strings... null... as values". 
# We will assume the data is sufficient to produce valid numbers for all metrics.
# If a metric is mathematically undefined (like division by zero), we'll set to 0.0 or similar if appropriate, 
# but here we check conditions.

def clean_for_json(obj):
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    if isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return 0.0 # Fallback for undefined metrics
    return obj

results = clean_for_json(results)

# Write findings to JSON
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)
