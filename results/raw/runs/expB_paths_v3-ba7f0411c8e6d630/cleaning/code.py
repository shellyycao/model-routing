import os
import json
import re
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def normalize_missing(df):
    """Strip whitespace and replace common missing tokens with NaN."""
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    missing_tokens = ['', 'NA', 'N/A', 'null', 'None', '-']
    df.replace(missing_tokens, np.nan, inplace=True)
    return df


def map_team(value):
    if pd.isna(value):
        return None
    v = str(value).lower().replace('team', '').strip()
    if 'alpha' in v:
        return 'Alpha'
    if 'beta' in v:
        return 'Beta'
    if 'gamma' in v:
        return 'Gamma'
    return None


def map_region(value):
    if pd.isna(value):
        return None
    v = str(value).strip().lower()
    if v in ('east', 'e'):
        return 'East'
    if v in ('west', 'w'):
        return 'West'
    return None


def parse_hourly_cost(value):
    if pd.isna(value):
        return None
    # Remove $ , USD and commas
    cleaned = re.sub(r'[$,]|USD', '', str(value), flags=re.IGNORECASE).strip()
    try:
        cost = float(cleaned)
        return cost if cost > 0 else None
    except ValueError:
        return None


def map_channel(value):
    if pd.isna(value):
        return None
    v = str(value).lower().replace('-', ' ').strip()
    if v in ('email', 'e mail', 'e-mail'):
        return 'email'
    if v in ('chat', 'live chat'):
        return 'chat'
    if v in ('phone', 'call'):
        return 'phone'
    return None


def parse_resolution(value):
    if pd.isna(value):
        return None
    # Remove the word "min" or "minutes"
    cleaned = re.sub(r'(?i)\s*min(utes)?\s*', '', str(value)).strip()
    match = re.search(r'\d+', cleaned)
    if not match:
        return None
    minutes = int(match.group())
    return minutes if 1 <= minutes <= 480 else None


def parse_satisfaction(value):
    if pd.isna(value):
        return np.nan
    try:
        iv = int(float(value))
        return iv if 1 <= iv <= 5 else np.nan
    except Exception:
        return np.nan


def map_reopened(value):
    if pd.isna(value):
        return None
    v = str(value).strip().lower()
    if v in ('yes', 'y', 'true', '1'):
        return 1
    if v in ('no', 'n', 'false', '0'):
        return 0
    return None

# ---------------------------------------------------------------------------
# Main cleaning routine
# ---------------------------------------------------------------------------

