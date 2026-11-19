# 2024 Smart-Meter Electricity Consumption Report

Analysis of 1,428 smart-meter readings across 2024 shows total consumption of 1,207,700 kWh. Industrial sites dominate usage, Q4 was the highest-demand quarter, and the second half of the year grew 4.7% over the first. Peak and off-peak tariffs are nearly balanced, while a moderate negative correlation between temperature and commercial energy use warrants further investigation.

## Key findings
- [q1] Across all 1,428 readings in the cleaned dataset, total electricity consumption reached 1,207,700 kWh, yielding a mean of approximately 845.7 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Industrial buildings consumed the most electricity at 995,362 kWh (82.4% of total), followed by Commercial at 196,367 kWh (16.3%) and Residential at 15,971 kWh (1.3%). Industrial usage is approximately 5.1 times that of Commercial.
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
  - Derived share(kwh_industrial, total_kwh): 82.4
  - Derived share(kwh_commercial, total_kwh): 16.3
  - Derived share(kwh_residential, total_kwh): 1.3
  - Derived ratio(kwh_industrial, kwh_commercial): 5.1
- [q3] Q4 (Oct–Dec) was the highest-consumption quarter at 352,882 kWh, followed by Q1 (319,678 kWh), Q2 (270,277 kWh), and Q3 (264,863 kWh). Mid-year quarters showed the lowest demand, with Q3 being the weakest.
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Second-half consumption (617,745 kWh) exceeded first-half consumption (589,955 kWh), representing an increase of 4.7% half-on-half.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
  - Derived difference(kwh_h2, kwh_h1): 27789.9
- [q5] On hot days (temperature ≥ 25 °C), 19 commercial readings were recorded with a mean consumption of 415.3 kWh per reading, compared to the overall mean of 845.7 kWh, suggesting commercial sites do not exhibit elevated load under high-temperature conditions in this dataset.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
- [q6] The median reading was 406.8 kWh with a sample standard deviation of 913.4 kWh, indicating a right-skewed distribution with high variability. Mean temperature across readings with valid data was 11.6 °C; 62 readings had missing temperature values. For commercial sites, the Pearson correlation between temperature and energy use was −0.64, a moderate negative relationship.
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636239865442
- [q7] Off-peak tariff consumption (608,076 kWh) marginally exceeded peak tariff consumption (599,624 kWh); peak usage accounted for 49.7% of total consumption. The dataset covers 12 distinct meters, and the highest single-meter total was 252,241 kWh.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251175, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak

## Limitations
- 62 readings (4.3% of the dataset) have missing temperature values, which may introduce bias into temperature-based analyses and the commercial correlation estimate.
- Only 19 commercial hot-day readings (temperature ≥ 25 °C) were available, making the hot-day commercial load estimate statistically fragile.
- The dataset covers only 12 distinct meters, limiting the generalisability of meter-level findings to the broader meter population.
- The negative commercial temperature–consumption correlation may reflect confounding factors (e.g., building occupancy patterns or seasonal effects) rather than a direct causal relationship; no causal inference should be drawn.
- Residential consumption is very low relative to other building types, which may indicate under-representation of residential meters in the sample rather than genuinely low residential demand.

## Conclusion
Industrial sites drive the overwhelming majority of electricity consumption, and demand peaks in Q4 and Q1, consistent with heating-season patterns. The modest 4.7% half-year increase and near-equal peak/off-peak split suggest stable load profiles. The strong negative temperature–commercial consumption correlation and the low hot-day commercial mean warrant further investigation. Expanding meter coverage and resolving missing temperature records would materially improve future analyses.
