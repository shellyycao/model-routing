# 2024 Smart‑Meter Energy Consumption Report

The 2024 dataset records 1,207,700 kWh across 1,428 readings from 12 meters. Industrial use dominates (82.4% of total), while residential consumption is minimal. Consumption grew 4.7% in the second half of the year, driven by higher industrial activity. Peak‑hour usage accounts for roughly half of total energy, and commercial demand drops on hot days. Temperature shows a modest negative correlation with commercial usage.

## Key findings
- [q1] Total electricity consumption in 2024 was 1,207,700 kWh, derived from 1,428 readings, averaging 846 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Industrial sites consumed the most energy (995,362 kWh), followed by commercial buildings (196,367 kWh) and residential units (15,971 kWh).
  - Reported values: kwh_residential=15970.650000000001, kwh_commercial=196367.15000000002, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
- [q3] Quarterly consumption was highest in Q4 (352,882 kWh) and lowest in Q2 (270,277 kWh).
  - Reported values: kwh_q1=319677.67000000004, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81000000006
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Energy use increased by 4.71 % in the second half of the year compared with the first half.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
  - Derived difference(kwh_h2, kwh_h1): 27789.9
- [q5] On days with temperature ≥ 25 °C, commercial meters recorded 19 readings with an average consumption of 415 kWh per reading.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
- [q6] The median consumption was 406.8 kWh with a standard deviation of 913.44 kWh. Average temperature across readings was 11.61 °C, with 62 readings missing temperature data. Among commercial sites, temperature and consumption are negatively correlated (‑0.64).
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636239865442
- [q7] Off‑peak tariffs accounted for 50.3 % of total energy (608,076 kWh) while peak tariffs contributed 49.7 % (599,624 kWh). Twelve distinct meters were observed, with the highest‑use meter delivering 252,241 kWh.
  - Reported values: kwh_peak=599624.0700000001, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251176, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak

## Limitations
- Temperature data is missing for 62 readings, which may bias correlation analysis.
- Only 12 meters are represented, limiting the generalisability of the findings to the broader portfolio.
- The dataset covers a single year; longer‑term trends cannot be assessed.
- Hot‑day commercial analysis is based on only 19 readings, so results should be interpreted cautiously.

## Conclusion
Industrial consumption drives the majority of electricity use, and overall demand rose modestly in the second half of 2024. Off‑peak usage slightly exceeds peak usage, suggesting opportunities for demand‑side management. The negative temperature‑consumption correlation for commercial sites indicates that higher temperatures may reduce load, possibly due to reduced heating demand. Addressing data gaps—especially temperature completeness and expanding meter coverage—will improve future analyses and support more precise energy‑efficiency initiatives.
