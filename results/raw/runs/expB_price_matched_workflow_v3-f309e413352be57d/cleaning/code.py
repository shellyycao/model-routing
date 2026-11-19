import os
import json
import re
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

# Strip whitespace from every cell
raw_df = raw_df.apply(lambda col: col.str.strip())

MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}

def to_missing(val):
    if isinstance(val, str) and val.strip().lower() in MISSING_TOKENS:
        return np.nan
    return val

raw_df = raw_df.applymap(to_missing)

# ── R2: Remove duplicates on reading_id (keep first) ──
before_dedup = len(raw_df)
raw_df = raw_df.drop_duplicates(subset=["reading_id"], keep="first")
duplicates_removed = before_dedup - len(raw_df)

df = raw_df.copy()

# ── R3: Parse reading_date ──
DATE_FORMATS = [
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%d-%b-%Y",
    "%Y/%m/%d",
    "%B %d, %Y",
    "%B %d, %Y",  # kept for safety
]

def parse_date(val):
    if pd.isna(val):
        return pd.NaT
    val = str(val).strip()
    for fmt in DATE_FORMATS:
        try:
            return pd.to_datetime(val, format=fmt)
        except (ValueError, TypeError):
            continue
    return pd.NaT

df["reading_date"] = df["reading_date"].apply(parse_date)
before_date = len(df)
df = df.dropna(subset=["reading_date"])
date_dropped = before_date - len(df)
df["reading_date"] = df["reading_date"].dt.strftime("%Y-%m-%d")

# ── R4: meter_id upper-case, drop missing ──
df["meter_id"] = df["meter_id"].apply(
    lambda x: str(x).upper() if pd.notna(x) else np.nan
)
before_meter = len(df)
df = df.dropna(subset=["meter_id"])
meter_dropped = before_meter - len(df)

# ── R5: building_type mapping ──
BUILDING_MAP = {
    "residential": "Residential",
    "res": "Residential",
    "resi": "Residential",
    "commercial": "Commercial",
    "comm": "Commercial",
    "industrial": "Industrial",
    "ind": "Industrial",
}

def map_building(val):
    if pd.isna(val):
        return np.nan
    return BUILDING_MAP.get(str(val).strip().lower(), np.nan)

df["building_type"] = df["building_type"].apply(map_building)
before_building = len(df)
df = df.dropna(subset=["building_type"])
building_dropped = before_building - len(df)

# ── R6: tariff mapping ──
TARIFF_MAP = {
    "peak": "peak",
    "off-peak": "off-peak",
    "offpeak": "off-peak",
    "off peak": "off-peak",
}

def map_tariff(val):
    if pd.isna(val):
        return np.nan
    return TARIFF_MAP.get(str(val).strip().lower(), np.nan)

df["tariff"] = df["tariff"].apply(map_tariff)
before_tariff = len(df)
df = df.dropna(subset=["tariff"])
tariff_dropped = before_tariff - len(df)

# ── R7: energy -> energy_kwh ──
def parse_energy(val):
    if pd.isna(val):
        return np.nan
    s = str(val).strip().replace(",", "")
    # Check for MWh (case-insensitive, optional space)
    m = re.match(r'^([\d.]+)\s*MWh$', s, re.IGNORECASE)
    if m:
        try:
            return round(float(m.group(1)) * 1000, 2)
        except ValueError:
            return np.nan
    # Check for kWh (case-insensitive, optional space)
    m = re.match(r'^([\d.]+)\s*kWh$', s, re.IGNORECASE)
    if m:
        try:
            return round(float(m.group(1)), 2)
        except ValueError:
            return np.nan
    # No unit – already kWh
    try:
        return round(float(s), 2)
    except ValueError:
        return np.nan

df["energy_kwh"] = df["energy"].apply(parse_energy)
before_energy = len(df)
df = df.dropna(subset=["energy_kwh"])
df = df[(df["energy_kwh"] >= 0) & (df["energy_kwh"] <= 100000)]
energy_dropped = before_energy - len(df)

# ── R8: temperature -> temperature_c ──
def parse_temperature(val):
    if pd.isna(val):
        return np.nan
    s = str(val).strip()
    # Remove degree sign variations
    # Check for Fahrenheit: ends with F or °F
    m = re.match(r'^([\-\d.]+)\s*°?\s*[Ff]$', s)
    if m:
        try:
            f_val = float(m.group(1))
            c_val = (f_val - 32) * 5 / 9
            return round(c_val, 1)
        except ValueError:
            return np.nan
    # Check for Celsius: ends with C or °C
    m = re.match(r'^([\-\d.]+)\s*°?\s*[Cc]$', s)
    if m:
        try:
            return round(float(m.group(1)), 1)
        except ValueError:
            return np.nan
    # No unit – already Celsius
    # Strip any stray degree sign
    s_clean = s.replace('°', '').strip()
    try:
        return round(float(s_clean), 1)
    except ValueError:
        return np.nan

df["temperature_c"] = df["temperature"].apply(parse_temperature)
# Out-of-range temperatures -> missing (keep row)
df.loc[
    df["temperature_c"].notna() &
    ((df["temperature_c"] < -40) | (df["temperature_c"] > 50)),
    "temperature_c"
] = np.nan

# ── R9: Select and order columns, sort by reading_id ──
df = df[["reading_id", "reading_date", "meter_id", "building_type",
         "tariff", "energy_kwh", "temperature_c"]]

# Sort by reading_id ascending (lexicographic is fine for zero-padded IDs)
df = df.sort_values("reading_id", ascending=True).reset_index(drop=True)

cleaned_rows = len(df)

# Write cleaned CSV
df.to_csv(
    os.path.join(OUTPUT_DIR, "cleaned.csv"),
    index=False,
    float_format="%.10g",  # avoids trailing zeros but keeps precision
)

# ── Write cleaning_summary.json ──
summary = {
    "raw_rows": raw_rows,
    "cleaned_rows": cleaned_rows,
    "duplicates_removed": duplicates_removed,
    "rows_dropped_bad_date": date_dropped,
    "rows_dropped_missing_meter_id": meter_dropped,
    "rows_dropped_bad_building_type": building_dropped,
    "rows_dropped_bad_tariff": tariff_dropped,
    "rows_dropped_bad_energy": energy_dropped,
    "total_rows_dropped": raw_rows - cleaned_rows,
}

with open(os.path.join(OUTPUT_DIR, "cleaning_summary.json"), "w") as f:
    json.dump(summary, f, indent=2)

print(f"Cleaning complete: {raw_rows} raw rows -> {cleaned_rows} cleaned rows.")
