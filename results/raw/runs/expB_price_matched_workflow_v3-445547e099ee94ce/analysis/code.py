import json
import os

import numpy as np
import pandas as pd


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    df = pd.read_csv(input_path, dtype={"customer_id": str})

    findings = {}

    # q1: overall metrics
    findings["customer_count"] = int(len(df))
    findings["churn_rate_pct"] = float(df["churned"].mean() * 100)
    findings["avg_monthly_fee"] = float(df["monthly_fee"].mean())

    # q2: churn rate by plan
    plan_keys = {
        "Basic": "churn_rate_basic_pct",
        "Standard": "churn_rate_standard_pct",
        "Premium": "churn_rate_premium_pct",
    }
    for plan, key in plan_keys.items():
        sub = df[df["plan"] == plan]
        findings[key] = float(sub["churned"].mean() * 100) if len(sub) > 0 else 0.0

    # q3: churn rate by signup-year cohort
    signup_year = pd.to_datetime(df["signup_date"], format="%Y-%m-%d").dt.year
    for year in (2021, 2022, 2023, 2024):
        sub = df[signup_year == year]
        findings["churn_rate_cohort_%d_pct" % year] = (
            float(sub["churned"].mean() * 100) if len(sub) > 0 else 0.0
        )

    # q4: churn by contract type and relative difference (Monthly vs Annual)
    monthly = df[df["contract_type"] == "Monthly"]
    annual = df[df["contract_type"] == "Annual"]
    churn_monthly = float(monthly["churned"].mean() * 100) if len(monthly) > 0 else 0.0
    churn_annual = float(annual["churned"].mean() * 100) if len(annual) > 0 else 0.0
    findings["churn_rate_monthly_pct"] = churn_monthly
    findings["churn_rate_annual_pct"] = churn_annual
    findings["churn_monthly_vs_annual_change_pct"] = (
        (churn_monthly - churn_annual) / churn_annual * 100 if churn_annual != 0 else 0.0
    )

    # q5: at-risk segment (support_tickets >= 5 and non-missing satisfaction_score <= 2)
    sat = df["satisfaction_score"]
    at_risk_mask = (df["support_tickets"] >= 5) & sat.notna() & (sat <= 2)
    at_risk = df[at_risk_mask]
    findings["at_risk_customer_count"] = int(len(at_risk))
    findings["at_risk_churn_rate_pct"] = (
        float(at_risk["churned"].mean() * 100) if len(at_risk) > 0 else 0.0
    )

    # q6: tenure and satisfaction summary
    tenure = df["tenure_months"].astype(float)
    findings["tenure_mean"] = float(tenure.mean())
    findings["tenure_median"] = float(tenure.median())
    findings["tenure_std"] = float(tenure.std(ddof=1))
    findings["satisfaction_mean"] = float(sat.mean())
    findings["satisfaction_missing_count"] = int(sat.isna().sum())

    # q7: lifetime value by plan and Premium vs Basic relative difference
    ltv_keys = {"Basic": "ltv_basic", "Standard": "ltv_standard", "Premium": "ltv_premium"}
    for plan, key in ltv_keys.items():
        sub = df[df["plan"] == plan]
        findings[key] = float(sub["lifetime_value"].mean()) if len(sub) > 0 else 0.0
    ltv_basic = findings["ltv_basic"]
    ltv_premium = findings["ltv_premium"]
    findings["premium_vs_basic_ltv_change_pct"] = (
        (ltv_premium - ltv_basic) / ltv_basic * 100 if ltv_basic != 0 else 0.0
    )

    # guarantee every value is a finite native Python number
    for key, value in findings.items():
        if not np.isfinite(float(value)):
            findings[key] = 0.0

    with open(output_path, "w") as f:
        json.dump(findings, f, indent=2)


if __name__ == "__main__":
    main()
