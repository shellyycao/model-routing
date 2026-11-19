import os
import json
import pandas as pd
import numpy as np

def clean_data():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    
    # Initialize summary stats
    stats = {}
    
    # R1: Read and strip whitespace, handle missing values
    na_values = ['', 'NA', 'N/A', 'null', 'None', '-']
    
    # Read tickets
    tickets_path = os.path.join(input_dir, "tickets.csv")
    df_tickets = pd.read_csv(tickets_path, skipinitialspace=True, na_values=na_values, keep_default_na=False, dtype=str)
    # Strip whitespace from all string columns
    for col in df_tickets.columns:
        if df_tickets[col].dtype == object:
            df_tickets[col] = df_tickets[col].str.strip()
    stats['raw_tickets_rows'] = len(df_tickets)
    
    # Read agents
    agents_path = os.path.join(input_dir, "agents.csv")
    df_agents = pd.read_csv(agents_path, skipinitialspace=True, na_values=na_values, keep_default_na=False, dtype=str)
    for col in df_agents.columns:
        if df_agents[col].dtype == object:
            df_agents[col] = df_agents[col].str.strip()
    stats['raw_agents_rows'] = len(df_agents)
    
    # R2: Remove duplicate ticket_id, keep first
    before_dedup = len(df_tickets)
    df_tickets = df_tickets.drop_duplicates(subset='ticket_id', keep='first')
    stats['tickets_dedup_removed'] = before_dedup - len(df_tickets)
    
    # R3: Normalize agent_id to upper case and remove duplicates in agents
    df_agents['agent_id'] = df_agents['agent_id'].str.upper()
    before_agent_dedup = len(df_agents)
    df_agents = df_agents.drop_duplicates(subset='agent_id', keep='first')
    stats['agents_dedup_removed'] = before_agent_dedup - len(df_agents)
    
    # R4: Clean agent roster
    # Map team
    team_map = {
        'alpha': 'Alpha', 'team alpha': 'Alpha',
        'beta': 'Beta', 'team beta': 'Beta',
        'gamma': 'Gamma', 'team gamma': 'Gamma'
    }
    df_agents['team'] = df_agents['team'].str.lower().map(team_map)
    
    # Map region
    region_map = {'east': 'East', 'e': 'East', 'west': 'West', 'w': 'West'}
    df_agents['region'] = df_agents['region'].str.lower().map(region_map)
    
    # Parse hourly_cost
    def parse_cost(val):
        if pd.isna(val): return np.nan
        s = str(val).replace('$', '').replace('USD', '').replace(',', '').strip()
        try: return float(s)
        except: return np.nan
    df_agents['hourly_cost'] = df_agents['hourly_cost'].apply(parse_cost)
    
    # Exclude invalid roster rows
    before_roster_filter = len(df_agents)
    df_agents = df_agents.dropna(subset=['agent_id', 'team', 'region', 'hourly_cost'])
    df_agents = df_agents[df_agents['hourly_cost'] > 0]
    stats['agents_invalid_removed'] = before_roster_filter - len(df_agents)
    
    # R5: Join tickets to cleaned agent roster
    df_tickets['agent_id'] = df_tickets['agent_id'].str.upper()
    df_merged = pd.merge(df_tickets, df_agents, on='agent_id', how='inner')
    stats['tickets_unmatched_removed'] = len(df_tickets) - len(df_merged)
    
    # R6: Map channel
    channel_map = {
        'email': 'email', 'e-mail': 'email',
        'chat': 'chat', 'live chat': 'chat',
        'phone': 'phone', 'call': 'phone'
    }
    df_merged['channel'] = df_merged['channel'].str.lower().map(channel_map)
    before_channel_filter = len(df_merged)
    df_merged = df_merged.dropna(subset=['channel'])
    stats['tickets_invalid_channel_removed'] = before_channel_filter - len(df_merged)
    
    # R7: Parse resolution_minutes
    def parse_minutes(val):
        if pd.isna(val): return np.nan
        s = str(val).lower().replace('min', '').replace('utes', '').strip()
        try:
            m = int(s)
            return m if 1 <= m <= 480 else np.nan
        except:
            return np.nan
    df_merged['resolution_minutes'] = df_merged['resolution_minutes'].apply(parse_minutes)
    before_min_filter = len(df_merged)
    df_merged = df_merged.dropna(subset=['resolution_minutes'])
    stats['tickets_invalid_minutes_removed'] = before_min_filter - len(df_merged)
    
    # R8: Parse satisfaction_score
    def parse_satisfaction(val):
        if pd.isna(val): return np.nan
        try:
            s = int(float(val))
            return s if 1 <= s <= 5 else np.nan
        except:
            return np.nan
    df_merged['satisfaction_score'] = df_merged['satisfaction_score'].apply(parse_satisfaction)
    # Keep rows with missing satisfaction_score
    
    # R9: Parse reopened
    reopened_map = {'yes': 1, 'y': 1, 'true': 1, '1': 1, 'no': 0, 'n': 0, 'false': 0, '0': 0}
    df_merged['reopened'] = df_merged['reopened'].str.lower().map(reopened_map)
    before_reopened_filter = len(df_merged)
    df_merged = df_merged.dropna(subset=['reopened'])
    stats['tickets_invalid_reopened_removed'] = before_reopened_filter - len(df_merged)
    
    # R10: Calculate labor_cost
    df_merged['resolution_minutes'] = df_merged['resolution_minutes'].astype(int)
    df_merged['hourly_cost'] = df_merged['hourly_cost'].astype(float)
    df_merged['labor_cost'] = (df_merged['resolution_minutes'] / 60 * df_merged['hourly_cost']).round(2)
    
    # R11: Final output formatting
    final_cols = ['ticket_id', 'agent_id', 'team', 'region', 'channel', 'resolution_minutes', 'satisfaction_score', 'reopened', 'hourly_cost', 'labor_cost']
    df_final = df_merged[final_cols].copy()
    df_final['reopened'] = df_final['reopened'].astype(int)
    
    # Convert satisfaction_score to nullable integer
    df_final['satisfaction_score'] = df_final['satisfaction_score'].astype('Int64')
    
    # Sort by ticket_id
    df_final = df_final.sort_values('ticket_id')
    
    stats['cleaned_rows'] = len(df_final)
    stats['raw_rows'] = stats['raw_tickets_rows']
    
    # Write outputs
    output_csv_path = os.path.join(output_dir, "cleaned.csv")
    df_final.to_csv(output_csv_path, index=False)
    
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(stats, f, indent=2)

if __name__ == "__main__":
    clean_data()