def main():
    input_dir = os.environ.get('INPUT_DIR', '.')
    output_dir = os.environ.get('OUTPUT_DIR', '.')

    tickets_path = os.path.join(input_dir, 'tickets.csv')
    agents_path = os.path.join(input_dir, 'agents.csv')

    # ---------------------------------------------------
    # 1. Load raw data as text and normalise missing values (R1)
    # ---------------------------------------------------
    tickets_raw = pd.read_csv(tickets_path, dtype=str, keep_default_na=False)
    agents_raw = pd.read_csv(agents_path, dtype=str, keep_default_na=False)

    raw_rows = len(tickets_raw)
    raw_agent_rows = len(agents_raw)

    tickets = normalize_missing(tickets_raw)
    agents = normalize_missing(agents_raw)

    # ---------------------------------------------------
    # 2. Remove duplicate ticket_id rows, keep first (R2)
    # ---------------------------------------------------
    dup_tickets = tickets.duplicated(subset='ticket_id').sum()
    tickets = tickets.drop_duplicates(subset='ticket_id', keep='first')

    # ---------------------------------------------------
    # 3. Normalise agent_id to upper case and deduplicate agents (R3)
    # ---------------------------------------------------
    agents['agent_id'] = agents['agent_id'].str.upper()
    dup_agents = agents.duplicated(subset='agent_id').sum()
    agents = agents.drop_duplicates(subset='agent_id', keep='first')

    # ---------------------------------------------------
    # 4. Clean agent roster (R4)
    # ---------------------------------------------------
    agents['team'] = agents['team'].apply(map_team)
    agents['region'] = agents['region'].apply(map_region)
    agents['hourly_cost'] = agents['hourly_cost'].apply(parse_hourly_cost)

    # Keep only rows with valid team, region and positive hourly_cost
    valid_agents_mask = (
        agents['team'].isin(['Alpha', 'Beta', 'Gamma']) &
        agents['region'].isin(['East', 'West']) &
        agents['hourly_cost'].notna()
    )
    excluded_invalid_agents = (~valid_agents_mask).sum()
    agents = agents[valid_agents_mask].copy()

    # ---------------------------------------------------
    # 5. Normalise ticket agent_id and join to roster (R5)
    # ---------------------------------------------------
    tickets['agent_id'] = tickets['agent_id'].str.upper()
    tickets = tickets.merge(agents, on='agent_id', how='inner', suffixes=('', '_agent'))
    tickets_dropped_no_agent = len(tickets_raw) - len(tickets) - dup_tickets

    # ---------------------------------------------------
    # 6. Map channel values, drop invalid (R6)
    # ---------------------------------------------------
    tickets['channel'] = tickets['channel'].apply(map_channel)
    invalid_channel_mask = ~tickets['channel'].isin(['email', 'chat', 'phone'])
    dropped_invalid_channel = invalid_channel_mask.sum()
    tickets = tickets[~invalid_channel_mask]

    # ---------------------------------------------------
    # 7. Clean resolution_minutes (R7)
    # ---------------------------------------------------
    tickets['resolution_minutes'] = tickets['resolution_minutes'].apply(parse_resolution)
    invalid_resolution_mask = tickets['resolution_minutes'].isna()
    dropped_invalid_resolution = invalid_resolution_mask.sum()
    tickets = tickets[~invalid_resolution_mask]

    # ---------------------------------------------------
    # 8. Clean satisfaction_score (R8) – keep row, set NaN if invalid
    # ---------------------------------------------------
    tickets['satisfaction_score'] = tickets['satisfaction_score'].apply(parse_satisfaction)

    # ---------------------------------------------------
    # 9. Map reopened flag, drop invalid/missing (R9)
    # ---------------------------------------------------
    tickets['reopened'] = tickets['reopened'].apply(map_reopened)
    invalid_reopened_mask = tickets['reopened'].isna()
    dropped_invalid_reopened = invalid_reopened_mask.sum()
    tickets = tickets[~invalid_reopened_mask]

    # ---------------------------------------------------
    # 10. Compute labor_cost (R10)
    # ---------------------------------------------------
    tickets['labor_cost'] = (tickets['resolution_minutes'] / 60.0) * tickets['hourly_cost']
    tickets['labor_cost'] = tickets['labor_cost'].round(2)

    # ---------------------------------------------------
    # 11. Final column selection, ordering and sorting (R11)
    # ---------------------------------------------------
    final_cols = [
        'ticket_id', 'agent_id', 'team', 'region', 'channel',
        'resolution_minutes', 'satisfaction_score', 'reopened',
        'hourly_cost', 'labor_cost'
    ]
    cleaned = tickets[final_cols].copy()
    cleaned.sort_values('ticket_id', inplace=True)

    cleaned_rows = len(cleaned)

    # ---------------------------------------------------
    # Write outputs
    # ---------------------------------------------------
    cleaned_path = os.path.join(output_dir, 'cleaned.csv')
    cleaned.to_csv(cleaned_path, index=False)

    summary = {
        'raw_rows': raw_rows,
        'raw_agent_rows': raw_agent_rows,
        'cleaned_rows': cleaned_rows,
        'duplicates_removed_tickets': int(dup_tickets),
        'duplicates_removed_agents': int(dup_agents),
        'agents_excluded_invalid': int(excluded_invalid_agents),
        'tickets_dropped_no_agent': int(tickets_dropped_no_agent),
        'tickets_dropped_invalid_channel': int(dropped_invalid_channel),
        'tickets_dropped_invalid_resolution': int(dropped_invalid_resolution),
        'tickets_dropped_invalid_reopened': int(dropped_invalid_reopened)
    }
    summary_path = os.path.join(output_dir, 'cleaning_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    # expose output filename for the orchestrator
    global output_filename
    output_filename = 'cleaned.csv'

if __name__ == '__main__':
    main()
