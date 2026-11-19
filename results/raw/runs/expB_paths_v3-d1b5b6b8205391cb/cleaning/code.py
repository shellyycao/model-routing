import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
import re

# ---------- Helper functions ----------

def is_missing(val):
    """Return True if the stripped string value should be considered missing."""
    if not isinstance(val, str):
        return True
    v = val.strip().lower()
    return v in {"", "na", "n/a", "null", "none", "-"}

def clean_missing(df):
    """Replace defined missing markers with np.nan across the whole DataFrame."""
    return df.applymap(lambda x: np.nan if is_missing(x) else x)

def parse_date(val):
    """Parse a date string using the allowed formats. Return ISO string or None."""
    if pd.isna(val):
        return None
    s = val.strip()
    formats = [
        "%Y-%m-%d",          # 2024-01-01
        "%m/%d/%Y",          # 01/31/2024
        "%d-%b-%Y",          # 05-Mar-2024 (abbr month)
        "%Y/%m/%d",          # 2024/01/02
        "%B %d, %Y",         # January 5, 2024 (full month name)
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None

def map_building_type(val):
    if pd.isna(val):
        return None
    v = val.strip().lower()
    mapping = {
        "res": "Residential",
        "resi": "Residential",
        "residential": "Residential",
        "comm": "Commercial",
        "commercial": "Commercial",
        "ind": "Industrial",
        "industrial": "Industrial",
    }
    return mapping.get(v)

def map_tariff(val):
    if pd.isna(val):
        return None
    v = val.strip().lower().replace(" ", "")  # remove spaces for matching
    if v == "peak":
        return "peak"
    if v in {"offpeak", "off-peak"}:
        return "off-peak"
    return None

energy_regex = re.compile(r"^\s*([\d,\.]+)\s*(MWh|kWh)?\s*$", re.IGNORECASE)

def convert_energy(val):
    if pd.isna(val):
        return None
    s = str(val).replace(",", "").strip()
    m = energy_regex.match(s)
    if not m:
        return None
    number_str, unit = m.groups()
    try:
        number = float(number_str)
    except ValueError:
        return None
    if unit:
        unit = unit.lower()
        if unit == "mwh":
            number *= 1000.0
        # kWh stays the same
    # Validate range
    if number < 0 or number > 100000:
        return None
    return round(number, 2)

temp_regex = re.compile(r"^\s*([-+]?\d*\.?\d+)\s*(°?([CFcf]))?\s*$")

def convert_temperature(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    m = temp_regex.match(s)
    if not m:
        return None
    number_str, _, unit = m.groups()
    try:
        number = float(number_str)
    except ValueError:
        return None
    if unit:
        unit = unit.upper()
        if unit == "F":
            # Fahrenheit to Celsius
            number = (number - 32) * 5.0 / 9.0
    # else assume Celsius already
    number = round(number, 1)
    if number < -40 or number > 50:
        return None
    return number

# ---------- Main cleaning routine ----------

def main():
    input_dir = os.getenv("INPUT_DIR")
    output_dir = os.getenv("OUTPUT_DIR")
    if not input_dir or not output_dir:
        raise RuntimeError("INPUT_DIR and OUTPUT_DIR environment variables must be set")

    raw_path = os.path.join(input_dir, "raw.csv")
    df_raw = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    raw_rows = len(df_raw)

    # R1: strip whitespace and normalise missing values
    df = df_raw.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    df = clean_missing(df)

    # R2: deduplicate on reading_id (keep first)
    before_dup = len(df)
    df = df.drop_duplicates(subset="reading_id", keep="first")
    dup_removed = before_dup - len(df)

    # Prepare counters for summary
    dropped_date = 0
    dropped_meter = 0
    dropped_building = 0
    dropped_tariff = 0
    dropped_energy = 0
    temp_invalid = 0
    dropped_missing_id = 0

    # Ensure reading_id is present (schema requires non‑null)
    df = df[~df["reading_id"].isna()]
    dropped_missing_id = before_dup - dup_removed - len(df)

    # R3: reading_date parsing
    df["reading_date_parsed"] = df["reading_date"].apply(parse_date)
    mask_date = df["reading_date_parsed"].notna()
    dropped_date = len(df) - mask_date.sum()
    df = df[mask_date]

    # R4: meter_id upper case
    df["meter_id"] = df["meter_id"].str.upper()
    mask_meter = df["meter_id"].notna()
    dropped_meter = len(df) - mask_meter.sum()
    df = df[mask_meter]

    # R5: building_type mapping
    df["building_type_mapped"] = df["building_type"].apply(map_building_type)
    mask_building = df["building_type_mapped"].notna()
    dropped_building = len(df) - mask_building.sum()
    df = df[mask_building]

    # R6: tariff mapping
    df["tariff_mapped"] = df["tariff"].apply(map_tariff)
    mask_tariff = df["tariff_mapped"].notna()
    dropped_tariff = len(df) - mask_tariff.sum()
    df = df[mask_tariff]

    # R7: energy conversion
    df["energy_kwh"] = df["energy"].apply(convert_energy)
    mask_energy = df["energy_kwh"].notna()
    dropped_energy = len(df) - mask_energy.sum()
    df = df[mask_energy]

    # R8: temperature conversion (keep row even if invalid)
    df["temperature_c"] = df["temperature"].apply(convert_temperature)
    temp_invalid = df["temperature_c"].isna().sum()
    # No row removal for temperature

    # Final column selection and ordering
    df_clean = df[[
        "reading_id",
        "reading_date_parsed",
        "meter_id",
        "building_type_mapped",
        "tariff_mapped",
        "energy_kwh",
        "temperature_c",
    ]].copy()
    df_clean.rename(columns={
        "reading_date_parsed": "reading_date",
        "building_type_mapped": "building_type",
        "tariff_mapped": "tariff",
    }, inplace=True)

    # Sort by reading_id ascending (string sort)
    df_clean.sort_values(by="reading_id", inplace=True)

    cleaned_rows = len(df_clean)

    # Write cleaned CSV
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    df_clean.to_csv(cleaned_path, index=False, float_format='%.2f')

    # Write cleaning summary JSON
    summary = {
        "raw_rows": raw_rows,
        "cleaned_rows": cleaned_rows,
        "duplicate_rows_removed": dup_removed,
        "rows_dropped_missing_reading_id": dropped_missing_id,
        "rows_dropped_reading_date": dropped_date,
        "rows_dropped_meter_id": dropped_meter,
        "rows_dropped_building_type": dropped_building,
        "rows_dropped_tariff": dropped_tariff,
        "rows_dropped_energy": dropped_energy,
        "rows_with_invalid_temperature": temp_invalid,
    }
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    main()
