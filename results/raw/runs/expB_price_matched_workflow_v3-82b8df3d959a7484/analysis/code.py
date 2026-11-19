import json
import math
import os

import numpy as np
import pandas as pd


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    df = pd.read_csv(input_path)

    # Ensure the columns we rely on have usable dtypes (no-op if already clean).
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
    df["discount_pct"] = pd.to_numeric(df["discount_pct"], errors="coerce")
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")

    findings = {}

    # q1: overall performance
    total_revenue = float(df["revenue"].sum())
    order_count = int(len(df))
    findings["total_revenue"] = total_revenue
    findings["order_count"] = float(order_count)
    findings["average_order_value"] = total_revenue / order_count if order_count else 0.0

    # q2: regional comparison
    revenue_by_region = df.groupby("region")["revenue"].sum()
    for region in ("North", "South", "East", "West"):
        findings["revenue_" + region.lower()] = float(revenue_by_region.get(region, 0.0))

    # q3: 2024 quarterly trend
    df["year"] = df["order_date"].dt.year
    df["quarter"] = df["order_date"].dt.quarter
    df_2024 = df[df["year"] == 2024]
    revenue_by_quarter_2024 = df_2024.groupby("quarter")["revenue"].sum()
    for q in (1, 2, 3, 4):
        findings["revenue_2024_q" + str(q)] = float(revenue_by_quarter_2024.get(q, 0.0))

    # q4: year-over-year change
    revenue_2023 = float(df.loc[df["year"] == 2023, "revenue"].sum())
    revenue_2024 = float(df.loc[df["year"] == 2024, "revenue"].sum())
    findings["revenue_2023"] = revenue_2023
    findings["revenue_2024"] = revenue_2024
    findings["revenue_yoy_change_pct"] = (
        (revenue_2024 - revenue_2023) / revenue_2023 * 100.0 if revenue_2023 else 0.0
    )

    # q5: high-discount electronics orders
    hd_mask = (df["product_category"] == "Electronics") & (df["discount_pct"] >= 20)
    findings["electronics_high_discount_orders"] = float(int(hd_mask.sum()))
    findings["electronics_high_discount_revenue"] = float(df.loc[hd_mask, "revenue"].sum())

    # q6: order revenue distribution (sample std, ddof=1)
    rev = df["revenue"]
    findings["order_revenue_mean"] = float(rev.mean())
    findings["order_revenue_median"] = float(rev.median())
    findings["order_revenue_std"] = float(rev.std(ddof=1))
    findings["order_revenue_min"] = float(rev.min())
    findings["order_revenue_max"] = float(rev.max())

    # q7: customer concentration
    revenue_by_customer = df.groupby("customer_id")["revenue"].sum()
    unique_customer_count = int(df["customer_id"].nunique())
    top_customer_revenue = float(revenue_by_customer.max()) if len(revenue_by_customer) else 0.0
    findings["unique_customer_count"] = float(unique_customer_count)
    findings["top_customer_revenue"] = top_customer_revenue
    findings["top_customer_revenue_share_pct"] = (
        top_customer_revenue / total_revenue * 100.0 if total_revenue else 0.0
    )

    # Guarantee a flat object of finite numbers only.
    clean_findings = {}
    for key, value in findings.items():
        value = float(value)
        clean_findings[key] = value if math.isfinite(value) else 0.0

    with open(output_path, "w") as f:
        json.dump(clean_findings, f, indent=2)


if __name__ == "__main__":
    main()
