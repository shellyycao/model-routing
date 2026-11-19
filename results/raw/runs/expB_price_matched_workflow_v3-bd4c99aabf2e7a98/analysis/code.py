import os
import json
import pandas as pd
import numpy as np

def run_analysis():
    # Define paths
    input_file = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_file = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
    
    # Read cleaned data
    # The cleaning stage ensures correct types for most columns, but we cast to be safe.
    # dates are read as objects (strings) by default in CSV unless parsed.
    df = pd.read_csv(input_file)
    
    # Parse signup_date to datetime for cohort analysis
    df['signup_date'] = pd.to_datetime(df['signup_date'])
    
    # Initialize results dictionary
    results = {}
    
    # --- Q1: Overall Aggregation ---
    customer_count = len(df)
    results['customer_count'] = customer_count
    
    churn_rate = (df['churned'].sum() / customer_count) * 100
    results['churn_rate_pct'] = churn_rate
    
    avg_monthly_fee = df['monthly_fee'].mean()
    results['avg_monthly_fee'] = avg_monthly_fee
    
    # --- Q2: Churn by Plan ---
    plan_groups = df.groupby('plan')
    for plan in ['Basic', 'Standard', 'Premium']:
        if plan in plan_groups.groups:
            plan_df = plan_groups.get_group(plan)
            rate = (plan_df['churned'].sum() / len(plan_df)) * 100
        else:
            rate = 0.0 # Should not happen per schema, but safe fallback
        key = f'churn_rate_{plan.lower()}_pct'
        results[key] = rate
    
    # --- Q3: Churn by Signup Cohort ---
    df['signup_year'] = df['signup_date'].dt.year
    year_groups = df.groupby('signup_year')
    
    for year in [2021, 2022, 2023, 2024]:
        if year in year_groups.groups:
            year_df = year_groups.get_group(year)
            rate = (year_df['churned'].sum() / len(year_df)) * 100
        else:
            rate = 0.0
        key = f'churn_rate_cohort_{year}_pct'
        results[key] = rate
        
    # --- Q4: Contract Effect ---
    contract_groups = df.groupby('contract_type')
    
    # Monthly
    if 'Monthly' in contract_groups.groups:
        monthly_df = contract_groups.get_group('Monthly')
        churn_monthly = (monthly_df['churned'].sum() / len(monthly_df)) * 100
    else:
        churn_monthly = 0.0
    results['churn_rate_monthly_pct'] = churn_monthly
    
    # Annual
    if 'Annual' in contract_groups.groups:
        annual_df = contract_groups.get_group('Annual')
        churn_annual = (annual_df['churned'].sum() / len(annual_df)) * 100
    else:
        churn_annual = 0.0
    results['churn_rate_annual_pct'] = churn_annual
    
    # Relative difference
    if churn_annual != 0:
        change = (churn_monthly - churn_annual) / churn_annual * 100
    else:
        change = 0.0 # Avoid division by zero
    results['churn_monthly_vs_annual_change_pct'] = change
    
    # --- Q5: At-risk Segment ---
    # Filter: support_tickets >= 5 AND satisfaction_score <= 2 (and not missing)
    at_risk_df = df[(df['support_tickets'] >= 5) & (df['satisfaction_score'].notna()) & (df['satisfaction_score'] <= 2)]
    
    at_risk_count = len(at_risk_df)
    results['at_risk_customer_count'] = at_risk_count
    
    if at_risk_count > 0:
        at_risk_churn = (at_risk_df['churned'].sum() / at_risk_count) * 100
    else:
        at_risk_churn = 0.0
    results['at_risk_churn_rate_pct'] = at_risk_churn
    
    # --- Q6: Tenure and Satisfaction Summary ---
    # Tenure
    results['tenure_mean'] = df['tenure_months'].mean()
    results['tenure_median'] = df['tenure_months'].median()
    results['tenure_std'] = df['tenure_months'].std(ddof=1) # Sample std dev
    
    # Satisfaction
    sat_valid = df['satisfaction_score'].dropna()
    results['satisfaction_mean'] = sat_valid.mean()
    results['satisfaction_missing_count'] = df['satisfaction_score'].isna().sum()
    
    # --- Q7: Lifetime Value by Plan ---
    ltv_basic = df[df['plan'] == 'Basic']['lifetime_value'].mean()
    ltv_standard = df[df['plan'] == 'Standard']['lifetime_value'].mean()
    ltv_premium = df[df['plan'] == 'Premium']['lifetime_value'].mean()
    
    results['ltv_basic'] = ltv_basic
    results['ltv_standard'] = ltv_standard
    results['ltv_premium'] = ltv_premium
    
    if ltv_basic != 0:
        ltv_change = (ltv_premium - ltv_basic) / ltv_basic * 100
    else:
        ltv_change = 0.0
    results['premium_vs_basic_ltv_change_pct'] = ltv_change
    
    # Write results to JSON
    # Ensure all values are JSON serializable (convert numpy types to native python types)
    results_serializable = {k: float(v) if isinstance(v, (np.floating, np.integer)) else v for k, v in results.items()}
    
    with open(output_file, 'w') as f:
        json.dump(results_serializable, f)

if __name__ == "__main__":
    run_analysis()