import os
import json
import pandas as pd
import numpy as np

def main():
    # Paths
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    # Load cleaned data
    df = pd.read_csv(input_path, parse_dates=["order_date"])

    # Basic aggregations
    total_revenue = df["revenue"].sum()
    order_count = len(df)
    average_order_value = total_revenue / order_count if order_count else 0.0

    # Revenue per region
    revenue_north = df.loc[df["region"] == "North", "revenue"].sum()
    revenue_south = df.loc[df["region"] == "South", "revenue"].sum()
    revenue_east = df.loc[df["region"] == "East", "revenue"].sum()
    revenue_west = df.loc[df["region"] == "West", "revenue"].sum()

    # Quarterly revenue for 2024
    df_2024 = df[df["order_date"].dt.year == 2024]
    # pandas provides .dt.quarter (1‑4)
    revenue_2024_q1 = df_2024.loc[df_2024["order_date"].dt.quarter == 1, "revenue"].sum()
    revenue_2024_q2 = df_2024.loc[df_2024["order_date"].dt.quarter == 2, "revenue"].sum()
    revenue_2024_q3 = df_2024.loc[df_2024["order_date"].dt.quarter == 3, "revenue"].sum()
    revenue_2024_q4 = df_2024.loc[df_2024["order_date"].dt.quarter == 4, "revenue"].sum()

    # Year‑over‑year revenue
    revenue_2023 = df.loc[df["order_date"].dt.year == 2023, "revenue"].sum()
    revenue_2024 = df.loc[df["order_date"].dt.year == 2024, "revenue"].sum()
    if revenue_2023 != 0:
        revenue_yoy_change_pct = (revenue_2024 - revenue_2023) / revenue_2023 * 100.0
    else:
        revenue_yoy_change_pct = 0.0  # avoid division by zero; dataset should have 2023 data

    # High‑discount electronics
    high_disc_elec = df[(df["product_category"] == "Electronics") & (df["discount_pct"] >= 20)]
    electronics_high_discount_orders = len(high_disc_elec)
    electronics_high_discount_revenue = high_disc_elec["revenue"].sum()

    # Order revenue distribution
    order_revenue_mean = df["revenue"].mean()
    order_revenue_median = df["revenue"].median()
    order_revenue_std = df["revenue"].std(ddof=1)  # sample std
    order_revenue_min = df["revenue"].min()
    order_revenue_max = df["revenue"].max()

    # Customer concentration
    unique_customer_count = df["customer_id"].nunique()
    revenue_by_customer = df.groupby("customer_id")["revenue"].sum()
    top_customer_revenue = revenue_by_customer.max()
    top_customer_revenue_share_pct = (top_customer_revenue / total_revenue) * 100.0 if total_revenue else 0.0

    # Assemble findings – ensure plain Python scalars
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
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(findings, f, ensure_ascii=False)

if __name__ == "__main__":
    main()
