# 2024 Smart-Meter Electricity Consumption Report

Analysis of 1,428 cleaned smart-meter readings for 2024 shows total consumption of 1,207,700 kWh across 12 meters. Industrial sites dominate usage, accounting for the vast majority of energy consumed. Consumption dipped mid-year before recovering strongly in Q4, and the second half of the year was 4.7% higher than the first. Peak and off-peak tariffs are nearly evenly split. A moderate negative correlation between temperature and commercial energy use was observed.

## Key findings
- [q1] Across all 1,428 readings in the cleaned dataset, total electricity consumption reached 1,207,700 kWh, with a mean of approximately 845.7 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Industrial buildings consumed by far the most energy at 995,362 kWh (82.4% of total), followed by Commercial at 196,367 kWh (16.3%) and Residential at 15,971 kWh (1.3%).
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
  - Derived share(kwh_industrial, total_kwh): 82.4
  - Derived share(kwh_commercial, total_kwh): 16.3
  - Derived share(kwh_residential, total_kwh): 1.3
- [q3] Quarterly consumption shows Q4 was the highest at 352,882 kWh, followed by Q1 at 319,678 kWh, Q2 at 270,277 kWh, and Q3 the lowest at 264,863 kWh, indicating a mid-year trough and a strong year-end recovery.
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Second-half consumption (617,745 kWh) exceeded first-half consumption (589,955 kWh) by 4.7%, representing an increase of approximately 27,790 kWh.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
  - Derived difference(kwh_h2, kwh_h1): 27789.9
- [q5] On hot days (temperature ≥ 25 °C), there were 19 commercial readings with a mean consumption of 415.3 kWh per reading, suggesting moderate but not extreme load during high-temperature periods.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
- [q6] The median consumption across all readings was 406.8 kWh with a standard deviation of 913.4 kWh, indicating a right-skewed distribution. The mean recorded temperature was 11.6 °C, with 62 readings missing temperature data. For commercial sites, the Pearson correlation between temperature and energy use was -0.64, a moderate negative relationship suggesting higher commercial consumption in cooler conditions.
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636239865442
- [q7] Off-peak tariff consumption (608,076 kWh) marginally exceeded peak tariff consumption (599,624 kWh), with peak accounting for 49.7% of total usage — an almost even split. Across 12 distinct meters, the highest-consuming single meter recorded 252,241 kWh.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251175, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak

## Limitations
- 62 readings (4.3% of the dataset) are missing temperature data, which may introduce bias in temperature-related analyses, particularly the correlation and hot-day filtering.
- Only 19 commercial readings met the hot-day threshold (≥ 25 °C), making the hot-day commercial mean statistically fragile and potentially unrepresentative.
- The dataset covers only 12 distinct meters, limiting the generalisability of findings to the broader meter population.
- Residential consumption is very low relative to other building types (1.3% of total), which may reflect under-representation of residential meters in the sample rather than actual usage patterns.
- Correlation does not imply causation; the negative temperature–commercial energy relationship may be confounded by seasonal factors not captured in this dataset.

## Conclusion
Industrial sites drive the overwhelming majority of 2024 electricity consumption. A mid-year dip in Q2–Q3 reversed sharply in Q4, and the second half of the year was 4.7% higher than the first. Peak and off-peak tariff loads are nearly balanced. Commercial consumption shows a moderate inverse relationship with temperature. Stakeholders should focus efficiency initiatives on industrial meters — particularly the single highest-use meter at 252,241 kWh — and investigate the Q4 demand surge to inform capacity planning for 2025.
