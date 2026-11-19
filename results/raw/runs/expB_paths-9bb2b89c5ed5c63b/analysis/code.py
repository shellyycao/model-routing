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

df['year'] = df['order_date'].dt.year
df['quarter'] = df['order_date'].dt.quarter
revenue_by_quarter_2024 = df[df['year'] == 2024].groupby('quarter')['revenue'].sum().to_dict()
revenue_2023 = df[df['year'] == 2023]['revenue'].sum()
revenue_2024 = df[df['year'] == 2024]['revenue'].sum()
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
top_customer = df.groupby('customer_id')['revenue'].sum().idxmax()
top_customer_revenue = df.groupby('customer_id')['revenue'].sum().max()
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
   'revenue_2024_q1': revenue_by_quarter_2024.get(1, 0),
   'revenue_2024_q2': revenue_by_quarter_2024.get(2, 0),
    'revenue_2024_q3': revenue_by_quarter_2024.get(3, 0),
    'revenue_2024_q4': revenue_by_quarter_2024.get(4, 0),
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
    pd.json.dump(findings, f)

