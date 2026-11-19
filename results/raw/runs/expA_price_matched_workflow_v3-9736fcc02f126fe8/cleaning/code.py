import json
import os
import re
from datetime import datetime

import pandas as pd

INPUT_DIR = os.environ["INPUT_DIR"]
OUTPUT_DIR = os.environ["OUTPUT_DIR"]

MISSING_VALUES = ["", "na", "n/a", "null", "none", "-"]

BUILDING_MAP = {
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

DATE_FORMATS = (
    "%Y-%m-%d",   # YYYY-MM-DD
    "%m/%d/%Y",   # MM/DD/YYYY (month first)
    "%d-%b-%Y",   # DD-Mon-YYYY (e.g. 05-Mar-2024)
    "%Y/%m/%d",   # YYYY/MM/DD
    "%B %d, %Y",  # Month D, YYYY (e.g. March 5, 2024)
)

MWH_RE = re.compile(r"^(.+?)\s*mwh\s*$", re.IGNORECASE)
KWH_RE = re.compile(r"^(.+?)\s*kwh\s*$", re.IGNORECASE)
TEMP_UNIT_RE = re.compile(r"^(.*?)\s*°?\s*([FfCc])\s*$")
TRAILING_DEG_RE = re.compile(r"°\s*$")


def parse_date(value):
    if value is None:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def parse_energy(value):
    """Return energy in kWh rounded to 2 decimals, or None if missing/invalid/out of range."""
    if value is None:
        return None
    text = value.replace(",", "").strip()
    factor = 1.0
    match = MWH_RE.match(text)
    if match:
        number_text = match.group(1)
        factor = 1000.0
    else:
        match = KWH_RE.match(text)
        if match:
            number_text = match.group(1)
        else:
            number_text = text
    try:
        kwh = float(number_text.strip()) * factor
    except (ValueError, TypeError):
        return None
    if kwh < 0 or kwh > 100000:
        return None
    return round(kwh, 2)


def parse_temperature(value):
    """Return temperature in Celsius rounded to 1 decimal, or None if missing/invalid/out of range."""
    if value is None:
        return None
    text = value.strip()
    unit = "C"
    match = TEMP_UNIT_RE.match(text)
    if match:
        number_text = match.group(1).strip()
        unit = match.group(2).upper()
    else:
        number_text = TRAILING_DEG_RE.sub("", text).strip()
    try:
        temp = float(number_text)
    except (ValueError, TypeError):
        return None
    if unit == "F":
        temp = (temp - 32.0) * 5.0 / 9.0
    temp = round(temp, 1)
    if temp < -40 or temp > 50:
        return None
    return temp


def main():
    summary = {}

    # R1: read every column as text, strip whitespace, normalise missing markers.
    raw = pd.read_csv(
        os.path.join(INPUT_DIR, "raw.csv"),
        dtype=str,
        keep_default_na=False,
        na_filter=False,
    )
    raw.columns = [c.strip() for c in raw.columns]
    summary["raw_rows"] = int(len(raw))
    for col in raw.columns:
        stripped = raw[col].str.strip()
        raw[col] = stripped.where(~stripped.str.lower().isin(MISSING_VALUES), None)

    # R2: drop duplicate reading_id rows, keeping the first occurrence in raw-file order.
    dup_mask = raw["reading_id"].notna() & raw.duplicated(subset="reading_id", keep="first")
    summary["duplicates_removed"] = int(dup_mask.sum())
    df = raw.loc[~dup_mask].copy()

    # R3: reading_date parsed against the five allowed formats; drop missing/unparseable.
    parsed = df["reading_date"].map(parse_date)
    bad = parsed.isna()
    summary["dropped_reading_date"] = int(bad.sum())
    df = df.loc[~bad].copy()
    df["reading_date"] = parsed.loc[~bad]

    # R4: meter_id upper-cased; drop missing.
    bad = df["meter_id"].isna()
    summary["dropped_meter_id"] = int(bad.sum())
    df = df.loc[~bad].copy()
    df["meter_id"] = df["meter_id"].str.upper()

    # R5: building_type mapped to the three canonical categories; drop missing/unmapped.
    mapped = df["building_type"].map(
        lambda v: BUILDING_MAP.get(v.lower()) if v is not None else None
    )
    bad = mapped.isna()
    summary["dropped_building_type"] = int(bad.sum())
    df = df.loc[~bad].copy()
    df["building_type"] = mapped.loc[~bad]

    # R6: tariff mapped to peak/off-peak; drop missing/unmapped.
    mapped = df["tariff"].map(
        lambda v: TARIFF_MAP.get(v.lower()) if v is not None else None
    )
    bad = mapped.isna()
    summary["dropped_tariff"] = int(bad.sum())
    df = df.loc[~bad].copy()
    df["tariff"] = mapped.loc[~bad]

    # R7: energy -> energy_kwh (unit handling, range 0..100000, 2 decimals); drop invalid.
    parsed = df["energy"].map(parse_energy)
    bad = parsed.isna()
    summary["dropped_energy"] = int(bad.sum())
    df = df.loc[~bad].copy()
    df["energy_kwh"] = parsed.loc[~bad].astype(float)

    # R8: temperature -> temperature_c; invalid/out-of-range becomes missing but row is kept.
    parsed = df["temperature"].map(parse_temperature)
    summary["temperature_set_missing"] = int(parsed.isna().sum())
    df["temperature_c"] = parsed.astype("float64")

    # R9: select the required columns, sort by reading_id ascending, write CSV (NaN -> empty cell).
    out = df[
        ["reading_id", "reading_date", "meter_id", "building_type", "tariff", "energy_kwh", "temperature_c"]
    ].sort_values("reading_id", ascending=True)
    summary["cleaned_rows"] = int(len(out))

    out.to_csv(os.path.join(OUTPUT_DIR, "cleaned.csv"), index=False)

    with open(os.path.join(OUTPUT_DIR, "cleaning_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)


if __name__ == "__main__":
    main()
