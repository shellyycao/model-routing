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
raw_df = raw_df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}

def to_missing(val):
    if isinstance(val, str) and val.strip().lower() in MISSING_TOKENS:
        return np.nan
    return val

raw_df = raw_df.applymap(to_missing)

# ── R2: Remove duplicates by reading_id (keep first occurrence) ──
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
    "%B %d, %Y",  # handles 'Month D, YYYY' (single-digit day)
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
    lambda x: x.upper() if isinstance(x, str) and not (isinstance(x, float) and np.isnan(x)) else x
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
            return float(m.group(1)) * 1000
        except ValueError:
            return np.nan
    # Check for kWh (case-insensitive)
    m = re.match(r'^([\d.]+)\s*kWh$', s, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            return np.nan
    # No unit – already kWh
    try:
        return float(s)
    except ValueError:
        return np.nan

df["energy_kwh"] = df["energy"].apply(parse_energy)
before_energy = len(df)
df = df.dropna(subset=["energy_kwh"])
df = df[(df["energy_kwh"] >= 0) & (df["energy_kwh"] <= 100000)]
energy_dropped = before_energy - len(df)
df["energy_kwh"] = df["energy_kwh"].round(2)

# ── R8: temperature -> temperature_c ──
def parse_temperature(val):
    if pd.isna(val):
        return np.nan
    s = str(val).strip()
    # Remove degree sign variations
    # Detect unit
    is_fahrenheit = False
    is_celsius = False

    # Check for Fahrenheit: ends with F or °F (case-insensitive)
    if re.search(r'[°\u00b0]?\s*[Ff]$', s):
        is_fahrenheit = True
        s = re.sub(r'[°\u00b0]?\s*[Ff]$', '', s).strip()
    # Check for Celsius: ends with C or °C (case-insensitive)
    elif re.search(r'[°\u00b0]?\s*[Cc]$', s):
        is_celsius = True
        s = re.sub(r'[°\u00b0]?\s*[Cc]$', '', s).strip()
    else:
        # No unit – treat as Celsius
        is_celsius = True
        # Remove any trailing degree sign
        s = re.sub(r'[°\u00b0]$', '', s).strip()

    try:
        num = float(s)
    except ValueError:
        return np.nan

    if is_fahrenheit:
        num = (num - 32) * 5 / 9

    num = round(num, 1)

    if num < -40 or num > 50:
        return np.nan

    return num

df["temperature_c"] = df["temperature"].apply(parse_temperature)
# Rows with bad temperature are KEPT (temperature_c set to NaN/empty)

# ── R9: Select and order columns, sort by reading_id ──
df = df[["reading_id", "reading_date", "meter_id", "building_type", "tariff", "energy_kwh", "temperature_c"]]
df = df.sort_values("reading_id", ascending=True)

cleaned_rows = len(df)

# Write cleaned CSV
df.to_csv(
    os.path.join(OUTPUT_DIR, "cleaned.csv"),
    index=False,
    na_rep="",
)

# Write cleaning summary
summary = {
    "raw_rows": raw_rows,
    "cleaned_rows": cleaned_rows,
    "duplicates_removed": duplicates_removed,
    "date_dropped": date_dropped,
    "meter_id_dropped": meter_dropped,
    "building_type_dropped": building_dropped,
    "tariff_dropped": tariff_dropped,
    "energy_dropped": energy_dropped,
    "temperature_set_missing": int(df["temperature_c"].isna().sum()),
}

with open(os.path.join(OUTPUT_DIR, "cleaning_summary.json"), "w") as f:
    json.dump(summary, f, indent=2)

print(f"Cleaning complete: {raw_rows} raw rows -> {cleaned_rows} cleaned rows.")
