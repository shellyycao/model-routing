import os
import json
import re
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Helper functions for cleaning
# ---------------------------------------------------------------------------
MISSING_VALUES = ["", "NA", "N/A", "null", "None", "-"]

def strip_and_normalise(df):
    """Strip whitespace from all string columns and replace defined missing values with NaN."""
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip()
    df = df.replace(MISSING_VALUES, np.nan)
    return df

# Agent roster helpers

def map_team(val):
    if pd.isna(val):
        return np.nan
    v = str(val).lower()
    if "alpha" in v:
        return "Alpha"
    if "beta" in v:
        return "Beta"
    if "gamma" in v:
        return "Gamma"
    return np.nan

def map_region(val):
    if pd.isna(val):
        return np.nan
    v = str(val).lower()
    if v in ["east", "e"]:
        return "East"
    if v in ["west", "w"]:
        return "West"
    return np.nan

def parse_hourly_cost(val):
    if pd.isna(val):
        return np.nan
    # Remove currency symbols, the word USD and commas
    cleaned = re.sub(r"[\$,]", "", str(val), flags=re.IGNORECASE)
    cleaned = re.sub(r"(?i)usd", "", cleaned)
    cleaned = cleaned.strip()
    try:
        cost = float(cleaned)
        return cost if cost > 0 else np.nan
    except Exception:
        return np.nan

# Ticket helpers

def map_channel(val):
    if pd.isna(val):
        return np.nan
    v = str(val).lower()
    if v in ["email", "e-mail"]:
        return "email"
    if v in ["chat", "live chat"]:
        return "chat"
    if v in ["phone", "call"]:
        return "phone"
    return np.nan

def parse_resolution(val):
    if pd.isna(val):
        return np.nan
    v = str(val).lower()
    # Remove textual suffixes
    v = v.replace("minutes", "").replace("minute", "").replace("min", "").strip()
    # Keep only digits
    v = re.sub(r"[^0-9]", "", v)
    if v == "":
        return np.nan
    try:
        minutes = int(v)
        if 1 <= minutes <= 480:
            return minutes
        else:
            return np.nan
    except Exception:
        return np.nan

def parse_satisfaction(val):
    if pd.isna(val):
        return np.nan
    try:
        s = int(float(val))
        if 1 <= s <= 5:
            return s
        else:
            return np.nan
    except Exception:
        return np.nan

def map_reopened(val):
    if pd.isna(val):
        return np.nan
    v = str(val).strip().lower()
    if v in ["yes", "y", "true", "1"]:
        return 1
    if v in ["no", "n", "false", "0"]:
        return 0
    return np.nan

