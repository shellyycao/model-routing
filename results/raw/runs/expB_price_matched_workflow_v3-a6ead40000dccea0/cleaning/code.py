import os
import json
import pandas as pd
import numpy as np

def main():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    
    # R1: Read as text, strip whitespace
    tickets_path = os.path.join(input_dir, "tickets.csv")
    agents_path = os.path.join(input_dir, "agents.csv")
    
    with open(tickets_path, 'r', encoding='utf-8') as f:
        tickets_text = f.read()
    with open(agents_path, 'r', encoding='utf-8') as f:
        agents_text = f.read()
    
    # Helper to normalize missing values
    missing_values = ['', 'NA', 'N/A', 'null', 'None', '-']
    
    def normalize_missing(df):
        # Strip whitespace from string columns
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].str.strip()
                df[col] = df[col].replace(missing_values, np.nan)
        return df
    
    # Parse CSVs
    from io import StringIO
    tickets_df = pd.read_csv(StringIO(tickets_text))
    agents_df = pd.read_csv(StringIO(agents_text))
    
    raw_tickets_rows = len(tickets_df)
    raw_agents_rows = len(agents_df)
    
    tickets_df = normalize_missing(tickets_df)
    agents_df = normalize_missing(agents_df)
    
    # R2: Remove duplicate ticket_id rows, keep first
    tickets_df = tickets_df.drop_duplicates(subset=['ticket_id'], keep='first')
    
    # R3: Normalize agent_id to upper case, remove duplicates
    agents_df['agent_id'] = agents_df['agent_id'].str.upper()
    agents_df = agents_df.drop_duplicates(subset=['agent_id'], keep='first')
    
    # R4: Agent roster cleaning
    # Map team case-insensitively
    team_map = {
        'alpha': 'Alpha', 'team alpha': 'Alpha',
        'beta': 'Beta', 'team beta': 'Beta',
        'gamma': 'Gamma', 'team gamma': 'Gamma'
    }
    agents_df['team_lower'] = agents_df['team'].str.lower().fillna('')
    agents_df['team'] = agents_df['team_lower'].map(team_map)
    
    # Map region
    region_map = {'east': 'East', 'e': 'East', 'west': 'West', 'w': 'West'}
    agents_df['region_lower'] = agents_df['region'].str.lower().fillna('')
    agents_df['region'] = agents_df['region_lower'].map(region_map)
    
    # Parse hourly_cost
    agents_df['hourly_cost'] = agents_df['hourly_cost'].astype(str).str.replace('$', '', regex=False)
    agents_df['hourly_cost'] = agents_df['hourly_cost'].str.replace('USD', '', regex=False)
    agents_df['hourly_cost'] = agents_df['hourly_cost'].str.replace(',', '', regex=False)
    agents_df['hourly_cost'] = pd.to_numeric(agents_df['hourly_cost'], errors='coerce')
    
    # Exclude invalid roster rows
    agents_df = agents_df.dropna(subset=['agent_id', 'team', 'region', 'hourly_cost'])
    agents_df = agents_df[agents_df['hourly_cost'] > 0]
    
    # R5: Tickets - normalize agent_id, join, drop unmatched
    tickets_df['agent_id'] = tickets_df['agent_id'].str.upper()
    tickets_df = tickets_df.merge(agents_df[['agent_id', 'team', 'region', 'hourly_cost']], 
                                   on='agent_id', how='inner')
    
    # R6: Map channel
    channel_map = {
        'email': 'email', 'e-mail': 'email',
        'chat': 'chat', 'live chat': 'chat',
        'phone': 'phone', 'call': 'phone'
    }
    tickets_df['channel_lower'] = tickets_df['channel'].str.lower().fillna('')
    tickets_df['channel'] = tickets_df['channel_lower'].map(channel_map)
    tickets_df = tickets_df.dropna(subset=['channel'])
    
    # R7: resolution_minutes
    tickets_df['resolution_minutes'] = tickets_df['resolution_minutes'].astype(str).str.lower()
    tickets_df['resolution_minutes'] = tickets_df['resolution_minutes'].str.replace('min', '', regex=False)
    tickets_df['resolution_minutes'] = tickets_df['resolution_minutes'].str.replace('utes', '', regex=False)
    tickets_df['resolution_minutes'] = tickets_df['resolution_minutes'].str.strip()
    tickets_df['resolution_minutes'] = pd.to_numeric(tickets_df['resolution_minutes'], errors='coerce')
    tickets_df['resolution_minutes'] = tickets_df['resolution_minutes'].astype('Int64')
    tickets_df = tickets_df[(tickets_df['resolution_minutes'] >= 1) & (tickets_df['resolution_minutes'] <= 480)]
    tickets_df['resolution_minutes'] = tickets_df['resolution_minutes'].astype(int)
    
    # R8: satisfaction_score
    tickets_df['satisfaction_score'] = pd.to_numeric(tickets_df['satisfaction_score'], errors='coerce')
    tickets_df['satisfaction_score'] = tickets_df['satisfaction_score'].astype('Int64')
    tickets_df.loc[~tickets_df['satisfaction_score'].between(1, 5), 'satisfaction_score'] = pd.NA
    
    # R9: reopened
    reopened_map = {'yes': 1, 'y': 1, 'true': 1, '1': 1, 'no': 0, 'n': 0, 'false': 0, '0': 0}
    tickets_df['reopened_lower'] = tickets_df['reopened'].astype(str).str.lower().fillna('')
    tickets_df['reopened'] = tickets_df['reopened_lower'].map(reopened_map)
    tickets_df = tickets_df.dropna(subset=['reopened'])
    tickets_df['reopened'] = tickets_df['reopened'].astype(int)
    
    # R10: labor_cost
    tickets_df['labor_cost'] = (tickets_df['resolution_minutes'] / 60 * tickets_df['hourly_cost']).round(2)
    
    # R11: Output columns
    output_cols = ['ticket_id', 'agent_id', 'team', 'region', 'channel', 
                   'resolution_minutes', 'satisfaction_score', 'reopened', 
                   'hourly_cost', 'labor_cost']
    tickets_df = tickets_df[output_cols]
    tickets_df = tickets_df.sort_values('ticket_id')
    
    # Write cleaned CSV
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    tickets_df.to_csv(cleaned_path, index=False)
    
    # Write cleaning summary
    summary = {
        "raw_rows": raw_tickets_rows,
        "cleaned_rows": len(tickets_df),
        "raw_agents_rows": raw_agents_rows,
        "cleaned_agents_rows": len(agents_df)
    }
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    main()
