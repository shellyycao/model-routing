# 2024 Smart‑Meter Electricity Consumption Report

The 2024 smart‑meter dataset records 1,428 readings totaling 1.21 GWh of electricity use. Industrial sites consume the vast majority (82 % of total), while commercial and residential usage are much smaller. Consumption was highest in Q4 and rose modestly (4.7 %) in the second half of the year. Hot‑day commercial demand is low, and temperature shows a moderate negative correlation with commercial consumption. Peak‑tariff energy accounts for roughly half of total use. Twelve meters are represented, with one meter responsible for over 20 % of total consumption.

## Key findings
- [q1] The dataset contains 1,428 readings with a total electricity consumption of 1,207,699.96 kWh, averaging 845.73 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.73
- [q2] Industrial buildings dominate consumption, using 995,362.16 kWh, followed by Commercial at 196,367.15 kWh and Residential at 15,970.65 kWh.
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
- [q3] Quarterly consumption peaked in Q4 with 352,881.81 kWh, then Q1 (319,677.67 kWh), Q2 (270,277.36 kWh), and Q3 (264,863.12 kWh).
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Second‑half consumption (617,744.93 kWh) was 4.71 % higher than the first half (589,955.03 kWh), an increase of 27,789.90 kWh.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.71
  - Direction: increase
  - Derived difference(kwh_h2, kwh_h1): 27789.9
- [q5] On hot days (≥25 °C) there were 19 Commercial readings, averaging 415.29 kWh each.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29
- [q6] Overall consumption has a median of 406.8 kWh and a standard deviation of 913.44 kWh. The average temperature recorded is 11.61 °C, with 62 readings missing temperature data. Among Commercial meters, temperature correlates negatively with consumption (Pearson r = ‑0.64).
  - Reported values: kwh_median=406.8, kwh_std=913.44, temperature_mean=11.61, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.64
- [q7] Peak‑tariff usage accounts for 49.65 % of total consumption (599,624.07 kWh) versus 50.35 % off‑peak (608,075.89 kWh). The dataset includes 12 distinct meters, the highest‑use meter consuming 252,241.26 kWh.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak

## Limitations
- The data covers only 12 meters, which may not be representative of all customers or regions.
- Missing temperature values (62 readings) could bias temperature‑related analyses.
- Hot‑day commercial analysis is based on a small sample (19 readings), limiting statistical confidence.
- Aggregations treat each reading equally; variations in reading duration or meter accuracy are not accounted for.

## Conclusion
Electricity consumption in 2024 is heavily weighted toward industrial use, with a modest seasonal increase in the second half of the year and the highest demand in Q4. Temperature appears to dampen commercial consumption, and peak‑tariff energy represents roughly half of total use. Stakeholders should consider targeted efficiency programs for industrial sites and evaluate tariff structures to manage peak demand.
