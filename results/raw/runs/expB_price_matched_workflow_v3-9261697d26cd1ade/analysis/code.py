import os
import json
import pandas as pd
import numpy as np

def main():
    # Define input and output paths
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
    
    # Read the cleaned data
    # The schema indicates order_date is a date, pandas usually infers or we can parse
    # Given the sample, it's YYYY-MM-DD
    df = pd.read_csv(input_path, parse_dates=['order_date'])
    
    # Initialize results dictionary
    results = {}
    
    # --- Q1: Overall performance ---
    total_revenue = df['revenue'].sum()
    order_count = len(df)
    average_order_value = total_revenue / order_count
    
    results['total_revenue'] = float(total_revenue)
    results['order_count'] = int(order_count)
    results['average_order_value'] = float(average_order_value)
    
    # --- Q2: Regional comparison ---
    # We pivot or group by region. Schema guarantees 'North', 'South', 'East', 'West'
    revenue_by_region = df.groupby('region')['revenue'].sum()
    
    results['revenue_north'] = float(revenue_by_region.get('North', 0.0))
    results['revenue_south'] = float(revenue_by_region.get('South', 0.0))
    results['revenue_east'] = float(revenue_by_region.get('East', 0.0))
    results['revenue_west'] = float(revenue_by_region.get('West', 0.0))
    
    # --- Q3: Quarterly trend in 2024 ---
    df_2024 = df[df['order_date'].dt.year == 2024].copy()
    
    # Define quarters
    # Q1: Jan-Mar (months 1-3)
    # Q2: Apr-Jun (months 4-6)
    # Q3: Jul-Sep (months 7-9)
    # Q4: Oct-Dec (months 10-12)
    
    def get_quarter(month):
        if month <= 3:
            return 'Q1'
        elif month <= 6:
            return 'Q2'
        elif month <= 9:
            return 'Q3'
        else:
            return 'Q4'
    
    df_2024['quarter'] = df_2024['order_date'].dt.month.apply(get_quarter)
    revenue_by_quarter = df_2024.groupby('quarter')['revenue'].sum()
    
    results['revenue_2024_q1'] = float(revenue_by_quarter.get('Q1', 0.0))
    results['revenue_2024_q2'] = float(revenue_by_quarter.get('Q2', 0.0))
    results['revenue_2024_q3'] = float(revenue_by_quarter.get('Q3', 0.0))
    results['revenue_2024_q4'] = float(revenue_by_quarter.get('Q4', 0.0))
    
    # --- Q4: Year-over-year change ---
    revenue_2023 = df[df['order_date'].dt.year == 2023]['revenue'].sum()
    revenue_2024_total = df[df['order_date'].dt.year == 2024]['revenue'].sum()
    
    if revenue_2023 != 0:
        yoy_change_pct = (revenue_2024_total - revenue_2023) / revenue_2023 * 100
    else:
        yoy_change_pct = 0.0  # Or handle as undefined, but defaulting to 0.0 for finite number requirement
    
    results['revenue_2023'] = float(revenue_2023)
    results['revenue_2024'] = float(revenue_2024_total)
    results['revenue_yoy_change_pct'] = float(yoy_change_pct)
    
    # --- Q5: High-discount electronics ---
    # Filter: product_category == 'Electronics' AND discount_pct >= 20
    high_discount_electronics = df[
        (df['product_category'] == 'Electronics') & 
        (df['discount_pct'] >= 20)
    ]
    
    results['electronics_high_discount_orders'] = int(len(high_discount_electronics))
    results['electronics_high_discount_revenue'] = float(high_discount_electronics['revenue'].sum())
    
    # --- Q6: Order revenue distribution ---
    # Mean, Median, Std (sample, ddof=1), Min, Max
    results['order_revenue_mean'] = float(df['revenue'].mean())
    results['order_revenue_median'] = float(df['revenue'].median())
    results['order_revenue_std'] = float(df['revenue'].std(ddof=1))
    results['order_revenue_min'] = float(df['revenue'].min())
    results['order_revenue_max'] = float(df['revenue'].max())
    
    # --- Q7: Customer concentration ---
    # Distinct customer_id count
    unique_customer_count = df['customer_id'].nunique()
    results['unique_customer_count'] = int(unique_customer_count)
    
    # Revenue by customer
    revenue_by_customer = df.groupby('customer_id')['revenue'].sum()
    
    # Top customer revenue
    if not revenue_by_customer.empty:
        top_customer_revenue = revenue_by_customer.max()
    else:
        top_customer_revenue = 0.0
    
    results['top_customer_revenue'] = float(top_customer_revenue)
    
    # Top customer revenue share (%)
    if total_revenue > 0:
        top_customer_share_pct = (top_customer_revenue / total_revenue) * 100
    else:
        top_customer_share_pct = 0.0
    
    results['top_customer_revenue_share_pct'] = float(top_customer_share_pct)
    
    # Write results to JSON
    # Ensure all values are finite numbers (int or float)
    # The script logic ensures this, but we can add a final check if needed.
    # The prompt requires a flat JSON object.
    
    with open(output_path, 'w') as f:
        json.dump(results, f)

if __name__ == "__main__":
    main()
