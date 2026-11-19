import json
import math
import os

import pandas as pd


def to_finite_float(value, fallback=0.0):
    """Convert a value to a finite Python float, falling back if not possible."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return fallback
    if not math.isfinite(v):
        return fallback
    return v


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_dir = os.environ["OUTPUT_DIR"]
    output_path = os.path.join(output_dir, "findings.json")

    df = pd.read_csv(input_path)

    findings = {}

    # q1: overall volume, speed and cost
    ticket_count = int(len(df))
    findings["ticket_count"] = ticket_count
    findings["mean_resolution_minutes"] = to_finite_float(df["resolution_minutes"].mean())
    findings["total_labor_cost"] = to_finite_float(df["labor_cost"].sum())

    # q2: total labor cost per team
    team_cost = df.groupby("team")["labor_cost"].sum()
    findings["labor_cost_alpha"] = to_finite_float(team_cost.get("Alpha", 0.0))
    findings["labor_cost_beta"] = to_finite_float(team_cost.get("Beta", 0.0))
    findings["labor_cost_gamma"] = to_finite_float(team_cost.get("Gamma", 0.0))

    # q3: mean resolution minutes per channel
    channel_resolution = df.groupby("channel")["resolution_minutes"].mean()
    findings["resolution_email"] = to_finite_float(channel_resolution.get("email", 0.0))
    findings["resolution_chat"] = to_finite_float(channel_resolution.get("chat", 0.0))
    findings["resolution_phone"] = to_finite_float(channel_resolution.get("phone", 0.0))

    # q4: reopen rates for email and chat, and relative change of email vs chat
    reopen_rate = df.groupby("channel")["reopened"].mean()
    email_rate = float(reopen_rate.get("email", 0.0))
    chat_rate = float(reopen_rate.get("chat", 0.0))
    findings["reopen_rate_email_pct"] = to_finite_float(email_rate * 100)
    findings["reopen_rate_chat_pct"] = to_finite_float(chat_rate * 100)
    if chat_rate > 0:
        findings["email_vs_chat_reopen_change_pct"] = to_finite_float(
            (email_rate - chat_rate) / chat_rate * 100
        )
    else:
        findings["email_vs_chat_reopen_change_pct"] = 0.0

    # q5: high-cost (labor_cost >= 100) and low-satisfaction (score <= 2, non-missing)
    segment = df[
        (df["labor_cost"] >= 100)
        & (df["satisfaction_score"].notna())
        & (df["satisfaction_score"] <= 2)
    ]
    segment_count = int(len(segment))
    findings["high_cost_low_sat_count"] = segment_count
    if segment_count > 0:
        findings["high_cost_low_sat_reopen_pct"] = to_finite_float(
            segment["reopened"].mean() * 100
        )
    else:
        findings["high_cost_low_sat_reopen_pct"] = 0.0

    # q6: distribution of resolution time and satisfaction
    findings["resolution_median"] = to_finite_float(df["resolution_minutes"].median())
    findings["resolution_std"] = to_finite_float(df["resolution_minutes"].std(ddof=1))
    findings["satisfaction_mean"] = to_finite_float(df["satisfaction_score"].mean())
    findings["satisfaction_missing_count"] = int(df["satisfaction_score"].isna().sum())

    # q7: agent concentration
    agent_ticket_counts = df["agent_id"].value_counts()
    unique_agents = int(df["agent_id"].nunique())
    top_agent_tickets = int(agent_ticket_counts.max()) if len(agent_ticket_counts) > 0 else 0
    findings["unique_agent_count"] = unique_agents
    findings["top_agent_ticket_count"] = top_agent_tickets
    if ticket_count > 0:
        findings["top_agent_ticket_share_pct"] = to_finite_float(
            top_agent_tickets / ticket_count * 100
        )
    else:
        findings["top_agent_ticket_share_pct"] = 0.0

    # Final safety pass: every value must be a native, finite int or float
    clean_findings = {}
    for key, value in findings.items():
        if isinstance(value, bool):
            clean_findings[key] = float(value)
        elif isinstance(value, int):
            clean_findings[key] = value
        else:
            clean_findings[key] = to_finite_float(value)

    os.makedirs(output_dir, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(clean_findings, f)


if __name__ == "__main__":
    main()
