import json
import os
from datetime import datetime

import pandas as pd

MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}

DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%Y/%m/%d", "%B %d, %Y")

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


def parse_date(value):
    if pd.isna(value):
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def parse_energy_kwh(value):
    if pd.isna(value):
        return None
    text = value.replace(",", "").strip()
    factor = 1.0
    lower = text.lower()
    if lower.endswith("mwh"):
        factor = 1000.0
        text = text[:-3].strip()
    elif lower.endswith("kwh"):
        text = text[:-3].strip()
    try:
        number = float(text)
    except ValueError:
        return None
    return number * factor


def parse_temperature_c(value):
    if pd.isna(value):
        return None
    text = value.strip()
    lower = text.lower()
    is_fahrenheit = lower.endswith("f")
    if is_fahrenheit or lower.endswith("c"):
        text = text[:-1].strip()
    if text.endswith("\u00b0"):
        text = text[:-1].strip()
    try:
        number = float(text)
    except ValueError:
        return None
    if is_fahrenheit:
        number = (number - 32.0) * 5.0 / 9.0
    if number < -40.0 or number > 50.0:
        return None
    return round(number, 1)


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "raw.csv")
    output_dir = os.environ["OUTPUT_DIR"]
    os.makedirs(output_dir, exist_ok=True)
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    summary_path = os.path.join(output_dir, "cleaning_summary.json")

    summary = {}

    # R1: read every column as text, strip whitespace, normalise missing tokens.
    df = pd.read_csv(input_path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    summary["raw_rows"] = int(len(df))
    for column in df.columns:
        stripped = df[column].astype(str).str.strip()
        df[column] = stripped.mask(stripped.str.lower().isin(MISSING_TOKENS), pd.NA)

    # R2: remove duplicate reading_id rows (keep first in raw-file order) before any other row filter.
    duplicate_mask = df["reading_id"].notna() & df.duplicated(subset=["reading_id"], keep="first")
    summary["duplicates_removed_reading_id"] = int(duplicate_mask.sum())
    df = df.loc[~duplicate_mask].copy()

    # R3: parse reading_date with the allowed formats; drop missing/unparseable; write YYYY-MM-DD.
    df["reading_date"] = df["reading_date"].map(parse_date)
    drop_mask = df["reading_date"].isna()
    summary["dropped_reading_date_missing_or_unparseable"] = int(drop_mask.sum())
    df = df.loc[~drop_mask].copy()

    # R4: upper-case meter_id; drop missing.
    df["meter_id"] = df["meter_id"].str.upper()
    drop_mask = df["meter_id"].isna()
    summary["dropped_meter_id_missing"] = int(drop_mask.sum())
    df = df.loc[~drop_mask].copy()

    # R5: standardise building_type (case-insensitive, with variants); drop missing/unknown.
    df["building_type"] = df["building_type"].str.lower().map(BUILDING_TYPE_MAP)
    drop_mask = df["building_type"].isna()
    summary["dropped_building_type_missing_or_unknown"] = int(drop_mask.sum())
    df = df.loc[~drop_mask].copy()

    # R6: standardise tariff; drop missing/unknown.
    df["tariff"] = df["tariff"].str.lower().map(TARIFF_MAP)
    drop_mask = df["tariff"].isna()
    summary["dropped_tariff_missing_or_unknown"] = int(drop_mask.sum())
    df = df.loc[~drop_mask].copy()

    # R7: convert energy to kWh (handle commas, kWh/MWh units); drop missing/non-numeric/out-of-range; round to 2 dp.
    summary["energy_mwh_values_converted"] = int(
        df["energy"].dropna().str.replace(",", "", regex=False).str.strip().str.lower().str.endswith("mwh").sum()
    )
    df["energy_kwh"] = pd.to_numeric(df["energy"].map(parse_energy_kwh))
    drop_mask = df["energy_kwh"].isna()
    summary["dropped_energy_missing_or_not_numeric"] = int(drop_mask.sum())
    df = df.loc[~drop_mask].copy()
    drop_mask = ~df["energy_kwh"].between(0.0, 100000.0)
    summary["dropped_energy_out_of_range"] = int(drop_mask.sum())
    df = df.loc[~drop_mask].copy()
    df["energy_kwh"] = df["energy_kwh"].round(2)

    # R8: convert temperature to Celsius (Fahrenheit when suffixed with F); missing/invalid/out-of-range
    # becomes an empty cell but the row is kept. Round to 1 dp.
    df["temperature_c"] = pd.to_numeric(df["temperature"].map(parse_temperature_c))
    summary["temperature_set_to_missing"] = int(df["temperature_c"].isna().sum())

    # R9: final column selection/order, sort by reading_id ascending, write CSV with header and no index.
    out = df[
        ["reading_id", "reading_date", "meter_id", "building_type", "tariff", "energy_kwh", "temperature_c"]
    ].sort_values("reading_id", kind="mergesort")
    out.to_csv(cleaned_path, index=False)
    summary["cleaned_rows"] = int(len(out))

    with open(summary_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)


if __name__ == "__main__":
    main()
