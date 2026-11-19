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
    with open(tickets_path, 'r', encoding='utf-8') as f:
        # Skip header, strip whitespace from lines
        lines = f.readlines()
    # Parse manually to ensure whitespace stripping on all fields
    header = [h.strip() for h in lines[0].strip().split(',')]
    data = []
    for line in lines[1:]:
        parts = [p.strip() for p in line.strip().split(',')]
        # Handle potential CSV irregularities if any, though sample suggests simple CSV
        if len(parts) == len(header):
            data.append(parts)
    tickets = pd.DataFrame(data, columns=header)
    # Replace missing indicators
    tickets.replace(na_values, np.nan, inplace=True)
    summary['raw_rows_tickets'] = len(tickets)
    
    # Read agents
    agents_path = os.path.join(input_dir, "agents.csv")
    with open(agents_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    header_a = [h.strip() for h in lines[0].strip().split(',')]
    data_a = []
    for line in lines[1:]:
        parts = [p.strip() for p in line.strip().split(',')]
        if len(parts) == len(header_a):
            data_a.append(parts)
    agents = pd.DataFrame(data_a, columns=header_a)
    agents.replace(na_values, np.nan, inplace=True)
    summary['raw_rows_agents'] = len(agents)
    
    # R2: Remove duplicate ticket_id rows, keep first
    tickets.drop_duplicates(subset='ticket_id', keep='first', inplace=True)
    summary['tickets_after_dedup'] = len(tickets)
    
    # R3: Normalise agent_id to upper case, remove duplicate agent_id rows, keep first
    agents['agent_id'] = agents['agent_id'].str.upper()
    agents.drop_duplicates(subset='agent_id', keep='first', inplace=True)
    summary['agents_after_dedup'] = len(agents)
    
    # R4: Agent roster cleaning
    # Map team
    team_map = {
        'alpha': 'Alpha', 'team alpha': 'Alpha',
        'beta': 'Beta', 'team beta': 'Beta',
        'gamma': 'Gamma', 'team gamma': 'Gamma'
    }
    agents['team'] = agents['team'].str.lower().map(team_map)
    
    # Map region
    region_map = {'east': 'East', 'e': 'East', 'west': 'West', 'w': 'West'}
    agents['region'] = agents['region'].str.lower().map(region_map)
    
    # Parse hourly_cost
    agents['hourly_cost'] = agents['hourly_cost'].astype(str).str.replace('$', '', regex=False).str.replace('USD', '', regex=False).str.replace(',', '', regex=False).str.strip()
    agents['hourly_cost'] = pd.to_numeric(agents['hourly_cost'], errors='coerce')
    
    # Exclude invalid roster rows
    agents_valid = agents.dropna(subset=['agent_id', 'team', 'region', 'hourly_cost']).copy()
    agents_valid = agents_valid[agents_valid['hourly_cost'] > 0]
    summary['agents_valid'] = len(agents_valid)
    
    # R5: Tickets: normalise agent_id, join, drop unmatched
    tickets['agent_id'] = tickets['agent_id'].str.upper()
    # Keep necessary columns from agents
    agents_subset = agents_valid[['agent_id', 'team', 'region', 'hourly_cost']]
    tickets_merged = pd.merge(tickets, agents_subset, on='agent_id', how='inner')
    summary['tickets_after_agent_match'] = len(tickets_merged)
    
    # R6: Map channel
    channel_map = {
        'email': 'email', 'e-mail': 'email',
        'chat': 'chat', 'live chat': 'chat',
        'phone': 'phone', 'call': 'phone'
    }
    tickets_merged['channel'] = tickets_merged['channel'].str.lower().map(channel_map)
    tickets_merged = tickets_merged.dropna(subset=['channel'])
    summary['tickets_after_channel_valid'] = len(tickets_merged)
    
    # R7: resolution_minutes
    # Remove 'min' or 'minutes', parse int 1-480
    tickets_merged['resolution_minutes'] = tickets_merged['resolution_minutes'].astype(str).str.lower().str.replace('minutes', '').str.replace('min', '').str.strip()
    tickets_merged['resolution_minutes'] = pd.to_numeric(tickets_merged['resolution_minutes'], errors='coerce', downcast='integer')
    tickets_merged = tickets_merged[tickets_merged['resolution_minutes'].between(1, 480)]
    summary['tickets_after_resolution_valid'] = len(tickets_merged)
    
    # R8: satisfaction_score
    # Parse int 1-5. Invalid/missing -> empty (NaN), keep row.
    tickets_merged['satisfaction_score'] = pd.to_numeric(tickets_merged['satisfaction_score'], errors='coerce', downcast='integer')
    # Enforce range, set out-of-range to NaN (though prompt says parse, usually implies valid range)
    # Prompt: "parse a whole number from 1 through 5. Invalid or missing values become an empty cell and the row is kept."
    tickets_merged.loc[~tickets_merged['satisfaction_score'].between(1, 5), 'satisfaction_score'] = np.nan
    # We keep the rows (no drop)
    
    # R9: reopened
    # Map Yes/Y/True/1 -> 1, No/N/False/0 -> 0. Drop invalid/missing.
    reopened_map = {
        'yes': 1, 'y': 1, 'true': 1, '1': 1,
        'no': 0, 'n': 0, 'false': 0, '0': 0
    }
    tickets_merged['reopened'] = tickets_merged['reopened'].astype(str).str.lower().map(reopened_map)
    tickets_merged = tickets_merged.dropna(subset=['reopened'])
    tickets_merged['reopened'] = tickets_merged['reopened'].astype(int)
    summary['tickets_after_reopened_valid'] = len(tickets_merged)
    
    # R10: Add labor_cost
    tickets_merged['labor_cost'] = (tickets_merged['resolution_minutes'] / 60 * tickets_merged['hourly_cost']).round(2)
    
    # R11: Output formatting
    final_cols = ['ticket_id', 'agent_id', 'team', 'region', 'channel', 'resolution_minutes', 'satisfaction_score', 'reopened', 'hourly_cost', 'labor_cost']
    # Ensure types
    tickets_merged['ticket_id'] = tickets_merged['ticket_id'].astype(str)
    tickets_merged['agent_id'] = tickets_merged['agent_id'].astype(str)
    tickets_merged['team'] = tickets_merged['team'].astype(str)
    tickets_merged['region'] = tickets_merged['region'].astype(str)
    tickets_merged['channel'] = tickets_merged['channel'].astype(str)
    tickets_merged['resolution_minutes'] = tickets_merged['resolution_minutes'].astype(int)
    # satisfaction_score stays numeric/NaN
    tickets_merged['reopened'] = tickets_merged['reopened'].astype(int)
    tickets_merged['hourly_cost'] = tickets_merged['hourly_cost'].astype(float)
    tickets_merged['labor_cost'] = tickets_merged['labor_cost'].astype(float)
    
    # Sort
    tickets_merged.sort_values('ticket_id', inplace=True)
    
    # Select columns
    output_df = tickets_merged[final_cols]
    
    # Write cleaned.csv
    output_csv_path = os.path.join(output_dir, "cleaned.csv")
    output_df.to_csv(output_csv_path, index=False)
    
    summary['cleaned_rows'] = len(output_df)
    
    # Write cleaning_summary.json
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    clean_data()