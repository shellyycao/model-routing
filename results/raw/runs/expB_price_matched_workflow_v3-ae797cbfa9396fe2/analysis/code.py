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
    
    findings = {}
    
    # Q1: Overall performance
    total_revenue = df['revenue'].sum()
    order_count = len(df)
    average_order_value = total_revenue / order_count
    findings['total_revenue'] = total_revenue
    findings['order_count'] = order_count
    findings['average_order_value'] = average_order_value
    
    # Q2: Regional comparison
    revenue_by_region = df.groupby('region')['revenue'].sum()
    findings['revenue_north'] = revenue_by_region.get('North', 0.0)
    findings['revenue_south'] = revenue_by_region.get('South', 0.0)
    findings['revenue_east'] = revenue_by_region.get('East', 0.0)
    findings['revenue_west'] = revenue_by_region.get('West', 0.0)
    
    # Q3: Quarterly trend in 2024
    df_2024 = df[df['order_date'].dt.year == 2024].copy()
    df_2024['quarter'] = df_2024['order_date'].dt.quarter
    revenue_by_quarter = df_2024.groupby('quarter')['revenue'].sum()
    findings['revenue_2024_q1'] = revenue_by_quarter.get(1, 0.0)
    findings['revenue_2024_q2'] = revenue_by_quarter.get(2, 0.0)
    findings['revenue_2024_q3'] = revenue_by_quarter.get(3, 0.0)
    findings['revenue_2024_q4'] = revenue_by_quarter.get(4, 0.0)
    
    # Q4: Year-over-year change
    revenue_2023 = df[df['order_date'].dt.year == 2023]['revenue'].sum()
    revenue_2024_total = df[df['order_date'].dt.year == 2024]['revenue'].sum()
    yoy_change_pct = (revenue_2024_total - revenue_2023) / revenue_2023 * 100
    findings['revenue_2023'] = revenue_2023
    findings['revenue_2024'] = revenue_2024_total
    findings['revenue_yoy_change_pct'] = yoy_change_pct
    
    # Q5: High-discount electronics
    high_discount_electronics = df[
        (df['product_category'] == 'Electronics') & 
        (df['discount_pct'] >= 20)
    ]
    findings['electronics_high_discount_orders'] = len(high_discount_electronics)
    findings['electronics_high_discount_revenue'] = high_discount_electronics['revenue'].sum()
    
    # Q6: Order revenue distribution
    findings['order_revenue_mean'] = df['revenue'].mean()
    findings['order_revenue_median'] = df['revenue'].median()
    findings['order_revenue_std'] = df['revenue'].std(ddof=1)  # sample std
    findings['order_revenue_min'] = df['revenue'].min()
    findings['order_revenue_max'] = df['revenue'].max()
    
    # Q7: Customer concentration
    unique_customer_count = df['customer_id'].nunique()
    revenue_by_customer = df.groupby('customer_id')['revenue'].sum()
    top_customer_revenue = revenue_by_customer.max()
    top_customer_revenue_share_pct = top_customer_revenue / total_revenue * 100
    findings['unique_customer_count'] = unique_customer_count
    findings['top_customer_revenue'] = top_customer_revenue
    findings['top_customer_revenue_share_pct'] = top_customer_revenue_share_pct
    
    # Write findings
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
    with open(output_path, 'w') as f:
        json.dump(findings, f)

if __name__ == "__main__":
    main()
