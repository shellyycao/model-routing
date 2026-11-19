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

def normalise_team(val):
    if pd.isna(val):
        return np.nan
    v = val.strip().lower()
    mapping = {
        "alpha": "Alpha",
        "team alpha": "Alpha",
        "beta": "Beta",
        "team beta": "Beta",
        "gamma": "Gamma",
        "team gamma": "Gamma",
    }
    return mapping.get(v, np.nan)

def normalise_region(val):
    if pd.isna(val):
        return np.nan
    v = val.strip().lower()
    mapping = {
        "east": "East",
        "e": "East",
        "west": "West",
        "w": "West",
    }
    return mapping.get(v, np.nan)

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
agents["team"] = agents["team"].apply(normalise_team)
agents["region"] = agents["region"].apply(normalise_region)
agents["hourly_cost"] = agents["hourly_cost"].apply(parse_hourly_cost)

before_agent_filter = len(agents)
agents = agents.dropna(subset=["agent_id", "team", "region", "hourly_cost"])
# Also drop cost <= 0 (already handled in parse, but be explicit)
agents = agents[agents["hourly_cost"] > 0]
summary["agents_invalid_dropped"] = before_agent_filter - len(agents)

# ── R5: Normalise agent_id in tickets, join to roster ─────────────────────────
tickets = tickets_raw.copy()
tickets["agent_id"] = tickets["agent_id"].str.upper()
before_join = len(tickets)
tickets = tickets.merge(agents[["agent_id", "team", "region", "hourly_cost"]],
                        on="agent_id", how="inner")
summary["tickets_no_agent_dropped"] = before_join - len(tickets)

# ── R6: Normalise channel ─────────────────────────────────────────────────────
def normalise_channel(val):
    if pd.isna(val):
        return np.nan
    v = val.strip().lower()
    if v in ("email", "e-mail"):
        return "email"
    if v in ("chat", "live chat"):
        return "chat"
    if v in ("phone", "call"):
        return "phone"
    return np.nan

before_channel = len(tickets)
tickets["channel"] = tickets["channel"].apply(normalise_channel)
tickets = tickets.dropna(subset=["channel"])
summary["tickets_invalid_channel_dropped"] = before_channel - len(tickets)

# ── R7: resolution_minutes ────────────────────────────────────────────────────
def parse_resolution(val):
    if pd.isna(val):
        return np.nan
    s = re.sub(r'(?i)\s*minutes?\s*$', '', str(val)).strip()
    s = re.sub(r'(?i)\s*min\s*$', '', s).strip()
    try:
        v = int(s)
        return v if 1 <= v <= 480 else np.nan
    except (ValueError, TypeError):
        return np.nan

before_res = len(tickets)
tickets["resolution_minutes"] = tickets["resolution_minutes"].apply(parse_resolution)
tickets = tickets.dropna(subset=["resolution_minutes"])
tickets["resolution_minutes"] = tickets["resolution_minutes"].astype(int)
summary["tickets_invalid_resolution_dropped"] = before_res - len(tickets)

# ── R8: satisfaction_score ────────────────────────────────────────────────────
def parse_satisfaction(val):
    if pd.isna(val):
        return np.nan
    try:
        v = int(str(val).strip())
        return v if 1 <= v <= 5 else np.nan
    except (ValueError, TypeError):
        return np.nan

tickets["satisfaction_score"] = tickets["satisfaction_score"].apply(parse_satisfaction)
# Row is kept; invalid/missing becomes NaN (empty cell)

# ── R9: reopened ──────────────────────────────────────────────────────────────
def parse_reopened(val):
    if pd.isna(val):
        return np.nan
    v = str(val).strip().lower()
    if v in ("yes", "y", "true", "1"):
        return 1
    if v in ("no", "n", "false", "0"):
        return 0
    return np.nan

before_reopened = len(tickets)
tickets["reopened"] = tickets["reopened"].apply(parse_reopened)
tickets = tickets.dropna(subset=["reopened"])
tickets["reopened"] = tickets["reopened"].astype(int)
summary["tickets_invalid_reopened_dropped"] = before_reopened - len(tickets)

# ── R10: labor_cost ───────────────────────────────────────────────────────────
tickets["labor_cost"] = (
    (tickets["resolution_minutes"] / 60.0) * tickets["hourly_cost"]
).round(2)

# ── R11: Select, order, sort, write ──────────────────────────────────────────
final_cols = [
    "ticket_id", "agent_id", "team", "region", "channel",
    "resolution_minutes", "satisfaction_score", "reopened",
    "hourly_cost", "labor_cost",
]
tickets = tickets[final_cols].copy()

# Cast categories
tickets["team"] = pd.Categorical(tickets["team"], categories=["Alpha", "Beta", "Gamma"])
tickets["region"] = pd.Categorical(tickets["region"], categories=["East", "West"])
tickets["channel"] = pd.Categorical(tickets["channel"], categories=["email", "chat", "phone"])

# satisfaction_score: keep as nullable int (use Int64 to allow NaN)
tickets["satisfaction_score"] = pd.array(
    tickets["satisfaction_score"], dtype=pd.Int64Dtype()
)

tickets = tickets.sort_values("ticket_id").reset_index(drop=True)

cleaned_rows = len(tickets)
summary["cleaned_rows"] = cleaned_rows

out_csv = os.path.join(OUTPUT_DIR, "cleaned.csv")
tickets.to_csv(out_csv, index=False)

out_json = os.path.join(OUTPUT_DIR, "cleaning_summary.json")
with open(out_json, "w") as f:
    json.dump(summary, f, indent=2)

print(f"Cleaning complete: {raw_rows} raw rows -> {cleaned_rows} cleaned rows.")
print(json.dumps(summary, indent=2))
