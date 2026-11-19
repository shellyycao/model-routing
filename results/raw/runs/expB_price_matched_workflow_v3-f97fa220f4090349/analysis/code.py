import json
import os

import numpy as np
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
    team_cost = df.groupby("team")["labor_cost"].sum()
    for team, key in (("Alpha", "labor_cost_alpha"),
                      ("Beta", "labor_cost_beta"),
                      ("Gamma", "labor_cost_gamma")):
        findings[key] = float(team_cost.get(team, 0.0))

    # q3: mean resolution minutes per channel
    chan_res = df.groupby("channel")["resolution_minutes"].mean()
    for channel, key in (("email", "resolution_email"),
                         ("chat", "resolution_chat"),
                         ("phone", "resolution_phone")):
        findings[key] = float(chan_res.get(channel, 0.0))

    # q4: reopen rates for email and chat, and relative change
    def reopen_pct(sub):
        if len(sub) == 0:
            return 0.0
        return float(sub["reopened"].mean() * 100.0)

    email_rate = reopen_pct(df[df["channel"] == "email"])
    chat_rate = reopen_pct(df[df["channel"] == "chat"])
    findings["reopen_rate_email_pct"] = email_rate
    findings["reopen_rate_chat_pct"] = chat_rate
    if chat_rate != 0.0:
        findings["email_vs_chat_reopen_change_pct"] = float(
            (email_rate - chat_rate) / chat_rate * 100.0)
    else:
        findings["email_vs_chat_reopen_change_pct"] = 0.0

    # q5: high-cost (>= 100) tickets with non-missing satisfaction <= 2
    seg = df[(df["labor_cost"] >= 100) &
             (df["satisfaction_score"].notna()) &
             (df["satisfaction_score"] <= 2)]
    findings["high_cost_low_sat_count"] = int(len(seg))
    findings["high_cost_low_sat_reopen_pct"] = reopen_pct(seg)

    # q6: distribution of resolution time and satisfaction
    findings["resolution_median"] = float(df["resolution_minutes"].median())
    findings["resolution_std"] = float(df["resolution_minutes"].std(ddof=1))
    findings["satisfaction_mean"] = float(df["satisfaction_score"].mean())
    findings["satisfaction_missing_count"] = int(df["satisfaction_score"].isna().sum())

    # q7: agent concentration
    findings["unique_agent_count"] = int(df["agent_id"].nunique())
    top_count = int(df["agent_id"].value_counts().max()) if ticket_count > 0 else 0
    findings["top_agent_ticket_count"] = top_count
    findings["top_agent_ticket_share_pct"] = (
        float(top_count / ticket_count * 100.0) if ticket_count > 0 else 0.0)

    # safety: guarantee every value is a finite JSON number
    for key, value in findings.items():
        if isinstance(value, float) and not np.isfinite(value):
            findings[key] = 0.0

    os.makedirs(os.environ["OUTPUT_DIR"], exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(findings, f, indent=2)


if __name__ == "__main__":
    main()
