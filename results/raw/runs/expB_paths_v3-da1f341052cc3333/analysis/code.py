import os
import json
import pandas as pd
import numpy as np

def main():
    # Paths
    input_dir = os.getenv("INPUT_DIR")
    output_dir = os.getenv("OUTPUT_DIR")
    cleaned_path = os.path.join(input_dir, "cleaned.csv")
    findings_path = os.path.join(output_dir, "findings.json")

    # Load cleaned data
    df = pd.read_csv(cleaned_path, parse_dates=["order_date"])

    # Basic aggregates
    total_revenue = df["revenue"].sum()
    order_count = len(df)
    average_order_value = total_revenue / order_count if order_count else 0.0

    # Regional revenue (ensure all regions appear)
    region_order = ["North", "South", "East", "West"]
    revenue_by_region = df.groupby("region")["revenue"].sum().reindex(region_order, fill_value=0.0)
    revenue_north = revenue_by_region["North"]
    revenue_south = revenue_by_region["South"]
    revenue_east = revenue_by_region["East"]
    revenue_west = revenue_by_region["West"]

    # Quarterly revenue for 2024
    df_2024 = df[df["order_date"].dt.year == 2024]
    df_2024 = df_2024.copy()
    df_2024["quarter"] = df_2024["order_date"].dt.quarter
    quarterly_rev = df_2024.groupby("quarter")["revenue"].sum().reindex([1, 2, 3, 4], fill_value=0.0)
    revenue_2024_q1 = quarterly_rev[1]
    revenue_2024_q2 = quarterly_rev[2]
    revenue_2024_q3 = quarterly_rev[3]
    revenue_2024_q4 = quarterly_rev[4]

    # Yearly revenue and YoY change
    revenue_2023 = df[df["order_date"].dt.year == 2023]["revenue"].sum()
    revenue_2024 = total_revenue - revenue_2023  # alternatively sum of df_2024
    revenue_yoy_change_pct = ((revenue_2024 - revenue_2023) / revenue_2023 * 100) if revenue_2023 != 0 else 0.0

    # High‑discount electronics
    high_disc_elec = df[(df["product_category"] == "Electronics") & (df["discount_pct"] >= 20)]
    electronics_high_discount_orders = len(high_disc_elec)
    electronics_high_discount_revenue = high_disc_elec["revenue"].sum()

    # Revenue distribution statistics
    order_revenue_mean = df["revenue"].mean()
    order_revenue_median = df["revenue"].median()
    order_revenue_std = df["revenue"].std(ddof=1)  # sample std
    order_revenue_min = df["revenue"].min()
    order_revenue_max = df["revenue"].max()

    # Customer concentration
    revenue_by_customer = df.groupby("customer_id")["revenue"].sum()
    unique_customer_count = revenue_by_customer.shape[0]
    top_customer_revenue = revenue_by_customer.max()
    top_customer_revenue_share_pct = (top_customer_revenue / total_revenue * 100) if total_revenue != 0 else 0.0

    # Assemble findings dictionary with plain Python scalars
    findings = {
        "total_revenue": float(total_revenue),
        "order_count": int(order_count),
        "average_order_value": float(average_order_value),
        "revenue_north": float(revenue_north),
        "revenue_south": float(revenue_south),
        "revenue_east": float(revenue_east),
        "revenue_west": float(revenue_west),
        "revenue_2024_q1": float(revenue_2024_q1),
        "revenue_2024_q2": float(revenue_2024_q2),
        "revenue_2024_q3": float(revenue_2024_q3),
        "revenue_2024_q4": float(revenue_2024_q4),
        "revenue_2023": float(revenue_2023),
        "revenue_2024": float(revenue_2024),
        "revenue_yoy_change_pct": float(revenue_yoy_change_pct),
        "electronics_high_discount_orders": int(electronics_high_discount_orders),
        "electronics_high_discount_revenue": float(electronics_high_discount_revenue),
        "order_revenue_mean": float(order_revenue_mean),
        "order_revenue_median": float(order_revenue_median),
        "order_revenue_std": float(order_revenue_std),
        "order_revenue_min": float(order_revenue_min),
        "order_revenue_max": float(order_revenue_max),
        "unique_customer_count": int(unique_customer_count),
        "top_customer_revenue": float(top_customer_revenue),
        "top_customer_revenue_share_pct": float(top_customer_revenue_share_pct)
    }

    # Write findings to JSON
    with open(findings_path, "w", encoding="utf-8") as f:
        json.dump(findings, f, ensure_ascii=False, separators=(',', ':'))

if __name__ == "__main__":
    main()
