import json
import os
import re
from datetime import datetime

import pandas as pd

MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}

DATE_FORMATS = (
    "%Y-%m-%d",   # YYYY-MM-DD
    "%m/%d/%Y",   # MM/DD/YYYY (month first)
    "%d-%b-%Y",   # DD-Mon-YYYY (e.g. 05-Mar-2024)
    "%Y/%m/%d",   # YYYY/MM/DD
    "%B %d, %Y",  # Month D, YYYY (e.g. March 5, 2024)
)

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

TEMP_RE = re.compile(r"^([+-]?(?:\d+(?:\.\d+)?|\.\d+))\s*\u00b0?\s*([CcFf])?$")


def parse_reading_date(value):
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def parse_energy(value):
    """Return energy in kWh as a float, or None if not numeric."""
    s = value.replace(",", "").strip()
    factor = 1.0
    low = s.lower()
    if low.endswith("mwh"):
        factor = 1000.0
        s = s[:-3].strip()
    elif low.endswith("kwh"):
        s = s[:-3].strip()
    if not s:
        return None
    try:
        return float(s) * factor
    except ValueError:
        return None


def parse_temperature(value):
    """Return temperature in Celsius (rounded to 1 dp), or None if invalid/out of range."""
    m = TEMP_RE.match(value.strip())
    if not m:
        return None
    try:
        t = float(m.group(1))
    except ValueError:
        return None
    if m.group(2) and m.group(2).lower() == "f":
        t = (t - 32.0) * 5.0 / 9.0
    if t < -40.0 or t > 50.0:
        return None
    return round(t, 1)


def main():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    os.makedirs(output_dir, exist_ok=True)
    raw_path = os.path.join(input_dir, "raw.csv")

    # R1: read every column as text, strip whitespace, normalise missing tokens.
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False, na_filter=False)
    summary = {"raw_rows": int(len(df))}
    df = df.apply(lambda col: col.astype(str).str.strip())
    df = df.apply(lambda col: col.map(lambda v: None if v.lower() in MISSING_TOKENS else v))

    # R2: de-duplicate on reading_id BEFORE any other row filter (keep first in raw order).
    missing_id = int(df["reading_id"].isna().sum())
    df = df[df["reading_id"].notna()]  # reading_id is not nullable in the output schema
    before = len(df)
    df = df.drop_duplicates(subset="reading_id", keep="first")
    summary["r2_missing_reading_id_dropped"] = missing_id
    summary["r2_duplicate_reading_id_dropped"] = int(before - len(df))

    # R3: reading_date -> YYYY-MM-DD; drop rows with missing/unparseable dates.
    parsed_date = df["reading_date"].map(lambda v: parse_reading_date(v) if v is not None else None)
    bad = parsed_date.isna()
    summary["r3_reading_date_dropped"] = int(bad.sum())
    df = df.loc[~bad].copy()
    df["reading_date"] = parsed_date[~bad]

    # R4: meter_id -> upper case; drop rows with missing meter_id.
    bad = df["meter_id"].isna()
    summary["r4_meter_id_dropped"] = int(bad.sum())
    df = df.loc[~bad].copy()
    df["meter_id"] = df["meter_id"].str.upper()

    # R5: building_type -> canonical category; drop missing/unmappable.
    bt = df["building_type"].map(lambda v: BUILDING_TYPE_MAP.get(v.lower()) if v is not None else None)
    bad = bt.isna()
    summary["r5_building_type_dropped"] = int(bad.sum())
    df = df.loc[~bad].copy()
    df["building_type"] = bt[~bad]

    # R6: tariff -> peak / off-peak; drop missing/unmappable.
    tf = df["tariff"].map(
        lambda v: TARIFF_MAP.get(re.sub(r"\s+", " ", v.lower())) if v is not None else None
    )
    bad = tf.isna()
    summary["r6_tariff_dropped"] = int(bad.sum())
    df = df.loc[~bad].copy()
    df["tariff"] = tf[~bad]

    # R7: energy -> energy_kwh; unit conversion, range check, round to 2 dp.
    en = df["energy"].map(lambda v: parse_energy(v) if v is not None else None)
    valid = en.map(lambda x: x is not None and 0.0 <= x <= 100000.0)
    summary["r7_energy_dropped"] = int((~valid).sum())
    df = df.loc[valid].copy()
    df["energy_kwh"] = en[valid].map(lambda x: round(float(x), 2))

    # R8: temperature -> temperature_c; invalid/out-of-range -> empty cell, keep row.
    tc = df["temperature"].map(lambda v: parse_temperature(v) if v is not None else None)
    summary["r8_temperature_set_missing"] = int(tc.isna().sum())
    df["temperature_c"] = tc.astype("float64")  # None becomes NaN -> empty CSV cell

    # R9: final column order, sort by reading_id ascending, write CSV (header, no index).
    out = df[[
        "reading_id", "reading_date", "meter_id", "building_type",
        "tariff", "energy_kwh", "temperature_c",
    ]].copy()
    out = out.sort_values("reading_id", kind="stable").reset_index(drop=True)
    out.to_csv(os.path.join(output_dir, "cleaned.csv"), index=False)

    summary["cleaned_rows"] = int(len(out))
    with open(os.path.join(output_dir, "cleaning_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)


if __name__ == "__main__":
    main()
