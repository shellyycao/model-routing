import os
import json
import pandas as pd
import numpy as np


def main():
    # Paths provided by the workflow environment
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    # Load the cleaned data
    df = pd.read_csv(input_path)

    # Ensure order_date is a proper datetime object
    df["order_date"] = pd.to_datetime(df["order_date"], format="%Y-%m-%d", errors="coerce")
    df = df.dropna(subset=["order_date"]).copy()

    # ---------------------------------------------------------------------
    # q1 – Overall performance
    # ---------------------------------------------------------------------
    total_revenue = df["revenue"].sum()
    order_count = len(df)
    average_order_value = total_revenue / order_count if order_count else 0.0

    # ---------------------------------------------------------------------
    # q2 – Regional comparison
    # ---------------------------------------------------------------------
    region_rev = df.groupby("region")["revenue"].sum()
    revenue_north = region_rev.get("North", 0.0)
    revenue_south = region_rev.get("South", 0.0)
    revenue_east = region_rev.get("East", 0.0)
    revenue_west = region_rev.get("West", 0.0)

    # ---------------------------------------------------------------------
    # q4 – Year‑over‑year totals and change
    # ---------------------------------------------------------------------
    df["year"] = df["order_date"].dt.year
    revenue_2023 = df.loc[df["year"] == 2023, "revenue"].sum()
    revenue_2024 = df.loc[df["year"] == 2024, "revenue"].sum()
    revenue_yoy_change_pct = (
        (revenue_2024 - revenue_2023) / revenue_2023 * 100
        if revenue_2023 != 0 else 0.0
    )

    # ---------------------------------------------------------------------
    # q3 – Quarterly trend for 2024
    # ---------------------------------------------------------------------
    df_2024 = df[df["year"] == 2024].copy()
    df_2024["quarter"] = df_2024["order_date"].dt.quarter
    q_rev = df_2024.groupby("quarter")["revenue"].sum()
    revenue_2024_q1 = q_rev.get(1, 0.0)
    revenue_2024_q2 = q_rev.get(2, 0.0)
    revenue_2024_q3 = q_rev.get(3, 0.0)
    revenue_2024_q4 = q_rev.get(4, 0.0)

    # ---------------------------------------------------------------------
    # q5 – High‑discount Electronics orders
    # ---------------------------------------------------------------------
    high_disc_elec = df[(df["product_category"] == "Electronics") & (df["discount_pct"] >= 20)]
    electronics_high_discount_orders = len(high_disc_elec)
    electronics_high_discount_revenue = high_disc_elec["revenue"].sum()

    # ---------------------------------------------------------------------
    # q6 – Order revenue distribution statistics
    # ---------------------------------------------------------------------
    order_revenue_mean = df["revenue"].mean()
    order_revenue_median = df["revenue"].median()
    order_revenue_std = df["revenue"].std(ddof=1)  # sample standard deviation
    order_revenue_min = df["revenue"].min()
    order_revenue_max = df["revenue"].max()

    # ---------------------------------------------------------------------
    # q7 – Customer concentration
    # ---------------------------------------------------------------------
    unique_customer_count = df["customer_id"].nunique()
    cust_rev = df.groupby("customer_id")["revenue"].sum()
    top_customer_revenue = cust_rev.max()
    top_customer_revenue_share_pct = (
        top_customer_revenue / total_revenue * 100 if total_revenue != 0 else 0.0
    )

    # ---------------------------------------------------------------------
    # Assemble findings dictionary (flat JSON as required)
    # ---------------------------------------------------------------------
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

    # Write results – disallow NaN/Infinity per contract
    with open(output_path, "w") as f:
        json.dump(findings, f, allow_nan=False)


if __name__ == "__main__":
    main()
