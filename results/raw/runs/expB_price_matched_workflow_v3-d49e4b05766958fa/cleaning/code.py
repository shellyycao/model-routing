#!/usr/bin/env python3
"""Cleaning stage for the energy_consumption project.

Reads raw.csv from INPUT_DIR, applies cleaning rules R1-R9 and writes
cleaned.csv and cleaning_summary.json to OUTPUT_DIR.
"""

import json
import math
import os
from datetime import datetime

import numpy as np
import pandas as pd

# R1: tokens treated as missing (compared case-insensitively after stripping).
MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}

# R3: exactly these date formats are accepted.
DATE_FORMATS = [
    "%Y-%m-%d",   # 2024-01-05
    "%m/%d/%Y",   # 01/05/2024 (month first)
    "%d-%b-%Y",   # 05-Jan-2024
    "%Y/%m/%d",   # 2024/01/05
    "%B %d, %Y",  # January 5, 2024
]

# R5: building_type mapping (keys are lower case).
BUILDING_TYPE_MAP = {
    "residential": "Residential",
    "res": "Residential",
    "resi": "Residential",
    "commercial": "Commercial",
    "comm": "Commercial",
    "industrial": "Industrial",
    "ind": "Industrial",
}

# R6: tariff mapping (keys are lower case).
TARIFF_MAP = {
    "peak": "peak",
    "off-peak": "off-peak",
    "offpeak": "off-peak",
    "off peak": "off-peak",
}

OUTPUT_COLUMNS = [
    "reading_id",
    "reading_date",
    "meter_id",
    "building_type",
    "tariff",
    "energy_kwh",
    "temperature_c",
]

DEGREE_SIGN = "\u00b0"


def normalize_text(value):
    """R1: strip whitespace and normalise missing tokens to NA."""
    if value is None:
        return pd.NA
    text = str(value).strip()
    if text.lower() in MISSING_TOKENS:
        return pd.NA
    return text


def parse_reading_date(value):
    """R3: parse a date using exactly one of the allowed formats."""
    if pd.isna(value):
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def parse_energy(value):
    """R7: return (energy_kwh or None, reason)."""
    if pd.isna(value):
        return None, "energy_missing"
    text = value.replace(",", "").strip()
    multiplier = 1.0
    lowered = text.lower()
    if lowered.endswith("mwh"):
        multiplier = 1000.0
        text = text[:-3]
    elif lowered.endswith("kwh"):
        text = text[:-3]
    text = text.strip()
    try:
        number = float(text)
    except (TypeError, ValueError):
        return None, "energy_not_a_number"
    if not math.isfinite(number):
        return None, "energy_not_a_number"
    number *= multiplier
    if number < 0 or number > 100000:
        return None, "energy_out_of_range"
    return round(number, 2), "ok"


def parse_temperature(value):
    """R8: return (temperature_c or NaN, reason). The row is always kept."""
    if pd.isna(value):
        return np.nan, "temperature_missing"
    text = value.strip()
    lowered = text.lower()
    is_fahrenheit = False
    if lowered.endswith("f"):
        is_fahrenheit = True
        text = text[:-1]
    elif lowered.endswith("c"):
        text = text[:-1]
    text = text.rstrip()
    if text.endswith(DEGREE_SIGN):
        text = text[:-1].rstrip()
    try:
        number = float(text)
    except (TypeError, ValueError):
        return np.nan, "temperature_not_a_number"
    if not math.isfinite(number):
        return np.nan, "temperature_not_a_number"
    if is_fahrenheit:
        number = (number - 32.0) * 5.0 / 9.0
    if number < -40.0 or number > 50.0:
        return np.nan, "temperature_out_of_range"
    return round(number, 1), "ok"


def main():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    os.makedirs(output_dir, exist_ok=True)

    raw_path = os.path.join(input_dir, "raw.csv")
    # R1: read every column as text; do not let pandas coerce anything.
    df = pd.read_csv(
        raw_path,
        dtype=str,
        keep_default_na=False,
        na_filter=False,
        encoding="utf-8-sig",
    )
    df.columns = [str(c).strip() for c in df.columns]

    summary = {"raw_rows": int(len(df))}

    for column in df.columns:
        df[column] = df[column].map(normalize_text)

    # reading_id is required by the output schema; rows without one cannot be used.
    summary["dropped_missing_reading_id"] = int(df["reading_id"].isna().sum())
    df = df[df["reading_id"].notna()]

    # R2: drop duplicate reading_id values BEFORE any other row filter,
    # keeping the first occurrence in raw-file order.
    before = len(df)
    df = df.drop_duplicates(subset="reading_id", keep="first")
    summary["duplicates_removed_reading_id"] = int(before - len(df))

    # R3: reading_date.
    parsed_dates = df["reading_date"].map(parse_reading_date)
    valid = parsed_dates.notna()
    summary["dropped_invalid_reading_date"] = int((~valid).sum())
    df = df[valid].copy()
    df["reading_date"] = [d.strftime("%Y-%m-%d") for d in parsed_dates[valid]]

    # R4: meter_id.
    valid = df["meter_id"].notna()
    summary["dropped_missing_meter_id"] = int((~valid).sum())
    df = df[valid].copy()
    df["meter_id"] = df["meter_id"].str.upper()

    # R5: building_type.
    mapped = df["building_type"].map(
        lambda v: BUILDING_TYPE_MAP.get(v.lower()) if pd.notna(v) else None
    )
    valid = mapped.notna()
    summary["dropped_invalid_building_type"] = int((~valid).sum())
    df = df[valid].copy()
    df["building_type"] = mapped[valid].values

    # R6: tariff.
    mapped = df["tariff"].map(
        lambda v: TARIFF_MAP.get(v.lower()) if pd.notna(v) else None
    )
    valid = mapped.notna()
    summary["dropped_invalid_tariff"] = int((~valid).sum())
    df = df[valid].copy()
    df["tariff"] = mapped[valid].values

    # R7: energy -> energy_kwh.
    parsed = df["energy"].map(parse_energy)
    energy_values = parsed.map(lambda p: p[0])
    energy_reasons = parsed.map(lambda p: p[1])
    valid = energy_values.notna()
    summary["dropped_energy_missing"] = int((energy_reasons == "energy_missing").sum())
    summary["dropped_energy_not_a_number"] = int((energy_reasons == "energy_not_a_number").sum())
    summary["dropped_energy_out_of_range"] = int((energy_reasons == "energy_out_of_range").sum())
    df = df[valid].copy()
    df["energy_kwh"] = energy_values[valid].astype(float).values

    # R8: temperature -> temperature_c (invalid values become empty; rows kept).
    parsed = df["temperature"].map(parse_temperature)
    df["temperature_c"] = parsed.map(lambda p: p[0]).astype(float)
    temp_reasons = parsed.map(lambda p: p[1])
    summary["temperature_missing_set_empty"] = int((temp_reasons == "temperature_missing").sum())
    summary["temperature_not_a_number_set_empty"] = int((temp_reasons == "temperature_not_a_number").sum())
    summary["temperature_out_of_range_set_empty"] = int((temp_reasons == "temperature_out_of_range").sum())

    # R9: select columns, sort by reading_id ascending, write CSV.
    out = df[OUTPUT_COLUMNS].sort_values("reading_id", ascending=True)
    summary["cleaned_rows"] = int(len(out))

    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    out.to_csv(cleaned_path, index=False, na_rep="")

    summary_path = os.path.join(output_dir, "cleaning_summary.json")
    with open(summary_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
