# 2024 Smart-Meter Electricity Consumption Report

Analysis of 1,428 smart-meter readings across 2024 shows total consumption of 1,207,700 kWh at a mean of 846 kWh per reading. Industrial sites dominate usage, Q4 was the highest-consumption quarter, and the second half of the year grew 4.7% over the first. Peak and off-peak tariffs are nearly balanced, and a moderate negative correlation exists between temperature and commercial energy use.

## Key findings
- [q1] Across all 1,428 readings in the cleaned dataset, total electricity consumption reached 1,207,700 kWh, yielding a mean of approximately 845.7 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Industrial buildings consumed 995,362 kWh (82.4% of total), far exceeding Commercial at 196,367 kWh (16.3%) and Residential at 15,971 kWh (1.3%). The ranking from highest to lowest is Industrial, Commercial, Residential.
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
  - Derived share(kwh_industrial, total_kwh): 82.4
  - Derived share(kwh_commercial, total_kwh): 16.3
  - Derived share(kwh_residential, total_kwh): 1.3
- [q3] Quarterly consumption shows Q4 as the peak at 352,882 kWh, followed by Q1 at 319,678 kWh, Q2 at 270,277 kWh, and Q3 as the lowest at 264,863 kWh, indicating higher demand in colder months.
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Second-half consumption (617,745 kWh) exceeded first-half consumption (589,955 kWh) by 4.7%, representing an increase of approximately 27,790 kWh over the year's midpoint.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
  - Derived difference(kwh_h2, kwh_h1): 27789.9
- [q5] On hot days (temperature ≥ 25 °C), 19 commercial readings were recorded with a mean consumption of 415.3 kWh per reading, providing a baseline for peak cooling-load planning.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
- [q6] The median reading was 406.8 kWh with a standard deviation of 913.4 kWh, indicating high dispersion. Mean temperature across available readings was 11.6 °C, with 62 readings missing temperature data. Among commercial readings, the Pearson correlation between temperature and energy was −0.64, suggesting higher commercial consumption in cooler conditions.
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636239865442
- [q7] Off-peak tariff accounted for 608,076 kWh versus 599,624 kWh on peak tariff, giving peak a 49.7% share of total consumption — an almost even split. Across 12 distinct meters, the highest single-meter total was 252,241 kWh, indicating significant concentration of load in one meter.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251175, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak

## Limitations
- 62 readings are missing temperature_c values, which may introduce bias into temperature-based analyses and reduce the reliability of the temperature–consumption correlation.
- Only 19 hot-day commercial readings (temperature ≥ 25 °C) were available, making the hot-day commercial load estimate statistically fragile.
- With only 12 distinct meters, the dataset is small; findings may not generalise to a broader meter population.
- The negative commercial temperature–energy correlation is observational; no causal inference can be drawn without controlling for confounders such as building occupancy or operational schedules.
- The cleaning stage validation passed, but any systematic errors introduced before data collection (e.g., meter miscalibration) would not be detectable in this workflow.

## Conclusion
Industrial sites drive the vast majority of 2024 electricity consumption, and demand is highest in the colder quarters (Q4 and Q1). The second half of the year saw a modest 4.7% uplift over the first half. Tariff usage is nearly balanced between peak and off-peak. Stakeholders should focus efficiency initiatives on industrial meters — particularly the single meter accounting for 252,241 kWh — and investigate the inverse relationship between temperature and commercial load to optimise heating-season demand management.
