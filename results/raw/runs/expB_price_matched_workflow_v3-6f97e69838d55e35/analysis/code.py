import os
import json
import pandas as pd
import numpy as np

def main():
    # Define input and output paths
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    input_file = os.path.join(input_dir, "cleaned.csv")
    output_file = os.path.join(output_dir, "findings.json")

    # Read cleaned data
    # The schema specifies columns and types. 
    # customer_id: str, signup_date: date (object for parsing), plan/contract_type: category (object), 
    # monthly_fee: float, tenure_months: int, support_tickets: int, 
    # satisfaction_score: Int64 (nullable int), churned: int, lifetime_value: float.
    df = pd.read_csv(input_file)

    # Ensure correct dtypes for calculations
    df['signup_date'] = pd.to_datetime(df['signup_date'])
    df['satisfaction_score'] = pd.to_numeric(df['satisfaction_score'], errors='coerce').astype('Int64')
    
    findings = {}

    # --- Q1: Overall Aggregation ---
    customer_count = len(df)
    findings['customer_count'] = customer_count
    
    churn_rate = df['churned'].mean() * 100
    findings['churn_rate_pct'] = churn_rate
    
    avg_monthly_fee = df['monthly_fee'].mean()
    findings['avg_monthly_fee'] = avg_monthly_fee

    # --- Q2: Churn by Plan ---
    plan_churn = df.groupby('plan')['churned'].mean() * 100
    findings['churn_rate_basic_pct'] = plan_churn.get('Basic', 0.0)
    findings['churn_rate_standard_pct'] = plan_churn.get('Standard', 0.0)
    findings['churn_rate_premium_pct'] = plan_churn.get('Premium', 0.0)

    # --- Q3: Churn by Signup Cohort ---
    df['signup_year'] = df['signup_date'].dt.year
    cohort_churn = df.groupby('signup_year')['churned'].mean() * 100
    # Using get with default 0.0 in case a year is missing in data
    findings['churn_rate_cohort_2021_pct'] = cohort_churn.get(2021, 0.0)
    findings['churn_rate_cohort_2022_pct'] = cohort_churn.get(2022, 0.0)
    findings['churn_rate_cohort_2023_pct'] = cohort_churn.get(2023, 0.0)
    findings['churn_rate_cohort_2024_pct'] = cohort_churn.get(2024, 0.0)

    # --- Q4: Contract Effect ---
    contract_churn = df.groupby('contract_type')['churned'].mean() * 100
    churn_rate_monthly = contract_churn.get('Monthly', 0.0)
    churn_rate_annual = contract_churn.get('Annual', 0.0)
    
    findings['churn_rate_monthly_pct'] = churn_rate_monthly
    findings['churn_rate_annual_pct'] = churn_rate_annual
    
    # Relative difference calculation
    if churn_rate_annual != 0:
        monthly_vs_annual_change = (churn_rate_monthly - churn_rate_annual) / churn_rate_annual * 100
    else:
        monthly_vs_annual_change = 0.0 # Or handle as appropriate if annual is 0
    findings['churn_monthly_vs_annual_change_pct'] = monthly_vs_annual_change

    # --- Q5: At-risk Segment ---
    # Filter: support_tickets >= 5 AND satisfaction_score <= 2 (non-missing)
    at_risk_df = df[(df['support_tickets'] >= 5) & (df['satisfaction_score'].notna() & (df['satisfaction_score'] <= 2))]
    
    at_risk_count = len(at_risk_df)
    findings['at_risk_customer_count'] = at_risk_count
    
    if at_risk_count > 0:
        at_risk_churn_rate = at_risk_df['churned'].mean() * 100
    else:
        at_risk_churn_rate = 0.0
    findings['at_risk_churn_rate_pct'] = at_risk_churn_rate

    # --- Q6: Tenure and Satisfaction Summary ---
    # Tenure stats
    findings['tenure_mean'] = df['tenure_months'].mean()
    findings['tenure_median'] = df['tenure_months'].median()
    # Sample standard deviation (ddof=1)
    findings['tenure_std'] = df['tenure_months'].std(ddof=1)
    
    # Satisfaction stats
    satisfaction_valid = df['satisfaction_score'].dropna()
    findings['satisfaction_mean'] = satisfaction_valid.mean()
    findings['satisfaction_missing_count'] = df['satisfaction_score'].isna().sum()

    # --- Q7: Lifetime Value by Plan ---
    plan_ltv = df.groupby('plan')['lifetime_value'].mean()
    ltv_basic = plan_ltv.get('Basic', 0.0)
    ltv_standard = plan_ltv.get('Standard', 0.0)
    ltv_premium = plan_ltv.get('Premium', 0.0)
    
    findings['ltv_basic'] = ltv_basic
    findings['ltv_standard'] = ltv_standard
    findings['ltv_premium'] = ltv_premium
    
    if ltv_basic != 0:
        premium_vs_basic_change = (ltv_premium - ltv_basic) / ltv_basic * 100
    else:
        premium_vs_basic_change = 0.0
    findings['premium_vs_basic_ltv_change_pct'] = premium_vs_basic_change

    # Write output
    with open(output_file, 'w') as f:
        json.dump(findings, f)

if __name__ == "__main__":
    main()