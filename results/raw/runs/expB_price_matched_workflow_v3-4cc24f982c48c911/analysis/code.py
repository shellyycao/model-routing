import os
import json
import pandas as pd
import numpy as np

def main():
    # Define input and output paths
    input_file = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_file = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
    
    # Read the cleaned data
    # The cleaning stage ensures the schema is correct.
    # We parse dates to handle quarterly and yearly filtering.
    df = pd.read_csv(input_file, parse_dates=['order_date'])
    
    findings = {}
    
    # --- Q1: Overall performance ---
    total_revenue = df['revenue'].sum()
    order_count = len(df)
    average_order_value = total_revenue / order_count if order_count > 0 else 0.0
    
    findings['total_revenue'] = total_revenue
    findings['order_count'] = order_count
    findings['average_order_value'] = average_order_value
    
    # --- Q2: Regional comparison ---
    # We pivot on region to get sums, then map to specific keys.
    revenue_by_region = df.groupby('region')['revenue'].sum()
    # Use .get() with default 0.0 to handle cases where a region might have no data (unlikely given cleaning)
    findings['revenue_north'] = revenue_by_region.get('North', 0.0)
    findings['revenue_south'] = revenue_by_region.get('South', 0.0)
    findings['revenue_east'] = revenue_by_region.get('East', 0.0)
    findings['revenue_west'] = revenue_by_region.get('West', 0.0)
    
    # --- Q3: Quarterly trend in 2024 ---
    # Filter for 2024
    df_2024 = df[df['order_date'].dt.year == 2024]
    
    # Define quarters
    q1 = df_2024[df_2024['order_date'].dt.month.isin([1, 2, 3])]['revenue'].sum()
    q2 = df_2024[df_2024['order_date'].dt.month.isin([4, 5, 6])]['revenue'].sum()
    q3 = df_2024[df_2024['order_date'].dt.month.isin([7, 8, 9])]['revenue'].sum()
    q4 = df_2024[df_2024['order_date'].dt.month.isin([10, 11, 12])]['revenue'].sum()
    
    findings['revenue_2024_q1'] = q1
    findings['revenue_2024_q2'] = q2
    findings['revenue_2024_q3'] = q3
    findings['revenue_2024_q4'] = q4
    
    # --- Q4: Year-over-year change ---
    revenue_2023 = df[df['order_date'].dt.year == 2023]['revenue'].sum()
    revenue_2024_total = df_2024['revenue'].sum()
    
    yoy_change = 0.0
    if revenue_2023 > 0:
        yoy_change = (revenue_2024_total - revenue_2023) / revenue_2023 * 100
    
    findings['revenue_2023'] = revenue_2023
    findings['revenue_2024'] = revenue_2024_total
    findings['revenue_yoy_change_pct'] = yoy_change
    
    # --- Q5: High-discount electronics ---
    # Filter: category is 'Electronics' AND discount >= 20
    high_disc_elec = df[
        (df['product_category'] == 'Electronics') & 
        (df['discount_pct'] >= 20.0)
    ]
    
    findings['electronics_high_discount_orders'] = len(high_disc_elec)
    findings['electronics_high_discount_revenue'] = high_disc_elec['revenue'].sum()
    
    # --- Q6: Order revenue distribution ---
    # Using ddof=1 for sample standard deviation
    findings['order_revenue_mean'] = df['revenue'].mean()
    findings['order_revenue_median'] = df['revenue'].median()
    findings['order_revenue_std'] = df['revenue'].std(ddof=1)
    findings['order_revenue_min'] = df['revenue'].min()
    findings['order_revenue_max'] = df['revenue'].max()
    
    # --- Q7: Customer concentration ---
    # Distinct count
    unique_customer_count = df['customer_id'].nunique()
    findings['unique_customer_count'] = unique_customer_count
    
    # Top customer revenue
    # Group by customer_id, sum revenue, find max
    customer_revenue = df.groupby('customer_id')['revenue'].sum()
    top_customer_revenue = customer_revenue.max() if not customer_revenue.empty else 0.0
    findings['top_customer_revenue'] = top_customer_revenue
    
    # Share percentage
    top_customer_share = (top_customer_revenue / total_revenue * 100) if total_revenue > 0 else 0.0
    findings['top_customer_revenue_share_pct'] = top_customer_share
    
    # Write findings to JSON
    # Ensure we write native Python floats/ints, not numpy types, though json.dump handles many.
    # We convert numpy types explicitly if needed, but standard json library handles float64/int64.
    with open(output_file, 'w') as f:
        json.dump(findings, f)

if __name__ == "__main__":
    main()
