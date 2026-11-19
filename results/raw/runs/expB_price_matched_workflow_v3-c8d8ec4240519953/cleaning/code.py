import os
import json
import pandas as pd
import numpy as np

def clean_data():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    
    summary = {}
    
    # R1: Read both files as text, strip whitespace
    tickets_path = os.path.join(input_dir, "tickets.csv")
    agents_path = os.path.join(input_dir, "agents.csv")
    
    tickets_df = pd.read_csv(tickets_path, dtype=str).applymap(lambda x: x.strip() if isinstance(x, str) else x)
    agents_df = pd.read_csv(agents_path, dtype=str).applymap(lambda x: x.strip() if isinstance(x, str) else x)
    
    summary['raw_rows_tickets'] = len(tickets_df)
    summary['raw_rows_agents'] = len(agents_df)
    
    # R1: Treat empty, NA, N/A, null, None and - as missing
    missing_vals = ['', 'NA', 'N/A', 'null', 'None', '-', np.nan]
    tickets_df = tickets_df.replace(missing_vals, np.nan)
    agents_df = agents_df.replace(missing_vals, np.nan)
    
    # R2: Remove duplicate ticket_id rows, keep first
    before_dedup = len(tickets_df)
    tickets_df = tickets_df.drop_duplicates(subset='ticket_id', keep='first')
    summary['r2_tickets_dropped_duplicates'] = before_dedup - len(tickets_df)
    
    # R3: Normalise agent_id to upper case, remove duplicates (keep first)
    agents_df['agent_id'] = agents_df['agent_id'].str.upper()
    before_agent_dedup = len(agents_df)
    agents_df = agents_df.drop_duplicates(subset='agent_id', keep='first')
    summary['r3_agents_dropped_duplicates'] = before_agent_dedup - len(agents_df)
    
    # R4: Agent roster mappings
    # Map team
    team_map = {
        'alpha': 'Alpha', 'team alpha': 'Alpha',
        'beta': 'Beta', 'team beta': 'Beta',
        'gamma': 'Gamma', 'team gamma': 'Gamma'
    }
    agents_df['team'] = agents_df['team'].str.lower().map(team_map)
    
    # Map region
    region_map = {'east': 'East', 'e': 'East', 'west': 'West', 'w': 'West'}
    agents_df['region'] = agents_df['region'].str.lower().map(region_map)
    
    # Parse hourly_cost
    agents_df['hourly_cost'] = agents_df['hourly_cost'].str.replace('$', '', regex=False)
    agents_df['hourly_cost'] = agents_df['hourly_cost'].str.replace('USD', '', regex=False)
    agents_df['hourly_cost'] = agents_df['hourly_cost'].str.replace(',', '', regex=False)
    agents_df['hourly_cost'] = pd.to_numeric(agents_df['hourly_cost'], errors='coerce')
    
    # Exclude roster rows with invalid field or cost <= 0
    before_r4 = len(agents_df)
    agents_df = agents_df.dropna(subset=['agent_id', 'team', 'region', 'hourly_cost'])
    agents_df = agents_df[agents_df['hourly_cost'] > 0]
    summary['r4_agents_excluded'] = before_r4 - len(agents_df)
    
    # R5: Tickets - normalise agent_id, join, drop unmatched
    tickets_df['agent_id'] = tickets_df['agent_id'].str.upper()
    before_join = len(tickets_df)
    tickets_df = tickets_df.merge(agents_df[['agent_id', 'team', 'region', 'hourly_cost']], on='agent_id', how='inner')
    summary['r5_tickets_dropped_no_agent'] = before_join - len(tickets_df)
    
    # R6: Map channel
    channel_map = {
        'email': 'email', 'e-mail': 'email',
        'chat': 'chat', 'live chat': 'chat',
        'phone': 'phone', 'call': 'phone'
    }
    tickets_df['channel'] = tickets_df['channel'].str.lower().map(channel_map)
    before_r6 = len(tickets_df)
    tickets_df = tickets_df.dropna(subset=['channel'])
    summary['r6_tickets_dropped_invalid_channel'] = before_r6 - len(tickets_df)
    
    # R7: resolution_minutes
    tickets_df['resolution_minutes'] = tickets_df['resolution_minutes'].str.lower().str.replace('min', '', regex=False).str.replace('utes', '', regex=False).str.strip()
    tickets_df['resolution_minutes'] = pd.to_numeric(tickets_df['resolution_minutes'], errors='coerce')
    before_r7 = len(tickets_df)
    tickets_df = tickets_df.dropna(subset=['resolution_minutes'])
    tickets_df['resolution_minutes'] = tickets_df['resolution_minutes'].astype(int)
    tickets_df = tickets_df[(tickets_df['resolution_minutes'] >= 1) & (tickets_df['resolution_minutes'] <= 480)]
    summary['r7_tickets_dropped_invalid_minutes'] = before_r7 - len(tickets_df)
    
    # R8: satisfaction_score
    tickets_df['satisfaction_score'] = pd.to_numeric(tickets_df['satisfaction_score'], errors='coerce')
    # Keep rows, set invalid to NaN, then filter range
    tickets_df.loc[~tickets_df['satisfaction_score'].isin([1, 2, 3, 4, 5]), 'satisfaction_score'] = np.nan
    # R8 says keep row, so no drop. Just ensure it's numeric/NaN.
    
    # R9: reopened
    reopened_map = {'yes': 1, 'y': 1, 'true': 1, '1': 1, 'no': 0, 'n': 0, 'false': 0, '0': 0}
    tickets_df['reopened'] = tickets_df['reopened'].astype(str).str.lower().map(reopened_map)
    before_r9 = len(tickets_df)
    tickets_df = tickets_df.dropna(subset=['reopened'])
    summary['r9_tickets_dropped_invalid_reopened'] = before_r9 - len(tickets_df)
    tickets_df['reopened'] = tickets_df['reopened'].astype(int)
    
    # R10: labor_cost
    tickets_df['labor_cost'] = (tickets_df['resolution_minutes'] / 60 * tickets_df['hourly_cost']).round(2)
    
    # R11: Output columns and sort
    output_cols = ['ticket_id', 'agent_id', 'team', 'region', 'channel', 'resolution_minutes', 'satisfaction_score', 'reopened', 'hourly_cost', 'labor_cost']
    tickets_df = tickets_df[output_cols]
    tickets_df = tickets_df.sort_values('ticket_id')
    
    # Write cleaned CSV
    output_path = os.path.join(output_dir, "cleaned.csv")
    tickets_df.to_csv(output_path, index=False)
    
    summary['cleaned_rows'] = len(tickets_df)
    summary['raw_rows'] = summary['raw_rows_tickets']
    
    # Write summary JSON
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    clean_data()