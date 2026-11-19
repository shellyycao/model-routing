# 2024 Smart‑Meter Electricity Consumption Report

The 2024 smart‑meter dataset captures 1,428 readings totaling 1.21 GWh of electricity use. Industrial customers account for the overwhelming majority of consumption, while consumption is fairly evenly split between peak and off‑peak periods. Quarterly analysis shows the highest usage in Q4, and a modest 4.7 % increase in the second half of the year. Hot‑day commercial demand is limited but notable, and temperature shows a moderate negative correlation with commercial consumption.

## Key findings
- [q1] The dataset contains 1,428 readings with a total electricity consumption of 1,207,700 kWh, averaging 846 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.728263
- [q2] Industrial sites dominate consumption, using about 995,362 kWh, which is roughly five times the commercial usage (196,367 kWh) and over 60 times residential (15,971 kWh).
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
- [q3] Quarterly consumption peaked in Q4 with 352,882 kWh, followed by Q1 (319,678 kWh), Q2 (270,277 kWh) and Q3 (264,863 kWh).
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Second‑half consumption (July‑Dec) was 4.7 % higher than the first half, indicating a modest increase.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710512
  - Direction: increase
- [q5] On hot days (≥ 25 °C) commercial meters recorded 19 readings with an average of 415 kWh per reading.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.293684
- [q6] Across all readings the median consumption is 406.8 kWh with a standard deviation of 913.4 kWh. The average temperature is 11.6 °C, with 62 readings missing temperature data. Among commercial sites, temperature and consumption are negatively correlated (‑0.64).
  - Reported values: kwh_median=406.8, kwh_std=913.438516, temperature_mean=11.612299, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636
- [q7] Peak‑time usage accounts for 49.7 % of total consumption (599,624 kWh) while off‑peak accounts for 50.3 % (608,076 kWh). The dataset includes 12 distinct meters, the highest‑use meter consuming 252,241 kWh.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.650086, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak

## Limitations
- Temperature data is missing for 62 readings, which may bias temperature‑related analyses.
- The hot‑day commercial analysis is based on only 19 readings, limiting statistical confidence.
- Meter IDs are limited to 12 unique values, so findings may not generalise to a larger population of meters.

## Conclusion
Industrial consumption drives the bulk of electricity use in 2024, with a fairly balanced split between peak and off‑peak periods. Consumption grew modestly in the second half of the year, and temperature appears to have a negative impact on commercial demand. Stakeholders should focus on industrial efficiency measures and consider the slight seasonal increase when planning capacity.
