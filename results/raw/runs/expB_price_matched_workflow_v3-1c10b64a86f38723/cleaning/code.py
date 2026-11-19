import os
import json
import math
import re
from datetime import date

import numpy as np
import pandas as pd

MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}
REQUIRED_COLUMNS = [
    "reading_id",
    "reading_date",
    "meter_id",
    "building_type",
    "tariff",
    "energy",
    "temperature",
]
OUTPUT_COLUMNS = [
    "reading_id",
    "reading_date",
    "meter_id",
    "building_type",
    "tariff",
    "energy_kwh",
    "temperature_c",
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
MONTH_ABBR = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}
MONTH_FULL = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

YMD_DASH_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
MDY_SLASH_RE = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")
DMON_DASH_RE = re.compile(r"^(\d{2})-([A-Za-z]{3})-(\d{4})$")
YMD_SLASH_RE = re.compile(r"^(\d{4})/(\d{2})/(\d{2})$")
MONTH_D_Y_RE = re.compile(r"^([A-Za-z]+) (\d{1,2}), (\d{4})$")
TEMP_RE = re.compile(r"^\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s*(.*?)\s*$")


def make_iso_date(year, month, day):
    try:
        return date(int(year), int(month), int(day)).isoformat()
    except (TypeError, ValueError):
        return None


def parse_reading_date(value):
    if pd.isna(value):
        return None
    text = str(value)

    match = YMD_DASH_RE.match(text)
    if match:
        return make_iso_date(match.group(1), match.group(2), match.group(3))

    match = MDY_SLASH_RE.match(text)
    if match:
        return make_iso_date(match.group(3), match.group(1), match.group(2))

    match = DMON_DASH_RE.match(text)
    if match:
        month = MONTH_ABBR.get(match.group(2).lower())
        if month is None:
            return None
        return make_iso_date(match.group(3), month, match.group(1))

    match = YMD_SLASH_RE.match(text)
    if match:
        return make_iso_date(match.group(1), match.group(2), match.group(3))

    match = MONTH_D_Y_RE.match(text)
    if match:
        month = MONTH_FULL.get(match.group(1).lower())
        if month is None:
            return None
        return make_iso_date(match.group(3), month, match.group(2))

    return None


def parse_energy_kwh(value):
    if pd.isna(value):
        return None
    text = str(value).replace(",", "").strip()
    if not text:
        return None

    lowered = text.lower()
    multiplier = 1.0
    number_text = text
    if lowered.endswith("mwh"):
        multiplier = 1000.0
        number_text = text[:-3].strip()
    elif lowered.endswith("kwh"):
        number_text = text[:-3].strip()

    if not number_text:
        return None
    try:
        energy = float(number_text) * multiplier
    except ValueError:
        return None
    if not math.isfinite(energy) or energy < 0 or energy > 100000:
        return None
    return round(energy, 2)


def parse_temperature_c(value):
    if pd.isna(value):
        return "missing", None
    text = str(value)
    match = TEMP_RE.match(text)
    if not match:
        return "invalid", None

    number_text, suffix = match.groups()
    compact_suffix = re.sub(r"\s+", "", suffix).lower()
    if compact_suffix in {"f", "°f"}:
        unit = "f"
    elif compact_suffix in {"", "c", "°c", "°"}:
        unit = "c"
    else:
        return "invalid", None

    try:
        measured = float(number_text)
    except ValueError:
        return "invalid", None

    celsius = (measured - 32.0) * 5.0 / 9.0 if unit == "f" else measured
    if not math.isfinite(celsius):
        return "invalid", None
    if celsius < -40.0 or celsius > 50.0:
        return "out_of_range", None
    return "ok", round(celsius, 1)


def map_building_type(value):
    if pd.isna(value):
        return None
    return BUILDING_MAP.get(str(value).lower())


