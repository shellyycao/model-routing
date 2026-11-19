"""Analysis stage: compute energy-consumption metrics from cleaned.csv."""

import json
import os

import pandas as pd


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    df = pd.read_csv(input_path)
    # reading_date is ISO YYYY-MM-DD after cleaning; empty temperature_c cells -> NaN.
    dates = pd.to_datetime(df["reading_date"], format="%Y-%m-%d")
    energy = df["energy_kwh"].astype(float)
    temp = df["temperature_c"].astype(float)
    btype = df["building_type"]
    tariff = df["tariff"]

    findings = {}

    # q1: overall aggregation
    total_kwh = float(energy.sum())
    reading_count = int(len(df))
    findings["total_kwh"] = total_kwh
    findings["reading_count"] = reading_count
    findings["mean_kwh_per_reading"] = total_kwh / reading_count

    # q2: totals per building type
    by_type = energy.groupby(btype).sum()
    findings["kwh_residential"] = float(by_type.get("Residential", 0.0))
    findings["kwh_commercial"] = float(by_type.get("Commercial", 0.0))
    findings["kwh_industrial"] = float(by_type.get("Industrial", 0.0))

    # q3: quarterly trend (calendar quarters of 2024)
    by_quarter = energy.groupby(dates.dt.quarter).sum()
    findings["kwh_q1"] = float(by_quarter.get(1, 0.0))
    findings["kwh_q2"] = float(by_quarter.get(2, 0.0))
    findings["kwh_q3"] = float(by_quarter.get(3, 0.0))
    findings["kwh_q4"] = float(by_quarter.get(4, 0.0))

    # q4: half-year change (Jan-Jun vs Jul-Dec)
    month = dates.dt.month
    kwh_h1 = float(energy[month <= 6].sum())
    kwh_h2 = float(energy[month >= 7].sum())
    findings["kwh_h1"] = kwh_h1
    findings["kwh_h2"] = kwh_h2
    findings["kwh_h2_vs_h1_change_pct"] = (kwh_h2 - kwh_h1) / kwh_h1 * 100.0

    # q5: hot-day commercial load (temperature_c >= 25, non-missing)
    hot_mask = (btype == "Commercial") & temp.notna() & (temp >= 25.0)
    hot_energy = energy[hot_mask]
    findings["hot_commercial_reading_count"] = int(hot_mask.sum())
    findings["hot_commercial_mean_kwh"] = float(hot_energy.mean())

    # q6: distribution summary
    findings["kwh_median"] = float(energy.median())
    findings["kwh_std"] = float(energy.std(ddof=1))
    findings["temperature_mean"] = float(temp.mean())
    findings["temperature_missing_count"] = int(temp.isna().sum())
    comm_mask = (btype == "Commercial") & temp.notna()
    findings["commercial_temp_kwh_corr"] = float(
        energy[comm_mask].corr(temp[comm_mask])
    )

    # q7: tariff and meter usage
    by_tariff = energy.groupby(tariff).sum()
    kwh_peak = float(by_tariff.get("peak", 0.0))
    kwh_off_peak = float(by_tariff.get("off-peak", 0.0))
    findings["kwh_peak"] = kwh_peak
    findings["kwh_off_peak"] = kwh_off_peak
    findings["peak_kwh_share_pct"] = kwh_peak / total_kwh * 100.0
    findings["unique_meter_count"] = int(df["meter_id"].nunique())
    findings["highest_use_meter_kwh"] = float(
        energy.groupby(df["meter_id"]).sum().max()
    )

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(findings, f, indent=2, allow_nan=False)


if __name__ == "__main__":
    main()
