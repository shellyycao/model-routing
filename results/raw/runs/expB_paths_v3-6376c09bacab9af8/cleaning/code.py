import os
import pandas as pd
import numpy as np
import json

# Constants
INPUT_DIR = os.environ['INPUT_DIR']
OUTPUT_DIR = os.environ['OUTPUT_DIR']
output_filename = 'cleaned.csv'

# Read input files
tickets_path = os.path.join(INPUT_DIR, 'tickets.csv')
agents_path = os.path.join(INPUT_DIR, 'agents.csv')

tickets_df = pd.read_csv(tickets_path, dtype=str).apply(lambda x: x.str.strip()).replace({'': np.nan, 'NA': np.nan, 'N/A': np.nan, 'null': np.nan, 'None': np.nan, '-': np.nan})
agents_df = pd.read_csv(agents_path, dtype=str).apply(lambda x: x.str.strip()).replace({'': np.nan, 'NA': np.nan, 'N/A': np.nan, 'null': np.nan, 'None': np.nan, '-': np.nan})

# R1: Read both tickets.csv and agents.csv as text. Strip whitespace. Treat empty, NA, N/A, null, None and - as missing.
# Done above

# R2: In tickets.csv, remove duplicate ticket_id rows before any filtering; keep the first in raw-file order.
tickets_df.drop_duplicates(subset=['ticket_id'], keep='first', inplace=True)

# R3: In agents.csv, normalise agent_id to upper case and remove duplicate agent_id rows, keeping the first.
agents_df['agent_id'] = agents_df['agent_id'].str.upper()
agents_df.drop_duplicates(subset=['agent_id'], keep='first', inplace=True)

# R4: Agent roster: map team case-insensitively from Alpha/Team Alpha, Beta/Team Beta, Gamma/Team Gamma; map region East/E and West/W; parse hourly_cost after removing $, USD and commas. Exclude roster rows with an invalid field or cost <= 0.
agents_df['team'] = agents_df['team'].str.upper().replace({'TEAM ALPHA': 'Alpha', 'TEAM BETA': 'Beta', 'TEAM GAMMA': 'Gamma'})
agents_df['region'] = agents_df['region'].str.upper().replace({'E': 'East', 'W': 'West'})
agents_df['hourly_cost'] = agents_df['hourly_cost'].replace({'\$': '', 'USD': '', ',': ''}, regex=True).astype(float)
agents_df = agents_df.dropna(subset=['team','region', 'hourly_cost']).query('hourly_cost > 0')

# R5: Tickets: normalise agent_id to upper case. Join to the cleaned agent roster by agent_id and drop tickets without a matching agent.
tickets_df['agent_id'] = tickets_df['agent_id'].str.upper()
tickets_df = tickets_df.merge(agents_df[['agent_id', 'team','region', 'hourly_cost']], on='agent_id', how='inner')

# R6: Map channel case-insensitively: Email/E-mail -> email, Chat/Live Chat -> chat, Phone/Call -> phone. Drop invalid channels.
tickets_df['channel'] = tickets_df['channel'].str.lower().replace({'e-mail': 'email', 'live chat': 'chat', 'call': 'phone'})
tickets_df = tickets_df[tickets_df['channel'].isin(['email', 'chat', 'phone']) & ~tickets_df['channel'].isna()]

# R7: resolution_minutes: remove a trailing'min' or'minutes', parse a whole number from 1 through 480, and drop invalid rows.
tickets_df['resolution_minutes'] = tickets_df['resolution_minutes'].replace({' minutes': '', 'min': ''}, regex=True).astype(int, errors='coerce')
tickets_df = tickets_df[(tickets_df['resolution_minutes'] >= 1) & (tickets_df['resolution_minutes'] <= 480) & ~tickets_df['resolution_minutes'].isna()]

# R8: satisfaction_score: parse a whole number from 1 through 5. Invalid or missing values become an empty cell and the row is kept.
tickets_df['satisfaction_score'] = pd.to_numeric(tickets_df['satisfaction_score'], errors='coerce')
tickets_df['satisfaction_score'] = tickets_df['satisfaction_score'].where((tickets_df['satisfaction_score'] >= 1) & (tickets_df['satisfaction_score'] <= 5), np.nan)

# R9: reopened: map Yes/Y/True/1 to 1 and No/N/False/0 to 0, case-insensitively. Drop invalid or missing values.
tickets_df['reopened'] = tickets_df['reopened'].str.lower().replace({'yes': 1, 'y': 1, 'true': 1, '1': 1, 'no': 0, 'n': 0, 'false': 0, '0': 0})
tickets_df = tickets_df[tickets_df['reopened'].isin([0, 1]) & ~tickets_df['reopened'].isna()]

# R10: Add labor_cost = resolution_minutes / 60 * hourly_cost, rounded to 2 decimals.
tickets_df['labor_cost'] = (tickets_df['resolution_minutes'] / 60 * tickets_df['hourly_cost']).round(2)

# R11: Output exactly: ticket_id, agent_id, team, region, channel, resolution_minutes, satisfaction_score, reopened, hourly_cost, labor_cost. Sort by ticket_id and write CSV without an index.
output_df = tickets_df[['ticket_id', 'agent_id', 'team','region', 'channel','resolution_minutes','satisfaction_score','reopened', 'hourly_cost', 'labor_cost']].sort_values(by='ticket_id')
output_path = os.path.join(OUTPUT_DIR, output_filename)
output_df.to_csv(output_path, index=False)

# Write cleaning summary
cleaning_summary = {
    'raw_rows': len(pd.read_csv(tickets_path)) + len(pd.read_csv(agents_path)),
    'cleaned_rows': len(output_df),
    'dropped_duplicates_tickets': len(tickets_df) - len(output_df),
    'dropped_invalid_agents': len(agents_df) - len(agents_df.dropna(subset=['team','region', 'hourly_cost']).query('hourly_cost > 0')),
    'dropped_invalid_tickets': len(tickets_df) - len(output_df)
}
cleaning_summary_path = os.path.join(OUTPUT_DIR, 'cleaning_summary.json')
with open(cleaning_summary_path, 'w') as f:
    json.dump(cleaning_summary, f)
