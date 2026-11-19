import os
import json
import pandas as pd

def main():
    # Paths from environment variables
    input_dir = os.environ.get("INPUT_DIR")
    output_dir = os.environ.get("OUTPUT_DIR")
    if not input_dir or not output_dir:
        raise RuntimeError("INPUT_DIR and OUTPUT_DIR environment variables must be set")

    cleaned_path = os.path.join(input_dir, "cleaned.csv")
    # Read cleaned data; order_date is parsed as datetime
    df = pd.read_csv(cleaned_path, parse_dates=["order_date"])

    # ----- q1: overall performance -----
    total_revenue = df["revenue"].sum()
    order_count = len(df)
    average_order_value = total_revenue / order_count if order_count else 0.0

    # ----- q2: regional revenue -----
    regional_rev = df.groupby("region")["revenue"].sum()
    revenue_north = regional_rev.get("North", 0.0)
    revenue_south = regional_rev.get("South", 0.0)
    revenue_east = regional_rev.get("East", 0.0)
    revenue_west = regional_rev.get("West", 0.0)

    # ----- q3: quarterly trend for 2024 -----
    df_2024 = df[df["order_date"].dt.year == 2024]
    quarterly_rev = df_2024.groupby(df_2024["order_date"].dt.quarter)["revenue"].sum()
    revenue_2024_q1 = quarterly_rev.get(1, 0.0)
    revenue_2024_q2 = quarterly_rev.get(2, 0.0)
    revenue_2024_q3 = quarterly_rev.get(3, 0.0)
    revenue_2024_q4 = quarterly_rev.get(4, 0.0)

    # ----- q4: year‑over‑year change -----
    revenue_2023 = df[df["order_date"].dt.year == 2023]["revenue"].sum()
    revenue_2024 = df_2024["revenue"].sum()
    if revenue_2023 != 0:
        revenue_yoy_change_pct = (revenue_2024 - revenue_2023) / revenue_2023 * 100.0
    else:
        revenue_yoy_change_pct = float('inf')  # safeguard, though unlikely in this dataset

    # ----- q5: high‑discount electronics -----
    high_disc_elec = df[(df["product_category"] == "Electronics") & (df["discount_pct"] >= 20.0)]
    electronics_high_discount_orders = len(high_disc_elec)
    electronics_high_discount_revenue = high_disc_elec["revenue"].sum()

    # ----- q6: order revenue distribution -----
    order_revenue_mean = df["revenue"].mean()
    order_revenue_median = df["revenue"].median()
    order_revenue_std = df["revenue"].std(ddof=1)  # sample std
    order_revenue_min = df["revenue"].min()
    order_revenue_max = df["revenue"].max()

    # ----- q7: customer concentration -----
    unique_customer_count = df["customer_id"].nunique()
    customer_rev = df.groupby("customer_id")["revenue"].sum()
    top_customer_revenue = customer_rev.max()
    top_customer_revenue_share_pct = (top_customer_revenue / total_revenue) * 100.0 if total_revenue else 0.0

    # Assemble findings dictionary (flat JSON)
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
    output_path = os.path.join(output_dir, "findings.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(findings, f, allow_nan=False)

if __name__ == "__main__":
    main()
