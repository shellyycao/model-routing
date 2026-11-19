import os
import json
import re
import pandas as pd
import numpy as np

INPUT_DIR = os.environ["INPUT_DIR"]
OUTPUT_DIR = os.environ["OUTPUT_DIR"]

MISSING_VALUES = ["", "NA", "N/A", "null", "None", "-"]

# ── R1: Read both files, strip whitespace, treat special strings as missing ──
tickets_raw = pd.read_csv(
    os.path.join(INPUT_DIR, "tickets.csv"),
    dtype=str,
    keep_default_na=False,
)
tickets_raw.columns = tickets_raw.columns.str.strip()
for col in tickets_raw.columns:
    tickets_raw[col] = tickets_raw[col].str.strip()
tickets_raw.replace(MISSING_VALUES, np.nan, inplace=True)

agents_raw = pd.read_csv(
    os.path.join(INPUT_DIR, "agents.csv"),
    dtype=str,
    keep_default_na=False,
)
agents_raw.columns = agents_raw.columns.str.strip()
for col in agents_raw.columns:
    agents_raw[col] = agents_raw[col].str.strip()
agents_raw.replace(MISSING_VALUES, np.nan, inplace=True)

raw_ticket_rows = len(tickets_raw)
raw_agent_rows = len(agents_raw)

# ── R2: Remove duplicate ticket_id rows, keep first ──
tickets = tickets_raw.copy()
before_dedup = len(tickets)
tickets = tickets.drop_duplicates(subset=["ticket_id"], keep="first")
duplicates_removed_tickets = before_dedup - len(tickets)

# ── R3: Normalise agent_id to upper case in agents, remove duplicates ──
agents = agents_raw.copy()
agents["agent_id"] = agents["agent_id"].str.upper()
before_agent_dedup = len(agents)
agents = agents.drop_duplicates(subset=["agent_id"], keep="first")
duplicates_removed_agents = before_agent_dedup - len(agents)

# ── R4: Clean agent roster ──
# Map team
TEAM_MAP = {
    "alpha": "Alpha",
    "team alpha": "Alpha",
    "beta": "Beta",
    "team beta": "Beta",
    "gamma": "Gamma",
    "team gamma": "Gamma",
}
def map_team(val):
    if pd.isna(val):
        return np.nan
    return TEAM_MAP.get(val.strip().lower(), np.nan)

agents["team"] = agents["team"].apply(map_team)

# Map region
REGION_MAP = {
    "east": "East",
    "e": "East",
    "west": "West",
    "w": "West",
}
def map_region(val):
    if pd.isna(val):
        return np.nan
    return REGION_MAP.get(val.strip().lower(), np.nan)

agents["region"] = agents["region"].apply(map_region)

# Parse hourly_cost
def parse_hourly_cost(val):
    if pd.isna(val):
        return np.nan
    cleaned = re.sub(r'[\$,]', '', val)
    cleaned = re.sub(r'USD', '', cleaned, flags=re.IGNORECASE).strip()
    try:
        cost = float(cleaned)
        return cost if cost > 0 else np.nan
    except ValueError:
        return np.nan

agents["hourly_cost"] = agents["hourly_cost"].apply(parse_hourly_cost)

# Exclude rows with any invalid field
before_agent_filter = len(agents)
agents = agents.dropna(subset=["agent_id", "team", "region", "hourly_cost"])
agents = agents[agents["hourly_cost"] > 0]
agent_rows_excluded = before_agent_filter - len(agents)

# ── R5: Normalise agent_id in tickets, join to cleaned roster ──
tickets["agent_id"] = tickets["agent_id"].str.upper()
before_join = len(tickets)
tickets = tickets.merge(agents[["agent_id", "team", "region", "hourly_cost"]], on="agent_id", how="inner")
tickets_dropped_no_agent = before_join - len(tickets)

# ── R6: Map channel ──
CHANNEL_MAP = {
    "email": "email",
    "e-mail": "email",
    "chat": "chat",
    "live chat": "chat",
    "phone": "phone",
    "call": "phone",
}
def map_channel(val):
    if pd.isna(val):
        return np.nan
    return CHANNEL_MAP.get(val.strip().lower(), np.nan)

