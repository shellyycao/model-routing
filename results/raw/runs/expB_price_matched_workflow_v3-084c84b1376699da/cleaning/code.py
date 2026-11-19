import os
import re
import json

import numpy as np
import pandas as pd

INPUT_DIR = os.environ["INPUT_DIR"]
OUTPUT_DIR = os.environ["OUTPUT_DIR"]
os.makedirs(OUTPUT_DIR, exist_ok=True)

MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}


def read_text_csv(path):
    """R1: read as text, strip whitespace, normalise missing tokens to NaN."""
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df.columns = [str(c).strip() for c in df.columns]
    for col in df.columns:
        df[col] = df[col].map(
            lambda v: np.nan
            if v is None or str(v).strip().lower() in MISSING_TOKENS
            else str(v).strip()
        )
    return df


def norm_key(value):
    if pd.isna(value):
        return None
    return " ".join(str(value).split()).lower()


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


def parse_hourly_cost(value):
    if pd.isna(value):
        return np.nan
    text = re.sub(r"(?i)usd", "", str(value))
    text = text.replace("$", "").replace(",", "").strip()
    if not re.fullmatch(r"\d+(?:\.\d+)?", text):
        return np.nan
    return float(text)


def parse_resolution_minutes(value):
    if pd.isna(value):
        return None
    text = re.sub(r"(?i)\s*(?:minutes|min)\s*$", "", str(value).strip()).strip()
    if not re.fullmatch(r"\d+", text):
        return None
    minutes = int(text)
    return minutes if 1 <= minutes <= 480 else None


def parse_satisfaction(value):
    if pd.isna(value):
        return pd.NA
    text = str(value).strip()
    if re.fullmatch(r"[1-5]", text):
        return int(text)
    return pd.NA


def parse_reopened(value):
    if pd.isna(value):
        return None
    return REOPENED_MAP.get(str(value).strip().lower())


summary = {}

# R1
tickets_raw = read_text_csv(os.path.join(INPUT_DIR, "tickets.csv"))
agents_raw = read_text_csv(os.path.join(INPUT_DIR, "agents.csv"))
summary["raw_rows"] = int(len(tickets_raw))
summary["raw_agent_rows"] = int(len(agents_raw))

# R2: drop duplicate ticket_id rows first, keeping first in raw-file order.
tickets = tickets_raw.drop_duplicates(subset="ticket_id", keep="first").copy()
summary["duplicate_ticket_id_rows_removed"] = int(len(tickets_raw) - len(tickets))
summary["tickets_dropped_missing_ticket_id"] = int(tickets["ticket_id"].isna().sum())
tickets = tickets.dropna(subset=["ticket_id"]).copy()

# R3: normalise agent_id to upper case, dedupe keeping first.
agents = agents_raw.copy()
agents["agent_id"] = agents["agent_id"].map(
    lambda v: np.nan if pd.isna(v) else str(v).upper()
)
n_before = len(agents)
agents = agents.drop_duplicates(subset="agent_id", keep="first").copy()
summary["duplicate_agent_id_rows_removed"] = int(n_before - len(agents))

# R4: normalise team/region, parse hourly_cost, exclude invalid roster rows.
agents["team"] = agents["team"].map(lambda v: TEAM_MAP.get(norm_key(v)))
agents["region"] = agents["region"].map(lambda v: REGION_MAP.get(norm_key(v)))
agents["hourly_cost"] = agents["hourly_cost"].map(parse_hourly_cost)
valid_agent = (
    agents["agent_id"].notna()
    & agents["team"].notna()
    & agents["region"].notna()
    & agents["hourly_cost"].notna()
    & (agents["hourly_cost"] > 0)
)
n_before = len(agents)
agents = agents[valid_agent].copy()
summary["agent_rows_excluded_invalid"] = int(n_before - len(agents))

# R5: upper-case ticket agent_id, inner join to roster, drop unmatched.
tickets["agent_id"] = tickets["agent_id"].map(
    lambda v: np.nan if pd.isna(v) else str(v).upper()
)
n_before = len(tickets)
merged = tickets.merge(agents, on="agent_id", how="inner", sort=False)
summary["tickets_dropped_unmatched_agent"] = int(n_before - len(merged))

# R6: channel mapping; drop invalid.
merged["channel"] = merged["channel"].map(lambda v: CHANNEL_MAP.get(norm_key(v)))
n_before = len(merged)
merged = merged[merged["channel"].notna()].copy()
summary["tickets_dropped_invalid_channel"] = int(n_before - len(merged))

# R7: resolution_minutes 1..480; drop invalid.
merged["resolution_minutes"] = merged["resolution_minutes"].map(parse_resolution_minutes)
n_before = len(merged)
merged = merged[merged["resolution_minutes"].notna()].copy()
summary["tickets_dropped_invalid_resolution_minutes"] = int(n_before - len(merged))
merged["resolution_minutes"] = merged["resolution_minutes"].astype(int)

# R8: satisfaction_score 1..5; invalid/missing -> empty cell, row kept.
merged["satisfaction_score"] = pd.array(
    [parse_satisfaction(v) for v in merged["satisfaction_score"]], dtype="Int64"
)
summary["satisfaction_score_blank"] = int(merged["satisfaction_score"].isna().sum())

# R9: reopened mapping; drop invalid/missing.
merged["reopened"] = merged["reopened"].map(parse_reopened)
n_before = len(merged)
merged = merged[merged["reopened"].notna()].copy()
summary["tickets_dropped_invalid_reopened"] = int(n_before - len(merged))
merged["reopened"] = merged["reopened"].astype(int)

# R10: labor cost.
merged["hourly_cost"] = merged["hourly_cost"].astype(float)
merged["labor_cost"] = (
    merged["resolution_minutes"] / 60.0 * merged["hourly_cost"]
).round(2)

# R11: column order, dtypes, sort, write.
out = merged[
    [
        "ticket_id", "agent_id", "team", "region", "channel",
        "resolution_minutes", "satisfaction_score", "reopened",
        "hourly_cost", "labor_cost",
    ]
].copy()
for col in ("team", "region", "channel"):
    out[col] = out[col].astype("category")
out = out.sort_values("ticket_id", kind="stable").reset_index(drop=True)
summary["cleaned_rows"] = int(len(out))

out.to_csv(os.path.join(OUTPUT_DIR, "cleaned.csv"), index=False)
with open(os.path.join(OUTPUT_DIR, "cleaning_summary.json"), "w") as fh:
    json.dump(summary, fh, indent=2)
