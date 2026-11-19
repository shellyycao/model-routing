import json
import math
import os

import pandas as pd


def pct(numerator, denominator):
    """Percentage with a guard against division by zero (returns 0.0)."""
    if denominator == 0:
        return 0.0
    return float(numerator) / float(denominator) * 100.0


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    df = pd.read_csv(input_path)
    df["signup_date"] = pd.to_datetime(df["signup_date"], errors="coerce")

    findings = {}

    # q1: overall aggregation
    n = len(df)
    findings["customer_count"] = int(n)
    findings["churn_rate_pct"] = pct(df["churned"].sum(), n)
    findings["avg_monthly_fee"] = float(df["monthly_fee"].mean())

    # q2: churn rate by plan
    for plan, key in [
        ("Basic", "churn_rate_basic_pct"),
        ("Standard", "churn_rate_standard_pct"),
        ("Premium", "churn_rate_premium_pct"),
    ]:
        sub = df[df["plan"] == plan]
        findings[key] = pct(sub["churned"].sum(), len(sub))

    # q3: churn rate by signup calendar-year cohort
    signup_year = df["signup_date"].dt.year
    for year in (2021, 2022, 2023, 2024):
        sub = df[signup_year == year]
        findings[f"churn_rate_cohort_{year}_pct"] = pct(sub["churned"].sum(), len(sub))

    # q4: contract effect
    monthly = df[df["contract_type"] == "Monthly"]
    annual = df[df["contract_type"] == "Annual"]
    churn_monthly = pct(monthly["churned"].sum(), len(monthly))
    churn_annual = pct(annual["churned"].sum(), len(annual))
    findings["churn_rate_monthly_pct"] = churn_monthly
    findings["churn_rate_annual_pct"] = churn_annual
    findings["churn_monthly_vs_annual_change_pct"] = (
        (churn_monthly - churn_annual) / churn_annual * 100.0
        if churn_annual != 0
        else 0.0
    )

    # q5: at-risk segment: many tickets AND low (non-missing) satisfaction
    sat = df["satisfaction_score"]
    at_risk = df[(df["support_tickets"] >= 5) & sat.notna() & (sat <= 2)]
    findings["at_risk_customer_count"] = int(len(at_risk))
    findings["at_risk_churn_rate_pct"] = pct(at_risk["churned"].sum(), len(at_risk))

    # q6: tenure and satisfaction summary
    findings["tenure_mean"] = float(df["tenure_months"].mean())
    findings["tenure_median"] = float(df["tenure_months"].median())
    findings["tenure_std"] = float(df["tenure_months"].std(ddof=1))
    findings["satisfaction_mean"] = float(sat.mean())
    findings["satisfaction_missing_count"] = int(sat.isna().sum())

    # q7: lifetime value by plan and premium-vs-basic relative change
    ltv_by_plan = df.groupby("plan")["lifetime_value"].mean()
    ltv_basic = float(ltv_by_plan.get("Basic", 0.0))
    ltv_standard = float(ltv_by_plan.get("Standard", 0.0))
    ltv_premium = float(ltv_by_plan.get("Premium", 0.0))
    findings["ltv_basic"] = ltv_basic
    findings["ltv_standard"] = ltv_standard
    findings["ltv_premium"] = ltv_premium
    findings["premium_vs_basic_ltv_change_pct"] = (
        (ltv_premium - ltv_basic) / ltv_basic * 100.0 if ltv_basic != 0 else 0.0
    )

    # Safety net: guarantee every value is a finite number (no NaN/Infinity)
    for key, value in findings.items():
        if isinstance(value, float) and not math.isfinite(value):
            findings[key] = 0.0

    os.makedirs(os.environ["OUTPUT_DIR"], exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(findings, f)


if __name__ == "__main__":
    main()
