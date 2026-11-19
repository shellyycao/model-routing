import json
import os

import numpy as np
import pandas as pd


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    df = pd.read_csv(input_path)
    df["order_date"] = pd.to_datetime(df["order_date"], format="%Y-%m-%d")
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
    df["discount_pct"] = pd.to_numeric(df["discount_pct"], errors="coerce")

    findings = {}

    # q1: Overall performance
    total_revenue = float(df["revenue"].sum())
    order_count = int(len(df))
    findings["total_revenue"] = total_revenue
    findings["order_count"] = order_count
    findings["average_order_value"] = (
        total_revenue / order_count if order_count > 0 else 0.0
    )

    # q2: Regional comparison (total revenue per region)
    region_revenue = df.groupby("region")["revenue"].sum()
    for region, key in (
        ("North", "revenue_north"),
        ("South", "revenue_south"),
        ("East", "revenue_east"),
        ("West", "revenue_west"),
    ):
        findings[key] = float(region_revenue.get(region, 0.0))

    # q3: Quarterly trend in 2024
    df_2024 = df[df["order_date"].dt.year == 2024]
    quarterly = df_2024.groupby(df_2024["order_date"].dt.quarter)["revenue"].sum()
    for quarter in (1, 2, 3, 4):
        findings[f"revenue_2024_q{quarter}"] = float(quarterly.get(quarter, 0.0))

    # q4: Year-over-year change
    revenue_2023 = float(df.loc[df["order_date"].dt.year == 2023, "revenue"].sum())
    revenue_2024 = float(df.loc[df["order_date"].dt.year == 2024, "revenue"].sum())
    findings["revenue_2023"] = revenue_2023
    findings["revenue_2024"] = revenue_2024
    findings["revenue_yoy_change_pct"] = (
        (revenue_2024 - revenue_2023) / revenue_2023 * 100.0
        if revenue_2023 != 0.0
        else 0.0
    )

    # q5: High-discount electronics orders (Electronics with discount_pct >= 20)
    high_discount = df[
        (df["product_category"] == "Electronics") & (df["discount_pct"] >= 20)
    ]
    findings["electronics_high_discount_orders"] = int(len(high_discount))
    findings["electronics_high_discount_revenue"] = float(high_discount["revenue"].sum())

    # q6: Order revenue distribution over all orders
    revenue = df["revenue"]
    findings["order_revenue_mean"] = float(revenue.mean())
    findings["order_revenue_median"] = float(revenue.median())
    findings["order_revenue_std"] = float(revenue.std(ddof=1))
    findings["order_revenue_min"] = float(revenue.min())
    findings["order_revenue_max"] = float(revenue.max())

    # q7: Customer concentration
    findings["unique_customer_count"] = int(df["customer_id"].nunique())
    customer_revenue = df.groupby("customer_id")["revenue"].sum()
    top_customer_revenue = float(customer_revenue.max()) if len(customer_revenue) else 0.0
    findings["top_customer_revenue"] = top_customer_revenue
    findings["top_customer_revenue_share_pct"] = (
        top_customer_revenue / total_revenue * 100.0 if total_revenue != 0.0 else 0.0
    )

    # Guarantee a flat object of finite numbers only
    for key, value in findings.items():
        if isinstance(value, float) and not np.isfinite(value):
            findings[key] = 0.0

    with open(output_path, "w") as f:
        json.dump(findings, f, indent=2)


if __name__ == "__main__":
    main()
