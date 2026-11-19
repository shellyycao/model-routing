# SYNTHETIC_FIXTURE - test solution, not a model output and not a result.
"""pandas analysis script for retail_sales written ONLY from project.json analysis_questions.

Independent of the trusted pure-Python reference (datasets/retail_sales.py): agreement between
the two is a cross-check of the ground truth. Reads $INPUT_DIR/cleaned.csv, writes
$OUTPUT_DIR/findings.json (flat {metric_key: number}).

`analyze(df, bug=...)` injects one deliberate mistake for negative tests:
  region_mean_not_sum, missing_std, population_std, yoy_wrong_base, discount_gt_not_ge
"""

import json
import os
import sys

import pandas as pd


def analyze(df: pd.DataFrame, bug: str | None = None) -> dict:
    df = df.copy()
    df["order_date"] = pd.to_datetime(df["order_date"], format="%Y-%m-%d")
    rev = df["revenue"].astype(float)
    m = {"total_revenue": rev.sum(), "order_count": len(df)}
    m["average_order_value"] = m["total_revenue"] / m["order_count"]
    agg = "mean" if bug == "region_mean_not_sum" else "sum"
    by_region = df.groupby("region")["revenue"].agg(agg)
    for r in ["North", "South", "East", "West"]:
        m[f"revenue_{r.lower()}"] = by_region.get(r, 0.0)
    y = df["order_date"].dt.year
    d24 = df[y == 2024]
    by_q = d24.groupby(d24["order_date"].dt.quarter)["revenue"].sum()
    for q in range(1, 5):
        m[f"revenue_2024_q{q}"] = by_q.get(q, 0.0)
    m["revenue_2023"] = df.loc[y == 2023, "revenue"].sum()
    m["revenue_2024"] = df.loc[y == 2024, "revenue"].sum()
    base = m["revenue_2024"] if bug == "yoy_wrong_base" else m["revenue_2023"]
    m["revenue_yoy_change_pct"] = (m["revenue_2024"] - m["revenue_2023"]) / base * 100
    disc = df["discount_pct"] > 20 if bug == "discount_gt_not_ge" else df["discount_pct"] >= 20
    sel = df[(df["product_category"] == "Electronics") & disc]
    m["electronics_high_discount_orders"] = len(sel)
    m["electronics_high_discount_revenue"] = sel["revenue"].sum()
    m["order_revenue_mean"] = rev.mean()
    m["order_revenue_median"] = rev.median()
    m["order_revenue_std"] = rev.std(ddof=0 if bug == "population_std" else 1)
    m["order_revenue_min"] = rev.min()
    m["order_revenue_max"] = rev.max()
    by_customer = df.groupby("customer_id")["revenue"].sum()
    m["unique_customer_count"] = df["customer_id"].nunique()
    m["top_customer_revenue"] = by_customer.max()
    m["top_customer_revenue_share_pct"] = m["top_customer_revenue"] / m["total_revenue"] * 100
    if bug == "missing_std":
        del m["order_revenue_std"]
    return {k: float(v) for k, v in m.items()}


def main():
    inp, out = os.environ["INPUT_DIR"], os.environ["OUTPUT_DIR"]
    df = pd.read_csv(os.path.join(inp, "cleaned.csv"))
    bug = sys.argv[1] if len(sys.argv) > 1 else None
    with open(os.path.join(out, "findings.json"), "w") as fh:
        json.dump(analyze(df, bug), fh, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
