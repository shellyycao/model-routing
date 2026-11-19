import os
import re
import json
import math
from datetime import datetime

import numpy as np
import pandas as pd

INPUT_DIR = os.environ["INPUT_DIR"]
OUTPUT_DIR = os.environ["OUTPUT_DIR"]
os.makedirs(OUTPUT_DIR, exist_ok=True)

MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}
DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%Y/%m/%d", "%B %d, %Y")

BUILDING_MAP = {
    "residential": "Residential", "res": "Residential", "resi": "Residential",
    "commercial": "Commercial", "comm": "Commercial",
    "industrial": "Industrial", "ind": "Industrial",
}
TARIFF_MAP = {
    "peak": "peak",
    "off-peak": "off-peak", "offpeak": "off-peak", "off peak": "off-peak",
}
TEMP_RE = re.compile(r"^([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*\u00b0?\s*([FfCc])?$")


def norm_key(v):
    return " ".join(str(v).split()).lower()


# ---- R1: read everything as text, strip whitespace, normalize missing tokens ----
raw_path = os.path.join(INPUT_DIR, "raw.csv")
df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
raw_rows = int(len(df))


def clean_cell(v):
    s = "" if v is None else str(v)
    s = s.strip()
    return np.nan if s.lower() in MISSING_TOKENS else s


for col in df.columns:
    df[col] = df[col].map(clean_cell)

# ---- R2: remove duplicate reading_id (keep first in raw order) BEFORE any row filter ----
before = len(df)
df = df.drop_duplicates(subset="reading_id", keep="first")
duplicates_removed = int(before - len(df))

# ---- R3: parse reading_date against the five allowed formats ----
def parse_date(v):
    if not isinstance(v, str):
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(v, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


parsed_date = df["reading_date"].map(parse_date)
dropped_date = int(parsed_date.isna().sum())
df = df.loc[parsed_date.notna()].copy()
df["reading_date"] = parsed_date[parsed_date.notna()].values

# ---- R4: meter_id to upper case, drop missing ----
df["meter_id"] = df["meter_id"].map(lambda v: v.upper() if isinstance(v, str) else np.nan)
before = len(df)
df = df.loc[df["meter_id"].notna()].copy()
dropped_meter = int(before - len(df))

# ---- R5: normalize building_type, drop missing/unmapped ----
bt = df["building_type"].map(lambda v: BUILDING_MAP.get(norm_key(v)) if isinstance(v, str) else None)
dropped_building = int(bt.isna().sum())
df = df.loc[bt.notna()].copy()
df["building_type"] = bt[bt.notna()].values

# ---- R6: normalize tariff, drop missing/unmapped ----
tf = df["tariff"].map(lambda v: TARIFF_MAP.get(norm_key(v)) if isinstance(v, str) else None)
dropped_tariff = int(tf.isna().sum())
df = df.loc[tf.notna()].copy()
df["tariff"] = tf[tf.notna()].values

# ---- R7: energy -> energy_kwh (strip commas/units, convert MWh, bound 0..100000) ----
def parse_energy(v):
    if not isinstance(v, str):
        return None
    s = v.replace(",", "").strip()
    if not s:
        return None
    low = s.lower()
    factor = 1.0
    if low.endswith("mwh"):
        s = s[:-3].strip()
        factor = 1000.0
    elif low.endswith("kwh"):
        s = s[:-3].strip()
    try:
        x = float(s)
    except ValueError:
        return None
    if not math.isfinite(x):
        return None
    x *= factor
    if x < 0 or x > 100000:
        return None
    return round(x, 2)


en = df["energy"].map(parse_energy)
dropped_energy = int(en.isna().sum())
df = df.loc[en.notna()].copy()
df["energy_kwh"] = en[en.notna()].astype(float).values

# ---- R8: temperature -> temperature_c (F->C, range check, keep row on failure) ----
def parse_temperature(v):
    if not isinstance(v, str):
        return np.nan
    m = TEMP_RE.match(v.strip())
    if not m:
        return np.nan
    x = float(m.group(1))
    unit = m.group(2)
    if unit is not None and unit.lower() == "f":
        x = (x - 32.0) * 5.0 / 9.0
    if x < -40 or x > 50:
        return np.nan
    return round(x, 1)


tc = df["temperature"].map(parse_temperature)
temperature_set_missing = int(pd.isna(tc).sum())
df["temperature_c"] = tc.values

# ---- R9: final column set, sort by reading_id, write outputs ----
out = df[["reading_id", "reading_date", "meter_id", "building_type", "tariff",
          "energy_kwh", "temperature_c"]].copy()
out = out.sort_values("reading_id", kind="mergesort").reset_index(drop=True)

cleaned_path = os.path.join(OUTPUT_DIR, "cleaned.csv")
out.to_csv(cleaned_path, index=False)

summary = {
    "raw_rows": raw_rows,
    "cleaned_rows": int(len(out)),
    "duplicates_removed_reading_id": duplicates_removed,
    "dropped_bad_reading_date": dropped_date,
    "dropped_missing_meter_id": dropped_meter,
    "dropped_bad_building_type": dropped_building,
    "dropped_bad_tariff": dropped_tariff,
    "dropped_bad_energy": dropped_energy,
    "temperature_set_missing": temperature_set_missing,
}
with open(os.path.join(OUTPUT_DIR, "cleaning_summary.json"), "w") as f:
    json.dump(summary, f, indent=2)
