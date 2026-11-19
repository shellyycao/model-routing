import os
import json
import pandas as pd
import numpy as np

def safe_mean(series):
    """Return mean of a pandas Series as a float, or 0.0 if empty."""
    if len(series) == 0:
        return 0.0
    return float(series.mean())

def safe_median(series):
    """Return median of a pandas Series as a float, or 0.0 if empty."""
    if len(series) == 0:
        return 0.0
    return float(series.median())

def safe_std(series):
    """Return sample standard deviation of a pandas Series as a float, or 0.0 if undefined."""
    if len(series) <= 1:
        return 0.0
    std = series.std(ddof=1)
    if pd.isna(std):
        return 0.0
    return float(std)

def main():
    # Paths from environment variables
    input_dir = os.getenv('INPUT_DIR')
    output_dir = os.getenv('OUTPUT_DIR')
    if not input_dir or not output_dir:
        raise RuntimeError('INPUT_DIR and OUTPUT_DIR environment variables must be set')

    cleaned_path = os.path.join(input_dir, 'cleaned.csv')
    df = pd.read_csv(cleaned_path)

    # Ensure correct dtypes for calculations
    # satisfaction_score may contain missing values – keep as float (NaN) for pandas handling
    df['satisfaction_score'] = pd.to_numeric(df['satisfaction_score'], errors='coerce')

    # Overall metrics
    ticket_count = int(len(df))
    mean_resolution_minutes = safe_mean(df['resolution_minutes'])
    total_labor_cost = float(df['labor_cost'].sum())

    # Team labor cost totals
    labor_cost_alpha = float(df.loc[df['team'] == 'Alpha', 'labor_cost'].sum())
    labor_cost_beta = float(df.loc[df['team'] == 'Beta', 'labor_cost'].sum())
    labor_cost_gamma = float(df.loc[df['team'] == 'Gamma', 'labor_cost'].sum())

    # Channel mean resolution minutes
    resolution_email = safe_mean(df.loc[df['channel'] == 'email', 'resolution_minutes'])
    resolution_chat = safe_mean(df.loc[df['channel'] == 'chat', 'resolution_minutes'])
    resolution_phone = safe_mean(df.loc[df['channel'] == 'phone', 'resolution_minutes'])

    # Reopen rates per channel (percentage)
    def reopen_rate_pct(channel_name):
        sub = df.loc[df['channel'] == channel_name]
        if len(sub) == 0:
            return 0.0
        return float(sub['reopened'].mean() * 100)

    reopen_rate_email_pct = reopen_rate_pct('email')
    reopen_rate_chat_pct = reopen_rate_pct('chat')
    # Change metric – avoid division by zero
    if reopen_rate_chat_pct == 0:
        email_vs_chat_reopen_change_pct = 0.0
    else:
        email_vs_chat_reopen_change_pct = ((reopen_rate_email_pct - reopen_rate_chat_pct) / reopen_rate_chat_pct) * 100

    # High‑cost low‑satisfaction segment
    high_cost_mask = df['labor_cost'] >= 100
    low_sat_mask = df['satisfaction_score'].notna() & (df['satisfaction_score'] <= 2)
    high_low_df = df[high_cost_mask & low_sat_mask]
    high_cost_low_sat_count = int(len(high_low_df))
    if high_cost_low_sat_count == 0:
        high_cost_low_sat_reopen_pct = 0.0
    else:
        high_cost_low_sat_reopen_pct = float(high_low_df['reopened'].mean() * 100)

    # Distribution metrics
    resolution_median = safe_median(df['resolution_minutes'])
    resolution_std = safe_std(df['resolution_minutes'])
    satisfaction_mean = safe_mean(df['satisfaction_score'].dropna())
    satisfaction_missing_count = int(df['satisfaction_score'].isna().sum())

    # Agent concentration
    unique_agent_count = int(df['agent_id'].nunique())
    top_agent_ticket_count = int(df['agent_id'].value_counts().iloc[0])
    top_agent_ticket_share_pct = (top_agent_ticket_count / ticket_count) * 100 if ticket_count > 0 else 0.0

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

    # Write findings.json
    output_path = os.path.join(output_dir, 'findings.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(findings, f, ensure_ascii=False, allow_nan=False)

if __name__ == "__main__":
    main()
