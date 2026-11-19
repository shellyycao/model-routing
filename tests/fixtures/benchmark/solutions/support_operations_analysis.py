# SYNTHETIC_FIXTURE - independent pandas follower for the two-file project.
import pandas as pd


def analyze(df: pd.DataFrame, bug=None) -> dict:
    m = {"ticket_count": len(df), "mean_resolution_minutes": df["resolution_minutes"].mean(),
         "total_labor_cost": df["labor_cost"].sum()}
    by_team = df.groupby("team")["labor_cost"].sum()
    for team in ["Alpha", "Beta", "Gamma"]:
        m[f"labor_cost_{team.lower()}"] = by_team[team]
    by_channel = df.groupby("channel")["resolution_minutes"].mean()
    for channel in ["email", "chat", "phone"]:
        m[f"resolution_{channel}"] = by_channel[channel]
    rates = df.groupby("channel")["reopened"].mean() * 100
    m["reopen_rate_email_pct"], m["reopen_rate_chat_pct"] = rates["email"], rates["chat"]
    m["email_vs_chat_reopen_change_pct"] = ((m["reopen_rate_email_pct"] - m["reopen_rate_chat_pct"])
                                               / m["reopen_rate_chat_pct"] * 100)
    seg = df[(df["labor_cost"] >= 100) & df["satisfaction_score"].notna()
             & (df["satisfaction_score"] <= 2)]
    m["high_cost_low_sat_count"] = len(seg)
    m["high_cost_low_sat_reopen_pct"] = seg["reopened"].mean() * 100
    m["resolution_median"] = df["resolution_minutes"].median()
    m["resolution_std"] = df["resolution_minutes"].std()
    m["satisfaction_mean"] = df["satisfaction_score"].mean()
    m["satisfaction_missing_count"] = df["satisfaction_score"].isna().sum()
    counts = df.groupby("agent_id").size()
    m["unique_agent_count"] = df["agent_id"].nunique()
    m["top_agent_ticket_count"] = counts.max()
    m["top_agent_ticket_share_pct"] = m["top_agent_ticket_count"] / m["ticket_count"] * 100
    return {k: float(v) for k, v in m.items()}
