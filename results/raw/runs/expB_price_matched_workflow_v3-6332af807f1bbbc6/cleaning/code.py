import os
import re
import json
import pandas as pd
import numpy as np

INPUT_DIR = os.environ["INPUT_DIR"]
OUTPUT_DIR = os.environ["OUTPUT_DIR"]
os.makedirs(OUTPUT_DIR, exist_ok=True)

MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}


def norm_text(value):
    """R1: strip whitespace and normalise missing tokens to NA."""
    if value is None:
        return pd.NA
    text = str(value).strip()
    if text.lower() in MISSING_TOKENS:
        return pd.NA
    return text


def read_text_csv(path):
    df = pd.read_csv(path, dtype=str, keep_default_na=False, na_filter=False)
    for col in df.columns:
        df[col] = df[col].map(norm_text)
    return df


summary = {}

# R1: read both files as text, strip, normalise missing values.
tickets = read_text_csv(os.path.join(INPUT_DIR, "tickets.csv"))
agents = read_text_csv(os.path.join(INPUT_DIR, "agents.csv"))
summary["raw_rows"] = int(len(tickets))
summary["agents_raw_rows"] = int(len(agents))

# R2: drop duplicate ticket_id rows (keep first in raw-file order) before filtering.
summary["r2_missing_ticket_id_removed"] = int(tickets["ticket_id"].isna().sum())
tickets = tickets.dropna(subset=["ticket_id"])
before = len(tickets)
tickets = tickets.drop_duplicates(subset="ticket_id", keep="first")
summary["r2_duplicate_ticket_id_removed"] = int(before - len(tickets))

# R3: upper-case agent_id, drop duplicates keeping the first.
agents["agent_id"] = agents["agent_id"].map(lambda v: v.upper() if pd.notna(v) else v)
agents = agents.dropna(subset=["agent_id"])
before = len(agents)
agents = agents.drop_duplicates(subset="agent_id", keep="first")
summary["r3_duplicate_agent_id_removed"] = int(before - len(agents))

# R4: normalise team, region and hourly_cost; exclude invalid roster rows.
TEAM_MAP = {
    "alpha": "Alpha", "team alpha": "Alpha",
    "beta": "Beta", "team beta": "Beta",
    "gamma": "Gamma", "team gamma": "Gamma",
}
REGION_MAP = {"east": "East", "e": "East", "west": "West", "w": "West"}


def parse_cost(value):
    if pd.isna(value):
        return np.nan
    text = re.sub(r"(?i)usd", "", value).replace("$", "").replace(",", "").strip()
    try:
        return float(text)
    except ValueError:
        return np.nan


agents["team"] = agents["team"].map(lambda v: TEAM_MAP.get(v.lower()) if pd.notna(v) else None)
agents["region"] = agents["region"].map(lambda v: REGION_MAP.get(v.lower()) if pd.notna(v) else None)
agents["hourly_cost"] = agents["hourly_cost"].map(parse_cost)
valid_roster = (
    agents["team"].notna()
    & agents["region"].notna()
    & agents["hourly_cost"].notna()
    & (agents["hourly_cost"] > 0)
)
summary["r4_invalid_roster_rows_removed"] = int((~valid_roster).sum())
agents = agents.loc[valid_roster, ["agent_id", "team", "region", "hourly_cost"]]

# R5: upper-case ticket agent_id and inner-join to the cleaned roster.
tickets["agent_id"] = tickets["agent_id"].map(lambda v: v.upper() if pd.notna(v) else v)
before = len(tickets)
df = tickets.merge(agents, on="agent_id", how="inner")
summary["r5_tickets_without_matching_agent_removed"] = int(before - len(df))

# R6: normalise channel; drop invalid rows.
CHANNEL_MAP = {
    "email": "email", "e-mail": "email",
    "chat": "chat", "live chat": "chat",
    "phone": "phone", "call": "phone",
}
df["channel"] = df["channel"].map(lambda v: CHANNEL_MAP.get(v.lower()) if pd.notna(v) else None)
before = len(df)
df = df[df["channel"].notna()]
summary["r6_invalid_channel_removed"] = int(before - len(df))

# R7: parse resolution_minutes (strip trailing 'min'/'minutes'); whole number 1..480; drop invalid.
def parse_resolution(value):
    if pd.isna(value):
        return np.nan
    text = re.sub(r"(?i)\s*(minutes|min)\s*$", "", value).strip()
    if not re.fullmatch(r"\d+", text):
        return np.nan
    number = int(text)
    return number if 1 <= number <= 480 else np.nan


df["resolution_minutes"] = df["resolution_minutes"].map(parse_resolution)
before = len(df)
df = df[df["resolution_minutes"].notna()]
summary["r7_invalid_resolution_minutes_removed"] = int(before - len(df))
df["resolution_minutes"] = df["resolution_minutes"].astype(int)

# R8: satisfaction_score whole number 1..5; invalid or missing becomes empty, row kept.
def parse_satisfaction(value):
    if pd.isna(value):
        return pd.NA
    text = value.strip()
    if re.fullmatch(r"\d+", text):
        number = int(text)
        if 1 <= number <= 5:
            return number
    return pd.NA


df["satisfaction_score"] = df["satisfaction_score"].map(parse_satisfaction).astype("Int64")
summary["r8_satisfaction_empty_cells"] = int(df["satisfaction_score"].isna().sum())

# R9: reopened mapped to 1/0; drop invalid or missing.
REOPENED_MAP = {
    "yes": 1, "y": 1, "true": 1, "1": 1,
    "no": 0, "n": 0, "false": 0, "0": 0,
}
df["reopened"] = df["reopened"].map(lambda v: REOPENED_MAP.get(v.lower()) if pd.notna(v) else None)
before = len(df)
df = df[df["reopened"].notna()]
summary["r9_invalid_reopened_removed"] = int(before - len(df))
df["reopened"] = df["reopened"].astype(int)

# R10: labour cost.
df["hourly_cost"] = df["hourly_cost"].astype(float)
df["labor_cost"] = (df["resolution_minutes"] / 60.0 * df["hourly_cost"]).round(2)

# R11: final schema, categories, sort, write.
df["team"] = pd.Categorical(df["team"], categories=["Alpha", "Beta", "Gamma"])
df["region"] = pd.Categorical(df["region"], categories=["East", "West"])
df["channel"] = pd.Categorical(df["channel"], categories=["email", "chat", "phone"])
df = df[[
    "ticket_id", "agent_id", "team", "region", "channel",
    "resolution_minutes", "satisfaction_score", "reopened",
    "hourly_cost", "labor_cost",
]]
df = df.sort_values("ticket_id", kind="stable")
df.to_csv(os.path.join(OUTPUT_DIR, "cleaned.csv"), index=False)
summary["cleaned_rows"] = int(len(df))

with open(os.path.join(OUTPUT_DIR, "cleaning_summary.json"), "w") as fh:
    json.dump(summary, fh, indent=2)
