"""Cleaning stage: clean the support-ticket export and agent roster, join them,
and emit cleaned.csv plus cleaning_summary.json."""

import json
import os
import re

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
RES_SUFFIX_RE = re.compile(r"(?i)\s*(?:minutes|min)\s*$")
INT_RE = re.compile(r"\d+")


def read_text_csv(path):
    """R1: read every column as text, strip whitespace, normalise missing tokens."""
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    frame.columns = [str(c).strip() for c in frame.columns]
    for col in frame.columns:
        values = frame[col].astype(str).str.strip()
        frame[col] = values.where(~values.str.lower().isin(MISSING_TOKENS), pd.NA)
    return frame


def parse_hourly_cost(value):
    """R4: strip $ / USD / commas and parse a float cost."""
    if pd.isna(value):
        return None
    text = re.sub(r"(?i)usd", "", str(value)).replace("$", "").replace(",", "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_resolution_minutes(value):
    """R7: drop a trailing 'min'/'minutes', parse a whole number in [1, 480]."""
    if pd.isna(value):
        return None
    text = RES_SUFFIX_RE.sub("", str(value)).strip()
    if not INT_RE.fullmatch(text):
        return None
    minutes = int(text)
    return minutes if 1 <= minutes <= 480 else None


def parse_satisfaction(value):
    """R8: whole number in [1, 5]; invalid or missing becomes an empty cell."""
    if pd.isna(value):
        return pd.NA
    text = str(value).strip()
    if INT_RE.fullmatch(text):
        score = int(text)
        if 1 <= score <= 5:
            return score
    return pd.NA


summary = {}

# ---- Load (R1) -------------------------------------------------------------
tickets = read_text_csv(os.path.join(INPUT_DIR, "tickets.csv"))
agents = read_text_csv(os.path.join(INPUT_DIR, "agents.csv"))
summary["raw_rows"] = len(tickets)
summary["raw_agent_rows"] = len(agents)

# ---- R2: de-duplicate tickets on ticket_id (keep first, raw-file order) ----
before = len(tickets)
tickets = tickets.drop_duplicates(subset=["ticket_id"], keep="first")
summary["duplicate_ticket_id_rows_removed"] = before - len(tickets)
missing_tid = int(tickets["ticket_id"].isna().sum())
tickets = tickets[tickets["ticket_id"].notna()].copy()
summary["tickets_dropped_missing_ticket_id"] = missing_tid

# ---- R3: normalise agent_id to upper case, de-duplicate roster -------------
agents["agent_id"] = agents["agent_id"].str.upper()
before = len(agents)
agents = agents.drop_duplicates(subset=["agent_id"], keep="first")
summary["duplicate_agent_id_rows_removed"] = before - len(agents)

# ---- R4: clean roster team / region / hourly_cost, drop invalid rows -------
agents["team"] = agents["team"].str.lower().map(TEAM_MAP)
agents["region"] = agents["region"].str.lower().map(REGION_MAP)
agents["hourly_cost"] = pd.to_numeric(
    agents["hourly_cost"].map(parse_hourly_cost), errors="coerce"
)
valid_agent = (
    agents["agent_id"].notna()
    & agents["team"].notna()
    & agents["region"].notna()
    & agents["hourly_cost"].notna()
    & (agents["hourly_cost"] > 0)
)
summary["agent_rows_excluded_invalid"] = int((~valid_agent).sum())
roster = agents.loc[valid_agent, ["agent_id", "team", "region", "hourly_cost"]].copy()

# ---- R5: normalise ticket agent_id, inner-join to roster -------------------
tickets["agent_id"] = tickets["agent_id"].str.upper()
before = len(tickets)
merged = tickets.merge(roster, on="agent_id", how="inner")
summary["tickets_dropped_unmatched_agent"] = before - len(merged)

# ---- R6: channel mapping, drop invalid channels ----------------------------
merged["channel"] = merged["channel"].str.lower().map(CHANNEL_MAP)
before = len(merged)
merged = merged[merged["channel"].notna()].copy()
summary["tickets_dropped_invalid_channel"] = before - len(merged)

# ---- R7: resolution_minutes, drop invalid rows -----------------------------
merged["resolution_minutes"] = merged["resolution_minutes"].map(parse_resolution_minutes)
before = len(merged)
merged = merged[merged["resolution_minutes"].notna()].copy()
summary["tickets_dropped_invalid_resolution_minutes"] = before - len(merged)

# ---- R8: satisfaction_score (invalid/missing -> empty cell, row kept) ------
merged["satisfaction_score"] = merged["satisfaction_score"].map(parse_satisfaction)
summary["satisfaction_scores_set_empty"] = int(merged["satisfaction_score"].isna().sum())

# ---- R9: reopened mapping, drop invalid or missing -------------------------
merged["reopened"] = merged["reopened"].str.lower().map(REOPENED_MAP)
before = len(merged)
merged = merged[merged["reopened"].notna()].copy()
summary["tickets_dropped_invalid_reopened"] = before - len(merged)

# ---- R10: labour cost -------------------------------------------------------
merged["resolution_minutes"] = merged["resolution_minutes"].astype(int)
merged["reopened"] = merged["reopened"].astype(int)
merged["hourly_cost"] = merged["hourly_cost"].astype(float)
merged["labor_cost"] = (
    merged["resolution_minutes"] / 60.0 * merged["hourly_cost"]
).round(2)

# ---- R11: final schema, sort, write -----------------------------------------
out = merged[
    [
        "ticket_id", "agent_id", "team", "region", "channel",
        "resolution_minutes", "satisfaction_score", "reopened",
        "hourly_cost", "labor_cost",
    ]
].sort_values("ticket_id").reset_index(drop=True)

out["team"] = pd.Categorical(out["team"], categories=["Alpha", "Beta", "Gamma"])
out["region"] = pd.Categorical(out["region"], categories=["East", "West"])
out["channel"] = pd.Categorical(out["channel"], categories=["email", "chat", "phone"])
out["satisfaction_score"] = out["satisfaction_score"].astype("Int64")

out.to_csv(os.path.join(OUTPUT_DIR, "cleaned.csv"), index=False)

summary["cleaned_rows"] = len(out)
with open(os.path.join(OUTPUT_DIR, "cleaning_summary.json"), "w", encoding="utf-8") as fh:
    json.dump(summary, fh, indent=2)
