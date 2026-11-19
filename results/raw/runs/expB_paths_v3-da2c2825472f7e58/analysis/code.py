import os
import json
import pandas as pd
import numpy as np

# --- Load cleaned data ---
input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
df = pd.read_csv(input_path, parse_dates=["order_date"])

# --- Q1: Overall performance ---
total_revenue = df["revenue"].sum()
order_count = len(df)
average_order_value = total_revenue / order_count

# --- Q2: Regional comparison ---
region_revenue = df.groupby("region")["revenue"].sum()
revenue_north = region_revenue.get("North", 0.0)
revenue_south = region_revenue.get("South", 0.0)
revenue_east = region_revenue.get("East", 0.0)
revenue_west = region_revenue.get("West", 0.0)

# --- Q3: Quarterly trend in 2024 ---
df_2024 = df[df["order_date"].dt.year == 2024].copy()
df_2024["quarter"] = df_2024["order_date"].dt.quarter
q2024_revenue = df_2024.groupby("quarter")["revenue"].sum()
revenue_2024_q1 = q2024_revenue.get(1, 0.0)
revenue_2024_q2 = q2024_revenue.get(2, 0.0)
revenue_2024_q3 = q2024_revenue.get(3, 0.0)
revenue_2024_q4 = q2024_revenue.get(4, 0.0)

# --- Q4: Year-over-year change ---
revenue_2023 = df[df["order_date"].dt.year == 2023]["revenue"].sum()
revenue_2024 = df[df["order_date"].dt.year == 2024]["revenue"].sum()
revenue_yoy_change_pct = (revenue_2024 - revenue_2023) / revenue_2023 * 100

# --- Q5: High-discount electronics ---
elec_high = df[(df["product_category"] == "Electronics") & (df["discount_pct"] >= 20)]
electronics_high_discount_orders = len(elec_high)
electronics_high_discount_revenue = elec_high["revenue"].sum()

# --- Q6: Order revenue distribution ---
order_revenue_mean = df["revenue"].mean()
order_revenue_median = df["revenue"].median()
order_revenue_std = df["revenue"].std(ddof=1)
order_revenue_min = df["revenue"].min()
order_revenue_max = df["revenue"].max()

# --- Q7: Customer concentration ---
unique_customer_count = df["customer_id"].nunique()
customer_revenue = df.groupby("customer_id")["revenue"].sum()
top_customer_revenue = customer_revenue.max()
top_customer_revenue_share_pct = top_customer_revenue / total_revenue * 100

# --- Assemble findings ---
findings = {
    "total_revenue": float(total_revenue),
    "order_count": float(order_count),
    "average_order_value": float(average_order_value),
    "revenue_north": float(revenue_north),
    "revenue_south": float(revenue_south),
    "revenue_east": float(revenue_east),
    "revenue_west": float(revenue_west),
    "revenue_2024_q1": float(revenue_2024_q1),
    "revenue_2024_q2": float(revenue_2024_q2),
    "revenue_2024_q3": float(revenue_2024_q3),
    "revenue_2024_q4": float(revenue_2024_q4),
    "revenue_2023": float(revenue_2023),
    "revenue_2024": float(revenue_2024),
    "revenue_yoy_change_pct": float(revenue_yoy_change_pct),
    "electronics_high_discount_orders": float(electronics_high_discount_orders),
    "electronics_high_discount_revenue": float(electronics_high_discount_revenue),
    "order_revenue_mean": float(order_revenue_mean),
    "order_revenue_median": float(order_revenue_median),
    "order_revenue_std": float(order_revenue_std),
    "order_revenue_min": float(order_revenue_min),
    "order_revenue_max": float(order_revenue_max),
    "unique_customer_count": float(unique_customer_count),
    "top_customer_revenue": float(top_customer_revenue),
    "top_customer_revenue_share_pct": float(top_customer_revenue_share_pct),
}

# Validate all values are finite numbers
for k, v in findings.items():
    if not isinstance(v, (int, float)) or not np.isfinite(v):
        raise ValueError(f"Non-finite or invalid value for metric '{k}': {v}")

# --- Write output ---
output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
with open(output_path, "w") as f:
    json.dump(findings, f)

print("findings.json written successfully.")
print(json.dumps(findings, indent=2))
