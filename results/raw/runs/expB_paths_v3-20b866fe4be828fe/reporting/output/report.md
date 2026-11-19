# 2024 Smart-Meter Electricity Consumption Report

Analysis of 1,428 smart-meter readings across 2024 shows total consumption of 1,207,700 kWh. Industrial buildings dominate usage, Q4 was the highest-consumption quarter, and the second half of the year grew 4.7% over the first. Peak and off-peak tariffs are nearly balanced, and a moderate negative correlation exists between temperature and commercial energy use.

## Key findings
- [q1] Across all 1,428 readings, total electricity consumption reached 1,207,700 kWh, yielding a mean of 845.7 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Industrial buildings accounted for 995,362 kWh (the vast majority of total consumption), followed by Commercial at 196,367 kWh and Residential at 15,971 kWh. Industrial usage alone represents approximately 82.4% of the total.
  - Reported values: kwh_residential=15970.650000000001, kwh_commercial=196367.15000000002, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
  - Derived share(kwh_industrial, total_kwh): 82.4
- [q3] Q4 was the highest-consumption quarter at 352,882 kWh, followed by Q1 (319,678 kWh), Q2 (270,277 kWh), and Q3 (264,863 kWh), indicating elevated demand in winter months and a mid-year trough in summer.
  - Reported values: kwh_q1=319677.67000000004, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81000000006
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Second-half consumption (617,745 kWh) exceeded first-half consumption (589,955 kWh), representing an increase of 4.7% half-on-half.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
  - Derived difference(kwh_h2, kwh_h1): 27789.9
- [q5] On hot days (temperature ≥ 25 °C), 19 commercial readings were recorded with a mean consumption of 415.3 kWh per reading, suggesting moderate but notable load during high-temperature periods.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
- [q6] The median reading was 406.8 kWh with a standard deviation of 913.4 kWh, indicating a right-skewed distribution. Mean temperature across valid readings was 11.6 °C; 62 readings had missing temperature data. For commercial buildings, the Pearson correlation between temperature and energy use was -0.64, a moderate negative relationship suggesting higher commercial consumption in cooler conditions.
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636239865442
- [q7] Off-peak tariff consumption (608,076 kWh) marginally exceeded peak tariff consumption (599,624 kWh); peak usage represents 49.7% of the total. Across 12 distinct meters, the highest single-meter total was 252,241 kWh.
  - Reported values: kwh_peak=599624.0700000001, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251176, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak

## Limitations
- 62 readings (4.3% of the dataset) have missing temperature values, which may introduce bias into temperature-based analyses and the commercial correlation estimate.
- Only 19 hot-day commercial readings (temperature ≥ 25 °C) were available; this small sample limits the reliability of hot-day load conclusions.
- The dataset covers only 12 distinct meters, which may not be representative of the broader meter population or all building subtypes.
- Pearson correlation assumes a linear relationship; non-linear temperature effects on commercial consumption are not captured.
- The cleaning stage may have removed or imputed records; any systematic bias introduced during cleaning is not fully quantifiable at the reporting stage.

## Conclusion
Industrial buildings overwhelmingly drive total electricity consumption, and demand peaks in Q4 and Q1, consistent with winter heating loads. The modest 4.7% half-year increase and near-equal peak/off-peak split suggest stable grid behaviour. The negative temperature–commercial consumption correlation warrants further investigation into heating-driven commercial demand. Expanding meter coverage and resolving missing temperature records would strengthen future analyses.
