import json
import os

import pandas as pd

INPUT_PATH = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
OUTPUT_PATH = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

df = pd.read_csv(INPUT_PATH)

# q1: overall volume, speed and cost
ticket_count = int(len(df))
mean_resolution_minutes = float(df["resolution_minutes"].mean())
total_labor_cost = float(df["labor_cost"].sum())

# q2: total labor cost per team
team_cost = df.groupby("team")["labor_cost"].sum()
labor_cost_alpha = float(team_cost.get("Alpha", 0.0))
labor_cost_beta = float(team_cost.get("Beta", 0.0))
labor_cost_gamma = float(team_cost.get("Gamma", 0.0))

# q3: mean resolution minutes per channel
channel_res = df.groupby("channel")["resolution_minutes"].mean()
resolution_email = float(channel_res.get("email", 0.0))
resolution_chat = float(channel_res.get("chat", 0.0))
resolution_phone = float(channel_res.get("phone", 0.0))

# q4: reopening rates (percent) for email and chat, and relative change

def reopen_rate_pct(sub):
    if len(sub) == 0:
        return 0.0
    return float(sub["reopened"].mean() * 100.0)

reopen_rate_email_pct = reopen_rate_pct(df[df["channel"] == "email"])
reopen_rate_chat_pct = reopen_rate_pct(df[df["channel"] == "chat"])
if reopen_rate_chat_pct != 0.0:
    email_vs_chat_reopen_change_pct = float(
        (reopen_rate_email_pct - reopen_rate_chat_pct) / reopen_rate_chat_pct * 100.0
    )
else:
    email_vs_chat_reopen_change_pct = 0.0

# q5: high-cost, low-satisfaction segment (non-missing satisfaction only)
segment = df[
    (df["labor_cost"] >= 100)
    & (df["satisfaction_score"].notna())
    & (df["satisfaction_score"] <= 2)
]
high_cost_low_sat_count = int(len(segment))
high_cost_low_sat_reopen_pct = (
    float(segment["reopened"].mean() * 100.0) if len(segment) > 0 else 0.0
)

# q6: distribution metrics
resolution_median = float(df["resolution_minutes"].median())
resolution_std = float(df["resolution_minutes"].std(ddof=1))
satisfaction_mean = float(df["satisfaction_score"].mean())
satisfaction_missing_count = int(df["satisfaction_score"].isna().sum())

# q7: agent concentration
unique_agent_count = int(df["agent_id"].nunique())
agent_ticket_counts = df["agent_id"].value_counts()
top_agent_ticket_count = int(agent_ticket_counts.max()) if len(agent_ticket_counts) else 0
top_agent_ticket_share_pct = (
    float(top_agent_ticket_count / ticket_count * 100.0) if ticket_count > 0 else 0.0
)

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

with open(OUTPUT_PATH, "w") as f:
    json.dump(findings, f, allow_nan=False)
