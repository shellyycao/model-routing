import os
import json
import pandas as pd
import numpy as np

# --- Load cleaned data ---
input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
df = pd.read_csv(input_path, parse_dates=["order_date"])

# Ensure correct dtypes
df["revenue"] = df["revenue"].astype(float)
df["discount_pct"] = df["discount_pct"].astype(float)
df["quantity"] = df["quantity"].astype(int)
df["unit_price"] = df["unit_price"].astype(float)

# Derive year and quarter columns
df["year"] = df["order_date"].dt.year
df["quarter"] = df["order_date"].dt.quarter

# --- Q1: Overall performance ---
total_revenue = float(df["revenue"].sum())
order_count = int(len(df))
average_order_value = total_revenue / order_count

# --- Q2: Regional comparison ---
region_revenue = df.groupby("region")["revenue"].sum()
revenue_north = float(region_revenue.get("North", 0.0))
revenue_south = float(region_revenue.get("South", 0.0))
revenue_east = float(region_revenue.get("East", 0.0))
revenue_west = float(region_revenue.get("West", 0.0))

# --- Q3: Quarterly trend in 2024 ---
df_2024 = df[df["year"] == 2024]
q_rev_2024 = df_2024.groupby("quarter")["revenue"].sum()
revenue_2024_q1 = float(q_rev_2024.get(1, 0.0))
revenue_2024_q2 = float(q_rev_2024.get(2, 0.0))
revenue_2024_q3 = float(q_rev_2024.get(3, 0.0))
revenue_2024_q4 = float(q_rev_2024.get(4, 0.0))

# --- Q4: Year-over-year change ---
revenue_2023 = float(df[df["year"] == 2023]["revenue"].sum())
revenue_2024 = float(df[df["year"] == 2024]["revenue"].sum())
revenue_yoy_change_pct = (revenue_2024 - revenue_2023) / revenue_2023 * 100

# --- Q5: High-discount electronics ---
mask_elec_hd = (df["product_category"] == "Electronics") & (df["discount_pct"] >= 20)
df_elec_hd = df[mask_elec_hd]
electronics_high_discount_orders = int(len(df_elec_hd))
electronics_high_discount_revenue = float(df_elec_hd["revenue"].sum())

# --- Q6: Order revenue distribution ---
order_revenue_mean = float(df["revenue"].mean())
order_revenue_median = float(df["revenue"].median())
order_revenue_std = float(df["revenue"].std(ddof=1))
order_revenue_min = float(df["revenue"].min())
order_revenue_max = float(df["revenue"].max())

# --- Q7: Customer concentration ---
unique_customer_count = int(df["customer_id"].nunique())
customer_revenue = df.groupby("customer_id")["revenue"].sum()
top_customer_revenue = float(customer_revenue.max())
top_customer_revenue_share_pct = top_customer_revenue / total_revenue * 100

# --- Assemble findings ---
findings = {
    "total_revenue": total_revenue,
    "order_count": float(order_count),
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
    "electronics_high_discount_orders": float(electronics_high_discount_orders),
    "electronics_high_discount_revenue": electronics_high_discount_revenue,
    "order_revenue_mean": order_revenue_mean,
    "order_revenue_median": order_revenue_median,
    "order_revenue_std": order_revenue_std,
    "order_revenue_min": order_revenue_min,
    "order_revenue_max": order_revenue_max,
    "unique_customer_count": float(unique_customer_count),
    "top_customer_revenue": top_customer_revenue,
    "top_customer_revenue_share_pct": top_customer_revenue_share_pct,
}

# Validate: all values must be finite numbers
for k, v in findings.items():
    assert isinstance(v, (int, float)), f"Non-numeric value for {k}: {v}"
    assert np.isfinite(v), f"Non-finite value for {k}: {v}"

# --- Write output ---
output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
with open(output_path, "w") as f:
    json.dump(findings, f, indent=2)

print("findings.json written successfully.")
print(json.dumps(findings, indent=2))
