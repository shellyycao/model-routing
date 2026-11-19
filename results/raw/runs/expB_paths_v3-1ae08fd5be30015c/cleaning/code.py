import os
import json
import pandas as pd
import numpy as np
from datetime import datetime

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def is_missing(val):
    """Return True if the string value should be considered missing.
    The check is case‑insensitive and performed after stripping whitespace.
    """
    if pd.isna(val):
        return True
    v = str(val).strip()
    return v.lower() in {"", "na", "n/a", "null", "none", "-"}

def clean_missing(df):
    """Strip whitespace from every cell and replace defined missing tokens with NaN."""
    return df.applymap(lambda x: np.nan if is_missing(x) else str(x).strip())

def parse_order_date(value):
    """Parse order_date using the allowed formats. Return a string YYYY‑MM‑DD or None."""
    if pd.isna(value):
        return None
    date_str = str(value).strip()
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%Y/%m/%d", "%B %d, %Y"]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None

def map_region(value):
    if pd.isna(value):
        return None
    v = str(value).strip().lower()
    mapping = {
        "n": "North",
        "north": "North",
        "s": "South",
        "south": "South",
        "e": "East",
        "east": "East",
        "w": "West",
        "west": "West",
    }
    return mapping.get(v)

def map_product_category(value):
    if pd.isna(value):
        return None
    # Normalise: lower case, remove spaces and ampersands
    norm = str(value).lower().replace(" ", "").replace("&", "")
    mapping = {
        "electronics": "Electronics",
        "electronic": "Electronics",
        "clothing": "Clothing",
        "apparel": "Clothing",
        "homegarden": "Home & Garden",
        "homeandgarden": "Home & Garden",
        "homegarden": "Home & Garden",
        "sports": "Sports",
        "sport": "Sports",
        "books": "Books",
        "book": "Books",
    }
    return mapping.get(norm)

def clean_unit_price(value):
    if pd.isna(value):
        return None
    v = str(value).replace("$", "").replace("USD", "").replace(",", "").strip()
    try:
        price = float(v)
        return price
    except ValueError:
        return None

def clean_quantity(value):
    if pd.isna(value):
        return None
    try:
        q = float(str(value).strip())
        if not q.is_integer():
            return None
        return int(q)
    except ValueError:
        return None

def clean_discount(value):
    if pd.isna(value):
        return 0.0
    v = str(value).strip()
    if v.endswith('%'):
        v = v[:-1]
    try:
        return float(v)
    except ValueError:
        return None

# ---------------------------------------------------------------------------
# Main cleaning routine
# ---------------------------------------------------------------------------

def main():
    input_dir = os.environ.get("INPUT_DIR")
    output_dir = os.environ.get("OUTPUT_DIR")
    if not input_dir or not output_dir:
        raise RuntimeError("INPUT_DIR and OUTPUT_DIR environment variables must be set")

    raw_path = os.path.join(input_dir, "raw.csv")
    df_raw = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    raw_rows = len(df_raw)

    # R1 – strip whitespace and normalise missing values
    df = clean_missing(df_raw)

    # R2 – remove duplicate order_id rows (keep first)
    dup_mask = df.duplicated(subset=["order_id"], keep='first')
    dup_count = dup_mask.sum()
    df = df[~dup_mask].reset_index(drop=True)

    # Counters for summary
    counters = {
        "duplicates_removed": int(dup_count),
        "invalid_order_date": 0,
        "invalid_region": 0,
        "invalid_product_category": 0,
        "invalid_unit_price": 0,
        "invalid_quantity": 0,
        "invalid_discount_pct": 0,
    }

    cleaned_rows = []
    for _, row in df.iterrows():
        # ----- order_date (R3) -----
        order_date = parse_order_date(row["order_date"])
        if not order_date:
            counters["invalid_order_date"] += 1
            continue

        # ----- region (R4) -----
        region = map_region(row["region"])
        if not region:
            counters["invalid_region"] += 1
            continue

        # ----- product_category (R5) -----
        product_category = map_product_category(row["product_category"])
        if not product_category:
            counters["invalid_product_category"] += 1
            continue

        # ----- unit_price (R6) -----
        unit_price = clean_unit_price(row["unit_price"])
        if unit_price is None or unit_price <= 0 or unit_price > 5000:
            counters["invalid_unit_price"] += 1
            continue

        # ----- quantity (R7) -----
        quantity = clean_quantity(row["quantity"])
        if quantity is None or quantity < 1 or quantity > 50:
            counters["invalid_quantity"] += 1
            continue

        # ----- discount_pct (R8) -----
        discount_pct = clean_discount(row["discount_pct"])
        if discount_pct is None or discount_pct < 0 or discount_pct > 100:
            counters["invalid_discount_pct"] += 1
            continue

        # ----- customer_id (R9) -----
        cust_raw = row["customer_id"]
        if pd.isna(cust_raw):
            customer_id = "UNKNOWN"
        else:
            customer_id = str(cust_raw).upper()

        # ----- revenue (R10) -----
        revenue = round(quantity * unit_price * (1 - discount_pct / 100), 2)

        cleaned_rows.append({
            "order_id": row["order_id"],
            "order_date": order_date,
            "customer_id": customer_id,
            "region": region,
            "product_category": product_category,
            "quantity": quantity,
            "unit_price": unit_price,
            "discount_pct": discount_pct,
            "revenue": revenue,
        })

    df_clean = pd.DataFrame(cleaned_rows)
    # R11 – final column order and sorting
    final_columns = [
        "order_id",
        "order_date",
        "customer_id",
        "region",
        "product_category",
        "quantity",
        "unit_price",
        "discount_pct",
        "revenue",
    ]
    df_clean = df_clean[final_columns]
    df_clean.sort_values(by="order_id", inplace=True)

    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    df_clean.to_csv(cleaned_path, index=False)

    # Write cleaning summary
    summary = {
        "raw_rows": raw_rows,
        "cleaned_rows": len(df_clean),
        **counters,
    }
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    main()
