import os
import json
import pandas as pd
import numpy as np

# --- Load cleaned data ---
input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
df = pd.read_csv(input_path, parse_dates=["signup_date"])

# Ensure correct dtypes
df["churned"] = pd.to_numeric(df["churned"], errors="coerce")
df["monthly_fee"] = pd.to_numeric(df["monthly_fee"], errors="coerce")
df["tenure_months"] = pd.to_numeric(df["tenure_months"], errors="coerce")
df["support_tickets"] = pd.to_numeric(df["support_tickets"], errors="coerce")
df["satisfaction_score"] = pd.to_numeric(df["satisfaction_score"], errors="coerce")
df["lifetime_value"] = pd.to_numeric(df["lifetime_value"], errors="coerce")

findings = {}

# --- Q1: Overall metrics ---
customer_count = len(df)
churn_rate_pct = df["churned"].mean() * 100.0
avg_monthly_fee = df["monthly_fee"].mean()

findings["customer_count"] = float(customer_count)
findings["churn_rate_pct"] = float(churn_rate_pct)
findings["avg_monthly_fee"] = float(avg_monthly_fee)

# --- Q2: Churn by plan ---
plan_churn = df.groupby("plan")["churned"].mean() * 100.0
findings["churn_rate_basic_pct"] = float(plan_churn.get("Basic", 0.0))
findings["churn_rate_standard_pct"] = float(plan_churn.get("Standard", 0.0))
findings["churn_rate_premium_pct"] = float(plan_churn.get("Premium", 0.0))

# --- Q3: Churn by signup cohort (calendar year) ---
df["signup_year"] = df["signup_date"].dt.year
cohort_churn = df.groupby("signup_year")["churned"].mean() * 100.0

for year in [2021, 2022, 2023, 2024]:
    key = f"churn_rate_cohort_{year}_pct"
    findings[key] = float(cohort_churn.get(year, 0.0))

# --- Q4: Contract effect ---
contract_churn = df.groupby("contract_type")["churned"].mean() * 100.0
churn_rate_monthly_pct = float(contract_churn.get("Monthly", 0.0))
churn_rate_annual_pct = float(contract_churn.get("Annual", 0.0))

if churn_rate_annual_pct != 0.0:
    churn_monthly_vs_annual_change_pct = (churn_rate_monthly_pct - churn_rate_annual_pct) / churn_rate_annual_pct * 100.0
else:
    churn_monthly_vs_annual_change_pct = 0.0

findings["churn_rate_monthly_pct"] = churn_rate_monthly_pct
findings["churn_rate_annual_pct"] = churn_rate_annual_pct
findings["churn_monthly_vs_annual_change_pct"] = float(churn_monthly_vs_annual_change_pct)

# --- Q5: At-risk segment ---
at_risk_mask = (df["support_tickets"] >= 5) & (df["satisfaction_score"].notna()) & (df["satisfaction_score"] <= 2)
at_risk_df = df[at_risk_mask]
at_risk_customer_count = len(at_risk_df)
at_risk_churn_rate_pct = float(at_risk_df["churned"].mean() * 100.0) if at_risk_customer_count > 0 else 0.0

findings["at_risk_customer_count"] = float(at_risk_customer_count)
findings["at_risk_churn_rate_pct"] = at_risk_churn_rate_pct

# --- Q6: Tenure and satisfaction summary ---
tenure_mean = float(df["tenure_months"].mean())
tenure_median = float(df["tenure_months"].median())
tenure_std = float(df["tenure_months"].std(ddof=1))

sat_valid = df["satisfaction_score"].dropna()
satisfaction_mean = float(sat_valid.mean())
satisfaction_missing_count = float(df["satisfaction_score"].isna().sum())

findings["tenure_mean"] = tenure_mean
findings["tenure_median"] = tenure_median
findings["tenure_std"] = tenure_std
findings["satisfaction_mean"] = satisfaction_mean
findings["satisfaction_missing_count"] = satisfaction_missing_count

# --- Q7: Lifetime value by plan ---
plan_ltv = df.groupby("plan")["lifetime_value"].mean()
ltv_basic = float(plan_ltv.get("Basic", 0.0))
ltv_standard = float(plan_ltv.get("Standard", 0.0))
ltv_premium = float(plan_ltv.get("Premium", 0.0))

if ltv_basic != 0.0:
    premium_vs_basic_ltv_change_pct = (ltv_premium - ltv_basic) / ltv_basic * 100.0
else:
    premium_vs_basic_ltv_change_pct = 0.0

findings["ltv_basic"] = ltv_basic
findings["ltv_standard"] = ltv_standard
findings["ltv_premium"] = ltv_premium
findings["premium_vs_basic_ltv_change_pct"] = float(premium_vs_basic_ltv_change_pct)

# --- Validate all values are finite numbers ---
for k, v in findings.items():
    if not isinstance(v, (int, float)) or not np.isfinite(v):
        raise ValueError(f"Non-finite or non-numeric value for key '{k}': {v}")

# --- Write findings.json ---
output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
with open(output_path, "w") as f:
    json.dump(findings, f)

print("findings.json written successfully.")
print(json.dumps(findings, indent=2))
