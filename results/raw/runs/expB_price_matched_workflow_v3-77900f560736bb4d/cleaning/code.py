import os
import json
import pandas as pd
import numpy as np

def main():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    
    # R1: Read and strip whitespace, treat specific values as missing
    na_values = ['', 'NA', 'N/A', 'null', 'None', '-']
    
    tickets_path = os.path.join(input_dir, "tickets.csv")
    agents_path = os.path.join(input_dir, "agents.csv")
    
    # Read tickets
    df_tickets = pd.read_csv(tickets_path, na_values=na_values, keep_default_na=False, dtype=str)
    df_tickets = df_tickets.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    raw_ticket_rows = len(df_tickets)
    
    # Read agents
    df_agents = pd.read_csv(agents_path, na_values=na_values, keep_default_na=False, dtype=str)
    df_agents = df_agents.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    raw_agent_rows = len(df_agents)
    
    # R2: Remove duplicate ticket_id rows, keep first
    df_tickets = df_tickets.drop_duplicates(subset='ticket_id', keep='first')
    
    # R3: Normalize agent_id to upper case, remove duplicate agent_id rows, keep first
    df_agents['agent_id'] = df_agents['agent_id'].str.upper()
    df_agents = df_agents.drop_duplicates(subset='agent_id', keep='first')
    
    # R4: Clean agent roster
    # Map team case-insensitively
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
        val = str(val).replace('$', '').replace('USD', '').replace(',', '').strip()
        try: return float(val)
        except: return np.nan
    df_agents['hourly_cost'] = df_agents['hourly_cost'].apply(parse_cost)
    
    # Exclude roster rows with invalid field or cost <= 0
    # Valid team: not null, valid region: not null, valid cost: not null and > 0
    valid_agents_mask = (
        df_agents['team'].notna() & 
        df_agents['region'].notna() & 
        df_agents['hourly_cost'].notna() & 
        (df_agents['hourly_cost'] > 0)
    )
    df_agents = df_agents[valid_agents_mask].copy()
    
    # R5: Normalize ticket agent_id and join
    df_tickets['agent_id'] = df_tickets['agent_id'].str.upper()
    df_tickets = df_tickets.merge(df_agents[['agent_id', 'team', 'region', 'hourly_cost']], 
                                  on='agent_id', how='inner')
    
    # R6: Map channel
    channel_map = {
        'email': 'email', 'e-mail': 'email',
        'chat': 'chat', 'live chat': 'chat',
        'phone': 'phone', 'call': 'phone'
    }
    df_tickets['channel'] = df_tickets['channel'].str.lower().map(channel_map)
    df_tickets = df_tickets[df_tickets['channel'].notna()].copy()
    
    # R7: resolution_minutes
    def parse_minutes(val):
        if pd.isna(val): return np.nan
        val = str(val).lower().replace('min', '').replace('utes', '').strip() # handles 'min' and 'minutes'
        try:
            mins = int(val)
            return mins if 1 <= mins <= 480 else np.nan
        except:
            return np.nan
    df_tickets['resolution_minutes'] = df_tickets['resolution_minutes'].apply(parse_minutes)
    df_tickets = df_tickets[df_tickets['resolution_minutes'].notna()].copy()
    
    # R8: satisfaction_score
    def parse_satisfaction(val):
        if pd.isna(val): return np.nan
        try:
            score = int(float(val))
            return score if 1 <= score <= 5 else np.nan
        except:
            return np.nan
    df_tickets['satisfaction_score'] = df_tickets['satisfaction_score'].apply(parse_satisfaction)
    # Keep rows even if satisfaction is NaN (requirement says "row is kept")
    
    # R9: reopened
    reopened_map = {
        'yes': 1, 'y': 1, 'true': 1, '1': 1,
        'no': 0, 'n': 0, 'false': 0, '0': 0
    }
    df_tickets['reopened'] = df_tickets['reopened'].str.lower().map(reopened_map)
    # Drop invalid or missing values
    df_tickets = df_tickets[df_tickets['reopened'].notna()].copy()
    
    # R10: Calculate labor_cost
    # resolution_minutes is float currently (from NaN handling logic), cast to int
    df_tickets['resolution_minutes'] = df_tickets['resolution_minutes'].astype(int)
    df_tickets['hourly_cost'] = df_tickets['hourly_cost'].astype(float)
    df_tickets['labor_cost'] = (df_tickets['resolution_minutes'] / 60 * df_tickets['hourly_cost']).round(2)
    
    # R11: Output formatting
    # Cast types
    df_tickets['reopened'] = df_tickets['reopened'].astype(int)
    # satisfaction_score should be nullable integer (float with NaNs or Int64), but output schema says int nullable. 
    # Pandas usually outputs float for nullable int in CSV, or empty string. We will keep as float for now to allow NaNs.
    # Schema: satisfaction_score: int; nullable.
    
    final_cols = ['ticket_id', 'agent_id', 'team', 'region', 'channel', 
                  'resolution_minutes', 'satisfaction_score', 'reopened', 
                  'hourly_cost', 'labor_cost']
    
    df_final = df_tickets[final_cols].sort_values('ticket_id')
    
    # Write cleaned CSV
    output_csv_path = os.path.join(output_dir, "cleaned.csv")
    df_final.to_csv(output_csv_path, index=False)
    
    # Write cleaning summary
    summary = {
        'raw_rows': raw_ticket_rows,
        'cleaned_rows': len(df_final),
        'raw_agent_rows': raw_agent_rows,
        'cleaned_agent_rows': len(df_agents)
    }
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    main()
