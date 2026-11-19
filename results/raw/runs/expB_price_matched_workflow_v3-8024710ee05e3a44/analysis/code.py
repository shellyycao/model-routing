import json
import os

import numpy as np
import pandas as pd

INPUT_PATH = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
OUTPUT_PATH = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")


def finite_number(value, fallback=0.0):
    """Coerce a value to a finite float; use fallback if NaN/inf/unparseable."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return float(fallback)
    if not np.isfinite(v):
        return float(fallback)
    return v


# ---- Load cleaned data ----
df = pd.read_csv(
    INPUT_PATH,
    dtype={
        "reading_id": str,
        "meter_id": str,
        "building_type": str,
        "tariff": str,
    },
)
df["reading_date"] = pd.to_datetime(df["reading_date"], format="%Y-%m-%d", errors="coerce")
df["energy_kwh"] = pd.to_numeric(df["energy_kwh"], errors="coerce")
df["temperature_c"] = pd.to_numeric(df["temperature_c"], errors="coerce")

# ---- q1: Overall ----
total_kwh = df["energy_kwh"].sum()
reading_count = int(len(df))
mean_kwh_per_reading = total_kwh / reading_count if reading_count else 0.0

# ---- q2: Building types ----
by_type = df.groupby("building_type")["energy_kwh"].sum()
kwh_residential = by_type.get("Residential", 0.0)
kwh_commercial = by_type.get("Commercial", 0.0)
kwh_industrial = by_type.get("Industrial", 0.0)

# ---- q3: Quarterly trend ----
quarter = df["reading_date"].dt.quarter
by_quarter = df.groupby(quarter)["energy_kwh"].sum()
kwh_q1 = by_quarter.get(1, 0.0)
kwh_q2 = by_quarter.get(2, 0.0)
kwh_q3 = by_quarter.get(3, 0.0)
kwh_q4 = by_quarter.get(4, 0.0)

# ---- q4: Half-year change ----
month = df["reading_date"].dt.month
kwh_h1 = df.loc[month <= 6, "energy_kwh"].sum()
kwh_h2 = df.loc[month >= 7, "energy_kwh"].sum()
kwh_h2_vs_h1_change_pct = ((kwh_h2 - kwh_h1) / kwh_h1 * 100.0) if kwh_h1 else 0.0

# ---- q5: Hot-day commercial load (non-missing temp >= 25 C) ----
hot_mask = (df["building_type"] == "Commercial") & (df["temperature_c"] >= 25.0)
hot_commercial = df.loc[hot_mask, "energy_kwh"]
hot_commercial_reading_count = int(hot_mask.sum())
hot_commercial_mean_kwh = hot_commercial.mean() if hot_commercial_reading_count else 0.0

# ---- q6: Distribution summary ----
kwh_median = df["energy_kwh"].median()
kwh_std = df["energy_kwh"].std(ddof=1)  # sample standard deviation
temperature_mean = df["temperature_c"].mean()  # pandas skips NaN by default
temperature_missing_count = int(df["temperature_c"].isna().sum())

commercial_with_temp = df.loc[
    (df["building_type"] == "Commercial") & df["temperature_c"].notna(),
    ["temperature_c", "energy_kwh"],
]
if len(commercial_with_temp) >= 2:
    commercial_temp_kwh_corr = commercial_with_temp["temperature_c"].corr(
        commercial_with_temp["energy_kwh"], method="pearson"
    )
else:
    commercial_temp_kwh_corr = 0.0

# ---- q7: Tariff and meter usage ----
by_tariff = df.groupby("tariff")["energy_kwh"].sum()
kwh_peak = by_tariff.get("peak", 0.0)
kwh_off_peak = by_tariff.get("off-peak", 0.0)
peak_kwh_share_pct = (kwh_peak / total_kwh * 100.0) if total_kwh else 0.0

unique_meter_count = int(df["meter_id"].nunique())
meter_totals = df.groupby("meter_id")["energy_kwh"].sum()
highest_use_meter_kwh = meter_totals.max() if len(meter_totals) else 0.0

# ---- Assemble flat findings ----
findings = {
    "total_kwh": finite_number(total_kwh),
    "reading_count": reading_count,
    "mean_kwh_per_reading": finite_number(mean_kwh_per_reading),
    "kwh_residential": finite_number(kwh_residential),
    "kwh_commercial": finite_number(kwh_commercial),
    "kwh_industrial": finite_number(kwh_industrial),
    "kwh_q1": finite_number(kwh_q1),
    "kwh_q2": finite_number(kwh_q2),
    "kwh_q3": finite_number(kwh_q3),
    "kwh_q4": finite_number(kwh_q4),
    "kwh_h1": finite_number(kwh_h1),
    "kwh_h2": finite_number(kwh_h2),
    "kwh_h2_vs_h1_change_pct": finite_number(kwh_h2_vs_h1_change_pct),
    "hot_commercial_reading_count": hot_commercial_reading_count,
    "hot_commercial_mean_kwh": finite_number(hot_commercial_mean_kwh),
    "kwh_median": finite_number(kwh_median),
    "kwh_std": finite_number(kwh_std),
    "temperature_mean": finite_number(temperature_mean),
    "temperature_missing_count": temperature_missing_count,
    "commercial_temp_kwh_corr": finite_number(commercial_temp_kwh_corr),
    "kwh_peak": finite_number(kwh_peak),
    "kwh_off_peak": finite_number(kwh_off_peak),
    "peak_kwh_share_pct": finite_number(peak_kwh_share_pct),
    "unique_meter_count": unique_meter_count,
    "highest_use_meter_kwh": finite_number(highest_use_meter_kwh),
}

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(findings, f, indent=2, allow_nan=False)