tickets["channel"] = tickets["channel"].apply(map_channel)
before_channel = len(tickets)
tickets = tickets.dropna(subset=["channel"])
tickets_dropped_channel = before_channel - len(tickets)

# ── R7: resolution_minutes ──
def parse_resolution(val):
    if pd.isna(val):
        return np.nan
    # Remove trailing 'minutes' or 'min'
    cleaned = re.sub(r'\s*minutes?\s*$', '', str(val), flags=re.IGNORECASE).strip()
    try:
        minutes = int(cleaned)
        if 1 <= minutes <= 480:
            return minutes
        return np.nan
    except ValueError:
        return np.nan

tickets["resolution_minutes"] = tickets["resolution_minutes"].apply(parse_resolution)
before_res = len(tickets)
tickets = tickets.dropna(subset=["resolution_minutes"])
tickets["resolution_minutes"] = tickets["resolution_minutes"].astype(int)
tickets_dropped_resolution = before_res - len(tickets)

# ── R8: satisfaction_score ──
def parse_satisfaction(val):
    if pd.isna(val):
        return np.nan
    try:
        score = int(float(str(val).strip()))
        if 1 <= score <= 5:
            return score
        return np.nan
    except (ValueError, TypeError):
        return np.nan

tickets["satisfaction_score"] = tickets["satisfaction_score"].apply(parse_satisfaction)
# Keep rows; invalid/missing become NaN (empty cell)

# ── R9: reopened ──
REOPENED_MAP = {
    "yes": 1, "y": 1, "true": 1, "1": 1,
    "no": 0, "n": 0, "false": 0, "0": 0,
}
def parse_reopened(val):
    if pd.isna(val):
        return np.nan
    return REOPENED_MAP.get(str(val).strip().lower(), np.nan)

tickets["reopened"] = tickets["reopened"].apply(parse_reopened)
before_reopened = len(tickets)
tickets = tickets.dropna(subset=["reopened"])
tickets["reopened"] = tickets["reopened"].astype(int)
tickets_dropped_reopened = before_reopened - len(tickets)

# ── R10: Add labor_cost ──
tickets["labor_cost"] = (tickets["resolution_minutes"] / 60.0 * tickets["hourly_cost"]).round(2)

# ── R11: Select, order, sort, write ──
OUTPUT_COLS = [
    "ticket_id", "agent_id", "team", "region", "channel",
    "resolution_minutes", "satisfaction_score", "reopened",
    "hourly_cost", "labor_cost"
]
tickets = tickets[OUTPUT_COLS].copy()

# Apply category types
tickets["team"] = pd.Categorical(tickets["team"], categories=["Alpha", "Beta", "Gamma"])
tickets["region"] = pd.Categorical(tickets["region"], categories=["East", "West"])
tickets["channel"] = pd.Categorical(tickets["channel"], categories=["email", "chat", "phone"])

# satisfaction_score: keep as nullable int (use Int64 for nullable integer)
tickets["satisfaction_score"] = tickets["satisfaction_score"].astype("Int64")

tickets = tickets.sort_values("ticket_id").reset_index(drop=True)

cleaned_rows = len(tickets)

out_csv = os.path.join(OUTPUT_DIR, "cleaned.csv")
tickets.to_csv(out_csv, index=False)

# ── Write cleaning_summary.json ──
summary = {
    "raw_rows": raw_ticket_rows,
    "cleaned_rows": cleaned_rows,
    "raw_agent_rows": raw_agent_rows,
    "duplicates_removed_tickets": duplicates_removed_tickets,
    "duplicates_removed_agents": duplicates_removed_agents,
    "agent_rows_excluded_invalid": agent_rows_excluded,
    "tickets_dropped_no_agent_match": tickets_dropped_no_agent,
    "tickets_dropped_invalid_channel": tickets_dropped_channel,
    "tickets_dropped_invalid_resolution": tickets_dropped_resolution,
    "tickets_dropped_invalid_reopened": tickets_dropped_reopened,
}

with open(os.path.join(OUTPUT_DIR, "cleaning_summary.json"), "w") as f:
    json.dump(summary, f, indent=2)

print(f"Cleaning complete: {raw_ticket_rows} raw rows -> {cleaned_rows} cleaned rows.")
