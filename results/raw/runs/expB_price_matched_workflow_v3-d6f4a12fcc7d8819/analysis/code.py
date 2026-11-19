import json
import os

import numpy as np
import pandas as pd


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    df = pd.read_csv(input_path)
    df["reading_date"] = pd.to_datetime(df["reading_date"], format="%Y-%m-%d")
    df["energy_kwh"] = df["energy_kwh"].astype(float)
    df["temperature_c"] = df["temperature_c"].astype(float)

    findings = {}

    # q1: overall aggregation
    total_kwh = float(df["energy_kwh"].sum())
    reading_count = int(len(df))
    findings["total_kwh"] = total_kwh
    findings["reading_count"] = reading_count
    findings["mean_kwh_per_reading"] = total_kwh / reading_count

    # q2: totals per building type
    by_type = df.groupby("building_type")["energy_kwh"].sum()
    findings["kwh_residential"] = float(by_type.get("Residential", 0.0))
    findings["kwh_commercial"] = float(by_type.get("Commercial", 0.0))
    findings["kwh_industrial"] = float(by_type.get("Industrial", 0.0))

    # q3: quarterly totals (calendar quarters of 2024)
    quarter = df["reading_date"].dt.quarter
    qsum = df.groupby(quarter)["energy_kwh"].sum()
    for q, key in zip((1, 2, 3, 4), ("kwh_q1", "kwh_q2", "kwh_q3", "kwh_q4")):
        findings[key] = float(qsum.get(q, 0.0))

    # q4: half-year totals and percentage change H2 vs H1
    month = df["reading_date"].dt.month
    kwh_h1 = float(df.loc[month <= 6, "energy_kwh"].sum())
    kwh_h2 = float(df.loc[month >= 7, "energy_kwh"].sum())
    findings["kwh_h1"] = kwh_h1
    findings["kwh_h2"] = kwh_h2
    findings["kwh_h2_vs_h1_change_pct"] = (kwh_h2 - kwh_h1) / kwh_h1 * 100.0

    # q5: hot-day commercial load (temperature_c >= 25, non-missing)
    hot_comm = df[
        (df["building_type"] == "Commercial")
        & df["temperature_c"].notna()
        & (df["temperature_c"] >= 25.0)
    ]
    findings["hot_commercial_reading_count"] = int(len(hot_comm))
    findings["hot_commercial_mean_kwh"] = float(hot_comm["energy_kwh"].mean())

    # q6: distribution summary
    findings["kwh_median"] = float(df["energy_kwh"].median())
    findings["kwh_std"] = float(df["energy_kwh"].std(ddof=1))
    findings["temperature_mean"] = float(df["temperature_c"].mean())
    findings["temperature_missing_count"] = int(df["temperature_c"].isna().sum())
    comm_valid = df[
        (df["building_type"] == "Commercial") & df["temperature_c"].notna()
    ]
    findings["commercial_temp_kwh_corr"] = float(
        comm_valid["temperature_c"].corr(comm_valid["energy_kwh"], method="pearson")
    )

    # q7: tariff and meter usage
    by_tariff = df.groupby("tariff")["energy_kwh"].sum()
    kwh_peak = float(by_tariff.get("peak", 0.0))
    kwh_off_peak = float(by_tariff.get("off-peak", 0.0))
    findings["kwh_peak"] = kwh_peak
    findings["kwh_off_peak"] = kwh_off_peak
    findings["peak_kwh_share_pct"] = kwh_peak / total_kwh * 100.0
    findings["unique_meter_count"] = int(df["meter_id"].nunique())
    findings["highest_use_meter_kwh"] = float(
        df.groupby("meter_id")["energy_kwh"].sum().max()
    )

    # Safety: every value must be a finite number
    for key, value in findings.items():
        if isinstance(value, float) and not np.isfinite(value):
            raise ValueError(f"Non-finite value computed for metric '{key}'")

    with open(output_path, "w") as f:
        json.dump(findings, f)


if __name__ == "__main__":
    main()
