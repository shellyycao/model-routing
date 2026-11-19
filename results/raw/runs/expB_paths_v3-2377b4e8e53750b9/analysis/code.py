import os
import json
import pandas as pd
import numpy as np

def safe_mean(series):
    """Return mean of a pandas Series, or 0.0 if the result is NaN."""
    m = series.mean()
    return 0.0 if pd.isna(m) else float(m)

def safe_std(series):
    """Return sample standard deviation (ddof=1) of a Series, or 0.0 if NaN."""
    s = series.std(ddof=1)
    return 0.0 if pd.isna(s) else float(s)

def safe_percentage(numerator, denominator):
    """Return (numerator/denominator)*100, handling zero denominator."""
    if denominator == 0:
        return 0.0
    return float(numerator) / denominator * 100.0

def main():
    input_dir = os.environ.get("INPUT_DIR", "")
    output_dir = os.environ.get("OUTPUT_DIR", "")
    cleaned_path = os.path.join(input_dir, "cleaned.csv")
    findings_path = os.path.join(output_dir, "findings.json")

    # Load cleaned data
    df = pd.read_csv(cleaned_path, dtype={
        "ticket_id": str,
        "agent_id": str,
        "team": str,
        "region": str,
        "channel": str,
        "resolution_minutes": int,
        "satisfaction_score": float,
        "reopened": int,
        "hourly_cost": float,
        "labor_cost": float,
    })

    # Overall metrics
    ticket_count = int(len(df))
    mean_resolution_minutes = safe_mean(df["resolution_minutes"])
    total_labor_cost = float(df["labor_cost"].sum())

    # Team labor cost totals
    labor_cost_alpha = float(df.loc[df["team"] == "Alpha", "labor_cost"].sum())
    labor_cost_beta = float(df.loc[df["team"] == "Beta", "labor_cost"].sum())
    labor_cost_gamma = float(df.loc[df["team"] == "Gamma", "labor_cost"].sum())

    # Channel mean resolution minutes
    resolution_email = safe_mean(df.loc[df["channel"] == "email", "resolution_minutes"])
    resolution_chat = safe_mean(df.loc[df["channel"] == "chat", "resolution_minutes"])
    resolution_phone = safe_mean(df.loc[df["channel"] == "phone", "resolution_minutes"])

    # Reopen rates per channel (percentage)
    email_mask = df["channel"] == "email"
    chat_mask = df["channel"] == "chat"
    reopen_rate_email_pct = safe_percentage(df.loc[email_mask, "reopened"].sum(), email_mask.sum())
    reopen_rate_chat_pct = safe_percentage(df.loc[chat_mask, "reopened"].sum(), chat_mask.sum())
    # Change metric
    if reopen_rate_chat_pct == 0:
        email_vs_chat_reopen_change_pct = 0.0
    else:
        email_vs_chat_reopen_change_pct = ((reopen_rate_email_pct - reopen_rate_chat_pct) / reopen_rate_chat_pct) * 100.0

    # High‑cost low‑satisfaction segment
    high_cost_mask = df["labor_cost"] >= 100
    low_sat_mask = df["satisfaction_score"].notna() & (df["satisfaction_score"] <= 2)
    segment_mask = high_cost_mask & low_sat_mask
    high_cost_low_sat_count = int(segment_mask.sum())
    if high_cost_low_sat_count == 0:
        high_cost_low_sat_reopen_pct = 0.0
    else:
        high_cost_low_sat_reopen_pct = safe_percentage(
            df.loc[segment_mask, "reopened"].sum(), high_cost_low_sat_count
        )

    # Distribution metrics
    resolution_median = float(df["resolution_minutes"].median())
    resolution_std = safe_std(df["resolution_minutes"])
    satisfaction_mean = safe_mean(df["satisfaction_score"].dropna())
    satisfaction_missing_count = int(df["satisfaction_score"].isna().sum())

    # Agent concentration
    unique_agent_count = int(df["agent_id"].nunique())
    top_agent_ticket_count = int(df["agent_id"].value_counts().iloc[0])
    top_agent_ticket_share_pct = safe_percentage(top_agent_ticket_count, ticket_count)

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

    # Write findings JSON
    with open(findings_path, "w", encoding="utf-8") as f:
        json.dump(findings, f, ensure_ascii=False, separators=(',', ':'))

if __name__ == "__main__":
    main()
