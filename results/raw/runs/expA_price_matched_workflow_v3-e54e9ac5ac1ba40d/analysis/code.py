import json
import os

import numpy as np
import pandas as pd

input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

df = pd.read_csv(input_path)

findings = {}

# q1: Overall metrics
findings["ticket_count"] = int(len(df))
findings["mean_resolution_minutes"] = float(df["resolution_minutes"].mean())
findings["total_labor_cost"] = float(df["labor_cost"].sum())

# q2: Total labor cost per team
team_cost = df.groupby("team", observed=True)["labor_cost"].sum()
findings["labor_cost_alpha"] = float(team_cost.get("Alpha", 0.0))
findings["labor_cost_beta"] = float(team_cost.get("Beta", 0.0))
findings["labor_cost_gamma"] = float(team_cost.get("Gamma", 0.0))

# q3: Mean resolution minutes per channel
chan_res = df.groupby("channel", observed=True)["resolution_minutes"].mean()
findings["resolution_email"] = float(chan_res.get("email", 0.0))
findings["resolution_chat"] = float(chan_res.get("chat", 0.0))
findings["resolution_phone"] = float(chan_res.get("phone", 0.0))

# q4: Reopened percentage for email and chat, and relative change
def reopen_pct(sub):
    if len(sub) == 0:
        return 0.0
    return float(sub["reopened"].mean() * 100.0)

email_rate = reopen_pct(df[df["channel"] == "email"])
chat_rate = reopen_pct(df[df["channel"] == "chat"])
findings["reopen_rate_email_pct"] = email_rate
findings["reopen_rate_chat_pct"] = chat_rate
if chat_rate != 0.0:
    findings["email_vs_chat_reopen_change_pct"] = float((email_rate - chat_rate) / chat_rate * 100.0)
else:
    findings["email_vs_chat_reopen_change_pct"] = 0.0

# q5: High-cost (labor_cost >= 100) and low-satisfaction (non-missing score <= 2) segment
sat = df["satisfaction_score"]
mask = (df["labor_cost"] >= 100) & sat.notna() & (sat <= 2)
seg = df[mask]
findings["high_cost_low_sat_count"] = int(len(seg))
findings["high_cost_low_sat_reopen_pct"] = float(seg["reopened"].mean() * 100.0) if len(seg) > 0 else 0.0

# q6: Distribution metrics (sample standard deviation uses ddof=1)
findings["resolution_median"] = float(df["resolution_minutes"].median())
findings["resolution_std"] = float(df["resolution_minutes"].std(ddof=1))
findings["satisfaction_mean"] = float(df["satisfaction_score"].mean())
findings["satisfaction_missing_count"] = int(df["satisfaction_score"].isna().sum())

# q7: Agent concentration
agent_counts = df["agent_id"].value_counts()
findings["unique_agent_count"] = int(df["agent_id"].nunique())
findings["top_agent_ticket_count"] = int(agent_counts.max())
findings["top_agent_ticket_share_pct"] = float(findings["top_agent_ticket_count"] / findings["ticket_count"] * 100.0)

# Final safety pass: guarantee every value is a finite JSON number
for key, value in findings.items():
    if not np.isfinite(value):
        findings[key] = 0.0

with open(output_path, "w") as f:
    json.dump(findings, f, indent=2)
