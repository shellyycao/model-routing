# SYNTHETIC_FIXTURE - test solution, not a model output and not a result.
"""pandas cleaning script for retail_sales written ONLY from project.json cleaning_requirements.

It plays the role of a model-generated cleaning script: reads $INPUT_DIR/raw.csv, writes
$OUTPUT_DIR/cleaned.csv and cleaning_summary.json. It is deliberately independent of the trusted
reference implementation in datasets/retail_sales.py (different library, different code), so a
pass by the validator shows the requirements are followable to the reference result.

`clean(raw, bug=...)` injects one deliberate mistake for negative tests:
  no_dedup, dayfirst_slash, no_category_synonyms, keep_invalid_quantity, drop_revenue,
  revenue_ignores_discount, unsorted_with_index
"""

import json
import os
import re
import sys

import pandas as pd

MISSING = {"", "na", "n/a", "null", "none", "-"}
MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august",
          "september", "october", "november", "december"]


def _date(s, dayfirst_slash=False):
    if not isinstance(s, str):
        return None
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", s) or re.fullmatch(r"(\d{4})/(\d{2})/(\d{2})", s)
    try:
        if m:
            return pd.Timestamp(int(m[1]), int(m[2]), int(m[3]))
        if m := re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", s):
            a, b = int(m[1]), int(m[2])
            month, day = (b, a) if dayfirst_slash else (a, b)
            return pd.Timestamp(int(m[3]), month, day)
        if m := re.fullmatch(r"(\d{2})-([A-Za-z]{3})-(\d{4})", s):
            abbr = [x[:3] for x in MONTHS]
            return pd.Timestamp(int(m[3]), abbr.index(m[2].lower()) + 1, int(m[1]))
        if m := re.fullmatch(r"([A-Za-z]+) (\d{1,2}), (\d{4})", s):
            return pd.Timestamp(int(m[3]), MONTHS.index(m[1].lower()) + 1, int(m[2]))
    except ValueError:
        return None
    return None


def _num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def clean(raw: pd.DataFrame, bug: str | None = None) -> pd.DataFrame:
    df = raw.copy()
    for c in df.columns:  # R1
        df[c] = df[c].map(lambda v: None if v is None or str(v).strip().lower() in MISSING else str(v).strip())
    if bug != "no_dedup":  # R2
        df = df.drop_duplicates(subset="order_id", keep="first")
    df["order_date"] = df["order_date"].map(lambda s: _date(s, dayfirst_slash=bug == "dayfirst_slash"))  # R3
    df = df[df["order_date"].notna()]
    regions = {"north": "North", "south": "South", "east": "East", "west": "West",
               "n": "North", "s": "South", "e": "East", "w": "West"}
    df["region"] = df["region"].map(lambda s: regions.get(s.lower()) if isinstance(s, str) else None)  # R4
    df = df[df["region"].notna()]
    cats = {c.lower(): c for c in ["Electronics", "Clothing", "Home & Garden", "Sports", "Books"]}
    if bug != "no_category_synonyms":
        cats |= {"electronic": "Electronics", "home and garden": "Home & Garden", "home&garden": "Home & Garden",
                 "sport": "Sports", "apparel": "Clothing", "book": "Books"}
    df["product_category"] = df["product_category"].map(lambda s: cats.get(s.lower()) if isinstance(s, str) else None)  # R5
    df = df[df["product_category"].notna()]
    df["unit_price"] = df["unit_price"].map(  # R6
        lambda s: _num(s.replace("$", "").replace("USD", "").replace(",", "").strip()) if isinstance(s, str) else None)
    df = df[df["unit_price"].notna() & (df["unit_price"] > 0) & (df["unit_price"] <= 5000)]
    df["quantity"] = df["quantity"].map(_num)  # R7
    ok = df["quantity"].notna() & (df["quantity"] == df["quantity"].round())
    if bug != "keep_invalid_quantity":
        ok &= (df["quantity"] >= 1) & (df["quantity"] <= 50)
    df = df[ok]
    df["quantity"] = df["quantity"].astype(int)
    df["discount_pct"] = df["discount_pct"].map(  # R8
        lambda s: 0.0 if not isinstance(s, str) else _num(s[:-1] if s.endswith("%") else s))
    df = df[df["discount_pct"].notna() & (df["discount_pct"] >= 0) & (df["discount_pct"] <= 100)]
    df["customer_id"] = df["customer_id"].map(lambda s: s.upper() if isinstance(s, str) else "UNKNOWN")  # R9
    factor = 1.0 if bug == "revenue_ignores_discount" else (1 - df["discount_pct"] / 100)
    df["revenue"] = (df["quantity"] * df["unit_price"] * factor).round(2)  # R10
    df["order_date"] = df["order_date"].map(lambda t: t.strftime("%Y-%m-%d"))
    cols = ["order_id", "order_date", "customer_id", "region", "product_category", "quantity",
            "unit_price", "discount_pct", "revenue"]
    if bug == "drop_revenue":
        cols.remove("revenue")
    df = df[cols]
    if bug != "unsorted_with_index":
        df = df.sort_values("order_id").reset_index(drop=True)  # R11
    return df


def main():
    inp, out = os.environ["INPUT_DIR"], os.environ["OUTPUT_DIR"]
    raw = pd.read_csv(os.path.join(inp, "raw.csv"), dtype=str, keep_default_na=False)
    bug = sys.argv[1] if len(sys.argv) > 1 else None
    cleaned = clean(raw, bug)
    cleaned.to_csv(os.path.join(out, "cleaned.csv"), index=bug == "unsorted_with_index",
                   float_format="%.2f", lineterminator="\n")
    with open(os.path.join(out, "cleaning_summary.json"), "w") as fh:
        json.dump({"raw_rows": len(raw), "cleaned_rows": len(cleaned)}, fh)


if __name__ == "__main__":
    main()
