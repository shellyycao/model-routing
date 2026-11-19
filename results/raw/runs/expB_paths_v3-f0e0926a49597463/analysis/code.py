import os
import json
import pandas as pd
import numpy as np

def safe_float(x):
    """Convert a value to a plain Python float, replacing NaN with 0.0."""
    if pd.isna(x):
        return 0.0
    return float(x)

def safe_int(x):
    """Convert a value to a plain Python int, replacing NaN with 0."""
    if pd.isna(x):
        return 0
    return int(x)

def main():
    # Paths from environment variables
    input_dir = os.environ.get("INPUT_DIR")
    output_dir = os.environ.get("OUTPUT_DIR")
    if not input_dir or not output_dir:
        raise RuntimeError("INPUT_DIR and OUTPUT_DIR environment variables must be set")

    cleaned_path = os.path.join(input_dir, "cleaned.csv")
    df = pd.read_csv(cleaned_path)

    # q1 – overall metrics
    ticket_count = len(df)
    mean_resolution_minutes = safe_float(df["resolution_minutes"].mean())
    total_labor_cost = safe_float(df["labor_cost"].sum())

    # q2 – team labour cost totals
    team_costs = df.groupby("team")["labor_cost"].sum()
    labor_cost_alpha = safe_float(team_costs.get("Alpha", 0.0))
    labor_cost_beta = safe_float(team_costs.get("Beta", 0.0))
    labor_cost_gamma = safe_float(team_costs.get("Gamma", 0.0))

    # q3 – mean resolution time per channel
    channel_means = df.groupby("channel")["resolution_minutes"].mean()
    resolution_email = safe_float(channel_means.get("email", np.nan))
    resolution_chat = safe_float(channel_means.get("chat", np.nan))
    resolution_phone = safe_float(channel_means.get("phone", np.nan))

    # q4 – reopen rates per channel and comparative change
    email_df = df[df["channel"] == "email"]
    chat_df = df[df["channel"] == "chat"]
    reopen_rate_email_pct = (
        safe_float(email_df["reopened"].sum()) / len(email_df) * 100
        if len(email_df) > 0 else 0.0
    )
    reopen_rate_chat_pct = (
        safe_float(chat_df["reopened"].sum()) / len(chat_df) * 100
        if len(chat_df) > 0 else 0.0
    )
    if reopen_rate_chat_pct != 0:
        email_vs_chat_reopen_change_pct = (
            (reopen_rate_email_pct - reopen_rate_chat_pct) / reopen_rate_chat_pct * 100
        )
    else:
        email_vs_chat_reopen_change_pct = 0.0

    # q5 – high‑cost, low‑satisfaction segment
    high_cost_low_sat = df[(df["labor_cost"] >= 100) &
                           df["satisfaction_score"].notna() &
                           (df["satisfaction_score"] <= 2)]
    high_cost_low_sat_count = len(high_cost_low_sat)
    if high_cost_low_sat_count > 0:
        high_cost_low_sat_reopen_pct = (
            safe_float(high_cost_low_sat["reopened"].sum()) / high_cost_low_sat_count * 100
        )
    else:
        high_cost_low_sat_reopen_pct = 0.0

    # q6 – distribution and satisfaction stats
    resolution_median = safe_float(df["resolution_minutes"].median())
    resolution_std = safe_float(df["resolution_minutes"].std(ddof=1))
    satisfaction_mean = safe_float(df["satisfaction_score"].mean())
    satisfaction_missing_count = safe_int(df["satisfaction_score"].isna().sum())

    # q7 – agent concentration
    unique_agent_count = safe_int(df["agent_id"].nunique())
    agent_ticket_counts = df["agent_id"].value_counts()
    top_agent_ticket_count = safe_int(agent_ticket_counts.iloc[0] if not agent_ticket_counts.empty else 0)
    top_agent_ticket_share_pct = (
        safe_float(top_agent_ticket_count) / ticket_count * 100
        if ticket_count > 0 else 0.0
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
        "top_agent_ticket_share_pct": top_agent_ticket_share_pct
    }

    output_path = os.path.join(output_dir, "findings.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(findings, f, ensure_ascii=False)

if __name__ == "__main__":
    main()
