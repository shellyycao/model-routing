import json
import os

import numpy as np
import pandas as pd


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    df = pd.read_csv(input_path)
    df["reading_date"] = pd.to_datetime(df["reading_date"])

    findings = {}

    # q1: overall aggregation
    total_kwh = float(df["energy_kwh"].sum())
    reading_count = int(len(df))
    findings["total_kwh"] = total_kwh
    findings["reading_count"] = reading_count
    findings["mean_kwh_per_reading"] = total_kwh / reading_count

    # q2: total energy per building type
    by_building = df.groupby("building_type")["energy_kwh"].sum()
    findings["kwh_residential"] = float(by_building.get("Residential", 0.0))
    findings["kwh_commercial"] = float(by_building.get("Commercial", 0.0))
    findings["kwh_industrial"] = float(by_building.get("Industrial", 0.0))

    # q3: quarterly totals for calendar year 2024
    df_2024 = df[df["reading_date"].dt.year == 2024]
    by_quarter = df_2024.groupby(df_2024["reading_date"].dt.quarter)["energy_kwh"].sum()
    findings["kwh_q1"] = float(by_quarter.get(1, 0.0))
    findings["kwh_q2"] = float(by_quarter.get(2, 0.0))
    findings["kwh_q3"] = float(by_quarter.get(3, 0.0))
    findings["kwh_q4"] = float(by_quarter.get(4, 0.0))

    # q4: half-year totals and percentage change H2 vs H1
    month = df_2024["reading_date"].dt.month
    kwh_h1 = float(df_2024.loc[month <= 6, "energy_kwh"].sum())
    kwh_h2 = float(df_2024.loc[month >= 7, "energy_kwh"].sum())
    findings["kwh_h1"] = kwh_h1
    findings["kwh_h2"] = kwh_h2
    findings["kwh_h2_vs_h1_change_pct"] = (kwh_h2 - kwh_h1) / kwh_h1 * 100.0 if kwh_h1 != 0 else 0.0

    # q5: commercial readings on hot days (temperature_c >= 25, non-missing)
    hot_commercial = df[
        (df["building_type"] == "Commercial")
        & (df["temperature_c"].notna())
        & (df["temperature_c"] >= 25)
    ]
    findings["hot_commercial_reading_count"] = int(len(hot_commercial))
    findings["hot_commercial_mean_kwh"] = (
        float(hot_commercial["energy_kwh"].mean()) if len(hot_commercial) > 0 else 0.0
    )

    # q6: distribution summaries
    findings["kwh_median"] = float(df["energy_kwh"].median())
    findings["kwh_std"] = float(df["energy_kwh"].std(ddof=1))
    temp_valid = df["temperature_c"].dropna()
    findings["temperature_mean"] = float(temp_valid.mean())
    findings["temperature_missing_count"] = int(df["temperature_c"].isna().sum())
    commercial_valid = df[
        (df["building_type"] == "Commercial") & (df["temperature_c"].notna())
    ]
    if len(commercial_valid) > 1:
        corr = float(
            commercial_valid["temperature_c"].corr(
                commercial_valid["energy_kwh"], method="pearson"
            )
        )
    else:
        corr = 0.0
    findings["commercial_temp_kwh_corr"] = corr

    # q7: tariff and meter usage
    by_tariff = df.groupby("tariff")["energy_kwh"].sum()
    kwh_peak = float(by_tariff.get("peak", 0.0))
    kwh_off_peak = float(by_tariff.get("off-peak", 0.0))
    findings["kwh_peak"] = kwh_peak
    findings["kwh_off_peak"] = kwh_off_peak
    findings["peak_kwh_share_pct"] = kwh_peak / total_kwh * 100.0 if total_kwh != 0 else 0.0
    findings["unique_meter_count"] = int(df["meter_id"].nunique())
    findings["highest_use_meter_kwh"] = float(
        df.groupby("meter_id")["energy_kwh"].sum().max()
    )

    # safety: guarantee every value is a finite number
    for key, value in findings.items():
        value = float(value)
        if not np.isfinite(value):
            value = 0.0
        findings[key] = value

    with open(output_path, "w") as f:
        json.dump(findings, f)


if __name__ == "__main__":
    main()
