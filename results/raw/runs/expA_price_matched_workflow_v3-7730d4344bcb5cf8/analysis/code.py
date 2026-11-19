import os
import json
import pandas as pd
import numpy as np

# Define input and output paths
input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

# Read the cleaned data
df = pd.read_csv(input_path)

# Initialize the findings dictionary
findings = {}

# --- Q1: Overall Aggregation ---
findings["customer_count"] = len(df)
findings["churn_rate_pct"] = (df["churned"].mean() * 100)
findings["avg_monthly_fee"] = df["monthly_fee"].mean()

# --- Q2: Churn by Plan ---
plan_groups = df.groupby("plan")["churned"].mean() * 100
findings["churn_rate_basic_pct"] = plan_groups.get("Basic", 0.0)
findings["churn_rate_standard_pct"] = plan_groups.get("Standard", 0.0)
findings["churn_rate_premium_pct"] = plan_groups.get("Premium", 0.0)

# --- Q3: Churn by Signup Cohort ---
df["signup_year"] = pd.to_datetime(df["signup_date"]).dt.year
cohort_groups = df.groupby("signup_year")["churned"].mean() * 100
for year in [2021, 2022, 2023, 2024]:
    key = f"churn_rate_cohort_{year}_pct"
    findings[key] = cohort_groups.get(year, 0.0)

# --- Q4: Contract Effect ---
contract_groups = df.groupby("contract_type")["churned"].mean() * 100
churn_monthly = contract_groups.get("Monthly", 0.0)
churn_annual = contract_groups.get("Annual", 0.0)

findings["churn_rate_monthly_pct"] = churn_monthly
findings["churn_rate_annual_pct"] = churn_annual

if churn_annual != 0:
    findings["churn_monthly_vs_annual_change_pct"] = ((churn_monthly - churn_annual) / churn_annual) * 100
else:
    findings["churn_monthly_vs_annual_change_pct"] = 0.0

# --- Q5: At-risk Segment ---
at_risk_filter = (df["support_tickets"] >= 5) & (df["satisfaction_score"].notna()) & (df["satisfaction_score"] <= 2)
at_risk_df = df[at_risk_filter]

findings["at_risk_customer_count"] = len(at_risk_df)
if len(at_risk_df) > 0:
    findings["at_risk_churn_rate_pct"] = at_risk_df["churned"].mean() * 100
else:
    findings["at_risk_churn_rate_pct"] = 0.0

# --- Q6: Tenure and Satisfaction Summary ---
findings["tenure_mean"] = df["tenure_months"].mean()
findings["tenure_median"] = df["tenure_months"].median()
findings["tenure_std"] = df["tenure_months"].std(ddof=1) # Sample standard deviation

satisfaction_valid = df["satisfaction_score"].dropna()
findings["satisfaction_mean"] = satisfaction_valid.mean()
findings["satisfaction_missing_count"] = df["satisfaction_score"].isna().sum()

# --- Q7: Lifetime Value by Plan ---
ltv_groups = df.groupby("plan")["lifetime_value"].mean()
ltv_basic = ltv_groups.get("Basic", 0.0)
ltv_standard = ltv_groups.get("Standard", 0.0)
ltv_premium = ltv_groups.get("Premium", 0.0)

findings["ltv_basic"] = ltv_basic
findings["ltv_standard"] = ltv_standard
findings["ltv_premium"] = ltv_premium

if ltv_basic != 0:
    findings["premium_vs_basic_ltv_change_pct"] = ((ltv_premium - ltv_basic) / ltv_basic) * 100
else:
    findings["premium_vs_basic_ltv_change_pct"] = 0.0

# Write findings to JSON
with open(output_path, 'w') as f:
    json.dump(findings, f)
