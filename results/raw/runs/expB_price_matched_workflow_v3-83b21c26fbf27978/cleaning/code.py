import os
import json
import pandas as pd
import numpy as np

def clean_data():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    
    summary = {}
    
    # R1: Read files and strip whitespace, treat specific strings as missing
    na_values = ['', 'NA', 'N/A', 'null', 'None', '-']
    
    tickets_path = os.path.join(input_dir, "tickets.csv")
    agents_path = os.path.join(input_dir, "agents.csv")
    
    # Read tickets
    with open(tickets_path, 'r') as f:
        tickets_raw = f.read()
    
    # Read agents
    with open(agents_path, 'r') as f:
        agents_raw = f.read()
    
    # Parse with pandas, stripping whitespace
    from io import StringIO
    df_tickets = pd.read_csv(StringIO(tickets_raw), skipinitialspace=True, na_values=na_values, keep_default_na=False)
    df_agents = pd.read_csv(StringIO(agents_raw), skipinitialspace=True, na_values=na_values, keep_default_na=False)
    
    # Strip whitespace from string columns
    for df in [df_tickets, df_agents]:
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].str.strip()
                # Replace empty strings with NaN for consistency
                df[col] = df[col].replace('', np.nan)
    
    summary['raw_rows_tickets'] = len(df_tickets)
    summary['raw_rows_agents'] = len(df_agents)
    
    # R2: Remove duplicate ticket_id, keep first
    before_dedup = len(df_tickets)
    df_tickets = df_tickets.drop_duplicates(subset='ticket_id', keep='first')
    summary['tickets_dropped_duplicates'] = before_dedup - len(df_tickets)
    
    # R3: Normalise agent_id to upper case and remove duplicates in agents
    df_agents['agent_id'] = df_agents['agent_id'].str.upper()
    before_agent_dedup = len(df_agents)
    df_agents = df_agents.drop_duplicates(subset='agent_id', keep='first')
    summary['agents_dropped_duplicates'] = before_agent_dedup - len(df_agents)
    
    # R4: Agent roster mapping and validation
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
    df_agents['hourly_cost'] = df_agents['hourly_cost'].astype(str).str.replace(r'[$,]', '', regex=True).str.replace('USD', '').str.strip()
    df_agents['hourly_cost'] = pd.to_numeric(df_agents['hourly_cost'], errors='coerce')
    
    # Exclude invalid roster rows
    before_roster_filter = len(df_agents)
    valid_roster_mask = (
        df_agents['agent_id'].notna() &
        df_agents['team'].notna() &
        df_agents['region'].notna() &
        df_agents['hourly_cost'].notna() &
        (df_agents['hourly_cost'] > 0)
    )
    df_agents = df_agents[valid_roster_mask].copy()
    summary['agents_invalid_rows'] = before_roster_filter - len(df_agents)
    
    # R5: Tickets agent_id normalise and join
    df_tickets['agent_id'] = df_tickets['agent_id'].str.upper()
    before_join = len(df_tickets)
    df_merged = pd.merge(df_tickets, df_agents[['agent_id', 'team', 'region', 'hourly_cost']], on='agent_id', how='inner')
    summary['tickets_dropped_no_agent'] = before_join - len(df_merged)
    
    # R6: Map channel
    channel_map = {
        'email': 'email', 'e-mail': 'email',
        'chat': 'chat', 'live chat': 'chat',
        'phone': 'phone', 'call': 'phone'
    }
    df_merged['channel'] = df_merged['channel'].str.lower().map(channel_map)
    before_channel = len(df_merged)
    df_merged = df_merged[df_merged['channel'].notna()].copy()
    summary['tickets_dropped_invalid_channel'] = before_channel - len(df_merged)
    
    # R7: resolution_minutes
    df_merged['resolution_minutes'] = (
        df_merged['resolution_minutes'].astype(str)
        .str.lower()
        .str.replace(r'minutes', '', regex=False)
        .str.replace(r'min', '', regex=False)
        .str.strip()
    )
    df_merged['resolution_minutes'] = pd.to_numeric(df_merged['resolution_minutes'], errors='coerce')
    before_res = len(df_merged)
    valid_res_mask = df_merged['resolution_minutes'].notna() & (df_merged['resolution_minutes'] >= 1) & (df_merged['resolution_minutes'] <= 480)
    df_merged = df_merged[valid_res_mask].copy()
    df_merged['resolution_minutes'] = df_merged['resolution_minutes'].astype(int)
    summary['tickets_dropped_invalid_resolution'] = before_res - len(df_merged)
    
    # R8: satisfaction_score
    df_merged['satisfaction_score'] = pd.to_numeric(df_merged['satisfaction_score'], errors='coerce')
    # Keep rows, but invalidate scores outside 1-5
    invalid_sat_mask = df_merged['satisfaction_score'].notna() & ((df_merged['satisfaction_score'] < 1) | (df_merged['satisfaction_score'] > 5))
    df_merged.loc[invalid_sat_mask, 'satisfaction_score'] = np.nan
    # Convert valid ones to int (nullable integer)
    # We'll handle type later to avoid issues with NaNs before final output
    
    # R9: reopened
    reopened_map = {'yes': 1, 'y': 1, 'true': 1, '1': 1, 'no': 0, 'n': 0, 'false': 0, '0': 0}
    df_merged['reopened'] = df_merged['reopened'].astype(str).str.lower().map(reopened_map)
    before_reopened = len(df_merged)
    df_merged = df_merged[df_merged['reopened'].notna()].copy()
    summary['tickets_dropped_invalid_reopened'] = before_reopened - len(df_merged)
    df_merged['reopened'] = df_merged['reopened'].astype(int)
    
    # R10: labor_cost
    df_merged['hourly_cost'] = df_merged['hourly_cost'].astype(float)
    df_merged['labor_cost'] = (df_merged['resolution_minutes'] / 60 * df_merged['hourly_cost']).round(2)
    
    # R11: Output formatting
    final_cols = ['ticket_id', 'agent_id', 'team', 'region', 'channel', 'resolution_minutes', 'satisfaction_score', 'reopened', 'hourly_cost', 'labor_cost']
    df_final = df_merged[final_cols].copy()
    
    # Sort
    df_final = df_final.sort_values('ticket_id')
    
    # Type conversions for output
    df_final['ticket_id'] = df_final['ticket_id'].astype(str)
    df_final['agent_id'] = df_final['agent_id'].astype(str)
    df_final['team'] = df_final['team'].astype('category')
    df_final['region'] = df_final['region'].astype('category')
    df_final['channel'] = df_final['channel'].astype('category')
    df_final['resolution_minutes'] = df_final['resolution_minutes'].astype(int)
    # satisfaction_score: nullable int
    df_final['satisfaction_score'] = df_final['satisfaction_score'].astype('Int64') # Pandas nullable integer
    df_final['reopened'] = df_final['reopened'].astype(int)
    df_final['hourly_cost'] = df_final['hourly_cost'].round(2)
    df_final['labor_cost'] = df_final['labor_cost'].round(2)
    
    summary['cleaned_rows'] = len(df_final)
    summary['raw_rows'] = summary['raw_rows_tickets']
    
    # Write outputs
    output_csv_path = os.path.join(output_dir, "cleaned.csv")
    output_json_path = os.path.join(output_dir, "cleaning_summary.json")
    
    df_final.to_csv(output_csv_path, index=False)
    
    with open(output_json_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    clean_data()