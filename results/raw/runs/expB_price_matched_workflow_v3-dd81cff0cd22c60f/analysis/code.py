import json
import os

import pandas as pd


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    # Read the cleaned data; keep identifier columns as strings.
    df = pd.read_csv(
        input_path,
        dtype={"order_id": str, "customer_id": str, "region": str, "product_category": str},
    )
    df["order_date"] = pd.to_datetime(df["order_date"], format="%Y-%m-%d")
    df["revenue"] = pd.to_numeric(df["revenue"], errors="raise").astype(float)
    df["discount_pct"] = pd.to_numeric(df["discount_pct"], errors="raise").astype(float)
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="raise").astype(float)
    df["quantity"] = pd.to_numeric(df["quantity"], errors="raise").astype(int)

    findings = {}

    # q1: Overall performance
    total_revenue = float(df["revenue"].sum())
    order_count = int(len(df))
    findings["total_revenue"] = total_revenue
    findings["order_count"] = order_count
    findings["average_order_value"] = total_revenue / order_count

    # q2: Regional comparison (explicit lookup so a missing region yields 0.0)
    revenue_by_region = df.groupby("region")["revenue"].sum()
    for region, key in (
        ("North", "revenue_north"),
        ("South", "revenue_south"),
        ("East", "revenue_east"),
        ("West", "revenue_west"),
    ):
        findings[key] = float(revenue_by_region.get(region, 0.0))

    # q3 & q4: calendar quarters of 2024 and year-over-year change
    year = df["order_date"].dt.year
    revenue_2023 = float(df.loc[year == 2023, "revenue"].sum())
    revenue_2024 = float(df.loc[year == 2024, "revenue"].sum())
    findings["revenue_2023"] = revenue_2023
    findings["revenue_2024"] = revenue_2024
    findings["revenue_yoy_change_pct"] = (revenue_2024 - revenue_2023) / revenue_2023 * 100.0

    is_2024 = year == 2024
    quarter = df["order_date"].dt.quarter
    for q in (1, 2, 3, 4):
        findings[f"revenue_2024_q{q}"] = float(
            df.loc[is_2024 & (quarter == q), "revenue"].sum()
        )

    # q5: High-discount electronics orders (discount_pct >= 20)
    hd_mask = (df["product_category"] == "Electronics") & (df["discount_pct"] >= 20.0)
    hd = df.loc[hd_mask]
    findings["electronics_high_discount_orders"] = int(len(hd))
    findings["electronics_high_discount_revenue"] = float(hd["revenue"].sum())

    # q6: Order revenue distribution over all orders (sample std, ddof=1)
    rev = df["revenue"]
    findings["order_revenue_mean"] = float(rev.mean())
    findings["order_revenue_median"] = float(rev.median())
    findings["order_revenue_std"] = float(rev.std(ddof=1))
    findings["order_revenue_min"] = float(rev.min())
    findings["order_revenue_max"] = float(rev.max())

    # q7: Customer concentration
    revenue_by_customer = df.groupby("customer_id")["revenue"].sum()
    top_customer_revenue = float(revenue_by_customer.max())
    findings["unique_customer_count"] = int(df["customer_id"].nunique())
    findings["top_customer_revenue"] = top_customer_revenue
    findings["top_customer_revenue_share_pct"] = top_customer_revenue / total_revenue * 100.0

    os.makedirs(os.environ["OUTPUT_DIR"], exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(findings, f, indent=2, allow_nan=False)


if __name__ == "__main__":
    main()
