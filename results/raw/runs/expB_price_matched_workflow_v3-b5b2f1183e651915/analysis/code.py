import os
import json
import pandas as pd
import numpy as np

# --- Load cleaned data ---
input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
df = pd.read_csv(
    input_path,
    dtype={
        "customer_id": str,
        "signup_date": str,
        "plan": str,
        "contract_type": str,
        "monthly_fee": float,
        "tenure_months": int,
        "support_tickets": int,
        "churned": int,
        "lifetime_value": float,
    },
    parse_dates=False,
)

# Parse satisfaction_score as nullable Int64
df["satisfaction_score"] = pd.to_numeric(df["satisfaction_score"], errors="coerce").astype("Int64")

# Parse signup_date as datetime
df["signup_date"] = pd.to_datetime(df["signup_date"], format="%Y-%m-%d")
df["signup_year"] = df["signup_date"].dt.year

findings = {}

# --- Q1: Overall aggregates ---
customer_count = len(df)
churn_rate_pct = df["churned"].mean() * 100.0
avg_monthly_fee = df["monthly_fee"].mean()

findings["customer_count"] = float(customer_count)
findings["churn_rate_pct"] = float(churn_rate_pct)
findings["avg_monthly_fee"] = float(avg_monthly_fee)

# --- Q2: Churn by plan ---
for plan, key in [("Basic", "churn_rate_basic_pct"),
                  ("Standard", "churn_rate_standard_pct"),
                  ("Premium", "churn_rate_premium_pct")]:
    subset = df[df["plan"] == plan]
    findings[key] = float(subset["churned"].mean() * 100.0)

# --- Q3: Churn by signup cohort ---
for year, key in [(2021, "churn_rate_cohort_2021_pct"),
                  (2022, "churn_rate_cohort_2022_pct"),
                  (2023, "churn_rate_cohort_2023_pct"),
                  (2024, "churn_rate_cohort_2024_pct")]:
    subset = df[df["signup_year"] == year]
    if len(subset) == 0:
        findings[key] = 0.0
    else:
        findings[key] = float(subset["churned"].mean() * 100.0)

# --- Q4: Contract effect ---
monthly_subset = df[df["contract_type"] == "Monthly"]
annual_subset = df[df["contract_type"] == "Annual"]

churn_rate_monthly_pct = float(monthly_subset["churned"].mean() * 100.0)
churn_rate_annual_pct = float(annual_subset["churned"].mean() * 100.0)
churn_monthly_vs_annual_change_pct = (
    (churn_rate_monthly_pct - churn_rate_annual_pct) / churn_rate_annual_pct * 100.0
)

findings["churn_rate_monthly_pct"] = churn_rate_monthly_pct
findings["churn_rate_annual_pct"] = churn_rate_annual_pct
findings["churn_monthly_vs_annual_change_pct"] = float(churn_monthly_vs_annual_change_pct)

# --- Q5: At-risk segment ---
at_risk = df[
    (df["support_tickets"] >= 5) &
    (df["satisfaction_score"].notna()) &
    (df["satisfaction_score"] <= 2)
]
at_risk_customer_count = len(at_risk)
if at_risk_customer_count == 0:
    at_risk_churn_rate_pct = 0.0
else:
    at_risk_churn_rate_pct = float(at_risk["churned"].mean() * 100.0)

findings["at_risk_customer_count"] = float(at_risk_customer_count)
findings["at_risk_churn_rate_pct"] = float(at_risk_churn_rate_pct)

# --- Q6: Tenure and satisfaction summary ---
tenure_mean = float(df["tenure_months"].mean())
tenure_median = float(df["tenure_months"].median())
tenure_std = float(df["tenure_months"].std(ddof=1))

valid_satisfaction = df[df["satisfaction_score"].notna()]["satisfaction_score"].astype(float)
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
premium_vs_basic_ltv_change_pct = (ltv_premium - ltv_basic) / ltv_basic * 100.0

findings["ltv_basic"] = ltv_basic
findings["ltv_standard"] = ltv_standard
findings["ltv_premium"] = ltv_premium
findings["premium_vs_basic_ltv_change_pct"] = float(premium_vs_basic_ltv_change_pct)

# --- Validate all values are finite numbers ---
required_keys = [
    "customer_count", "churn_rate_pct", "avg_monthly_fee",
    "churn_rate_basic_pct", "churn_rate_standard_pct", "churn_rate_premium_pct",
    "churn_rate_cohort_2021_pct", "churn_rate_cohort_2022_pct",
    "churn_rate_cohort_2023_pct", "churn_rate_cohort_2024_pct",
    "churn_rate_monthly_pct", "churn_rate_annual_pct", "churn_monthly_vs_annual_change_pct",
    "at_risk_customer_count", "at_risk_churn_rate_pct",
    "tenure_mean", "tenure_median", "tenure_std",
    "satisfaction_mean", "satisfaction_missing_count",
    "ltv_basic", "ltv_standard", "ltv_premium", "premium_vs_basic_ltv_change_pct",
]

for k in required_keys:
    v = findings[k]
    assert isinstance(v, float), f"{k} is not float: {type(v)}"
    assert np.isfinite(v), f"{k} is not finite: {v}"

# --- Write findings.json ---
output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
with open(output_path, "w") as f:
    json.dump(findings, f, indent=2)

print("Analysis complete. findings.json written.")
print(json.dumps(findings, indent=2))
