import os
import json
import re
import pandas as pd
import numpy as np

# ---------- Helper functions ----------

def clean_string_series(series):
    """Strip whitespace from all string values in a Series."""
    return series.apply(lambda x: x.strip() if isinstance(x, str) else x)

def normalize_agent_id(df, col="agent_id"):
    df[col] = df[col].str.upper()
    return df

def map_team(val):
    if pd.isna(val):
        return None
    low = str(val).lower()
    if "alpha" in low:
        return "Alpha"
    if "beta" in low:
        return "Beta"
    if "gamma" in low:
        return "Gamma"
    return None

def map_region(val):
    if pd.isna(val):
        return None
    low = str(val).lower()
    if low.startswith('e'):
        return "East"
    if low.startswith('w'):
        return "West"
    return None

def parse_hourly_cost(val):
    if pd.isna(val):
        return np.nan
    # Remove $ , USD and spaces
    cleaned = re.sub(r"[\$,USDusd]", "", str(val))
    cleaned = cleaned.replace(",", "").strip()
    try:
        cost = float(cleaned)
        return cost if cost > 0 else np.nan
    except ValueError:
        return np.nan

def map_channel(val):
    if pd.isna(val):
        return None
    low = str(val).lower().replace(" ", "")
    mapping = {
        "email": "email",
        "e-mail": "email",
        "chat": "chat",
        "livechat": "chat",
        "phone": "phone",
        "call": "phone"
    }
    return mapping.get(low)

def clean_resolution(val):
    if pd.isna(val):
        return np.nan
    s = str(val).lower().replace("minutes", "").replace("minute", "").replace("min", "").strip()
    # Extract leading integer
    m = re.search(r"(\d+)", s)
    if not m:
        return np.nan
    minutes = int(m.group(1))
    if 1 <= minutes <= 480:
        return minutes
    return np.nan

def parse_satisfaction(val):
    if pd.isna(val):
        return np.nan
    try:
        iv = int(float(val))
        if 1 <= iv <= 5:
            return iv
    except Exception:
        pass
    return np.nan

def map_reopened(val):
    if pd.isna(val):
        return None
    low = str(val).strip().lower()
    true_set = {"yes", "y", "true", "1"}
    false_set = {"no", "n", "false", "0"}
    if low in true_set:
        return 1
    if low in false_set:
        return 0
    return None

# ---------- Main cleaning routine ----------

def main():
    input_dir = os.getenv("INPUT_DIR")
    output_dir = os.getenv("OUTPUT_DIR")
    if not input_dir or not output_dir:
        raise RuntimeError("INPUT_DIR and OUTPUT_DIR environment variables must be set")

    tickets_path = os.path.join(input_dir, "tickets.csv")
    agents_path = os.path.join(input_dir, "agents.csv")

    # Define missing value markers
    na_vals = ["", "NA", "N/A", "null", "None", "-"]

    # ---- Read raw files ----
    tickets_raw = pd.read_csv(tickets_path, dtype=str, keep_default_na=False, na_values=na_vals)
    agents_raw = pd.read_csv(agents_path, dtype=str, keep_default_na=False, na_values=na_vals)

    # Strip whitespace from all string cells
    tickets_raw = tickets_raw.apply(clean_string_series)
    agents_raw = agents_raw.apply(clean_string_series)

    # Summary counters
    summary = {
        "raw_rows": len(tickets_raw),
        "duplicate_ticket_id_removed": 0,
        "duplicate_agent_id_removed": 0,
        "invalid_agent_rows_excluded": 0,
        "tickets_without_agent": 0,
        "invalid_channel_removed": 0,
        "invalid_resolution_removed": 0,
        "invalid_reopened_removed": 0,
        "cleaned_rows": 0
    }

    # ---- R2: Remove duplicate ticket_id rows (keep first) ----
    before_dup = len(tickets_raw)
    tickets = tickets_raw.drop_duplicates(subset="ticket_id", keep="first")
    summary["duplicate_ticket_id_removed"] = before_dup - len(tickets)

    # ---- R3: Normalise agent_id in agents and drop duplicates ----
    agents = agents_raw.copy()
    agents = normalize_agent_id(agents, "agent_id")
    before_agent_dup = len(agents)
    agents = agents.drop_duplicates(subset="agent_id", keep="first")
    summary["duplicate_agent_id_removed"] = before_agent_dup - len(agents)

    # ---- R4: Clean agent roster fields ----
    agents["team"] = agents["team"].apply(map_team)
    agents["region"] = agents["region"].apply(map_region)
    agents["hourly_cost"] = agents["hourly_cost"].apply(parse_hourly_cost)

    # Keep only rows with valid team, region and positive hourly_cost
    valid_agents_mask = (
        agents["team"].notna() &
        agents["region"].notna() &
        agents["hourly_cost"].notna()
    )
    summary["invalid_agent_rows_excluded"] = len(agents) - valid_agents_mask.sum()
    agents = agents[valid_agents_mask].copy()

    # ---- R5: Normalise agent_id in tickets and join ----
    tickets = normalize_agent_id(tickets, "agent_id")
    tickets = tickets.merge(
        agents[["agent_id", "team", "region", "hourly_cost"]],
        on="agent_id",
        how="inner",
        suffixes=("", "_agent")
    )
    # Count tickets dropped because of missing agent
    summary["tickets_without_agent"] = len(tickets_raw) - len(tickets)

    # ---- R6: Map channel, drop invalid ----
    tickets["channel"] = tickets["channel"].apply(map_channel)
    before_chan = len(tickets)
    tickets = tickets[tickets["channel"].notna()].copy()
    summary["invalid_channel_removed"] = before_chan - len(tickets)

    # ---- R7: Clean resolution_minutes, drop invalid ----
    tickets["resolution_minutes"] = tickets["resolution_minutes"].apply(clean_resolution)
    before_res = len(tickets)
    tickets = tickets[tickets["resolution_minutes"].notna()].copy()
    summary["invalid_resolution_removed"] = before_res - len(tickets)
    tickets["resolution_minutes"] = tickets["resolution_minutes"].astype(int)

    # ---- R8: Satisfaction score (keep row, set NaN if invalid) ----
    tickets["satisfaction_score"] = tickets["satisfaction_score"].apply(parse_satisfaction)
    # Keep as float/int, pandas will store NaN for missing

    # ---- R9: Reopened mapping, drop invalid/missing ----
    tickets["reopened"] = tickets["reopened"].apply(map_reopened)
    before_reopen = len(tickets)
    tickets = tickets[tickets["reopened"].notna()].copy()
    summary["invalid_reopened_removed"] = before_reopen - len(tickets)
    tickets["reopened"] = tickets["reopened"].astype(int)

    # ---- R10: Compute labor_cost ----
    tickets["hourly_cost"] = tickets["hourly_cost"].astype(float)
    tickets["labor_cost"] = (tickets["resolution_minutes"] / 60.0) * tickets["hourly_cost"]
    tickets["labor_cost"] = tickets["labor_cost"].round(2)

    # ---- R11: Select and order columns, sort ----
    final_cols = [
        "ticket_id",
        "agent_id",
        "team",
        "region",
        "channel",
        "resolution_minutes",
        "satisfaction_score",
        "reopened",
        "hourly_cost",
        "labor_cost"
    ]
    cleaned = tickets[final_cols].copy()
    cleaned = cleaned.sort_values(by="ticket_id")

    # Write cleaned CSV
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    cleaned.to_csv(cleaned_path, index=False)

    # Update summary
    summary["cleaned_rows"] = len(cleaned)

    # Write cleaning summary JSON
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    main()
