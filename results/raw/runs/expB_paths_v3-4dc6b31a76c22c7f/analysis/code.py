import os
import pandas as pd
import numpy as np

# Read the cleaned data
input_file = os.path.join(os.environ['INPUT_DIR'], 'cleaned.csv')
df = pd.read_csv(input_file, parse_dates=['order_date'])

# Overall performance
total_revenue = df['revenue'].sum()
order_count = len(df)
average_order_value = total_revenue / order_count

# Regional comparison
revenue_by_region = df.groupby('region')['revenue'].sum().to_dict()

# Quarterly trend in 2024
df['quarter'] = df['order_date'].dt.to_period('Q')
df_2024 = df[df['order_date'].dt.year == 2024]
revenue_by_quarter_2024 = df_2024.groupby('quarter')['revenue'].sum().to_dict()

# Year-over-year change
df['year'] = df['order_date'].dt.year
revenue_by_year = df.groupby('year')['revenue'].sum().to_dict()
revenue_2023 = revenue_by_year.get(2023, 0)
revenue_2024 = revenue_by_year.get(2024, 0)
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
revenue_by_customer = df.groupby('customer_id')['revenue'].sum().to_dict()
top_customer_revenue = max(revenue_by_customer.values(), default=0)
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
   'revenue_2024_q1': revenue_by_quarter_2024.get('2024Q1', 0),
   'revenue_2024_q2': revenue_by_quarter_2024.get('2024Q2', 0),
   'revenue_2024_q3': revenue_by_quarter_2024.get('2024Q3', 0),
   'revenue_2024_q4': revenue_by_quarter_2024.get('2024Q4', 0),
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
methods_description = 'This script computes various metrics from the cleaned retail sales data, including overall performance, regional comparison, quarterly trend in 2024, year-over-year change, high-discount electronics orders, order revenue distribution, and customer concentration. The results are written to a JSON file named findings.json.'
