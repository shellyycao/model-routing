import os
import json
import re
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def strip_and_normalise(df):
    """Strip whitespace from all string cells and replace common missing markers with NaN."""
    missing_markers = {"", "NA", "N/A", "null", "None", "-"}
    def clean_cell(x):
        if isinstance(x, str):
            x = x.strip()
            if x in missing_markers:
                return np.nan
            return x
        return x
    return df.applymap(clean_cell)

def parse_hourly_cost(val):
    if pd.isna(val):
        return np.nan
    # Remove currency symbols, commas, spaces
    cleaned = re.sub(r"[\$,USDusd]", "", str(val))
    cleaned = cleaned.replace(",", "").strip()
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
    cleaned = re.sub(r"(?i)\s*(min|minutes)$", "", str(val)).strip()
    if not cleaned.isdigit():
        return np.nan
    minutes = int(cleaned)
    if 1 <= minutes <= 480:
        return minutes
    return np.nan

def parse_satisfaction(val):
    if pd.isna(val):
        return np.nan
    if isinstance(val, (int, float)) and not pd.isna(val):
        iv = int(val)
    else:
        s = str(val).strip()
        if not s.isdigit():
            return np.nan
        iv = int(s)
    if 1 <= iv <= 5:
        return iv
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
    input_dir = os.environ.get("INPUT_DIR", ".")
    output_dir = os.environ.get("OUTPUT_DIR", ".")

    tickets_path = os.path.join(input_dir, "tickets.csv")
    agents_path = os.path.join(input_dir, "agents.csv")

    # ---------------------------------------------------
    # R1 – read as text, strip whitespace, normalise missing
    # ---------------------------------------------------
    tickets_raw = pd.read_csv(tickets_path, dtype=str, keep_default_na=False)
    agents_raw = pd.read_csv(agents_path, dtype=str, keep_default_na=False)

    tickets = strip_and_normalise(tickets_raw)
    agents = strip_and_normalise(agents_raw)

    summary = {
        "raw_rows": len(tickets),
        "duplicate_tickets_removed": 0,
        "duplicate_agents_removed": 0,
        "invalid_agent_rows": 0,
        "tickets_no_agent": 0,
        "invalid_channels": 0,
        "invalid_resolution": 0,
        "invalid_reopened": 0,
        "cleaned_rows": 0
    }

    # ---------------------------------------------------
    # R2 – deduplicate tickets on ticket_id (keep first)
    # ---------------------------------------------------
    before = len(tickets)
    tickets = tickets.drop_duplicates(subset="ticket_id", keep="first")
    summary["duplicate_tickets_removed"] = before - len(tickets)

    # ---------------------------------------------------
    # R3 – normalise agent_id to upper case and deduplicate agents
    # ---------------------------------------------------
    agents["agent_id"] = agents["agent_id"].str.upper()
    before_agents = len(agents)
    agents = agents.drop_duplicates(subset="agent_id", keep="first")
    summary["duplicate_agents_removed"] = before_agents - len(agents)

    # ---------------------------------------------------
    # R4 – clean agent roster fields
    # ---------------------------------------------------
    agents["team"] = agents["team"].apply(map_team)
    agents["region"] = agents["region"].apply(map_region)
    agents["hourly_cost"] = agents["hourly_cost"].apply(parse_hourly_cost)

    # Identify rows with any invalid field (team, region, hourly_cost)
    valid_agents_mask = agents["team"].notna() & agents["region"].notna() & agents["hourly_cost"].notna()
    summary["invalid_agent_rows"] = len(agents) - valid_agents_mask.sum()
    agents = agents[valid_agents_mask].copy()

    # ---------------------------------------------------
    # R5 – normalise ticket agent_id and join to roster
    # ---------------------------------------------------
    tickets["agent_id"] = tickets["agent_id"].str.upper()
    before_join = len(tickets)
    tickets = tickets.merge(agents, on="agent_id", how="inner", suffixes=("", "_agent"))
    summary["tickets_no_agent"] = before_join - len(tickets)

    # ---------------------------------------------------
    # R6 – map channel, drop invalid
    # ---------------------------------------------------
    tickets["channel"] = tickets["channel"].apply(map_channel)
    before_chan = len(tickets)
    tickets = tickets[tickets["channel"].notna()]
    summary["invalid_channels"] = before_chan - len(tickets)

    # ---------------------------------------------------
    # R7 – parse resolution_minutes, drop invalid
    # ---------------------------------------------------
    tickets["resolution_minutes"] = tickets["resolution_minutes"].apply(parse_resolution)
    before_res = len(tickets)
    tickets = tickets[tickets["resolution_minutes"].notna()]
    summary["invalid_resolution"] = before_res - len(tickets)
    tickets["resolution_minutes"] = tickets["resolution_minutes"].astype(int)

    # ---------------------------------------------------
    # R8 – parse satisfaction_score (keep row, set NaN if invalid)
    # ---------------------------------------------------
    tickets["satisfaction_score"] = tickets["satisfaction_score"].apply(parse_satisfaction)
    # keep as float/int with NaN allowed

    # ---------------------------------------------------
    # R9 – map reopened, drop invalid/missing
    # ---------------------------------------------------
    tickets["reopened"] = tickets["reopened"].apply(map_reopened)
    before_reopen = len(tickets)
    tickets = tickets[tickets["reopened"].notna()]
    summary["invalid_reopened"] = before_reopen - len(tickets)
    tickets["reopened"] = tickets["reopened"].astype(int)

    # ---------------------------------------------------
    # R10 – compute labor_cost
    # ---------------------------------------------------
    tickets["hourly_cost"] = tickets["hourly_cost"].astype(float)
    tickets["labor_cost"] = (tickets["resolution_minutes"] / 60.0) * tickets["hourly_cost"]
    tickets["labor_cost"] = tickets["labor_cost"].round(2)

    # ---------------------------------------------------
    # R11 – final column order, sort, write CSV
    # ---------------------------------------------------
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

    # Ensure dtypes / categories (categories are not required for CSV output)
    cleaned["ticket_id"] = cleaned["ticket_id"].astype(str)
    cleaned["agent_id"] = cleaned["agent_id"].astype(str)
    cleaned["team"] = cleaned["team"].astype(str)
    cleaned["region"] = cleaned["region"].astype(str)
    cleaned["channel"] = cleaned["channel"].astype(str)
    cleaned["resolution_minutes"] = cleaned["resolution_minutes"].astype(int)
    # satisfaction_score may be NaN – keep as float/int
    cleaned["reopened"] = cleaned["reopened"].astype(int)
    cleaned["hourly_cost"] = cleaned["hourly_cost"].astype(float)
    cleaned["labor_cost"] = cleaned["labor_cost"].astype(float)

    # Write cleaned CSV
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    cleaned.to_csv(cleaned_path, index=False)

    # Write cleaning summary JSON
    summary["cleaned_rows"] = len(cleaned)
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # For external reference (not required but helpful)
    print(json.dumps({"status": "cleaning completed", "output": "cleaned.csv"}))

if __name__ == "__main__":
    main()
