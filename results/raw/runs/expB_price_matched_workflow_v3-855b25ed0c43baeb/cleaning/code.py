import json
import os
import re
from datetime import datetime

import numpy as np
import pandas as pd

INPUT_DIR = os.environ["INPUT_DIR"]
OUTPUT_DIR = os.environ["OUTPUT_DIR"]

MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}

DATE_FORMATS = [
    "%Y-%m-%d",   # YYYY-MM-DD
    "%m/%d/%Y",   # MM/DD/YYYY (month first)
    "%d-%b-%Y",   # DD-Mon-YYYY (e.g. 05-Mar-2024)
    "%Y/%m/%d",   # YYYY/MM/DD
    "%B %d, %Y",  # Month D, YYYY (e.g. March 5, 2024)
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

ENERGY_RE = re.compile(
    r"^([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s*(mwh|kwh)?$",
    re.IGNORECASE,
)

TEMP_RE = re.compile(
    r"^([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s*°?\s*([fc])?$",
    re.IGNORECASE,
)


def parse_reading_date(value):
    if not isinstance(value, str):
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def parse_energy(value):
    """Return energy in kWh, or None if missing/invalid/out of range."""
    if not isinstance(value, str):
        return None
    text = value.replace(",", "").strip()
    match = ENERGY_RE.match(text)
    if match is None:
        return None
    number = float(match.group(1))
    if (match.group(2) or "").lower() == "mwh":
        number *= 1000.0
    if number < 0 or number > 100000:
        return None
    return round(number, 2)


def parse_temperature(value):
    """Return temperature in Celsius, or NaN if missing/invalid/out of range."""
    if not isinstance(value, str):
        return np.nan
    match = TEMP_RE.match(value)
    if match is None:
        return np.nan
    number = float(match.group(1))
    unit = match.group(2)
    if unit is not None and unit.lower() == "f":
        number = (number - 32.0) * 5.0 / 9.0
    if number < -40 or number > 50:
        return np.nan
    return round(number, 1)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # R1: read every column as text; strip whitespace; normalize missing tokens.
    raw_path = os.path.join(INPUT_DIR, "raw.csv")
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False, na_filter=False,
                     encoding="utf-8-sig")
    raw_rows = int(len(df))
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].map(lambda v: np.nan if v.lower() in MISSING_TOKENS else v)

    # R2: drop duplicate reading_id rows first, keeping the first raw-file occurrence.
    dropped_missing_reading_id = int(df["reading_id"].isna().sum())
    df = df[df["reading_id"].notna()].copy()
    before = len(df)
    df = df.drop_duplicates(subset="reading_id", keep="first").copy()
    duplicates_removed = int(before - len(df))

    # R3: reading_date -> YYYY-MM-DD; drop missing/unparseable.
    parsed = df["reading_date"].map(parse_reading_date)
    mask = parsed.notna()
    dropped_reading_date = int((~mask).sum())
    df = df[mask].copy()
    df["reading_date"] = parsed[mask]

    # R4: meter_id upper case; drop missing.
    mask = df["meter_id"].notna()
    dropped_meter_id = int((~mask).sum())
    df = df[mask].copy()
    df["meter_id"] = df["meter_id"].str.upper()

    # R5: building_type canonical mapping; drop missing/unmapped.
    mapped = df["building_type"].map(
        lambda v: BUILDING_TYPE_MAP.get(v.lower()) if isinstance(v, str) else None)
    mask = mapped.notna()
    dropped_building_type = int((~mask).sum())
    df = df[mask].copy()
    df["building_type"] = mapped[mask]

    # R6: tariff canonical mapping; drop missing/unmapped.
    mapped = df["tariff"].map(
        lambda v: TARIFF_MAP.get(v.lower()) if isinstance(v, str) else None)
    mask = mapped.notna()
    dropped_tariff = int((~mask).sum())
    df = df[mask].copy()
    df["tariff"] = mapped[mask]

    # R7: energy -> energy_kwh (kWh/MWh units, thousands separators, range 0..100000).
    parsed_energy = df["energy"].map(parse_energy)
    mask = parsed_energy.notna()
    dropped_energy = int((~mask).sum())
    df = df[mask].copy()
    df["energy_kwh"] = parsed_energy[mask].astype(float)

    # R8: temperature -> temperature_c; invalid/out-of-range becomes empty, row kept.
    df["temperature_c"] = df["temperature"].map(parse_temperature).astype(float)
    temperature_c_missing = int(df["temperature_c"].isna().sum())

    # R9: final column set/order, sort by reading_id ascending, write CSV.
    columns = ["reading_id", "reading_date", "meter_id", "building_type",
               "tariff", "energy_kwh", "temperature_c"]
    out = df[columns].sort_values("reading_id", kind="stable")
    out.to_csv(os.path.join(OUTPUT_DIR, "cleaned.csv"), index=False)

    summary = {
        "raw_rows": raw_rows,
        "cleaned_rows": int(len(out)),
        "duplicates_removed": duplicates_removed,
        "dropped_missing_reading_id": dropped_missing_reading_id,
        "dropped_reading_date_unparseable": dropped_reading_date,
        "dropped_meter_id_missing": dropped_meter_id,
        "dropped_building_type_invalid": dropped_building_type,
        "dropped_tariff_invalid": dropped_tariff,
        "dropped_energy_invalid": dropped_energy,
        "temperature_c_set_missing": temperature_c_missing,
    }
    with open(os.path.join(OUTPUT_DIR, "cleaning_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)


if __name__ == "__main__":
    main()
