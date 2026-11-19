# 2024 Smart-Meter Electricity Consumption Report

Analysis of 1,428 smart-meter readings across 2024 reveals total consumption of 1,207,700 kWh. Industrial sites dominate usage, Q4 was the highest-demand quarter, and the second half of the year saw a modest 4.7% increase over the first. Tariff split is near-even, and a negative temperature–energy correlation in commercial buildings suggests cooling-driven load patterns.

## Key findings
- [q1] Across all 1,428 readings in the cleaned dataset, total electricity consumption reached 1,207,700 kWh, yielding a mean of approximately 845.7 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Industrial buildings consumed the most energy at 995,362 kWh (82.4% of total), followed by Commercial at 196,367 kWh (16.3%) and Residential at 15,971 kWh (1.3%).
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
  - Derived share(kwh_industrial, total_kwh): 82.4
  - Derived share(kwh_commercial, total_kwh): 16.3
  - Derived share(kwh_residential, total_kwh): 1.3
- [q3] Q4 (Oct–Dec) was the highest-consumption quarter at 352,882 kWh, followed by Q1 (319,678 kWh), Q2 (270,277 kWh), and Q3 (264,863 kWh), indicating a mid-year trough and a strong year-end peak.
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Second-half consumption (617,745 kWh) exceeded first-half consumption (589,955 kWh) by approximately 27,790 kWh, representing a 4.7% increase from H1 to H2.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
  - Derived difference(kwh_h2, kwh_h1): 27789.9
- [q5] On hot days (temperature ≥ 25 °C), there were 19 commercial readings with a mean consumption of 415.3 kWh per reading, suggesting elevated but moderate cooling-related load.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
- [q6] The median reading was 406.8 kWh with a standard deviation of 913.4 kWh, indicating a right-skewed distribution. The mean recorded temperature was 11.6 °C, with 62 readings missing temperature data. Among commercial readings with valid temperatures, the Pearson correlation between temperature and energy was −0.64, suggesting that higher temperatures are associated with lower commercial consumption.
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636239865442
- [q7] Off-peak tariff accounted for 608,076 kWh versus 599,624 kWh on peak tariff; peak's share of total consumption was 49.7%. Across 12 distinct meters, the highest single-meter total was 252,241 kWh.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251175, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak

## Limitations
- 62 readings (4.3% of the dataset) are missing temperature data, which may introduce bias in temperature-related analyses, particularly the commercial correlation.
- The hot-day commercial subset contains only 19 readings, making the mean highly sensitive to individual outliers and limiting statistical confidence.
- The negative commercial temperature–energy correlation is observational; confounding factors such as building occupancy schedules or seasonal operational patterns are not controlled for.
- With only 12 distinct meters, meter-level conclusions (e.g., highest-use meter) may not generalise to a broader fleet.
- Non-finite values in the analysis output were sanitised to 0.0, which could mask edge cases in sparsely populated groups.

## Conclusion
Industrial sites drive the vast majority of consumption and warrant priority attention for efficiency initiatives. The near-even peak/off-peak tariff split offers limited arbitrage opportunity without behavioural or operational changes. The H2 uptick and Q4 peak suggest seasonal heating demand; the negative commercial temperature–energy correlation points to a different seasonal driver in that segment. Addressing missing temperature records and expanding the meter estate would strengthen future analyses.
