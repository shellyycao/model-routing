import os
import json
import re
from datetime import datetime
import pandas as pd
import numpy as np

# ---------- Helper functions ----------

def normalize_cell(value):
    """Strip whitespace and convert known missing markers to NaN."""
    if not isinstance(value, str):
        return np.nan
    v = value.strip()
    if v.lower() in {"", "na", "n/a", "null", "none", "-"}:
        return np.nan
    return v

def parse_date(date_str):
    """Try the allowed date formats, return ISO string or None."""
    if pd.isna(date_str):
        return None
    formats = [
        "%Y-%m-%d",          # 2024-01-01
        "%m/%d/%Y",          # 01/31/2024
        "%d-%b-%Y",          # 05-Mar-2024
        "%Y/%m/%d",          # 2024/01/02
        "%B %d, %Y",         # January 5, 2024
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None

def clean_energy(val):
    """Convert energy string to kWh float, applying MWh conversion if needed.
    Returns (value, valid_flag)."""
    if pd.isna(val):
        return (None, False)
    # remove commas and surrounding whitespace
    s = val.replace(",", "").strip()
    # regex to capture number and optional unit
    m = re.fullmatch(r"(?i)([0-9]*\.?[0-9]+)\s*(mwh|kwh)?", s)
    if not m:
        return (None, False)
    number = float(m.group(1))
    unit = m.group(2)
    if unit:
        unit = unit.lower()
    if unit == "mwh":
        number *= 1000.0
    # kWh or no unit stays as is
    if number < 0 or number > 100000:
        return (None, False)
    return (round(number, 2), True)

def clean_temperature(val):
    """Convert temperature to Celsius float (rounded to 1 decimal).
    Returns (value, is_missing_flag)."""
    if pd.isna(val):
        return (np.nan, True)
    s = val.strip()
    # capture number and optional unit (C, F, °C, °F)
    m = re.fullmatch(r"(?i)(-?[0-9]*\.?[0-9]+)\s*(°?\s*[cf])?", s)
    if not m:
        return (np.nan, True)
    number = float(m.group(1))
    unit = m.group(2)
    if unit:
        unit = unit.replace("°", "").replace(" ", "").lower()
    if unit == "f":
        number = (number - 32) * 5.0 / 9.0
    # if unit is C or missing, keep number as Celsius
    number = round(number, 1)
    if number < -40 or number > 50:
        return (np.nan, True)
    return (number, False)

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
    df = df_raw.applymap(normalize_cell)

    # R2: drop duplicate reading_id, keep first
    before_dup = len(df)
    df = df.drop_duplicates(subset=["reading_id"], keep="first")
    dup_removed = before_dup - len(df)

    # R3: parse reading_date
    df["reading_date_parsed"] = df["reading_date"].apply(parse_date)
    before_date = len(df)
    df = df.dropna(subset=["reading_date_parsed"])
    date_invalid = before_date - len(df)
    df = df.drop(columns=["reading_date"]).rename(columns={"reading_date_parsed": "reading_date"})

    # R4: meter_id upper case, drop missing
    df["meter_id"] = df["meter_id"].apply(lambda x: x.upper() if pd.notna(x) else x)
    before_meter = len(df)
    df = df.dropna(subset=["meter_id"])
    meter_missing = before_meter - len(df)

    # R5: building_type mapping
    building_map = {
        "res": "Residential",
        "resi": "Residential",
        "residential": "Residential",
        "comm": "Commercial",
        "commercial": "Commercial",
        "ind": "Industrial",
        "industrial": "Industrial",
    }
    def map_building(val):
        if pd.isna(val):
            return np.nan
        return building_map.get(val.lower())
    df["building_type"] = df["building_type"].apply(map_building)
    before_build = len(df)
    df = df.dropna(subset=["building_type"])
    building_invalid = before_build - len(df)

    # R6: tariff mapping
    tariff_map = {
        "peak": "peak",
        "off-peak": "off-peak",
        "offpeak": "off-peak",
        "off peak": "off-peak",
    }
    def map_tariff(val):
        if pd.isna(val):
            return np.nan
        return tariff_map.get(val.lower())
    df["tariff"] = df["tariff"].apply(map_tariff)
    before_tariff = len(df)
    df = df.dropna(subset=["tariff"])
    tariff_invalid = before_tariff - len(df)

    # R7: energy conversion
    def apply_energy(val):
        conv, ok = clean_energy(val)
        return conv if ok else np.nan
    df["energy_kwh"] = df["energy"].apply(apply_energy)
    before_energy = len(df)
    df = df.dropna(subset=["energy_kwh"])
    energy_invalid = before_energy - len(df)

    # R8: temperature conversion (keep row even if invalid)
    def apply_temp(val):
        conv, missing = clean_temperature(val)
        return conv if not missing else np.nan
    df["temperature_c"] = df["temperature"].apply(apply_temp)
    # No row removal for temperature

    # R9: final column selection, ordering and sorting
    final_cols = ["reading_id", "reading_date", "meter_id", "building_type", "tariff", "energy_kwh", "temperature_c"]
    df_clean = df[final_cols].copy()
    df_clean = df_clean.sort_values(by="reading_id", ascending=True)

    cleaned_rows = len(df_clean)

    # Write cleaned CSV
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    df_clean.to_csv(cleaned_path, index=False, float_format='%.2f')

    # Write cleaning summary JSON
    summary = {
        "raw_rows": raw_rows,
        "cleaned_rows": cleaned_rows,
        "duplicates_removed": dup_removed,
        "date_invalid": date_invalid,
        "meter_missing": meter_missing,
        "building_invalid": building_invalid,
        "tariff_invalid": tariff_invalid,
        "energy_invalid": energy_invalid,
        "temperature_missing_or_out_of_range": int(df["temperature_c"].isna().sum()),
    }
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    main()
