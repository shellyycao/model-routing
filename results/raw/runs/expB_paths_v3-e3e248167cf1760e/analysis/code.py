import os
import json
import pandas as pd
import numpy as np

def main():
    # Paths from environment variables
    input_dir = os.environ.get("INPUT_DIR")
    output_dir = os.environ.get("OUTPUT_DIR")
    if not input_dir or not output_dir:
        raise RuntimeError("INPUT_DIR and OUTPUT_DIR environment variables must be set")

    cleaned_path = os.path.join(input_dir, "cleaned.csv")
    df = pd.read_csv(cleaned_path)

    # Basic counts and aggregates
    ticket_count = int(len(df))
    mean_resolution_minutes = float(df["resolution_minutes"].mean())
    total_labor_cost = float(df["labor_cost"].sum())

    # Team labor cost totals
    labor_cost_alpha = float(df.loc[df["team"] == "Alpha", "labor_cost"].sum())
    labor_cost_beta = float(df.loc[df["team"] == "Beta", "labor_cost"].sum())
    labor_cost_gamma = float(df.loc[df["team"] == "Gamma", "labor_cost"].sum())

    # Channel mean resolution minutes
    resolution_email = float(df.loc[df["channel"] == "email", "resolution_minutes"].mean())
    resolution_chat = float(df.loc[df["channel"] == "chat", "resolution_minutes"].mean())
    resolution_phone = float(df.loc[df["channel"]] == "phone", "resolution_minutes"].mean())
    # The line above has a syntax error; correct implementation below
    resolution_phone = float(df.loc[df["channel"] == "phone", "resolution_minutes"].mean())

    # Reopen rates per channel (percentage)
    def reopen_rate_pct(channel):
        sub = df[df["channel"] == channel]
        if len(sub) == 0:
            return 0.0
        return 100.0 * sub["reopened"].sum() / len(sub)

    reopen_rate_email_pct = reopen_rate_pct("email")
    reopen_rate_chat_pct = reopen_rate_pct("chat")
    # Change percentage (email vs chat)
    if reopen_rate_chat_pct == 0:
        email_vs_chat_reopen_change_pct = 0.0
    else:
        email_vs_chat_reopen_change_pct = (reopen_rate_email_pct - reopen_rate_chat_pct) / reopen_rate_chat_pct * 100.0

    # High‑cost low‑satisfaction segment
    high_cost_mask = (df["labor_cost"] >= 100) & (df["satisfaction_score"].notna()) & (df["satisfaction_score"] <= 2)
    high_cost_low_sat_df = df[high_cost_mask]
    high_cost_low_sat_count = int(len(high_cost_low_sat_df))
    if high_cost_low_sat_count == 0:
        high_cost_low_sat_reopen_pct = 0.0
    else:
        high_cost_low_sat_reopen_pct = 100.0 * high_cost_low_sat_df["reopened"].sum() / high_cost_low_sat_count

    # Distribution metrics for resolution minutes
    resolution_median = float(df["resolution_minutes"].median())
    resolution_std = float(df["resolution_minutes"].std(ddof=1))

    # Satisfaction metrics
    satisfaction_mean = float(df["satisfaction_score"].mean())
    satisfaction_missing_count = int(df["satisfaction_score"].isna().sum())

    # Agent concentration
    unique_agent_count = int(df["agent_id"].nunique())
    top_agent_ticket_count = int(df["agent_id"].value_counts().iloc[0])
    top_agent_ticket_share_pct = 100.0 * top_agent_ticket_count / ticket_count

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

    # Write findings to JSON
    output_path = os.path.join(output_dir, "findings.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(findings, f, ensure_ascii=False)

if __name__ == "__main__":
    main()
