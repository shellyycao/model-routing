import os
import json
import pandas as pd
import numpy as np

def run_analysis():
    # Define paths
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
    
    # Read cleaned data
    # The cleaning stage ensures correct types, but we enforce them for safety
    df = pd.read_csv(input_path)
    
    # Ensure correct data types based on cleaning contract
    df['signup_date'] = pd.to_datetime(df['signup_date'])
    df['tenure_months'] = df['tenure_months'].astype(int)
    df['support_tickets'] = df['support_tickets'].astype(int)
    df['churned'] = df['churned'].astype(int)
    # satisfaction_score is nullable int, pandas reads as float if NaNs exist, or int
    # We handle it appropriately in calculations
    
    findings = {}
    
    # q1: Overall aggregation
    customer_count = len(df)
    findings['customer_count'] = customer_count
    
    churn_rate_pct = (df['churned'].mean() * 100)
    findings['churn_rate_pct'] = churn_rate_pct
    
    avg_monthly_fee = df['monthly_fee'].mean()
    findings['avg_monthly_fee'] = avg_monthly_fee
    
    # q2: Churn by plan
    plan_churn = df.groupby('plan')['churned'].mean() * 100
    findings['churn_rate_basic_pct'] = plan_churn.get('Basic', 0.0)
    findings['churn_rate_standard_pct'] = plan_churn.get('Standard', 0.0)
    findings['churn_rate_premium_pct'] = plan_churn.get('Premium', 0.0)
    
    # q3: Churn by signup cohort (year)
    df['signup_year'] = df['signup_date'].dt.year
    cohort_churn = df.groupby('signup_year')['churned'].mean() * 100
    findings['churn_rate_cohort_2021_pct'] = cohort_churn.get(2021, 0.0)
    findings['churn_rate_cohort_2022_pct'] = cohort_churn.get(2022, 0.0)
    findings['churn_rate_cohort_2023_pct'] = cohort_churn.get(2023, 0.0)
    findings['churn_rate_cohort_2024_pct'] = cohort_churn.get(2024, 0.0)
    
    # q4: Contract effect
    contract_churn = df.groupby('contract_type')['churned'].mean() * 100
    churn_rate_monthly_pct = contract_churn.get('Monthly', 0.0)
    churn_rate_annual_pct = contract_churn.get('Annual', 0.0)
    
    findings['churn_rate_monthly_pct'] = churn_rate_monthly_pct
    findings['churn_rate_annual_pct'] = churn_rate_annual_pct
    
    # Relative difference calculation
    if churn_rate_annual_pct != 0:
        churn_monthly_vs_annual_change_pct = ((churn_rate_monthly_pct - churn_rate_annual_pct) / churn_rate_annual_pct) * 100
    else:
        churn_monthly_vs_annual_change_pct = 0.0
    findings['churn_monthly_vs_annual_change_pct'] = churn_monthly_vs_annual_change_pct
    
    # q5: At-risk segment
    # Filter: support_tickets >= 5 AND satisfaction_score <= 2 (and not missing)
    at_risk_mask = (df['support_tickets'] >= 5) & (df['satisfaction_score'].notna()) & (df['satisfaction_score'] <= 2)
    at_risk_df = df[at_risk_mask]
    
    at_risk_customer_count = len(at_risk_df)
    findings['at_risk_customer_count'] = at_risk_customer_count
    
    if at_risk_customer_count > 0:
        at_risk_churn_rate_pct = (at_risk_df['churned'].mean() * 100)
    else:
        at_risk_churn_rate_pct = 0.0
    findings['at_risk_churn_rate_pct'] = at_risk_churn_rate_pct
    
    # q6: Tenure and satisfaction summary
    findings['tenure_mean'] = df['tenure_months'].mean()
    findings['tenure_median'] = df['tenure_months'].median()
    # Sample standard deviation (ddof=1)
    findings['tenure_std'] = df['tenure_months'].std(ddof=1)
    
    # Satisfaction: only over non-missing scores
    valid_satisfaction = df['satisfaction_score'].dropna()
    findings['satisfaction_mean'] = valid_satisfaction.mean()
    findings['satisfaction_missing_count'] = df['satisfaction_score'].isna().sum()
    
    # q7: Lifetime value by plan
    ltv_by_plan = df.groupby('plan')['lifetime_value'].mean()
    ltv_basic = ltv_by_plan.get('Basic', 0.0)
    ltv_standard = ltv_by_plan.get('Standard', 0.0)
    ltv_premium = ltv_by_plan.get('Premium', 0.0)
    
    findings['ltv_basic'] = ltv_basic
    findings['ltv_standard'] = ltv_standard
    findings['ltv_premium'] = ltv_premium
    
    if ltv_basic != 0:
        premium_vs_basic_ltv_change_pct = ((ltv_premium - ltv_basic) / ltv_basic) * 100
    else:
        premium_vs_basic_ltv_change_pct = 0.0
    findings['premium_vs_basic_ltv_change_pct'] = premium_vs_basic_ltv_change_pct
    
    # Write output
    # Ensure all values are standard python floats for JSON serialization
    # (Pandas/numpy types can sometimes cause issues, though json.dump usually handles float64)
    findings_serializable = {k: float(v) if isinstance(v, (np.floating, float)) else v for k, v in findings.items()}
    # Convert numpy integers if any (counts)
    findings_serializable = {k: int(v) if isinstance(v, (np.integer, int)) else v for k, v in findings_serializable.items()}

    with open(output_path, 'w') as f:
        json.dump(findings_serializable, f)

if __name__ == "__main__":
    run_analysis()