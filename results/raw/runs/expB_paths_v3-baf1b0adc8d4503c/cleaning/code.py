import os
import json
import re
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Helper functions for cleaning
# ---------------------------------------------------------------------------

def strip_and_mark_missing(df):
    """Strip whitespace from all string cells and replace common missing tokens with NaN."""
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    missing_tokens = {'', 'NA', 'N/A', 'null', 'None', '-'}
    df = df.replace(list(missing_tokens), np.nan)
    return df


def map_team(val):
    if pd.isna(val):
        return np.nan
    low = val.lower()
    if 'alpha' in low:
        return 'Alpha'
    if 'beta' in low:
        return 'Beta'
    if 'gamma' in low:
        return 'Gamma'
    return np.nan


def map_region(val):
    if pd.isna(val):
        return np.nan
    low = val.lower()
    if low in ('east', 'e'):
        return 'East'
    if low in ('west', 'w'):
        return 'West'
    return np.nan


def parse_hourly_cost(val):
    if pd.isna(val):
        return np.nan
    s = str(val).replace('$', '').replace('USD', '').replace(',', '').strip()
    try:
        return float(s)
    except ValueError:
        return np.nan


def map_channel(val):
    if pd.isna(val):
        return np.nan
    low = val.lower()
    if low in ('email', 'e-mail'):
        return 'email'
    if low in ('chat', 'live chat'):
        return 'chat'
    if low in ('phone', 'call'):
        return 'phone'
    return np.nan


def parse_resolution(val):
    if pd.isna(val):
        return np.nan
    # Remove the words "min" or "minutes"
    cleaned = re.sub(r"(?i)\s*minutes?", "", str(val)).strip()
    # Extract the first integer
    m = re.search(r"(\d+)", cleaned)
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
        iv = int(float(val))  # handles strings like "4.0"
        if 1 <= iv <= 5:
            return iv
    except Exception:
        pass
    return np.nan


def map_reopened(val):
    if pd.isna(val):
        return np.nan
    low = str(val).strip().lower()
    if low in ('yes', 'y', 'true', '1'):
        return 1
    if low in ('no', 'n', 'false', '0'):
        return 0
    return np.nan

# ---------------------------------------------------------------------------
# Main cleaning routine
# ---------------------------------------------------------------------------

