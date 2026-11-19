import json
import os

import numpy as np
import pandas as pd

INPUT_PATH = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
OUTPUT_PATH = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")


def finite(value):
    """Convert to a native Python float; replace NaN/inf (e.g. from an empty
    slice or division by zero) with 0.0 so the JSON stays valid."""
    v = float(value)
    return v if np.isfinite(v) else 0.0


df = pd.read_csv(INPUT_PATH, parse_dates=["signup_date"])

findings = {}

# q1: overall aggregation
findings["customer_count"] = finite(len(df))
findings["churn_rate_pct"] = finite(df["churned"].mean() * 100)
findings["avg_monthly_fee"] = finite(df["monthly_fee"].mean())

# q2: churn rate by plan
for plan, key in (("Basic", "churn_rate_basic_pct"),
                  ("Standard", "churn_rate_standard_pct"),
                  ("Premium", "churn_rate_premium_pct")):
    subset = df[df["plan"] == plan]
    findings[key] = finite(subset["churned"].mean() * 100)

# q3: churn rate by signup-year cohort
signup_year = df["signup_date"].dt.year
for year in (2021, 2022, 2023, 2024):
    subset = df[signup_year == year]
    findings["churn_rate_cohort_%d_pct" % year] = finite(subset["churned"].mean() * 100)

# q4: contract effect
monthly_rate = df.loc[df["contract_type"] == "Monthly", "churned"].mean() * 100
annual_rate = df.loc[df["contract_type"] == "Annual", "churned"].mean() * 100
findings["churn_rate_monthly_pct"] = finite(monthly_rate)
findings["churn_rate_annual_pct"] = finite(annual_rate)
findings["churn_monthly_vs_annual_change_pct"] = finite(
    (monthly_rate - annual_rate) / annual_rate * 100 if annual_rate != 0 else np.nan
)

# q5: at-risk segment (many tickets AND low, non-missing satisfaction)
at_risk = df[(df["support_tickets"] >= 5) &
             (df["satisfaction_score"].notna()) &
             (df["satisfaction_score"] <= 2)]
findings["at_risk_customer_count"] = finite(len(at_risk))
findings["at_risk_churn_rate_pct"] = finite(at_risk["churned"].mean() * 100)

# q6: tenure and satisfaction summary
findings["tenure_mean"] = finite(df["tenure_months"].mean())
findings["tenure_median"] = finite(df["tenure_months"].median())
findings["tenure_std"] = finite(df["tenure_months"].std(ddof=1))
findings["satisfaction_mean"] = finite(df["satisfaction_score"].mean())  # skips NaN
findings["satisfaction_missing_count"] = finite(df["satisfaction_score"].isna().sum())

# q7: lifetime value by plan
ltv_by_plan = df.groupby("plan")["lifetime_value"].mean()
ltv_basic = finite(ltv_by_plan["Basic"])
ltv_standard = finite(ltv_by_plan["Standard"])
ltv_premium = finite(ltv_by_plan["Premium"])
findings["ltv_basic"] = ltv_basic
findings["ltv_standard"] = ltv_standard
findings["ltv_premium"] = ltv_premium
findings["premium_vs_basic_ltv_change_pct"] = finite(
    (ltv_premium - ltv_basic) / ltv_basic * 100 if ltv_basic != 0 else np.nan
)

# Flat JSON: every metric key maps to one finite native-float number.
with open(OUTPUT_PATH, "w") as f:
    json.dump({k: float(v) for k, v in findings.items()}, f, indent=2)
