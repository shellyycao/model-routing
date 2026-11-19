import os
import json
import pandas as pd
import numpy as np

def clean_data():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    
    summary = {}
    
    # R1: Read both files as text, strip whitespace
    with open(os.path.join(input_dir, "tickets.csv"), 'r', encoding='utf-8') as f:
        tickets_raw = f.read()
    with open(os.path.join(input_dir, "agents.csv"), 'r', encoding='utf-8') as f:
        agents_raw = f.read()
    
    # Helper to normalize missing values
    def normalize_missing(val):
        if pd.isna(val):
            return np.nan
        s = str(val).strip()
        if s.lower() in ['', 'na', 'n/a', 'null', 'none', '-']:
            return np.nan
        return s
    
    # Parse tickets
    from io import StringIO
    tickets_df = pd.read_csv(StringIO(tickets_raw), dtype=str)
    summary['raw_rows_tickets'] = len(tickets_df)
    
    # Parse agents
    agents_df = pd.read_csv(StringIO(agents_raw), dtype=str)
    summary['raw_rows_agents'] = len(agents_df)
    
    # Apply missing value normalization to all columns
    for col in tickets_df.columns:
        tickets_df[col] = tickets_df[col].apply(normalize_missing)
    for col in agents_df.columns:
        agents_df[col] = agents_df[col].apply(normalize_missing)
    
    # R2: Remove duplicate ticket_id, keep first
    tickets_df = tickets_df.drop_duplicates(subset='ticket_id', keep='first')
    
    # R3: Normalize agent_id to upper case, remove duplicates
    agents_df['agent_id'] = agents_df['agent_id'].str.upper()
    agents_df = agents_df.drop_duplicates(subset='agent_id', keep='first')
    
    # R4: Agent roster cleaning
    # Map team
    def map_team(val):
        if pd.isna(val):
            return np.nan
        v = str(val).strip().lower()
        if v in ['alpha', 'team alpha']:
            return 'Alpha'
        if v in ['beta', 'team beta']:
            return 'Beta'
        if v in ['gamma', 'team gamma']:
            return 'Gamma'
        return np.nan
    
    agents_df['team'] = agents_df['team'].apply(map_team)
    
    # Map region
    def map_region(val):
        if pd.isna(val):
            return np.nan
        v = str(val).strip().lower()
        if v in ['east', 'e']:
            return 'East'
        if v in ['west', 'w']:
            return 'West'
        return np.nan
    
    agents_df['region'] = agents_df['region'].apply(map_region)
    
    # Parse hourly_cost
    def parse_cost(val):
        if pd.isna(val):
            return np.nan
        s = str(val).replace('$', '').replace('USD', '').replace(',', '').strip()
        try:
            return float(s)
        except:
            return np.nan
    
    agents_df['hourly_cost'] = agents_df['hourly_cost'].apply(parse_cost)
    
    # Exclude roster rows with invalid field or cost <= 0
    agents_df = agents_df.dropna(subset=['agent_id', 'team', 'region', 'hourly_cost'])
    agents_df = agents_df[agents_df['hourly_cost'] > 0]
    
    # R5: Tickets - normalize agent_id, join, drop unmatched
    tickets_df['agent_id'] = tickets_df['agent_id'].str.upper()
    tickets_df = tickets_df.merge(agents_df[['agent_id', 'team', 'region', 'hourly_cost']], 
                                   on='agent_id', how='inner')
    
    # R6: Map channel
    def map_channel(val):
        if pd.isna(val):
            return np.nan
        v = str(val).strip().lower()
        if v in ['email', 'e-mail']:
            return 'email'
        if v in ['chat', 'live chat']:
            return 'chat'
        if v in ['phone', 'call']:
            return 'phone'
        return np.nan
    
    tickets_df['channel'] = tickets_df['channel'].apply(map_channel)
    tickets_df = tickets_df.dropna(subset=['channel'])
    
    # R7: resolution_minutes
    def parse_minutes(val):
        if pd.isna(val):
            return np.nan
        s = str(val).lower().replace('min', '').replace('utes', '').replace('minute', '').strip()
        try:
            m = int(s)
            if 1 <= m <= 480:
                return m
            return np.nan
        except:
            return np.nan
    
    tickets_df['resolution_minutes'] = tickets_df['resolution_minutes'].apply(parse_minutes)
    tickets_df = tickets_df.dropna(subset=['resolution_minutes'])
    
    # R8: satisfaction_score
    def parse_satisfaction(val):
        if pd.isna(val):
            return np.nan
        try:
            s = int(float(val))
            if 1 <= s <= 5:
                return s
            return np.nan
        except:
            return np.nan
    
    tickets_df['satisfaction_score'] = tickets_df['satisfaction_score'].apply(parse_satisfaction)
    # Keep rows even if satisfaction is NaN (per R8)
    
    # R9: reopened
    def map_reopened(val):
        if pd.isna(val):
            return np.nan
        v = str(val).strip().lower()
        if v in ['yes', 'y', 'true', '1']:
            return 1
        if v in ['no', 'n', 'false', '0']:
            return 0
        return np.nan
    
    tickets_df['reopened'] = tickets_df['reopened'].apply(map_reopened)
    tickets_df = tickets_df.dropna(subset=['reopened'])
    
    # R10: labor_cost
    tickets_df['labor_cost'] = (tickets_df['resolution_minutes'] / 60 * tickets_df['hourly_cost']).round(2)
    
    # R11: Output columns
    output_cols = ['ticket_id', 'agent_id', 'team', 'region', 'channel', 
                   'resolution_minutes', 'satisfaction_score', 'reopened', 
                   'hourly_cost', 'labor_cost']
    
    tickets_df = tickets_df[output_cols]
    tickets_df = tickets_df.sort_values('ticket_id')
    
    # Convert types for output
    tickets_df['resolution_minutes'] = tickets_df['resolution_minutes'].astype(int)
    tickets_df['reopened'] = tickets_df['reopened'].astype(int)
    # satisfaction_score stays as float (NaN allowed)
    
    summary['cleaned_rows'] = len(tickets_df)
    
    # Write outputs
    tickets_df.to_csv(os.path.join(output_dir, 'cleaned.csv'), index=False)
    
    with open(os.path.join(output_dir, 'cleaning_summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    clean_data()
