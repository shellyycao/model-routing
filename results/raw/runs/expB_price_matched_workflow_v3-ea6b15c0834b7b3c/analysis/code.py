import os
import json
import pandas as pd
import numpy as np

# --- Load cleaned data ---
input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
df = pd.read_csv(input_path, parse_dates=["signup_date"])

findings = {}

# --- Q1: Overall aggregates ---
customer_count = len(df)
churn_rate_pct = df["churned"].mean() * 100
avg_monthly_fee = df["monthly_fee"].mean()

findings["customer_count"] = float(customer_count)
findings["churn_rate_pct"] = float(churn_rate_pct)
findings["avg_monthly_fee"] = float(avg_monthly_fee)

# --- Q2: Churn by plan ---
for plan, key in [("Basic", "churn_rate_basic_pct"),
                  ("Standard", "churn_rate_standard_pct"),
                  ("Premium", "churn_rate_premium_pct")]:
    subset = df[df["plan"] == plan]
    findings[key] = float(subset["churned"].mean() * 100)

# --- Q3: Churn by signup cohort (calendar year) ---
df["signup_year"] = df["signup_date"].dt.year
for year, key in [(2021, "churn_rate_cohort_2021_pct"),
                  (2022, "churn_rate_cohort_2022_pct"),
                  (2023, "churn_rate_cohort_2023_pct"),
                  (2024, "churn_rate_cohort_2024_pct")]:
    subset = df[df["signup_year"] == year]
    if len(subset) == 0:
        findings[key] = 0.0
    else:
        findings[key] = float(subset["churned"].mean() * 100)

# --- Q4: Contract effect ---
monthly_subset = df[df["contract_type"] == "Monthly"]
annual_subset = df[df["contract_type"] == "Annual"]
churn_rate_monthly_pct = float(monthly_subset["churned"].mean() * 100)
churn_rate_annual_pct = float(annual_subset["churned"].mean() * 100)
churn_monthly_vs_annual_change_pct = (churn_rate_monthly_pct - churn_rate_annual_pct) / churn_rate_annual_pct * 100

findings["churn_rate_monthly_pct"] = churn_rate_monthly_pct
findings["churn_rate_annual_pct"] = churn_rate_annual_pct
findings["churn_monthly_vs_annual_change_pct"] = float(churn_monthly_vs_annual_change_pct)

# --- Q5: At-risk segment ---
at_risk = df[(df["support_tickets"] >= 5) & (df["satisfaction_score"].notna()) & (df["satisfaction_score"] <= 2)]
at_risk_customer_count = len(at_risk)
at_risk_churn_rate_pct = float(at_risk["churned"].mean() * 100) if at_risk_customer_count > 0 else 0.0

findings["at_risk_customer_count"] = float(at_risk_customer_count)
findings["at_risk_churn_rate_pct"] = at_risk_churn_rate_pct

# --- Q6: Tenure and satisfaction summary ---
tenure_mean = float(df["tenure_months"].mean())
tenure_median = float(df["tenure_months"].median())
tenure_std = float(df["tenure_months"].std(ddof=1))

valid_satisfaction = df["satisfaction_score"].dropna()
satisfaction_mean = float(valid_satisfaction.mean())
satisfaction_missing_count = float(df["satisfaction_score"].isna().sum())

findings["tenure_mean"] = tenure_mean
findings["tenure_median"] = tenure_median
findings["tenure_std"] = tenure_std
findings["satisfaction_mean"] = satisfaction_mean
findings["satisfaction_missing_count"] = satisfaction_missing_count

# --- Q7: Lifetime value by plan ---
ltv_by_plan = df.groupby("plan")["lifetime_value"].mean()
ltv_basic = float(ltv_by_plan["Basic"])
ltv_standard = float(ltv_by_plan["Standard"])
ltv_premium = float(ltv_by_plan["Premium"])
premium_vs_basic_ltv_change_pct = (ltv_premium - ltv_basic) / ltv_basic * 100

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
