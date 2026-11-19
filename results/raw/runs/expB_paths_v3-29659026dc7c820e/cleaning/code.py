import os
import pandas as pd
import numpy as np
import json

# Constants
INPUT_DIR = os.environ['INPUT_DIR']
OUTPUT_DIR = os.environ['OUTPUT_DIR']
output_filename = 'cleaned.csv'

# Read input files
tickets_df = pd.read_csv(os.path.join(INPUT_DIR, 'tickets.csv'), dtype=str).apply(lambda x: x.str.strip())
agents_df = pd.read_csv(os.path.join(INPUT_DIR, 'agents.csv'), dtype=str).apply(lambda x: x.str.strip())

# R1: Treat empty, NA, N/A, null, None and - as missing
tickets_df.replace({'': np.nan, 'NA': np.nan, 'N/A': np.nan, 'null': np.nan, 'None': np.nan, '-': np.nan}, inplace=True)
agents_df.replace({'': np.nan, 'NA': np.nan, 'N/A': np.nan, 'null': np.nan, 'None': np.nan, '-': np.nan}, inplace=True)

# R2: Remove duplicate ticket_id rows in tickets.csv
tickets_df.drop_duplicates(subset=['ticket_id'], inplace=True)

# R3: Normalise agent_id to upper case and remove duplicates in agents.csv
agents_df['agent_id'] = agents_df['agent_id'].str.upper()
agents_df.drop_duplicates(subset=['agent_id'], inplace=True)

# R4: Clean agent roster
agents_df['team'] = agents_df['team'].str.upper().replace({'ALPHA': 'Alpha', 'TEAM ALPHA': 'Alpha', 'BETA': 'Beta', 'TEAM BETA': 'Beta', 'GAMMA': 'Gamma', 'TEAM GAMMA': 'Gamma'})
agents_df['region'] = agents_df['region'].str.upper().replace({'EAST': 'East', 'E': 'East', 'WEST': 'West', 'W': 'West'})
agents_df['hourly_cost'] = agents_df['hourly_cost'].replace({'\$': '', 'USD': '', ',': ''}, regex=True).astype(float)
agents_df = agents_df[agents_df['hourly_cost'].gt(0)]

# R5: Normalise agent_id in tickets and join with agents
tickets_df['agent_id'] = tickets_df['agent_id'].str.upper()
tickets_df = tickets_df.merge(agents_df, on='agent_id', how='inner')

# R6: Map channel
tickets_df['channel'] = tickets_df['channel'].str.lower().replace({'email': 'email', 'e-mail': 'email', 'chat': 'chat', 'live chat': 'chat', 'phone': 'phone', 'call': 'phone'})
tickets_df = tickets_df[tickets_df['channel'].isin(['email', 'chat', 'phone']) & tickets_df['channel'].notna()]

# R7: Clean resolution_minutes
tickets_df['resolution_minutes'] = tickets_df['resolution_minutes'].replace({' minutes': '','min': ''}, regex=True).astype(int)
tickets_df = tickets_df[(tickets_df['resolution_minutes'].between(1, 480)) & tickets_df['resolution_minutes'].notna()]

# R8: Clean satisfaction_score
tickets_df['satisfaction_score'] = pd.to_numeric(tickets_df['satisfaction_score'], errors='coerce')
tickets_df['satisfaction_score'] = tickets_df['satisfaction_score'].where(tickets_df['satisfaction_score'].between(1, 5), np.nan)

# R9: Clean reopened
tickets_df['reopened'] = tickets_df['reopened'].replace({'yes': 1, 'y': 1, 'true': 1, '1': 1, 'no': 0, 'n': 0, 'false': 0, '0': 0}, regex=True).astype(int)
tickets_df = tickets_df[tickets_df['reopened'].isin([0, 1]) & tickets_df['reopened'].notna()]

# R10: Add labor_cost
tickets_df['labor_cost'] = (tickets_df['resolution_minutes'] / 60 * tickets_df['hourly_cost']).round(2)

# Select and order columns
cleaned_df = tickets_df[['ticket_id', 'agent_id', 'team','region', 'channel','resolution_minutes','satisfaction_score','reopened', 'hourly_cost', 'labor_cost']].sort_values(by='ticket_id')

# Write cleaned data
cleaned_df.to_csv(os.path.join(OUTPUT_DIR, output_filename), index=False)

# Cleaning summary
cleaning_summary = {
    'raw_rows': len(tickets_df),
    'cleaned_rows': len(cleaned_df),
    'dropped_duplicates': len(tickets_df) - len(tickets_df.drop_duplicates()),
    'invalid_agents': len(agents_df) - len(agents_df[agents_df['hourly_cost'].gt(0)]),
    'invalid_channels': len(tickets_df) - len(tickets_df[tickets_df['channel'].isin(['email', 'chat', 'phone']) & tickets_df['channel'].notna()]),
    'invalid_resolution_minutes': len(tickets_df) - len(tickets_df[(tickets_df['resolution_minutes'].between(1, 480)) & tickets_df['resolution_minutes'].notna()]),
    'invalid_satisfaction_scores': len(tickets_df) - len(tickets_df[tickets_df['satisfaction_score'].between(1, 5) & tickets_df['satisfaction_score'].notna()]),
    'invalid_reopened': len(tickets_df) - len(tickets_df[tickets_df['reopened'].isin([0, 1]) & tickets_df['reopened'].notna()])
}

with open(os.path.join(OUTPUT_DIR, 'cleaning_summary.json'), 'w') as f:
    json.dump(cleaning_summary, f)
