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
    tickets_raw[col] = tickets_raw[col].str.strip()

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

raw_rows = len(tickets_raw)
summary = {"raw_rows": raw_rows}

# ── R2: Remove duplicate ticket_id rows (keep first) ─────────────────────────
before_dedup = len(tickets_raw)
tickets_raw = tickets_raw.drop_duplicates(subset=["ticket_id"], keep="first")
summary["tickets_deduped"] = before_dedup - len(tickets_raw)

# ── R3: Normalise agent_id to upper case in agents, remove duplicates ─────────
agents_raw["agent_id"] = agents_raw["agent_id"].str.upper()
before_agent_dedup = len(agents_raw)
agents_raw = agents_raw.drop_duplicates(subset=["agent_id"], keep="first")
summary["agents_deduped"] = before_agent_dedup - len(agents_raw)

# ── R4: Clean agent roster ────────────────────────────────────────────────────
TEAM_MAP = {
    "alpha": "Alpha", "team alpha": "Alpha",
    "beta": "Beta",   "team beta": "Beta",
    "gamma": "Gamma", "team gamma": "Gamma",
}
REGION_MAP = {
    "east": "East", "e": "East",
    "west": "West", "w": "West",
}

def clean_team(val):
    if pd.isna(val):
        return np.nan
    return TEAM_MAP.get(str(val).strip().lower(), np.nan)

def clean_region(val):
    if pd.isna(val):
        return np.nan
    return REGION_MAP.get(str(val).strip().lower(), np.nan)

def clean_hourly_cost(val):
    if pd.isna(val):
        return np.nan
    cleaned = re.sub(r'[\$,]', '', str(val))
    cleaned = re.sub(r'(?i)usd\s*', '', cleaned).strip()
    try:
        cost = float(cleaned)
        return cost if cost > 0 else np.nan
    except ValueError:
        return np.nan

agents = agents_raw.copy()
agents["team"] = agents["team"].apply(clean_team)
agents["region"] = agents["region"].apply(clean_region)
agents["hourly_cost"] = agents["hourly_cost"].apply(clean_hourly_cost)

before_agent_filter = len(agents)
agents = agents.dropna(subset=["team", "region", "hourly_cost"])
summary["agents_invalid_dropped"] = before_agent_filter - len(agents)

# ── R5: Normalise ticket agent_id, join to roster, drop unmatched ─────────────
tickets = tickets_raw.copy()
tickets["agent_id"] = tickets["agent_id"].str.upper()

before_join = len(tickets)
tickets = tickets.merge(agents[["agent_id", "team", "region", "hourly_cost"]],
                        on="agent_id", how="inner")
summary["tickets_no_agent"] = before_join - len(tickets)

# ── R6: Normalise channel ─────────────────────────────────────────────────────
CHANNEL_MAP = {
    "email": "email",   "e-mail": "email",
    "chat": "chat",     "live chat": "chat",
    "phone": "phone",   "call": "phone",
}

def clean_channel(val):
    if pd.isna(val):
        return np.nan
    return CHANNEL_MAP.get(str(val).strip().lower(), np.nan)

tickets["channel"] = tickets["channel"].apply(clean_channel)
before_channel = len(tickets)
tickets = tickets.dropna(subset=["channel"])
summary["tickets_invalid_channel"] = before_channel - len(tickets)

# ── R7: resolution_minutes ────────────────────────────────────────────────────
def clean_resolution(val):
    if pd.isna(val):
        return np.nan
    s = re.sub(r'(?i)\s*minutes?\s*$', '', str(val)).strip()
    try:
        v = int(s)
        return v if 1 <= v <= 480 else np.nan
    except ValueError:
        return np.nan

tickets["resolution_minutes"] = tickets["resolution_minutes"].apply(clean_resolution)
before_res = len(tickets)
tickets = tickets.dropna(subset=["resolution_minutes"])
tickets["resolution_minutes"] = tickets["resolution_minutes"].astype(int)
summary["tickets_invalid_resolution"] = before_res - len(tickets)

# ── R8: satisfaction_score (nullable) ────────────────────────────────────────
def clean_satisfaction(val):
    if pd.isna(val):
        return np.nan
    try:
        v = int(float(str(val).strip()))
        return v if 1 <= v <= 5 else np.nan
    except (ValueError, TypeError):
        return np.nan

tickets["satisfaction_score"] = tickets["satisfaction_score"].apply(clean_satisfaction)
# Row is kept; invalid/missing becomes NaN

# ── R9: reopened ─────────────────────────────────────────────────────────────
REOPENED_MAP = {
    "yes": 1, "y": 1, "true": 1, "1": 1,
    "no": 0,  "n": 0, "false": 0, "0": 0,
}

def clean_reopened(val):
    if pd.isna(val):
        return np.nan
    return REOPENED_MAP.get(str(val).strip().lower(), np.nan)

tickets["reopened"] = tickets["reopened"].apply(clean_reopened)
before_reopened = len(tickets)
tickets = tickets.dropna(subset=["reopened"])
tickets["reopened"] = tickets["reopened"].astype(int)
summary["tickets_invalid_reopened"] = before_reopened - len(tickets)

# ── R10: labor_cost ───────────────────────────────────────────────────────────
tickets["labor_cost"] = (tickets["resolution_minutes"] / 60.0 * tickets["hourly_cost"]).round(2)

# ── R11: Select, order, sort, write ──────────────────────────────────────────
OUTPUT_COLS = [
    "ticket_id", "agent_id", "team", "region", "channel",
    "resolution_minutes", "satisfaction_score", "reopened",
    "hourly_cost", "labor_cost",
]
tickets = tickets[OUTPUT_COLS].sort_values("ticket_id").reset_index(drop=True)

# Cast categoricals
for cat_col in ["team", "region", "channel"]:
    tickets[cat_col] = tickets[cat_col].astype("category")

# satisfaction_score: keep as nullable int (use Int64 / object with NaN)
# Write as int where present, empty where NaN
tickets["satisfaction_score"] = tickets["satisfaction_score"].apply(
    lambda x: int(x) if not pd.isna(x) else np.nan
)

cleaned_rows = len(tickets)
summary["cleaned_rows"] = cleaned_rows

out_csv = os.path.join(OUTPUT_DIR, "cleaned.csv")
tickets.to_csv(out_csv, index=False)

out_json = os.path.join(OUTPUT_DIR, "cleaning_summary.json")
with open(out_json, "w") as f:
    json.dump(summary, f, indent=2)

print(f"Cleaning complete: {raw_rows} raw rows -> {cleaned_rows} cleaned rows.")
print(json.dumps(summary, indent=2))
