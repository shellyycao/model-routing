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


def load_text_csv(path):
    """R1: read as text, strip whitespace, normalise missing tokens to NaN."""
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df.columns = df.columns.str.strip()
    for col in df.columns:
        s = df[col].str.strip()
        df[col] = s.mask(s.str.lower().isin(MISSING_TOKENS))
    return df


def parse_hourly_cost(value):
    if pd.isna(value):
        return np.nan
    text = re.sub(r"(?i)usd", "", str(value))
    text = text.replace("$", "").replace(",", "").strip()
    try:
        return float(text)
    except ValueError:
        return np.nan


def parse_resolution_minutes(value):
    if pd.isna(value):
        return np.nan
    text = str(value).strip().lower()
    text = re.sub(r"\s*(minutes|min)\s*$", "", text).strip()
    if re.fullmatch(r"\d+", text):
        minutes = int(text)
        if 1 <= minutes <= 480:
            return float(minutes)
    return np.nan


def parse_satisfaction(value):
    if pd.isna(value):
        return np.nan
    text = str(value).strip()
    if re.fullmatch(r"\d+", text):
        score = int(text)
        if 1 <= score <= 5:
            return float(score)
    return np.nan


summary = {}

tickets = load_text_csv(os.path.join(INPUT_DIR, "tickets.csv"))
agents = load_text_csv(os.path.join(INPUT_DIR, "agents.csv"))
summary["raw_rows"] = int(len(tickets))
summary["raw_agent_rows"] = int(len(agents))

# R2: deduplicate ticket_id before any filtering, keep first in raw-file order.
before = len(tickets)
tickets = tickets.drop_duplicates(subset="ticket_id", keep="first")
summary["r2_duplicate_ticket_id_removed"] = int(before - len(tickets))
before = len(tickets)
tickets = tickets[tickets["ticket_id"].notna()].copy()
summary["r2_missing_ticket_id_removed"] = int(before - len(tickets))

# R3: normalise agent_id to upper case, deduplicate keeping first.
agents["agent_id"] = agents["agent_id"].str.upper()
before = len(agents)
agents = agents.drop_duplicates(subset="agent_id", keep="first")
summary["r3_duplicate_agent_id_removed"] = int(before - len(agents))

# R4: normalise team/region, parse hourly_cost, drop invalid roster rows.
agents["team"] = agents["team"].str.lower().map(TEAM_MAP)
agents["region"] = agents["region"].str.lower().map(REGION_MAP)
agents["hourly_cost"] = agents["hourly_cost"].apply(parse_hourly_cost)
valid_agent = (
    agents["agent_id"].notna()
    & agents["team"].notna()
    & agents["region"].notna()
    & agents["hourly_cost"].notna()
    & (agents["hourly_cost"] > 0)
)
summary["r4_invalid_agent_rows_removed"] = int((~valid_agent).sum())
agents = agents[valid_agent].copy()

# R5: normalise ticket agent_id, inner-join to cleaned roster.
tickets["agent_id"] = tickets["agent_id"].str.upper()
before = len(tickets)
merged = tickets.merge(agents, on="agent_id", how="inner")
summary["r5_tickets_without_matching_agent_removed"] = int(before - len(merged))

# R6: normalise channel, drop invalid.
merged["channel"] = merged["channel"].str.lower().map(CHANNEL_MAP)
before = len(merged)
merged = merged[merged["channel"].notna()].copy()
summary["r6_invalid_channel_removed"] = int(before - len(merged))

# R7: parse resolution_minutes (1-480), drop invalid.
merged["resolution_minutes"] = merged["resolution_minutes"].apply(parse_resolution_minutes)
before = len(merged)
merged = merged[merged["resolution_minutes"].notna()].copy()
summary["r7_invalid_resolution_minutes_removed"] = int(before - len(merged))
merged["resolution_minutes"] = merged["resolution_minutes"].astype(int)

# R8: satisfaction_score 1-5; invalid/missing -> empty, row kept.
parsed_satisfaction = merged["satisfaction_score"].apply(parse_satisfaction)
summary["r8_satisfaction_score_set_empty"] = int(parsed_satisfaction.isna().sum())
merged["satisfaction_score"] = parsed_satisfaction.astype("Int64")

# R9: map reopened to 0/1, drop invalid or missing.
merged["reopened"] = merged["reopened"].str.lower().map(REOPENED_MAP)
before = len(merged)
merged = merged[merged["reopened"].notna()].copy()
summary["r9_invalid_reopened_removed"] = int(before - len(merged))
merged["reopened"] = merged["reopened"].astype(int)

# R10: labor cost.
merged["labor_cost"] = (merged["resolution_minutes"] / 60 * merged["hourly_cost"]).round(2)

# R11: final schema, categorical columns, sort by ticket_id, write CSV.
columns = [
    "ticket_id", "agent_id", "team", "region", "channel",
    "resolution_minutes", "satisfaction_score", "reopened",
    "hourly_cost", "labor_cost",
]
out = merged[columns].sort_values("ticket_id", kind="mergesort").reset_index(drop=True)
out["team"] = pd.Categorical(out["team"], categories=["Alpha", "Beta", "Gamma"])
out["region"] = pd.Categorical(out["region"], categories=["East", "West"])
out["channel"] = pd.Categorical(out["channel"], categories=["email", "chat", "phone"])

summary["cleaned_rows"] = int(len(out))

out.to_csv(os.path.join(OUTPUT_DIR, "cleaned.csv"), index=False, float_format="%.2f")
with open(os.path.join(OUTPUT_DIR, "cleaning_summary.json"), "w") as fh:
    json.dump(summary, fh, indent=2)
