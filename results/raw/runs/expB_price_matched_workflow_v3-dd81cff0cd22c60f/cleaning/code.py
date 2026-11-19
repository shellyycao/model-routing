import os
import re
import json
from datetime import datetime

import numpy as np
import pandas as pd

INPUT_DIR = os.environ["INPUT_DIR"]
OUTPUT_DIR = os.environ["OUTPUT_DIR"]
os.makedirs(OUTPUT_DIR, exist_ok=True)

MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}
summary = {}

# ---------------- R1: read everything as text, strip, normalise missing ----------------
raw_path = os.path.join(INPUT_DIR, "raw.csv")
df = pd.read_csv(raw_path, dtype=str, keep_default_na=False, na_filter=False)
summary["raw_rows"] = int(len(df))

def clean_text(v):
    if not isinstance(v, str):
        return v
    v = v.strip()
    if v.lower() in MISSING_TOKENS:
        return None
    return v

for col in df.columns:
    df[col] = df[col].map(clean_text)

# ---------------- R2: drop duplicate order_id (keep first in raw order) ----------------
before = len(df)
df = df.drop_duplicates(subset="order_id", keep="first")
summary["duplicates_removed"] = int(before - len(df))

# order_id is not nullable in the required schema
before = len(df)
df = df[df["order_id"].notna()].copy()
summary["dropped_missing_order_id"] = int(before - len(df))

# ---------------- helpers ----------------
def apply_rule(df, col, func, drop_key):
    """Map col through func (None => invalid), drop invalid rows, count drops."""
    parsed = df[col].map(func)
    mask = parsed.notna()
    summary[drop_key] = int((~mask).sum())
    out = df.loc[mask].copy()
    out[col] = parsed.loc[mask]
    return out

# ---------------- R3: order_date ----------------
MONTHS_ABBR = {m.lower(): i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}
MONTHS_FULL = {m.lower(): i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], 1)}

def parse_order_date(s):
    if s is None:
        return None
    s = str(s)
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", s)            # YYYY-MM-DD
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    else:
        m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", s)        # MM/DD/YYYY
        if m:
            mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        else:
            m = re.fullmatch(r"(\d{2})-([A-Za-z]{3})-(\d{4})", s)  # DD-Mon-YYYY
            if m:
                mo = MONTHS_ABBR.get(m.group(2).lower())
                if mo is None:
                    return None
                d, y = int(m.group(1)), int(m.group(3))
            else:
                m = re.fullmatch(r"(\d{4})/(\d{2})/(\d{2})", s)  # YYYY/MM/DD
                if m:
                    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
                else:
                    m = re.fullmatch(r"([A-Za-z]+) (\d{1,2}), (\d{4})", s)  # Month D, YYYY
                    if not m:
                        return None
                    mo = MONTHS_FULL.get(m.group(1).lower())
                    if mo is None:
                        return None
                    d, y = int(m.group(2)), int(m.group(3))
    try:
        return datetime(y, mo, d).strftime("%Y-%m-%d")
    except ValueError:
        return None

df = apply_rule(df, "order_date", parse_order_date, "dropped_invalid_order_date")

# ---------------- R4: region ----------------
REGION_MAP = {
    "north": "North", "south": "South", "east": "East", "west": "West",
    "n": "North", "s": "South", "e": "East", "w": "West",
}

def parse_region(s):
    if s is None:
        return None
    return REGION_MAP.get(str(s).strip().lower())

df = apply_rule(df, "region", parse_region, "dropped_invalid_region")

# ---------------- R5: product_category ----------------
CAT_MAP = {
    "electronics": "Electronics", "electronic": "Electronics",
    "clothing": "Clothing", "apparel": "Clothing",
    "home & garden": "Home & Garden", "home and garden": "Home & Garden",
    "home&garden": "Home & Garden",
    "sports": "Sports", "sport": "Sports",
    "books": "Books", "book": "Books",
}
CAT_MAP_NOSPACE = {k.replace(" ", ""): v for k, v in CAT_MAP.items()}

def parse_category(s):
    if s is None:
        return None
    key = re.sub(r"\s+", " ", str(s).strip().lower())
    hit = CAT_MAP.get(key)
    if hit is not None:
        return hit
    return CAT_MAP_NOSPACE.get(key.replace(" ", ""))

df = apply_rule(df, "product_category", parse_category, "dropped_invalid_product_category")

# ---------------- R6: unit_price ----------------
def parse_unit_price(s):
    if s is None:
        return None
    t = re.sub(r"(?i)usd", "", str(s))
    t = t.replace("$", "").replace(",", "").strip()
    if not t:
        return None
    try:
        v = float(t)
    except ValueError:
        return None
    if not np.isfinite(v) or v <= 0 or v > 5000:
        return None
    return v

df = apply_rule(df, "unit_price", parse_unit_price, "dropped_invalid_unit_price")
df["unit_price"] = df["unit_price"].astype(float)

# ---------------- R7: quantity ----------------
def parse_quantity(s):
    if s is None:
        return None
    try:
        v = float(str(s).strip())
    except ValueError:
        return None
    if not np.isfinite(v) or not v.is_integer():
        return None
    iv = int(v)
    if iv < 1 or iv > 50:
        return None
    return iv

df = apply_rule(df, "quantity", parse_quantity, "dropped_invalid_quantity")
df["quantity"] = df["quantity"].astype(int)

# ---------------- R8: discount_pct ----------------
summary["discount_pct_missing_set_to_zero"] = int(df["discount_pct"].isna().sum())

def parse_discount(s):
    if s is None:                      # missing means no discount
        return 0.0
    t = str(s).strip()
    if t.endswith("%"):
        t = t[:-1].strip()
    if not t:
        return None
    try:
        v = float(t)
    except ValueError:
        return None
    if not np.isfinite(v) or v < 0 or v > 100:
        return None
    return v

df = apply_rule(df, "discount_pct", parse_discount, "dropped_invalid_discount_pct")
df["discount_pct"] = df["discount_pct"].astype(float)

# ---------------- R9: customer_id ----------------
summary["customer_id_missing_filled"] = int(df["customer_id"].isna().sum())
df["customer_id"] = df["customer_id"].fillna("UNKNOWN").astype(str).str.upper()

# ---------------- R10: revenue ----------------
df["revenue"] = (df["quantity"] * df["unit_price"] * (1 - df["discount_pct"] / 100)).round(2)

# ---------------- R11: final columns, sort, write ----------------
FINAL_COLS = ["order_id", "order_date", "customer_id", "region", "product_category",
              "quantity", "unit_price", "discount_pct", "revenue"]
out = df[FINAL_COLS].copy()
out = out.sort_values("order_id", kind="mergesort").reset_index(drop=True)

out_path = os.path.join(OUTPUT_DIR, "cleaned.csv")
out.to_csv(out_path, index=False)
summary["cleaned_rows"] = int(len(out))

with open(os.path.join(OUTPUT_DIR, "cleaning_summary.json"), "w") as f:
    json.dump(summary, f, indent=2)
