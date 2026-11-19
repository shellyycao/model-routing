# 2024 Smart-Meter Electricity Consumption Report

Analysis of 1,428 smart-meter readings for 2024 shows total consumption of 1,207,700 kWh across 12 meters. Industrial sites dominate usage, Q4 was the highest-consumption quarter, and the second half of the year grew 4.7% over the first. Peak and off-peak tariffs are nearly balanced, and commercial buildings show a moderate negative correlation between temperature and consumption.

## Key findings
- [q1] Across all 1,428 readings, total electricity consumption reached 1,207,700 kWh, with a mean of 845.7 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.728263
- [q2] Industrial buildings accounted for 995,362 kWh (the largest share), followed by Commercial at 196,367 kWh and Residential at 15,971 kWh. Industrial consumption alone represents approximately 82.4% of total usage.
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
  - Derived share(kwh_industrial, total_kwh): 82.4
- [q3] Q4 (Oct–Dec) was the highest-consumption quarter at 352,882 kWh, followed by Q1 at 319,678 kWh. Q2 and Q3 were lower at 270,277 kWh and 264,863 kWh respectively, indicating a mid-year dip with a strong year-end rebound.
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Second-half consumption (617,745 kWh) exceeded first-half consumption (589,955 kWh), representing an increase of 4.7% half-on-half.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710512
  - Direction: increase
  - Derived difference(kwh_h2, kwh_h1): 27789.9
- [q5] On hot days (temperature ≥ 25 °C), there were 19 commercial readings with a mean consumption of 415.3 kWh per reading, suggesting moderate load levels under high-temperature conditions.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.293684
- [q6] The median consumption across all readings was 406.8 kWh with a standard deviation of 913.4 kWh, indicating high variability. The mean recorded temperature was 11.6 °C, with 62 readings missing temperature data. For commercial buildings, the Pearson correlation between temperature and consumption was −0.64, suggesting that commercial energy use tends to decrease on warmer days.
  - Reported values: kwh_median=406.8, kwh_std=913.438516, temperature_mean=11.612299, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636
- [q7] Off-peak tariff consumption (608,076 kWh) marginally exceeded peak tariff consumption (599,624 kWh), with peak usage representing 49.7% of total consumption. Across 12 distinct meters, the highest single-meter total was 252,241 kWh.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.650086, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak

## Limitations
- 62 readings are missing temperature data, which may bias temperature-based analyses including the hot-day commercial load and correlation calculations.
- Only 19 hot-day commercial readings (temperature ≥ 25 °C) were available; conclusions about commercial load under high-temperature conditions are based on a small sample.
- The dataset covers only 12 distinct meters, limiting the generalisability of findings across a broader meter population.
- The high standard deviation (913.4 kWh) relative to the median (406.8 kWh) indicates significant heterogeneity across readings; aggregate averages may mask important sub-group differences.
- Causal interpretation of the temperature–consumption correlation is not possible from this observational dataset alone.

## Conclusion
Industrial sites drive the vast majority of 2024 electricity consumption. A mid-year dip in Q2–Q3 reversed strongly in Q4, and second-half consumption grew 4.7% over the first half. Peak and off-peak tariff loads are nearly equal, offering limited arbitrage opportunity. The negative temperature–commercial consumption correlation and the small hot-day sample warrant further investigation before drawing operational conclusions.
