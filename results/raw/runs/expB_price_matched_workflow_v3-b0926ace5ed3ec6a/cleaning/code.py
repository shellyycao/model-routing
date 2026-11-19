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


def clean_cell(x):
    if not isinstance(x, str):
        return x
    s = x.strip()
    if s.lower() in MISSING_TOKENS:
        return pd.NA
    return s


def read_text_csv(path):
    df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    df.columns = [str(c).strip() for c in df.columns]
    for col in df.columns:
        df[col] = df[col].map(clean_cell)
    return df


def parse_hourly_cost(x):
    if x is None or pd.isna(x):
        return np.nan
    s = re.sub(r"(?i)usd", "", str(x))
    s = s.replace("$", "").replace(",", "").strip()
    if not re.fullmatch(r"\d+(\.\d+)?", s):
        return np.nan
    return float(s)


def parse_minutes(x):
    if x is None or pd.isna(x):
        return None
    s = re.sub(r"(?i)\s*(minutes|min)\s*$", "", str(x)).strip()
    if not re.fullmatch(r"\d+", s):
        return None
    v = int(s)
    return v if 1 <= v <= 480 else None


def parse_satisfaction(x):
    if x is None or pd.isna(x):
        return pd.NA
    s = str(x).strip()
    if re.fullmatch(r"\d+", s):
        v = int(s)
        if 1 <= v <= 5:
            return v
    return pd.NA


summary = {}

# R1: read both files as text, strip whitespace, standardise missing tokens.
tickets = read_text_csv(os.path.join(INPUT_DIR, "tickets.csv"))
agents = read_text_csv(os.path.join(INPUT_DIR, "agents.csv"))
summary["raw_rows"] = int(len(tickets))
summary["agents_raw_rows"] = int(len(agents))

# R2: drop duplicate ticket_id rows (keep first in raw-file order) before filtering.
n0 = len(tickets)
tickets = tickets.drop_duplicates(subset="ticket_id", keep="first")
summary["tickets_duplicate_ticket_id_removed"] = int(n0 - len(tickets))
n0 = len(tickets)
tickets = tickets[tickets["ticket_id"].notna()]
summary["tickets_missing_ticket_id_removed"] = int(n0 - len(tickets))

# R3: normalise roster agent_id to upper case, drop duplicates (keep first).
agents["agent_id"] = agents["agent_id"].str.upper()
n0 = len(agents)
agents = agents.drop_duplicates(subset="agent_id", keep="first")
summary["agents_duplicate_agent_id_removed"] = int(n0 - len(agents))

# R4: normalise team/region, parse hourly_cost, exclude invalid roster rows.
agents["team"] = agents["team"].map(lambda v: TEAM_MAP.get(str(v).lower()) if pd.notna(v) else None)
agents["region"] = agents["region"].map(lambda v: REGION_MAP.get(str(v).lower()) if pd.notna(v) else None)
agents["hourly_cost"] = pd.to_numeric(agents["hourly_cost"].map(parse_hourly_cost), errors="coerce")
valid_agent = (
    agents["agent_id"].notna()
    & agents["team"].notna()
    & agents["region"].notna()
    & agents["hourly_cost"].notna()
    & (agents["hourly_cost"] > 0)
)
summary["agents_invalid_rows_removed"] = int((~valid_agent).sum())
agents = agents.loc[valid_agent, ["agent_id", "team", "region", "hourly_cost"]].copy()

# R5: normalise ticket agent_id and inner-join to the cleaned roster.
tickets["agent_id"] = tickets["agent_id"].str.upper()
n0 = len(tickets)
df = tickets.merge(agents, on="agent_id", how="inner")
summary["tickets_without_matching_agent_removed"] = int(n0 - len(df))

# R6: normalise channel, drop invalid.
df["channel"] = df["channel"].map(lambda v: CHANNEL_MAP.get(str(v).lower()) if pd.notna(v) else None)
n0 = len(df)
df = df[df["channel"].notna()].copy()
summary["tickets_invalid_channel_removed"] = int(n0 - len(df))

# R7: parse resolution_minutes (strip trailing 'min'/'minutes'), keep 1..480, drop invalid.
df["resolution_minutes"] = df["resolution_minutes"].map(parse_minutes)
n0 = len(df)
df = df[df["resolution_minutes"].notna()].copy()
df["resolution_minutes"] = df["resolution_minutes"].astype(int)
summary["tickets_invalid_resolution_minutes_removed"] = int(n0 - len(df))

# R8: satisfaction_score 1..5; invalid/missing becomes empty (nullable Int64), row kept.
df["satisfaction_score"] = df["satisfaction_score"].map(parse_satisfaction).astype("Int64")
summary["tickets_satisfaction_score_set_empty"] = int(df["satisfaction_score"].isna().sum())

# R9: map reopened to 0/1, drop invalid or missing.
df["reopened"] = df["reopened"].map(lambda v: REOPENED_MAP.get(str(v).lower()) if pd.notna(v) else None)
n0 = len(df)
df = df[df["reopened"].notna()].copy()
df["reopened"] = df["reopened"].astype(int)
summary["tickets_invalid_reopened_removed"] = int(n0 - len(df))

# R10: labour cost.
df["labor_cost"] = (df["resolution_minutes"] / 60.0 * df["hourly_cost"]).round(2)

# R11: final column order, dtypes, sort by ticket_id, write CSV without index.
out = df[[
    "ticket_id", "agent_id", "team", "region", "channel",
    "resolution_minutes", "satisfaction_score", "reopened",
    "hourly_cost", "labor_cost",
]].copy()
out["team"] = pd.Categorical(out["team"], categories=["Alpha", "Beta", "Gamma"])
out["region"] = pd.Categorical(out["region"], categories=["East", "West"])
out["channel"] = pd.Categorical(out["channel"], categories=["email", "chat", "phone"])
out["hourly_cost"] = out["hourly_cost"].astype(float)
out["labor_cost"] = out["labor_cost"].astype(float)
out = out.sort_values("ticket_id", kind="mergesort").reset_index(drop=True)

out.to_csv(os.path.join(OUTPUT_DIR, "cleaned.csv"), index=False)
summary["cleaned_rows"] = int(len(out))

with open(os.path.join(OUTPUT_DIR, "cleaning_summary.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)