# ---------------------------------------------------------------------------
# Main cleaning routine
# ---------------------------------------------------------------------------
def main():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]

    tickets_path = os.path.join(input_dir, "tickets.csv")
    agents_path = os.path.join(input_dir, "agents.csv")

    # ---------------------------------------------------
    # 1. Load raw data (as text) and normalise whitespace
    # ---------------------------------------------------
    tickets_raw = pd.read_csv(tickets_path, dtype=str, keep_default_na=False)
    agents_raw = pd.read_csv(agents_path, dtype=str, keep_default_na=False)

    raw_ticket_rows = len(tickets_raw)
    raw_agent_rows = len(agents_raw)

    tickets = strip_and_normalise(tickets_raw)
    agents = strip_and_normalise(agents_raw)

    # ---------------------------------------------------
    # 2. Remove duplicate ticket_id rows (keep first)
    # ---------------------------------------------------
    tickets_before_dup = len(tickets)
    tickets = tickets.drop_duplicates(subset="ticket_id", keep="first")
    dup_tickets_removed = tickets_before_dup - len(tickets)

    # ---------------------------------------------------
    # 3. Normalise agent_id in agents, drop duplicate agent_id rows
    # ---------------------------------------------------
    agents["agent_id"] = agents["agent_id"].str.upper()
    agents_before_dup = len(agents)
    agents = agents.drop_duplicates(subset="agent_id", keep="first")
    dup_agents_removed = agents_before_dup - len(agents)

    # ---------------------------------------------------
    # 4. Clean agent roster fields
    # ---------------------------------------------------
    agents["team"] = agents["team"].apply(map_team)
    agents["region"] = agents["region"].apply(map_region)
    agents["hourly_cost"] = agents["hourly_cost"].apply(parse_hourly_cost)

    # Identify invalid roster rows (any NaN in required fields or cost <= 0 already handled)
    valid_agent_mask = agents["team"].notna() & agents["region"].notna() & agents["hourly_cost"].notna()
    invalid_agents = len(agents) - valid_agent_mask.sum()
    agents = agents[valid_agent_mask].copy()

    # ---------------------------------------------------
    # 5. Normalise ticket agent_id and join with roster
    # ---------------------------------------------------
    tickets["agent_id"] = tickets["agent_id"].str.upper()
    tickets_before_join = len(tickets)
    tickets = tickets.merge(agents, on="agent_id", how="inner", suffixes=("", "_agent"))
    tickets_without_agent = tickets_before_join - len(tickets)

    # ---------------------------------------------------
    # 6. Map channel values, drop invalid
    # ---------------------------------------------------
    tickets["channel"] = tickets["channel"].apply(map_channel)
    valid_channel_mask = tickets["channel"].notna()
    invalid_channel = (~valid_channel_mask).sum()
    tickets = tickets[valid_channel_mask]

    # ---------------------------------------------------
    # 7. Clean resolution_minutes, drop invalid
    # ---------------------------------------------------
    tickets["resolution_minutes"] = tickets["resolution_minutes"].apply(parse_resolution)
    valid_resolution_mask = tickets["resolution_minutes"].notna()
    invalid_resolution = (~valid_resolution_mask).sum()
    tickets = tickets[valid_resolution_mask]

    # ---------------------------------------------------
    # 8. Clean satisfaction_score (keep row, set NaN if invalid)
    # ---------------------------------------------------
    tickets["satisfaction_score"] = tickets["satisfaction_score"].apply(parse_satisfaction)

    # ---------------------------------------------------
    # 9. Map reopened, drop invalid or missing
    # ---------------------------------------------------
    tickets["reopened"] = tickets["reopened"].apply(map_reopened)
    valid_reopened_mask = tickets["reopened"].notna()
    invalid_reopened = (~valid_reopened_mask).sum()
    tickets = tickets[valid_reopened_mask]

    # ---------------------------------------------------
    # 10. Compute labor_cost
    # ---------------------------------------------------
    tickets["hourly_cost"] = tickets["hourly_cost"].astype(float)
    tickets["resolution_minutes"] = tickets["resolution_minutes"].astype(int)
    tickets["labor_cost"] = (tickets["resolution_minutes"] / 60.0) * tickets["hourly_cost"]
    tickets["labor_cost"] = tickets["labor_cost"].round(2)

    # ---------------------------------------------------
    # 11. Select and order final columns, sort by ticket_id
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
        "labor_cost",
    ]
    cleaned = tickets[final_cols].copy()
    cleaned = cleaned.sort_values(by="ticket_id")

    # ---------------------------------------------------
    # 12. Write outputs
    # ---------------------------------------------------
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    cleaned.to_csv(cleaned_path, index=False)

    summary = {
        "raw_rows": raw_ticket_rows,
        "cleaned_rows": len(cleaned),
        "duplicate_tickets_removed": int(dup_tickets_removed),
        "duplicate_agents_removed": int(dup_agents_removed),
        "invalid_agent_roster_rows": int(invalid_agents),
        "tickets_without_matching_agent": int(tickets_without_agent),
        "invalid_channel_rows": int(invalid_channel),
        "invalid_resolution_rows": int(invalid_resolution),
        "invalid_reopened_rows": int(invalid_reopened),
    }
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # expose output filename for the orchestrator
    global output_filename
    output_filename = "cleaned.csv"

if __name__ == "__main__":
    main()
