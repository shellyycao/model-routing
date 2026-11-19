import json
import math
import os

import pandas as pd


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
    os.makedirs(os.environ["OUTPUT_DIR"], exist_ok=True)

    df = pd.read_csv(input_path)

    findings = {}

    # q1: overall volume, speed and cost
    ticket_count = int(len(df))
    findings["ticket_count"] = ticket_count
    findings["mean_resolution_minutes"] = float(df["resolution_minutes"].mean())
    findings["total_labor_cost"] = float(df["labor_cost"].sum())

    # q2: total labor cost per team
    team_cost = df.groupby("team")["labor_cost"].sum()
    findings["labor_cost_alpha"] = float(team_cost.get("Alpha", 0.0))
    findings["labor_cost_beta"] = float(team_cost.get("Beta", 0.0))
    findings["labor_cost_gamma"] = float(team_cost.get("Gamma", 0.0))

    # q3: mean resolution minutes per channel
    channel_res = df.groupby("channel")["resolution_minutes"].mean()
    findings["resolution_email"] = float(channel_res.get("email", 0.0))
    findings["resolution_chat"] = float(channel_res.get("chat", 0.0))
    findings["resolution_phone"] = float(channel_res.get("phone", 0.0))

    # q4: reopen rates for email and chat, and relative change of email vs chat
    reopen_rate = df.groupby("channel")["reopened"].mean() * 100.0
    email_rate = float(reopen_rate.get("email", 0.0))
    chat_rate = float(reopen_rate.get("chat", 0.0))
    findings["reopen_rate_email_pct"] = email_rate
    findings["reopen_rate_chat_pct"] = chat_rate
    if chat_rate > 0.0:
        findings["email_vs_chat_reopen_change_pct"] = (email_rate - chat_rate) / chat_rate * 100.0
    else:
        findings["email_vs_chat_reopen_change_pct"] = 0.0

    # q5: high-cost (labor_cost >= 100) and low-satisfaction (score <= 2, non-missing) segment
    seg_mask = (
        (df["labor_cost"] >= 100)
        & df["satisfaction_score"].notna()
        & (df["satisfaction_score"] <= 2)
    )
    seg = df[seg_mask]
    seg_count = int(len(seg))
    findings["high_cost_low_sat_count"] = seg_count
    if seg_count > 0:
        findings["high_cost_low_sat_reopen_pct"] = float(seg["reopened"].mean() * 100.0)
    else:
        findings["high_cost_low_sat_reopen_pct"] = 0.0

    # q6: distribution metrics
    findings["resolution_median"] = float(df["resolution_minutes"].median())
    findings["resolution_std"] = float(df["resolution_minutes"].std(ddof=1))
    findings["satisfaction_mean"] = float(df["satisfaction_score"].mean())
    findings["satisfaction_missing_count"] = int(df["satisfaction_score"].isna().sum())

    # q7: agent concentration
    findings["unique_agent_count"] = int(df["agent_id"].nunique())
    agent_counts = df["agent_id"].value_counts()
    top_count = int(agent_counts.iloc[0]) if len(agent_counts) > 0 else 0
    findings["top_agent_ticket_count"] = top_count
    if ticket_count > 0:
        findings["top_agent_ticket_share_pct"] = top_count / ticket_count * 100.0
    else:
        findings["top_agent_ticket_share_pct"] = 0.0

    # Guarantee a flat object of finite numeric values only
    clean = {}
    for key, value in findings.items():
        if isinstance(value, int):
            clean[key] = value
        else:
            f = float(value)
            clean[key] = f if math.isfinite(f) else 0.0

    with open(output_path, "w") as fh:
        json.dump(clean, fh, indent=2)


if __name__ == "__main__":
    main()
