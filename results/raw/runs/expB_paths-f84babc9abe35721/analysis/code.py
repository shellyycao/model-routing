import os
import json
import pandas as pd
import numpy as np

def main():
    # Paths from environment variables
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    # Load cleaned data; parse order_date as datetime
    df = pd.read_csv(input_path, parse_dates=["order_date"])

    # ----- q1: overall performance -----
    total_revenue = float(df["revenue"].sum())
    order_count = int(len(df))
    average_order_value = total_revenue / order_count if order_count else 0.0

    # ----- q2: regional revenue -----
    region_rev = df.groupby("region")["revenue"].sum()
    revenue_north = float(region_rev.get("North", 0.0))
    revenue_south = float(region_rev.get("South", 0.0))
    revenue_east = float(region_rev.get("East", 0.0))
    revenue_west = float(region_rev.get("West", 0.0))

    # ----- q3: 2024 quarterly trend -----
    df_2024 = df[df["order_date"].dt.year == 2024].copy()
    if not df_2024.empty:
        df_2024["quarter"] = ((df_2024["order_date"].dt.month - 1) // 3) + 1
        quarterly = df_2024.groupby("quarter")["revenue"].sum()
    else:
        quarterly = pd.Series(dtype=float)
    revenue_2024_q1 = float(quarterly.get(1, 0.0))
    revenue_2024_q2 = float(quarterly.get(2, 0.0))
    revenue_2024_q3 = float(quarterly.get(3, 0.0))
    revenue_2024_q4 = float(quarterly.get(4, 0.0))

    # ----- q4: year‑over‑year change -----
    revenue_2023 = float(df[df["order_date"].dt.year == 2023]["revenue"].sum())
    revenue_2024 = float(df_2024["revenue"].sum())
    if revenue_2023 != 0:
        revenue_yoy_change_pct = (revenue_2024 - revenue_2023) / revenue_2023 * 100.0
    else:
        revenue_yoy_change_pct = 0.0

    # ----- q5: high‑discount electronics -----
    mask_elec = (df["product_category"] == "Electronics") & (df["discount_pct"] >= 20.0)
    df_elec_high = df[mask_elec]
    electronics_high_discount_orders = int(len(df_elec_high))
    electronics_high_discount_revenue = float(df_elec_high["revenue"].sum())

    # ----- q6: order revenue distribution -----
    rev_series = df["revenue"]
    order_revenue_mean = float(rev_series.mean())
    order_revenue_median = float(rev_series.median())
    order_revenue_std = float(rev_series.std(ddof=1))
    order_revenue_min = float(rev_series.min())
    order_revenue_max = float(rev_series.max())

    # ----- q7: customer concentration -----
    unique_customer_count = int(df["customer_id"].nunique())
    customer_rev = df.groupby("customer_id")["revenue"].sum()
    top_customer_revenue = float(customer_rev.max())
    top_customer_revenue_share_pct = (
        top_customer_revenue / total_revenue * 100.0 if total_revenue != 0 else 0.0
    )

    # Assemble findings dictionary
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
        "top_customer_revenue_share_pct": top_customer_revenue_share_pct
    }

    # Write findings to JSON file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(findings, f, ensure_ascii=False)

if __name__ == "__main__":
    main()
