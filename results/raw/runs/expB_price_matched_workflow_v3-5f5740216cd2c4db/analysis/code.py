import json
import math
import os

import pandas as pd


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    df = pd.read_csv(input_path)

    findings = {}

    # q1: overall volume, speed and cost
    ticket_count = int(len(df))
    findings["ticket_count"] = ticket_count
    findings["mean_resolution_minutes"] = float(df["resolution_minutes"].mean())
    findings["total_labor_cost"] = float(df["labor_cost"].sum())

    # q2: total labor cost per team
    team_cost = df.groupby("team", observed=True)["labor_cost"].sum()
    for team in ("Alpha", "Beta", "Gamma"):
        findings["labor_cost_" + team.lower()] = float(team_cost.get(team, 0.0))

    # q3: mean resolution minutes per channel
    chan_res = df.groupby("channel", observed=True)["resolution_minutes"].mean()
    for channel in ("email", "chat", "phone"):
        findings["resolution_" + channel] = float(chan_res.get(channel, 0.0))

    # q4: reopen rates for email and chat, and relative change of email vs chat
    reopen_by_channel = df.groupby("channel", observed=True)["reopened"].mean() * 100.0
    email_rate = float(reopen_by_channel.get("email", 0.0))
    chat_rate = float(reopen_by_channel.get("chat", 0.0))
    findings["reopen_rate_email_pct"] = email_rate
    findings["reopen_rate_chat_pct"] = chat_rate
    if chat_rate != 0.0:
        findings["email_vs_chat_reopen_change_pct"] = (email_rate - chat_rate) / chat_rate * 100.0
    else:
        findings["email_vs_chat_reopen_change_pct"] = 0.0

    # q5: high-cost (>=100) and low-satisfaction (<=2, non-missing) segment
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

    # q6: distribution of resolution time and satisfaction
    findings["resolution_median"] = float(df["resolution_minutes"].median())
    findings["resolution_std"] = float(df["resolution_minutes"].std(ddof=1))
    findings["satisfaction_mean"] = float(df["satisfaction_score"].mean())
    findings["satisfaction_missing_count"] = int(df["satisfaction_score"].isna().sum())

    # q7: agent concentration
    unique_agents = int(df["agent_id"].nunique())
    if unique_agents > 0:
        top_count = int(df["agent_id"].value_counts().iloc[0])
    else:
        top_count = 0
    findings["unique_agent_count"] = unique_agents
    findings["top_agent_ticket_count"] = top_count
    if ticket_count > 0:
        findings["top_agent_ticket_share_pct"] = top_count / ticket_count * 100.0
    else:
        findings["top_agent_ticket_share_pct"] = 0.0

    # Safety: every value must be a finite number
    for key, value in findings.items():
        if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise ValueError("Metric %s is not a finite number: %r" % (key, value))

    os.makedirs(os.environ["OUTPUT_DIR"], exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(findings, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
