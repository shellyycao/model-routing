import os
import json
import pandas as pd
import numpy as np

def run_analysis():
    # Read cleaned data
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    df = pd.read_csv(input_path)
    
    # Initialize findings dictionary
    findings = {}
    
    # Q1: Overall aggregation
    findings["customer_count"] = len(df)
    findings["churn_rate_pct"] = df["churned"].mean() * 100
    findings["avg_monthly_fee"] = df["monthly_fee"].mean()
    
    # Q2: Churn by plan
    plan_churn = df.groupby("plan")["churned"].mean() * 100
    findings["churn_rate_basic_pct"] = plan_churn.get("Basic", 0.0)
    findings["churn_rate_standard_pct"] = plan_churn.get("Standard", 0.0)
    findings["churn_rate_premium_pct"] = plan_churn.get("Premium", 0.0)
    
    # Q3: Churn by signup cohort (calendar year)
    df["signup_year"] = pd.to_datetime(df["signup_date"]).dt.year
    cohort_churn = df.groupby("signup_year")["churned"].mean() * 100
    findings["churn_rate_cohort_2021_pct"] = cohort_churn.get(2021, 0.0)
    findings["churn_rate_cohort_2022_pct"] = cohort_churn.get(2022, 0.0)
    findings["churn_rate_cohort_2023_pct"] = cohort_churn.get(2023, 0.0)
    findings["churn_rate_cohort_2024_pct"] = cohort_churn.get(2024, 0.0)
    
    # Q4: Contract effect
    contract_churn = df.groupby("contract_type")["churned"].mean() * 100
    churn_monthly = contract_churn.get("Monthly", 0.0)
    churn_annual = contract_churn.get("Annual", 0.0)
    findings["churn_rate_monthly_pct"] = churn_monthly
    findings["churn_rate_annual_pct"] = churn_annual
    if churn_annual != 0:
        findings["churn_monthly_vs_annual_change_pct"] = (churn_monthly - churn_annual) / churn_annual * 100
    else:
        findings["churn_monthly_vs_annual_change_pct"] = 0.0
    
    # Q5: At-risk segment
    at_risk_mask = (df["support_tickets"] >= 5) & (df["satisfaction_score"].notna()) & (df["satisfaction_score"] <= 2)
    at_risk_df = df[at_risk_mask]
    findings["at_risk_customer_count"] = len(at_risk_df)
    if len(at_risk_df) > 0:
        findings["at_risk_churn_rate_pct"] = at_risk_df["churned"].mean() * 100
    else:
        findings["at_risk_churn_rate_pct"] = 0.0
    
    # Q6: Tenure and satisfaction summary
    findings["tenure_mean"] = df["tenure_months"].mean()
    findings["tenure_median"] = df["tenure_months"].median()
    findings["tenure_std"] = df["tenure_months"].std(ddof=1)
    
    satisfaction_valid = df["satisfaction_score"].dropna()
    findings["satisfaction_mean"] = satisfaction_valid.mean()
    findings["satisfaction_missing_count"] = df["satisfaction_score"].isna().sum()
    
    # Q7: Lifetime value by plan
    ltv_by_plan = df.groupby("plan")["lifetime_value"].mean()
    ltv_basic = ltv_by_plan.get("Basic", 0.0)
    ltv_standard = ltv_by_plan.get("Standard", 0.0)
    ltv_premium = ltv_by_plan.get("Premium", 0.0)
    
    findings["ltv_basic"] = ltv_basic
    findings["ltv_standard"] = ltv_standard
    findings["ltv_premium"] = ltv_premium
    
    if ltv_basic != 0:
        findings["premium_vs_basic_ltv_change_pct"] = (ltv_premium - ltv_basic) / ltv_basic * 100
    else:
        findings["premium_vs_basic_ltv_change_pct"] = 0.0
    
    # Write findings to JSON
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
    with open(output_path, "w") as f:
        json.dump(findings, f)

if __name__ == "__main__":
    run_analysis()
