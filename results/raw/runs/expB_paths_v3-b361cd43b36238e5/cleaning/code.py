import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
from collections import Counter

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def is_missing(val):
    """Return True if a stripped string value should be considered missing."""
    if not isinstance(val, str):
        return False
    return val.strip().lower() in {"", "na", "n/a", "null", "none", "-"}

def clean_missing(df):
    """Replace defined missing markers with np.nan across the whole DataFrame."""
    for col in df.columns:
        df[col] = df[col].apply(lambda x: np.nan if is_missing(x) else x)
    return df

def parse_date(val):
    """Parse a date string using the allowed formats. Return a string YYYY-MM-DD or None."""
    if pd.isna(val):
        return None
    val = val.strip()
    formats = [
        "%Y-%m-%d",          # 2024-01-01
        "%m/%d/%Y",          # 01/31/2024
        "%d-%b-%Y",          # 05-Mar-2024
        "%Y/%m/%d",          # 2024/01/02
        "%B %d, %Y",         # January 5, 2024
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(val, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None

def map_building_type(val):
    if pd.isna(val):
        return None
    mapping = {
        "residential": "Residential",
        "commercial": "Commercial",
        "industrial": "Industrial",
        "res": "Residential",
        "resi": "Residential",
        "comm": "Commercial",
        "ind": "Industrial",
    }
    return mapping.get(val.strip().lower())

def map_tariff(val):
    if pd.isna(val):
        return None
    val_low = val.strip().lower().replace(" ", "")  # remove spaces for matching
    if val_low == "peak":
        return "peak"
    if val_low in {"offpeak", "off-peak"}:
        return "off-peak"
    return None

def clean_energy(val):
    """Convert raw energy string to float kWh. Return None on failure or out‑of‑range."""
    if pd.isna(val):
        return None
    s = str(val).replace(",", "").strip()
    # Detect unit
    lower = s.lower()
    multiplier = 1.0
    if lower.endswith("mwh"):
        multiplier = 1000.0
        num_part = s[:-3].strip()
    elif lower.endswith("kwh"):
        num_part = s[:-3].strip()
    else:
        num_part = s
    # Remove possible trailing space before unit already handled
    try:
        num = float(num_part)
    except ValueError:
        return None
    kwh = num * multiplier
    if kwh < 0 or kwh > 100000:
        return None
    return round(kwh, 2)

def clean_temperature(val):
    """Convert raw temperature to Celsius float. Return np.nan if invalid or out‑of‑range."""
    if pd.isna(val):
        return np.nan
    s = str(val).strip()
    # Remove degree symbol if present
    s = s.replace("°", "")
    # Identify unit (last character if alphabetic)
    if s[-1].isalpha():
        unit = s[-1].upper()
        num_part = s[:-1].strip()
    else:
        unit = "C"  # assume Celsius when no unit
        num_part = s
    try:
        num = float(num_part)
    except ValueError:
        return np.nan
    if unit == "F":
        c = (num - 32) * 5.0 / 9.0
    else:  # C or unknown treated as Celsius
        c = num
    if c < -40 or c > 50:
        return np.nan
    return round(c, 1)

# ---------------------------------------------------------------------------
# Main cleaning routine
# ---------------------------------------------------------------------------

def main():
    input_dir = os.getenv("INPUT_DIR")
    output_dir = os.getenv("OUTPUT_DIR")
    if not input_dir or not output_dir:
        raise RuntimeError("Both INPUT_DIR and OUTPUT_DIR environment variables must be set.")

    raw_path = os.path.join(input_dir, "raw.csv")
    df_raw = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    counters = Counter()
    counters["raw_rows"] = len(df_raw)

    # R1: strip whitespace and treat defined missing markers as NaN
    df = df_raw.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    df = clean_missing(df)

    # R2: deduplicate on reading_id (keep first)
    before_dup = len(df)
    df = df.drop_duplicates(subset="reading_id", keep="first")
    counters["duplicates_removed"] = before_dup - len(df)

    # R3: parse reading_date
    df["reading_date_parsed"] = df["reading_date"].apply(parse_date)
    df = df.dropna(subset=["reading_date_parsed"])
    counters["date_parse_failed"] = before_dup - len(df) - counters["duplicates_removed"]
    df = df.rename(columns={"reading_date_parsed": "reading_date"})

    # R4: meter_id uppercase, drop missing
    df["meter_id"] = df["meter_id"].apply(lambda x: x.upper() if pd.notna(x) else x)
    before_meter = len(df)
    df = df.dropna(subset=["meter_id"])
    counters["meter_missing"] = before_meter - len(df)

    # R5: building_type mapping
    df["building_type_mapped"] = df["building_type"].apply(map_building_type)
    before_bt = len(df)
    df = df.dropna(subset=["building_type_mapped"])
    counters["building_type_invalid"] = before_bt - len(df)
    df = df.rename(columns={"building_type_mapped": "building_type"})

    # R6: tariff mapping
    df["tariff_mapped"] = df["tariff"].apply(map_tariff)
    before_tariff = len(df)
    df = df.dropna(subset=["tariff_mapped"])
    counters["tariff_invalid"] = before_tariff - len(df)
    df = df.rename(columns={"tariff_mapped": "tariff"})

    # R7: energy conversion
    df["energy_kwh"] = df["energy"].apply(clean_energy)
    before_energy = len(df)
    df = df.dropna(subset=["energy_kwh"])
    counters["energy_invalid"] = before_energy - len(df)

    # R8: temperature conversion (keep row even if result is NaN)
    df["temperature_c"] = df["temperature"].apply(clean_temperature)

    # R9: select and order columns
    final_cols = ["reading_id", "reading_date", "meter_id", "building_type", "tariff", "energy_kwh", "temperature_c"]
    df_clean = df[final_cols].copy()
    # Ensure correct dtypes for output (pandas will handle conversion when writing)
    df_clean = df_clean.sort_values(by="reading_id", ascending=True)
    counters["cleaned_rows"] = len(df_clean)

    # Write cleaned CSV
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    df_clean.to_csv(cleaned_path, index=False, float_format='%.2f')

    # Write cleaning summary JSON
    summary = {
        "raw_rows": counters["raw_rows"],
        "cleaned_rows": counters["cleaned_rows"],
        "duplicates_removed": counters.get("duplicates_removed", 0),
        "date_parse_failed": counters.get("date_parse_failed", 0),
        "meter_missing": counters.get("meter_missing", 0),
        "building_type_invalid": counters.get("building_type_invalid", 0),
        "tariff_invalid": counters.get("tariff_invalid", 0),
        "energy_invalid": counters.get("energy_invalid", 0)
    }
    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    main()
