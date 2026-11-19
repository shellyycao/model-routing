import os
import json
import pandas as pd
import numpy as np

def main():
    # Paths from environment variables
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    # Load cleaned data
    df = pd.read_csv(input_path, parse_dates=["order_date"])

    # Basic aggregates
    total_revenue = float(df["revenue"].sum())
    order_count = int(df.shape[0])
    average_order_value = total_revenue / order_count if order_count else 0.0

    # Regional revenue
    regions = ["North", "South", "East", "West"]
    regional_rev = {}
    for r in regions:
        regional_rev[r] = float(df.loc[df["region"] == r, "revenue"].sum())

    # Yearly and quarterly revenue for 2023 and 2024
    df["year"] = df["order_date"].dt.year
    df["quarter"] = df["order_date"].dt.quarter

    revenue_2023 = float(df.loc[df["year"] == 2023, "revenue"].sum())
    revenue_2024 = float(df.loc[df["year"] == 2024, "revenue"].sum())
    revenue_yoy_change_pct = (
        (revenue_2024 - revenue_2023) / revenue_2023 * 100 if revenue_2023 else 0.0
    )

    # Quarterly revenue for 2024
    q_rev = {}
    for q in range(1, 5):
        q_rev[q] = float(df.loc[(df["year"] == 2024) & (df["quarter"] == q), "revenue"].sum())

    # High‑discount electronics
    elec_high = df[(df["product_category"] == "Electronics") & (df["discount_pct"] >= 20)]
    electronics_high_discount_orders = int(elec_high.shape[0])
    electronics_high_discount_revenue = float(elec_high["revenue"].sum())

    # Revenue distribution statistics
    order_revenue_mean = float(df["revenue"].mean())
    order_revenue_median = float(df["revenue"].median())
    order_revenue_std = float(df["revenue"].std(ddof=1))
    if np.isnan(order_revenue_std):
        order_revenue_std = 0.0
    order_revenue_min = float(df["revenue"].min())
    order_revenue_max = float(df["revenue"].max())

    # Customer concentration
    unique_customer_count = int(df["customer_id"].nunique())
    customer_rev = df.groupby("customer_id")["revenue"].sum()
    top_customer_revenue = float(customer_rev.max())
    top_customer_revenue_share_pct = (
        top_customer_revenue / total_revenue * 100 if total_revenue else 0.0
    )

    # Assemble findings dictionary
    findings = {
        "total_revenue": total_revenue,
        "order_count": order_count,
        "average_order_value": average_order_value,
        "revenue_north": regional_rev["North"],
        "revenue_south": regional_rev["South"],
        "revenue_east": regional_rev["East"],
        "revenue_west": regional_rev["West"],
        "revenue_2024_q1": q_rev[1],
        "revenue_2024_q2": q_rev[2],
        "revenue_2024_q3": q_rev[3],
        "revenue_2024_q4": q_rev[4],
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

    # Write findings to JSON file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(findings, f, ensure_ascii=False)

if __name__ == "__main__":
    main()
