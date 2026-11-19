# 2024 Smart‑Meter Electricity Consumption Report

The 2024 smart‑meter dataset (1,428 readings) shows total consumption of 1.21 GWh, heavily weighted toward industrial use. Consumption rose 4.7 % in the second half of the year, with peak‑tariff usage accounting for just under half of total energy. Hot‑day commercial demand is modest, and temperature shows a moderate negative correlation with commercial consumption. Data gaps and limited scope constrain deeper insights.

## Key findings
- [q1] The dataset contains 1,428 readings with a total electricity consumption of 1,207,699.96 kWh, averaging 845.73 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Industrial buildings dominate consumption (995,362.16 kWh), followed by Commercial (196,367.15 kWh) and Residential (15,970.65 kWh).
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
- [q3] Quarterly consumption peaks in Q4 (352,881.81 kWh), then Q1 (319,677.67 kWh), Q2 (270,277.36 kWh) and Q3 (264,863.12 kWh).
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Second‑half consumption (617,744.93 kWh) exceeds the first half (589,955.03 kWh) by 27,789.90 kWh, a 4.71 % increase.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
  - Derived difference(kwh_h2, kwh_h1): 27789.9
- [q5] On days with temperature ≥ 25 °C, 19 Commercial readings were recorded, averaging 415.29 kWh each.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
- [q6] Overall consumption median is 406.8 kWh with a standard deviation of 913.44 kWh. The average temperature across readings is 11.61 °C, with 62 missing temperature values. Among Commercial meters, temperature and consumption are negatively correlated (‑0.64).
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636239865442
- [q7] Peak‑tariff usage accounts for 49.65 % of total consumption (599,624.07 kWh) while off‑peak accounts for 50.35 % (608,075.89 kWh). Twelve distinct meters are represented, and the highest‑use meter consumed 252,241.26 kWh.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251175, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak

## Limitations
- Temperature data are missing for 62 readings, limiting the reliability of temperature‑related analyses.
- The dataset covers only a single year (2024) and a limited set of meters (12), which may not represent broader consumption patterns.
- Commercial hot‑day analysis is based on only 19 readings, so the average may be sensitive to outliers.
- Correlation analysis is restricted to Commercial meters and does not account for potential confounding factors.

## Conclusion
Industrial consumption drives the majority of electricity use in 2024, with a modest seasonal increase in the second half of the year. Peak‑tariff demand is nearly balanced with off‑peak usage, and temperature appears to dampen commercial consumption on hotter days. While the data provide clear high‑level insights, gaps in temperature records and the narrow meter sample suggest caution when extrapolating these findings to larger portfolios.
