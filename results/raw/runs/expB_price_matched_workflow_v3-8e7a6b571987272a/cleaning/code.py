import os
import json
from datetime import datetime

import pandas as pd

MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}

DATE_FORMATS = [
    "%Y-%m-%d",   # YYYY-MM-DD
    "%m/%d/%Y",   # MM/DD/YYYY (month first)
    "%d-%b-%Y",   # DD-Mon-YYYY (e.g. 05-Mar-2024)
    "%Y/%m/%d",   # YYYY/MM/DD
    "%B %d, %Y",  # Month D, YYYY (e.g. March 5, 2024)
]

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


def clean_cell(x):
    """R1: strip whitespace; normalise missing tokens to None."""
    if not isinstance(x, str):
        return None
    x = x.strip()
    if x.lower() in MISSING_TOKENS:
        return None
    return x


def parse_date(value):
    """R3: try each allowed format exactly; return YYYY-MM-DD or None."""
    if value is None:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def parse_energy(value):
    """R7: return energy in kWh (rounded 2dp) or None if invalid."""
    if value is None:
        return None
    s = value.replace(",", "").strip()
    low = s.lower()
    factor = 1.0
    if low.endswith("mwh"):
        s = s[:-3].strip()
        factor = 1000.0
    elif low.endswith("kwh"):
        s = s[:-3].strip()
    if s == "":
        return None
    try:
        num = float(s)
    except ValueError:
        return None
    kwh = num * factor
    if kwh < 0 or kwh > 100000:
        return None
    return round(kwh, 2)


def parse_temperature(value):
    """R8: return Celsius (rounded 1dp) or None -> stored as missing, row kept."""
    if value is None:
        return None
    s = value.strip()
    low = s.lower()
    unit = "c"
    if low.endswith("\u00b0f"):
        s = s[:-2].strip()
        unit = "f"
    elif low.endswith("f"):
        s = s[:-1].strip()
        unit = "f"
    elif low.endswith("\u00b0c"):
        s = s[:-2].strip()
    elif low.endswith("c"):
        s = s[:-1].strip()
    elif low.endswith("\u00b0"):
        s = s[:-1].strip()
    if s == "":
        return None
    try:
        num = float(s)
    except ValueError:
        return None
    if unit == "f":
        num = (num - 32) * 5 / 9
    if num < -40 or num > 50:
        return None
    return round(num, 1)


def main():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    raw_path = os.path.join(input_dir, "raw.csv")

    # Read every column as text; keep raw strings so we control missing values.
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    summary = {"raw_rows": int(len(df))}

    # R1: strip whitespace and normalise missing tokens.
    df = df.apply(lambda col: col.map(clean_cell))

    # R2: drop duplicate reading_id BEFORE any other row filter; keep first in raw order.
    before = len(df)
    df = df.drop_duplicates(subset="reading_id", keep="first")
    summary["duplicates_removed_reading_id"] = int(before - len(df))

    # reading_id is not nullable in the output schema.
    before = len(df)
    df = df[df["reading_id"].notna()]
    summary["dropped_missing_reading_id"] = int(before - len(df))

    # R3: reading_date
    parsed_date = df["reading_date"].map(parse_date)
    bad = parsed_date.isna()
    summary["dropped_bad_reading_date"] = int(bad.sum())
    df = df.loc[~bad].copy()
    df["reading_date"] = parsed_date.loc[~bad]

    # R4: meter_id -> upper case; drop missing.
    bad = df["meter_id"].isna()
    summary["dropped_missing_meter_id"] = int(bad.sum())
    df = df.loc[~bad].copy()
    df["meter_id"] = df["meter_id"].str.upper()

    # R5: building_type canonical mapping.
    mapped_bt = df["building_type"].map(
        lambda v: BUILDING_MAP.get(v.lower()) if v is not None else None
    )
    bad = mapped_bt.isna()
    summary["dropped_bad_building_type"] = int(bad.sum())
    df = df.loc[~bad].copy()
    df["building_type"] = mapped_bt.loc[~bad]

    # R6: tariff canonical mapping.
    mapped_tariff = df["tariff"].map(
        lambda v: TARIFF_MAP.get(v.lower()) if v is not None else None
    )
    bad = mapped_tariff.isna()
    summary["dropped_bad_tariff"] = int(bad.sum())
    df = df.loc[~bad].copy()
    df["tariff"] = mapped_tariff.loc[~bad]

    # R7: energy -> energy_kwh
    parsed_energy = df["energy"].map(parse_energy)
    bad = parsed_energy.isna()
    summary["dropped_bad_energy"] = int(bad.sum())
    df = df.loc[~bad].copy()
    df["energy_kwh"] = pd.to_numeric(parsed_energy.loc[~bad])

    # R8: temperature -> temperature_c (missing allowed; row kept).
    parsed_temp = df["temperature"].map(parse_temperature)
    summary["temperature_set_missing"] = int(parsed_temp.isna().sum())
    df["temperature_c"] = pd.to_numeric(parsed_temp)

    # R9: final column set/order, sort by reading_id ascending, write CSV.
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
    ].copy()
    out = out.sort_values("reading_id", kind="mergesort").reset_index(drop=True)
    summary["cleaned_rows"] = int(len(out))

    os.makedirs(output_dir, exist_ok=True)
    out.to_csv(os.path.join(output_dir, "cleaned.csv"), index=False)

    with open(os.path.join(output_dir, "cleaning_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
