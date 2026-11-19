# 2024 Smart-Meter Electricity Consumption Report

Analysis of 1,428 cleaned smart-meter readings for 2024 shows total consumption of 1,207,700 kWh across 12 meters. Industrial buildings dominate usage, accounting for over 82% of all consumption. Quarterly demand peaked in Q4 and Q1, reflecting seasonal heating patterns. Second-half consumption rose ~4.7% versus the first half. Commercial load on hot days is modest, and a moderate negative temperature–consumption correlation exists for commercial sites. Peak and off-peak tariff splits are nearly equal.

## Key findings
- [q1] Across all 1,428 readings in the cleaned dataset, total electricity consumption reached 1,207,700 kWh, with a mean of 845.7 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Industrial buildings consumed 995,362 kWh (82.4% of total), far exceeding Commercial at 196,367 kWh (16.3%) and Residential at 15,971 kWh (1.3%). The ranking from highest to lowest is Industrial, Commercial, Residential.
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
  - Derived share(kwh_industrial, total_kwh): 82.4
  - Derived share(kwh_commercial, total_kwh): 16.3
  - Derived share(kwh_residential, total_kwh): 1.3
- [q3] Quarterly consumption shows a U-shaped pattern: Q4 was highest at 352,882 kWh, followed by Q1 (319,678 kWh), Q2 (270,277 kWh), and Q3 (264,863 kWh) — the lowest quarter. The ranking from highest to lowest is Q4, Q1, Q2, Q3.
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Second-half consumption (617,745 kWh, July–December) exceeded first-half consumption (589,955 kWh, January–June) by approximately 27,790 kWh, representing an increase of 4.7%.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
  - Derived difference(kwh_h2, kwh_h1): 27789.9
- [q5] On hot days (temperature ≥ 25 °C), there were 19 commercial readings with a mean consumption of 415.3 kWh per reading — below the overall dataset mean of 845.7 kWh, suggesting commercial sites do not exhibit elevated load under high-temperature conditions in this dataset.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
- [q6] The distribution of consumption is right-skewed: the median is 406.8 kWh while the standard deviation is 913.4 kWh, indicating a wide spread driven by high-consumption industrial meters. The mean temperature across readings with valid data is 11.6 °C; 62 readings have missing temperature values. For commercial sites, the Pearson correlation between temperature and consumption is −0.64, a moderate negative relationship suggesting lower commercial consumption at higher temperatures.
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636239865442
- [q7] Off-peak tariff consumption (608,076 kWh) marginally exceeded peak tariff consumption (599,624 kWh), with peak accounting for 49.7% of total usage — an almost even split. The dataset covers 12 distinct meters; the highest-consuming single meter recorded 252,241 kWh, representing 20.9% of total consumption. The tariff ranking from highest to lowest is off-peak, peak.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251175, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak
  - Derived share(highest_use_meter_kwh, total_kwh): 20.9

## Limitations
- 62 readings (4.3% of the dataset) have missing temperature values, which may introduce bias into temperature-based analyses, particularly the commercial temperature–consumption correlation.
- Only 19 commercial readings qualify as hot-day observations (temperature ≥ 25 °C), making the hot-day commercial load estimate statistically fragile.
- The dataset covers only 12 distinct meters, limiting the generalisability of findings to the broader meter population.
- Residential consumption is very low relative to other building types (1.3% of total), which may reflect under-representation of residential meters rather than true consumption patterns.
- The analysis uses calendar quarters and half-years; seasonal effects may not align perfectly with these fixed boundaries.
- Correlation does not imply causation; the negative commercial temperature–consumption relationship may be confounded by other variables not present in the dataset.

## Conclusion
Industrial sites drive the vast majority of electricity consumption in 2024, and demand follows a seasonal U-shape with peaks in Q4 and Q1. Second-half consumption grew modestly (+4.7%) relative to the first half. Peak and off-peak tariff usage is nearly balanced. The wide standard deviation and skewed distribution highlight the outsized influence of a small number of high-consumption industrial meters. Improving temperature data completeness and expanding meter coverage would strengthen future analyses.
