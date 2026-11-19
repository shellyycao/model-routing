import os
import json
import pandas as pd
import numpy as np

def main():
    # Paths from environment variables
    input_dir = os.getenv('INPUT_DIR')
    output_dir = os.getenv('OUTPUT_DIR')
    if input_dir is None or output_dir is None:
        raise EnvironmentError('INPUT_DIR and OUTPUT_DIR must be set')

    cleaned_path = os.path.join(input_dir, 'cleaned.csv')
    findings_path = os.path.join(output_dir, 'findings.json')

    # Load cleaned data
    df = pd.read_csv(cleaned_path, parse_dates=['order_date'])

    # ----- q1: overall performance -----
    total_revenue = df['revenue'].sum()
    order_count = len(df)
    average_order_value = total_revenue / order_count if order_count else 0.0

    # ----- q2: regional revenue -----
    region_rev = df.groupby('region')['revenue'].sum()
    revenue_north = float(region_rev.get('North', 0.0))
    revenue_south = float(region_rev.get('South', 0.0))
    revenue_east = float(region_rev.get('East', 0.0))
    revenue_west = float(region_rev.get('West', 0.0))

    # ----- q3: quarterly trend for 2024 -----
    df_2024 = df[df['order_date'].dt.year == 2024]
    # Determine quarter number (1-4)
    quarters = ((df_2024['order_date'].dt.month - 1) // 3) + 1
    df_2024 = df_2024.assign(quarter=quarters)
    quarterly_rev = df_2024.groupby('quarter')['revenue'].sum()
    revenue_2024_q1 = float(quarterly_rev.get(1, 0.0))
    revenue_2024_q2 = float(quarterly_rev.get(2, 0.0))
    revenue_2024_q3 = float(quarterly_rev.get(3, 0.0))
    revenue_2024_q4 = float(quarterly_rev.get(4, 0.0))

    # ----- q4: year‑over‑year -----
    revenue_2023 = float(df[df['order_date'].dt.year == 2023]['revenue'].sum())
    revenue_2024 = float(df_2024['revenue'].sum())
    if revenue_2023 != 0:
        revenue_yoy_change_pct = (revenue_2024 - revenue_2023) / revenue_2023 * 100.0
    else:
        revenue_yoy_change_pct = 0.0

    # ----- q5: high‑discount electronics -----
    high_disc_elec = df[(df['product_category'] == 'Electronics') & (df['discount_pct'] >= 20)]
    electronics_high_discount_orders = int(high_disc_elec.shape[0])
    electronics_high_discount_revenue = float(high_disc_elec['revenue'].sum())

    # ----- q6: order revenue distribution -----
    revenue_series = df['revenue']
    order_revenue_mean = float(revenue_series.mean())
    order_revenue_median = float(revenue_series.median())
    order_revenue_std = float(revenue_series.std(ddof=1))
    order_revenue_min = float(revenue_series.min())
    order_revenue_max = float(revenue_series.max())

    # ----- q7: customer concentration -----
    unique_customer_count = int(df['customer_id'].nunique())
    customer_rev = df.groupby('customer_id')['revenue'].sum()
    top_customer_revenue = float(customer_rev.max())
    top_customer_revenue_share_pct = (top_customer_revenue / total_revenue * 100.0) if total_revenue else 0.0

    # Assemble findings
    findings = {
        "total_revenue": float(total_revenue),
        "order_count": int(order_count),
        "average_order_value": float(average_order_value),
        "revenue_north": revenue_north,
        "revenue_south": revenue_south,
        "revenue_east": revenue_east,
        "revenue_west": revenue_west,
        "revenue_2024_q1": revenue_2024_q1,
        "revenue_2024_q2": revenue_2024_q2,
        "revenue_2024_q3": revenue_2024_q3,
        "revenue_2024_q4": revenue_2024_q4,
        "revenue_2023": revenue_2023,
        "revenue_2024": revenue_2024,
        "revenue_yoy_change_pct": float(revenue_yoy_change_pct),
        "electronics_high_discount_orders": electronics_high_discount_orders,
        "electronics_high_discount_revenue": electronics_high_discount_revenue,
        "order_revenue_mean": order_revenue_mean,
        "order_revenue_median": order_revenue_median,
        "order_revenue_std": order_revenue_std,
        "order_revenue_min": order_revenue_min,
        "order_revenue_max": order_revenue_max,
        "unique_customer_count": unique_customer_count,
        "top_customer_revenue": top_customer_revenue,
        "top_customer_revenue_share_pct": float(top_customer_revenue_share_pct)
    }

    # Write findings to JSON (flat, no NaN/Inf)
    with open(findings_path, 'w', encoding='utf-8') as f:
        json.dump(findings, f, ensure_ascii=False, separators=(',', ':'))

if __name__ == '__main__':
    main()
