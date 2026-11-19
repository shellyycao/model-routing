import os
import json
import pandas as pd

def main():
    input_dir = os.getenv('INPUT_DIR')
    output_dir = os.getenv('OUTPUT_DIR')
    if not input_dir or not output_dir:
        raise EnvironmentError('INPUT_DIR and OUTPUT_DIR must be set')

    # Load cleaned data
    df = pd.read_csv(os.path.join(input_dir, 'cleaned.csv'), parse_dates=['order_date'])

    # --------------------
    # q1: Overall performance
    # --------------------
    total_revenue = df['revenue'].sum()
    order_count = len(df)
    average_order_value = total_revenue / order_count if order_count else 0.0

    # --------------------
    # q2: Regional comparison
    # --------------------
    region_rev = df.groupby('region')['revenue'].sum()
    revenue_north = region_rev.get('North', 0.0)
    revenue_south = region_rev.get('South', 0.0)
    revenue_east = region_rev.get('East', 0.0)
    revenue_west = region_rev.get('West', 0.0)

    # --------------------
    # q4: Year‑over‑year change (2023 vs 2024)
    # --------------------
    df['year'] = df['order_date'].dt.year
    revenue_2023 = df.loc[df['year'] == 2023, 'revenue'].sum()
    revenue_2024 = df.loc[df['year'] == 2024, 'revenue'].sum()
    revenue_yoy_change_pct = ((revenue_2024 - revenue_2023) / revenue_2023 * 100) if revenue_2023 != 0 else 0.0

    # --------------------
    # q3: Quarterly trend in 2024
    # --------------------
    df_2024 = df[df['year'] == 2024].copy()
    df_2024['quarter'] = df_2024['order_date'].dt.quarter
    quarterly_rev = df_2024.groupby('quarter')['revenue'].sum()
    revenue_2024_q1 = quarterly_rev.get(1, 0.0)
    revenue_2024_q2 = quarterly_rev.get(2, 0.0)
    revenue_2024_q3 = quarterly_rev.get(3, 0.0)
    revenue_2024_q4 = quarterly_rev.get(4, 0.0)

    # --------------------
    # q5: High‑discount electronics
    # --------------------
    high_disc_elec = df[(df['product_category'] == 'Electronics') & (df['discount_pct'] >= 20)]
    electronics_high_discount_orders = len(high_disc_elec)
    electronics_high_discount_revenue = high_disc_elec['revenue'].sum()

    # --------------------
    # q6: Order revenue distribution
    # --------------------
    order_revenue_mean = df['revenue'].mean()
    order_revenue_median = df['revenue'].median()
    order_revenue_std = df['revenue'].std(ddof=1)  # sample standard deviation
    order_revenue_min = df['revenue'].min()
    order_revenue_max = df['revenue'].max()

    # --------------------
    # q7: Customer concentration
    # --------------------
    unique_customer_count = df['customer_id'].nunique()
    customer_rev = df.groupby('customer_id')['revenue'].sum()
    top_customer_revenue = customer_rev.max()
    top_customer_revenue_share_pct = (top_customer_revenue / total_revenue * 100) if total_revenue != 0 else 0.0

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

    # Write results
    output_path = os.path.join(output_dir, 'findings.json')
    with open(output_path, 'w') as f:
        json.dump(findings, f, allow_nan=False)

if __name__ == "__main__":
    main()
