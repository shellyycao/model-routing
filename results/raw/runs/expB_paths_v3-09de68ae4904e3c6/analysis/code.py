import os
import json
import pandas as pd
import numpy as np

# Paths from environment variables
input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

# Load cleaned data; reading_date is already in ISO format
df = pd.read_csv(input_path, parse_dates=["reading_date"])

# Helper to ensure no NaN values are written
def _nan_to_zero(val):
    return 0.0 if pd.isna(val) else float(val)

# ------------------- q1: overall aggregation -------------------
total_kwh = df["energy_kwh"].sum()
reading_count = len(df)
mean_kwh_per_reading = total_kwh / reading_count if reading_count else 0.0

# ------------------- q2: building type totals -------------------
kwh_residential = df.loc[df["building_type"] == "Residential", "energy_kwh"].sum()
kwh_commercial = df.loc[df["building_type"] == "Commercial", "energy_kwh"].sum()
kwh_industrial = df.loc[df["building_type"] == "Industrial", "energy_kwh"].sum()

# ------------------- q3: quarterly trend -------------------
# Ensure the year is 2024 – the dataset is expected to contain only 2024 dates
quarters = df["reading_date"].dt.quarter
kwh_q1 = df.loc[quarters == 1, "energy_kwh"].sum()
kwh_q2 = df.loc[quarters == 2, "energy_kwh"].sum()
kwh_q3 = df.loc[quarters == 3, "energy_kwh"].sum()
kwh_q4 = df.loc[quarters == 4, "energy_kwh"].sum()

# ------------------- q4: half‑year change -------------------
months = df["reading_date"].dt.month
kwh_h1 = df.loc[months <= 6, "energy_kwh"].sum()
kwh_h2 = df.loc[months >= 7, "energy_kwh"].sum()
if kwh_h1 != 0:
    kwh_h2_vs_h1_change_pct = (kwh_h2 - kwh_h1) / kwh_h1 * 100.0
else:
    kwh_h2_vs_h1_change_pct = 0.0

# ------------------- q5: hot‑day commercial load -------------------
hot_commercial = df[(df["building_type"] == "Commercial") & (df["temperature_c"].notna()) & (df["temperature_c"] >= 25)]
hot_commercial_reading_count = len(hot_commercial)
if hot_commercial_reading_count:
    hot_commercial_mean_kwh = hot_commercial["energy_kwh"].mean()
else:
    hot_commercial_mean_kwh = 0.0

# ------------------- q6: distribution summary -------------------
kwh_median = df["energy_kwh"].median()
kwh_std = df["energy_kwh"].std(ddof=1)  # sample std
temperature_mean = df["temperature_c"].mean()
temperature_missing_count = df["temperature_c"].isna().sum()
# Correlation for Commercial rows with temperature present
commercial_temp = df[(df["building_type"] == "Commercial") & (df["temperature_c"].notna())]
if len(commercial_temp) >= 2:
    commercial_temp_kwh_corr = commercial_temp["temperature_c"].corr(commercial_temp["energy_kwh"])
else:
    commercial_temp_kwh_corr = 0.0

# ------------------- q7: tariff & meter usage -------------------
kwh_peak = df.loc[df["tariff"] == "peak", "energy_kwh"].sum()
kwh_off_peak = df.loc[df["tariff"] == "off-peak", "energy_kwh"].sum()
peak_kwh_share_pct = (kwh_peak / total_kwh) * 100.0 if total_kwh else 0.0
unique_meter_count = df["meter_id"].nunique()
highest_use_meter_kwh = df.groupby("meter_id")["energy_kwh"].sum().max()

# Assemble findings ensuring all values are plain Python numbers (no NaN)
findings = {
    "total_kwh": _nan_to_zero(total_kwh),
    "reading_count": int(reading_count),
    "mean_kwh_per_reading": _nan_to_zero(mean_kwh_per_reading),
    "kwh_residential": _nan_to_zero(kwh_residential),
    "kwh_commercial": _nan_to_zero(kwh_commercial),
    "kwh_industrial": _nan_to_zero(kwh_industrial),
    "kwh_q1": _nan_to_zero(kwh_q1),
    "kwh_q2": _nan_to_zero(kwh_q2),
    "kwh_q3": _nan_to_zero(kwh_q3),
    "kwh_q4": _nan_to_zero(kwh_q4),
    "kwh_h1": _nan_to_zero(kwh_h1),
    "kwh_h2": _nan_to_zero(kwh_h2),
    "kwh_h2_vs_h1_change_pct": _nan_to_zero(kwh_h2_vs_h1_change_pct),
    "hot_commercial_reading_count": int(hot_commercial_reading_count),
    "hot_commercial_mean_kwh": _nan_to_zero(hot_commercial_mean_kwh),
    "kwh_median": _nan_to_zero(kwh_median),
    "kwh_std": _nan_to_zero(kwh_std),
    "temperature_mean": _nan_to_zero(temperature_mean),
    "temperature_missing_count": int(temperature_missing_count),
    "commercial_temp_kwh_corr": _nan_to_zero(commercial_temp_kwh_corr),
    "kwh_peak": _nan_to_zero(kwh_peak),
    "kwh_off_peak": _nan_to_zero(kwh_off_peak),
    "peak_kwh_share_pct": _nan_to_zero(peak_kwh_share_pct),
    "unique_meter_count": int(unique_meter_count),
    "highest_use_meter_kwh": _nan_to_zero(highest_use_meter_kwh)
}

# Write findings to JSON (no NaN allowed)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(findings, f, ensure_ascii=False)
