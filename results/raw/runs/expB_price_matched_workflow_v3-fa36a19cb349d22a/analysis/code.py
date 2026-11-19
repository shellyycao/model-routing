import json
import math
import os

import numpy as np
import pandas as pd


def churn_rate_pct(series):
    """Churn rate in percent for a churned (0/1) series; 0.0 for empty groups."""
    if len(series) == 0:
        return 0.0
    return float(series.mean() * 100.0)


def finite(value):
    """Coerce to a finite Python float; fall back to 0.0 for NaN/inf."""
    v = float(value)
    return v if math.isfinite(v) else 0.0


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    df = pd.read_csv(input_path)

    findings = {}

    # q1: overall aggregation
    findings["customer_count"] = int(len(df))
    findings["churn_rate_pct"] = churn_rate_pct(df["churned"])
    findings["avg_monthly_fee"] = float(df["monthly_fee"].mean())

    # q2: churn rate by plan
    for plan, key in [
        ("Basic", "churn_rate_basic_pct"),
        ("Standard", "churn_rate_standard_pct"),
        ("Premium", "churn_rate_premium_pct"),
    ]:
        findings[key] = churn_rate_pct(df.loc[df["plan"] == plan, "churned"])

    # q3: churn rate by signup cohort (calendar year)
    signup_year = pd.to_datetime(df["signup_date"], format="%Y-%m-%d").dt.year
    for year in (2021, 2022, 2023, 2024):
        findings[f"churn_rate_cohort_{year}_pct"] = churn_rate_pct(
            df.loc[signup_year == year, "churned"]
        )

    # q4: contract effect
    monthly_rate = churn_rate_pct(df.loc[df["contract_type"] == "Monthly", "churned"])
    annual_rate = churn_rate_pct(df.loc[df["contract_type"] == "Annual", "churned"])
    findings["churn_rate_monthly_pct"] = monthly_rate
    findings["churn_rate_annual_pct"] = annual_rate
    if annual_rate != 0.0:
        findings["churn_monthly_vs_annual_change_pct"] = (
            (monthly_rate - annual_rate) / annual_rate * 100.0
        )
    else:
        findings["churn_monthly_vs_annual_change_pct"] = 0.0

    # q5: at-risk segment (>=5 support tickets and non-missing satisfaction <= 2)
    at_risk_mask = (
        (df["support_tickets"] >= 5)
        & df["satisfaction_score"].notna()
        & (df["satisfaction_score"] <= 2)
    )
    at_risk = df.loc[at_risk_mask]
    findings["at_risk_customer_count"] = int(len(at_risk))
    findings["at_risk_churn_rate_pct"] = churn_rate_pct(at_risk["churned"])

    # q6: tenure and satisfaction summary
    findings["tenure_mean"] = float(df["tenure_months"].mean())
    findings["tenure_median"] = float(df["tenure_months"].median())
    findings["tenure_std"] = float(df["tenure_months"].std(ddof=1))
    findings["satisfaction_mean"] = float(df["satisfaction_score"].mean(skipna=True))
    findings["satisfaction_missing_count"] = int(df["satisfaction_score"].isna().sum())

    # q7: lifetime value by plan
    ltv_by_plan = df.groupby("plan")["lifetime_value"].mean()
    ltv_basic = float(ltv_by_plan.get("Basic", np.nan))
    ltv_standard = float(ltv_by_plan.get("Standard", np.nan))
    ltv_premium = float(ltv_by_plan.get("Premium", np.nan))
    findings["ltv_basic"] = ltv_basic
    findings["ltv_standard"] = ltv_standard
    findings["ltv_premium"] = ltv_premium
    if math.isfinite(ltv_basic) and ltv_basic != 0.0 and math.isfinite(ltv_premium):
        findings["premium_vs_basic_ltv_change_pct"] = (
            (ltv_premium - ltv_basic) / ltv_basic * 100.0
        )
    else:
        findings["premium_vs_basic_ltv_change_pct"] = 0.0

    # Guarantee every value is a finite JSON number (full precision, no rounding).
    clean = {
        key: (int(value) if isinstance(value, int) else finite(value))
        for key, value in findings.items()
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(clean, f, allow_nan=False)


if __name__ == "__main__":
    main()
