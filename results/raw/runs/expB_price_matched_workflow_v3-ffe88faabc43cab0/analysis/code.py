import json
import os

import numpy as np
import pandas as pd


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    df = pd.read_csv(input_path)

    # Coerce numeric columns to safe dtypes (satisfaction_score may contain blanks -> NaN).
    df["resolution_minutes"] = pd.to_numeric(df["resolution_minutes"], errors="coerce")
    df["labor_cost"] = pd.to_numeric(df["labor_cost"], errors="coerce")
    df["reopened"] = pd.to_numeric(df["reopened"], errors="coerce")
    df["satisfaction_score"] = pd.to_numeric(df["satisfaction_score"], errors="coerce")

    findings = {}

    # q1: overall volume, speed and cost.
    ticket_count = int(len(df))
    findings["ticket_count"] = ticket_count
    findings["mean_resolution_minutes"] = float(df["resolution_minutes"].mean())
    findings["total_labor_cost"] = float(df["labor_cost"].sum())

    # q2: total labor cost per team.
    team_cost = df.groupby("team")["labor_cost"].sum()
    findings["labor_cost_alpha"] = float(team_cost.get("Alpha", 0.0))
    findings["labor_cost_beta"] = float(team_cost.get("Beta", 0.0))
    findings["labor_cost_gamma"] = float(team_cost.get("Gamma", 0.0))

    # q3: mean resolution minutes per channel.
    chan_res = df.groupby("channel")["resolution_minutes"].mean()
    findings["resolution_email"] = float(chan_res.get("email", 0.0))
    findings["resolution_chat"] = float(chan_res.get("chat", 0.0))
    findings["resolution_phone"] = float(chan_res.get("phone", 0.0))

    # q4: reopen rates for email and chat, and relative change of email vs chat.
    email_df = df[df["channel"] == "email"]
    chat_df = df[df["channel"] == "chat"]
    email_pct = float(email_df["reopened"].mean() * 100.0) if len(email_df) > 0 else 0.0
    chat_pct = float(chat_df["reopened"].mean() * 100.0) if len(chat_df) > 0 else 0.0
    findings["reopen_rate_email_pct"] = email_pct
    findings["reopen_rate_chat_pct"] = chat_pct
    if chat_pct == 0.0:
        # Convention: no chat reopens -> relative change defined as 0 to keep the metric finite.
        findings["email_vs_chat_reopen_change_pct"] = 0.0
    else:
        findings["email_vs_chat_reopen_change_pct"] = (email_pct - chat_pct) / chat_pct * 100.0

    # q5: high-cost (labor_cost >= 100) and low-satisfaction (non-missing score <= 2) segment.
    seg_mask = (df["labor_cost"] >= 100) & df["satisfaction_score"].notna() & (df["satisfaction_score"] <= 2)
    seg_df = df[seg_mask]
    seg_count = int(len(seg_df))
    findings["high_cost_low_sat_count"] = seg_count
    findings["high_cost_low_sat_reopen_pct"] = float(seg_df["reopened"].mean() * 100.0) if seg_count > 0 else 0.0

    # q6: distribution metrics.
    findings["resolution_median"] = float(df["resolution_minutes"].median())
    findings["resolution_std"] = float(df["resolution_minutes"].std(ddof=1)) if ticket_count >= 2 else 0.0
    sat = df["satisfaction_score"].dropna()
    findings["satisfaction_mean"] = float(sat.mean()) if len(sat) > 0 else 0.0
    findings["satisfaction_missing_count"] = int(df["satisfaction_score"].isna().sum())

    # q7: agent concentration.
    findings["unique_agent_count"] = int(df["agent_id"].nunique())
    top_count = int(df["agent_id"].value_counts().max()) if ticket_count > 0 else 0
    findings["top_agent_ticket_count"] = top_count
    findings["top_agent_ticket_share_pct"] = (top_count / ticket_count * 100.0) if ticket_count > 0 else 0.0

    # Final safety check: every metric must be a finite number.
    for key, value in findings.items():
        if not np.isfinite(float(value)):
            raise ValueError("Non-finite metric %s: %r" % (key, value))

    with open(output_path, "w") as f:
        json.dump(findings, f, indent=2, allow_nan=False)


if __name__ == "__main__":
    main()
