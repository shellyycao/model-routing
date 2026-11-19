import os
import json
import pandas as pd
import numpy as np

def main():
    # Read cleaned data
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    df = pd.read_csv(input_path)
    
    # Parse order_date as datetime for filtering
    df['order_date'] = pd.to_datetime(df['order_date'])
    
    # Initialize results dictionary
    results = {}
    
    # Q1: Overall performance
    total_revenue = df['revenue'].sum()
    order_count = len(df)
    average_order_value = total_revenue / order_count
    
    results['total_revenue'] = float(total_revenue)
    results['order_count'] = int(order_count)
    results['average_order_value'] = float(average_order_value)
    
    # Q2: Regional comparison
    revenue_by_region = df.groupby('region')['revenue'].sum()
    results['revenue_north'] = float(revenue_by_region.get('North', 0.0))
    results['revenue_south'] = float(revenue_by_region.get('South', 0.0))
    results['revenue_east'] = float(revenue_by_region.get('East', 0.0))
    results['revenue_west'] = float(revenue_by_region.get('West', 0.0))
    
    # Q3: Quarterly trend in 2024
    df_2024 = df[df['order_date'].dt.year == 2024].copy()
    df_2024['quarter'] = df_2024['order_date'].dt.quarter
    revenue_by_quarter = df_2024.groupby('quarter')['revenue'].sum()
    
    results['revenue_2024_q1'] = float(revenue_by_quarter.get(1, 0.0))
    results['revenue_2024_q2'] = float(revenue_by_quarter.get(2, 0.0))
    results['revenue_2024_q3'] = float(revenue_by_quarter.get(3, 0.0))
    results['revenue_2024_q4'] = float(revenue_by_quarter.get(4, 0.0))
    
    # Q4: Year-over-year change
    revenue_2023 = df[df['order_date'].dt.year == 2023]['revenue'].sum()
    revenue_2024_total = df[df['order_date'].dt.year == 2024]['revenue'].sum()
    revenue_yoy_change_pct = ((revenue_2024_total - revenue_2023) / revenue_2023) * 100
    
    results['revenue_2023'] = float(revenue_2023)
    results['revenue_2024'] = float(revenue_2024_total)
    results['revenue_yoy_change_pct'] = float(revenue_yoy_change_pct)
    
    # Q5: High-discount electronics
    electronics_high_discount = df[
        (df['product_category'] == 'Electronics') & 
        (df['discount_pct'] >= 20)
    ]
    results['electronics_high_discount_orders'] = int(len(electronics_high_discount))
    results['electronics_high_discount_revenue'] = float(electronics_high_discount['revenue'].sum())
    
    # Q6: Order revenue distribution
    results['order_revenue_mean'] = float(df['revenue'].mean())
    results['order_revenue_median'] = float(df['revenue'].median())
    results['order_revenue_std'] = float(df['revenue'].std(ddof=1))
    results['order_revenue_min'] = float(df['revenue'].min())
    results['order_revenue_max'] = float(df['revenue'].max())
    
    # Q7: Customer concentration
    unique_customer_count = df['customer_id'].nunique()
    revenue_by_customer = df.groupby('customer_id')['revenue'].sum()
    top_customer_revenue = float(revenue_by_customer.max())
    top_customer_revenue_share_pct = (top_customer_revenue / total_revenue) * 100
    
    results['unique_customer_count'] = int(unique_customer_count)
    results['top_customer_revenue'] = top_customer_revenue
    results['top_customer_revenue_share_pct'] = float(top_customer_revenue_share_pct)
    
    # Write results to JSON
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
    with open(output_path, 'w') as f:
        json.dump(results, f)

if __name__ == "__main__":
    main()
