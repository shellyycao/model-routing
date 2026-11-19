import os
import re
import json
import pandas as pd
import numpy as np

INPUT_DIR = os.environ["INPUT_DIR"]
OUTPUT_DIR = os.environ["OUTPUT_DIR"]
os.makedirs(OUTPUT_DIR, exist_ok=True)

MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}

summary = {}

def read_csv_text(path):
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df.columns = [str(c).strip() for c in df.columns]
    for c in df.columns:
        df[c] = df[c].astype(str).str.strip()
        df[c] = df[c].where(~df[c].str.lower().isin(MISSING_TOKENS), pd.NA)
    return df

# R1: read both files as text, strip whitespace, normalise missing tokens
tickets = read_csv_text(os.path.join(INPUT_DIR, "tickets.csv"))
agents = read_csv_text(os.path.join(INPUT_DIR, "agents.csv"))
summary["raw_rows"] = int(len(tickets))
summary["raw_agent_rows"] = int(len(agents))

# R2: drop duplicate ticket_id rows first (keep first in raw-file order)
before = len(tickets)
tickets = tickets.dropna(subset=["ticket_id"])
tickets = tickets.drop_duplicates(subset="ticket_id", keep="first")
summary["r2_duplicate_ticket_ids_removed"] = int(before - len(tickets))

# R3: normalise agent_id to upper case, dedupe roster keeping first
agents["agent_id"] = agents["agent_id"].str.upper()
before = len(agents)
agents = agents.dropna(subset=["agent_id"])
agents = agents.drop_duplicates(subset="agent_id", keep="first")
summary["r3_duplicate_agent_ids_removed"] = int(before - len(agents))

# R4: normalise roster team/region, parse hourly_cost, exclude invalid rows
TEAM_MAP = {
    "alpha": "Alpha", "team alpha": "Alpha",
    "beta": "Beta", "team beta": "Beta",
    "gamma": "Gamma", "team gamma": "Gamma",
}
REGION_MAP = {"east": "East", "e": "East", "west": "West", "w": "West"}

def parse_cost(s):
    if pd.isna(s):
        return None
    t = s.replace("$", "").replace(",", "")
    t = re.sub(r"(?i)usd", "", t).strip()
    if not re.fullmatch(r"\d+(\.\d+)?", t):
        return None
    v = float(t)
    return v if v > 0 else None

agents["team"] = agents["team"].str.lower().map(TEAM_MAP)
agents["region"] = agents["region"].str.lower().map(REGION_MAP)
agents["hourly_cost"] = agents["hourly_cost"].map(parse_cost)
before = len(agents)
agents = agents.dropna(subset=["team", "region", "hourly_cost"])
agents["hourly_cost"] = agents["hourly_cost"].astype(float)
summary["r4_invalid_roster_rows_excluded"] = int(before - len(agents))
summary["roster_rows_kept"] = int(len(agents))

# R5: normalise ticket agent_id, join to roster, drop unmatched tickets
tickets["agent_id"] = tickets["agent_id"].str.upper()
before = len(tickets)
df = tickets.merge(agents, on="agent_id", how="inner", sort=False)
summary["r5_tickets_without_matching_agent_dropped"] = int(before - len(df))

# R6: normalise channel, drop invalid
CHANNEL_MAP = {
    "email": "email", "e-mail": "email",
    "chat": "chat", "live chat": "chat",
    "phone": "phone", "call": "phone",
}
df["channel"] = df["channel"].str.lower().map(CHANNEL_MAP)
before = len(df)
df = df.dropna(subset=["channel"])
summary["r6_invalid_channel_dropped"] = int(before - len(df))

# R7: parse resolution_minutes (strip trailing 'min'/'minutes'), whole number 1..480
def parse_minutes(s):
    if pd.isna(s):
        return None
    t = re.sub(r"(?i)\s*(minutes|min)\s*$", s.strip())
    t = t.strip()
    if re.fullmatch(r"\d+", t):
        v = int(t)
        if 1 <= v <= 480:
            return v
    return None

df["resolution_minutes"] = df["resolution_minutes"].map(parse_minutes)
before = len(df)
df = df.dropna(subset=["resolution_minutes"])
df["resolution_minutes"] = df["resolution_minutes"].astype(int)
summary["r7_invalid_resolution_minutes_dropped"] = int(before - len(df))

# R8: satisfaction_score whole number 1..5; invalid/missing -> empty, row kept
def parse_satisfaction(s):
    if pd.isna(s):
        return None
    t = s.strip()
    if re.fullmatch(r"\d+", t):
        v = int(t)
        if 1 <= v <= 5:
            return v
    return None

df["satisfaction_score"] = df["satisfaction_score"].map(parse_satisfaction).astype("Int64")
summary["r8_satisfaction_set_to_empty"] = int(df["satisfaction_score"].isna().sum())

# R9: reopened -> 1/0; drop invalid or missing
REOPENED_MAP = {
    "yes": 1, "y": 1, "true": 1, "1": 1,
    "no": 0, "n": 0, "false": 0, "0": 0,
}
df["reopened"] = df["reopened"].str.lower().map(REOPENED_MAP)
before = len(df)
df = df.dropna(subset=["reopened"])
df["reopened"] = df["reopened"].astype(int)
summary["r9_invalid_reopened_dropped"] = int(before - len(df))

# R10: labor_cost = resolution_minutes / 60 * hourly_cost, rounded to 2 decimals
df["labor_cost"] = (df["resolution_minutes"] / 60.0 * df["hourly_cost"]).round(2)

# R11: select exact columns, set categorical dtypes, sort by ticket_id, write CSV
out = df[["ticket_id", "agent_id", "team", "region", "channel",
          "resolution_minutes", "satisfaction_score", "reopened",
          "hourly_cost", "labor_cost"]].copy()
out["team"] = out["team"].astype("category")
out["region"] = out["region"].astype("category")
out["channel"] = out["channel"].astype("category")
out = out.sort_values("ticket_id", kind="stable").reset_index(drop=True)

output_path = os.path.join(OUTPUT_DIR, "cleaned.csv")
out.to_csv(output_path, index=False)
summary["cleaned_rows"] = int(len(out))

with open(os.path.join(OUTPUT_DIR, "cleaning_summary.json"), "w") as f:
    json.dump(summary, f, indent=2)

print("cleaned_rows:", summary["cleaned_rows"])
