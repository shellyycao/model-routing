import json
import os
import re

import numpy as np
import pandas as pd

INPUT_DIR = os.environ["INPUT_DIR"]
OUTPUT_DIR = os.environ["OUTPUT_DIR"]
os.makedirs(OUTPUT_DIR, exist_ok=True)

MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}

TEAM_MAP = {
    "alpha": "Alpha", "team alpha": "Alpha",
    "beta": "Beta", "team beta": "Beta",
    "gamma": "Gamma", "team gamma": "Gamma",
}
REGION_MAP = {"east": "East", "e": "East", "west": "West", "w": "West"}
CHANNEL_MAP = {
    "email": "email", "e-mail": "email",
    "chat": "chat", "live chat": "chat",
    "phone": "phone", "call": "phone",
}
REOPENED_MAP = {
    "yes": 1, "y": 1, "true": 1, "1": 1,
    "no": 0, "n": 0, "false": 0, "0": 0,
}


def read_text_csv(path):
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df.columns = [str(c).strip() for c in df.columns]
    for col in df.columns:
        df[col] = df[col].map(lambda v: v.strip() if isinstance(v, str) else v)
        df[col] = df[col].map(
            lambda v: np.nan if (pd.isna(v) or str(v).strip().lower() in MISSING_TOKENS) else v
        )
    return df


def parse_cost(v):
    if pd.isna(v):
        return np.nan
    s = str(v).replace("$", "").replace(",", "")
    s = re.sub(r"(?i)usd", "", s).strip()
    try:
        val = float(s)
    except ValueError:
        return np.nan
    return val if np.isfinite(val) else np.nan


def parse_resolution(v):
    if pd.isna(v):
        return np.nan
    s = re.sub(r"(?i)\s*(minutes|min)\s*$", "", str(v).strip()).strip()
    if not re.fullmatch(r"\d+", s):
        return np.nan
    n = int(s)
    return n if 1 <= n <= 480 else np.nan


def parse_satisfaction(v):
    if pd.isna(v):
        return pd.NA
    s = str(v).strip()
    if re.fullmatch(r"[1-5]", s):
        return int(s)
    return pd.NA


summary = {}

# R1: read both files as text, strip whitespace, normalise missing tokens
tickets = read_text_csv(os.path.join(INPUT_DIR, "tickets.csv"))
agents = read_text_csv(os.path.join(INPUT_DIR, "agents.csv"))
summary["raw_rows"] = int(len(tickets))
summary["agents_raw_rows"] = int(len(agents))

# R2: deduplicate tickets by ticket_id, keep first in raw-file order (before any filtering)
before = len(tickets)
tickets = tickets.drop_duplicates(subset="ticket_id", keep="first")
summary["duplicate_ticket_id_removed"] = int(before - len(tickets))
before = len(tickets)
tickets = tickets[tickets["ticket_id"].notna()].copy()
summary["missing_ticket_id_dropped"] = int(before - len(tickets))

# R3: normalise agent_id to upper case, deduplicate roster keeping first
agents["agent_id"] = agents["agent_id"].map(lambda v: str(v).upper() if pd.notna(v) else v)
agents = agents[agents["agent_id"].notna()].copy()
before = len(agents)
agents = agents.drop_duplicates(subset="agent_id", keep="first")
summary["agents_duplicate_agent_id_removed"] = int(before - len(agents))

# R4: normalise team/region/hourly_cost; exclude invalid roster rows or cost <= 0
agents["team"] = agents["team"].map(lambda v: TEAM_MAP.get(str(v).strip().lower()) if pd.notna(v) else np.nan)
agents["region"] = agents["region"].map(lambda v: REGION_MAP.get(str(v).strip().lower()) if pd.notna(v) else np.nan)
agents["hourly_cost"] = agents["hourly_cost"].map(parse_cost)
before = len(agents)
agents = agents.dropna(subset=["team", "region", "hourly_cost"])
agents = agents[agents["hourly_cost"] > 0].copy()
summary["agents_invalid_rows_excluded"] = int(before - len(agents))

# R5: upper-case ticket agent_id and inner-join to cleaned roster
tickets["agent_id"] = tickets["agent_id"].map(lambda v: str(v).upper() if pd.notna(v) else v)
merged = tickets.merge(agents, on="agent_id", how="inner")
summary["tickets_without_matching_agent_dropped"] = int(len(tickets) - len(merged))

# R6: normalise channel, drop invalid
merged["channel"] = merged["channel"].map(lambda v: CHANNEL_MAP.get(str(v).strip().lower()) if pd.notna(v) else np.nan)
before = len(merged)
merged = merged[merged["channel"].notna()].copy()
summary["invalid_channel_dropped"] = int(before - len(merged))

# R7: parse resolution_minutes (strip trailing 'min'/'minutes', whole number 1-480), drop invalid
merged["resolution_minutes"] = merged["resolution_minutes"].map(parse_resolution)
before = len(merged)
merged = merged[merged["resolution_minutes"].notna()].copy()
merged["resolution_minutes"] = merged["resolution_minutes"].astype(int)
summary["invalid_resolution_minutes_dropped"] = int(before - len(merged))

# R8: satisfaction_score 1-5; invalid/missing -> empty, row kept
parsed_sat = merged["satisfaction_score"].map(parse_satisfaction)
summary["satisfaction_score_emptied"] = int(parsed_sat.isna().sum())
merged["satisfaction_score"] = parsed_sat.astype("Int64")

# R9: reopened -> 1/0, drop invalid or missing
merged["reopened"] = merged["reopened"].map(lambda v: REOPENED_MAP.get(str(v).strip().lower()) if pd.notna(v) else np.nan)
before = len(merged)
merged = merged[merged["reopened"].notna()].copy()
merged["reopened"] = merged["reopened"].astype(int)
summary["invalid_reopened_dropped"] = int(before - len(merged))

# R10: labor_cost
merged["labor_cost"] = (merged["resolution_minutes"] / 60.0 * merged["hourly_cost"]).round(2)

# R11: select columns, sort by ticket_id, write without index
out = merged[[
    "ticket_id", "agent_id", "team", "region", "channel",
    "resolution_minutes", "satisfaction_score", "reopened",
    "hourly_cost", "labor_cost",
]].copy()
out = out.sort_values("ticket_id", kind="mergesort").reset_index(drop=True)
out["team"] = pd.Categorical(out["team"], categories=["Alpha", "Beta", "Gamma"])
out["region"] = pd.Categorical(out["region"], categories=["East", "West"])
out["channel"] = pd.Categorical(out["channel"], categories=["email", "chat", "phone"])
out["hourly_cost"] = out["hourly_cost"].astype(float)
out["labor_cost"] = out["labor_cost"].astype(float)

out_path = os.path.join(OUTPUT_DIR, "cleaned.csv")
out.to_csv(out_path, index=False)

summary["cleaned_rows"] = int(len(out))
with open(os.path.join(OUTPUT_DIR, "cleaning_summary.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

print(f"cleaned.csv written: {summary['cleaned_rows']} rows (from {summary['raw_rows']} raw rows)")
