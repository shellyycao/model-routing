import os
import json
import pandas as pd
import numpy as np

def main():
    # Read cleaned data
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    df = pd.read_csv(input_path)
    
    # Convert order_date to datetime for date-based filtering
    df['order_date'] = pd.to_datetime(df['order_date'])
    
    findings = {}
    
    # q1: Overall performance
    total_revenue = df['revenue'].sum()
    order_count = len(df)
    average_order_value = total_revenue / order_count
    findings['total_revenue'] = float(total_revenue)
    findings['order_count'] = int(order_count)
    findings['average_order_value'] = float(average_order_value)
    
    # q2: Regional comparison
    revenue_by_region = df.groupby('region')['revenue'].sum()
    findings['revenue_north'] = float(revenue_by_region.get('North', 0.0))
    findings['revenue_south'] = float(revenue_by_region.get('South', 0.0))
    findings['revenue_east'] = float(revenue_by_region.get('East', 0.0))
    findings['revenue_west'] = float(revenue_by_region.get('West', 0.0))
    
    # q3: Quarterly trend in 2024
    df_2024 = df[df['order_date'].dt.year == 2024]
    df_2024_q1 = df_2024[(df_2024['order_date'].dt.month >= 1) & (df_2024['order_date'].dt.month <= 3)]
    df_2024_q2 = df_2024[(df_2024['order_date'].dt.month >= 4) & (df_2024['order_date'].dt.month <= 6)]
    df_2024_q3 = df_2024[(df_2024['order_date'].dt.month >= 7) & (df_2024['order_date'].dt.month <= 9)]
    df_2024_q4 = df_2024[(df_2024['order_date'].dt.month >= 10) & (df_2024['order_date'].dt.month <= 12)]
    findings['revenue_2024_q1'] = float(df_2024_q1['revenue'].sum())
    findings['revenue_2024_q2'] = float(df_2024_q2['revenue'].sum())
    findings['revenue_2024_q3'] = float(df_2024_q3['revenue'].sum())
    findings['revenue_2024_q4'] = float(df_2024_q4['revenue'].sum())
    
    # q4: Year-over-year change
    revenue_2023 = df[df['order_date'].dt.year == 2023]['revenue'].sum()
    revenue_2024_total = df[df['order_date'].dt.year == 2024]['revenue'].sum()
    revenue_yoy_change_pct = ((revenue_2024_total - revenue_2023) / revenue_2023) * 100
    findings['revenue_2023'] = float(revenue_2023)
    findings['revenue_2024'] = float(revenue_2024_total)
    findings['revenue_yoy_change_pct'] = float(revenue_yoy_change_pct)
    
    # q5: High-discount electronics
    electronics_high_discount = df[(df['product_category'] == 'Electronics') & (df['discount_pct'] >= 20)]
    findings['electronics_high_discount_orders'] = int(len(electronics_high_discount))
    findings['electronics_high_discount_revenue'] = float(electronics_high_discount['revenue'].sum())
    
    # q6: Order revenue distribution
    findings['order_revenue_mean'] = float(df['revenue'].mean())
    findings['order_revenue_median'] = float(df['revenue'].median())
    findings['order_revenue_std'] = float(df['revenue'].std(ddof=1))
    findings['order_revenue_min'] = float(df['revenue'].min())
    findings['order_revenue_max'] = float(df['revenue'].max())
    
    # q7: Customer concentration
    # Exclude UNKNOWN customer_id for customer analysis
    df_known_customers = df[df['customer_id'] != 'UNKNOWN']
    unique_customer_count = df_known_customers['customer_id'].nunique()
    customer_revenue = df_known_customers.groupby('customer_id')['revenue'].sum()
    top_customer_revenue = customer_revenue.max() if len(customer_revenue) > 0 else 0.0
    top_customer_revenue_share_pct = (top_customer_revenue / total_revenue) * 100
    findings['unique_customer_count'] = int(unique_customer_count)
    findings['top_customer_revenue'] = float(top_customer_revenue)
    findings['top_customer_revenue_share_pct'] = float(top_customer_revenue_share_pct)
    
    # Write findings
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
    with open(output_path, 'w') as f:
        json.dump(findings, f)

if __name__ == "__main__":
    main()
