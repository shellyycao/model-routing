import json
import os

import numpy as np
import pandas as pd


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    df = pd.read_csv(input_path)
    df["signup_date"] = pd.to_datetime(df["signup_date"], format="%Y-%m-%d")

    def rate_pct(churned_count, total):
        if total == 0:
            return 0.0
        return float(churned_count) / float(total) * 100.0

    findings = {}

    # q1: overall metrics
    customer_count = int(len(df))
    findings["customer_count"] = customer_count
    findings["churn_rate_pct"] = rate_pct(int((df["churned"] == 1).sum()), customer_count)
    findings["avg_monthly_fee"] = float(df["monthly_fee"].mean())

    # q2: churn rate by plan
    for plan, key in (("Basic", "churn_rate_basic_pct"),
                      ("Standard", "churn_rate_standard_pct"),
                      ("Premium", "churn_rate_premium_pct")):
        sub = df[df["plan"] == plan]
        findings[key] = rate_pct(int((sub["churned"] == 1).sum()), len(sub))

    # q3: churn rate by signup cohort (calendar year)
    signup_year = df["signup_date"].dt.year
    for year in (2021, 2022, 2023, 2024):
        sub = df[signup_year == year]
        findings["churn_rate_cohort_%d_pct" % year] = rate_pct(
            int((sub["churned"] == 1).sum()), len(sub))

    # q4: contract effect
    monthly = df[df["contract_type"] == "Monthly"]
    annual = df[df["contract_type"] == "Annual"]
    churn_monthly = rate_pct(int((monthly["churned"] == 1).sum()), len(monthly))
    churn_annual = rate_pct(int((annual["churned"] == 1).sum()), len(annual))
    findings["churn_rate_monthly_pct"] = churn_monthly
    findings["churn_rate_annual_pct"] = churn_annual
    if churn_annual == 0.0:
        findings["churn_monthly_vs_annual_change_pct"] = 0.0
    else:
        findings["churn_monthly_vs_annual_change_pct"] = (
            (churn_monthly - churn_annual) / churn_annual * 100.0)

    # q5: at-risk segment (support_tickets >= 5 and non-missing satisfaction_score <= 2)
    sat = df["satisfaction_score"]
    at_risk_mask = (df["support_tickets"] >= 5) & sat.notna() & (sat <= 2)
    at_risk = df[at_risk_mask]
    findings["at_risk_customer_count"] = int(len(at_risk))
    findings["at_risk_churn_rate_pct"] = rate_pct(
        int((at_risk["churned"] == 1).sum()), len(at_risk))

    # q6: tenure and satisfaction summary
    tenure = df["tenure_months"]
    findings["tenure_mean"] = float(tenure.mean())
    findings["tenure_median"] = float(tenure.median())
    findings["tenure_std"] = float(tenure.std(ddof=1))
    findings["satisfaction_mean"] = float(sat.dropna().mean())
    findings["satisfaction_missing_count"] = int(sat.isna().sum())

    # q7: lifetime value by plan
    ltv = {}
    for plan, key in (("Basic", "ltv_basic"),
                      ("Standard", "ltv_standard"),
                      ("Premium", "ltv_premium")):
        sub = df[df["plan"] == plan]
        value = float(sub["lifetime_value"].mean()) if len(sub) > 0 else 0.0
        ltv[plan] = value
        findings[key] = value
    if ltv["Basic"] == 0.0:
        findings["premium_vs_basic_ltv_change_pct"] = 0.0
    else:
        findings["premium_vs_basic_ltv_change_pct"] = (
            (ltv["Premium"] - ltv["Basic"]) / ltv["Basic"] * 100.0)

    # Guarantee a flat object of finite numbers only
    clean = {}
    for key, value in findings.items():
        fv = float(value)
        clean[key] = fv if np.isfinite(fv) else 0.0

    with open(output_path, "w") as f:
        json.dump(clean, f, indent=2)


if __name__ == "__main__":
    main()
