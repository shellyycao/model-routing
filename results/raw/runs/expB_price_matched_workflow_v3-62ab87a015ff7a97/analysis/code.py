import os
import json
import pandas as pd
import numpy as np

def main():
    # Read cleaned data
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    df = pd.read_csv(input_path)
    
    # Parse order_date
    df['order_date'] = pd.to_datetime(df['order_date'])
    
    # Initialize findings dictionary
    findings = {}
    
    # Q1: Overall performance
    total_revenue = df['revenue'].sum()
    order_count = len(df)
    average_order_value = total_revenue / order_count
    
    findings['total_revenue'] = float(total_revenue)
    findings['order_count'] = int(order_count)
    findings['average_order_value'] = float(average_order_value)
    
    # Q2: Regional comparison
    revenue_by_region = df.groupby('region')['revenue'].sum()
    findings['revenue_north'] = float(revenue_by_region.get('North', 0.0))
    findings['revenue_south'] = float(revenue_by_region.get('South', 0.0))
    findings['revenue_east'] = float(revenue_by_region.get('East', 0.0))
    findings['revenue_west'] = float(revenue_by_region.get('West', 0.0))
    
    # Q3: Quarterly trend in 2024
    df_2024 = df[df['order_date'].dt.year == 2024].copy()
    df_2024['quarter'] = df_2024['order_date'].dt.quarter
    revenue_2024_by_quarter = df_2024.groupby('quarter')['revenue'].sum()
    
    findings['revenue_2024_q1'] = float(revenue_2024_by_quarter.get(1, 0.0))
    findings['revenue_2024_q2'] = float(revenue_2024_by_quarter.get(2, 0.0))
    findings['revenue_2024_q3'] = float(revenue_2024_by_quarter.get(3, 0.0))
    findings['revenue_2024_q4'] = float(revenue_2024_by_quarter.get(4, 0.0))
    
    # Q4: Year-over-year change
    revenue_2023 = df[df['order_date'].dt.year == 2023]['revenue'].sum()
    revenue_2024 = df[df['order_date'].dt.year == 2024]['revenue'].sum()
    revenue_yoy_change_pct = ((revenue_2024 - revenue_2023) / revenue_2023) * 100
    
    findings['revenue_2023'] = float(revenue_2023)
    findings['revenue_2024'] = float(revenue_2024)
    findings['revenue_yoy_change_pct'] = float(revenue_yoy_change_pct)
    
    # Q5: High-discount electronics
    electronics_high_discount = df[
        (df['product_category'] == 'Electronics') & 
        (df['discount_pct'] >= 20)
    ]
    findings['electronics_high_discount_orders'] = int(len(electronics_high_discount))
    findings['electronics_high_discount_revenue'] = float(electronics_high_discount['revenue'].sum())
    
    # Q6: Order revenue distribution
    findings['order_revenue_mean'] = float(df['revenue'].mean())
    findings['order_revenue_median'] = float(df['revenue'].median())
    findings['order_revenue_std'] = float(df['revenue'].std(ddof=1))  # sample std with n-1 denominator
    findings['order_revenue_min'] = float(df['revenue'].min())
    findings['order_revenue_max'] = float(df['revenue'].max())
    
    # Q7: Customer concentration
    unique_customer_count = df['customer_id'].nunique()
    revenue_by_customer = df.groupby('customer_id')['revenue'].sum()
    top_customer_revenue = float(revenue_by_customer.max())
    top_customer_revenue_share_pct = (top_customer_revenue / total_revenue) * 100
    
    findings['unique_customer_count'] = int(unique_customer_count)
    findings['top_customer_revenue'] = top_customer_revenue
    findings['top_customer_revenue_share_pct'] = float(top_customer_revenue_share_pct)
    
    # Write findings to output
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
    with open(output_path, 'w') as f:
        json.dump(findings, f)

if __name__ == "__main__":
    main()
