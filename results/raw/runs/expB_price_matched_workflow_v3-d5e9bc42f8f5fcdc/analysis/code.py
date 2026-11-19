import json
import os

import numpy as np
import pandas as pd


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    df = pd.read_csv(input_path)

    findings = {}

    def churn_rate_pct(sub):
        """Churn rate in percent for a subset; 0.0 for an empty subset."""
        if len(sub) == 0:
            return 0.0
        return float(sub["churned"].mean() * 100)

    # q1: overall metrics
    findings["customer_count"] = int(len(df))
    findings["churn_rate_pct"] = float(df["churned"].mean() * 100)
    findings["avg_monthly_fee"] = float(df["monthly_fee"].mean())

    # q2: churn rate by plan
    for plan, key in [
        ("Basic", "churn_rate_basic_pct"),
        ("Standard", "churn_rate_standard_pct"),
        ("Premium", "churn_rate_premium_pct"),
    ]:
        findings[key] = churn_rate_pct(df[df["plan"] == plan])

    # q3: churn rate by signup cohort (calendar year)
    signup_year = pd.to_datetime(df["signup_date"]).dt.year
    for year in (2021, 2022, 2023, 2024):
        findings[f"churn_rate_cohort_{year}_pct"] = churn_rate_pct(
            df[signup_year == year]
        )

    # q4: contract effect
    churn_monthly = churn_rate_pct(df[df["contract_type"] == "Monthly"])
    churn_annual = churn_rate_pct(df[df["contract_type"] == "Annual"])
    findings["churn_rate_monthly_pct"] = churn_monthly
    findings["churn_rate_annual_pct"] = churn_annual
    if churn_annual == 0:
        findings["churn_monthly_vs_annual_change_pct"] = 0.0
    else:
        findings["churn_monthly_vs_annual_change_pct"] = float(
            (churn_monthly - churn_annual) / churn_annual * 100
        )

    # q5: at-risk segment: support_tickets >= 5 and non-missing satisfaction_score <= 2
    satisfaction = pd.to_numeric(df["satisfaction_score"], errors="coerce")
    at_risk_mask = (
        (df["support_tickets"] >= 5) & satisfaction.notna() & (satisfaction <= 2)
    )
    at_risk = df[at_risk_mask]
    findings["at_risk_customer_count"] = int(len(at_risk))
    findings["at_risk_churn_rate_pct"] = churn_rate_pct(at_risk)

    # q6: tenure and satisfaction summary
    tenure = pd.to_numeric(df["tenure_months"], errors="coerce")
    findings["tenure_mean"] = float(tenure.mean())
    findings["tenure_median"] = float(tenure.median())
    findings["tenure_std"] = float(tenure.std(ddof=1))
    findings["satisfaction_mean"] = float(satisfaction.mean())
    findings["satisfaction_missing_count"] = int(satisfaction.isna().sum())

    # q7: lifetime value by plan
    ltv_basic = float(df.loc[df["plan"] == "Basic", "lifetime_value"].mean())
    ltv_standard = float(df.loc[df["plan"] == "Standard", "lifetime_value"].mean())
    ltv_premium = float(df.loc[df["plan"] == "Premium", "lifetime_value"].mean())
    findings["ltv_basic"] = ltv_basic
    findings["ltv_standard"] = ltv_standard
    findings["ltv_premium"] = ltv_premium
    if ltv_basic == 0:
        findings["premium_vs_basic_ltv_change_pct"] = 0.0
    else:
        findings["premium_vs_basic_ltv_change_pct"] = float(
            (ltv_premium - ltv_basic) / ltv_basic * 100
        )

    # Safety: guarantee every value is a finite number (no NaN/Infinity).
    for key, value in list(findings.items()):
        if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
            findings[key] = 0.0

    with open(output_path, "w") as f:
        json.dump(findings, f, indent=2)


if __name__ == "__main__":
    main()
