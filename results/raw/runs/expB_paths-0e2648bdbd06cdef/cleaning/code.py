import os
import json
import pandas as pd
import numpy as np

INPUT_DIR = os.environ["INPUT_DIR"]
OUTPUT_DIR = os.environ["OUTPUT_DIR"]

# ── R1: Read everything as text, strip whitespace, normalise missing values ──
raw_path = os.path.join(INPUT_DIR, "raw.csv")
df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
raw_rows = len(df)

# Strip every cell
df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

MISSING_SENTINELS = {"", "na", "n/a", "null", "none", "-"}

def to_missing(val):
    if isinstance(val, str) and val.strip().lower() in MISSING_SENTINELS:
        return np.nan
    return val

df = df.applymap(to_missing)

# ── R2: Deduplicate on order_id (keep first) ──
before_dedup = len(df)
df = df.drop_duplicates(subset=["order_id"], keep="first")
duplicates_removed = before_dedup - len(df)

# ── R3: Parse order_date ──
DATE_FORMATS = [
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%d-%b-%Y",
    "%Y/%m/%d",
    "%B %d, %Y",
]

def parse_date(val):
    if pd.isna(val):
        return pd.NaT
    for fmt in DATE_FORMATS:
        try:
            return pd.to_datetime(val, format=fmt)
        except (ValueError, TypeError):
            pass
    return pd.NaT

df["order_date"] = df["order_date"].apply(parse_date)
before_date = len(df)
df = df.dropna(subset=["order_date"])
date_dropped = before_date - len(df)
df["order_date"] = df["order_date"].dt.strftime("%Y-%m-%d")

# ── R4: Normalise region ──
REGION_MAP = {
    "north": "North", "n": "North",
    "south": "South", "s": "South",
    "east": "East",  "e": "East",
    "west": "West",  "w": "West",
}

def map_region(val):
    if pd.isna(val):
        return np.nan
    return REGION_MAP.get(str(val).strip().lower(), np.nan)

df["region"] = df["region"].apply(map_region)
before_region = len(df)
df = df.dropna(subset=["region"])
region_dropped = before_region - len(df)

# ── R5: Normalise product_category ──
CATEGORY_MAP = {
    "electronics": "Electronics",
    "electronic": "Electronics",
    "clothing": "Clothing",
    "apparel": "Clothing",
    "home & garden": "Home & Garden",
    "home and garden": "Home & Garden",
    "home&garden": "Home & Garden",
    "sports": "Sports",
    "sport": "Sports",
    "books": "Books",
    "book": "Books",
}

def map_category(val):
    if pd.isna(val):
        return np.nan
    return CATEGORY_MAP.get(str(val).strip().lower(), np.nan)

df["product_category"] = df["product_category"].apply(map_category)
before_cat = len(df)
df = df.dropna(subset=["product_category"])
category_dropped = before_cat - len(df)

# ── R6: Parse unit_price ──
def parse_price(val):
    if pd.isna(val):
        return np.nan
    s = str(val).replace("$", "").replace("USD", "").replace(",", "").strip()
    try:
        v = float(s)
    except ValueError:
        return np.nan
    if v <= 0 or v > 5000:
        return np.nan
    return v

df["unit_price"] = df["unit_price"].apply(parse_price)
before_price = len(df)
df = df.dropna(subset=["unit_price"])
price_dropped = before_price - len(df)

# ── R7: Parse quantity ──
def parse_quantity(val):
    if pd.isna(val):
        return np.nan
    try:
        f = float(str(val).strip())
    except ValueError:
        return np.nan
    if f != int(f):
        return np.nan
    i = int(f)
    if i < 1 or i > 50:
        return np.nan
    return i

df["quantity"] = df["quantity"].apply(parse_quantity)
before_qty = len(df)
df = df.dropna(subset=["quantity"])
qty_dropped = before_qty - len(df)
df["quantity"] = df["quantity"].astype(int)

# ── R8: Parse discount_pct ──
def parse_discount(val):
    if pd.isna(val):
        return 0.0
    s = str(val).strip().rstrip("%").strip()
    try:
        v = float(s)
    except ValueError:
        return np.nan
    if v < 0 or v > 100:
        return np.nan
    return v

df["discount_pct"] = df["discount_pct"].apply(parse_discount)
before_disc = len(df)
df = df.dropna(subset=["discount_pct"])
disc_dropped = before_disc - len(df)

# ── R9: customer_id ──
def clean_customer(val):
    if pd.isna(val):
        return "UNKNOWN"
    return str(val).strip().upper()

df["customer_id"] = df["customer_id"].apply(clean_customer)

# ── R10: Compute revenue ──
df["revenue"] = (
    df["quantity"] * df["unit_price"] * (1 - df["discount_pct"] / 100)
).round(2)

# ── R11: Select, order columns, sort by order_id ──
COLUMNS = [
    "order_id", "order_date", "customer_id", "region",
    "product_category", "quantity", "unit_price", "discount_pct", "revenue"
]
df = df[COLUMNS]
df = df.sort_values("order_id", ascending=True).reset_index(drop=True)

cleaned_rows = len(df)

# ── Write cleaned CSV ──
out_csv = os.path.join(OUTPUT_DIR, "cleaned.csv")
df.to_csv(out_csv, index=False)

# ── Write cleaning summary ──
summary = {
    "raw_rows": raw_rows,
    "cleaned_rows": cleaned_rows,
    "duplicates_removed": duplicates_removed,
    "dropped_bad_date": date_dropped,
    "dropped_bad_region": region_dropped,
    "dropped_bad_category": category_dropped,
    "dropped_bad_unit_price": price_dropped,
    "dropped_bad_quantity": qty_dropped,
    "dropped_bad_discount": disc_dropped,
    "total_dropped": raw_rows - cleaned_rows,
}
out_json = os.path.join(OUTPUT_DIR, "cleaning_summary.json")
with open(out_json, "w") as f:
    json.dump(summary, f, indent=2)

print(f"Cleaning complete: {raw_rows} raw rows -> {cleaned_rows} cleaned rows.")
