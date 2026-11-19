import json
import os
import re

import numpy as np
import pandas as pd

INPUT_DIR = os.environ['INPUT_DIR']
OUTPUT_DIR = os.environ['OUTPUT_DIR']
os.makedirs(OUTPUT_DIR, exist_ok=True)

MISSING_TOKENS = {'', 'na', 'n/a', 'null', 'none', '-'}
INT_RE = re.compile(r'\d+')
MINUTES_SUFFIX_RE = re.compile(r'(?i)\s*(minutes|min)\s*$')

TEAM_MAP = {
    'alpha': 'Alpha', 'team alpha': 'Alpha',
    'beta': 'Beta', 'team beta': 'Beta',
    'gamma': 'Gamma', 'team gamma': 'Gamma',
}
REGION_MAP = {'east': 'East', 'e': 'East', 'west': 'West', 'w': 'West'}
CHANNEL_MAP = {
    'email': 'email', 'e-mail': 'email',
    'chat': 'chat', 'live chat': 'chat',
    'phone': 'phone', 'call': 'phone',
}
REOPENED_MAP = {
    'yes': 1, 'y': 1, 'true': 1, '1': 1,
    'no': 0, 'n': 0, 'false': 0, '0': 0,
}
OUTPUT_COLUMNS = [
    'ticket_id', 'agent_id', 'team', 'region', 'channel',
    'resolution_minutes', 'satisfaction_score', 'reopened',
    'hourly_cost', 'labor_cost',
]

summary = {}


def read_text_csv(path):
    # R1: read everything as text, strip whitespace, standardise missing tokens.
    df = pd.read_csv(path, dtype=str, na_filter=False, encoding='utf-8-sig')
    df.columns = [str(c).strip() for c in df.columns]
    for col in df.columns:
        s = df[col].astype(str).str.strip()
        df[col] = s.mask(s.str.lower().isin(MISSING_TOKENS), pd.NA)
    return df


def parse_hourly_cost(value):
    if pd.isna(value):
        return np.nan
    text = re.sub(r'(?i)usd', '', str(value))
    text = text.replace('$', '').replace(',', '').strip()
    if not text:
        return np.nan
    try:
        return float(text)
    except ValueError:
        return np.nan


def parse_resolution_minutes(value):
    if pd.isna(value):
        return pd.NA
    text = MINUTES_SUFFIX_RE.sub('', str(value)).strip()
    if INT_RE.fullmatch(text):
        minutes = int(text)
        if 1 <= minutes <= 480:
            return minutes
    return pd.NA


def parse_satisfaction(value):
    if pd.isna(value):
        return pd.NA
    text = str(value).strip()
    if INT_RE.fullmatch(text):
        score = int(text)
        if 1 <= score <= 5:
            return score
    return pd.NA


# R1: load inputs.
tickets = read_text_csv(os.path.join(INPUT_DIR, 'tickets.csv'))
agents = read_text_csv(os.path.join(INPUT_DIR, 'agents.csv'))
summary['raw_rows'] = int(len(tickets))
summary['raw_agent_rows'] = int(len(agents))

# R2: drop duplicate ticket_ids (first occurrence wins) before any filtering.
before = len(tickets)
tickets = tickets.drop_duplicates(subset=['ticket_id'], keep='first')
summary['r2_duplicate_ticket_id_rows_removed'] = int(before - len(tickets))
summary['r2_missing_ticket_id_rows_removed'] = int(tickets['ticket_id'].isna().sum())
tickets = tickets[tickets['ticket_id'].notna()].copy()

# R3: upper-case roster ids and drop duplicates, keeping the first.
agents['agent_id'] = agents['agent_id'].str.upper()
before = len(agents)
agents = agents.drop_duplicates(subset=['agent_id'], keep='first')
summary['r3_duplicate_agent_id_rows_removed'] = int(before - len(agents))

# R4: normalise roster fields; exclude rows with an invalid field or cost <= 0.
agents['team'] = agents['team'].str.lower().map(TEAM_MAP)
agents['region'] = agents['region'].str.lower().map(REGION_MAP)
agents['hourly_cost'] = agents['hourly_cost'].map(parse_hourly_cost)
valid_roster = (
    agents['agent_id'].notna()
    & agents['team'].notna()
    & agents['region'].notna()
    & agents['hourly_cost'].notna()
    & (agents['hourly_cost'] > 0)
)
summary['r4_invalid_roster_rows_removed'] = int((~valid_roster).sum())
agents = agents[valid_roster].copy()

# R5: upper-case ticket agent ids and keep only tickets with a matching agent.
tickets['agent_id'] = tickets['agent_id'].str.upper()
before = len(tickets)
data = tickets.merge(agents, on='agent_id', how='inner')
summary['r5_tickets_without_matching_agent_removed'] = int(before - len(data))

# R6: normalise channel case-insensitively and drop invalid rows.
data['channel'] = data['channel'].str.lower().map(CHANNEL_MAP)
summary['r6_invalid_channel_rows_removed'] = int(data['channel'].isna().sum())
data = data[data['channel'].notna()].copy()

# R7: parse resolution_minutes as a whole number 1..480, drop invalid rows.
data['resolution_minutes'] = data['resolution_minutes'].map(parse_resolution_minutes)
summary['r7_invalid_resolution_minutes_rows_removed'] = int(data['resolution_minutes'].isna().sum())
data = data[data['resolution_minutes'].notna()].copy()
data['resolution_minutes'] = data['resolution_minutes'].astype('int64')

# R8: parse satisfaction_score 1..5; invalid or missing becomes empty, row kept.
raw_satisfaction = data['satisfaction_score']
parsed_satisfaction = raw_satisfaction.map(parse_satisfaction)
summary['r8_missing_satisfaction_score_emptied'] = int(raw_satisfaction.isna().sum())
summary['r8_invalid_satisfaction_score_emptied'] = int(
    (raw_satisfaction.notna() & parsed_satisfaction.isna()).sum()
)
data['satisfaction_score'] = parsed_satisfaction.astype('Int64')

# R9: map reopened to 0/1; drop invalid or missing values.
data['reopened'] = data['reopened'].str.lower().map(REOPENED_MAP)
summary['r9_invalid_reopened_rows_removed'] = int(data['reopened'].isna().sum())
data = data[data['reopened'].notna()].copy()
data['reopened'] = data['reopened'].astype('int64')

# R10: labour cost derived from minutes and hourly cost, rounded to 2 decimals.
data['labor_cost'] = (data['resolution_minutes'] / 60.0 * data['hourly_cost']).round(2)

# R11: enforce schema dtypes/categories, order columns, sort, write output.
data['team'] = pd.Categorical(data['team'], categories=['Alpha', 'Beta', 'Gamma'])
data['region'] = pd.Categorical(data['region'], categories=['East', 'West'])
data['channel'] = pd.Categorical(data['channel'], categories=['email', 'chat', 'phone'])
result = data[OUTPUT_COLUMNS].sort_values('ticket_id').reset_index(drop=True)
result.to_csv(os.path.join(OUTPUT_DIR, 'cleaned.csv'), index=False)
summary['cleaned_rows'] = int(len(result))

with open(os.path.join(OUTPUT_DIR, 'cleaning_summary.json'), 'w', encoding='utf-8') as fh:
    json.dump(summary, fh, indent=2)
