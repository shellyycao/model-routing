import json
import math
import os

import pandas as pd


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    df = pd.read_csv(
        input_path,
        dtype={"order_id": str, "customer_id": str, "region": str, "product_category": str},
    )
    df["order_date"] = pd.to_datetime(df["order_date"], format="%Y-%m-%d")
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
    df["discount_pct"] = pd.to_numeric(df["discount_pct"], errors="coerce")

    findings = {}

    # q1: Overall performance
    total_revenue = float(df["revenue"].sum())
    order_count = int(len(df))
    findings["total_revenue"] = total_revenue
    findings["order_count"] = order_count
    findings["average_order_value"] = total_revenue / order_count if order_count else 0.0

    # q2: Regional comparison
    region_revenue = df.groupby("region")["revenue"].sum()
    findings["revenue_north"] = float(region_revenue.get("North", 0.0))
    findings["revenue_south"] = float(region_revenue.get("South", 0.0))
    findings["revenue_east"] = float(region_revenue.get("East", 0.0))
    findings["revenue_west"] = float(region_revenue.get("West", 0.0))

    # q3: Quarterly trend in 2024
    df["year"] = df["order_date"].dt.year
    df["quarter"] = df["order_date"].dt.quarter
    df_2024 = df[df["year"] == 2024]
    quarter_revenue = df_2024.groupby("quarter")["revenue"].sum()
    for q in (1, 2, 3, 4):
        findings[f"revenue_2024_q{q}"] = float(quarter_revenue.get(q, 0.0))

    # q4: Year-over-year change
    revenue_2023 = float(df.loc[df["year"] == 2023, "revenue"].sum())
    revenue_2024 = float(df.loc[df["year"] == 2024, "revenue"].sum())
    findings["revenue_2023"] = revenue_2023
    findings["revenue_2024"] = revenue_2024
    findings["revenue_yoy_change_pct"] = (
        (revenue_2024 - revenue_2023) / revenue_2023 * 100.0 if revenue_2023 else 0.0
    )

    # q5: High-discount electronics
    hd_mask = (df["product_category"] == "Electronics") & (df["discount_pct"] >= 20)
    findings["electronics_high_discount_orders"] = int(hd_mask.sum())
    findings["electronics_high_discount_revenue"] = float(df.loc[hd_mask, "revenue"].sum())

    # q6: Order revenue distribution
    revenue = df["revenue"]
    findings["order_revenue_mean"] = float(revenue.mean())
    findings["order_revenue_median"] = float(revenue.median())
    findings["order_revenue_std"] = float(revenue.std(ddof=1))
    findings["order_revenue_min"] = float(revenue.min())
    findings["order_revenue_max"] = float(revenue.max())

    # q7: Customer concentration
    customer_revenue = df.groupby("customer_id")["revenue"].sum()
    unique_customer_count = int(df["customer_id"].nunique())
    top_customer_revenue = float(customer_revenue.max()) if len(customer_revenue) else 0.0
    findings["unique_customer_count"] = unique_customer_count
    findings["top_customer_revenue"] = top_customer_revenue
    findings["top_customer_revenue_share_pct"] = (
        top_customer_revenue / total_revenue * 100.0 if total_revenue else 0.0
    )

    # Ensure a flat object of finite floats only (full precision, no rounding)
    clean_findings = {}
    for key, value in findings.items():
        numeric = float(value)
        clean_findings[key] = numeric if math.isfinite(numeric) else 0.0

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(clean_findings, f, indent=2)


if __name__ == "__main__":
    main()
