import os, json
import pandas as pd
import numpy as np

def main():
    # Paths provided by the workflow environment
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    df = pd.read_csv(input_path, parse_dates=["order_date"])

    # -------------------
    # q1: Overall performance
    # -------------------
    total_revenue = df["revenue"].sum()
    order_count = len(df)
    average_order_value = total_revenue / order_count if order_count else 0.0

    # -------------------
    # q2: Regional comparison
    # -------------------
    region_rev = df.groupby("region")["revenue"].sum()
    revenue_north = float(region_rev.get("North", 0.0))
    revenue_south = float(region_rev.get("South", 0.0))
    revenue_east = float(region_rev.get("East", 0.0))
    revenue_west = float(region_rev.get("West", 0.0))

    # -------------------
    # q3: Quarterly trend in 2024
    # -------------------
    df_2024 = df[df["order_date"].dt.year == 2024].copy()
    df_2024["quarter"] = ((df_2024["order_date"].dt.month - 1) // 3) + 1
    q_rev = df_2024.groupby("quarter")["revenue"].sum()
    revenue_2024_q1 = float(q_rev.get(1, 0.0))
    revenue_2024_q2 = float(q_rev.get(2, 0.0))
    revenue_2024_q3 = float(q_rev.get(3, 0.0))
    revenue_2024_q4 = float(q_rev.get(4, 0.0))

    # -------------------
    # q4: Year‑over‑year change
    # -------------------
    revenue_2023 = float(df[df["order_date"].dt.year == 2023]["revenue"].sum())
    revenue_2024 = float(df[df["order_date"].dt.year == 2024]["revenue"].sum())
    if revenue_2023 != 0:
        revenue_yoy_change_pct = (revenue_2024 - revenue_2023) / revenue_2023 * 100.0
    else:
        revenue_yoy_change_pct = 0.0

    # -------------------
    # q5: High‑discount electronics
    # -------------------
    high_disc_elec = df[(df["product_category"] == "Electronics") & (df["discount_pct"] >= 20)]
    electronics_high_discount_orders = int(high_disc_elec.shape[0])
    electronics_high_discount_revenue = float(high_disc_elec["revenue"].sum())

    # -------------------
    # q6: Order revenue distribution
    # -------------------
    rev_series = df["revenue"]
    order_revenue_mean = float(rev_series.mean())
    order_revenue_median = float(rev_series.median())
    order_revenue_std = float(rev_series.std(ddof=1))
    if np.isnan(order_revenue_std):
        order_revenue_std = 0.0
    order_revenue_min = float(rev_series.min())
    order_revenue_max = float(rev_series.max())

    # -------------------
    # q7: Customer concentration
    # -------------------
    unique_customer_count = int(df["customer_id"].nunique())
    customer_rev = df.groupby("customer_id")["revenue"].sum()
    top_customer_revenue = float(customer_rev.max())
    top_customer_revenue_share_pct = (
        top_customer_revenue / total_revenue * 100.0 if total_revenue != 0 else 0.0
    )

    # Assemble findings dictionary with flat structure
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

    # Write results
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(findings, f, ensure_ascii=False)

if __name__ == "__main__":
    main()
