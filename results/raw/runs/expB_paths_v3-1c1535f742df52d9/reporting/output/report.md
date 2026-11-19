# 2024 Smart‑Meter Electricity Consumption Report

The 2024 smart‑meter dataset comprises 1,428 readings with a total electricity consumption of 1,207,699.96 kWh (≈845.73 kWh per reading). Industrial use dominates (≈83% of total), while commercial and residential use are much smaller. Consumption peaks in the fourth quarter and rises modestly (4.71 %) in the second half of the year. Hot‑day commercial demand is low (19 readings, 415.29 kWh average). Energy use shows high variability (std ≈ 913 kWh) and a negative temperature‑consumption correlation for commercial meters (‑0.64). Peak tariffs represent just under half of total use, with 12 meters active and the highest‑use meter accounting for 252,241.26 kWh.

## Key findings
- [q1] The dataset contains 1,428 readings with a total electricity consumption of 1,207,699.96 kWh, averaging 845.73 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.73
- [q2] Industrial buildings dominate consumption at 995,362.16 kWh, far exceeding Commercial (196,367.15 kWh) and Residential (15,970.65 kWh).
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
- [q3] Quarterly consumption shows the highest use in Q4 (352,881.81 kWh) followed by Q1 (319,677.67 kWh), Q2 (270,277.36 kWh) and Q3 (264,863.12 kWh).
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Second‑half consumption (617,744.93 kWh) is 4.71 % higher than the first half (589,955.03 kWh), indicating an increase.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.71
  - Direction: increase
  - Derived difference(kwh_h2, kwh_h1): 27789.9
- [q5] On days with temperature ≥ 25 °C, the 19 Commercial readings averaged 415.29 kWh.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29
- [q6] Across all readings, the median consumption is 406.8 kWh with a standard deviation of 913.44 kWh. The average temperature is 11.61 °C, with 62 missing temperature values. For Commercial meters, temperature and consumption are negatively correlated (‑0.64).
  - Reported values: kwh_median=406.8, kwh_std=913.44, temperature_mean=11.61, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.64
- [q7] Peak tariffs account for 49.65 % of total use (599,624.07 kWh) versus 50.35 % off‑peak (608,075.89 kWh). Twelve distinct meters are recorded, and the single highest‑use meter consumed 252,241.26 kWh.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak

## Limitations
- The data cover only the calendar year 2024 and may not reflect longer‑term trends.
- Temperature readings are missing for 62 records, which could bias the temperature‑consumption analysis.
- Only 12 distinct meters are present, limiting the generalisability of meter‑level insights.
- Commercial temperature‑consumption correlation is based on a small subset of readings with valid temperatures.

## Conclusion
Electricity consumption in 2024 is heavily weighted toward industrial use, with a modest seasonal increase in the second half of the year and a clear quarterly pattern that peaks in Q4. Hot‑day commercial demand is low, and temperature appears to reduce commercial consumption. Tariff analysis shows a near‑even split between peak and off‑peak usage. Stakeholders should focus on industrial demand management, consider seasonal load‑shifting strategies, and address data gaps in temperature reporting to improve future analyses.
