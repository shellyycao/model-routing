import os
import json
import pandas as pd
import numpy as np

# Define input and output paths
input_dir = os.environ["INPUT_DIR"]
output_dir = os.environ["OUTPUT_DIR"]
input_file = os.path.join(input_dir, "cleaned.csv")
output_file = os.path.join(output_dir, "findings.json")

# Read the cleaned data
df = pd.read_csv(input_file)

# Ensure correct data types as per schema
df['order_date'] = pd.to_datetime(df['order_date'])
df['revenue'] = df['revenue'].astype(float)

# Initialize results dictionary
results = {}

# Q1: Overall performance
results['total_revenue'] = df['revenue'].sum()
results['order_count'] = len(df)
results['average_order_value'] = results['total_revenue'] / results['order_count']

# Q2: Regional comparison
region_revenue = df.groupby('region')['revenue'].sum()
results['revenue_north'] = region_revenue.get('North', 0.0)
results['revenue_south'] = region_revenue.get('South', 0.0)
results['revenue_east'] = region_revenue.get('East', 0.0)
results['revenue_west'] = region_revenue.get('West', 0.0)

# Q3: Quarterly trend in 2024
df_2024 = df[df['order_date'].dt.year == 2024].copy()
df_2024['quarter'] = df_2024['order_date'].dt.quarter
quarterly_revenue = df_2024.groupby('quarter')['revenue'].sum()
results['revenue_2024_q1'] = quarterly_revenue.get(1, 0.0)
results['revenue_2024_q2'] = quarterly_revenue.get(2, 0.0)
results['revenue_2024_q3'] = quarterly_revenue.get(3, 0.0)
results['revenue_2024_q4'] = quarterly_revenue.get(4, 0.0)

# Q4: Year-over-year change
revenue_2023 = df[df['order_date'].dt.year == 2023]['revenue'].sum()
revenue_2024 = df[df['order_date'].dt.year == 2024]['revenue'].sum()
results['revenue_2023'] = revenue_2023
results['revenue_2024'] = revenue_2024
if revenue_2023 != 0:
    results['revenue_yoy_change_pct'] = (revenue_2024 - revenue_2023) / revenue_2023 * 100
else:
    results['revenue_yoy_change_pct'] = 0.0

# Q5: High-discount electronics
electronics_high_discount = df[
    (df['product_category'] == 'Electronics') & 
    (df['discount_pct'] >= 20)
]
results['electronics_high_discount_orders'] = len(electronics_high_discount)
results['electronics_high_discount_revenue'] = electronics_high_discount['revenue'].sum()

# Q6: Order revenue distribution
results['order_revenue_mean'] = df['revenue'].mean()
results['order_revenue_median'] = df['revenue'].median()
results['order_revenue_std'] = df['revenue'].std(ddof=1)
results['order_revenue_min'] = df['revenue'].min()
results['order_revenue_max'] = df['revenue'].max()

# Q7: Customer concentration
results['unique_customer_count'] = df['customer_id'].nunique()
customer_revenue = df.groupby('customer_id')['revenue'].sum()
results['top_customer_revenue'] = customer_revenue.max()
results['top_customer_revenue_share_pct'] = (results['top_customer_revenue'] / results['total_revenue']) * 100

# Write results to JSON
with open(output_file, 'w') as f:
    json.dump(results, f)
