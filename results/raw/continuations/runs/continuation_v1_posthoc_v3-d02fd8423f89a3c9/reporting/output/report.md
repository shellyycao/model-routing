# 2024 Smart‑Meter Electricity Consumption Report

The 2024 smart‑meter dataset comprises 1,428 readings with a total electricity consumption of 1.21 million kWh. Industrial sites account for the overwhelming majority of use, while consumption peaks in the fourth quarter and rises modestly in the second half of the year. Commercial loads on hot days are relatively low, and temperature shows a moderate negative correlation with commercial consumption. Peak‑tariff usage is almost evenly split with off‑peak, and the data cover 12 distinct meters, the most active of which consumed about 252 kWh.

## Key findings
- [q1] The dataset contains 1,428 readings with a total electricity consumption of 1,207,699.96 kWh, averaging 845.73 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.73
- [q2] Industrial buildings dominate consumption (995,362.16 kWh), followed by Commercial (196,367.15 kWh) and Residential (15,970.65 kWh).
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
- [q3] Quarterly consumption was highest in Q4 (352,881.81 kWh) and lowest in Q3 (264,863.12 kWh).
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Second‑half consumption increased by about 4.71 % compared with the first half.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.71
  - Direction: increase
- [q5] On hot days (temperature ≥ 25 °C) there were 19 Commercial readings with an average consumption of 415.29 kWh.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29
- [q6] The median consumption is 406.8 kWh with a standard deviation of 913.44 kWh. Average temperature is 11.61 °C; 62 readings lack temperature data. Among Commercial meters, temperature and consumption are negatively correlated (r ≈ ‑0.64).
  - Reported values: kwh_median=406.8, kwh_std=913.44, temperature_mean=11.61, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.64
- [q7] Peak‑tariff usage accounts for 49.65 % of total consumption (599,624.07 kWh) and off‑peak for 50.35 % (608,075.89 kWh). The dataset includes 12 distinct meters; the highest‑use meter consumed 252,241.26 kWh.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak

## Limitations
- Temperature data are missing for 62 of the 1,428 readings, limiting the reliability of temperature‑related analyses.
- Hot‑day commercial load is based on only 19 readings, which may not represent typical high‑temperature demand patterns.
- The analysis covers 12 distinct meters; results may not generalise to a larger fleet of meters.
- Tariff classification assumes correct labeling of peak/off‑peak periods; any mis‑labeling would affect the share calculations.

## Conclusion
Industrial consumption drives the bulk of electricity use, with a modest seasonal increase in the second half of 2024. Off‑peak usage slightly exceeds peak usage, suggesting opportunities for demand‑side management. Improving temperature data completeness and expanding meter coverage would enhance future analyses and support more precise load‑shaping strategies.
