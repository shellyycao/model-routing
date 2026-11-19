import os
import json
import math
from datetime import datetime

import pandas as pd
import numpy as np

INPUT_DIR = os.environ["INPUT_DIR"]
OUTPUT_DIR = os.environ["OUTPUT_DIR"]

input_path = os.path.join(INPUT_DIR, "raw.csv")
output_csv = os.path.join(OUTPUT_DIR, "cleaned.csv")
summary_path = os.path.join(OUTPUT_DIR, "cleaning_summary.json")

MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}

# ---------- R1: read everything as text, strip, normalize missing ----------
df = pd.read_csv(input_path, dtype=str, keep_default_na=False, na_filter=False)
raw_rows = len(df)

def normalize(v):
    if v is None:
        return None
    s = str(v).strip()
    if s.lower() in MISSING_TOKENS:
        return None
    return s

for col in df.columns:
    df[col] = df[col].map(normalize)

counts = {}

# reading_id must be present (schema: not nullable)
missing_rid = int(df["reading_id"].isna().sum())
counts["rows_dropped_missing_reading_id"] = missing_rid
df = df[df["reading_id"].notna()].copy()

# ---------- R2: deduplicate on reading_id, keep first in raw order ----------
dup_mask = df.duplicated(subset="reading_id", keep="first")
counts["duplicates_removed"] = int(dup_mask.sum())
df = df[~dup_mask].copy()

# ---------- R3: reading_date parsing ----------
DATE_FORMATS = ["%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%Y/%m/%d", "%B %d, %Y"]

def parse_date(s):
    if s is None:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None

parsed_date = df["reading_date"].map(parse_date)
bad_date = parsed_date.isna()
counts["rows_dropped_bad_reading_date"] = int(bad_date.sum())
df = df[~bad_date].copy()
df["reading_date"] = parsed_date[~bad_date].map(lambda d: d.strftime("%Y-%m-%d"))

# ---------- R4: meter_id to upper case ----------
bad_meter = df["meter_id"].isna()
counts["rows_dropped_missing_meter_id"] = int(bad_meter.sum())
df = df[~bad_meter].copy()
df["meter_id"] = df["meter_id"].str.upper()

# ---------- R5: building_type mapping ----------
BUILDING_MAP = {
    "residential": "Residential",
    "res": "Residential",
    "resi": "Residential",
    "commercial": "Commercial",
    "comm": "Commercial",
    "industrial": "Industrial",
    "ind": "Industrial",
}
bt = df["building_type"].map(lambda s: BUILDING_MAP.get(s.lower()) if s is not None else None)
bad_bt = bt.isna()
counts["rows_dropped_bad_building_type"] = int(bad_bt.sum())
df = df[~bad_bt].copy()
df["building_type"] = bt[~bad_bt]

# ---------- R6: tariff mapping ----------
TARIFF_MAP = {
    "peak": "peak",
    "off-peak": "off-peak",
    "offpeak": "off-peak",
    "off peak": "off-peak",
}
tariff = df["tariff"].map(lambda s: TARIFF_MAP.get(s.lower()) if s is not None else None)
bad_tariff = tariff.isna()
counts["rows_dropped_bad_tariff"] = int(bad_tariff.sum())
df = df[~bad_tariff].copy()
df["tariff"] = tariff[~bad_tariff]

# ---------- R7: energy -> energy_kwh ----------
def parse_energy(s):
    if s is None:
        return None
    v = s.replace(",", "").strip()
    low = v.lower()
    mult = 1.0
    if low.endswith("mwh"):
        mult = 1000.0
        v = v[:-3].strip()
    elif low.endswith("kwh"):
        v = v[:-3].strip()
    try:
        num = float(v)
    except ValueError:
        return None
    if math.isnan(num) or math.isinf(num):
        return None
    return num * mult

energy = df["energy"].map(parse_energy)
bad_energy = energy.isna() | (energy < 0) | (energy > 100000)
counts["rows_dropped_bad_energy"] = int(bad_energy.sum())
df = df[~bad_energy].copy()
df["energy_kwh"] = energy[~bad_energy].round(2)

# ---------- R8: temperature -> temperature_c (keep rows, set missing on failure) ----------
def parse_temperature(s):
    if s is None:
        return None
    v = s.replace("\u00b0", "").strip().lower()
    is_f = False
    if v.endswith("f"):
        is_f = True
        v = v[:-1].strip()
    elif v.endswith("c"):
        v = v[:-1].strip()
    try:
        num = float(v)
    except ValueError:
        return None
    if math.isnan(num) or math.isinf(num):
        return None
    if is_f:
        num = (num - 32.0) * 5.0 / 9.0
    if num < -40 or num > 50:
        return None
    return round(num, 1)

temp = df["temperature"].map(parse_temperature)
counts["temperature_set_missing"] = int(temp.isna().sum())
df["temperature_c"] = temp

# ---------- R9: final columns, sort, write ----------
out = df[["reading_id", "reading_date", "meter_id", "building_type", "tariff", "energy_kwh", "temperature_c"]].copy()
out = out.sort_values("reading_id", ascending=True, kind="stable")
out.to_csv(output_csv, index=False)

cleaned_rows = len(out)

summary = {
    "raw_rows": int(raw_rows),
    "cleaned_rows": int(cleaned_rows),
}
summary.update({k: int(v) for k, v in counts.items()})

with open(summary_path, "w") as f:
    json.dump(summary, f, indent=2)
