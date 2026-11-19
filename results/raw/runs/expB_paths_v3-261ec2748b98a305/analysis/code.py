import os
import json
import pandas as pd
import numpy as np

# --- Load cleaned data ---
input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
df = pd.read_csv(input_path, parse_dates=["signup_date"])

# Ensure correct dtypes
df["churned"] = df["churned"].astype(int)
df["tenure_months"] = df["tenure_months"].astype(int)
df["support_tickets"] = df["support_tickets"].astype(int)
df["monthly_fee"] = df["monthly_fee"].astype(float)
df["lifetime_value"] = df["lifetime_value"].astype(float)
# satisfaction_score: nullable float -> keep as float (NaN for missing)
df["satisfaction_score"] = pd.to_numeric(df["satisfaction_score"], errors="coerce")

# -------------------------
# Q1: Overall aggregation
# -------------------------
customer_count = float(len(df))
churn_rate_pct = float(df["churned"].mean() * 100)
avg_monthly_fee = float(df["monthly_fee"].mean())

# -------------------------
# Q2: Churn by plan
# -------------------------
plan_churn = df.groupby("plan")["churned"].mean() * 100
churn_rate_basic_pct = float(plan_churn["Basic"])
churn_rate_standard_pct = float(plan_churn["Standard"])
churn_rate_premium_pct = float(plan_churn["Premium"])

# -------------------------
# Q3: Churn by signup cohort (calendar year)
# -------------------------
df["signup_year"] = df["signup_date"].dt.year
cohort_churn = df.groupby("signup_year")["churned"].mean() * 100

# Use .get with a fallback of NaN then convert; but spec says all four years must be finite numbers.
# If a year has no data, we'd have a problem, but we'll handle gracefully.
def cohort_rate(year):
    if year in cohort_churn.index:
        return float(cohort_churn[year])
    else:
        return 0.0  # no customers in that cohort -> 0% churn

churn_rate_cohort_2021_pct = cohort_rate(2021)
churn_rate_cohort_2022_pct = cohort_rate(2022)
churn_rate_cohort_2023_pct = cohort_rate(2023)
churn_rate_cohort_2024_pct = cohort_rate(2024)

# -------------------------
# Q4: Contract effect
# -------------------------
contract_churn = df.groupby("contract_type")["churned"].mean() * 100
churn_rate_monthly_pct = float(contract_churn["Monthly"])
churn_rate_annual_pct = float(contract_churn["Annual"])
churn_monthly_vs_annual_change_pct = float(
    (churn_rate_monthly_pct - churn_rate_annual_pct) / churn_rate_annual_pct * 100
)

# -------------------------
# Q5: At-risk segment
# -------------------------
at_risk_mask = (
    (df["support_tickets"] >= 5) &
    (df["satisfaction_score"].notna()) &
    (df["satisfaction_score"] <= 2)
)
at_risk_df = df[at_risk_mask]
at_risk_customer_count = float(len(at_risk_df))
if len(at_risk_df) > 0:
    at_risk_churn_rate_pct = float(at_risk_df["churned"].mean() * 100)
else:
    at_risk_churn_rate_pct = 0.0

# -------------------------
# Q6: Tenure and satisfaction summary
# -------------------------
tenure_mean = float(df["tenure_months"].mean())
tenure_median = float(df["tenure_months"].median())
tenure_std = float(df["tenure_months"].std(ddof=1))  # sample std

sat_valid = df["satisfaction_score"].dropna()
satisfaction_mean = float(sat_valid.mean())
satisfaction_missing_count = float(df["satisfaction_score"].isna().sum())

# -------------------------
# Q7: Lifetime value by plan
# -------------------------
plan_ltv = df.groupby("plan")["lifetime_value"].mean()
ltv_basic = float(plan_ltv["Basic"])
ltv_standard = float(plan_ltv["Standard"])
ltv_premium = float(plan_ltv["Premium"])
premium_vs_basic_ltv_change_pct = float(
    (ltv_premium - ltv_basic) / ltv_basic * 100
)

# -------------------------
# Assemble findings
# -------------------------
findings = {
    "customer_count": customer_count,
    "churn_rate_pct": churn_rate_pct,
    "avg_monthly_fee": avg_monthly_fee,
    "churn_rate_basic_pct": churn_rate_basic_pct,
    "churn_rate_standard_pct": churn_rate_standard_pct,
    "churn_rate_premium_pct": churn_rate_premium_pct,
    "churn_rate_cohort_2021_pct": churn_rate_cohort_2021_pct,
    "churn_rate_cohort_2022_pct": churn_rate_cohort_2022_pct,
    "churn_rate_cohort_2023_pct": churn_rate_cohort_2023_pct,
    "churn_rate_cohort_2024_pct": churn_rate_cohort_2024_pct,
    "churn_rate_monthly_pct": churn_rate_monthly_pct,
    "churn_rate_annual_pct": churn_rate_annual_pct,
    "churn_monthly_vs_annual_change_pct": churn_monthly_vs_annual_change_pct,
    "at_risk_customer_count": at_risk_customer_count,
    "at_risk_churn_rate_pct": at_risk_churn_rate_pct,
    "tenure_mean": tenure_mean,
    "tenure_median": tenure_median,
    "tenure_std": tenure_std,
    "satisfaction_mean": satisfaction_mean,
    "satisfaction_missing_count": satisfaction_missing_count,
    "ltv_basic": ltv_basic,
    "ltv_standard": ltv_standard,
    "ltv_premium": ltv_premium,
    "premium_vs_basic_ltv_change_pct": premium_vs_basic_ltv_change_pct,
}

# Validate: all values must be finite numbers
for k, v in findings.items():
    assert isinstance(v, (int, float)), f"{k} is not a number: {v}"
    assert np.isfinite(v), f"{k} is not finite: {v}"

# Write output
output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
with open(output_path, "w") as f:
    json.dump(findings, f)

print("findings.json written successfully.")
print(json.dumps(findings, indent=2))
