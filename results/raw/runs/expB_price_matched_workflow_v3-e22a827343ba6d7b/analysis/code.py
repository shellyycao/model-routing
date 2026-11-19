import os
import json
import pandas as pd
import numpy as np

# --- Load cleaned data ---
input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
df = pd.read_csv(input_path, parse_dates=["reading_date"])

# Ensure correct dtypes
df["energy_kwh"] = pd.to_numeric(df["energy_kwh"], errors="coerce")
df["temperature_c"] = pd.to_numeric(df["temperature_c"], errors="coerce")

# --- Q1: Overall aggregation ---
total_kwh = float(df["energy_kwh"].sum())
reading_count = int(len(df))
mean_kwh_per_reading = total_kwh / reading_count

# --- Q2: Building type totals ---
bt_totals = df.groupby("building_type")["energy_kwh"].sum()
kwh_residential = float(bt_totals.get("Residential", 0.0))
kwh_commercial = float(bt_totals.get("Commercial", 0.0))
kwh_industrial = float(bt_totals.get("Industrial", 0.0))

# --- Q3: Quarterly trend ---
df["quarter"] = df["reading_date"].dt.quarter
q_totals = df.groupby("quarter")["energy_kwh"].sum()
kwh_q1 = float(q_totals.get(1, 0.0))
kwh_q2 = float(q_totals.get(2, 0.0))
kwh_q3 = float(q_totals.get(3, 0.0))
kwh_q4 = float(q_totals.get(4, 0.0))

# --- Q4: Half-year change ---
df["month"] = df["reading_date"].dt.month
kwh_h1 = float(df[df["month"] <= 6]["energy_kwh"].sum())
kwh_h2 = float(df[df["month"] >= 7]["energy_kwh"].sum())
kwh_h2_vs_h1_change_pct = (kwh_h2 - kwh_h1) / kwh_h1 * 100

# --- Q5: Hot-day commercial load ---
hot_commercial = df[
    (df["building_type"] == "Commercial") &
    (df["temperature_c"].notna()) &
    (df["temperature_c"] >= 25)
]
hot_commercial_reading_count = int(len(hot_commercial))
hot_commercial_mean_kwh = float(hot_commercial["energy_kwh"].mean()) if hot_commercial_reading_count > 0 else 0.0

# --- Q6: Distribution summary ---
kwh_median = float(df["energy_kwh"].median())
kwh_std = float(df["energy_kwh"].std(ddof=1))

temp_valid = df[df["temperature_c"].notna()]
temperature_mean = float(temp_valid["temperature_c"].mean())
temperature_missing_count = int(df["temperature_c"].isna().sum())

commercial_with_temp = df[
    (df["building_type"] == "Commercial") &
    (df["temperature_c"].notna())
]
commercial_temp_kwh_corr = float(
    commercial_with_temp["temperature_c"].corr(commercial_with_temp["energy_kwh"])
)

# --- Q7: Tariff and meter usage ---
tariff_totals = df.groupby("tariff")["energy_kwh"].sum()
kwh_peak = float(tariff_totals.get("peak", 0.0))
kwh_off_peak = float(tariff_totals.get("off-peak", 0.0))
peak_kwh_share_pct = kwh_peak / total_kwh * 100

unique_meter_count = int(df["meter_id"].nunique())
meter_totals = df.groupby("meter_id")["energy_kwh"].sum()
highest_use_meter_kwh = float(meter_totals.max())

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
    "highest_use_meter_kwh": highest_use_meter_kwh,
}

# Validate all values are finite numbers
for k, v in findings.items():
    if not isinstance(v, (int, float)):
        raise ValueError(f"Non-numeric value for key '{k}': {v}")
    if not np.isfinite(v):
        raise ValueError(f"Non-finite value for key '{k}': {v}")

# --- Write output ---
output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")
with open(output_path, "w") as f:
    json.dump(findings, f)

print("findings.json written successfully.")
print(json.dumps(findings, indent=2))
