import os
import pandas as pd
import numpy as np

# Read the cleaned data
input_file = os.path.join(os.environ['INPUT_DIR'], 'cleaned.csv')
df = pd.read_csv(input_file, parse_dates=['order_date'])

# Analysis
total_revenue = df['revenue'].sum()
order_count = len(df)
average_order_value = total_revenue / order_count

revenue_by_region = df.groupby('region')['revenue'].sum().to_dict()

# Filter for 2024 data
df_2024 = df[df['order_date'].dt.year == 2024]
revenue_2024_by_quarter = df_2024.groupby(df_2024['order_date'].dt.quarter)['revenue'].sum().to_dict()

# Yearly revenue
df_2023 = df[df['order_date'].dt.year == 2023]
df_2024 = df[df['order_date'].dt.year == 2024]
revenue_2023 = df_2023['revenue'].sum()
revenue_2024 = df_2024['revenue'].sum()
revenue_yoy_change_pct = ((revenue_2024 - revenue_2023) / revenue_2023) * 100 if revenue_2023!= 0 else 0

# High-discount electronics
df_electronics_high_discount = df[(df['product_category'] == 'Electronics') & (df['discount_pct'] >= 20)]
electronics_high_discount_orders = len(df_electronics_high_discount)
electronics_high_discount_revenue = df_electronics_high_discount['revenue'].sum()

# Order revenue distribution
order_revenue_mean = df['revenue'].mean()
order_revenue_median = df['revenue'].median()
order_revenue_std = df['revenue'].std()
order_revenue_min = df['revenue'].min()
order_revenue_max = df['revenue'].max()

# Customer concentration
unique_customer_count = df['customer_id'].nunique()
top_customer_revenue = df.groupby('customer_id')['revenue'].sum().max()
top_customer_revenue_share_pct = (top_customer_revenue / total_revenue) * 100 if total_revenue!= 0 else 0

# Prepare findings
findings = {
    'total_revenue': total_revenue,
    'order_count': order_count,
    'average_order_value': average_order_value,
   'revenue_north': revenue_by_region.get('North', 0),
   'revenue_south': revenue_by_region.get('South', 0),
   'revenue_east': revenue_by_region.get('East', 0),
   'revenue_west': revenue_by_region.get('West', 0),
   'revenue_2024_q1': revenue_2024_by_quarter.get(1, 0),
   'revenue_2024_q2': revenue_2024_by_quarter.get(2, 0),
   'revenue_2024_q3': revenue_2024_by_quarter.get(3, 0),
    'revenue_2024_q4': revenue_2024_by_quarter.get(4, 0),
   'revenue_2023': revenue_2023,
   'revenue_2024': revenue_2024,
    'revenue_yoy_change_pct': revenue_yoy_change_pct,
    'electronics_high_discount_orders': electronics_high_discount_orders,
    'electronics_high_discount_revenue': electronics_high_discount_revenue,
    'order_revenue_mean': order_revenue_mean,
    'order_revenue_median': order_revenue_median,
    'order_revenue_std': order_revenue_std,
    'order_revenue_min': order_revenue_min,
    'order_revenue_max': order_revenue_max,
    'unique_customer_count': unique_customer_count,
    'top_customer_revenue': top_customer_revenue,
    'top_customer_revenue_share_pct': top_customer_revenue_share_pct
}

# Write findings to JSON
output_file = os.path.join(os.environ['OUTPUT_DIR'], 'findings.json')
with open(output_file, 'w') as f:
    import json
    json.dump(findings, f)
