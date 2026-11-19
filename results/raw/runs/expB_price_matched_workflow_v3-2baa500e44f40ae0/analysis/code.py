import os
import json
import pandas as pd
import numpy as np

def main():
    # Define input and output paths
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    input_file = os.path.join(input_dir, "cleaned.csv")
    output_file = os.path.join(output_dir, "findings.json")
    
    # Read the cleaned data
    # The cleaning stage ensures the data is clean, but we parse dates for filtering
    df = pd.read_csv(input_file, parse_dates=['order_date'])
    
    # Initialize the findings dictionary
    findings = {}
    
    # --- Q1: Overall performance ---
    total_revenue = df['revenue'].sum()
    order_count = len(df)
    average_order_value = total_revenue / order_count if order_count > 0 else 0.0
    
    findings['total_revenue'] = total_revenue
    findings['order_count'] = order_count
    findings['average_order_value'] = average_order_value
    
    # --- Q2: Regional comparison ---
    # We pivot or group by region to get sums
    region_revenue = df.groupby('region')['revenue'].sum()
    # Ensure all regions exist, default to 0.0 if missing
    for region in ['North', 'South', 'East', 'West']:
        key = f'revenue_{region.lower()}'
        findings[key] = region_revenue.get(region, 0.0)
    
    # --- Q3: Quarterly trend in 2024 ---
    df_2024 = df[df['order_date'].dt.year == 2024].copy()
    df_2024['quarter'] = df_2024['order_date'].dt.quarter
    quarterly_revenue = df_2024.groupby('quarter')['revenue'].sum()
    
    for q in [1, 2, 3, 4]:
        key = f'revenue_2024_q{q}'
        findings[key] = quarterly_revenue.get(q, 0.0)
    
    # --- Q4: Year-over-year change ---
    df_2023 = df[df['order_date'].dt.year == 2023]
    revenue_2023 = df_2023['revenue'].sum()
    revenue_2024 = df_2024['revenue'].sum()
    
    findings['revenue_2023'] = revenue_2023
    findings['revenue_2024'] = revenue_2024
    
    if revenue_2023 != 0:
        yoy_change = (revenue_2024 - revenue_2023) / revenue_2023 * 100
    else:
        yoy_change = 0.0  # Or handle as undefined, but 0 is safe for finite requirement
    findings['revenue_yoy_change_pct'] = yoy_change
    
    # --- Q5: High-discount electronics ---
    high_disc_elec = df[
        (df['product_category'] == 'Electronics') & 
        (df['discount_pct'] >= 20)
    ]
    findings['electronics_high_discount_orders'] = len(high_disc_elec)
    findings['electronics_high_discount_revenue'] = high_disc_elec['revenue'].sum()
    
    # --- Q6: Order revenue distribution ---
    findings['order_revenue_mean'] = df['revenue'].mean()
    findings['order_revenue_median'] = df['revenue'].median()
    findings['order_revenue_std'] = df['revenue'].std(ddof=1) # Sample standard deviation
    findings['order_revenue_min'] = df['revenue'].min()
    findings['order_revenue_max'] = df['revenue'].max()
    
    # --- Q7: Customer concentration ---
    findings['unique_customer_count'] = df['customer_id'].nunique()
    customer_revenue = df.groupby('customer_id')['revenue'].sum()
    top_customer_revenue = customer_revenue.max() if not customer_revenue.empty else 0.0
    findings['top_customer_revenue'] = top_customer_revenue
    
    if total_revenue > 0:
        top_share = (top_customer_revenue / total_revenue) * 100
    else:
        top_share = 0.0
    findings['top_customer_revenue_share_pct'] = top_share
    
    # Write findings to JSON
    # Ensure all values are standard Python floats/ints for JSON serialization
    # (Pandas dtypes might cause issues, so we cast explicitly if necessary, though json.dump handles many)
    clean_findings = {k: float(v) if isinstance(v, (np.floating, np.integer)) else v for k, v in findings.items()}
    
    with open(output_file, 'w') as f:
        json.dump(clean_findings, f)

if __name__ == "__main__":
    main()