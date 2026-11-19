# 2024 Smart-Meter Electricity Consumption Report

Analysis of 1,428 smart-meter readings across 2024 shows total consumption of 1,207,700 kWh at a mean of 846 kWh per reading. Industrial sites dominate usage, Q4 was the highest-consumption quarter, and the second half of the year grew 4.7% over the first. Tariff split is near-even, and commercial load on hot days averages 415 kWh per reading.

## Key findings
- [q1] Across all 1,428 readings in the cleaned dataset, total electricity consumption reached 1,207,700 kWh, yielding a mean of approximately 845.7 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Industrial buildings account for the vast majority of consumption at 995,362 kWh (82.4% of total), followed by Commercial at 196,367 kWh (16.3%), with Residential contributing only 15,971 kWh (1.3%).
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
  - Derived share(kwh_industrial, total_kwh): 82.4
  - Derived share(kwh_commercial, total_kwh): 16.3
  - Derived share(kwh_residential, total_kwh): 1.3
- [q3] Q4 (Oct–Dec) was the highest-consumption quarter at 352,882 kWh, followed by Q1 (319,678 kWh), Q2 (270,277 kWh), and Q3 (264,863 kWh) as the lowest. Consumption dipped through mid-year before recovering strongly in Q4.
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Second-half consumption (617,745 kWh) exceeded first-half consumption (589,955 kWh), representing an increase of 4.7% half-on-half.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
  - Derived difference(kwh_h2, kwh_h1): 27789.9
- [q5] On hot days (temperature ≥ 25 °C), 19 commercial readings were recorded with a mean consumption of 415.3 kWh per reading, indicating elevated but moderate load under high-temperature conditions.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
- [q6] The median consumption across all readings is 406.8 kWh with a standard deviation of 913.4 kWh, indicating a right-skewed distribution. The mean recorded temperature is 11.6 °C; 62 readings have missing temperature data. Among commercial readings, the Pearson correlation between temperature and consumption is −0.64, suggesting higher temperatures are associated with lower commercial energy use.
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636239865442
- [q7] Off-peak tariff accounts for 608,076 kWh versus 599,624 kWh on peak tariff; peak usage represents 49.7% of total consumption—an almost equal split. Across 12 distinct meters, the highest-consuming single meter recorded 252,241 kWh for the year.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251175, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak

## Limitations
- 62 readings (4.3% of the dataset) have missing temperature values, which may introduce bias into temperature-based analyses and the commercial correlation estimate.
- Only 19 hot-day commercial readings (temperature ≥ 25 °C) were available; this small sample limits the reliability of hot-day load conclusions.
- The dataset covers only 12 distinct meters, which may not be representative of the broader meter population or all building types.
- Residential consumption is very low relative to other categories; it is unclear whether this reflects genuine usage patterns or under-representation of residential meters in the sample.
- The negative commercial temperature–consumption correlation may reflect confounding factors (e.g., seasonal occupancy patterns) rather than a direct causal relationship.

## Conclusion
Industrial sites drive the overwhelming majority of 2024 electricity consumption. Demand follows a U-shaped quarterly pattern with Q3 as the trough and Q4 as the peak, and the second half of the year grew 4.7% over the first. The near-even peak/off-peak tariff split offers limited scope for demand-shifting savings. Priority actions should focus on industrial efficiency programmes and further investigation of the seasonal commercial load pattern, particularly given the moderate negative temperature–consumption correlation observed in that segment.
