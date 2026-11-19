import os
import json
import pandas as pd
import numpy as np

# Define input and output paths
input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

# Read the cleaned data
df = pd.read_csv(input_path)

# Initialize findings dictionary
findings = {}

# --- q1: Overall aggregation ---
findings["customer_count"] = len(df)
findings["churn_rate_pct"] = (df["churned"].mean() * 100)
findings["avg_monthly_fee"] = df["monthly_fee"].mean()

# --- q2: Churn by plan ---
plan_groups = df.groupby("plan")
findings["churn_rate_basic_pct"] = (plan_groups.get_group("Basic")["churned"].mean() * 100)
findings["churn_rate_standard_pct"] = (plan_groups.get_group("Standard")["churned"].mean() * 100)
findings["churn_rate_premium_pct"] = (plan_groups.get_group("Premium")["churned"].mean() * 100)

# --- q3: Churn by signup cohort ---
df["signup_year"] = pd.to_datetime(df["signup_date"]).dt.year
cohort_groups = df.groupby("signup_year")
for year in [2021, 2022, 2023, 2024]:
    key = f"churn_rate_cohort_{year}_pct"
    if year in cohort_groups.groups:
        findings[key] = (cohort_groups.get_group(year)["churned"].mean() * 100)
    else:
        findings[key] = 0.0

# --- q4: Contract effect ---
contract_groups = df.groupby("contract_type")
churn_monthly = contract_groups.get_group("Monthly")["churned"].mean() * 100
churn_annual = contract_groups.get_group("Annual")["churned"].mean() * 100
findings["churn_rate_monthly_pct"] = churn_monthly
findings["churn_rate_annual_pct"] = churn_annual
findings["churn_monthly_vs_annual_change_pct"] = ((churn_monthly - churn_annual) / churn_annual) * 100

# --- q5: At-risk segment ---
at_risk_filter = (df["support_tickets"] >= 5) & (df["satisfaction_score"].notna()) & (df["satisfaction_score"] <= 2)
at_risk_df = df[at_risk_filter]
findings["at_risk_customer_count"] = len(at_risk_df)
if len(at_risk_df) > 0:
    findings["at_risk_churn_rate_pct"] = (at_risk_df["churned"].mean() * 100)
else:
    findings["at_risk_churn_rate_pct"] = 0.0

# --- q6: Tenure and satisfaction summary ---
findings["tenure_mean"] = df["tenure_months"].mean()
findings["tenure_median"] = df["tenure_months"].median()
findings["tenure_std"] = df["tenure_months"].std(ddof=1)

satisfaction_valid = df["satisfaction_score"].dropna()
findings["satisfaction_mean"] = satisfaction_valid.mean()
findings["satisfaction_missing_count"] = df["satisfaction_score"].isna().sum()

# --- q7: Lifetime value by plan ---
ltv_basic = plan_groups.get_group("Basic")["lifetime_value"].mean()
ltv_standard = plan_groups.get_group("Standard")["lifetime_value"].mean()
ltv_premium = plan_groups.get_group("Premium")["lifetime_value"].mean()

findings["ltv_basic"] = ltv_basic
findings["ltv_standard"] = ltv_standard
findings["ltv_premium"] = ltv_premium
findings["premium_vs_basic_ltv_change_pct"] = ((ltv_premium - ltv_basic) / ltv_basic) * 100

# Write findings to JSON
with open(output_path, "w") as f:
    json.dump(findings, f)
