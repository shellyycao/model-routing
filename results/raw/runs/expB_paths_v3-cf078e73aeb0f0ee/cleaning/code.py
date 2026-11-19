import os
import json
import re
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def clean_missing(df):
    """Strip whitespace and replace common missing tokens with NaN."""
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    missing_vals = ['', 'NA', 'N/A', 'null', 'None', '-']
    df.replace(missing_vals, np.nan, inplace=True)
    return df

def map_team(val):
    if pd.isna(val):
        return np.nan
    val = val.strip().lower()
    mapping = {
        'alpha': 'Alpha',
        'team alpha': 'Alpha',
        'beta': 'Beta',
        'team beta': 'Beta',
        'gamma': 'Gamma',
        'team gamma': 'Gamma'
    }
    return mapping.get(val, np.nan)

def map_region(val):
    if pd.isna(val):
        return np.nan
    val = val.strip().lower()
    mapping = {
        'east': 'East',
        'e': 'East',
        'west': 'West',
        'w': 'West'
    }
    return mapping.get(val, np.nan)

def parse_hourly_cost(val):
    if pd.isna(val):
        return np.nan
    # Remove $ , commas, the string "USD" and surrounding spaces
    cleaned = re.sub(r'[\$,]', '', str(val))
    cleaned = cleaned.replace('USD', '')
    cleaned = cleaned.strip()
    try:
        cost = float(cleaned)
        return cost if cost > 0 else np.nan
    except ValueError:
        return np.nan

def map_channel(val):
    if pd.isna(val):
        return np.nan
    val = val.strip().lower()
    mapping = {
        'email': 'email',
        'e-mail': 'email',
        'chat': 'chat',
        'live chat': 'chat',
        'phone': 'phone',
        'call': 'phone'
    }
    return mapping.get(val, np.nan)

def clean_resolution(val):
    if pd.isna(val):
        return np.nan
    # Remove trailing "min" or "minutes" (case‑insensitive)
    val = re.sub(r'(?i)\s*(min|minutes)\s*$', '', str(val)).strip()
    try:
        minutes = int(val)
        if 1 <= minutes <= 480:
            return minutes
        else:
            return np.nan
    except ValueError:
        return np.nan

def clean_satisfaction(val):
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
    val = str(val).strip().lower()
    yes = {'yes', 'y', 'true', '1'}
    no = {'no', 'n', 'false', '0'}
    if val in yes:
        return 1
    if val in no:
        return 0
    return np.nan

# ---------------------------------------------------------------------------
# Main cleaning routine
# ---------------------------------------------------------------------------

