import json
import os

import numpy as np
import pandas as pd


def churn_rate_pct(churned_series):
    """Churn rate in percent for a (possibly empty) churned 0/1 series."""
    if len(churned_series) == 0:
        return 0.0
    return float(churned_series.mean() * 100.0)


def safe_pct_change(numerator, denominator):
    """(numerator / denominator) * 100 with a zero-denominator guard."""
    if denominator == 0:
        return 0.0
    return float(numerator / denominator * 100.0)


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    df = pd.read_csv(input_path)
    df["signup_date"] = pd.to_datetime(df["signup_date"], format="%Y-%m-%d")
    df["signup_year"] = df["signup_date"].dt.year
    # satisfaction_score arrives as float with NaN for empty cells (cleaning R12)

    findings = {}

    # q1: overall aggregation
    findings["customer_count"] = float(len(df))
    findings["churn_rate_pct"] = churn_rate_pct(df["churned"])
    findings["avg_monthly_fee"] = float(df["monthly_fee"].mean())

    # q2: churn rate by plan
    for plan, key in (("Basic", "churn_rate_basic_pct"),
                      ("Standard", "churn_rate_standard_pct"),
                      ("Premium", "churn_rate_premium_pct")):
        findings[key] = churn_rate_pct(df.loc[df["plan"] == plan, "churned"])

    # q3: churn rate by signup calendar-year cohort
    for year in (2021, 2022, 2023, 2024):
        findings["churn_rate_cohort_{}_pct".format(year)] = churn_rate_pct(
            df.loc[df["signup_year"] == year, "churned"]
        )

    # q4: contract effect
    monthly_rate = churn_rate_pct(df.loc[df["contract_type"] == "Monthly", "churned"])
    annual_rate = churn_rate_pct(df.loc[df["contract_type"] == "Annual", "churned"])
    findings["churn_rate_monthly_pct"] = monthly_rate
    findings["churn_rate_annual_pct"] = annual_rate
    findings["churn_monthly_vs_annual_change_pct"] = safe_pct_change(
        monthly_rate - annual_rate, annual_rate
    )

    # q5: at-risk segment (support_tickets >= 5 and non-missing satisfaction_score <= 2)
    at_risk_mask = (
        (df["support_tickets"] >= 5)
        & df["satisfaction_score"].notna()
        & (df["satisfaction_score"] <= 2)
    )
    at_risk = df.loc[at_risk_mask]
    findings["at_risk_customer_count"] = float(len(at_risk))
    findings["at_risk_churn_rate_pct"] = churn_rate_pct(at_risk["churned"])

    # q6: tenure and satisfaction summary
    tenure = df["tenure_months"].astype(float)
    findings["tenure_mean"] = float(tenure.mean())
    findings["tenure_median"] = float(tenure.median())
    tenure_std = float(tenure.std(ddof=1))
    findings["tenure_std"] = tenure_std if np.isfinite(tenure_std) else 0.0
    satisfaction = df["satisfaction_score"].dropna()
    findings["satisfaction_mean"] = float(satisfaction.mean()) if len(satisfaction) > 0 else 0.0
    findings["satisfaction_missing_count"] = float(df["satisfaction_score"].isna().sum())

    # q7: lifetime value by plan
    ltv = {}
    for plan, key in (("Basic", "ltv_basic"),
                      ("Standard", "ltv_standard"),
                      ("Premium", "ltv_premium")):
        sub = df.loc[df["plan"] == plan, "lifetime_value"]
        ltv[key] = float(sub.mean()) if len(sub) > 0 else 0.0
        findings[key] = ltv[key]
    findings["premium_vs_basic_ltv_change_pct"] = safe_pct_change(
        ltv["ltv_premium"] - ltv["ltv_basic"], ltv["ltv_basic"]
    )

    # Final safety: every value must be a finite number
    for key, value in findings.items():
        if not np.isfinite(value):
            findings[key] = 0.0

    with open(output_path, "w") as f:
        json.dump(findings, f)


if __name__ == "__main__":
    main()
