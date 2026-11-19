# 2024 Smart‑Meter Electricity Consumption Report

The 2024 smart‑meter dataset records 1,428 readings totalling 1,207,699.96 kWh of electricity use. Industrial sites dominate consumption (≈83% of total), while residential use is minimal. Quarterly demand peaks in Q4, and the second half of the year shows a modest 4.71 % increase over the first half. Commercial consumption on hot days (≥25 °C) is low, with an average of 415.29 kWh per reading. Temperature and consumption are negatively correlated for commercial sites (r ≈ ‑0.64). Energy use is almost evenly split between peak (49.65 % share) and off‑peak periods, with 12 distinct meters represented and the highest single‑meter usage at 252,241.26 kWh.

## Key findings
- [q1] The dataset contains 1,428 readings totaling 1,207,699.96 kWh, averaging 845.73 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.73
- [q2] Industrial sites consume the most electricity, followed by commercial and residential.
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
- [q3] Quarterly consumption is highest in Q4, then Q1, Q2, and Q3.
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Second‑half consumption (617,744.93 kWh) is 4.71 % higher than the first half (589,955.03 kWh).
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.71
  - Direction: increase
- [q5] On hot days (≥25 °C) commercial meters recorded 19 readings with an average of 415.29 kWh per reading.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29
- [q6] Overall consumption has a median of 406.8 kWh and a standard deviation of 913.44 kWh. The average temperature is 11.61 °C, with 62 readings missing temperature data. Among commercial meters, temperature and consumption are negatively correlated (r ≈ ‑0.64).
  - Reported values: kwh_median=406.8, kwh_std=913.44, temperature_mean=11.61, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.64
- [q7] Off‑peak periods account for the largest share of energy use (608,075.89 kWh), slightly exceeding peak use (599,624.07 kWh). Peak consumption represents 49.65 % of total usage. The dataset includes 12 distinct meters, the highest single‑meter consumption being 252,241.26 kWh.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak

## Limitations
- Temperature data is missing for 62 of the 1,428 readings, limiting the robustness of temperature‑related analyses.
- Hot‑day commercial analysis is based on only 19 readings, which may not represent typical summer load patterns.
- Only 12 distinct meters are present, so findings may not generalise to the broader portfolio of smart‑metered sites.
- Correlation between temperature and consumption is calculated solely for commercial meters; residential and industrial relationships are not examined.
- The dataset covers a single year (2024); longer‑term trends cannot be assessed.

## Conclusion
The 2024 electricity consumption profile is heavily weighted toward industrial use, with a clear seasonal peak in Q4 and a modest increase in the second half of the year. Energy demand is split almost evenly between peak and off‑peak tariffs, and temperature appears to suppress commercial consumption on hot days. Stakeholders should consider targeted efficiency programs for industrial sites, monitor off‑peak usage opportunities, and improve temperature data capture to enhance future analyses.
