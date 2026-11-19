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
    na_values=MISSING_VALUES,
    skipinitialspace=True,
)
tickets_raw.columns = tickets_raw.columns.str.strip()
for col in tickets_raw.columns:
    tickets_raw[col] = tickets_raw[col].str.strip()
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
    agents_raw[col] = agents_raw[col].str.strip()
for col in agents_raw.columns:
    agents_raw[col] = agents_raw[col].replace(MISSING_VALUES, np.nan)

raw_ticket_rows = len(tickets_raw)
raw_agent_rows = len(agents_raw)

# ── R2: Remove duplicate ticket_id rows, keep first ──
tickets = tickets_raw.copy()
tickets_before_dedup = len(tickets)
tickets = tickets.drop_duplicates(subset=["ticket_id"], keep="first")
tickets_dedup_removed = tickets_before_dedup - len(tickets)

# ── R3: Normalise agent_id to upper case in agents, remove duplicates ──
agents = agents_raw.copy()
agents["agent_id"] = agents["agent_id"].str.upper()
agents_before_dedup = len(agents)
agents = agents.drop_duplicates(subset=["agent_id"], keep="first")
agents_dedup_removed = agents_before_dedup - len(agents)

# ── R4: Clean agent roster ──
# Map team
team_map = {
    "alpha": "Alpha", "team alpha": "Alpha",
    "beta": "Beta", "team beta": "Beta",
    "gamma": "Gamma", "team gamma": "Gamma",
}
agents["team"] = agents["team"].str.lower().map(team_map)

# Map region
region_map = {
    "east": "East", "e": "East",
    "west": "West", "w": "West",
}
agents["region"] = agents["region"].str.lower().map(region_map)

# Parse hourly_cost: remove $, USD, commas, then convert to float
def parse_cost(val):
    if pd.isna(val):
        return np.nan
    cleaned = re.sub(r'[\$,]', '', str(val))
    cleaned = re.sub(r'USD', '', cleaned, flags=re.IGNORECASE).strip()
    try:
        return float(cleaned)
    except ValueError:
        return np.nan

agents["hourly_cost"] = agents["hourly_cost"].apply(parse_cost)

# Exclude rows with any invalid/missing field or cost <= 0
agents_before_filter = len(agents)
agents = agents.dropna(subset=["agent_id", "team", "region", "hourly_cost"])
agents = agents[agents["hourly_cost"] > 0]
agents_invalid_removed = agents_before_filter - len(agents)

# ── R5: Normalise agent_id in tickets, join to cleaned roster ──
tickets["agent_id"] = tickets["agent_id"].str.upper()
tickets_before_join = len(tickets)
tickets = tickets.merge(agents[["agent_id", "team", "region", "hourly_cost"]], on="agent_id", how="inner")
tickets_no_agent = tickets_before_join - len(tickets)

# ── R6: Map channel ──
channel_map = {
    "email": "email", "e-mail": "email",
    "chat": "chat", "live chat": "chat",
    "phone": "phone", "call": "phone",
}
tickets_before_channel = len(tickets)
tickets["channel"] = tickets["channel"].str.lower().map(channel_map)
tickets = tickets.dropna(subset=["channel"])
tickets_invalid_channel = tickets_before_channel - len(tickets)

# ── R7: resolution_minutes ──
def parse_resolution(val):
    if pd.isna(val):
        return np.nan
    s = str(val)
    # Remove trailing 'minutes' or 'min'
    s = re.sub(r'\s*minutes?\s*$', '', s, flags=re.IGNORECASE).strip()
    try:
        v = int(s)
        if 1 <= v <= 480:
            return v
        return np.nan
    except ValueError:
        return np.nan

tickets_before_res = len(tickets)
tickets["resolution_minutes"] = tickets["resolution_minutes"].apply(parse_resolution)
tickets = tickets.dropna(subset=["resolution_minutes"])
tickets["resolution_minutes"] = tickets["resolution_minutes"].astype(int)
tickets_invalid_res = tickets_before_res - len(tickets)

# ── R8: satisfaction_score ──
def parse_satisfaction(val):
    if pd.isna(val):
        return np.nan
    try:
        v = int(float(str(val).strip()))
        if 1 <= v <= 5:
            return v
        return np.nan
    except (ValueError, TypeError):
        return np.nan

tickets["satisfaction_score"] = tickets["satisfaction_score"].apply(parse_satisfaction)
# Keep rows; invalid/missing become NaN (empty cell)

# ── R9: reopened ──
reopened_map = {
    "yes": 1, "y": 1, "true": 1, "1": 1,
    "no": 0, "n": 0, "false": 0, "0": 0,
}
tickets_before_reopened = len(tickets)
tickets["reopened"] = tickets["reopened"].str.lower().map(reopened_map)
tickets = tickets.dropna(subset=["reopened"])
tickets["reopened"] = tickets["reopened"].astype(int)
tickets_invalid_reopened = tickets_before_reopened - len(tickets)

# ── R10: Add labor_cost ──
tickets["labor_cost"] = (tickets["resolution_minutes"] / 60.0 * tickets["hourly_cost"]).round(2)

# ── R11: Select, order, sort, write ──
output_cols = [
    "ticket_id", "agent_id", "team", "region", "channel",
    "resolution_minutes", "satisfaction_score", "reopened",
    "hourly_cost", "labor_cost"
]
tickets = tickets[output_cols].sort_values("ticket_id").reset_index(drop=True)

# Cast types
tickets["ticket_id"] = tickets["ticket_id"].astype(str)
tickets["agent_id"] = tickets["agent_id"].astype(str)
tickets["team"] = pd.Categorical(tickets["team"], categories=["Alpha", "Beta", "Gamma"])
tickets["region"] = pd.Categorical(tickets["region"], categories=["East", "West"])
tickets["channel"] = pd.Categorical(tickets["channel"], categories=["email", "chat", "phone"])
tickets["resolution_minutes"] = tickets["resolution_minutes"].astype(int)
# satisfaction_score: keep as nullable int (use Int64 or float with NaN)
tickets["satisfaction_score"] = pd.array(
    tickets["satisfaction_score"].where(tickets["satisfaction_score"].notna(), other=pd.NA),
    dtype=pd.Int64Dtype()
)
tickets["reopened"] = tickets["reopened"].astype(int)
tickets["hourly_cost"] = tickets["hourly_cost"].astype(float)
tickets["labor_cost"] = tickets["labor_cost"].astype(float)

cleaned_rows = len(tickets)

# Write cleaned CSV
out_csv = os.path.join(OUTPUT_DIR, "cleaned.csv")
tickets.to_csv(out_csv, index=False)

# Write summary JSON
summary = {
    "raw_rows": raw_ticket_rows,
    "cleaned_rows": cleaned_rows,
    "raw_agent_rows": raw_agent_rows,
    "tickets_duplicate_ticket_id_removed": tickets_dedup_removed,
    "agents_duplicate_agent_id_removed": agents_dedup_removed,
    "agents_invalid_or_zero_cost_removed": agents_invalid_removed,
    "tickets_dropped_no_matching_agent": tickets_no_agent,
    "tickets_dropped_invalid_channel": tickets_invalid_channel,
    "tickets_dropped_invalid_resolution_minutes": tickets_invalid_res,
    "tickets_dropped_invalid_reopened": tickets_invalid_reopened,
}
with open(os.path.join(OUTPUT_DIR, "cleaning_summary.json"), "w") as f:
    json.dump(summary, f, indent=2)

print(f"Cleaning complete: {raw_ticket_rows} raw rows -> {cleaned_rows} cleaned rows.")
