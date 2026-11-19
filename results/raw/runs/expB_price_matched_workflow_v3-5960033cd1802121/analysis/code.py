import os
import json
import pandas as pd
import numpy as np

def main():
    # Define input and output paths
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
    
    # Read cleaned data
    # The cleaning stage ensures correct types, but we parse dates to be sure for filtering
    df = pd.read_csv(input_path, parse_dates=['order_date'])
    
    # Initialize findings dictionary
    findings = {}
    
    # --- Q1: Overall performance ---
    total_revenue = df['revenue'].sum()
    order_count = len(df)
    average_order_value = total_revenue / order_count
    
    findings['total_revenue'] = total_revenue
    findings['order_count'] = float(order_count)
    findings['average_order_value'] = average_order_value
    
    # --- Q2: Regional comparison ---
    region_revenue = df.groupby('region')['revenue'].sum()
    findings['revenue_north'] = region_revenue.get('North', 0.0)
    findings['revenue_south'] = region_revenue.get('South', 0.0)
    findings['revenue_east'] = region_revenue.get('East', 0.0)
    findings['revenue_west'] = region_revenue.get('West', 0.0)
    
    # --- Q3: Quarterly trend in 2024 ---
    df_2024 = df[df['order_date'].dt.year == 2024].copy()
    df_2024['quarter'] = df_2024['order_date'].dt.quarter
    
    quarterly_revenue = df_2024.groupby('quarter')['revenue'].sum()
    findings['revenue_2024_q1'] = quarterly_revenue.get(1, 0.0)
    findings['revenue_2024_q2'] = quarterly_revenue.get(2, 0.0)
    findings['revenue_2024_q3'] = quarterly_revenue.get(3, 0.0)
    findings['revenue_2024_q4'] = quarterly_revenue.get(4, 0.0)
    
    # --- Q4: Year-over-year change ---
    revenue_2023 = df[df['order_date'].dt.year == 2023]['revenue'].sum()
    revenue_2024 = df[df['order_date'].dt.year == 2024]['revenue'].sum()
    
    findings['revenue_2023'] = revenue_2023
    findings['revenue_2024'] = revenue_2024
    
    if revenue_2023 != 0:
        yoy_change = (revenue_2024 - revenue_2023) / revenue_2023 * 100
    else:
        yoy_change = 0.0  # Or handle as appropriate, assuming non-zero base per prompt context
    findings['revenue_yoy_change_pct'] = yoy_change
    
    # --- Q5: High-discount electronics ---
    high_discount_electronics = df[
        (df['product_category'] == 'Electronics') & 
        (df['discount_pct'] >= 20)
    ]
    findings['electronics_high_discount_orders'] = float(len(high_discount_electronics))
    findings['electronics_high_discount_revenue'] = high_discount_electronics['revenue'].sum()
    
    # --- Q6: Order revenue distribution ---
    findings['order_revenue_mean'] = df['revenue'].mean()
    findings['order_revenue_median'] = df['revenue'].median()
    findings['order_revenue_std'] = df['revenue'].std(ddof=1) # Sample standard deviation
    findings['order_revenue_min'] = df['revenue'].min()
    findings['order_revenue_max'] = df['revenue'].max()
    
    # --- Q7: Customer concentration ---
    findings['unique_customer_count'] = float(df['customer_id'].nunique())
    
    customer_revenue = df.groupby('customer_id')['revenue'].sum()
    top_customer_revenue = customer_revenue.max()
    findings['top_customer_revenue'] = top_customer_revenue
    
    if total_revenue != 0:
        top_share = (top_customer_revenue / total_revenue) * 100
    else:
        top_share = 0.0
    findings['top_customer_revenue_share_pct'] = top_share
    
    # Write findings to JSON
    with open(output_path, 'w') as f:
        json.dump(findings, f)

if __name__ == "__main__":
    main()