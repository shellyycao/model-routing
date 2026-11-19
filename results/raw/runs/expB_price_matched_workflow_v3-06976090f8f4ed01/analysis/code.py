import json
import math
import os

import numpy as np
import pandas as pd


def finite_number(value, fallback=0.0):
    """Convert a value to a finite Python float; fall back if NaN/inf/invalid."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return fallback
    if math.isnan(v) or math.isinf(v):
        return fallback
    return v


def main():
    input_path = os.path.join(os.environ["INPUT_DIR"], "cleaned.csv")
    output_path = os.path.join(os.environ["OUTPUT_DIR"], "findings.json")

    df = pd.read_csv(input_path)

    # Ensure correct dtypes (data is already cleaned; this is defensive).
    df["reading_date"] = pd.to_datetime(df["reading_date"], format="%Y-%m-%d", errors="coerce")
    df["energy_kwh"] = pd.to_numeric(df["energy_kwh"], errors="coerce")
    df["temperature_c"] = pd.to_numeric(df["temperature_c"], errors="coerce")

    findings = {}

    # q1: Overall aggregation
    total_kwh = finite_number(df["energy_kwh"].sum())
    reading_count = int(len(df))
    findings["total_kwh"] = total_kwh
    findings["reading_count"] = reading_count
    findings["mean_kwh_per_reading"] = (
        finite_number(total_kwh / reading_count) if reading_count > 0 else 0.0
    )

    # q2: Total energy per building type
    by_type = df.groupby("building_type")["energy_kwh"].sum()
    findings["kwh_residential"] = finite_number(by_type.get("Residential", 0.0))
    findings["kwh_commercial"] = finite_number(by_type.get("Commercial", 0.0))
    findings["kwh_industrial"] = finite_number(by_type.get("Industrial", 0.0))

    # q3: Quarterly trend (calendar quarters of 2024)
    quarter = df["reading_date"].dt.quarter
    qsum = df.groupby(quarter)["energy_kwh"].sum()
    for q, key in ((1, "kwh_q1"), (2, "kwh_q2"), (3, "kwh_q3"), (4, "kwh_q4")):
        findings[key] = finite_number(qsum.get(q, 0.0))

    # q4: Half-year change (Jan-Jun vs Jul-Dec)
    month = df["reading_date"].dt.month
    kwh_h1 = finite_number(df.loc[month <= 6, "energy_kwh"].sum())
    kwh_h2 = finite_number(df.loc[month >= 7, "energy_kwh"].sum())
    findings["kwh_h1"] = kwh_h1
    findings["kwh_h2"] = kwh_h2
    findings["kwh_h2_vs_h1_change_pct"] = (
        finite_number((kwh_h2 - kwh_h1) / kwh_h1 * 100.0) if kwh_h1 != 0.0 else 0.0
    )

    # q5: Hot-day commercial load (Commercial, non-missing temp >= 25 C)
    hot_mask = (
        (df["building_type"] == "Commercial")
        & df["temperature_c"].notna()
        & (df["temperature_c"] >= 25)
    )
    hot_comm = df.loc[hot_mask]
    findings["hot_commercial_reading_count"] = int(len(hot_comm))
    findings["hot_commercial_mean_kwh"] = (
        finite_number(hot_comm["energy_kwh"].mean()) if len(hot_comm) > 0 else 0.0
    )

    # q6: Distribution summary
    findings["kwh_median"] = finite_number(df["energy_kwh"].median())
    findings["kwh_std"] = finite_number(df["energy_kwh"].std(ddof=1))
    temp_valid = df["temperature_c"].dropna()
    findings["temperature_mean"] = (
        finite_number(temp_valid.mean()) if len(temp_valid) > 0 else 0.0
    )
    findings["temperature_missing_count"] = int(df["temperature_c"].isna().sum())
    comm_valid = df.loc[
        (df["building_type"] == "Commercial") & df["temperature_c"].notna()
    ]
    if (
        len(comm_valid) >= 2
        and comm_valid["temperature_c"].nunique() > 1
        and comm_valid["energy_kwh"].nunique() > 1
    ):
        corr = finite_number(
            comm_valid["temperature_c"].corr(comm_valid["energy_kwh"], method="pearson")
        )
    else:
        corr = 0.0
    findings["commercial_temp_kwh_corr"] = corr

    # q7: Tariff and meter usage
    by_tariff = df.groupby("tariff")["energy_kwh"].sum()
    kwh_peak = finite_number(by_tariff.get("peak", 0.0))
    kwh_off_peak = finite_number(by_tariff.get("off-peak", 0.0))
    findings["kwh_peak"] = kwh_peak
    findings["kwh_off_peak"] = kwh_off_peak
    findings["peak_kwh_share_pct"] = (
        finite_number(kwh_peak / total_kwh * 100.0) if total_kwh != 0.0 else 0.0
    )
    findings["unique_meter_count"] = int(df["meter_id"].nunique())
    by_meter = df.groupby("meter_id")["energy_kwh"].sum()
    findings["highest_use_meter_kwh"] = (
        finite_number(by_meter.max()) if len(by_meter) > 0 else 0.0
    )

    # Guarantee a flat object of finite JSON numbers only.
    clean_findings = {}
    for key, value in findings.items():
        if isinstance(value, bool):
            clean_findings[key] = finite_number(value)
        elif isinstance(value, int):
            clean_findings[key] = value
        else:
            clean_findings[key] = finite_number(value)

    os.makedirs(os.environ["OUTPUT_DIR"], exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(clean_findings, f, indent=2)


if __name__ == "__main__":
    main()
