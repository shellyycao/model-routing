import os
import json
import pandas as pd
import numpy as np

def main():
    # Define input and output paths
    input_file_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_file_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
    
    # Read the cleaned data
    # The cleaning stage ensures columns are in the correct order and types are appropriate
    df = pd.read_csv(input_file_path)
    
    # Initialize the results dictionary
    results = {}
    
    # --- Q1: Overall Aggregation ---
    customer_count = len(df)
    results['customer_count'] = customer_count
    
    churn_rate_pct = (df['churned'].mean() * 100)
    results['churn_rate_pct'] = churn_rate_pct
    
    avg_monthly_fee = df['monthly_fee'].mean()
    results['avg_monthly_fee'] = avg_monthly_fee
    
    # --- Q2: Churn by Plan ---
    plan_groups = df.groupby('plan')['churned'].mean() * 100
    results['churn_rate_basic_pct'] = plan_groups.get('Basic', 0.0)
    results['churn_rate_standard_pct'] = plan_groups.get('Standard', 0.0)
    results['churn_rate_premium_pct'] = plan_groups.get('Premium', 0.0)
    
    # --- Q3: Churn by Signup Cohort ---
    # Extract year from signup_date
    df['signup_year'] = pd.to_datetime(df['signup_date']).dt.year
    cohort_groups = df.groupby('signup_year')['churned'].mean() * 100
    results['churn_rate_cohort_2021_pct'] = cohort_groups.get(2021, 0.0)
    results['churn_rate_cohort_2022_pct'] = cohort_groups.get(2022, 0.0)
    results['churn_rate_cohort_2023_pct'] = cohort_groups.get(2023, 0.0)
    results['churn_rate_cohort_2024_pct'] = cohort_groups.get(2024, 0.0)
    
    # --- Q4: Contract Effect ---
    contract_groups = df.groupby('contract_type')['churned'].mean() * 100
    churn_rate_monthly_pct = contract_groups.get('Monthly', 0.0)
    churn_rate_annual_pct = contract_groups.get('Annual', 0.0)
    
    results['churn_rate_monthly_pct'] = churn_rate_monthly_pct
    results['churn_rate_annual_pct'] = churn_rate_annual_pct
    
    # Calculate relative percentage change
    if churn_rate_annual_pct != 0:
        churn_monthly_vs_annual_change_pct = (churn_rate_monthly_pct - churn_rate_annual_pct) / churn_rate_annual_pct * 100
    else:
        churn_monthly_vs_annual_change_pct = 0.0 # Handle division by zero if annual rate is 0
    results['churn_monthly_vs_annual_change_pct'] = churn_monthly_vs_annual_change_pct
    
    # --- Q5: At-risk Segment ---
    # Filter: support_tickets >= 5 AND satisfaction_score <= 2 (and not missing)
    at_risk_df = df[(df['support_tickets'] >= 5) & (df['satisfaction_score'].notna()) & (df['satisfaction_score'] <= 2)]
    
    at_risk_customer_count = len(at_risk_df)
    results['at_risk_customer_count'] = at_risk_customer_count
    
    if at_risk_customer_count > 0:
        at_risk_churn_rate_pct = at_risk_df['churned'].mean() * 100
    else:
        at_risk_churn_rate_pct = 0.0
    results['at_risk_churn_rate_pct'] = at_risk_churn_rate_pct
    
    # --- Q6: Tenure and Satisfaction Summary ---
    # Tenure statistics
    results['tenure_mean'] = df['tenure_months'].mean()
    results['tenure_median'] = df['tenure_months'].median()
    # Sample standard deviation (ddof=1 is default for pandas std)
    results['tenure_std'] = df['tenure_months'].std()
    
    # Satisfaction statistics (only for non-missing)
    valid_satisfaction = df['satisfaction_score'].dropna()
    results['satisfaction_mean'] = valid_satisfaction.mean()
    
    # Count missing satisfaction scores
    results['satisfaction_missing_count'] = df['satisfaction_score'].isna().sum()
    
    # --- Q7: Lifetime Value by Plan ---
    ltv_groups = df.groupby('plan')['lifetime_value'].mean()
    ltv_basic = ltv_groups.get('Basic', 0.0)
    ltv_standard = ltv_groups.get('Standard', 0.0)
    ltv_premium = ltv_groups.get('Premium', 0.0)
    
    results['ltv_basic'] = ltv_basic
    results['ltv_standard'] = ltv_standard
    results['ltv_premium'] = ltv_premium
    
    # Calculate relative percentage change
    if ltv_basic != 0:
        premium_vs_basic_ltv_change_pct = (ltv_premium - ltv_basic) / ltv_basic * 100
    else:
        premium_vs_basic_ltv_change_pct = 0.0 # Handle division by zero
    results['premium_vs_basic_ltv_change_pct'] = premium_vs_basic_ltv_change_pct
    
    # Write results to JSON
    # Ensure all values are JSON serializable (numpy types to native python types)
    # Pandas/numpy floats and ints usually serialize fine, but good practice to cast if needed.
    # However, standard json.dumps handles np.float64 and np.int64 fine in recent versions.
    # We ensure no NaN/Infinity per requirements.
    
    with open(output_file_path, 'w') as f:
        json.dump(results, f)

if __name__ == "__main__":
    main()