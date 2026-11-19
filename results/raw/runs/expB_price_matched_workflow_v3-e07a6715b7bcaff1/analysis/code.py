import os
import json
import pandas as pd
import numpy as np

# Read cleaned data
input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
df = pd.read_csv(input_path, dtype={"ticket_id": str, "agent_id": str})

# Ensure correct types
df["resolution_minutes"] = df["resolution_minutes"].astype(int)
df["reopened"] = df["reopened"].astype(int)
df["labor_cost"] = df["labor_cost"].astype(float)
df["hourly_cost"] = df["hourly_cost"].astype(float)
# satisfaction_score: nullable int
df["satisfaction_score"] = pd.to_numeric(df["satisfaction_score"], errors="coerce")

findings = {}

# Q1: Overall metrics
findings["ticket_count"] = float(len(df))
findings["mean_resolution_minutes"] = float(df["resolution_minutes"].mean())
findings["total_labor_cost"] = float(df["labor_cost"].sum())

# Q2: Team labor costs
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

reopen_rate_email = float(email_df["reopened"].mean() * 100) if len(email_df) > 0 else 0.0
reopen_rate_chat = float(chat_df["reopened"].mean() * 100) if len(chat_df) > 0 else 0.0

findings["reopen_rate_email_pct"] = reopen_rate_email
findings["reopen_rate_chat_pct"] = reopen_rate_chat

# (email rate - chat rate) / chat rate * 100
if reopen_rate_chat != 0.0:
    email_vs_chat = (reopen_rate_email - reopen_rate_chat) / reopen_rate_chat * 100
else:
    # If chat reopen rate is 0, difference is undefined; use 0 to avoid inf
    email_vs_chat = 0.0
findings["email_vs_chat_reopen_change_pct"] = float(email_vs_chat)

# Q5: High-cost low-satisfaction segment
high_cost_low_sat = df[
    (df["labor_cost"] >= 100) &
    (df["satisfaction_score"].notna()) &
    (df["satisfaction_score"] <= 2)
]
findings["high_cost_low_sat_count"] = float(len(high_cost_low_sat))
if len(high_cost_low_sat) > 0:
    findings["high_cost_low_sat_reopen_pct"] = float(high_cost_low_sat["reopened"].mean() * 100)
else:
    findings["high_cost_low_sat_reopen_pct"] = 0.0

# Q6: Distribution metrics
findings["resolution_median"] = float(df["resolution_minutes"].median())
findings["resolution_std"] = float(df["resolution_minutes"].std(ddof=1))

sat_valid = df["satisfaction_score"].dropna()
findings["satisfaction_mean"] = float(sat_valid.mean()) if len(sat_valid) > 0 else 0.0
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
        raise ValueError(f"Non-finite or invalid value for metric '{key}': {val}")

# Write findings.json
output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
with open(output_path, "w") as f:
    json.dump(findings, f)

print("findings.json written successfully.")
print(json.dumps(findings, indent=2))
