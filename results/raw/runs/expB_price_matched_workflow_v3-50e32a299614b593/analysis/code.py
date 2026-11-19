import os
import json
import pandas as pd
import numpy as np

input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

df = pd.read_csv(input_path)

findings = {}

# q1: Overall
n = len(df)
findings["ticket_count"] = int(n)
findings["mean_resolution_minutes"] = float(df["resolution_minutes"].mean())
findings["total_labor_cost"] = float(df["labor_cost"].sum())

# q2: Team comparison - total labor cost per team
team_cost = df.groupby("team", observed=True)["labor_cost"].sum()
findings["labor_cost_alpha"] = float(team_cost.get("Alpha", 0.0))
findings["labor_cost_beta"] = float(team_cost.get("Beta", 0.0))
findings["labor_cost_gamma"] = float(team_cost.get("Gamma", 0.0))

# q3: Channel comparison - mean resolution minutes per channel
channel_res = df.groupby("channel", observed=True)["resolution_minutes"].mean()
findings["resolution_email"] = float(channel_res.get("email", 0.0))
findings["resolution_chat"] = float(channel_res.get("chat", 0.0))
findings["resolution_phone"] = float(channel_res.get("phone", 0.0))

# q4: Reopening rates for email and chat, and relative change
reopen_by_channel = df.groupby("channel", observed=True)["reopened"].mean() * 100.0
email_rate = float(reopen_by_channel.get("email", 0.0))
chat_rate = float(reopen_by_channel.get("chat", 0.0))
findings["reopen_rate_email_pct"] = email_rate
findings["reopen_rate_chat_pct"] = chat_rate
if chat_rate != 0.0:
    findings["email_vs_chat_reopen_change_pct"] = float((email_rate - chat_rate) / chat_rate * 100.0)
else:
    findings["email_vs_chat_reopen_change_pct"] = 0.0

# q5: High-cost (labor_cost >= 100) & low-satisfaction (non-missing score <= 2) segment
sat = df["satisfaction_score"]
seg_mask = (df["labor_cost"] >= 100) & sat.notna() & (sat <= 2)
seg = df[seg_mask]
seg_count = int(len(seg))
findings["high_cost_low_sat_count"] = seg_count
if seg_count > 0:
    findings["high_cost_low_sat_reopen_pct"] = float(seg["reopened"].mean() * 100.0)
else:
    findings["high_cost_low_sat_reopen_pct"] = 0.0

# q6: Distribution metrics
findings["resolution_median"] = float(df["resolution_minutes"].median())
findings["resolution_std"] = float(df["resolution_minutes"].std(ddof=1))
findings["satisfaction_mean"] = float(sat.mean())
findings["satisfaction_missing_count"] = int(sat.isna().sum())

# q7: Agent concentration
findings["unique_agent_count"] = int(df["agent_id"].nunique())
top_count = int(df["agent_id"].value_counts().max())
findings["top_agent_ticket_count"] = top_count
findings["top_agent_ticket_share_pct"] = float(top_count / n * 100.0) if n > 0 else 0.0

# Safety: guarantee flat JSON with only finite numbers
for k, v in list(findings.items()):
    v = float(v)
    findings[k] = v if np.isfinite(v) else 0.0

with open(output_path, "w") as f:
    json.dump(findings, f, indent=2)
