# 2024 Smart-Meter Electricity Consumption Report

Analysis of 1,428 cleaned smart-meter readings for 2024 shows total consumption of 1,207,700 kWh across 12 meters. Industrial sites dominate usage, accounting for over 82% of all energy consumed. Consumption peaked in Q4 and Q1, with a modest 4.7% increase from H1 to H2. Peak and off-peak tariffs are nearly balanced. A moderate negative correlation between temperature and commercial energy use suggests cooling-driven demand is not the primary commercial driver.

## Key findings
- [q1] Across all 1,428 readings in the cleaned dataset, total electricity consumption reached 1,207,700 kWh, yielding a mean of approximately 845.7 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Industrial buildings consumed the most energy at 995,362 kWh (82.4% of total), followed by Commercial at 196,367 kWh (16.3%) and Residential at 15,971 kWh (1.3%). Industrial usage is approximately 5.1 times that of Commercial.
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
  - Derived share(kwh_industrial, total_kwh): 82.4
  - Derived share(kwh_commercial, total_kwh): 16.3
  - Derived share(kwh_residential, total_kwh): 1.3
  - Derived ratio(kwh_industrial, kwh_commercial): 5.1
- [q3] Quarterly consumption shows a U-shaped pattern: Q4 was highest at 352,882 kWh, followed by Q1 (319,678 kWh), Q2 (270,277 kWh), and Q3 (264,863 kWh) — the lowest quarter. This suggests elevated demand in colder months.
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Second-half consumption (617,745 kWh) exceeded first-half consumption (589,955 kWh) by approximately 27,790 kWh, representing an increase of 4.7% from H1 to H2.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
  - Derived difference(kwh_h2, kwh_h1): 27789.9
- [q5] On hot days (temperature ≥ 25 °C), 19 commercial readings were recorded with a mean consumption of 415.3 kWh per reading, which is below the overall dataset mean of 845.7 kWh, suggesting commercial sites do not exhibit unusually high load on hot days.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
- [q6] The distribution of consumption is right-skewed: the median is 406.8 kWh while the standard deviation is 913.4 kWh, indicating a long upper tail driven by high-use industrial meters. The mean recorded temperature was 11.6 °C, with 62 readings missing temperature data. For commercial sites, the Pearson correlation between temperature and energy use is −0.64, a moderate negative relationship suggesting commercial consumption tends to be higher in cooler conditions.
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636239865442
- [q7] Peak-tariff consumption (599,624 kWh, 49.7% of total) and off-peak consumption (608,076 kWh, 50.3%) are nearly equal, indicating no strong tariff-driven load shift. The dataset covers 12 distinct meters; the highest-consuming single meter recorded 252,241 kWh — about 20.9% of total consumption.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251175, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak
  - Derived share(kwh_off_peak, total_kwh): 50.3
  - Derived share(highest_use_meter_kwh, total_kwh): 20.9

## Limitations
- 62 readings have missing temperature data, which may introduce bias into temperature-based analyses, particularly the commercial correlation estimate.
- Only 19 hot-day commercial readings (temperature ≥ 25 °C) were available, making the hot-day commercial mean statistically fragile and potentially unrepresentative.
- With only 12 distinct meters, the dataset is small; results — especially the single-meter maximum — may not generalise to the broader meter population.
- The analysis uses calendar quarters and half-years as fixed boundaries; any seasonal effects that straddle these boundaries may be partially obscured.
- Correlation between temperature and commercial energy use is observational; no causal inference can be drawn without controlling for other variables such as occupancy or production schedules.

## Conclusion
Industrial sites overwhelmingly drive total consumption, and demand is highest in the colder bookend quarters (Q4 and Q1). The modest 4.7% H2 increase and near-equal peak/off-peak split suggest stable load patterns with limited tariff arbitrage. Attention should focus on the single highest-use meter (252,241 kWh) and on improving temperature data completeness to strengthen future seasonal analyses.