def map_tariff(value):
    if pd.isna(value):
        return None
    return TARIFF_MAP.get(str(value).lower())


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "raw.csv")
    output_dir = os.environ["OUTPUT_DIR"]
    os.makedirs(output_dir, exist_ok=True)
    cleaned_path = os.path.join(output_dir, "cleaned.csv")
    summary_path = os.path.join(output_dir, "cleaning_summary.json")

    df = pd.read_csv(
        input_path,
        dtype=str,
        keep_default_na=False,
        na_filter=False,
        encoding="utf-8-sig",
    )
    raw_rows = int(len(df))
    df.columns = [str(column).strip() for column in df.columns]
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing_columns:
        raise ValueError("Missing required columns: " + ", ".join(missing_columns))

    values_marked_missing = 0
    for column in df.columns:
        stripped = df[column].astype(str).str.strip()
        missing_mask = stripped.str.lower().isin(MISSING_TOKENS)
        values_marked_missing += int(missing_mask.sum())
        df[column] = stripped.mask(missing_mask, pd.NA)
    df = df[REQUIRED_COLUMNS].copy()

    summary = {
        "raw_rows": raw_rows,
        "r1_values_marked_missing": values_marked_missing,
    }

    missing_reading_id_mask = df["reading_id"].isna()
    summary["r2_missing_reading_id_dropped"] = int(missing_reading_id_mask.sum())
    df = df.loc[~missing_reading_id_mask].copy()
    before_dedup = len(df)
    df = df.drop_duplicates(subset=["reading_id"], keep="first").copy()
    summary["r2_duplicate_reading_id_dropped"] = int(before_dedup - len(df))

    parsed_dates = df["reading_date"].apply(parse_reading_date)
    valid_date_mask = parsed_dates.notna()
    summary["r3_reading_date_dropped"] = int((~valid_date_mask).sum())
    df = df.loc[valid_date_mask].copy()
    df["reading_date"] = parsed_dates.loc[valid_date_mask].astype(str)

    missing_meter_mask = df["meter_id"].isna()
    summary["r4_meter_id_dropped"] = int(missing_meter_mask.sum())
    df = df.loc[~missing_meter_mask].copy()
    df["meter_id"] = df["meter_id"].astype(str).str.upper()

    mapped_buildings = df["building_type"].apply(map_building_type)
    valid_building_mask = mapped_buildings.notna()
    summary["r5_building_type_dropped"] = int((~valid_building_mask).sum())
    df = df.loc[valid_building_mask].copy()
    df["building_type"] = mapped_buildings.loc[valid_building_mask].astype(str)

    mapped_tariffs = df["tariff"].apply(map_tariff)
    valid_tariff_mask = mapped_tariffs.notna()
    summary["r6_tariff_dropped"] = int((~valid_tariff_mask).sum())
    df = df.loc[valid_tariff_mask].copy()
    df["tariff"] = mapped_tariffs.loc[valid_tariff_mask].astype(str)

    parsed_energy = df["energy"].apply(parse_energy_kwh)
    valid_energy_mask = parsed_energy.notna()
    summary["r7_energy_dropped"] = int((~valid_energy_mask).sum())
    df = df.loc[valid_energy_mask].copy()
    df["energy_kwh"] = parsed_energy.loc[valid_energy_mask].astype(float)

    temperature_statuses = []
    temperature_values = []
    for value in df["temperature"]:
        status, parsed_temperature = parse_temperature_c(value)
        temperature_statuses.append(status)
        temperature_values.append(parsed_temperature)

    summary["r8_temperature_missing_input"] = int(temperature_statuses.count("missing"))
    summary["r8_temperature_invalid"] = int(temperature_statuses.count("invalid"))
    summary["r8_temperature_out_of_range"] = int(temperature_statuses.count("out_of_range"))
    summary["r8_temperature_set_missing"] = int(
        sum(status != "ok" for status in temperature_statuses)
    )
    df["temperature_c"] = [
        float(value) if status == "ok" else np.nan
        for status, value in zip(temperature_statuses, temperature_values)
    ]

    cleaned = df[OUTPUT_COLUMNS].copy()
    cleaned["energy_kwh"] = cleaned["energy_kwh"].astype(float)
    cleaned["temperature_c"] = cleaned["temperature_c"].astype(float)
    cleaned = cleaned.sort_values("reading_id", ascending=True, kind="mergesort").reset_index(drop=True)
    cleaned.to_csv(cleaned_path, index=False, na_rep="")

    summary["cleaned_rows"] = int(len(cleaned))
    with open(summary_path, "w", encoding="utf-8") as summary_file:
        json.dump(summary, summary_file, indent=2)


if __name__ == "__main__":
    main()
