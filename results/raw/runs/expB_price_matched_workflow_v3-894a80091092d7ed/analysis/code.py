import json
import os

import numpy as np
import pandas as pd


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    df = pd.read_csv(input_path, dtype={"order_id": str, "customer_id": str})
    df["order_date"] = pd.to_datetime(df["order_date"], format="%Y-%m-%d")
    df["revenue"] = df["revenue"].astype(float)
    df["discount_pct"] = df["discount_pct"].astype(float)

    findings = {}

    # q1: overall performance
    total_revenue = float(df["revenue"].sum())
    order_count = int(len(df))
    findings["total_revenue"] = total_revenue
    findings["order_count"] = order_count
    findings["average_order_value"] = total_revenue / order_count if order_count else 0.0

    # q2: total revenue per region
    by_region = df.groupby("region")["revenue"].sum()
    for key, region in [
        ("revenue_north", "North"),
        ("revenue_south", "South"),
        ("revenue_east", "East"),
        ("revenue_west", "West"),
    ]:
        findings[key] = float(by_region.get(region, 0.0))

    # calendar year and quarter derived from order_date
    df["year"] = df["order_date"].dt.year
    df["quarter"] = df["order_date"].dt.quarter

    # q3: quarterly revenue in 2024
    rev_2024_by_q = df.loc[df["year"] == 2024].groupby("quarter")["revenue"].sum()
    for q in (1, 2, 3, 4):
        findings["revenue_2024_q%d" % q] = float(rev_2024_by_q.get(q, 0.0))

    # q4: year-over-year revenue change
    revenue_2023 = float(df.loc[df["year"] == 2023, "revenue"].sum())
    revenue_2024 = float(df.loc[df["year"] == 2024, "revenue"].sum())
    findings["revenue_2023"] = revenue_2023
    findings["revenue_2024"] = revenue_2024
    if revenue_2023 != 0.0:
        findings["revenue_yoy_change_pct"] = (revenue_2024 - revenue_2023) / revenue_2023 * 100.0
    else:
        findings["revenue_yoy_change_pct"] = 0.0

    # q5: high-discount (>=20%) electronics orders
    hd_mask = (df["product_category"] == "Electronics") & (df["discount_pct"] >= 20.0)
    hd = df.loc[hd_mask]
    findings["electronics_high_discount_orders"] = int(len(hd))
    findings["electronics_high_discount_revenue"] = float(hd["revenue"].sum())

    # q6: order revenue distribution (sample std, ddof=1)
    rev = df["revenue"]
    findings["order_revenue_mean"] = float(rev.mean())
    findings["order_revenue_median"] = float(rev.median())
    std_val = float(rev.std(ddof=1)) if len(df) > 1 else 0.0
    findings["order_revenue_std"] = std_val if np.isfinite(std_val) else 0.0
    findings["order_revenue_min"] = float(rev.min())
    findings["order_revenue_max"] = float(rev.max())

    # q7: customer concentration
    by_customer = df.groupby("customer_id")["revenue"].sum()
    findings["unique_customer_count"] = int(df["customer_id"].nunique())
    top_customer_revenue = float(by_customer.max()) if len(by_customer) else 0.0
    findings["top_customer_revenue"] = top_customer_revenue
    if total_revenue != 0.0:
        findings["top_customer_revenue_share_pct"] = top_customer_revenue / total_revenue * 100.0
    else:
        findings["top_customer_revenue_share_pct"] = 0.0

    # guarantee every metric is a single finite number
    for k, v in findings.items():
        if not isinstance(v, (int, float)) or isinstance(v, bool) or not np.isfinite(v):
            raise ValueError("Metric %s is not a finite number: %r" % (k, v))

    with open(output_path, "w") as f:
        json.dump(findings, f, allow_nan=False)


if __name__ == "__main__":
    main()
