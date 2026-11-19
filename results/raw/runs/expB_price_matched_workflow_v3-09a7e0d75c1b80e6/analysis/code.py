import os
import json
import pandas as pd
import numpy as np

# Configuration
INPUT_FILE = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
OUTPUT_FILE = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

def main():
    # Read cleaned data
    # Schema: ticket_id, agent_id, team, region, channel, resolution_minutes, 
    # satisfaction_score, reopened, hourly_cost, labor_cost
    df = pd.read_csv(INPUT_FILE)
    
    # Initialize results dictionary
    results = {}
    
    # --- Q1: Overall Metrics ---
    results['ticket_count'] = len(df)
    results['mean_resolution_minutes'] = df['resolution_minutes'].mean()
    results['total_labor_cost'] = df['labor_cost'].sum()
    
    # --- Q2: Team Comparison ---
    team_costs = df.groupby('team')['labor_cost'].sum()
    results['labor_cost_alpha'] = team_costs.get('Alpha', 0.0)
    results['labor_cost_beta'] = team_costs.get('Beta', 0.0)
    results['labor_cost_gamma'] = team_costs.get('Gamma', 0.0)
    
    # --- Q3: Channel Comparison ---
    channel_resolution = df.groupby('channel')['resolution_minutes'].mean()
    results['resolution_email'] = channel_resolution.get('email', np.nan)
    results['resolution_chat'] = channel_resolution.get('chat', np.nan)
    results['resolution_phone'] = channel_resolution.get('phone', np.nan)
    
    # --- Q4: Reopening Change ---
    # Calculate reopen rate per channel
    reopen_stats = df.groupby('channel')['reopened'].agg(['sum', 'count'])
    
    # Email stats
    email_reopened = reopen_stats.loc['email', 'sum'] if 'email' in reopen_stats.index else 0
    email_total = reopen_stats.loc['email', 'count'] if 'email' in reopen_stats.index else 0
    email_reopen_rate = (email_reopened / email_total * 100) if email_total > 0 else 0.0
    
    # Chat stats
    chat_reopened = reopen_stats.loc['chat', 'sum'] if 'chat' in reopen_stats.index else 0
    chat_total = reopen_stats.loc['chat', 'count'] if 'chat' in reopen_stats.index else 0
    chat_reopen_rate = (chat_reopened / chat_total * 100) if chat_total > 0 else 0.0
    
    results['reopen_rate_email_pct'] = email_reopen_rate
    results['reopen_rate_chat_pct'] = chat_reopen_rate
    
    # Email vs chat reopen change: (email - chat) / chat * 100
    if chat_reopen_rate != 0:
        results['email_vs_chat_reopen_change_pct'] = (email_reopen_rate - chat_reopen_rate) / chat_reopen_rate * 100
    else:
        results['email_vs_chat_reopen_change_pct'] = 0.0
    
    # --- Q5: High-cost Low-satisfaction Segment ---
    # Tickets with labor_cost >= 100 AND non-missing satisfaction_score <= 2
    high_cost_low_sat = df[(df['labor_cost'] >= 100) & (df['satisfaction_score'].notna()) & (df['satisfaction_score'] <= 2)]
    results['high_cost_low_sat_count'] = len(high_cost_low_sat)
    
    if len(high_cost_low_sat) > 0:
        results['high_cost_low_sat_reopen_pct'] = high_cost_low_sat['reopened'].mean() * 100
    else:
        results['high_cost_low_sat_reopen_pct'] = 0.0
    
    # --- Q6: Distribution ---
    results['resolution_median'] = df['resolution_minutes'].median()
    # Sample standard deviation (ddof=1)
    results['resolution_std'] = df['resolution_minutes'].std(ddof=1)
    
    # Mean of non-missing satisfaction_score
    valid_satisfaction = df['satisfaction_score'].dropna()
    results['satisfaction_mean'] = valid_satisfaction.mean() if len(valid_satisfaction) > 0 else np.nan
    
    # Count of missing satisfaction_score
    results['satisfaction_missing_count'] = df['satisfaction_score'].isna().sum()
    
    # --- Q7: Agent Concentration ---
    results['unique_agent_count'] = df['agent_id'].nunique()
    
    agent_ticket_counts = df['agent_id'].value_counts()
    results['top_agent_ticket_count'] = agent_ticket_counts.iloc[0] if len(agent_ticket_counts) > 0 else 0
    
    if results['ticket_count'] > 0:
        results['top_agent_ticket_share_pct'] = results['top_agent_ticket_count'] / results['ticket_count'] * 100
    else:
        results['top_agent_ticket_share_pct'] = 0.0
    
    # Write results to JSON
    # Ensure all values are JSON serializable (convert numpy types to native Python types)
    results_clean = {}
    for k, v in results.items():
        if pd.isna(v):
            # Should not happen based on requirements, but handle gracefully
            results_clean[k] = None
        elif isinstance(v, (np.integer, np.int64, np.int32)):
            results_clean[k] = int(v)
        elif isinstance(v, (np.floating, np.float64, np.float32)):
            results_clean[k] = float(v)
        else:
            results_clean[k] = v
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results_clean, f)

if __name__ == "__main__":
    main()
