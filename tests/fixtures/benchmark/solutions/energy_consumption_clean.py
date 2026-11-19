# SYNTHETIC_FIXTURE - test solution, not a model output and not a result.
"""pandas cleaning script for energy_consumption written ONLY from project.json cleaning_requirements.
Independent of datasets/energy_consumption.py. Bugs for negative tests:
  ignore_mwh, ignore_fahrenheit, drop_bad_temperature
"""

import os
import re
import sys

import pandas as pd

MISSING = {"", "na", "n/a", "null", "none", "-"}
MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august",
          "september", "october", "november", "december"]


def _date(s):
    if not isinstance(s, str):
        return None
    if m := re.fullmatch(r"(\d{4})[-/](\d{2})[-/](\d{2})", s):
        return pd.Timestamp(int(m[1]), int(m[2]), int(m[3]))
    if m := re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", s):
        return pd.Timestamp(int(m[3]), int(m[1]), int(m[2]))
    if m := re.fullmatch(r"(\d{2})-([A-Za-z]{3})-(\d{4})", s):
        return pd.Timestamp(int(m[3]), [x[:3] for x in MONTHS].index(m[2].lower()) + 1, int(m[1]))
    if m := re.fullmatch(r"([A-Za-z]+) (\d{1,2}), (\d{4})", s):
        return pd.Timestamp(int(m[3]), MONTHS.index(m[1].lower()) + 1, int(m[2]))
    return None


def _num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def _energy(s, bug):
    if not isinstance(s, str):
        return None
    s = s.replace(",", "").strip()
    if m := re.fullmatch(r"(.*?)\s*mwh", s, flags=re.I):
        x = _num(m[1])
        return None if x is None else x * (1 if bug == "ignore_mwh" else 1000)
    s = re.sub(r"\s*kwh$", "", s, flags=re.I)
    return _num(s)


def _temp(s, bug):
    if not isinstance(s, str):
        return None
    m = re.fullmatch(r"(.*?)\s*°?\s*([CcFf])?", s)
    x = _num(m[1]) if m else None
    if x is None:
        return None
    if m[2] and m[2].lower() == "f" and bug != "ignore_fahrenheit":
        x = (x - 32) * 5 / 9
    x = round(x, 1)
    return x if -40 <= x <= 50 else None


def clean(raw: pd.DataFrame, bug: str | None = None) -> pd.DataFrame:
    df = raw.copy()
    for c in df.columns:
        df[c] = df[c].map(lambda v: None if str(v).strip().lower() in MISSING else str(v).strip())
    df = df.drop_duplicates("reading_id", keep="first")
    df["reading_date"] = df["reading_date"].map(_date)
    df = df[df["reading_date"].notna() & df["meter_id"].notna()]
    df["meter_id"] = df["meter_id"].str.upper()
    types = {"residential": "Residential", "commercial": "Commercial", "industrial": "Industrial",
             "res": "Residential", "resi": "Residential", "comm": "Commercial", "ind": "Industrial"}
    df["building_type"] = df["building_type"].map(lambda s: types.get(s.lower()) if isinstance(s, str) else None)
    tariffs = {"peak": "peak", "off-peak": "off-peak", "offpeak": "off-peak", "off peak": "off-peak"}
    df["tariff"] = df["tariff"].map(lambda s: tariffs.get(s.lower()) if isinstance(s, str) else None)
    df = df[df["building_type"].notna() & df["tariff"].notna()]
    df["energy_kwh"] = df["energy"].map(lambda s: _energy(s, bug))
    df = df[df["energy_kwh"].notna() & (df["energy_kwh"] >= 0) & (df["energy_kwh"] <= 100000)]
    df["energy_kwh"] = df["energy_kwh"].round(2)
    df["temperature_c"] = df["temperature"].map(lambda s: _temp(s, bug))
    if bug == "drop_bad_temperature":
        df = df[df["temperature_c"].notna()]
    df["reading_date"] = df["reading_date"].map(lambda t: t.strftime("%Y-%m-%d"))
    cols = ["reading_id", "reading_date", "meter_id", "building_type", "tariff", "energy_kwh", "temperature_c"]
    return df[cols].sort_values("reading_id").reset_index(drop=True)


def main():
    raw = pd.read_csv(os.path.join(os.environ["INPUT_DIR"], "raw.csv"), dtype=str, keep_default_na=False)
    clean(raw, sys.argv[1] if len(sys.argv) > 1 else None).to_csv(
        os.path.join(os.environ["OUTPUT_DIR"], "cleaned.csv"), index=False)


if __name__ == "__main__":
    main()
