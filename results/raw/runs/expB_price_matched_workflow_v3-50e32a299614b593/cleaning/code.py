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


def read_text_csv(filename):
    """R1: read everything as text, strip whitespace, standardise missing tokens."""
    path = os.path.join(INPUT_DIR, filename)
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df.columns = df.columns.str.strip()
    for col in df.columns:
        s = df[col].astype(str).str.strip()
        df[col] = s.mask(s.str.lower().isin(MISSING_TOKENS), pd.NA)
    return df


def parse_hourly_cost(value):
    if pd.isna(value):
        return np.nan
    text = re.sub(r"(?i)usd", "", value).replace("$", "").replace(",", "").strip()
    try:
        return float(text)
    except ValueError:
        return np.nan


def parse_resolution(value):
    if pd.isna(value):
        return pd.NA
    text = re.sub(r"(?i)\s*(?:minutes|min)\s*$", "", value).strip()
    if re.fullmatch(r"\d+", text):
        minutes = int(text)
        if 1 <= minutes <= 480:
            return minutes
    return pd.NA


def parse_satisfaction(value):
    if pd.isna(value):
        return pd.NA
    text = value.strip()
    if re.fullmatch(r"\d+", text):
        score = int(text)
        if 1 <= score <= 5:
            return score
    return pd.NA


# ---- Load (R1) ----
tickets = read_text_csv("tickets.csv")
agents = read_text_csv("agents.csv")
raw_ticket_rows = len(tickets)
raw_agent_rows = len(agents)

# ---- R2: drop duplicate ticket_id rows first, keep first in raw order ----
n = len(tickets)
tickets = tickets.drop_duplicates(subset="ticket_id", keep="first")
duplicate_ticket_rows_removed = n - len(tickets)

# ---- R3: normalise agent_id to upper case, dedupe roster keeping first ----
agents["agent_id"] = agents["agent_id"].str.upper()
n = len(agents)
agents = agents.drop_duplicates(subset="agent_id", keep="first")
duplicate_agent_rows_removed = n - len(agents)

# ---- R4: roster team/region/hourly_cost normalisation and validation ----
agents["team"] = agents["team"].str.lower().map(TEAM_MAP)
agents["region"] = agents["region"].str.lower().map(REGION_MAP)
agents["hourly_cost"] = agents["hourly_cost"].map(parse_hourly_cost)
n = len(agents)
agents = agents.dropna(subset=["agent_id", "team", "region", "hourly_cost"])
agents = agents[agents["hourly_cost"] > 0]
roster_rows_excluded_invalid = n - len(agents)

# ---- R5: normalise ticket agent_id, inner join to roster, drop unmatched ----
tickets["agent_id"] = tickets["agent_id"].str.upper()
n = len(tickets)
df = tickets.merge(agents, on="agent_id", how="inner")
tickets_dropped_no_matching_agent = n - len(df)

# ---- R6: channel mapping, drop invalid ----
df["channel"] = df["channel"].str.lower().map(CHANNEL_MAP)
n = len(df)
df = df.dropna(subset=["channel"])
tickets_dropped_invalid_channel = n - len(df)

# ---- R7: resolution_minutes, whole number 1..480, drop invalid ----
df["resolution_minutes"] = df["resolution_minutes"].map(parse_resolution)
n = len(df)
df = df.dropna(subset=["resolution_minutes"])
tickets_dropped_invalid_resolution_minutes = n - len(df)
df["resolution_minutes"] = df["resolution_minutes"].astype("int64")

# ---- R8: satisfaction_score 1..5; invalid/missing -> blank, keep row ----
df["satisfaction_score"] = df["satisfaction_score"].map(parse_satisfaction).astype("Int64")

# ---- R9: reopened mapped to 0/1, drop invalid or missing ----
df["reopened"] = df["reopened"].str.lower().map(REOPENED_MAP)
n = len(df)
df = df.dropna(subset=["reopened"])
tickets_dropped_invalid_reopened = n - len(df)
df["reopened"] = df["reopened"].astype("int64")

# ---- R10: labor_cost ----
df["labor_cost"] = (df["resolution_minutes"] / 60.0 * df["hourly_cost"]).round(2)

# ---- R11: select columns, enforce categories, sort, write ----
columns = [
    "ticket_id", "agent_id", "team", "region", "channel",
    "resolution_minutes", "satisfaction_score", "reopened",
    "hourly_cost", "labor_cost",
]
out = df[columns].copy()
out["team"] = out["team"].astype(pd.CategoricalDtype(["Alpha", "Beta", "Gamma"]))
out["region"] = out["region"].astype(pd.CategoricalDtype(["East", "West"]))
out["channel"] = out["channel"].astype(pd.CategoricalDtype(["email", "chat", "phone"]))
out = out.sort_values("ticket_id", kind="stable", na_position="last")

output_filename = "cleaned.csv"
out.to_csv(os.path.join(OUTPUT_DIR, output_filename), index=False)

summary = {
    "raw_rows": int(raw_ticket_rows),
    "raw_agent_rows": int(raw_agent_rows),
    "cleaned_rows": int(len(out)),
    "duplicate_ticket_rows_removed": int(duplicate_ticket_rows_removed),
    "duplicate_agent_rows_removed": int(duplicate_agent_rows_removed),
    "roster_rows_excluded_invalid": int(roster_rows_excluded_invalid),
    "tickets_dropped_no_matching_agent": int(tickets_dropped_no_matching_agent),
    "tickets_dropped_invalid_channel": int(tickets_dropped_invalid_channel),
    "tickets_dropped_invalid_resolution_minutes": int(tickets_dropped_invalid_resolution_minutes),
    "tickets_dropped_invalid_reopened": int(tickets_dropped_invalid_reopened),
    "satisfaction_scores_left_blank": int(out["satisfaction_score"].isna().sum()),
}
with open(os.path.join(OUTPUT_DIR, "cleaning_summary.json"), "w", encoding="utf-8") as fh:
    json.dump(summary, fh, indent=2)
