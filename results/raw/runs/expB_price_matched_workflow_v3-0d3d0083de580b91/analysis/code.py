import json
import math
import os

import pandas as pd

INPUT_PATH = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
OUTPUT_PATH = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")


def finite_number(value):
    """Convert to a plain Python float; fall back to 0.0 if not finite."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return 0.0
    return v if math.isfinite(v) else 0.0


# --- Load cleaned data ---
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

energy = df["energy_kwh"]

# --- q1: Overall aggregation ---
total_kwh = energy.sum()
reading_count = int(len(df))
mean_kwh_per_reading = total_kwh / reading_count if reading_count else 0.0

# --- q2: Totals per building type ---
by_type = df.groupby("building_type")["energy_kwh"].sum()
kwh_residential = by_type.get("Residential", 0.0)
kwh_commercial = by_type.get("Commercial", 0.0)
kwh_industrial = by_type.get("Industrial", 0.0)

# --- q3: Quarterly totals (calendar quarters of 2024) ---
month = df["reading_date"].dt.month
kwh_q1 = energy[month.between(1, 3)].sum()
kwh_q2 = energy[month.between(4, 6)].sum()
kwh_q3 = energy[month.between(7, 9)].sum()
kwh_q4 = energy[month.between(10, 12)].sum()

# --- q4: Half-year totals and percentage change ---
kwh_h1 = energy[month.between(1, 6)].sum()
kwh_h2 = energy[month.between(7, 12)].sum()
kwh_h2_vs_h1_change_pct = (kwh_h2 - kwh_h1) / kwh_h1 * 100 if kwh_h1 != 0 else 0.0

# --- q5: Commercial load on hot days (temperature_c >= 25, non-missing) ---
hot_commercial = df[
    (df["building_type"] == "Commercial")
    & (df["temperature_c"].notna())
    & (df["temperature_c"] >= 25)
]
hot_commercial_reading_count = int(len(hot_commercial))
hot_commercial_mean_kwh = (
    hot_commercial["energy_kwh"].mean() if hot_commercial_reading_count else 0.0
)

# --- q6: Distribution summary ---
kwh_median = energy.median()
kwh_std = energy.std(ddof=1)  # sample standard deviation (n - 1)
temp_valid = df["temperature_c"].dropna()
temperature_mean = temp_valid.mean() if len(temp_valid) else 0.0
temperature_missing_count = int(df["temperature_c"].isna().sum())

commercial_with_temp = df[
    (df["building_type"] == "Commercial") & (df["temperature_c"].notna())
]
if len(commercial_with_temp) >= 2:
    commercial_temp_kwh_corr = commercial_with_temp["temperature_c"].corr(
        commercial_with_temp["energy_kwh"], method="pearson"
    )
else:
    commercial_temp_kwh_corr = 0.0

# --- q7: Tariff and meter usage ---
by_tariff = df.groupby("tariff")["energy_kwh"].sum()
kwh_peak = by_tariff.get("peak", 0.0)
kwh_off_peak = by_tariff.get("off-peak", 0.0)
peak_kwh_share_pct = kwh_peak / total_kwh * 100 if total_kwh != 0 else 0.0
unique_meter_count = int(df["meter_id"].nunique())
by_meter = df.groupby("meter_id")["energy_kwh"].sum()
highest_use_meter_kwh = by_meter.max() if len(by_meter) else 0.0

# --- Assemble findings (flat object, finite numbers, full precision) ---
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

findings = {key: finite_number(value) for key, value in findings.items()}

os.makedirs(os.environ["OUTPUT_DIR"], exist_ok=True)
with open(OUTPUT_PATH, "w") as f:
    json.dump(findings, f)
