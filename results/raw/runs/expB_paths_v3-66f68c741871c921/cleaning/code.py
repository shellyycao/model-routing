import os
import json
import re
import pandas as pd
import numpy as np

INPUT_DIR = os.environ["INPUT_DIR"]
OUTPUT_DIR = os.environ["OUTPUT_DIR"]

MISSING_VALUES = ["", "NA", "N/A", "null", "None", "-"]

# ── R1: Read both files, strip whitespace, treat special strings as NaN ──────
tickets_raw = pd.read_csv(
    os.path.join(INPUT_DIR, "tickets.csv"),
    dtype=str,
    keep_default_na=False,
    na_values=MISSING_VALUES,
    skipinitialspace=True,
)
tickets_raw.columns = tickets_raw.columns.str.strip()
for col in tickets_raw.columns:
    tickets_raw[col] = tickets_raw[col].apply(
        lambda x: x.strip() if isinstance(x, str) else x
    )
# Re-apply missing detection after strip
for col in tickets_raw.columns:
    tickets_raw[col] = tickets_raw[col].replace(MISSING_VALUES, np.nan)

agents_raw = pd.read_csv(
    os.path.join(INPUT_DIR, "agents.csv"),
    dtype=str,
    keep_default_na=False,
    na_values=MISSING_VALUES,
    skipinitialspace=True,
)
agents_raw.columns = agents_raw.columns.str.strip()
for col in agents_raw.columns:
    agents_raw[col] = agents_raw[col].apply(
        lambda x: x.strip() if isinstance(x, str) else x
    )
for col in agents_raw.columns:
    agents_raw[col] = agents_raw[col].replace(MISSING_VALUES, np.nan)

raw_rows = len(tickets_raw)

# ── R2: Remove duplicate ticket_id rows, keep first ─────────────────────────
before_dedup = len(tickets_raw)
tickets_raw = tickets_raw.drop_duplicates(subset=["ticket_id"], keep="first")
duplicates_removed = before_dedup - len(tickets_raw)

# ── R3: Normalise agent_id to upper case in agents, remove duplicates ────────
agents_raw["agent_id"] = agents_raw["agent_id"].str.upper()
agents_raw = agents_raw.drop_duplicates(subset=["agent_id"], keep="first")

# ── R4: Clean agent roster ───────────────────────────────────────────────────
TEAM_MAP = {
    "alpha": "Alpha", "team alpha": "Alpha",
    "beta": "Beta",   "team beta": "Beta",
    "gamma": "Gamma", "team gamma": "Gamma",
}
REGION_MAP = {
    "east": "East", "e": "East",
    "west": "West", "w": "West",
}

def map_team(val):
    if pd.isna(val):
        return np.nan
    return TEAM_MAP.get(val.strip().lower(), np.nan)

def map_region(val):
    if pd.isna(val):
        return np.nan
    return REGION_MAP.get(val.strip().lower(), np.nan)

def parse_hourly_cost(val):
    if pd.isna(val):
        return np.nan
    cleaned = re.sub(r'[\$,]', '', str(val))
    cleaned = re.sub(r'USD', '', cleaned, flags=re.IGNORECASE).strip()
    try:
        cost = float(cleaned)
        return cost if cost > 0 else np.nan
    except ValueError:
        return np.nan

agents = agents_raw.copy()
agents["team"] = agents["team"].apply(map_team)
agents["region"] = agents["region"].apply(map_region)
agents["hourly_cost"] = agents["hourly_cost"].apply(parse_hourly_cost)

# Exclude rows with any invalid/missing field or cost <= 0
agents_before = len(agents)
agents = agents.dropna(subset=["agent_id", "team", "region", "hourly_cost"])
agents_excluded = agents_before - len(agents)

# ── R5: Normalise agent_id in tickets, join to roster, drop unmatched ────────
tickets_raw["agent_id"] = tickets_raw["agent_id"].str.upper()
tickets = tickets_raw.merge(agents[["agent_id", "team", "region", "hourly_cost"]],
                            on="agent_id", how="inner")
unmatched_dropped = len(tickets_raw) - len(tickets)

