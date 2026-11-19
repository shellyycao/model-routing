import os
import json
import re
import pandas as pd
import numpy as np

INPUT_DIR = os.environ["INPUT_DIR"]
OUTPUT_DIR = os.environ["OUTPUT_DIR"]

# ── R1: Read everything as text, strip whitespace, normalise missing values ──
raw = pd.read_csv(
    os.path.join(INPUT_DIR, "raw.csv"),
    dtype=str,
    keep_default_na=False,
)
raw_rows = len(raw)

# Strip whitespace from every cell
raw = raw.applymap(lambda x: x.strip() if isinstance(x, str) else x)

MISSING_SENTINELS = {"", "na", "n/a", "null", "none", "-"}

def to_missing(val):
    if isinstance(val, str) and val.strip().lower() in MISSING_SENTINELS:
        return np.nan
    return val

raw = raw.applymap(to_missing)

# ── R2: Remove duplicates by reading_id (keep first occurrence) ──
before_dedup = len(raw)
raw = raw.drop_duplicates(subset=["reading_id"], keep="first")
duplicates_removed = before_dedup - len(raw)

df = raw.copy()

# ── R3: Parse reading_date ──
DATE_FORMATS = [
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%d-%b-%Y",
    "%Y/%m/%d",
    "%B %d, %Y",
    "%B %d, %Y",  # handles 'Month D, YYYY' via pandas
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
before_meter = len(df)
df = df.dropna(subset=["meter_id"])
df["meter_id"] = df["meter_id"].str.upper()
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

before_building = len(df)
df["building_type"] = df["building_type"].apply(map_building)
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

before_tariff = len(df)
df["tariff"] = df["tariff"].apply(map_tariff)
df = df.dropna(subset=["tariff"])
tariff_dropped = before_tariff - len(df)

# ── R7: energy -> energy_kwh ──
def parse_energy(val):
    if pd.isna(val):
        return np.nan
    s = str(val).strip()
    # Remove thousands commas
    s = s.replace(",", "")
    # Check for MWh (case-insensitive, optional space)
    mwh_match = re.match(r'^([\d.]+)\s*MWh$', s, re.IGNORECASE)
    if mwh_match:
        try:
            return float(mwh_match.group(1)) * 1000
        except ValueError:
            return np.nan
    # Check for kWh (case-insensitive, optional space)
    kwh_match = re.match(r'^([\d.]+)\s*kWh$', s, re.IGNORECASE)
    if kwh_match:
        try:
            return float(kwh_match.group(1))
        except ValueError:
            return np.nan
    # No unit — plain number
    try:
        return float(s)
    except ValueError:
        return np.nan

before_energy = len(df)
df["energy_kwh"] = df["energy"].apply(parse_energy)
df = df.dropna(subset=["energy_kwh"])
df = df[(df["energy_kwh"] >= 0) & (df["energy_kwh"] <= 100000)]
energy_dropped = before_energy - len(df)
df["energy_kwh"] = df["energy_kwh"].round(2)

# ── R8: temperature -> temperature_c ──
def parse_temperature(val):
    if pd.isna(val):
        return np.nan
    s = str(val).strip()
    # Remove degree sign if present
    s_clean = s.replace("\u00b0", "").strip()  # remove °
    # Fahrenheit: ends with F (case-insensitive)
    if re.match(r'^-?[\d.]+\s*F$', s_clean, re.IGNORECASE):
        num_str = re.sub(r'[Ff]$', '', s_clean).strip()
        try:
            f_val = float(num_str)
            return round((f_val - 32) * 5 / 9, 1)
        except ValueError:
            return np.nan
    # Celsius: ends with C (case-insensitive) or no unit
    if re.match(r'^-?[\d.]+\s*C$', s_clean, re.IGNORECASE):
        num_str = re.sub(r'[Cc]$', '', s_clean).strip()
        try:
            return round(float(num_str), 1)
        except ValueError:
            return np.nan
    # No unit — treat as Celsius
    try:
        return round(float(s_clean), 1)
    except ValueError:
        return np.nan

df["temperature_c"] = df["temperature"].apply(parse_temperature)
# Out-of-range temperatures become missing (row kept)
df.loc[
    df["temperature_c"].notna() & ((df["temperature_c"] < -40) | (df["temperature_c"] > 50)),
    "temperature_c"
] = np.nan

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
    "meter_dropped": meter_dropped,
    "building_dropped": building_dropped,
    "tariff_dropped": tariff_dropped,
    "energy_dropped": energy_dropped,
    "total_dropped": raw_rows - cleaned_rows,
}

with open(os.path.join(OUTPUT_DIR, "cleaning_summary.json"), "w") as f:
    json.dump(summary, f, indent=2)

print(f"Cleaning complete: {raw_rows} raw rows -> {cleaned_rows} cleaned rows.")
