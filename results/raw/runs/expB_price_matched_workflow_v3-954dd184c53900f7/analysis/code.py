"""Analysis stage for retail_sales: compute 2023-2024 sales metrics from cleaned.csv."""
import json
import math
import os

import pandas as pd


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    df = pd.read_csv(input_path, dtype={"order_id": str, "customer_id": str})
    df["order_date"] = pd.to_datetime(df["order_date"], format="%Y-%m-%d")
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
    df["discount_pct"] = pd.to_numeric(df["discount_pct"], errors="coerce")

    findings = {}

    # q1: overall performance
    total_revenue = float(df["revenue"].sum())
    order_count = int(len(df))
    findings["total_revenue"] = total_revenue
    findings["order_count"] = order_count
    findings["average_order_value"] = total_revenue / order_count if order_count > 0 else 0.0

    # q2: total revenue per region
    revenue_by_region = df.groupby("region")["revenue"].sum()
    findings["revenue_north"] = float(revenue_by_region.get("North", 0.0))
    findings["revenue_south"] = float(revenue_by_region.get("South", 0.0))
    findings["revenue_east"] = float(revenue_by_region.get("East", 0.0))
    findings["revenue_west"] = float(revenue_by_region.get("West", 0.0))

    # q3: quarterly revenue in 2024 (calendar quarters)
    df_2024 = df.loc[df["order_date"].dt.year == 2024]
    revenue_by_quarter = df_2024.groupby(df_2024["order_date"].dt.quarter)["revenue"].sum()
    findings["revenue_2024_q1"] = float(revenue_by_quarter.get(1, 0.0))
    findings["revenue_2024_q2"] = float(revenue_by_quarter.get(2, 0.0))
    findings["revenue_2024_q3"] = float(revenue_by_quarter.get(3, 0.0))
    findings["revenue_2024_q4"] = float(revenue_by_quarter.get(4, 0.0))

    # q4: year-over-year revenue change
    revenue_2023 = float(df.loc[df["order_date"].dt.year == 2023, "revenue"].sum())
    revenue_2024 = float(df_2024["revenue"].sum())
    findings["revenue_2023"] = revenue_2023
    findings["revenue_2024"] = revenue_2024
    findings["revenue_yoy_change_pct"] = (
        (revenue_2024 - revenue_2023) / revenue_2023 * 100.0 if revenue_2023 != 0.0 else 0.0
    )

    # q5: high-discount electronics orders (discount_pct >= 20)
    high_disc_electronics = df[
        (df["product_category"] == "Electronics") & (df["discount_pct"] >= 20)
    ]
    findings["electronics_high_discount_orders"] = int(len(high_disc_electronics))
    findings["electronics_high_discount_revenue"] = float(high_disc_electronics["revenue"].sum())

    # q6: order revenue distribution (sample standard deviation, ddof=1)
    findings["order_revenue_mean"] = float(df["revenue"].mean())
    findings["order_revenue_median"] = float(df["revenue"].median())
    findings["order_revenue_std"] = float(df["revenue"].std(ddof=1))
    findings["order_revenue_min"] = float(df["revenue"].min())
    findings["order_revenue_max"] = float(df["revenue"].max())

    # q7: customer concentration
    findings["unique_customer_count"] = int(df["customer_id"].nunique())
    revenue_by_customer = df.groupby("customer_id")["revenue"].sum()
    top_customer_revenue = float(revenue_by_customer.max()) if len(revenue_by_customer) > 0 else 0.0
    findings["top_customer_revenue"] = top_customer_revenue
    findings["top_customer_revenue_share_pct"] = (
        top_customer_revenue / total_revenue * 100.0 if total_revenue != 0.0 else 0.0
    )

    # Safety: guarantee every value is a finite JSON number.
    for key, value in findings.items():
        if not math.isfinite(float(value)):
            findings[key] = 0.0

    with open(output_path, "w") as f:
        json.dump(findings, f, indent=2)


if __name__ == "__main__":
    main()
