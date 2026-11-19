import os
import json
import pandas as pd
import numpy as np

# Read cleaned data
input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
df = pd.read_csv(input_path, parse_dates=["signup_date"])

findings = {}

# Q1: Overall aggregation
findings["customer_count"] = float(len(df))
findings["churn_rate_pct"] = float(df["churned"].mean() * 100)
findings["avg_monthly_fee"] = float(df["monthly_fee"].mean())

# Q2: Churn by plan
plan_churn = df.groupby("plan")["churned"].mean() * 100
findings["churn_rate_basic_pct"] = float(plan_churn["Basic"])
findings["churn_rate_standard_pct"] = float(plan_churn["Standard"])
findings["churn_rate_premium_pct"] = float(plan_churn["Premium"])

# Q3: Churn by signup cohort (calendar year)
df["signup_year"] = df["signup_date"].dt.year
cohort_churn = df.groupby("signup_year")["churned"].mean() * 100
for year in [2021, 2022, 2023, 2024]:
    key = f"churn_rate_cohort_{year}_pct"
    if year in cohort_churn.index:
        findings[key] = float(cohort_churn[year])
    else:
        findings[key] = 0.0

# Q4: Contract effect
contract_churn = df.groupby("contract_type")["churned"].mean() * 100
findings["churn_rate_monthly_pct"] = float(contract_churn["Monthly"])
findings["churn_rate_annual_pct"] = float(contract_churn["Annual"])
findings["churn_monthly_vs_annual_change_pct"] = float(
    (contract_churn["Monthly"] - contract_churn["Annual"]) / contract_churn["Annual"] * 100
)

# Q5: At-risk segment
at_risk = df[(df["support_tickets"] >= 5) & (df["satisfaction_score"].notna()) & (df["satisfaction_score"] <= 2)]
findings["at_risk_customer_count"] = float(len(at_risk))
if len(at_risk) > 0:
    findings["at_risk_churn_rate_pct"] = float(at_risk["churned"].mean() * 100)
else:
    findings["at_risk_churn_rate_pct"] = 0.0

# Q6: Tenure and satisfaction summary
findings["tenure_mean"] = float(df["tenure_months"].mean())
findings["tenure_median"] = float(df["tenure_months"].median())
findings["tenure_std"] = float(df["tenure_months"].std(ddof=1))
valid_satisfaction = df["satisfaction_score"].dropna()
findings["satisfaction_mean"] = float(valid_satisfaction.mean())
findings["satisfaction_missing_count"] = float(df["satisfaction_score"].isna().sum())

# Q7: Lifetime value by plan
plan_ltv = df.groupby("plan")["lifetime_value"].mean()
findings["ltv_basic"] = float(plan_ltv["Basic"])
findings["ltv_standard"] = float(plan_ltv["Standard"])
findings["ltv_premium"] = float(plan_ltv["Premium"])
findings["premium_vs_basic_ltv_change_pct"] = float(
    (plan_ltv["Premium"] - plan_ltv["Basic"]) / plan_ltv["Basic"] * 100
)

# Validate all values are finite numbers
for k, v in findings.items():
    if not isinstance(v, (int, float)) or not np.isfinite(v):
        raise ValueError(f"Non-finite or non-numeric value for key '{k}': {v}")

# Write findings.json
output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
with open(output_path, "w") as f:
    json.dump(findings, f)

print("findings.json written successfully.")
print(json.dumps(findings, indent=2))
