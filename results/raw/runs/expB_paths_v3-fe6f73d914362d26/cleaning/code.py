import os
import json
import re
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def strip_and_mark_missing(df):
    """Strip whitespace from all string cells and replace common missing tokens.
    """
    missing_tokens = ['', 'NA', 'N/A', 'null', 'None', '-']
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
    df.replace(missing_tokens, np.nan, inplace=True)
    return df

def normalise_agent_id(series):
    return series.str.upper()

def map_team(val):
    if pd.isna(val):
        return np.nan
    v = str(val).lower()
    if 'alpha' in v:
        return 'Alpha'
    if 'beta' in v:
        return 'Beta'
    if 'gamma' in v:
        return 'Gamma'
    return np.nan

def map_region(val):
    if pd.isna(val):
        return np.nan
    v = str(val).lower()
    if v in ('east', 'e'):
        return 'East'
    if v in ('west', 'w'):
        return 'West'
    return np.nan

def parse_hourly_cost(val):
    if pd.isna(val):
        return np.nan
    # Remove $ , USD and commas
    cleaned = re.sub(r'[^0-9.]', '', str(val))
    try:
        cost = float(cleaned)
        return cost if cost > 0 else np.nan
    except ValueError:
        return np.nan

def map_channel(val):
    if pd.isna(val):
        return np.nan
    v = str(val).lower().replace(' ', '')
    if v in ('email', 'e-mail'):
        return 'email'
    if v in ('chat', 'livechat'):
        return 'chat'
    if v in ('phone', 'call'):
        return 'phone'
    return np.nan

def parse_resolution(val):
    if pd.isna(val):
        return np.nan
    # Remove the word "min" or "minutes"
    v = re.sub(r'(?i)\s*min(utes)?\s*', '', str(val))
    m = re.search(r'\d+', v)
    if not m:
        return np.nan
    minutes = int(m.group())
    if 1 <= minutes <= 480:
        return minutes
    return np.nan

def parse_satisfaction(val):
    if pd.isna(val):
        return np.nan
    try:
        s = int(float(val))
        if 1 <= s <= 5:
            return s
    except Exception:
        pass
    return np.nan

def map_reopened(val):
    if pd.isna(val):
        return np.nan
    v = str(val).strip().lower()
    if v in ('yes', 'y', 'true', '1'):
        return 1
    if v in ('no', 'n', 'false', '0'):
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
    # R1 – read raw files as text, strip whitespace, mark missing values
    # -----------------------------------------------------------------------
    tickets_raw = pd.read_csv(tickets_path, dtype=str, keep_default_na=False)
    agents_raw = pd.read_csv(agents_path, dtype=str, keep_default_na=False)

    tickets = strip_and_mark_missing(tickets_raw.copy())
    agents = strip_and_mark_missing(agents_raw.copy())

    summary = {
        'raw_rows': {
            'tickets': len(tickets_raw),
            'agents': len(agents_raw)
        }
    }

    # -----------------------------------------------------------------------
    # R2 – deduplicate tickets on ticket_id (keep first)
    # -----------------------------------------------------------------------
    before = len(tickets)
    tickets = tickets.drop_duplicates(subset='ticket_id', keep='first')
    summary['duplicates_removed_tickets'] = before - len(tickets)

    # -----------------------------------------------------------------------
    # R3 – normalise agent_id in agents and deduplicate
    # -----------------------------------------------------------------------
    agents['agent_id'] = normalise_agent_id(agents['agent_id'])
    before = len(agents)
    agents = agents.drop_duplicates(subset='agent_id', keep='first')
    summary['duplicates_removed_agents'] = before - len(agents)

    # -----------------------------------------------------------------------
    # R4 – clean roster fields
    # -----------------------------------------------------------------------
    agents['team'] = agents['team'].apply(map_team)
    agents['region'] = agents['region'].apply(map_region)
    agents['hourly_cost'] = agents['hourly_cost'].apply(parse_hourly_cost)

    # Drop rows with any invalid field after mapping
    before = len(agents)
    agents = agents.dropna(subset=['team', 'region', 'hourly_cost'])
    summary['invalid_roster_rows_removed'] = before - len(agents)

    # -----------------------------------------------------------------------
    # R5 – normalise ticket agent_id and inner join with roster
    # -----------------------------------------------------------------------
    tickets['agent_id'] = normalise_agent_id(tickets['agent_id'])
    before = len(tickets)
    tickets = tickets.merge(agents, on='agent_id', how='inner', suffixes=('', '_agent'))
    summary['tickets_without_agent_removed'] = before - len(tickets)

    # -----------------------------------------------------------------------
    # R6 – normalise channel
    # -----------------------------------------------------------------------
    tickets['channel'] = tickets['channel'].apply(map_channel)
    before = len(tickets)
    tickets = tickets.dropna(subset=['channel'])
    summary['invalid_channel_rows_removed'] = before - len(tickets)

    # -----------------------------------------------------------------------
    # R7 – clean resolution_minutes
    # -----------------------------------------------------------------------
    tickets['resolution_minutes'] = tickets['resolution_minutes'].apply(parse_resolution)
    before = len(tickets)
    tickets = tickets.dropna(subset=['resolution_minutes'])
    summary['invalid_resolution_rows_removed'] = before - len(tickets)
    tickets['resolution_minutes'] = tickets['resolution_minutes'].astype(int)

    # -----------------------------------------------------------------------
    # R8 – satisfaction_score (keep row, set NaN if invalid)
    # -----------------------------------------------------------------------
    tickets['satisfaction_score'] = tickets['satisfaction_score'].apply(parse_satisfaction)
    # keep as float/int, pandas will write empty cell for NaN

    # -----------------------------------------------------------------------
    # R9 – reopened mapping (drop invalid)
    # -----------------------------------------------------------------------
    tickets['reopened'] = tickets['reopened'].apply(map_reopened)
    before = len(tickets)
    tickets = tickets.dropna(subset=['reopened'])
    summary['invalid_reopened_rows_removed'] = before - len(tickets)
    tickets['reopened'] = tickets['reopened'].astype(int)

    # -----------------------------------------------------------------------
    # R10 – compute labor_cost
    # -----------------------------------------------------------------------
    tickets['hourly_cost'] = tickets['hourly_cost'].astype(float)
    tickets['labor_cost'] = (tickets['resolution_minutes'] / 60.0) * tickets['hourly_cost']
    tickets['labor_cost'] = tickets['labor_cost'].round(2)

    # -----------------------------------------------------------------------
    # R11 – final column order, sort, write CSV
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
    # Write cleaning summary JSON
    # -----------------------------------------------------------------------
    summary['cleaned_rows'] = len(cleaned)
    summary_path = os.path.join(output_dir, 'cleaning_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    main()
