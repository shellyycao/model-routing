import os
import json
import re
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def clean_string_series(series):
    """Strip whitespace and replace common missing markers with NaN."""
    return series.apply(lambda x: x.strip() if isinstance(x, str) else x) \
                 .replace(['', 'NA', 'N/A', 'null', 'None', '-'], np.nan)

def map_team(value):
    if pd.isna(value):
        return np.nan
    v = str(value).lower()
    if 'alpha' in v:
        return 'Alpha'
    if 'beta' in v:
        return 'Beta'
    if 'gamma' in v:
        return 'Gamma'
    return np.nan

def map_region(value):
    if pd.isna(value):
        return np.nan
    v = str(value).lower()
    if v in ('east', 'e'):
        return 'East'
    if v in ('west', 'w'):
        return 'West'
    return np.nan

def parse_hourly_cost(value):
    if pd.isna(value):
        return np.nan
    # Remove currency symbols, commas and whitespace
    cleaned = re.sub(r'[$,]', '', str(value), flags=re.IGNORECASE)
    cleaned = re.sub(r'(?i)usd', '', cleaned)
    cleaned = cleaned.strip()
    try:
        cost = float(cleaned)
        return cost if cost > 0 else np.nan
    except ValueError:
        return np.nan

def map_channel(value):
    if pd.isna(value):
        return np.nan
    v = str(value).lower().replace(' ', '')
    if v in ('email', 'e-mail'):
        return 'email'
    if v in ('chat', 'livechat'):
        return 'chat'
    if v in ('phone', 'call'):
        return 'phone'
    return np.nan

def parse_resolution(value):
    if pd.isna(value):
        return np.nan
    v = str(value).lower()
    v = re.sub(r'(min|minutes)', '', v)
    v = v.strip()
    if not v.isdigit():
        return np.nan
    minutes = int(v)
    return minutes if 1 <= minutes <= 480 else np.nan

def parse_satisfaction(value):
    if pd.isna(value):
        return np.nan
    v = str(value).strip()
    if not v.isdigit():
        return np.nan
    score = int(v)
    return score if 1 <= score <= 5 else np.nan

