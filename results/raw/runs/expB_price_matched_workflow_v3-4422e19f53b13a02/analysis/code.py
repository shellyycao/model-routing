import json
import math
import os

import pandas as pd


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    df = pd.read_csv(input_path)

    findings = {}

    # q1: overall
    ticket_count = int(len(df))
    findings["ticket_count"] = float(ticket_count)
    findings["mean_resolution_minutes"] = float(df["resolution_minutes"].mean())
    findings["total_labor_cost"] = float(df["labor_cost"].sum())

    # q2: total labor_cost by team
    team_cost = df.groupby("team")["labor_cost"].sum()
    for team, key in (("Alpha", "labor_cost_alpha"),
                      ("Beta", "labor_cost_beta"),
                      ("Gamma", "labor_cost_gamma")):
        findings[key] = float(team_cost.get(team, 0.0))

    # q3: mean resolution_minutes by channel
    chan_res = df.groupby("channel")["resolution_minutes"].mean()
    for ch, key in (("email", "resolution_email"),
                    ("chat", "resolution_chat"),
                    ("phone", "resolution_phone")):
        findings[key] = float(chan_res.get(ch, 0.0))

    # q4: reopen rates for email and chat, and relative change
    def reopen_pct(sub):
        if len(sub) == 0:
            return 0.0
        return float(sub["reopened"].mean() * 100.0)

    email_pct = reopen_pct(df[df["channel"] == "email"])
    chat_pct = reopen_pct(df[df["channel"] == "chat"])
    findings["reopen_rate_email_pct"] = email_pct
    findings["reopen_rate_chat_pct"] = chat_pct
    if chat_pct != 0.0:
        findings["email_vs_chat_reopen_change_pct"] = float(
            (email_pct - chat_pct) / chat_pct * 100.0)
    else:
        findings["email_vs_chat_reopen_change_pct"] = 0.0

    # q5: high-cost (>=100) and low-satisfaction (<=2, non-missing) segment
    sat = df["satisfaction_score"]
    seg_mask = (df["labor_cost"] >= 100) & sat.notna() & (sat <= 2)
    seg = df[seg_mask]
    seg_count = int(len(seg))
    findings["high_cost_low_sat_count"] = float(seg_count)
    if seg_count > 0:
        findings["high_cost_low_sat_reopen_pct"] = float(seg["reopened"].mean() * 100.0)
    else:
        findings["high_cost_low_sat_reopen_pct"] = 0.0

    # q6: distribution metrics
    findings["resolution_median"] = float(df["resolution_minutes"].median())
    findings["resolution_std"] = float(df["resolution_minutes"].std(ddof=1))
    findings["satisfaction_mean"] = float(sat.mean())  # NaN skipped by default
    findings["satisfaction_missing_count"] = float(int(sat.isna().sum()))

    # q7: agent concentration
    unique_agents = int(df["agent_id"].nunique())
    top_count = int(df["agent_id"].value_counts().max()) if ticket_count > 0 else 0
    findings["unique_agent_count"] = float(unique_agents)
    findings["top_agent_ticket_count"] = float(top_count)
    if ticket_count > 0:
        findings["top_agent_ticket_share_pct"] = float(top_count / ticket_count * 100.0)
    else:
        findings["top_agent_ticket_share_pct"] = 0.0

    # Safety: guarantee finite numeric values only
    for key, value in findings.items():
        if not isinstance(value, (int, float)) or not math.isfinite(value):
            findings[key] = 0.0

    os.makedirs(os.environ["OUTPUT_DIR"], exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(findings, f, indent=2)


if __name__ == "__main__":
    main()
