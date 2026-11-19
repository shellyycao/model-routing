import json
import os

import numpy as np
import pandas as pd


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    df = pd.read_csv(input_path, parse_dates=["order_date"])

    revenue = df["revenue"].astype(float)

    # q1: overall performance
    total_revenue = float(revenue.sum())
    order_count = int(len(df))
    average_order_value = float(total_revenue / order_count)

    # q2: regional comparison
    region_revenue = df.groupby("region", observed=True)["revenue"].sum()
    revenue_north = float(region_revenue.get("North", 0.0))
    revenue_south = float(region_revenue.get("South", 0.0))
    revenue_east = float(region_revenue.get("East", 0.0))
    revenue_west = float(region_revenue.get("West", 0.0))

    # q3: quarterly trend in 2024
    df_2024 = df[df["order_date"].dt.year == 2024]
    quarters_2024 = df_2024.groupby(df_2024["order_date"].dt.quarter)["revenue"].sum()
    revenue_2024_q1 = float(quarters_2024.get(1, 0.0))
    revenue_2024_q2 = float(quarters_2024.get(2, 0.0))
    revenue_2024_q3 = float(quarters_2024.get(3, 0.0))
    revenue_2024_q4 = float(quarters_2024.get(4, 0.0))

    # q4: year-over-year change
    revenue_2023 = float(df.loc[df["order_date"].dt.year == 2023, "revenue"].sum())
    revenue_2024 = float(df_2024["revenue"].sum())
    revenue_yoy_change_pct = float((revenue_2024 - revenue_2023) / revenue_2023 * 100.0)

    # q5: high-discount electronics
    hd_elec = df[(df["product_category"] == "Electronics") & (df["discount_pct"] >= 20)]
    electronics_high_discount_orders = int(len(hd_elec))
    electronics_high_discount_revenue = float(hd_elec["revenue"].sum())

    # q6: order revenue distribution (sample std with ddof=1)
    order_revenue_mean = float(revenue.mean())
    order_revenue_median = float(revenue.median())
    order_revenue_std = float(revenue.std(ddof=1))
    order_revenue_min = float(revenue.min())
    order_revenue_max = float(revenue.max())

    # q7: customer concentration
    unique_customer_count = int(df["customer_id"].nunique())
    customer_revenue = df.groupby("customer_id")["revenue"].sum()
    top_customer_revenue = float(customer_revenue.max())
    top_customer_revenue_share_pct = float(top_customer_revenue / total_revenue * 100.0)

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
        "top_customer_revenue_share_pct": top_customer_revenue_share_pct,
    }

    # Guarantee every value is a finite number before writing.
    for key, value in findings.items():
        if not np.isfinite(value):
            raise ValueError(f"Metric {key} is not finite: {value}")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(findings, f)


if __name__ == "__main__":
    main()
