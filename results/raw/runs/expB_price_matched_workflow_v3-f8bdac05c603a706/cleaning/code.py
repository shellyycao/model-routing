"""Cleaning stage for the energy_consumption project (prompt v3).

Reads raw.csv from INPUT_DIR, applies cleaning rules R1-R9 in order and writes
cleaned.csv plus cleaning_summary.json to OUTPUT_DIR.
"""

import json
import math
import os
import re
from datetime import datetime

import numpy as np
import pandas as pd

MISSING_TOKENS = ["", "na", "n/a", "null", "none", "-"]

DATE_FORMATS = [
    "%Y-%m-%d",   # YYYY-MM-DD
    "%m/%d/%Y",   # MM/DD/YYYY (month first)
    "%d-%b-%Y",   # DD-Mon-YYYY, English 3-letter month abbreviation
    "%Y/%m/%d",   # YYYY/MM/DD
    "%B %d, %Y",  # Month D, YYYY, full English month name
]

BUILDING_TYPE_MAP = {
    "residential": "Residential",
    "res": "Residential",
    "resi": "Residential",
    "commercial": "Commercial",
    "comm": "Commercial",
    "industrial": "Industrial",
    "ind": "Industrial",
}

TARIFF_MAP = {
    "peak": "peak",
    "off-peak": "off-peak",
    "offpeak": "off-peak",
    "off peak": "off-peak",
}

ENERGY_UNIT_RE = re.compile(r"^(.*?)\s*(mwh|kwh)\s*$", re.IGNORECASE)
TEMP_UNIT_RE = re.compile(r"^(.*?)\s*\u00b0?\s*([fc])$", re.IGNORECASE)
TRAILING_DEGREE_RE = re.compile(r"\s*\u00b0\s*$")


def parse_reading_date(value):
    """Parse with exactly the allowed formats; return a date or None."""
    if pd.isna(value):
        return None
    text = str(value)
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def parse_energy(value):
    """Return energy in kWh rounded to 2 decimals, or NaN if the row must be dropped."""
    if pd.isna(value):
        return np.nan
    text = str(value).replace(",", "")
    multiplier = 1.0
    match = ENERGY_UNIT_RE.match(text)
    if match:
        number_text = match.group(1)
        if match.group(2).lower() == "mwh":
            multiplier = 1000.0
    else:
        number_text = text
    number_text = number_text.strip()
    if not number_text:
        return np.nan
    try:
        number = float(number_text)
    except ValueError:
        return np.nan
    if not math.isfinite(number):
        return np.nan
    number *= multiplier
    if number < 0 or number > 100000:
        return np.nan
    return round(number, 2)


def parse_temperature(value):
    """Return temperature in Celsius rounded to 1 decimal, or NaN (row is kept)."""
    if pd.isna(value):
        return np.nan
    text = str(value)
    unit = "C"
    match = TEMP_UNIT_RE.match(text)
    if match:
        number_text = match.group(1)
        unit = match.group(2).upper()
    else:
        number_text = TRAILING_DEGREE_RE.sub("", text)
    number_text = number_text.strip()
    if not number_text:
        return np.nan
    try:
        number = float(number_text)
    except ValueError:
        return np.nan
    if not math.isfinite(number):
        return np.nan
    if unit == "F":
        number = (number - 32.0) * 5.0 / 9.0
    number = round(number, 1)
    if number < -40 or number > 50:
        return np.nan
    return number


