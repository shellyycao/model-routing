import json
import os

import numpy as np
import pandas as pd

INPUT_DIR = os.environ["INPUT_DIR"]
OUTPUT_DIR = os.environ["OUTPUT_DIR"]

df = pd.read_csv(
    os.path.join(INPUT_DIR, "cleaned.csv"),
    dtype={"order_id": str, "customer_id": str, "region": str, "product_category": str},
)
df["order_date"] = pd.to_datetime(df["order_date"], format="%Y-%m-%d")
df["year"] = df["order_date"].dt.year
df["quarter"] = df["order_date"].dt.quarter

# q1: overall performance
total_revenue = float(df["revenue"].sum())
order_count = int(len(df))
average_order_value = total_revenue / order_count

# q2: regional revenue
rev_by_region = df.groupby("region")["revenue"].sum()

# q3: 2024 quarterly revenue
rev_2024_by_q = df[df["year"] == 2024].groupby("quarter")["revenue"].sum()

# q4: year-over-year
revenue_2023 = float(df.loc[df["year"] == 2023, "revenue"].sum())
revenue_2024 = float(df.loc[df["year"] == 2024, "revenue"].sum())
revenue_yoy_change_pct = (revenue_2024 - revenue_2023) / revenue_2023 * 100.0

# q5: high-discount electronics
hd = df[(df["product_category"] == "Electronics") & (df["discount_pct"] >= 20)]
electronics_high_discount_orders = int(len(hd))
electronics_high_discount_revenue = float(hd["revenue"].sum())

# q6: order revenue distribution (sample std, ddof=1)
rev = df["revenue"]

# q7: customer concentration
rev_by_customer = df.groupby("customer_id")["revenue"].sum()
unique_customer_count = int(df["customer_id"].nunique())
top_customer_revenue = float(rev_by_customer.max())
top_customer_revenue_share_pct = top_customer_revenue / total_revenue * 100.0

findings = {
    "total_revenue": total_revenue,
    "order_count": order_count,
    "average_order_value": float(average_order_value),
    "revenue_north": float(rev_by_region.get("North", 0.0)),
    "revenue_south": float(rev_by_region.get("South", 0.0)),
    "revenue_east": float(rev_by_region.get("East", 0.0)),
    "revenue_west": float(rev_by_region.get("West", 0.0)),
    "revenue_2024_q1": float(rev_2024_by_q.get(1, 0.0)),
    "revenue_2024_q2": float(rev_2024_by_q.get(2, 0.0)),
    "revenue_2024_q3": float(rev_2024_by_q.get(3, 0.0)),
    "revenue_2024_q4": float(rev_2024_by_q.get(4, 0.0)),
    "revenue_2023": revenue_2023,
    "revenue_2024": revenue_2024,
    "revenue_yoy_change_pct": float(revenue_yoy_change_pct),
    "electronics_high_discount_orders": electronics_high_discount_orders,
    "electronics_high_discount_revenue": electronics_high_discount_revenue,
    "order_revenue_mean": float(rev.mean()),
    "order_revenue_median": float(rev.median()),
    "order_revenue_std": float(rev.std(ddof=1)),
    "order_revenue_min": float(rev.min()),
    "order_revenue_max": float(rev.max()),
    "unique_customer_count": unique_customer_count,
    "top_customer_revenue": top_customer_revenue,
    "top_customer_revenue_share_pct": float(top_customer_revenue_share_pct),
}

# safety: ensure every value is a finite number
for k, v in findings.items():
    fv = float(v)
    if not np.isfinite(fv):
        raise ValueError(f"Metric {k} is not finite: {v}")

with open(os.path.join(OUTPUT_DIR, "findings.json"), "w") as f:
    json.dump(findings, f, indent=2)
