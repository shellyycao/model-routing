import os
import re
import json
import math
from datetime import datetime

import numpy as np
import pandas as pd

INPUT_DIR = os.environ["INPUT_DIR"]
OUTPUT_DIR = os.environ["OUTPUT_DIR"]
os.makedirs(OUTPUT_DIR, exist_ok=True)

RAW_PATH = os.path.join(INPUT_DIR, "raw.csv")
CLEAN_PATH = os.path.join(OUTPUT_DIR, "cleaned.csv")
SUMMARY_PATH = os.path.join(OUTPUT_DIR, "cleaning_summary.json")

MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}

DATE_FORMATS = (
    "%Y-%m-%d",   # YYYY-MM-DD
    "%m/%d/%Y",   # MM/DD/YYYY (month first)
    "%d-%b-%Y",   # DD-Mon-YYYY, e.g. 05-Mar-2024
    "%Y/%m/%d",   # YYYY/MM/DD
    "%B %d, %Y",  # Month D, YYYY, e.g. March 5, 2024
)

REGION_MAP = {
    "north": "North", "south": "South", "east": "East", "west": "West",
    "n": "North", "s": "South", "e": "East", "w": "West",
}

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


def normalize_cell(value):
    """R1: strip whitespace; map configured missing tokens (case-insensitive) to NaN."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return np.nan
    text = str(value).strip()
    if text.lower() in MISSING_TOKENS:
        return np.nan
    return text


def parse_date(text):
    """R3: try each allowed format exactly; return datetime or None."""
    if not isinstance(text, str):
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def parse_unit_price(text):
    """R6: strip '$', 'USD', ',' (plus spaces adjacent to $ and ,) then parse as float."""
    if not isinstance(text, str):
        return np.nan
    cleaned = re.sub(r"\s*[$,]\s*", "", text)
    cleaned = cleaned.replace("USD", "").strip()
    if cleaned == "":
        return np.nan
    try:
        value = float(cleaned)
    except ValueError:
        return np.nan
    if not math.isfinite(value):
        return np.nan
    return value


def parse_quantity(text):
    """R7: parse as number; must be a finite whole number."""
    if not isinstance(text, str):
        return np.nan
    try:
        value = float(text)
    except ValueError:
        return np.nan
    if not math.isfinite(value) or not value.is_integer():
        return np.nan
    return value


def parse_discount(text):
    """R8: remove one trailing '%', then parse as a finite number."""
    if not isinstance(text, str):
        return np.nan
    cleaned = text[:-1].strip() if text.endswith("%") else text
    if cleaned == "":
        return np.nan
    try:
        value = float(cleaned)
    except ValueError:
        return np.nan
    if not math.isfinite(value):
        return np.nan
    return value


summary = {}

# R1: read every column as text, strip, normalise missing tokens.
df = pd.read_csv(RAW_PATH, dtype=str, keep_default_na=False, na_filter=False)
summary["raw_rows"] = int(len(df))
for col in df.columns:
    df[col] = df[col].map(normalize_cell)

# R2: drop duplicate order_id rows FIRST, keeping the first occurrence in raw-file order.
before = len(df)
df = df.drop_duplicates(subset="order_id", keep="first")
summary["duplicates_removed"] = int(before - len(df))

# order_id cannot be imputed; drop rows where it is missing (schema requires it non-null).
before = len(df)
df = df[df["order_id"].notna()]
summary["dropped_missing_order_id"] = int(before - len(df))

# R3: order_date parsing / filtering, output as YYYY-MM-DD.
parsed_dates = df["order_date"].map(parse_date)
valid = parsed_dates.notna()
summary["dropped_missing_or_unparseable_order_date"] = int((~valid).sum())
df = df.loc[valid].copy()
df["order_date"] = parsed_dates.loc[valid].map(lambda d: d.strftime("%Y-%m-%d"))

# R4: region canonicalisation.
mapped_region = df["region"].map(lambda v: REGION_MAP.get(v.lower()) if isinstance(v, str) else None)
valid = mapped_region.notna()
summary["dropped_missing_or_invalid_region"] = int((~valid).sum())
df = df.loc[valid].copy()
df["region"] = mapped_region.loc[valid]

# R5: product_category canonicalisation.
mapped_cat = df["product_category"].map(lambda v: CATEGORY_MAP.get(v.lower()) if isinstance(v, str) else None)
valid = mapped_cat.notna()
summary["dropped_missing_or_invalid_product_category"] = int((~valid).sum())
df = df.loc[valid].copy()
df["product_category"] = mapped_cat.loc[valid]

# R6: unit_price cleaning and range filter (0 < price <= 5000); value kept as given.
price = df["unit_price"].map(parse_unit_price)
valid = price.notna() & (price > 0) & (price <= 5000)
summary["dropped_missing_or_invalid_unit_price"] = int((~valid).sum())
df = df.loc[valid].copy()
df["unit_price"] = price.loc[valid].astype(float)

# R7: quantity must be a whole number in [1, 50]; stored as integer.
qty = df["quantity"].map(parse_quantity)
valid = qty.notna() & (qty >= 1) & (qty <= 50)
summary["dropped_missing_or_invalid_quantity"] = int((~valid).sum())
df = df.loc[valid].copy()
df["quantity"] = qty.loc[valid].astype(int)

# R8: discount_pct; missing means no discount (0); must be within [0, 100].
missing_disc = df["discount_pct"].isna()
summary["missing_discount_pct_set_to_zero"] = int(missing_disc.sum())
disc = df["discount_pct"].map(parse_discount)
disc = disc.mask(missing_disc, 0.0)
valid = disc.notna() & (disc >= 0) & (disc <= 100)
summary["dropped_invalid_discount_pct"] = int((~valid).sum())
df = df.loc[valid].copy()
df["discount_pct"] = disc.loc[valid].astype(float)

# R9: customer_id upper-cased; missing becomes 'UNKNOWN' (row kept).
missing_cust = df["customer_id"].isna()
summary["missing_customer_id_set_to_unknown"] = int(missing_cust.sum())
df["customer_id"] = df["customer_id"].map(lambda v: "UNKNOWN" if not isinstance(v, str) else v.upper())

# R10: revenue = quantity * unit_price * (1 - discount_pct/100), rounded to 2 decimals.
df["revenue"] = (df["quantity"] * df["unit_price"] * (1.0 - df["discount_pct"] / 100.0)).round(2)

# R11: final column selection/order, sort by order_id ascending, write CSV without index.
df = df[["order_id", "order_date", "customer_id", "region", "product_category",
         "quantity", "unit_price", "discount_pct", "revenue"]]
df = df.sort_values("order_id", kind="mergesort").reset_index(drop=True)
df.to_csv(CLEAN_PATH, index=False)
summary["cleaned_rows"] = int(len(df))

with open(SUMMARY_PATH, "w", encoding="utf-8") as fh:
    json.dump(summary, fh, indent=2)
