import os
import json
import pandas as pd
import numpy as np

def clean_data():
    input_dir = os.environ.get('INPUT_DIR', '.')
    output_dir = os.environ.get('OUTPUT_DIR', '.')
    
    summary = {
        'raw_rows_tickets': 0,
        'raw_rows_agents': 0,
        'cleaned_rows': 0,
        'duplicates_removed_tickets': 0,
        'duplicates_removed_agents': 0,
        'invalid_agents_dropped': 0,
        'invalid_channels_dropped': 0,
        'invalid_resolution_dropped': 0,
        'invalid_reopened_dropped': 0
    }
    
    # R1: Read files and handle missing values
    missing_values = ['', 'NA', 'N/A', 'null', 'None', '-']
    
    tickets_path = os.path.join(input_dir, 'tickets.csv')
    agents_path = os.path.join(input_dir, 'agents.csv')
    
    # Read tickets
    with open(tickets_path, 'r') as f:
        tickets_raw = f.read()
    
    # Read agents
    with open(agents_path, 'r') as f:
        agents_raw = f.read()
    
    # Strip whitespace from all fields
    tickets_lines = [line.strip() for line in tickets_raw.strip().split('\n')]
    agents_lines = [line.strip() for line in agents_raw.strip().split('\n')]
    
    # Parse CSV manually to handle whitespace properly
    def parse_csv(lines):
        result = []
        for line in lines:
            fields = [f.strip() for f in line.split(',')]
            result.append(fields)
        return result
    
    tickets_data = parse_csv(tickets_lines)
    agents_data = parse_csv(agents_lines)
    
    tickets_headers = tickets_data[0]
    agents_headers = agents_data[0]
    
    tickets_df = pd.DataFrame(tickets_data[1:], columns=tickets_headers)
    agents_df = pd.DataFrame(agents_data[1:], columns=agents_headers)
    
    summary['raw_rows_tickets'] = len(tickets_df)
    summary['raw_rows_agents'] = len(agents_df)
    
    # Replace missing values with NaN
    tickets_df = tickets_df.replace(missing_values, np.nan)
    agents_df = agents_df.replace(missing_values, np.nan)
    
    # R2: Remove duplicate ticket_id rows, keep first
    before_dedup = len(tickets_df)
    tickets_df = tickets_df.drop_duplicates(subset='ticket_id', keep='first')
    summary['duplicates_removed_tickets'] = before_dedup - len(tickets_df)
    
    # R3: Normalize agent_id to upper case and remove duplicates in agents
    agents_df['agent_id'] = agents_df['agent_id'].str.upper()
    before_dedup = len(agents_df)
    agents_df = agents_df.drop_duplicates(subset='agent_id', keep='first')
    summary['duplicates_removed_agents'] = before_dedup - len(agents_df)
    
    # R4: Clean agent roster
    # Map team case-insensitively
    team_mapping = {
        'alpha': 'Alpha', 'team alpha': 'Alpha',
        'beta': 'Beta', 'team beta': 'Beta',
        'gamma': 'Gamma', 'team gamma': 'Gamma'
    }
    agents_df['team'] = agents_df['team'].str.lower().str.strip()
    agents_df['team'] = agents_df['team'].map(team_mapping)
    
    # Map region
    region_mapping = {
        'east': 'East', 'e': 'East',
        'west': 'West', 'w': 'West'
    }
    agents_df['region'] = agents_df['region'].str.lower().str.strip()
    agents_df['region'] = agents_df['region'].map(region_mapping)
    
    # Parse hourly_cost
    agents_df['hourly_cost'] = agents_df['hourly_cost'].str.replace('$', '', regex=False)
    agents_df['hourly_cost'] = agents_df['hourly_cost'].str.replace('USD', '', regex=False)
    agents_df['hourly_cost'] = agents_df['hourly_cost'].str.replace(',', '', regex=False)
    agents_df['hourly_cost'] = agents_df['hourly_cost'].str.strip()
    agents_df['hourly_cost'] = pd.to_numeric(agents_df['hourly_cost'], errors='coerce')
    
    # Exclude roster rows with invalid field or cost <= 0
    valid_agents_mask = (
        agents_df['agent_id'].notna() &
        agents_df['team'].notna() &
        agents_df['region'].notna() &
        agents_df['hourly_cost'].notna() &
        (agents_df['hourly_cost'] > 0)
    )
    agents_df = agents_df[valid_agents_mask].copy()
    
    # R5: Normalize agent_id in tickets and join
    tickets_df['agent_id'] = tickets_df['agent_id'].str.upper()
    
    before_join = len(tickets_df)
    tickets_df = tickets_df.merge(agents_df[['agent_id', 'team', 'region', 'hourly_cost']], 
                                   on='agent_id', how='inner')
    summary['invalid_agents_dropped'] = before_join - len(tickets_df)
    
    # R6: Map channel
    channel_mapping = {
        'email': 'email', 'e-mail': 'email',
        'chat': 'chat', 'live chat': 'chat',
        'phone': 'phone', 'call': 'phone'
    }
    tickets_df['channel'] = tickets_df['channel'].str.lower().str.strip()
    tickets_df['channel'] = tickets_df['channel'].map(channel_mapping)
    
    before_filter = len(tickets_df)
    tickets_df = tickets_df[tickets_df['channel'].notna()].copy()
    summary['invalid_channels_dropped'] = before_filter - len(tickets_df)
    
    # R7: Parse resolution_minutes
    tickets_df['resolution_minutes'] = tickets_df['resolution_minutes'].str.lower().str.strip()
    tickets_df['resolution_minutes'] = tickets_df['resolution_minutes'].str.replace('min', '', regex=False)
    tickets_df['resolution_minutes'] = tickets_df['resolution_minutes'].str.replace('minutes', '', regex=False)
    tickets_df['resolution_minutes'] = tickets_df['resolution_minutes'].str.strip()
    tickets_df['resolution_minutes'] = pd.to_numeric(tickets_df['resolution_minutes'], errors='coerce')
    
    before_filter = len(tickets_df)
    valid_resolution_mask = (
        tickets_df['resolution_minutes'].notna() &
        (tickets_df['resolution_minutes'] >= 1) &
        (tickets_df['resolution_minutes'] <= 480)
    )
    tickets_df = tickets_df[valid_resolution_mask].copy()
    tickets_df['resolution_minutes'] = tickets_df['resolution_minutes'].astype(int)
    summary['invalid_resolution_dropped'] = before_filter - len(tickets_df)
    
    # R8: Parse satisfaction_score (keep rows with invalid/missing, set to empty)
    tickets_df['satisfaction_score'] = pd.to_numeric(tickets_df['satisfaction_score'], errors='coerce')
    valid_sat_mask = (
        tickets_df['satisfaction_score'].notna() &
        (tickets_df['satisfaction_score'] >= 1) &
        (tickets_df['satisfaction_score'] <= 5)
    )
    tickets_df.loc[~valid_sat_mask, 'satisfaction_score'] = np.nan
    tickets_df.loc[valid_sat_mask, 'satisfaction_score'] = tickets_df.loc[valid_sat_mask, 'satisfaction_score'].astype(int)
    
    # R9: Parse reopened
    reopened_mapping = {
        'yes': 1, 'y': 1, 'true': 1, '1': 1,
        'no': 0, 'n': 0, 'false': 0, '0': 0
    }
    tickets_df['reopened'] = tickets_df['reopened'].str.lower().str.strip()
    tickets_df['reopened'] = tickets_df['reopened'].map(reopened_mapping)
    
    before_filter = len(tickets_df)
    tickets_df = tickets_df[tickets_df['reopened'].notna()].copy()
    tickets_df['reopened'] = tickets_df['reopened'].astype(int)
    summary['invalid_reopened_dropped'] = before_filter - len(tickets_df)
    
    # R10: Calculate labor_cost
    tickets_df['labor_cost'] = (tickets_df['resolution_minutes'] / 60 * tickets_df['hourly_cost']).round(2)
    
    # R11: Select and order columns, sort by ticket_id
    output_columns = ['ticket_id', 'agent_id', 'team', 'region', 'channel', 
                      'resolution_minutes', 'satisfaction_score', 'reopened', 
                      'hourly_cost', 'labor_cost']
    tickets_df = tickets_df[output_columns].copy()
    tickets_df = tickets_df.sort_values('ticket_id')
    
    summary['cleaned_rows'] = len(tickets_df)
    
    # Write cleaned CSV
    output_csv_path = os.path.join(output_dir, 'cleaned.csv')
    tickets_df.to_csv(output_csv_path, index=False)
    
    # Write cleaning summary JSON
    summary_path = os.path.join(output_dir, 'cleaning_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    clean_data()