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
        # Read lines to manually strip whitespace to ensure strict compliance
        lines = f.readlines()
    # Write to a temporary buffer or use pandas directly with skipinitialwhitespace if possible
    # However, pandas read_csv with skipinitialwhitespace=True only skips initial whitespace.
    # Requirement says "Strip whitespace". Let's assume it means leading/trailing for fields.
    # We will process via pandas converters or post-load strip.
    
    # Let's read raw first to handle whitespace stripping manually for robustness
    # Actually, using pandas read_csv with sep=',' and then applying strip is safer for quoted fields.
    
    tickets_raw = pd.read_csv(tickets_path, dtype=str, keep_default_na=False, na_values=na_values)
    agents_raw = pd.read_csv(agents_path, dtype=str, keep_default_na=False, na_values=na_values)
    
    summary['raw_rows_tickets'] = len(tickets_raw)
    summary['raw_rows_agents'] = len(agents_raw)
    
    # Strip whitespace from all string columns
    def strip_df(df):
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.strip()
                # Re-apply NA logic after strip if needed, though pandas did it on read
                df[col] = df[col].replace(na_values, np.nan)
        return df
    
    tickets = strip_df(tickets_raw)
    agents = strip_df(agents_raw)
    
    # R2: Remove duplicate ticket_id, keep first
    tickets = tickets.drop_duplicates(subset='ticket_id', keep='first')
    
    # R3: Normalise agent_id to upper case, remove duplicates
    agents['agent_id'] = agents['agent_id'].str.upper()
    agents = agents.drop_duplicates(subset='agent_id', keep='first')
    
    # R4: Agent roster cleaning
    # Map team
    team_map = {
        'alpha': 'Alpha', 'team alpha': 'Alpha',
        'beta': 'Beta', 'team beta': 'Beta',
        'gamma': 'Gamma', 'team gamma': 'Gamma'
    }
    agents['team_clean'] = agents['team'].str.lower().str.strip().map(team_map)
    
    # Map region
    region_map = {
        'east': 'East', 'e': 'East',
        'west': 'West', 'w': 'West'
    }
    agents['region_clean'] = agents['region'].str.lower().str.strip().map(region_map)
    
    # Parse hourly_cost
    agents['cost_clean'] = agents['hourly_cost'].str.replace(r'[$,USD\s]', '', regex=True)
    agents['cost_clean'] = pd.to_numeric(agents['cost_clean'], errors='coerce')
    
    # Filter valid agents
    agents_valid = agents.dropna(subset=['agent_id', 'team_clean', 'region_clean', 'cost_clean'])
    agents_valid = agents_valid[agents_valid['cost_clean'] > 0]
    
    # Prepare agents for join
    agents_final = agents_valid[['agent_id', 'team_clean', 'region_clean', 'cost_clean']].copy()
    agents_final.columns = ['agent_id', 'team', 'region', 'hourly_cost']
    
    # R5: Tickets agent_id normalise and join
    tickets['agent_id'] = tickets['agent_id'].str.upper()
    tickets_joined = pd.merge(tickets, agents_final, on='agent_id', how='inner')
    
    # R6: Map channel
    channel_map = {
        'email': 'email', 'e-mail': 'email',
        'chat': 'chat', 'live chat': 'chat',
        'phone': 'phone', 'call': 'phone'
    }
    tickets_joined['channel_clean'] = tickets_joined['channel'].str.lower().str.strip().map(channel_map)
    tickets_joined = tickets_joined.dropna(subset=['channel_clean'])
    
    # R7: resolution_minutes
    # Remove 'min' or 'minutes', parse int 1-480
    res_min = tickets_joined['resolution_minutes'].astype(str).str.lower()
    res_min = res_min.str.replace(r'\s*(minutes|min)\s*$', '', regex=True)
    res_min = pd.to_numeric(res_min, errors='coerce')
    tickets_joined['resolution_minutes_clean'] = res_min
    tickets_joined = tickets_joined.dropna(subset=['resolution_minutes_clean'])
    tickets_joined = tickets_joined[
        (tickets_joined['resolution_minutes_clean'] >= 1) & 
        (tickets_joined['resolution_minutes_clean'] <= 480)
    ]
    tickets_joined['resolution_minutes_clean'] = tickets_joined['resolution_minutes_clean'].astype(int)
    
    # R8: satisfaction_score
    sat = pd.to_numeric(tickets_joined['satisfaction_score'], errors='coerce')
    # Valid 1-5, invalid/missing becomes empty (NaN)
    # We check bounds. Note: requirement says "Invalid or missing values become an empty cell and the row is kept."
    # So we only filter if it's out of bounds? Or just coerce errors?
    # "parse a whole number from 1 through 5". If it's outside, it's invalid -> NaN.
    sat = sat.apply(lambda x: x if pd.notna(x) and 1 <= x <= 5 else np.nan)
    tickets_joined['satisfaction_score_clean'] = sat
    # We keep the row even if NaN.
    
    # R9: reopened
    # Map Yes/Y/True/1 -> 1, No/N/False/0 -> 0. Drop invalid/missing.
    reopened_map = {
        'yes': 1, 'y': 1, 'true': 1, '1': 1,
        'no': 0, 'n': 0, 'false': 0, '0': 0
    }
    reopened_clean = tickets_joined['reopened'].astype(str).str.lower().str.strip().map(reopened_map)
    tickets_joined['reopened_clean'] = reopened_clean
    tickets_joined = tickets_joined.dropna(subset=['reopened_clean'])
    tickets_joined['reopened_clean'] = tickets_joined['reopened_clean'].astype(int)
    
    # R10: labor_cost
    tickets_joined['labor_cost'] = (tickets_joined['resolution_minutes_clean'] / 60) * tickets_joined['hourly_cost']
    tickets_joined['labor_cost'] = tickets_joined['labor_cost'].round(2)
    
    # R11: Output formatting
    output_cols = [
        'ticket_id', 'agent_id', 'team', 'region', 'channel_clean', 
        'resolution_minutes_clean', 'satisfaction_score_clean', 'reopened_clean', 
        'hourly_cost', 'labor_cost'
    ]
    
    # Rename columns to final names
    final_df = tickets_joined[output_cols].copy()
    final_df.columns = [
        'ticket_id', 'agent_id', 'team', 'region', 'channel', 
        'resolution_minutes', 'satisfaction_score', 'reopened', 
        'hourly_cost', 'labor_cost'
    ]
    
    # Sort
    final_df = final_df.sort_values('ticket_id')
    
    # Write outputs
    summary['cleaned_rows'] = len(final_df)
    summary['raw_rows'] = summary['raw_rows_tickets'] # Primary raw count
    
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    final_df.to_csv(cleaned_path, index=False)
    
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    clean_data()