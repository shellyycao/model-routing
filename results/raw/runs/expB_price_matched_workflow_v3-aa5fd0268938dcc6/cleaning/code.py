import os
import json
import pandas as pd
import numpy as np

def clean_data():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    
    summary = {}
    
    # R1: Read both files as text, strip whitespace, treat specific strings as missing
    na_values = ['', 'NA', 'N/A', 'null', 'None', '-']
    
    # Read tickets
    tickets_path = os.path.join(input_dir, "tickets.csv")
    with open(tickets_path, 'r') as f:
        # Read lines to strip whitespace manually per field if needed, 
        # but pandas read_csv with skipinitialspace and strip handles most cases.
        # We implement strict stripping by reading raw and processing.
        pass
    
    # Using pandas with converters/strip for robustness
    tickets_df = pd.read_csv(tickets_path, skipinitialspace=True, dtype=str)
    # Strip all string columns
    for col in tickets_df.columns:
        tickets_df[col] = tickets_df[col].astype(str).str.strip()
    tickets_df.replace(na_values, np.nan, inplace=True)
    summary['raw_rows_tickets'] = len(tickets_df)
    
    # Read agents
    agents_path = os.path.join(input_dir, "agents.csv")
    agents_df = pd.read_csv(agents_path, skipinitialspace=True, dtype=str)
    for col in agents_df.columns:
        agents_df[col] = agents_df[col].astype(str).str.strip()
    agents_df.replace(na_values, np.nan, inplace=True)
    summary['raw_rows_agents'] = len(agents_df)
    
    # R2: Remove duplicate ticket_id, keep first
    tickets_df.drop_duplicates(subset='ticket_id', keep='first', inplace=True)
    
    # R3: Normalise agent_id to upper case, remove duplicates (agents)
    agents_df['agent_id'] = agents_df['agent_id'].str.upper()
    agents_df.drop_duplicates(subset='agent_id', keep='first', inplace=True)
    
    # R4: Agent roster cleaning
    # Map team
    team_map = {
        'alpha': 'Alpha', 'team alpha': 'Alpha',
        'beta': 'Beta', 'team beta': 'Beta',
        'gamma': 'Gamma', 'team gamma': 'Gamma'
    }
    agents_df['team'] = agents_df['team'].str.lower().map(team_map)
    
    # Map region
    region_map = {
        'east': 'East', 'e': 'East',
        'west': 'West', 'w': 'West'
    }
    agents_df['region'] = agents_df['region'].str.lower().map(region_map)
    
    # Parse hourly_cost
    agents_df['hourly_cost'] = agents_df['hourly_cost'].str.replace('$', '', regex=False)
    agents_df['hourly_cost'] = agents_df['hourly_cost'].str.replace('USD', '', regex=False)
    agents_df['hourly_cost'] = agents_df['hourly_cost'].str.replace(',', '', regex=False)
    agents_df['hourly_cost'] = pd.to_numeric(agents_df['hourly_cost'], errors='coerce')
    
    # Exclude invalid roster rows
    # Valid fields: team, region not null. cost > 0 and not null.
    valid_agents_mask = (
        agents_df['team'].notna() & 
        agents_df['region'].notna() & 
        agents_df['hourly_cost'].notna() & 
        (agents_df['hourly_cost'] > 0)
    )
    agents_df = agents_df[valid_agents_mask].copy()
    summary['valid_agents'] = len(agents_df)
    
    # R5: Tickets agent_id normalise and join
    tickets_df['agent_id'] = tickets_df['agent_id'].str.upper()
    # We only need specific columns from agents for the join
    agents_clean = agents_df[['agent_id', 'team', 'region', 'hourly_cost']].copy()
    
    # Inner join to drop tickets without matching agent
    merged_df = pd.merge(tickets_df, agents_clean, on='agent_id', how='inner')
    summary['tickets_after_join'] = len(merged_df)
    
    # R6: Map channel
    channel_map = {
        'email': 'email', 'e-mail': 'email',
        'chat': 'chat', 'live chat': 'chat',
        'phone': 'phone', 'call': 'phone'
    }
    merged_df['channel'] = merged_df['channel'].str.lower().map(channel_map)
    # Drop invalid channels
    merged_df = merged_df[merged_df['channel'].notna()].copy()
    summary['tickets_after_channel'] = len(merged_df)
    
    # R7: resolution_minutes
    merged_df['resolution_minutes'] = merged_df['resolution_minutes'].str.lower()
    merged_df['resolution_minutes'] = merged_df['resolution_minutes'].str.replace('min', '', regex=False)
    merged_df['resolution_minutes'] = merged_df['resolution_minutes'].str.replace('utes', '', regex=False) # handles 'minutes'
    merged_df['resolution_minutes'] = merged_df['resolution_minutes'].str.strip()
    merged_df['resolution_minutes'] = pd.to_numeric(merged_df['resolution_minutes'], errors='coerce')
    # Validate range 1-480, drop invalid
    merged_df = merged_df[
        merged_df['resolution_minutes'].notna() & 
        (merged_df['resolution_minutes'] >= 1) & 
        (merged_df['resolution_minutes'] <= 480)
    ].copy()
    merged_df['resolution_minutes'] = merged_df['resolution_minutes'].astype(int)
    summary['tickets_after_resolution'] = len(merged_df)
    
    # R8: satisfaction_score
    merged_df['satisfaction_score'] = pd.to_numeric(merged_df['satisfaction_score'], errors='coerce')
    # Validate range 1-5. Invalid becomes NaN (empty cell), row kept.
    merged_df['satisfaction_score'] = merged_df['satisfaction_score'].apply(
        lambda x: int(x) if pd.notna(x) and 1 <= x <= 5 else np.nan
    )
    
    # R9: reopened
    reopened_map = {
        'yes': 1, 'y': 1, 'true': 1, '1': 1,
        'no': 0, 'n': 0, 'false': 0, '0': 0
    }
    merged_df['reopened'] = merged_df['reopened'].str.lower().map(reopened_map)
    # Drop invalid or missing
    merged_df = merged_df[merged_df['reopened'].notna()].copy()
    merged_df['reopened'] = merged_df['reopened'].astype(int)
    summary['tickets_after_reopened'] = len(merged_df)
    
    # R10: labor_cost
    # hourly_cost is already float from agent merge
    merged_df['hourly_cost'] = merged_df['hourly_cost'].astype(float)
    merged_df['labor_cost'] = (merged_df['resolution_minutes'] / 60 * merged_df['hourly_cost']).round(2)
    
    # R11: Output formatting
    final_cols = [
        'ticket_id', 'agent_id', 'team', 'region', 'channel', 
        'resolution_minutes', 'satisfaction_score', 'reopened', 
        'hourly_cost', 'labor_cost'
    ]
    final_df = merged_df[final_cols].copy()
    
    # Sort by ticket_id
    # Extract numeric part for correct sorting if mixed, but spec implies simple sort.
    # Assuming ticket_id string sort is acceptable or extracting number.
    # Let's sort by string as per 'Sort by ticket_id'.
    final_df.sort_values(by='ticket_id', inplace=True)
    
    # Write outputs
    os.makedirs(output_dir, exist_ok=True)
    output_csv_path = os.path.join(output_dir, "cleaned.csv")
    final_df.to_csv(output_csv_path, index=False)
    
    summary['cleaned_rows'] = len(final_df)
    summary['raw_rows'] = summary['raw_rows_tickets'] # Primary raw count
    
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    clean_data()