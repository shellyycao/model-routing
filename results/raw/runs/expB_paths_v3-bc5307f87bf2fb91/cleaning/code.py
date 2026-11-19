import os
import json
import re
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def strip_and_normalise(df):
    """Strip whitespace from all string cells and replace defined missing values with NaN."""
    missing_vals = {"", "NA", "N/A", "null", "None", "-"}
    # Strip whitespace
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    # Replace missing values (case‑insensitive)
    df = df.replace(to_replace=lambda x: isinstance(x, str) and x.upper() in missing_vals, value=np.nan)
    return df

def clean_hourly_cost(val):
    if pd.isna(val):
        return np.nan
    # Remove currency symbols, commas, spaces, the word USD, etc.
    cleaned = re.sub(r"[\$,]", "", str(val), flags=re.IGNORECASE)
    cleaned = re.sub(r"USD", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip()
    try:
        cost = float(cleaned)
        return cost if cost > 0 else np.nan
    except ValueError:
        return np.nan

def map_team(val):
    if pd.isna(val):
        return np.nan
    low = val.lower()
    if "alpha" in low:
        return "Alpha"
    if "beta" in low:
        return "Beta"
    if "gamma" in low:
        return "Gamma"
    return np.nan

def map_region(val):
    if pd.isna(val):
        return np.nan
    low = val.lower()
    if low in {"east", "e"}:
        return "East"
    if low in {"west", "w"}:
        return "West"
    return np.nan

def map_channel(val):
    if pd.isna(val):
        return np.nan
    low = val.lower()
    if low in {"email", "e-mail"}:
        return "email"
    if low in {"chat", "live chat"}:
        return "chat"
    if low in {"phone", "call"}:
        return "phone"
    return np.nan

def parse_resolution(val):
    if pd.isna(val):
        return np.nan
    # Remove trailing words like 'min' or 'minutes'
    cleaned = re.sub(r"\s*(min|minutes)$", "", str(val).strip(), flags=re.IGNORECASE)
    try:
        minutes = int(cleaned)
        if 1 <= minutes <= 480:
            return minutes
        else:
            return np.nan
    except ValueError:
        return np.nan

def parse_satisfaction(val):
    if pd.isna(val):
        return np.nan
    try:
        score = int(val)
        if 1 <= score <= 5:
            return score
        else:
            return np.nan
    except ValueError:
        return np.nan

def map_reopened(val):
    if pd.isna(val):
        return np.nan
    low = str(val).strip().lower()
    if low in {"yes", "y", "true", "1"}:
        return 1
    if low in {"no", "n", "false", "0"}:
        return 0
    return np.nan

# ---------------------------------------------------------------------------
# Main cleaning routine
# ---------------------------------------------------------------------------

def main():
    input_dir = os.environ.get("INPUT_DIR")
    output_dir = os.environ.get("OUTPUT_DIR")
    if not input_dir or not output_dir:
        raise RuntimeError("Both INPUT_DIR and OUTPUT_DIR environment variables must be set.")

    tickets_path = os.path.join(input_dir, "tickets.csv")
    agents_path = os.path.join(input_dir, "agents.csv")

    # -------------------------------------------------------------------
    # R1 – read as text, strip whitespace, treat defined strings as missing
    # -------------------------------------------------------------------
    tickets_raw = pd.read_csv(tickets_path, dtype=str, keep_default_na=False)
    agents_raw = pd.read_csv(agents_path, dtype=str, keep_default_na=False)

    tickets = strip_and_normalise(tickets_raw)
    agents = strip_and_normalise(agents_raw)

    # Counters for summary
    summary = {
        "raw_rows": len(tickets_raw),
        "duplicate_ticket_id_removed": 0,
        "duplicate_agent_id_removed": 0,
        "invalid_agent_rows_excluded": 0,
        "tickets_without_agent": 0,
        "invalid_channel_dropped": 0,
        "invalid_resolution_dropped": 0,
        "invalid_reopened_dropped": 0,
        "cleaned_rows": 0
    }

    # -------------------------------------------------------------------
    # R2 – remove duplicate ticket_id, keep first occurrence
    # -------------------------------------------------------------------
    before_dup = len(tickets)
    tickets = tickets.drop_duplicates(subset="ticket_id", keep="first")
    summary["duplicate_ticket_id_removed"] = before_dup - len(tickets)

    # -------------------------------------------------------------------
    # R3 – normalise agent_id to upper case and deduplicate agents
    # -------------------------------------------------------------------
    agents["agent_id"] = agents["agent_id"].str.upper()
    before_agent_dup = len(agents)
    agents = agents.drop_duplicates(subset="agent_id", keep="first")
    summary["duplicate_agent_id_removed"] = before_agent_dup - len(agents)

    # -------------------------------------------------------------------
    # R4 – clean agent roster fields
    # -------------------------------------------------------------------
    agents["team"] = agents["team"].apply(map_team)
    agents["region"] = agents["region"].apply(map_region)
    agents["hourly_cost"] = agents["hourly_cost"].apply(clean_hourly_cost)

    # Exclude rows with any invalid field (team, region, hourly_cost) or cost <= 0
    valid_agent_mask = (
        agents["team"].notna() &
        agents["region"].notna() &
        agents["hourly_cost"].notna()
    )
    summary["invalid_agent_rows_excluded"] = len(agents) - valid_agent_mask.sum()
    agents = agents[valid_agent_mask].copy()

    # -------------------------------------------------------------------
    # R5 – normalise ticket agent_id and join to roster, drop non‑matching tickets
    # -------------------------------------------------------------------
    tickets["agent_id"] = tickets["agent_id"].str.upper()
    tickets = tickets.merge(agents, on="agent_id", how="inner", suffixes=("", "_agent"))
    # After inner join, rows without a matching agent are already removed
    summary["tickets_without_agent"] = summary["raw_rows"] - len(tickets) - summary["duplicate_ticket_id_removed"]

    # -------------------------------------------------------------------
    # R6 – map channel, drop invalid
    # -------------------------------------------------------------------
    tickets["channel"] = tickets["channel"].apply(map_channel)
    before_channel = len(tickets)
    tickets = tickets[tickets["channel"].notna()]
    summary["invalid_channel_dropped"] = before_channel - len(tickets)

    # -------------------------------------------------------------------
    # R7 – clean resolution_minutes, drop invalid
    # -------------------------------------------------------------------
    tickets["resolution_minutes"] = tickets["resolution_minutes"].apply(parse_resolution)
    before_res = len(tickets)
    tickets = tickets[tickets["resolution_minutes"].notna()]
    summary["invalid_resolution_dropped"] = before_res - len(tickets)

    # -------------------------------------------------------------------
    # R8 – parse satisfaction_score (keep row, set NaN if invalid)
    # -------------------------------------------------------------------
    tickets["satisfaction_score"] = tickets["satisfaction_score"].apply(parse_satisfaction)

    # -------------------------------------------------------------------
    # R9 – map reopened, drop invalid or missing
    # -------------------------------------------------------------------
    tickets["reopened"] = tickets["reopened"].apply(map_reopened)
    before_reopen = len(tickets)
    tickets = tickets[tickets["reopened"].notna()]
    summary["invalid_reopened_dropped"] = before_reopen - len(tickets)

    # -------------------------------------------------------------------
    # R10 – compute labor_cost
    # -------------------------------------------------------------------
    tickets["labor_cost"] = (tickets["resolution_minutes"] / 60.0) * tickets["hourly_cost"]
    tickets["labor_cost"] = tickets["labor_cost"].round(2)

    # -------------------------------------------------------------------
    # R11 – final column order and output
    # -------------------------------------------------------------------
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

    # Ensure dtypes / categories as required (pandas will keep as object/int/float)
    cleaned["resolution_minutes"] = cleaned["resolution_minutes"].astype(int)
    cleaned["reopened"] = cleaned["reopened"].astype(int)
    cleaned["hourly_cost"] = cleaned["hourly_cost"].astype(float)
    cleaned["labor_cost"] = cleaned["labor_cost"].astype(float)
    # satisfaction_score may be NaN – keep as float/int compatible

    # Write cleaned CSV
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    cleaned.to_csv(cleaned_path, index=False)
    summary["cleaned_rows"] = len(cleaned)

    # Write cleaning summary JSON
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    main()
