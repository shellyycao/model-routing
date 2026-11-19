import json
import math
import os

import pandas as pd


REQUIRED_KEYS = [
    "total_kwh", "reading_count", "mean_kwh_per_reading",
    "kwh_residential", "kwh_commercial", "kwh_industrial",
    "kwh_q1", "kwh_q2", "kwh_q3", "kwh_q4",
    "kwh_h1", "kwh_h2", "kwh_h2_vs_h1_change_pct",
    "hot_commercial_reading_count", "hot_commercial_mean_kwh",
    "kwh_median", "kwh_std", "temperature_mean", "temperature_missing_count",
    "commercial_temp_kwh_corr",
    "kwh_peak", "kwh_off_peak", "peak_kwh_share_pct",
    "unique_meter_count", "highest_use_meter_kwh",
]


def finite(value):
    """Return a finite float, falling back to 0.0 for NaN/inf (degenerate inputs only)."""
    v = float(value)
    return v if math.isfinite(v) else 0.0


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    df = pd.read_csv(input_path)
    df["reading_date"] = pd.to_datetime(df["reading_date"], format="%Y-%m-%d", errors="coerce")
    df["energy_kwh"] = pd.to_numeric(df["energy_kwh"], errors="coerce")
    df["temperature_c"] = pd.to_numeric(df["temperature_c"], errors="coerce")

    findings = {}

    # q1: overall aggregation
    total_kwh = float(df["energy_kwh"].sum())
    reading_count = int(len(df))
    findings["total_kwh"] = total_kwh
    findings["reading_count"] = reading_count
    findings["mean_kwh_per_reading"] = finite(total_kwh / reading_count) if reading_count else 0.0

    # q2: totals per building type
    by_type = df.groupby("building_type")["energy_kwh"].sum()
    findings["kwh_residential"] = finite(by_type.get("Residential", 0.0))
    findings["kwh_commercial"] = finite(by_type.get("Commercial", 0.0))
    findings["kwh_industrial"] = finite(by_type.get("Industrial", 0.0))

    # q3: quarterly totals for calendar year 2024
    df_2024 = df[df["reading_date"].dt.year == 2024]
    by_quarter = df_2024.groupby(df_2024["reading_date"].dt.quarter)["energy_kwh"].sum()
    findings["kwh_q1"] = finite(by_quarter.get(1, 0.0))
    findings["kwh_q2"] = finite(by_quarter.get(2, 0.0))
    findings["kwh_q3"] = finite(by_quarter.get(3, 0.0))
    findings["kwh_q4"] = finite(by_quarter.get(4, 0.0))

    # q4: half-year totals and percentage change (H2 vs H1)
    month = df_2024["reading_date"].dt.month
    kwh_h1 = float(df_2024.loc[month <= 6, "energy_kwh"].sum())
    kwh_h2 = float(df_2024.loc[month >= 7, "energy_kwh"].sum())
    findings["kwh_h1"] = kwh_h1
    findings["kwh_h2"] = kwh_h2
    findings["kwh_h2_vs_h1_change_pct"] = finite((kwh_h2 - kwh_h1) / kwh_h1 * 100.0) if kwh_h1 != 0 else 0.0

    # q5: commercial load on hot days (temperature_c >= 25, non-missing)
    hot_comm = df[(df["building_type"] == "Commercial") & df["temperature_c"].notna() & (df["temperature_c"] >= 25)]
    findings["hot_commercial_reading_count"] = int(len(hot_comm))
    findings["hot_commercial_mean_kwh"] = finite(hot_comm["energy_kwh"].mean()) if len(hot_comm) else 0.0

    # q6: distribution summary
    findings["kwh_median"] = finite(df["energy_kwh"].median())
    findings["kwh_std"] = finite(df["energy_kwh"].std(ddof=1)) if reading_count >= 2 else 0.0
    temp_valid = df["temperature_c"].dropna()
    findings["temperature_mean"] = finite(temp_valid.mean()) if len(temp_valid) else 0.0
    findings["temperature_missing_count"] = int(df["temperature_c"].isna().sum())
    comm = df[(df["building_type"] == "Commercial") & df["temperature_c"].notna()]
    if len(comm) >= 2 and comm["temperature_c"].std(ddof=1) > 0 and comm["energy_kwh"].std(ddof=1) > 0:
        findings["commercial_temp_kwh_corr"] = finite(comm["temperature_c"].corr(comm["energy_kwh"], method="pearson"))
    else:
        findings["commercial_temp_kwh_corr"] = 0.0

    # q7: tariff and meter usage
    by_tariff = df.groupby("tariff")["energy_kwh"].sum()
    kwh_peak = float(by_tariff.get("peak", 0.0))
    kwh_off_peak = float(by_tariff.get("off-peak", 0.0))
    findings["kwh_peak"] = kwh_peak
    findings["kwh_off_peak"] = kwh_off_peak
    findings["peak_kwh_share_pct"] = finite(kwh_peak / total_kwh * 100.0) if total_kwh != 0 else 0.0
    findings["unique_meter_count"] = int(df["meter_id"].nunique())
    by_meter = df.groupby("meter_id")["energy_kwh"].sum()
    findings["highest_use_meter_kwh"] = finite(by_meter.max()) if len(by_meter) else 0.0

    # Contract check: every required key present, numeric and finite.
    for key in REQUIRED_KEYS:
        if key not in findings:
            raise KeyError(f"Missing metric: {key}")
        value = findings[key]
        if isinstance(value, float) and not math.isfinite(value):
            findings[key] = 0.0
    findings = {key: findings[key] for key in REQUIRED_KEYS}

    with open(output_path, "w") as f:
        json.dump(findings, f, indent=2, allow_nan=False)


if __name__ == "__main__":
    main()
