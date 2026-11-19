# 2024 Smart-Meter Electricity Consumption Report

Analysis of 1,428 cleaned smart-meter readings for 2024 shows total consumption of 1,207,700 kWh across residential, commercial, and industrial buildings. Industrial sites dominate usage. Consumption dipped mid-year before recovering strongly in Q4, and the second half of the year outpaced the first by 4.7%. Peak and off-peak tariff splits are nearly equal. Twelve distinct meters were active, with the highest single-meter contribution exceeding 252,000 kWh.

## Key findings
- [q1] Across all 1,428 readings, total electricity consumption reached 1,207,700.0 kWh, with a mean of 845.7 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Industrial buildings consumed the most electricity at 995,362.2 kWh (82.4% of total), far ahead of Commercial at 196,367.2 kWh (16.3%) and Residential at 15,970.7 kWh (1.3%).
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
  - Derived share(kwh_industrial, total_kwh): 82.4
  - Derived share(kwh_commercial, total_kwh): 16.3
  - Derived share(kwh_residential, total_kwh): 1.3
- [q3] Q4 was the highest-consumption quarter at 352,881.8 kWh, followed by Q1 (319,677.7 kWh), Q2 (270,277.4 kWh), and Q3 (264,863.1 kWh), indicating a mid-year trough with a strong year-end recovery.
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Second-half consumption (617,744.9 kWh) exceeded first-half consumption (589,955.0 kWh) by 4.7%, representing an increase of approximately 27,789.9 kWh.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
  - Derived difference(kwh_h2, kwh_h1): 27789.9
- [q5] On hot days (temperature ≥ 25 °C), 19 commercial readings were recorded with a mean consumption of 415.3 kWh per reading, slightly above the overall median of 406.8 kWh.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
- [q6] The median consumption across all readings was 406.8 kWh with a standard deviation of 913.4 kWh, indicating high variability. The mean recorded temperature was 11.6 °C, with 62 readings missing temperature data. Among commercial readings with valid temperatures, the Pearson correlation between temperature and consumption was -0.64, suggesting higher temperatures are associated with lower commercial energy use.
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636239865442
- [q7] Off-peak tariff consumption (608,075.9 kWh) marginally exceeded peak tariff consumption (599,624.1 kWh); peak usage accounted for 49.7% of total kWh. Twelve distinct meters were active, with the highest single-meter total reaching 252,241.3 kWh.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251175, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak

## Limitations
- 62 readings (4.3% of the dataset) are missing temperature_c values, which may introduce bias into temperature-based analyses and reduce the reliability of the commercial temperature-consumption correlation.
- The commercial temperature-consumption correlation is based on a relatively small subset of commercial readings with valid temperatures; results should be interpreted cautiously.
- Only 19 hot-day commercial readings (temperature ≥ 25 °C) were available, limiting the statistical robustness of the hot-day load analysis.
- The dataset covers only 12 distinct meters, which may not be representative of the broader meter population or all building types.
- Residential consumption is very low relative to other building types (1.3% of total), which may reflect under-representation of residential meters in the sample rather than actual usage patterns.

## Conclusion
Industrial buildings overwhelmingly drive total electricity consumption, while commercial and residential sites contribute modestly. The year followed a U-shaped quarterly pattern with Q3 as the trough and Q4 as the peak, and second-half consumption grew 4.7% over the first half. Peak and off-peak tariff usage is nearly balanced. The negative temperature-consumption correlation in commercial buildings warrants further investigation into cooling versus heating dynamics. Expanding meter coverage and resolving missing temperature records would strengthen future analyses.
