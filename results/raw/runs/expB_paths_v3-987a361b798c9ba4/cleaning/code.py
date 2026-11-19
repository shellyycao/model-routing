import os
import pandas as pd
import numpy as np
import json

# Constants
INPUT_DIR = os.environ['INPUT_DIR']
OUTPUT_DIR = os.environ['OUTPUT_DIR']
output_filename = 'cleaned.csv'

# Read input files
tickets_df = pd.read_csv(os.path.join(INPUT_DIR, 'tickets.csv'), keep_default_na=False)
agents_df = pd.read_csv(os.path.join(INPUT_DIR, 'agents.csv'), keep_default_na=False)

# R1: Strip whitespace and treat specified values as missing
for df in [tickets_df, agents_df]:
    df.replace({'': np.nan, 'NA': np.nan, 'N/A': np.nan, 'null': np.nan, 'None': np.nan, '-': np.nan}, inplace=True)
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

# R2: Remove duplicate ticket_id rows in tickets.csv
tickets_df.drop_duplicates(subset='ticket_id', inplace=True)

# R3: Normalise agent_id to upper case and remove duplicates in agents.csv
agents_df['agent_id'] = agents_df['agent_id'].str.upper()
agents_df.drop_duplicates(subset='agent_id', inplace=True)

# R4: Clean agent roster
agents_df['team'] = agents_df['team'].str.upper().replace({'TEAM ALPHA': 'Alpha', 'TEAM BETA': 'Beta', 'TEAM GAMMA': 'Gamma'})
agents_df['region'] = agents_df['region'].str.upper().replace({'E': 'East', 'W': 'West'})
agents_df['hourly_cost'] = agents_df['hourly_cost'].replace({'\$': '', 'USD': '', ',': ''}, regex=True).astype(float)
agents_df = agents_df[agents_df['hourly_cost'] > 0]

# R5: Normalise agent_id in tickets and join with agents
tickets_df['agent_id'] = tickets_df['agent_id'].str.upper()
tickets_df = tickets_df.merge(agents_df[['agent_id', 'team', 'region', 'hourly_cost']], on='agent_id', how='inner')

# R6: Map channel
tickets_df['channel'] = tickets_df['channel'].str.lower().replace({'e-mail': 'email', 'live chat': 'chat', 'call': 'phone'})
tickets_df = tickets_df[tickets_df['channel'].isin(['email', 'chat', 'phone']) & ~tickets_df['channel'].isna()]

# R7: Clean resolution_minutes
tickets_df['resolution_minutes'] = tickets_df['resolution_minutes'].replace({' minutes': '','min': ''}, regex=True).astype(int)
tickets_df = tickets_df[(tickets_df['resolution_minutes'] >= 1) & (tickets_df['resolution_minutes'] <= 480)]

# R8: Clean satisfaction_score
tickets_df['satisfaction_score'] = pd.to_numeric(tickets_df['satisfaction_score'], errors='coerce')
tickets_df['satisfaction_score'] = tickets_df['satisfaction_score'].where((tickets_df['satisfaction_score'] >= 1) & (tickets_df['satisfaction_score'] <= 5), np.nan)

# R9: Clean reopened
tickets_df['reopened'] = tickets_df['reopened'].replace({'YES': 1, 'Y': 1, 'TRUE': 1, '1': 1, 'NO': 0, 'N': 0, 'FALSE': 0, '0': 0}, regex=True)
tickets_df = tickets_df[tickets_df['reopened'].isin([0, 1])]

# R10: Calculate labor_cost
tickets_df['labor_cost'] = (tickets_df['resolution_minutes'] / 60 * tickets_df['hourly_cost']).round(2)

# Select and order columns
cleaned_df = tickets_df[['ticket_id', 'agent_id', 'team','region', 'channel','resolution_minutes','satisfaction_score','reopened', 'hourly_cost', 'labor_cost']].sort_values(by='ticket_id')

# Write cleaned data
cleaned_df.to_csv(os.path.join(OUTPUT_DIR, output_filename), index=False)

# Cleaning summary
cleaning_summary = {
    'raw_rows': len(tickets_df) + len(agents_df),
    'cleaned_rows': len(cleaned_df),
    'dropped_tickets': len(tickets_df) - len(cleaned_df),
    'dropped_agents': len(agents_df) - len(agents_df[agents_df['agent_id'].isin(cleaned_df['agent_id'])]),
}

with open(os.path.join(OUTPUT_DIR, 'cleaning_summary.json'), 'w') as f:
    json.dump(cleaning_summary, f)
