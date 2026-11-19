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

# Initialize findings dictionary
findings = {}

# q1: Overall metrics
findings["ticket_count"] = len(df)
findings["mean_resolution_minutes"] = df["resolution_minutes"].mean()
findings["total_labor_cost"] = df["labor_cost"].sum()

# q2: Team comparison (total labor_cost for Alpha, Beta and Gamma)
findings["labor_cost_alpha"] = df[df["team"] == "Alpha"]["labor_cost"].sum()
findings["labor_cost_beta"] = df[df["team"] == "Beta"]["labor_cost"].sum()
findings["labor_cost_gamma"] = df[df["team"] == "Gamma"]["labor_cost"].sum()

# q3: Channel comparison (mean resolution_minutes by channel)
findings["resolution_email"] = df[df["channel"] == "email"]["resolution_minutes"].mean()
findings["resolution_chat"] = df[df["channel"] == "chat"]["resolution_minutes"].mean()
findings["resolution_phone"] = df[df["channel"] == "phone"]["resolution_minutes"].mean()

# q4: Reopening change
email_tickets = df[df["channel"] == "email"]
chat_tickets = df[df["channel"] == "chat"]

reopen_rate_email = email_tickets["reopened"].mean()
reopen_rate_chat = chat_tickets["reopened"].mean()

findings["reopen_rate_email_pct"] = reopen_rate_email * 100
findings["reopen_rate_chat_pct"] = reopen_rate_chat * 100

# (email rate - chat rate) / chat rate * 100
if reopen_rate_chat != 0:
    findings["email_vs_chat_reopen_change_pct"] = ((reopen_rate_email - reopen_rate_chat) / reopen_rate_chat) * 100
else:
    findings["email_vs_chat_reopen_change_pct"] = 0.0

# q5: High-cost low-satisfaction segment
# Tickets with labor_cost >= 100 and a non-missing satisfaction_score <= 2
high_cost_low_sat = df[(df["labor_cost"] >= 100) & (df["satisfaction_score"].notna()) & (df["satisfaction_score"] <= 2)]
findings["high_cost_low_sat_count"] = len(high_cost_low_sat)
if len(high_cost_low_sat) > 0:
    findings["high_cost_low_sat_reopen_pct"] = high_cost_low_sat["reopened"].mean() * 100
else:
    findings["high_cost_low_sat_reopen_pct"] = 0.0

# q6: Distribution
findings["resolution_median"] = df["resolution_minutes"].median()
findings["resolution_std"] = df["resolution_minutes"].std(ddof=1)  # sample standard deviation
findings["satisfaction_mean"] = df["satisfaction_score"].mean()  # mean of non-missing values
findings["satisfaction_missing_count"] = df["satisfaction_score"].isna().sum()

# q7: Agent concentration
findings["unique_agent_count"] = df["agent_id"].nunique()
agent_counts = df["agent_id"].value_counts()
findings["top_agent_ticket_count"] = agent_counts.iloc[0] if len(agent_counts) > 0 else 0
findings["top_agent_ticket_share_pct"] = (findings["top_agent_ticket_count"] / findings["ticket_count"]) * 100

# Write findings to JSON file
with open(output_file, "w") as f:
    json.dump(findings, f)
