import json
import os

import numpy as np
import pandas as pd

input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

# Load cleaned data, enforcing expected dtypes.
df = pd.read_csv(
    input_path,
    dtype={
        "reading_id": str,
        "meter_id": str,
        "building_type": str,
        "tariff": str,
    },
)
df["reading_date"] = pd.to_datetime(df["reading_date"], format="%Y-%m-%d")
df["energy_kwh"] = pd.to_numeric(df["energy_kwh"], errors="coerce")
df["temperature_c"] = pd.to_numeric(df["temperature_c"], errors="coerce")

energy = df["energy_kwh"]

# q1: overall aggregation
total_kwh = float(energy.sum())
reading_count = int(len(df))
mean_kwh_per_reading = total_kwh / reading_count if reading_count else 0.0

# q2: totals per building type
by_type = df.groupby("building_type")["energy_kwh"].sum()
kwh_residential = float(by_type.get("Residential", 0.0))
kwh_commercial = float(by_type.get("Commercial", 0.0))
kwh_industrial = float(by_type.get("Industrial", 0.0))

# q3: quarterly totals for calendar year 2024
month = df["reading_date"].dt.month
quarter = ((month - 1) // 3) + 1
by_quarter = df.groupby(quarter)["energy_kwh"].sum()
kwh_q1 = float(by_quarter.get(1, 0.0))
kwh_q2 = float(by_quarter.get(2, 0.0))
kwh_q3 = float(by_quarter.get(3, 0.0))
kwh_q4 = float(by_quarter.get(4, 0.0))

# q4: half-year totals and percentage change H2 vs H1
kwh_h1 = float(energy[month.between(1, 6)].sum())
kwh_h2 = float(energy[month.between(7, 12)].sum())
kwh_h2_vs_h1_change_pct = (kwh_h2 - kwh_h1) / kwh_h1 * 100 if kwh_h1 else 0.0

# q5: commercial load on hot days (temperature >= 25 C, non-missing)
hot_mask = (
    (df["building_type"] == "Commercial")
    & df["temperature_c"].notna()
    & (df["temperature_c"] >= 25)
)
hot = df.loc[hot_mask, "energy_kwh"]
hot_commercial_reading_count = int(hot.shape[0])
hot_commercial_mean_kwh = float(hot.mean()) if hot_commercial_reading_count else 0.0

# q6: distribution summary
kwh_median = float(energy.median())
kwh_std = float(energy.std(ddof=1))
temp = df["temperature_c"]
temperature_mean = float(temp.dropna().mean())
temperature_missing_count = int(temp.isna().sum())

comm = df.loc[(df["building_type"] == "Commercial") & df["temperature_c"].notna(),
              ["temperature_c", "energy_kwh"]]
if (
    len(comm) >= 2
    and comm["temperature_c"].std(ddof=1) > 0
    and comm["energy_kwh"].std(ddof=1) > 0
):
    commercial_temp_kwh_corr = float(comm["temperature_c"].corr(comm["energy_kwh"], method="pearson"))
else:
    commercial_temp_kwh_corr = 0.0

# q7: tariff and meter usage
by_tariff = df.groupby("tariff")["energy_kwh"].sum()
kwh_peak = float(by_tariff.get("peak", 0.0))
kwh_off_peak = float(by_tariff.get("off-peak", 0.0))
peak_kwh_share_pct = kwh_peak / total_kwh * 100 if total_kwh else 0.0
unique_meter_count = int(df["meter_id"].nunique())
meter_totals = df.groupby("meter_id")["energy_kwh"].sum()
highest_use_meter_kwh = float(meter_totals.max()) if len(meter_totals) else 0.0

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

# Safety: guarantee every value is a finite plain Python number.
for key, value in findings.items():
    if value is None or not np.isfinite(float(value)):
        findings[key] = 0.0

with open(output_path, "w") as f:
    json.dump(findings, f, indent=2)
