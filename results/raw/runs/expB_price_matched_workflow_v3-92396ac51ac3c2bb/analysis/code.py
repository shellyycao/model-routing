import os
import json
import math

import pandas as pd
import numpy as np

INPUT_DIR = os.environ["INPUT_DIR"]
OUTPUT_DIR = os.environ["OUTPUT_DIR"]


def finite(value, default=0.0):
    """Convert to a plain Python float guaranteed to be finite (no NaN/Inf)."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return float(default)
    if math.isnan(v) or math.isinf(v):
        return float(default)
    return v


df = pd.read_csv(os.path.join(INPUT_DIR, "cleaned.csv"), parse_dates=["reading_date"])

findings = {}

# q1: overall aggregation
total_kwh = df["energy_kwh"].sum()
reading_count = len(df)
findings["total_kwh"] = finite(total_kwh)
findings["reading_count"] = int(reading_count)
findings["mean_kwh_per_reading"] = finite(total_kwh / reading_count) if reading_count else 0.0

# q2: totals per building type
by_type = df.groupby("building_type")["energy_kwh"].sum()
findings["kwh_residential"] = finite(by_type.get("Residential", 0.0))
findings["kwh_commercial"] = finite(by_type.get("Commercial", 0.0))
findings["kwh_industrial"] = finite(by_type.get("Industrial", 0.0))

# q3: quarterly totals (calendar quarters of 2024)
by_quarter = df.groupby(df["reading_date"].dt.quarter)["energy_kwh"].sum()
findings["kwh_q1"] = finite(by_quarter.get(1, 0.0))
findings["kwh_q2"] = finite(by_quarter.get(2, 0.0))
findings["kwh_q3"] = finite(by_quarter.get(3, 0.0))
findings["kwh_q4"] = finite(by_quarter.get(4, 0.0))

# q4: first-half vs second-half change
month = df["reading_date"].dt.month
kwh_h1 = df.loc[month <= 6, "energy_kwh"].sum()
kwh_h2 = df.loc[month >= 7, "energy_kwh"].sum()
findings["kwh_h1"] = finite(kwh_h1)
findings["kwh_h2"] = finite(kwh_h2)
findings["kwh_h2_vs_h1_change_pct"] = finite((kwh_h2 - kwh_h1) / kwh_h1 * 100.0) if kwh_h1 else 0.0

# q5: hot-day commercial load (temperature >= 25 C, non-missing)
hot_commercial = df[
    (df["building_type"] == "Commercial")
    & (df["temperature_c"].notna())
    & (df["temperature_c"] >= 25.0)
]
findings["hot_commercial_reading_count"] = int(len(hot_commercial))
findings["hot_commercial_mean_kwh"] = finite(hot_commercial["energy_kwh"].mean()) if len(hot_commercial) else 0.0

# q6: distribution summary
findings["kwh_median"] = finite(df["energy_kwh"].median())
findings["kwh_std"] = finite(df["energy_kwh"].std(ddof=1))
temps = df["temperature_c"].dropna()
findings["temperature_mean"] = finite(temps.mean()) if len(temps) else 0.0
findings["temperature_missing_count"] = int(df["temperature_c"].isna().sum())

commercial_with_temp = df[(df["building_type"] == "Commercial") & (df["temperature_c"].notna())]
if (
    len(commercial_with_temp) >= 2
    and commercial_with_temp["temperature_c"].std(ddof=1) > 0
    and commercial_with_temp["energy_kwh"].std(ddof=1) > 0
):
    corr = commercial_with_temp["temperature_c"].corr(commercial_with_temp["energy_kwh"], method="pearson")
else:
    corr = 0.0
findings["commercial_temp_kwh_corr"] = finite(corr)

# q7: tariff and meter usage
by_tariff = df.groupby("tariff")["energy_kwh"].sum()
kwh_peak = by_tariff.get("peak", 0.0)
kwh_off_peak = by_tariff.get("off-peak", 0.0)
findings["kwh_peak"] = finite(kwh_peak)
findings["kwh_off_peak"] = finite(kwh_off_peak)
findings["peak_kwh_share_pct"] = finite(kwh_peak / total_kwh * 100.0) if total_kwh else 0.0
findings["unique_meter_count"] = int(df["meter_id"].nunique())
meter_totals = df.groupby("meter_id")["energy_kwh"].sum()
findings["highest_use_meter_kwh"] = finite(meter_totals.max()) if len(meter_totals) else 0.0

os.makedirs(OUTPUT_DIR, exist_ok=True)
with open(os.path.join(OUTPUT_DIR, "findings.json"), "w") as f:
    json.dump(findings, f, indent=2)
