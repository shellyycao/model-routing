import json
import os

import numpy as np
import pandas as pd


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    df = pd.read_csv(input_path, parse_dates=["signup_date"])

    # Coerce analytic columns to numeric types (satisfaction_score may be missing -> NaN).
    for col in ["monthly_fee", "tenure_months", "support_tickets",
                "satisfaction_score", "churned", "lifetime_value"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    def churn_rate_pct(mask):
        """Churn rate in percent for the subset selected by a boolean mask."""
        subset = df.loc[mask, "churned"].dropna()
        if len(subset) == 0:
            return 0.0
        return float(subset.mean() * 100.0)

    findings = {}

    # q1: Overall aggregation
    findings["customer_count"] = int(len(df))
    findings["churn_rate_pct"] = float(df["churned"].mean() * 100.0)
    findings["avg_monthly_fee"] = float(df["monthly_fee"].mean())

    # q2: Churn rate by plan
    for plan, key in [("Basic", "churn_rate_basic_pct"),
                      ("Standard", "churn_rate_standard_pct"),
                      ("Premium", "churn_rate_premium_pct")]:
        findings[key] = churn_rate_pct(df["plan"] == plan)

    # q3: Churn rate by signup calendar-year cohort
    signup_year = df["signup_date"].dt.year
    for year in (2021, 2022, 2023, 2024):
        findings["churn_rate_cohort_%d_pct" % year] = churn_rate_pct(signup_year == year)

    # q4: Contract effect
    churn_monthly = churn_rate_pct(df["contract_type"] == "Monthly")
    churn_annual = churn_rate_pct(df["contract_type"] == "Annual")
    findings["churn_rate_monthly_pct"] = churn_monthly
    findings["churn_rate_annual_pct"] = churn_annual
    findings["churn_monthly_vs_annual_change_pct"] = (
        (churn_monthly - churn_annual) / churn_annual * 100.0 if churn_annual != 0.0 else 0.0
    )

    # q5: At-risk segment (>=5 support tickets and non-missing satisfaction <= 2).
    # NaN <= 2 evaluates to False in pandas, so missing scores are excluded automatically.
    at_risk_mask = (df["support_tickets"] >= 5) & (df["satisfaction_score"] <= 2)
    at_risk = df.loc[at_risk_mask]
    findings["at_risk_customer_count"] = int(len(at_risk))
    findings["at_risk_churn_rate_pct"] = (
        float(at_risk["churned"].mean() * 100.0) if len(at_risk) > 0 else 0.0
    )

    # q6: Tenure and satisfaction summary
    findings["tenure_mean"] = float(df["tenure_months"].mean())
    findings["tenure_median"] = float(df["tenure_months"].median())
    findings["tenure_std"] = float(df["tenure_months"].std(ddof=1))
    findings["satisfaction_mean"] = float(df["satisfaction_score"].mean())  # skips NaN
    findings["satisfaction_missing_count"] = int(df["satisfaction_score"].isna().sum())

    # q7: Lifetime value by plan and premium-vs-basic relative difference
    ltv_by_plan = df.groupby("plan")["lifetime_value"].mean()
    ltv_basic = float(ltv_by_plan["Basic"])
    ltv_standard = float(ltv_by_plan["Standard"])
    ltv_premium = float(ltv_by_plan["Premium"])
    findings["ltv_basic"] = ltv_basic
    findings["ltv_standard"] = ltv_standard
    findings["ltv_premium"] = ltv_premium
    findings["premium_vs_basic_ltv_change_pct"] = (
        (ltv_premium - ltv_basic) / ltv_basic * 100.0 if ltv_basic != 0.0 else 0.0
    )

    # Guarantee a flat JSON object with only finite numeric values.
    for key, value in findings.items():
        if isinstance(value, float) and not np.isfinite(value):
            raise ValueError("Non-finite value for metric %s" % key)

    with open(output_path, "w") as fh:
        json.dump(findings, fh, indent=2)


if __name__ == "__main__":
    main()
