import os
import json
import pandas as pd
import numpy as np

def main():
    # Paths from environment variables
    input_dir = os.getenv('INPUT_DIR')
    output_dir = os.getenv('OUTPUT_DIR')
    if not input_dir or not output_dir:
        raise EnvironmentError('INPUT_DIR and OUTPUT_DIR must be set')

    cleaned_path = os.path.join(input_dir, 'cleaned.csv')
    findings_path = os.path.join(output_dir, 'findings.json')

    # Load cleaned data
    df = pd.read_csv(cleaned_path, parse_dates=['order_date'])

    # ----- q1: Overall performance -----
    total_revenue = df['revenue'].sum()
    order_count = len(df)
    average_order_value = total_revenue / order_count if order_count else 0.0

    # ----- q2: Regional comparison -----
    revenue_by_region = df.groupby('region')['revenue'].sum()
    revenue_north = revenue_by_region.get('North', 0.0)
    revenue_south = revenue_by_region.get('South', 0.0)
    revenue_east = revenue_by_region.get('East', 0.0)
    revenue_west = revenue_by_region.get('West', 0.0)

    # ----- q3: Quarterly trend in 2024 -----
    df_2024 = df[df['order_date'].dt.year == 2024]
    revenue_by_quarter = df_2024.groupby(df_2024['order_date'].dt.quarter)['revenue'].sum()
    revenue_2024_q1 = revenue_by_quarter.get(1, 0.0)
    revenue_2024_q2 = revenue_by_quarter.get(2, 0.0)
    revenue_2024_q3 = revenue_by_quarter.get(3, 0.0)
    revenue_2024_q4 = revenue_by_quarter.get(4, 0.0)

    # ----- q4: Year‑over‑year change -----
    revenue_2023 = df[df['order_date'].dt.year == 2023]['revenue'].sum()
    revenue_2024 = df_2024['revenue'].sum()
    if revenue_2023 != 0:
        revenue_yoy_change_pct = (revenue_2024 - revenue_2023) / revenue_2023 * 100.0
    else:
        revenue_yoy_change_pct = 0.0

    # ----- q5: High‑discount electronics -----
    high_disc_elec = df[(df['product_category'] == 'Electronics') & (df['discount_pct'] >= 20.0)]
    electronics_high_discount_orders = len(high_disc_elec)
    electronics_high_discount_revenue = high_disc_elec['revenue'].sum()

    # ----- q6: Order revenue distribution -----
    order_revenue_mean = df['revenue'].mean()
    order_revenue_median = df['revenue'].median()
    order_revenue_std = df['revenue'].std(ddof=1)  # sample std
    order_revenue_min = df['revenue'].min()
    order_revenue_max = df['revenue'].max()

    # ----- q7: Customer concentration -----
    unique_customer_count = df['customer_id'].nunique()
    revenue_by_customer = df.groupby('customer_id')['revenue'].sum()
    top_customer_revenue = revenue_by_customer.max()
    top_customer_revenue_share_pct = (top_customer_revenue / total_revenue) * 100.0 if total_revenue != 0 else 0.0

    # Assemble findings
    findings = {
        "total_revenue": float(total_revenue),
        "order_count": int(order_count),
        "average_order_value": float(average_order_value),
        "revenue_north": float(revenue_north),
        "revenue_south": float(revenue_south),
        "revenue_east": float(revenue_east),
        "revenue_west": float(revenue_west),
        "revenue_2024_q1": float(revenue_2024_q1),
        "revenue_2024_q2": float(revenue_2024_q2),
        "revenue_2024_q3": float(revenue_2024_q3),
        "revenue_2024_q4": float(revenue_2024_q4),
        "revenue_2023": float(revenue_2023),
        "revenue_2024": float(revenue_2024),
        "revenue_yoy_change_pct": float(revenue_yoy_change_pct),
        "electronics_high_discount_orders": int(electronics_high_discount_orders),
        "electronics_high_discount_revenue": float(electronics_high_discount_revenue),
        "order_revenue_mean": float(order_revenue_mean),
        "order_revenue_median": float(order_revenue_median),
        "order_revenue_std": float(order_revenue_std),
        "order_revenue_min": float(order_revenue_min),
        "order_revenue_max": float(order_revenue_max),
        "unique_customer_count": int(unique_customer_count),
        "top_customer_revenue": float(top_customer_revenue),
        "top_customer_revenue_share_pct": float(top_customer_revenue_share_pct)
    }

    # Write findings to JSON (flat structure, no NaN/Infinity)
    # Ensure all values are finite; replace any possible NaN with 0.0
    for k, v in findings.items():
        if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
            findings[k] = 0.0

    with open(findings_path, 'w', encoding='utf-8') as f:
        json.dump(findings, f, ensure_ascii=False)

if __name__ == '__main__':
    main()
