# 2024 Smart-Meter Electricity Consumption Report

Analysis of 1,428 cleaned smart-meter readings for 2024 shows total consumption of 1,207,700 kWh across 12 meters. Industrial sites dominate usage, accounting for over 82% of all energy consumed. Consumption dipped mid-year before recovering strongly in Q4, and the second half of the year was 4.7% higher than the first. Tariff split is nearly even between peak and off-peak. A moderate negative correlation between temperature and commercial energy use suggests cooling loads are not the primary commercial driver.

## Key findings
- [q1] The dataset contains 1,428 readings with a combined consumption of 1,207,700 kWh, yielding a mean of approximately 845.7 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Industrial buildings consumed the most energy at 995,362 kWh (82.4% of total), followed by Commercial at 196,367 kWh (16.3%) and Residential at 15,971 kWh (1.3%). The gap between Industrial and Commercial is substantial at approximately 799,000 kWh.
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
  - Derived share(kwh_industrial, total_kwh): 82.4
  - Derived share(kwh_commercial, total_kwh): 16.3
  - Derived share(kwh_residential, total_kwh): 1.3
  - Derived difference(kwh_industrial, kwh_commercial): 798995.01
- [q3] Q4 (Oct–Dec) was the highest-consumption quarter at 352,882 kWh, followed by Q1 (319,678 kWh), Q2 (270,277 kWh), and Q3 (264,863 kWh). Consumption fell through mid-year before rebounding sharply in Q4.
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Second-half consumption (617,745 kWh) exceeded first-half consumption (589,955 kWh) by 4.7%, indicating an increase in demand over the course of the year.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
  - Derived difference(kwh_h2, kwh_h1): 27789.9
- [q5] On hot days (temperature ≥ 25 °C), there were 19 commercial readings with a mean consumption of 415.3 kWh per reading, suggesting elevated but not extreme load under high-temperature conditions.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
- [q6] The median reading is 406.8 kWh with a standard deviation of 913.4 kWh, indicating a right-skewed distribution with high variability. The mean recorded temperature is 11.6 °C; 62 readings have missing temperature data. Among commercial readings, temperature and consumption show a moderate negative Pearson correlation of −0.64, suggesting commercial energy use tends to decrease as temperatures rise.
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636239865442
- [q7] Off-peak tariff consumption (608,076 kWh) slightly exceeded peak tariff consumption (599,624 kWh), with peak accounting for 49.7% of total usage — an almost even split. Across 12 distinct meters, the highest single-meter total was 252,241 kWh, representing 20.9% of all consumption.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251175, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak
  - Derived share(highest_use_meter_kwh, total_kwh): 20.9

## Limitations
- 62 readings (4.3% of the dataset) have missing temperature values, which may introduce bias into temperature-based analyses, particularly the commercial temperature–consumption correlation.
- Only 19 commercial hot-day readings (temperature ≥ 25 °C) were available, making the hot-day commercial load estimate statistically fragile.
- The dataset covers only 12 distinct meters, limiting the generalisability of findings to the broader meter population.
- Residential consumption is very low relative to other building types, which may reflect under-representation of residential meters rather than actual low usage.
- The analysis uses calendar quarters and half-years; seasonal effects may not align perfectly with these fixed boundaries.

## Conclusion
Industrial sites overwhelmingly drive total electricity consumption, while the near-equal peak/off-peak tariff split suggests load is spread across the day. The 4.7% second-half increase and Q4 peak warrant attention for capacity planning. The negative commercial temperature–consumption correlation and limited hot-day data suggest cooling is not a dominant commercial load driver, though the small sample size warrants caution. Expanding meter coverage and resolving missing temperature records would materially improve future analyses.
