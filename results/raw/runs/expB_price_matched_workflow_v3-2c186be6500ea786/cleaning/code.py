import os
import json
import pandas as pd
import numpy as np
import re

def main():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]

    # R1: Read as text, strip whitespace
    tickets_path = os.path.join(input_dir, "tickets.csv")
    agents_path = os.path.join(input_dir, "agents.csv")

    with open(tickets_path, 'r', encoding='utf-8') as f:
        tickets_raw_text = f.read()
    with open(agents_path, 'r', encoding='utf-8') as f:
        agents_raw_text = f.read()

    # Parse CSVs stripping whitespace from cells
    def parse_csv_stripping(text):
        lines = text.strip().split('\n')
        data = [[cell.strip() for cell in line.split(',')] for line in lines]
        header = data[0]
        return pd.DataFrame(data[1:], columns=header)

    tickets_df = parse_csv_stripping(tickets_raw_text)
    agents_df = parse_csv_stripping(agents_raw_text)

    raw_rows_tickets = len(tickets_df)
    raw_rows_agents = len(agents_df)

    # R1: Treat empty, NA, N/A, null, None and - as missing
    missing_vals = ['', 'NA', 'N/A', 'null', 'None', '-']
    tickets_df.replace(missing_vals, np.nan, inplace=True)
    agents_df.replace(missing_vals, np.nan, inplace=True)

    # R2: Remove duplicate ticket_id rows, keep first
    tickets_df.drop_duplicates(subset='ticket_id', keep='first', inplace=True)

    # R3: Normalise agent_id to upper case, remove duplicates
    agents_df['agent_id'] = agents_df['agent_id'].str.upper()
    agents_df.drop_duplicates(subset='agent_id', keep='first', inplace=True)

    # R4: Agent roster cleaning
    # Team mapping
    team_map = {
        'alpha': 'Alpha', 'team alpha': 'Alpha',
        'beta': 'Beta', 'team beta': 'Beta',
        'gamma': 'Gamma', 'team gamma': 'Gamma'
    }
    agents_df['team_norm'] = agents_df['team'].str.lower().map(team_map)
    agents_df.dropna(subset=['team_norm'], inplace=True)
    agents_df['team'] = agents_df['team_norm']
    agents_df.drop(columns=['team_norm'], inplace=True)

    # Region mapping
    region_map = {'east': 'East', 'e': 'East', 'west': 'West', 'w': 'West'}
    agents_df['region_norm'] = agents_df['region'].str.lower().map(region_map)
    agents_df.dropna(subset=['region_norm'], inplace=True)
    agents_df['region'] = agents_df['region_norm']
    agents_df.drop(columns=['region_norm'], inplace=True)

    # Hourly cost parsing
    def parse_cost(val):
        if pd.isna(val): return np.nan
        val_str = str(val)
        val_str = val_str.replace('$', '').replace('USD', '').replace(',', '').strip()
        try:
            return float(val_str)
        except ValueError:
            return np.nan
    
    agents_df['hourly_cost'] = agents_df['hourly_cost'].apply(parse_cost)
    agents_df = agents_df[agents_df['hourly_cost'] > 0]

    # R5: Tickets agent_id normalise and join
    tickets_df['agent_id'] = tickets_df['agent_id'].str.upper()
    # Inner join drops tickets without matching agent
    df = pd.merge(tickets_df, agents_df[['agent_id', 'team', 'region', 'hourly_cost']], on='agent_id', how='inner')

    # R6: Channel mapping
    channel_map = {
        'email': 'email', 'e-mail': 'email',
        'chat': 'chat', 'live chat': 'chat',
        'phone': 'phone', 'call': 'phone'
    }
    df['channel_norm'] = df['channel'].str.lower().map(channel_map)
    df.dropna(subset=['channel_norm'], inplace=True)
    df['channel'] = df['channel_norm']
    df.drop(columns=['channel_norm'], inplace=True)

    # R7: resolution_minutes
    def parse_minutes(val):
        if pd.isna(val): return np.nan
        val_str = str(val).lower().replace('min', '').replace('minutes', '').strip()
        try:
            minutes = int(float(val_str))
            if 1 <= minutes <= 480:
                return minutes
        except ValueError:
            pass
        return np.nan

    df['resolution_minutes'] = df['resolution_minutes'].apply(parse_minutes)
    df.dropna(subset=['resolution_minutes'], inplace=True)

    # R8: satisfaction_score
    def parse_satisfaction(val):
        if pd.isna(val): return np.nan
        try:
            score = int(float(val))
            if 1 <= score <= 5:
                return score
        except ValueError:
            pass
        return np.nan

    df['satisfaction_score'] = df['satisfaction_score'].apply(parse_satisfaction)
    # Keep rows with NaN satisfaction_score

    # R9: reopened
    reopened_map = {
        'yes': 1, 'y': 1, 'true': 1, '1': 1,
        'no': 0, 'n': 0, 'false': 0, '0': 0
    }
    df['reopened_norm'] = df['reopened'].str.lower().map(reopened_map)
    df.dropna(subset=['reopened_norm'], inplace=True)
    df['reopened'] = df['reopened_norm'].astype(int)
    df.drop(columns=['reopened_norm'], inplace=True)

    # R10: labor_cost
    df['labor_cost'] = (df['resolution_minutes'] / 60 * df['hourly_cost']).round(2)

    # R11: Output schema and sorting
    final_cols = ['ticket_id', 'agent_id', 'team', 'region', 'channel', 
                  'resolution_minutes', 'satisfaction_score', 'reopened', 
                  'hourly_cost', 'labor_cost']
    
    df = df[final_cols]
    df.sort_values(by='ticket_id', inplace=True)

    # Write cleaned CSV
    output_csv_path = os.path.join(output_dir, "cleaned.csv")
    df.to_csv(output_csv_path, index=False)

    # Write cleaning summary JSON
    summary = {
        'raw_rows': raw_rows_tickets,
        'cleaned_rows': len(df),
        'agents_raw': raw_rows_agents,
        'agents_cleaned': len(agents_df)
    }
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    main()
