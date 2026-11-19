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
    quarter = df["order_date"].dt.quarter

    # q1: overall performance
    total_revenue = float(revenue.sum())
    order_count = int(len(df))
    average_order_value = total_revenue / order_count

    # q2: revenue per region
    by_region = df.groupby("region")["revenue"].sum()
    revenue_north = float(by_region.get("North", 0.0))
    revenue_south = float(by_region.get("South", 0.0))
    revenue_east = float(by_region.get("East", 0.0))
    revenue_west = float(by_region.get("West", 0.0))

    # q3: 2024 quarterly revenue
    revenue_2024_q1 = float(revenue[(year == 2024) & (quarter == 1)].sum())
    revenue_2024_q2 = float(revenue[(year == 2024) & (quarter == 2)].sum())
    revenue_2024_q3 = float(revenue[(year == 2024) & (quarter == 3)].sum())
    revenue_2024_q4 = float(revenue[(year == 2024) & (quarter == 4)].sum())

    # q4: year-over-year change
    revenue_2023 = float(revenue[year == 2023].sum())
    revenue_2024 = float(revenue[year == 2024].sum())
    revenue_yoy_change_pct = (revenue_2024 - revenue_2023) / revenue_2023 * 100.0

    # q5: high-discount electronics orders
    elec_mask = (df["product_category"] == "Electronics") & (df["discount_pct"] >= 20)
    electronics_high_discount_orders = int(elec_mask.sum())
    electronics_high_discount_revenue = float(revenue[elec_mask].sum())

    # q6: order revenue distribution (sample std, ddof=1)
    order_revenue_mean = float(revenue.mean())
    order_revenue_median = float(revenue.median())
    order_revenue_std = float(revenue.std(ddof=1))
    order_revenue_min = float(revenue.min())
    order_revenue_max = float(revenue.max())

    # q7: customer concentration
    by_customer = df.groupby("customer_id")["revenue"].sum()
    unique_customer_count = int(df["customer_id"].nunique())
    top_customer_revenue = float(by_customer.max())
    top_customer_revenue_share_pct = top_customer_revenue / total_revenue * 100.0

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

    for key, value in findings.items():
        if not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"Metric {key} is not a finite number: {value!r}")

    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(findings, fh, indent=2)


if __name__ == "__main__":
    main()
