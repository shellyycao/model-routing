import json
import os

import numpy as np
import pandas as pd


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    df = pd.read_csv(input_path)

    # Ensure correct dtypes; satisfaction_score may contain missing values.
    df["signup_date"] = pd.to_datetime(df["signup_date"], format="%Y-%m-%d")
    df["churned"] = pd.to_numeric(df["churned"], errors="coerce").fillna(0).astype(int)
    df["monthly_fee"] = pd.to_numeric(df["monthly_fee"], errors="coerce")
    df["tenure_months"] = pd.to_numeric(df["tenure_months"], errors="coerce")
    df["support_tickets"] = pd.to_numeric(df["support_tickets"], errors="coerce").fillna(0)
    df["satisfaction_score"] = pd.to_numeric(df["satisfaction_score"], errors="coerce")
    df["lifetime_value"] = pd.to_numeric(df["lifetime_value"], errors="coerce")

    findings = {}

    # q1: Overall aggregation
    customer_count = int(len(df))
    findings["customer_count"] = customer_count
    findings["churn_rate_pct"] = float(df["churned"].mean() * 100) if customer_count else 0.0
    findings["avg_monthly_fee"] = float(df["monthly_fee"].mean()) if customer_count else 0.0

    # q2: Churn rate by plan
    for plan, key in [
        ("Basic", "churn_rate_basic_pct"),
        ("Standard", "churn_rate_standard_pct"),
        ("Premium", "churn_rate_premium_pct"),
    ]:
        sub = df[df["plan"] == plan]
        findings[key] = float(sub["churned"].mean() * 100) if len(sub) else 0.0

    # q3: Churn rate by signup cohort (calendar year)
    cohort_year = df["signup_date"].dt.year
    for year in (2021, 2022, 2023, 2024):
        sub = df[cohort_year == year]
        findings["churn_rate_cohort_%d_pct" % year] = (
            float(sub["churned"].mean() * 100) if len(sub) else 0.0
        )

    # q4: Contract effect
    monthly = df[df["contract_type"] == "Monthly"]
    annual = df[df["contract_type"] == "Annual"]
    churn_monthly = float(monthly["churned"].mean() * 100) if len(monthly) else 0.0
    churn_annual = float(annual["churned"].mean() * 100) if len(annual) else 0.0
    findings["churn_rate_monthly_pct"] = churn_monthly
    findings["churn_rate_annual_pct"] = churn_annual
    if churn_annual != 0.0:
        findings["churn_monthly_vs_annual_change_pct"] = (
            (churn_monthly - churn_annual) / churn_annual * 100
        )
    else:
        findings["churn_monthly_vs_annual_change_pct"] = 0.0

    # q5: At-risk segment: support_tickets >= 5 and non-missing satisfaction_score <= 2
    at_risk = df[
        (df["support_tickets"] >= 5)
        & (df["satisfaction_score"].notna())
        & (df["satisfaction_score"] <= 2)
    ]
    findings["at_risk_customer_count"] = int(len(at_risk))
    findings["at_risk_churn_rate_pct"] = (
        float(at_risk["churned"].mean() * 100) if len(at_risk) else 0.0
    )

    # q6: Tenure and satisfaction summary
    findings["tenure_mean"] = float(df["tenure_months"].mean()) if customer_count else 0.0
    findings["tenure_median"] = float(df["tenure_months"].median()) if customer_count else 0.0
    findings["tenure_std"] = (
        float(df["tenure_months"].std(ddof=1)) if customer_count > 1 else 0.0
    )
    sat = df["satisfaction_score"].dropna()
    findings["satisfaction_mean"] = float(sat.mean()) if len(sat) else 0.0
    findings["satisfaction_missing_count"] = int(df["satisfaction_score"].isna().sum())

    # q7: Lifetime value by plan
    ltv = {}
    for plan, key in [
        ("Basic", "ltv_basic"),
        ("Standard", "ltv_standard"),
        ("Premium", "ltv_premium"),
    ]:
        sub = df[df["plan"] == plan]
        ltv[key] = float(sub["lifetime_value"].mean()) if len(sub) else 0.0
        findings[key] = ltv[key]
    if ltv["ltv_basic"] != 0.0:
        findings["premium_vs_basic_ltv_change_pct"] = (
            (ltv["ltv_premium"] - ltv["ltv_basic"]) / ltv["ltv_basic"] * 100
        )
    else:
        findings["premium_vs_basic_ltv_change_pct"] = 0.0

    # Guarantee every value is a finite number.
    for key, value in findings.items():
        value = float(value)
        if not np.isfinite(value):
            value = 0.0
        findings[key] = value

    with open(output_path, "w") as f:
        json.dump(findings, f, indent=2)


if __name__ == "__main__":
    main()