def main():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    os.makedirs(output_dir, exist_ok=True)

    raw_path = os.path.join(input_dir, "raw.csv")
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    summary_path = os.path.join(output_dir, "cleaning_summary.json")

    # R1: read every column as text, strip whitespace, normalise missing tokens.
    df = pd.read_csv(raw_path, dtype=str, na_filter=False, encoding="utf-8-sig")
    raw_rows = int(len(df))
    for col in df.columns:
        df[col] = df[col].str.strip()
    lowered = df.apply(lambda s: s.str.lower())
    df = df.mask(lowered.isin(MISSING_TOKENS))

    # R2: remove duplicate reading_id rows first, keeping the first raw-file occurrence.
    id_present = df["reading_id"].notna()
    dup_mask = id_present & df.duplicated(subset=["reading_id"], keep="first")
    duplicates_removed = int(dup_mask.sum())
    df = df.loc[~dup_mask].copy()
    missing_id_mask = df["reading_id"].isna()
    dropped_missing_reading_id = int(missing_id_mask.sum())
    df = df.loc[~missing_id_mask].copy()

    # R3: parse reading_date with the allowed formats; drop unparseable rows.
    parsed_dates = df["reading_date"].map(parse_reading_date)
    bad_date_mask = parsed_dates.isna()
    dropped_invalid_reading_date = int(bad_date_mask.sum())
    df = df.loc[~bad_date_mask].copy()
    df["reading_date"] = parsed_dates.loc[~bad_date_mask].map(
        lambda d: d.strftime("%Y-%m-%d")
    )

    # R4: uppercase meter_id; drop rows with missing meter_id.
    missing_meter_mask = df["meter_id"].isna()
    dropped_missing_meter_id = int(missing_meter_mask.sum())
    df = df.loc[~missing_meter_mask].copy()
    df["meter_id"] = df["meter_id"].str.upper()

    # R5: canonicalise building_type; drop unmappable/missing values.
    mapped_building = df["building_type"].str.lower().map(BUILDING_TYPE_MAP)
    bad_building_mask = mapped_building.isna()
    dropped_invalid_building_type = int(bad_building_mask.sum())
    df = df.loc[~bad_building_mask].copy()
    df["building_type"] = mapped_building.loc[~bad_building_mask]

    # R6: canonicalise tariff; drop unmappable/missing values.
    mapped_tariff = df["tariff"].str.lower().map(TARIFF_MAP)
    bad_tariff_mask = mapped_tariff.isna()
    dropped_invalid_tariff = int(bad_tariff_mask.sum())
    df = df.loc[~bad_tariff_mask].copy()
    df["tariff"] = mapped_tariff.loc[~bad_tariff_mask]

    # R7: convert energy to energy_kwh; drop missing/non-numeric/out-of-range values.
    energy_kwh = df["energy"].map(parse_energy).astype(float)
    bad_energy_mask = energy_kwh.isna()
    dropped_invalid_energy = int(bad_energy_mask.sum())
    df = df.loc[~bad_energy_mask].copy()
    df["energy_kwh"] = energy_kwh.loc[~bad_energy_mask]

    # R8: convert temperature to Celsius; invalid/out-of-range becomes missing, row kept.
    df["temperature_c"] = df["temperature"].map(parse_temperature).astype(float)
    temperature_missing = int(df["temperature_c"].isna().sum())

    # R9: select/order columns, sort by reading_id ascending, write CSV.
    out = df[
        [
            "reading_id",
            "reading_date",
            "meter_id",
            "building_type",
            "tariff",
            "energy_kwh",
            "temperature_c",
        ]
    ].sort_values("reading_id", kind="mergesort").reset_index(drop=True)
    out.to_csv(cleaned_path, index=False, na_rep="")

    summary = {
        "raw_rows": raw_rows,
        "duplicates_removed": duplicates_removed,
        "dropped_missing_reading_id": dropped_missing_reading_id,
        "dropped_invalid_reading_date": dropped_invalid_reading_date,
        "dropped_missing_meter_id": dropped_missing_meter_id,
        "dropped_invalid_building_type": dropped_invalid_building_type,
        "dropped_invalid_tariff": dropped_invalid_tariff,
        "dropped_invalid_energy": dropped_invalid_energy,
        "temperature_missing": temperature_missing,
        "cleaned_rows": int(len(out)),
    }
    with open(summary_path, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)


if __name__ == "__main__":
    main()
