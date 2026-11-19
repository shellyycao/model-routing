import os
import re
import json

import numpy as np
import pandas as pd

INPUT_DIR = os.environ["INPUT_DIR"]
OUTPUT_DIR = os.environ["OUTPUT_DIR"]
os.makedirs(OUTPUT_DIR, exist_ok=True)

MISSING_EXACT = {"", "NA", "N/A", "null", "None", "-"}
MISSING_LOWER = {"na", "n/a", "null", "none"}

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

TRAILING_MIN_RE = re.compile(r"\s*(?:minutes|min)\s*$", re.IGNORECASE)
WHOLE_NUM_RE = re.compile(r"\d+")


def clean_cell(v):
    s = str(v).strip()
    if s in MISSING_EXACT or s.lower() in MISSING_LOWER:
        return pd.NA
    return s


def read_text_csv(path):
    # R1: read as text, strip whitespace, standardise missing tokens
    df = pd.read_csv(path, dtype=str, keep_default_na=False,
                     na_filter=False, encoding="utf-8-sig")
    df.columns = [str(c).strip() for c in df.columns]
    for col in df.columns:
        df[col] = df[col].map(clean_cell)
    return df


def parse_hourly_cost(v):
    if pd.isna(v):
        return np.nan
    s = re.sub("usd", "", str(v), flags=re.IGNORECASE)
    s = s.replace("$", "").replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        return np.nan


def parse_resolution_minutes(v):
    if pd.isna(v):
        return pd.NA
    s = TRAILING_MIN_RE.sub("", str(v)).strip()
    if WHOLE_NUM_RE.fullmatch(s):
        n = int(s)
        if 1 <= n <= 480:
            return n
    return pd.NA


def parse_satisfaction(v):
    if pd.isna(v):
        return pd.NA
    s = str(v).strip()
    if WHOLE_NUM_RE.fullmatch(s):
        n = int(s)
        if 1 <= n <= 5:
            return n
    return pd.NA


def main():
    summary = {}

    tickets = read_text_csv(os.path.join(INPUT_DIR, "tickets.csv"))
    agents = read_text_csv(os.path.join(INPUT_DIR, "agents.csv"))
    summary["raw_rows"] = int(len(tickets))
    summary["agents_raw_rows"] = int(len(agents))

    # R2: drop duplicate ticket_id (keep first in raw-file order), then blank ids
    n = len(tickets)
    tickets = tickets.drop_duplicates(subset="ticket_id", keep="first")
    summary["tickets_dropped_duplicate_ticket_id"] = int(n - len(tickets))
    n = len(tickets)
    tickets = tickets[tickets["ticket_id"].notna()].copy()
    summary["tickets_dropped_missing_ticket_id"] = int(n - len(tickets))

    # R3: upper-case roster agent_id, drop blanks, dedupe keep first
    agents["agent_id"] = agents["agent_id"].str.upper()
    n = len(agents)
    agents = agents[agents["agent_id"].notna()].copy()
    summary["agents_dropped_missing_agent_id"] = int(n - len(agents))
    n = len(agents)
    agents = agents.drop_duplicates(subset="agent_id", keep="first")
    summary["agents_dropped_duplicate_agent_id"] = int(n - len(agents))

    # R4: normalise team / region / hourly_cost; drop invalid roster rows
    agents["team"] = agents["team"].str.lower().map(TEAM_MAP)
    agents["region"] = agents["region"].str.lower().map(REGION_MAP)
    agents["hourly_cost"] = agents["hourly_cost"].map(parse_hourly_cost)
    n = len(agents)
    valid = (agents["team"].notna() & agents["region"].notna()
             & agents["hourly_cost"].notna() & (agents["hourly_cost"] > 0))
    agents = agents[valid].copy()
    summary["agents_dropped_invalid_roster_row"] = int(n - len(agents))

    # R5: upper-case ticket agent_id, inner join to roster, drop unmatched
    tickets["agent_id"] = tickets["agent_id"].str.upper()
    n = len(tickets)
    df = tickets.merge(agents, on="agent_id", how="inner")
    summary["tickets_dropped_no_matching_agent"] = int(n - len(df))

    # R6: channel mapping, drop invalid
    df["channel"] = df["channel"].str.lower().map(CHANNEL_MAP)
    n = len(df)
    df = df[df["channel"].notna()].copy()
    summary["tickets_dropped_invalid_channel"] = int(n - len(df))

    # R7: resolution_minutes whole number 1..480, drop invalid
    df["resolution_minutes"] = df["resolution_minutes"].map(parse_resolution_minutes)
    n = len(df)
    df = df[df["resolution_minutes"].notna()].copy()
    summary["tickets_dropped_invalid_resolution_minutes"] = int(n - len(df))
    df["resolution_minutes"] = df["resolution_minutes"].astype("int64")

    # R8: satisfaction_score 1..5; invalid/missing -> empty cell, row kept
    df["satisfaction_score"] = (df["satisfaction_score"]
                                .map(parse_satisfaction).astype("Int64"))
    summary["tickets_satisfaction_score_set_empty"] = int(
        df["satisfaction_score"].isna().sum())

    # R9: reopened mapping, drop invalid/missing
    df["reopened"] = df["reopened"].str.lower().map(REOPENED_MAP)
    n = len(df)
    df = df[df["reopened"].notna()].copy()
    summary["tickets_dropped_invalid_reopened"] = int(n - len(df))
    df["reopened"] = df["reopened"].astype("int64")

    # R10: labor_cost = resolution_minutes / 60 * hourly_cost, 2 decimals
    df["hourly_cost"] = df["hourly_cost"].astype("float64")
    df["labor_cost"] = (df["resolution_minutes"] / 60.0
                        * df["hourly_cost"]).round(2)

    # R11: final schema (categoricals), sort by ticket_id, write CSV no index
    for col in ("team", "region", "channel"):
        df[col] = df[col].astype("category")

    out = (df[["ticket_id", "agent_id", "team", "region", "channel",
               "resolution_minutes", "satisfaction_score", "reopened",
               "hourly_cost", "labor_cost"]]
           .sort_values("ticket_id").reset_index(drop=True))

    summary["cleaned_rows"] = int(len(out))

    out.to_csv(os.path.join(OUTPUT_DIR, "cleaned.csv"), index=False)
    with open(os.path.join(OUTPUT_DIR, "cleaning_summary.json"),
              "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)

    print("cleaned_rows:", len(out))


if __name__ == "__main__":
    main()