def map_reopened(value):
    if pd.isna(value):
        return np.nan
    v = str(value).strip().lower()
    if v in ('yes', 'y', 'true', '1'):
        return 1
    if v in ('no', 'n', 'false', '0'):
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

    tickets_path = os.path.join(input_dir, 'tickets.csv')
    agents_path = os.path.join(input_dir, 'agents.csv')

    # ---------------------------------------------------
    # R1 – read as text, strip, treat missing markers
    # ---------------------------------------------------
    tickets_raw = pd.read_csv(tickets_path, dtype=str, keep_default_na=False)
    agents_raw = pd.read_csv(agents_path, dtype=str, keep_default_na=False)

    tickets_raw = tickets_raw.apply(clean_string_series)
    agents_raw = agents_raw.apply(clean_string_series)

    summary = {
        'raw_rows': len(tickets_raw),
        'duplicates_removed_tickets': 0,
        'duplicates_removed_agents': 0,
        'invalid_agents_excluded': 0,
        'tickets_without_agent': 0,
        'invalid_channels': 0,
        'invalid_resolution': 0,
        'invalid_reopened': 0,
        'final_rows': 0
    }

    # ---------------------------------------------------
    # R2 – drop duplicate ticket_id, keep first
    # ---------------------------------------------------
    before_dup = len(tickets_raw)
    tickets = tickets_raw.drop_duplicates(subset='ticket_id', keep='first')
    summary['duplicates_removed_tickets'] = before_dup - len(tickets)

    # ---------------------------------------------------
    # R3 – normalise agent_id upper case, drop duplicate agents
    # ---------------------------------------------------
    agents = agents_raw.copy()
    agents['agent_id'] = agents['agent_id'].str.upper()
    before_dup_agents = len(agents)
    agents = agents.drop_duplicates(subset='agent_id', keep='first')
    summary['duplicates_removed_agents'] = before_dup_agents - len(agents)

    # ---------------------------------------------------
    # R4 – clean roster fields, map team/region, parse cost, drop invalid rows
    # ---------------------------------------------------
    agents['team'] = agents['team'].apply(map_team)
    agents['region'] = agents['region'].apply(map_region)
    agents['hourly_cost'] = agents['hourly_cost'].apply(parse_hourly_cost)

    # Identify rows with any NaN in required fields
    valid_agents_mask = agents[['agent_id', 'team', 'region', 'hourly_cost']].notnull().all(axis=1)
    summary['invalid_agents_excluded'] = (~valid_agents_mask).sum()
    agents = agents[valid_agents_mask].reset_index(drop=True)

    # ---------------------------------------------------
    # R5 – normalise ticket agent_id, join to roster, drop unmatched tickets
    # ---------------------------------------------------
    tickets['agent_id'] = tickets['agent_id'].str.upper()
    tickets = tickets.merge(agents, on='agent_id', how='inner', suffixes=('', '_agent'))
    summary['tickets_without_agent'] = before_dup - len(tickets) - summary['duplicates_removed_tickets']

    # ---------------------------------------------------
    # R6 – map channel, drop invalid
    # ---------------------------------------------------
    tickets['channel'] = tickets['channel'].apply(map_channel)
    before_channel = len(tickets)
    tickets = tickets[tickets['channel'].notnull()]
    summary['invalid_channels'] = before_channel - len(tickets)

    # ---------------------------------------------------
    # R7 – clean resolution_minutes, drop invalid
    # ---------------------------------------------------
    tickets['resolution_minutes'] = tickets['resolution_minutes'].apply(parse_resolution)
    before_res = len(tickets)
    tickets = tickets[tickets['resolution_minutes'].notnull()]
    summary['invalid_resolution'] = before_res - len(tickets)

    # ---------------------------------------------------
    # R8 – satisfaction_score (keep row, set NaN if invalid)
    # ---------------------------------------------------
    tickets['satisfaction_score'] = tickets['satisfaction_score'].apply(parse_satisfaction)

    # ---------------------------------------------------
    # R9 – reopened mapping, drop invalid/missing
    # ---------------------------------------------------
    tickets['reopened'] = tickets['reopened'].apply(map_reopened)
    before_reopen = len(tickets)
    tickets = tickets[tickets['reopened'].notnull()]
    summary['invalid_reopened'] = before_reopen - len(tickets)

    # ---------------------------------------------------
    # R10 – compute labor_cost
    # ---------------------------------------------------
    tickets['labor_cost'] = (tickets['resolution_minutes'] / 60.0) * tickets['hourly_cost']
    tickets['labor_cost'] = tickets['labor_cost'].round(2)

    # ---------------------------------------------------
    # R11 – final column order, types, sorting, write output
    # ---------------------------------------------------
    final_cols = [
        'ticket_id', 'agent_id', 'team', 'region', 'channel',
        'resolution_minutes', 'satisfaction_score', 'reopened',
        'hourly_cost', 'labor_cost'
    ]
    cleaned = tickets[final_cols].copy()
    cleaned = cleaned.sort_values('ticket_id')

    # Ensure correct dtypes (pandas will infer, but we enforce where needed)
    cleaned['resolution_minutes'] = cleaned['resolution_minutes'].astype(int)
    cleaned['reopened'] = cleaned['reopened'].astype(int)
    cleaned['hourly_cost'] = cleaned['hourly_cost'].astype(float)
    cleaned['labor_cost'] = cleaned['labor_cost'].astype(float)
    # satisfaction_score may be NaN – keep as float/int nullable

    cleaned_path = os.path.join(output_dir, 'cleaned.csv')
    cleaned.to_csv(cleaned_path, index=False)

    summary['cleaned_rows'] = len(cleaned)
    summary['final_rows'] = len(cleaned)

    # Write cleaning summary JSON
    summary_path = os.path.join(output_dir, 'cleaning_summary.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    main()
