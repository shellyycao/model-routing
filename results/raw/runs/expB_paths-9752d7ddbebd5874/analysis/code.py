import os
import pandas as pd
import numpy as np

# Read the cleaned data
input_dir = os.environ['INPUT_DIR']
output_dir = os.environ['OUTPUT_DIR']
cleaned_data_path = os.path.join(input_dir, 'cleaned.csv')
df = pd.read_csv(cleaned_data_path, parse_dates=['order_date'])

# Analysis
total_revenue = df['revenue'].sum()
order_count = len(df)
average_order_value = total_revenue / order_count

revenue_by_region = df.groupby('region')['revenue'].sum().to_dict()

df['quarter'] = df['order_date'].dt.to_period('Q')
revenue_by_quarter_2024 = df[df['order_date'].dt.year == 2024].groupby('quarter')['revenue'].sum().to_dict()

df['year'] = df['order_date'].dt.year
revenue_by_year = df.groupby('year')['revenue'].sum().to_dict()
revenue_2023 = revenue_by_year.get(2023, 0)
revenue_2024 = revenue_by_year.get(2024, 0)
revenue_yoy_change_pct = ((revenue_2024 - revenue_2023) / revenue_2023) * 100 if revenue_2023!= 0 else 0

electronics_high_discount = df[(df['product_category'] == 'Electronics') & (df['discount_pct'] >= 20)]
electronics_high_discount_orders = len(electronics_high_discount)
electronics_high_discount_revenue = electronics_high_discount['revenue'].sum()

order_revenue_stats = df['revenue'].describe()
order_revenue_mean = order_revenue_stats['mean']
order_revenue_median = order_revenue_stats['50%']
order_revenue_std = order_revenue_stats['std']
order_revenue_min = order_revenue_stats['min']
order_revenue_max = order_revenue_stats['max']

unique_customer_count = df['customer_id'].nunique()
customer_revenue = df.groupby('customer_id')['revenue'].sum()
top_customer_revenue = customer_revenue.max()
top_customer_revenue_share_pct = (top_customer_revenue / total_revenue) * 100

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
findings_path = os.path.join(output_dir, 'findings.json')
with open(findings_path, 'w') as f:
    import json
    json.dump(findings, f)

# Expected artifacts
expected_artifacts = ['findings.json']

# Methods description
methods_description = 'This script performs various analyses on the cleaned retail sales data, including overall performance, regional comparison, quarterly trend, year-over-year growth, high-discount electronics orders, customer concentration, and order revenue distribution. It writes the findings to a JSON file.'
