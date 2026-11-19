import json
import math
import os

import pandas as pd


def pct_rate(series):
    """Churn rate (%) of a 0/1 series; 0.0 for an empty group."""
    if len(series) == 0:
        return 0.0
    return float(series.mean() * 100.0)


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    df = pd.read_csv(input_path, dtype={"customer_id": str})
    df["signup_date"] = pd.to_datetime(df["signup_date"], format="%Y-%m-%d")
    df["satisfaction_score"] = pd.to_numeric(df["satisfaction_score"], errors="coerce")
    df["churned"] = df["churned"].astype(int)

    findings = {}

    # q1: overall
    n = len(df)
    findings["customer_count"] = int(n)
    findings["churn_rate_pct"] = pct_rate(df["churned"])
    findings["avg_monthly_fee"] = float(df["monthly_fee"].mean())

    # q2: churn by plan
    for plan, key in [
        ("Basic", "churn_rate_basic_pct"),
        ("Standard", "churn_rate_standard_pct"),
        ("Premium", "churn_rate_premium_pct"),
    ]:
        findings[key] = pct_rate(df.loc[df["plan"] == plan, "churned"])

    # q3: churn by signup cohort (calendar year)
    signup_year = df["signup_date"].dt.year
    for year in (2021, 2022, 2023, 2024):
        findings[f"churn_rate_cohort_{year}_pct"] = pct_rate(
            df.loc[signup_year == year, "churned"]
        )

    # q4: contract effect
    churn_monthly = pct_rate(df.loc[df["contract_type"] == "Monthly", "churned"])
    churn_annual = pct_rate(df.loc[df["contract_type"] == "Annual", "churned"])
    findings["churn_rate_monthly_pct"] = churn_monthly
    findings["churn_rate_annual_pct"] = churn_annual
    findings["churn_monthly_vs_annual_change_pct"] = (
        (churn_monthly - churn_annual) / churn_annual * 100.0
        if churn_annual != 0.0
        else 0.0
    )

    # q5: at-risk segment (many tickets AND low, non-missing satisfaction)
    sat = df["satisfaction_score"]
    at_risk_mask = (df["support_tickets"] >= 5) & sat.notna() & (sat <= 2)
    findings["at_risk_customer_count"] = int(at_risk_mask.sum())
    findings["at_risk_churn_rate_pct"] = pct_rate(df.loc[at_risk_mask, "churned"])

    # q6: tenure and satisfaction summary
    tenure = df["tenure_months"].astype(float)
    findings["tenure_mean"] = float(tenure.mean())
    findings["tenure_median"] = float(tenure.median())
    findings["tenure_std"] = float(tenure.std(ddof=1))
    findings["satisfaction_mean"] = float(sat.mean())
    findings["satisfaction_missing_count"] = int(sat.isna().sum())

    # q7: lifetime value by plan
    ltv_by_plan = df.groupby("plan")["lifetime_value"].mean()
    ltv_basic = float(ltv_by_plan.get("Basic", 0.0))
    ltv_standard = float(ltv_by_plan.get("Standard", 0.0))
    ltv_premium = float(ltv_by_plan.get("Premium", 0.0))
    findings["ltv_basic"] = ltv_basic
    findings["ltv_standard"] = ltv_standard
    findings["ltv_premium"] = ltv_premium
    findings["premium_vs_basic_ltv_change_pct"] = (
        (ltv_premium - ltv_basic) / ltv_basic * 100.0 if ltv_basic != 0.0 else 0.0
    )

    # guarantee flat JSON with only finite numeric values
    for key, value in findings.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"Metric {key} is not numeric: {value!r}")
        if not math.isfinite(float(value)):
            raise ValueError(f"Metric {key} is not finite: {value!r}")

    os.makedirs(os.environ["OUTPUT_DIR"], exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(findings, fh, indent=2)


if __name__ == "__main__":
    main()
