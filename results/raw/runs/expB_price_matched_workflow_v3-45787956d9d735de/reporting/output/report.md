# 2024 Smart-Meter Electricity Consumption Report

Analysis of 1,428 smart-meter readings across 2024 reveals total consumption of 1,207,700 kWh. Industrial sites dominate usage, Q4 was the highest-demand quarter, and the second half of the year saw a modest 4.7% increase over the first. Tariff split is near-even, and a negative temperature–consumption correlation exists for commercial buildings.

## Key findings
- [q1] Across all 1,428 readings in the cleaned dataset, total electricity consumption reached 1,207,700 kWh, with a mean of 845.7 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Industrial buildings consumed the most electricity at 995,362 kWh (82.4% of total), followed by Commercial at 196,367 kWh (16.3%) and Residential at 15,971 kWh (1.3%).
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
  - Derived share(kwh_industrial, total_kwh): 82.4
  - Derived share(kwh_commercial, total_kwh): 16.3
  - Derived share(kwh_residential, total_kwh): 1.3
- [q3] Q4 was the highest-consumption quarter at 352,882 kWh, followed by Q1 (319,678 kWh), Q2 (270,277 kWh), and Q3 (264,863 kWh), indicating a mid-year trough and a strong year-end peak.
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Second-half consumption (617,745 kWh) exceeded first-half consumption (589,955 kWh), representing an increase of 4.7% from H1 to H2.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
  - Derived difference(kwh_h2, kwh_h1): 27789.9
- [q5] On hot days (temperature ≥ 25°C), 19 commercial readings were recorded with a mean consumption of 415.3 kWh per reading, suggesting moderate but concentrated load during high-temperature periods.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
- [q6] The median consumption was 406.8 kWh with a standard deviation of 913.4 kWh, indicating a right-skewed distribution. Mean recorded temperature was 11.6°C; 62 readings had missing temperature data. For commercial buildings, the Pearson correlation between temperature and consumption was −0.64, suggesting higher commercial usage in cooler conditions.
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636239865442
- [q7] Off-peak tariff accounted for 608,076 kWh versus 599,624 kWh at peak tariff, giving peak a 49.7% share of total consumption — an almost equal split. Across 12 unique meters, the highest single-meter total was 252,241 kWh.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251175, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak

## Limitations
- 62 readings (4.3% of the dataset) have missing temperature values, which may introduce bias into temperature-based analyses and the commercial correlation estimate.
- Only 19 hot-day commercial readings (temperature ≥ 25°C) were available, making the hot-day mean highly sensitive to individual outliers and limiting statistical confidence.
- The dataset covers only 12 unique meters, which may not be representative of the broader meter population; findings should be interpreted with caution before generalising.
- Causal inference cannot be drawn from the temperature–consumption correlation alone; confounding factors such as building occupancy, insulation, or operational schedules are not captured in this dataset.

## Conclusion
Industrial sites drive the overwhelming majority of 2024 electricity consumption. Demand follows a U-shaped quarterly pattern with a mid-year trough and a strong Q4 peak, and the second half of the year was 4.7% higher than the first. The near-equal peak/off-peak tariff split offers limited opportunity for straightforward tariff arbitrage. Priority actions should focus on industrial efficiency programmes and further investigation of the negative temperature–commercial consumption relationship to optimise heating and cooling strategies.
