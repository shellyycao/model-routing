"""Analysis stage for the retail_sales project.

Reads the cleaned order data produced by the cleaning stage, computes the
required business metrics, and writes them as a flat JSON object to
findings.json.
"""

import json
import math
import os

import pandas as pd


def main() -> None:
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    df = pd.read_csv(input_path, parse_dates=["order_date"])

    revenue = df["revenue"].astype(float)
    year = df["order_date"].dt.year

    # q1: overall performance
    total_revenue = float(revenue.sum())
    order_count = int(len(df))
    average_order_value = total_revenue / order_count

    # q2: regional comparison
    revenue_by_region = df.groupby("region")["revenue"].sum()

    # q3: quarterly trend in 2024
    mask_2024 = year == 2024
    df_2024 = df.loc[mask_2024]
    revenue_2024_by_quarter = df_2024.groupby(df_2024["order_date"].dt.quarter)["revenue"].sum()

    # q4: year-over-year change
    revenue_2023 = float(revenue[year == 2023].sum())
    revenue_2024 = float(revenue[mask_2024].sum())
    revenue_yoy_change_pct = (revenue_2024 - revenue_2023) / revenue_2023 * 100.0

    # q5: high-discount electronics orders
    mask_hd_elec = (df["product_category"] == "Electronics") & (df["discount_pct"] >= 20.0)
    electronics_high_discount_orders = int(mask_hd_elec.sum())
    electronics_high_discount_revenue = float(revenue[mask_hd_elec].sum())

    # q6: order revenue distribution (sample standard deviation, ddof=1)
    order_revenue_mean = float(revenue.mean())
    order_revenue_median = float(revenue.median())
    order_revenue_std = float(revenue.std(ddof=1))
    order_revenue_min = float(revenue.min())
    order_revenue_max = float(revenue.max())

    # q7: customer concentration
    unique_customer_count = int(df["customer_id"].nunique())
    revenue_by_customer = df.groupby("customer_id")["revenue"].sum()
    top_customer_revenue = float(revenue_by_customer.max())
    top_customer_revenue_share_pct = top_customer_revenue / total_revenue * 100.0

    findings = {
        "total_revenue": total_revenue,
        "order_count": order_count,
        "average_order_value": average_order_value,
        "revenue_north": float(revenue_by_region.get("North", 0.0)),
        "revenue_south": float(revenue_by_region.get("South", 0.0)),
        "revenue_east": float(revenue_by_region.get("East", 0.0)),
        "revenue_west": float(revenue_by_region.get("West", 0.0)),
        "revenue_2024_q1": float(revenue_2024_by_quarter.get(1, 0.0)),
        "revenue_2024_q2": float(revenue_2024_by_quarter.get(2, 0.0)),
        "revenue_2024_q3": float(revenue_2024_by_quarter.get(3, 0.0)),
        "revenue_2024_q4": float(revenue_2024_by_quarter.get(4, 0.0)),
        "revenue_2023": revenue_2023,
        "revenue_2024": revenue_2024,
        "revenue_yoy_change_pct": revenue_yoy_change_pct,
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

    for key, value in findings.items():
        if not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"Metric {key!r} is not a finite number: {value!r}")

    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(findings, fh, indent=2)


if __name__ == "__main__":
    main()
