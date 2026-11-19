import os
import json
import pandas as pd
import numpy as np

# Read cleaned data
input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
df = pd.read_csv(input_path)

findings = {}

# Q1: Overall metrics
findings["ticket_count"] = float(len(df))
findings["mean_resolution_minutes"] = float(df["resolution_minutes"].mean())
findings["total_labor_cost"] = float(df["labor_cost"].sum())

# Q2: Team labor cost
team_costs = df.groupby("team")["labor_cost"].sum()
findings["labor_cost_alpha"] = float(team_costs.get("Alpha", 0.0))
findings["labor_cost_beta"] = float(team_costs.get("Beta", 0.0))
findings["labor_cost_gamma"] = float(team_costs.get("Gamma", 0.0))

# Q3: Channel mean resolution minutes
channel_res = df.groupby("channel")["resolution_minutes"].mean()
findings["resolution_email"] = float(channel_res.get("email", float("nan")))
findings["resolution_chat"] = float(channel_res.get("chat", float("nan")))
findings["resolution_phone"] = float(channel_res.get("phone", float("nan")))

# Q4: Reopening rates by channel
email_df = df[df["channel"] == "email"]
chat_df = df[df["channel"] == "chat"]

reopen_rate_email = float(email_df["reopened"].mean() * 100)
reopen_rate_chat = float(chat_df["reopened"].mean() * 100)
email_vs_chat_reopen_change = float((reopen_rate_email - reopen_rate_chat) / reopen_rate_chat * 100)

findings["reopen_rate_email_pct"] = reopen_rate_email
findings["reopen_rate_chat_pct"] = reopen_rate_chat
findings["email_vs_chat_reopen_change_pct"] = email_vs_chat_reopen_change

# Q5: High-cost low-satisfaction segment
high_cost_low_sat = df[(df["labor_cost"] >= 100) & (df["satisfaction_score"].notna()) & (df["satisfaction_score"] <= 2)]
findings["high_cost_low_sat_count"] = float(len(high_cost_low_sat))
if len(high_cost_low_sat) > 0:
    findings["high_cost_low_sat_reopen_pct"] = float(high_cost_low_sat["reopened"].mean() * 100)
else:
    findings["high_cost_low_sat_reopen_pct"] = 0.0

# Q6: Distribution metrics
findings["resolution_median"] = float(df["resolution_minutes"].median())
findings["resolution_std"] = float(df["resolution_minutes"].std(ddof=1))
sat_non_missing = df["satisfaction_score"].dropna()
findings["satisfaction_mean"] = float(sat_non_missing.mean())
findings["satisfaction_missing_count"] = float(df["satisfaction_score"].isna().sum())

# Q7: Agent concentration
findings["unique_agent_count"] = float(df["agent_id"].nunique())
agent_ticket_counts = df.groupby("agent_id")["ticket_id"].count()
top_agent_ticket_count = float(agent_ticket_counts.max())
findings["top_agent_ticket_count"] = top_agent_ticket_count
findings["top_agent_ticket_share_pct"] = float(top_agent_ticket_count / findings["ticket_count"] * 100)

# Validate all values are finite numbers
for key, val in findings.items():
    if not isinstance(val, (int, float)) or not np.isfinite(val):
        raise ValueError(f"Non-finite or invalid value for key '{key}': {val}")

# Write findings.json
output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
with open(output_path, "w") as f:
    json.dump(findings, f)

print("findings.json written successfully.")
print(json.dumps(findings, indent=2))
