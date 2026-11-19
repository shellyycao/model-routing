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

# ── R2: Remove duplicate ticket_id rows, keep first ──────────────────────────
before_dedup = len(tickets_raw)
tickets_raw = tickets_raw.drop_duplicates(subset=["ticket_id"], keep="first")
duplicates_removed = before_dedup - len(tickets_raw)

# ── R3: Normalise agent_id to upper case in agents, remove duplicates ─────────
agents_raw["agent_id"] = agents_raw["agent_id"].str.upper()
agents_raw = agents_raw.drop_duplicates(subset=["agent_id"], keep="first")

# ── R4: Clean agent roster ────────────────────────────────────────────────────
def normalise_team(val):
    if pd.isna(val):
        return np.nan
    v = val.strip().lower()
    if v in ("alpha", "team alpha"):
        return "Alpha"
    elif v in ("beta", "team beta"):
        return "Beta"
    elif v in ("gamma", "team gamma"):
        return "Gamma"
    return np.nan

def normalise_region(val):
    if pd.isna(val):
        return np.nan
    v = val.strip().lower()
    if v in ("east", "e"):
        return "East"
    elif v in ("west", "w"):
        return "West"
    return np.nan

def parse_hourly_cost(val):
    if pd.isna(val):
        return np.nan
    # Remove $, USD, commas, whitespace
    cleaned = re.sub(r'[\$,]', '', str(val))
    cleaned = re.sub(r'USD', '', cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip()
    try:
        cost = float(cleaned)
        return cost if cost > 0 else np.nan
    except ValueError:
        return np.nan

agents = agents_raw.copy()
agents["team"] = agents["team"].apply(normalise_team)
agents["region"] = agents["region"].apply(normalise_region)
agents["hourly_cost"] = agents["hourly_cost"].apply(parse_hourly_cost)

# Exclude rows with any invalid/missing field or cost <= 0
agents_before_filter = len(agents)
agents = agents.dropna(subset=["agent_id", "team", "region", "hourly_cost"])
agents_excluded = agents_before_filter - len(agents)

# ── R5: Normalise agent_id in tickets, join to cleaned roster ─────────────────
tickets = tickets_raw.copy()
tickets["agent_id"] = tickets["agent_id"].str.upper()
before_join = len(tickets)
tickets = tickets.merge(agents[["agent_id", "team", "region", "hourly_cost"]], on="agent_id", how="inner")
no_agent_match = before_join - len(tickets)

# ── R6: Normalise channel ─────────────────────────────────────────────────────
def normalise_channel(val):
    if pd.isna(val):
        return np.nan
    v = val.strip().lower()
    if v in ("email", "e-mail"):
        return "email"
    elif v in ("chat", "live chat"):
        return "chat"
    elif v in ("phone", "call"):
        return "phone"
    return np.nan

tickets["channel"] = tickets["channel"].apply(normalise_channel)
before_channel = len(tickets)
tickets = tickets.dropna(subset=["channel"])
invalid_channel = before_channel - len(tickets)

# ── R7: resolution_minutes ────────────────────────────────────────────────────
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
invalid_resolution = before_res - len(tickets)

# ── R8: satisfaction_score ────────────────────────────────────────────────────
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
# Invalid/missing -> empty cell, row kept (no drop)

# ── R9: reopened ──────────────────────────────────────────────────────────────
def parse_reopened(val):
    if pd.isna(val):
        return np.nan
    v = str(val).strip().lower()
    if v in ("yes", "y", "true", "1"):
        return 1
    elif v in ("no", "n", "false", "0"):
        return 0
    return np.nan

tickets["reopened"] = tickets["reopened"].apply(parse_reopened)
before_reopened = len(tickets)
tickets = tickets.dropna(subset=["reopened"])
tickets["reopened"] = tickets["reopened"].astype(int)
invalid_reopened = before_reopened - len(tickets)

# ── R10: labor_cost ───────────────────────────────────────────────────────────
tickets["labor_cost"] = (tickets["resolution_minutes"] / 60.0 * tickets["hourly_cost"]).round(2)

# ── R11: Select, order, sort, write ──────────────────────────────────────────
final_cols = [
    "ticket_id", "agent_id", "team", "region", "channel",
    "resolution_minutes", "satisfaction_score", "reopened",
    "hourly_cost", "labor_cost"
]
tickets = tickets[final_cols].copy()

# Apply category types
tickets["team"] = pd.Categorical(tickets["team"], categories=["Alpha", "Beta", "Gamma"])
tickets["region"] = pd.Categorical(tickets["region"], categories=["East", "West"])
tickets["channel"] = pd.Categorical(tickets["channel"], categories=["email", "chat", "phone"])

# satisfaction_score: keep as nullable int (use Int64 for pandas nullable integer)
tickets["satisfaction_score"] = tickets["satisfaction_score"].astype("Int64")

tickets = tickets.sort_values("ticket_id").reset_index(drop=True)

cleaned_rows = len(tickets)

out_csv = os.path.join(OUTPUT_DIR, "cleaned.csv")
tickets.to_csv(out_csv, index=False)

# ── Write cleaning summary ────────────────────────────────────────────────────
summary = {
    "raw_rows": raw_rows,
    "cleaned_rows": cleaned_rows,
    "duplicate_ticket_ids_removed": duplicates_removed,
    "agent_roster_rows_excluded": agents_excluded,
    "tickets_dropped_no_agent_match": no_agent_match,
    "tickets_dropped_invalid_channel": invalid_channel,
    "tickets_dropped_invalid_resolution_minutes": invalid_resolution,
    "tickets_dropped_invalid_reopened": invalid_reopened,
}

out_json = os.path.join(OUTPUT_DIR, "cleaning_summary.json")
with open(out_json, "w") as f:
    json.dump(summary, f, indent=2)

print(f"Cleaning complete: {raw_rows} raw rows -> {cleaned_rows} cleaned rows.")
