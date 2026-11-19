import os
import json
import pandas as pd
import numpy as np

# Read cleaned data
input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
df = pd.read_csv(input_path, parse_dates=["reading_date"])

# Ensure correct types
df["energy_kwh"] = pd.to_numeric(df["energy_kwh"], errors="coerce")
df["temperature_c"] = pd.to_numeric(df["temperature_c"], errors="coerce")
df["reading_date"] = pd.to_datetime(df["reading_date"], errors="coerce")

# --- Q1: Overall aggregation ---
total_kwh = float(df["energy_kwh"].sum())
reading_count = float(len(df))
mean_kwh_per_reading = float(total_kwh / reading_count) if reading_count > 0 else 0.0

# --- Q2: Building type totals ---
bt = df.groupby("building_type")["energy_kwh"].sum()
kwh_residential = float(bt.get("Residential", 0.0))
kwh_commercial = float(bt.get("Commercial", 0.0))
kwh_industrial = float(bt.get("Industrial", 0.0))

# --- Q3: Quarterly trend ---
df["quarter"] = df["reading_date"].dt.quarter
qt = df.groupby("quarter")["energy_kwh"].sum()
kwh_q1 = float(qt.get(1, 0.0))
kwh_q2 = float(qt.get(2, 0.0))
kwh_q3 = float(qt.get(3, 0.0))
kwh_q4 = float(qt.get(4, 0.0))

# --- Q4: Half-year change ---
df["month"] = df["reading_date"].dt.month
kwh_h1 = float(df[df["month"] <= 6]["energy_kwh"].sum())
kwh_h2 = float(df[df["month"] >= 7]["energy_kwh"].sum())
kwh_h2_vs_h1_change_pct = float((kwh_h2 - kwh_h1) / kwh_h1 * 100) if kwh_h1 != 0 else 0.0

# --- Q5: Hot-day commercial load ---
hot_commercial = df[
    (df["building_type"] == "Commercial") &
    (df["temperature_c"].notna()) &
    (df["temperature_c"] >= 25)
]
hot_commercial_reading_count = float(len(hot_commercial))
hot_commercial_mean_kwh = float(hot_commercial["energy_kwh"].mean()) if len(hot_commercial) > 0 else 0.0

# --- Q6: Distribution summary ---
kwh_median = float(df["energy_kwh"].median())
kwh_std = float(df["energy_kwh"].std(ddof=1))

df_temp_valid = df[df["temperature_c"].notna()]
temperature_mean = float(df_temp_valid["temperature_c"].mean()) if len(df_temp_valid) > 0 else 0.0
temperature_missing_count = float(df["temperature_c"].isna().sum())

commercial_with_temp = df[
    (df["building_type"] == "Commercial") &
    (df["temperature_c"].notna())
]
if len(commercial_with_temp) >= 2:
    commercial_temp_kwh_corr = float(
        commercial_with_temp["temperature_c"].corr(commercial_with_temp["energy_kwh"])
    )
else:
    commercial_temp_kwh_corr = 0.0

# --- Q7: Tariff and meter usage ---
tariff_totals = df.groupby("tariff")["energy_kwh"].sum()
kwh_peak = float(tariff_totals.get("peak", 0.0))
kwh_off_peak = float(tariff_totals.get("off-peak", 0.0))
peak_kwh_share_pct = float(kwh_peak / total_kwh * 100) if total_kwh != 0 else 0.0
unique_meter_count = float(df["meter_id"].nunique())
highest_use_meter_kwh = float(df.groupby("meter_id")["energy_kwh"].sum().max())

# --- Assemble findings ---
findings = {
    "total_kwh": total_kwh,
    "reading_count": reading_count,
    "mean_kwh_per_reading": mean_kwh_per_reading,
    "kwh_residential": kwh_residential,
    "kwh_commercial": kwh_commercial,
    "kwh_industrial": kwh_industrial,
    "kwh_q1": kwh_q1,
    "kwh_q2": kwh_q2,
    "kwh_q3": kwh_q3,
    "kwh_q4": kwh_q4,
    "kwh_h1": kwh_h1,
    "kwh_h2": kwh_h2,
    "kwh_h2_vs_h1_change_pct": kwh_h2_vs_h1_change_pct,
    "hot_commercial_reading_count": hot_commercial_reading_count,
    "hot_commercial_mean_kwh": hot_commercial_mean_kwh,
    "kwh_median": kwh_median,
    "kwh_std": kwh_std,
    "temperature_mean": temperature_mean,
    "temperature_missing_count": temperature_missing_count,
    "commercial_temp_kwh_corr": commercial_temp_kwh_corr,
    "kwh_peak": kwh_peak,
    "kwh_off_peak": kwh_off_peak,
    "peak_kwh_share_pct": peak_kwh_share_pct,
    "unique_meter_count": unique_meter_count,
    "highest_use_meter_kwh": highest_use_meter_kwh
}

# Validate all values are finite numbers
for k, v in findings.items():
    if not isinstance(v, (int, float)) or not np.isfinite(v):
        findings[k] = 0.0

# Write output
output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
with open(output_path, "w") as f:
    json.dump(findings, f)
