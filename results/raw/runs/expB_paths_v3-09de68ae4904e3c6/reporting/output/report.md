# 2024 Smart-Meter Electricity Consumption Report

Analysis of 1,428 smart-meter readings across 2024 recorded a total of 1,207,700 kWh. Industrial sites dominate consumption, Q4 was the highest-demand quarter, and the second half of the year grew 4.7% over the first. Tariff usage is nearly balanced, and a moderate negative correlation between temperature and commercial energy use was observed.

## Key findings
- [q1] Across all 1,428 readings in the cleaned dataset, total electricity consumption reached 1,207,700 kWh, yielding a mean of approximately 845.7 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Industrial buildings accounted for the vast majority of consumption at 995,362 kWh, followed by Commercial at 196,367 kWh and Residential at 15,971 kWh. Industrial sites represent approximately 82.4% of total usage.
  - Reported values: kwh_residential=15970.650000000001, kwh_commercial=196367.15000000002, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
  - Derived share(kwh_industrial, total_kwh): 82.4
- [q3] Q4 (Oct–Dec) was the highest-consumption quarter at 352,882 kWh, followed by Q1 at 319,678 kWh. Q2 and Q3 were lower at 270,277 kWh and 264,863 kWh respectively, indicating a mid-year dip with a strong year-end rebound.
  - Reported values: kwh_q1=319677.67000000004, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81000000006
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Second-half consumption (617,745 kWh) exceeded first-half consumption (589,955 kWh) by approximately 4.7%, indicating a modest but meaningful increase in demand over the course of the year.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
  - Derived difference(kwh_h2, kwh_h1): 27789.9
- [q5] On hot days (temperature ≥ 25 °C), 19 commercial readings were recorded with a mean consumption of 415.3 kWh per reading, providing a baseline for peak cooling-load planning.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
- [q6] The median consumption across all readings was 406.8 kWh with a standard deviation of 913.4 kWh, indicating high variability. The mean recorded temperature was 11.6 °C, with 62 readings missing temperature data. Among commercial readings, a Pearson correlation of −0.64 between temperature and energy use suggests that commercial sites consume more electricity in cooler conditions.
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636239865442
- [q7] Off-peak tariff readings accounted for 608,076 kWh versus 599,624 kWh on peak tariff, giving peak a 49.7% share of total consumption — an almost even split. Across 12 distinct meters, the highest single-meter total was 252,241 kWh.
  - Reported values: kwh_peak=599624.0700000001, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251176, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak

## Limitations
- 62 readings are missing temperature data, which may introduce bias into temperature-based analyses, particularly the commercial correlation and hot-day filter.
- Only 19 hot-day commercial readings (temperature ≥ 25 °C) were available, making the hot-day mean estimate statistically fragile.
- The dataset covers only 12 distinct meters, limiting the generalisability of meter-level findings to the broader meter population.
- The high standard deviation (913.4 kWh) relative to the median (406.8 kWh) suggests significant outliers or heterogeneous site types that could skew aggregate metrics.
- Correlation between temperature and commercial energy use is observational; no causal inference can be drawn without controlling for other variables such as occupancy or building size.

## Conclusion
Industrial sites drive the overwhelming majority of 2024 electricity consumption. Demand dipped mid-year before recovering strongly in Q4, and second-half usage grew 4.7% over the first half. Tariff load is nearly balanced between peak and off-peak. Stakeholders should monitor the single highest-use meter (252,241 kWh) and investigate the negative temperature–commercial consumption relationship to optimise heating and cooling strategies.
