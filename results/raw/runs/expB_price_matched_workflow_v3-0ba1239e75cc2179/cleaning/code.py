import os
import re
import json

import numpy as np
import pandas as pd

INPUT_DIR = os.environ["INPUT_DIR"]
OUTPUT_DIR = os.environ["OUTPUT_DIR"]

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
    """R1: read everything as text, strip whitespace, normalise missing tokens."""
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df.columns = [str(c).strip() for c in df.columns]
    for col in df.columns:
        s = df[col].astype(str).str.strip()
        df[col] = s.where(~s.str.lower().isin(MISSING_TOKENS), pd.NA)
    return df


def parse_hourly_cost(value):
    if pd.isna(value):
        return np.nan
    s = re.sub(r"(?i)usd", "", str(value))
    s = s.replace("$", "").replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        return np.nan


def parse_resolution_minutes(value):
    if pd.isna(value):
        return np.nan
    s = re.sub(r"(?i)\s*(?:minutes|min)\s*$", "", str(value)).strip()
    if not re.fullmatch(r"\d+", s):
        return np.nan
    number = int(s)
    return number if 1 <= number <= 480 else np.nan


def parse_satisfaction(value):
    if pd.isna(value):
        return pd.NA
    s = str(value).strip()
    if not re.fullmatch(r"\d+", s):
        return pd.NA
    number = int(s)
    return number if 1 <= number <= 5 else pd.NA


summary = {}

# R1
tickets = read_text_csv(os.path.join(INPUT_DIR, "tickets.csv"))
agents = read_text_csv(os.path.join(INPUT_DIR, "agents.csv"))
summary["raw_rows"] = int(len(tickets))
summary["agents_raw_rows"] = int(len(agents))

# R2: de-duplicate ticket_id before any filtering, keep first in raw-file order
n0 = len(tickets)
tickets = tickets[tickets["ticket_id"].notna()].copy()
summary["tickets_removed_missing_ticket_id"] = int(n0 - len(tickets))
n0 = len(tickets)
tickets = tickets.drop_duplicates(subset="ticket_id", keep="first").copy()
summary["tickets_removed_duplicate_ticket_id"] = int(n0 - len(tickets))

# R3: upper-case agent_id and de-duplicate roster, keep first
n0 = len(agents)
agents = agents[agents["agent_id"].notna()].copy()
summary["agents_removed_missing_agent_id"] = int(n0 - len(agents))
agents["agent_id"] = agents["agent_id"].str.upper()
n0 = len(agents)
agents = agents.drop_duplicates(subset="agent_id", keep="first").copy()
summary["agents_removed_duplicate_agent_id"] = int(n0 - len(agents))

# R4: normalise team/region, parse hourly_cost, drop invalid roster rows
agents["team"] = agents["team"].str.lower().map(TEAM_MAP)
agents["region"] = agents["region"].str.lower().map(REGION_MAP)
agents["hourly_cost"] = agents["hourly_cost"].map(parse_hourly_cost)
valid_agent = (
    agents["team"].notna()
    & agents["region"].notna()
    & agents["hourly_cost"].notna()
    & (agents["hourly_cost"] > 0)
)
summary["agents_removed_invalid_roster_row"] = int((~valid_agent).sum())
agents = agents[valid_agent].copy()

# R5: upper-case ticket agent_id, inner join to cleaned roster
tickets["agent_id"] = tickets["agent_id"].str.upper()
n0 = len(tickets)
merged = tickets.merge(
    agents[["agent_id", "team", "region", "hourly_cost"]],
    on="agent_id",
    how="inner",
)
summary["tickets_removed_no_matching_agent"] = int(n0 - len(merged))

# R6: normalise channel, drop invalid
merged["channel"] = merged["channel"].str.lower().map(CHANNEL_MAP)
n0 = len(merged)
merged = merged[merged["channel"].notna()].copy()
summary["tickets_removed_invalid_channel"] = int(n0 - len(merged))

# R7: parse resolution_minutes (strip trailing 'min'/'minutes'), require 1..480
merged["resolution_minutes"] = merged["resolution_minutes"].map(parse_resolution_minutes)
n0 = len(merged)
merged = merged[merged["resolution_minutes"].notna()].copy()
summary["tickets_removed_invalid_resolution_minutes"] = int(n0 - len(merged))
merged["resolution_minutes"] = merged["resolution_minutes"].astype(int)

# R8: satisfaction_score 1..5; invalid/missing becomes empty, row kept
satisfaction = merged["satisfaction_score"].map(parse_satisfaction)
summary["tickets_satisfaction_score_set_empty"] = int(satisfaction.isna().sum())
merged["satisfaction_score"] = satisfaction.astype("Int64")

# R9: reopened -> 1/0; drop invalid or missing
merged["reopened"] = merged["reopened"].str.lower().map(REOPENED_MAP)
n0 = len(merged)
merged = merged[merged["reopened"].notna()].copy()
summary["tickets_removed_invalid_reopened"] = int(n0 - len(merged))
merged["reopened"] = merged["reopened"].astype(int)

# R10: labor cost
merged["labor_cost"] = (merged["resolution_minutes"] / 60.0 * merged["hourly_cost"]).round(2)

# R11: schema, ordering and output
merged["team"] = pd.Categorical(merged["team"], categories=["Alpha", "Beta", "Gamma"])
merged["region"] = pd.Categorical(merged["region"], categories=["East", "West"])
merged["channel"] = pd.Categorical(merged["channel"], categories=["email", "chat", "phone"])

columns = [
    "ticket_id", "agent_id", "team", "region", "channel",
    "resolution_minutes", "satisfaction_score", "reopened",
    "hourly_cost", "labor_cost",
]
cleaned = merged[columns].copy()
cleaned["ticket_id"] = cleaned["ticket_id"].astype(str)
cleaned["agent_id"] = cleaned["agent_id"].astype(str)
cleaned["hourly_cost"] = cleaned["hourly_cost"].astype(float)
cleaned = cleaned.sort_values("ticket_id", kind="mergesort").reset_index(drop=True)

cleaned.to_csv(os.path.join(OUTPUT_DIR, "cleaned.csv"), index=False)
summary["cleaned_rows"] = int(len(cleaned))

with open(os.path.join(OUTPUT_DIR, "cleaning_summary.json"), "w", encoding="utf-8") as fh:
    json.dump(summary, fh, indent=2)
