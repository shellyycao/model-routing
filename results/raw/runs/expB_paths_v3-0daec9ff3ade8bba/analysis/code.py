import os
import json
import pandas as pd
import numpy as np

# Paths from environment variables
input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

# Load cleaned data – order_date parsed as datetime
df = pd.read_csv(input_path, parse_dates=["order_date"])

# ---------- Q1: Overall performance ----------
total_revenue = float(df["revenue"].sum())
order_count = int(len(df))
average_order_value = total_revenue / order_count if order_count else 0.0

# ---------- Q2: Regional comparison ----------
region_rev = df.groupby("region")["revenue"].sum().to_dict()
# Ensure all four regions are present
revenue_north = float(region_rev.get("North", 0.0))
revenue_south = float(region_rev.get("South", 0.0))
revenue_east = float(region_rev.get("East", 0.0))
revenue_west = float(region_rev.get("West", 0.0))

# ---------- Q3: Quarterly trend in 2024 ----------
df_2024 = df[df["order_date"].dt.year == 2024]
# pandas quarter is 1‑4
quarter_sums = df_2024.groupby(df_2024["order_date"].dt.quarter)["revenue"].sum()
revenue_2024_q1 = float(quarter_sums.get(1, 0.0))
revenue_2024_q2 = float(quarter_sums.get(2, 0.0))
revenue_2024_q3 = float(quarter_sums.get(3, 0.0))
revenue_2024_q4 = float(quarter_sums.get(4, 0.0))

# ---------- Q4: Year‑over‑Year change ----------
revenue_2023 = float(df[df["order_date"].dt.year == 2023]["revenue"].sum())
revenue_2024 = float(df_2024["revenue"].sum())
if revenue_2023 != 0:
    revenue_yoy_change_pct = (revenue_2024 - revenue_2023) / revenue_2023 * 100.0
else:
    revenue_yoy_change_pct = 0.0

# ---------- Q5: High‑discount Electronics ----------
high_disc_elec = df[(df["product_category"] == "Electronics") & (df["discount_pct"] >= 20)]
electronics_high_discount_orders = int(len(high_disc_elec))
electronics_high_discount_revenue = float(high_disc_elec["revenue"].sum())

# ---------- Q6: Order revenue distribution ----------
order_revenue_mean = float(df["revenue"].mean())
order_revenue_median = float(df["revenue"].median())
order_revenue_std = float(df["revenue"].std(ddof=1))  # sample std
order_revenue_min = float(df["revenue"].min())
order_revenue_max = float(df["revenue"].max())

# ---------- Q7: Customer concentration ----------
unique_customer_count = int(df["customer_id"].nunique())
customer_rev = df.groupby("customer_id")["revenue"].sum()
top_customer_revenue = float(customer_rev.max())
if total_revenue != 0:
    top_customer_revenue_share_pct = top_customer_revenue / total_revenue * 100.0
else:
    top_customer_revenue_share_pct = 0.0

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

# Write findings to JSON file – ensure no NaN/Infinity values are emitted
with open(output_path, "w") as f:
    json.dump(findings, f, allow_nan=False)
