import os
import json
import pandas as pd
import numpy as np

INPUT_DIR = os.environ["INPUT_DIR"]
OUTPUT_DIR = os.environ["OUTPUT_DIR"]

df = pd.read_csv(os.path.join(INPUT_DIR, "cleaned.csv"), dtype={"customer_id": str})

# Enforce numeric types; satisfaction_score may contain empty cells -> NaN (rows kept)
df["signup_date"] = pd.to_datetime(df["signup_date"], format="%Y-%m-%d", errors="coerce")
for col in ["monthly_fee", "tenure_months", "support_tickets", "satisfaction_score", "churned", "lifetime_value"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

def churn_rate_pct(sub):
    """Churn rate in percent for a subset; 0.0 if the subset is empty."""
    if len(sub) == 0:
        return 0.0
    return float(sub["churned"].mean() * 100.0)

metrics = {}

# q1: overall
metrics["customer_count"] = int(len(df))
metrics["churn_rate_pct"] = churn_rate_pct(df)
metrics["avg_monthly_fee"] = float(df["monthly_fee"].mean())

# q2: churn by plan
for plan, key in [("Basic", "churn_rate_basic_pct"),
                  ("Standard", "churn_rate_standard_pct"),
                  ("Premium", "churn_rate_premium_pct")]:
    metrics[key] = churn_rate_pct(df[df["plan"] == plan])

# q3: churn by signup cohort (calendar year)
signup_year = df["signup_date"].dt.year
for year in (2021, 2022, 2023, 2024):
    metrics[f"churn_rate_cohort_{year}_pct"] = churn_rate_pct(df[signup_year == year])

# q4: contract effect
monthly_rate = churn_rate_pct(df[df["contract_type"] == "Monthly"])
annual_rate = churn_rate_pct(df[df["contract_type"] == "Annual"])
metrics["churn_rate_monthly_pct"] = monthly_rate
metrics["churn_rate_annual_pct"] = annual_rate
metrics["churn_monthly_vs_annual_change_pct"] = (
    (monthly_rate - annual_rate) / annual_rate * 100.0 if annual_rate != 0 else 0.0
)

# q5: at-risk segment (support_tickets >= 5 and non-missing satisfaction_score <= 2)
at_risk_mask = (
    (df["support_tickets"] >= 5)
    & df["satisfaction_score"].notna()
    & (df["satisfaction_score"] <= 2)
)
at_risk = df[at_risk_mask]
metrics["at_risk_customer_count"] = int(len(at_risk))
metrics["at_risk_churn_rate_pct"] = churn_rate_pct(at_risk)

# q6: tenure and satisfaction summary
metrics["tenure_mean"] = float(df["tenure_months"].mean())
metrics["tenure_median"] = float(df["tenure_months"].median())
metrics["tenure_std"] = float(df["tenure_months"].std(ddof=1))
metrics["satisfaction_mean"] = float(df["satisfaction_score"].mean())  # skips NaN
metrics["satisfaction_missing_count"] = int(df["satisfaction_score"].isna().sum())

# q7: lifetime value by plan
ltv_basic = float(df.loc[df["plan"] == "Basic", "lifetime_value"].mean())
ltv_standard = float(df.loc[df["plan"] == "Standard", "lifetime_value"].mean())
ltv_premium = float(df.loc[df["plan"] == "Premium", "lifetime_value"].mean())
metrics["ltv_basic"] = ltv_basic
metrics["ltv_standard"] = ltv_standard
metrics["ltv_premium"] = ltv_premium
metrics["premium_vs_basic_ltv_change_pct"] = (
    (ltv_premium - ltv_basic) / ltv_basic * 100.0 if ltv_basic != 0 else 0.0
)

# Guarantee a flat JSON object of native finite numbers
flat = {}
for key, value in metrics.items():
    if isinstance(value, (int, np.integer)):
        flat[key] = int(value)
    else:
        v = float(value)
        flat[key] = v if np.isfinite(v) else 0.0

out_path = os.path.join(OUTPUT_DIR, "findings.json")
with open(out_path, "w") as f:
    json.dump(flat, f, indent=2)
