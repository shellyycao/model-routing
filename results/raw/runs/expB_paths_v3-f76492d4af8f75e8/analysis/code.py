import os
import json
import pandas as pd
import numpy as np

# --- Load cleaned data ---
input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
df = pd.read_csv(
    input_path,
    dtype={
        "ticket_id": str,
        "agent_id": str,
        "team": str,
        "region": str,
        "channel": str,
        "resolution_minutes": int,
        "reopened": int,
        "hourly_cost": float,
        "labor_cost": float,
    },
)
# satisfaction_score is nullable Int64
df["satisfaction_score"] = pd.to_numeric(df["satisfaction_score"], errors="coerce")

# --- Q1: Overall metrics ---
ticket_count = float(len(df))
mean_resolution_minutes = float(df["resolution_minutes"].mean())
total_labor_cost = float(df["labor_cost"].sum())

# --- Q2: Team labor cost ---
team_labor = df.groupby("team")["labor_cost"].sum()
labor_cost_alpha = float(team_labor.get("Alpha", 0.0))
labor_cost_beta = float(team_labor.get("Beta", 0.0))
labor_cost_gamma = float(team_labor.get("Gamma", 0.0))

# --- Q3: Channel mean resolution minutes ---
channel_res = df.groupby("channel")["resolution_minutes"].mean()
resolution_email = float(channel_res.get("email", float("nan")))
resolution_chat = float(channel_res.get("chat", float("nan")))
resolution_phone = float(channel_res.get("phone", float("nan")))

# --- Q4: Reopening rates by channel ---
email_df = df[df["channel"] == "email"]
chat_df = df[df["channel"] == "chat"]

reopen_rate_email_pct = float(email_df["reopened"].mean() * 100)
reopen_rate_chat_pct = float(chat_df["reopened"].mean() * 100)

# (email rate - chat rate) / chat rate * 100
email_vs_chat_reopen_change_pct = float(
    (reopen_rate_email_pct - reopen_rate_chat_pct) / reopen_rate_chat_pct * 100
)

# --- Q5: High-cost low-satisfaction segment ---
high_cost_low_sat = df[
    (df["labor_cost"] >= 100) &
    (df["satisfaction_score"].notna()) &
    (df["satisfaction_score"] <= 2)
]
high_cost_low_sat_count = float(len(high_cost_low_sat))
if high_cost_low_sat_count > 0:
    high_cost_low_sat_reopen_pct = float(high_cost_low_sat["reopened"].mean() * 100)
else:
    high_cost_low_sat_reopen_pct = 0.0

# --- Q6: Distribution metrics ---
resolution_median = float(df["resolution_minutes"].median())
resolution_std = float(df["resolution_minutes"].std(ddof=1))  # sample std
satisfaction_mean = float(df["satisfaction_score"].mean())  # ignores NaN
satisfaction_missing_count = float(df["satisfaction_score"].isna().sum())

# --- Q7: Agent concentration ---
agent_counts = df.groupby("agent_id")["ticket_id"].count()
unique_agent_count = float(agent_counts.shape[0])
top_agent_ticket_count = float(agent_counts.max())
top_agent_ticket_share_pct = float(top_agent_ticket_count / ticket_count * 100)

# --- Assemble findings ---
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
    "top_agent_ticket_share_pct": top_agent_ticket_share_pct,
}

# Validate: all values must be finite numbers
for k, v in findings.items():
    if not isinstance(v, (int, float)):
        raise ValueError(f"Non-numeric value for key '{k}': {v}")
    if not np.isfinite(v):
        raise ValueError(f"Non-finite value for key '{k}': {v}")

# --- Write output ---
output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
with open(output_path, "w") as f:
    json.dump(findings, f)

print("findings.json written successfully.")
print(json.dumps(findings, indent=2))
