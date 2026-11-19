import json
import os

import pandas as pd


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    df = pd.read_csv(input_path)
    df["order_date"] = pd.to_datetime(df["order_date"], format="%Y-%m-%d")
    df["revenue"] = df["revenue"].astype(float)

    revenue = df["revenue"]

    # q1: overall performance
    total_revenue = float(revenue.sum())
    order_count = int(len(df))
    average_order_value = total_revenue / order_count if order_count else 0.0

    # q2: regional comparison
    by_region = df.groupby("region")["revenue"].sum()
    revenue_north = float(by_region.get("North", 0.0))
    revenue_south = float(by_region.get("South", 0.0))
    revenue_east = float(by_region.get("East", 0.0))
    revenue_west = float(by_region.get("West", 0.0))

    # q3: quarterly trend in 2024
    df_2024 = df[df["order_date"].dt.year == 2024]
    by_quarter = df_2024.groupby(df_2024["order_date"].dt.quarter)["revenue"].sum()
    revenue_2024_q1 = float(by_quarter.get(1, 0.0))
    revenue_2024_q2 = float(by_quarter.get(2, 0.0))
    revenue_2024_q3 = float(by_quarter.get(3, 0.0))
    revenue_2024_q4 = float(by_quarter.get(4, 0.0))

    # q4: year-over-year change
    revenue_2023 = float(df.loc[df["order_date"].dt.year == 2023, "revenue"].sum())
    revenue_2024 = float(df_2024["revenue"].sum())
    revenue_yoy_change_pct = (
        (revenue_2024 - revenue_2023) / revenue_2023 * 100.0
        if revenue_2023 != 0.0
        else 0.0
    )

    # q5: high-discount electronics orders
    mask_hd_elec = (df["product_category"] == "Electronics") & (df["discount_pct"] >= 20)
    hd_elec = df.loc[mask_hd_elec, "revenue"]
    electronics_high_discount_orders = int(mask_hd_elec.sum())
    electronics_high_discount_revenue = float(hd_elec.sum())

    # q6: order revenue distribution
    order_revenue_mean = float(revenue.mean())
    order_revenue_median = float(revenue.median())
    order_revenue_std = float(revenue.std(ddof=1)) if order_count > 1 else 0.0
    order_revenue_min = float(revenue.min())
    order_revenue_max = float(revenue.max())

    # q7: customer concentration
    by_customer = df.groupby("customer_id")["revenue"].sum()
    unique_customer_count = int(df["customer_id"].nunique())
    top_customer_revenue = float(by_customer.max()) if len(by_customer) else 0.0
    top_customer_revenue_share_pct = (
        top_customer_revenue / total_revenue * 100.0 if total_revenue != 0.0 else 0.0
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

    with open(output_path, "w") as f:
        json.dump(findings, f, indent=2)


if __name__ == "__main__":
    main()