# ── R6: Map channel ──────────────────────────────────────────────────────────
CHANNEL_MAP = {
    "email": "email",   "e-mail": "email",
    "chat": "chat",     "live chat": "chat",
    "phone": "phone",   "call": "phone",
}

def map_channel(val):
    if pd.isna(val):
        return np.nan
    return CHANNEL_MAP.get(val.strip().lower(), np.nan)

tickets["channel"] = tickets["channel"].apply(map_channel)
before_channel = len(tickets)
tickets = tickets.dropna(subset=["channel"])
invalid_channel = before_channel - len(tickets)

# ── R7: resolution_minutes ───────────────────────────────────────────────────
def parse_resolution(val):
    if pd.isna(val):
        return np.nan
    s = re.sub(r'(?i)\s*minutes?\s*$', '', str(val)).strip()
    try:
        v = int(s)
        return v if 1 <= v <= 480 else np.nan
    except ValueError:
        return np.nan

tickets["resolution_minutes"] = tickets["resolution_minutes"].apply(parse_resolution)
before_res = len(tickets)
tickets = tickets.dropna(subset=["resolution_minutes"])
tickets["resolution_minutes"] = tickets["resolution_minutes"].astype(int)
invalid_resolution = before_res - len(tickets)

# ── R8: satisfaction_score ───────────────────────────────────────────────────
def parse_satisfaction(val):
    if pd.isna(val):
        return np.nan
    try:
        v = int(float(str(val).strip()))
        return v if 1 <= v <= 5 else np.nan
    except (ValueError, TypeError):
        return np.nan

tickets["satisfaction_score"] = tickets["satisfaction_score"].apply(parse_satisfaction)
# Rows are KEPT; invalid/missing become NaN (empty cell)

# ── R9: reopened ─────────────────────────────────────────────────────────────
REOPENED_MAP = {
    "yes": 1, "y": 1, "true": 1, "1": 1,
    "no": 0,  "n": 0, "false": 0, "0": 0,
}

def parse_reopened(val):
    if pd.isna(val):
        return np.nan
    return REOPENED_MAP.get(str(val).strip().lower(), np.nan)

tickets["reopened"] = tickets["reopened"].apply(parse_reopened)
before_reopened = len(tickets)
tickets = tickets.dropna(subset=["reopened"])
tickets["reopened"] = tickets["reopened"].astype(int)
invalid_reopened = before_reopened - len(tickets)

# ── R10: labor_cost ──────────────────────────────────────────────────────────
tickets["labor_cost"] = (
    (tickets["resolution_minutes"] / 60.0) * tickets["hourly_cost"]
).round(2)

# ── R11: Select, order, sort, write ─────────────────────────────────────────
OUTPUT_COLS = [
    "ticket_id", "agent_id", "team", "region", "channel",
    "resolution_minutes", "satisfaction_score", "reopened",
    "hourly_cost", "labor_cost",
]
tickets = tickets[OUTPUT_COLS].sort_values("ticket_id").reset_index(drop=True)

# Cast categories
for cat_col in ["team", "region", "channel"]:
    tickets[cat_col] = tickets[cat_col].astype("category")

# satisfaction_score: keep as nullable int (use Int64 to allow NaN)
tickets["satisfaction_score"] = pd.array(
    tickets["satisfaction_score"], dtype=pd.Int64Dtype()
)

cleaned_rows = len(tickets)

out_csv = os.path.join(OUTPUT_DIR, "cleaned.csv")
tickets.to_csv(out_csv, index=False)

# ── Write cleaning summary ───────────────────────────────────────────────────
summary = {
    "raw_rows": raw_rows,
    "cleaned_rows": cleaned_rows,
    "duplicate_ticket_ids_removed": duplicates_removed,
    "agent_roster_rows_excluded": agents_excluded,
    "tickets_dropped_no_agent_match": unmatched_dropped,
    "tickets_dropped_invalid_channel": invalid_channel,
    "tickets_dropped_invalid_resolution": invalid_resolution,
    "tickets_dropped_invalid_reopened": invalid_reopened,
}

with open(os.path.join(OUTPUT_DIR, "cleaning_summary.json"), "w") as f:
    json.dump(summary, f, indent=2)

print(f"Cleaning complete: {raw_rows} raw rows -> {cleaned_rows} cleaned rows.")
