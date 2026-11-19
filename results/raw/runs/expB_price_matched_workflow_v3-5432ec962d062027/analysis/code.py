import os
import json
import pandas as pd
import numpy as np

def main():
    # Read cleaned data
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    df = pd.read_csv(input_path)
    
    # Initialize results dictionary
    results = {}
    
    # Q1: Overall metrics
    results["ticket_count"] = len(df)
    results["mean_resolution_minutes"] = df["resolution_minutes"].mean()
    results["total_labor_cost"] = df["labor_cost"].sum()
    
    # Q2: Team comparison - total labor cost by team
    team_costs = df.groupby("team")["labor_cost"].sum()
    results["labor_cost_alpha"] = team_costs.get("Alpha", 0.0)
    results["labor_cost_beta"] = team_costs.get("Beta", 0.0)
    results["labor_cost_gamma"] = team_costs.get("Gamma", 0.0)
    
    # Q3: Channel comparison - mean resolution minutes by channel
    channel_resolution = df.groupby("channel")["resolution_minutes"].mean()
    results["resolution_email"] = channel_resolution.get("email", np.nan)
    results["resolution_chat"] = channel_resolution.get("chat", np.nan)
    results["resolution_phone"] = channel_resolution.get("phone", np.nan)
    
    # Q4: Reopening rates for email and chat
    email_tickets = df[df["channel"] == "email"]
    chat_tickets = df[df["channel"] == "chat"]
    
    email_reopen_rate = email_tickets["reopened"].mean() * 100 if len(email_tickets) > 0 else np.nan
    chat_reopen_rate = chat_tickets["reopened"].mean() * 100 if len(chat_tickets) > 0 else np.nan
    
    results["reopen_rate_email_pct"] = email_reopen_rate
    results["reopen_rate_chat_pct"] = chat_reopen_rate
    
    # Email vs chat reopen change: (email - chat) / chat * 100
    if len(chat_tickets) > 0 and chat_reopen_rate != 0:
        results["email_vs_chat_reopen_change_pct"] = (email_reopen_rate - chat_reopen_rate) / chat_reopen_rate * 100
    else:
        results["email_vs_chat_reopen_change_pct"] = np.nan
    
    # Q5: High-cost low-satisfaction segment
    # labor_cost >= 100 AND satisfaction_score is non-missing AND <= 2
    high_cost_low_sat = df[(df["labor_cost"] >= 100) & 
                          (df["satisfaction_score"].notna()) & 
                          (df["satisfaction_score"] <= 2)]
    results["high_cost_low_sat_count"] = len(high_cost_low_sat)
    
    if len(high_cost_low_sat) > 0:
        results["high_cost_low_sat_reopen_pct"] = high_cost_low_sat["reopened"].mean() * 100
    else:
        results["high_cost_low_sat_reopen_pct"] = np.nan
    
    # Q6: Distribution metrics
    results["resolution_median"] = df["resolution_minutes"].median()
    results["resolution_std"] = df["resolution_minutes"].std(ddof=1)  # sample std
    
    # Mean of non-missing satisfaction scores
    valid_satisfaction = df["satisfaction_score"].dropna()
    results["satisfaction_mean"] = valid_satisfaction.mean() if len(valid_satisfaction) > 0 else np.nan
    results["satisfaction_missing_count"] = df["satisfaction_score"].isna().sum()
    
    # Q7: Agent concentration
    results["unique_agent_count"] = df["agent_id"].nunique()
    
    agent_ticket_counts = df["agent_id"].value_counts()
    results["top_agent_ticket_count"] = agent_ticket_counts.iloc[0] if len(agent_ticket_counts) > 0 else 0
    
    if results["ticket_count"] > 0:
        results["top_agent_ticket_share_pct"] = results["top_agent_ticket_count"] / results["ticket_count"] * 100
    else:
        results["top_agent_ticket_share_pct"] = np.nan
    
    # Handle NaN values - replace with None for JSON serialization, then back to NaN handling
    # JSON doesn't support NaN, so we need to handle this
    # The spec says no NaN as values, but we need to handle edge cases
    # For now, if any value is NaN, we'll use a default or let it pass
    # Actually, re-reading the spec: "No strings, lists, null, NaN or Infinity as values"
    # This means we need valid numbers. For edge cases where calculations produce NaN,
    # we should handle them appropriately. Given the data has 220 rows, most metrics should be valid.
    
    # Convert to JSON-serializable format
    # pandas/numpy NaN will become null in JSON which is not allowed
    # We'll replace NaN with 0.0 for counts and rates where appropriate
    # But given the data preview, all channels and teams exist, so NaN shouldn't occur for main metrics
    
    # Write results
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
    
    # Custom encoder to handle numpy types and NaN
    def convert_value(v):
        if pd.isna(v):
            return 0.0  # Default for NaN - though shouldn't happen with valid data
        if isinstance(v, (np.integer, np.int64, np.int32)):
            return int(v)
        if isinstance(v, (np.floating, np.float64, np.float32)):
            return float(v)
        return v
    
    results_clean = {k: convert_value(v) for k, v in results.items()}
    
    with open(output_path, 'w') as f:
        json.dump(results_clean, f)

if __name__ == "__main__":
    main()