def main():
    input_dir = os.getenv('INPUT_DIR')
    output_dir = os.getenv('OUTPUT_DIR')
    if not input_dir or not output_dir:
        raise RuntimeError('Both INPUT_DIR and OUTPUT_DIR environment variables must be set')

    # -----------------------------------------------------------------------
    # 1. Load raw files as text, strip whitespace, mark missing values (R1)
    # -----------------------------------------------------------------------
    tickets_path = os.path.join(input_dir, 'tickets.csv')
    agents_path = os.path.join(input_dir, 'agents.csv')

    tickets_raw = pd.read_csv(tickets_path, dtype=str, keep_default_na=False)
    agents_raw = pd.read_csv(agents_path, dtype=str, keep_default_na=False)

    raw_ticket_rows = len(tickets_raw)
    raw_agent_rows = len(agents_raw)

    tickets = strip_and_mark_missing(tickets_raw)
    agents = strip_and_mark_missing(agents_raw)

    # -----------------------------------------------------------------------
    # 2. Remove duplicate ticket_id rows, keep first (R2)
    # -----------------------------------------------------------------------
    dup_tickets = tickets.duplicated(subset='ticket_id').sum()
    tickets = tickets.drop_duplicates(subset='ticket_id', keep='first')

    # -----------------------------------------------------------------------
    # 3. Normalise agent_id to upper case and deduplicate agents (R3)
    # -----------------------------------------------------------------------
    agents['agent_id'] = agents['agent_id'].str.upper()
    dup_agents = agents.duplicated(subset='agent_id').sum()
    agents = agents.drop_duplicates(subset='agent_id', keep='first')

    # -----------------------------------------------------------------------
    # 4. Clean agent roster fields (R4)
    # -----------------------------------------------------------------------
    agents['team'] = agents['team'].apply(map_team)
    agents['region'] = agents['region'].apply(map_region)
    agents['hourly_cost'] = agents['hourly_cost'].apply(parse_hourly_cost)

    # Exclude rows with any invalid field or non‑positive cost
    valid_agent_mask = (
        agents['team'].notna() &
        agents['region'].notna() &
        agents['hourly_cost'].notna() &
        (agents['hourly_cost'] > 0)
    )
    excluded_invalid_agents = (~valid_agent_mask).sum()
    agents = agents[valid_agent_mask].copy()

    # -----------------------------------------------------------------------
    # 5. Normalise ticket agent_id and inner join with cleaned roster (R5)
    # -----------------------------------------------------------------------
    tickets['agent_id'] = tickets['agent_id'].str.upper()
    tickets = tickets.merge(agents, on='agent_id', how='inner', suffixes=('', '_agent'))
    tickets_dropped_no_agent = raw_ticket_rows - len(tickets) - dup_tickets

    # -----------------------------------------------------------------------
    # 6. Map channel, drop invalid (R6)
    # -----------------------------------------------------------------------
    tickets['channel'] = tickets['channel'].apply(map_channel)
    invalid_channel_mask = tickets['channel'].isna()
    tickets_dropped_invalid_channel = invalid_channel_mask.sum()
    tickets = tickets[~invalid_channel_mask]

    # -----------------------------------------------------------------------
    # 7. Clean resolution_minutes, drop invalid (R7)
    # -----------------------------------------------------------------------
    tickets['resolution_minutes'] = tickets['resolution_minutes'].apply(parse_resolution)
    invalid_res_mask = tickets['resolution_minutes'].isna()
    tickets_dropped_invalid_resolution = invalid_res_mask.sum()
    tickets = tickets[~invalid_res_mask]

    # -----------------------------------------------------------------------
    # 8. Clean satisfaction_score (R8) – keep row, set NaN if invalid
    # -----------------------------------------------------------------------
    tickets['satisfaction_score'] = tickets['satisfaction_score'].apply(parse_satisfaction)

    # -----------------------------------------------------------------------
    # 9. Map reopened, drop invalid/missing (R9)
    # -----------------------------------------------------------------------
    tickets['reopened'] = tickets['reopened'].apply(map_reopened)
    invalid_reopened_mask = tickets['reopened'].isna()
    tickets_dropped_invalid_reopened = invalid_reopened_mask.sum()
    tickets = tickets[~invalid_reopened_mask]

    # -----------------------------------------------------------------------
    # 10. Compute labor_cost (R10)
    # -----------------------------------------------------------------------
    tickets['labor_cost'] = (tickets['resolution_minutes'] / 60.0) * tickets['hourly_cost']
    tickets['labor_cost'] = tickets['labor_cost'].round(2)

    # -----------------------------------------------------------------------
    # 11. Select and order final columns, sort by ticket_id, write CSV (R11)
    # -----------------------------------------------------------------------
    final_cols = [
        'ticket_id', 'agent_id', 'team', 'region', 'channel',
        'resolution_minutes', 'satisfaction_score', 'reopened',
        'hourly_cost', 'labor_cost'
    ]
    cleaned = tickets[final_cols].copy()
    cleaned = cleaned.sort_values('ticket_id')

    cleaned_path = os.path.join(output_dir, 'cleaned.csv')
    cleaned.to_csv(cleaned_path, index=False)

    # -----------------------------------------------------------------------
    # 12. Write cleaning summary JSON
    # -----------------------------------------------------------------------
    summary = {
        'raw_rows': raw_ticket_rows,
        'cleaned_rows': len(cleaned),
        'duplicates_removed_tickets': int(dup_tickets),
        'duplicates_removed_agents': int(dup_agents),
        'agents_excluded_invalid': int(excluded_invalid_agents),
        'tickets_dropped_no_agent': int(tickets_dropped_no_agent),
        'tickets_dropped_invalid_channel': int(tickets_dropped_invalid_channel),
        'tickets_dropped_invalid_resolution': int(tickets_dropped_invalid_resolution),
        'tickets_dropped_invalid_reopened': int(tickets_dropped_invalid_reopened)
    }
    summary_path = os.path.join(output_dir, 'cleaning_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    main()
