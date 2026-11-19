import json
import math
import os

import numpy as np
import pandas as pd


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    # Read the cleaned data as produced by the cleaning stage.
    df = pd.read_csv(
        input_path,
        dtype={"order_id": str, "customer_id": str, "region": str, "product_category": str},
    )

    # Defensive type normalization (cleaned schema guarantees these parse cleanly).
    df["order_date"] = pd.to_datetime(df["order_date"], format="%Y-%m-%d", errors="coerce")
    for col in ("quantity", "unit_price", "discount_pct", "revenue"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["order_date", "revenue", "discount_pct"])

    # ---- q1: Overall performance ----
    total_revenue = float(df["revenue"].sum())
    order_count = float(len(df))
    average_order_value = total_revenue / order_count if order_count > 0 else 0.0

    # ---- q2: Regional comparison ----
    region_revenue = df.groupby("region")["revenue"].sum()
    revenue_north = float(region_revenue.get("North", 0.0))
    revenue_south = float(region_revenue.get("South", 0.0))
    revenue_east = float(region_revenue.get("East", 0.0))
    revenue_west = float(region_revenue.get("West", 0.0))

    # ---- q3: Quarterly trend in 2024 ----
    df["year"] = df["order_date"].dt.year
    df["quarter"] = df["order_date"].dt.quarter
    df_2024 = df[df["year"] == 2024]
    quarter_revenue_2024 = df_2024.groupby("quarter")["revenue"].sum()
    revenue_2024_q1 = float(quarter_revenue_2024.get(1, 0.0))
    revenue_2024_q2 = float(quarter_revenue_2024.get(2, 0.0))
    revenue_2024_q3 = float(quarter_revenue_2024.get(3, 0.0))
    revenue_2024_q4 = float(quarter_revenue_2024.get(4, 0.0))

    # ---- q4: Year-over-year change ----
    revenue_2023 = float(df.loc[df["year"] == 2023, "revenue"].sum())
    revenue_2024 = float(df_2024["revenue"].sum())
    if revenue_2023 != 0.0:
        revenue_yoy_change_pct = (revenue_2024 - revenue_2023) / revenue_2023 * 100.0
    else:
        revenue_yoy_change_pct = 0.0

    # ---- q5: High-discount electronics ----
    hd_electronics = df[
        (df["product_category"] == "Electronics") & (df["discount_pct"] >= 20.0)
    ]
    electronics_high_discount_orders = float(len(hd_electronics))
    electronics_high_discount_revenue = float(hd_electronics["revenue"].sum())

    # ---- q6: Order revenue distribution ----
    order_revenue_mean = float(df["revenue"].mean())
    order_revenue_median = float(df["revenue"].median())
    order_revenue_std = float(df["revenue"].std(ddof=1))  # sample std, denominator n-1
    order_revenue_min = float(df["revenue"].min())
    order_revenue_max = float(df["revenue"].max())

    # ---- q7: Customer concentration ----
    customer_revenue = df.groupby("customer_id")["revenue"].sum()
    unique_customer_count = float(df["customer_id"].nunique())
    top_customer_revenue = float(customer_revenue.max()) if len(customer_revenue) > 0 else 0.0
    top_customer_revenue_share_pct = (
        top_customer_revenue / total_revenue * 100.0 if total_revenue > 0 else 0.0
    )

    findings = {
        "total_revenue": total_revenue,
        "order_count": order_count,
        "average_order_value": average_order_value,
        "revenue_north": revenue_north,
        "revenue_south": revenue_south,
        "revenue_east": revenue_east,
        "revenue_west": revenue_west,
        "revenue_2024_q1": revenue_2024_q1,
        "revenue_2024_q2": revenue_2024_q2,
        "revenue_2024_q3": revenue_2024_q3,
        "revenue_2024_q4": revenue_2024_q4,
        "revenue_2023": revenue_2023,
        "revenue_2024": revenue_2024,
        "revenue_yoy_change_pct": float(revenue_yoy_change_pct),
        "electronics_high_discount_orders": electronics_high_discount_orders,
        "electronics_high_discount_revenue": electronics_high_discount_revenue,
        "order_revenue_mean": order_revenue_mean,
        "order_revenue_median": order_revenue_median,
        "order_revenue_std": order_revenue_std,
        "order_revenue_min": order_revenue_min,
        "order_revenue_max": order_revenue_max,
        "unique_customer_count": unique_customer_count,
        "top_customer_revenue": top_customer_revenue,
        "top_customer_revenue_share_pct": top_customer_revenue_share_pct,
    }

    # Guarantee every value is a finite number before serializing.
    for key, value in findings.items():
        if not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"Metric '{key}' is not a finite number: {value!r}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(findings, f, allow_nan=False)


if __name__ == "__main__":
    main()
