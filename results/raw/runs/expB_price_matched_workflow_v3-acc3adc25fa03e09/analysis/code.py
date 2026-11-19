import os
import json
import math

import pandas as pd


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    df = pd.read_csv(input_path, dtype={"customer_id": str})

    # Parse signup dates (cleaning stage standardised them as YYYY-MM-DD) and
    # derive the calendar-year cohort.
    signup_year = pd.to_datetime(df["signup_date"], format="%Y-%m-%d").dt.year
    churn = df["churned"].astype(float)

    def churn_rate_pct(mask):
        """Churn rate in percent for the rows selected by mask."""
        sub = churn[mask]
        if len(sub) == 0:
            return 0.0
        return float(sub.mean() * 100.0)

    findings = {}

    # q1: Overall aggregation
    findings["customer_count"] = int(len(df))
    findings["churn_rate_pct"] = float(churn.mean() * 100.0)
    findings["avg_monthly_fee"] = float(df["monthly_fee"].mean())

    # q2: Churn rate by plan
    for plan, key in (
        ("Basic", "churn_rate_basic_pct"),
        ("Standard", "churn_rate_standard_pct"),
        ("Premium", "churn_rate_premium_pct"),
    ):
        findings[key] = churn_rate_pct(df["plan"] == plan)

    # q3: Churn rate by signup-year cohort
    for year in (2021, 2022, 2023, 2024):
        findings[f"churn_rate_cohort_{year}_pct"] = churn_rate_pct(signup_year == year)

    # q4: Contract effect
    monthly_rate = churn_rate_pct(df["contract_type"] == "Monthly")
    annual_rate = churn_rate_pct(df["contract_type"] == "Annual")
    findings["churn_rate_monthly_pct"] = monthly_rate
    findings["churn_rate_annual_pct"] = annual_rate
    if annual_rate != 0.0:
        findings["churn_monthly_vs_annual_change_pct"] = (
            (monthly_rate - annual_rate) / annual_rate * 100.0
        )
    else:
        findings["churn_monthly_vs_annual_change_pct"] = 0.0

    # q5: At-risk segment: support_tickets >= 5 and non-missing satisfaction <= 2
    sat = df["satisfaction_score"]
    at_risk_mask = (df["support_tickets"] >= 5) & sat.notna() & (sat <= 2)
    findings["at_risk_customer_count"] = int(at_risk_mask.sum())
    findings["at_risk_churn_rate_pct"] = churn_rate_pct(at_risk_mask)

    # q6: Tenure and satisfaction summary
    tenure = df["tenure_months"].astype(float)
    findings["tenure_mean"] = float(tenure.mean())
    findings["tenure_median"] = float(tenure.median())
    findings["tenure_std"] = float(tenure.std(ddof=1))  # sample std, denominator n-1
    sat_valid = sat.dropna()
    findings["satisfaction_mean"] = float(sat_valid.mean()) if len(sat_valid) > 0 else 0.0
    findings["satisfaction_missing_count"] = int(sat.isna().sum())

    # q7: Lifetime value by plan
    ltv_by_plan = df.groupby("plan")["lifetime_value"].mean()
    ltv_basic = float(ltv_by_plan.get("Basic", 0.0))
    ltv_standard = float(ltv_by_plan.get("Standard", 0.0))
    ltv_premium = float(ltv_by_plan.get("Premium", 0.0))
    findings["ltv_basic"] = ltv_basic
    findings["ltv_standard"] = ltv_standard
    findings["ltv_premium"] = ltv_premium
    if ltv_basic != 0.0:
        findings["premium_vs_basic_ltv_change_pct"] = (
            (ltv_premium - ltv_basic) / ltv_basic * 100.0
        )
    else:
        findings["premium_vs_basic_ltv_change_pct"] = 0.0

    # Safety net: guarantee every value is a finite number.
    for key, value in findings.items():
        if isinstance(value, float) and not math.isfinite(value):
            findings[key] = 0.0

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(findings, f, indent=2)


if __name__ == "__main__":
    main()
