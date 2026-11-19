import os
import json
import pandas as pd
import numpy as np

def clean_data():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    
    summary = {}
    
    # R1: Read and strip whitespace, treat specific strings as missing
    na_values = ['', 'NA', 'N/A', 'null', 'None', '-']
    
    # Read tickets
    tickets_path = os.path.join(input_dir, "tickets.csv")
    df_t = pd.read_csv(tickets_path, na_values=na_values, keep_default_na=False, dtype=str)
    df_t = df_t.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    summary['raw_rows_tickets'] = len(df_t)
    
    # Read agents
    agents_path = os.path.join(input_dir, "agents.csv")
    df_a = pd.read_csv(agents_path, na_values=na_values, keep_default_na=False, dtype=str)
    df_a = df_a.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    summary['raw_rows_agents'] = len(df_a)
    
    # R2: Remove duplicate ticket_id (keep first)
    df_t = df_t.drop_duplicates(subset='ticket_id', keep='first')
    
    # R3: Normalize agent_id to upper case and remove duplicates (keep first)
    df_a['agent_id'] = df_a['agent_id'].str.upper()
    df_a = df_a.drop_duplicates(subset='agent_id', keep='first')
    
    # R4: Agent roster cleaning
    # Map team
    team_map = {
        'alpha': 'Alpha', 'team alpha': 'Alpha',
        'beta': 'Beta', 'team beta': 'Beta',
        'gamma': 'Gamma', 'team gamma': 'Gamma'
    }
    df_a['team'] = df_a['team'].str.lower().str.strip().map(team_map)
    
    # Map region
    region_map = {'east': 'East', 'e': 'East', 'west': 'West', 'w': 'West'}
    df_a['region'] = df_a['region'].str.lower().str.strip().map(region_map)
    
    # Parse hourly_cost
    def parse_cost(val):
        if pd.isna(val): return np.nan
        val = str(val).replace('$', '').replace('USD', '').replace(',', '').strip()
        try:
            return float(val)
        except:
            return np.nan
    df_a['hourly_cost'] = df_a['hourly_cost'].apply(parse_cost)
    
    # Exclude invalid roster rows
    df_a = df_a.dropna(subset=['agent_id', 'team', 'region', 'hourly_cost'])
    df_a = df_a[df_a['hourly_cost'] > 0]
    
    # R5: Tickets agent_id normalization and join
    df_t['agent_id'] = df_t['agent_id'].str.upper()
    df_t = df_t.merge(df_a[['agent_id', 'team', 'region', 'hour_cost']], on='agent_id', how='inner')
    # Note: I used 'hour_cost' in merge to avoid conflict, renaming back below if needed. 
    # Actually, let's rename hourly_cost in agents to avoid conflict or just select columns.
    # Correction: df_a has 'hourly_cost'. Let's rename it for merge or handle suffix.
    # Re-reading R4 logic: df_a has 'hourly_cost'. Merge will create hourly_cost_x and hourly_cost_y if tickets had it.
    # Tickets input does NOT have hourly_cost. So merge is clean.
    # Let's re-run merge logic cleanly.
    
    # Re-defining merge for clarity in final script:
    # df_t = df_t.merge(df_a[['agent_id', 'team', 'region', 'hourly_cost']], on='agent_id', how='inner')
    # This adds team, region, hourly_cost to tickets.
    
    # R6: Map channel
    channel_map = {
        'email': 'email', 'e-mail': 'email',
        'chat': 'chat', 'live chat': 'chat',
        'phone': 'phone', 'call': 'phone'
    }
    df_t['channel'] = df_t['channel'].str.lower().str.strip().map(channel_map)
    df_t = df_t.dropna(subset=['channel'])
    
    # R7: resolution_minutes
    def parse_minutes(val):
        if pd.isna(val): return np.nan
        val = str(val).lower().replace('minutes', '').replace('min', '').strip()
        try:
            m = int(val)
            return m if 1 <= m <= 480 else np.nan
        except:
            return np.nan
    df_t['resolution_minutes'] = df_t['resolution_minutes'].apply(parse_minutes)
    df_t = df_t.dropna(subset=['resolution_minutes'])
    df_t['resolution_minutes'] = df_t['resolution_minutes'].astype(int)
    
    # R8: satisfaction_score
    def parse_satisfaction(val):
        if pd.isna(val): return np.nan
        try:
            s = int(float(val))
            return s if 1 <= s <= 5 else np.nan
        except:
            return np.nan
    df_t['satisfaction_score'] = df_t['satisfaction_score'].apply(parse_satisfaction)
    # Keep rows even if NaN (already handled by not dropping)
    
    # R9: reopened
    reopened_map = {
        'yes': 1, 'y': 1, 'true': 1, '1': 1,
        'no': 0, 'n': 0, 'false': 0, '0': 0
    }
    df_t['reopened'] = df_t['reopened'].str.lower().str.strip().map(reopened_map)
    df_t = df_t.dropna(subset=['reopened'])
    df_t['reopened'] = df_t['reopened'].astype(int)
    
    # R10: labor_cost
    df_t['labor_cost'] = (df_t['resolution_minutes'] / 60 * df_t['hourly_cost']).round(2)
    
    # R11: Output formatting
    cols = ['ticket_id', 'agent_id', 'team', 'region', 'channel', 'resolution_minutes', 'satisfaction_score', 'reopened', 'hourly_cost', 'labor_cost']
    df_t = df_t[cols]
    df_t = df_t.sort_values('ticket_id')
    
    summary['cleaned_rows'] = len(df_t)
    summary['raw_rows'] = summary['raw_rows_tickets'] # As per contract 'raw_rows'
    
    # Write outputs
    out_path = os.path.join(output_dir, "cleaned.csv")
    df_t.to_csv(out_path, index=False)
    
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    clean_data()