# 2024 Smart-Meter Electricity Consumption Report

Analysis of 1,428 smart-meter readings across 2024 shows total consumption of 1,207,700 kWh at a mean of 846 kWh per reading. Industrial sites dominate usage, Q4 was the highest-consumption quarter, and the second half of the year grew 4.7% over the first. Peak and off-peak tariffs are nearly balanced, and a moderate negative correlation exists between temperature and commercial energy use.

## Key findings
- [q1] Across all 1,428 readings in the dataset, total electricity consumption reached 1,207,700 kWh, yielding a mean of approximately 845.7 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Industrial buildings consumed the most electricity at 995,362 kWh (82.4% of total), followed by Commercial at 196,367 kWh (16.3%) and Residential at just 15,971 kWh (1.3%).
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
  - Derived share(kwh_industrial, total_kwh): 82.4
  - Derived share(kwh_commercial, total_kwh): 16.3
  - Derived share(kwh_residential, total_kwh): 1.3
- [q3] Q4 (Oct–Dec) was the highest-consumption quarter at 352,882 kWh, followed by Q1 (319,678 kWh), Q2 (270,277 kWh), and Q3 (264,863 kWh) as the lowest.
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Second-half consumption (617,745 kWh, Jul–Dec) exceeded first-half consumption (589,955 kWh, Jan–Jun) by 4.7%, indicating a modest year-on-year increase in the latter part of 2024.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
  - Derived difference(kwh_h2, kwh_h1): 27789.9
- [q5] On hot days (temperature ≥ 25 °C), 18 commercial readings were recorded with a mean consumption of 417.0 kWh per reading, suggesting moderate but not extreme load uplift under high-temperature conditions.
  - Reported values: hot_commercial_reading_count=18.0, hot_commercial_mean_kwh=416.9894444444444
- [q6] The median consumption across all readings was 406.8 kWh with a sample standard deviation of 913.4 kWh, indicating a right-skewed distribution. The mean recorded temperature was 11.8 °C, with 182 readings missing temperature data. For commercial sites with valid temperatures, the Pearson correlation between temperature and consumption was −0.64, suggesting that higher temperatures are associated with lower commercial energy use.
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.794462279293738, temperature_missing_count=182.0, commercial_temp_kwh_corr=-0.6386877924578244
- [q7] Off-peak tariff consumption (608,076 kWh) marginally exceeded peak tariff consumption (599,624 kWh), with peak accounting for 49.7% of total usage. The dataset covers 12 distinct meters; the highest single-meter total was 252,241 kWh.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251175, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak

## Limitations
- Both the cleaning and analysis pipeline stages reported validation failures; results should be treated as provisional until the underlying data quality issues are investigated and resolved.
- 182 readings (approximately 12.7% of the dataset) are missing temperature data, which may bias the temperature-related statistics and the commercial temperature–consumption correlation.
- Only 18 hot-day commercial readings (temperature ≥ 25 °C) were available, making the hot-day mean highly sensitive to individual outliers and limiting statistical confidence.
- The dataset contains only 12 distinct meters, which restricts the generalisability of per-meter and building-type findings.
- The analysis assumes the cleaned dataset accurately reflects the original smart-meter export; any errors introduced or not corrected during the failed cleaning stage will propagate to all metrics.

## Conclusion
Industrial sites drive the overwhelming majority of electricity consumption, and demand is highest in Q4 and lowest in Q3. Second-half usage grew modestly (+4.7%) relative to the first half. Peak and off-peak loads are nearly equal, and a negative temperature–consumption relationship is evident for commercial buildings. Given the validation failures in both prior pipeline stages, these findings should be confirmed once data quality issues are addressed before informing operational or procurement decisions.
