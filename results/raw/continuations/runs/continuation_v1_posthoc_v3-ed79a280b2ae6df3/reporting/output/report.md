# 2024 Energy Consumption Analysis Report

This report presents the findings from the analysis of 2024 smart-meter data, focusing on total and per-building-type energy consumption, quarterly trends, half-year changes, commercial load on hot days, and tariff and meter usage. Key findings include a 4.71% increase in energy consumption from the first to the second half of the year, with industrial buildings consuming the most energy. The quarterly trend shows the highest consumption in Q4, and commercial buildings exhibit a negative correlation between temperature and energy consumption on hot days.

## Key findings
- [q1] The total energy consumption for 2024 was 1,207,699.96 kWh, with an average of 845.73 kWh per reading across 1,428 readings.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Energy consumption varied significantly by building type, with Industrial (995,362.16 kWh) > Commercial (196,367.15 kWh) > Residential (15,970.65 kWh).
  - Reported values: kwh_residential=15970.650000000001, kwh_commercial=196367.15000000002, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
- [q3] Quarterly energy consumption was highest in Q4 (352,881.81 kWh) and lowest in Q2 (270,277.36 kWh), with Q1 (319,677.67 kWh) and Q3 (264,863.12 kWh) in between.
  - Reported values: kwh_q1=319677.67000000004, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81000000006
  - Ranking: Q4, Q1, Q3, Q2
- [q4] Energy consumption increased by 4.71% from the first half (589,955.03 kWh) to the second half (617,744.93 kWh) of the year.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
  - Derived pct_change(kwh_h2, kwh_h1): 4.710511579162232
- [q5] On hot days (temperature >= 25°C), commercial buildings had 19 readings with an average consumption of 415.29 kWh.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
- [q6] The median energy consumption was 406.8 kWh, with a standard deviation of 913.44 kWh. The mean temperature was 11.61°C, with 62 readings missing temperature data. Commercial buildings showed a negative correlation (-0.638) between temperature and energy consumption on days with recorded temperatures.
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.6376362398654432
- [q7] Energy consumption was nearly evenly split between peak (599,624.07 kWh, 49.65%) and off-peak (608,075.89 kWh) periods. There were 12 unique meters, with the highest usage by a single meter at 252,241.26 kWh.
  - Reported values: kwh_peak=599624.0700000001, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251176, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak

## Limitations
- The analysis is based on a single year of data, which may not capture long-term trends or anomalies.
- Missing temperature data for 62 readings could affect the accuracy of temperature-related findings.
- The correlation between temperature and energy consumption for commercial buildings is based on a small sample size (19 readings).

## Conclusion
The analysis provides valuable insights into energy consumption patterns in 2024, highlighting the significant role of industrial buildings, the seasonal variation in consumption, and the impact of temperature on commercial energy use. Future analyses should consider extending the time frame and addressing data gaps to enhance the reliability of findings.
