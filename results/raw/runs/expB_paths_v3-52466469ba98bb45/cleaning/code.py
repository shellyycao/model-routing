import os
import pandas as pd
import numpy as np
import json

# Read input files
tickets_path = os.path.join(os.environ['INPUT_DIR'], 'tickets.csv')
agents_path = os.path.join(os.environ['INPUT_DIR'], 'agents.csv')

# Read and strip whitespace
tickets_df = pd.read_csv(tickets_path, dtype=str).apply(lambda x: x.str.strip())
agents_df = pd.read_csv(agents_path, dtype=str).apply(lambda x: x.str.strip())

# R1: Treat empty, NA, N/A, null, None and - as missing
tickets_df.replace({'': np.nan, 'NA': np.nan, 'N/A': np.nan, 'null': np.nan, 'None': np.nan, '-': np.nan}, inplace=True)
agents_df.replace({'': np.nan, 'NA': np.nan, 'N/A': np.nan, 'null': np.nan, 'None': np.nan, '-': np.nan}, inplace=True)

# R2: Remove duplicate ticket_id rows in tickets.csv
tickets_df.drop_duplicates(subset='ticket_id', inplace=True)

# R3: Normalise agent_id to upper case and remove duplicates in agents.csv
agents_df['agent_id'] = agents_df['agent_id'].str.upper()
agents_df.drop_duplicates(subset='agent_id', inplace=True)

# R4: Map team and region, parse hourly_cost
agents_df['team'] = agents_df['team'].str.upper().replace({'TEAM ALPHA': 'Alpha', 'TEAM BETA': 'Beta', 'TEAM GAMMA': 'Gamma'})
agents_df['region'] = agents_df['region'].str.upper().replace({'E': 'East', 'W': 'West'})
agents_df['hourly_cost'] = agents_df['hourly_cost'].replace({'\$|USD|,': ''}, regex=True).astype(float)
agents_df = agents_df[agents_df['hourly_cost'] > 0]

# R5: Normalise agent_id in tickets and join with agents
tickets_df['agent_id'] = tickets_df['agent_id'].str.upper()
tickets_df = tickets_df.merge(agents_df[['agent_id', 'team','region', 'hourly_cost']], on='agent_id', how='inner')

# R6: Map channel
tickets_df['channel'] = tickets_df['channel'].str.lower().replace({'email': 'email', 'e-mail': 'email', 'chat': 'chat', 'live chat': 'chat', 'phone': 'phone', 'call': 'phone'})
tickets_df = tickets_df[tickets_df['channel'].isin(['email', 'chat', 'phone']) & tickets_df['channel'].notna()]

# R7: Parse resolution_minutes
tickets_df['resolution_minutes'] = tickets_df['resolution_minutes'].replace({'min|minutes': ''}, regex=True).astype(int)
tickets_df = tickets_df[(tickets_df['resolution_minutes'] >= 1) & (tickets_df['resolution_minutes'] <= 480)]

# R8: Parse satisfaction_score
tickets_df['satisfaction_score'] = pd.to_numeric(tickets_df['satisfaction_score'], errors='coerce')
tickets_df['satisfaction_score'] = tickets_df['satisfaction_score'].where((tickets_df['satisfaction_score'] >= 1) & (tickets_df['satisfaction_score'] <= 5), np.nan)

# R9: Map reopened
tickets_df['reopened'] = tickets_df['reopened'].str.lower().replace({'yes': 1, 'y': 1, 'true': 1, '1': 1, 'no': 0, 'n': 0, 'false': 0, '0': 0})
tickets_df = tickets_df[tickets_df['reopened'].isin([0, 1])]

# R10: Calculate labor_cost
tickets_df['labor_cost'] = (tickets_df['resolution_minutes'] / 60 * tickets_df['hourly_cost']).round(2)

# Select and order columns
cleaned_df = tickets_df[['ticket_id', 'agent_id', 'team','region', 'channel','resolution_minutes','satisfaction_score','reopened', 'hourly_cost', 'labor_cost']].sort_values(by='ticket_id')

# Write cleaned CSV
output_path = os.path.join(os.environ['OUTPUT_DIR'], 'cleaned.csv')
cleaned_df.to_csv(output_path, index=False)

# Write cleaning summary
cleaning_summary = {
    'raw_rows': len(tickets_df),
    'cleaned_rows': len(cleaned_df)
}
summary_path = os.path.join(os.environ['OUTPUT_DIR'], 'cleaning_summary.json')
with open(summary_path, 'w') as f:
    json.dump(cleaning_summary, f)

# Explanation of cleaning steps
cleaning_logic = 'The script reads the input files, strips whitespace, and treats specified values as missing. It removes duplicates, normalizes agent_id, maps team and region, parses hourly_cost, and joins tickets with agents. It maps channel, parses resolution_minutes and satisfaction_score, maps reopened, calculates labor_cost, and selects/orders the required columns.'
