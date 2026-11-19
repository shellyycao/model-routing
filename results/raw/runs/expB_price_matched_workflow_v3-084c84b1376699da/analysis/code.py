import os
import json
import pandas as pd
import numpy as np

# Read cleaned data
input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
df = pd.read_csv(
    input_path,
    dtype={
        "ticket_id": str,
        "agent_id": str,
        "team": "category",
        "region": "category",
        "channel": "category",
        "resolution_minutes": int,
        "reopened": int,
        "hourly_cost": float,
        "labor_cost": float,
    },
    dtype_backend="numpy_nullable"
)

# Ensure satisfaction_score is nullable Int64
df["satisfaction_score"] = pd.array(df["satisfaction_score"], dtype="Int64")

# ── q1: Overall metrics ──────────────────────────────────────────────────────
ticket_count = len(df)
mean_resolution_minutes = df["resolution_minutes"].mean()
total_labor_cost = df["labor_cost"].sum()

# ── q2: Team labor cost ──────────────────────────────────────────────────────
team_labor = df.groupby("team", observed=True)["labor_cost"].sum()
labor_cost_alpha = float(team_labor.get("Alpha", 0.0))
labor_cost_beta  = float(team_labor.get("Beta",  0.0))
labor_cost_gamma = float(team_labor.get("Gamma", 0.0))

# ── q3: Channel mean resolution ──────────────────────────────────────────────
channel_res = df.groupby("channel", observed=True)["resolution_minutes"].mean()
resolution_email = float(channel_res.get("email", float("nan")))
resolution_chat  = float(channel_res.get("chat",  float("nan")))
resolution_phone = float(channel_res.get("phone", float("nan")))

# ── q4: Reopening rates by channel ───────────────────────────────────────────
channel_groups = df.groupby("channel", observed=True)["reopened"]
reopen_rate_email_pct = float(channel_groups.get_group("email").mean() * 100)
reopen_rate_chat_pct  = float(channel_groups.get_group("chat").mean()  * 100)
email_vs_chat_reopen_change_pct = (
    (reopen_rate_email_pct - reopen_rate_chat_pct) / reopen_rate_chat_pct * 100
)

# ── q5: High-cost low-satisfaction segment ───────────────────────────────────
hcls_mask = (df["labor_cost"] >= 100) & (df["satisfaction_score"].notna()) & (df["satisfaction_score"] <= 2)
hcls = df[hcls_mask]
high_cost_low_sat_count = len(hcls)
if high_cost_low_sat_count > 0:
    high_cost_low_sat_reopen_pct = float(hcls["reopened"].mean() * 100)
else:
    high_cost_low_sat_reopen_pct = 0.0

# ── q6: Distribution metrics ─────────────────────────────────────────────────
resolution_median = float(df["resolution_minutes"].median())
resolution_std    = float(df["resolution_minutes"].std(ddof=1))  # sample std

sat_valid = df["satisfaction_score"].dropna()
satisfaction_mean          = float(sat_valid.mean())
satisfaction_missing_count = int(df["satisfaction_score"].isna().sum())

# ── q7: Agent concentration ───────────────────────────────────────────────────
agent_counts     = df["agent_id"].value_counts()
unique_agent_count      = int(df["agent_id"].nunique())
top_agent_ticket_count  = int(agent_counts.iloc[0])
top_agent_ticket_share_pct = top_agent_ticket_count / ticket_count * 100

# ── Assemble findings ─────────────────────────────────────────────────────────
findings = {
    "ticket_count":                    float(ticket_count),
    "mean_resolution_minutes":         float(mean_resolution_minutes),
    "total_labor_cost":                float(total_labor_cost),
    "labor_cost_alpha":                labor_cost_alpha,
    "labor_cost_beta":                 labor_cost_beta,
    "labor_cost_gamma":                labor_cost_gamma,
    "resolution_email":                resolution_email,
    "resolution_chat":                 resolution_chat,
    "resolution_phone":                resolution_phone,
    "reopen_rate_email_pct":           reopen_rate_email_pct,
    "reopen_rate_chat_pct":            reopen_rate_chat_pct,
    "email_vs_chat_reopen_change_pct": email_vs_chat_reopen_change_pct,
    "high_cost_low_sat_count":         float(high_cost_low_sat_count),
    "high_cost_low_sat_reopen_pct":    high_cost_low_sat_reopen_pct,
    "resolution_median":               resolution_median,
    "resolution_std":                  resolution_std,
    "satisfaction_mean":               satisfaction_mean,
    "satisfaction_missing_count":      float(satisfaction_missing_count),
    "unique_agent_count":              float(unique_agent_count),
    "top_agent_ticket_count":          float(top_agent_ticket_count),
    "top_agent_ticket_share_pct":      float(top_agent_ticket_share_pct),
}

# Validate: all values must be finite numbers
for k, v in findings.items():
    if not isinstance(v, (int, float)) or not np.isfinite(v):
        raise ValueError(f"Non-finite or non-numeric value for key '{k}': {v}")

output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
with open(output_path, "w") as f:
    json.dump(findings, f, indent=2)

print("findings.json written successfully.")
print(json.dumps(findings, indent=2))
