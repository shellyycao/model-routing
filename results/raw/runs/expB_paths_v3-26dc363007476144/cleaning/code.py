import os
import json
import re
import pandas as pd
import numpy as np

def clean_string_df(df):
    # Strip whitespace from all string cells
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    # Define missing tokens
    missing = {'': np.nan, 'NA': np.nan, 'N/A': np.nan, 'null': np.nan, 'None': np.nan, '-': np.nan}
    df.replace(missing, inplace=True)
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

def parse_cost(val):
    if pd.isna(val):
        return np.nan
    # Remove currency symbols and commas
    cleaned = re.sub(r'[\$,]', '', val, flags=re.IGNORECASE)
    cleaned = cleaned.replace('USD', '').strip()
    try:
        return float(cleaned)
    except Exception:
        return np.nan

def map_channel(val):
    if pd.isna(val):
        return np.nan
    low = val.lower()
    if 'email' in low:
        return 'email'
    if 'chat' in low:
        return 'chat'
    if 'phone' in low or 'call' in low:
        return 'phone'
    return np.nan

def parse_resolution(val):
    if pd.isna(val):
        return np.nan
    m = re.search(r'(\d+)', val)
    if m:
        minutes = int(m.group(1))
        if 1 <= minutes <= 480:
            return minutes
    return np.nan

def parse_satisfaction(val):
    if pd.isna(val):
        return np.nan
    try:
        i = int(float(val))
        if 1 <= i <= 5:
            return i
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

def main():
    input_dir = os.environ.get('INPUT_DIR', '.')
    output_dir = os.environ.get('OUTPUT_DIR', '.')

    tickets_path = os.path.join(input_dir, 'tickets.csv')
    agents_path = os.path.join(input_dir, 'agents.csv')

    # R1 – read as text, strip, treat missing tokens
    tickets = pd.read_csv(tickets_path, dtype=str, keep_default_na=False)
    agents = pd.read_csv(agents_path, dtype=str, keep_default_na=False)
    raw_rows_tickets = len(tickets)
    raw_rows_agents = len(agents)
    tickets = clean_string_df(tickets)
    agents = clean_string_df(agents)

    # R2 – deduplicate tickets on ticket_id (keep first)
    tickets = tickets.drop_duplicates(subset='ticket_id', keep='first')
    dup_removed_tickets = raw_rows_tickets - len(tickets)

    # R3 – normalise agent_id to upper case and deduplicate agents
    agents['agent_id'] = agents['agent_id'].str.upper()
    agents = agents.drop_duplicates(subset='agent_id', keep='first')
    dup_removed_agents = raw_rows_agents - len(agents)

    # R4 – clean roster fields
    agents['team'] = agents['team'].apply(map_team)
    agents['region'] = agents['region'].apply(map_region)
    agents['hourly_cost'] = agents['hourly_cost'].apply(parse_cost)
    # Exclude rows with invalid fields or non‑positive cost
    agents_clean = agents.dropna(subset=['team', 'region', 'hourly_cost'])
    agents_clean = agents_clean[agents_clean['hourly_cost'] > 0]
    roster_invalid = len(agents) - len(agents_clean)

    # R5 – normalise ticket agent_id and inner join with roster
    tickets['agent_id'] = tickets['agent_id'].str.upper()
    tickets = tickets.merge(
        agents_clean[['agent_id', 'team', 'region', 'hourly_cost']],
        on='agent_id',
        how='inner'
    )
    after_join = len(tickets)

    # R6 – map channel, drop invalid
    tickets['channel'] = tickets['channel'].apply(map_channel)
    tickets = tickets.dropna(subset=['channel'])
    after_channel = len(tickets)

    # R7 – clean resolution_minutes, drop invalid
    tickets['resolution_minutes'] = tickets['resolution_minutes'].apply(parse_resolution)
    tickets = tickets.dropna(subset=['resolution_minutes'])
    tickets['resolution_minutes'] = tickets['resolution_minutes'].astype(int)
    after_resolution = len(tickets)

    # R8 – parse satisfaction_score, keep row even if missing/invalid
    tickets['satisfaction_score'] = tickets['satisfaction_score'].apply(parse_satisfaction)
    # keep as float/int, pandas will store NaN for missing

    # R9 – map reopened, drop invalid/missing
    tickets['reopened'] = tickets['reopened'].apply(map_reopened)
    tickets = tickets.dropna(subset=['reopened'])
    tickets['reopened'] = tickets['reopened'].astype(int)
    after_reopened = len(tickets)

    # R10 – compute labor_cost
    tickets['labor_cost'] = (tickets['resolution_minutes'] / 60.0) * tickets['hourly_cost']
    tickets['labor_cost'] = tickets['labor_cost'].round(2)

    # R11 – final column order and sort
    final_cols = [
        'ticket_id', 'agent_id', 'team', 'region', 'channel',
        'resolution_minutes', 'satisfaction_score', 'reopened',
        'hourly_cost', 'labor_cost'
    ]
    cleaned = tickets[final_cols].copy()
    cleaned = cleaned.sort_values('ticket_id')
    cleaned_rows = len(cleaned)

    # Write cleaned CSV
    cleaned_path = os.path.join(output_dir, 'cleaned.csv')
    cleaned.to_csv(cleaned_path, index=False)

    # Write cleaning summary JSON
    summary = {
        'raw_rows': {
            'tickets': raw_rows_tickets,
            'agents': raw_rows_agents
        },
        'rows_removed': {
            'duplicate_tickets': dup_removed_tickets,
            'duplicate_agents': dup_removed_agents,
            'invalid_roster_rows': roster_invalid,
            'tickets_without_agent': raw_rows_tickets - after_join,
            'invalid_channel': after_join - after_channel,
            'invalid_resolution_minutes': after_channel - after_resolution,
            'invalid_reopened': after_resolution - after_reopened
        },
        'cleaned_rows': cleaned_rows
    }
    summary_path = os.path.join(output_dir, 'cleaning_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    main()