def main():
    input_dir = os.environ.get('INPUT_DIR', '.')
    output_dir = os.environ.get('OUTPUT_DIR', '.')

    tickets_path = os.path.join(input_dir, 'tickets.csv')
    agents_path = os.path.join(input_dir, 'agents.csv')

    # -----------------------------------------------------------------------
    # 1. Load raw files as text, strip whitespace, normalise missing values (R1)
    # -----------------------------------------------------------------------
    tickets_raw = pd.read_csv(tickets_path, dtype=str, keep_default_na=False)
    agents_raw = pd.read_csv(agents_path, dtype=str, keep_default_na=False)

    raw_ticket_rows = len(tickets_raw)
    raw_agent_rows = len(agents_raw)

    tickets = clean_missing(tickets_raw)
    agents = clean_missing(agents_raw)

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
    # 4. Clean agent roster (R4)
    # -----------------------------------------------------------------------
    agents['team'] = agents['team'].apply(map_team)
    agents['region'] = agents['region'].apply(map_region)
    agents['hourly_cost'] = agents['hourly_cost'].apply(parse_hourly_cost)

    # Exclude rows with any invalid field or non‑positive cost
    valid_agents_mask = (
        agents['team'].notna() &
        agents['region'].notna() &
        agents['hourly_cost'].notna()
    )
    excluded_agents = len(agents) - valid_agents_mask.sum()
    agents = agents[valid_agents_mask].copy()

    # -----------------------------------------------------------------------
    # 5. Normalise ticket agent_id and join to roster (R5)
    # -----------------------------------------------------------------------
    tickets['agent_id'] = tickets['agent_id'].str.upper()
    tickets = tickets.merge(
        agents[['agent_id', 'team', 'region', 'hourly_cost']],
        on='agent_id',
        how='inner'
    )
    tickets_no_agent = raw_ticket_rows - dup_tickets - len(tickets)

    # -----------------------------------------------------------------------
    # 6. Normalise channel, drop invalid (R6)
    # -----------------------------------------------------------------------
    tickets['channel'] = tickets['channel'].apply(map_channel)
    invalid_channel_mask = tickets['channel'].isna()
    dropped_invalid_channel = invalid_channel_mask.sum()
    tickets = tickets[~invalid_channel_mask]

    # -----------------------------------------------------------------------
    # 7. Clean resolution_minutes, drop invalid (R7)
    # -----------------------------------------------------------------------
    tickets['resolution_minutes'] = tickets['resolution_minutes'].apply(clean_resolution)
    invalid_res_mask = tickets['resolution_minutes'].isna()
    dropped_invalid_resolution = invalid_res_mask.sum()
    tickets = tickets[~invalid_res_mask]

    # -----------------------------------------------------------------------
    # 8. Clean satisfaction_score (R8) – keep row, set NaN if invalid
    # -----------------------------------------------------------------------
    tickets['satisfaction_score'] = tickets['satisfaction_score'].apply(clean_satisfaction)

    # -----------------------------------------------------------------------
    # 9. Map reopened, drop invalid or missing (R9)
    # -----------------------------------------------------------------------
    tickets['reopened'] = tickets['reopened'].apply(map_reopened)
    invalid_reopened_mask = tickets['reopened'].isna()
    dropped_invalid_reopened = invalid_reopened_mask.sum()
    tickets = tickets[~invalid_reopened_mask]

    # -----------------------------------------------------------------------
    # 10. Compute labor_cost (R10)
    # -----------------------------------------------------------------------
    tickets['labor_cost'] = (tickets['resolution_minutes'] / 60.0) * tickets['hourly_cost']
    tickets['labor_cost'] = tickets['labor_cost'].round(2)

    # -----------------------------------------------------------------------
    # 11. Final column selection, ordering and sorting (R11)
    # -----------------------------------------------------------------------
    final_cols = [
        'ticket_id', 'agent_id', 'team', 'region', 'channel',
        'resolution_minutes', 'satisfaction_score', 'reopened',
        'hourly_cost', 'labor_cost'
    ]
    cleaned = tickets[final_cols].copy()
    cleaned.sort_values('ticket_id', inplace=True)

    # Ensure correct dtypes (pandas nullable integer for satisfaction_score)
    cleaned['resolution_minutes'] = cleaned['resolution_minutes'].astype(int)
    cleaned['reopened'] = cleaned['reopened'].astype(int)
    cleaned['hourly_cost'] = cleaned['hourly_cost'].astype(float)
    cleaned['labor_cost'] = cleaned['labor_cost'].astype(float)
    cleaned['satisfaction_score'] = cleaned['satisfaction_score'].astype('Int64')

    # -----------------------------------------------------------------------
    # Write outputs
    # -----------------------------------------------------------------------
    cleaned_path = os.path.join(output_dir, 'cleaned.csv')
    cleaned.to_csv(cleaned_path, index=False)

    summary = {
        'raw_rows': raw_ticket_rows,
        'cleaned_rows': len(cleaned),
        'duplicate_tickets_removed': int(dup_tickets),
        'duplicate_agents_removed': int(dup_agents),
        'agents_excluded_invalid': int(excluded_agents),
        'tickets_without_agent': int(tickets_no_agent),
        'tickets_invalid_channel': int(dropped_invalid_channel),
        'tickets_invalid_resolution': int(dropped_invalid_resolution),
        'tickets_invalid_reopened': int(dropped_invalid_reopened)
    }
    summary_path = os.path.join(output_dir, 'cleaning_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    main()
