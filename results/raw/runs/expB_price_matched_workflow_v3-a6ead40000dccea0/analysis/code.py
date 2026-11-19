import json
import os

import numpy as np
import pandas as pd


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    df = pd.read_csv(input_path)

    findings = {}

    # q1 - Overall: ticket count, mean resolution minutes, total labor cost
    ticket_count = int(len(df))
    findings["ticket_count"] = ticket_count
    findings["mean_resolution_minutes"] = float(df["resolution_minutes"].mean())
    findings["total_labor_cost"] = float(df["labor_cost"].sum())

    # q2 - Team comparison: total labor cost per team
    team_cost = df.groupby("team")["labor_cost"].sum()
    findings["labor_cost_alpha"] = float(team_cost.get("Alpha", 0.0))
    findings["labor_cost_beta"] = float(team_cost.get("Beta", 0.0))
    findings["labor_cost_gamma"] = float(team_cost.get("Gamma", 0.0))

    # q3 - Channel comparison: mean resolution minutes per channel
    channel_resolution = df.groupby("channel")["resolution_minutes"].mean()
    findings["resolution_email"] = float(channel_resolution.get("email", 0.0))
    findings["resolution_chat"] = float(channel_resolution.get("chat", 0.0))
    findings["resolution_phone"] = float(channel_resolution.get("phone", 0.0))

    # q4 - Reopen rates for email and chat, plus relative change of email vs chat
    email_reopened = df.loc[df["channel"] == "email", "reopened"]
    chat_reopened = df.loc[df["channel"] == "chat", "reopened"]
    reopen_rate_email_pct = float(email_reopened.mean()) * 100.0 if len(email_reopened) else 0.0
    reopen_rate_chat_pct = float(chat_reopened.mean()) * 100.0 if len(chat_reopened) else 0.0
    findings["reopen_rate_email_pct"] = reopen_rate_email_pct
    findings["reopen_rate_chat_pct"] = reopen_rate_chat_pct
    if reopen_rate_chat_pct != 0.0:
        findings["email_vs_chat_reopen_change_pct"] = (
            (reopen_rate_email_pct - reopen_rate_chat_pct) / reopen_rate_chat_pct * 100.0
        )
    else:
        findings["email_vs_chat_reopen_change_pct"] = 0.0

    # q5 - High-cost (labor_cost >= 100) and low-satisfaction (non-missing score <= 2) segment
    segment = df[
        (df["labor_cost"] >= 100.0)
        & (df["satisfaction_score"].notna())
        & (df["satisfaction_score"] <= 2)
    ]
    seg_count = int(len(segment))
    findings["high_cost_low_sat_count"] = seg_count
    findings["high_cost_low_sat_reopen_pct"] = (
        float(segment["reopened"].mean()) * 100.0 if seg_count else 0.0
    )

    # q6 - Distribution: median, sample std (ddof=1), satisfaction mean and missing count
    findings["resolution_median"] = float(df["resolution_minutes"].median())
    findings["resolution_std"] = float(df["resolution_minutes"].std(ddof=1))
    satisfaction = df["satisfaction_score"].dropna()
    findings["satisfaction_mean"] = float(satisfaction.mean()) if len(satisfaction) else 0.0
    findings["satisfaction_missing_count"] = int(df["satisfaction_score"].isna().sum())

    # q7 - Agent concentration
    findings["unique_agent_count"] = int(df["agent_id"].nunique())
    top_agent_ticket_count = int(df["agent_id"].value_counts().max())
    findings["top_agent_ticket_count"] = top_agent_ticket_count
    findings["top_agent_ticket_share_pct"] = (
        top_agent_ticket_count / ticket_count * 100.0 if ticket_count else 0.0
    )

    # Safety pass: guarantee a flat object of finite numeric values
    clean = {}
    for key, value in findings.items():
        if isinstance(value, (int, np.integer)):
            clean[key] = int(value)
        else:
            v = float(value)
            clean[key] = v if np.isfinite(v) else 0.0

    with open(output_path, "w") as fh:
        json.dump(clean, fh, indent=2)


if __name__ == "__main__":
    main()
