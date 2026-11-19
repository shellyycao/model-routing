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

tickets_df = pd.read_csv(tickets_path, dtype=str).apply(lambda x: x.str.strip()).replace([None, 'NA', 'N/A', 'null', '-'], np.nan)
agents_df = pd.read_csv(agents_path, dtype=str).apply(lambda x: x.str.strip()).replace([None, 'NA', 'N/A', 'null', '-'], np.nan)

# R1: Treat empty, NA, N/A, null, None and - as missing
# Already handled above

# R2: Remove duplicate ticket_id rows in tickets.csv
tickets_df.drop_duplicates(subset=['ticket_id'], inplace=True)

# R3: Normalise agent_id to upper case and remove duplicate agent_id rows in agents.csv
agents_df['agent_id'] = agents_df['agent_id'].str.upper()
agents_df.drop_duplicates(subset=['agent_id'], inplace=True)

# R4: Agent roster cleaning
team_map = {'ALPHA': 'Alpha', 'TEAM ALPHA': 'Alpha', 'BETA': 'Beta', 'TEAM BETA': 'Beta', 'GAMMA': 'Gamma', 'TEAM GAMMA': 'Gamma'}
region_map = {'EAST': 'East', 'E': 'East', 'WEST': 'West', 'W': 'West'}

agents_df['team'] = agents_df['team'].str.upper().map(team_map)
agents_df['region'] = agents_df['region'].str.upper().map(region_map)
agents_df['hourly_cost'] = agents_df['hourly_cost'].replace({'\$': '', 'USD': '', ',': ''}, regex=True).astype(float)
agents_df = agents_df.dropna(subset=['team','region', 'hourly_cost'])
agents_df = agents_df[agents_df['hourly_cost'] > 0]

# R5: Tickets cleaning and join
tickets_df['agent_id'] = tickets_df['agent_id'].str.upper()
tickets_df = tickets_df.merge(agents_df, on='agent_id', how='inner')

# R6: Map channel
channel_map = {'EMAIL': 'email', 'E-MAIL': 'email', 'CHAT': 'chat', 'LIVE CHAT': 'chat', 'PHONE': 'phone', 'CALL': 'phone'}
tickets_df['channel'] = tickets_df['channel'].str.upper().map(channel_map)
tickets_df = tickets_df.dropna(subset=['channel'])

# R7: Clean resolution_minutes
tickets_df['resolution_minutes'] = tickets_df['resolution_minutes'].replace({' minutes': '', 'min': ''}, regex=True).astype(int)
tickets_df = tickets_df[(tickets_df['resolution_minutes'] >= 1) & (tickets_df['resolution_minutes'] <= 480)]

# R8: Clean satisfaction_score
tickets_df['satisfaction_score'] = pd.to_numeric(tickets_df['satisfaction_score'], errors='coerce')
tickets_df['satisfaction_score'] = tickets_df['satisfaction_score'].where((tickets_df['satisfaction_score'] >= 1) & (tickets_df['satisfaction_score'] <= 5), np.nan)

# R9: Clean reopened
reopened_map = {'YES': 1, 'Y': 1, 'TRUE': 1, '1': 1, 'NO': 0, 'N': 0, 'FALSE': 0, '0': 0}
tickets_df['reopened'] = tickets_df['reopened'].str.upper().map(reopened_map)
tickets_df = tickets_df.dropna(subset=['reopened'])

# R10: Add labor_cost
tickets_df['labor_cost'] = (tickets_df['resolution_minutes'] / 60 * tickets_df['hourly_cost']).round(2)

# Select and order columns
cleaned_df = tickets_df[['ticket_id', 'agent_id', 'team','region', 'channel','resolution_minutes','satisfaction_score','reopened', 'hourly_cost', 'labor_cost']].sort_values(by='ticket_id')

# Write cleaned CSV
cleaned_csv_path = os.path.join(OUTPUT_DIR, output_filename)
cleaned_df.to_csv(cleaned_csv_path, index=False)

# Cleaning summary
cleaning_summary = {
    'raw_rows': len(tickets_df),
    'cleaned_rows': len(cleaned_df),
    'dropped_duplicates': len(tickets_df) - len(cleaned_df),
    'invalid_agents': len(agents_df) - len(agents_df.dropna(subset=['team','region', 'hourly_cost']))
}

cleaning_summary_path = os.path.join(OUTPUT_DIR, 'cleaning_summary.json')
with open(cleaning_summary_path, 'w') as f:
    json.dump(cleaning_summary, f)
