import os
import pandas as pd
import numpy as np

# Read the cleaned data
input_file = os.path.join(os.environ['INPUT_DIR'], 'cleaned.csv')
df = pd.read_csv(input_file)

# Analysis
total_revenue = df['revenue'].sum()
order_count = len(df)
average_order_value = total_revenue / order_count

revenue_north = df[df['region'] == 'North']['revenue'].sum()
revenue_south = df[df['region'] == 'South']['revenue'].sum()
revenue_east = df[df['region'] == 'East']['revenue'].sum()
revenue_west = df[df['region'] == 'West']['revenue'].sum()

df['order_date'] = pd.to_datetime(df['order_date'])
df['year'] = df['order_date'].dt.year
df['quarter'] = df['order_date'].dt.quarter

revenue_2024_q1 = df[(df['year'] == 2024) & (df['quarter'] == 1)]['revenue'].sum()
revenue_2024_q2 = df[(df['year'] == 2024) & (df['quarter'] == 2)]['revenue'].sum()
revenue_2024_q3 = df[(df['year'] == 2024) & (df['quarter'] == 3)]['revenue'].sum()
revenue_2024_q4 = df[(df['year'] == 2024) & (df['quarter'] == 4)]['revenue'].sum()

revenue_2023 = df[df['year'] == 2023]['revenue'].sum()
revenue_2024 = df[df['year'] == 2024]['revenue'].sum()
revenue_yoy_change_pct = ((revenue_2024 - revenue_2023) / revenue_2023) * 100 if revenue_2023!= 0 else 0

electronics_high_discount = df[(df['product_category'] == 'Electronics') & (df['discount_pct'] >= 20)]
electronics_high_discount_orders = len(electronics_high_discount)
electronics_high_discount_revenue = electronics_high_discount['revenue'].sum()

order_revenue_mean = df['revenue'].mean()
order_revenue_median = df['revenue'].median()
order_revenue_std = df['revenue'].std()
order_revenue_min = df['revenue'].min()
order_revenue_max = df['revenue'].max()

unique_customer_count = df['customer_id'].nunique()
top_customer = df.groupby('customer_id')['revenue'].sum().idxmax()
top_customer_revenue = df[df['customer_id'] == top_customer]['revenue'].sum()
top_customer_revenue_share_pct = (top_customer_revenue / total_revenue) * 100

# Prepare findings
findings = {
    'total_revenue': total_revenue,
    'order_count': order_count,
    'average_order_value': average_order_value,
   'revenue_north': revenue_north,
   'revenue_south': revenue_south,
    'revenue_east': revenue_east,
   'revenue_west': revenue_west,
   'revenue_2024_q1': revenue_2024_q1,
    'revenue_2024_q2': revenue_2024_q2,
   'revenue_2024_q3': revenue_2024_q3,
   'revenue_2024_q4': revenue_2024_q4,
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

# Expected artifacts
expected_artifacts = ['findings.json']

# Methods description
methods_description = 'This script performs the analysis on the cleaned retail sales data to compute various metrics such as total revenue, regional revenue, quarterly trends, year-over-year growth, high-discount electronics orders, and customer concentration. The results are written to a JSON file named findings.json.'