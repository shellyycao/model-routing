import os
import json
import pandas as pd
import numpy as np

INPUT_DIR = os.environ["INPUT_DIR"]
OUTPUT_DIR = os.environ["OUTPUT_DIR"]

# ── R1: Read everything as text, strip whitespace, normalise missing values ──
raw_df = pd.read_csv(
    os.path.join(INPUT_DIR, "raw.csv"),
    dtype=str,
    keep_default_na=False,
)
raw_rows = len(raw_df)

# Strip every cell
raw_df = raw_df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

MISSING_SENTINELS = {"", "na", "n/a", "null", "none", "-"}

def to_missing(val):
    if isinstance(val, str) and val.strip().lower() in MISSING_SENTINELS:
        return np.nan
    return val

raw_df = raw_df.applymap(to_missing)

counts = {}

# ── R2: Deduplicate on order_id (keep first) ──
before_dedup = len(raw_df)
raw_df = raw_df.drop_duplicates(subset=["order_id"], keep="first")
counts["R2_duplicates_removed"] = before_dedup - len(raw_df)
df = raw_df.copy()

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
            return pd.to_datetime(str(val).strip(), format=fmt)
        except (ValueError, TypeError):
            pass
    return pd.NaT

df["order_date"] = df["order_date"].apply(parse_date)
before = len(df)
df = df.dropna(subset=["order_date"])
counts["R3_dropped_bad_date"] = before - len(df)
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
before = len(df)
df = df.dropna(subset=["region"])
counts["R4_dropped_bad_region"] = before - len(df)

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
before = len(df)
df = df.dropna(subset=["product_category"])
counts["R5_dropped_bad_category"] = before - len(df)

# ── R6: Clean unit_price ──
def parse_unit_price(val):
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

df["unit_price"] = df["unit_price"].apply(parse_unit_price)
before = len(df)
df = df.dropna(subset=["unit_price"])
counts["R6_dropped_bad_unit_price"] = before - len(df)

# ── R7: Clean quantity ──
def parse_quantity(val):
    if pd.isna(val):
        return np.nan
    try:
        v = float(str(val).strip())
    except ValueError:
        return np.nan
    if v != int(v):
        return np.nan
    iv = int(v)
    if iv < 1 or iv > 50:
        return np.nan
    return iv

df["quantity"] = df["quantity"].apply(parse_quantity)
before = len(df)
df = df.dropna(subset=["quantity"])
counts["R7_dropped_bad_quantity"] = before - len(df)
df["quantity"] = df["quantity"].astype(int)

# ── R8: Clean discount_pct ──
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
before = len(df)
df = df.dropna(subset=["discount_pct"])
counts["R8_dropped_bad_discount"] = before - len(df)

# ── R9: Normalise customer_id ──
def clean_customer_id(val):
    if pd.isna(val):
        return "UNKNOWN"
    return str(val).strip().upper()

df["customer_id"] = df["customer_id"].apply(clean_customer_id)

# ── R10: Compute revenue ──
df["unit_price"] = df["unit_price"].astype(float)
df["discount_pct"] = df["discount_pct"].astype(float)
df["revenue"] = (
    df["quantity"] * df["unit_price"] * (1 - df["discount_pct"] / 100)
).round(2)

# ── R11: Select, order columns, sort by order_id, write CSV ──
OUTPUT_COLS = [
    "order_id", "order_date", "customer_id", "region", "product_category",
    "quantity", "unit_price", "discount_pct", "revenue",
]
df = df[OUTPUT_COLS].copy()
df = df.sort_values("order_id", ascending=True).reset_index(drop=True)

cleaned_rows = len(df)

df.to_csv(os.path.join(OUTPUT_DIR, "cleaned.csv"), index=False)

# ── Write cleaning summary ──
summary = {
    "raw_rows": raw_rows,
    "cleaned_rows": cleaned_rows,
    "total_rows_dropped": raw_rows - cleaned_rows,
    **counts,
}
with open(os.path.join(OUTPUT_DIR, "cleaning_summary.json"), "w") as f:
    json.dump(summary, f, indent=2)

print(f"Cleaning complete: {raw_rows} raw rows -> {cleaned_rows} cleaned rows.")
