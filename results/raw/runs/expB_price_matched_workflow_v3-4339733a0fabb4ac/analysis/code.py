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
    # The cleaning stage ensures correct types, but we parse dates to be safe for filtering
    df = pd.read_csv(input_file, parse_dates=['order_date'])
    
    # Initialize results dictionary
    results = {}
    
    # Q1: Overall performance
    total_revenue = df['revenue'].sum()
    order_count = len(df)
    average_order_value = total_revenue / order_count if order_count > 0 else 0.0
    
    results['total_revenue'] = total_revenue
    results['order_count'] = order_count
    results['average_order_value'] = average_order_value
    
    # Q2: Regional comparison
    # Group by region and sum revenue. Reindex to ensure all regions exist.
    region_revenue = df.groupby('region')['revenue'].sum()
    region_revenue = region_revenue.reindex(['North', 'South', 'East', 'West'], fill_value=0.0)
    
    results['revenue_north'] = region_revenue['North']
    results['revenue_south'] = region_revenue['South']
    results['revenue_east'] = region_revenue['East']
    results['revenue_west'] = region_revenue['West']
    
    # Q3: Quarterly trend in 2024
    df['year'] = df['order_date'].dt.year
    df['quarter'] = df['order_date'].dt.quarter
    
    df_2024 = df[df['year'] == 2024]
    quarterly_revenue_2024 = df_2024.groupby('quarter')['revenue'].sum()
    # Reindex to ensure all quarters Q1-Q4 are present
    quarterly_revenue_2024 = quarterly_revenue_2024.reindex([1, 2, 3, 4], fill_value=0.0)
    
    results['revenue_2024_q1'] = quarterly_revenue_2024[1]
    results['revenue_2024_q2'] = quarterly_revenue_2024[2]
    results['revenue_2024_q3'] = quarterly_revenue_2024[3]
    results['revenue_2024_q4'] = quarterly_revenue_2024[4]
    
    # Q4: Year-over-year change
    revenue_2023 = df[df['year'] == 2023]['revenue'].sum()
    revenue_2024 = df[df['year'] == 2024]['revenue'].sum()
    
    if revenue_2023 != 0:
        revenue_yoy_change_pct = ((revenue_2024 - revenue_2023) / revenue_2023) * 100
    else:
        revenue_yoy_change_pct = 0.0
    
    results['revenue_2023'] = revenue_2023
    results['revenue_2024'] = revenue_2024
    results['revenue_yoy_change_pct'] = revenue_yoy_change_pct
    
    # Q5: High-discount electronics
    high_discount_electronics = df[
        (df['product_category'] == 'Electronics') & 
        (df['discount_pct'] >= 20)
    ]
    
    results['electronics_high_discount_orders'] = len(high_discount_electronics)
    results['electronics_high_discount_revenue'] = high_discount_electronics['revenue'].sum()
    
    # Q6: Order revenue distribution
    # Using ddof=1 for sample standard deviation (n-1 denominator)
    results['order_revenue_mean'] = df['revenue'].mean()
    results['order_revenue_median'] = df['revenue'].median()
    results['order_revenue_std'] = df['revenue'].std(ddof=1)
    results['order_revenue_min'] = df['revenue'].min()
    results['order_revenue_max'] = df['revenue'].max()
    
    # Q7: Customer concentration
    unique_customer_count = df['customer_id'].nunique()
    customer_revenue = df.groupby('customer_id')['revenue'].sum()
    top_customer_revenue = customer_revenue.max() if not customer_revenue.empty else 0.0
    
    if total_revenue > 0:
        top_customer_revenue_share_pct = (top_customer_revenue / total_revenue) * 100
    else:
        top_customer_revenue_share_pct = 0.0
    
    results['unique_customer_count'] = unique_customer_count
    results['top_customer_revenue'] = top_customer_revenue
    results['top_customer_revenue_share_pct'] = top_customer_revenue_share_pct
    
    # Write results to JSON
    # Ensure all values are standard Python types (float/int) for JSON serialization
    # Pandas dtypes (like Float64Dtype) or numpy types can cause issues with default encoder
    clean_results = {k: float(v) if isinstance(v, (np.floating, np.integer)) else v for k, v in results.items()}
    # Handle numpy booleans if any, though unlikely here
    clean_results = {k: bool(v) if isinstance(v, np.bool_) else v for k, v in clean_results.items()}
    
    with open(output_file, 'w') as f:
        json.dump(clean_results, f)

if __name__ == "__main__":
    main()
