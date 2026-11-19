import json
import math
import os

import pandas as pd


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    df = pd.read_csv(input_path)
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["revenue"] = pd.to_numeric(df["revenue"])
    df["year"] = df["order_date"].dt.year

    # q1: overall performance
    total_revenue = float(df["revenue"].sum())
    order_count = int(len(df))
    average_order_value = total_revenue / order_count if order_count else 0.0

    # q2: revenue per region
    rev_by_region = df.groupby("region")["revenue"].sum()
    revenue_north = float(rev_by_region.get("North", 0.0))
    revenue_south = float(rev_by_region.get("South", 0.0))
    revenue_east = float(rev_by_region.get("East", 0.0))
    revenue_west = float(rev_by_region.get("West", 0.0))

    # q3: quarterly revenue in 2024 (calendar quarters)
    df_2024 = df[df["year"] == 2024]
    rev_by_quarter = df_2024.groupby(df_2024["order_date"].dt.quarter)["revenue"].sum()
    revenue_2024_q1 = float(rev_by_quarter.get(1, 0.0))
    revenue_2024_q2 = float(rev_by_quarter.get(2, 0.0))
    revenue_2024_q3 = float(rev_by_quarter.get(3, 0.0))
    revenue_2024_q4 = float(rev_by_quarter.get(4, 0.0))

    # q4: year-over-year change
    revenue_2023 = float(df.loc[df["year"] == 2023, "revenue"].sum())
    revenue_2024 = float(df_2024["revenue"].sum())
    if revenue_2023 != 0.0:
        revenue_yoy_change_pct = (revenue_2024 - revenue_2023) / revenue_2023 * 100.0
    else:
        revenue_yoy_change_pct = 0.0

    # q5: high-discount electronics orders (discount_pct >= 20)
    elec_hd = df[(df["product_category"] == "Electronics") & (df["discount_pct"] >= 20)]
    electronics_high_discount_orders = int(len(elec_hd))
    electronics_high_discount_revenue = float(elec_hd["revenue"].sum())

    # q6: order revenue distribution (sample std, ddof=1)
    order_revenue_mean = float(df["revenue"].mean())
    order_revenue_median = float(df["revenue"].median())
    order_revenue_std = float(df["revenue"].std(ddof=1))
    order_revenue_min = float(df["revenue"].min())
    order_revenue_max = float(df["revenue"].max())

    # q7: customer concentration
    rev_by_customer = df.groupby("customer_id")["revenue"].sum()
    unique_customer_count = int(df["customer_id"].nunique())
    top_customer_revenue = float(rev_by_customer.max()) if len(rev_by_customer) else 0.0
    if total_revenue != 0.0:
        top_customer_revenue_share_pct = top_customer_revenue / total_revenue * 100.0
    else:
        top_customer_revenue_share_pct = 0.0

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

    # Safety: guarantee every value is a finite number (no NaN/Infinity)
    for key, value in findings.items():
        if isinstance(value, float) and not math.isfinite(value):
            findings[key] = 0.0

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(findings, f, indent=2)


if __name__ == "__main__":
    main()
