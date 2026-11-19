import os
import json
import pandas as pd
import numpy as np

def safe_mean(series):
    """Return mean of a pandas Series or 0.0 if the series is empty."""
    if len(series) == 0:
        return 0.0
    return float(series.mean())

def safe_std(series):
    """Return sample standard deviation (ddof=1) or 0.0 if the series has <2 items."""
    if len(series) < 2:
        return 0.0
    return float(series.std(ddof=1))

def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    df = pd.read_csv(input_path)

    # q1
    ticket_count = int(df.shape[0])
    mean_resolution_minutes = safe_mean(df["resolution_minutes"])
    total_labor_cost = float(df["labor_cost"].sum())

    # q2: labor cost per team
    labor_cost_alpha = float(df.loc[df["team"] == "Alpha", "labor_cost"].sum())
    labor_cost_beta = float(df.loc[df["team"] == "Beta", "labor_cost"].sum())
    labor_cost_gamma = float(df.loc[df["team"] == "Gamma", "labor_cost"].sum())

    # q3: mean resolution by channel
    resolution_email = safe_mean(df.loc[df["channel"] == "email", "resolution_minutes"])
    resolution_chat = safe_mean(df.loc[df["channel"] == "chat", "resolution_minutes"])
    resolution_phone = safe_mean(df.loc[df["channel"] == "phone", "resolution_minutes"])

    # q4: reopen rates by channel (percentage)
    def reopen_rate_pct(channel):
        sub = df.loc[df["channel"] == channel]
        if sub.empty:
            return 0.0
        return float(sub["reopened"].sum() / len(sub) * 100)

    reopen_rate_email_pct = reopen_rate_pct("email")
    reopen_rate_chat_pct = reopen_rate_pct("chat")
    # change percentage
    if reopen_rate_chat_pct == 0:
        email_vs_chat_reopen_change_pct = 0.0
    else:
        email_vs_chat_reopen_change_pct = (reopen_rate_email_pct - reopen_rate_chat_pct) / reopen_rate_chat_pct * 100

    # q5: high-cost low-satisfaction segment
    high_cost_mask = (df["labor_cost"] >= 100) & (df["satisfaction_score"].notna()) & (df["satisfaction_score"] <= 2)
    high_cost_low_sat_df = df.loc[high_cost_mask]
    high_cost_low_sat_count = int(high_cost_low_sat_df.shape[0])
    if high_cost_low_sat_count == 0:
        high_cost_low_sat_reopen_pct = 0.0
    else:
        high_cost_low_sat_reopen_pct = float(high_cost_low_sat_df["reopened"].sum() / high_cost_low_sat_count * 100)

    # q6: distribution and satisfaction stats
    resolution_median = float(df["resolution_minutes"].median())
    resolution_std = safe_std(df["resolution_minutes"])
    satisfaction_mean = safe_mean(df["satisfaction_score"].dropna())
    satisfaction_missing_count = int(df["satisfaction_score"].isna().sum())

    # q7: agent concentration
    unique_agent_count = int(df["agent_id"].nunique())
    tickets_per_agent = df["agent_id"].value_counts()
    top_agent_ticket_count = int(tickets_per_agent.iloc[0])
    top_agent_ticket_share_pct = top_agent_ticket_count / ticket_count * 100 if ticket_count else 0.0

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
        "top_agent_ticket_share_pct": top_agent_ticket_share_pct
    }

    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
    with open(output_path, "w") as f:
        json.dump(findings, f, allow_nan=False)

if __name__ == "__main__":
    main()
